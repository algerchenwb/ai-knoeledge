# 客服转接 Agent：共享上下文与明确责任

核验日期：2026-10-04。证据级别：官方可运行示例；FAQ 和选座工具是本地模拟，不连接航空订单系统。

## 1. 成功实现的范围

官方客服示例把一个航空服务对话拆成 Triage Agent、FAQ Agent 和 Seat Booking Agent。分诊负责判断问题交给谁，FAQ 通过工具查信息，选座专员收集确认号和座位，处理结束或遇到无关问题时可以转回分诊。

这是一个实现完整的转接示例，但 FAQ 是代码中的固定文本，update_seat 只改变内存上下文，航班号在转接回调中随机生成。它证明了转接机制如何连接，不能当作真实航空业务上线效果。

## 2. Handoff 与“把 Agent 当工具”有什么不同

Handoff 可以先理解成“把电话转到另一位专员”：目标 Agent 成为接下来处理会话的主体。Agent-as-tool 则更像“当前客服向专家咨询”：专家返回结果后，由当前客服继续组织回复。两者的关键差别是控制权与对外责任，不能仅凭多了几个 Agent 名称就判断协作结构。

代码把 FAQ 与选座 Agent 注册为分诊的 handoffs，又给二者增加返回分诊的 handoff。on_seat_booking_handoff 是转入选座时执行的回调。Runner.run 返回 last_agent，外层把它保留为下一次输入的 current_agent，所以后续消息不会无条件从分诊重新开始。

## 3. 上下文与消息历史要分开理解

AirlineAgentContext 是类型化业务状态，含 passenger_name、confirmation_number、seat_number 和 flight_number；RunContextWrapper 让工具与回调访问这些状态。消息历史则通过 result.to_input_list() 接续下一轮。业务状态属于程序对象，不等于所有字段会自动以可见文字送给模型。

好处是订单标识和工作进度不必反复从聊天文本中解析。风险是把共享状态误当作授权依据：用户说出的确认号只是输入，真实订单所有权还需要后端校验。会话 ID 也不能直接替代登录身份。

## 4. 逐步读代码

1. 用户发送问题，程序把输入加入消息列表。
2. Runner 驱动当前 Agent，可能产生普通回复、转接或工具调用。
3. 程序分别识别 MessageOutputItem、HandoffOutputItem、ToolCallItem 和 ToolCallOutputItem。
4. update_seat 更新上下文，并断言航班号已由转接回调填入。
5. 保存消息与 last_agent，进入下一轮。

trace 使用同一个 group_id 把多轮关联起来。它便于看“为什么到了选座”，但轨迹存在不代表所有业务操作都正确。日志还应区分提议、执行、成功和失败。

## 5. API Agent 可以借鉴什么

如果已有大量业务接口，可以先按真实责任分为查询、解释和变更三个处理域。不是给每个接口都建一个 Agent，而是给模型少量语义明确的工具入口，例如“获取区域画像”和“解释指标定义”。

教学扩展的转接单应带 request_id、目标域、已解析对象、缺失参数和路由原因。接口参数经过 schema 检查后，再由服务端补入鉴权主体。变更类工具返回真实事务结果或任务 ID，不能仅靠上下文赋值便回复“已完成”。需要审批的实际动作可以暂停等待外部审批事件；这是本文落地建议，不是本例已经实现的功能。

## 6. 验证与常见误区

测试包括：FAQ 成功；无答案回退；选座信息缺失；选座中途问行李；同一请求重复提交；转接循环超过上限。指标分别记录路由准确率、信息收集完成率、真实执行成功率和平均转接次数。

[离线脚本](examples/agent_case_checks.py)检查模拟转接后上下文与 current_agent 保持一致；没有调用 SDK 或模型。练习：为什么不能把随机航班号回调直接搬到生产？因为示例在模拟前置条件，真实航班应从已验证订单取得。

## 开源来源

- [examples/customer_service/main.py](https://github.com/openai/openai-agents-python/blob/81f0ccf20c6e24063b9da36fa37f2bdb6a43d8d3/examples/customer_service/main.py)
- [docs/handoffs.md](https://github.com/openai/openai-agents-python/blob/81f0ccf20c6e24063b9da36fa37f2bdb6a43d8d3/docs/handoffs.md)

来源与许可见[快照清单](sources.md)。中文解释与业务改造由本知识库独立编写，不是官方逐字翻译；改造建议不表示上游已经实现。

[返回案例目录](README.md)
