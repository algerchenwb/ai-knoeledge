# 梯度累积：有效batch、尾窗口与token归一化

## 显存只能装两条，也可以累计更多条的梯度

若目标batch为8，而每次只能处理2条，可连续做4次forward/backward，把梯度累加，再更新一次参数。每个micro-batch后释放不再需要的计算图，避免同时保留8条的全部激活。

梯度本身仍要保存，基础权重与optimizer状态也没有消失。累积可以降低一次forward的激活规模，但不能解决模型参数本身放不下的问题。

## 等大小mean loss的简式

若每个micro-batch均有相同有效样本数，各自使用mean loss，目标是整个窗口的平均loss，可将每份loss除以累积次数K再backward，累积后step一次。

窗口内参数必须不更新，zero_grad只能在窗口边界；若每次backward后立即step，得到的是多次小batch更新，不是一次大batch更新。

有效batch近似=每设备micro-batch×累积次数×数据并行rank数。这描述等大小样本batch，语言模型通常还要跟踪有效token数量。

## 不等长token最容易算错

考虑两个micro-batch：第一份有2个监督token，每token梯度均为1；第二份有8个监督token，每token梯度均为3。

整体token平均梯度=(2×1+8×3)/10=2.6。若先分别求均值再除以2，得到(1+3)/2=2，是另一个目标。

正确方式应基于整个更新窗口的总有效loss和总有效token：L_total=Σloss_sum/Σvalid_tokens。padding和被mask掉的prompt不能进入分母。Accelerate文档专门讨论了这类错误。

## 怎么知道整个窗口分母

可先收集当前窗口micro-batch的有效token数，再对每份sum loss除以全窗口分母；或采用经验证的框架机制。这样收集输入或token计数，不代表必须保留所有batch的计算图。

如果自己额外除以K，而框架的backward已经做了累积归一化，就会重复缩小梯度。使用Accelerate等封装时需核对它自动处理哪些部分，不能机械混用手写循环。

## 最后不足K份怎么处理

例如计划每4份更新，epoch末尾只剩2份。可明确用这2份的实际分母完成更新，或丢弃，或跨epoch累积。若用等大小mean loss但仍除以4，最后更新梯度会缩小一半。

按有效token归一化时，分母应使用该实际窗口。对应scheduler也要按实际optimizer更新推进。零有效监督token的窗口应明确跳过或报错，不应除以0。

## DDP加一层平均

普通DDP会在rank间平均梯度。若各rank有效token不同，直接平均每rank的mean loss仍会偏。教学上若使用各rank的loss_sum/N_global，再被DDP平均，就少一个world_size因子；需相应调整，或使用已验证的框架路径。

当某个框架又自动除以K时，还要考虑该层缩放。这里说明机制，不提供可以任意套用到所有框架的通用乘法口诀。

## no_sync与数值差异

非最终micro-step可以暂缓同步，最终统一同步以减少通信。PyTorch通常使用no_sync上下文，并应让相关forward处于该上下文中。rank之间更新边界必须一致。

累积与一次大batch并非任意模型都逐字节等价：BatchNorm统计、dropout随机路径、浮点求和次序和batch相关目标都会影响结果。线性可加loss、固定参数等条件下才便于建立等价演示。

## 练习

运行数学示例对比2与2.6，模拟两rank有效token不等，再验证尾窗口。学习率不变却效果突然变差时，检查归一化分母常比增加训练轮数更有价值。

## 来源

Accelerate gradient_accumulation.md的可变长度token段落，以及nanoGPT训练循环。本文手算与反例独立编写，没有实跑Accelerate/DDP集成。

核验日期：2026-10-04。固定来源：

- [huggingface/accelerate / docs/source/usage_guides/gradient_accumulation.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/gradient_accumulation.md)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
