# 经营报告：结论、证据、缺失项与审核

本篇为独立业务设计，全部输入与ID虚构；没有连接真实业务系统，也不声称开源项目已经实现这些业务功能。

## 业务问题与交付物

运营要每周收到区域客流、竞品和客群变化摘要。更可靠的报告应有结论覆盖表、数据版本、证据及无法回答的问题，不只是长篇流畅文字。

先约定必须回答的claim清单，再取得统计结果和可用原因证据。报告不能把“下降”这一事实与“下降的原因”合并为一条自动推断。稿件审核与实际发送另有权限；本篇只生成结构化草稿。

## 证据先行的编排

数据工具取得同口径结果；证据整理器为每条结论关联source_id和支持内容；确定性检查器核对覆盖；模型把通过检查的材料组织成可读报告。借鉴GPT Researcher的conduct_research与write_report分阶段机制。

建议每节包含claim_id、answer、sources、status、assumptions和next_action。缺证据不一定取消整份报告，可输出partial并明确“变化已确认、原因待核实”。原始统计与证据引用保持可寻址。

## 教学案例

必须回答traffic_change与change_cause，唯一资料fixture-1只支持traffic_change。build_report输出partial；第一节有source，第二节missing_evidence。

```json
{
  "status": "partial",
  "sections": [
    {"claim": "traffic_change", "sources": ["fixture-1"], "status": "supported"},
    {"claim": "change_cause", "sources": [], "status": "missing_evidence"}
  ]
}
```

supports集合由夹具预先标注；这不是通用自动事实检查器。真实引文能否支持结论，需要人工、规则或经过校准的语义评判。链接存在、来源很多都不等于内容正确。

## 面向业务的输出范式

先写关键结论，再给可行动建议与证据范围。行动建议应标明依据和假设：如“先核对数据成熟度”，而不是未经证实要求改变营销预算。可以附负责人待确认事项，但不自动指派或通知真实人员。

时间维度必须一致；昨天统计结果不能作为上周报告结论，当前产品文档也不能证明历史功能已存在。写作模型若增加新事实，应退回证据检查，不把新增句子自动放行。

## 验收与发布

人工金标准检查必需问题覆盖、数字正确、引文支持和缺失项保真；规则验证报告版本、日期与数据版本。正式发布应保存审核人或批准记录以及最终产物摘要。

本例只验证覆盖与证据集合匹配，没有搜索互联网、导出PDF或发送消息。真实效果以报告复核工时、错误更正和读者使用情况评估，不以文章长度衡量。

## 开源机制与示例验证

- [assafelovic/gpt-researcher：gpt_researcher/agent.py](https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/gpt_researcher/agent.py)：借鉴工具接口、上下文或评测机制，业务口径独立定义。
- 关联[100项应用知识](../ai-application-playbook/README.md)：004、009、028、087。
- [业务规则脚本](examples/business_rules.py)中的build_report；[已运行检查](examples/test_business_rules.py)；[实际示例输出](examples/expected-results.json)。

固定来源核验于2026-10-04；许可沿用[来源清单](../agent-case-studies/sources.md)。中文设计与示例独立编写，与原项目无隶属关系。

[返回业务案例目录](README.md)
