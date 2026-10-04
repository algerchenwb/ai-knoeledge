"""Real scikit-learn integration on synthetic data; does not use SHAP."""
import itertools
import json
import numpy as np
import sklearn
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.linear_model import LinearRegression


class InteractionRegressor(RegressorMixin, BaseEstimator):
    """Known fitted function, to isolate inspection semantics from training."""
    def fit(self, X, y=None):
        self.n_features_in_ = np.asarray(X).shape[1]
        return self

    def predict(self, X):
        X = np.asarray(X)
        return X[:, 0] * X[:, 1]


def main():
    X = np.array(list(itertools.product([-1., 0., 1.], repeat=3)))
    y = 2 * X[:, 0] + X[:, 1]
    model = LinearRegression().fit(X, y)
    assert np.allclose(model.coef_, [2, 1, 0], atol=1e-10)
    # Independent held-out points under the same deterministic generating rule.
    heldout = np.array(list(itertools.product([-.75, .25, .75], repeat=3)))
    heldout_y = 2 * heldout[:, 0] + heldout[:, 1]
    r = permutation_importance(model, heldout, heldout_y,
                               scoring="neg_mean_squared_error", n_repeats=30,
                               random_state=42)
    assert r.importances_mean[0] > r.importances_mean[1] > .1
    assert abs(r.importances_mean[2]) < 1e-20
    original = heldout.copy()
    p = partial_dependence(model, heldout, [0], method="brute",
                           grid_resolution=3, percentiles=(0, 1))
    grid = p["grid_values"][0]
    assert np.allclose(p["average"][0], 2 * grid + heldout[:, 1].mean())
    assert np.array_equal(heldout, original)
    # Each background row's ICE is known analytically, while PDP cancels.
    background = np.array([[0., -1.], [1., -1.], [0., 1.], [1., 1.]])
    interaction = InteractionRegressor().fit(background)
    curves = partial_dependence(interaction, background, [0], method="brute",
                                kind="both", percentiles=(0, 1))
    assert np.allclose(curves["average"], 0)
    assert np.allclose(curves["individual"][0, 0], [0, -1])
    assert np.allclose(curves["individual"][0, 2], [0, 1])
    assert np.allclose(curves["individual"].mean(axis=1), curves["average"])
    print(json.dumps({"sklearn_version": sklearn.__version__,
                      "numpy_version": np.__version__,
                      "permutation_mean": r.importances_mean.tolist(),
                      "permutation_std": r.importances_std.tolist(),
                      "pdp_grid": grid.tolist(),
                      "pdp_average": p["average"][0].tolist(),
                      "interaction_average": curves["average"].tolist(),
                      "checks": "PASS"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
