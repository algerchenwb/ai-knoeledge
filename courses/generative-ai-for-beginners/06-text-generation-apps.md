# 06 · 文本生成应用

> 原课程解读与中文重写；「工程补充」为额外实践。核对日期：2026-10-03。

## 文本生成应用的最小闭环

输入 → 构造请求 → 模型生成 → 校验输出 → 展示。课程用故事续写、食谱、学习助手等案例演示。后端开发者可以把它理解为一条额外外部服务依赖，但这条依赖的输出带有不确定性。

## 结合实际代码阅读

原仓库 python/oai-app.py 加载 .env、构造 OpenAI 客户端，调用 client.responses.create，最后打印 response.output_text。快照中使用 gpt-5-mini；这是该示例的配置，不是本知识库的永久选型建议。

与常见旧教程相比，这份示例已经使用 Responses API。不要直接把其他教程的 Chat Completions 消息、tools 格式或旧 Completion 参数混进来。Azure、OpenAI 与其他兼容服务仍要依据各自端点校验。

## 可运行的最小改写

先按第 00 课建立虚拟环境并安装 openai、python-dotenv。设置 OPENAI_API_KEY 和 OPENAI_MODEL。以下沿用原仓库接口形态，模型名称由环境配置提供。

~~~python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(timeout=30.0, max_retries=2)
response = client.responses.create(
    model=os.environ["OPENAI_MODEL"],
    input="用三句话解释什么是语义搜索，面向 Go 后端开发者。",
    max_output_tokens=300,
    store=False,
)
print(response.output_text)
~~~

这是在线示例，本知识库未使用真实凭据执行。store=False 控制接口所述的响应存储选项，不代表消除了所有供应商日志或数据保留，实际数据政策仍要单独核查。

## 应用层必须补什么〔工程补充〕

- 输入长度限制：避免用户一次塞入无法处理的内容。
- 请求超时：不能无限等待上游。
- 重试边界：只对可重试错误处理，避免鉴权失败也不停重试。
- 输出验证：JSON 解析、字段类型和业务规则分别校验。
- 错误映射：区分无权限、上游超时、内容不可处理。
- 可观测性：记录耗时、token、版本和失败类别，敏感内容脱敏。

SDK 重试与业务层重试可能相乘。例如两个层各尝试三次，最坏可能产生九次请求。给一次业务任务定义整体超时、调用次数与费用预算。

## 为什么流式输出有用

流式传输让用户较早看到文字，但不代表完整任务更快。区分首个输出时间、完整响应时间与工具执行时间。流中断时，部分内容应标为未完成；JSON 和结构化结论不要在验证前提交到业务数据库。

## 食谱案例的工程意义

原课逐步添加食材限制、过滤与购物清单，展示同一模型怎样在约束下改变结果。类似业务应用应把限制变成结构化输入，而不是把所有选择拼成一段长句。例如过敏成分、禁止字段和输出数量可以在前后端共同校验。

## 练习

把生成结果从直接打印改成返回 text、request_id、elapsed_ms。用错误模型名、缺失密钥和过长输入观察失败分类。目标是构建可解释的接口行为，而不仅是成功生成一次文字。

## 代码来源

[原始 oai-app.py](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/06-text-generation-apps/python/oai-app.py)。

## 来源与继续阅读

- [原课程正文](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/06-text-generation-apps/README.md)
- [专题目录](README.md)
