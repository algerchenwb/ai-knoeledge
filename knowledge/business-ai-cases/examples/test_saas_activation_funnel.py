import json
import platform
import unittest
from dataclasses import replace
from pathlib import Path
from saas_activation_funnel import analyze, examples, fixtures


class Checks(unittest.TestCase):
    def setUp(self):
        self.events, self.options = fixtures()

    def run_funnel(self, events=None, **kw):
        return analyze(self.events if events is None else events, **{**self.options, **kw})

    def test_counts_and_denominators(self):
        r = self.run_funnel()
        self.assertEqual((r["entrants"], r["eligible"], r["pending"], r["queried"], r["activated"]), (4, 3, 1, 3, 1))
        self.assertEqual(r["signup_to_report"], {"numerator": 1, "denominator": 3, "ratio": 1 / 3})

    def test_duplicate_delivery(self):
        self.assertEqual(self.run_funnel(), self.run_funnel(self.events * 2))

    def test_conflicting_duplicate(self):
        with self.assertRaises(ValueError):
            self.run_funnel(self.events + [replace(self.events[0], user_id="other")])

    def test_tenant_isolation(self):
        foreign = [replace(e, tenant="b") for e in self.events]
        self.assertEqual(self.run_funnel(), self.run_funnel(self.events + foreign))

    def test_event_order_not_delivery_order(self):
        self.assertEqual(self.run_funnel(), self.run_funnel(list(reversed(self.events))))

    def test_report_before_query_not_activation(self):
        r = self.run_funnel(self.events[5:8])
        self.assertEqual((r["queried"], r["activated"]), (1, 0))

    def test_missing_query_not_activation(self):
        r = self.run_funnel([self.events[0], self.events[2]])
        self.assertEqual((r["queried"], r["activated"]), (0, 0))

    def test_query_at_signup_strict_order(self):
        r = self.run_funnel([self.events[0], replace(self.events[1], at=self.events[0].at), self.events[2]])
        self.assertEqual(r["activated"], 0)

    def test_report_at_query_strict_order(self):
        r = self.run_funnel([self.events[0], self.events[1], replace(self.events[2], at=self.events[1].at)])
        self.assertEqual(r["activated"], 0)

    def test_deadline_exclusive(self):
        r = self.run_funnel([self.events[0], self.events[1], replace(self.events[2], at="2026-09-08T00:00:00Z")])
        self.assertEqual(r["activated"], 0)

    def test_followup_equal_cutoff_mature(self):
        r = self.run_funnel(self.events[5:8])
        self.assertEqual((r["eligible"], r["pending"]), (1, 0))

    def test_cohort_end_exclusive(self):
        r = self.run_funnel([replace(self.events[0], at=self.options["cohort_end"])])
        self.assertEqual(r["entrants"], 0)

    def test_repeated_signup_one_user(self):
        r = self.run_funnel(self.events + [replace(self.events[0], event_id="s1-again", at="2026-09-05T00:00:00Z")])
        self.assertEqual(r["entrants"], 4)

    def test_no_mature_sample_is_not_zero(self):
        r = self.run_funnel([self.events[-1]])
        self.assertEqual(r["status"], "no_mature_sample")
        self.assertIsNone(r["signup_to_report"]["ratio"])

    def test_coverage_gaps(self):
        for kw in ({"coverage_start": "2026-09-02T00:00:00Z"}, {"coverage_end": "2026-09-09T00:00:00Z"}):
            with self.assertRaises(ValueError):
                self.run_funnel(**kw)

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            self.run_funnel([replace(self.events[0], at="2026-09-01T00:00:00")])

    def test_invalid_window(self):
        for window in (True, 0, 31):
            with self.assertRaises(ValueError):
                self.run_funnel(window_days=window)

    def test_cutoff_future_event_excluded(self):
        future = replace(self.events[2], event_id="future-report", user_id="u2", at=self.options["as_of"])
        self.assertEqual(self.run_funnel(), self.run_funnel(self.events + [future]))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(), "checks_passed": result.testsRun,
              "examples": examples(), "limitations": "synthetic user events and trusted coverage fixtures; no LLM, real telemetry, identity merging, statistical significance or PostHog execution"}
    Path(__file__).with_name("saas-activation-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
