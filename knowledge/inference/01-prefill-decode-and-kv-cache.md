# Prefill、Decode 与 KV Cache：为什么长对话占显存

## 首字慢和后续慢不是同一个问题

Prefill处理已经给出的输入token，生成各层上下文表示与缓存；Decode按生成步骤继续处理新token。常规自回归生成依赖之前输出，同一个序列的后续token不能全部提前并行算完。

长输入会增加prefill工作；长输出会增加decode步骤。排队、网络、检索和工具执行也能拖慢首字，不能看到“首字慢”就断定GPU算力不足。

## KV缓存保存的是什么

因果注意力下，已经处理的历史位置不读取未来token，因此其K/V可以复用。生成新token时，各层计算新位置的Q/K/V，新Q关注缓存的历史K/V和当前K/V，再把新K/V追加进去。

缓存的是中间计算结果，不是独立的事实库，也不等于永久聊天记忆。修改历史输入、position处理、模型权重或相关配置后，旧缓存不一定可用。双向attention或其他架构不能原样套用这一解释。

## 为什么一般不缓存Q

普通单步decode只需要新位置的Q来预测后续token，历史位置的输出无需重算；历史K/V则会被新位置读取。某些复杂算法可能有额外缓存，本文描述标准自回归路径。

## 显存公式要标清范围

对普通全上下文注意力，未分片、未量化、没有滑动窗口等特殊压缩时，KV数据本体可粗算：

```text
bytes = 2 × 层数L × 并发序列数B × 缓存长度T
          × KV头数H_kv × 每头维度D_head × 每元素字节s
```

2代表K与V。例：L=32、B=1、T=8192、H_kv=8、D_head=128、s=2，结果为1073741824字节，即1GiB。B=4且同长度，约4GiB。

MHA通常H_kv与query头数相同；GQA共享部分K/V头；MQA使用更少K/V头。按query头数代入GQA会高估KV本体。MLA、混合架构、滑窗、分片和缓存量化则需使用对应结构，不能套此公式。

这不包含模型权重、临时工作区、页管理、碎片和其他激活。进程实际峰值可能明显更高。

## 缓存减少什么，不减少什么

它避免重复生成历史K/V及历史位置的很多计算。但新Q仍要读取相关历史K/V，所以在普通全注意力单步decode中，attention工作随上下文长度增长。缓存并不把整个生成过程变成与长度无关。

## 前缀缓存

多个请求有完全可复用的前缀时，可以重用前缀KV，减少prefill。vLLM的APC文档明确区分它对prefill的收益与对新输出decode的限制。

前缀缓存通常要求相同token前缀和兼容的执行条件；文义相似而token不同不能直接算命中。频繁在system前加时间戳、随机ID等可能破坏复用。权限、租户隔离和实现缓存键仍要核对。

## 后端容量例子

请求数一样，平均上下文从2k增长到16k，KV和attention读取会显著变化。因此除了限制并发请求，也应限制token预算、单序列长度和总缓存容量，设置超时与取消释放，记录输入/输出长度分布。

## 练习

运行数学示例核对1GiB结果。若把H_kv从8改为32，同样假设下KV变成4GiB；这只是理论数据本体，不是某款模型的实测显存。

## 来源

Transformers cache_explanation.md与vLLM automatic_prefix_caching.md，固定链接见[来源清单](../expansion-2026-10/SOURCES.md)。关联：[原有小模型内存专题](../../courses/generative-ai-for-beginners/deep-dives/19-small-model-memory-and-inference.md)。

核验日期：2026-10-04。对应固定快照：

- [huggingface/transformers / docs/source/en/cache_explanation.md](https://github.com/huggingface/transformers/blob/469230357aab0f2b303b0d638c1f8d06edb14184/docs/source/en/cache_explanation.md)
- [vllm-project/vllm / README.md](https://github.com/vllm-project/vllm/blob/84bcbc62644356270aaaa5e2d0237d03adc9bb3a/README.md)
