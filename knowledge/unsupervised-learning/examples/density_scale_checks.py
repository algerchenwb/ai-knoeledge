"""OPTICS and sklearn HDBSCAN checks on an explicit one-dimensional dataset."""
import json
import numpy as np
import scipy
import sklearn
from sklearn.cluster import OPTICS, HDBSCAN, cluster_optics_dbscan
from sklearn.metrics import pairwise_distances


def groups(labels):
    return sorted(sorted(np.flatnonzero(labels == k).tolist())
                  for k in set(labels) if k >= 0)


def run():
    x = np.array([0., .1, .2, .3, 4., 4.4, 4.8, 5.2, 12.]).reshape(-1, 1)
    distance = pairwise_distances(x)
    core = np.sort(distance, axis=1)[:, 2]  # third neighbor includes self
    np.testing.assert_allclose(core, [.2, .1, .1, .2, .8, .4, .4, .8, 7.2])
    mutual = np.maximum(np.maximum(core[:, None], core[None, :]), distance)
    assert np.allclose(mutual, mutual.T)
    assert np.isclose(mutual[0, 1], .2)
    assert np.isclose(mutual[4, 5], .8)
    assert np.isclose(mutual[3, 4], 3.7)
    optics = OPTICS(min_samples=3, max_eps=8, cluster_method="xi", xi=.05,
                    min_cluster_size=3).fit(x)
    np.testing.assert_allclose(optics.core_distances_, core)
    np.testing.assert_array_equal(np.sort(optics.ordering_), np.arange(len(x)))
    # Reachability is stored by original sample index, not by plot order.
    for point, predecessor in enumerate(optics.predecessor_):
        if predecessor >= 0:
            np.testing.assert_allclose(optics.reachability_[point],
                max(core[predecessor], distance[predecessor, point]))
        else:
            assert np.isinf(optics.reachability_[point])
    extractions = {}
    for eps in [.25, 1.]:
        labels = cluster_optics_dbscan(reachability=optics.reachability_,
                                      core_distances=optics.core_distances_,
                                      ordering=optics.ordering_, eps=eps)
        expected = [[0, 1, 2, 3]] if eps == .25 else [[0, 1, 2, 3], [4, 5, 6, 7]]
        assert groups(labels) == expected
        extractions[str(eps)] = {"groups": groups(labels), "noise": int(np.sum(labels == -1))}
    hdbscan = HDBSCAN(min_cluster_size=3, min_samples=3, copy=True,
                      cluster_selection_method="eom").fit(x)
    assert groups(hdbscan.labels_) == [[0, 1, 2, 3], [4, 5, 6, 7]]
    assert hdbscan.labels_[-1] == -1
    assert hdbscan.probabilities_.shape == (len(x),)
    assert ((hdbscan.probabilities_ >= 0) & (hdbscan.probabilities_ <= 1)).all()
    assert hdbscan.probabilities_[-1] == 0
    assert not hasattr(hdbscan, "predict") and not hasattr(optics, "predict")
    # Document sklearn's invalid-row labels separately from ordinary noise.
    dirty = np.r_[x, [[np.inf]], [[np.nan]]]
    dirty_model = HDBSCAN(min_cluster_size=3, min_samples=3, copy=True).fit(dirty)
    np.testing.assert_array_equal(dirty_model.labels_[-2:], [-2, -3])
    assert dirty_model.probabilities_[-2] == 0
    assert np.isnan(dirty_model.probabilities_[-1])
    return {"versions": {"numpy": np.__version__, "scipy": scipy.__version__,
                         "sklearn": sklearn.__version__},
            "x": x.ravel().tolist(), "core_distances": core.tolist(),
            "optics_ordering": optics.ordering_.tolist(),
            "optics_reachability_in_order": [None if not np.isfinite(v) else float(v)
                                             for v in optics.reachability_[optics.ordering_]],
            "dbscan_extractions": extractions,
            "hdbscan_groups": groups(hdbscan.labels_),
            "hdbscan_strength": hdbscan.probabilities_.tolist(),
            "invalid_row_labels": dirty_model.labels_[-2:].tolist()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
