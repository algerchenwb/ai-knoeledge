# AI 中文知识库

面向应用开发者，把 AI 概念解释清楚，再落实到可以验证的工程方法。

## 新增的深入专题

- [AI 业务应用案例](knowledge/business-ai-cases/README.md)：十个可复算业务案例，另附HTTP集成、工具注册、批量查询、金标准评测、结果缓存、对象解析、结果校验、售前知识库、客服工单、报告验收、报价计价、数据导入、客户激活、业务试点与用量额度十五篇教程；含源码、已运行检查和业务验收边界。

- [AI 应用落地：100个知识点](knowledge/ai-application-playbook/README.md)：十个方向，逐项提供应用场景、实现步骤、验收方法与常见误区，附15个开源项目快照。

- [Agent 开源实现案例：十篇深度教程](knowledge/agent-case-studies/README.md)：SQL流程、客服转接、代码执行、报告交付、工具组合、仓库修复、控制面、浏览器、研究与Agentic RAG，区分上游演示与实际验证。

- [Agent 应用工程：十七篇深入教程](knowledge/agent-engineering/README.md)：工具重试、幂等键、未知结果、checkpoint 恢复、回执与补偿、人工审批及版本绑定、取消与部分完成、资源预算及并发准入、结构化输出与工具参数校验、结果缓存及数据新鲜度、熔断与故障隔离、分页游标及快照、链路观测与统计口径、轨迹与业务验收、速率及租户配额、异步队列背压与任务收尾、工具协议及契约版本、持久任务租约与回执账本、业务指标语义及人群汇总、异常诊断与因果边界、推荐排序及敏感性；结合 LangGraph / Temporal / Pydantic AI / Pydantic / cachetools / PyBreaker / Kubernetes / OpenTelemetry / agentevals / aiolimiter / CPython / MCP / MetricFlow / DoWhy / pymcdm 固定开源来源，附已运行离线检查。

- [半监督学习与伪标签](knowledge/semi-supervised/README.md)：自训练筛选、置信度与确认偏差、标签轮次、独立测试及已运行scikit-learn实验。

- [应用算法：文本、推荐、图与数据流](knowledge/applied-algorithms/README.md)：逐轮补充TF-IDF、特征哈希、NMF、关联规则、隐式ALS、排序指标、PageRank、图消息传递、在线学习和漂移检测，附开源快照与已运行实验。

- [预测区间与不确定性](knowledge/prediction-uncertainty/README.md)：区间含义、覆盖率、校准集与 split-conformal 有限样本手算，附已运行模拟及开源来源。

- [时间序列预测与回测](knowledge/time-series/README.md)：滞后与滚动特征、可用时间、标签成熟、顺序回测及预测指标，附已运行实验。

- [特征工程基础](knowledge/feature-engineering/README.md)：缩放、缺失、类别编码与目标编码，附已运行的 scikit-learn 检查。

- [模型可解释性](knowledge/explainability/README.md)：置换重要性、PDP/ICE、Shapley/SHAP，涵盖相关特征、背景选择与因果边界，附手算及已运行 scikit-learn 集成示例。

- [训练工程详解](knowledge/training-engineering/README.md)：8篇覆盖优化器、学习率、数据加载、梯度累积、AMP、训练恢复、DDP和排障，附13组已运行标准库实验。

- [本轮18篇详解总导航](knowledge/expansion-2026-10/README.md)：涵盖6个专题，核对10个开源项目，附固定来源与15组已运行数学示例。

- [Transformer 内部机制](knowledge/transformer/README.md)：Embedding 与位置、注意力与掩码、残差、归一化与前馈层、标签对齐、交叉熵与困惑度、解码与采样。

- [检索算法与质量](knowledge/retrieval/README.md)：相似度与检索评估、Flat、IVF、HNSW 与 PQ、混合检索与重排。

- [微调与偏好对齐](knowledge/post-training/README.md)：SFT 数据与损失掩码、LoRA 与 QLoRA、DPO、GRPO 与奖励投机。

- [模型推理与服务性能](knowledge/inference/README.md)：Prefill、Decode 与 KV Cache、量化与内存预算、批处理、调度与延迟。

- [多模态基础](knowledge/multimodal/README.md)：CLIP 与对比学习、扩散模型与调度器。

- [强化学习基础](knowledge/reinforcement-learning/README.md)：MDP、策略、价值与 Q-learning、环境、终止、截断与评估。

## 已有专题与课程

- [无监督学习基础](knowledge/unsupervised-learning/README.md)：K-means、DBSCAN、PCA、高斯混合模型与 EM、层次聚类、OPTICS 与 HDBSCAN、聚类稳定性，涵盖评估、空间距离、信息损失、软归属、密度估计、树状图、密度尺度与标签比较，附已运行示例。

- [经典机器学习模型基础](knowledge/classical-ml/README.md)：线性回归、逻辑回归、正则化、决策树、随机森林、梯度提升、支持向量机、核方法、近邻模型、朴素贝叶斯、概率校准、类别不平衡、异常检测、特征选择、置换重要性、模型保存、输入协议与学习/验证曲线，附已运行的验证脚本。

- [深度学习训练基础](knowledge/deep-learning-basics/README.md)：张量、自动求导、神经网络与训练循环，基于 PyTorch 官方开源教程，附可运行数学演示。

- [机器学习评估基础](knowledge/ml-evaluation/README.md)：数据泄漏、交叉验证、指标与业务决策，基于 scikit-learn 开源文档。

- [Microsoft Generative AI for Beginners 中文详解](courses/generative-ai-for-beginners/README.md)：已覆盖环境准备与 21 节课程，另有术语表、后端实践、代码审阅和离线示例；逐篇独立提交。

## 阅读约定

每篇包含通俗解释、关键机制、业务示例、误区、练习与来源。课程解读和额外工程实践分别标明；不把历史模型、价格、SDK 用法当作永久有效的结论。示例中所有账号、标识和数据均为虚构。

这是独立学习知识库，与 Microsoft 官方课程没有隶属关系。原课程采用 MIT License，相关来源与版权声明随专题保留。
