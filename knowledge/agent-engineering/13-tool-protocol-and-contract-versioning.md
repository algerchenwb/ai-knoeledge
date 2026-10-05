# 13. Agent 工具协议与契约版本：发现、失效和结果分类

一个选址 Agent 昨天使用 poi_profile 工具，传 poi_id 和月份，拿到客流画像。今天后端将“客流”改成“常驻人群”，字段仍叫 populationScale，返回仍是整数。JSON 完全合法，报告却可能失去业务意义。另一种问题是模型已经制定计划，工具列表随后更新，执行器还照旧调用。

本章结合 MCP 官方开源规范，解释协议兼容与业务契约如何协作，附原创离线目录守卫。规范依据固定的 **2026-07-28** 版本，并明确与 **2025-11-25** 及更早版本的差异；未运行 MCP SDK 或真实 HTTP 服务。

## 1. 四类版本必须分开理解

| 版本 | 回答的问题 | 示例 |
| --- | --- | --- |
| 协议版本 | 消息如何交换、结果如何解释？ | MCP 2026-07-28 |
| SDK/服务版本 | 具体程序是哪次发布？ | 网关构建编号、SDK 包版本 |
| 工具契约版本 | 参数、输出、语义和副作用是否变化？ | poi_profile 指标定义 v2 |
| 数据版本 | 这次结果对应哪批数据？ | 2026-09 月快照 |

支持相同协议，不代表指标口径一致。升级 SDK，也不代表所有下游工具都采用新 Schema。数据版本则影响报告复现和缓存，不能借工具契约版本代替。

建议业务结果显式返回统计周期、对象身份、population_type、口径版本和数据快照。它们是应用设计建议，不是 MCP 给所有业务统一规定的字段。

## 2. 新旧协议不能拼接使用

固定版本的官方兼容文档把 2026-07-28 及以后称为 modern，把 2025-11-25 及以前称为 legacy：

- modern 不依赖 initialize 握手，每个请求携带协议版本与客户端能力。
- legacy 使用 initialize 建立对应版本的语义。
- dual-era 实现可同时支持两种时代，按规范区分行为。

modern 请求在 params._meta 中包含必需的 io.modelcontextprotocol/protocolVersion 与 io.modelcontextprotocol/clientCapabilities；clientInfo 是建议提供，而非必填。HTTP 还涉及对应协议版本头和其他传输规则，本文示例不实现这些头。

不能从旧教程拿 initialize，再随意套入新版无状态机制。接入前先确认客户端、服务端支持的明确版本及传输绑定。

## 3. 版本选择必须来自共同支持的集合

modern 服务端必须实现 server/discover；客户端可先发现，也可直接请求后处理 UnsupportedProtocolVersionError。固定文档规定该错误代码为 -32022，并给出服务端支持版本。

离线 choose_version 按客户端偏好，从服务端声明集合选交集；无交集则失败。它仅是集合选择，不负责探测时代、不执行握手，也不实现网络降级。

真实兼容探测与 stdio、HTTP 有关。不要把任意超时或工具执行失败都解释成“服务端太老”，否则业务故障可能被错误降级掩盖。

## 4. 工具名字只在一个服务内标识工具

规范工具名称区分大小写的建议、允许字符等规则需要遵守，但跨服务仍可能同时出现 search。serverInfo.name 也不保证跨服务器唯一。

网关内部身份宜绑定受控 endpoint/configuration ID 与工具名，再为模型暴露不冲突的别名。示例 Scope 使用 endpoint，避免把不同服务的同名工具混用；真实系统应处理域名变更、路由别名等规范化问题。哈希或名字都不能证明服务身份可信。

## 5. 发现目录应按调用者上下文隔离

固定版本 tools/list 不应随连接状态或连接上其他请求的副作用变化，但允许按本次请求的授权范围返回不同工具。列表可能为空，也可能随时间变化，并支持分页。

把管理员的工具列表缓存给普通用户，会产生错误规划。教学 Scope 绑定 endpoint、tenant、subject、permission_revision 和 protocol；这是一种保守应用缓存键，不是协议要求的固定字段集。

服务端执行时仍必须验证输入和访问范围。客户端目录守卫不能替代服务端鉴权；传入权限版本的可信来源需要单独设计。

## 6. 分页目录要完整收集，再发布给规划器

如果前两页工具已对模型可见，第三页失败，Agent 会面对不完整目录。更安全的策略是把分页结果暂存在 staging 区，检查重复名称、游标循环及边界，全部完成后一次替换目录。

示例 refresh 接收调用者已收集完的列表，临时字典构建成功才替换；重复名字使整次更新失败。它不负责请求分页、判断分页期间是否发生更新，也没有上游目录快照保证。

固定规范建议稳定的工具顺序，以支持缓存与模型提示缓存。稳定顺序是工程便利，不是业务语义正确的证明。

## 7. 列表变化通知和 TTL 都有各自的边界

固定版本 tools/list 等列表结果有 ttlMs 和 cacheScope；通知能提示发生变化，但客户端可能没订阅、掉线或尚未收到通知。

支持 listChanged 的服务端，向通过 subscriptions/listen 并选择 toolsListChanged 的客户端发送变化通知。不要照搬旧版连接通知流程。通知应触发目录失效与重新发现，不能只修改 UI 标题。

示例 invalidate 立即禁止规划和派发，refresh 后重新开放。脚本不实现 TTL、订阅、掉线恢复和缓存协议；生产实现需要把通知与期限结合，未知新鲜度时采用明确策略。

## 8. Schema 变化检测采用保守指纹

教学指纹对整个工具定义和应用自定 semantic_revision 做稳定 JSON 序列化，再取 SHA-256。对象键顺序不影响结果；描述、annotations、输入输出定义或语义版本变化会影响指纹。

这里选择保守策略，因为描述变化也可能改变模型选工具的行为。但 required 数组换序即使语义一样，也会触发不同哈希；它不是完整的 JSON Schema 语义规范化。

哈希仅表示“这些字节定义是否相同”，不保证来源真实、不证明兼容、更不能发现服务端暗中改变指标。semantic_revision 必须由受控业务发布流程维护；它不是 MCP 自动提供的工具版本字段。

## 9. “只加一个字段”也可能破坏调用

新增可选输入字段通常比新增必填字段更容易兼容，但仍应检查默认值是否改变。输出新增字段可能被严格客户端拒绝；整数改字符串、时间单位改秒、坐标系改变、口径改变都有风险。

兼容性应分别测试旧输入是否接受、旧结果解析是否成功、业务意义是否保持、写入副作用是否改变。不能用“Schema diff 很小”直接批准。

本章没有实现通用兼容性判定器，也没有 JSON Schema 验证器。对于 $ref、组合关键字、远程引用及资源上限，应使用满足相应规范的验证层；参见[结构化输出与工具参数](05-structured-output-and-tool-contracts.md)。

## 10. 规划、审批与执行要绑定同一份定义

模型制定计划时记录目录 generation、工具指纹、作用域及参数快照。执行前再次比较；任一改变就阻止旧计划，重新规划或重新审批。

脚本将参数序列化成不可变 bytes，调用者之后修改原字典不影响计划。每次 refresh 都增加 generation，因此即使定义相同，旧计划也会被保守拒绝。这会增加重新规划次数，但示例不尝试自动证明旧计划可复用。

该检查只在同步 mock operation 调用前进行，不覆盖网络期间的目录更新、跨进程原子性或后端参数校验。Plan 是教学对象，不是签名审批票据，可被本地代码伪造；应结合[审批与版本绑定](02-human-approval-and-versioned-actions.md)。

## 11. JSON-RPC 成功响应不等于工具或业务成功

| 响应状态 | 含义 | 处理建议 |
| --- | --- | --- |
| 顶层 error | 协议层错误，例如未知工具、请求结构问题 | 按具体错误处理，避免无脑重复 |
| result 且 isError=true | 工具执行错误，可能可调整参数 | 读取反馈，按预算和幂等策略处理 |
| resultType=input_required | 尚需输入的中间结果 | 进入相应交互/继续流程，不能记成功 |
| resultType=complete 且无工具错误 | 工具完成候选结果 | 继续校验输出 Schema、证据和业务条件 |

固定版本还允许 structuredContent 是任意 JSON 值，只要符合声明的 outputSchema；不能假定总是对象。服务端提供 outputSchema 时必须给出符合它的结构化结果，客户端应校验。工具结构化结果也不同于模型的 Schema 约束生成。

响应必须匹配请求 ID，数字 1 与字符串 "1" 不能混淆；Python True==1，因此脚本同时检查类型。实际 JSON-RPC 客户端还需完整验证合法 ID、通知与数据格式。示例只处理调用响应子集。

## 12. 中间结果、重试身份与业务幂等不能混用

固定工具文档规定，input_required 的重试携带 inputResponses 和可选 requestState，并使用不同的 JSON-RPC id。新 RPC id 用于区分消息；同一业务操作的幂等键是否沿用，仍取决于业务协议。

如果是创建报告或支付操作，不应因为 RPC id 换了就创建重复业务动作。需要把操作身份、参数快照、回执与 MRTR 延续状态关联起来。

脚本把 needs_input 单独分类，不处理输入内容、不执行 MRTR 重试、不实现 requestState 验证。complete_candidate 也仅是分类标签，不代表数据可信或业务验收通过。

## 开源来源、日期与许可

核验日期 **2026-10-05（北京时间）**。官方仓库当前使用 [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol)；旧 specification API 地址返回迁移提示。固定提交 **75db1e987cbbba6d170315dc99d0dfc440754aef**，提交时间 **2026-10-03T01:52:20Z**。

| 固定源码 | 已核验重点 |
| --- | --- |
| [Versioning](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/docs/specification/2026-07-28/basic/versioning.mdx) | modern/legacy、每请求版本、错误与双时代兼容 |
| [Tools](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/docs/specification/2026-07-28/server/tools.mdx) | 名称范围、目录、Schema、结果、MRTR 与错误层次 |
| [Basic](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/docs/specification/2026-07-28/basic/index.mdx) | 必需和可选的请求 _meta 字段 |
| [Changelog](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/docs/specification/2026-07-28/changelog.mdx) | 无状态、订阅、resultType、Schema 与缓存变化 |

许可不能沿用旧 README 的单一 MIT 说法。固定 [LICENSE](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/75db1e987cbbba6d170315dc99d0dfc440754aef/LICENSE) 明示许可过渡：新代码与规范贡献使用 Apache-2.0，已获重许可同意的贡献亦如此；未同意重许可的原 MIT 贡献仍为 MIT；非规范文档贡献采用 CC-BY-4.0。本文以原创中文释义和应用推导讲解，并编写独立脚本，没有复制上游实现；上游权利归其作者及 Model Context Protocol 项目，具体复用须以文件及贡献适用许可为准。

## 已运行检查与限制

[tool_protocol_checks.py](examples/tool_protocol_checks.py) 无第三方依赖：

~~~bash
python knowledge/agent-engineering/examples/tool_protocol_checks.py
~~~

Python **3.12.14** 下 **18 项 unittest 全部通过**：有效派发、稳定键顺序、语义/描述变化、参数快照、目录失效、旧计划拒绝、权限/服务/租户隔离、重复目录原子拒绝、版本交集、响应 ID、result/error 互斥、错误层次、中间结果、新旧版本标记差异、未知标记、非法错误布尔值与 NaN 参数。

范围为同步单线程离线对象，mock 工具只登记调用；没有完整 MCP 封装、HTTP/stdio、SDK、订阅、目录分页、TTL、OAuth、输出 Schema、并发竞态或真实 Agent 集成。Scope 和 semantic_revision 由测试直接提供；它们不是真实认证证据。示例不是协议一致性认证，不应作为生产网关直接部署。

## 自测练习

1. populationScale 仍为整数，但从客流改为居住人数，应变更哪些版本和报告字段？
2. 同名 search 来自两个服务，如何防止计划路由到错误服务？
3. 列表通知在审批后到达，为什么旧审批不能直接套用到新定义？
4. input_required 后重试使用新 RPC id，业务幂等键是否也必须变？说明判断依据。

[返回专题目录](README.md)
