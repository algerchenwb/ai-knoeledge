# 14. Agent 长任务持久化：租约、恢复与回执账本

Agent 要为一百家门店生成分析报告，程序执行到第六十家时重启。内存里的任务队列、已完成列表和待发报告都消失了。把进度存数据库能帮助继续执行，但若第六十家已向外部服务成功创建报告、本地还没保存回执，重新调用仍可能创建两份。

本章结合 LangGraph SQLite checkpoint 开源实现，解释持久化的实际边界，提供独立 SQLite 任务账本。它与[工具可靠性](01-tool-retries-idempotency-and-recovery.md)、[异步队列](12-async-queues-backpressure-and-shutdown.md)互补：前者讨论操作身份，后者处理进程内等待，本章实际验证文件数据库中的任务状态和恢复守卫。

## 1. 恢复需要保存事实，而不只是“进度 60%”

一个数字无法说明第六十家是未开始、调用中、已成功还是结果未知。建议至少分别保存任务身份、输入快照或引用、流程版本、阶段结果、外部操作身份、回执和错误状态。

| 数据 | 回答的问题 |
| --- | --- |
| job_id + tenant | 这是哪个业务任务、属于谁？ |
| input snapshot/hash | 原始参数是什么，后来是否被替换？ |
| recipe/schema version | 用哪套流程和定义解释旧状态？ |
| state + stage results | 哪些阶段已有可靠结论？ |
| operation_id + receipt | 外部动作是否完成，如何对账？ |
| lease owner + generation | 哪个执行者当前有权更新本地账本？ |

教学脚本只保存输入哈希，不保存完整 payload。因此不能单凭数据库记录重新构造工具参数；生产实现需要可恢复的输入存储，并确保引用保留足够久。

## 2. checkpoint、业务账本与消息队列职责不同

checkpoint 记录计算流程状态、节点值和版本，帮助框架恢复。业务账本记录报告是否创建、交付是否确认、哪些外部操作未知。消息队列帮助分发工作，通常还需要自己的确认和重投策略。

它们可以协作，但互相不能自动替代。LangGraph checkpoint 数据库存有节点状态，不代表客户邮箱已收到报告；任务队列已确认，也不代表指标验收通过。

实际设计可以让 worker 从持久任务账本找待执行任务，再加载框架 checkpoint，外部操作回执单独绑定 job_id 与 operation_id。本文脚本不集成 LangGraph，也不实现消息队列。

## 3. LangGraph SQLiteSaver 如何组织存储

固定源码 setup 创建 checkpoints 与 writes 表，启用 WAL。checkpoint 主键由 thread_id、checkpoint_ns、checkpoint_id 组成，还保存 parent_checkpoint_id、序列化类型、状态与 metadata。writes 表增加 task_id 和 idx，用来关联中间写入。

put 序列化 checkpoint，再用 INSERT OR REPLACE 保存；put_writes 对部分内部通道采用替换，对其他通道采用 INSERT OR IGNORE。具体通道策略属于框架实现，不应照搬成外部支付、发送报告的幂等规则。

thread_id 是运行状态的归属标识，不能当成已鉴权的用户身份。checkpoint_id 也不能代替外部操作的业务幂等键。

## 4. 文件持久化与内存数据库有明显区别

":memory:" 适合单连接演示，关闭后不能靠它恢复任务。文件数据库让新连接和独立进程能够读取已提交状态。

脚本实际创建临时 SQLite 文件，另启动一个 Python 进程读取 running 状态；另一项关闭并重新打开连接进行未知结果对账。这验证了正常提交后的可见性，不是断电恢复、文件系统损坏恢复或强制杀进程故障实验。

数据库文件还需要容量管理、备份、保留策略、访问控制和恢复演练。WAL 不是异地备份，也不消除单机故障。

## 5. 领取任务要把检查和修改放在同一事务

错误流程是先 SELECT 看到 queued，再稍后 UPDATE 为 running；两个 worker 都可能看到 queued。示例使用 BEGIN IMMEDIATE，在事务内读取状态、检查流程版本、增加 generation、登记 owner 和租约，然后提交。

双线程各用独立 SQLite 连接，同时竞争同一任务，检查只有一个返回 generation=1，另一个得到 None。连接不跨线程共享；这是同一机器、同一文件的竞争实验，不是分布式数据库基准。

LangGraph 的同步 Saver 内部也用 threading.Lock 协调自身 cursor，但该 Python 锁不覆盖其他进程，且 checkpoint API 不等于本文任务领取协议。源码注释将同步 Saver 定位为轻量场景，不应据此推断适合大规模多 worker 调度。

## 6. 租约表示暂时的处理权，不表示任务真的停止

租约过期说明系统不再接受该执行者作为当前负责人；原执行者可能还在网络等待、线程执行或外部服务中处理。

示例 finish 要同时匹配 running、owner、generation，并满足 now < expires；到期时刻也拒绝完成。expire 则把任务改为 unknown、增加 generation，并清除 owner。旧 token 随后不能更新本地任务。

这只是本地账本守卫。它不能阻止旧执行者继续向外部服务写入；需要下游支持操作身份或真正的 fencing 校验，才能限制外部副作用。不要把“拒绝旧回执写数据库”误认为“旧请求已经撤销”。

## 7. 心跳延长租约，业务进度描述已完成事实

示例 heartbeat 只有当前 owner 和 generation 在到期前才能更新 expires，且不缩短现有期限。它表示执行者仍在活动，不证明又完成一家门店。

进度则应由已确认结果驱动。例如一百家任务里，四十家成功、五家失败、两家未知，需要分别统计；“心跳发了四十次”不能写成“完成四十家”。

示例时间由测试注入，不运行真实定时心跳。生产系统应明确时间来源，避免不同机器的单调时钟互传；统一数据库时间、时钟误差和最大续租策略需要另行实现。

## 8. 恢复前先检查旧流程版本

旧任务可能保存的是 v1 画像流程，部署后 v2 改为另一种 population_type。直接用新代码读取旧状态，可能重复处理或解释错误。

脚本 claim 要求 recipe 完全一致，同一 tenant/job 的重复提交还必须输入哈希与 recipe 相同；不一致则拒绝。它没有状态迁移，只验证“不能静默混用版本”。

真实系统需要版本兼容规则：继续用旧执行器、显式迁移状态，或终止旧任务后创建新任务。checkpoint 反序列化成功，也不等于业务语义兼容。输入哈希仅做一致性比较，不是数字签名或授权凭证。

## 9. 租约过期后不应盲目重投写入任务

对只读查询，重新请求可能可接受，但还需考虑费用、速率及数据版本变化。对发送报告、创建订单等写入，过期任务的结果可能未知，重投可能重复副作用。

教学账本采用保守统一策略：running 到期后变为 unknown，claim 只接受 queued，unknown 不自动重新领取。这让系统暂时停住，需要对账；它不追求自动恢复吞吐。

生产系统可以按工具类别设计恢复策略，但应由可靠回执和幂等协议证明安全。长期 unknown 还需告警与人工处理入口；本章没有实现 unknown→queued 的自动转换。

## 10. 外部成功与本地保存之间始终有故障窗口

时间顺序可能是：

1. 外部服务创建报告，返回 receipt。
2. 程序在本地保存成功之前中断。
3. 重启后数据库仍显示 running。
4. 租约过期，账本登记 unknown。
5. 使用同一操作身份向外部服务查询，确认已成功，再保存回执。

脚本用独立字典模拟外部已成功，关闭连接后重新打开数据库，将过期任务对账为 succeeded；没有再次执行外部动作。该字典不是持久外部服务，测试也没有真正查询网络。

reconcile_success 接收的是调用者声称已核验的回执，没有实现签名、租户、操作参数或真实性验证。生产对账必须验证回执对应的业务操作，并记录证据来源；不能让模型自由编写 receipt 字符串就放行。

## 11. 完成状态与待通知事件应同时保存

若先保存 succeeded，再单独插入“通知用户”事件，两者之间故障会导致任务已成功却永远没通知。示例在同一事务中更新任务并插入 outbox 记录；故意在两步之间抛异常，检查状态和事件都回滚。

outbox 表主键 tenant/job/event 防止同一完成事件重复登记。重复 finish 也会因状态已改变而拒绝。它验证本地数据库中的一致性，不保证用户只收到一次通知。

实际发布器可能在发送消息成功、标记已发送之前故障，因此会再次发送。需要事件 ID、接收端幂等和明确回执。脚本没有发布器、消息通道或已发送字段，不能称为完整 transactional outbox 服务。

## 12. 数据库事务不能把外部调用一起包住

在数据库事务内调用慢 API，可能长时间占用写锁，也无法让外部服务跟数据库一起回滚。更合理的应用流程是短事务领取；事务外调用；短事务保存结果和事件；故障后按操作身份对账。

即使节点状态、回执和 outbox 都有事务，跨系统的“恰好执行一次”仍需各参与方协议。框架重放、checkpoint、锁或 WAL 本身都不能自动消除远端副作用的重复。

同步 SQLiteSaver cursor 在锁内执行数据库操作，并在 finally 中提交；这是源码实际行为。不要把它当作所有异常都会自动回滚的通用事务封装。本文原创账本则明确在异常时 rollback，二者策略不能混淆。

## 开源来源与版本

核验日期：**2026-10-05（北京时间）**。来源 [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)，固定提交 **9a0394d88b2211f299dcd69df92db3480c69ee61**，提交时间 **2026-10-03T12:55:59Z**。

| 固定文件 | 核验内容 |
| --- | --- |
| [SQLiteSaver 源码](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py) | setup、cursor、get_tuple、put、put_writes 的状态与存储机制 |
| [组件 README](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/libs/checkpoint-sqlite/README.md) | 本地/轻量场景、同步与异步用法、序列化注意事项 |
| [MIT LICENSE](https://github.com/langchain-ai/langgraph/blob/9a0394d88b2211f299dcd69df92db3480c69ee61/LICENSE) | Copyright (c) 2024 LangChain, Inc. |

中文说明、业务推导和脚本为原创；未复制上游实现。上游许可和版权归原项目；复用其代码应保留 MIT 许可与版权声明。这里只读了源码，没有安装或实跑 LangGraph Saver。

## 已运行实验

脚本：[durable_job_checks.py](examples/durable_job_checks.py)，Python **3.12.14**、SQLite **3.53.1**，使用标准库，无第三方依赖。

~~~bash
python knowledge/agent-engineering/examples/durable_job_checks.py
~~~

**14 项 unittest 全部通过**：

| 检查 | 目标 |
| --- | --- |
| 1–4 | 重复提交一致性、变更输入拒绝、流程版本拒绝、租户键隔离 |
| 5–6 | 独立进程读取已提交文件状态、双连接竞争只领取一次 |
| 7–9 | 心跳不缩短租约、到期边界、错误 owner/generation 拒绝 |
| 10–12 | unknown 不自动重领、完成与事件回滚、重复完成不重复建事件 |
| 13–14 | 外部成功/本地未记录的模拟窗口对账、非法租约参数拒绝 |

限制：实际 SQLite 文件及同机线程/独立读进程；未验证断电、强制终止、磁盘损坏、多机数据库、真实外部写入、消息发布或框架恢复。输入只存哈希、状态无完整迁移、时间由调用者提供、回执真实性未校验。未实现失败/取消恢复、批量扫描、自动回收、备份和清理。

脚本生成的数据库放临时目录，测试结束即删除；用于验证机制，不能承载用户真实长任务。生产实现还需要租户鉴权、受控状态机、任务内容持久化与状态事务；本地 token 不是防伪授权票据。

## 自测练习

1. 进度已保存 60%，为什么仍无法判断第六十家能否重试？
2. lease 过期后旧 worker 继续向远端创建报告，本地 generation 能阻止吗？
3. outbox 发布器发送后重启，如何避免接收端重复交付？
4. v1 checkpoint 被 v2 程序成功反序列化，为何仍可能不能恢复业务？

[返回专题目录](README.md)
