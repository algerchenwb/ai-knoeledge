# 第04–11课深化笔记

这些笔记在课程概览基础上进一步解释机制、业务案例、失败模式和后端实现。原课程解读与原创工程扩展均在各篇说明；核对日期：2026-10-03。

| 课次 | 深化笔记 | 重点 |
| --- | --- | --- |
| 04 | [提示词设计与验证](04-prompt-design-and-validation.md) | Token、任务结构、数据口径、模板、缺项、评测 |
| 05 | [高级提示词与失败模式](05-prompt-techniques-and-failure-modes.md) | 示例、任务分解、自检、事实依据、采样与无解条件 |
| 06 | [文本生成后端服务](06-text-generation-service.md) | 请求生命周期、输出验证、超时重试、流式与成本 |
| 07 | [聊天状态与评测](07-chat-state-and-evaluation.md) | 业务状态、历史压缩、并发、领域定制与任务指标 |
| 08 | [语义搜索与索引](08-semantic-search-and-indexing.md) | Embedding、切块、余弦、索引升级、混合检索与评测 |
| 09 | [图像生成与交付](09-image-generation-delivery.md) | 提示词、编辑、Base64、文件校验与异步任务 |
| 10 | [低代码工作流边界](10-low-code-workflow-boundaries.md) | 数据模型、发票抽取、重复事件、异常恢复与后端分工 |
| 11 | [Function Calling执行](11-function-calling-execution.md) | 工具契约、调用循环、鉴权、幂等与安全执行 |


建议按04→05→06→07阅读基础应用，再继续08→09→10→11。实践时先理解业务定义，再实现确定性校验，最后让模型生成说明。

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

## 后续深化范围

全课程概览已覆盖00–21；本目录目前详细展开04–11。后续可继续扩展12–21，以及00–03的机制与示例。已有章节可以按来源、口径、实现与练习继续补充，避免重复新建同主题笔记。

## 来源与版权

课程来源：[Microsoft Generative AI for Beginners](https://github.com/microsoft/generative-ai-for-beginners/tree/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8)。各篇使用固定提交链接，便于核对来源。

课程采用 MIT License，Copyright (c) Microsoft Corporation；完整声明见 [LICENSE-Microsoft.txt](LICENSE-Microsoft.txt)。

本目录是独立中文学习笔记，与 Microsoft 官方课程没有隶属关系。业务示例、校验代码与工程扩展由本知识库编写。

[返回课程目录](../README.md)
