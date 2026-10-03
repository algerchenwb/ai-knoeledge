"""独立教学验证：树分裂、森林概率平均与一轮梯度提升。"""
import numpy as np
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

X = np.array([[1.], [2.], [3.], [4.]])
y = np.array([0, 0, 1, 1])
clf = DecisionTreeClassifier(max_depth=1, random_state=42).fit(X, y)
print("split", clf.tree_.threshold[0])
print("class", clf.predict([[1.5], [3.5]]))
assert np.isclose(clf.tree_.threshold[0], 2.5)
assert np.array_equal(clf.predict([[1.5], [3.5]]), [0, 1])

reg = DecisionTreeRegressor(max_depth=1, random_state=42).fit(
    X, [10., 12., 30., 34.]
)
print("regression", reg.predict([[1.5], [3.5], [100.]]))
assert np.allclose(reg.predict([[1.5], [3.5], [100.]]), [11., 32., 32.])

import numpy as np
from sklearn.ensemble import RandomForestClassifier

X = np.array([[i, i % 3] for i in range(12)], dtype=float)
y = np.array([0]*6 + [1]*6)
forest = RandomForestClassifier(
    n_estimators=40, max_depth=3, min_samples_leaf=2,
    max_features="sqrt", random_state=42, n_jobs=1
).fit(X, y)
X_check = np.array([[2., 2.], [9., 0.]])
per_tree = np.stack([tree.predict_proba(X_check) for tree in forest.estimators_])
averaged = per_tree.mean(axis=0)
print("forest probability", forest.predict_proba(X_check))
assert np.allclose(averaged, forest.predict_proba(X_check))
assert np.allclose(averaged.sum(axis=1), 1)

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

X = np.array([[1.], [2.], [3.], [4.]])
y = np.array([10., 20., 30., 40.])
model = GradientBoostingRegressor(
    n_estimators=1, learning_rate=0.5,
    max_depth=1, loss="squared_error", random_state=42
).fit(X, y)
pred = model.predict(X)
print("initial", model.init_.predict(X))
print("after one stage", pred)
assert np.allclose(model.init_.predict(X), [25.]*4)
assert np.allclose(pred, [20., 20., 30., 30.])
assert np.isclose(mean_squared_error(y, pred), 50.)

