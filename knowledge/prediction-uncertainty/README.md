# 预测区间与不确定性基础

从点预测走向明确说明含义、前提和验证范围的区间输出。

| 文章 | 主要内容 |
| --- | --- |
| [预测区间与覆盖率](01-prediction-intervals-and-coverage.md) | 置信/预测区间、宽度、总体与分组覆盖、数据角色、漂移 |
| [Split conformal 手算](02-split-conformal-by-hand.md) | 绝对误差、有限样本秩、无穷边界、固定宽度与模拟 |

建议先读 [评估基础](../ml-evaluation/README.md)；时间相关数据还应结合 [时间序列](../time-series/README.md)。本批只完成基础 split-conformal 机制，不把其他方法计为已实现。

## 实际运行与结果

```bash
python knowledge/prediction-uncertainty/examples/conformal_checks.py
```

核验日期：2026-10-04。脚本仅依赖标准库，已执行并通过：

- n=9 时，α=0.2/0.1/0.05 分别给出半宽 8/9/+∞。
- 固定人工测试覆盖率 0.8、区间宽度 16。
- 示例整体覆盖 0.9，而少数群体覆盖为 0。
- 4000 次可交换均匀分数模拟，经验覆盖率 0.90025。
- 新分数整体偏移的人工漂移模拟覆盖为 0。
- 分数排序、重复分数和区间批次约定检查通过。

模拟只检查教学机制，不证明定理、不验证现实门店数据；可交换模拟与漂移模拟使用明确的人造生成规则。环境未安装 MAPIE，本批未运行 MAPIE 库、CQR、时间序列 conformal、真实模型训练或生产服务。

来源以 MAPIE 官方开源文档为主，有限样本公式补充核对原理论文；固定来源、署名和许可见 [SOURCES.md](SOURCES.md)。

[返回总入口](../../README.md)
