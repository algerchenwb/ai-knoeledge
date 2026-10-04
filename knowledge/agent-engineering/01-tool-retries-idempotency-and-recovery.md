# 01 Agent 工具执行可靠性：重试、幂等与恢复

> 面向后端应用，以“Agent 生成并保存月度报表”为例，讲清外部写入、超时和恢复。
>
> 前置：[Agent 状态与有界工作流](../../courses/generative-ai-for-beginners/deep-dives/17-agent-state-and-bounded-workflows.md)。本篇补充源码案例和六组离线故障注入，不把上游示例当作生产效果证明。

## 1. 超时表示“不知道”，不一定表示失败

Agent 调用 create_report，后端已保存报表，却在返回响应前断网。Agent 只看到超时，如果换一个请求 ID 再保存，就可能得到两份报表。

| 真实情况 | 客户端看到 | 重试风险 |
| --- | --- | --- |
| 请求没到后端 | 超时 | 原动作尚未发生 |
| 后端收到但事务回滚 | 超时 | 可按同一动作重新尝试 |
| 后端成功但响应丢失 | 超时 | 再执行可能重复产生副作用 |

执行状态应包含 outcome_unknown（结果未知）或等价状态，不能遇到超时一律 failed。模型猜测不能决定数据库事实。应通过权威查询、已有回执或服务端幂等机制解决不确定性，也不能把未知谎报成 succeeded。

## 2. 四类 ID 必须分开

| ID | 含义 | 同一动作重试时 |
| --- | --- | --- |
| task_id | 用户的一项任务 | 通常不变 |
| operation_id | 一个明确的业务动作 | 必须不变 |
| attempt_id | 该动作的一次尝试 | 每次变化 |
| trace_id / span_id | 日志链路关联 | 按观测协议决定 |

task-42 的 report-v1 操作，每次重试使用同一 operation_id。若用户明确要求另生成一版，应建立新操作。每次随机生成 UUID 会让去重永远无法命中。

LLM tool_call_id 可能在重新规划后改变，不适合无条件作为长期业务幂等键。应由执行层为获准的动作分配并持久保存操作身份。

作用域通常还包含租户和工具类型。ID 分区不代替认证授权。

## 3. 幂等键要绑定参数摘要

同一操作第一次要求九月报表，第二次改成十月，不能默默返回旧九月结果。

常见协议：

- 不存在该键：登记并执行。
- 已存在且参数相同：返回已有回执或当前状态。
- 已存在但参数不同：返回冲突，阻止另一副作用。

参数摘要应来自固定版本的规范化方式，再作 SHA-256 等摘要。需要约束类型、单位、时区和默认值语义。脚本仅演示简单 JSON 键排序，不能覆盖所有语言数值、Unicode 或浮点业务语义。

去重记录保留期也属于协议：记录过期后，旧请求可能被视为新动作。重试窗口与保留期应协调。

## 4. 记录结果和副作用要考虑原子性

危险流程：先检查未执行 → 创建报表 → 记录幂等结果。若创建后、记录前崩溃，就留下“产物存在、账本不存在”的状态。

若产物和账本在同一数据库，可在同一事务写入，配合唯一约束。本文 SQLite mock 就这样做：报表行与回执行一起提交，异常时一起回滚。

若副作用是第三方 API，本地事务无法把它自动纳入原子提交。需要第三方支持稳定幂等键、可查询业务标识，或其他明确恢复协议。

“本地先写 pending 再调用 API”让未知状态可追踪，但仍存在外部成功与本地写回之间的窗口，不能省去对账。

## 5. checkpoint 不等于外部去重

checkpoint 保存工作流进度，幂等账本保存业务动作结果。

典型窗口：外部成功 → 本地 checkpoint 尚未提交 → 进程退出。恢复时旧 checkpoint 仍显示“步骤未完成”，但外部动作已经发生。

即使框架可恢复节点，也不能凭 checkpoint 缺失断定外部未执行。

~~~mermaid
flowchart TD
  A["加载任务与操作记录"] --> B{"已有权威回执？"}
  B -->|有| C["复用结果并推进"]
  B -->|无| D{"服务支持同键去重？"}
  D -->|支持| E["按原操作 ID 调用"]
  D -->|不支持| F["查询或对账结果"]
  E --> G{"收到可靠结果？"}
  F --> G
  G -->|是| C
  G -->|否| H["保留未知状态"]
~~~

对账可由程序或明确运维流程完成，模型自由推断不构成成功证据。

## 6. 重试应分类，并受总预算限制

| 错误 | 常见处理 | 注意 |
| --- | --- | --- |
| 参数不合法 | 修正或结束 | 同参数反复重试无帮助 |
| 认证/权限失败 | 按授权流程处理 | 重试不扩大权限 |
| 限流 | 按协议等待 | 等待计入总期限 |
| 临时网络错误 | 限定安全重试 | 写操作先处理未知结果 |
| 业务冲突 | 读取当前状态 | 不把冲突一律视为暂时错误 |
| 用户取消 | 阻止新尝试 | 已发生副作用不会自动撤销 |

读操作也有配额，LLM 重试还可能再次计费并产生不同文本。至少限制尝试数、每次超时和总期限。

退避减少拥堵，抖动避免客户端同时重试；还应遵循 Retry-After 等服务约定。Agent、SDK、网关层层各重试三次，实际调用数可能相乘。应明确责任层并记录实际尝试。

预算耗尽不是成功；若结果未知，应保留未知状态而非假装回滚。

## 7. 开源案例：LangGraph 的任务重试

固定快照的 pregel/_retry.py 中，run_with_retry 会选择重试策略、调用任务、匹配 retry_on；没有匹配策略或达到 max_attempts 就继续抛错。

同步实现的退避以 initial_interval、backoff_factor、max_interval 计算；启用 jitter 时加上 0–1 秒随机量。max_attempts 包含首次执行，不是额外重试次数。这些细节属于核验快照，不代表所有库的统一规则。

源码会清理上次尝试的 task.writes。**推断边界：**这是框架写缓存，不能据此推导此前外部 HTTP 创建的报表也被撤销。业务幂等仍由应用和外部服务实现。

func/__init__.py 的 entrypoint 说明 checkpointer 可保存跨运行状态，previous 可访问同线程先前返回值。状态保存也不替第三方操作提供原子事务。

本篇只阅读源码，没有安装执行 LangGraph；内部路径不是建议应用直接调用的公共 API。

## 8. 开源案例：Temporal Activity 和 Agent 插件

### Activity 重试样例

hello/hello_activity_retry.py 中，compose_greeting 在尝试号小于 4 时故意抛错，第 4 次返回问候。工作流设置每次 start_to_close_timeout 为 10 秒，RetryPolicy 的 maximum_interval 为 2 秒；Worker 注册并执行该流程。

这展示的是重试接线，不是支付幂等，也不是本篇已运行四次真实 Activity。示例保留较宽的默认重试边界，迁移到有总预算的 Agent 时应设计最大尝试和任务期限。

### Agent 接线样例

deepagents_plugin/hello_world 的 workflow.py 在 Workflow 内创建 Deep Agent 并调用一次 ainvoke；run_worker.py 给 Client.connect 添加 DeepAgentsPlugin。

快照 README 说明模型调用通过 Temporal Activity 执行，控制循环在 Workflow 内按协议恢复/重放；suite README 明确标为 experimental，API 可能变化。

它提供“Agent 控制流程与可重试外部调用分离”的实际开源接线案例。这个单次问答没有展示自定义业务写入幂等，Activity 调度不意味着所有第三方操作不会重复。

样例需要依赖、Temporal 服务和模型凭据。本篇未执行该集成，不宣称生产成功率、模型当前可用性或跨版本兼容。源码模型名称只视为快照内容。

## 9. 可查询账本与回执

| 字段 | 用途 |
| --- | --- |
| tenant / actor | 作用域与审计身份 |
| operation_id / task_id | 稳定动作及所属任务 |
| tool_name / protocol_version | 调用契约 |
| canonical_payload_hash | 同键参数绑定 |
| status | pending / succeeded / failed / outcome_unknown |
| external_receipt / object_id | 权威查询证据 |
| attempt_count / timestamps | 排查尝试和恢复 |
| error_class | 错误分类 |

真实服务还需定义 pending 超时恢复、推进资格、租约/并发竞争及保留期。日志链路、业务账本和 checkpoint 各有职责，不用散乱日志替代结构化记录。

重试或复用回执前，仍应核对当前权限、对象版本、取消状态和任务是否有效。

## 10. 幂等与补偿不是一回事

幂等避免同一动作重复产生副作用。补偿是对已成功动作发起新的纠正动作。

撤销报表发布可以是补偿，但删除文件无法保证别人没读过。发出消息也不能靠删数据库行消除接收方影响。

补偿也有自己的操作身份、状态和验证，并可能失败。不能把尽力补偿描述成跨系统自动回滚或 exactly-once 保证。

事务 outbox 可把本地业务状态与待发事件一起提交，再由发送者投递；接收方仍需处理重复。本篇没有实现完整 outbox。

## 11. 六组离线故障注入

[agent_idempotency_checks.py](examples/agent_idempotency_checks.py)使用临时 SQLite，产物与账本共享事务。没有网络、模型或框架依赖。

| 检查 | 场景 | 已核验结果 |
| --- | --- | --- |
| 1 | 提交后丢失响应、重建服务对象 | 查到回执，同键重试仍只一份报表 |
| 2 | 重复请求、JSON 字段顺序变化 | 相同回执，无新增产物 |
| 3 | 同键改月份 | 冲突被拒绝 |
| 4 | 不同租户同一操作 ID | 各自有独立回执 |
| 5 | 事务提交前抛错 | 产物和账本一起回滚，再试成功 |
| 6 | 同一意图换两个新 ID | 去重被绕过，新增两份 |

输出计数按阶段为 1 → 3 → 5。最后是反例，说明随机新 ID 破坏业务去重。

重建对象只核验数据库状态跨对象实例保留；抛错是模拟故障，未强杀进程、断电、真实断网或压测并发。租户测试只核验键作用域，没有认证层。SQLite 原子性也不能代表外部 API 的原子性。

~~~bash
python knowledge/agent-engineering/examples/agent_idempotency_checks.py
~~~

## 12. 练习与答案

1. 超时且 checkpoint 没成功记录，能换新 ID 再写一次吗？  
   **答案：** 不能据此断定未执行，应查询或复用原 ID 安全重试。

2. 参数哈希直接作 operation_id 有什么问题？  
   **答案：** 相同参数可能代表用户明确要求的两个动作，会误合并；摘要适合绑定参数，不无条件代替业务身份。

3. pending 后调用外部 API，是否消除重复窗口？  
   **答案：** 没有，外部成功但本地未写回仍需对账。

4. 清空节点写缓存会撤销外部报表吗？  
   **答案：** 不能这样推导，取决于业务服务协议。

5. 用户取消是否代表已创建的报表不存在？  
   **答案：** 不代表，取消阻止新动作，已完成动作另按业务规则处理。

## 来源与验证边界

核验日期：2026-10-04。以下是开源代码阅读案例，不是商业客户成功案例或已实跑框架集成。

- LangGraph 固定提交 9a0394d88b2211f299dcd69df92db3480c69ee61：[重试实现](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/libs/langgraph/langgraph/pregel/_retry.py)、[entrypoint](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/libs/langgraph/langgraph/func/__init__.py)。[MIT 许可](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/LICENSE)，Copyright (c) 2024 LangChain, Inc.
- Temporal samples-python 固定提交 811062812152519af5bc078375aaf061c9bda6ae：[Activity 重试](https://github.com/temporalio/samples-python/blob/811062812152519af5bc078375aaf061c9bda6ae/hello/hello_activity_retry.py)、[Agent workflow](https://github.com/temporalio/samples-python/blob/811062812152519af5bc078375aaf061c9bda6ae/deepagents_plugin/hello_world/workflow.py)、[Worker](https://github.com/temporalio/samples-python/blob/811062812152519af5bc078375aaf061c9bda6ae/deepagents_plugin/hello_world/run_worker.py)、[实验插件说明](https://github.com/temporalio/samples-python/blob/811062812152519af5bc078375aaf061c9bda6ae/deepagents_plugin/README.md)。[MIT 许可](https://github.com/temporalio/samples-python/blob/811062812152519af5bc078375aaf061c9bda6ae/LICENSE)，Copyright (c) 2022 Temporal Technologies Inc. All rights reserved.

中文解释、mock 与故障注入独立编写，没有复制上游实现。实跑范围是 Python 3.12.14 标准库脚本六组检查；真实服务仍需验证网络、并发、进程崩溃、保留期和权限。

[返回专题目录](README.md)
