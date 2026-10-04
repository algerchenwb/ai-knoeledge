# 17｜模型保存与上线输入协议：文件能加载，还不代表预测正确

> 目标：保存完整预测流程，理解格式与版本边界，明确字段、类别映射、阈值和回归验证。本文是工程学习教程，不部署真实服务。

## 1. 真正需要保存的是什么？

一个分类器可能只看到缩放后的数值。如果训练时面积均值为 120、标准差为 40，原始面积 200 被转换为 2；上线若直接把 200 送入分类器，文件虽然能加载，预测含义却变了。

通常应保存完整拟合 Pipeline，包括缺失处理、缩放、类别编码、特征选择和最终模型的状态。词表、IDF、选中字段等同样属于已学习的预测流程。

Pipeline 不能替你保存所有外部业务逻辑：客流统计窗口、坐标转换、接口字段映射、时间可用性仍可能位于模型之外。应明确哪些转换在模型内，哪些由调用端负责。

## 2. 保存格式怎样选择？

| 格式 | 常见用途 | 需要明确的边界 |
| --- | --- | --- |
| pickle | Python 对象保存，标准库可用 | 加载可能执行代码；依赖目标环境 |
| joblib | Python 模型和 NumPy 数组，某些场景可内存映射 | 同样基于 pickle，不是安全沙箱 |
| cloudpickle | 某些动态函数或非包化对象 | 不保证向前兼容，环境仍重要 |
| skops.io | 对对象类型和引用进行更显式检查 | 支持范围、可信类型与环境仍需核对 |
| ONNX | 将支持的预测计算导出到推理运行时 | 转换支持、输入类型、算子与输出一致性需验证 |

没有一种格式自动包办特征语义、版本迁移与部署验收。ONNX 通常不用于恢复原始 Python 训练对象；skops 也不能用“把所有未知类型都设成可信”来替代审阅。

本文实跑 joblib 保存自己刚训练的本地示例，未运行 skops、cloudpickle 或 ONNX 转换。

## 3. 信任来源与 SHA-256 是两个问题

pickle、joblib、cloudpickle 的加载可能执行任意代码，不能把来自陌生来源的模型文件当普通数据加载。此限制来自上游持久化文档。

文件摘要可以发现文件是否与可信记录一致，但不能自动确认发布者身份。攻击者若同时替换文件与 manifest，摘要仍可能匹配。身份与发布来源需要独立可信机制，不能仅靠同目录里的哈希。

示例只加载本程序刚产生的文件与 manifest，并检查字节变化；它没有实现签名、权限控制或完整安全下载流程。应先确定来源，再做兼容性和一致性验证。

## 4. 同样的字段数量，不等于同样的输入

模型输入两个数，训练协议为 [area_m2,population_500m]。如果调用方按字典遍历顺序构成 [population_500m,area_m2]，形状仍是 [N,2]，却交换了意义。

因此接口应先校验字段，再按明确的 schema 顺序构造矩阵，而不是依赖 JSON 键顺序或语言容器的临时排列。

示例 schema 为：
- area_m2：面积，平方米，有限非负数。
- population_500m：500 米口径内的人口指标，有限非负数。
- 每行必须恰好包含这两个字段；多余字段不静默接受。
- 不接受布尔、数字字符串、NaN 或负值。

这些规则只针对本例，不是所有人口接口的通用规范。实际系统还应明确人数是估算、去重还是某月快照，面积是建筑面积还是营业面积。语义和单位不能只写一个 float 类型。

## 5. 可运行输入转换的核心

```python
import numpy as np

SCHEMA = ["area_m2", "population_500m"]

def rows_to_matrix(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a nonempty list")
    matrix = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(SCHEMA):
            raise ValueError("exact field set required")
        values = []
        for field in SCHEMA:
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("numeric values required")
            if not np.isfinite(value) or value < 0:
                raise ValueError("finite nonnegative values required")
            values.append(float(value))
        matrix.append(values)
    return np.array(matrix, dtype=np.float64)
```

Python 中 bool 是 int 的子类，需先拒绝 bool。允许什么类型、是否转换字符串、如何处理缺失，应该由协议决定；不能无声猜测。

此函数面向已解码 JSON 的基本数字类型，不接受全部 NumPy 标量类型。没有实现请求大小上限、重复 JSON 键检测或统计业务合理性检查；这些应在对应解析或服务层设计。

缺失不一定必须拒绝。若训练明确包含缺失处理，可以按同一策略接受；但不能在上线时临时填零，假装与训练协议一致。

## 6. 完整保存与加载实验

完整代码：[model_persistence_contract_checks.py](examples/model_persistence_contract_checks.py)。

```bash
python knowledge/classical-ml/examples/model_persistence_contract_checks.py
```

依赖 NumPy、SciPy、joblib 与 scikit-learn。程序在临时目录保存并加载自己训练的 StandardScaler + LogisticRegression，不下载文件，不开启网络服务；结束后临时模型自动清理。

程序执行：

1. 按 schema 将六条人工记录构造成训练矩阵。
2. 拟合完整 Pipeline，用两条请求生成保存前概率。
3. 保存 Pipeline 与 JSON manifest。
4. 检查环境、schema 和摘要后加载，再核对列数与类别映射。
5. 比较保存前后概率，并按明确正类与阈值生成决策。
6. 修改本地文件字节，确认在 joblib.load 前拒绝摘要不匹配的文件。

人工训练数据很小，只验证持久化和协议机制，不提供泛化性能结论。

## 7. manifest 为什么值得单独记录？

| 项目 | 用途 | 不能替代什么 |
| --- | --- | --- |
| schema 与版本 | 明确字段顺序和接口版本 | 业务语义文档、真实性验证 |
| 环境版本 | 提前识别不同运行环境 | 跨版本兼容保证 |
| classes 与正类标签 | 正确解释概率列 | 概率校准、业务授权 |
| 决策阈值 | 重现具体行动规则 | 阈值成本验证 |
| 模型摘要 | 发现字节变化 | 发布身份认证 |
| 训练数据引用 | 找到人工样本或不可变快照 | 完整可重现训练记录 |

本例 manifest 记录 Python、NumPy、SciPy、scikit-learn 和 joblib 版本，并要求字符串完全匹配。这是简单的示例策略，不是所有项目必须使用的唯一兼容规则。

真实训练还应保存源码提交、依赖锁定、数据快照、字段定义、超参数、随机种子、交叉验证协议与指标。只记模型类名，不足以重建训练。

## 8. 正类不一定在第 1 列

示例标签为 "high" 与 "low"，classes_ 的实际顺序为 ["high","low"]，所以 p(high) 在第 0 列。

应通过类别映射定位：

```python
positive_column = np.flatnonzero(model.classes_ == "high")[0]
p_high = model.predict_proba(X)[:, positive_column]
```

这段展示定位方法；其中 model 和 X 应来自已拟合模型及按协议转换的输入。完整脚本包含对应对象和检查。

概率与决策也不是同一输出。示例阈值为 0.5，用 p_high>=0.5 生成 high/low；真实阈值应依据开发验证与成本决定，不应根据最终测试反复调整。

多分类、异常模型和只有 decision_function 的模型输出协议不同。不能给所有模型统一贴一个“confidence=输出第一列”的含义。

## 9. 版本兼容：成功加载不是支持保证

scikit-learn 不提供跨不同版本加载已保存模型的支持保证。另一个版本偶然能加载，仍可能行为变化或报错；不能仅以 load 未抛异常判断兼容。

遇到环境升级，优先重建可复现训练环境，或在新环境重新训练并按相同评估协议验收。警告捕获可辅助诊断，不会自动迁移模型，也不能作为反序列化安全屏障。

自定义变换和函数还可能依赖模块路径。训练脚本里临时定义的 lambda 或类，目标环境未必可导入。应评估包化、版本固定及格式支持，而不是随意改为另一种序列化格式后宣布长期可用。

## 10. 跨语言服务应验证计算与输入两层

Go 服务可以调用 Python 推理服务，或使用支持的转换模型和运行时。两条路径都要明确输入 dtype、shape、字段顺序、类别输出与错误响应。

若导出 ONNX，应验证支持的预处理是否一并转换，比较代表样本、极端值、缺失策略和类别边界的结果。float32 与 float64、运行时版本和算子实现可能导致差异，误差容限应根据任务设定。

本文没有安装或测试 Go ONNX Runtime，也没有提供性能比较；不能把格式可跨语言理解成当前项目已经可直接上线。

## 11. 回归验证应覆盖哪些内容？

持久化往返一致，是最基本的检查；还应关注输入转换一致性、类别映射、阈值决策和无效输入处理。

本例运行结果：
- 六类无效请求全部拒绝。
- 两条 p(high) 约为 [0.2104,0.8814]，阈值决策为 [low,high]。
- 保存前后最大概率差为 0。
- 修改文件后在反序列化前拒绝。

这些结果仅在已运行环境与人工样本下成立。程序没有执行真实业务准确率评估、负载测试、并发发布或环境迁移。

更新模型时，应将模型、schema、阈值和 manifest 作为对应的一组版本发布，避免新模型配旧字段协议。如何原子切换、回滚和记录服务版本属于进一步工程设计，不能从 dump 成功推断发布正确。

## 12. 练习与答案

1. 只保存最终分类器就够吗？答：若依赖已拟合预处理，通常不够，应保存完整流程及外部协议。
2. JSON 字段相同但顺序不同该怎么办？答：按 schema 明确重排，而不是依赖传入顺序。
3. 摘要匹配证明来源可信吗？答：不，摘要记录也可能被替换。
4. 正类概率一定是 predict_proba 的第 1 列吗？答：不，应检查 classes_。
5. 跨版本 load 成功证明兼容吗？答：不，需遵守支持边界并验证或重新训练。
6. 概率往返一致证明上线业务效果好吗？答：不，它只验证对应计算的持久化一致性。

## 来源与验证

核验日期：2026-10-04。主要来源：[scikit-learn model_persistence.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/model_persistence.rst)，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。输入协议、manifest 和版本组合建议为独立工程延伸；中文讲解与代码独立编写，非官方逐字翻译。

实跑环境：Python 3.12.14、NumPy 2.3.5、SciPy 1.17.0、scikit-learn 1.8.0、joblib 1.5.3。固定来源主分支与安装版本不完全相同。仅测试可信本地 joblib 文件，未测试 ONNX、skops、cloudpickle、跨版本加载或真实服务部署。

[返回专题目录](README.md)
