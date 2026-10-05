import json
import platform
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from business_report_gate import SUPPORTED, digest, examples, fixture_gate


class Checks(unittest.TestCase):
    def setUp(self):
        self.gate = fixture_gate()
        self.metrics = list(self.gate.metrics.values())
        self.draft = self.gate.prepare(sorted(SUPPORTED))
        self.approval = self.gate.approve(self.draft, "reviewer-demo", 100, 200)
        self.versions = {m.name: m.data_version for m in self.metrics}

    def check(self, **kw):
        args = {"draft": self.draft, "approval": self.approval,
                "current_versions": self.versions, "current_policy": "report-policy-1", "now": 101}
        args.update(kw)
        return self.gate.check_release(**args)

    def prepare_metrics(self, metrics):
        return fixture_gate(metrics).prepare(sorted(SUPPORTED))

    def test_exact_values(self):
        values = {s["metric"]: s["value"] for s in self.draft["body"]["sections"]}
        self.assertEqual(values, {"coverage": "0.5", "co_visit": "0.3", "traffic_change": "-0.1"})

    def test_release_eligible(self):
        self.assertEqual(self.check()["status"], "eligible_for_release")

    def test_required_order_canonical(self):
        self.assertEqual(self.draft, self.gate.prepare(list(reversed(sorted(SUPPORTED)))))

    def test_missing_metric_partial(self):
        draft = self.prepare_metrics(self.metrics[:2])
        self.assertEqual(draft["body"]["status"], "partial")
        self.assertEqual(draft["body"]["sections"][-1]["status"], "missing")

    def test_provisional_not_approved(self):
        gate = fixture_gate([replace(m, mature=False) for m in self.metrics])
        draft = gate.prepare(sorted(SUPPORTED))
        self.assertEqual(draft["body"]["sections"][0]["status"], "provisional")
        with self.assertRaises(ValueError):
            gate.approve(draft, "reviewer", 100, 200)

    def test_empty_denominator_undefined(self):
        draft = self.prepare_metrics([replace(self.metrics[0], numerator=0, denominator=0), *self.metrics[1:]])
        section = next(s for s in draft["body"]["sections"] if s["metric"] == "coverage")
        self.assertEqual((section["status"], section["value"]), ("undefined", None))

    def test_object_mismatch(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], object_id="other"), *self.metrics[1:]])

    def test_period_mismatch(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], period=("2026-08-01", "2026-09-01")), *self.metrics[1:]])

    def test_definition_mismatch(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], definition="old"), *self.metrics[1:]])

    def test_bool_count_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], numerator=True), *self.metrics[1:]])

    def test_subset_out_of_range(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], numerator=101), *self.metrics[1:]])

    def test_missing_evidence(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([replace(self.metrics[0], evidence_id=" "), *self.metrics[1:]])

    def test_duplicate_evidence(self):
        with self.assertRaises(ValueError):
            self.prepare_metrics([self.metrics[0], replace(self.metrics[1], evidence_id=self.metrics[0].evidence_id), self.metrics[2]])

    def test_duplicate_metric(self):
        with self.assertRaises(ValueError):
            fixture_gate([self.metrics[0], self.metrics[0]])

    def test_unknown_required(self):
        for required in ([], ["coverage", "coverage"], ["change_cause"]):
            with self.assertRaises(ValueError):
                self.gate.prepare(required)

    def test_changed_body_even_rehashed(self):
        draft = deepcopy(self.draft)
        draft["body"]["sections"][0]["value"] = "0.99"
        draft["digest"] = digest(draft["body"])
        with self.assertRaises(ValueError):
            self.check(draft=draft)

    def test_added_causal_text_rejected(self):
        draft = deepcopy(self.draft)
        draft["body"]["cause"] = "marketing failed"
        draft["digest"] = digest(draft["body"])
        with self.assertRaises(ValueError):
            self.check(draft=draft)

    def test_approval_hash_mismatch(self):
        with self.assertRaises(ValueError):
            self.check(approval={**self.approval, "digest": "other"})

    def test_approval_tenant_mismatch(self):
        with self.assertRaises(ValueError):
            self.check(approval={**self.approval, "tenant": "other"})

    def test_approval_expiry_boundary(self):
        self.assertEqual(self.check(now=100)["status"], "eligible_for_release")
        for now in (99, 200):
            with self.assertRaises(ValueError):
                self.check(now=now)

    def test_data_version_changed(self):
        with self.assertRaises(ValueError):
            self.check(current_versions={**self.versions, "coverage": "coverage-data-3"})

    def test_missing_current_version(self):
        with self.assertRaises(ValueError):
            self.check(current_versions={"coverage": "coverage-data-2"})

    def test_policy_changed(self):
        with self.assertRaises(ValueError):
            self.check(current_policy="report-policy-2")

    def test_result_copy_isolated(self):
        result = self.check()
        result["manifest"]["sections"][0]["value"] = "edited"
        self.assertEqual(self.check()["status"], "eligible_for_release")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(),
              "checks_passed": result.testsRun, "examples": examples(),
              "limitations": "synthetic trusted snapshots and approval fixtures; no LLM, causal-text validation, real evidence service, authentication or publication"}
    Path(__file__).with_name("business-report-gate-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
