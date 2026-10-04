import json
import platform
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from support_ticket_demo import Actor, Rejected, Tickets, examples


class Checks(unittest.TestCase):
    def setUp(self):
        self.book = Tickets()
        self.bot = Actor("a", False)
        self.human = Actor("a", True)
        self.created = self.book.create(self.bot, "c1", "data", "p1", 100)
        self.id = self.created["ticket"]["id"]

    def tearDown(self):
        self.book.close()

    def assign(self):
        return self.book.action(self.human, "a1", self.id, 1, "assign", 101)

    def test_creation_receipt(self):
        t = self.created["ticket"]
        self.assertEqual((t["state"], t["queue"], t["version"], t["due_at"]),
                         ("new", "data-support", 1, 160))

    def test_retry_creates_once(self):
        r = self.book.create(self.bot, "c1", "data", "p1", 120)
        self.assertTrue(r["replayed"])
        self.assertEqual(r["ticket"], self.created["ticket"])
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], 1)

    def test_key_payload_conflict(self):
        with self.assertRaises(Rejected):
            self.book.create(self.bot, "c1", "account", "p1", 120)

    def test_tenant_key_partition(self):
        other = self.book.create(Actor("b", False), "c1", "data", "p1", 100)
        self.assertNotEqual(other["ticket"]["id"], self.id)

    def test_cross_tenant_cannot_act(self):
        with self.assertRaises(Rejected):
            self.book.action(Actor("b", True), "a1", self.id, 1, "assign", 101)

    def test_agent_cannot_resolve_or_assign(self):
        for op in ("assign", "resolve"):
            with self.assertRaises(Rejected):
                self.book.action(self.bot, "x", self.id, 1, op, 101, "proof" if op == "resolve" else None)

    def test_assign_does_not_count_as_response(self):
        self.assertIsNone(self.assign()["ticket"]["first_response_at"])

    def test_stale_version(self):
        self.assign()
        with self.assertRaises(Rejected):
            self.book.action(self.human, "r1", self.id, 1, "respond", 102)

    def test_invalid_transition_rolled_back(self):
        with self.assertRaises(Rejected):
            self.book.action(self.human, "r1", self.id, 1, "resolve", 101, "proof")
        self.assertEqual(self.book.get(self.human, self.id)["version"], 1)
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0], 1)

    def test_action_retry_uses_original_receipt(self):
        original = self.assign()
        self.book.action(self.human, "r1", self.id, 2, "respond", 102)
        retry = self.book.action(self.human, "a1", self.id, 1, "assign", 103)
        self.assertTrue(retry["replayed"])
        self.assertEqual(retry["ticket"], original["ticket"])
        self.assertEqual(self.book.get(self.human, self.id)["version"], 3)

    def test_action_key_conflict(self):
        self.assign()
        with self.assertRaises(Rejected):
            self.book.action(self.human, "a1", self.id, 2, "respond", 102)

    def test_first_response_preserved(self):
        self.assign()
        self.book.action(self.human, "r1", self.id, 2, "respond", 102)
        r = self.book.action(self.human, "r2", self.id, 3, "respond", 110)
        self.assertEqual(r["ticket"]["first_response_at"], 102)

    def test_before_due_and_due_boundary(self):
        self.assertEqual(self.book.escalate_due(self.bot, 159), [])
        r = self.book.escalate_due(self.bot, 160)
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["queue"], r[0]["version"]), ("human-escalation", 2))

    def test_escalate_once(self):
        self.book.escalate_due(self.bot, 160)
        self.assertEqual(self.book.escalate_due(self.bot, 200), [])
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM events WHERE kind='escalated'").fetchone()[0], 1)

    def test_response_stops_first_response_escalation(self):
        self.assign()
        self.book.action(self.human, "r1", self.id, 2, "respond", 102)
        self.assertEqual(self.book.escalate_due(self.bot, 200), [])

    def test_wait_does_not_pause_first_response_timer(self):
        self.assign()
        self.book.action(self.human, "w1", self.id, 2, "wait_customer", 102)
        self.assertEqual(len(self.book.escalate_due(self.bot, 160)), 1)

    def test_resume(self):
        self.assign()
        self.book.action(self.human, "w1", self.id, 2, "wait_customer", 102)
        r = self.book.action(self.human, "back", self.id, 3, "resume", 103)
        self.assertEqual(r["ticket"]["state"], "assigned")

    def test_resolve_requires_reference(self):
        self.assign()
        with self.assertRaises(Rejected):
            self.book.action(self.human, "done", self.id, 2, "resolve", 102)

    def test_resolved_is_terminal_and_not_escalated(self):
        self.assign()
        r = self.book.action(self.human, "done", self.id, 2, "resolve", 102, "proof")
        self.assertEqual(r["ticket"]["state"], "resolved")
        self.assertEqual(self.book.escalate_due(self.bot, 200), [])
        with self.assertRaises(Rejected):
            self.book.action(self.human, "again", self.id, 3, "assign", 201)

    def test_tenant_scoped_escalation(self):
        self.assertEqual(self.book.escalate_due(Actor("b", False), 200), [])
        self.assertEqual(self.book.get(self.human, self.id)["queue"], "data-support")

    def test_clock_regression(self):
        self.assign()
        with self.assertRaises(Rejected):
            self.book.action(self.human, "r", self.id, 2, "respond", 100)

    def test_invalid_inputs(self):
        for key, priority, now in (("", "p1", 100), ("x", "p9", 100), ("x", "p1", True)):
            with self.assertRaises(Rejected):
                self.book.create(self.bot, key, "data", priority, now)

    def test_disk_reopen_preserves_receipt_and_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "tickets.sqlite")
            first = Tickets(path)
            original = first.create(self.bot, "disk", "data", "p1", 100)
            first.close()
            second = Tickets(path)
            try:
                retry = second.create(self.bot, "disk", "data", "p1", 101)
                self.assertTrue(retry["replayed"])
                self.assertEqual(retry["ticket"], original["ticket"])
            finally:
                second.close()

    def test_two_connection_duplicate_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "tickets.sqlite")
            seed = Tickets(path)
            seed.close()
            gate = threading.Barrier(2)
            def worker():
                book = Tickets(path)
                try:
                    gate.wait(timeout=5)
                    return book.create(self.bot, "same", "data", "p1", 100)
                finally:
                    book.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: worker(), range(2)))
            self.assertEqual(sorted(r["replayed"] for r in results), [False, True])
            self.assertEqual(results[0]["ticket"]["id"], results[1]["ticket"]["id"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(),
              "checks_passed": result.testsRun, "examples": examples(),
              "limitations": "synthetic tickets and trusted actor fixtures; local SQLite only; no LLM, authentication, real support platform, notification or contractual SLA"}
    Path(__file__).with_name("support-ticket-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
