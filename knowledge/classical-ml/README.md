# 经典机器学习模型基础

基于 scikit-learn 官方开源文档，面向想理解模型机制的应用开发者。先学数值预测，再学分类概率，再理解正则化与调参，最后学习决策树和集成模型。

## 已完成教程

| 顺序 | 教程 | 内容 |
| --- | --- | --- |
| 1 | [线性回归](01-linear-regression.md) | 系数、截距、残差、最小二乘、共线性、非线性特征 |
| 2 | [逻辑回归](02-logistic-regression.md) | sigmoid、odds、对数损失、阈值、类别与特征编码 |
| 3 | [正则化](03-regularization.md) | Ridge、Lasso、ElasticNet、尺度、alpha 与安全调参 |
| 4 | [决策树](04-decision-trees.md) | 分裂纯度、叶值、复杂度控制与外推限制 |
| 5 | [随机森林](05-random-forests.md) | Bootstrap、概率平均、OOB 与特征重要性 |
| 6 | [梯度提升树](06-gradient-boosting.md) | 残差/负梯度、学习率、早停与公平比较 |
| 树示例 | [树与集成验证脚本](examples/tree_ensemble_checks.py) | 分裂阈值、森林合并与一轮提升核对 |
| 示例 | [线性模型验证脚本](examples/linear_model_checks.py) | 手算核对、正则收缩、分类阈值与 GridSearchCV |

相关前置知识：[评估基础](../ml-evaluation/README.md)。理解梯度可进一步读 [深度学习训练基础](../deep-learning-basics/README.md)。

## 固定来源

核验日期：2026-10-04。

- 项目：[scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)。
- 来源提交：`a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。
- 来源文件：[doc/modules/linear_model.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/linear_model.rst)。
- 树模型来源：[tree.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/tree.rst)、[ensemble.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/ensemble.rst)、[permutation_importance.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/permutation_importance.rst)，使用同一固定提交。
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

这些数值只用于核对示例，不是实际业务性能结论。边界概率和浮点输出可能随环境略有变化。

运行：

```bash
python knowledge/classical-ml/examples/linear_model_checks.py
python knowledge/classical-ml/examples/tree_ensemble_checks.py
```

## 后续扩展（尚未完成）

支持向量机、聚类与降维。只有完成并核验的条目才加入上面的教程表。

[返回总入口](../../README.md)
