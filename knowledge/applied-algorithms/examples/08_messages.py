"""Message aggregation invariants and undirected GCN normalization, in NumPy."""
import numpy as np

def aggregate(x, edges):
    out = np.zeros_like(x)
    for source, target in edges:
        out[target] += x[source]
    return out

x = np.array([[1.], [2.], [4.]])
edges = [(0, 1), (2, 1)]
out = aggregate(x, edges)
np.testing.assert_array_equal(out, [[0.], [5.], [0.]])
np.testing.assert_array_equal(aggregate(x, edges[::-1]), out)
old_to_new = np.array([2, 0, 1])
renumbered_x = np.empty_like(x)
renumbered_x[old_to_new] = x
renumbered_edges = [(old_to_new[s], old_to_new[t]) for s, t in edges]
np.testing.assert_array_equal(aggregate(renumbered_x, renumbered_edges)[old_to_new], out)
a = np.array([[0., 1., 0], [1., 0, 1.], [0, 1., 0]]) + np.eye(3)
degree = a.sum(axis=1)
norm = a / np.sqrt(degree[:, None] * degree[None, :])
np.testing.assert_allclose(norm, norm.T)
np.testing.assert_allclose(norm[0, 0], 0.5)
np.testing.assert_allclose(norm[0, 1], 1 / np.sqrt(6))
assert np.all(np.isfinite(norm @ x))
print("PASS message arithmetic, edge order, node equivariance, GCN normalization")
