# 开源来源、固定快照与验证范围

核验日期：2026-10-04。覆盖15个开源仓库；每个仓库读取README和许可，十个Agent案例另读取具体示例或实现。SHA只是读取快照，不代表发布版本、稳定分支或商业产品版本。完整读取路径见[机器可读清单](sources.json)。

| ID | 仓库 | 快照 | 许可 |
|---|---|---|---|
| S01 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | [9a0394d88b22](https://github.com/langchain-ai/langgraph/tree/9a0394d88b2211f299dcd69df92db3480c69ee61) | MIT |
| S02 | [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | [81f0ccf20c6e](https://github.com/openai/openai-agents-python/tree/81f0ccf20c6e24063b9da36fa37f2bdb6a43d8d3) | MIT |
| S03 | [microsoft/autogen](https://github.com/microsoft/autogen) | [027ecf0a379b](https://github.com/microsoft/autogen/tree/027ecf0a379bcc1d09956d46d12d44a3ad9cee14) | 文档 CC-BY-4.0；代码 MIT |
| S04 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | [738c8e19e35c](https://github.com/crewAIInc/crewAI/tree/738c8e19e35c2888d8e0663bc5cc45c5acf6ac2d) | MIT |
| S05 | [huggingface/smolagents](https://github.com/huggingface/smolagents) | [c30b115286e0](https://github.com/huggingface/smolagents/tree/c30b115286e000e98711fae5e85993547b73d826) | Apache-2.0 |
| S06 | [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | [3ea751c087f3](https://github.com/SWE-agent/SWE-agent/tree/3ea751c087f32b16e039a2233dd6eefecef325d5) | MIT |
| S07 | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | [a6bba78ffd5a](https://github.com/OpenHands/OpenHands/tree/a6bba78ffd5a8b31620770f52383b1a2c0477fcd) | MIT |
| S08 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | [7be96ed8bafa](https://github.com/browser-use/browser-use/tree/7be96ed8bafa8dfe1eef228b59cf5c884b8b2431) | MIT |
| S09 | [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | [0957c301ed06](https://github.com/assafelovic/gpt-researcher/tree/0957c301ed06c2a5857b834358c7227c739041d4) | Apache-2.0 |
| S10 | [run-llama/llama_index](https://github.com/run-llama/llama_index) | [962940ddc079](https://github.com/run-llama/llama_index/tree/962940ddc079cc21701d28d1237c84c82a7c5164) | MIT |
| S11 | [fastapi/fastapi](https://github.com/fastapi/fastapi) | [5f9fc5c59a9b](https://github.com/fastapi/fastapi/tree/5f9fc5c59a9bb54608aa35376715f3ba9708188e) | MIT |
| S12 | [qdrant/qdrant](https://github.com/qdrant/qdrant) | [6ab21cac18eb](https://github.com/qdrant/qdrant/tree/6ab21cac18ebb6f4ae29102c7f8f5cc11affd5de) | Apache-2.0 |
| S13 | [docling-project/docling](https://github.com/docling-project/docling) | [58f1f8d907fd](https://github.com/docling-project/docling/tree/58f1f8d907fdc4610cd8dca20da6ef53a4550ee8) | MIT |
| S14 | [BerriAI/litellm](https://github.com/BerriAI/litellm) | [a2bf67a03707](https://github.com/BerriAI/litellm/tree/a2bf67a03707e474be41e07806ee4fd9791ca7cd) | MIT（enterprise/另有许可） |
| S15 | [comet-ml/opik](https://github.com/comet-ml/opik) | [657e3197dc46](https://github.com/comet-ml/opik/tree/657e3197dc460e6441471c832d93666c7fc730c8) | Apache-2.0 |

## 历史材料与当前状态

LangGraph当前归档Notebook指向历史SQL教程；本文实际读取的是[历史SQL教程](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/sql/sql-agent.md)，提交23961cff61a42b52525f3b20b4094d8d2fba1744。相应[历史许可](licenses/langgraph-historical.txt)单独保留。不能把历史create_react_agent示例当作当前安装指南。

AutoGen当前README标明维护模式，SWE-agent说明主要开发转向mini-swe-agent；OpenHands主仓库现为Agent Canvas，底层Agent Server属于其他项目；LlamaIndexREADME说明当前公司主要聚焦文档解析。以上状态只按该日该提交记录，不推断所有相关生态停止维护。

## 内容如何归因

本知识库独立编写中文解释、架构简图、业务改造与离线夹具。它们不是官方逐字翻译，也不代表项目方背书。每个案例末尾给出已读取的具体源码；应用知识卡的模块给出相关机制来源，字段设计、策略、验收办法为本文工程建议，不声称来源项目已经完整实现。

AutoGen文档采用CC-BY-4.0，作者Microsoft，本文对文档进行了中文概述与重组；原代码另按LICENSE-CODE采用MIT。其余许可按实际文本保留。LiteLLM根许可明确enterprise/另有许可；不能笼统认定仓库和所有商业功能均为MIT。云平台、模型权重、外部服务与数据文件还可能有独立条款。

## 本轮验证做了什么

- 核对15个仓库README与许可、十个案例的具体文档或代码路径，保留固定提交链接。
- 独立标准库脚本运行10项机制检查，涉及只读SQL、上下文转接、有界反馈、依赖、查询金标准、回归、事件去重、页面过期、证据夹具和检索范围。
- 检查文档结构、相对链接、来源URL路径、知识卡数量和唯一编号。

## 本轮没有验证什么

没有安装和运行这15个完整项目；没有调用外部模型、付费API、真实网站操作或业务生产数据；没有复现公开排行榜或证明生产成功率。离线检查仅验证教学机制，不是框架集成测试。项目演示或宣传不作为本知识库实测结论。正式部署应先固定环境，再评估业务问题集、成本和错误边界。

## 完整许可文本

- [langchain-ai/langgraph](licenses/langgraph.txt)
- [openai/openai-agents-python](licenses/openai-agents-python.txt)
- [microsoft/autogen](licenses/autogen.txt)
- [crewAIInc/crewAI](licenses/crewai.txt)
- [huggingface/smolagents](licenses/smolagents.txt)
- [SWE-agent/SWE-agent](licenses/swe-agent.txt)
- [OpenHands/OpenHands](licenses/openhands.txt)
- [browser-use/browser-use](licenses/browser-use.txt)
- [assafelovic/gpt-researcher](licenses/gpt-researcher.txt)
- [run-llama/llama_index](licenses/llama-index.txt)
- [fastapi/fastapi](licenses/fastapi.txt)
- [qdrant/qdrant](licenses/qdrant.txt)
- [docling-project/docling](licenses/docling.txt)
- [BerriAI/litellm](licenses/litellm.txt)
- [comet-ml/opik](licenses/opik.txt)
- [AutoGen代码许可](licenses/autogen-code.txt)

[返回案例目录](README.md)
