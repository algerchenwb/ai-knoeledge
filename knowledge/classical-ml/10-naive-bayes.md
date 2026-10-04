# 10｜朴素贝叶斯：从条件概率到文本分类

> 目标：读懂先验、似然、后验和条件独立，正确选择 NB 变体，并理解平滑与概率局限。

## 1. “观察到退款词”与“属于投诉”不是同一概率

P(退款词|投诉) 问：投诉文本中，有多少会出现退款词？
P(投诉|退款词) 问：出现退款词的文本中，有多少属于投诉？

两个分母不同，数值通常不同。贝叶斯公式将它们联系起来：

P(类别|特征)=P(类别)×P(特征|类别)/P(特征)。

先验 P(类别) 表示观察该条特征前的类别分布；似然 P(特征|类别) 描述该类产生这种观察的可能性；后验 P(类别|特征) 是结合观察后的类别分布。

这些是模型中的统计量，不是对客户心理、因果关系或事实真实性的自动判断。

## 2. 一个能手算的二值算例

假设两个类别：普通、投诉，先验分别为 0.8、0.2。两个二值特征是“出现退款”“出现延期”，都观察为 1。

在投诉类中，两词各自出现概率为 0.75；普通类中分别为 0.1、0.2。朴素贝叶斯按条件独立假设计算：

- 投诉未归一化分数：0.2×0.75×0.75=0.1125。
- 普通未归一化分数：0.8×0.1×0.2=0.016。
- 投诉后验：0.1125/(0.1125+0.016)=225/257≈0.8755。

如果样本实际没有“延期”，对应项应为 P(延期=0|类别)，在二值模型中是 1−P(延期=1|类别)。不能把“没有出现”一律忽略。

```python
import numpy as np
scores = np.array([0.8 * 0.1 * 0.2, 0.2 * 0.75 * 0.75])
posterior = scores / scores.sum()
assert np.allclose(posterior[1], 225/257)
print("manual complaint posterior", posterior[1])
```

此例是人为给定参数的机制解释，不是某个真实客服系统的概率评估。

## 3. “朴素”指给定类别后的条件独立

模型假设：知道类别后，各特征可以分别估计再相乘。不是要求特征在全体样本中毫无关系。

例如“退款”和“退钱”可能高度相关。把两者作为独立证据，会重复加强同一种信号。模型可能仍有不错分类能力，但概率会过度自信。

重复复制同一列也不是增加新信息。NB 不会自动识别它们其实是同一份证据。相关性、数据泄漏和重复字段都应单独检查。

## 4. 为什么计算对数而不直接乘？

成百上千个小概率相乘，数值可能下溢到零。利用 log(a×b)=log(a)+log(b)，比较类别时可以求：

log P(类别)+Σ log P(特征ᵢ|类别)。

固定输入下，分母对各类相同，因此比较未归一化分数即可选择最大类。但若要输出概率，需要稳定归一化；不能直接把对数分数叫作百分比。

MultinomialNB 的文本计数形式为 log P(c)+Σ xᵢ log θ_cᵢ，其中 xᵢ 是词计数。一个词出现三次会产生三倍该项，不能把所有变体都套成“每个词只乘一次”。

## 5. 变体选择取决于输入含义

| 模型 | 典型输入与假设 | 关键提醒 |
| --- | --- | --- |
| GaussianNB | 连续特征，每类每列使用高斯密度 | 不是要求所有类别合起来服从单个高斯；密度不是区间概率 |
| MultinomialNB | 非负词计数，实践中也用于非负 TF-IDF | 不能输入负值；中心化后的数据通常不合适 |
| BernoulliNB | 是否出现的 0/1 特征 | 显式考虑出现与未出现；词频 10 不等同 10 份证据 |
| CategoricalNB | 每列的离散类别编码 | 非负整数编码，语义是类别而非连续距离；要规划未知类别 |
| ComplementNB | 利用每类补集统计的文本模型 | 可用于比较不平衡任务，不保证所有数据都更好 |

GaussianNB 的高斯密度可能大于 1，因为它是密度值；这不代表类别概率大于 100%。不同输入单位也影响密度数值。

CategoricalNB 允许用整数表示无序类别，原因是模型将整数当成类别索引。这与 KNN 把整数差值当距离不同；编码是否合理依赖下游算法。

## 6. 平滑：没有见过，不等于永远不可能

假设某类训练文本中的两词总计为 [3,0]。直接频率会把第二个词概率估计为 0；新文本出现它时，乘积便变成 0。

加性平滑：
θ_cᵢ=(N_cᵢ+alpha)/(N_c+alpha×V)。

N_c 是该类所有词的总计数，不是文档数量；V 是词表大小。alpha=1 常称 Laplace 平滑。

算例 [3,0]、V=2、alpha=1，得到 [4/5,1/5]。平滑不是偷偷增加真实训练记录，而是改变估计规则。alpha 应在开发数据选；alpha 很大时，词分布趋向更平坦，可能削弱信息。若类别没有训练样本，词平滑也不自动修复类别先验缺失。

## 7. 可运行：手算与 MultinomialNB 一致

两篇训练文档的词计数是 [3,0] 与 [0,3]，类别分别为 0、1。新文档 [1,0]，等先验与 alpha=1 下，两类似然为 0.8 与 0.2，后验也为 0.8 与 0.2。

```python
import numpy as np
from sklearn.naive_bayes import MultinomialNB

X = np.array([[3., 0.], [0., 3.]])
y = [0, 1]
model = MultinomialNB(alpha=1).fit(X, y)
assert np.allclose(np.exp(model.feature_log_prob_),
                   [[0.8, 0.2], [0.2, 0.8]])
assert np.allclose(model.predict_proba([[1., 0.]]), [[0.8, 0.2]])
assert np.allclose(model.predict_proba([[0., 0.]]), [[0.5, 0.5]])
print("NB smoothed likelihood", np.exp(model.feature_log_prob_))
print("NB posterior", model.predict_proba([[1., 0.]]))
```

全零文本在这个模型中只剩先验，因为所有计数 xᵢ 都为零。这不能推广成 BernoulliNB 的规则，后者会考虑特征未出现。

## 8. 可运行：将词表学习放进 Pipeline

```python
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# 显式空格分词的中文教学文本；不是完整中文分词器。
texts = ["退款 延期 退款", "退款 失败", "延期 失败",
         "导航 地址", "营业 时间", "地址 时间"]
labels = ["投诉", "投诉", "投诉", "咨询", "咨询", "咨询"]
pipe = make_pipeline(
    CountVectorizer(tokenizer=str.split, token_pattern=None),
    MultinomialNB(alpha=1)
)
pipe.fit(texts, labels)
pred = pipe.predict(["退款 延期", "地址 营业"])
assert pred.tolist() == ["投诉", "咨询"]
print("text predictions", pred)
vocabulary = pipe.named_steps["countvectorizer"].vocabulary_
assert "停车" not in vocabulary
print("unseen word counts", pipe.named_steps["countvectorizer"]
      .transform(["停车"]).toarray())
```

未知词不在训练词表中，CountVectorizer 会忽略；仅包含未知词的文本可能变成全零。平滑只处理已有词表的零计数，不自动把任何新词加入词表。

这两条断言只是演示机制，不是独立测试集上的业务性能。如果要做交叉验证，应将整个 pipe 交给 GridSearchCV，使词表在每个训练折学习；TF-IDF 的 IDF、筛词和监督特征选择同样要遵守边界。

中文文本需要定义分词、字符 n-gram 或其他表示；默认正则词切分不会自动提供你想要的中文语义粒度。真实文本还应处理模板重复和同一客户跨切分问题。

## 9. 先验变化与不平衡任务

若训练中投诉占 50%，上线只占 2%，模型学习的先验可能与实际不符。过采样也会改变观测类别比例，需要在接近上线分布的验证集上评估。

不能因少数类召回提高就宣布概率可靠。分类阈值、Precision/Recall、成本和概率校准要分别检查。高后验不是“必须自动执行退款”的授权依据。

可以比较 ComplementNB、线性分类器等基线，但所有比较应使用同一数据切分和指标，不能分别挑选最好结果。

## 10. 增量学习与表示一致性

部分 NB 模型支持 partial_fit；第一次调用需提供全部预期类别。分批累积统计可以减少同时加载的数据量，但不是会遗忘历史的流式学习：旧分布的影响不会自然消失。

向量化列含义必须保持一致。第一批第 3 列是“退款”，第二批第 3 列若变成“地址”，累积统计就失去意义。固定词表或一致的哈希表示可帮助维持列协议，但各自仍有未知词或碰撞问题。

数据规模大时，除模型以外还要估算词表、稀疏矩阵和批处理内存。不能只因为 NB 训练快就无限增大输入批次。

## 11. 练习与答案

1. P(退款|投诉) 等于 P(投诉|退款) 吗？答：一般不等，分母和含义不同。
2. 两列完全重复，NB 会自动只记一份证据吗？答：不会，可能重复计入。
3. MultinomialNB 应直接使用中心化后的负值特征吗？答：不应，它要求非负输入。
4. alpha=1 能识别所有未见新词吗？答：不能，平滑不等于扩充词表。
5. predict_proba=0.99 就代表真实投诉率恰为 99% 吗？答：不保证，应独立检查校准和分布变化。
6. NB 的条件独立假设一定成立才可用吗？答：不一定，它仍可作为基线；但不能忽视假设失配的影响。

## 来源与验证

核验日期：2026-10-04。主要来源为 [scikit-learn 官方开源文档 naive_bayes.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/naive_bayes.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、业务例子与代码独立编写，非官方逐字翻译。配套代码使用 scikit-learn 1.8.0 实跑；来源主分支与安装版本不完全相同。

[返回专题目录](README.md)
