"""Independent small-sample teaching checks; optional installed SciPy cross-checks."""
from fractions import Fraction as F
from itertools import combinations, product
from math import comb
import hashlib
import json
import unittest


def exact_binomial(k, n, p=F(1, 2)):
    if type(k) is not int or type(n) is not int or not 0 <= k <= n or not 1 <= n <= 100:
        raise ValueError('integer counts, 1 <= n <= 100 required')
    if not isinstance(p, F) or not 0 < p < 1:
        raise ValueError('rational probability strictly inside (0,1) required')
    masses = [comb(n, i) * p**i * (1-p)**(n-i) for i in range(n+1)]
    return sum((x for x in masses if x <= masses[k]), F(0))


def exact_permutation(a, b, alternative='two-sided'):
    if alternative not in ('greater', 'less', 'two-sided'):
        raise ValueError('invalid alternative')
    if len(a) < 2 or len(b) < 2 or len(a) + len(b) > 12:
        raise ValueError('small groups of at least two units required')
    if any(type(v) is not int for v in a+b):
        raise ValueError('integer unit outcomes required')
    pool = a+b
    observed = F(sum(b), len(b)) - F(sum(a), len(a))
    null = []
    for indices in combinations(range(len(pool)), len(b)):
        chosen = set(indices)
        null.append(F(sum(pool[i] for i in chosen), len(b))
                    - F(sum(pool[i] for i in range(len(pool)) if i not in chosen), len(a)))
    less = F(sum(v <= observed for v in null), len(null))
    greater = F(sum(v >= observed for v in null), len(null))
    p = {'less': less, 'greater': greater,
         'two-sided': min(F(1), 2*min(less, greater))}[alternative]
    return observed, p, len(null)


def assignment(tenant, experiment, unit):
    # Trusted synthetic identifiers; JSON encoding avoids concatenation collisions.
    if any(type(x) is not str or not x for x in (tenant, experiment, unit)):
        raise ValueError('nonempty trusted identifiers required')
    payload = json.dumps([tenant, experiment, unit], ensure_ascii=False,
                         separators=(',', ':')).encode()
    bucket = int.from_bytes(hashlib.sha256(payload).digest(), 'big')
    return 'B' if bucket < 2**255 else 'A'


def summarize(rows, maturity=7):
    if type(maturity) is not int or maturity < 1:
        raise ValueError('invalid maturity')
    seen = set(); group = {'A': [], 'B': []}; unknown = False
    for unit, arm, outcome, age in rows:
        if type(unit) is not str or not unit or unit in seen:
            raise ValueError('one row per unique randomization unit required')
        if arm not in group or type(age) is not int or age < 0:
            raise ValueError('invalid assignment or age')
        if outcome is not None and (type(outcome) is not int or outcome not in (0, 1)):
            raise ValueError('binary outcome or unknown required')
        seen.add(unit)
        if age < maturity:
            return {'status': 'immature'}
        group[arm].append(outcome)
        unknown |= outcome is None
    counts = {arm: len(xs) for arm, xs in group.items()}
    if unknown or min(counts.values()) == 0:
        return {'status': 'insufficient', 'counts': counts}
    rates = {arm: F(sum(xs), len(xs)) for arm, xs in group.items()}
    return {'status': 'ready', 'counts': counts, 'rates': rates,
            'lift': rates['B'] - rates['A']}


def repeated_look_probability():
    hits = final_hits = 0
    for bits in product((0, 1), repeat=12):
        hits += any(exact_binomial(sum(bits[:n]), n) < F(1, 20) for n in (4, 8, 12))
        final_hits += exact_binomial(sum(bits), 12) < F(1, 20)
    return F(hits, 2**12), F(final_hits, 2**12)


class Checks(unittest.TestCase):
    def test_binomial_balanced(self):
        self.assertEqual(exact_binomial(5, 10), 1)

    def test_binomial_extreme(self):
        self.assertEqual(exact_binomial(0, 10), F(1, 512))

    def test_binomial_symmetry(self):
        for n in range(1, 13):
            for k in range(n+1):
                self.assertEqual(exact_binomial(k, n), exact_binomial(n-k, n))

    def test_srm_gate(self):
        self.assertLess(exact_binomial(20, 100), F(1, 1000))
        self.assertEqual(exact_binomial(50, 100), 1)

    def test_invalid_binomial(self):
        for args in ((True, 10), (11, 10), (0, 0), (0, 101), (2, 4, 0.5)):
            with self.assertRaises(ValueError): exact_binomial(*args)

    def test_permutation_hand_count(self):
        d, p, total = exact_permutation([0, 0, 0], [1, 1, 1], 'greater')
        self.assertEqual((d, p, total), (F(1), F(1, 20), 20))

    def test_permutation_two_sided(self):
        self.assertEqual(exact_permutation([0, 0, 0], [1, 1, 1])[1], F(1, 10))

    def test_permutation_equal(self):
        self.assertEqual(exact_permutation([1, 1], [1, 1])[1], 1)

    def test_permutation_swap(self):
        a, b = [0, 1, 0], [1, 1, 0]
        self.assertEqual(exact_permutation(a, b, 'greater')[1],
                         exact_permutation(b, a, 'less')[1])

    def test_invalid_permutation(self):
        for args in (([0], [1, 2]), ([True, 1], [0, 1]), ([0, 1], [1, 2], 'auto')):
            with self.assertRaises(ValueError): exact_permutation(*args)

    def test_assignment_stable(self):
        self.assertEqual(assignment('t', 'e-v1', 'u'), assignment('t', 'e-v1', 'u'))
        self.assertIn(assignment('t', 'e-v1', 'u'), ('A', 'B'))
        with self.assertRaises(ValueError): assignment('t', '', 'u')

    def test_missing_keeps_denominator(self):
        result = summarize([('u1', 'A', 0, 7), ('u2', 'B', None, 7)])
        self.assertEqual(result, {'status': 'insufficient', 'counts': {'A': 1, 'B': 1}})

    def test_maturity_gate(self):
        self.assertEqual(summarize([('u1', 'A', 1, 7), ('u2', 'B', 1, 6)])['status'], 'immature')

    def test_duplicate_unit(self):
        with self.assertRaises(ValueError):
            summarize([('u1', 'A', 0, 7), ('u1', 'B', 1, 7)])

    def test_absolute_lift(self):
        r = summarize([('u1', 'A', 1, 7), ('u2', 'A', 0, 7),
                       ('u3', 'B', 1, 7), ('u4', 'B', 1, 7)])
        self.assertEqual(r['lift'], F(1, 2))

    def test_multiple_metrics(self):
        false_positive = 1 - F(19, 20)**20
        self.assertGreater(false_positive, F(3, 5))
        # Bonferroni threshold, applicable without independence if individual tests valid.
        self.assertEqual(F(1, 20)/20, F(1, 400))

    def test_repeated_looks(self):
        early, final = repeated_look_probability()
        self.assertGreater(early, final)
        self.assertLessEqual(final, F(1, 20))

    def test_installed_scipy_crosscheck(self):
        try:
            from scipy.stats import binomtest, permutation_test
        except ImportError:
            self.skipTest('optional scipy not installed')
        for p in (F(1, 2), F(3, 10)):
            for n in range(1, 13):
                for k in range(n+1):
                    self.assertAlmostEqual(float(exact_binomial(k, n, p)),
                                           binomtest(k, n, float(p)).pvalue, places=12)
        for a, b in (([0, 0, 0], [1, 1, 1]), ([0, 1, 0], [1, 1, 0]), ([1, 1], [1, 1])):
            for alt in ('greater', 'less', 'two-sided'):
                result = permutation_test((a, b), lambda x, y: y.mean()-x.mean(),
                                          vectorized=False, n_resamples=float('inf'), alternative=alt)
                self.assertAlmostEqual(float(exact_permutation(a, b, alt)[1]), result.pvalue, places=12)

if __name__ == '__main__':
    unittest.main(verbosity=2)
