"""Hash collisions and stable batch transformation with sklearn."""
import numpy as np
from sklearn.feature_extraction import FeatureHasher

one = FeatureHasher(n_features=1, input_type="dict", alternate_sign=False)
np.testing.assert_allclose(one.transform([{"apple": 2, "pear": 3}]).toarray(), [[5]])
rows = [{"apple": 2}, {"unknown": 3}, {"pear": 1, "apple": 4}]
h = FeatureHasher(n_features=32, input_type="dict", alternate_sign=False)
batch = h.transform(rows).toarray()
split = np.vstack([h.transform([r]).toarray() for r in rows])
np.testing.assert_array_equal(batch, split)
assert batch.shape == (3, 32)
signed = FeatureHasher(n_features=64, input_type="dict", alternate_sign=True)
values = signed.transform([{f"token_{i}": 1} for i in range(100)]).data
assert np.any(values < 0)
print("PASS forced collision, fixed width, batch consistency, signed negatives")
