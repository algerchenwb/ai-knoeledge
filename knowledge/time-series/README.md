# 时间序列预测与回测基础

面向客流、销量、需求等有时间顺序的数据，从可用信息、特征构建和模拟上线评估开始。

| 文章 | 覆盖内容 |
| --- | --- |
| [滞后与信息可用性](01-lags-and-information-availability.md) | lag/rolling、先移位、实体分组、时间轴、多步预测 |
| [回测与预测指标](02-backtesting-and-forecast-metrics.md) | 扩展/滑动窗口、gap、标签成熟、基线、horizon 与汇总 |

衔接 [特征工程](../feature-engineering/README.md) 和 [评估基础](../ml-evaluation/README.md)。每篇有例子、机制、误区及练习答案。

## 已运行验证

```bash
python knowledge/time-series/examples/temporal_checks.py
```

核验日期：2026-10-04。使用 scikit-learn 1.8.0，已验证：历史窗口不随未知目标/未来值变化、未移位窗口包含目标、全表滞后会串门店、TimeSeriesSplit 的顺序与 gap、标签结束边界、滑动窗口上限、随机拆分的未来训练行、周期基线及 pooled/macro 指标差异。

三折 train/test 分别为 0..3/6..7、0..5/8..9、0..7/10..11，gap 均为 2 行。人工周序列季节性基线 MAE=0、上一期基线 MAE≈17.142857；示例 pooled MAE=1、每门店平均 MAE=5。

这是人工机制与 API 验证，未下载官方自行车数据集，未训练真实预测模型，未实现不规则时间或面板数据专用切分器，也未证明业务预测效果。来源与许可见 [SOURCES.md](SOURCES.md)。

[返回总入口](../../README.md)
