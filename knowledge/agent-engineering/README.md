# Agent 应用工程：十三篇深入教程

从真实开源实现提取工程知识，配合独立离线故障注入。“实现案例”表示已核验代码路径，不等同于商业成功案例或生产效果证明。

| 教程 | 应用重点 |
| --- | --- |
| [工具执行可靠性](01-tool-retries-idempotency-and-recovery.md) | 10 个核心主题：未知结果、操作身份、参数绑定、原子性、checkpoint、重试预算、两类开源案例、回执账本、补偿；附六组检查 |
| [人工审批与版本化动作](02-human-approval-and-versioned-actions.md) | 审批快照、身份与范围、参数/版本绑定、过期、重复决定、执行前再校验；附十个离线检查 |
| [取消、进度与部分完成](03-cancellation-progress-and-partial-results.md) | 取消传播、心跳与业务进度、迟到回执、未知结果、旧回调与成功边界；附八个离线交错检查 |
| [资源预算与准入控制](04-resource-budgets-and-admission-control.md) | 请求/尝试/Token/费用边界、共享预算、并发预占与未知结算；附九个离线检查 |
| [结构化输出与工具参数](05-structured-output-and-tool-contracts.md) | 严格类型、JSON 边界、日期/坐标语义、Schema 覆盖与服务端权限；附 23 项 Pydantic 检查 |
| [工具结果缓存与新鲜度](06-tool-result-cache-and-freshness.md) | 租户/权限隔离、语义键、TTL、负缓存、复制隔离、回源竞争和版本失效；附 21 项离线检查 |
| [熔断与故障隔离](07-circuit-breakers-and-failure-isolation.md) | 故障分类、冷却与探测、旧回执、隔离范围、重试统计与业务降级；附 15 项离线检查 |
| [分页游标与快照](08-pagination-cursors-and-snapshots.md) | 分页完整性、快照、查询/权限绑定、过期、循环游标与部分排名；附 16 项离线检查 |
| [链路、业务结果与统计口径](09-tracing-outcomes-and-metric-denominators.md) | 父子链路、重试、异常/状态、业务完成、统计分母、费用未知与属性白名单；附 13 项离线检查 |
| [轨迹与业务验收](10-trajectory-and-business-acceptance.md) | 轨迹模式、参数、依赖、证据、部分交付、禁止动作与回归门禁；附 18 项离线样例检查 |
| [速率、租户配额与截止时间](11-rate-limits-queues-and-deadlines.md) | 突发额度、联合准入、权重、公平性、排队、退避与 deadline；附 18 项离线检查 |
| [异步队列与任务收尾](12-async-queues-backpressure-and-shutdown.md) | 背压、等待取消、收尾确认、过期、TaskGroup 与正常停机；附 12 项真实 asyncio 检查 |
| [工具协议与契约版本](13-tool-protocol-and-contract-versioning.md) | MCP 新旧协议、发现目录、契约指纹、旧计划失效与结果分类；附 18 项离线检查 |

案例：LangGraph 节点重试与 entrypoint 状态机制；Temporal Activity 重试及实验性 Deep Agents 插件。Pydantic AI 用量限制与累计机制。Pydantic 严格类型与业务校验。cachetools TTL 与回源协调机制。PyBreaker 故障分类与三态转换。Kubernetes 官方文档中的分块列表与快照契约。OpenTelemetry 官方 Trace 与 Baggage 规范。agentevals 轨迹匹配与参数比较机制。aiolimiter 加权容量、突发及事件循环机制。CPython asyncio 队列、取消与 TaskGroup 生命周期。MCP 2026-07-28 官方规范与新旧版本兼容。固定提交、许可与未实跑边界见教程。

~~~bash
python knowledge/agent-engineering/examples/agent_idempotency_checks.py
python knowledge/agent-engineering/examples/approval_gate_checks.py
python knowledge/agent-engineering/examples/cancellation_checks.py
python knowledge/agent-engineering/examples/budget_checks.py
python knowledge/agent-engineering/examples/structured_output_checks.py
python knowledge/agent-engineering/examples/tool_cache_checks.py
python knowledge/agent-engineering/examples/circuit_breaker_checks.py
python knowledge/agent-engineering/examples/pagination_checks.py
python knowledge/agent-engineering/examples/observability_checks.py
python knowledge/agent-engineering/examples/agent_acceptance_checks.py
python knowledge/agent-engineering/examples/rate_limit_checks.py
python knowledge/agent-engineering/examples/async_queue_checks.py
python knowledge/agent-engineering/examples/tool_protocol_checks.py
~~~

Python 3.12.14 标准库 mock 已验证；异步队列脚本另实跑单事件循环的 Queue、取消、timeout 和 TaskGroup；资源预算、熔断和速率脚本另验证了单进程双线程竞争；结构化输出脚本使用 Pydantic 2.13.5（需安装该依赖）实跑；未验证 Agent 框架集成、真实外部 API 或分布式并发，示例不能直接作为生产服务部署。

相关：[Agent 状态与权限](../../courses/generative-ai-for-beginners/deep-dives/17-agent-state-and-bounded-workflows.md)、[API Agent 后端实践](../../courses/generative-ai-for-beginners/appendices/api-agent-backend.md)。

后续待扩展：MCP 真实传输与订阅集成、授权生命周期、观测系统集成与采样/导出验证、审批界面与持久化、长任务持久化、跨进程排队取消与持久收尾、跨进程配额与截止时间传播、真实 Agent 集成评估与独立标注集。尚未完成条目不计为已有内容。

[返回总目录](../../README.md)
