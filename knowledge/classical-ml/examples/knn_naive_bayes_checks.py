# -*- coding: utf-8 -*-
"""Mechanism checks; toy examples are not business performance estimates."""
import sklearn
print("scikit-learn", sklearn.__version__)

import numpy as np
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor

X = np.array([[0.], [2.], [5.]])
query = [[0.5]]
labels = np.array(["A", "B", "B"])
uniform = KNeighborsClassifier(n_neighbors=3, weights="uniform").fit(X, labels)
weighted = KNeighborsClassifier(n_neighbors=3, weights="distance").fit(X, labels)
assert uniform.predict(query)[0] == "B"
assert weighted.predict(query)[0] == "A"
assert np.allclose(weighted.predict_proba(query), [[9/13, 4/13]])
print("classes", weighted.classes_, "weighted vote", weighted.predict_proba(query))

values = [10., 20., 50.]
ru = KNeighborsRegressor(n_neighbors=3).fit(X, values)
rw = KNeighborsRegressor(n_neighbors=3, weights="distance").fit(X, values)
assert np.allclose(ru.predict(query), [80/3])
assert np.allclose(rw.predict(query), [200/13])
print("regression", ru.predict(query), rw.predict(query))


from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import balanced_accuracy_score

X, y = load_iris(return_X_y=True)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), KNeighborsClassifier()),
    {"kneighborsclassifier__n_neighbors": [3, 5, 9],
     "kneighborsclassifier__weights": ["uniform", "distance"]},
    scoring="balanced_accuracy",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
print("KNN chosen", search.best_params_)
print("KNN CV", search.best_score_)
print("KNN final test",
      balanced_accuracy_score(y_test, search.predict(X_test)))


import numpy as np
scores = np.array([0.8 * 0.1 * 0.2, 0.2 * 0.75 * 0.75])
posterior = scores / scores.sum()
assert np.allclose(posterior[1], 225/257)
print("manual complaint posterior", posterior[1])


import numpy as np
from sklearn.naive_bayes import MultinomialNB

X = np.array([[3., 0.], [0., 3.]])
y = [0, 1]
model = MultinomialNB(alpha=1).fit(X, y)
assert np.allclose(np.exp(model.feature_log_prob_),
                   [[0.8, 0.2], [0.2, 0.8]])
assert np.allclose(model.predict_proba([[1., 0.]]), [[0.8, 0.2]])
assert np.allclose(model.predict_proba([[0., 0.]]), [[0.5, 0.5]])
print("NB smoothed likelihood", np.exp(model.feature_log_prob_))
print("NB posterior", model.predict_proba([[1., 0.]]))


from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# 显式空格分词的中文教学文本；不是完整中文分词器。
texts = ["退款 延期 退款", "退款 失败", "延期 失败",
         "导航 地址", "营业 时间", "地址 时间"]
labels = ["投诉", "投诉", "投诉", "咨询", "咨询", "咨询"]
pipe = make_pipeline(
    CountVectorizer(tokenizer=str.split, token_pattern=None),
    MultinomialNB(alpha=1)
)
pipe.fit(texts, labels)
pred = pipe.predict(["退款 延期", "地址 营业"])
assert pred.tolist() == ["投诉", "咨询"]
print("text predictions", pred)
vocabulary = pipe.named_steps["countvectorizer"].vocabulary_
assert "停车" not in vocabulary
print("unseen word counts", pipe.named_steps["countvectorizer"]
      .transform(["停车"]).toarray())
