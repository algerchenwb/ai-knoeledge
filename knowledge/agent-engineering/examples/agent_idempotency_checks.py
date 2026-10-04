"""Offline failure-injection model. Not a distributed service or framework test."""
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path


class KeyConflict(Exception):
    pass


class AmbiguousOutcome(Exception):
    pass


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


class MockReportService:
    """Dedupe and the simulated side effect share one SQLite transaction."""
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS operations (tenant TEXT, op TEXT, digest TEXT, receipt TEXT, PRIMARY KEY(tenant,op))")
            db.execute("CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, tenant TEXT, body TEXT)")

    def submit(self, tenant, op, payload, lose_response=False, crash_before_commit=False):
        digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT digest,receipt FROM operations WHERE tenant=? AND op=?", (tenant, op)).fetchone()
            if existing:
                if existing[0] != digest:
                    raise KeyConflict("same operation ID with different payload")
                receipt = json.loads(existing[1])
            else:
                cursor = db.execute("INSERT INTO reports(tenant,body) VALUES (?,?)", (tenant, canonical(payload)))
                receipt = {"report_id": cursor.lastrowid, "status": "succeeded"}
                db.execute("INSERT INTO operations VALUES (?,?,?,?)", (tenant, op, digest, canonical(receipt)))
                if crash_before_commit:
                    raise RuntimeError("simulated failure before transaction commit")
        # The transaction has committed; a timeout is not evidence of rollback.
        if lose_response:
            raise AmbiguousOutcome("response lost after commit")
        return receipt

    def lookup(self, tenant, op):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT receipt FROM operations WHERE tenant=? AND op=?", (tenant, op)).fetchone()
        return None if row is None else json.loads(row[0])

    def count(self):
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT count(*) FROM reports").fetchone()[0]


def checks():
    payload = {"month": "2026-09", "region": "demo-region", "input_version": "v1"}
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "service.sqlite")
        service = MockReportService(path)
        # 1. Remote commit succeeds but neither reply nor local checkpoint survives.
        try:
            service.submit("tenant-a", "task-42/report-v1", payload, lose_response=True)
            raise AssertionError("failure injection did not run")
        except AmbiguousOutcome:
            pass
        assert service.count() == 1
        # Reconstruct service object, query authority, then reuse the same operation ID.
        recovered = MockReportService(path)
        queried = recovered.lookup("tenant-a", "task-42/report-v1")
        retried = recovered.submit("tenant-a", "task-42/report-v1", dict(reversed(list(payload.items()))))
        assert queried == retried and recovered.count() == 1
        # 2. Multiple calls with the same ID and parameter order changes are deduplicated.
        for _ in range(5):
            assert recovered.submit("tenant-a", "task-42/report-v1", payload) == retried
        assert recovered.count() == 1
        # 3. Same ID, changed body is rejected before another side effect.
        try:
            recovered.submit("tenant-a", "task-42/report-v1", {**payload, "month": "2026-10"})
            raise AssertionError("conflict not detected")
        except KeyConflict:
            pass
        assert recovered.count() == 1
        # 4. Tenant namespace prevents another tenant from inheriting a receipt.
        other = recovered.submit("tenant-b", "task-42/report-v1", payload)
        assert other["report_id"] != retried["report_id"] and recovered.count() == 2
        # 5. Failure inside transaction rolls both the report and ledger back.
        try:
            recovered.submit("tenant-a", "task-43/report-v1", payload, crash_before_commit=True)
            raise AssertionError("failure injection did not run")
        except RuntimeError:
            pass
        assert recovered.lookup("tenant-a", "task-43/report-v1") is None
        assert recovered.count() == 2
        recovered.submit("tenant-a", "task-43/report-v1", payload)
        assert recovered.count() == 3
        # 6. New IDs bypass deduplication even when the business intent is unchanged.
        recovered.submit("tenant-a", "wrong-new-id-1", payload)
        recovered.submit("tenant-a", "wrong-new-id-2", payload)
        assert recovered.count() == 5
        return {"checks_passed": 6, "after_lost_response_and_retries": 1,
                "after_tenant_and_rollback_checks": 3,
                "after_wrong_new_ids": recovered.count(),
                "recovered_receipt": queried}


if __name__ == "__main__":
    print(json.dumps(checks(), indent=2))
