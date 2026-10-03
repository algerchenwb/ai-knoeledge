# 02｜逻辑回归：从线性分数到分类概率

> 目标：理解 sigmoid、log-odds、交叉熵和分类阈值，不被“回归”二字误导。

## 1. 为什么叫回归，却用于分类？

线性回归预测连续数值，普通输出不受 [0,1] 限制。逻辑回归先计算线性分数 z=b+w·x，再用 sigmoid 转为二分类正类的概率形式：

p=1/(1+exp(−z))。

最后根据阈值把概率变成类别。因此它在机器学习工具中通常是分类器，尽管名字包含“回归”。

| z | sigmoid(z) | 直观含义 |
| --- | --- | --- |
| −2 | 约 0.1192 | 偏向负类 |
| 0 | 0.5 | 两类分界位置 |
| 2 | 约 0.8808 | 偏向正类 |

这些数值是模型输出，不自动保证在业务数据上已经校准。预测 0.8 的样本群，实际正类比例是否接近 80%，还需另行验证。

## 2. “线性”的究竟是什么？

概率不是 x 的直线；log-odds 是线性关系：

log(p/(1−p))=b+w·x。

odds 是正类概率与负类概率之比。例如 p=0.8，odds=4，不是 80，也不是概率本身。log-odds 是 odds 的自然对数。

某输入增加一个单位，在其他模型输入固定时，odds 乘以 exp(w)。若 w≈0.693，odds 约翻倍，但概率不会直接翻倍：p 从 0.2 变到约 0.333，而不是 0.4。

这仍是模型内的条件关系，不能直接解释为真实因果效应。特征单位、标准化和相关性也会影响系数解释。

## 3. 它如何根据标签学习？

二分类标签 y∈{0,1}，常用每条样本的对数损失：

L=−[y log(p)+(1−y)log(1−p)]。

若真实标签为 1：
- p=0.9，损失约 0.1054。
- p=0.1，损失约 2.3026。

自信地答错会受到较大惩罚。这与“只要分类正确就得一分”的 Accuracy 不同。

实际实现应使用稳定的数值公式，避免 p 极接近 0 或 1 时直接计算 log 造成问题。不要把手算形式直接当成大规模训练代码。

## 4. 分类边界与阈值

默认示意阈值 0.5 对应 z=0。二维输入下，w₁x₁+w₂x₂+b=0 是直线，高维下是超平面。

把阈值改成 t，相应分数边界是 log(t/(1−t))。阈值变化改变决策，不必重新训练系数；但选阈值必须使用开发阶段的验证数据。

例如识别需要人工处理的异常请求，漏报成本高时可能希望增加召回，人工容量有限时又需控制误报。不要把 0.5 当成业务上必然最优。

降低固定模型的阈值通常增加预测正类集合，召回率不减，但 Precision 不保证单调下降。具体看新增样本中有多少真正例。

## 5. 正则化与 C：方向别记反

scikit-learn 的 LogisticRegression 默认通常包含正则化。C 表示正则化强度的倒数：C 越小，正则约束越强。

这与 Ridge/Lasso 常用的 alpha 方向不同，后者 alpha 越大通常约束越强。不要把“把数字调大”当成统一操作。

不同版本对 penalty、l1_ratio、无正则化等参数的支持与弃用情况可能不同。本篇完整例子仅使用已实跑的基本构造，不给出未经本地验证的新版参数组合。

## 6. 可运行的独立分类示例

```python
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss

X_train = np.array([[-3.], [-2.], [-1.], [1.], [2.], [3.]])
y_train = np.array([0, 0, 0, 1, 1, 1])
model = make_pipeline(
    StandardScaler(), LogisticRegression(C=1.0, max_iter=1000)
)
model.fit(X_train, y_train)
X_check = np.array([[-2.5], [0.], [2.5]])
proba = model.predict_proba(X_check)
classes = model[-1].classes_
positive_column = int(np.flatnonzero(classes == 1)[0])
p = proba[:, positive_column]
print("classes", classes, "p", p)
print("threshold 0.5", (p >= 0.5).astype(int))
print("threshold 0.8", (p >= 0.8).astype(int))
assert p[0] < p[1] < p[2]
assert np.allclose(proba.sum(axis=1), 1)
print("train log loss",
      log_loss(y_train, model.predict_proba(X_train), labels=classes))
```

这个例子用对称合成数据解释概率与阈值，不是生产性能评测。边界点附近的精确浮点值可能略有差异，不应依赖某个输出永远严格等于 0.5。

predict_proba 的列顺序来自 classes_，不能永远假定第二列对应你定义的业务正类。正类若是字符串“异常”，应定位该标签对应列。

## 7. 多类与多标签不是同一问题

多类单标签：每条样本只能属于一个类别，例如“正常/网络故障/鉴权故障”。多项逻辑回归可给每类一个分数，再用 Softmax 形成和为 1 的概率。

多标签：同一请求可以同时“超时”且“缺字段”，应按多个二分类标签等方式建模，不能强迫只能选一个。

One-vs-Rest 与直接多项逻辑回归也不是同一个优化目标；即使都输出多类结果，其训练结构和概率处理可能不同。具体 solver 支持应查使用版本文档。

## 8. 特征工程如何改变边界？

逻辑回归对输入特征的分数是线性的。加入平方项、交互项后，它可以在原始输入空间产生非线性分类边界。

类别特征通常要明确编码；把业态编码 1、2、3 直接作为连续数值，会引入间隔与顺序假设。One-hot 等方案避免部分假设，但仍需在训练数据中学习和保存一致的映射。

标准化应在 Pipeline 中完成，不能先用全量数据算均值后再划分。不要把“简单模型”误解成不需要防泄漏。

## 9. 类别权重的作用与限制

业务扩展：类别权重改变训练目标，让某类错误的影响变大。它不同于仅在预测后移动阈值，学到的系数也可能改变。

使用重采样或类别权重后，输出概率的解释需要额外小心。应在代表真实上线分布的数据上检查校准与阈值，不能把权重后的概率无条件当成总体发生率。

## 10. 练习与答案

1. p=0.8，odds 是多少？  
   答：0.8/0.2=4。

2. C 从 1 改成 0.1，是增强还是减弱正则化？  
   答：增强，C 是逆强度。

3. 高概率但大量误报，应只换成更大模型吗？  
   答：先检查正类定义、校准、阈值、分布与标签质量。

4. 同一对象可同时拥有多个标签，能直接用互斥 Softmax 吗？  
   答：通常不符合问题定义，应该使用适合多标签的建模方式。

## 来源与边界

核验日期：2026-10-04。主要来源：[scikit-learn 线性模型官方开源文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/linear_model.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。中文说明、业务类比、算例和练习为独立整理，非官方逐字翻译。来源项目采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。示例在 scikit-learn 1.8.0 环境验证；固定来源主分支与本地安装版本不完全相同，避免依赖尚未验证的新版参数。
