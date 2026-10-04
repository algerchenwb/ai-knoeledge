"""Independent educational checks; no downloaded dataset is needed."""
import json
import platform
import numpy as np
import sklearn
from scipy.special import logsumexp
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import train_test_split


def one_em_step():
    x = np.array([-2., -1., 1., 2.])
    mu = np.array([-1., 1.])
    variance = np.ones(2)
    weight = np.full(2, .5)

    def estep(mu, variance, weight):
        joint = (np.log(weight) - .5 * np.log(2 * np.pi * variance)
                 - .5 * (x[:, None] - mu)**2 / variance)
        logp = logsumexp(joint, axis=1)
        return np.exp(joint - logp[:, None]), logp.sum()

    resp, old_ll = estep(mu, variance, weight)
    np.testing.assert_allclose(resp.sum(axis=1), 1)
    np.testing.assert_allclose(resp[:, 0], 1 / (1 + np.exp(2 * x)))
    nk = resp.sum(axis=0)
    mu = (resp.T @ x) / nk
    variance = (resp * (x[:, None] - mu)**2).sum(axis=0) / nk
    weight = nk / len(x)
    _, new_ll = estep(mu, variance, weight)
    assert new_ll >= old_ll
    return {"responsibility_left": resp[:, 0].tolist(), "means": mu.tolist(),
            "variance": variance.tolist(), "ll_before": old_ll, "ll_after": new_ll}


def library_checks():
    rng = np.random.default_rng(42)
    x = np.r_[rng.normal(-3, .55, (300, 1)), rng.normal(3, .8, (300, 1))]
    train, test = train_test_split(x, test_size=.25, random_state=42)
    models = [GaussianMixture(n_components=k, n_init=5, reg_covar=1e-6,
                              max_iter=300, random_state=42).fit(train)
              for k in range(1, 5)]
    rows = []
    for k, model in enumerate(models, 1):
        assert model.converged_
        # In 1D all covariance choices have k variances, k means, k-1 weights
        # except tied, which has a single shared variance.
        p = 3 * k - 1
        ll = model.score_samples(train).sum()
        np.testing.assert_allclose(model.bic(train), -2 * ll + p * np.log(len(train)))
        np.testing.assert_allclose(model.aic(train), -2 * ll + 2 * p)
        rows.append({"k": k, "parameters": p, "bic": model.bic(train),
                     "train_mean_log_density": model.score(train)})
    chosen = models[int(np.argmin([r["bic"] for r in rows]))]
    assert chosen.n_components == 2  # Only an expectation for this synthetic example.
    probe = np.array([[-3.], [0.], [3.]])
    resp = chosen.predict_proba(probe)
    np.testing.assert_allclose(resp.sum(axis=1), 1)
    np.testing.assert_array_equal(chosen.predict(probe), resp.argmax(axis=1))
    # Reconstruct probability density without sklearn private APIs.
    log_joint = (np.log(chosen.weights_) - .5 * np.log(2 * np.pi * chosen.covariances_[:, 0, 0])
                 - .5 * (probe - chosen.means_.T)**2 / chosen.covariances_[:, 0, 0])
    np.testing.assert_allclose(chosen.score_samples(probe), logsumexp(log_joint, axis=1))
    # Pure permutation of components changes IDs, not the density.
    np.testing.assert_allclose(logsumexp(log_joint[:, ::-1], axis=1), chosen.score_samples(probe))
    # API shapes on a separate two-dimensional dataset.
    x2 = np.c_[x[:, 0], .6 * x[:, 0] + rng.normal(0, .5, len(x))]
    shapes = {"full": (2, 2, 2), "tied": (2, 2), "diag": (2, 2), "spherical": (2,)}
    for kind, shape in shapes.items():
        m = GaussianMixture(n_components=2, covariance_type=kind, n_init=3,
                            random_state=42).fit(x2)
        assert m.converged_ and m.covariances_.shape == shape
        assert np.isfinite(m.score_samples(x2)).all()
    return {"train_n": len(train), "test_n": len(test), "selection": rows,
            "chosen_k": chosen.n_components, "test_mean_log_density": chosen.score(test),
            "means_in_component_order": chosen.means_.ravel().tolist(),
            "probe_responsibilities": resp.tolist(), "covariance_shapes": shapes}


if __name__ == "__main__":
    print(json.dumps({"environment": {"python": platform.python_version(),
                       "numpy": np.__version__, "sklearn": sklearn.__version__},
                       "hand_em": one_em_step(), "library": library_checks()}, indent=2))
