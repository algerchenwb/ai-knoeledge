import json
import platform
import unittest
from dataclasses import replace
from pathlib import Path
from ai_business_pilot import assign, examples, fixtures, summarize


class Checks(unittest.TestCase):
    def setUp(self):
        self.enrollments, self.outcomes, self.options = fixtures()

    def report(self, enrollments=None, outcomes=None, **kw):
        return summarize(self.enrollments if enrollments is None else enrollments,
                         self.outcomes if outcomes is None else outcomes, **{**self.options, **kw})

    def test_stable_assignment(self):
        for row in self.enrollments:
            self.assertEqual(assign(row.tenant, row.unit, row.experiment, row.version), row.arm)

    def test_hand_counts(self):
        r = self.report()
        self.assertEqual((r["arms"]["A"]["successes"], r["arms"]["B"]["successes"]), (6, 8))
        self.assertAlmostEqual(r["observed_absolute_difference"], 0.2)
        self.assertEqual(r["decision"], "ready_for_statistical_review")

    def test_cost_totals(self):
        r = self.report()
        self.assertEqual((r["arms"]["A"]["total_observed_cost"], r["arms"]["B"]["total_observed_cost"]), ("20.00", "30.00"))

    def test_duplicate_identical_records(self):
        self.assertEqual(self.report(), self.report(self.enrollments * 2, self.outcomes * 2))

    def test_assignment_conflict(self):
        with self.assertRaises(ValueError):
            self.report([replace(self.enrollments[0], arm="B" if self.enrollments[0].arm == "A" else "A")])

    def test_enrollment_conflict(self):
        with self.assertRaises(ValueError):
            self.report(self.enrollments + [replace(self.enrollments[0], enrolled_at=101)])

    def test_outcome_conflict(self):
        with self.assertRaises(ValueError):
            self.report(outcomes=self.outcomes + [replace(self.outcomes[0], success=not self.outcomes[0].success)])

    def test_missing_outcome_not_failure(self):
        r = self.report(outcomes=self.outcomes[:-1])
        self.assertEqual(r["decision"], "data_incomplete")
        arm = self.enrollments[-1].arm
        self.assertIsNone(r["arms"][arm]["success_rate"])
        self.assertEqual(r["arms"][arm]["missing"], 1)

    def test_not_mature(self):
        r = self.report(now=106)
        self.assertEqual(r["decision"], "insufficient_sample")
        self.assertEqual(r["arms"]["A"]["pending"], 10)

    def test_sample_policy(self):
        self.assertEqual(self.report(min_per_arm=11)["decision"], "insufficient_sample")

    def test_cost_guardrail(self):
        self.assertEqual(self.report(max_average_cost="2.50")["decision"], "guardrail_failed")

    def test_safety_guardrail(self):
        self.assertEqual(self.report(max_failure_rate=0)["decision"], "guardrail_failed")

    def test_unregistered_outcome(self):
        with self.assertRaises(ValueError):
            self.report(outcomes=self.outcomes + [replace(self.outcomes[0], unit="unknown")])

    def test_invalid_outcome_types(self):
        for row in (replace(self.outcomes[0], success=1), replace(self.outcomes[0], cost="NaN"),
                    replace(self.outcomes[0], cost="-1")):
            with self.assertRaises(ValueError):
                self.report(outcomes=[row, *self.outcomes[1:]])

    def test_invalid_clock_and_policy(self):
        for kw in ({"now": True}, {"min_per_arm": 0}, {"max_failure_rate": -1}, {"max_average_cost": "NaN"}):
            with self.assertRaises(ValueError):
                self.report(**kw)

    def test_foreign_enrollment_ignored(self):
        self.assertEqual(self.report(), self.report(self.enrollments + [replace(self.enrollments[0], tenant="other")]))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(), "checks_passed": result.testsRun,
              "examples": examples(), "limitations": "synthetic experiment units and completed outcome fixtures; no LLM, real assignment service, statistical inference or GrowthBook execution"}
    Path(__file__).with_name("ai-business-pilot-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
