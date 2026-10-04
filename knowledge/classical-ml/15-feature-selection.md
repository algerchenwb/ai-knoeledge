# 15｜特征选择：哪些字段值得留，怎样避免筛选泄漏？

> 目标：理解过滤法、模型相关方法和包装法，区分“当前模型不用”与“字段永远没用”。

## 1. 字段多，不等于信息多

随机噪声、重复字段、无意义 ID 和未来才产生的字段，可能增加训练成本、影响距离、造成过拟合或泄漏。

预测下月门店客流时，已知面积和历史人口可能可用，下月末才汇总的实际到店人数不应作为输入。再高的相关性，也不能让未来字段变成合法输入。

选择特征也要考虑采集费用、接口延迟、覆盖率与上线稳定性。分数略高但依赖经常缺失的字段，未必是可部署的方案。

## 2. 特征选择与 PCA 的区别

特征选择保留原列子集；PCA 通常生成原列的线性组合。二者都减少维度，但部署依赖和解释方式不同。

保留两个主成分，可能仍需要采集全部原字段。保留两个原字段，才可能减少实际输入依赖。高方差不是自动的高预测价值，低方差也不是自动的无用。

## 3. 三类方法

| 方法 | 例子 | 选择依据 | 限制 |
| --- | --- | --- | --- |
| 过滤法 | VarianceThreshold、SelectKBest | 列统计或每列与标签的关系 | 单变量方法可能漏掉交互 |
| 模型相关方法 | L1、SelectFromModel | 当前模型的系数或重要性 | 依赖尺度、模型和正则化 |
| 包装法 | RFE、顺序选择 | 反复训练和评估子集 | 昂贵，搜索分数可能乐观 |

没有通用胜者。先建立全字段基线，使用同一数据边界和指标比较。

## 4. 方差筛选：删除常数列的机制

VarianceThreshold 默认删除训练数据中的零方差列。二值字段的 1 占比为 p 时，方差为 p(1−p)。

稀有状态 p=0.01 时方差仅 0.0099，却可能很重要。高阈值删除低方差列不等于自动删除无用字段。

连续字段的方差依赖单位：元改为分，方差放大一万倍。标准化后再按方差筛选会改变原目的，因为非恒定列通常被缩放到约单位方差。

```python
import numpy as np
from sklearn.feature_selection import VarianceThreshold
X = np.array([[1.,0.,0.], [1.,1.,0.], [1.,0.,1.], [1.,1.,1.]])
sel = VarianceThreshold().fit(X)
assert sel.get_support().tolist() == [False, True, True]
assert np.allclose(sel.variances_, [0., 0.25, 0.25])
assert sel.transform(X).shape == (4, 2)
print("variance/support", sel.variances_, sel.get_support())
```

字段训练中恒定、上线后变化，并不意味着模型已学会处理这种变化。默认规则仅反映当前训练样本。

## 5. 单变量筛选与 XOR

SelectKBest 分别给每列打分，再保留最高的 k 列。分类有 f_classif、chi2、mutual_info_classif，回归有对应回归函数。评分任务必须匹配，chi2 应使用符合要求的非负特征，例如计数，不能直接套在中心化负值上。

F 检验主要捕捉相应均值或线性关联结构；互信息能捕捉更多非线性关系，但仍逐列评价，有限样本估计也有噪声。

XOR 两列单独不提供标签信息，合起来却能决定标签。即使单列互信息估计完全准确，也不能自动发现这种纯交互。

```python
import numpy as np
from sklearn.feature_selection import f_classif
from sklearn.tree import DecisionTreeClassifier
X_xor = np.array([[0.,0.], [0.,1.], [1.,0.], [1.,1.]])
y_xor = np.array([0,1,1,0])
scores, p_values = f_classif(X_xor, y_xor)
assert np.allclose(scores, [0.,0.])
assert np.allclose(p_values, [1.,1.])
tree = DecisionTreeClassifier(random_state=42).fit(X_xor, y_xor)
assert np.array_equal(tree.predict(X_xor), y_xor)
print("XOR F/p", scores, p_values)
```

树全对只验证四点拟合，不证明泛化优秀；例子说明单变量筛选可能丢失联合信息。

## 6. L1、RFE 与顺序选择

L1 可以将系数压到零，SelectFromModel 据系数或重要性筛选。但零系数只代表当前模型与正则化条件下未利用它，不证明永远无用。相关列可能互相替代，特征单位也影响系数大小。

RFE 反复拟合并移除较低重要性列，RFECV 还用交叉验证选数量。顺序前向选择逐步加列，后向选择逐步删列；贪心路径不保证找到全局最优子集。

这些过程会消耗许多次拟合。内部交叉验证用于搜索，内部最高分不应直接当作独立最终性能。

prefit=True 使用已拟合模型。如果其拟合数据曾包含验证标签，再包装进 Pipeline 也不能逆转泄漏。应重新限定所有拟合步骤的数据。

## 7. 可运行：训练折内选 k 与模型参数

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score

X, y = make_classification(
    n_samples=600, n_features=12, n_informative=3, n_redundant=0,
    n_clusters_per_class=1, shuffle=False, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
pipe = Pipeline([
    ("scale", StandardScaler()),
    ("select", SelectKBest(f_classif)),
    ("model", LogisticRegression(max_iter=1000))
])
search = GridSearchCV(
    pipe, {"select__k":[3,6,"all"], "model__C":[0.1,1.]},
    scoring="balanced_accuracy",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
selected = search.best_estimator_.named_steps["select"].get_support(indices=True)
print("selected columns", selected)
print("selection params/CV", search.best_params_, search.best_score_)
print("selection final test",
      balanced_accuracy_score(y_test, search.predict(X_test)))
```

缩放器和筛选器每折独立拟合；k="all" 包含不筛选的候选。shuffle=False 只用于教学，不意味着真实任务知道信息列的位置。

若根据测试结果改字段、改 k 再报告同一测试，它已参与决策。应另留最终数据或使用嵌套验证。[评估基础](../ml-evaluation/README.md)解释了这种边界。

## 8. 无监督步骤也要隔离

先在全部数据拟合方差阈值、相关性聚类或缩放器，再交叉验证，仍使验证分布参与了学习。监督筛选还直接利用标签，风险更明显。

包装法的内部 CV 也需要检查预处理层级：若进入内部 CV 前已经用整个开发集拟合缩放，内部验证没有被完整隔离。不是只要某处写了 CV 就自动安全。

## 9. 选择稳定性与部署协议

高维小样本会产生偶然关联。可记录各折保留频率，但相关列互相替代会让单列频率不稳定；应结合特征组和预测表现解释。

多个 one-hot 列来自同一原字段，删除部分列不一定减少采集费用。部署应保存字段名、顺序、类型、编码和选择掩码，不能只有“保留第 2、5 列”。

对于门店重复记录、未来预测，应采用分组或时间协议；随机切分不自动检验新门店泛化。

## 10. 练习与答案

1. 低方差字段一定没用吗？答：不，稀有重要状态也可能低方差。
2. XOR 两列单独无信号，联合也无信号吗？答：不，联合可决定标签。
3. 零系数证明没有业务价值吗？答：不，只反映当前模型条件。
4. 按测试重要性删列是模型选择吗？答：是，应重新保留独立最终评估。
5. Pipeline 能修复预先全数据筛选吗？答：不能，应将学习步骤真正放在训练边界内。

## 来源与验证

核验日期：2026-10-04。基于 [scikit-learn 官方开源文档 feature_selection.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/feature_selection.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、代码与业务延伸独立编写，非官方逐字翻译。示例使用 scikit-learn 1.8.0 核验；固定来源主分支与安装版本不完全相同。

[返回目录](README.md)
