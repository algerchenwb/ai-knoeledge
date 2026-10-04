"""Deterministic Isomap mechanism checks; not a performance benchmark."""
import json
import platform
import warnings

import numpy as np
import scipy
import sklearn
from sklearn.manifold import Isomap
from sklearn.metrics import pairwise_distances


def main():
    # Only adjacent vertices are within 1.01: a connected seven-node path.
    x = np.array([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2], [2, 1], [2, 0]], dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model = Isomap(n_neighbors=None, radius=1.01, n_components=1, eigen_solver="dense")
        y = model.fit_transform(x)
        expected = np.abs(np.arange(7)[:, None] - np.arange(7)[None, :])
        np.testing.assert_allclose(model.dist_matrix_, expected, atol=1e-12)
        np.testing.assert_allclose(pairwise_distances(y), expected, atol=1e-7)
        # Independent double-centering and eigendecomposition oracle.
        h = np.eye(7) - np.ones((7, 7)) / 7
        b = -0.5 * h @ (expected**2) @ h
        values, vectors = np.linalg.eigh(b)
        oracle = vectors[:, -1:] * np.sqrt(values[-1])
        np.testing.assert_allclose(pairwise_distances(oracle), pairwise_distances(y), atol=1e-7)
        query = model.transform(np.array([[0, 0.5]]))
        assert query.shape == (1, 1) and np.isfinite(query).all()
        # Bigger radius changes the graph; endpoints can now connect directly.
        shortcut = Isomap(n_neighbors=None, radius=2.01, n_components=1, eigen_solver="dense").fit(x)
        np.testing.assert_allclose(shortcut.dist_matrix_[0, -1], 2.0)
    try:
        Isomap(n_neighbors=2, radius=1.01).fit(x)
    except ValueError:
        pass
    else:
        raise AssertionError("n_neighbors and radius must not both be supplied")
    print(json.dumps({
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
        "euclidean_endpoint_distance": float(np.linalg.norm(x[0] - x[-1])),
        "geodesic_endpoint_distance": float(model.dist_matrix_[0, -1]),
        "shortcut_endpoint_distance": float(shortcut.dist_matrix_[0, -1]),
        "max_embedding_distance_error": float(np.max(np.abs(pairwise_distances(y) - expected))),
        "largest_centered_kernel_eigenvalue": float(values[-1]),
        "query_shape": list(query.shape), "all_checks_passed": True,
    }, indent=2))


if __name__ == "__main__":
    main()
