# -*- coding: utf-8 -*-
"""Mechanism checks, not business anomaly performance claims."""
import sklearn
print("scikit-learn", sklearn.__version__)

import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(42)
X_train = np.vstack([
    rng.normal(0, 0.4, size=(300, 2)),
    rng.uniform(3, 5, size=(15, 2))
])
X_query = np.array([[0., 0.], [4., 4.]])
models = [
    IsolationForest(n_estimators=100, max_samples=128,
                    contamination=c, random_state=42).fit(X_train)
    for c in [0.05, 0.2]
]
scores = [m.score_samples(X_query) for m in models]
assert np.allclose(scores[0], scores[1])
for m in models:
    d = m.decision_function(X_query)
    assert np.allclose(d, m.score_samples(X_query) - m.offset_)
    assert np.array_equal(m.predict(X_query), np.where(d < 0, -1, 1))
    print("IF offset/query score/predict",
          m.offset_, m.score_samples(X_query), m.predict(X_query))
    print("IF train flagged", np.sum(m.predict(X_train) == -1))


import numpy as np
from sklearn.metrics import average_precision_score, precision_score, recall_score

# 继续使用上一段已拟合的 models[0]。
model = models[0]
X_normal_cal = rng.normal(0, 0.4, size=(200, 2))
cal_scores = model.score_samples(X_normal_cal)
threshold = np.quantile(cal_scores, 0.05)
# 独立新样本；教学异常被故意放得很远。
X_test = np.vstack([
    rng.normal(0, 0.4, size=(400, 2)),
    rng.uniform(3, 5, size=(20, 2))
])
y_test = np.r_[np.zeros(400, dtype=int), np.ones(20, dtype=int)]
test_scores = model.score_samples(X_test)
flag = test_scores < threshold
assert test_scores.shape == y_test.shape
print("IF chosen threshold", threshold)
print("IF calibration flag fraction", np.mean(cal_scores < threshold))
print("IF test AP", average_precision_score(y_test, -test_scores))
print("IF test Precision/Recall",
      precision_score(y_test, flag, zero_division=0),
      recall_score(y_test, flag))
print("IF test normal FPR", np.mean(flag[y_test == 0]))


import numpy as np
from sklearn.neighbors import LocalOutlierFactor

X = np.array([[0.], [1.], [2.], [10.]])
lof = LocalOutlierFactor(n_neighbors=2, contamination=0.25)
labels = lof.fit_predict(X)
expected_lof = np.array([7/8, 4/3, 7/8, 119/24])
assert np.allclose(-lof.negative_outlier_factor_, expected_lof, atol=1e-7)
assert labels[-1] == -1
assert np.all(labels[:-1] == 1)
print("theoretical LOF", -lof.negative_outlier_factor_)
print("LOF training labels", labels)


import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

rng_lof = np.random.default_rng(17)
X_reference = rng_lof.normal(0, 0.3, size=(200, 2))
X_new = np.array([[0.02, -0.03], [4., 4.]])
pipe = make_pipeline(
    StandardScaler(),
    LocalOutlierFactor(n_neighbors=20, contamination=0.05, novelty=True)
)
pipe.fit(X_reference)
model = pipe.named_steps["localoutlierfactor"]
X_new_scaled = pipe.named_steps["standardscaler"].transform(X_new)
score = model.score_samples(X_new_scaled)
decision = model.decision_function(X_new_scaled)
pred = pipe.predict(X_new)
assert np.allclose(decision, score - model.offset_)
assert np.array_equal(pred, [1, -1])
assert score[1] < score[0]
print("LOF new score/decision/predict", score, decision, pred)
# 训练样本只查看已计算属性，不调用新颖性 predict(X_reference)。
print("LOF reference factor shape", model.negative_outlier_factor_.shape)
