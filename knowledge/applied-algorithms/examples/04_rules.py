"""Small independent Apriori exercise; not an mlxtend integration test."""
from itertools import combinations
from math import isclose

transactions = [set("ab"), set("ab"), set("a"), set("b")]

def support(items):
    return sum(items <= row for row in transactions) / len(transactions)

def apriori(min_support):
    universe = sorted(set().union(*transactions))
    level = {frozenset([t]) for t in universe if support({t}) >= min_support}
    found = set(level)
    k = 2
    while level:
        candidates = {a | b for a in level for b in level if len(a | b) == k}
        candidates = {c for c in candidates if all(
            frozenset(s) in level for s in combinations(sorted(c), k - 1))}
        level = {c for c in candidates if support(c) >= min_support}
        found |= level
        k += 1
    return found

for dataset in [[set("ab"), set("ab"), set("a"), set("b")],
                [set("abc"), set("ab"), set("ac"), set("bc"), set("abcd")]]:
    transactions = dataset
    universe = sorted(set().union(*transactions))
    for threshold in [0.2, 0.25, 0.5, 0.75, 1.0]:
        brute = {frozenset(c) for k in range(1, len(universe) + 1)
                 for c in combinations(universe, k) if support(set(c)) >= threshold}
        assert apriori(threshold) == brute
transactions = [set("ab"), set("ab"), set("a"), set("b")]
a, b = support({"a"}), support({"b"})
joint = support({"a", "b"})
confidence = joint / a
lift = confidence / b
assert isclose(joint, 0.5) and isclose(confidence, 2 / 3)
assert isclose(lift, 8 / 9) and lift < 1
print("PASS Apriori vs exhaustive sets and support/confidence/lift arithmetic")
