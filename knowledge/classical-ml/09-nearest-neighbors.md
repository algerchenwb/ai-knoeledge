# 09｜近邻模型：距离、投票与“找相似样本”的边界

> 目标：理解 KNN 分类和回归，知道距离如何改变结果，以及怎样避免把训练记忆误认为泛化。

## 1. 不先写公式，先找邻居

假设你要判断一家新门店属于“高客流”还是“低客流”。KNN 的做法是：在训练门店中找出特征最接近的 k 家，查看它们的标签，再投票。

这里的“接近”不是默认地理距离。输入若是面积、周边人口、营业时长，距离衡量的是这些特征的差异；输入若是坐标，才是在某种坐标度量下的接近。

KNN 是监督学习：邻居的标签用于预测。K-means 是无监督聚类：学习中心、分配簇。名字都有 K，不代表它们是一回事。

## 2. 分类投票与回归平均

设一维训练坐标为 0、2、5，分类标签为 A、B、B，查询位置为 0.5。距离分别为 0.5、1.5、4.5。

取 k=3：
- 均匀投票：A 一票，B 两票，预测 B。
- 按距离倒数投票：A 权重 2；B 权重 2/3+2/9=8/9，预测 A。
- 归一化后的 A 权重比例为 2/(2+8/9)=9/13≈0.6923。

如果标签改为连续数值 10、20、50，均匀回归预测为 80/3≈26.6667；距离加权预测为 (10×2+20×2/3+50×2/9)/(2+2/3+2/9)=200/13≈15.3846。

投票和平均的区别来自目标类型。不能把“客流量 100”当成第 100 类，再声称仍在做回归。

## 3. 可运行：同一邻居，不同权重

```python
import numpy as np
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor

X = np.array([[0.], [2.], [5.]])
query = [[0.5]]
labels = np.array(["A", "B", "B"])
uniform = KNeighborsClassifier(n_neighbors=3, weights="uniform").fit(X, labels)
weighted = KNeighborsClassifier(n_neighbors=3, weights="distance").fit(X, labels)
assert uniform.predict(query)[0] == "B"
assert weighted.predict(query)[0] == "A"
assert np.allclose(weighted.predict_proba(query), [[9/13, 4/13]])
print("classes", weighted.classes_, "weighted vote", weighted.predict_proba(query))

values = [10., 20., 50.]
ru = KNeighborsRegressor(n_neighbors=3).fit(X, values)
rw = KNeighborsRegressor(n_neighbors=3, weights="distance").fit(X, values)
assert np.allclose(ru.predict(query), [80/3])
assert np.allclose(rw.predict(query), [200/13])
print("regression", ru.predict(query), rw.predict(query))
```

此处 predict_proba 表示局部标签权重比例，不自动成为校准良好的业务概率。三票全是 B，并不证明新门店有 100% 概率属于 B。

查询恰好与训练点重合时距离为零，不能直接执行除零；scikit-learn 对零距离邻居有专门处理。重复点若标签矛盾，也无法靠距离凭空解决矛盾。

## 4. k 是平滑程度，不是准确率旋钮

k=1 只参考最近记录，通常对局部变化和噪声敏感。k 增大让更多邻居参与，边界更平滑，却可能抹掉少数类或局部结构。

k 太大时，稀疏区域也被迫找远处邻居；这与“样本足够相似”不是同一个条件。RadiusNeighbors 用半径限制邻居范围，但可能找不到任何邻居，必须明确未覆盖输入如何处理。

选 k 应在开发数据上比较，而不是反复查看最终测试集。还要确保每个交叉验证训练折的样本数不少于候选 k。

## 5. 距离定义就是模型定义的一部分

欧氏距离为 sqrt(Σ(xᵢ−zᵢ)²)；曼哈顿距离为 Σ|xᵢ−zᵢ|。默认 Minkowski 距离的 p=2 对应欧氏距离，p=1 对应曼哈顿距离。

面积单位从平方米变成平方厘米，数字会放大一万倍，可能完全改变邻居。StandardScaler 可以减轻尺度支配，但“每列同等重要”本身也是假设，并不自动反映业务价值。

类别编码 1、2、3 会在距离中产生顺序与大小关系。对无序业态应考虑合理编码，不能把便利店编码 1、商场编码 9，就理解为相距八个单位。

经纬度单位是角度，不是米。地理查询要结合坐标体系、距离公式与单位；Haversine 通常使用弧度并乘合适地球半径。GCJ-02 与 WGS84 混用也不会因为选择 KNN 自动修复。此处是工程延伸，不是对地理精度的保证。

## 6. 可运行：在训练折里缩放与选 k

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import balanced_accuracy_score

X, y = load_iris(return_X_y=True)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), KNeighborsClassifier()),
    {"kneighborsclassifier__n_neighbors": [3, 5, 9],
     "kneighborsclassifier__weights": ["uniform", "distance"]},
    scoring="balanced_accuracy",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
print("KNN chosen", search.best_params_)
print("KNN CV", search.best_score_)
print("KNN final test",
      balanced_accuracy_score(y_test, search.predict(X_test)))
```

这只是公开教学数据的流程演示。若预测未来客流，应采用时间验证；若目标是未见过的门店，应检查门店分组。随机切分不能代替具体业务协议。

## 7. 为什么训练准确率特别容易误导？

如果 k=1，又拿同一批训练数据去预测，样本的最近邻可能就是自己，距离为零，训练结果因此非常好。这不代表新数据预测成功。

显式传入训练 X 查询邻居，与某些接口不传 X 时排除自身的行为不同。不要随意假设两个调用产生完全相同邻居集合。

边界上第 k 与第 k+1 个邻居等距且标签不同，选择可能受训练行顺序影响。取奇数 k 也不能消除多分类平票或距离边界歧义。验收时应关注重复记录和等距样本。

## 8. 高维空间与检索成本

“非参数”不等于“没有超参数”或“不占内存”。KNN 仍要保存训练实例或其索引，预测时搜索邻居。

对一个 D 维查询、N 个训练样本，直接距离扫描通常需要 O(ND) 工作；Q 个查询约 O(QND)，实际实现会分块、向量化或用索引。KDTree、BallTree 在适合的维度与几何下能加速，但高维时可能失去优势，不能承诺永远是 O(log N)。

维度增加时，噪声列和距离集中会影响“近”的意义。先检查特征质量，必要时在训练折内做特征选择或降维；不要直接添加大量无关字段。

## 9. KNN 与向量检索有什么关系？

共同点是寻找相近向量；差异在于后续任务。NearestNeighbors 可以只返回索引和距离；KNN 分类还要聚合邻居标签；RAG 检索通常返回文档，再由其他过程组织答案。

近似最近邻索引可以用更低成本换取部分召回损失，不能当成精确 KNN 的结果保证。检索召回率、分类指标与生成答案质量是不同指标，应分别评估。

业务延伸：老门店样本会因环境变化失效，KNN 不会自动知道哪些记录已经过时。需要定义样本更新、删除、有效期及重新评估策略。

## 10. 练习与答案

1. KNN 的 k 与 K-means 的 k 含义相同吗？答：前者是邻居数量，后者是簇数量。
2. 三个邻居两票 B，一票 A，距离加权后一定预测 B 吗？答：不一定，A 若更近可能权重更大。
3. 1-NN 训练全对能证明泛化优秀吗？答：不能，样本可能找到了自己。
4. 50 个特征里新增 500 个随机噪声列一定有益吗？答：不一定，距离可能被噪声支配。
5. 不同门店反复出现的记录应怎样验证？答：根据目标使用分组、时间或组合约束，避免把同门店记忆当成新门店泛化。

## 来源与验证

核验日期：2026-10-04。主要来源为 [scikit-learn 官方开源文档 neighbors.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/neighbors.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、业务例子与代码独立编写，非官方逐字翻译。配套代码使用 scikit-learn 1.8.0 实跑；来源主分支与安装版本不完全相同。

[返回专题目录](README.md)
