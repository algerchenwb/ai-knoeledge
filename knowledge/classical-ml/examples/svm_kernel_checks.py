# -*- coding: utf-8 -*-
"""Executable examples from the SVM and kernel tutorials."""
import sklearn
print("scikit-learn", sklearn.__version__)

import numpy as np
from sklearn.svm import SVC

X = np.array([[-2.], [-1.], [1.], [2.]])
y = np.array([-1, -1, 1, 1])
model = SVC(kernel="linear", C=10).fit(X, y)
print("coef", model.coef_, "intercept", model.intercept_)
print("support", model.support_vectors_.ravel())
print("score", model.decision_function([[-0.5], [0.5]]))
assert np.allclose(model.coef_, [[1.]])
assert np.allclose(model.intercept_, [0.])
assert np.allclose(np.sort(model.support_vectors_.ravel()), [-1., 1.])
assert np.array_equal(model.predict([[-0.5], [0.5]]), [-1, 1])
print("total margin width", 2 / np.linalg.norm(model.coef_))


import numpy as np
from sklearn.svm import SVC

X = np.array([[-1., -1.], [-1., 1.], [1., -1.], [1., 1.]])
y = np.array([0, 1, 1, 0])
linear = SVC(kernel="linear", C=10).fit(X, y)
rbf = SVC(kernel="rbf", C=10, gamma=1).fit(X, y)
print("linear train accuracy", linear.score(X, y))
print("RBF train accuracy", rbf.score(X, y))
assert linear.score(X, y) < 1
assert np.array_equal(rbf.predict(X), y)


from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score

X, y = make_moons(n_samples=240, noise=0.2, random_state=42)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), SVC()),
    {"svc__C": [0.1, 1., 10.], "svc__gamma": [0.1, 1., 10.]},
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
    scoring="balanced_accuracy"
)
search.fit(X_dev, y_dev)
print("chosen", search.best_params_)
print("CV", search.best_score_)
print("final test", balanced_accuracy_score(y_test, search.predict(X_test)))
