# -*- coding: utf-8 -*-
"""Learning/validation curves on synthetic regression data; not business metrics."""
import argparse
from pathlib import Path
import numpy as np
import sklearn
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, train_test_split, learning_curve, validation_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

def estimator(degree):
    return Pipeline([
        ("poly", PolynomialFeatures(degree=degree, include_bias=False)),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=1e-6))
    ])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Optional SVG output path")
    args = parser.parse_args()
    print("scikit-learn", sklearn.__version__, "numpy", np.__version__)
    rng = np.random.default_rng(42)
    X = rng.uniform(-1, 1, size=(300, 1))
    y = np.sin(np.pi * X[:, 0]) + rng.normal(0, 0.12, size=300)
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )
    cv = KFold(n_splits=3, shuffle=True, random_state=42)
    degrees = [1, 3, 9, 15]
    train, valid = validation_curve(
        estimator(1), X_dev, y_dev,
        param_name="poly__degree", param_range=degrees,
        scoring="neg_mean_squared_error", cv=cv, error_score="raise"
    )
    assert train.shape == valid.shape == (4, 3)
    train_mse, valid_mse = -train, -valid
    assert np.isfinite(train_mse).all() and np.isfinite(valid_mse).all()
    print("degree train_MSE validation_MSE fold_std")
    for degree, tr, va in zip(degrees, train_mse, valid_mse):
        print(degree, tr.mean(), va.mean(), va.std())

    curves = []
    for degree in [1, 9]:
        sizes, tr, va = learning_curve(
            estimator(degree), X_dev, y_dev,
            train_sizes=[15, 45, 100, 150], cv=cv,
            shuffle=True, random_state=42,
            scoring="neg_mean_squared_error", error_score="raise"
        )
        assert sizes.tolist() == [15, 45, 100, 150]
        assert tr.shape == va.shape == (4, 3)
        assert np.isfinite(tr).all() and np.isfinite(va).all()
        curves.append((degree, sizes, -tr, -va))
        print("learning degree", degree)
        for size, t, v in zip(sizes, -tr, -va):
            print(size, t.mean(), v.mean())
    # Select using development CV only, then evaluate the held-out test once.
    best_degree = degrees[int(np.argmin(valid_mse.mean(axis=1)))]
    final = estimator(best_degree).fit(X_dev, y_dev)
    print("selected degree", best_degree)
    print("final held-out MSE", mean_squared_error(y_test, final.predict(X_test)))
    if args.output:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["svg.fonttype"] = "none"
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
        axes[0].plot(degrees, train_mse.mean(axis=1), "o-", label="Train")
        axes[0].plot(degrees, valid_mse.mean(axis=1), "o-", label="Development CV")
        axes[0].set(xlabel="Polynomial degree", title="Validation curve", yscale="log")
        axes[0].set_xticks(degrees)
        for ax, (degree, sizes, tr, va) in zip(axes[1:], curves):
            ax.plot(sizes, tr.mean(axis=1), "o-", label="Train")
            ax.plot(sizes, va.mean(axis=1), "o-", label="Development CV")
            ax.set(xlabel="Training rows per fold",
                   title=f"Learning curve: degree {degree}", yscale="log")
        for ax in axes:
            ax.set_ylabel("Mean squared error (log scale)")
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
        fig.suptitle("Synthetic sine data; fixed splits, 3 folds; not business performance")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, format="svg")
        plt.close(fig)
        print("SVG saved", args.output)

if __name__ == "__main__":
    main()
