# 第04–07课深化笔记

这些笔记在课程概览基础上进一步解释机制、业务案例、失败模式和后端实现。原课程解读与原创工程扩展均在各篇说明；核对日期：2026-10-03。

| 课次 | 深化笔记 | 重点 |
| --- | --- | --- |
| 04 | [提示词设计与验证](04-prompt-design-and-validation.md) | Token、任务结构、数据口径、模板、缺项、评测 |
| 05 | [高级提示词与失败模式](05-prompt-techniques-and-failure-modes.md) | 示例、任务分解、自检、事实依据、采样与无解条件 |
| 06 | [文本生成后端服务](06-text-generation-service.md) | 请求生命周期、输出验证、超时重试、流式与成本 |
| 07 | [聊天状态与评测](07-chat-state-and-evaluation.md) | 业务状态、历史压缩、并发、领域定制与任务指标 |

建议按04→05→06→07阅读。实践时先理解业务定义，再实现确定性校验，最后让模型生成说明。

## 示例验证记录

第06课的报告校验代码、第07课的状态变更代码已在 Python 环境执行检查：

- 正确报告通过；错误类型、月份、额外字段与空摘要被拒绝。
- 有效人群变更通过；非法月份、人群与字段被拒绝。
- 返回新状态，原状态不受成功或失败变更污染。

这些检查验证示例的局部行为，不代表完整生产服务已实现，也没有调用付费模型服务。代码尚未实现真实权限、实体解析、业务月份范围与敏感内容检查，见各篇说明。

## 来源与版权

课程来源：[Microsoft Generative AI for Beginners](https://github.com/microsoft/generative-ai-for-beginners/tree/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8)。各篇使用固定提交链接，便于核对来源。

课程采用 MIT License，Copyright (c) Microsoft Corporation；完整声明见 [LICENSE-Microsoft.txt](LICENSE-Microsoft.txt)。

本目录是独立中文学习笔记，与 Microsoft 官方课程没有隶属关系。业务示例、校验代码与工程扩展由本知识库编写。

[返回课程目录](../README.md)
