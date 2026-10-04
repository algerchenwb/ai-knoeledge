# 学习率：Warmup、余弦退火与更新次数

## 一个参数，控制整个训练节奏

学习率决定梯度或优化器方向转换成多大步幅。太小可能进展慢，太大可能震荡、损失发散或出现数值异常。它不是准确率旋钮，也不能独立于batch、优化器与训练目标选择。

优化器自适应并不代表不需要调学习率。Adam仍有全局lr，各参数还有基于历史统计的有效尺度。

## Warmup的目的

训练初期统计和表示尚不稳定，直接使用较大学习率可能带来猛烈更新。Warmup让学习率从较小值逐渐上升，使训练更平稳；是否需要及长度是多少必须由任务验证。

教学用0-based更新编号u，前W次更新可设置lr(u)=peak×(u+1)/W。W=4、peak=0.1时，前四次为0.025、0.05、0.075、0.1。这里没有0学习率的第一步。

nanoGPT固定快照的get_lr使用不同边界约定，warmup分母为warmup_iters+1；不要把本文教学函数当作与源码逐步数值等价。阅读scheduler必须明确编号从0还是1开始。

## 余弦退火

峰值之后，用进度p∈[0,1]平滑下降：

```text
lr = floor + 0.5*(1+cos(π*p))*(peak-floor)
```

p=0时是peak，p=1时是floor；中点p=0.5时是两者平均。floor通常避免下降到完全停止，但它不是必要固定设置。余弦方案也有重启、不同周期等变体。

Linear decay按直线下降，Step decay在指定点乘系数，Reduce-on-plateau依验证指标调整。每种都需要明确触发频率；按epoch调用与按optimizer update调用可能完全不同。

## Batch step与optimizer step不能混用

有100个micro-batch、每5个累积一次，完整累积窗口产生20次参数更新。若scheduler本应按更新调用，却每读一个batch调用一次，衰减会快5倍。

如果epoch末尾还有不足5个的窗口，需要明确处理：更新、丢弃还是跨epoch继续累积；实际更新次数据此变化。总步数计算不能仅用整数除法而忽略尾部。

AMP遇到溢出时可能跳过optimizer更新。如果scheduler仍照常前进，参数与学习率计划会错位。框架封装可能处理这个问题，但手写循环必须核对。

## 常见调用顺序

许多PyTorch scheduler通常在optimizer.step之后调用；有些指标驱动scheduler还需要传入验证值。初始学习率、首次调用和框架封装决定实际序列，应记录“本次真正用于更新的lr”，不要只打印更新后的下一步lr。

不能用一段通用代码概括所有scheduler与训练框架的顺序。恢复训练时也需同时还原scheduler状态及global update编号。

## Batch变大要同比放大学习率吗

线性缩放等规则在一些训练设置中有效，但属于条件性经验。调整batch会改变噪声、每epoch更新次数与token预算；有动量、自适应统计或不同训练目标时，简单同比放大可能不稳定。

比较时至少对齐有效batch、有效token、总更新数、总数据量和评估方式。相同epoch数不意味着相同优化轨迹或计算成本。

## 业务实验记录

微调API参数任务时，保存base revision、optimizer配置、peak/floor、warmup更新数、总更新数、batch/accumulation、有效token和验证结果。一次成功的0.0001不能当成其他模型的默认答案。

## 练习

运行数学实验检查warmup/余弦的边界和中点。假设101个micro-batch、每5个更新且尾部也更新，一共21次；若只完整窗口更新则20次。先决定训练语义，再配置scheduler。

## 来源

nanoGPT train.py/get_lr核对warmup与余弦实现；Accelerate梯度累积文档核对更新边界。公式示例与计数例子独立编写，未测试真实模型最优学习率。

核验日期：2026-10-04。固定来源：

- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)
- [huggingface/accelerate / docs/source/usage_guides/gradient_accumulation.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/gradient_accumulation.md)

[专题入口](README.md) · [验证记录](VALIDATION.md)
