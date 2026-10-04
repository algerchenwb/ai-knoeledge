# 训练工程：验证记录

日期：2026-10-04。Python 3.12.14，未安装PyTorch。本轮新增8篇正文，参考4个开源项目；原有正文保持不变，总入口和旧路线补充交叉链接。

## 执行命令

```bash
python knowledge/training-engineering/examples/training_math_checks.py
```

13组标准库检查全部通过，完整输出保存在[results.json](examples/results.json)。

| 检查 | 结果 |
| --- | --- |
| SGD与过大学习率 | 一步w=0.6、loss=5.76；过大lr后loss=12.96 |
| Adam校正/AdamW衰减 | m_hat=2、v_hat=4；纯衰减w=9.99 |
| 学习率边界/更新计数 | warmup到0.1，余弦中点0.055，结束0.01；尾窗口计入为21次 |
| padding/丢尾 | padding占25%；10条、batch4时drop_last丢2条 |
| 等长梯度累积 | 完整/累积梯度均-25.5，与有限差分一致 |
| 不等长token | 正确全局平均2.6，错误平均2 |
| 尾累积窗口 | 实际2份归一化得2；错除计划4份得1 |
| DDP分子分母 | 模拟全局梯度2.6；正确准确率0.1，错误rank平均0.5 |
| 反缩放与裁剪顺序 | 正确[0.6,0.8]，错误[0.006,0.008] |
| half下溢 | 1e-8直接舍入为0；缩放后能保留非零结果 |
| sampler补齐 | 5项分到两rank共6槽，ID0重复 |
| 完整状态恢复 | 连续20步与7+13步的后续轨迹、最终状态及RNG完全一致 |
| 故意漏状态 | 漏momentum/RNG/数据游标分别导致不同最终参数 |

恢复实验用临时JSON文件经历实际序列化/加载；它不是PyTorch checkpoint，也没有真实DataLoader worker状态。恢复后的标量权重与连续训练相同约2.23432993，只说明示例轨迹一致，不代表这个20步模型已经收敛或训练效果优良。

## 文档校验

本轮文件的相对链接按远程已有文件和本轮文件的合并集合检查；Markdown代码围栏检查闭合；正文来源使用固定40位提交SHA。来源文件已通过GitHub读取核对。

## 没有做的验证

未运行PyTorch/Accelerate训练集成、真实GradScaler/autocast、多个DataLoader worker、分布式进程组、GPU profiler、激活checkpoint或多卡恢复。没有真实模型准确率、显存峰值、吞吐与加速比结果。

教学scheduler边界不与nanoGPT逐步等价；模拟DDP只演示缩放数学，不执行通信；half实验使用Python二进制16bit舍入，不证明特定GPU kernel的次正规数行为。许可与来源见[SOURCES.md](SOURCES.md)。
