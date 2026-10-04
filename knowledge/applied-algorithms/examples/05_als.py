"""Dense exact implicit ALS mathematics; does not execute implicit APIs."""
import numpy as np

r = np.array([[3., 0, 1, 0], [2., 1, 0, 0], [0, 0, 2., 4.]])
p = (r > 0).astype(float)
c = 1 + 2 * r
reg = 0.3

def loss(x, y):
    return np.sum(c * (p - x @ y.T) ** 2) + reg * (np.sum(x*x) + np.sum(y*y))

def run():
    rng = np.random.default_rng(17)
    x, y = rng.normal(size=(3, 2)), rng.normal(size=(4, 2))
    history = [loss(x, y)]
    for _ in range(12):
        for u in range(3):
            a = y.T @ (c[u, :, None] * y) + reg * np.eye(2)
            b = y.T @ (c[u] * p[u])
            x[u] = np.linalg.solve(a, b)
            np.testing.assert_allclose(a @ x[u], b, atol=1e-10)
        history.append(loss(x, y))
        for i in range(4):
            a = x.T @ (c[:, i, None] * x) + reg * np.eye(2)
            b = x.T @ (c[:, i] * p[:, i])
            y[i] = np.linalg.solve(a, b)
        history.append(loss(x, y))
    assert np.all(np.diff(history) <= 1e-9)
    return x @ y.T, history

scores, history = run()
np.testing.assert_allclose(scores, run()[0])
assert history[-1] < history[0]
print("PASS exact ALS objective descent, solve residuals and reproducibility")
