# Agent 应用工程

从真实开源实现提取工程知识，配合独立离线故障注入。“实现案例”表示已核验代码路径，不等同于商业成功案例或生产效果证明。

| 教程 | 应用重点 |
| --- | --- |
| [工具执行可靠性](01-tool-retries-idempotency-and-recovery.md) | 10 个核心主题：未知结果、操作身份、参数绑定、原子性、checkpoint、重试预算、两类开源案例、回执账本、补偿；附六组检查 |

| [人工审批与版本化动作](02-human-approval-and-versioned-actions.md) | 审批快照、身份与范围、参数/版本绑定、过期、重复决定、执行前再校验；附十个离线检查 |

案例：LangGraph 节点重试与 entrypoint 状态机制；Temporal Activity 重试及实验性 Deep Agents 插件。固定提交、许可与未实跑边界见教程。

~~~bash
python knowledge/agent-engineering/examples/agent_idempotency_checks.py
python knowledge/agent-engineering/examples/approval_gate_checks.py
~~~

Python 3.12.14 标准库 mock 已验证；未验证框架集成、真实外部 API 或分布式并发，示例不能直接作为生产服务部署。

相关：[Agent 状态与权限](../../courses/generative-ai-for-beginners/deep-dives/17-agent-state-and-bounded-workflows.md)、[API Agent 后端实践](../../courses/generative-ai-for-beginners/appendices/api-agent-backend.md)。

后续待扩展：工具协议版本、授权生命周期、执行观测、审批界面与持久化、取消与长任务、集成评估。尚未完成条目不计为已有内容。

[返回总目录](../../README.md)
