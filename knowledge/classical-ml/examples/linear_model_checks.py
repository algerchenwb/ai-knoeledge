"""独立教学示例：核验线性模型手算、阈值与调参流程。
依赖 numpy、scikit-learn；在 scikit-learn 1.8.0 验证。
"""
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import mean_squared_error

X = np.array([[1.], [2.], [3.]])
y = np.array([2., 3., 5.])
ols = LinearRegression().fit(X, y)
assert np.allclose(ols.coef_, [1.5])
assert np.isclose(ols.intercept_, 1/3)
assert np.isclose(mean_squared_error(y, ols.predict(X)), 1/18)
print("OLS:", ols.coef_, ols.intercept_, "MSE:", mean_squared_error(y, ols.predict(X)))

X_centered = np.array([[-1.], [0.], [1.]])
y_centered = np.array([-2., 0., 2.])
ridge = Ridge(alpha=2.0, fit_intercept=False).fit(X_centered, y_centered)
lasso = Lasso(alpha=0.5, fit_intercept=False, max_iter=10000).fit(X_centered, y_centered)
lasso_zero = Lasso(alpha=2.0, fit_intercept=False, max_iter=10000).fit(X_centered, y_centered)
assert np.allclose(ridge.coef_, [1.0])
assert np.allclose(lasso.coef_, [1.25])
assert np.allclose(lasso_zero.coef_, [0.0])
print("Ridge/Lasso/strong Lasso:", ridge.coef_, lasso.coef_, lasso_zero.coef_)

# 以下两个完整示例由对应教程独立编写的代码组合而成。

import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

X_train = np.array([[-3.], [-2.], [-1.], [1.], [2.], [3.]])
y_train = np.array([0, 0, 0, 1, 1, 1])
model = make_pipeline(
    StandardScaler(), LogisticRegression(C=1.0, max_iter=1000)
)
model.fit(X_train, y_train)
X_check = np.array([[-2.5], [0.], [2.5]])
proba = model.predict_proba(X_check)
classes = model[-1].classes_
positive_column = int(np.flatnonzero(classes == 1)[0])
p = proba[:, positive_column]
print("classes", classes, "p", p)
print("threshold 0.5", (p >= 0.5).astype(int))
print("threshold 0.8", (p >= 0.8).astype(int))
assert p[0] < p[1] < p[2]
assert np.allclose(proba.sum(axis=1), 1)
print("train log loss",
      log_loss(y_train, model.predict_proba(X_train), labels=classes))

import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

X, y = make_regression(
    n_samples=240, n_features=12, n_informative=5,
    noise=20, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)
pipeline = make_pipeline(StandardScaler(), Ridge())
search = GridSearchCV(
    pipeline, {"ridge__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
    cv=KFold(n_splits=5, shuffle=True, random_state=42),
    scoring="neg_mean_squared_error"
)
search.fit(X_dev, y_dev)
pred = search.predict(X_test)
print("chosen", search.best_params_)
print("CV MSE", -search.best_score_)
print("final test MSE", mean_squared_error(y_test, pred))
assert np.isfinite(pred).all()
