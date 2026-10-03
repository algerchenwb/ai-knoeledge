# 第00–21课深化笔记

这些笔记在课程概览基础上进一步解释机制、业务案例、失败模式和后端实现。原课程解读与原创工程扩展均在各篇说明；目录更新日期：2026-10-04；各篇核对日期见正文。

| 课次 | 深化笔记 | 重点 |
| --- | --- | --- |
| 00 | [环境与故障定位](00-environment-and-failure-diagnosis.md) | 解释器、WSL、凭据、Notebook与排错分层 |
| 01 | [Token、训练与生成](01-tokens-training-and-generation.md) | 自回归、上下文、采样、幻觉与职责边界 |
| 02 | [模型选择与对照评测](02-model-selection-and-controlled-evaluation.md) | 多维分类、硬约束、任务集、质量与成本 |
| 03 | [负责任AI控制与验收](03-responsible-ai-controls-and-acceptance.md) | 风险登记、公平、缓解层、透明与事故处理 |
| 04 | [提示词设计与验证](04-prompt-design-and-validation.md) | Token、任务结构、数据口径、模板、缺项、评测 |
| 05 | [高级提示词与失败模式](05-prompt-techniques-and-failure-modes.md) | 示例、任务分解、自检、事实依据、采样与无解条件 |
| 06 | [文本生成后端服务](06-text-generation-service.md) | 请求生命周期、输出验证、超时重试、流式与成本 |
| 07 | [聊天状态与评测](07-chat-state-and-evaluation.md) | 业务状态、历史压缩、并发、领域定制与任务指标 |
| 08 | [语义搜索与索引](08-semantic-search-and-indexing.md) | Embedding、切块、余弦、索引升级、混合检索与评测 |
| 09 | [图像生成与交付](09-image-generation-delivery.md) | 提示词、编辑、Base64、文件校验与异步任务 |
| 10 | [低代码工作流边界](10-low-code-workflow-boundaries.md) | 数据模型、发票抽取、重复事件、异常恢复与后端分工 |
| 11 | [Function Calling执行](11-function-calling-execution.md) | 工具契约、调用循环、鉴权、幂等与安全执行 |
| 12 | [AI体验、信任与恢复](12-ai-ux-trust-and-recovery.md) | 结果卡、可核查依据、状态、纠正与可访问性 |
| 13 | [安全与信任边界](13-ai-security-trust-boundaries.md) | 提示注入、租户隔离、知识污染、输出防护与红队 |
| 14 | [LLMOps评测与发布](14-llmops-evaluation-and-releases.md) | 评测集、版本、Trace、发布门槛、灰度与回滚 |
| 15 | [RAG证据与验证](15-rag-evidence-and-validation.md) | 证据传递、原课代码差异、来源、冲突与评测 |
| 16 | [开放模型资产与部署](16-open-model-assets-and-deployment.md) | 权重、模板、许可、版本、任务评测与部署清单 |
| 17 | [Agent状态与有界工作流](17-agent-state-and-bounded-workflows.md) | 权威状态、预算、停止、回执、幂等与原例边界 |
| 18 | [微调数据与适配器](18-fine-tuning-data-and-adapters.md) | SFT、LoRA、QLoRA、数据泄漏、loss mask与交付 |
| 19 | [小模型内存与推理](19-small-model-memory-and-inference.md) | 权重、KV cache、MoE、量化、WSL与性能验收 |
| 20 | [Mistral RAG与Tokenizer实验](20-mistral-rag-and-tokenizer-experiments.md) | 下载、切块、FAISS、有效近邻、时延与计数 |
| 21 | [Llama工具协议与视觉输入](21-llama-tool-protocol-and-vision-inputs.md) | 模板、调用建议、受控执行、视觉与合成数据 |



建议按04→05→06→07阅读基础应用，再继续08→09→10→11；12→13→14→15用于可靠交付和RAG深化。实践时先理解业务定义，再实现确定性校验，最后让模型生成说明。

## 示例验证记录

第06课的报告校验代码、第07课的状态变更代码已在 Python 环境执行检查：

- 正确报告通过；错误类型、月份、额外字段与空摘要被拒绝。
- 有效人群变更通过；非法月份、人群与字段被拒绝。
- 返回新状态，原状态不受成功或失败变更污染。

这些检查验证示例的局部行为，不代表完整生产服务已实现，也没有调用付费模型服务。代码尚未实现真实权限、实体解析、业务月份范围与敏感内容检查，见各篇说明。

## 第08与11课离线检查

新增[可运行检查脚本](../examples/deep_dive_search_tool_checks.py)，仅依赖Python标准库。脚本包含两篇笔记中的示例实现及10项检查：

- 余弦相似度的同向、正交、反向；拒绝零向量、维度不一致、空向量和非有限值。
- 工具执行的合法结果、无数据状态、未知工具、缺项、额外字段、非法月份与人群。
- 越权区域、空授权集合、非对象JSON与损坏JSON。

从仓库根目录运行：

```bash
python courses/generative-ai-for-beginners/examples/deep_dive_search_tool_checks.py -v
```

2026-10-04执行结果：10项检查全部通过。这里的向量和业务数据是教学替身，没有调用真实Embedding服务、业务接口或图像模型，不能据此推断在线模型质量。

## 第15课证据组装检查

新增[证据组装检查脚本](../examples/deep_dive_rag_evidence_checks.py)，仅依赖Python标准库。2026-10-04执行结果：12项检查全部通过，覆盖实际消息中的原文与来源版本、授权过滤、去重、空检索、预算边界、非法输入与输入对象不被修改。

```bash
python courses/generative-ai-for-beginners/examples/deep_dive_rag_evidence_checks.py -v
```

这些检查不调用真实语言模型，不证明模型免疫提示注入或答案有事实依据。它们验证“正确的证据是否进入实际请求”这一独立环节。原论文中的RAG-Sequence/RAG-Token区别也已在第15篇说明，并保留论文链接。

## 第19课内存公式检查

新增[内存估算检查脚本](../examples/deep_dive_model_memory_checks.py)，2026-10-04执行12项检查全部通过，覆盖权重位宽、打包取整、GB/GiB区别、KV缓存与批量/上下文增长，以及无效输入。

```bash
python courses/generative-ai-for-beginners/examples/deep_dive_model_memory_checks.py
```

该脚本计算假设下的原始存储量，不测量实际设备，不计入激活、量化元数据和运行时峰值，不能用于保证模型可加载。第16–19课明确区分源课程示意、历史型号与原创工程补充。

## 全课程覆盖与验证

目前00–21共22个课次均有概览与深化文章。最后补充的00–03解释基础机制、环境、选型和责任控制；20–21对模型案例的原代码逐步解读，并明确历史版本、示意调用与实际执行的区别。

2026-10-04从远端读取四份测试模块，执行46项离线测试，全部通过。完整运行命令（仓库根目录）：

```bash
cd courses/generative-ai-for-beginners/examples
python -m unittest -v test_offline_demo deep_dive_search_tool_checks deep_dive_rag_evidence_checks deep_dive_model_memory_checks
```

测试验证教学代码的证据传递、权限边界、参数、向量与内存计算。未验证真实云服务、模型质量、GPU运行、线上配额或当前型号可用性。

后续可在已有文章中按具体问题与上游变更继续更新；完成本版整理不表示知识不再变化，也不表示所有上游示例都可直接上线。

## 来源与版权

课程来源：[Microsoft Generative AI for Beginners](https://github.com/microsoft/generative-ai-for-beginners/tree/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8)。各篇使用固定提交链接，便于核对来源。

课程采用 MIT License，Copyright (c) Microsoft Corporation；完整声明见 [LICENSE-Microsoft.txt](LICENSE-Microsoft.txt)。

本目录是独立中文学习笔记，与 Microsoft 官方课程没有隶属关系。业务示例、校验代码与工程扩展由本知识库编写。

[返回课程目录](../README.md)
