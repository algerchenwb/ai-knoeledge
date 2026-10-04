"""Nonnegative factorization, scale ambiguity and negative-input rejection."""
import numpy as np
from sklearn.decomposition import NMF

w0 = np.array([[1., 0], [2., 0], [0, 1.], [0, 2.], [1., 1.]])
h0 = np.array([[2., 1., 0, 0], [0, 0, 1., 2.]])
x = w0 @ h0
m = NMF(n_components=2, init="nndsvda", random_state=0, tol=1e-8, max_iter=2000)
w = m.fit_transform(x)
h = m.components_
assert np.all(w >= 0) and np.all(h >= 0)
assert np.linalg.norm(x - w @ h) / np.linalg.norm(x) < 1e-5
s = np.array([2., 0.5])
np.testing.assert_allclose((w * s) @ (h / s[:, None]), w @ h)
try:
    NMF(n_components=1).fit(np.array([[1., -1.], [2., 1.]]))
except ValueError:
    pass
else:
    raise AssertionError("NMF accepted negative input")
print("PASS nonnegative factors, reconstruction, scale ambiguity, input rejection")
