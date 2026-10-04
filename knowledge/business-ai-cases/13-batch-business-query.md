# 批量业务查询：结果对应、请求去重、并发上限与部分失败

用户让Agent比较多个区域，或者后台需要预热一批地点画像时，不能只把单对象接口放进循环。需要回答：哪个结果属于哪个输入、重复对象是否重复取数、某一项失败会不会丢掉其他项，以及一次任务能给下游施加多少压力。

本篇扩展[批量查询映射知识点015](../ai-application-playbook/02-tools-and-api-integration.md)，复用[HTTP业务示例](11-api-agent-http-integration.md)的两个只读计算适配器。标准库脚本实际运行线程池，但只查询公开虚构夹具，不调用模型、HTTP服务或生产数据库。FastAPI开源文档提供嵌套列表输入契约的依据；去重、权限、调度和业务状态规则为本文独立设计。

## 1. 输入项ID与业务对象ID分别保存

假设用户提交六项：两次查询同一区域，然后查空数据区域、未成熟区域、不可用区域和另一租户区域。业务对象ID可以重复，输入项ID必须唯一。这样才能既复用查询，又保留每个输入位置的独立回执。

```json
[
  {
    "item_id": "request-item-1",
    "query": {
      "intent": "category_coverage",
      "region_id": "area-alpha",
      "population_type": 4,
      "start": "2026-09-01",
      "end_exclusive": "2026-10-01",
      "metric_version": "coverage-v1"
    }
  }
]
```

item_id是调用者给本次输入项的关联标识，不是数据库主键、用户身份、全局幂等键或权限证明。示例要求1至40字符、批内唯一。重复region_id允许；重复item_id拒绝整个批次，因为响应无法可靠对应。

正式跨服务任务可进一步增加batch_id、run_id和attempt，但这些字段不是本例已经实现的能力。不要把重试次数编码进对象ID，导致同一对象被当作新对象处理。

## 2. 契约先定义整批错误与单项错误

本例分两层验证：

| 层次 | 例子 | 行为 |
|---|---|---|
| 批次外壳 | 非列表、空列表、超过20项、并发配置非法 | 整批拒绝，无业务执行 |
| 项结构 | 缺item_id/query、未知顶层字段、重复项ID | 整批拒绝，无业务执行 |
| 查询内容 | 人群类型为布尔值、缺必填字段、非法日期 | 该项error，其他项继续 |
| 对象权限 | 区域不在当前Principal范围 | 该项error，不提交执行 |
| 业务数据 | 快照窗口不匹配、源不可用 | 执行后该项error，其他项继续 |

先遍历检查全部外壳，再开始任何执行，避免已经处理前十项才发现第十一项ID重复。单项查询错误则独立保存，不把有效输入全部丢弃。

这些是产品协议选择。付款、库存修改或正式报价的批次可能需要不同的事务与审核规则，不能直接套用本篇只读查询的“部分继续”。本例也不执行写操作。

## 3. 结果靠关联键对应，显示顺序只是便利

并发查询先完成哪一项不可预测。实现用as_completed接收Future，Future对应一组item_id，结果存入按ID索引的rows，再按原输入顺序组装返回。

返回顺序固定方便前端展示，但调用者仍应按item_id关联。若将来协议允许分页、乱序或流式返回，依靠数组位置的客户端就会失效。测试使用Event让第二个区域先完成，确认完成顺序改变后，返回ID和业务状态仍对应正确。

不要用zip(inputs, completed_results)：两个列表长度相同也不能证明对象对应。后端若省略某个失败对象，应生成明确missing/error项；不能把下一项结果补到它的位置。本例对每个合法输入项都返回一行。

## 4. 去重键包含全部有效查询条件

同一region_id可能对应不同月份、人群、指标或竞品。只用对象ID作为键，会把“本月客流”与“上月居住人群”错误合并。

本例先用parse_query规范化输入，再把以下内容稳定序列化：Principal.tenant、排序后的授权区域范围，以及Query所有字段：intent、region_id、population_type、start、end_exclusive、metric_version、competitor_id、max_tool_calls。

默认max_tool_calls=2与显式写2会合并，因为有效参数相同。预算1与预算2不能合并：预算1在第二次工具调用前失败，预算2正常完成。日期合法但不同也不能合并，其中不匹配夹具范围的查询必须独立返回DATA_SCOPE_MISMATCH。

此处键在内存中用于当前请求分组，不写日志、不含token、不作为全局缓存键。正式共享缓存还需覆盖权限策略、数据版本、集合定义版本、成熟度、时区、查询协议及失效条件；本文没有实现这些缓存机制。

## 5. 能复用计算，不等于能复用授权

Principal来自服务端可信上下文，不能接受每项query里的tenant_id。进入分组前检查区域权限，底层DemoService执行时还会再次检查区域及竞品范围。未知字段也由parse_query拒绝。

两个无权限查询不会因为相互重复而获得查询机会。示例对area-beta的两个越权输入都保存错误，executed_unique_queries为0。能力权限、区域权限、竞品权限仍应按各自协议检查，去重不替代其中任何一层。

本函数只处理同一Principal的一批请求，没有多租户混合批次。另一次请求重新计算，没有跨请求缓存；测试另外用tenant-b验证其area-beta返回合法0比例。本轮没有验证真实权限系统、权限热更新或跨租户共享缓存。

## 6. 去重后的结果也要复制

重复输入共用一个Future，但每个item_id获得deepcopy的结果。这样前端适配或后续处理修改某一行的嵌套result，不会悄悄修改另一行。

测试给第一行ratio写入99，第二行仍为0.5。这里检验的是响应对象独立性，不是在允许客户端修改正式业务结果。生产协议应把结果视为事实记录，额外展示字段另存。

对大对象逐项deepcopy可能昂贵，可以采用不可变结果或按artifact_id共享，但仍需明确所有权。不要为了省复制而让多个任务共享可变结果对象。本例数据很小，没有测试大JSON的内存成本。

## 7. 并发上限与批次上限分别控制

本例批次最多20项，max_workers为严格整数1至4，默认2。去重后唯一查询提交ThreadPoolExecutor；最多max_workers个service.execute同时运行。

两项限制不同：并发控制同时占用资源的数量，批次上限控制提交与结果规模。仅限制线程数而接受百万输入，排队内存和总耗时仍可能失控。ThreadPoolExecutor本身并不替本例提供全局有界队列；这里靠批次最多20项限制单次提交规模。

本例没有进程级或多实例级并发限额。十个并发请求各开两个线程，仍可能同时产生二十次执行。真实系统应共享资源池，并按租户、下游依赖和查询成本设置限额；不能把max_workers误读为系统整体QPS。

测试用Event阻塞执行，确认两个worker同时进入，第三个等待，并记录peak=2。它证明本地线程调度边界，不证明真实数据库连接数、接口吞吐或延迟SLA。

## 8. 分项预算与总体截止时间不能混为一谈

Query的max_tool_calls仍对每个唯一查询有效；重复输入复用一次查询预算。本例没有整批统一工具预算，只通过最多20项和每项1至3次调用限制教学规模。executed_unique_queries统计service.execute尝试次数，不统计内部工具步骤，也不是数据库实际请求数。

线程池并不实现业务deadline。本例适配器是立即完成的内存计算；如果换成会无限阻塞的网络调用，整个批次仍可能一直等，退出线程池时也会等待执行结束。Future取消通常不能强制终止已经运行的线程。

正式接口应让各下游客户端接收剩余截止时间并支持取消，确定已超时任务是否继续占资源。不要给每项各30秒再声称整批30秒内完成。本例没有实现超时、取消或网络故障注入，这些不是13项检查证明的能力。

## 9. 传输错误、业务状态与批次摘要分别看

正常查询是ok，空分母是no_denominator，数据未成熟是provisional，异常是error。本例把这些状态保存在每项，顶层仅在所有项ok时为ok，否则为partial；因此即使全部失败，顶层也为partial，并可由counts.error==submitted_items识别。正式产品可以另设failed状态，但要形成清晰协议。

示例六项返回：

| item_id | 对象 | 状态 | 关键内容 |
|---|---|---|---|
| item-1 | area-alpha | ok | 2/4=50% |
| item-2 | area-alpha | ok | 复用同一查询，独立结果对象 |
| item-3 | area-empty | no_denominator | 比例null |
| item-4 | area-provisional | provisional | 暂不输出正式比例 |
| item-5 | area-unavailable | error | UPSTREAM_UNAVAILABLE |
| item-6 | area-beta | error | OBJECT_FORBIDDEN |

submitted_items=6，executed_unique_queries=4：两次alpha合并为一次，越权项没有执行，其余三个各一次。counts为ok=2、no_denominator=1、provisional=1、error=2。它是状态计数，不是业务成功率评测。

错误中的http_status是复用适配器错误分类的建议映射，本函数没有HTTP入口，不表示该批请求真的返回了502或403。若以后提供批量HTTP服务，应独立确定外层状态和逐项状态，不能把所有单项错误强行转换为同一个空列表。

## 10. 异常摘要不能泄露后端细节

BusinessError保存code和http_status；未预期异常返回INTERNAL_ADAPTER_ERROR，其他项继续。测试模拟含secret-fixture-value的内部异常，确认不出现在返回JSON中。

正式项目需要服务端记录经过脱敏的异常及关联request_id，让维护人员能诊断；本脚本没有实现持久日志与关联ID，也不把异常全部吞掉当作成功。禁止向模型暴露连接串、token、原始用户轨迹或未经处理的堆栈。

本例不自动重试。参数错误和越权不应重试；暂时不可用也应按依赖协议、剩余预算和退避策略决定。读请求去重不等于写操作幂等，更不证明超时写请求没有成功，相关内容见[Agent应用工程](../agent-engineering/README.md)。

## 11. 单批查询与分页作业要分开

本函数没有分页、数据库扫描、游标或断点恢复。数千个AOI/POI任务应该按稳定ID或版本化清单分批，保留每项状态与批次边界；如果清单在扫描期间变化，需要明确快照及重复/遗漏处理。

OSS适合保存已经生成的版本化任务清单或结果产物；数据库适合查询可更新状态及选择待处理对象。二者选择应看更新频率、筛选条件、权限和恢复需求，不是由“对象数量多”直接决定。本文没有部署OSS或任务数据库。

## 12. 运行、验收与开源依据

在仓库根目录运行，Python3.10及以上，标准库即可；本轮Python3.12.14：

```bash
python knowledge/business-ai-cases/examples/batch_query_demo.py
python knowledge/business-ai-cases/examples/test_batch_query_demo.py
```

2026-10-05实际运行13项检查，全部通过；第二条写入[结果记录](examples/batch-query-results.json)。包含外壳先检、参数失败隔离、对象权限、有效参数去重、无跨请求缓存、乱序完成、并发峰值、复制独立性与异常脱敏。没有验证LLM、HTTP、生产权限、数据库、网络deadline、重试、分页和持久恢复，也不证明线上业务已成功。

本轮重新读取[FastAPI嵌套请求模型文档](https://github.com/fastapi/fastapi/blob/5f9fc5c59a9bb54608aa35376715f3ba9708188e/docs/en/docs/tutorial/body-nested-models.md)，固定提交5f9fc5c59a9bb54608aa35376715f3ba9708188e。它介绍带类型元素的列表及嵌套模型；本文用手写标准库校验，没有安装FastAPI/Pydantic，也没有复用上游代码。批量大小、身份检查、去重键、线程调度和业务状态为独立教学设计，不由该文档自动保证。

FastAPI采用MIT，[完整许可](../agent-case-studies/licenses/fastapi.txt)已保留；[来源及验证范围](examples/batch-query-sources.json)可机器读取。

[批量源码](examples/batch_query_demo.py) · [检查源码](examples/test_batch_query_demo.py) · [返回业务目录](README.md)
