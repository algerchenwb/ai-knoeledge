# AutoGen 代码执行协作：把运行结果反馈给生成者

核验日期：2026-10-04。证据级别：官方 Notebook 描述生成图表并给出展示单元；本轮未复现模型及 Docker 执行。

## 1. 不只是两个模型轮流聊天

官方示例用 Assistant 编写 Python，用 Executor 执行代码，任务是生成两家公司的历史股票收益对照图。Assistant 负责调用模型；Executor 负责提取 Markdown 代码块并交给执行器；运行输出再次发布成消息。

知识点是**把推断与执行拆成可观察的职责**：模型说“应该运行成功”没有证明力，执行器返回的退出结果、异常和文件才是下一轮依据。图表业务只是演示载体，本篇不提供金融建议。

## 2. 源码中的通信机制

两个自定义类继承 RoutedAgent，用 message_handler 处理 Message，并通过 DefaultTopicId 发布消息。Assistant 维护自己的聊天历史，Executor 从消息里提取 CodeBlock。SingleThreadedAgentRuntime 负责注册、消息分发和生命周期；DockerCommandLineCodeExecutor 承担执行。

所以 Executor 不必再使用第二个大模型。一个确定性的执行 Agent 也能参与协作；“多 Agent”并不要求每个节点都昂贵地调用模型。通信基础设施与各 Agent 业务逻辑分离，使执行器可以更换而不改研究任务的提示。

## 3. 运行反馈为何比自我评价更强

假设模型把 date 列拼成 data。Executor 把 KeyError 作为观测返回，Assistant 才能针对具体错误修复。反之，只让另一个模型阅读代码并打分，仍可能一起忽略错误。

但反馈也有层次：退出码为0只说明进程结束；生成 PNG 只说明产物存在；收益区间、缺失值与坐标含义正确需要业务检查。不同层的成功不能混为一谈。公开 Notebook 保留图像展示单元，本轮没有验证图片是否能在当前网络与模型配置下重建。

## 4. 该教学样例还需要补什么

示例用 stop_when_idle 等待消息系统空闲；空闲不一定就是业务目标完成。生产版本需显式任务状态、最大生成次数、执行超时、文件检查以及失败出口。否则生成者与执行者可能反复交换消息，费用和时间增长。

Docker 是执行环境，隔离强度取决于配置。只挂载任务工作目录，限制网络和资源，避免向生成代码暴露宿主机凭据；不能把“用了 Docker”写成“任何代码都安全”。代码块正则只负责定位，不负责安全验证。

## 5. 迁移到数据分析助手

教学改造：后端先从受控接口导出虚构区域客流 CSV；模型只能在临时目录做聚合与绘图；Executor 返回 summary.json 和图片清单；业务验证器核对日期范围、总数和空值口径。统计汇总由确定性函数承担，文字解释由模型完成。

可约定产物清单：文件路径、内容摘要、数据版本、执行退出码、检查结果。重试前保留原始输入与上次错误，修复后重新运行所有受影响校验。不要删除错误日志后只保留最终看起来漂亮的一张图。

## 6. 版本、测试与练习

2026-10-04 所读 README 标明 AutoGen 为维护模式，并建议新项目使用 Microsoft Agent Framework。本篇保留它的历史设计价值，不把它推荐为当前新项目的默认选型；不混用0.2与新版导入方式。

[离线脚本](examples/agent_case_checks.py)用可控反馈模拟两次尝试，核对达到目标与有界失败，未执行模型生成代码。练习：如果输出数字与金标准不一致，但代码无异常，应该重试解释还是修正计算？应先定位计算和数据口径，再生成解释。

## 开源来源

- [python/docs/src/user-guide/core-user-guide/design-patterns/code-execution-groupchat.ipynb](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/docs/src/user-guide/core-user-guide/design-patterns/code-execution-groupchat.ipynb)
- [README.md](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/README.md)

来源与许可见[快照清单](sources.md)。中文解释与业务改造由本知识库独立编写，不是官方逐字翻译；改造建议不表示上游已经实现。

[返回案例目录](README.md)
