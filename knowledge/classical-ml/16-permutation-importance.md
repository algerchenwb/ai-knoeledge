# 16｜置换重要性：模型依赖哪些字段，为什么不是因果解释？

> 目标：读懂分数下降、指标方向、相关特征和组置换，区分解释当前模型与删除特征后重训。

## 1. 提问对象是一个已拟合模型

置换重要性问：固定模型，在给定数据上打乱某列，预测表现下降多少？

它描述特定模型、数据和指标下的依赖，不是字段的固有价值，也不是改变该变量就一定改变业务结果的因果结论。

人口字段重要，不能直接推出人为增加人口会带来同等客流提升；人口可能与位置、规模和未观测因素共同变化。

先评估模型泛化能力。一个表现很差的模型没有学会使用某字段，不能证明字段没有信息。

## 2. 算法与指标方向

先算基准分数 s；固定模型，每次随机打乱一列再算 s_shuffle。重要性=s−平均 s_shuffle。

正值表示破坏该列后表现变差；近零表示当前模型在当前协议下不明显依赖它；负值可能来自随机波动、过拟合或破坏某种有害关系。

scikit-learn scorer 按越高越好定义。neg_mean_squared_error 对应的重要性为 MSE_shuffle−MSE_base；不要再次翻转负号。

指标可改变排行。AP、Recall、R² 与成本关心不同目标，应说明 scoring，而非只给一个“重要性”数字。

## 3. 可运行：重要性可以大于 1

模型 y=2x，x=[0,1,2,3]。将输入倒序后预测为 [6,4,2,0]，MSE=20，标签方差=5，R²=1−20/5=−3。

基准 R²=1，下降为 4。它不是 400% 概率，也不是归一化贡献比例。

```python
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
X = np.arange(4., dtype=float).reshape(-1,1)
y = 2 * X[:,0]
model = LinearRegression().fit(X,y)
base = r2_score(y, model.predict(X))
shuffled = r2_score(y, model.predict(X[::-1]))
assert np.isclose(base,1.)
assert np.isclose(shuffled,-3.)
assert np.isclose(mean_squared_error(y,model.predict(X[::-1])),20.)
assert np.isclose(base-shuffled,4.)
print("manual R2 importance",base-shuffled)
```

这是指定排列的机制核对，未进行随机重复估计；不同排列会改变数值。

## 4. 不重新训练，是定义的一部分

普通置换重要性只改评估输入，不重新学习参数。删除字段后重训并比较表现，是另一种消融实验。

固定模型可能依赖某列，但重训后能改用替代列。当前没被使用的字段也可能在另一个模型或交互表示中有用。两种实验不能用同一句“字段没用”混为一谈。

在最终测试上计算重要性并据此删列，是模型选择；解释报告不自动免除验证边界。

## 5. 与树的纯度重要性比较

树 feature_importances_ 通常汇总训练分裂的纯度改善。取值很多的字段提供更多候选切分，可能被偏爱；训练过拟合时噪声也可能得高分。

置换可在未见数据上计算，也适用于多种模型和指标；但相关性与不合理打乱组合仍会影响解释，不能称为完全真实的字段价值。

树的重要性通常归一化；置换重要性不保证非负、和为 1 或各列可加。两张表不能按相同数字直接对比。

## 6. 相关列与组置换

两列都保存同一信号，打乱其中一列时，模型仍可能从另一列获取信息。单列重要性较低不能推出整组无用。

也不能保证相关列单列重要性一定接近零：模型可能把权重分给两列，打乱一列仍会损坏当前计算。结果依赖已拟合模型如何使用替代信息。

组置换用同一行排列共同打乱相关列，保留它们组内关系，并破坏整组与标签的关联。组结果不必等于单列结果之和。

## 7. 可运行：单列置换与整组置换

```python
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error

rng = np.random.default_rng(42)
signal_train = rng.normal(size=400)
X_train = np.column_stack([
    signal_train,signal_train,rng.normal(size=400)
])
y_train = 3*signal_train+rng.normal(0,0.1,size=400)
signal_val = rng.normal(size=300)
X_val = np.column_stack([
    signal_val,signal_val,rng.normal(size=300)
])
y_val = 3*signal_val+rng.normal(0,0.1,size=300)
model = Ridge(alpha=1).fit(X_train,y_train)
result = permutation_importance(
    model,X_val,y_val,scoring="neg_mean_squared_error",
    n_repeats=20,random_state=42
)
base_mse = mean_squared_error(y_val,model.predict(X_val))
group_increase = []
for _ in range(20):
    order = rng.permutation(len(X_val))
    changed = X_val.copy()
    changed[:,:2] = X_val[order,:2]
    group_increase.append(
        mean_squared_error(y_val,model.predict(changed))-base_mse
    )
assert np.mean(group_increase)>np.max(result.importances_mean[:2])
print("Ridge coef/base MSE",model.coef_,base_mse)
print("single column importance",result.importances_mean)
print("shuffle std",result.importances_std)
print("group increase",np.mean(group_increase),np.std(group_increase))
```

训练和解释数据独立生成；本例不是生产性能评估，也没有据此删除字段。Ridge 给两个副本分配权重，组置换比任一单列置换造成更大误差，验证的是特意构造的机制。

## 8. 置换标准差不等于总体置信区间

n_repeats 反映固定模型、固定评估集上随机打乱的波动，不自动覆盖重训、数据采样、筛选和漂移的不确定性。

“均值减两倍标准差大于零”可作探索性规则，不能自动当成严格显著性检验；大量字段同时比较也会有选择问题。

稳定性研究可预先设定多个训练折或时期，并记录覆盖了哪些变化。不能事后丢弃不利时期使排行好看。

## 9. 打乱可能制造不存在的业务记录

总人口与年龄人数相互约束，单独打乱可能制造不可能组合。经纬度单列打乱可能把位置移动到不合理区域。

置换测量模型对破坏关联的响应，不是模拟真实干预。合理特征组共同置换或条件置换可以回答更合适的问题，但会改变估计目标、引入新的假设。

时间序列或同一门店多行记录不一定可以自由交换。应按任务研究分组、分块等协议，不把默认行置换解释成真实业务变化。

## 10. 解释报告至少应交代什么？

模型版本、字段表示、数据范围与时间、scoring、重复次数、随机种子和置换组定义，决定了报告含义。

重要字段若线上经常缺失，仍可能不适合部署；低重要字段若便宜且改善特定群体，也不一定立即删掉。应结合覆盖率、成本和子群体表现。

本篇只实跑总体置换与组置换，未运行 SHAP、因果推断或局部归因。总体排行不能直接作为某条门店记录的完整解释。

## 11. 练习与答案

1. 置换时要重训吗？答：普通方法不重训。
2. 重要性=4 是概率吗？答：不是，是给定指标下的分数下降。
3. 单列不重要代表相关整组无用吗？答：不，其他列可能提供替代信息。
4. 置换标准差覆盖漂移吗？答：不，它只覆盖当前条件下的打乱波动。
5. 字段重要证明因果影响吗？答：不，它描述当前模型依赖。

## 来源与验证

核验日期：2026-10-04。基于 [scikit-learn 官方开源文档 permutation_importance.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/permutation_importance.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。中文解释、代码与业务延伸独立编写，非官方逐字翻译。示例使用 scikit-learn 1.8.0 核验；固定来源主分支与安装版本不完全相同。

[返回目录](README.md)
