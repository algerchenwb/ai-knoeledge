# Agent 开源实现案例：十篇深度教程

把公开代码中已经实现的机制拆清楚，再解释如何迁移到业务。这里的“成功实现”指存在可追溯的实现或上游演示；每篇标明证据级别，不把模拟工具、配置文件或README宣传当作已验证的生产成效。

| 序号 | 案例与核心知识点 | 适合研究的问题 |
|---|---|---|
| 1 | [LangGraph SQL Agent：把必经步骤写进流程图](01-langgraph-sql-workflow.md) | 数据查询与口径控制 |
| 2 | [客服转接 Agent：共享上下文与明确责任](02-agents-sdk-customer-handoff.md) | 客服/API请求路由 |
| 3 | [AutoGen 代码执行协作：把运行结果反馈给生成者](03-autogen-code-execution-feedback.md) | 生成与执行反馈 |
| 4 | [CrewAI 研究报告流水线：角色之后还要有交付契约](04-crewai-research-report-contracts.md) | 研究与写作交付 |
| 5 | [smolagents CodeAgent：用代码组合工具完成查询](05-smolagents-code-as-action.md) | 批量工具组合 |
| 6 | [SWE-agent 修复闭环：复现、修改、验证与提交检查](06-swe-agent-repair-verification.md) | 仓库修复回归 |
| 7 | [OpenHands Agent Canvas：让 Agent 接入执行后端与任务控制面](07-openhands-agent-canvas-control-plane.md) | 后端与任务运行管理 |
| 8 | [Browser Use 浏览器 Agent：观察、行动与页面变化保护](08-browser-use-observe-act-verify.md) | 动态页面交互 |
| 9 | [GPT Researcher：规划检索、汇集证据、再写报告](09-gpt-researcher-evidence-pipeline.md) | 研究报告与证据 |
| 10 | [LlamaIndex Agentic RAG：把不同资料库封装成检索工具](10-llamaindex-agentic-rag-tools.md) | 多语料检索比较 |

每篇包含具体任务、代码执行路径、可迁移机制、业务改造、验收和练习。读API Agent时优先1、2、5、7；读知识库应用时优先4、9、10；读编码与自动化时优先3、6、8。先从单Agent与明确工具试点，再按权限、数据源和检查责任划分协作，不以Agent数量作为成熟度。

[来源、许可与验证范围](sources.md) · [100个应用知识点](../ai-application-playbook/README.md)

## 已运行的离线机制检查

```bash
python knowledge/agent-case-studies/examples/agent_case_checks.py
```

Python3.12.14，10项标准库检查全部通过。只执行独立教学夹具，没有运行上游框架或模型。涉及有界重试、幂等和引用等部分只演示基本条件，不替代并发、崩溃和语义集成测试。

[返回总入口](../../README.md)
