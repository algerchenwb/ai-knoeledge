# 术语速查：把名词放回系统中

本页是课程概念与工程补充的导航。每个术语只给最关键的解释，深入机制见对应章节。不是供应商当前产品规格表。

## 模型与生成

| 术语 | 通俗解释 | 常见误解 |
| --- | --- | --- |
| AI | 让计算机完成通常需要智能的任务的领域 | 所有 AI 都是 LLM |
| 机器学习 | 从数据学习规律 | 完全不需要人工设计 |
| 深度学习 | 使用多层神经网络的方法 | 层数越多必然越好 |
| 生成式 AI | 根据学到的模式生成内容 | 生成就代表原创且准确 |
| LLM | 大规模语言模型 | 能直接查所有实时事实 |
| SLM | 相对紧凑的语言模型 | 必须由大模型压缩而来 |
| Foundation model | 可适配多类任务的预训练基础 | 只包括文本 |
| Token | Tokenizer 切出的文本单位 | 固定一个汉字 |
| Tokenizer | 文本和 token ID 之间的编码工具 | 各模型完全相同 |
| Embedding | 将内容映射成数值向量 | 向量能直接恢复原文 |
| Parameter | 模型训练调整的数值 | 参数量等于业务质量 |
| Transformer | 基于注意力的架构类别 | 唯一的生成模型架构 |
| Attention | 根据上下文计算位置关联 | 等同人类注意力 |
| Autoregressive | 依次生成 token | 仅做简单词频匹配 |
| Context window | 单次处理的 token 容量 | 永久记忆容量 |
| Temperature | 在支持时调节采样分布 | 智商或事实准确度开关 |
| Top-p | 按累计概率选择采样候选范围 | 与所有模型都兼容 |
| Hallucination | 看似合理但错误或无依据内容 | 只指凭空捏造名词 |
| Multimodal | 支持多种输入或输出模态 | 所有模态都同时支持 |
| Dense | 主体网络通常整体参与计算 | 大参数量必然慢 |
| MoE | 通过路由选择部分专家计算 | 未激活专家完全不占资源 |

详见 [01 模型原理](../01-introduction-to-genai.md)、[02 选型](../02-exploring-and-comparing-different-llms.md)、[19 小模型](../19-slm.md)。

## 提示与知识

| 术语 | 通俗解释 | 常见误解 |
| --- | --- | --- |
| Prompt | 模型收到的任务与上下文 | 只有用户那一句话 |
| System message | 定义行为的较高层说明 | 能替代业务鉴权 |
| Metaprompt | 约束生成行为的上层提示 | 唯一通用标准格式 |
| Zero-shot | 不给任务示例直接请求 | 不需要规则 |
| Few-shot | 给少量输入输出示例 | 示例越多越好 |
| Task decomposition | 把任务拆成可验证步骤 | 拆解自然会答对 |
| Self-refine | 先评估再修改输出 | 自我确认等于证据 |
| Grounding | 将结论约束到证据与来源 | 放入资料就不会幻觉 |
| RAG | 检索资料后用于生成 | 有向量库就已实现 |
| Chunk | 可检索的内容片段 | 固定长度永远最优 |
| Overlap | 切分片段保留重复上下文 | 越多越不丢信息 |
| Vector index | 支持向量近邻检索的结构 | 自动具有完整数据库能力 |
| Cosine similarity | 比较向量方向 | 正确答案概率 |
| ANN | 近似最近邻检索 | 保证找到精确最近项 |
| Hybrid search | 结合关键词与向量等检索 | 两路分数可直接相加 |
| Reranker | 再评价候选相关性并排序 | 重复一次原检索 |
| Top-k | 返回前 k 个候选 | 候选都足够相关 |

详见 [04 提示词](../04-prompt-engineering-fundamentals.md)、[08 搜索](../08-building-search-applications.md)、[15 RAG](../15-rag-and-vector-databases.md)。

## 工具与工程

| 术语 | 通俗解释 | 常见误解 |
| --- | --- | --- |
| Function calling | 模型提出工具与参数 | 模型已执行函数 |
| Tool schema | 工具的结构化输入契约 | 保证业务值正确 |
| JSON Schema | 描述 JSON 字段与类型的规范 | 所有服务支持全规范 |
| Structured output | 约束生成结果的结构 | 自动校验事实 |
| MCP | 客户端与工具服务交互协议 | 自动提供业务权限 |
| Agent | 依据状态和工具推进任务的系统 | 只是拟人化提示词 |
| Workflow | 预先定义步骤和分支 | 不能使用模型 |
| State | 已知条件、执行结果与任务进度 | 只有聊天历史 |
| Idempotency | 重复请求不会重复产生同一效果 | 重试天然安全 |
| Tenant isolation | 不同租户的数据与权限隔离 | UI 隐藏就足够 |
| Prompt injection | 不可信内容诱导改变系统行为 | 只来自用户输入 |
| Data poisoning | 污染训练或知识数据 | 只影响训练系统 |
| Trace | 一次任务中各阶段的关联记录 | 一条最终日志就够 |
| LLMOps | 维护模型应用的质量与运行 | 只监控模型 API |
| P95 latency | 95% 请求不超过的耗时分位 | 平均耗时 |
| Abstention | 证据不足时明确不下结论 | 应永远拒绝困难问题 |

详见 [11 函数调用](../11-integrating-with-function-calling.md)、[13 安全](../13-securing-ai-applications.md)、[14 生命周期](../14-the-generative-ai-application-lifecycle.md)、[17 Agent](../17-ai-agents.md)。

## 微调与评估

| 术语 | 通俗解释 | 常见误解 |
| --- | --- | --- |
| SFT | 学输入与期望输出样本 | 等同注入全部实时知识 |
| DPO | 用偏好对优化回答倾向 | 不需要高质量标注 |
| LoRA | 用低秩适配训练少量参数 | 与 SFT 互斥 |
| Quantization | 降低数值表示精度 | 一定不损失质量 |
| Distillation | 让学生模型学习教师行为 | 与量化相同 |
| Epoch | 训练数据使用轮次 | 越大越好 |
| Learning rate | 参数更新的步长尺度 | 提高就训练得更好 |
| Overfitting | 训练样本好，未见数据差 | 训练损失低就不存在 |
| Data leakage | 测试信息进入训练或调参 | 只有完全重复才泄漏 |
| Recall@k | 前 k 项覆盖多少已标注相关资料 | 回答流畅度 |
| MRR | 第一条相关结果倒数排名的平均 | 多个相关项覆盖率 |
| nDCG | 带相关等级和位置权重的排名指标 | 任意分数都可当标签 |
| Groundedness | 回答是否由提供证据支持 | 有引用就一定正确 |
| Model judge | 用模型按规则评分 | 无偏差的终审者 |

[返回目录](../README.md)
