# 业务结果缓存与失效：让命中结果仍然可信

区域分析、共访排行或画像查询常有重复读取。缓存可以减少重复计算，但也会把过期口径、旧权限或旧数据放大。应先明确“什么情况下两个请求可以复用”，再决定用内存、Redis或其他存储。

本篇接续[批量查询去重](13-batch-business-query.md)，把请求内复用扩展到顺序跨请求结果缓存。示例复用[HTTP业务夹具](11-api-agent-http-integration.md)，只用标准库；没有运行真实HTTP、模型、Redis、数据库或cachetools库。缓存类及业务规则由知识库独立编写，开源源码仅提供TTL/LRU机制依据。

## 1. 三种复用的生命周期不同

| 类型 | 生命周期 | 保存什么 | 本库位置 |
|---|---|---|---|
| 单请求依赖复用 | 一次HTTP请求 | 共享依赖返回值 | FastAPI文档依据 |
| 批次查询去重 | 一次run_batch调用 | 同参数Future结果 | 批量教程 |
| 业务结果缓存 | 当前缓存实例，跨顺序调用 | 经许可复用的业务汇总 | 本篇 |

FastAPI子依赖文档说明，同一请求内的共享依赖可以只执行一次，use_cache=False可以关闭该复用。这不等于跨请求缓存，也不自动保证多租户结果隔离。本例第三种复用需要另外实现身份、版本和失效协议。

## 2. 哪些结果可以缓存

本例只缓存status=ok的只读计算。合法0比例也属于ok，允许缓存；空分母no_denominator和未成熟provisional都绕过缓存。异常不缓存，没有负缓存或重试。

这不是说所有空数据永远不能缓存。真实产品可以对权威确认的空结果设短TTL，但必须区别“确定没有数据”和“数据源没有返回”。不能将401、403或数据源失败缓存为0人，更不能缓存工单创建或正式报价动作来假装实现幂等。

缓存中保存业务结果，不保存token、request_id或自然语言会话。模型解释与数据结果可以采用不同复用策略；本例没有答案语义缓存。

## 3. 有效参数比原始JSON更适合作为键

CachedBusiness.query先调用parse_query，再使用Query所有字段构造键：intent、region_id、population_type、start、end_exclusive、metric_version、competitor_id、max_tool_calls。

未写max_tool_calls与显式2会规范化为同一有效值，从而命中；预算1与预算2必须分开。不同窗口、人群或竞品也不能仅因region_id相同而合并。未知字段和非法输入仍在查缓存前拒绝。

真实项目需补时区、单位、分页范围、数据协议和所有影响结果的参数。只把原问题文本做哈希，既难解释，也不能证明业务查询等价。

## 4. 身份与权限版本进入键，授权仍先检查

键还包含Principal.tenant、排序后的授权区域范围和permission_revision。Principal与权限版本来自可信服务端上下文，不接受模型或query选择。

每次读取缓存前检查当前区域权限；共访还检查当前竞品范围。即使已有命中记录，区域或竞品权限撤销后也必须拒绝。缓存不是授权凭证，不能为了提高命中率把授权步骤跳过。

本例Principal是公开夹具，不验证JWT或OAuth。permission_revision默认为fixture-policy-v1，生产中必须绑定真实权限系统的版本与作用范围。全量区域列表入键仅适用于小型示例；正式项目可使用稳定的范围指纹，但仍需覆盖实际结果可见性。

## 5. 数据版本与集合定义版本同时绑定

缓存键保存当前快照的data_version、definition_version、窗口、人群、mature和available。数据版本变化使旧键不再被读取；定义版本变化则重新进入业务检查，不能拿旧结果回答新口径。

测试把区域快照升级为synthetic-r2，并把业态到访集合改为1人，结果由50%变为25%，cache.status=miss。集合定义改为不支持版本时，返回DATA_DEFINITION_MISMATCH，旧结果不会替代检查。

关键前提是版本可信且不可变。若数据改变却保持同一data_version，本例可能返回旧结果；TTL只能缩短旧结果存活时间，不能修复错误版本协议。正式数据生产链路需要确保快照内容与版本绑定，并在读取元数据和计算期间保持一致视图。

## 6. 多数据源结果必须覆盖所有依赖

共访依赖区域与竞品两侧集合，只绑定区域版本不够。竞品变化也必须失效。

夹具没有竞品版本服务，所以本例每次读取授权竞品集合，将排序去重后的集合计算SHA-256并加入键。测试将竞品集合改为u1，命中失效，共访区域方向变为25%。

这种全集合哈希仅供小数据教学：真实用户集合可能很大，逐次读取和哈希会抵消缓存收益，还涉及数据访问范围。正式适配器应提供可信的竞品快照版本或依赖清单，不把原始用户集合交给模型。哈希不是匿名化或权限保护的替代方案。

## 7. 元数据检查也有成本

本例每次查缓存都读取当前字典快照和竞品授权状态，命中减少的是DemoService.execute计算，不减少全部读取。executions统计执行尝试，不代表数据库QPS或实际网络请求数。

生产可用轻量元数据接口判断版本，但若元数据本身也被缓存，就需要明确其TTL、权限更新传播和一致性边界。不能用一层过期缓存去证明另一层缓存“绝对新鲜”。本篇未实现真实版本接口、事件广播或分布式失效。

## 8. TTL使用单调时间，边界明确

ResultCache默认TTL为5秒，仅为教学参数。创建时间加TTL达到边界即过期，读取会先清除过期项。命中不会延长创建时间，没有滑动续期。

默认timer为time.monotonic，避免系统时钟调整影响进程内存活时长。测试注入可控时钟，不等待真实五秒：

| 逻辑时间 | 行为 | 缓存状态 |
|---|---|---|
| 0秒 | 首次计算50% | miss |
| 2秒 | 相同可信上下文读取 | hit，age_seconds=2 |
| 5秒 | 正好TTL边界，再次计算 | miss |

三个调用只执行两次计算。这个结果不是延迟压测，更不证明生产TTL应该设置5秒。业务需根据数据更新节奏、允许陈旧程度和成本确定TTL。

## 9. 过期不可读与内存回收不同

本例get和put会调用expire，清理过期记录；没有后台定时清理。长期不再访问的缓存实例，过期值可能仍占内存，直到下一次操作或clear。

cachetools固定源码的TTLCache也区分过期判断与expire清理，并提供受容量限制的LRU淘汰机制。阅读源码不能直接推断它已为项目配置线程锁、业务权限或分布式更新。

本例容量默认10条、允许1至1000条，LRU读取更新顺序，超限淘汰最久未用条目。容量按条数而非字节计算；一条巨大JSON仍可能造成内存压力。正式服务应结合结果体积、序列化和总内存预算设置约束。

## 10. 返回副本并区分原始计算trace

保存与读取都deepcopy，调用者修改某行ratio不会改变缓存里的结果。这避免可变对象跨请求污染；并不授权客户端随意修改业务事实。

命中返回cache.status=hit及age_seconds，business.trace仍是生成缓存值时的步骤，所以trace_scope标为origin_calculation。miss或bypass标为current_calculation。不能把命中后的旧步骤当成本次实际执行了两次工具。

正式观测应创建当前请求自己的cache_lookup span，再关联原始结果来源与版本。不要缓存整个HTTP响应中的request_id、耗时或当前授权信息。本例没有持久trace和跨请求关联ID。

## 11. 故障时是否返回旧结果是产品策略

本例当前数据源available=False时直接UPSTREAM_UNAVAILABLE，即使旧缓存未过期也不返回。未实现stale-if-error或stale-while-revalidate。

如果业务允许旧结果降级，应显式标记stale、原数据日期、年龄、可用范围和原因，不允许把旧结果伪装为刚取到的新数据。授权撤销、口径不兼容及部分高风险决策不能简单套用旧值。不同场景由业务方决定，不把“有缓存”当通用降级理由。

## 12. 线程安全与缓存击穿要另外实现

ResultCache与CachedBusiness为单进程顺序教学实现，没有锁。不能直接把同一实例接到多线程HTTP服务。

同时到来的相同请求可能都未命中并重复计算。缓存值保护、请求合并single-flight、全局并发上限与分布式锁是不同机制；线程池限制数量也不会自动合并相同请求。本篇没有实现它们，更没有验证多实例一致性、崩溃恢复或Redis锁。

旧版本键会保留到TTL或容量淘汰，不存在版本事件立即删除。若正式系统收到更新事件，应确认事件范围、顺序和重复处理，避免先删旧键后又由并发旧计算写回陈旧值。

## 13. 如何运行与验收

仓库根目录运行，Python3.10及以上、标准库即可，依赖api_agent_demo.py：

```bash
python knowledge/business-ai-cases/examples/business_cache_demo.py
python knowledge/business-ai-cases/examples/test_business_cache_demo.py
```

2026-10-05在Python3.12.14运行14项检查全部通过，第二条写入[结果记录](examples/business-cache-results.json)。覆盖TTL边界、默认参数等价、区域与竞品数据失效、定义版本、权限撤销、非ok绕过、故障不返回旧值、结果副本和LRU容量。

只验证顺序夹具与可控时钟，不验证真实缓存服务、模型、HTTP、数据更新竞态、并发、内存压力、网络deadline或线上收益。正式验收至少分开测结果正确、权限边界、陈旧比例、计算节省和总体延迟，不能只展示命中率。

## 14. 固定开源来源与许可

2026-10-05读取：
- [cachetools TTL/LRU源码](https://github.com/tkem/cachetools/blob/3c082c654c2804b9354e4b62dbd2994f1aac464d/src/cachetools/__init__.py)：TTLCache使用单调时间、过期判断、expire及容量淘汰；MIT，[完整许可](examples/cachetools-LICENSE.txt)随本篇保留。
- [FastAPI子依赖与请求内复用](https://github.com/fastapi/fastapi/blob/5f9fc5c59a9bb54608aa35376715f3ba9708188e/docs/en/docs/tutorial/dependencies/sub-dependencies.md)：仅支持单请求依赖复用的说明；MIT，[许可](../agent-case-studies/licenses/fastapi.txt)已保留。

本文没有复制上游实现，也未安装运行cachetools/FastAPI；业务键、权限与版本策略独立设计。[机器可读来源](examples/business-cache-sources.json)记录提交与验证范围。

[缓存源码](examples/business_cache_demo.py) · [检查源码](examples/test_business_cache_demo.py) · [返回业务目录](README.md)

