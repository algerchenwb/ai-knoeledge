"""Original SQLite job ledger demo, not LangGraph or an external side-effect engine."""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite numeric time required")


class Ledger:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=2, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                tenant TEXT NOT NULL, job TEXT NOT NULL, payload_hash TEXT NOT NULL,
                recipe TEXT NOT NULL, state TEXT NOT NULL, generation INTEGER NOT NULL,
                owner TEXT, expires REAL, receipt TEXT,
                PRIMARY KEY(tenant, job));
            CREATE TABLE IF NOT EXISTS outbox (
                tenant TEXT NOT NULL, job TEXT NOT NULL, event TEXT NOT NULL,
                PRIMARY KEY(tenant, job, event));
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def get(self, tenant, job):
        row = self.db.execute("SELECT * FROM jobs WHERE tenant=? AND job=?", (tenant, job)).fetchone()
        return dict(row) if row else None

    def submit(self, tenant, job, payload, recipe):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fingerprint = hashlib.sha256(raw.encode()).hexdigest()
        with self.transaction():
            row = self.get(tenant, job)
            if row:
                if row["payload_hash"] != fingerprint or row["recipe"] != recipe:
                    raise ValueError("same job identity, different input or recipe")
                return False
            self.db.execute("INSERT INTO jobs VALUES(?,?,?,?, 'queued',0,NULL,NULL,NULL)",
                            (tenant, job, fingerprint, recipe))
        return True

    def claim(self, tenant, job, owner, now, duration, recipe):
        finite(now)
        finite(duration)
        if duration <= 0:
            raise ValueError("positive lease required")
        finite(now + duration)
        with self.transaction():
            row = self.get(tenant, job)
            if not row or row["recipe"] != recipe:
                raise ValueError("missing job or incompatible recipe")
            if row["state"] != "queued":
                return None
            generation = row["generation"] + 1
            self.db.execute("UPDATE jobs SET state='running',generation=?,owner=?,expires=? WHERE tenant=? AND job=?",
                            (generation, owner, now + duration, tenant, job))
            return generation

    def heartbeat(self, tenant, job, owner, generation, now, duration):
        finite(now)
        finite(duration)
        if duration <= 0:
            raise ValueError("positive lease required")
        finite(now + duration)
        with self.transaction():
            row = self.get(tenant, job)
            if not self.active(row, owner, generation, now):
                return False
            self.db.execute("UPDATE jobs SET expires=? WHERE tenant=? AND job=?",
                            (max(row["expires"], now + duration), tenant, job))
            return True

    @staticmethod
    def active(row, owner, generation, now):
        return bool(row and row["state"] == "running" and row["owner"] == owner
                    and row["generation"] == generation and now < row["expires"])

    def finish(self, tenant, job, owner, generation, now, receipt, inject_failure=False):
        finite(now)
        with self.transaction():
            row = self.get(tenant, job)
            if not self.active(row, owner, generation, now):
                return False
            self.db.execute("UPDATE jobs SET state='succeeded',receipt=?,owner=NULL,expires=NULL WHERE tenant=? AND job=?",
                            (receipt, tenant, job))
            if inject_failure:
                raise RuntimeError("failure between state and event")
            self.db.execute("INSERT INTO outbox VALUES(?,?, 'completed')", (tenant, job))
            return True

    def expire(self, tenant, job, now):
        finite(now)
        with self.transaction():
            row = self.get(tenant, job)
            if not row or row["state"] != "running" or now < row["expires"]:
                return False
            self.db.execute("UPDATE jobs SET state='unknown',generation=generation+1,owner=NULL,expires=NULL WHERE tenant=? AND job=?",
                            (tenant, job))
            return True

    def reconcile_success(self, tenant, job, receipt):
        # Caller must supply an independently verified receipt; this demo has no verifier.
        with self.transaction():
            row = self.get(tenant, job)
            if not row or row["state"] != "unknown":
                return False
            self.db.execute("UPDATE jobs SET state='succeeded',receipt=? WHERE tenant=? AND job=?", (receipt, tenant, job))
            self.db.execute("INSERT INTO outbox VALUES(?,?, 'completed')", (tenant, job))
            return True

    def event_count(self):
        return self.db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]


class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "jobs.sqlite")
        self.ledger = Ledger(self.path)
        self.ledger.submit("A", "J", {"poi": "P1"}, "v1")

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def claim(self):
        return self.ledger.claim("A", "J", "worker", 0, 10, "v1")

    def test_01_duplicate_submit(self):
        self.assertFalse(self.ledger.submit("A", "J", {"poi": "P1"}, "v1"))

    def test_02_changed_input_rejected(self):
        with self.assertRaises(ValueError):
            self.ledger.submit("A", "J", {"poi": "P2"}, "v1")

    def test_03_recipe_change_rejected(self):
        with self.assertRaises(ValueError):
            self.ledger.claim("A", "J", "worker", 0, 10, "v2")

    def test_04_tenant_isolation(self):
        self.ledger.submit("B", "J", {"poi": "P2"}, "v1")
        self.claim()
        self.assertEqual(self.ledger.get("B", "J")["state"], "queued")

    def test_05_committed_state_visible_in_new_process(self):
        self.claim()
        code = "import sqlite3,sys; d=sqlite3.connect(sys.argv[1]); print(d.execute(\"SELECT state FROM jobs WHERE tenant='A' AND job='J'\").fetchone()[0])"
        r = subprocess.run([sys.executable, "-c", code, self.path], text=True, capture_output=True, timeout=5, check=True)
        self.assertEqual(r.stdout.strip(), "running")

    def test_06_two_connections_one_claim(self):
        barrier = threading.Barrier(2)
        results, errors = [], []
        def contender(owner):
            ledger = Ledger(self.path)
            try:
                barrier.wait(timeout=2)
                results.append(ledger.claim("A", "J", owner, 0, 10, "v1"))
            except BaseException as error:
                errors.append(error)
            finally:
                ledger.close()
        threads = [threading.Thread(target=contender, args=(name,)) for name in ("one", "two")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results, key=lambda x: x is None), [1, None])

    def test_07_heartbeat_extends_without_shortening(self):
        generation = self.claim()
        self.assertTrue(self.ledger.heartbeat("A", "J", "worker", generation, 5, 10))
        self.assertTrue(self.ledger.heartbeat("A", "J", "worker", generation, 6, 1))
        self.assertEqual(self.ledger.get("A", "J")["expires"], 15)

    def test_08_expiry_boundary_blocks_finish(self):
        generation = self.claim()
        self.assertFalse(self.ledger.finish("A", "J", "worker", generation, 10, "receipt"))
        self.assertTrue(self.ledger.expire("A", "J", 10))

    def test_09_stale_owner_and_generation_rejected(self):
        generation = self.claim()
        self.assertFalse(self.ledger.finish("A", "J", "other", generation, 1, "receipt"))
        self.assertFalse(self.ledger.finish("A", "J", "worker", generation + 1, 1, "receipt"))

    def test_10_unknown_is_not_automatically_reclaimed(self):
        self.claim()
        self.ledger.expire("A", "J", 10)
        self.assertIsNone(self.ledger.claim("A", "J", "new", 11, 10, "v1"))
        self.assertEqual(self.ledger.get("A", "J")["state"], "unknown")

    def test_11_completion_and_event_atomic_rollback(self):
        generation = self.claim()
        with self.assertRaises(RuntimeError):
            self.ledger.finish("A", "J", "worker", generation, 1, "receipt", inject_failure=True)
        self.assertEqual(self.ledger.get("A", "J")["state"], "running")
        self.assertEqual(self.ledger.event_count(), 0)

    def test_12_duplicate_completion_no_duplicate_event(self):
        generation = self.claim()
        self.assertTrue(self.ledger.finish("A", "J", "worker", generation, 1, "receipt"))
        self.assertFalse(self.ledger.finish("A", "J", "worker", generation, 2, "receipt"))
        self.assertEqual(self.ledger.event_count(), 1)

    def test_13_external_effect_before_local_receipt_gap(self):
        self.claim()
        external = {("A", "J"): "external-receipt"}  # Mock external effect, outside SQLite.
        self.ledger.close()
        self.ledger = Ledger(self.path)
        self.ledger.expire("A", "J", 10)
        self.assertTrue(self.ledger.reconcile_success("A", "J", external[("A", "J")]))
        self.assertEqual(self.ledger.get("A", "J")["receipt"], "external-receipt")
        self.assertEqual(self.ledger.event_count(), 1)

    def test_14_invalid_lease_rejected(self):
        for duration in (0, -1, True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.ledger.claim("A", "J", "worker", 0, duration, "v1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
