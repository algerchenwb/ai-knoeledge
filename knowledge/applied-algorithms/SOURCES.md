# 开源来源与核验记录

核验日期：2026-10-04。以下链接固定到实际读取的提交，而非随时变化的main。本专题是独立中文讲解与教学实验；没有整篇翻译或复制上游实现。核心算法和API约定来自这些官方仓库，业务流程、误区与练习为独立扩展。固定源码版本与本地安装的运行版本不是同一个概念。

| 轮次 | 主题 | 已读取源码/文档快照 | 上游许可 |
| --- | --- | --- | --- |
| 1 | TF-IDF | [scikit-learn/scikit-learn / doc/modules/feature_extraction.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/feature_extraction.rst) | BSD-3-Clause |
| 2 | 特征哈希 | [scikit-learn/scikit-learn / doc/modules/feature_extraction.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/feature_extraction.rst) | BSD-3-Clause |
| 3 | NMF主题模型 | [scikit-learn/scikit-learn / doc/modules/decomposition.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/decomposition.rst) | BSD-3-Clause |
| 4 | Apriori与关联规则 | [rasbt/mlxtend / mlxtend/frequent_patterns/association_rules.py](https://github.com/rasbt/mlxtend/blob/1aee767ef57b84a8191511a08955c583b65de382/mlxtend/frequent_patterns/association_rules.py) | BSD-3-Clause（代码） |
| 5 | 隐式反馈ALS | [benfred/implicit / implicit/cpu/als.py](https://github.com/benfred/implicit/blob/8a95dbe24ca675a6edd86aafb3b4cd5ae7287edf/implicit/cpu/als.py) | MIT |
| 6 | 排序指标深入 | [scikit-learn/scikit-learn / sklearn/metrics/_ranking.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/metrics/_ranking.py) | BSD-3-Clause |
| 7 | PageRank | [networkx/networkx / networkx/algorithms/link_analysis/pagerank_alg.py](https://github.com/networkx/networkx/blob/31b74e96903d7f873b30c8ff36d71a4c9252b107/networkx/algorithms/link_analysis/pagerank_alg.py) | BSD-3-Clause |
| 8 | 图消息传递 | [pyg-team/pytorch_geometric / docs/source/tutorial/create_gnn.rst](https://github.com/pyg-team/pytorch_geometric/blob/79d33965a40b7fa83616a9f598a0f8619f25d939/docs/source/tutorial/create_gnn.rst) | MIT |
| 9 | 在线学习 | [scikit-learn/scikit-learn / sklearn/linear_model/_stochastic_gradient.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/linear_model/_stochastic_gradient.py) | BSD-3-Clause |
| 10 | 漂移检测 | [online-ml/river / river/drift/page_hinkley.py](https://github.com/online-ml/river/blob/086e8028b4867ee7dbc40d4e7b9886c5fe80f4a7/river/drift/page_hinkley.py) | BSD-3-Clause |

补充核对：[Apriori候选生成](https://github.com/rasbt/mlxtend/blob/1aee767ef57b84a8191511a08955c583b65de382/mlxtend/frequent_patterns/apriori.py)、[implicit README](https://github.com/benfred/implicit/blob/8a95dbe24ca675a6edd86aafb3b4cd5ae7287edf/README.md)。mlxtend文档另有CC-BY许可；本专题采用的是已读取的BSD代码说明，未复制其文档。

## 实验范围

实际库集成：第1、2、3、6、9轮调用scikit-learn。独立数学实验：第4轮标准库Apriori，第5轮NumPy稠密精确ALS，第7轮NumPy PageRank，第8轮NumPy消息聚合，第10轮标准库简化Page-Hinkley。未运行mlxtend、implicit、NetworkX、PyG或River包，也不宣称这些包的完整API通过验证。

所有例子使用小型合成数据，无需网络、账号、GPU或真实用户数据。通过断言只说明对应机制在这些案例中满足预期，不等于生产性能或普适正确性证明。完整运行结果及环境见[验证记录](VALIDATION.md)。

## 上游版权与许可

上游许可证原文随专题保留，以便追溯；它们适用于各自上游项目，并非把本仓库整体重新许可。无上游背书或隶属关系。

- [scikit-learn许可原文](licenses/scikit-learn.txt)；[上游文件](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。
- [mlxtend许可原文](licenses/mlxtend.txt)；[上游文件](https://github.com/rasbt/mlxtend/blob/1aee767ef57b84a8191511a08955c583b65de382/LICENSE-BSD3.txt)。
- [implicit许可原文](licenses/implicit.txt)；[上游文件](https://github.com/benfred/implicit/blob/8a95dbe24ca675a6edd86aafb3b4cd5ae7287edf/LICENSE)。
- [networkx许可原文](licenses/networkx.txt)；[上游文件](https://github.com/networkx/networkx/blob/31b74e96903d7f873b30c8ff36d71a4c9252b107/LICENSE.txt)。
- [pyg许可原文](licenses/pyg.txt)；[上游文件](https://github.com/pyg-team/pytorch_geometric/blob/79d33965a40b7fa83616a9f598a0f8619f25d939/LICENSE)。
- [river许可原文](licenses/river.txt)；[上游文件](https://github.com/online-ml/river/blob/086e8028b4867ee7dbc40d4e7b9886c5fe80f4a7/LICENSE)。
