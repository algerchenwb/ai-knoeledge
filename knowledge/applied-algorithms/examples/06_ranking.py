"""Manual linear-gain NDCG compared with sklearn, including tied scores."""
import numpy as np
from sklearn.metrics import ndcg_score

def dcg(gains):
    return sum(g / np.log2(j + 2) for j, g in enumerate(gains))

truth = np.array([[2., 3., 0.]])
scores = np.array([[3., 2., 1.]])
linear = dcg(truth[0]) / dcg(sorted(truth[0], reverse=True))
np.testing.assert_allclose(ndcg_score(truth, scores), linear)
np.testing.assert_allclose(ndcg_score(truth, truth), 1)
np.testing.assert_allclose(ndcg_score(np.zeros((1, 3)), scores), 0)
exp_truth = 2 ** truth - 1
exp_manual = dcg(exp_truth[0]) / dcg(sorted(exp_truth[0], reverse=True))
np.testing.assert_allclose(ndcg_score(exp_truth, scores), exp_manual)
assert not np.isclose(linear, exp_manual)
np.testing.assert_allclose(ndcg_score([[3., 0.]], [[1., 1.]], k=1), 0.5)

def reciprocal_rank(labels):
    return next((1 / j for j, relevant in enumerate(labels, 1) if relevant), 0.)

assert reciprocal_rank([False, True, True]) == 0.5
assert reciprocal_rank([False, False]) == 0
print("PASS NDCG manual/API agreement, gain variants, zero relevance, ties and RR")
