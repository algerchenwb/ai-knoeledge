# 09｜Agent 可观测性：链路、重试、业务结果与统计口径

用户看到一份不完整的选址报告，后端却显示“请求成功”。这可能因为 HTTP 返回了 200，模型正常生成文本，但画像接口失败、分页预算耗尽或证据过期。

可观测性需要回答三个不同问题：程序做了什么、业务交付了什么、统计口径怎样计算。本篇基于 OpenTelemetry 官方开源规范解释链路机制，并给出原创标准库示例。示例不使用 OpenTelemetry SDK，不连接 Langfuse、Collector 或任何真实模型/API。

## 1. 日志、指标、Trace 各自回答什么

| 形式 | 适合的问题 | 局限 |
| --- | --- | --- |
| 日志/事件 | 某个步骤发生了什么？ | 大量独立行不容易还原关系 |
| 指标 | 每分钟多少失败？延迟分布如何？ | 聚合后通常看不到完整单次过程 |
| Trace | 某次请求经历了哪些相关操作？ | 采样、丢失或未传播时可能不完整 |
| 业务结果/审计账本 | 最终交付、批准或外部动作是什么？ | 不能被监控系统的 span 状态替代 |

例如，工具重试失败一次再成功，Trace 可以展示这两次尝试；指标要分别统计物理尝试与逻辑操作；写入动作最终是否发生仍需可信回执。不要拿“没有错误 span”证明没有业务错误。

## 2. 一次任务、逻辑操作、物理尝试分开标识

可以设置业务 task_id、稳定 operation_id 和每次执行不同的 attempt_id。TraceId 负责链路关联，SpanId 负责某个操作；它们与业务身份并非一回事。

一次长任务可能在重启后产生多个 Trace。task_id 仍稳定，可通过有权限的业务记录关联；不能因为换了 TraceId 就认为这是一个新订单。

本例构造 report → tool.operation → 两个 tool.attempt。重试尝试的 span ID 不同，但属于同一逻辑操作父 span；也共享同一 trace ID。应用内部建议采用固定低基数的 span 名称，把必要标识放在受控属性中。

本例 UUID 生成只是教学标识，不实现完整 W3C TraceContext、TraceFlags、远程标识解析或抽样协议。

## 3. 上游父子关系与 Link 的边界

OpenTelemetry Tracing API 说明，每个 span 最多一个父 span；同一 trace 内的子 span 继承父 trace ID。没有当前 span 时，新建的是根 span。

并非所有关联都适合硬塞成父子树。例如多个队列消息合并成一个批任务，或持久任务跨一次新的执行恢复，可以考虑 Links。规范允许链接同一或不同 trace 的 SpanContext。

本例只实现单父子关系，没有 Link。真实设计还需明确 SERVER/CLIENT、PRODUCER/CONSUMER 的语义和传播方式，不要把一个下游 HTTP 客户端 span 与后台队列消费者随意混成同一种事件。

## 4. 上下文传播不能靠日志文本猜

服务间要通过约定的传播器注入/提取上下文；协程、线程池、队列和回调也要保留正确上下文。只把 task_id 打在字符串日志里，通常不能自动生成正确父子关系。

本例使用 ContextVar 保存当前 span，用 token 在 finally 中恢复；用 copy_context 捕获上下文，并在另一上下文中执行模拟排队步骤。检查验证父关系保持，以及异常后回到原父 span。

该检查没有跨线程、进程或网络，也不验证任何 HTTP header。Python contextvars 的这段教学代码不能直接替代 Go context、OpenTelemetry propagator 或消息队列的注入/提取逻辑。

Trace 信息用于关联，不能用于身份认证。收到某个 trace ID 或 baggage 值，不表示获得租户权限。

## 5. 异常事件与错误状态是两件事

规范的 RecordException 是一种事件记录操作；SetStatus 独立处理 span 状态。某个 SDK 的上下文管理器可能把两者结合，但不能把它当作 API 本身的唯一行为。

本例显式验证：只调用 record_exception，状态仍为 unset；context manager 捕获逃逸异常时，则主动记录异常类型并设置 error，再重新抛出。

事件不记录原始异常消息，避免本例中的秘密字符串进入事件；但真实堆栈、URL、数据库错误和请求体仍可能泄露敏感值，需要按采集链路处理。示例只验证有限字段策略，不是通用脱敏库。

## 6. 不要过早把整个任务设成 Ok

本次固定规范的状态为 Unset、Ok、Error，并定义 Ok > Error > Unset。显式 Ok 会覆盖之前及之后尝试设置的 Error；规范建议一般 instrumentation 不主动设置 Ok，而是没有错误时保持 Unset。

因此，刚收到 HTTP 200 或模型输出就把父任务设成 Ok，后面发现证据不足时再写 Error，可能无法达到预期。状态语义必须事先定义，不能把 Ok 当成随时可撤销的进度标签。

本例模拟上述状态优先级，并验证 error → ok → error 最后仍为 ok。它不是完整 OpenTelemetry Span 实现，只展示相关规则。

业务状态另设 business.outcome：complete、partial、failed。本例 report 标注 partial、技术状态保持 unset，说明教学 report 操作完成了“输出部分交付状态”的职责；这不是建议所有部分交付都不记 error。实际根 span 的操作定义与业务契约若要求完整交付，可按明确规范标记失败。不要让不同团队对同一状态使用不同含义。

## 7. 子调用失败不会自动决定最终交付

第一次工具超时后，第二次重试成功，逻辑操作最终可能成功；失败的尝试 span 仍应保留，方便评估可靠性与成本。

画像失败但客流成功时，业务报告可能 partial。若把任何子 span 的 error 都自动传播为全任务 failed，可能忽略已有交付；若完全忽略子 span，则会掩盖缺失内容。

结果判定需要明确必需步骤、可选步骤、降级规则和证据质量。例如“区域全部门店排名”需要完整枚举，而“已查询候选中的排名”可接受部分范围，措辞不同。

本例把一次失败尝试捕获后继续执行，不自动给父 span 标 error；最终结果由显式业务属性描述。它没有生成真实报告或实现业务验收器。

## 8. Span 结束不是取消或提交

规范 End 只结束该 span 描述的操作，不自动结束子 span，也不从所有 Context 中撤销它；已结束 span 仍可能被用作父上下文。

本例 start 上下文管理器在 finally 中同时执行结束和 ContextVar reset，这是示例包装器的选择；不是 End API 自身自动清理当前上下文的保证。

也不能把 span.end() 当作数据库提交、工具取消、费用结算或 checkpoint。遥测系统采样/丢失不应决定订单是否执行；执行事实仍需业务账本。示例没有展示子 span 比父 span 更晚结束的并发情况。

## 9. 统计分母：尝试率与操作率

教学数据如下，费用为任意演示单位：

| 逻辑操作 | 尝试 | 结果 | 费用 |
| --- | --- | --- | --- |
| A | 1 | 失败 | 未知 |
| A | 2 | 成功 | 3 |
| B | 1 | 成功 | 2 |
| C | 1 | 失败 | 未知 |

物理尝试成功率为 2/4=50%；逻辑操作至少一次成功的比例为 2/3，约 66.7%。它们回答的问题不同。代码的操作成功判定只是“同一操作任一尝试成功”，前提是同一操作身份和成功回执语义可信；不适用于所有补偿或多步骤操作。

另有一次缓存命中，单独统计 cache_hits=1，没有把它伪装成供应商实际执行成功。若统计面向用户的逻辑查询成功率，需要将所有查询统一建模后计算，不能随意把缓存计数塞进上述分母。

已知费用小计为 5，还有两次费用未知。5 不能称为总成本，更不能据此说失败免费。使用真实费用时还应记录币种、来源与费率版本；本文不提供价格建议。

## 10. 延迟与采样口径

并行工具的耗时不能直接相加当作用户端到端时间：两项并行各两秒，关键路径可能约两秒而非四秒。用户等待还包括排队、首 Token、生成、审批和回源。

分别定义端到端、排队、模型、工具尝试、逻辑操作与恢复时间；比较分位数时不能把多组 p95 简单平均成总体 p95。

规范说明 IsRecording 与是否整条 Trace 被采样不是完全同一个概念；已记录的数据也不一定发送到后端。只分析可见 Trace 可能受到采样、丢失与导出故障影响，不能无条件当作所有业务请求的统计分母。

应通过定义明确的业务计数和指标获得总量，并验证采集是否重复或丢失。本例无计时、分位数、采样、Exporter 或 Collector；这些是设计解释，不是已测试能力。

## 11. 白名单、低基数与 Baggage

本例属性只接受有限枚举：business.outcome 与两个允许的 tool.name。access_token 或自由工具名字会被忽略。使用允许的键不意味着其值一定安全；本例进一步限制值，但仍未构建一般隐私审查机制。

常见敏感内容包括访问令牌、Cookie、手机号、精细位置、人群明细、提示词原文和内部错误信息。应定义必要采集、保留期限、访问权限和删除策略，不自动记录完整模型输入/输出，更不要求采集模型内部推理过程。

高基数值，如请求 ID、用户 ID、任意 SQL，通常不适合无界指标标签；它们可能导致大量时间序列。需要关联时可在受控 Trace/日志中记录，并评估访问与保留规则。

OpenTelemetry Baggage API 将 baggage 定义为随上下文关联的属性集合，并要求提供清空方式以避免向不可信进程发送这些值。不要把所有租户元数据或凭据放进 baggage 后自动传给供应商。本文只阅读规范，没有实现 baggage。

## 12. 已运行检查与接入路线

运行[标准库脚本](examples/observability_checks.py)：

~~~bash
python knowledge/agent-engineering/examples/observability_checks.py
~~~

本次 Python 3.12.14，输出：

~~~text
13 observability checks passed
{'attempts': 4, 'attempt_successes': 2, 'operations': 3,
 'operation_successes': 2, 'known_cost_units': 5,
 'unknown_cost_attempts': 2, 'cache_hits': 1}
~~~

十三组检查覆盖：异常后恢复父上下文；重试 span 身份；根/父关系；失败与重试状态；只记录异常类型；partial 与技术状态分离；属性白名单；复制上下文中的父关系；结束与根上下文清理；结束后拒绝修改；新请求生成新根；异常事件/状态优先级；尝试/操作/费用/缓存统计。

这是内存教学记录器，字段名中 business.* 为应用自定义，不声称符合某个 GenAI semantic conventions 版本。它没有执行 OpenTelemetry SDK，也没有验证序列化、传播、抽样、异步导出、丢失补偿、访问控制、并发安全或生产性能。

接入真实系统时，先选择并锁定 SDK 与语义约定版本，确定固定操作名和安全属性，再对一条业务链路验证传播、重试与结果判定。随后测试队列/服务边界和导出异常，确认可见 Trace 能与业务回执对上，而不只确认监控页面“有数据”。

练习：Agent 返回 HTTP 200，业务状态 partial，工具尝试成功率 50%。能否说明整个系统成功率 50%？答案：不能。三个结果属于不同层次，需先定义业务完成分母，再说明尝试可靠性与降级比例。

## 来源、许可与核验范围

核验日期：2026-10-04（UTC）；固定提交：[d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b](https://github.com/open-telemetry/opentelemetry-specification/commit/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b)，提交时间 2026-10-02T23:36:28Z。

- [Tracing API](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/specification/trace/api.md)：已阅读 SpanContext、父关系、Links、SetStatus、RecordException、End、IsRecording 与无 SDK 行为相关内容。
- [Baggage API](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/specification/baggage/api.md)：已阅读定义、上下文关联、清空和传播说明。
- [Apache License 2.0](https://github.com/open-telemetry/opentelemetry-specification/blob/d167c3b32e25b16a153e7cde5c6c9cb425bbdc3b/LICENSE)。

本文和脚本为独立教学解释与实现，未复制上游代码。复用上游材料应遵守其许可与适用声明要求；本文不是规范兼容性认证，后续版本应重新核验。

[返回 Agent 应用工程目录](README.md)
