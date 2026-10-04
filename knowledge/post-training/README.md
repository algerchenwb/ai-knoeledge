# 微调与偏好对齐

这是基于开源代码/文档核验的独立中文详解，采用直觉解释、数学或形状、工程场景、误区与练习的顺序。

## 阅读顺序

1. [SFT 数据与损失掩码](01-sft-data-and-loss-masks.md)
2. [LoRA 与 QLoRA](02-lora-and-qlora.md)
3. [DPO、GRPO 与奖励投机](03-preference-dpo-and-grpo.md)

## 来源与验证

核验日期：2026-10-04。主要来源：[huggingface/peft](https://github.com/huggingface/peft)、[huggingface/trl](https://github.com/huggingface/trl)。每篇末尾提供固定提交链接；完整快照与许可见[来源清单](../expansion-2026-10/SOURCES.md)。

本专题的中文讲解、业务例子和标准库数学演示独立编写，没有整段搬运上游文档。基础数学示例已在Python 3.12.14运行；没有下载大模型、运行GPU训练或做真实硬件性能基准。具体对应检查见[验证记录](../expansion-2026-10/VALIDATION.md)。

[扩充总导航](../expansion-2026-10/README.md) · [全库入口](../../README.md)
