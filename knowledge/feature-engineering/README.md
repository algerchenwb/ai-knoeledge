# 特征工程基础

把业务字段转换成模型可以稳定学习、上线可以一致重现的表示。

| 文章 | 主要内容 |
| --- | --- |
| [数值缩放与缺失值](01-scaling-and-missing-values.md) | Standard/MinMax/Robust、稀疏输入、填补与缺失指示、标签缺失 |
| [类别编码与组合流水线](02-categorical-encoding-and-pipelines.md) | ordinal/one-hot、未知类别、高基数、target cross fitting、按列处理 |

建议衔接 [评估基础](../ml-evaluation/README.md) 和 [经典机器学习](../classical-ml/README.md)。每篇有业务例子、数学或完整步骤、误区、练习与答案。

## 验证与运行

```bash
python knowledge/feature-engineering/examples/feature_checks.py
```

核验日期：2026-10-04。已在 scikit-learn 1.8.0、NumPy 2.3.5 运行并通过：训练统计量复用、新值超出 MinMax 范围、中位填补与指示列、未知 one-hot、目标编码 cross fitting、ColumnTransformer 输出与字段名。

关键数值：40 标准化为 2.4494897428；唯一类别完整目标编码为 [0,2,4,6]，两折训练编码为 [5,5,1,1]。这些检查验证具体人工数据与 API 行为，不证明真实门店预测质量。

未运行复杂填补、高维大规模稀疏训练或线上部署。源码阅读快照与本地安装版本分别记录，不声称逐行一致。来源与许可见 [SOURCES.md](SOURCES.md)。

[返回总入口](../../README.md)
