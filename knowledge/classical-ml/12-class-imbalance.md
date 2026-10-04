# 12｜类别不平衡：少数类、权重与重采样

> 目标：理解“99% 准确率”为什么可能毫无帮助，区分类别权重、阈值与采样，并把验证保留在真实分布上。

## 1. 先定义少数类为什么重要

一万条记录中 100 条是正类，全部预测负类，准确率已有 99%，但正类召回为零。如果目标是识别少数异常门店，这样的模型可能无法完成任务。

类别比例不均不自动意味着必须采样到 1:1。先确认目标：提高正类召回、减少误报、提高排序，还是给人工审核排队？不同目标需要不同指标与决策协议。

标签噪声同样重要。少数类中若包含大量误标，提高其权重或复制它们可能放大错误，而不是解决信息缺失。

## 2. 基础发生率改变 Precision

设真阳性率 TPR=0.8、假阳性率 FPR=0.05，正类比例 π=0.01，则：

Precision=(TPR×π)/(TPR×π+FPR×(1−π))
=0.008/(0.008+0.0495)≈0.1391。

一万条记录中，100 正类命中 80；9900 负类误报 495；总报正 575 条，只有约 13.9% 是真正正类。

如果把评估集改成正负各半，在相同 TPR/FPR 下 Precision 变成 0.8/(0.8+0.05)≈0.9412。并非模型突然更强，而是评估群体发生率改变。

```python
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score
from sklearn.utils.class_weight import compute_class_weight

y = np.r_[np.ones(100, dtype=int), np.zeros(9900, dtype=int)]
pred = np.zeros_like(y)
pred[:80] = 1
pred[100:595] = 1
assert np.isclose(precision_score(y, pred), 80/575)
all_negative = np.zeros_like(y)
assert np.isclose(accuracy_score(y, all_negative), 0.99)
assert np.isclose(balanced_accuracy_score(y, all_negative), 0.5)
weights = compute_class_weight("balanced", classes=np.array([0, 1]), y=y)
assert np.allclose(weights, [10000/(2*9900), 50])
print("precision", precision_score(y, pred), "class weights", weights)
```

这里假设 TPR/FPR 不随分布变化。真实业务中数据条件分布也可能变化，不能只调整比例就保证上线效果。

## 3. 指标应对应实际决策

| 问题 | 可观察指标 | 注意事项 |
| --- | --- | --- |
| 少数类漏得多不多 | Recall 与 FN 数 | 同时报告误报，不能只追求 Recall=1 |
| 交给人工的记录有多准 | Precision 与 FP 数 | 随发生率与阈值变化 |
| 各类是否都覆盖 | Balanced accuracy、每类指标 | 类平均不等于实际经济成本 |
| 正类排序效果 | PR 曲线、Average Precision | AP 与梯形积分 PR-AUC 不是同一个计算 |
| 审核队列上限 | Precision@K、Recall@K | K 应反映真实容量 |
| 是否值得执行行动 | 总成本或效益 | 必须说明成本单位与假设 |

ROC-AUC 可以作为排序指标，但少数类场景应同时看具体误报数量。低 FPR 乘上很大的负类基数，仍可能产生大量误报。

分层切分可以保留大致比例，却不自动解决门店重复或时间泄漏。极少正类时，某些折可能缺少正类，需要检查每折计数，不能只增加折数。

## 4. 三类办法改变不同环节

类别权重改变训练损失中各类的贡献；改变阈值调整已训练模型的决策；重采样改变用于拟合的样本分布。

它们可以组合，但不是完全等价。改变权重可能影响参数、正则化相对强度和排序；阈值变化通常不改原始分数；复制样本可能改变训练量与实现细节。

balanced 常见权重为 w_c=N/(K×N_c)。在一万条、100 正类、9900 负类的例子中，正类权重 50，负类约 0.5051。两类总权重都约 5000。

这个公式是类别频率启发式，不是“误报和漏报真实成本”的测量。还要检查类权重与 sample_weight 是否共同生效，避免无意叠加。

## 5. 可运行：训练折内比较类别权重

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score

X, y = make_classification(
    n_samples=1600, n_features=10, n_informative=5,
    n_redundant=2, weights=[0.95, 0.05], flip_y=0.01, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    {"logisticregression__class_weight": [None, "balanced"],
     "logisticregression__C": [0.1, 1.]},
    scoring="average_precision",
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
)
search.fit(X_dev, y_dev)
p = search.predict_proba(X_test)[:, 1]  # 此例 classes_ 为 [0,1]
pred = p >= 0.5
print("imbalance chosen", search.best_params_)
print("CV AP", search.best_score_, "test AP", average_precision_score(y_test, p))
print("test Precision/Recall",
      precision_score(y_test, pred, zero_division=0),
      recall_score(y_test, pred))
```

候选以开发数据 AP 选，测试只报告一次。0.5 只是显式固定的示例阈值，没有在测试集上搜索最佳阈值。若要按审核成本选阈值，需额外设计开发验证步骤。

不能预先断言 balanced 一定胜出，也不能从一次合成数据实验给所有业务指定 C。这个例子展示比较流程，而非生产性能保证。

## 6. 随机重采样与 SMOTE 的区别

随机过采样复制训练少数类样本，不创造新的独立事实。随机欠采样减少多数类样本，节省训练规模，却可能丢掉有用边界或子群体。

SMOTE 在同类邻居之间插值：x_new=x_i+λ(x_neighbor−x_i)，λ∈[0,1]。例如两点 [2,10]、[6,30]，λ=0.25，得到 [3,15]。

合成点应符合字段语义。门店 ID、无序业态不能直接插值得到“介于两个 ID 之间的新门店”；混合类别和数值的处理应采用适合的方法与约束。普通 SMOTE 不是业务样本生成器，也不是大模型文本生成。

噪声点和跨区域邻居可能产生不合理合成样本。距离尺度、邻居数量与训练折少数类样本数都需检查。SMOTE-NC 针对混合字段，SMOTEN 针对纯类别字段，仍不免除语义验证。

## 7. 为什么“采样后再切分”危险？

先复制整批样本再切分，某个原始样本的副本可能同时落入训练与验证；先对整批数据做邻居插值，还可能利用未来验证样本构造训练点。

同时，若验证集也被采样成 1:1，其 Precision、成本和概率表现可能偏离自然业务分布。

正确边界是：先留下最终测试；开发集交叉验证中，每折只重采样训练部分，验证部分保留自然比例。归一化、特征选择与邻居学习也需要遵守相同边界。

## 8. 可运行：手动折内随机复制，验证不采样

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

X_demo, y_demo = make_classification(
    n_samples=400, n_features=6, n_informative=3,
    n_redundant=1, weights=[0.9, 0.1], random_state=7
)
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=7)
scores = []
for fold, (train, valid) in enumerate(cv.split(X_demo, y_demo)):
    rng = np.random.default_rng(7 + fold)
    groups = [train[y_demo[train] == c] for c in [0, 1]]
    target = max(len(g) for g in groups)
    # 保留原记录，再补齐较少的那一类。
    sampled = np.concatenate([
        np.r_[g, rng.choice(g, size=target-len(g), replace=True)]
        for g in groups
    ])
    assert not np.intersect1d(sampled, valid).size
    assert np.bincount(y_demo[sampled]).tolist() == [target, target]
    model = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=1000))
    model.fit(X_demo[sampled], y_demo[sampled])
    p_valid = model.predict_proba(X_demo[valid])[:, 1]
    scores.append(average_precision_score(y_demo[valid], p_valid))
    print("fold", fold, "resampled train", np.bincount(y_demo[sampled]),
          "natural validation", np.bincount(y_demo[valid]))
print("fold AP", scores)
```

此代码只演示二分类随机复制和行号边界，没有实现 SMOTE、分组时间协议或生产调参，也未提供最终测试性能。上面的独立实验与本例数据不是同一批，不能把两组数值组合成一个比较结论。

imbalanced-learn 的 Pipeline 可把采样器放进交叉验证流程；普通 sklearn Pipeline 主要处理 transform 协议，不能简单将 fit_resample 采样器当普通转换器。推理阶段不应复制待预测用户记录。当前环境未安装 imbalanced-learn，本篇不声称实跑了其 Pipeline 或 SMOTE API。

## 9. 训练分布改变后的概率

采样或损失加权可能让模型概率与真实发生率不一致。提高少数类召回不等于概率已校准，应在自然分布、未参与模型拟合的数据上评估或校准。

仅在“类别先验改变、各类条件特征分布保持不变、采样分布概率本身可靠”等严格条件下，才可以从采样先验推导真实先验修正。真实数据常不满足这些条件，不能无条件套一个赔率公式就承诺修复。

对极稀有事件，新增高质量正类样本、修复标签和改善表示有时比不断调整采样比例更重要。

## 10. 练习与答案

1. 全预测负类准确率 99% 就够了吗？答：不，先看正类目标和召回。
2. 把测试集平衡到 1:1 会影响 Precision 吗？答：会，发生率改变了。
3. balanced 权重就是业务成本吗？答：不是，它按类频率计算。
4. SMOTE 是否复制真实的新事实？答：不，它按假设合成插值样本。
5. 采样器应在哪一部分拟合？答：每折训练部分，验证与最终测试保持目标分布。
6. 行号不重复就保证没有泄漏吗？答：不，实体、重复内容与时间信息也要隔离。

## 来源与验证

核验日期：2026-10-04。

- [scikit-learn 类权重实现](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/utils/class_weight.py)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，[BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。
- [imbalanced-learn 常见陷阱](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/doc/common_pitfalls.rst)与[过采样文档](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/doc/over_sampling.rst)，固定提交 `8504e95f0160f61d1b617ca66f779646d2ee609e`，[MIT License](https://github.com/scikit-learn-contrib/imbalanced-learn/blob/8504e95f0160f61d1b617ca66f779646d2ee609e/LICENSE)，Copyright (c) 2014-2020 The imbalanced-learn developers。

中文讲解、手算、代码与业务延伸独立编写，非官方逐字翻译。运行代码依赖 NumPy 与 scikit-learn 1.8.0；未运行 imbalanced-learn API，手动随机复制不是对其实现的复刻。

[返回专题目录](README.md)
