"""Actual sklearn checks for self-training semantics and a held-out comparison."""
import json
import platform
import numpy as np
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.semi_supervised import SelfTrainingClassifier


def boundary_checks():
    x = np.arange(6., dtype=float).reshape(-1, 1)
    y = np.array([0, 1, -1, -1, -1, -1])
    no_change = SelfTrainingClassifier(
        estimator=DummyClassifier(strategy="uniform"), threshold=0.5)
    no_change.fit(x, y)
    assert no_change.termination_condition_ == "no_change"
    np.testing.assert_array_equal(no_change.transduction_, y)
    np.testing.assert_array_equal(no_change.labeled_iter_, [0, 0, -1, -1, -1, -1])

    all_labeled = SelfTrainingClassifier(
        estimator=DummyClassifier(strategy="uniform"), threshold=0.49)
    all_labeled.fit(x, y)
    assert all_labeled.termination_condition_ == "all_labeled"
    np.testing.assert_array_equal(all_labeled.labeled_iter_, [0, 0, 1, 1, 1, 1])
    np.testing.assert_array_equal(all_labeled.transduction_[:2], y[:2])

    quota = SelfTrainingClassifier(estimator=DummyClassifier(strategy="uniform"),
                                   criterion="k_best", k_best=1, max_iter=1)
    quota.fit(x, y)
    assert quota.termination_condition_ == "max_iter"
    assert np.sum(quota.labeled_iter_ == 1) == 1
    assert np.sum(quota.transduction_ == -1) == 3
    np.testing.assert_array_equal(quota.transduction_[:2], y[:2])
    print("PASS strict threshold, no_change, all_labeled, k_best quota, label preservation")


def held_out_experiment():
    x, y = make_classification(n_samples=600, n_features=8, n_informative=5,
                               n_redundant=1, class_sep=1., flip_y=0.08,
                               random_state=31)
    train_x, test_x, train_y, test_y = train_test_split(
        x, y, test_size=200, stratify=y, random_state=19)
    rng = np.random.default_rng(11)
    # Stratified seed selection is a simulated annotation setup, not future labels.
    seeds = np.concatenate([rng.choice(np.flatnonzero(train_y == c), 20, replace=False)
                            for c in [0, 1]])
    labels = np.full(len(train_y), -1, dtype=int)
    labels[seeds] = train_y[seeds]
    mask = labels != -1
    base = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    baseline = base().fit(train_x[mask], labels[mask])
    trained = SelfTrainingClassifier(estimator=base(), threshold=0.9, max_iter=10)
    trained.fit(train_x, labels)
    np.testing.assert_array_equal(trained.transduction_[mask], labels[mask])
    assert np.all(trained.labeled_iter_[mask] == 0)
    accepted = (~mask) & (trained.labeled_iter_ > 0)
    unresolved = trained.labeled_iter_ == -1
    assert np.all(trained.transduction_[unresolved] == -1)
    result = {
        "training_pool": len(train_y), "true_seed_labels": int(mask.sum()),
        "held_out_test": len(test_y), "accepted_pseudo_labels": int(accepted.sum()),
        "unresolved": int(unresolved.sum()), "rounds": int(trained.n_iter_),
        "termination": trained.termination_condition_,
        "baseline_test_accuracy": float(accuracy_score(test_y, baseline.predict(test_x))),
        "self_training_test_accuracy": float(accuracy_score(test_y, trained.predict(test_x))),
        "pseudo_label_audit_accuracy": (float(accuracy_score(
            train_y[accepted], trained.transduction_[accepted])) if accepted.any() else None),
    }
    # Audit-only ground truth is never supplied to training or threshold selection.
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    print(json.dumps({"python": platform.python_version(), "numpy": np.__version__,
                      "scikit_learn": sklearn.__version__}))
    boundary_checks()
    held_out_experiment()
