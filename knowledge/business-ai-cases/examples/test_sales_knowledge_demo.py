"""Boundary checks for fictional capability facts, not model benchmarks."""
import json
import platform
import unittest
from dataclasses import replace
from pathlib import Path
from sales_knowledge_demo import CapabilityBook, examples, fixture_book


class Checks(unittest.TestCase):
    def setUp(self):
        self.book = fixture_book()
        self.context = {"plan": "pro", "region": "CN"}

    def query(self, **kw):
        args = {"product": "atlas", "capability": "export", "as_of": "2026-10-05",
                "context": self.context}
        args.update(kw)
        return self.book.answer(**args)

    def test_supported(self):
        r = self.query()
        self.assertEqual(r["status"], "supported")
        self.assertEqual(r["record_ids"], ["export-v2"])
        self.assertEqual(r["evidence_ids"], ["release-2#export"])

    def test_missing_region(self):
        r = self.query(context={"plan": "pro"})
        self.assertEqual(r["status"], "needs_info")
        self.assertEqual(r["missing_fields"], ["region"])

    def test_wrong_plan(self):
        r = self.query(context={"plan": "basic", "region": "CN"})
        self.assertEqual(r["status"], "not_applicable")
        self.assertEqual(r["failed_conditions"], ["plan"])

    def test_known_failure_before_missing(self):
        r = self.query(context={"plan": "basic"})
        self.assertEqual(r["status"], "not_applicable")
        self.assertEqual(r["missing_fields"], ["region"])

    def test_approved_plan(self):
        self.assertEqual(self.query(capability="forecast")["status"], "planned")

    def test_explicit_unsupported(self):
        self.assertEqual(self.query(capability="realtime")["status"], "unsupported")

    def test_unknown_is_not_unsupported(self):
        r = self.query(capability="unknown")
        self.assertEqual(r["status"], "insufficient_evidence")
        self.assertEqual(r["record_ids"], [])

    def test_product_isolation(self):
        self.assertEqual(self.query(product="other")["record_ids"], [])

    def test_internal_hidden(self):
        r = self.query(capability="private-preview")
        self.assertEqual(r["status"], "insufficient_evidence")
        self.assertEqual(r["evidence_ids"], [])

    def test_internal_service_context(self):
        self.assertEqual(self.query(capability="private-preview", audience="internal")["status"], "supported")

    def test_expiry_exclusive_and_start_inclusive(self):
        r = self.query(as_of="2026-09-01")
        self.assertEqual(r["record_ids"], ["export-v2"])

    def test_historical_version(self):
        r = self.query(as_of="2026-08-31", context={"plan": "basic"})
        self.assertEqual(r["record_ids"], ["export-v1"])
        self.assertEqual(r["status"], "supported")

    def test_future_only(self):
        self.assertEqual(self.query(as_of="2025-12-31")["status"], "insufficient_evidence")

    def test_latest_draft_cannot_override(self):
        self.assertNotIn("export-v3-draft", self.query()["record_ids"])

    def test_conflicting_approved_records(self):
        fact = self.book.facts[1]
        self.book = CapabilityBook((fact, replace(fact, record_id="conflict", state="unsupported")), "test")
        self.assertEqual(self.query()["status"], "conflict")

    def test_blank_evidence(self):
        self.book = CapabilityBook((replace(self.book.facts[1], evidence=" "),), "test")
        self.assertEqual(self.query()["status"], "insufficient_evidence")

    def test_bad_context(self):
        for ctx in ({"plan": True}, {"plan": ""}, {"admin": "true"}):
            with self.assertRaises(ValueError):
                self.query(context=ctx)

    def test_bad_date_or_audience(self):
        for args in ({"as_of": "2026-02-30"}, {"audience": "admin"}):
            with self.assertRaises(ValueError):
                self.query(**args)

    def test_duplicate_id_and_bad_interval(self):
        fact = self.book.facts[1]
        for facts in ((fact, fact), (replace(fact, end=fact.start),)):
            with self.assertRaises(ValueError):
                CapabilityBook(facts, "test")

    def test_invalid_prerequisites(self):
        fact = self.book.facts[1]
        for req in ((("secret", "x"),), (("plan", "pro"), ("plan", "basic"))):
            with self.assertRaises(ValueError):
                CapabilityBook((replace(fact, requirements=req),), "test")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(),
              "checks_passed": result.testsRun, "examples": examples(),
              "limitations": "offline exact-key synthetic facts; no LLM, embeddings, retrieval engine, CRM, authorization service or evidence existence checks"}
    Path(__file__).with_name("sales-knowledge-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
