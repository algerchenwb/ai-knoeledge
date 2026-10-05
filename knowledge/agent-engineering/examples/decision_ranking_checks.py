"""Original exact weighted utility demo; not pymcdm or a learned revenue model."""
from dataclasses import dataclass, replace
from fractions import Fraction
import unittest


@dataclass(frozen=True)
class Candidate:
    key: str
    traffic: int | None
    rent: int | None
    traffic_unit: str = "persons_per_day"
    rent_unit: str = "thousand_per_month"
    allowed: bool = True


@dataclass(frozen=True)
class Policy:
    traffic_weight: Fraction = Fraction(3, 5)
    rent_weight: Fraction = Fraction(2, 5)
    rent_cap: int = 90
    version: str = "utility-v1"

    def validate(self):
        weights = (self.traffic_weight, self.rent_weight)
        if any(type(w) is not Fraction or w < 0 for w in weights) or sum(weights) != 1:
            raise ValueError("exact nonnegative weights summing to one required")
        if type(self.rent_cap) is not int or not 0 <= self.rent_cap <= 100:
            raise ValueError("rent cap outside teaching range")


def evaluate(candidate, policy):
    policy.validate()
    if type(candidate.allowed) is not bool:
        raise ValueError("boolean permission flag required")
    if not candidate.allowed:
        return {"status": "excluded", "reason": "outside_allowed_scope", "score": None}
    if candidate.traffic_unit != "persons_per_day" or candidate.rent_unit != "thousand_per_month":
        raise ValueError("unit mismatch")
    if candidate.traffic is None or candidate.rent is None:
        return {"status": "needs_data", "reason": "missing_criterion", "score": None}
    if type(candidate.traffic) is not int or type(candidate.rent) is not int:
        raise ValueError("strict integer criteria required")
    if not 0 <= candidate.traffic <= 1000 or not 0 <= candidate.rent <= 100:
        raise ValueError("outside fixed utility anchors")
    if candidate.rent > policy.rent_cap:
        return {"status": "excluded", "reason": "over_rent_cap", "score": None}
    traffic_utility = Fraction(candidate.traffic, 1000)
    rent_utility = 1 - Fraction(candidate.rent, 100)
    parts = (policy.traffic_weight * traffic_utility, policy.rent_weight * rent_utility)
    return {"status": "scored", "score": sum(parts), "parts": parts,
            "utilities": (traffic_utility, rent_utility), "policy_version": policy.version}


def rank(candidates, policy):
    keys = [c.key for c in candidates]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate candidate key")
    results = {c.key: evaluate(c, policy) for c in candidates}
    scored = [(k, r["score"]) for k, r in results.items() if r["status"] == "scored"]
    ordered = sorted(scored, key=lambda item: (-item[1], item[0]))
    winners = tuple(k for k, score in ordered if score == ordered[0][1]) if ordered else ()
    return {"results": results, "ordered": ordered, "winners": winners}


def dominates(left, right):
    # Only for complete, comparable criteria with these fixed directions.
    return (left.traffic >= right.traffic and left.rent <= right.rent
            and (left.traffic > right.traffic or left.rent < right.rent))


def candidate_minmax_scores(candidates, weight):
    # Deliberate counterexample: anchors depend on the current candidate set.
    traffic = [c.traffic for c in candidates]
    rents = [c.rent for c in candidates]
    if max(traffic) == min(traffic) or max(rents) == min(rents):
        raise ValueError("constant criterion in counterexample")
    return {c.key: weight * Fraction(c.traffic - min(traffic), max(traffic) - min(traffic))
            + (1 - weight) * Fraction(max(rents) - c.rent, max(rents) - min(rents))
            for c in candidates}


A = Candidate("A", 800, 80)
B = Candidate("B", 600, 40)


class Checks(unittest.TestCase):
    def test_01_default_exact_scores(self):
        self.assertEqual(evaluate(A, Policy())["score"], Fraction(56, 100))
        self.assertEqual(evaluate(B, Policy())["score"], Fraction(60, 100))

    def test_02_contribution_sum(self):
        r = evaluate(B, Policy())
        self.assertEqual(r["parts"], (Fraction(36, 100), Fraction(24, 100)))
        self.assertEqual(sum(r["parts"]), r["score"])

    def test_03_hard_cap_before_scoring(self):
        c = Candidate("C", 1000, 100)
        r = rank([A, B, c], Policy())
        self.assertEqual(r["results"]["C"]["reason"], "over_rent_cap")
        self.assertIsNone(r["results"]["C"]["score"])

    def test_04_missing_is_not_zero(self):
        r = evaluate(Candidate("D", 900, None), Policy())
        self.assertEqual(r["status"], "needs_data")
        self.assertIsNone(r["score"])

    def test_05_scope_exclusion(self):
        self.assertEqual(evaluate(replace(A, allowed=False), Policy())["reason"], "outside_allowed_scope")

    def test_06_unit_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(replace(A, rent_unit="yuan_per_year"), Policy())

    def test_07_strict_values_and_anchors(self):
        for candidate in (replace(A, traffic=True), replace(A, rent=80.0),
                          replace(A, traffic=-1), replace(A, traffic=1001)):
            with self.assertRaises(ValueError):
                evaluate(candidate, Policy())

    def test_08_weight_validation(self):
        for weights in ((Fraction(1), Fraction(1)), (Fraction(-1), Fraction(2)), (.6, .4)):
            with self.assertRaises(ValueError):
                evaluate(A, Policy(*weights))

    def test_09_preference_change_changes_winner(self):
        self.assertEqual(rank([A, B], Policy())["winners"], ("B",))
        self.assertEqual(rank([A, B], Policy(Fraction(4, 5), Fraction(1, 5)))["winners"], ("A",))

    def test_10_exact_tie_preserved(self):
        self.assertEqual(rank([B, A], Policy(Fraction(2, 3), Fraction(1, 3)))["winners"], ("A", "B"))

    def test_11_fixed_anchor_scores_unchanged_by_extra_candidate(self):
        r = rank([A, B, Candidate("D", 0, 90)], Policy())
        self.assertEqual(r["results"]["A"]["score"], Fraction(56, 100))
        self.assertEqual(r["winners"], ("B",))

    def test_12_candidate_minmax_rank_reversal(self):
        old = candidate_minmax_scores([A, B], Fraction(3, 5))
        new = candidate_minmax_scores([A, B, Candidate("D", 0, 90)], Fraction(3, 5))
        self.assertGreater(old["A"], old["B"])
        self.assertGreater(new["B"], new["A"])
        self.assertTrue(dominates(B, Candidate("D", 0, 90)))

    def test_13_dominance_and_tradeoff(self):
        self.assertTrue(dominates(B, Candidate("D", 500, 50)))
        self.assertFalse(dominates(A, B))
        self.assertFalse(dominates(B, A))

    def test_14_weight_grid_is_scenario_count(self):
        winners = [rank([A, B], Policy(Fraction(i, 10), Fraction(10-i, 10)))["winners"] for i in range(11)]
        self.assertEqual(winners.count(("B",)), 7)
        self.assertEqual(winners.count(("A",)), 4)

    def test_15_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            rank([A, A], Policy())

    def test_16_no_eligible_winner(self):
        r = rank([replace(A, allowed=False), Candidate("D", None, 40)], Policy())
        self.assertEqual(r["winners"], ())


if __name__ == "__main__":
    unittest.main(verbosity=2)
