# Microsoft Generative AI for Beginners · 中文知识库

本专题解读微软的生成式 AI 应用开发课程，覆盖环境准备和 21 节课程。面向希望把概念落实到接口、数据查询与可维护服务的开发者。

## 这是什么仓库

原仓库是一套课程与教学样例，主线是一个虚构的教育创业项目：学习助手、课程搜索、作业与发票处理。它不是一个可直接上线的统一 AI 平台，也不是从数学到训练大模型的完整教材。Python、TypeScript 与部分其他语言实现分布在不同章节，实际可运行性要按版本检查。

本专题用中文重新解释知识点，加入区域洞察、商圈画像和 API Agent 例子。标为「工程补充」的内容是额外实践；具体代码问题以固定快照为依据。笔记没有复制整个上游仓库，没有声称所有原例子已在线运行。

## 来源与版本

- [上游仓库](https://github.com/microsoft/generative-ai-for-beginners)
- 核对日期：2026-10-03。
- 固定上游提交：d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8。
- [上游固定目录](https://github.com/microsoft/generative-ai-for-beginners/tree/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8)。
- [来源、许可与更新规则](SOURCES.md)。

每篇完成后通过独立 GitHub 提交同步，提交历史可查看每个主题的加入过程。未来补充可在现有文章修改，而不用重复建同一课程目录。

## 全部课程

| 编号 | 中文详解 | 学完能做什么 |
| --- | --- | --- |
| 00 | [环境准备与仓库导航](00-course-setup.md) | 配置环境并识别调用失败层次 |
| 01 | [生成式 AI 与大语言模型](01-introduction-to-genai.md) | 理解 token、预训练、推理与幻觉 |
| 02 | [模型分类与选择](02-exploring-and-comparing-different-llms.md) | 用任务评测选择模型 |
| 03 | [负责任地使用 AI](03-using-generative-ai-responsibly.md) | 定义风险与缓解措施 |
| 04 | [提示词工程基础](04-prompt-engineering-fundamentals.md) | 编写可验证的提示模板 |
| 05 | [高级提示词与任务拆解](05-advanced-prompts.md) | 使用示例、拆解和验证 |
| 06 | [文本生成应用](06-text-generation-apps.md) | 构建模型调用闭环 |
| 07 | [对话应用与上下文管理](07-building-chat-applications.md) | 管理历史与任务状态 |
| 08 | [Embedding 与语义搜索](08-building-search-applications.md) | 设计向量检索与索引 |
| 09 | [图像生成应用](09-building-image-applications.md) | 理解生成、编辑与输出处理 |
| 10 | [低代码 AI 应用](10-building-low-code-ai-applications.md) | 划分低代码与后端职责 |
| 11 | [函数调用与外部 API](11-integrating-with-function-calling.md) | 实现模型建议与后端执行闭环 |
| 12 | [AI 产品体验设计](12-designing-ux-for-ai-applications.md) | 设计可信、可恢复的交互 |
| 13 | [AI 应用安全](13-securing-ai-applications.md) | 守住资料、工具与租户权限 |
| 14 | [LLMOps 与应用生命周期](14-the-generative-ai-application-lifecycle.md) | 建立评测、监控与回滚 |
| 15 | [RAG 与向量数据库](15-rag-and-vector-databases.md) | 实现检索到生成的完整链路 |
| 16 | [开放模型与 Hugging Face](16-open-source-models.md) | 检查模型资产与部署条件 |
| 17 | [Agent 与工作流](17-ai-agents.md) | 选择工作流或受控 Agent |
| 18 | [模型微调](18-fine-tuning.md) | 判断何时微调并评估收益 |
| 19 | [小语言模型与本地推理](19-slm.md) | 估算资源并测试本地推理 |
| 20 | [Mistral 模型案例](20-mistral.md) | 用具体版本理解家族差异 |
| 21 | [Meta Llama 模型案例](21-meta.md) | 理解工具格式与视觉变体 |

## 建议学习路线

基础路线：00 → 01 → 02 → 04 → 05 → 06 → 07。

RAG 路线：08 → 15 → 13 → 14。先把搜索做好，再让模型依据搜索结果回答。

API Agent 路线：04 → 11 → 17 → 13 → 14 → [后端实践](appendices/api-agent-backend.md)。先验证单工具，再扩展受控循环。

本地模型路线：02 → 16 → 19 → 18；20 和 21 用作家族案例，不能替代当前具体型号的官方资料。

03、12、13 和 14 应贯穿开发，而不是项目最后才补。

## 延伸材料

- [术语速查表](appendices/glossary.md)
- [API Agent 后端实践](appendices/api-agent-backend.md)
- [原代码问题与修正指南](appendices/code-review.md)
- [练习与验收清单](appendices/exercises.md)
- [离线 RAG 与工具执行示例](examples/README.md)

## 知识之间的关系

提示词定义任务，Embedding 支持检索，RAG 提供证据，Function Calling 连接外部工具，Agent 在状态中组织动作，LLMOps 让整个系统可评价和维护。微调改变模型行为；它与检索和工具接入可以组合，但不能互相替代。

## 已有深化笔记

仓库已有[第 00—21 课深化笔记](deep-dives/README.md)，保留作为进一步阅读，涵盖提示词校验、服务实现、聊天状态、语义搜索、图像交付、低代码工作流、受控工具执行、产品体验、安全边界、LLMOps、RAG证据链、开放模型、Agent状态、微调数据和小模型部署。第08、11、15与19课另附可运行的离线检查脚本。00–03补充环境、机制、选型和责任验收；20–21补充模型案例代码解读。2026-10-04，四份测试模块合计46项离线检查全部通过。全部22个课次均已提供概览和深化讲解；不代表真实模型与云服务已完成集成验证。
