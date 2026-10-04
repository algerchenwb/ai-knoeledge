# 11｜概率校准：模型说 80%，究竟意味着什么？

> 先修：[分类指标与业务成本](../ml-evaluation/03-metrics-and-business-decisions.md)。目标：区分排序、概率可信度与行动阈值。

## 1. 校准是“一批类似预测”的统计性质

模型给某条门店记录输出“高客流概率 0.8”，不意味着已经观察到这家门店未来客流，也不是可以重复验证一次就判断对错的承诺。

二分类模型校准良好时，在大量预测概率接近 0.8 的记录中，实际正类比例应接近 80%。比较的是一批相近预测与实际结果，不能因为一个 0.8 的样本最终是负类，就证明模型失准。

校准也依赖数据分布。历史门店、未来门店、新城市可能有不同概率关系，应明确概率针对哪个群体和时间范围。

## 2. 排序好，概率仍可能不可信

假设真实正类排在负类前面，排序指标可能很好。但把所有分数推得过于接近 0 和 1，会制造过度自信。

二分类对同一组分数做严格递增变换，通常保留排序，因此 ROC-AUC 不变；概率误差却可改变。换一个阈值则改变硬分类决策，通常不改变原始分数的排序指标。

三件事应分别回答：
- 区分能力：正类能否排在负类前面？
- 校准：报出的 0.8 是否在统计上对应约 80%？
- 决策：给定成本和处理容量，应该对哪些记录采取动作？

## 3. 可靠性曲线怎样读？

把预测概率分箱，例如 [0,0.2]、(0.2,0.4] 等。每箱计算平均预测概率与实际正类比例，横轴是前者，纵轴是后者。

如果横轴 0.8、纵轴 0.6，意味着这一箱平均报 80%，但实际只有约 60% 正类，表现为过度自信。若横轴 0.2、纵轴 0.4，则低估了正类比例。

还要看每箱样本数。两条记录估出来的 50% 与两千条记录估出来的 50%，不具有相同稳定性。均匀宽度分箱与等频分箱产生不同视角；空箱不会产生有效比例。更多箱不自动更准确，小箱可能噪声很大。

总体曲线好也可能掩盖子群体失准，例如老门店概率可信，新门店却偏高。分组检查仍要注意样本量与不确定性。

## 4. Brier 与 Log loss 衡量什么？

二分类 Brier 定义为 mean((p−y)²)，越低越好。这里 p 是正类概率，y 是 0/1；本篇手算采用这个二分类定义。

Log loss 对误判且非常自信的预测惩罚较大，例如真实 y=0 却预测 p=0.99。实现为避免 log(0) 会有数值处理；不能利用裁剪声称极端误判没有代价。

两者是整体概率质量指标，同时受校准、区分能力和数据不确定性影响。更低的 Brier 不必然意味着单独的校准更好；应结合可靠性曲线和样本量。

全体都报正类比例的常数模型可以在总体上校准，却没有个体区分能力。不能为了让曲线接近对角线，牺牲所有排序信息后就称模型优秀。

## 5. 可运行：AUC 相同，概率质量不同

```python
import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

y = np.array([0, 1, 0, 1, 0, 1, 0, 1])
p = np.repeat([0.6, 0.9], 4)
assert np.isclose(roc_auc_score(y, p), 0.5)
assert np.isclose(brier_score_loss(y, p), 0.335)
constant = np.full(len(y), 0.5)
assert np.isclose(brier_score_loss(y, constant), 0.25)
print("Brier", brier_score_loss(y, p), brier_score_loss(y, constant))
print("log loss", log_loss(y, p), log_loss(y, constant))

p_sharp = 1 / (1 + np.exp(-3 * np.log(p / (1-p))))
assert np.isclose(roc_auc_score(y, p_sharp), roc_auc_score(y, p))
print("same AUC; changed Brier", brier_score_loss(y, p_sharp))
for value in [0.6, 0.9]:
    mask = p == value
    print("bin mean/count/positive rate",
          p[mask].mean(), mask.sum(), y[mask].mean())
```

两个组都实际 50% 正类，模型却报 60% 和 90%。这只是人为构造的机制核对，不是估算真实业务的校准误差。

## 6. 校准器怎样学习？

校准器学习从模型输出到概率的映射。Sigmoid 使用带参数的 S 型映射；参数应从校准数据学习，不能任意套 sigmoid 后宣称概率可信。

Isotonic 学习单调、通常呈阶梯状的映射，灵活但小样本更容易过拟合。它可能把不同分数映射到相同概率，从而引入平票。选择方法应看开发数据表现，不能照搬某个固定样本数作为普适保证。

对固定二分类分数的单个严格递增映射，排序通常不变；但交叉验证校准集成同时平均多个不同模型，不能因此断言整个训练前后 AUC 一定相同。

来源主分支还有其他方法；本篇只实跑安装版本中的 sigmoid，未把主分支新增 API 当作环境里一定可用的接口。

## 7. 必须隔离训练、校准与最终评估

基础模型在自己训练数据上的分数常比新样本更乐观。再用这些分数拟合校准器，会把这种乐观偏差带进去。

一种清楚的方案是：
1. 训练集拟合模型以及缩放器等预处理。
2. 不重叠的校准集拟合概率映射。
3. 若要选择行动阈值，另用决策验证数据或设计交叉拟合流程。
4. 最终测试只报告已确定流程的结果。

不同集合不只是行号不重复；重复文本、同一门店或未来数据也可能跨越边界。时间协议、分组协议应贯穿基础模型和校准器。

CalibratedClassifierCV 可以用交叉验证生成未参与对应基础模型训练的分数。必须检查每折类别覆盖；普通分层随机划分不自动满足门店分组或预测未来的要求。

## 8. 可运行：显式三份数据与已拟合模型校准

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.frozen import FrozenEstimator
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, log_loss

X, y = make_classification(
    n_samples=1200, n_features=8, n_informative=4,
    n_redundant=2, weights=[0.8, 0.2], random_state=42
)
X_rest, X_test, y_rest, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)
X_train, X_cal, y_train, y_cal = train_test_split(
    X_rest, y_rest, test_size=1/3, stratify=y_rest, random_state=43
)
base = make_pipeline(StandardScaler(), LinearSVC(random_state=42))
base.fit(X_train, y_train)
calibrated = CalibratedClassifierCV(
    FrozenEstimator(base), method="sigmoid"
)
calibrated.fit(X_cal, y_cal)
positive_column = np.flatnonzero(calibrated.classes_ == 1)[0]
p_test = calibrated.predict_proba(X_test)[:, positive_column]
assert np.all((p_test >= 0) & (p_test <= 1))
print("calibrated Brier/log loss",
      brier_score_loss(y_test, p_test),
      log_loss(y_test, np.column_stack([1-p_test, p_test])))
fraction, mean = calibration_curve(
    y_test, p_test, n_bins=5, strategy="quantile"
)
print("bin mean", mean, "bin positive fraction", fraction)
```

FrozenEstimator 表示基础模型已拟合，校准过程不重新学习它。使用者负责保证 X_train 与 X_cal 隔离；包装器不能修复错误数据划分。预处理放在 base 内，因此校准集也没有参与缩放器拟合。

示例输出只展示流程，没有对其他方案作公平比较，不承诺每个分箱都吻合。合成数据也不证明某个真实门店任务概率可信。

## 9. 概率校准后，阈值仍要单独决定

在二分类、预测概率可靠、正确决策成本为零、误报成本 C_FP 与漏报成本 C_FN 为固定值的简化条件下：

预测正类的期望成本=C_FP×(1−p)；
预测负类的期望成本=C_FN×p。

因此 p>C_FP/(C_FP+C_FN) 时预测正类更划算。例如误报 1、漏报 9，阈值为 0.1。等号时两种决策期望成本相同，需要约定处理方式。

这是有前提的数学推导，不是所有业务的阈值建议。容量限制、审核成本、不同门店成本、行动对结果的影响，都可能改变决策规则。校准不会自动解决这些约束。

## 10. 练习与答案

1. 单条 0.8 预测结果为负就证明失准吗？答：不，需比较大量相近预测的实际比例。
2. Brier 更低一定代表单独校准更好？答：不一定，也受区分能力等影响。
3. isotonic 后 AUC 必须不变吗？答：不，阶梯映射可引入平票。
4. 训练和校准行号不同就一定安全？答：不，重复实体、时间和预处理可能仍泄漏。
5. 校准好就必须用 0.5 阈值？答：不，阈值取决于决策成本及约束。

## 来源与验证

核验日期：2026-10-04。基于 [scikit-learn calibration.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/calibration.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文讲解、手算与业务延伸独立编写，非官方逐字翻译。代码使用 scikit-learn 1.8.0 实跑，来源主分支与安装版本不完全相同。

[返回专题目录](README.md)
