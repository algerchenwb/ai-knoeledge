# 离线示例：验证证据传递与工具边界

本示例是工程补充，无需 API Key，不访问网络，只使用 Python 3.10+ 标准库。所有数据与结果均为虚构。

## 运行

在仓库根目录：

~~~bash
cd courses/generative-ai-for-beginners/examples
python3 offline_demo.py
python3 -m unittest -v test_offline_demo.py
~~~

Windows 可在对应目录使用 python 替代 python3。

## 包含什么

- [offline_demo.py](offline_demo.py)：词面检索、显式证据 payload、确定性生成替身，以及参数与权限检查后的工具执行。
- [test_offline_demo.py](test_offline_demo.py)：12 个测试，覆盖证据未丢失、无资料、未知工具、非法参数与越权。

检索使用英文词与中文二元字符组的 Jaccard 相似度，是刻意简单的词面基线。它没有调用 Embedding，也没有验证真实语义召回。

fake_generator 只读取发送的 evidence，直接返回其中一段原文，是测试替身；它不是语言模型，不展示真正生成、幻觉、上下文攻击或 RAG 质量。没有资料时返回无法确认。

## 为什么这个示例有价值

原课程第 15 课中，检索与模型请求之间出现了证据丢失。本示例将检索结果和最终 payload 分开，测试明确检查文本与来源进入 input。再删除 evidence，检查结果发生变化。这样能检测“检索了，但请求没用”的链路回归。

工具身份从 Principal 取得，模型传入 tenant_id 会被拒绝。region_id 也必须位于可信身份的允许范围。真实服务仍需在数据库和下游 API 独立实施授权，不能只依赖外层检查。

## 已验证范围

2026-10-03 在当前环境执行：12 个测试全部通过。测试没有证明真实模型能准确选工具，也没有测在线限流、延迟或模型服务兼容性。

## 深化笔记的独立检查

以下脚本可从仓库根目录独立运行：

```bash
python courses/generative-ai-for-beginners/examples/deep_dive_search_tool_checks.py -v
python courses/generative-ai-for-beginners/examples/deep_dive_rag_evidence_checks.py -v
python courses/generative-ai-for-beginners/examples/deep_dive_model_memory_checks.py
```

- [检索与工具检查](deep_dive_search_tool_checks.py)：第08与11课示例，10项检查，验证余弦计算、参数契约与权限边界。
- [RAG证据组装检查](deep_dive_rag_evidence_checks.py)：第15课示例，12项检查，验证原文与来源进入消息、授权过滤、去重、字符预算及无证据状态。

- [模型内存估算检查](deep_dive_model_memory_checks.py)：第19课示例，12项检查，验证原始权重与普通KV缓存公式、单位和非法参数；不代表实际设备可运行模型。

三份独立脚本均已在2026-10-04执行通过。它们和原离线示例一样使用教学数据，不调用在线模型，不能作为在线模型质量或安全保证。

## 完整离线回归

2026-10-04重新读取远端代码，四份测试模块共46项检查全部通过：

```bash
python -m unittest -v test_offline_demo deep_dive_search_tool_checks deep_dive_rag_evidence_checks deep_dive_model_memory_checks
```

在本目录中运行。该结果覆盖离线教学逻辑，不包含真实模型或云服务集成。

## 扩展方向

用真正的 Embedding 替换词面检索，保留 payload 测试；用在线模型替换 fake_generator，增加引用准确度与证据支持评估；用真实受控 API 替换 demo_query，增加超时、错误契约与幂等。每替换一层，就增加对应的集成验证。

[返回 RAG 章节](../15-rag-and-vector-databases.md) · [返回专题目录](../README.md)
