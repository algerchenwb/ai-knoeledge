# 混合精度、梯度缩放与裁剪：三种不同的操作

## 少一点精度，换取一定资源收益

混合精度让不同算子使用适合的dtype：某些矩阵乘法用较低精度获得效率，某些归约或敏感计算保持较高精度。不是把整个训练所有数字都粗暴变成FP16。

PyTorch autocast按算子和设备选择计算类型，实际规则随版本与硬件变化。模型参数、optimizer状态、输入和算子输出也未必使用同一dtype。

## FP16与BF16

两者都占16bit，但指数与尾数分配不同。FP16指数范围较小，更容易出现很小梯度下溢或大数溢出；BF16有接近FP32的指数范围，但尾数更短。BF16仍有舍入误差，也不保证任意计算稳定。

对简单二进制半精度表示，1e-8可能舍入为0，而乘1024后约1.024e-5可被表示。数学示例使用Python的half格式演示；真实GPU还可能有不同的次正规数处理路径，不能据此保证所有kernel结果一致。

## GradScaler缩放梯度

把loss乘以scale S再backward，梯度也乘S，减少小值在FP16路径下过早变成0的机会。更新前需除回S。它不增加原始信息精度，也不能修复loss定义错误、无效标签或爆炸的输入。

动态scaler会检查非有限梯度，必要时跳过optimizer更新并调整scale。通常BF16训练较少需要这种梯度缩放，但仍需按实际配置判断。

## 标准AMP步骤

下列是单窗口的机制顺序，非完整可直接运行程序：

```text
在autocast下forward与loss
scale(loss).backward()
完成本窗口所有micro-batch累积
unscale(optimizer)
对真实梯度做检查/clip
scaler.step(optimizer)
scaler.update()
窗口边界zero_grad
```

Backward通常不需要再包在autocast中。梯度累积期间保持同一窗口缩放方式，并在更新边界反缩放；不要每个micro-batch随意更换scale或反复unscale。

如果已经调用unscale，scaler.step会按自身状态避免重复反缩放，具体以实现为准。恢复时GradScaler状态也应保存。

## 梯度裁剪为什么不是逐项截断

全局范数裁剪先计算所有参与梯度的总范数，再统一按系数缩小。g=[3,4]的L2范数为5，阈值1，则结果约[0.6,0.8]，方向保持、长度变成1。

按值裁剪把每项限制到区间，例如[-1,1]，会得到[1,1]，方向不同。两种方法不是一个参数的不同叫法。

分布式分片或模型并行下，全局范数可能需要跨分片统计，不能用单卡局部norm冒充完整模型norm。

## 为什么必须先unscale再clip

若S=100，真实g=[3,4]被保存为[300,400]。直接按阈值1裁剪得到[0.6,0.8]，随后再除100就变成[0.006,0.008]，比希望的[0.6,0.8]小100倍。

梯度缩放解决表示范围，裁剪限制更新方向的幅度，学习率决定优化器步幅；三者分别有职责，不能互相替代。

## 遇到NaN怎么查

从数据与标签开始，检查loss是否有限、分母是否为0、mask是否导致全屏蔽、log/除法输入是否合法，再看激活与梯度。必要时缩小任务，用FP32对照，定位首个非有限点。

降低scale只可能帮助缩放造成的溢出；输入本身含NaN，或attention mask逻辑错，scaler无法修好。频繁跳步应统计而不是悄悄忽略；scheduler要避免在没有更新时错误前进。

## 练习

运行数学示例比较正确与错误裁剪顺序，并用half舍入观察梯度缩放。示例没有GPU、autocast或GradScaler实例，不能作为真实混合精度稳定性验收。

## 来源

PyTorch AMP recipe与nanoGPT训练循环核对autocast、scale/unscale/clip/step顺序。数值反例与故障定位独立编写。

核验日期：2026-10-04。固定来源：

- [pytorch/tutorials / recipes_source/recipes/amp_recipe.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/recipes_source/recipes/amp_recipe.py)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
