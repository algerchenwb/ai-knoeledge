# 模型推理与服务性能

这是基于开源代码/文档核验的独立中文详解，采用直觉解释、数学或形状、工程场景、误区与练习的顺序。

## 阅读顺序

1. [Prefill、Decode 与 KV Cache](01-prefill-decode-and-kv-cache.md)
2. [量化与内存预算](02-quantization-and-memory.md)
3. [批处理、调度与延迟](03-batching-scheduling-and-latency.md)

## 来源与验证

核验日期：2026-10-04。主要来源：[huggingface/transformers](https://github.com/huggingface/transformers)、[vllm-project/vllm](https://github.com/vllm-project/vllm)、[huggingface/peft](https://github.com/huggingface/peft)。每篇末尾提供固定提交链接；完整快照与许可见[来源清单](../expansion-2026-10/SOURCES.md)。

本专题的中文讲解、业务例子和标准库数学演示独立编写，没有整段搬运上游文档。基础数学示例已在Python 3.12.14运行；没有下载大模型、运行GPU训练或做真实硬件性能基准。具体对应检查见[验证记录](../expansion-2026-10/VALIDATION.md)。

[扩充总导航](../expansion-2026-10/README.md) · [全库入口](../../README.md)
