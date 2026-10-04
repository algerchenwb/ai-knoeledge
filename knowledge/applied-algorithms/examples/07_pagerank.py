"""Independent PageRank with dangling redistribution and linear-solve oracle."""
import numpy as np

def pagerank(adj, alpha=0.85, tol=1e-12):
    n = len(adj)
    p = np.ones(n) / n
    transition = np.zeros_like(adj, dtype=float)
    for i, row in enumerate(adj):
        transition[i] = row / row.sum() if row.sum() else p
    r = p.copy()
    for _ in range(1000):
        nxt = alpha * transition.T @ r + (1 - alpha) * p
        assert np.isclose(nxt.sum(), 1) and np.all(nxt >= 0)
        if np.linalg.norm(nxt - r, 1) < tol:
            r = nxt
            break
        r = nxt
    else:
        raise RuntimeError("No convergence")
    exact = np.linalg.solve(np.eye(n) - alpha * transition.T, (1 - alpha) * p)
    np.testing.assert_allclose(r, exact, atol=1e-10)
    assert np.linalg.norm(r - alpha * transition.T @ r - (1 - alpha) * p, 1) < 1e-11
    return r

rank = pagerank(np.array([[0., 1.], [0, 0]]))
np.testing.assert_allclose(rank, [0.3508771929824561, 0.6491228070175439])
np.testing.assert_allclose(pagerank(np.zeros((3, 3))), np.ones(3) / 3)
pagerank(np.array([[0., 1., 0], [1., 0, 0], [0, 0, 0]]))
print("PASS PageRank mass, dangling nodes, fixed-point residual and independent solve")
