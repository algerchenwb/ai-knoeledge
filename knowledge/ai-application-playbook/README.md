# AI 应用落地：100个知识点

整理日期：2026-10-04。每条独立编号001—100，包含应用场景、实现步骤、验收方法和常见误区；覆盖应用开发、API Agent、知识库、数据分析、文档处理与运维。

这100条是可执行的设计与验证指南，并不表示100项功能已经实现。模块以已核对的开源机制为依据，业务字段、策略与验收规则由本知识库独立整理。需要读具体代码时，配合[十篇Agent实现案例](../agent-case-studies/README.md)。

## 十个应用方向

| 范围 | 模块 | 数量 |
|---|---|---|
| 001—010 | [业务目标与输出契约](01-business-and-output-contracts.md) | 10 |
| 011—020 | [工具调用与 API 接入](02-tools-and-api-integration.md) | 10 |
| 021—030 | [Agent 路由与协作](03-agent-routing-and-coordination.md) | 10 |
| 031—040 | [RAG 与检索应用](04-rag-and-retrieval.md) | 10 |
| 041—050 | [文档处理与多模态输入](05-documents-and-multimodal-input.md) | 10 |
| 051—060 | [业务数据与确定性计算](06-business-data-and-calculation.md) | 10 |
| 061—070 | [状态、记忆与个性化](07-state-memory-and-personalization.md) | 10 |
| 071—080 | [工作流恢复与事件处理](08-workflow-recovery-and-events.md) | 10 |
| 081—090 | [评测、可观测性与质量迭代](09-evaluation-and-observability.md) | 10 |
| 091—100 | [服务部署、权限与运维](10-serving-security-and-operations.md) | 10 |

## 建议阅读顺序

- API Agent：001—020、021—030、051—060、071—080。先固定对象与业务口径，再限制工具，再增加协作。
- 企业知识库：031—050、061—070、081—090。先处理文档质量与范围，再检索与回答，最后评估。
- 编码与自动化：十个案例中的代码执行、修复、控制面与浏览器篇；配合071—100。

开始试点先选002结构输出、013鉴权注入、016错误分类、028真实反馈、051同范围计算、066会话隔离、073去重、081金标准和097凭据隔离；这些是本文建议的最小可靠路径，不是强制要求采用某个框架。

## 所有知识点索引

| 编号 | 知识点 | 所属模块 |
|---|---|---|
| 001 | [任务边界](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 002 | [字段级结构化输出](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 003 | [未知与空值语义](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 004 | [事实与解释分栏](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 005 | [数值与单位绑定](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 006 | [缺参澄清策略](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 007 | [输入规范化与保真](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 008 | [对象ID与显示名](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 009 | [报告覆盖清单](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 010 | [交付产物清单](01-business-and-output-contracts.md) | 业务目标与输出契约 |
| 011 | [工具语义分组](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 012 | [参数白名单](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 013 | [鉴权上下文注入](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 014 | [分页与截断标记](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 015 | [批量查询映射](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 016 | [错误分类](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 017 | [只读与写工具分离](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 018 | [超时与截止时间](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 019 | [MCP工具适配层](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 020 | [工具结果压缩](02-tools-and-api-integration.md) | 工具调用与 API 接入 |
| 021 | [规则路由与模型路由](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 022 | [Handoff控制权](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 023 | [专家作为工具](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 024 | [顺序任务依赖](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 025 | [并行独立任务](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 026 | [协调者与最终责任](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 027 | [有界反思](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 028 | [工具反馈优先](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 029 | [终止条件分层](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 030 | [协作成本基线](03-agent-routing-and-coordination.md) | Agent 路由与协作 |
| 031 | [语料范围与来源时间](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 032 | [切块按语义边界](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 033 | [块与父文档追溯](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 034 | [Embedding版本迁移](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 035 | [关键词与语义互补](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 036 | [候选重排](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 037 | [无证据拒答](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 038 | [查询改写保留约束](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 039 | [上下文去重与多样性](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 040 | [检索与生成分开评测](04-rag-and-retrieval.md) | RAG 与检索应用 |
| 041 | [解析格式识别](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 042 | [阅读顺序](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 043 | [表格结构恢复](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 044 | [OCR低置信复核](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 045 | [页码与引用定位](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 046 | [图片说明与事实来源](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 047 | [公式与代码保真](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 048 | [音频转写与说话人](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 049 | [脱敏后的可用性](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 050 | [解析质量门槛](05-documents-and-multimodal-input.md) | 文档处理与多模态输入 |
| 051 | [分子分母同范围](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 052 | [去重层级](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 053 | [时间窗与时区](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 054 | [坐标系协议](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 055 | [距离与空间尺度](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 056 | [多围栏对象](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 057 | [JSON数值类型](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 058 | [重复行与连接膨胀](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 059 | [数据成熟度](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 060 | [空分母与精度](06-business-data-and-calculation.md) | 业务数据与确定性计算 |
| 061 | [业务状态与聊天分离](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 062 | [短期工作记忆](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 063 | [长期偏好来源](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 064 | [记忆过期策略](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 065 | [记忆写入门槛](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 066 | [会话与租户隔离](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 067 | [摘要的保真字段](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 068 | [状态版本冲突](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 069 | [忘记与删除](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 070 | [记忆是否带来收益](07-state-memory-and-personalization.md) | 状态、记忆与个性化 |
| 071 | [检查点粒度](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 072 | [副作用与重放](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 073 | [事件ID去重](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 074 | [重试退避](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 075 | [部分成功汇合](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 076 | [取消传播](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 077 | [人工介入恢复](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 078 | [任务租约与心跳](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 079 | [失败队列与人工修复](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 080 | [补偿与真实回滚](08-workflow-recovery-and-events.md) | 工作流恢复与事件处理 |
| 081 | [黄金问题集](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 082 | [分层失败归因](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 083 | [运行轨迹关联](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 084 | [成本归因](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 085 | [首字延迟与完成时间](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 086 | [LLM裁判校准](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 087 | [引用支持率](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 088 | [离线到在线验证](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 089 | [反馈标签化](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 090 | [评测集防泄漏](09-evaluation-and-observability.md) | 评测、可观测性与质量迭代 |
| 091 | [统一模型网关](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 092 | [模型能力矩阵](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 093 | [故障切换语义](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 094 | [租户配额与公平性](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 095 | [缓存范围与版本](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 096 | [流式事件协议](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 097 | [凭据隔离与日志脱敏](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 098 | [执行环境最小权限](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 099 | [版本固定与兼容检查](10-serving-security-and-operations.md) | 服务部署、权限与运维 |
| 100 | [回滚与运行手册](10-serving-security-and-operations.md) | 服务部署、权限与运维 |

## 来源、验证与扩展方式

[15个开源项目的固定快照与许可](../agent-case-studies/sources.md) · [机器可读卡片清单](catalog.json)。清单保留每条的场景、步骤、验收、误区及模块来源，可用于按编号检索和继续扩写。

本轮已检查100个编号连续且唯一，每个模块10条，每条四个字段完整；与十篇案例关联的离线脚本运行10项机制检查通过。未逐项实现这些应用策略，也未进行上游框架集成或真实业务评测。后续将有价值的卡片升级成完整示例时，应增加依赖版本、数据夹具、真实结果和失败边界，保留原编号方便追踪。

[返回总入口](../../README.md)
