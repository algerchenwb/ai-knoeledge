# 13｜异常检测与 Isolation Forest：容易被隔离，意味着什么？

> 目标：理解异常检测任务、随机隔离机制、异常分数与阈值；不把“少见”直接认定为“错误”。

## 1. 异常首先需要参照系

一家门店夜间客流突然升高，可能是采集故障，也可能是活动、节假日或营业时间变化。模型能指出“和参照样本不一样”，不能凭空确定是哪一种原因。

输入特征定义了比较对象。用原始客流，容易把大商场标成异常；用同业态、同时间段的相对变化，比较的是另一种现象。异常检测并没有免除业务建模。

点异常指单条记录偏离常态；上下文异常指在某个时间或群体条件下异常；集体异常指一段记录的联合模式异常。这些是任务设计概念，不代表把数据交给一个通用接口就会全部识别。

## 2. Outlier detection 与 novelty detection

| 任务 | 训练数据 | 要回答的问题 |
| --- | --- | --- |
| 离群点检测 | 未标注数据，可能混有异常 | 当前这一批中哪些记录偏离主要结构？ |
| 新颖性检测 | 以可信正常数据作为参照 | 后续新记录是否偏离正常参照？ |
| 监督异常分类 | 有正常/异常标签 | 根据已标注类型预测新记录 |

无监督不意味着不用验证；监督分类也不能保证覆盖从未出现过的异常类型。极不平衡监督任务可先读[类别不平衡](12-class-imbalance.md)。

正常参照严重受污染时，模型可能把异常学成正常。异常若形成一个较大、密集的群体，也可能不像单个孤立点；不能把稀疏性假设当作“所有异常都稀疏”的事实。

## 3. Isolation Forest 随机切分的直觉

一维数据集中在 0 附近，另有一个点位于 10。随机选特征，再在该特征当前范围内随机选切分值。远离主体的点经常很快就能单独落进一个分支，主体内部的点往往需要更多次切分才能分开。

从根走到叶的路径越短，越容易被隔离。模型使用多棵随机树的路径信息形成分数，减轻单棵树的随机性。

这是统计倾向，不是每棵树都必然更早隔离同一个异常。重复点、复杂分布和特征表示会改变结果。

## 4. 与随机森林分类的区别

随机森林分类用标签寻找有利分裂，并聚合类别预测。Isolation Forest 不靠异常标签来学习这类分裂；随机选择特征和切分位置，用隔离过程生成异常相关分数。

实现中使用树结构或某种回归树组件，不等于业务目标是预测一个连续标签。应看算法目标，不能仅从内部类名推断任务。

n_estimators 控制树数；max_samples 控制每棵树使用的样本规模；random_state 控制随机过程。更多树通常增加成本、降低随机波动，但不保证发现所有业务异常。

## 5. scikit-learn 分数方向特别容易看反

在本篇 IsolationForest 接口中：

- score_samples：数值越低，越异常。
- decision_function=score_samples−offset_。
- predict：−1 表示异常，+1 表示正常；负 decision_function 判异常，非负判正常。

异常分数不是概率，也不是监督分类里的正类 1。若评估数据定义“异常=1”，需要用 −score_samples 作为越大越异常的排序分数，并显式转换硬标签。

同一数值不能直接跨模型、特征版本或重新训练的参照集比较。将 −0.6 报成“60% 欺诈概率”没有依据。

## 6. contamination 主要控制判定阈值

给定浮点 contamination，模型依据训练分数分位数设置阈值。它不是自动发现真实异常比例，更不是对未来异常比例的保证。

固定其他设置与随机种子，改变 contamination 可以改变 offset_ 和硬标签，而不改变 IsolationForest 的原始隔离分数。浮点阈值、并列分数和样本数量可能让最终异常条数不恰好等于某个百分比。

contamination="auto" 采用算法约定的阈值；不是“自动精确估计业务异常占比”。如果业务每天只能审核 100 条，可以考虑排名队列，但排名队列也不证明这 100 条全是真异常。

## 7. 可运行：阈值变了，原始分数不变

```python
import numpy as np
from sklearn.ensemble import IsolationForest

rng = np.random.default_rng(42)
X_train = np.vstack([
    rng.normal(0, 0.4, size=(300, 2)),
    rng.uniform(3, 5, size=(15, 2))
])
X_query = np.array([[0., 0.], [4., 4.]])
models = [
    IsolationForest(n_estimators=100, max_samples=128,
                    contamination=c, random_state=42).fit(X_train)
    for c in [0.05, 0.2]
]
scores = [m.score_samples(X_query) for m in models]
assert np.allclose(scores[0], scores[1])
for m in models:
    d = m.decision_function(X_query)
    assert np.allclose(d, m.score_samples(X_query) - m.offset_)
    assert np.array_equal(m.predict(X_query), np.where(d < 0, -1, 1))
    print("IF offset/query score/predict",
          m.offset_, m.score_samples(X_query), m.predict(X_query))
    print("IF train flagged", np.sum(m.predict(X_train) == -1))
```

这不是异常比例的真实估计。训练中加入的远处点是人为构造的结构，模型把它们识别为异常也不代表已解决实际业务异常识别。

## 8. 可运行：独立正常校验集定阈值，最终测试只评估

```python
import numpy as np
from sklearn.metrics import average_precision_score, precision_score, recall_score

# 继续使用上一段已拟合的 models[0]。
model = models[0]
X_normal_cal = rng.normal(0, 0.4, size=(200, 2))
cal_scores = model.score_samples(X_normal_cal)
threshold = np.quantile(cal_scores, 0.05)
# 独立新样本；教学异常被故意放得很远。
X_test = np.vstack([
    rng.normal(0, 0.4, size=(400, 2)),
    rng.uniform(3, 5, size=(20, 2))
])
y_test = np.r_[np.zeros(400, dtype=int), np.ones(20, dtype=int)]
test_scores = model.score_samples(X_test)
flag = test_scores < threshold
assert test_scores.shape == y_test.shape
print("IF chosen threshold", threshold)
print("IF calibration flag fraction", np.mean(cal_scores < threshold))
print("IF test AP", average_precision_score(y_test, -test_scores))
print("IF test Precision/Recall",
      precision_score(y_test, flag, zero_division=0),
      recall_score(y_test, flag))
print("IF test normal FPR", np.mean(flag[y_test == 0]))
```

分位数按独立正常样本的分布设置，仅是经验阈值；校验集约 5% 告警不保证未来正常记录恰好 5% 告警。需要考虑样本量、时间变化与群体变化。

示例先决定 5% 分位数再查看最终测试；不能反复选择分位数使这个测试最好。代码没有提供复杂漂移场景的风险保证，也没有经过真实业务验证。

## 9. 如何评价无标签模型？

有可信标签时，使用异常方向正确的 AP/ROC-AUC、阈值 Precision/Recall、正常误报率与告警数量。若测试异常被刻意放得极远，分数容易漂亮；应说明合成方式，不把它当上线性能。

没有标签时，人工审阅、历史回放、事件记录和规则基线仍可提供证据。直接把分数最高的样本定义为真异常，再报告模型找到了它们，会形成循环论证。

只审核告警记录会遗漏未告警中的异常，无法据此完整估算 Recall。可在合理范围内加入未告警样本的抽样审阅，并记录抽样协议与标签不确定性。

## 10. 业务输入与上线边界

异常往往来自单位变化、缺失编码、采集迟到或正常节假日。应先建立字段质量检查与时间基线。

Isolation Forest 的随机轴向切分与 LOF 的距离几何不同，不能把“所有异常算法都必须同样缩放”当成结论。仍应检查表示、无意义 ID、异常缺失值和混合群体。

若目标是检测未来，模型与任何预处理应只使用此前数据；阈值的确定也要遵守时间边界。更新参照模型后，分数和阈值通常应重新验证。异常输出适合作为调查线索，不自动构成删除数据或认定违规的理由。

## 11. 练习与答案

1. 异常=1 是 IsolationForest 的默认标签吗？答：不是，默认异常为 −1。
2. 分数越大一定越异常吗？答：不是，本篇 score_samples 越低越异常。
3. contamination=0.05 保证未来异常占 5% 吗？答：不，它主要设置训练分数阈值。
4. 当前模型分数 −0.7 能解释成 70% 异常概率吗？答：不能。
5. 没有标签还要评估吗？答：需要，至少通过独立审阅、回放和业务证据检验。

## 来源与验证

核验日期：2026-10-04。基于 [scikit-learn 官方开源文档 outlier_detection.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/outlier_detection.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、手算、业务延伸和代码独立编写，非官方逐字翻译。示例在 scikit-learn 1.8.0 实跑；来源主分支与安装版本不完全相同。

[返回专题目录](README.md)
