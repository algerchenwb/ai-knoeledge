# -*- coding: utf-8 -*-
"""Teaching checks, not business performance claims."""
import sklearn
print("scikit-learn",sklearn.__version__)

import numpy as np
from sklearn.feature_selection import VarianceThreshold
X = np.array([[1.,0.,0.], [1.,1.,0.], [1.,0.,1.], [1.,1.,1.]])
sel = VarianceThreshold().fit(X)
assert sel.get_support().tolist() == [False, True, True]
assert np.allclose(sel.variances_, [0., 0.25, 0.25])
assert sel.transform(X).shape == (4, 2)
print("variance/support", sel.variances_, sel.get_support())


import numpy as np
from sklearn.feature_selection import f_classif
from sklearn.tree import DecisionTreeClassifier
X_xor = np.array([[0.,0.], [0.,1.], [1.,0.], [1.,1.]])
y_xor = np.array([0,1,1,0])
scores, p_values = f_classif(X_xor, y_xor)
assert np.allclose(scores, [0.,0.])
assert np.allclose(p_values, [1.,1.])
tree = DecisionTreeClassifier(random_state=42).fit(X_xor, y_xor)
assert np.array_equal(tree.predict(X_xor), y_xor)
print("XOR F/p", scores, p_values)


from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score

X, y = make_classification(
    n_samples=600, n_features=12, n_informative=3, n_redundant=0,
    n_clusters_per_class=1, shuffle=False, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
pipe = Pipeline([
    ("scale", StandardScaler()),
    ("select", SelectKBest(f_classif)),
    ("model", LogisticRegression(max_iter=1000))
])
search = GridSearchCV(
    pipe, {"select__k":[3,6,"all"], "model__C":[0.1,1.]},
    scoring="balanced_accuracy",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
selected = search.best_estimator_.named_steps["select"].get_support(indices=True)
print("selected columns", selected)
print("selection params/CV", search.best_params_, search.best_score_)
print("selection final test",
      balanced_accuracy_score(y_test, search.predict(X_test)))


import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
X = np.arange(4., dtype=float).reshape(-1,1)
y = 2 * X[:,0]
model = LinearRegression().fit(X,y)
base = r2_score(y, model.predict(X))
shuffled = r2_score(y, model.predict(X[::-1]))
assert np.isclose(base,1.)
assert np.isclose(shuffled,-3.)
assert np.isclose(mean_squared_error(y,model.predict(X[::-1])),20.)
assert np.isclose(base-shuffled,4.)
print("manual R2 importance",base-shuffled)


import numpy as np
from sklearn.linear_model import Ridge
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error

rng = np.random.default_rng(42)
signal_train = rng.normal(size=400)
X_train = np.column_stack([
    signal_train,signal_train,rng.normal(size=400)
])
y_train = 3*signal_train+rng.normal(0,0.1,size=400)
signal_val = rng.normal(size=300)
X_val = np.column_stack([
    signal_val,signal_val,rng.normal(size=300)
])
y_val = 3*signal_val+rng.normal(0,0.1,size=300)
model = Ridge(alpha=1).fit(X_train,y_train)
result = permutation_importance(
    model,X_val,y_val,scoring="neg_mean_squared_error",
    n_repeats=20,random_state=42
)
base_mse = mean_squared_error(y_val,model.predict(X_val))
group_increase = []
for _ in range(20):
    order = rng.permutation(len(X_val))
    changed = X_val.copy()
    changed[:,:2] = X_val[order,:2]
    group_increase.append(
        mean_squared_error(y_val,model.predict(changed))-base_mse
    )
assert np.mean(group_increase)>np.max(result.importances_mean[:2])
print("Ridge coef/base MSE",model.coef_,base_mse)
print("single column importance",result.importances_mean)
print("shuffle std",result.importances_std)
print("group increase",np.mean(group_increase),np.std(group_increase))
