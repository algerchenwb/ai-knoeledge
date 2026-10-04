# 语言模型的训练目标：标签右移、交叉熵与困惑度

## 不是让模型直接背完整答案的分数

自回归语言模型把序列概率拆成逐位置的条件概率。训练时给出正确前缀，让模型预测下一个token；各位置可以通过因果掩码并行计算。推理时没有完整正确答案，只能接着自己已经生成的内容继续预测。

这类训练使用teacher forcing：模型学习的上下文包含真实历史token，而不是每步都使用自己采样的错误。训练与真实生成的输入分布因此可能有差异。

## 标签对齐例子

原始序列是[甲,去,北京,EOS]：

| 输入位置 | 可见前缀 | 目标 |
| --- | --- | --- |
| 0 | 甲 | 去 |
| 1 | 甲 去 | 北京 |
| 2 | 甲 去 北京 | EOS |

若把目标设为当前token而不是下一个，模型可能学成复述输入。不同库可能在collator、model或trainer内部完成右移，必须核对一次，不能漏移也不能移两次。nanoGPT的get_batch直接构造错开一位的x/y。

## 从logits到损失

logits是每个候选token的原始分数，Softmax得到概率p。正确token是y时，单位置交叉熵是-log(p_y)。真实训练通常用数值稳定的log-softmax，不先手工做Softmax再喂给期望logits的CrossEntropyLoss。

正确token概率为0.8，损失约0.2231；概率为0.2，损失约1.6094。惩罚更大的错误概率，让模型通过梯度提高训练目标的相对分数。但训练只见到某个续写，不代表其他合理续写都语义错误。

## 不是所有位置都应该参与损失

Padding一般要被忽略。SFT任务还可能只在assistant回答位置计算损失；system/user内容可作为上下文，却不必作为要模仿的输出目标。

把prompt损失关掉不等于模型看不到prompt。损失mask控制监督范围，attention mask控制信息可见性。答案被截断、EOS丢失、模板角色混乱都可能改变训练目标。

## 困惑度是什么

若用自然对数、在有效token上计算平均负对数似然L，则perplexity=exp(L)。它可理解成平均预测不确定性的指数刻度。概率都为0.5时，L=log(2)，困惑度为2。

跨批次汇总时应按有效token数加权：某批10个有效token，另一批1000个，不宜把两个批次平均loss等权平均。不同tokenizer、数据切分、loss mask和语料下的困惑度不宜直接横向比较。

困惑度低不等于事实正确、工具执行成功或回答对用户有用。它评价给定文本的预测能力，任务仍需自己的验收指标。

## 训练下降、验证变差说明什么

可能过拟合、样本重复或分布不一致。先检查训练/验证分割是否泄漏，尤其同一文档切片或近重复问答是否跨集合。每次调参都盯着测试集会逐渐把测试集变成开发集。

## 业务例子

对于API参数生成，语言损失之外还应测Schema通过率、正确接口选择、枚举合法性、缺参处理、授权拒绝和真实执行结果。一个token写错导致接口失败，不能因为整段平均损失较低就忽略。

## 练习

运行数学示例，核对交叉熵和困惑度。再设计一条只有prompt、没有assistant回答的样本：若采用assistant-only loss，应检查有效监督token数，避免零分母或把它当作正常训练样本。

## 来源

nanoGPT train.py/get_batch与model.py/GPT.forward；TRL SFT文档的label shifting/masking。见[来源清单](../expansion-2026-10/SOURCES.md)。关联：[原有评估基础](../ml-evaluation/README.md)。

核验日期：2026-10-04。对应固定快照：

- [karpathy/nanoGPT / model.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/model.py)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)
