# 业务Agent金标准评测：从“演示成功”到可复跑验收

Agent能回答一个问题，不代表改提示词、换工具版本或调整数据接口后仍能回答正确。业务开发需要一套可复跑题集：输入固定、期望由业务口径确定、失败能定位到环节，发布时比较同一题的变化。

本篇把[评测与可观测知识点](../ai-application-playbook/09-evaluation-and-observability.md)落实为12道结构化教学题及标准库评测器，复用[工具注册路由](12-business-tool-registry-routing.md)和[业务计算](11-api-agent-http-integration.md)。全部对象、数据和身份为虚构；本轮没有调用LLM、HTTP或Opik SDK，也没有真实客户题集。本例评估确定性后端行为，不测自然语言理解准确率。

## 1. 金标准先固定业务定义

“区域到访占比50%”必须说明分子、分母、去重、时间和人群范围。否则评测员各自理解，模型结果对不对没有统一答案。

本例area-alpha有4名区域用户，业态到访与区域集合交集为2人，所以2/4=0.5；竞品共访为2人，区域方向0.5、竞品方向1.0。空分母返回null，未成熟数据返回provisional。期望值按这些虚构口径手工定义，不从被测函数输出自动生成。

题集应记录业务定义版本和标注依据。真实项目还需业务人员独立复核、覆盖不同对象和时间，出现争议时先澄清口径，再修改答案。把同一实现算出的结果保存成“正确答案”，容易把实现错误一起固化。

## 2. 输入题与最终答案之间有多层

| 层次 | 要回答的问题 | 本例覆盖 |
|---|---|---|
| 语义理解 | 用户话语被解析成正确任务了吗 | 未覆盖，只接受结构化提案 |
| 工具路由 | coverage与overlap选择正确能力了吗 | 5道结果题 |
| 业务数值与状态 | 比例、人数、空分母、未成熟状态正确吗 | 5道结果题 |
| 证据 | 固定快照来源与数据版本匹配吗 | 仅1道题 |
| 拒绝与失败边界 | 非法输入、越权、预算和数据错误如何返回 | 7道错误题 |
| 最终文字解释 | 文案是否新增无证据原因或承诺 | 未覆盖 |

一个总体分数无法说明哪里退化。也不能看到route正确，就认为对象、窗口和数值都正确。把模型接入后，应单独评估提案生成，再评估端到端交付。

## 3. 每题包含可观察期望

[题集JSON](examples/business-golden-dataset.json)记录version、basis和cases。每题包含id、critical、proposal以及checks；每条check只包含dimension、path和expected。

例如coverage-50检查工具名、status=ok、numerator=2、denominator=4、ratio=0.5，以及context和evidence的数据版本。检查值来自结构化输出路径，不比较整段答案文字，避免空格或措辞变化使正确数字误判。

这里是有限路径断言，不是完整JSON Schema校验。额外字段、所有上下文字段、解释文案以及未列入题集的结果都不会自动验收。正式项目应补协议校验、数据版本一致性和必要字段覆盖，再对解释做独立评价。

## 4. 正例之外要有边界题

本轮12道题分别是：

| 题ID | 期望 |
|---|---|
| coverage-50 | 占比2/4=50%，来源与数据版本固定 |
| overlap-directions | 共访2人，两个方向50%与100% |
| empty-population | 分母0，比例null，no_denominator |
| empty-competitor | 区域方向0，竞品方向null |
| provisional-data | 未成熟，result=null |
| cross-tenant | execute阶段OBJECT_FORBIDDEN |
| upstream-unavailable | execute阶段UPSTREAM_UNAVAILABLE |
| bool-population | plan阶段INVALID_POPULATION |
| metric-injection | plan阶段INVALID_PARAMETERS |
| unsupported-goal | plan阶段UNSUPPORTED_TASK |
| uncovered-window | execute阶段DATA_SCOPE_MISMATCH |
| insufficient-budget | execute阶段TOOL_BUDGET_EXCEEDED |

正确拒绝也算题通过，但不应与成功业务查询混为一谈。报告按维度分别列分子分母。题集没有真实对象别名、复杂歧义、权限热更新、长对话、并发或写操作；12题不是生产覆盖率证明。

## 5. 错误码和拒绝阶段都要核对

run_case先执行Registry.plan，再执行Registry.execute；BusinessError记录kind=error、stage和code。错误码相同而阶段错误，也可能暴露职责混乱。

比如区域对象权限在当前示例的业务execute检查；非法人群类型在plan就拒绝。把越权题改成plan阶段，评测会失败。真实架构如果有意前移校验，应审查新边界并提升题集版本，而不是为了让分数通过随意改标签。

未预期异常返回harness_error，不能伪装为业务拒绝成功。它表示需要检查被测实现或测试执行环境，本例仅保存阶段，不实现服务端异常日志与trace关联。

## 6. 缺字段、null、0和布尔值分别判断

lookup同时返回present与actual，缺失字段不等于字段存在且值为null。空分母的ratio必须存在且为null；字段被删除时题失败。合法0比例也不能用“无数据”替代。

整数期望采用严格类型比较，True不能冒充1名用户。浮点期望允许有限int/float，绝对容差1e-12、相对容差0；NaN和Infinity拒绝。本容差适用于小型教学比例，不适合作为金额、所有科学计算或百分比展示的通用规则。金额应按币种精度和Decimal等规则独立评估。

实际业务允许的误差应先由口径确定，区分源数据估计误差、浮点误差和四舍五入展示。不能在发现结果错误后不断扩大容差，让失败消失。

## 7. 按题聚合，避免断言数量改变权重

coverage-50有多条business断言，但business维度只计为一题。该维度所有断言通过，才计passed_cases加1；有一个失败则整题该维度失败。

这样不会因为某题写了十个字段检查，就比只写一个字段的题权重大十倍。报告保留case_id与失败路径，既能看汇总，也能回到原题。

总体passed_cases要求每题所有适用断言通过。维度只统计适用题，不能把没有evidence断言的11题记成“证据正确”。当前基线为business 5/5、route 5/5、evidence 1/1、boundary 7/7，总体12/12；evidence样本太少，需继续扩充。

## 8. 关键错误不应被平均分掩盖

cross-tenant和metric-injection标记critical。只要关键题失败，报告critical_failures列出题ID。教学gate要求全部题通过，而不是只看关键题；其他题失败也会gate=fail。

这一策略仅服务于固定确定性回归。真实LLM评测可能需要重复运行、置信区间、业务分层阈值和人工审批；越权等严重错误仍应设置独立阻断条件，不能靠大量简单题抵消。阈值由业务风险与试点数据决定，本文没有虚构“90%就能上线”的通用标准。

脚本gate失败退出码1，通过退出码0，可作为未来CI步骤。本轮没有新增GitHub Actions工作流，也没有触发真实发布；退出码只是本地回归门槛。

## 9. 评测器本身也要验证

不能只展示基线全绿。测试人为改错输出，检查评测器是否变红：错误工具、比例0.75、布尔人数、NaN/Infinity、缺证据、错误来源、删除null字段、错误拒绝阶段、错误数据版本。

10项评测器检查全部通过，包括聚合不会按断言数量加权、重复题ID及空题集被拒绝。它们检验评分逻辑和本组案例的故障识别能力，不代表已经测完所有恶意输入或证明评测器无缺陷。

若评分器从不拒绝任何错误输出，可能是取错字段、漏跑断言或将异常当作通过。新增评分规则时，应先增加一个能被它捕获的错误样本；不用大量镜像实现的测试替代业务金标准。

## 10. 数据集、注册表与运行记录分别留版本

报告保存dataset_version、完整题集内容的dataset_sha256、catalog_revision、日期、逐题结果与summary。修改期望来源版本会改变题集指纹，并使对应题失败。

catalog_revision来自注册表元数据，不自动覆盖适配器源码。真实实验应进一步记录代码commit、模型标识、提示版本、工具协议、数据快照、随机性配置和评价器版本，才能比较同一配置下的结果。当前报告没有这些完整生产实验字段。

固定题集容易被训练或提示词调试反复拟合，正式系统应保留独立验收集，并按对象、时间或客户划分，避免相似样本泄漏。新增业务能力后要补对应题，而不是一直只用旧任务得到漂亮分数。

## 11. 规则评价与LLM裁判分工

可以复算的金额、比例、对象、日期、权限与返回状态优先用确定性规则。解释是否清楚、引用是否真正支持因果判断，可以由人工或校准后的LLM裁判补充。

LLM裁判也可能偏向长答案、偏好某种措辞或受被评答案中的指令影响。应固定rubric、隔离输入、提供正负例并与人工标签核对；不要让模型自行宣布“我已正确完成”。本例没有LLM裁判，也不评估答案中新增因果。

Opik固定README介绍数据集、实验、启发式和LLM裁判指标，以及CI/PyTest评测。它支持组织此类流程，但平台本身不替业务团队定义分母、权限或正确答案。这里的题集和评分器独立编写，未安装运行Opik，也未向平台上传数据。

## 12. 运行与来源

在仓库根目录运行，Python3.10及以上、标准库即可；依赖现有tool_registry_demo.py与api_agent_demo.py，本轮Python3.12.14：

```bash
python knowledge/business-ai-cases/examples/business_golden_eval.py
python knowledge/business-ai-cases/examples/test_business_golden_eval.py
```

第一条运行12道题，写入[评测报告](examples/business-golden-report.json)；第二条运行10项评分器检查。2026-10-05两条命令退出码0。没有测试真实LLM、HTTP、生产数据库、自然语言题集、人工标注一致性、延迟成本或经营效果。

本轮重新读取[comet-ml/opik README](https://github.com/comet-ml/opik/blob/657e3197dc460e6441471c832d93666c7fc730c8/README.md)，固定提交657e3197dc460e6441471c832d93666c7fc730c8；开源依据限于数据集、实验、指标和CI评测机制，不采用其中营销性能数字或其他产品对比。采用Apache-2.0，[完整许可](../agent-case-studies/licenses/opik.txt)已保留。[来源与验证记录](examples/business-golden-sources.json)包含范围。

[评测器源码](examples/business_golden_eval.py) · [故障注入检查](examples/test_business_golden_eval.py) · [返回业务目录](README.md)
