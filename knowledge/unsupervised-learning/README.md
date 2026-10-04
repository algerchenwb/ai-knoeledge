# 无监督学习基础：聚类与降维

基于 scikit-learn 官方开源文档整理，面向应用开发者。重点理解算法“优化什么”，并避免把几何分组或数据压缩误认为已验证的业务结论。

## 已完成教程

| 顺序 | 教程 | 重点 |
| --- | --- | --- |
| 1 | [K-means](01-kmeans-and-cluster-evaluation.md) | 中心、距离、尺度、K 的选择、轮廓系数与验证边界 |
| 2 | [DBSCAN](02-dbscan-density-and-noise.md) | 核心/边界/噪声、邻域参数、地理距离、覆盖与内存 |
| 3 | [PCA](03-pca-and-information-loss.md) | 主成分、中心化、方差解释率、重建、Whitening 与泄漏 |
| 4 | [高斯混合模型与 EM](04-gaussian-mixture-and-em.md) | 软归属、责任度手算、协方差约束、BIC 与密度边界 |
| 5 | [谱聚类](05-spectral-clustering.md) | 相似图、图拉普拉斯、归一化切割、输入语义与转导边界 |
| 示例 | [机制核验脚本](examples/unsupervised_checks.py) | 三个完整算例，可离线运行 |

相关知识：[评估基础](../ml-evaluation/README.md)、[经典监督模型](../classical-ml/README.md)、[张量形状](../deep-learning-basics/01-tensors-shapes-and-devices.md)。

## 来源记录

核验日期：2026-10-04。来源项目：[scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)。

固定提交：`a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。

| 来源文件 | 对应内容 |
| --- | --- |
| [clustering.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/clustering.rst) | K-means、DBSCAN、轮廓系数 |
| [_dbscan.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/cluster/_dbscan.py) | min_samples 包含自身、eps 与最坏内存边界 |
| [decomposition.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/decomposition.rst) | PCA、中心化、方差解释、Whitening、增量方法 |

中文解释、算例与业务扩展独立编写，不是官方逐字翻译。来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)，Copyright (c) 2007-2026 The scikit-learn developers。本整理与官方项目无隶属关系。

## 示例验证记录

环境：scikit-learn 1.8.0。来源主分支与本地版本不完全相同，本批只对已运行的基本 API 声明实跑。

- K-means：中心 [1.5,8.5]，inertia=1，轮廓系数约 0.8564。
- DBSCAN：两个簇和一个噪声，核心点索引为 [1,4]；所有成员关系断言通过。
- PCA：一维解释率为 1，共线数据重建误差约 6.16×10⁻³²，属于浮点误差范围。

这些结果仅核对人工例子，不是生产聚类效果承诺。簇编号和主成分符号不是业务等级。

运行：

```bash
python knowledge/unsupervised-learning/examples/unsupervised_checks.py
```

### GMM 验证补充

[GMM 脚本](examples/gmm_checks.py)核对一轮人工 EM、AIC/BIC 公式、密度重构、编号交换和四种协方差形状。Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、scikit-learn 1.8.0；8 次拟合、32 次初始化均完成。合成数据 BIC 选择 K=2，最终测试平均对数密度 −1.698965。详见教程中的数据划分与验证边界。

新增固定来源：[mixture.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/mixture.rst)、[_gaussian_mixture.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/mixture/_gaussian_mixture.py)，与上方同一提交及 BSD 3-Clause 许可。

运行：

```bash
python knowledge/unsupervised-learning/examples/gmm_checks.py
```

## 后续扩展（尚未完成）

层次聚类、HDBSCAN/OPTICS、非线性降维与聚类稳定性实验。尚未完成条目不作为已有教程计数。

[返回总入口](../../README.md)

### 谱聚类验证补充

[谱聚类脚本](examples/spectral_checks.py)核对边能量等式、两个连通分量的零特征值、弱桥图分组、ARI编号不变性及无predict接口。Python 3.12.14、NumPy 2.3.5、scikit-learn 1.8.0，退出码0，无stderr。固定300条同心圆案例上谱聚类ARI=1.0，K-means ARI≈−0.003355；只是单一结构演示，不是普遍性能结论。来源快照、API约定和限制详见教程。

运行：`python knowledge/unsupervised-learning/examples/spectral_checks.py`。
