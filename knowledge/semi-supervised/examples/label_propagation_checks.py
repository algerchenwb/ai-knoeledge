"""Real sklearn hard/soft clamping and seedless-component diagnostics."""
import json
import warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.semi_supervised import LabelPropagation, LabelSpreading


def fixed_graph_checks():
    adjacency = np.zeros((6, 6))
    for i, j in [(0, 1), (1, 2), (2, 3), (4, 5)]:
        adjacency[i, j] = adjacency[j, i] = 1
    # Feature column contains node IDs; this callable is a tiny fixed graph oracle.
    def kernel(a, b):
        return adjacency[np.ix_(a[:, 0].astype(int), b[:, 0].astype(int))].copy()
    x = np.arange(6.).reshape(-1, 1)
    y = np.array([0, -1, -1, 1, -1, -1])
    original = y.copy()
    model = LabelPropagation(kernel=kernel, tol=1e-10, max_iter=2000).fit(x, y)
    np.testing.assert_array_equal(y, original)
    np.testing.assert_allclose(model.label_distributions_[1:3],
                               [[2/3, 1/3], [1/3, 2/3]], atol=1e-9)
    np.testing.assert_array_equal(model.label_distributions_[[0, 3]], [[1, 0], [0, 1]])
    np.testing.assert_array_equal(model.label_distributions_[4:], np.zeros((2, 2)))
    np.testing.assert_array_equal(model.transduction_[4:], [model.classes_[0]] * 2)
    print("PASS chain hand calculation, hard clamping, seedless zero evidence, argmax fallback")


def rbf_clamping_checks():
    x = np.array([[0.], [0.1], [0.05], [0.07]])
    y = np.array([0, 1, -1, -1])
    hard = LabelPropagation(kernel="rbf", gamma=1., tol=1e-10, max_iter=2000).fit(x, y)
    soft = LabelSpreading(kernel="rbf", gamma=1., alpha=0.8,
                          tol=1e-10, max_iter=2000).fit(x, y)
    np.testing.assert_array_equal(hard.label_distributions_[:2], np.eye(2))
    assert np.all(soft.label_distributions_[:2] > 0)
    assert np.all(soft.label_distributions_[:2] < 1)
    for model in [hard, soft]:
        assert np.all(np.isfinite(model.label_distributions_))
        np.testing.assert_allclose(model.label_distributions_.sum(axis=1), 1)
        probs = model.predict_proba([[0.03], [0.08]])
        assert probs.shape == (2, 2) and np.all(np.isfinite(probs))
        np.testing.assert_allclose(probs.sum(axis=1), 1)
    print("PASS real RBF hard vs soft clamping, normalized rows and new-input probabilities")
    print(json.dumps({"hard_seed_rows": hard.label_distributions_[:2].tolist(),
                      "soft_seed_rows": soft.label_distributions_[:2].tolist()}))


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        fixed_graph_checks()
        rbf_clamping_checks()
