# 混合检索与重排：召回、融合、Reranker 和权限

## 两阶段的直觉

从一百万文档里先找100个可能相关项，再认真比较这100个。第一阶段追求候选覆盖与速度，第二阶段追求排序质量。Sentence Transformers的retrieve-rerank文档用bi-encoder召回、cross-encoder重排说明这一思路。

Bi-encoder分别编码问题和文档，文档可以提前计算向量。Cross-encoder同时读取问题与候选文本，让二者在网络中直接交互；每个查询—文档对都需要计算，通常更贵。它只能重新排列看到的候选，无法救回第一阶段没找来的证据。

## 为什么同时保留关键词检索

关键词擅长精确标识、罕见术语、代码路径、错误码；向量检索擅长一定范围的改写与语义关系。比如“/v1/signal/ap_location”与“WiFi定位接口”的检索需求不同，组合两路能减少单一方法盲区，但效果必须用任务集验证。

BM25是一类常见词项检索打分，结合词频、词项稀有度和文档长度处理。实际中文分词、别名词典、字段权重和索引设置仍决定效果，不能认为启用BM25就自动解决所有精确匹配。

## RRF为何用排名融合

不同检索器分数量纲不一致，简单把BM25=12与cosine=0.8相加没有可靠解释。Reciprocal Rank Fusion采用各路排名：

```text
RRF(doc) = Σ 1 / (c + rank_i(doc))
```

rank从1开始，某路未出现的文档在该路贡献0，c是平滑常数。例：列表1=[A,B,C]，列表2=[C,B,D]，c=60，则C得1/63+1/61，B得2/62。C略高于B；这只是一个演示，c=60不是所有任务的最优值。

RRF能绕开原始分数尺度问题，但也丢掉分数差距信息；完全无关候选仍可能被排在前面，需要质量门槛和后续判断。此公式是原创通用工程补充，来源文件主要核对两阶段检索。

## 重排分数为什么也不是概率

某些cross-encoder输出logit，某些经激活得到[0,1]分数，其他模型可能使用不同范围。不能假设所有reranker都输出校准概率。设拒答阈值前要使用真实领域数据校准。

候选越多，重排越贵；文本越长也越贵。截断策略可能恰好丢掉答案所在的结尾，应该测候选长度、截断位置、批次配置和延迟。

## 切片、去重与父文档

相邻片段可能覆盖同一段内容，导致top5实际上只来自一份文档。可按doc_id或章节去重，保存chunk到父文档关系，必要时扩展上下文。去重不能误删同一文档中回答不同子问题的片段。

生成前保留稳定doc_id、源路径、版本和原文片段，引用才能核查。漂亮答案没有可追溯证据，仍不算检索增强的有效验收。

## 权限是服务端约束

如果未经授权文档参与召回、重排或LLM上下文，即使最终没有展示，也可能已发生数据越界。因此应在进入这些阶段前限制候选为当前用户可访问集合，并在展示或使用前再校验。实现上可以采用预分区或过滤查询，不应让模型自行决定权限。

## 业务例子

API知识检索可以先按租户、接口是否可用、权限和版本过滤，再用精确路径/名称召回与语义召回，融合后重排。指标口径中的月份、人群和分母作为明确字段校验，不能仅凭文本相关分数确定。

## 练习

运行数学示例核对RRF。设计“检索到错误版本但主题很相关”的负例；记录失败发生在源文档管理、过滤、召回还是重排。按阶段定位比直接换模型更容易解释改进原因。

## 来源

Sentence Transformers semantic-search与retrieve-rerank文档。BM25、RRF、权限与父文档策略为独立工程补充，未将其声称为这两份示例的完整实现。见[固定来源](../expansion-2026-10/SOURCES.md)。

核验日期：2026-10-04。对应固定快照：

- [facebookresearch/faiss / README.md](https://github.com/facebookresearch/faiss/blob/b0074a3fa426027d9ff8575b44386d5922859ac9/README.md)
- [huggingface/sentence-transformers / examples/sentence_transformer/applications/retrieve_rerank/README.md](https://github.com/huggingface/sentence-transformers/blob/4a3b5cd6ec718e421f57e824a41ed3fd99595df6/examples/sentence_transformer/applications/retrieve_rerank/README.md)
