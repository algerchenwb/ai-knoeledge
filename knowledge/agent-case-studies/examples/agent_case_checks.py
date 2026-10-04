"""Ten independent offline teaching checks. No LLM/framework integration tests."""
import sqlite3
import unittest


class AgentMechanismChecks(unittest.TestCase):
    def test_01_sql_readonly(self):
        db = sqlite3.connect(":memory:")
        db.execute("create table metrics (value integer)")
        db.execute("insert into metrics values (7)")
        db.execute("pragma query_only=on")
        self.assertEqual(db.execute("select value from metrics").fetchone(), (7,))
        with self.assertRaises(sqlite3.OperationalError):
            db.execute("delete from metrics")
        db.close()

    def test_02_handoff_state(self):
        state = {"agent": "triage", "order": "fictional-order", "seat": None}
        state["agent"] = "seat_booking"
        state["seat"] = "12A"
        self.assertEqual(state, {"agent": "seat_booking", "order": "fictional-order", "seat": "12A"})

    def test_03_bounded_feedback(self):
        def run(outcomes, limit):
            attempts = 0
            for ok in outcomes:
                if attempts >= limit:
                    break
                attempts += 1
                if ok:
                    return "done", attempts
            return "failed", attempts
        self.assertEqual(run([False, True], 2), ("done", 2))
        self.assertEqual(run([False, False, True], 2), ("failed", 2))

    def test_04_task_dependency(self):
        results = {}
        def report():
            if "research" not in results:
                raise ValueError("missing evidence")
            return {"evidence": results["research"]}
        with self.assertRaises(ValueError):
            report()
        results["research"] = {"claim": "fixture", "version": 1}
        self.assertIs(report()["evidence"], results["research"])

    def test_05_receipt_oracle(self):
        db = sqlite3.connect(":memory:")
        db.execute("create table receipts (name text, price real, tip real)")
        db.executemany("insert into receipts values (?,?,?)", [
            ("Alan Payne", 12.06, 1.20), ("Alex Mason", 23.86, .24),
            ("Woodrow Wilson", 53.43, 5.43), ("Margaret James", 21.11, 1.00)])
        self.assertEqual(db.execute("select name,price from receipts order by price desc limit 1").fetchone(), ("Woodrow Wilson", 53.43))
        self.assertAlmostEqual(db.execute("select max(price+tip) from receipts").fetchone()[0], 58.86)
        db.close()

    def test_06_repair_regression(self):
        def before(params):
            return 200, params["region"]
        with self.assertRaises(KeyError):
            before({})
        def after(params):
            if not params.get("region"):
                return 400, "missing region"
            return 200, params["region"]
        self.assertEqual(after({}), (400, "missing region"))
        self.assertEqual(after({"region": "fictional-region"}), (200, "fictional-region"))

    def test_07_event_deduplication(self):
        seen = {}
        def register(event_id):
            if event_id not in seen:
                seen[event_id] = f"run-{len(seen)+1}"
            return seen[event_id]
        self.assertEqual(register("event-a"), register("event-a"))
        self.assertNotEqual(register("event-a"), register("event-b"))
        self.assertEqual(len(seen), 2)

    def test_08_stale_page(self):
        def click(observed_version, current_version):
            if observed_version != current_version:
                raise ValueError("observe again")
            return "clicked"
        with self.assertRaises(ValueError):
            click(1, 2)
        self.assertEqual(click(2, 2), "clicked")

    def test_09_citation_fixture(self):
        evidence = {"source-a": {"supports": {"claim-1"}}}
        def validate(claim, source):
            return source in evidence and claim in evidence[source]["supports"]
        self.assertTrue(validate("claim-1", "source-a"))
        self.assertFalse(validate("claim-2", "source-a"))
        self.assertFalse(validate("claim-1", "unknown"))

    def test_10_retrieval_scope(self):
        docs = [{"company": "A", "year": 2021, "tenant": "t1", "value": 10},
                {"company": "B", "year": 2021, "tenant": "t1", "value": 20},
                {"company": "A", "year": 2021, "tenant": "t2", "value": 99}]
        def retrieve(company, year, tenant):
            return [d for d in docs if (d["company"], d["year"], d["tenant"]) == (company, year, tenant)]
        self.assertEqual([d["value"] for d in retrieve("A", 2021, "t1")], [10])
        self.assertEqual(retrieve("A", 2026, "t1"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
