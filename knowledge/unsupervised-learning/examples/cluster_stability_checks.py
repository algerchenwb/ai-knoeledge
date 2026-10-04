"""Label-invariant agreement and repeated-subsample stability checks."""
import json
from itertools import combinations
from math import comb
import numpy as np
import sklearn
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score
from sklearn.metrics.cluster import contingency_matrix


def manual_ari(a, b):
    table = contingency_matrix(a, b)
    pair_sum = sum(comb(int(v), 2) for v in table.ravel())
    row_sum = sum(comb(int(v), 2) for v in table.sum(axis=1))
    col_sum = sum(comb(int(v), 2) for v in table.sum(axis=0))
    all_pairs = comb(len(a), 2)
    expected = row_sum * col_sum / all_pairs
    denominator = (row_sum + col_sum) / 2 - expected
    # Degenerate cases are tested through sklearn separately.
    assert denominator != 0
    return (pair_sum - expected) / denominator


def run():
    a = [0, 0, 0, 1, 1, 1]
    b = [0, 0, 1, 1, 1, 1]
    value = manual_ari(a, b)
    np.testing.assert_allclose(value, 12 / 37)
    np.testing.assert_allclose(value, adjusted_rand_score(a, b))
    assert adjusted_rand_score(a, [9, 9, 9, 7, 7, 7]) == 1
    np.testing.assert_allclose(adjusted_mutual_info_score(a, [9, 9, 9, 7, 7, 7]), 1)
    assert adjusted_rand_score([0, 0, 1, 1], [0, 1, 0, 1]) == -.5
    assert adjusted_rand_score([0] * 6, [8] * 6) == 1
    noise_a = np.array([0, 0, -1, -1, 1, 1])
    noise_b = np.array([0, 0, 2, 2, 1, 1])
    mask = (noise_a >= 0) & (noise_b >= 0)
    assert adjusted_rand_score(noise_a, noise_b) == 1
    assert mask.sum() == 4
    assert adjusted_rand_score(noise_a[mask], noise_b[mask]) == 1

    x, _ = make_blobs(n_samples=240, centers=[[-4, 0], [0, 4], [4, 0]],
                      cluster_std=1.5, random_state=42)
    rng = np.random.default_rng(2026)
    subsets = [np.sort(rng.choice(len(x), size=192, replace=False)) for _ in range(20)]
    summaries = []
    for k in [2, 3, 4]:
        fitted = [KMeans(n_clusters=k, n_init=10, random_state=seed).fit(x[ids])
                  for seed, ids in enumerate(subsets)]
        scores, overlap = [], []
        for i, j in combinations(range(len(subsets)), 2):
            common, left, right = np.intersect1d(subsets[i], subsets[j], return_indices=True)
            assert np.array_equal(subsets[i][left], subsets[j][right])
            overlap.append(len(common))
            scores.append(adjusted_rand_score(fitted[i].labels_[left], fitted[j].labels_[right]))
        assert len(scores) == 190 and np.isfinite(scores).all()
        summaries.append({"k": k, "pair_comparisons": len(scores),
                          "overlap_min": min(overlap), "overlap_max": max(overlap),
                          "ari_median": float(np.median(scores)),
                          "ari_q10": float(np.quantile(scores, .1)),
                          "ari_q90": float(np.quantile(scores, .9))})
    return {"sklearn": sklearn.__version__, "numpy": np.__version__,
            "manual_table": contingency_matrix(a, b).tolist(), "manual_ari": value,
            "noise_included_ari": adjusted_rand_score(noise_a, noise_b),
            "both_assigned_fraction": float(mask.mean()),
            "stability": summaries}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
