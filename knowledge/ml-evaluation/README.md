# 机器学习评估基础

基于 scikit-learn 开源项目整理，面向应用与后端开发者。先说明“分数为什么可信”，再讨论“分数应该怎么看”。这是独立中文知识整理，并非官方逐字翻译。

## 推荐阅读顺序

| 顺序 | 已完成知识点 | 重点 |
| --- | --- | --- |
| 1 | [数据泄漏与 Pipeline](01-data-leakage-and-pipelines.md) | 预测时点、未来字段、统计预处理、特征选择与线上一致性 |
| 2 | [数据划分与交叉验证](02-validation-and-cross-validation.md) | 训练/验证/测试、K 折、分层、分组、时间切分与嵌套验证 |
| 3 | [模型指标与业务决策](03-metrics-and-business-decisions.md) | 混淆矩阵、Precision/Recall/F1、AUC/AP、阈值、成本与回归指标 |

每篇包含机制、虚构业务例子、误区、Python 练习和参考答案。POI/客流场景是为了帮助理解，不表示某项生产数据已经适合训练。

## 来源与可追溯性

核验日期：2026-10-03。固定来源提交：`a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。

| 来源文件 | 对应知识点 |
| --- | --- |
| [doc/common_pitfalls.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/common_pitfalls.rst) | 数据泄漏、预处理一致性、Pipeline |
| [doc/modules/cross_validation.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/cross_validation.rst) | 切分器、交叉验证和组/时间边界 |
| [doc/modules/model_evaluation.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/model_evaluation.rst) | 分类与回归指标、排名与概率评估 |
| [COPYING](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING) | BSD 3-Clause 许可；Copyright (c) 2007-2026 The scikit-learn developers |

中文解释、业务扩展、代码和算例独立编写，没有整段复制来源。许可证链接不表示本知识库全部内容自动采用来源项目许可证。

## 示例验证记录

本批三个完整示例已在 Python / scikit-learn 1.8.0 环境运行。第三篇输出与手算一致：Accuracy=0.94、Precision≈0.6667、Recall=0.8、F1≈0.7273。合成数据分数仅用于验证示例能执行，不是生产效果承诺。

## 后续扩展方向（尚未完成）

- 线性/逻辑回归、损失函数、正则化与偏差方差。
- 树模型、梯度提升、特征工程与解释方法。
- 概率校准、阈值调优与分布漂移。
- 深度学习训练机制、Embedding、向量检索和 RAG 评估。

完成条目应加入上面的“已完成知识点”，并保留明确来源。尚未完成的目录不应被当作现有教程。

[返回总入口](../../README.md)
