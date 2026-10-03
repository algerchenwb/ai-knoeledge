# 03｜正则化：Ridge、Lasso、ElasticNet 怎样抑制不稳定？

> 目标：理解“训练误差加上约束”的思路，能正确比较 alpha，并避免错误特征选择。

## 1. 为什么训练误差最小不一定最好？

模型可能为了贴合训练噪声，把系数放得很大。例如两个几乎相同的特征，系数一个很正、一个很负，相互抵消，在训练数据中看似不错，稍有扰动就不稳定。

正则化给某些参数形态额外代价：不仅要求预测误差小，也希望系数别任意增长，或者希望少一些非零系数。它引入偏好，可能牺牲训练拟合来改善泛化与稳定性。

正则化不是数据清洗，也不能修复泄漏、未来字段和错误标签。

## 2. Ridge：平方系数惩罚

Ridge 的典型目标：

Σ(yᵢ−ŷᵢ)² + alpha×Σwⱼ²。

第二项是 L2 惩罚，系数越大代价越高。alpha 增大通常使系数收缩；收缩并不表示每个系数沿所有情况下都严格单调变化。

Ridge 通常不会像 Lasso 那样产生大量精确零系数，它倾向保留多个相关特征并限制其整体幅度。它适合建立稳定基线，但不能保证一定优于无正则化回归。

## 3. Lasso：绝对值惩罚与稀疏性

scikit-learn Lasso 的目标：

(1/(2n))Σ(yᵢ−ŷᵢ)² + alpha×Σ|wⱼ|。

L1 惩罚可使某些系数精确变为零，因此有特征选择作用。它不是“每个重要特征都能正确找到”：相关特征之间可能选择不稳定，小样本或错误 alpha 也可能丢掉有用信息。

“系数为零”表示这个拟合方案没有使用它，不证明它在业务世界中没价值，也不证明与标签毫无关系。

## 4. ElasticNet：结合两种偏好

目标可写成：

(1/(2n))RSS + alpha×rho×Σ|w| + alpha×(1−rho)/2×Σw²。

rho 对应 l1_ratio：
- rho=1，对应此参数化下的 Lasso。
- rho=0，是仅 L2 的目标。
- 0<rho<1，两者混合。

它既可以产生稀疏性，也可以缓和 Lasso 在相关特征中的选择不稳定。但“更复杂”不保证更好，要在相同切分上比较。

注意参数化：rho=0 时虽然是 L2，不能直接认为 ElasticNet(alpha=a) 与 Ridge(alpha=a) 是同一个问题。一个使用 1/(2n) 的误差缩放，另一个使用平方和，数字强度不是同一尺度。

## 5. 用一元问题理解 L1 与 L2

取 x=[−1,0,1]，y=[−2,0,2]，均值为零，截距设为零。Σx²=2，Σxy=4。

普通最小二乘斜率为 w=4/2=2。

Ridge(alpha=2) 的斜率为 w=Σxy/(Σx²+alpha)=4/4=1。

Lasso 的单变量解为软阈值形式：
w=soft(Σxy/n, alpha)/(Σx²/n)，
soft(z,a)=sign(z)×max(|z|−a,0)。

在 n=3、alpha=0.5 时，w=(4/3−0.5)/(2/3)=1.25。alpha 大到至少 4/3 时，w=0。

这展示 L1 能把系数直接压到零，而 L2 在这里连续收缩。不能拿这几个手算数字证明真实模型的最佳 alpha。

## 6. 特征尺度为什么必须关心？

假设把一个特征扩大一千倍，维持同样预测只需把系数缩小一千倍。若惩罚只看系数大小，该特征就容易用“更便宜”的系数表达相同作用。

因此正则化结果会受尺度影响，StandardScaler 是常用选择。它必须只在训练集学习，并在每折交叉验证中重新学习。

标准化不是所有模型的万能预处理；稀疏矩阵、异常值和业务单位都有额外考虑。不要为了整齐而把所有数据强制变成密集矩阵。

## 7. 不同模型的 alpha 不能机械对比

| 模型 | 误差项的常见缩放 | 参数方向 |
| --- | --- | --- |
| Ridge | RSS | alpha 大，惩罚通常更强 |
| Lasso | RSS/(2n) | alpha 大，惩罚通常更强 |
| ElasticNet | RSS/(2n) | alpha 控总量，l1_ratio 控混合 |
| LogisticRegression | 对数损失加惩罚，具体缩放见版本 | C 小，惩罚通常更强 |

相同 alpha 数字不表示同等约束。样本数量、是否加权、特征尺度和目标缩放也会影响它的意义。

实际选择应围绕明确候选网格，用开发数据验证，而不是套用“alpha=1 永远合理”。

## 8. 一个可运行的正确调参流程

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

X, y = make_regression(
    n_samples=240, n_features=12, n_informative=5,
    noise=20, random_state=42
)
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)
pipeline = make_pipeline(StandardScaler(), Ridge())
search = GridSearchCV(
    pipeline, {"ridge__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
    cv=KFold(n_splits=5, shuffle=True, random_state=42),
    scoring="neg_mean_squared_error"
)
search.fit(X_dev, y_dev)
pred = search.predict(X_test)
print("chosen", search.best_params_)
print("CV MSE", -search.best_score_)
print("final test MSE", mean_squared_error(y_test, pred))
assert np.isfinite(pred).all()
```

GridSearchCV 的 scoring 约定越大越好，因此误差用负值返回。best_score_=-300 优于 -500，对应 MSE 300 小于 500；打印真实误差时要取负号。

完整 Pipeline 在每折重新学习缩放参数，避免泄漏。默认 refit 会按最佳配置在整个开发集重新拟合。示例是近似独立的合成数据；POI 与时间面板任务应替换切分策略。

这次最终测试仅用于报告，不用于继续调整 alpha。如果根据测试分数改方案，它也就参与了选择。

## 9. 正则化与欠拟合、过拟合

- 约束太弱，可能高方差：训练好，验证差。
- 约束太强，可能高偏差：训练与验证都差。
- 适度约束可能降低验证误差，但分数也会受样本量、噪声和分布影响。

这里的“偏差”描述模型学习能力受限的系统误差，不等于社会偏见。偏差方差的直观解释也不是每个业务数据集都能直接算出的诊断结果。

训练和验证的落差不是过拟合的唯一证据；数据分布不同、标签口径变化和特征不可用也会造成落差。先排查协议，再调模型。

## 10. 特征选择必须放在哪一步？

如果用 Lasso 选择特征，再用另一个模型预测，选择本身也属于训练流程。不能在全量数据上选完特征后再切分，或者先看最终测试标签再决定保留哪列。

需要比较不同候选特征集时，应在训练/验证流程内完成，并对相同对象、时间边界保持一致。Lasso 选出来的变量也不应被包装为已经确认的因果解释。

## 11. 练习与答案

1. Ridge 的训练误差比普通回归高，是否表示失败？  
   答：不一定，约束本来就可能牺牲训练拟合，关键看公平验证与业务表现。

2. Lasso 系数为零，能宣布该特征不重要吗？  
   答：不能，需要看相关性、尺度、样本和选择稳定性。

3. Ridge 与 Lasso 都设 alpha=1，能说正则化强度一样吗？  
   答：不能，误差项的缩放和惩罚定义不同。

4. 标准化在交叉验证之前对全量开发集 fit 一次，安全吗？  
   答：不安全，验证折会影响预处理。应把 scaler 放在交叉验证的 Pipeline 内。

## 来源与边界

核验日期：2026-10-04。主要来源：[scikit-learn 线性模型官方开源文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/linear_model.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。中文说明、业务类比、算例和练习为独立整理，非官方逐字翻译。来源项目采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。示例在 scikit-learn 1.8.0 环境验证；固定来源主分支与本地安装版本不完全相同，避免依赖尚未验证的新版参数。
