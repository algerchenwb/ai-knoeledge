"""Hand-checked oracles and failure boundaries for the ten business examples."""
import unittest
from business_rules import (coverage, co_visit, cohort, matched_day_trend, site_score,
                            capability_match, ticket_route, build_report, prewarm, quote_total)


class BusinessRuleChecks(unittest.TestCase):
    def test_coverage_scope_and_dedup(self):
        r = coverage(["a", "b", "b", "c", "d"], ["b", "b", "d", "outsider"])
        self.assertEqual((r["numerator"], r["denominator"], r["ratio"], r["out_of_scope"]), (2, 4, .5, 1))

    def test_empty_denominator(self):
        self.assertIsNone(coverage([], ["a"])["ratio"])
        self.assertIsNone(co_visit([], ["a"])["a_to_b"])

    def test_co_visit_direction(self):
        r = co_visit(["a", "b", "c", "d"], ["b", "d"])
        self.assertEqual((r["overlap"], r["a_to_b"], r["b_to_a"], r["jaccard"]), (2, .5, 1, .5))

    def test_cohort_event_dedup(self):
        r = cohort(["a", "b"], [("1", "a"), ("2", "a"), ("2", "a"), ("3", "c")])
        self.assertEqual((r["active"], r["new"], r["old"], r["old_frequency"]), (2, 1, 1, {2: 1}))

    def test_conflicting_event(self):
        with self.assertRaises(ValueError):
            cohort([], [("1", "a"), ("1", "b")])

    def test_trend_maturity_and_matching(self):
        self.assertEqual(matched_day_trend({"work": [80, 100]}, {"work": [100, 100]}, True)["changes"], {"work": -.1})
        self.assertEqual(matched_day_trend({}, {}, False)["status"], "provisional")
        with self.assertRaises(ValueError):
            matched_day_trend({"work": [100]}, {"holiday": [100]}, True)
        with self.assertRaises(ValueError):
            matched_day_trend({"work": [None]}, {"work": [100]}, True)

    def test_site_score_oracle(self):
        r = site_score({"demand": 80, "access": 60, "cost_fit": 40}, {"demand": .5, "access": .3, "cost_fit": .2}, True)
        self.assertEqual(r["score"], "66.0")
        self.assertEqual(r["contributions"], {"demand": "40.0", "access": "18.0", "cost_fit": "8.0"})

    def test_site_missing_and_gate(self):
        self.assertIsNone(site_score({"x": None}, {"x": 1}, True)["score"])
        self.assertEqual(site_score({"x": 99}, {"x": 1}, False)["status"], "ineligible")
        with self.assertRaises(ValueError):
            site_score({"x": 1}, {"x": .5}, True)

    def test_capability_gap(self):
        r = capability_match(["query", "export"], ["query"])
        self.assertEqual((r["status"], r["missing"]), ("gap", ["export"]))

    def test_ticket_route(self):
        self.assertEqual(ticket_route("data_delay", True), {"team": "data_operations", "priority": "high"})
        self.assertEqual(ticket_route("unknown")["team"], "manual_triage")

    def test_report_missing_cause(self):
        r = build_report(["change", "cause"], [{"id": "s1", "supports": ["change"]}])
        self.assertEqual(r["status"], "partial")
        self.assertEqual(r["sections"][1]["sources"], [])

    def test_prewarm_keys_and_retries(self):
        calls = []
        def fetch(key):
            calls.append(key)
            if key == ("B", 1) and calls.count(key) == 1:
                raise TimeoutError()
            return 10
        r = prewarm([("A", 1), ("A", 1), ("A", 2), ("B", 1)], fetch)
        self.assertEqual(len(r), 3)
        self.assertEqual(calls, [("A", 1), ("A", 2), ("B", 1), ("B", 1)])
        self.assertTrue(all(item["status"] == "ok" for item in r))

    def test_prewarm_bounded_failure(self):
        def fail(key):
            raise TimeoutError()
        r = prewarm([("A", 1)], fail, 2)
        self.assertEqual(r, [{"target": ["A", 1], "status": "failed", "attempts": 2}])

    def test_quote_exact_decimal(self):
        self.assertEqual(quote_total([{"quantity": 20, "unit_price": "120.00", "currency": "CNY"}], "300.00"), {"currency": "CNY", "total": "2700.00"})
        with self.assertRaises(ValueError):
            quote_total([{"quantity": 1, "unit_price": "2.00", "currency": "USD"}])
        with self.assertRaises(ValueError):
            quote_total([{"quantity": 1, "unit_price": "2.001", "currency": "CNY"}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
