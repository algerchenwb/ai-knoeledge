# 客户服务：问题分类、工单路由与响应优先级

本篇为独立业务设计，全部输入与ID虚构；没有连接真实业务系统，也不声称开源项目已经实现这些业务功能。

## 业务问题与目标

客户反馈“昨天数据没有更新”或“指标看不懂”，两者不应都由同一技术人员从头排查。Agent可以识别问题、收集最小信息、路由到正确团队，并保留当前处理状态。

教学策略区分data_delay、metric_question与outage。优先级是示例业务规则，不是合同SLA：延迟默认normal，影响多人则high；outage路由incident且high；未知类型进入manual_triage。

## 从对话到工单

模型先建议类别，并收集对象、统计日期、request_id及现象；规则服务确定队列和优先级；授权工单工具创建工单；回复层依据真实ticket_id报告状态。借鉴客服handoff，让专业处理域继续对话，但不能只改current_agent就宣布工单已创建。

建议工单字段category、impact_scope、evidence、owner_team、priority、status和idempotency_key。实际响应时限从客户合同或服务政策取得；本篇不编造“必须几分钟响应”的通用数字。

## 确定性案例

输入kind=data_delay，affects_many=true；ticket_route返回team=data_operations、priority=high。未知kind返回manual_triage与normal。具体类别只有在已经确认后才进入函数；自然语言分类未在脚本实现。

```json
{
  "team": "data_operations",
  "priority": "high"
}
```

模型认为“影响很大”不等于affects_many已证实。影响范围可以通过监控、关联投诉或服务状态确认，并保存依据。未知问题必要时应提高人工关注，而非机械永远按normal处理；示例策略须按业务政策调整。

## 状态与用户沟通

区分“已记录问题”“已创建工单”“正在处理”“已修复”“已验证恢复”。每次对外状态基于系统记录；创建接口超时先查询幂等键或已有工单，避免同一次投诉重复创建。

解释类问题可以从指标定义库回答，仍要引用定义版本。数据故障要承认未确认的部分，不把“可能是延迟”说成确定原因。历史SLA和旧状态不能无限沿用。

## 验收标准

金标准包含含糊反馈、混合问题、重复投诉、错误对象和未知故障；评估路由准确率、有效信息完整率、转接次数、首次有效响应时间与错误结案率。

离线检查只覆盖规则路由和未知兜底；没有创建、取消或通知任何工单，没有运行对话分类模型，也不验证SLA。生产路由需结合真实团队责任与数据权限。

## 开源机制与示例验证

- [openai/openai-agents-python：examples/customer_service/main.py](https://github.com/openai/openai-agents-python/blob/81f0ccf20c6e24063b9da36fa37f2bdb6a43d8d3/examples/customer_service/main.py)：借鉴工具接口、上下文或评测机制，业务口径独立定义。
- 关联[100项应用知识](../ai-application-playbook/README.md)：016、021、022、029、089。
- [业务规则脚本](examples/business_rules.py)中的ticket_route；[已运行检查](examples/test_business_rules.py)；[实际示例输出](examples/expected-results.json)。

固定来源核验于2026-10-04；许可沿用[来源清单](../agent-case-studies/sources.md)。中文设计与示例独立编写，与原项目无隶属关系。

[返回业务案例目录](README.md)
