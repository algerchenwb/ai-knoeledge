"""Small-data mechanism checks; optionally export a dendrogram figure."""
import argparse
import json
import numpy as np
import scipy
import sklearn
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances


def partition(labels):
    return sorted(sorted(np.flatnonzero(labels == k).tolist()) for k in set(labels))


def linkage_matrix(model, n):
    counts = np.zeros(n - 1)
    for i, children in enumerate(model.children_):
        counts[i] = sum(1 if child < n else counts[child - n] for child in children)
    return np.c_[model.children_, model.distances_, counts]


def run(output=None):
    x = np.array([[0.], [1.], [4.], [10.]])
    expected = {"single": [1., 3., 6.], "complete": [1., 4., 10.],
                "average": [1., 3.5, 25 / 3],
                "ward": [1., np.sqrt(49 / 3), np.sqrt(625 / 6)]}
    models = {}
    for kind, heights in expected.items():
        m = AgglomerativeClustering(n_clusters=None, distance_threshold=5,
                                    linkage=kind, compute_full_tree=True).fit(x)
        np.testing.assert_allclose(m.distances_, heights)
        assert partition(m.labels_) == [[0, 1, 2], [3]]
        assert m.children_.shape == (3, 2)
        assert not hasattr(m, "predict")
        models[kind] = m
    for kind in ["single", "complete", "average"]:
        m = AgglomerativeClustering(n_clusters=2, linkage=kind,
                                    metric="precomputed").fit(pairwise_distances(x))
        assert partition(m.labels_) == partition(models[kind].labels_)
    # sklearn refuses a merge at exactly the threshold.
    boundary = {}
    for threshold in [1., np.nextafter(1., np.inf)]:
        m = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold,
                                    linkage="single").fit(x)
        boundary[str(threshold)] = int(m.n_clusters_)
    assert list(boundary.values()) == [4, 3]
    chain = np.arange(5, dtype=float).reshape(-1, 1)
    chain_counts = {}
    for kind in ["single", "complete"]:
        m = AgglomerativeClustering(n_clusters=None, distance_threshold=1.1,
                                    linkage=kind).fit(chain)
        chain_counts[kind] = int(m.n_clusters_)
    assert chain_counts == {"single": 1, "complete": 3}
    if output:
        import matplotlib.pyplot as plt
        plt.rcParams["svg.fonttype"] = "none"
        fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
        for ax, (kind, m) in zip(axes.ravel(), models.items()):
            dendrogram(linkage_matrix(m, len(x)), labels=["P0: 0", "P1: 1", "P2: 4", "P3: 10"],
                       color_threshold=5, ax=ax)
            ax.axhline(5, color="black", linestyle="--", linewidth=1, label="cut threshold = 5")
            ax.set(title=kind.capitalize(), ylabel="Linkage height", ylim=(0, 11))
            ax.legend(loc="upper left", fontsize=8)
        fig.suptitle("Same four observations, different merge criteria")
        fig.savefig(output)
        plt.close(fig)
    return {"versions": {"numpy": np.__version__, "scipy": scipy.__version__,
                         "sklearn": sklearn.__version__},
            "heights": {k: m.distances_.tolist() for k, m in models.items()},
            "threshold_5_partition": partition(models["ward"].labels_),
            "threshold_boundary_cluster_counts": boundary,
            "chain_cluster_counts": chain_counts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Optional figure path, e.g. linkage-dendrograms.svg")
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))
