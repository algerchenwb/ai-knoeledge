# AI 知识扩充：从模型内部到工程落地

本轮新增18篇正文，分成6个专题，主要核对10个GitHub开源项目。它们补充原有机器学习、深度学习和微软生成式AI课程，重点讲清机制及可以验证的工程边界。

## 已完成的正文

| 专题 | 篇数 | 核心知识 |
| --- | --- | --- |
| [Transformer 内部机制](../transformer/README.md) | 5 | Embedding 与位置；注意力与掩码；残差、归一化与前馈层；标签对齐、交叉熵与困惑度；解码与采样 |
| [检索算法与质量](../retrieval/README.md) | 3 | 相似度与检索评估；Flat、IVF、HNSW 与 PQ；混合检索与重排 |
| [微调与偏好对齐](../post-training/README.md) | 3 | SFT 数据与损失掩码；LoRA 与 QLoRA；DPO、GRPO 与奖励投机 |
| [模型推理与服务性能](../inference/README.md) | 3 | Prefill、Decode 与 KV Cache；量化与内存预算；批处理、调度与延迟 |
| [多模态基础](../multimodal/README.md) | 2 | CLIP 与对比学习；扩散模型与调度器 |
| [强化学习基础](../reinforcement-learning/README.md) | 2 | MDP、策略、价值与 Q-learning；环境、终止、截断与评估 |

每篇均有通俗解释、机制或公式、业务例子、误区/边界、练习与来源。计数只包含正文，不把导航、来源和验证文件算成知识文章。

## 按需要选路线

- 想读懂LLM代码：先[已有张量/求导基础](../deep-learning-basics/README.md)，再读Transformer五篇。
- 想改善API知识检索：先读检索三篇，再接[已有RAG证据验证](../../courses/generative-ai-for-beginners/deep-dives/15-rag-evidence-and-validation.md)。
- 想训练任务模型：先读SFT数据，再LoRA，最后偏好对齐；配合[已有评估](../ml-evaluation/README.md)。
- 想部署模型服务：按KV缓存、量化、调度顺序读，结合真实负载评测。
- 想扩大AI知识面：多模态和强化学习独立入门，不要求先运行大模型。

## 运行与来源

```bash
python knowledge/expansion-2026-10/examples/ai_math_checks.py
```

只用Python标准库，无需API Key、网络、第三方库或GPU。已在Python 3.12.14通过15组数学检查，详见[验证记录](VALIDATION.md)。这些检查验证例子，不证明真实模型效果或硬件性能。

[固定来源与许可](SOURCES.md) · [机器可读来源](sources.json) · [全库导航](../../README.md)

## 后续已经补充

[训练工程详解](../training-engineering/README.md)已新增8篇与13组标准库实验，覆盖优化器、调度、数据加载、累积、混合精度、恢复和DDP；它们是本轮18篇之后的续篇，不改变上表历史计数。

## 后续缺口：尚未完成

以下是未来扩展方向，不计入本轮已完成文章，也不是已自动安排的任务：

- 训练工程进阶：FSDP/ZeRO、真实GPU profiler、分布式checkpoint和端到端框架训练。
- 模型结构：CNN、RNN、RoPE细节、MoE、状态空间模型。
- 数据与评估：数据标注/去重、OOD、校准、LLM评测集、统计显著性。
- 检索进阶：中文BM25实作、稀疏检索、图检索、查询重写、领域embedding训练。
- 多模态进阶：视觉语言生成、OCR/图表、语音识别/合成、视频建模。
- 智能体进阶：规划、工具轨迹、持久状态、失败恢复与端到端执行评估。

每个后续专题应先盘点现有内容，查阅主要开源实现，固定来源，并明确哪些示例已运行。
