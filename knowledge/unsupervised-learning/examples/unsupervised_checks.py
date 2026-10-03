"""独立教学示例：K-means、DBSCAN 与 PCA 机制核验。"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

X = np.array([[1.], [2.], [8.], [9.]])
model = KMeans(n_clusters=2, n_init=10, random_state=42).fit(X)
print("centers", np.sort(model.cluster_centers_.ravel()))
print("inertia", model.inertia_)
print("silhouette", silhouette_score(X, model.labels_))
assert np.allclose(np.sort(model.cluster_centers_.ravel()), [1.5, 8.5])
assert np.isclose(model.inertia_, 1.)
assert model.labels_[0] == model.labels_[1]
assert model.labels_[2] == model.labels_[3]
assert model.labels_[0] != model.labels_[2]
print("new samples", model.predict([[1.8], [8.2]]))

import numpy as np
from sklearn.cluster import DBSCAN

X = np.array([[0.], [0.1], [0.2], [3.], [3.1], [3.2], [10.]])
model = DBSCAN(eps=0.15, min_samples=3).fit(X)
labels = model.labels_
print("labels", labels)
print("core indices", model.core_sample_indices_)
assert set(model.core_sample_indices_) == {1, 4}
assert labels[-1] == -1
assert labels[0] == labels[1] == labels[2]
assert labels[3] == labels[4] == labels[5]
assert labels[0] != labels[3]
assert len(set(labels) - {-1}) == 2

import numpy as np
from sklearn.decomposition import PCA

X = np.array([[-2., -2.], [-1., -1.], [1., 1.], [2., 2.]])
pca = PCA(n_components=1, svd_solver="full").fit(X)
Z = pca.transform(X)
reconstructed = pca.inverse_transform(Z)
print("component", pca.components_)
print("variance ratio", pca.explained_variance_ratio_)
print("reconstruction error", np.mean((X - reconstructed)**2))
assert Z.shape == (4, 1)
assert np.allclose(pca.explained_variance_ratio_, [1.])
assert np.allclose(np.abs(pca.components_[0]), [1/np.sqrt(2)]*2)
assert np.allclose(reconstructed, X)

