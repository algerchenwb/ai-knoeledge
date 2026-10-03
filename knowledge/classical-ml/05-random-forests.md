# 05｜随机森林：为什么很多棵不同的树会更稳？

> 先修：[决策树](04-decision-trees.md)。目标：理解 bootstrap、随机特征、概率平均、OOB 与特征重要性的边界。

## 1. 集成不是简单复制同一个模型

如果十棵树完全相同，它们会犯同样错误，平均预测几乎没有新价值。随机森林希望各棵树既有预测能力，又不要完全一致。

直观上，一个模型高估、另一个低估，平均可能抵消部分误差；但如果所有模型都被同一个泄漏字段误导，它们会一起失败。集成缓解某些方差问题，不会自动修复数据协议。

## 2. 两个随机来源

### Bootstrap 样本

每棵树常从训练数据有放回抽样。抽 N 次仍只有 N 个抽样位置，但某些原始样本出现多次，另一些没出现。

一个样本一次没被抽到的概率为 1−1/N，N 次均未被抽到的概率为 (1−1/N)^N，N 较大时约为 e⁻¹≈36.8%。因此每棵树大约看见 63.2% 的不同原始样本。

这不表示训练数据损失了 36.8%；不同树抽样不同，样本可参与其他树。这个比例对应典型抽 N 次设置，不能无条件推广到其他 max_samples 配置。

### 每个节点的随机候选特征

树在节点分裂时只考虑一部分候选特征，减少所有树总使用同一强特征的倾向。max_features 控制候选规模。

它通常不是“每棵树永久删除一批列”，而是在分裂过程中随机挑候选。较小候选集增加差异，也可能削弱单棵树，必须验证折中。

## 3. 最终预测怎样合并？

回归通常平均各树数值预测。

scikit-learn RandomForestClassifier 通常平均各树类别概率，再选择平均概率最高的类别。不要不加区分地说实现永远是“每棵树硬投一票”。

例如三棵树给正类概率 [0.51,0.51,0.01]。硬投票有两棵赞成正类；平均概率约 0.3433，最终偏向负类。这展示两种合并方式可产生不同结果。

平均概率仍需校准检查；多棵树平均不等于获得真实世界的确定性。

## 4. OOB：没有抽到的样本能做什么？

某样本对某棵树是 out-of-bag，表示这棵树的 bootstrap 抽样没有包含它。只汇总没见过该样本的树，可得到 OOB 预测并评估。

它利用 bootstrap 带来的自然留出，但不是万能独立测试：

- 同一 POI 其他日期仍可能进入这些树，OOB 不能隔离地点。
- 时间表中未来样本可能进入树，OOB 不自动模拟历史预测未来。
- 在全量开发数据上 fit 的预处理可能影响 OOB 样本。
- 反复用 OOB 分数选配置，也会对其产生选择偏差。
- 树数量过少时，某些样本可能缺少可靠 OOB 预测。

因此 OOB 适用于满足相应样本假设的内部估计，不能替代业务要求的分组、时间验证和最终独立测试。

## 5. 怎样调参？

| 参数 | 主要影响 | 实际取舍 |
| --- | --- | --- |
| n_estimators | 树数量 | 更多树通常提高平均稳定性，但成本增加且收益递减 |
| max_features | 分裂候选特征数量 | 单树能力与树间差异 |
| min_samples_leaf | 叶子最小样本量 | 概率/数值平滑与局部细节 |
| max_depth | 树深度 | 拟合能力、内存与推理成本 |
| bootstrap | 是否有放回采样 | 改变随机性和 OOB 适用性 |
| n_jobs | 并行工作数量 | 运行资源，不直接表示模型复杂度 |

更多树不保证每次测试分数单调变好。对在线接口，应同时关注加载内存、延迟和吞吐；不能只报告离线准确率。

## 6. 一个可运行的概率平均例子

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

X = np.array([[i, i % 3] for i in range(12)], dtype=float)
y = np.array([0]*6 + [1]*6)
forest = RandomForestClassifier(
    n_estimators=40, max_depth=3, min_samples_leaf=2,
    max_features="sqrt", random_state=42, n_jobs=1
).fit(X, y)
X_check = np.array([[2., 2.], [9., 0.]])
per_tree = np.stack([tree.predict_proba(X_check) for tree in forest.estimators_])
averaged = per_tree.mean(axis=0)
print("forest probability", forest.predict_proba(X_check))
assert np.allclose(averaged, forest.predict_proba(X_check))
assert np.allclose(averaged.sum(axis=1), 1)
```

此例确认实现的合并机制，不是泛化评估。真实训练仍要按任务留出数据；类别列对应关系要看模型的 classes_，不要将某列永远当成业务正类。

## 7. 特征重要性为什么可能误导？

基于不纯度下降的 feature_importances_ 衡量模型训练中各特征对分裂改善的贡献。它容易偏好取值多、候选切分多的特征，可能给无用 ID 较高重要性。

Permutation importance 在指定评估数据上打乱一列，观察分数下降，描述模型在这份数据上的依赖。它也有边界：

- 两列高度相关时，一列打乱后另一列能代替，单列重要性可能偏低。
- 模型整体预测很差时，重要性不能拯救结论。
- 打乱可能制造现实中不可能的特征组合。
- 重要性不是因果效应，也不是“删掉此列重训后的性能差”。

如果使用验证数据的特征重要性决定下一次改动，那份数据就参与了模型选择；最终测试仍应隔离。

## 8. ExtraTrees 与随机森林

ExtraTrees 在阈值选择上进一步随机化，再从随机候选中选较好分裂。不同方法的 bootstrap 默认设置也可能不同。

不要把“树越随机越好”当作结论。随机性可降低树间相关，也可能增加偏差。应在同一数据协议、指标和资源预算下比较。

## 9. 练习与答案

1. 三棵树硬投票与概率平均一定一样吗？  
   答：不一定，[0.51,0.51,0.01] 就是反例。

2. OOB 是否保证同一地点不跨训练和评估？  
   答：不能，它隔离抽样记录，不自动隔离地点。

3. 一列重要性最高是否证明它造成客流变化？  
   答：不证明，它反映特定模型与数据下的关联和依赖。

4. n_jobs 增大是否让森林更聪明？  
   答：它主要影响执行并行度，不直接改变树数量或模型能力。

## 来源与验证

核验日期：2026-10-04。主要来源：[scikit-learn 官方开源文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/ensemble.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。中文解释、业务场景、算例与代码独立编写，不是官方逐字翻译。来源项目采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。示例在 scikit-learn 1.8.0 验证；来源主分支与安装版本不完全相同，其他 API 请核对使用版本。

补充来源：[Permutation importance 官方文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/permutation_importance.rst)，用于模型依赖与重要性解释的边界。
