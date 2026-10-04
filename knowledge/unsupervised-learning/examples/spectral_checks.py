"""Graph Laplacian arithmetic and actual sklearn spectral clustering checks."""
import json
import warnings
import numpy as np
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.datasets import make_circles
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import adjusted_rand_score


def graph_checks():
    w = np.zeros((6, 6))
    for group in [range(3), range(3, 6)]:
        for i in group:
            for j in group:
                if i != j:
                    w[i, j] = 1
    degree = w.sum(axis=1)
    laplacian = np.diag(degree) - w
    eigenvalues = np.linalg.eigvalsh(laplacian)
    assert np.sum(np.isclose(eigenvalues, 0, atol=1e-10)) == 2
    z = np.array([1., 2, 4, 8, 16, 32])
    edge_energy = 0.5 * np.sum(w * (z[:, None] - z[None, :]) ** 2)
    np.testing.assert_allclose(z @ laplacian @ z, edge_energy)
    # Small bridge makes the graph connected while retaining two strong groups.
    w[2, 3] = w[3, 2] = 0.01
    model = SpectralClustering(n_clusters=2, affinity="precomputed",
                               assign_labels="cluster_qr", random_state=0)
    labels = model.fit_predict(w)
    assert adjusted_rand_score([0, 0, 0, 1, 1, 1], labels) == 1
    assert adjusted_rand_score(labels, 1 - labels) == 1
    assert not hasattr(model, "predict")
    print("PASS Laplacian edge energy, two zero eigenvalues, graph partition, label swap, no predict")


def circles_experiment():
    x, reference = make_circles(n_samples=300, factor=0.45, noise=0.03, random_state=11)
    baseline = KMeans(n_clusters=2, n_init=10, random_state=0).fit_predict(x)
    spectral = SpectralClustering(n_clusters=2, affinity="rbf", gamma=30,
                                  assign_labels="cluster_qr", random_state=0).fit_predict(x)
    assert len(spectral) == len(x) and len(np.unique(spectral)) == 2
    print(json.dumps({"samples": len(x), "gamma": 30,
                      "kmeans_ari": float(adjusted_rand_score(reference, baseline)),
                      "spectral_ari": float(adjusted_rand_score(reference, spectral))}))


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        graph_checks()
        circles_experiment()
