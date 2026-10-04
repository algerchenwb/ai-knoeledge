# 向量相似度：余弦、内积、L2 与检索效果

## 先区分“表示好不好”和“搜索快不快”

Embedding模型将文本映射成向量；索引负责寻找相近向量。如果正确文档在向量空间里就不靠近问题，换更快的索引也不会修好语义。先用精确搜索测表示质量，再测近似索引损失。

Sentence Transformers区分对称与非对称检索：相似问题匹配通常长度和任务接近；短问题找长段落则不对称。检索模型的query/document模板、前缀或编码方法应遵循模型约定，不能只看维度。

## 三种相似度怎么理解

```text
内积：a·b = Σ a_i b_i，越大通常越近
余弦：cos(a,b) = a·b / (||a|| ||b||)，越大越近
欧氏距离：||a-b||，越小越近
```

余弦主要比较方向，内积还受向量长度影响。若a=[1,0]、b=[10,1]、c=[1,1]，b的内积比c大；不能据此说b在所有任务中一定更相关。哪种度量合适取决于模型训练目标。

对于非零向量，先单位化再做内积，等于余弦。单位向量有L2²=2-2cos，因此按余弦降序与按L2距离升序等价。Faiss的L2结果通常是平方距离，不能把它当未经平方的欧氏距离。

零向量的余弦没有定义；空文本、异常预处理和无效向量需要明确处置。归一化不是无成本万能修正：若模型依赖长度表达信息，擅自归一化会改变行为。

## 相似度不是可靠概率

分数0.8不等于80%正确。不同模型、语种、领域、文本长度和负样本下分布不同；一条“不支持退款”的文档可能与“支持退款”的问题高度相似。

固定阈值前，应标注本领域问题—文档对，观察正负样本分布、漏召回和误召回。高相似度说明值得进一步检查，不证明证据能回答问题。

## 如何建立评估集

为每条query保存一个或多个相关doc_id，加入同主题但口径错误的困难负例。例如“2026年9月居住人口”与“2026年9月客流”“2025年9月居住人口”只差少量词，业务含义却不同。

| 指标 | 关注点 | 注意事项 |
| --- | --- | --- |
| Recall@k | 已知相关文档找回多少 | 多相关文档时分母是相关集合大小 |
| Hit@k | 是否至少命中一个相关项 | 不应与Recall混称 |
| MRR | 首个相关文档排名 | 后面的相关项不直接影响这项 |
| nDCG@k | 排序与分级相关性 | 需要明确等级及增益定义 |

还应按中文、代码、长文、数字、否定句和别名分组看效果。总体均值可能掩盖关键类别失败。

## 工程中的版本契约

至少记录模型revision、tokenizer、query/document模板、池化、归一化、维度、分块版本、源文档版本和创建时间。索引迁移要么全量重建，要么明确多版本分区，不能把新旧向量无标识地混入。

## 练习

运行[数学示例](../expansion-2026-10/examples/ai_math_checks.py)检查单位向量的距离关系。若有2篇相关文档、top3只找回1篇，Recall@3=0.5而Hit@3=1。检索评估应写清采用哪个定义。

## 来源

Faiss README的度量约定；Sentence Transformers semantic-search文档的对称/非对称检索。固定链接见[来源清单](../expansion-2026-10/SOURCES.md)。下一篇：[近似索引](02-flat-ivf-hnsw-pq.md)。

核验日期：2026-10-04。对应固定快照：

- [facebookresearch/faiss / README.md](https://github.com/facebookresearch/faiss/blob/b0074a3fa426027d9ff8575b44386d5922859ac9/README.md)
- [huggingface/sentence-transformers / examples/sentence_transformer/applications/semantic-search/README.md](https://github.com/huggingface/sentence-transformers/blob/4a3b5cd6ec718e421f57e824a41ed3fd99595df6/examples/sentence_transformer/applications/semantic-search/README.md)
