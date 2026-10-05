"""Original exact arithmetic for descriptive changes, not causal estimation."""
from fractions import Fraction
import random
import unittest


def checked(groups):
    if not groups:
        raise ValueError("nonempty groups required")
    result = {}
    for name, counts in groups.items():
        n, d = counts
        if type(n) is not int or type(d) is not int or d <= 0 or not 0 <= n <= d:
            raise ValueError("valid subset counts with positive denominator required")
        result[name] = (n, d)
    return result


def components(groups):
    groups = checked(groups)
    total = sum(d for n, d in groups.values())
    rates = {k: Fraction(n, d) for k, (n, d) in groups.items()}
    weights = {k: Fraction(d, total) for k, (n, d) in groups.items()}
    return rates, weights


def total_rate(groups):
    groups = checked(groups)
    return Fraction(sum(n for n, d in groups.values()), sum(d for n, d in groups.values()))


def standardized_rate(groups, weights):
    rates, _ = components(groups)
    if set(rates) != set(weights):
        raise ValueError("group mismatch")
    if any(type(w) is not Fraction or w < 0 for w in weights.values()) or sum(weights.values()) != 1:
        raise ValueError("nonnegative exact Fraction weights summing to one required")
    return sum(weights[k] * rates[k] for k in rates)


def decompose(before, after, order="rates_first"):
    old_rates, old_weights = components(before)
    new_rates, new_weights = components(after)
    if set(old_rates) != set(new_rates):
        raise ValueError("aligned complete groups required")
    if order == "rates_first":
        within = sum(old_weights[k] * (new_rates[k] - old_rates[k]) for k in old_rates)
        mix = sum((new_weights[k] - old_weights[k]) * new_rates[k] for k in old_rates)
    elif order == "mix_first":
        mix = sum((new_weights[k] - old_weights[k]) * old_rates[k] for k in old_rates)
        within = sum(new_weights[k] * (new_rates[k] - old_rates[k]) for k in old_rates)
    else:
        raise ValueError("unknown decomposition order")
    return {"before": total_rate(before), "after": total_rate(after),
            "change": total_rate(after) - total_rate(before), "within": within, "mix": mix,
            "order": order, "interpretation": "descriptive_not_causal"}


BEFORE = {"high": (81, 90), "low": (1, 10)}
AFTER = {"high": (19, 20), "low": (16, 80)}


class Checks(unittest.TestCase):
    def test_01_overall_declines(self):
        self.assertEqual(total_rate(BEFORE), Fraction(82, 100))
        self.assertEqual(total_rate(AFTER), Fraction(35, 100))

    def test_02_every_group_improves(self):
        old, _ = components(BEFORE)
        new, _ = components(AFTER)
        self.assertTrue(all(new[k] > old[k] for k in old))

    def test_03_standardized_with_old_mix(self):
        _, weights = components(BEFORE)
        self.assertEqual(standardized_rate(AFTER, weights), Fraction(875, 1000))

    def test_04_rate_first_exact_identity(self):
        r = decompose(BEFORE, AFTER)
        self.assertEqual(r["within"], Fraction(55, 1000))
        self.assertEqual(r["mix"], Fraction(-525, 1000))
        self.assertEqual(r["within"] + r["mix"], Fraction(-47, 100))

    def test_05_path_changes_components_not_total(self):
        a = decompose(BEFORE, AFTER)
        b = decompose(BEFORE, AFTER, "mix_first")
        self.assertEqual(b["within"], Fraction(9, 100))
        self.assertEqual(b["mix"], Fraction(-56, 100))
        self.assertNotEqual(a["within"], b["within"])
        self.assertEqual(a["change"], b["change"])

    def test_06_no_change(self):
        r = decompose(BEFORE, BEFORE)
        self.assertEqual((r["change"], r["within"], r["mix"]), (0, 0, 0))

    def test_07_only_mix_changes(self):
        r = decompose(BEFORE, {"high": (18, 20), "low": (8, 80)})
        self.assertEqual(r["within"], 0)
        self.assertEqual(r["change"], r["mix"])

    def test_08_only_rates_change(self):
        r = decompose(BEFORE, {"high": (85, 90), "low": (2, 10)})
        self.assertEqual(r["mix"], 0)
        self.assertEqual(r["change"], r["within"])

    def test_09_new_group_requires_explicit_alignment(self):
        with self.assertRaises(ValueError):
            decompose(BEFORE, dict(AFTER, new=(1, 5)))

    def test_10_zero_denominator_not_imputed(self):
        with self.assertRaises(ValueError):
            decompose(BEFORE, {"high": (0, 0), "low": (16, 80)})

    def test_11_bad_counts_rejected(self):
        for counts in ((True, 10), (1.0, 10), (-1, 10), (11, 10), (0, -1)):
            with self.assertRaises(ValueError):
                checked({"a": counts})

    def test_12_bad_standard_weights_rejected(self):
        for weights in ({"high": Fraction(1), "low": Fraction(1)},
                        {"high": Fraction(-1), "low": Fraction(2)},
                        {"high": Fraction(1)}, {"high": .9, "low": .1}):
            with self.assertRaises(ValueError):
                standardized_rate(BEFORE, weights)

    def test_13_generated_identity_cases(self):
        rng = random.Random(20261005)
        for _ in range(100):
            tables = []
            for period in range(2):
                groups = {}
                for name in ("a", "b", "c"):
                    d = rng.randint(1, 100)
                    groups[name] = (rng.randint(0, d), d)
                tables.append(groups)
            for order in ("rates_first", "mix_first"):
                r = decompose(*tables, order=order)
                self.assertEqual(r["within"] + r["mix"], r["change"])

    def test_14_output_does_not_claim_causality(self):
        self.assertEqual(decompose(BEFORE, AFTER)["interpretation"], "descriptive_not_causal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
