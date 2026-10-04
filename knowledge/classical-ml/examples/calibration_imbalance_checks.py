# -*- coding: utf-8 -*-
"""Teaching checks; synthetic outputs are not business performance claims."""
import sklearn
print("scikit-learn", sklearn.__version__)

import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

y = np.array([0, 1, 0, 1, 0, 1, 0, 1])
p = np.repeat([0.6, 0.9], 4)
assert np.isclose(roc_auc_score(y, p), 0.5)
assert np.isclose(brier_score_loss(y, p), 0.335)
constant = np.full(len(y), 0.5)
assert np.isclose(brier_score_loss(y, constant), 0.25)
print("Brier", brier_score_loss(y, p), brier_score_loss(y, constant))
print("log loss", log_loss(y, p), log_loss(y, constant))

p_sharp = 1 / (1 + np.exp(-3 * np.log(p / (1-p))))
assert np.isclose(roc_auc_score(y, p_sharp), roc_auc_score(y, p))
print("same AUC; changed Brier", brier_score_loss(y, p_sharp))
for value in [0.6, 0.9]:
    mask = p == value
    print("bin mean/count/positive rate",
          p[mask].mean(), mask.sum(), y[mask].mean())


import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.frozen import FrozenEstimator
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, log_loss

X, y = make_classification(
    n_samples=1200, n_features=8, n_informative=4,
    n_redundant=2, weights=[0.8, 0.2], random_state=42
)
X_rest, X_test, y_rest, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
X_train, X_cal, y_train, y_cal = train_test_split(
    X_rest, y_rest, test_size=1/3, stratify=y_rest, random_state=43
)
base = make_pipeline(StandardScaler(), LinearSVC(random_state=42))
base.fit(X_train, y_train)
calibrated = CalibratedClassifierCV(
    FrozenEstimator(base), method="sigmoid"
)
calibrated.fit(X_cal, y_cal)
positive_column = np.flatnonzero(calibrated.classes_ == 1)[0]
p_test = calibrated.predict_proba(X_test)[:, positive_column]
assert np.all((p_test >= 0) & (p_test <= 1))
print("calibrated Brier/log loss",
      brier_score_loss(y_test, p_test),
      log_loss(y_test, np.column_stack([1-p_test, p_test])))
fraction, mean = calibration_curve(
    y_test, p_test, n_bins=5, strategy="quantile"
)
print("bin mean", mean, "bin positive fraction", fraction)


import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score
from sklearn.utils.class_weight import compute_class_weight

y = np.r_[np.ones(100, dtype=int), np.zeros(9900, dtype=int)]
pred = np.zeros_like(y)
pred[:80] = 1
pred[100:595] = 1
assert np.isclose(precision_score(y, pred), 80/575)
all_negative = np.zeros_like(y)
assert np.isclose(accuracy_score(y, all_negative), 0.99)
assert np.isclose(balanced_accuracy_score(y, all_negative), 0.5)
weights = compute_class_weight("balanced", classes=np.array([0, 1]), y=y)
assert np.allclose(weights, [10000/(2*9900), 50])
print("precision", precision_score(y, pred), "class weights", weights)


from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score

X, y = make_classification(
    n_samples=1600, n_features=10, n_informative=5,
    n_redundant=2, weights=[0.95, 0.05], flip_y=0.01, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    {"logisticregression__class_weight": [None, "balanced"],
     "logisticregression__C": [0.1, 1.]},
    scoring="average_precision",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
p = search.predict_proba(X_test)[:, 1]  # 此例 classes_ 为 [0,1]
pred = p >= 0.5
print("imbalance chosen", search.best_params_)
print("CV AP", search.best_score_, "test AP", average_precision_score(y_test, p))
print("test Precision/Recall",
      precision_score(y_test, pred, zero_division=0),
      recall_score(y_test, pred))


import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

X_demo, y_demo = make_classification(
    n_samples=400, n_features=6, n_informative=3,
    n_redundant=1, weights=[0.9, 0.1], random_state=7
)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=7)
scores = []
for fold, (train, valid) in enumerate(cv.split(X_demo, y_demo)):
    rng = np.random.default_rng(7 + fold)
    groups = [train[y_demo[train] == c] for c in [0, 1]]
    target = max(len(g) for g in groups)
    # 保留原记录，再补齐较少的那一类。
    sampled = np.concatenate([
        np.r_[g, rng.choice(g, size=target-len(g), replace=True)]
        for g in groups
    ])
    assert not np.intersect1d(sampled, valid).size
    assert np.bincount(y_demo[sampled]).tolist() == [target, target]
    model = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=1000))
    model.fit(X_demo[sampled], y_demo[sampled])
    p_valid = model.predict_proba(X_demo[valid])[:, 1]
    scores.append(average_precision_score(y_demo[valid], p_valid))
    print("fold", fold, "resampled train", np.bincount(y_demo[sampled]),
          "natural validation", np.bincount(y_demo[valid]))
print("fold AP", scores)
