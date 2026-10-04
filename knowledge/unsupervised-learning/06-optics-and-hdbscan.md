# 06 OPTICS 与 HDBSCAN：不同密度的分组怎么找

> 目标：理解密度尺度为什么难选，区分 OPTICS 可达距离与 HDBSCAN 互可达距离，能解释参数、标签和成员强度。
>
> 前置：[DBSCAN](02-dbscan-density-and-noise.md)、[层次聚类](05-hierarchical-clustering.md)。本篇运行的是 scikit-learn 内置实现，不是第三方 hdbscan 包。

## 1. 一个固定邻域半径为什么不够

想象一张空间分布图：市中心位置点挤在一起，郊区点比较分散。DBSCAN 的 eps 给所有点使用同一个邻域半径：

- 半径小：密集群体能成簇，稀疏但真实的群体可能被打成噪声。
- 半径大：稀疏群体被保留，桥接点又可能把不同群体连起来。

这不意味着 DBSCAN 不能处理任何密度变化，只是单一全局尺度可能难以兼顾。

OPTICS 先整理“密度连接顺序”，然后选择提取规则。HDBSCAN 建立密度层次，再选择其中比较持久的簇。两者都不需要提前指定最终簇数，但仍有参数和假设；不能称为“完全自动发现真实类别”。

## 2. 共同基础：核心距离

先选一个邻居数 m。某点的核心距离可以理解为“至少包含 m 个样本，需要把邻域撑多大”。

在本文 scikit-learn 的约定中，样本自身也算一个邻居。m=3 就是把距离从小到大排序后的第三个距离；第一个通常为到自身的 0。重复样本还可能占据多个零距离位置。

核心距离小：附近较密；核心距离大：需要更大半径才能找到足够邻居。它是尺度，不是异常概率。

手算数据：

~~~text
[0, 0.1, 0.2, 0.3, 4, 4.4, 4.8, 5.2, 12]
~~~

有一组紧密的点、一组较松的点，以及一个孤立点。

| 坐标 | m=3 的核心距离 | 说明 |
| --- | ---: | --- |
| 0 | 0.2 | 自身、0.1、0.2 |
| 0.1 | 0.1 | 自身、0、0.2 |
| 0.2 | 0.1 | 自身、0.1、0.3 |
| 0.3 | 0.2 | 自身、0.2、0.1 |
| 4 | 0.8 | 自身、4.4、4.8 |
| 4.4 | 0.4 | 自身及两侧近邻 |
| 4.8 | 0.4 | 自身及两侧近邻 |
| 5.2 | 0.8 | 自身、4.8、4.4 |
| 12 | 7.2 | 自身、5.2、4.8 |

浮点计算可能出现 0.10000000000000005 等结果，脚本使用近似比较。

对给定 DBSCAN 半径 ε，某点核心距离不大于 ε，表示该尺度下邻域数量满足核心条件。核心距离大于 ε 的点不是核心点，但普通 DBSCAN 中仍可能是边界点。不能把“非核心”等同于“噪声”。

## 3. OPTICS：先排出密度连接顺序

OPTICS（Ordering Points To Identify the Clustering Structure）不只是返回标签，还产生顺序、核心距离和可达距离。

从一个核心点 p 出发，到 q 的候选可达距离：

$$
reach(q\mid p)=\max\{core(p),d(p,q)\}
$$

它只使用出发点 p 的核心距离，因此这个候选量通常有方向性。算法在处理过程中更新未处理点的候选值，并选择下一点；最终记录的是该顺序下得到的值，不是对所有点对计算的完整对称距离矩阵。

本例 min_samples=3、max_eps=8，实跑顺序恰好与坐标从小到大的顺序一致：

| 坐标 | 最终可达距离 |
| --- | ---: |
| 0 | ∞ |
| 0.1 | 0.2 |
| 0.2 | 0.1 |
| 0.3 | 0.1 |
| 4 | 3.7 |
| 4.4 | 0.8 |
| 4.8 | 0.4 |
| 5.2 | 0.4 |
| 12 | 6.8 |

∞ 表示没有此前处理点提供有限的可达连接，比如首次启动的种子。它本身不表示“异常概率无限大”。

请留意 12：它的核心距离是 7.2，可达距离是 6.8，因为从 5.2 到 12 的距离为 6.8，而 5.2 的核心距离只有 0.8。两个属性回答不同问题。

## 4. 可达距离图怎么读，索引怎么用

把 OPTICS 处理顺序放在横轴、可达距离放在纵轴，就得到 reachability plot。低谷常表示局部密集结构，进入另一个区域时可能出现高峰。

横轴不是时间、原始行号，也不必是坐标大小。低谷还可能嵌套，不能把每个凹陷都直接命名成业务群体。

scikit-learn 的几个属性：

| 属性 | 存储方式 |
| --- | --- |
| ordering_ | 按处理顺序排列的原始样本索引 |
| reachability_ | 按原始样本索引存储的可达距离 |
| core_distances_ | 按原始样本索引存储的核心距离 |
| predecessor_ | 到达该点的前驱原始索引；种子为 −1 |
| labels_ | 按原始样本行顺序返回的标签 |
| cluster_hierarchy_ | xi 提取的层次区间，区间索引对应 ordering_ 中的位置，两端包含 |

绘图应使用：

~~~python
ordered_reachability = model.reachability_[model.ordering_]
ordered_labels = model.labels_[model.ordering_]
~~~

不要先排序 reachability_ 的数值：那会丢掉邻接顺序。也不要把本例 ordering_ 恰好为递增索引误认为 API 永远如此。

## 5. OPTICS 的两种提取方式

### 固定 eps：复用排序

cluster_optics_dbscan 用已有的可达距离、核心距离和顺序提取 DBSCAN 风格的标签，不需要重新拟合 OPTICS。

本例一次拟合后做两次提取：

| 提取 eps | 找到的非噪声组 | 噪声数 |
| --- | --- | ---: |
| 0.25 | [0,0.1,0.2,0.3] | 5 |
| 1.0 | 上述组，以及 [4,4.4,4.8,5.2] | 1 |

这展示了半径选择的含义。本例可以找到一个半径同时保留两组，所以它不是“DBSCAN 必然失败”的证据。

**不要简单把所有 reachability > eps 的点标成噪声。** 如果一个点的可达距离大，但核心距离满足 eps，它可以启动新簇；本例坐标 4 的可达距离 3.7 大于 1，却是第二簇的一部分。

核心/边界与遍历顺序还可能使 OPTICS 提取结果与直接 DBSCAN 不完全一致。源码文档明确说明它是接近而非总是相同。

### xi：看相对陡峭变化

cluster_method="xi" 依据可达距离序列的陡降、陡升及相关规则识别区间；xi 控制什么变化算足够陡峭，min_cluster_size 控制最小簇规模。

xi 是相对变化阈值，不是欧氏半径，也不是噪声比例。小 xi 对较缓变化也可能敏感，但最终输出还依赖邻居数、区间规则与前驱校正，不能只靠一句“越小簇越多”预测所有结果。

max_eps 决定拟合时探索的最大邻域尺度，和提取时 eps 不同。设得小可能节省时间，却可能截断较稀疏结构。本脚本两个提取 eps 都小于拟合 max_eps；不要使用超过探索尺度的提取参数并假装信息完整。

## 6. HDBSCAN：用互可达距离建立密度层次

HDBSCAN 的核心构件是互可达距离：

$$
d_{mutual}(p,q)=
\max\{core(p),core(q),d(p,q)\}
$$

与 OPTICS 的候选可达距离不同，这里两端的核心距离都参与，结果对称。

本例：

- 0 与 0.1 的原始距离 0.1，互可达距离 max(0.2,0.1,0.1)=0.2。
- 4 与 4.4 的原始距离 0.4，互可达距离 max(0.8,0.4,0.4)=0.8。
- 0.3 与 4 的互可达距离为 3.7。

这使处于稀疏区域的点不容易仅靠一条短连接就显得密集。它不是把所有噪声“删除”，而是改变层次连接的权重。

可把主要过程理解成四步：

1. 根据核心距离构造互可达关系。
2. 通过最小生成树等结构保留不同距离尺度下的连接信息。
3. 形成密度层次，并根据 min_cluster_size 凝练为簇的生灭结构。
4. 按选择规则挑出最终非重叠分组，剩余点可标为噪声。

最小生成树是在保持所有点连通的树中，选择总边权最小者；这不是最近中心分类。密度层次常用 λ=1/距离 表达，λ 越大对应越密的尺度。

它探索的是固定距离、固定 min_samples 下的密度层次，不是探索所有可能特征或业务语义。

## 7. 持久的簇是什么意思

一个簇如果在较宽的密度尺度范围内保持，并且包含较多样本，其稳定性贡献可能较大。直观上可对簇中各点累积“从簇出现到点离开之间的 λ 区间长度”。

EOM（Excess of Mass）规则比较父簇与其后代的稳定性贡献，选择一组互不重叠的簇；leaf 更偏向选择凝练树的叶节点，往往提供更细分结果。

这属于算法在密度尺度上的稳定性，**不是独立重采样后结果稳定，也不是已验证的业务价值**。一个长期存在的数据采集偏差也可能形成稳定簇。

本例 HDBSCAN(min_cluster_size=3, min_samples=3, cluster_selection_method="eom") 得到两组，各 4 点，12 为噪声。本篇没有独立实现完整凝练树/EOM，也没有对其内部每个节点作逐步核验；脚本验证公开 API 和最终成员。

## 8. 两个“最小数量”不要混为一谈

| 参数 | 主要作用 | 易错点 |
| --- | --- | --- |
| min_samples | 核心距离使用的邻居数，影响密度保守程度 | 不是最终簇最小数量 |
| min_cluster_size | 层次凝练中可保留为簇的最低规模 | 不是邻域半径 |
| cluster_selection_method | eom 或 leaf 的簇选择方式 | 不代表业务层级名称 |
| cluster_selection_epsilon | 影响近距离簇合并的尺度设置 | 不是把整个算法改回一次 DBSCAN |
| allow_single_cluster | 是否允许选择一个整体簇 | 默认 False 不意味着数据一定有多群体 |

scikit-learn 的 min_samples=None 会使用 min_cluster_size。因此，若只调整 min_cluster_size，可能同时改变邻居数与最低簇规模。想单独研究一种作用，应显式固定另一参数。

跨库尤其小心：核验源码注明，scikit-learn 的 HDBSCAN min_samples 包含自身，而 scikit-learn-contrib/hdbscan 的约定不包含自身。迁移时，前者邻居数通常需要比后者加 1 来对齐这个含义。不能因此保证所有版本、其他参数和最终标签逐位一致；本篇没有安装或实跑第三方包。

## 9. probabilities_、噪声与无效输入

scikit-learn HDBSCAN 的 probabilities_ 是一维数组：每个点在**已分配簇中的成员强度**，关联它在该簇中持续存在的程度。

它不是 GMM 的 n×K 后验责任度矩阵，也不是“欺诈概率”或监督分类置信度；不要求所有点的值加起来为 1。本例 8 个非噪声点强度都为 1，仅反映这个简化数据上的计算结果。

标签含义：

| sklearn HDBSCAN 标签 | 含义 | 对应强度 |
| --- | --- | --- |
| 0 及以上 | 某个簇，编号任意 | 0 到 1 |
| −1 | 普通噪声 | 0 |
| −2 | 含无穷值的样本 | 0 |
| −3 | 含缺失值的样本 | NaN |

脚本另添加一个 inf 行、一个 NaN 行，核对后两类标签。不能把所有负数都当成同一种业务异常。如果用 labels >= 0 统计“覆盖率”，还应分别报告有效数据中的噪声比例和无效输入比例。

该无效行处理是特定实现行为，不代表其他库或 OPTICS 也接受相同输入。生产入口仍需明确字段和有限值协议。

## 10. 使用示例与应用边界

完整可离线运行代码：[density_scale_checks.py](examples/density_scale_checks.py)。

~~~python
from sklearn.cluster import OPTICS, HDBSCAN, cluster_optics_dbscan

# X 为 (样本数, 特征数) 数组
optics = OPTICS(
    min_samples=3, max_eps=8,
    cluster_method="xi", xi=0.05, min_cluster_size=3,
).fit(X)

labels = cluster_optics_dbscan(
    reachability=optics.reachability_,
    core_distances=optics.core_distances_,
    ordering=optics.ordering_,
    eps=1.0,
)

density_model = HDBSCAN(
    min_cluster_size=3,
    min_samples=3,
    cluster_selection_method="eom",
    copy=True,
).fit(X)
~~~

这两个 scikit-learn 类都没有原生 predict。fit_predict(new_X) 会在新数据上重新拟合，不是对旧分组的持续预测。第三方包可能有额外预测工具，但不能直接套到 scikit-learn 对象上；本篇未验证这类能力。

尺度、距离和维度仍决定结果。特别是高维稀疏文本，欧氏密度不一定符合语义；位置数据也不能把经纬度度数无条件当作米。需要采用合适距离与单位，并验证采样变化对分组的影响。

性能方面，本篇核验的 scikit-learn OPTICS 实现使用未处理集合中的搜索，没有采用原始算法的堆管理，文档注明 O(n²) 时间特征。HDBSCAN 的性能与所选邻居/树算法、距离及数据形状有关；不能仅凭算法名称承诺一定更快或内存只线性增长。本篇没有大规模性能基准。

评估至少报告：有效样本量、非噪声覆盖、簇大小分布、独立稳定性和业务效用。只对剩下的“容易分组点”计算很高的轮廓系数，而隐去大量噪声，会误导使用者。

## 11. 练习与答案

1. core(p)=0.2、core(q)=0.8、d(p,q)=0.4，两个可达概念是多少？  
   **答案：** 从 p 到 q 的候选 OPTICS 可达距离是 0.4，HDBSCAN 互可达距离是 0.8。

2. reachability 大于提取 eps，一定噪声吗？  
   **答案：** 不一定，核心距离满足条件时可启动新簇。需要结合核心距离与处理顺序。

3. 某成员强度为 1，可以理解为 100% 业务归类正确吗？  
   **答案：** 不能，这是模型内部的成员强度，不是业务标签校准或正确率。

4. 为何要显式设置 HDBSCAN 的 min_samples？  
   **答案：** 防止它随 min_cluster_size 的默认耦合一起变化，便于控制实验。

5. 低噪声比例就说明分组好么？  
   **答案：** 不说明，宽松规则也可能把无关点合并。要同时看分离、稳定性和业务结果。

## 12. 开源来源及验证记录

核验日期：2026-10-04。来源 [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)，固定提交 a442e4bb39551feb7b0af4c00075e2cb91cf9b77：

- [clustering.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/clustering.rst)：OPTICS、HDBSCAN 机制与算法比较。
- [_optics.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/cluster/_optics.py)：顺序索引、提取 API、xi 和复杂度说明。
- [hdbscan.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/cluster/_hdbscan/hdbscan.py)：参数、簇选择、成员强度、无效标签及跨库邻居约定。
- [COPYING](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)：BSD 3-Clause；Copyright (c) 2007-2026 The scikit-learn developers。

中文解释和脚本独立编写，不是官方逐字翻译。部分概述中的简化描述以参数文档、实现与实跑边界为准；本文不把单一可达高度机械等同于噪声。与来源项目无隶属关系。

环境：Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、scikit-learn 1.8.0。来源提交与安装版本不同，只声明实际使用 API 的实跑结果。

已核验：核心距离手算、互可达矩阵对称与三个值、OPTICS 排序置换、前驱与可达值、两个半径提取的成员、HDBSCAN 两簇及噪声、成员强度范围、inf/NaN 标签和无 predict。输出中的 null 仅是脚本用来表示种子无穷可达距离的 JSON 编码，不是模型缺失值。

~~~bash
python knowledge/unsupervised-learning/examples/density_scale_checks.py
~~~

这是九点机制算例，没有完整算法独立重实现、真实业务效果、跨库一致性或大型性能的验证结论。

[返回专题目录](README.md)
