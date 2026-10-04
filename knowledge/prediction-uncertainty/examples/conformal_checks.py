"""Independent split-conformal arithmetic and simulation; not MAPIE library."""
import json
import math
import random
from statistics import mean


def conformal_radius(scores, alpha):
    if not 0 < alpha < 1 or not scores:
        raise ValueError("need nonempty scores and alpha in (0,1)")
    if any(not math.isfinite(s) or s < 0 for s in scores):
        raise ValueError("absolute scores must be finite and nonnegative")
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    return math.inf if rank > len(scores) else sorted(scores)[rank - 1]


def coverage(truth, lower, upper):
    if not truth or len(truth) != len(lower) or len(truth) != len(upper):
        raise ValueError("invalid interval batch")
    if any(a > b for a, b in zip(lower, upper)):
        raise ValueError("reversed interval")
    return mean(a <= y <= b for y, a, b in zip(truth, lower, upper))


def main():
    scores = list(range(1, 10))
    assert conformal_radius(scores, .2) == 8
    assert conformal_radius(scores, .1) == 9
    assert math.isinf(conformal_radius(scores, .05))
    assert conformal_radius(scores[::-1], .2) == 8
    assert conformal_radius([1] * 9, .2) == 1
    test = list(range(101, 111))
    assert coverage(test, [92] * 10, [108] * 10) == .8
    assert mean([108 - 92] * 10) == 16
    a, b = [0] * 90, [2] * 10
    assert coverage(a + b, [-1] * 100, [1] * 100) == .9
    assert coverage(a, [-1] * 90, [1] * 90) == 1
    assert coverage(b, [-1] * 10, [1] * 10) == 0
    rng = random.Random(20261004)
    same, shifted = [], []
    for _ in range(4000):
        q = conformal_radius([rng.random() for _ in range(49)], .1)
        fresh = rng.random()
        same.append(fresh <= q)
        shifted.append(fresh + 2 <= q)
    observed = mean(same)
    assert .87 < observed < .93
    assert mean(shifted) == 0
    # This tolerance is only a deterministic simulation check, not a theorem.
    print(json.dumps({"n9_alpha02_radius": 8, "toy_coverage": .8, "toy_width": 16,
                      "pooled_group_coverage": .9, "minority_group_coverage": 0,
                      "trials": 4000, "exchangeable_simulation_coverage": observed,
                      "shifted_simulation_coverage": mean(shifted),
                      "checks": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
