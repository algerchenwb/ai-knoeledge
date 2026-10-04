# CrewAI 研究报告流水线：角色之后还要有交付契约

核验日期：2026-10-04。证据级别：官方研究员与报告员模板及 README 的顺序任务配置；未提供本轮运行效果。

## 1. 实际案例结构

官方例子用 researcher 搜集主题资料，再由 reporting_analyst 扩写成 Markdown 报告。旧式 Python/YAML 模板定义两个 Agent、两个 Task 和 Process.sequential；当前 README 的 JSON 配置明确让 reporting_task 的 context 指向 research_task，并指定输出文件。

它展示的知识点不是“给模型取两个职位就会合作”，而是**任务依赖与交付格式决定合作是否可用**。研究员像交材料的人，报告员像拿材料整理的人；如果前者没交可信资料，后者文笔再好也没有事实依据。

## 2. Agent、Task、Crew、Flow 分别负责什么

Agent 定义执行者的角色、目标和工具范围；Task 定义具体要完成的工作与预期产物；Crew 组织人员和任务过程；Flow 用事件和状态控制整个流程。角色说明影响模型行为，程序化任务依赖则决定谁先做、谁收到什么结果。

仓库区分 Crews 的自主协作与 Flows 的流程控制。可以用 Flow 处理请求校验、条件分支和异常出口，只把不确定的研究或写作阶段交给 Crew。不必把一个固定格式转换也包装成自主讨论。

## 3. 什么是交付契约

上游任务要求研究结果若干要点、后续 Markdown 报告。教学扩展可以把研究产物变成结构化记录：claim、source_url、published_at、fetched_at、supporting_excerpt、uncertainty。报告阶段只接收通过校验的记录。

例如研究“开放平台是否支持 OAuth”，一条材料应区分“已上线”“测试中”“计划”；发布时间与证据片段应能追溯。写作 Agent 不应把计划改写成现有能力。结构正确也不代表事实正确，校验器要分别检查字段与引用支持。

## 4. 明确依赖，避免隐式上下文误会

当前 JSON 示例通过 context 指定 research_task，是显式依赖；本文不把所有版本的顺序模式概括为“自动可靠传递任意状态”。旧模板只是项目生成器的材料，含占位符，不能复制成普通 Python 后直接运行。

2026-10-04 当前 README 写明默认创建 JSON-first 项目；Python/YAML 旧脚手架需要 --classic。选型和复现时必须记录所用版本与脚手架形式，不能同时采用新 CLI 说明与旧目录假设。

## 5. 为什么多角色有时反而变差

报告员可能继承研究员的错误；同一模型换角色并不意味着独立证据。任务数增加会增加费用、延迟和交接损失。只有当分工对应不同工具、数据权限或检查责任时，才更容易带来工程价值。

报告生成失败时应保留已收集资料，允许仅重做写作。研究结论变化则要使下游报告失效。若只重试最后一步却不管依赖版本，容易发布引用旧材料的新报告。版本号和产物摘要应随任务结果保存。

## 6. 如何做一个可评估试点

教学试点：选10个固定问题，每个准备人工核实的引用和必须覆盖的要点；比较单 Agent 与两阶段 Crew 的完整率、引用正确率、总费用和耗时。缺失证据时要求明确标记，而不是编补内容。报告保存成功与事实正确分别评分。

[离线脚本](examples/agent_case_checks.py)检查研究未完成前禁止报告、完成后传递同一证据产物，未运行 CrewAI。练习：expected_output 写“详细报告”为什么不够？因为它没有规定哪些要点必需、每个结论如何验证，也没有可执行的合格条件。

## 开源来源

- [README.md](https://github.com/crewAIInc/crewAI/blob/738c8e19e35c2888d8e0663bc5cc45c5acf6ac2d/README.md)
- [lib/cli/src/crewai_cli/templates/crew/crew.py](https://github.com/crewAIInc/crewAI/blob/738c8e19e35c2888d8e0663bc5cc45c5acf6ac2d/lib/cli/src/crewai_cli/templates/crew/crew.py)
- [lib/cli/src/crewai_cli/templates/crew/config/tasks.yaml](https://github.com/crewAIInc/crewAI/blob/738c8e19e35c2888d8e0663bc5cc45c5acf6ac2d/lib/cli/src/crewai_cli/templates/crew/config/tasks.yaml)

来源与许可见[快照清单](sources.md)。中文解释与业务改造由本知识库独立编写，不是官方逐字翻译；改造建议不表示上游已经实现。

[返回案例目录](README.md)
