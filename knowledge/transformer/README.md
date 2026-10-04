# Transformer 内部机制

这是基于开源代码/文档核验的独立中文详解，采用直觉解释、数学或形状、工程场景、误区与练习的顺序。

## 阅读顺序

1. [Embedding 与位置](01-embeddings-and-position.md)
2. [注意力与掩码](02-attention-and-masks.md)
3. [残差、归一化与前馈层](03-blocks-residuals-and-normalization.md)
4. [标签对齐、交叉熵与困惑度](04-language-model-objective.md)
5. [解码与采样](05-decoding-and-sampling.md)

## 补充验证实验

- [注意力输入干预与不变性实验](labs/attention-invariants.md)：逐步计算 Q/K/V，运行屏蔽隔离、因果隔离、置换等变、稳定 softmax 与位置编码检查，附标准库脚本及 D2L 固定来源。

## 来源与验证

核验日期：2026-10-04。主要来源：[karpathy/nanoGPT](https://github.com/karpathy/nanoGPT)。每篇末尾提供固定提交链接；完整快照与许可见[来源清单](../expansion-2026-10/SOURCES.md)。

本专题的中文讲解、业务例子和标准库数学演示独立编写，没有整段搬运上游文档。基础数学示例已在Python 3.12.14运行；没有下载大模型、运行GPU训练或做真实硬件性能基准。具体对应检查见[验证记录](../expansion-2026-10/VALIDATION.md)。

[扩充总导航](../expansion-2026-10/README.md) · [全库入口](../../README.md)
