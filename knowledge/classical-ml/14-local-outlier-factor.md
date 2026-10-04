# 14｜LOF：局部密度、新颖性检测与训练样本接口

> 先修：[近邻模型](09-nearest-neighbors.md)、[异常检测与 Isolation Forest](13-isolation-forest.md)。目标：读懂局部密度，正确区分 LOF 的两种使用方式。

## 1. 离中心远，不一定异常

一个城市有高密度商圈，也有分散的正常郊区门店。只看距离全局中心的远近，可能误伤整个郊区。

LOF 比较“这个点的局部密度”与“邻居的局部密度”。稀疏区域内的点如果邻居同样稀疏，未必异常；若它明显比邻居更稀疏，就更值得关注。

这并不表示 LOF 对所有密度差异都稳健。邻居数量、群体规模和特征距离决定了“局部”范围；小群体可能被更大的群体吞进邻域。

## 2. 邻居密度为什么需要 reachability distance？

直接用点到邻居的距离算密度，局部极近点可能让密度剧烈波动。LOF 用可达距离的构造来降低这种敏感性：

reach_dist_k(p,o)=max(k_distance(o), distance(p,o))。

k_distance(o) 是邻居 o 到其第 k 个近邻的距离，不是查询点 p 的第 k 个距离。局部可达密度 lrd(p) 约为平均可达距离的倒数。

LOF(p)=邻居 lrd 的平均值 / lrd(p)。

理论 LOF 约为 1 表示与邻域密度相似；明显大于 1 表示自身密度低于邻居。这里解释主要机制；并列距离、近邻集合定义与数值稳定项会影响实现细节。

## 3. 一个能手算的四点例子

一维点为 0、1、2、10，k=2，查询训练点时不把自身计入近邻。

第 k 距离为 [2,1,2,9]。点 10 的邻居是 2 和 1，两条可达距离为 max(2,8)=8、max(1,9)=9，所以 lrd(10)=1/8.5=2/17。

点 2 的局部可达密度为 2/3，点 1 为 1/2。点 10 的 LOF 为 ((2/3+1/2)/2)/(2/17)=119/24≈4.9583。

前三点的 LOF 分别约为 [0.875,1.3333,0.875]。位于中间的点不一定恰好为 1；LOF 是相对密度量，不是“距离最近就必然最正常”的简单公式。

## 4. scikit-learn 存的是负 LOF

negative_outlier_factor_ 记录训练样本的负局部异常因子，正常值常在 −1 附近，越负通常越异常。因此理论 LOF=4.96 在该属性里约为 −4.96。

不要与其他模型分数或概率混用。不同 n_neighbors、尺度、训练样本和版本会改变分数。offset_ 用于将分数转成异常标签，设定浮点 contamination 时通常按训练分数分位数确定。

## 5. 可运行：手算与训练属性核对

```python
import numpy as np
from sklearn.neighbors import LocalOutlierFactor

X = np.array([[0.], [1.], [2.], [10.]])
lof = LocalOutlierFactor(n_neighbors=2, contamination=0.25)
labels = lof.fit_predict(X)
expected_lof = np.array([7/8, 4/3, 7/8, 119/24])
assert np.allclose(-lof.negative_outlier_factor_, expected_lof, atol=1e-7)
assert labels[-1] == -1
assert np.all(labels[:-1] == 1)
print("theoretical LOF", -lof.negative_outlier_factor_)
print("LOF training labels", labels)
```

模型有数值稳定处理，结果可能略有浮点差异。这个四点例子只能验证机制，不适合选择业务阈值或证明泛化。

## 6. 两种模式，接口有意不同

| 操作 | 默认 novelty=False | novelty=True |
| --- | --- | --- |
| fit_predict(X) | 对拟合数据检测离群点 | 不使用此接口 |
| negative_outlier_factor_ | 训练样本负 LOF | 训练样本负 LOF |
| predict(X_new) | 不提供此新样本预测方式 | 仅用于新、未见过的数据 |
| score_samples / decision_function | 训练分数应查属性 | 仅用于新、未见过的数据 |

默认 LOF 是针对当前样本批次的离群检测。需要后续新记录预测时，应在拟合前显式设置 novelty=True。

不能先默认 fit_predict，再假设以后能直接 predict；也不能把 novelty=True 的模型拿训练 X 去 predict，然后与默认 fit_predict 的结果比较，宣称模型不稳定。两者查询邻域的语义不同，官方明确要求新颖性接口只用于未见样本。

## 7. 可运行：训练正常参照，预测独立新点

```python
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

rng_lof = np.random.default_rng(17)
X_reference = rng_lof.normal(0, 0.3, size=(200, 2))
X_new = np.array([[0.02, -0.03], [4., 4.]])
pipe = make_pipeline(
    StandardScaler(),
    LocalOutlierFactor(n_neighbors=20, contamination=0.05, novelty=True)
)
pipe.fit(X_reference)
model = pipe.named_steps["localoutlierfactor"]
X_new_scaled = pipe.named_steps["standardscaler"].transform(X_new)
score = model.score_samples(X_new_scaled)
decision = model.decision_function(X_new_scaled)
pred = pipe.predict(X_new)
assert np.allclose(decision, score - model.offset_)
assert np.array_equal(pred, [1, -1])
assert score[1] < score[0]
print("LOF new score/decision/predict", score, decision, pred)
# 训练样本只查看已计算属性，不调用新颖性 predict(X_reference)。
print("LOF reference factor shape", model.negative_outlier_factor_.shape)
```

缩放器只在正常参照上学习，后续新点使用同一转换。示例两个新点被特意设得很容易区分，不代表真实业务准确率。

训练参照应覆盖正常的营业类型、时间和区域。新商圈、新节假日若未覆盖，可能被当成新颖点；模型不自动判断这种变化是否有害。

## 8. n_neighbors 控制局部尺度

小 k 关注更小邻域，可能对噪声、重复点和小群体敏感；大 k 跨越更广范围，可能让局部模式被其他群体影响。

k 不应由最终测试反复挑选。训练集过小可能触发有效近邻数量调整，应检查 n_neighbors_ 和数据规模。参考文档中的默认或经验数字，不等于自己的数据也具有相同密度结构。

重复点可能产生很小的可达距离和很大的密度。数值稳定处理可避免简单除零，却不能自动区分“重复采集”与“真实重复状态”。

## 9. 特征几何与群体参照

LOF 基于近邻距离，面积、人口和比例尺度差异可能改变邻域。合理缩放通常有帮助，但不同列是否同等重要仍需业务判断。

无序 ID、坐标单位与编码问题可直接破坏邻域语义。地理检测还应明确城市、坐标体系与距离单位。不同城市门店混在一起，不一定拥有一个合理的公共“正常密度”。

如果先使用全体数据拟合降维或缩放，再划训练参照与未来测试，仍可能泄漏。无监督预处理同样要遵守评估边界。

## 10. 密集异常群体可能互相“证明正常”

多个异常点彼此很近，而且足够多时，可能成为彼此邻居，局部密度相似。此时 LOF 未必将整个群体判异常。

在新颖性场景，模型相对于已有正常参照评价新点；若新群体远离正常参照，可以有不同结果。但一旦把新群体持续混入训练参照，参照含义也会改变。

所以批次离群检测与持续新颖性检测的结果不能无条件互换。业务应记录哪些数据进入参照、什么时候更新、是否经过审阅。

## 11. 与 Isolation Forest 怎样选择？

Isolation Forest 依靠随机隔离，LOF 依靠局部距离和密度。两者可能关注不同样本，并没有通用胜者。

比较时固定特征、数据边界、标签和预算；异常分数方向应统一。分别报告排名质量、阈值误报、少数事件召回、预测成本和人工审阅命中。

近邻搜索在大样本或高维上可能变贵，是否使用某种索引需结合维度、距离和实现支持。不能因为 LOF 只调了一个邻居参数，就认为预测成本可忽略。

## 12. 练习与答案

1. 远离全局中心就一定 LOF 很大吗？答：不，它还比较局部邻居密度。
2. negative_outlier_factor_ 越负通常越正常吗？答：相反，通常越异常。
3. novelty=True 后可对训练 X 调 predict 来验证训练离群点吗？答：不，应查看训练属性，预测接口只用新样本。
4. 四点例子里点 10 的理论 LOF 是多少？答：119/24≈4.9583。
5. 密集异常群体一定被 LOF 找到吗？答：不，它们可能形成相似局部密度。

## 来源与验证

核验日期：2026-10-04。基于 [scikit-learn 官方开源文档 outlier_detection.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/outlier_detection.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、手算、业务延伸和代码独立编写，非官方逐字翻译。示例在 scikit-learn 1.8.0 实跑；来源主分支与安装版本不完全相同。

[返回专题目录](README.md)
