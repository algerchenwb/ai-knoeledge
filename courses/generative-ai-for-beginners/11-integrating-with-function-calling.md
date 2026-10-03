# 11 · 函数调用与外部 API

> 原课程解读与中文重写；「工程补充」为额外实践。核对日期：2026-10-03。

## 函数调用的一句话理解

模型提出“调用哪个函数、传什么参数”，应用真正执行函数，并把结果交回模型。它连接自然语言与 API，但模型输出的调用计划不是已经完成的操作。

原课用课程搜索 API 举例：用户描述角色、产品与学习程度，模型选择 search_courses，后端查询 Microsoft Learn 目录，再让模型组织结果。

## 标准闭环

1. 应用给模型提供工具名、用途与参数 schema。
2. 模型返回 function_call。
3. 应用检查工具是否存在、参数是否合法、用户是否有权限。
4. 应用调用后端工具并获得真实结果。
5. 按 call_id 将结果作为 function_call_output 回传。
6. 模型生成回应，或提出下一次调用。

不同 API 的消息格式不同。快照中的 Responses API 使用扁平工具结构，name、description、parameters 位于同一层；Chat Completions 的结构不能不加转换地复制过来。

## 工具契约为什么重要

~~~json
{
  "type": "function",
  "name": "query_region_population",
  "description": "查询一个已解析区域在指定月份、指定人口口径下的统计值",
  "parameters": {
    "type": "object",
    "properties": {
      "region_id": {"type": "string"},
      "month": {"type": "string", "description": "YYYY-MM"},
      "population_type": {
        "type": "string",
        "enum": ["resident", "worker", "visitor"]
      }
    },
    "required": ["region_id", "month", "population_type"],
    "additionalProperties": false
  }
}
~~~

这是通用契约示例。实际业务应使用自己的完整枚举，不从这个教学枚举推导真实人口定义。日期正则只能验证形状，还要检查月份范围、数据存在性和用户可访问范围。

## 原代码中的可改进点

Notebook 的工具 schema 只要求 role，但 search_courses 函数要求 role、product、level 三个位置参数。当模型省略未必填的字段时，直接解包会失败。解决方式是让 schema 与函数默认值保持一致，或要求三项都必填并在缺项时先澄清。

requests.get 没有显式超时、状态检查；直接 response.json()["modules"] 假设返回结构恒定。示例还只执行 tool_calls[0]，忽略其余调用。最终请求可能继续返回工具调用，不能假设一定只有自然语言答案。

这些是快照中可直接观察的实现边界，不表示所有服务上都必然触发同一种错误。

## 执行器的基本规则〔工程补充〕

~~~python
import json

def execute_call(call, registry, validate, authorize):
    if call.name not in registry:
        raise ValueError("unknown tool")
    args = json.loads(call.arguments)
    validate(call.name, args)
    authorize(call.name, args)
    result = registry[call.name](**args)
    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": json.dumps(result, ensure_ascii=False),
    }
~~~

这是执行器骨架；validate、authorize 需要业务实现。不要使用 eval 执行模型给出的函数名或代码。异常应转换成可识别的错误结果，不泄露 token、DSN 或内部堆栈。

## 权限、幂等与预算

权限由请求的可信用户身份确定，不能由模型传入的 tenant_id 决定。只读工具和写工具要分开；需要确认的副作用必须经过业务授权流程。重试写请求可能重复执行，用幂等键和操作状态解决。

为循环定义最大调用次数、整体超时和输出体积。多个独立查询可以并发，但依赖前一步结果的调用应按顺序执行；同一个写资源的并发必须遵守业务一致性要求。

## Function Calling 与 MCP

函数调用是模型输出工具选择的机制；MCP 是客户端与工具服务之间的协议。可以通过 MCP 暴露工具，再适配为模型可识别的工具定义。它们既不自动提供业务授权，也不保证工具调用一定正确。

## 练习

对同一个查询工具测试完整参数、缺月份、错误枚举、越权地区、未知工具和上游超时。正确率应分别统计工具选择与参数准确率，不能只看最终文字是否流畅。

## 代码来源

[原课 oai-assignment.ipynb](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/11-integrating-with-function-calling/python/oai-assignment.ipynb)。

## 来源与继续阅读

- [原课程正文](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/11-integrating-with-function-calling/README.md)
- [专题目录](README.md)
