# 经典机器学习模型基础

基于 scikit-learn 官方开源文档，面向想理解模型机制的应用开发者。先学数值预测，再学分类概率，再理解正则化与调参，再学习决策树和集成模型，并理解支持向量机、核方法、近邻模型和朴素贝叶斯，进一步处理概率校准、类别不平衡、异常检测、特征选择、模型依赖解释与保存/加载协议。

## 已完成教程

| 顺序 | 教程 | 内容 |
| --- | --- | --- |
| 1 | [线性回归](01-linear-regression.md) | 系数、截距、残差、最小二乘、共线性、非线性特征 |
| 2 | [逻辑回归](02-logistic-regression.md) | sigmoid、odds、对数损失、阈值、类别与特征编码 |
| 3 | [正则化](03-regularization.md) | Ridge、Lasso、ElasticNet、尺度、alpha 与安全调参 |
| 4 | [决策树](04-decision-trees.md) | 分裂纯度、叶值、复杂度控制与外推限制 |
| 5 | [随机森林](05-random-forests.md) | Bootstrap、概率平均、OOB 与特征重要性 |
| 6 | [梯度提升树](06-gradient-boosting.md) | 残差/负梯度、学习率、早停与公平比较 |
| 7 | [支持向量机](07-support-vector-machines.md) | 最大间隔、软约束、C、分类分数与 SVR |
| 8 | [核方法与 RBF](08-kernels-and-rbf.md) | XOR、gamma、联合调参、核矩阵与计算规模 |
| 9 | [近邻模型](09-nearest-neighbors.md) | 距离、投票、加权回归、尺度、索引与自查询 |
| 10 | [朴素贝叶斯](10-naive-bayes.md) | 先验/后验、条件独立、模型变体、平滑与词表 |
| 11 | [概率校准](11-probability-calibration.md) | 可靠性曲线、Brier、校准隔离与成本阈值 |
| 12 | [类别不平衡](12-class-imbalance.md) | 发生率、类权重、重采样与折内验证 |
| 13 | [异常检测与 Isolation Forest](13-isolation-forest.md) | 随机隔离、分数方向、阈值与独立评估 |
| 14 | [Local Outlier Factor](14-local-outlier-factor.md) | 局部可达密度、手算与新颖性接口 |
| 15 | [特征选择](15-feature-selection.md) | 方差、单变量与交互、L1、包装法和筛选泄漏 |
| 16 | [置换重要性](16-permutation-importance.md) | 指标方向、相关列、组置换和因果边界 |
| 17 | [模型保存与输入协议](17-model-persistence-and-input-contracts.md) | Pipeline、格式、版本、字段、类别映射与加载验证 |
| 持久化示例 | [验证脚本](examples/model_persistence_contract_checks.py) | 可信本地往返、六类输入拒绝、摘要与正类映射 |
| 特征选择与解释示例 | [验证脚本](examples/feature_selection_importance_checks.py) | 常数列、XOR、折内筛选和单列/组置换 |
| 异常检测示例 | [验证脚本](examples/anomaly_detection_checks.py) | 隔离分数/阈值、正常校验集与 LOF 手算 |
| 校准与不平衡示例 | [验证脚本](examples/calibration_imbalance_checks.py) | 概率质量、校准、权重与折内随机复制 |
| 近邻与 NB 示例 | [验证脚本](examples/knn_naive_bayes_checks.py) | 加权手算、保留测试调参、平滑与未知词 |
| 核示例 | [SVM 与核方法验证脚本](examples/svm_kernel_checks.py) | 一维间隔、XOR 与保留测试集的网格搜索 |
| 树示例 | [树与集成验证脚本](examples/tree_ensemble_checks.py) | 分裂阈值、森林合并与一轮提升核对 |
| 示例 | [线性模型验证脚本](examples/linear_model_checks.py) | 手算核对、正则收缩、分类阈值与 GridSearchCV |

深入解释方法另见 [模型可解释性专题](../explainability/README.md)。本专题第 16 篇侧重经典模型的固定算例与组置换，不替代该专题的 PDP/ICE 和 Shapley 内容。

相关前置知识：[评估基础](../ml-evaluation/README.md)。理解梯度可进一步读 [深度学习训练基础](../deep-learning-basics/README.md)。

## 固定来源

核验日期：2026-10-04。

- 项目：[scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)。
- 来源提交：`a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。
- 来源文件：[doc/modules/linear_model.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/linear_model.rst)。
- 树模型来源：[tree.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/tree.rst)、[ensemble.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/ensemble.rst)、[permutation_importance.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/permutation_importance.rst)，使用同一固定提交。
- SVM 与核方法来源：[svm.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/svm.rst)，使用同一固定提交。
- 近邻与朴素贝叶斯来源：[neighbors.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/neighbors.rst)、[naive_bayes.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/naive_bayes.rst)，使用同一固定提交。
- 校准与类权重来源：[calibration.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/calibration.rst)、[class_weight.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/utils/class_weight.py)，使用同一固定提交。
- 采样补充来源：[imbalanced-learn common_pitfalls.rst](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/doc/common_pitfalls.rst) 与 [over_sampling.rst](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/doc/over_sampling.rst)，固定提交 `8504e95f0160f61d1b617ca66f779646d2ee609e`，采用 [MIT License](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/LICENSE)。该项目 API 未实跑，本批随机复制代码独立编写。
- 异常检测来源：[outlier_detection.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/outlier_detection.rst)，另核对 [Isolation Forest 阈值实现](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/ensemble/_iforest.py)，使用同一固定提交。
- 特征选择来源：[feature_selection.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/feature_selection.rst)，置换解释使用上列 permutation_importance.rst，同一固定提交。
- 持久化来源：[model_persistence.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/model_persistence.rst)，同一固定提交；输入协议与 manifest 为独立工程延伸。
- 对应章节：Ordinary Least Squares、Ridge、Lasso、Elastic-Net、Logistic regression。
- 许可：[BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)，Copyright (c) 2007-2026 The scikit-learn developers。

中文解释、算例、业务延伸与代码独立编写，不是官方逐字翻译。此整理与 scikit-learn 官方没有隶属关系，来源许可也不自动决定整个知识库的许可。

## 示例验证

环境：scikit-learn 1.8.0。固定来源主分支与安装版本不完全相同，本批使用已实跑的基本 API。

- 一元回归：斜率 1.5，截距约 1/3，训练 MSE 约 1/18。
- 同一中心化算例：Ridge(alpha=2) 系数为 1，Lasso(alpha=0.5) 为 1.25，Lasso(alpha=2) 为 0。
- 合成二分类检查点正类概率约 [0.1960,0.5,0.8040]；阈值 0.5 与 0.8 得到不同决策。
- 五折调参示例选中 Ridge alpha=0.1；CV MSE 约 432.68，独立最终测试 MSE 约 377.39。

- 分类树阈值为 2.5，回归叶预测为 11 与 32；范围外输入 100 仍预测 32。
- 随机森林输出与各树类别概率平均一致。
- 一轮平方误差提升从初始 [25,25,25,25] 得到 [20,20,30,30]，MSE 从 125 降为 50。

- 一维线性 SVM：系数为 1，支持向量为 −1 与 1，总间隔宽度为 2。
- XOR：线性 SVC 训练准确率为 0.5，RBF 为 1.0；这不是泛化比较。
- 合成双月数据网格搜索选中 C=10、gamma=1，CV balanced accuracy 约 0.9444，保留测试集约 0.9833。

- KNN 加权 A 类比例为 9/13；均匀回归为 80/3，距离加权回归为 200/13，与手算一致。
- Iris 开发集三折搜索选中 k=3、uniform，CV balanced accuracy 约 0.9613，保留测试集约 0.9111。
- NB 人为二值算例的投诉后验为 225/257；词计数平滑得到 [0.8,0.2]，与模型结果一致。
- 中文教学文本预测与断言一致；未知词“停车”转换成全零向量。该示例没有提供独立业务性能评估。

- 概率算例：Brier 为 0.335，常数 0.5 模型为 0.25；严格递增变换保留 AUC=0.5，但 Brier 变为约 0.4112。
- 三份合成数据隔离校准示例：最终测试 Brier 约 0.1208，log loss 约 0.4267；不代表对其他方法的性能比较。
- 1% 正类、TPR=0.8、FPR=0.05 算例 Precision 为 80/575≈0.1391；balanced 权重约为 [0.5051,50]。
- 类权重开发集比较选中 C=1、无类别权重，CV AP 约 0.4677，测试 AP 约 0.5986；固定阈值 0.5 的 Precision=1、Recall≈0.2273。
- 手动折内随机复制验证了训练/验证行号不重叠；每折重采样训练计数 [240,240]，验证保留 [120,14] 或 [120,13]。

- Isolation Forest 固定种子下 contamination=0.05 与 0.2 的查询原始分数一致，训练告警数分别为 16 与 63。
- 独立正常校验集的 5% 分位数阈值约为 −0.5617；人为远处异常测试 AP=1，Precision=0.5、Recall=1，正常 FPR=0.05。此合成异常被刻意设得容易，不是业务性能保证。
- 四点 LOF 为 [0.875,1.3333,0.875,4.9583]，与手算一致；新颖性示例只预测独立新点，正常与远点分别为 +1 与 −1。

- 方差筛选删除常数列；XOR 两列 F 分数都为 0，联合树模型可拟合四点。
- 筛选搜索选中 k=3、C=0.1，列索引 [0,1,10]，CV balanced accuracy≈0.8804，最终测试≈0.8608；选中噪声列也说明统计筛选不等于识别真实机制。
- 手算 R² 置换下降为 4；重复信号列的单列 MSE 重要性约 4.917，整组置换 MSE 增量约 19.830，验证两种估计目标不同。

- joblib 完整 Pipeline 保存/加载前后最大概率差为 0；classes_=['high','low']，正类在第 0 列，p(high)≈[0.2104,0.8814]。
- 六类无效输入被拒绝；修改文件字节后在反序列化前发现摘要不匹配。摘要不是来源认证。
- 持久化运行环境另记录为 Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、scikit-learn 1.8.0、joblib 1.5.3；未测试其他格式、跨版本加载或真实部署。

这些数值只用于核对示例，不是实际业务性能结论。边界概率和浮点输出可能随环境略有变化。

运行：

```bash
python knowledge/classical-ml/examples/linear_model_checks.py
python knowledge/classical-ml/examples/tree_ensemble_checks.py
python knowledge/classical-ml/examples/svm_kernel_checks.py
python knowledge/classical-ml/examples/knn_naive_bayes_checks.py
python knowledge/classical-ml/examples/calibration_imbalance_checks.py
python knowledge/classical-ml/examples/anomaly_detection_checks.py
python knowledge/classical-ml/examples/feature_selection_importance_checks.py
python knowledge/classical-ml/examples/model_persistence_contract_checks.py
```

## 后续扩展（尚未完成）

模型服务集成、模型更新与增量学习等。聚类与降维已另设 [无监督学习专题](../unsupervised-learning/README.md)。只有完成并核验的条目才加入上面的教程表。

[返回总入口](../../README.md)
