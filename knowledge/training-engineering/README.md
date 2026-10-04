# 深度学习训练工程

承接[张量、求导与基础训练循环](../deep-learning-basics/README.md)，把训练循环中容易被忽略的工程机制拆开讲清。已完成8篇正文，不将导航、来源或验证文件计入正文篇数。

## 阅读顺序

1. [优化器：SGD、Momentum、Adam/AdamW](01-sgd-momentum-adamw.md)
2. [学习率：Warmup与余弦调度](02-learning-rate-warmup-and-schedules.md)
3. [Dataset、DataLoader与padding](03-dataset-dataloader-and-padding.md)
4. [梯度累积与token归一化](04-gradient-accumulation-and-token-normalization.md)
5. [AMP、梯度缩放与裁剪](05-amp-gradient-scaling-and-clipping.md)
6. [Checkpoint与训练恢复](06-checkpoints-and-exact-resume.md)
7. [DDP、分布式采样与全局指标](07-ddp-sampling-and-global-metrics.md)
8. [显存、重计算、性能与复现](08-memory-profiling-and-reproducibility.md)

每篇包含直觉、机制或公式、手算/工程例子、常见误区、练习与固定来源。优化器统计、token分母、AMP顺序与恢复状态都有相应数学实验。

## 运行实验

```bash
python knowledge/training-engineering/examples/training_math_checks.py
```

Python标准库即可，无API Key、模型下载或GPU。已在Python 3.12.14通过13组检查，详见[验证记录](VALIDATION.md)；包括连续训练与完整状态恢复轨迹一致，以及故意漏状态后轨迹不同。

这些是独立数学与状态机制实验，不是PyTorch/Accelerate训练器集成，不提供真实模型效果、DDP通信或GPU性能结果。

## 开源来源

参考PyTorch、PyTorch Tutorials、Accelerate与nanoGPT，共4个项目。来源快照、文件和许可见[SOURCES.md](SOURCES.md)。

## 与已有内容衔接

- [SFT数据与损失mask](../post-training/01-sft-data-and-loss-masks.md)：决定监督什么；本专题解释如何累计与更新。
- [LoRA/QLoRA](../post-training/02-lora-and-qlora.md)：改变可训练参数和权重存储，不消除训练状态与激活成本。
- [语言模型训练目标](../transformer/04-language-model-objective.md)：标签对齐、交叉熵、有效token与困惑度。
- [模型推理内存](../inference/01-prefill-decode-and-kv-cache.md)：推理KV缓存与训练激活不是同一份内存。
- [评估基础](../ml-evaluation/README.md)：训练loss下降之后，仍需验证数据泄漏与真实任务表现。

## 尚未完成的进阶方向

FSDP/ZeRO、张量/流水线并行、真实GPU profiler、分布式checkpoint、可恢复流式数据加载，以及端到端PyTorch/Accelerate训练实验。未完成部分不计入本轮成果。

[返回全库](../../README.md)
