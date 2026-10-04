# 深度学习训练基础

基于 PyTorch 官方开源教程的独立中文知识整理。先理解数字如何组织，再理解梯度如何计算，最后读懂完整训练循环。

## 已完成内容

| 顺序 | 教程 | 核心问题 |
| --- | --- | --- |
| 1 | [张量、形状与设备](01-tensors-shapes-and-devices.md) | batch 轴、dtype/device、矩阵乘法、广播、共享内存 |
| 2 | [梯度与自动求导](02-autograd-and-backpropagation.md) | 链式法则、backward/step、梯度累加、eval/no_grad |
| 3 | [网络与训练循环](03-networks-and-training-loops.md) | 线性层、非线性、logits、损失、batch/epoch、验证 |
| 示例 | [纯 Python 数学演示](examples/math_basics.py) | 矩阵运算、有限差分、一次参数更新、全批量训练 |

建议先理解 [评估基础](../ml-evaluation/README.md) 中的数据泄漏和验证原则。能把训练损失降下来，不等于已证明上线表现。

## 来源记录

核验日期：2026-10-04。主要来源 [pytorch/tutorials](https://github.com/pytorch/tutorials)，固定提交 `11512db7cbbcc4b530ecfc63205d3fed13fa190d`。

来源文件位于 beginner_source/basics：
tensorqs_tutorial.py、autogradqs_tutorial.py、buildmodel_tutorial.py、optimization_tutorial.py。每篇末尾保留固定链接。

补充核验 [pytorch/pytorch 的损失实现](https://github.com/pytorch/pytorch/blob/e188cec401c09c3a41b9fa40d58724c3fd28d06f/torch/nn/modules/loss.py)，提交 `e188cec401c09c3a41b9fa40d58724c3fd28d06f`，用于二分类/多标签损失约定。

教程来源采用 [BSD 3-Clause](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/LICENSE)，Copyright (c) 2017-2022, Pytorch contributors。本知识库未整段搬运源文档；中文解释、业务例子和演示代码独立编写。此整理与 PyTorch 官方没有隶属关系。

## 验证记录与限制

当前环境未安装 PyTorch，文中的 PyTorch 代码没有实跑。所有文件清楚标注此限制。

纯 Python 示例已执行并通过数学断言：

- A*B=[[5,12],[21,32]]，A@B=[[19,22],[43,50]]。
- 解析梯度 dw=-12，与有限差分约 -12.00000000008 一致。
- 手算更新得到 w=2.2、b≈0.6，单样本损失为零。
- Softmax([2,0]) 第一类值约 0.880797。
- 对人工关系 y=2x+1，全批量训练得到 w≈1.99999858、b≈1，训练与验证 MSE 均小于 1e-10。

这些断言仅验证数学示例，不替代 PyTorch 集成运行或真实业务效果验证。纯 Python 演示使用全批量更新，与文中的 PyTorch 微批训练不是逐步数值等价。

运行数学演示：

```bash
python knowledge/deep-learning-basics/examples/math_basics.py
```

## 后续已补充

- [训练工程8篇](../training-engineering/README.md)：Dataset/DataLoader、优化器、学习率、梯度累积、AMP、checkpoint恢复、DDP与训练排障。
- [Transformer内部机制](../transformer/README.md)：Embedding、注意力、残差、训练目标与解码。

## 尚待扩展

深度学习中的正则化与早停专项实验，以及真实PyTorch/GPU训练集成。未完成的主题不作为已完成教程计数。

[返回总入口](../../README.md)
