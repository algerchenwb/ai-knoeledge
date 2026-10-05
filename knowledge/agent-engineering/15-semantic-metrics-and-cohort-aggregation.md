# 15. 业务 Agent 的指标语义：去重、关联与跨区域汇总

用户问：“这两片区域近90天到访过4S店的人群占比是多少？整体呢？”Agent 分别查到两个区域的占比，再平均一下，看似自然，却可能计算错误：两个区域人群有重叠，去重人数不能直接相加；两个区域规模不同，占比也不能简单平均。

本章从“解释一个指标”深入到“保证多次工具查询与汇总仍采用同一语义”。结合 MetricFlow 开源语义模型夹具，使用真实 SQLite SQL 和虚构事件验证。已有[区域触达案例](../business-ai-cases/01-area-category-coverage.md)介绍集合交集，本章补充关联扇出、非可加性、比例合并和上下文兼容检查。

## 1. 指标名称需要一份可执行的定义卡

“客流”“触达”“转化”只是名字，不能直接决定 SQL。教学口径把触达定义为：指定区域访客集合中，在同一窗口观察到目标三级业态到访的人群比例。它不表示广告曝光、联系成功或购买。

一份业务定义卡至少说明：

| 内容 | 本例约定 |
| --- | --- |
| 中文名与用途 | 目标业态到访覆盖率，用于描述已观察到的人群行为 |
| 分母 | 区域访客集合去重 person |
| 分子 | 分母人群中有目标业态到访记录的去重 person |
| 时间 | 同一个半开区间，日历日口径 |
| 空间与人群 | 明确区域选择及 visitor，人群类型不能混用 |
| 输出 | 分子、分母、占比、质量状态与上下文版本 |
| 排除项 | 空身份、窗口外记录、其他租户、分母外人群 |
| 正向规则 | 同一人员多次到访只计一人 |
| 负向规则 | 不把到访推断成购买意图，不平均局部比例得整体 |

技术实现可以使用内部实体、字段和维度；面向销售或用户只展示业务名称、口径和适用边界。中文命名帮助理解，受控 metric_id 帮助程序稳定定位。

## 2. 事件数、去重人数与订单数是不同量

区域 R1 有四条记录：u1、u1、u2、u3。事件数为4，去重人数为3。COUNT(*)、COUNT(person) 和 COUNT(DISTINCT person) 有不同含义，空值处理也不同。

MetricFlow 的固定测试模型将 bookings 定义为 expr=1、agg=sum，将 bookers 定义为 guest_id 的 count_distinct，将 average_booking_value 定义为 average。这个配置例子直接说明：选择聚合方式是指标定义的一部分。

它们是上游测试夹具，不是实际业务部署结果；本文也没有运行 MetricFlow 编译器。

## 3. 分子应从分母人群中筛选

本例先形成 cohort，再用 EXISTS 筛选是否有目标业态到访。这样分子天然属于分母集合，不会把区域外的 outside 用户算进来。

SQL 的逻辑骨架为：

~~~sql
WITH cohort AS (
  SELECT DISTINCT person
  FROM area_events
  WHERE tenant = ?
    AND day >= ? AND day < ?
    AND population = ?
    AND region IN (...)
    AND person IS NOT NULL
), reached AS (
  SELECT person
  FROM cohort c
  WHERE EXISTS (
    SELECT 1 FROM category_events v
    WHERE v.person = c.person
      AND v.tenant = ?
      AND v.day >= ? AND v.day < ?
      AND v.category = '4S'
  )
)
SELECT
  (SELECT COUNT(*) FROM reached) AS numerator,
  (SELECT COUNT(*) FROM cohort) AS denominator;
~~~

片段中的 region IN(...) 仅展示结构；脚本为每个区域生成绑定占位符，不拼接区域字符串。目标业态在脚本中固定为虚构分类 '4S'，未接入真实三级分类词表。

并非所有 ratio 都要求分子≤分母。例如订单数/下单人数是每人订单量，可能大于1。应按“覆盖率”或“强度”分别约束，不能给所有比例一刀切。

## 4. 关联扇出会悄悄改变计算粒度

u1 在区域有两条到访记录，在标签表有两个标签。直接 JOIN 后，u1 对应四条关联行；u2 和 u3 各一条，总行数从4变6。

只在最后 COUNT(DISTINCT person) 可以修复本例人数，但不一定修复金额 SUM：同一订单金额已被复制多次。SUM(DISTINCT amount) 也不是通用修复，因为两笔真实订单可能金额相同。

应先确认每张表一行代表什么、关联键是否唯一、关联是一对一还是一对多，再选择预聚合、半连接/EXISTS 或受控桥接。不要靠 SQL 能运行来判断关联正确。

## 5. 去重人数跨区域不能直接求和

虚构数据：

| 区域 | 去重访客集合 | 到访目标业态的人群 | 分子/分母 |
| --- | --- | --- | --- |
| R1 | {u1,u2,u3} | {u1} | 1/3 |
| R2 | {u1,u4,u5} | {u1,u4} | 2/3 |
| R1∪R2 | {u1,u2,u3,u4,u5} | {u1,u4} | 2/5 |

把局部分母相加得到6，分子相加得到3，再除得到50%；正确整体是40%。即使对局部比例按分母加权，也仍无法消除跨区域重叠。

因此服务应重新在合并区域上查询去重集合或采用可靠的等价汇总结构。Agent 只有两组聚合数字时，无法一般性地恢复重叠人数。应明确请求整体指标，或说明缺少合并去重结果。

## 6. 比例的平均，与总体比例回答不同问题

若两个群体**互不重叠**，第一组1/10，第二组45/90：

- 等权平均区域占比是 (10%+50%)/2=30%，回答“每个区域等权时的平均比例”。
- 合并人群占比是 (1+45)/(10+90)=46%，回答“所有人员中目标人群占多少”。

只有人群身份与范围可合并、分子分母口径一致、没有重叠时，计数加总再除才适合总体比例。如果重叠，就回到上一节重新去重。

模型生成摘要时必须说明“平均区域”还是“整体人群”，不能只输出模糊的“平均占比”。

## 7. 时间窗口要采用同一边界与粒度

脚本采用日历日期 [2026-07-03, 2026-10-01)，正好90天；包含7月3日，排除10月1日。分母和目标到访使用同一窗口。

它验证日期字符串和日历日边界，没有时分秒、时区转换或夏令时。真实“近90天”可能指90个业务日历日或滚动2160小时，需明确。端点“含今天”也要转成一致的查询边界。

两个结果分别使用统计月份、到访月份或数据加载日期时，即使都写“9月”，也不一定可比。MetricFlow 测试模型分别为部分度量设置 ds 与 paid_at，说明聚合时间字段也需要在定义中声明。

## 8. 指标语义与数据快照要一起绑定

每次工具结果应带 metric_definition_version、统计窗口、population_type 和 snapshot/data_version。比较前检查上下文一致；缓存键也应覆盖影响语义的字段。

脚本 Context 绑定 tenant、窗口、人群、definition 和 snapshot。assert_comparable 拒绝版本、窗口、人群或快照不同的结果。区域选择可不同，这是比较区域的目的；其他语义上下文必须一致。

但脚本中的 snapshot 只是标签，没有真正读取对应数据库快照；definition 也只是受控接口设计的示意，SQL没有按它动态换口径。传同一标签不能保证数据确实同批，必须由数据服务执行并证明这种绑定。

## 9. 零值、空分母和数据不完整应分开

| 状态 | 本例输出 | 可表达什么 |
| --- | --- | --- |
| 数据完整、分母大于0、分子0 | ratio=0，status=ok | 本例窗口内未观察到目标到访 |
| 数据完整、分母0 | ratio=null，status=no_denominator | 没有可计算的人群分母 |
| 数据不完整 | ratio=null，status=partial，保留观察计数 | 只有当前已观察到的部分结果 |

部分数据时，观察分子与分母都可能缺失，真实比例既可能更高也可能更低，不能自动称当前比例是下界。

complete 标记由调用者提供，脚本不评估覆盖率、延迟或数据成熟度。它验证缺失表达规则，不证明真实数据完整。业务上应由数据提供方返回可审计的成熟度，而不是模型猜测。

## 10. 开源语义层帮助组织口径，但不能替你决定业务

MetricFlow README 描述了从指标定义到数据流查询计划，再到不同引擎 SQL 的编译路径。固定夹具展示 simple、ratio、derived、cumulative 和 conversion 等不同指标类型。

bookings_per_booker 配置将 bookings 作为 numerator、bookers 作为 denominator；bookings_mom 用带时间偏移的基数和 NULLIF 防止除零。它们体现了复用基础度量、表达公式和时间语义的方式。

这些配置不能证明你的区域围栏正确、分类完整、访客身份可跨源匹配或归因合理。语义层仍需业务负责人审核口径、技术负责人验证数据和关联，Agent 才能在受控定义上解释。

## 11. Agent 应请求指标，再解释证据

推荐交互过程：识别业务对象与窗口；获取指标定义；服务端固定租户和权限；调用受控指标接口；检查版本、质量和分子分母；若要求整体，调用整体去重接口；输出带边界的结论。

回答可以写：“按本例访客口径，两区域合并后的5名去重访客中，2名有目标业态到访，占40%；分别为33.3%和66.7%。”不能写“40%准备购车”，也不应把区域级统计当个人行动依据。

纯展示层保留人数和比例，便于复算。若实际产品存在展示阈值或统计保护规则，应由既有数据治理策略决定，本文不编造通用阈值。

## 12. 验收应准备能暴露错误的微型数据

仅用每人一条记录、区域互不重叠的数据，错误 SQL 也容易通过。至少加入重复到访、区域重叠、域外目标访客、一对多标签、相同金额订单、窗口边界、空身份、其他租户、数据缺失和口径版本变化。

本例故意让错误关联得到6条行、错误局部计数合并得到50%，正确合并为40%。测试比较明确可手算结果，不只是比较两个采用同一算法的函数。

此外应验收 SQL 执行成本、真实结果和数据成熟度。15个教学检查不足以证明生产查询性能、指标体系完整性或 Agent 准确率。

## 固定开源来源与许可

核验于 **2026-10-05（北京时间）**。来源：[dbt-labs/metricflow](https://github.com/dbt-labs/metricflow)，固定提交 **a8d263d019010b0b4e227539c4ff356d15824dff**，提交时间 **2026-09-29T18:23:27Z**。

| 文件 | 已核验内容 |
| --- | --- |
| [README](https://github.com/dbt-labs/metricflow/blob/a8d263d019010b0b4e227539c4ff356d15824dff/README.md) | 语义层、查询计划与 SQL 编译定位 |
| [bookings_source.yaml](https://github.com/dbt-labs/metricflow/blob/a8d263d019010b0b4e227539c4ff356d15824dff/metricflow_semantics/test_helpers/semantic_manifest_yamls/simple_manifest/semantic_models/bookings_source.yaml) | sum、count_distinct、average、聚合时间与实体配置 |
| [metrics.yaml](https://github.com/dbt-labs/metricflow/blob/a8d263d019010b0b4e227539c4ff356d15824dff/metricflow_semantics/test_helpers/semantic_manifest_yamls/simple_manifest/metrics.yaml) | ratio 的分子分母、derived 公式、偏移与累计的测试配置 |
| [LICENSE](https://github.com/dbt-labs/metricflow/blob/a8d263d019010b0b4e227539c4ff356d15824dff/LICENSE) | 本提交 Apache-2.0 |

许可以固定 LICENSE 为准，README 图标仍出现历史 AGPL 字样；不能据此将所有版本归为同一许可。本文中文释义、SQL与业务夹具独立编写，未复制上游实现或部署配置；上游版权归原项目及其贡献者。本文没有运行 MetricFlow 或 dbt 项目，不声称上游已经实现区域业务。

## 已运行验证

[semantic_metric_checks.py](examples/semantic_metric_checks.py)，Python **3.12.14** + SQLite **3.53.1**，无第三方依赖。

~~~bash
python knowledge/agent-engineering/examples/semantic_metric_checks.py
~~~

15 项检查全部通过：局部与整体去重、不可加反例、互斥群体的比例平均差异、JOIN 扇出、重复目标到访、90天边界、租户/人群过滤、空分母/零值/部分数据、上下文比较守卫，以及绑定参数和窗口输入。

示例使用 SQLite 内存数据库和虚构身份，不访问真实人群数据。单机 SQL 实跑不等于 StarRocks/MySQL 方言、海量 distinct 性能或生产权限已验证。身份证明、分类历史、快照一致性、时区、成熟度检测、近似去重和统计保护未接入。Context 比较只是本地规则，不是服务端授权。

## 自测练习

1. 哪些条件下局部分子分母可以相加？区域有重叠时需要补充什么？
2. 把标签表 JOIN 到订单表，为什么 SUM(DISTINCT amount) 仍可能错误？
3. “平均区域占比30%”与“总体人群占比46%”分别适合回答什么问题？
4. 两次查询 snapshot 标签相同，就能保证一致性吗？服务需要怎样实现？

[返回专题目录](README.md)
