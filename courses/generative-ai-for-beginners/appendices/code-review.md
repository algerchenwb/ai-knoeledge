# 原课程代码审阅与修正指南

核对上游固定提交 d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8。本页仅对实际读取的代码给出观察，不把整个仓库概括为不可运行，也不声称已用所有平台在线验证。

## 第 06 课：文本生成

[源码](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/06-text-generation-apps/python/oai-app.py)使用 load_dotenv、OpenAI 和 responses.create，示例模型为 gpt-5-mini，输出 response.output_text。

需要注意：这是最小教学脚本，没有应用层请求预算、业务错误映射和输出校验。迁移到 Web 服务时先封装供应商客户端，再加入总超时与观测。不要将未验证的模型输出直接写入关键业务表。

## 第 11 课：函数调用

[Notebook](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/11-integrating-with-function-calling/python/oai-assignment.ipynb)。

| 直接观察 | 可能后果 | 修正方向 |
| --- | --- | --- |
| schema 只要求 role，函数要求 role/product/level | 省略后两项时解包失败 | 契约与默认值一致 |
| requests.get 未显式 timeout | 等待时间不可控 | 连接和读超时、整体预算 |
| 直接 json()["modules"] | 非成功或结构变化时报错 | raise_for_status 与结构验证 |
| 只处理 tool_calls[0] | 后续调用未执行 | 遍历或明确只允许单调用 |
| 最后一次响应可能仍为工具调用 | 最终文字为空或任务未完成 | 受预算限制的循环 |
| 返回 str(results) | 不是稳定 JSON 契约 | json.dumps 与结构化状态 |

模型返回的函数名不能动态 eval。注册表只是第一层，还需参数验证、授权和幂等。对于有依赖的多调用，必须按顺序执行。

## 第 15 课：RAG

[Notebook](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/15-rag-and-vector-databases/notebook-rag-vector-databases.ipynb)。

| 直接观察 | 影响 | 修正方向 |
| --- | --- | --- |
| 检索片段加入 history，但 messages 只用 history[-1] | 原文未进入模型请求 | 显式序列化 evidence |
| data_paths 带网站追踪参数 | 普通本地路径无法找到 | 使用真实文件路径 |
| split_text 按空白拆分 | 中文切分与长度控制不可靠 | 结构或 tokenizer 切分 |
| NearestNeighbors 未指定 cosine | 不应按余弦解释默认距离 | 显式设置度量并说明 |
| n_neighbors=5 固定 | 样本不足可能报错 | 按实际样本限制 k |
| 连接 Cosmos，但示例检索在本地 | 不能推断完成了数据库持久化 | 实际写入及查询验证 |
| 双层打印循环与 for/else | 重复输出，else 含义混淆 | 简化循环，显式条件 |
| 生成句与候选句完全相等后算 AP | 无法可靠评估同义答案及检索排名 | 以相关文档标签评检索，单独评生成 |

最关键的验证不是“答案像相关资料”，而是检查请求中确实有资料。模型预训练可能恰好知道答案，掩盖 RAG 请求组装错误。

## 正文中的概念也要谨慎读

RAG 并非限定 Encoder-Decoder；向量通常不是解码回文本，而是通过 ID 找原文；重复一次近邻搜索不是完整重排；建立 DataFrame 不等于真正实现混合检索。对模型家族的通用描述要以具体变体为准，不能推断整个品牌都用 MoE。

这些澄清在中文章节里已展开。来自原课程的说法可以作为学习起点，但真实实现要检查调用链和数据流。

## 已验证与未验证

- 离线示例使用 Python 标准库，验证检索证据传递、未知问题、工具参数与权限拒绝。
- 离线生成器是确定性测试替身，不是实际语言模型。
- 没有使用真实供应商密钥执行在线课程，因此不报告在线成功率、费用或延迟。
- 没有修改上游微软仓库；修正示例与说明保存在本知识库。

[返回目录](../README.md)
