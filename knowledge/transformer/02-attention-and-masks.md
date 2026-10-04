# Attention：Q、K、V、Softmax 与因果掩码

## 一句话直觉

注意力让一个位置按当前需要，从其他位置收集信息。Q像“我要找什么”，K像“我包含什么线索”，V像“我能提供什么内容”。这些只是帮助理解的比喻，Q/K/V实际上是模型学习的线性变换，不是人工写好的问题和答案。

## 计算分成四步

对输入表示X分别做投影：Q=XW_Q，K=XW_K，V=XW_V。然后：

```text
scores = Q @ K.T / sqrt(d_k)
scores = scores + mask
weights = softmax(scores, 按被关注的位置归一化)
output = weights @ V
```

d_k 是每个头的 key/query 维度。除以平方根是为缓和维度增大时点积分数尺度变化，避免分布过早过尖；它不是把结果变成准确率。

Softmax将分数转换成非负且总和为1的权重。实际实现常先减去最大分数，再计算指数，避免大数溢出；减去同一常数不改变结果。

## 一个能手算的例子

某个Q与两个K的缩放后分数是[2,0]，则权重约[0.8808,0.1192]。若两个V是[10,0]和[0,10]，输出约[8.808,1.192]。模型更多地组合第一个位置的信息，但没有完全抛弃第二个位置。

如果第二个位置在未来，加入掩码后分数为[2,-∞]，权重变成[1,0]，输出为[10,0]。掩码必须在Softmax之前正确作用；把0/1掩码直接乘到分数上会让被屏蔽位置变成0分，仍可能分到权重。

## 因果掩码与padding掩码

因果语言模型预测下个token，训练位置i只能使用位置≤i的信息。所有位置能并行计算，是因为掩码阻止了未来泄漏，而不是因为模型生成时能预知未来。

Padding用于把不同长度序列拼成批次，它不属于真实内容。padding掩码限制对这些位置的关注；损失掩码则限制哪些位置参与训练目标。二者作用不同，通常都需要正确处理。

整行都被设置为负无穷可能导致Softmax未定义或NaN，必须避免无有效key的情况。不同框架的布尔mask语义可能相反，不能仅凭True/False猜含义。

## 多头为何不是多台模型

若隐藏维度C=128，头数H=4，每头维度32。Q/K/V会重排为[B,H,T,32]，各头分别形成[B,H,T,T]的注意力权重，再拼回[B,T,128]并通过输出投影。

头之间参数可学习到不同关系，但不是预设“一个专门语法、一个专门数学”。多头也不是把四份独立LLM的答案投票。

## 复杂度与长文本

朴素完整注意力显式形成T×T矩阵，其相关计算量随T²增长。T翻倍，分数矩阵元素约变成4倍；这只描述注意力部分，整个网络还有投影和前馈层。

FlashAttention等实现减少大中间矩阵的显存读写与显式存储。它们可以显著提高效率，但不能简单解释成“注意力数学上变成线性复杂度”。缓存解码与完整训练也不是同一种计算场景。

## 怎么读nanoGPT代码

从CausalSelfAttention.forward按顺序找：c_attn一次生成Q/K/V；split拆开；view/transpose拆头；is_causal=True或手工三角mask；Softmax；乘V；拼头；c_proj输出。理解每一步形状，比先背模型名称更有价值。

## 常见误区

注意力权重不是可靠的因果解释：权重高不等于该词对最终答案具有唯一决定作用。模型能关注某段文字也不等于理解或核验该段事实。mask写错时训练损失可能看似漂亮，因为模型偷看了答案。

## 练习

运行[数学示例](../expansion-2026-10/examples/ai_math_checks.py)，观察masked attention。在末尾替换一个V：如果它被完全屏蔽，输出应不变。这验证屏蔽机制，而不是验证真实LLM的能力。

## 来源

nanoGPT model.py 的CausalSelfAttention；Transformers缓存文档。固定提交与路径见[来源清单](../expansion-2026-10/SOURCES.md)。下一篇：[Transformer模块](03-blocks-residuals-and-normalization.md)。

核验日期：2026-10-04。对应固定快照：

- [karpathy/nanoGPT / model.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/model.py)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)
