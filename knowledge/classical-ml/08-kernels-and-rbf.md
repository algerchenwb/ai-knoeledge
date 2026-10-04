# 08｜核方法与 RBF：不用显式展开，也能学习非线性边界

> 先修：[SVM 与间隔](07-support-vector-machines.md)。目标：理解核函数、C/gamma、预计算矩阵与调参边界。

## 1. 直线分不开时怎么办？

XOR 的四个点：同号的 (−1,−1)、(1,1) 属于 0，异号的 (−1,1)、(1,−1) 属于 1。在原二维空间，一条直线无法把对角线两类完全分开。

可以增加特征 z=x₁x₂。同号点的 z=1，异号点的 z=−1，于是在新表示中容易线性分开。这是“换一种表示使问题变简单”的直觉。

核方法并不必须先实际生成所有新特征，而是直接计算某个映射后向量的内积：K(x,x′)=φ(x)·φ(x′)。这叫核技巧。

## 2. 核不只是任意相似度函数

在常见理论框架中，合适的核应对应某个特征空间的内积；有限样本得到的 Gram 矩阵具有对称、半正定等性质。

不是任何“看起来像相似分”的业务函数都能无条件成为有效核。随意修改相似度可能破坏优化性质。也不要把核技巧理解成“凭空创造新信息”：它改变模型的表示和约束，仍只使用已有输入。

## 3. 常见核

| 核 | 表达式 | 直观作用 |
| --- | --- | --- |
| Linear | x·x′ | 原空间线性关系 |
| Polynomial | (gamma×x·x′+coef0)^degree | 对应某些多项式组合 |
| RBF | exp(−gamma×||x−x′||²) | 距离近则响应高，远则衰减 |

多项式度数越高不代表更好。RBF 常用，但也不是所有领域的通用胜者。应与线性和其他合理基线在同一协议下比较。

RBF 的相似度范围在 (0,1]，这个值不是类别概率。两条样本 RBF 相似度 0.9，不表示同类概率就是 90%。

## 4. gamma 控制影响范围

设平方距离为 1：
- gamma=0.5，核值 exp(−0.5)≈0.6065。
- gamma=2，核值 exp(−2)≈0.1353。

gamma 越大，相似响应随距离下降越快，每个样本的影响更局部；gamma 较小，响应范围更宽。太大的 gamma 可能记住训练局部细节，太小可能区分能力不足。

特征尺度改变，距离平方也改变，所以 gamma 的含义变化。即使使用 gamma="scale" 的自动规则，也不等于自动获得最佳业务边界。

## 5. C 与 gamma 要联合选择

C 控制违反间隔的惩罚，gamma 控制核响应的局部程度。它们不是可以独立凭直觉拍定的两个旋钮。

小 gamma、大 C 可能尝试在较平滑表示下加强拟合；大 gamma、大 C 可能形成非常局部的复杂边界。具体结果取决于数据，不能把这句话当作固定性能排行。

常见做法是在对数尺度选择若干候选，例如 C=[0.1,1,10]、gamma=[0.1,1,10]，在开发数据交叉验证。候选网格只是教学例子，不是已经适合生产的建议。

## 6. 可运行的 XOR 例子

```python
import numpy as np
from sklearn.svm import SVC

X = np.array([[-1., -1.], [-1., 1.], [1., -1.], [1., 1.]])
y = np.array([0, 1, 1, 0])
linear = SVC(kernel="linear", C=10).fit(X, y)
rbf = SVC(kernel="rbf", C=10, gamma=1).fit(X, y)
print("linear train accuracy", linear.score(X, y))
print("RBF train accuracy", rbf.score(X, y))
assert linear.score(X, y) < 1
assert np.array_equal(rbf.predict(X), y)
```

RBF 在这四个点上拟合成功，只证明表达能力与例子兼容。四个训练点不提供新样本泛化证据，不能据此说 RBF 永远优于线性模型。

## 7. 一个保留最终测试的调参流程

```python
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score

X, y = make_moons(n_samples=240, noise=0.2, random_state=42)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
search = GridSearchCV(
    make_pipeline(StandardScaler(), SVC()),
    {"svc__C": [0.1, 1., 10.], "svc__gamma": [0.1, 1., 10.]},
    cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=42),
    scoring="balanced_accuracy"
)
search.fit(X_dev, y_dev)
print("chosen", search.best_params_)
print("CV", search.best_score_)
print("final test", balanced_accuracy_score(y_test, search.predict(X_test)))
```

缩放参数在每个训练折学习，C/gamma 用开发数据选，最终测试只用于报告。make_moons 是合成数据；若任务是新 POI 或未来日期，应替换切分方法，不要把分层随机划分当成通用安全协议。

网格搜索比较 9 组设置，每组 3 折，通常约 27 次拟合，另有最佳方案重训。选择成本应记录，不能只展示最好的一个分数。

## 8. 预计算核矩阵的形状

使用 kernel="precomputed" 时，训练输入是 K_train，形状 [N_train,N_train]；预测输入是新样本与训练样本的核值，形状 [N_new,N_train]。

预测不是传 [N_new,N_new]，也不是把原始特征直接传进去。列顺序必须严格对应训练样本顺序。如果训练样本换了顺序，核列也要相应改变。

交叉验证中，对每折训练行列及验证对训练列都要正确切分。若核计算包含要从数据学习的归一化或表示，它仍应只在折内训练数据上学习，预计算不自动消除泄漏。

## 9. 规模、内存与推理代价

完整 N×N 的 float64 核矩阵约需 8N² 字节。N=10,000 时仅原始矩阵约 800 MB，约 763 MiB；其他工作内存还没算。

SVC 实现可能使用缓存和按需计算，不代表必定分配完整矩阵，但训练规模仍是重要限制。预测成本也与支持向量数量相关。

大规模线性任务可比较 LinearSVC 或合适的 SGD 模型；非线性任务可研究核近似。本篇不声称这些方法与精确核 SVC 完全等价，选择应比较效果、时间、内存与维护成本。

## 10. 为什么“核值”不是语义检索的万能答案？

工程补充：RBF 在当前数值空间测距离，不自动理解业务文本。Embedding 的语义取决于训练模型，RBF 不能补回未编码的信息，也不会让不同模型输出的空间天然兼容。

同样，位置、ID、时间和数值混合输入时，要先定义表示。一个接口 ID 与另一个接口 ID 的数字差距通常没有语义距离含义。

## 11. 练习与答案

1. RBF 相似度 0.9 是同类概率 90% 吗？  
   答：不是，它是核值，不是分类概率。

2. gamma 增大，影响范围更宽还是更窄？  
   答：通常更窄，距离响应衰减更快。

3. 100 个新样本、1000 个训练样本，预测预计算核是什么形状？  
   答：[100,1000]，列顺序对应训练样本。

4. XOR 训练全对，能报告泛化准确率 100% 吗？  
   答：不能，只能报告这个训练例子的拟合结果。

## 来源与验证边界

核验日期：2026-10-04。[scikit-learn SVM 官方开源文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/svm.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。中文讲解、算例、代码和业务扩展独立编写，非官方逐字翻译。来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。完整示例在 scikit-learn 1.8.0 核验；来源主分支与安装版本不完全相同。
