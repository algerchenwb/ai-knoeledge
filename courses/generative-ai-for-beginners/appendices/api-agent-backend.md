# API Agent 后端实践：从问题到可信结果

本页是工程补充，结合课程的 04、07、11、13、14、15、17 课。例子均为虚构，不包含真实公司接口或数据。目标是让 Go 后端开发者看清模型之外的责任。

## 一个完整例子

用户：“比较甲商场与乙商场 2026 年 9 月客流，并说明哪个更适合开店。”

这个问题混合了查询、比较与推荐。先解析商场实体、月份、客流口径；查询真实数据；用代码比较；解释数据。若“适合开店”需要租金、竞品和业态但资料缺失，应说明无法仅凭客流做完整推荐。

## 责任分配

| 层次 | 负责 | 不应把什么交给模型 |
| --- | --- | --- |
| 路由 / Handler | 身份、输入体积、request_id | 用户和租户身份 |
| 应用 Service | 状态、预算、工具循环、错误恢复 | 是否越权 |
| 能力检索 | 找到合适接口与定义 | 无条件暴露全部工具 |
| 工具适配层 | schema、权限、参数、结果格式 | 任意 URL 或 SQL |
| DAO / Data | 参数化查询、范围限制 | 拼接生成 SQL |
| 确定性计算 | 汇总、分子分母、单位 | 自由编百分比 |
| 模型解释 | 组织证据、说明局限 | 将推测说成事实 |

## 80 个接口怎样提供给模型

先建立能力目录：中文用途、适用对象、输入输出、口径、限制与错误类型。根据任务检索少量候选再给模型选择，避免一次塞满所有工具。但候选剪枝可能漏工具，需测试召回和回退机制。

检索工具描述与业务数据是两个不同问题。前者决定“有什么能力”，后者决定“答案的事实是什么”。混合成一个无结构文本库会增加错误路由。

接口描述应包含正向与不适用条件。例如“月度客流趋势，不能提供个人轨迹”。同名指标的日期类型、去重规则与人群口径要明确。

## 实体解析

用户名称 → 候选实体 → 唯一 ID → 必要时澄清。不要把用户说的名字直接当数据库主键。候选有同名商场时，利用城市、行政区和位置缩小范围；仍无法唯一确定才询问。

坐标必须带坐标系；日期转换必须带当前日期和业务时区。业务实体变更时，使依赖旧实体的工具结果失效。

## 状态的结构

~~~json
{
  "task_id": "task-demo",
  "status": "querying",
  "params": {
    "region_ids": ["region-a", "region-b"],
    "month": "2026-09",
    "population_type": "visitor"
  },
  "evidence_ids": [],
  "remaining_tool_calls": 4,
  "missing_fields": ["store_category"]
}
~~~

可信身份不放在由模型自由覆盖的 params 里。状态变更按明确事件处理：参数更新、工具成功、工具失败、预算耗尽、用户取消。

## Go 工具接口形态

~~~go
type Principal struct {
    UserID   string
    TenantID string
}

type ToolResult struct {
    Status   string          // ok / no_data / error
    Data     json.RawMessage
    SourceID string
    Version  string
}

type Tool interface {
    Name() string
    Validate(args json.RawMessage) error
    Authorize(ctx context.Context, p Principal, args json.RawMessage) error
    Execute(ctx context.Context, p Principal, args json.RawMessage) (ToolResult, error)
}
~~~

这是接口设计片段，不是完整可编译工程；需要导入 context 和 encoding/json，并实现具体工具。context 传递整体超时和取消信号，Execute 仍必须在数据层使用可信身份限制查询。

## 数据查询与计算

模型只提供白名单参数，不提供任意 SQL。DAO 使用参数绑定、月份与地区范围检查、行数上限及超时。精确标识走精确匹配，不能随意模糊 ID。

增长率 = (本期 - 基期) / 基期。基期为零时应单独定义展示规则，不能直接除以零。比率必须区分分子和分母的时间、地区、人群与去重口径；有一项不同就可能无法比较。

聚合人群数也不能简单相加所有网格：若各网格统计同一用户的到访，可能重复。是否可相加取决于数据定义，模型不能自行决定。

## 缓存与幂等

缓存键包括权限范围、实体、月份、口径、指标版本和数据版本。两个租户相同问题不能无条件共享缓存。数据更新后，需要失效或版本切换。

只读查询通常可有限重试；写任务必须有业务幂等键。保存执行状态和返回的操作 ID，超时后先查状态，不应立即重复发起副作用。

## 错误反馈

区分 invalid_argument、unauthorized、no_data、upstream_timeout、budget_exhausted。工具返回 error 时禁止模型把它总结成零值。将可展示的错误与内部诊断分开；保留 request_id 供追踪。

## 验收案例

正确实体和月份；同名实体；缺少口径；相对时间；API 无数据；超时；返回格式变化；未知工具；越权；重复调用；前后轮参数更改。用固定资料比较模型选路与真实后端执行，不只检查生成文本。

本知识库的[离线示例](../examples/README.md)展示证据组装和工具执行边界；不模拟整个生产 Agent。

[返回目录](../README.md)
