# 销售支持：客户需求与产品能力匹配

本篇为独立业务设计，全部输入与ID虚构；没有连接真实业务系统，也不声称开源项目已经实现这些业务功能。

## 业务问题与交付

售前收到“需要区域画像、OAuth接入和自动导出”的需求，希望快速判断能否交付。Agent应输出已支持、条件支持、未支持和待确认项，以及证据与下一步，不应凭相似功能名承诺全部支持。

这里分析的是客户公司的业务需求，不建立个人敏感画像，也不执行营销外发。公开案例里的产品、能力与客户标识均虚构。

## 两层匹配流程

第一层把客户描述拆成能力、范围和验收条件；第二层从版本化能力库取得证据并匹配。能力库可分为产品说明、接口文档和交付限制，分别封装检索工具，借鉴LlamaIndex跨语料查询机制。

结构建议requirement_id、capability_id、support_status、version、evidence、conditions、owner。比如“有OAuth”还要确认客户端注册、授权流程和所需工具范围，不能只查到OAuth这个词就判断满足要求。

## 确定性样例

需求集合{profile,oauth,export}，已验证能力集合{profile,oauth}。capability_match返回gap、matched=[oauth,profile]、missing=[export]。它是集合级金标准，不是自然语言理解或完整产品匹配算法。

```json
{
  "status": "gap",
  "matched": ["oauth", "profile"],
  "missing": ["export"]
}
```

模型负责提出候选映射，业务规则和证据负责确认。条件支持与待确认状态尚未在简化函数实现；文档设计应先保留这些状态，再按真实产品规则扩展。

## 业务回复怎样避免误承诺

可以写“画像和OAuth已找到对应版本证据；导出尚未确认，需要负责人提供支持范围或交付方案”。不能把“可通过二次开发实现”改写成“当前已支持”。预计工期、合同价格和上线承诺需由授权人员确认。

客户描述里可能把业务结果与技术方式混在一起。先识别核心结果，再比较是否有其他已支持路径；例如客户要批量结果，不一定只接受浏览器下载。但替代方案也要说明差异并确认是否满足验收。

## 评估方法

建立人工确认的需求—能力匹配集，评分包括必要条件覆盖、错误承诺率、证据新鲜度和人工补充次数。未知能力应该保持未知，而不是为了提高匹配率强行归类。

离线示例只检查精确能力ID集合，不检索文档、不推断相似能力，也不连接CRM。检索版本与交付负责人工作流需另行实现。

## 开源机制与示例验证

- [run-llama/llama_index：docs/examples/agent/react_agent_with_query_engine.ipynb](https://github.com/run-llama/llama_index/blob/962940ddc079cc21701d28d1237c84c82a7c5164/docs/examples/agent/react_agent_with_query_engine.ipynb)：借鉴工具接口、上下文或评测机制，业务口径独立定义。
- 关联[100项应用知识](../ai-application-playbook/README.md)：009、011、031、087。
- [业务规则脚本](examples/business_rules.py)中的capability_match；[已运行检查](examples/test_business_rules.py)；[实际示例输出](examples/expected-results.json)。

固定来源核验于2026-10-04；许可沿用[来源清单](../agent-case-studies/sources.md)。中文设计与示例独立编写，与原项目无隶属关系。

[返回业务案例目录](README.md)
