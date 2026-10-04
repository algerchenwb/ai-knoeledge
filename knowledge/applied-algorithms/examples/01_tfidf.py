"""Default smooth TF-IDF, frozen vocabulary, and all-OOV checks."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

v = TfidfVectorizer(tokenizer=str.split, token_pattern=None, norm="l2")
x = v.fit_transform(["苹果 苹果 甜", "苹果 梨", "梨"])
terms = list(v.get_feature_names_out())
df = {"苹果": 2, "梨": 2, "甜": 1}
expected_idf = np.array([1 + np.log(4 / (1 + df[t])) for t in terms])
np.testing.assert_allclose(v.idf_, expected_idf)
manual = np.array([{"苹果": 2, "甜": 1}.get(t, 0) for t in terms]) * expected_idf
manual /= np.linalg.norm(manual)
np.testing.assert_allclose(x.toarray()[0], manual)
np.testing.assert_allclose(np.sqrt(x.multiply(x).sum(axis=1)).A1, 1)
before = v.vocabulary_.copy()
assert v.transform(["香蕉"]).nnz == 0
assert before == v.vocabulary_
print("PASS TF-IDF formula, normalization, frozen vocabulary, OOV")
