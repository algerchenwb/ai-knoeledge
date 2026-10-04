# Transformer Block：残差、归一化与前馈网络

## 把一层理解成两种处理

Attention在不同位置之间交换信息；前馈网络通常在每个位置上分别做非线性变换。同一组前馈权重应用到所有位置，但各位置输入不同，因此输出不同。前馈层不是查询数据库，也不是预先写好的知识规则。

nanoGPT的Block采用常见pre-norm结构：

```text
x = x + Attention(LayerNorm(x))
x = x + MLP(LayerNorm(x))
```

每个加号是残差连接。模型既保留原有表示，又学习增量变化。深层网络不必每层完全重写所有信息，也为梯度提供较直接的传播路径。这有助训练，不保证任意加深都不会出现问题。

## LayerNorm到底归一化什么

对某个token的D个特征，计算均值μ和方差σ²：

```text
z_j = (x_j - μ) / sqrt(σ² + ε)
y_j = γ_j * z_j + β_j
```

γ和β是可学习参数，ε防止数值不稳定。它通常沿特征维归一化，不是把同一批全部token混在一起求均值。对于[1,3]，μ=2、方差=1，忽略ε时得到[-1,1]；γ/β会再调整结果。

LayerNorm与BatchNorm不能随意互换：归一化轴和训练/推理统计行为不同。许多新模型使用RMSNorm等其他机制，不能因为都叫“norm”就认为完全相同。

## 前馈层为什么先扩大再缩小

nanoGPT的MLP将C维变成4C维，经过GELU，再投影回C维。这提供更大的中间非线性表示空间。只连续做线性变换而没有非线性，整体仍可合并为一个线性变换，表达能力受到限制。

例如C=128时，两层权重约有128×512+512×128=131072个参数，暂不计bias。它们返回同样的C维，所以能够和原输入相加。扩展倍数是架构选择，不是所有Transformer都必须等于4。

门控前馈层、稀疏MoE是进一步变化。MoE可让每个token只激活部分专家，但需要路由、负载平衡与分布式通信；“总参数很多但激活少”不等于服务成本必然低，也不能凭总参数直接估计单请求速度。

## Dropout与推理

Dropout训练时随机屏蔽部分激活以起到正则化作用，标准实现会做相应缩放。常规推理应关闭随机dropout。eval()改变某些层的行为，no_grad()限制梯度记录，两者目的不同。

nanoGPT在attention实现中根据training状态选择dropout_p。只给模型包上no_grad()却没有切到eval()，可能仍保留训练行为；具体取决于使用的模块。

## 一条token如何走完整网络

它从embedding进入多个Block，在注意力中读取上下文，在MLP中转换自身表示，通过残差累计更新；最后做归一化和词表投影。每层参数不同，不能把层数理解成同一算法重复查同一个表。

训练时还保留反向传播需要的信息。推理只前向，但可能储存KV缓存。所以参数量、激活量与缓存量必须分别统计。

## 故障定位

若出现NaN，按输入dtype和数值范围、mask有效性、学习率、梯度尺度、混合精度顺序排查。盲目加更多norm不一定解决根因。若维度报错，先检查残差两端形状是否一致，以及拆头时C能否被H整除。

## 练习与答案方向

为什么残差不能随便把128维与256维直接相加？形状不匹配，需要投影或改变设计。关闭梯度是否自动关闭dropout？不会。MLP按位置计算是否代表模型没有上下文？不会，MLP输入已可包含attention组合的上下文。

## 来源

nanoGPT model.py的LayerNorm、MLP、Block、GPT.forward；固定链接见[来源清单](../expansion-2026-10/SOURCES.md)。MoE和RMSNorm仅为概念拓展，不作为本代码实现能力的声明。

核验日期：2026-10-04。对应固定快照：

- [karpathy/nanoGPT / model.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/model.py)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)
