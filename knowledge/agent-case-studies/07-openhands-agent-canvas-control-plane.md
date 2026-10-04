# OpenHands Agent Canvas：让 Agent 接入执行后端与任务控制面

核验日期：2026-10-04。证据级别：当前主仓库的控制台、Docker 接入示例与自动化 API 客户端；后端执行保障未在本轮验证。

## 1. 先认识当前仓库实际是什么

2026-10-04 主仓库 README 标题是 Agent Canvas，定位为自托管编码 Agent 与自动化的开发者控制中心。它可以连接本地、远程和云端后端，也支持通过 ACP 接入不同编码 Agent。不能继续把这个主仓库描述成旧版 Python 单体修复 Agent。

该案例的知识点是**Agent 执行器与任务控制面可以分开**：执行器负责读代码、调用工具和完成工作；控制台负责选择后端、管理会话、配置触发和查看运行。更换 Agent 不一定要求重写所有运维入口。

## 2. 源码证据如何串起来

examples/acp-docker 提供容器化 Agent Server 的连接流程，带持久化 volume；控制台可以指向其后端地址。文档还提供按 config/defaults.json 生成固定镜像配置的方法，以保持控制台和执行服务器兼容。

automation-service.api.ts 是客户端封装，含自动化创建、更新、派发、运行列表和取消方法。代码会按当前后端选择本地请求或云代理；某些导入过程把请求固定到开始时的后端，防止中途切换导致创建和清理落到不同机器。这是非常具体的状态一致性设计。

## 3. 哪些能力不能由客户端推出

看见 cancelAutomationRun 的 API 调用，只能证明客户端有取消入口，不能证明所有模型调用或外部写操作都能立即停止。看见自动化列表，不等于后端已提供 exactly-once 执行。后端行为需要另外查看服务器实现并实测。

控制台里的任务状态应对应执行后端记录，而不是单靠浏览器本地计时。“触发成功”与“任务完成”也不同：前者可能只拿到了 run_id，后者还要有产物和验证结果。本篇不把 UI/API 客户端包装成端到端保障。

## 4. 可以怎样做持续迭代任务

教学改造：一次 GitHub issue 事件先产生 job_id，执行器在独立分支或工作目录处理，完成后上传补丁摘要和测试结果，控制面展示状态及产物位置。定时任务与事件任务都记录 trigger_id、run_id、仓库基准 SHA 和代码产物 SHA。

重复投递同一事件时，依赖后端唯一键或幂等记录避免重复启动。若操作执行成功但回执丢失，先查询真实结果再决定重试。幂等、并发锁和事务外盒是本文建议，不是当前所读客户端已经实现的结论。

## 5. 部署边界要具体

同一控制台可以切换后端，但凭据、文件系统和网络权限跟随实际执行环境。文档提示无沙箱模式会直接访问宿主机；Docker volume 也会保留会话和凭据。测试机器与生产机器不能仅靠一个显示名称区分，任务请求中应绑定实际 backend_id。

示例涉及凭据 onboarding，本篇不复制凭据文件或建议提交凭据。复现应使用测试身份，固定镜像并记录兼容要求；模型、云服务与本地运行成本分别核算。项目的云与企业产品能力不等同于仓库所有代码都开源。

## 6. 检查与练习

[离线脚本](examples/agent_case_checks.py)演示同一事件重复到达只登记一次任务，同时检查不同事件不会被错误合并；它没有运行 Agent Canvas，也没有模拟跨进程崩溃。生产版本需要持久化与并发测试。

练习：用户在导入中途切换后端，为什么必须继续把清理请求发回原后端？因为新后端没有原来创建的临时资源，清理错位置会留下孤立任务。

## 开源来源

- [README.md](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/README.md)
- [examples/acp-docker/README.md](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/examples/acp-docker/README.md)
- [src/api/automation-service/automation-service.api.ts](https://github.com/OpenHands/OpenHands/blob/a6bba78ffd5a8b31620770f52383b1a2c0477fcd/src/api/automation-service/automation-service.api.ts)

来源与许可见[快照清单](sources.md)。中文解释与业务改造由本知识库独立编写，不是官方逐字翻译；改造建议不表示上游已经实现。

[返回案例目录](README.md)
