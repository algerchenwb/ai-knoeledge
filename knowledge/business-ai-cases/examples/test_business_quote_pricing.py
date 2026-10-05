import json
import platform
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from business_quote_pricing import digest, examples, fixture_pricing


class Checks(unittest.TestCase):
    def setUp(self):
        self.pricing = fixture_pricing()
        self.line = {"sku": "analysis-unit", "quantity": 150, "discount": "0.10"}
        self.quote = self.build()

    def build(self, lines=None, **kw):
        args = {"lines": [self.line] if lines is None else lines, "currency": "CNY",
                "as_of": "2026-10-05", "valid_days": 14}
        args.update(kw)
        return self.pricing.build(**args)

    def recheck(self, **kw):
        args = {"quote": self.quote, "current_card_version": "rate-demo-2",
                "current_policy_version": "discount-demo-1", "now": "2026-10-06"}
        args.update(kw)
        return self.pricing.recheck(**args)

    def test_graduated_price_not_volume(self):
        row = self.quote["body"]["lines"][0]
        self.assertEqual((row["base"], row["net"]), ("275.00", "247.50"))
        self.assertEqual([s["units"] for s in row["segments"]], [100, 50])

    def test_tier_boundary(self):
        a = self.build([{**self.line, "quantity": 100, "discount": "0"}])
        b = self.build([{**self.line, "quantity": 101, "discount": "0"}])
        self.assertEqual((a["body"]["total"], b["body"]["total"]), ("200.00", "201.50"))

    def test_multiple_lines_and_sum(self):
        quote = self.build([self.line, {"sku": "setup-once", "quantity": 1, "discount": "0"}])
        self.assertEqual(quote["body"]["total"], "297.50")

    def test_line_round_half_up(self):
        card = replace(self.pricing.card, skus=(("analysis-unit", ((None, "0.05"),)),))
        self.pricing = fixture_pricing(card)
        quote = self.build([{**self.line, "quantity": 1}])
        self.assertEqual(quote["body"]["total"], "0.05")

    def test_discount_boundary_allowed(self):
        self.assertEqual(self.quote["body"]["status"], "pricing_checked")
        self.assertEqual(self.recheck()["status"], "pricing_rechecked")

    def test_excess_discount_not_rechecked(self):
        quote = self.build([{**self.line, "discount": "0.20"}])
        self.assertEqual(quote["body"]["status"], "needs_discount_approval")
        with self.assertRaises(ValueError):
            self.recheck(quote=quote)

    def test_duplicate_sku_not_silently_split(self):
        with self.assertRaises(ValueError):
            self.build([self.line, self.line])

    def test_unknown_sku(self):
        with self.assertRaises(ValueError):
            self.build([{**self.line, "sku": "invented"}])

    def test_invalid_quantity(self):
        for quantity in (True, 0, -1, 1.5, 10001):
            with self.assertRaises(ValueError):
                self.build([{**self.line, "quantity": quantity}])

    def test_invalid_discount(self):
        for discount in (0.1, "NaN", "Infinity", "-0.1", "1.01", "1e-1"):
            with self.assertRaises(ValueError):
                self.build([{**self.line, "discount": discount}])

    def test_currency_mismatch(self):
        with self.assertRaises(ValueError):
            self.build(currency="USD")

    def test_inactive_card(self):
        for day in ("2026-08-31", "2026-11-01"):
            with self.assertRaises(ValueError):
                self.build(as_of=day)

    def test_card_end_caps_validity(self):
        quote = self.build(as_of="2026-10-25")
        self.assertEqual(quote["body"]["expires_at"], "2026-11-01")

    def test_invalid_validity(self):
        for days in (True, 0, 15):
            with self.assertRaises(ValueError):
                self.build(valid_days=days)

    def test_expiry_exclusive(self):
        self.assertEqual(self.recheck(now="2026-10-05")["status"], "pricing_rechecked")
        for day in ("2026-10-04", "2026-10-19"):
            with self.assertRaises(ValueError):
                self.recheck(now=day)

    def test_current_versions(self):
        for kw in ({"current_card_version": "rate-demo-3"}, {"current_policy_version": "new-policy"}):
            with self.assertRaises(ValueError):
                self.recheck(**kw)

    def test_forged_total_even_rehashed(self):
        quote = deepcopy(self.quote)
        quote["body"]["total"] = "1.00"
        quote["digest"] = digest(quote["body"])
        with self.assertRaises(ValueError):
            self.recheck(quote=quote)

    def test_customer_binding(self):
        quote = deepcopy(self.quote)
        quote["body"]["customer"] = "other-customer"
        quote["digest"] = digest(quote["body"])
        with self.assertRaises(ValueError):
            self.recheck(quote=quote)

    def test_invalid_tier(self):
        for tiers in (((100, "2.00"), (50, "1.50"), (None, "1.00")),
                      ((100, "2.00"),), ((None, "0.001"),)):
            with self.assertRaises(ValueError):
                fixture_pricing(replace(self.pricing.card, skus=(("analysis-unit", tiers),)))

    def test_input_whitelist(self):
        with self.assertRaises(ValueError):
            self.build([{**self.line, "unit_price": "0.01"}])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(), "checks_passed": result.testsRun,
              "examples": examples(), "limitations": "fictional pre-tax card and trusted customer fixtures; no document extraction, LLM, real discount approval, tax, FX, invoice or payment"}
    Path(__file__).with_name("business-quote-pricing-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
