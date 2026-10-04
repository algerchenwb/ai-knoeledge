# GPT Researcher：规划检索、汇集证据、再写报告

核验日期：2026-10-04。证据级别：完整研究入口与检索调度实现；本篇未复现外部搜索或报告事实正确率。

## 1. 与直接问模型的不同

GPT Researcher 把研究过程分成搜集上下文和撰写报告。README 描述从研究问题规划、网络查找、内容汇总到带来源的报告。agent.py 的 GPTResearcher 组合 ResearchConductor、ReportGenerator、ContextManager 等组件，提供 conduct_research 与 write_report 两个主要阶段。

知识点是**先形成可追溯证据，再把证据组织成文章**。模型的语言能力负责表达，检索获得的资料负责支撑事实；两者混在一个自由回答里，往往难以解释结论从哪里来。

## 2. 代码中已经实现的机制

ResearchConductor 先进行初始搜索，再规划子查询，收集对应内容。源码在多来源路径中使用 asyncio.gather 并发汇集上下文，visited_urls 帮助避免重复处理同一 URL。主 Agent 保留 context、research_sources、research_costs 和分步费用等状态。

这不是十个完全独立研究员各自随意讨论。更准确的理解是有规划的检索任务、抓取与上下文处理，共同进入报告阶段。深度研究另有独立分支，本篇不把普通流程与递归深度研究的参数和成本混为一谈。

## 3. 有引用不等于结论正确

引用链接存在只是第一层；页面确实支持邻近结论才是第二层；来源足够新、原始与独立是进一步条件。十个网站转载同一条消息，不能当作十份独立证据。URL 去重也不会自动识别内容转载。

教学扩展的证据单包含 claim_id、source_url、source_date、fetched_at、supporting_text 和 conflict。写作前先核对证据支持程度，把推断标成推断，冲突资料并列解释。研究工具不能保证文章天然客观无偏，README 的定位不应直接改写为测得的准确率。

## 4. 业务研究可以怎么做

例如研究“哪些开源 Agent 能适配80个业务 API”。先定义维度：工具描述、鉴权、任务状态、错误恢复、流式事件和可观测性；按维度查原始仓库文档与代码；结果表逐项给出支持、限制和来源提交。

不要仅根据项目宣传词“生产可用”打勾。某项目有 MCP 客户端，不代表拥有符合公司要求的 OAuth 服务端；有 trace，不代表现成接入内部 Langfuse。功能清单和真实集成成本需要分别记录。这些业务改造是本文设计。

## 5. 控制研究树的成本

查询数、分支深度、抓取页面、上下文长度都会增加时间和费用。先限制目标问题与来源域，设置超时、最大查询数和每个来源的长度，缺失资料作为明确结果返回。并发减少等待时间，也可能增加限流与共享状态冲突，应记录每个分支状态。

缓存要考虑时间范围和数据版本，不能仅以问题文本做永久缓存。重试一个失败来源时尽量保留其他成功证据；最终报告明确写出覆盖范围。源码有费用和去重状态，但预算策略仍需按部署条件评估。

## 6. 怎么验收

准备含公开金标准的问题集，分别评估关键结论正确率、引用支持率、独立来源覆盖、冲突处理和报告时效；把完整成本与耗时记录到运行 ID。不要让同一个写作模型的自评分成为唯一裁判。

[离线脚本](examples/agent_case_checks.py)用固定证据夹具验证缺失或不支持结论的引用会被拒绝。这是严格的夹具匹配演示，未实现通用语义蕴含验证，也未调用 GPT Researcher。练习：抓到20个链接为什么仍可能回答不了问题？因为资料数量与问题所需的具体证据是两个概念。

## 开源来源

- [README.md](https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/README.md)
- [gpt_researcher/agent.py](https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/gpt_researcher/agent.py)
- [gpt_researcher/skills/researcher.py](https://github.com/assafelovic/gpt-researcher/blob/0957c301ed06c2a5857b834358c7227c739041d4/gpt_researcher/skills/researcher.py)

来源与许可见[快照清单](sources.md)。中文解释与业务改造由本知识库独立编写，不是官方逐字翻译；改造建议不表示上游已经实现。

[返回案例目录](README.md)
