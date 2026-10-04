# 画像预热：批量对象、部分失败与可恢复作业

本篇为独立业务设计，全部输入与ID虚构；没有连接真实业务系统，也不声称开源项目已经实现这些业务功能。

## 业务问题与价值

页面查询某些对象画像很慢，团队希望提前读取并填入缓存。Agent适合解释需求、生成作业计划和汇总结果；大量重复读取更适合确定性的worker完成，不必为每个对象调用模型。

先确定预热对象、population_type、统计窗口、数据版本和缓存有效期。成功的定义是必要内容已核验并按约定可查询，不是HTTP返回200或Agent说“预热完成”。

## 作业编排与键

教学真实键设计为tenant+object_id+population_type+window+data_version；同对象不同人群类型不能去重成一项。计划生成后登记job_id，worker执行、保存每项状态，汇合后给出完整或partial结果。

OpenHands控制面客户端提供运行列表、派发与取消入口，可借鉴任务ID和控制面职责；它不能证明本篇画像worker的幂等、缓存写入和崩溃恢复已经实现。真正的保障应在后端存储与执行层。

## 最小可运行示例

prewarm夹具只使用(object_id,population_type)二元组，因为租户、窗口和版本在此固定。输入(A,1)、重复(A,1)、(A,2)、(B,1)，共有3个不同目标。B首次模拟超时，第二次成功；实际读取共4次。

函数仅重试TimeoutError，最多两次；超过上限记failed。其他异常不会被统一吞掉。这是模拟读取，不创建订单、不调用真实API，也没有实际缓存写入。

## 从示例升级到生产

加入批量上限、租户并发、总deadline和下游限流；尽量使用批量接口，按对象ID映射部分成功。只有确认可安全重试的操作才重试，未知写入结果先查实际状态。

持久化任务与每项attempt、last_error、result_version。worker崩溃后以租约或检查点恢复；旧worker不得覆盖新版本结果。输入对象名单可来自数据库或文件，选择依据更新频率、一致性和批量规模，而不一概认为某存储更好。

## 业务验收

报告计划项、去重项、成功项、失败项、费用和完成窗口；成功缓存还应抽样读取检查。重复作业是否覆盖旧数据取决于明确版本策略，不能按“最后完成的请求”决定新旧。

离线检查覆盖二元键去重、部分重试与次数上限；未验证跨进程恢复、并发、真实缓存和任务取消。业务收益以查询延迟变化与缓存命中率测量，不能仅以预热任务数增加为目标。

## 开源机制与示例验证

- [OpenHands/OpenHands：src/api/automation-service/automation-service.api.ts](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/src/api/automation-service/automation-service.api.ts)：借鉴工具接口、上下文或评测机制，业务口径独立定义。
- 关联[100项应用知识](../ai-application-playbook/README.md)：015、018、071、073、075、078。
- [业务规则脚本](examples/business_rules.py)中的prewarm；[已运行检查](examples/test_business_rules.py)；[实际示例输出](examples/expected-results.json)。

固定来源核验于2026-10-04；许可沿用[来源清单](../agent-case-studies/sources.md)。中文设计与示例独立编写，与原项目无隶属关系。

[返回业务案例目录](README.md)
