# 03｜神经网络与训练循环：一次训练究竟发生了什么？

> 先修：[张量](01-tensors-shapes-and-devices.md)、[梯度](02-autograd-and-backpropagation.md)。目标：能读懂模型、损失、优化器、batch、epoch 与验证的关系。

## 1. 一个小网络如何处理业务特征？

假设每个地点有三个数值特征：历史客流、面积、周边商户数。暂不讨论这些特征是否足够有效，只用它们解释网络结构。

网络可以是 Linear(3,8) → ReLU → Linear(8,2)。输入 [B,3]，隐藏表示 [B,8]，输出 [B,2]。B 是这一批样本数，两个输出是二分类的原始分数。

第一层学习三个特征的不同组合，ReLU 把负值变成零，第二层把隐藏表示组合成类别分数。隐藏单元不天然等于可解释的业务指标，不能把某个神经元任意命名为“消费力”。

## 2. 多加几个线性层为什么还不够？

若没有非线性，两次仿射变换仍可以合并成一次仿射变换：

z=W₂(W₁x+b₁)+b₂=(W₂W₁)x+(W₂b₁+b₂)。

因此只堆叠线性层，不会获得一般非线性映射的表达能力。ReLU 等激活函数改变这一点。这不意味着非线性模型一定优于简单模型；数据规模、目标和验证结果仍决定选择。

## 3. logits、Softmax、CrossEntropyLoss

logits 是未经归一化的实数分数，不要求在 [0,1]，各类分数也不必相加为 1。Softmax 把一组 logits 转成和为 1 的数值。

例如 logits=[2,0]，第一类 Softmax 值约为 0.8808。此处是模型输出的概率形式，不保证已经校准成真实发生频率。

常见单标签分类中，nn.CrossEntropyLoss 接收 logits 和整型类别索引。它内部包含稳定的 log-softmax 计算，不要先做 Softmax 再把概率当成 logits 传入。

| 任务 | 输出示例 | 常用损失搭配 |
| --- | --- | --- |
| K 类单标签分类 | [B,K] logits，标签 [B] 整数 | CrossEntropyLoss |
| 二分类单个分数 / 多标签分类 | logits 与标签形状一致，标签浮点 | BCEWithLogitsLoss |
| 标量回归 | [B,1]，标签也统一成 [B,1] | MSELoss 等 |

二分类可用两类 logits，也可用一个 logits，关键是标签、输出形状与损失约定一致。多标签不是多分类：前者一条样本可以同时属于多个类别，不能直接要求所有类别概率之和为 1。

## 4. model、loss_fn、optimizer 各自负责什么？

- model：按参数将输入变成输出。
- loss_fn：将输出与标签比较，得到可优化的损失。
- optimizer：管理要更新的参数，依据梯度执行更新。
- DataLoader：组织数据迭代和批次；它不保证样本切分公平。
- 验证指标：回答业务关心的表现，不一定就是训练损失。

CrossEntropyLoss 可以用于训练，而验证还可能同时看 Recall、AP 或人工审核成本。模型只优化损失，不会自动知道哪些错误更昂贵。

## 5. batch、step、epoch

假设训练集 1000 条，batch_size=128，保留最后不足一批的数据：

- 一个 batch 是一次取出的样本。
- 一次遍历产生 8 个 batch，最后一批 104 条。
- 通常每批更新一次，则一个 epoch 有 8 次 optimizer.step。
- 训练 10 个 epoch，通常约 80 次参数更新。

若 drop_last=True，最后不足一批会被丢弃，次数改变；若使用梯度累积，多个微批才更新一次，次数也改变。

增大 batch 不一定只是让模型更快，可能改变内存消耗、梯度噪声和优化表现。学习率也不应在没有验证的情况下机械套用固定比例。

## 6. 一个独立的最小回归示例

下面用已知关系 y=2x+1 生成数据，不下载图片，也不调用外部模型。它演示训练机制，不是生产预测方案：

```python
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader

torch.manual_seed(42)
x_train = torch.linspace(-1, 1, 81).reshape(-1, 1)
y_train = 2 * x_train + 1
x_val = torch.tensor([[-0.85], [-0.25], [0.35], [0.95]])
y_val = 2 * x_val + 1

loader = DataLoader(TensorDataset(x_train, y_train),
                    batch_size=16, shuffle=True)
model = nn.Linear(1, 1)
loss_fn = nn.MSELoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

for epoch in range(100):
    model.train()
    total_loss, seen = 0.0, 0
    for X, y in loader:
        optimizer.zero_grad()
        pred = model(X)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(X)
        seen += len(X)
    if epoch in (0, 99):
        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(x_val), y_val).item()
        print(epoch, total_loss / seen, val_loss)

print(model.weight.detach(), model.bias.detach())
```

weight 应接近 2，bias 接近 1，但本环境没有 PyTorch，以上片段尚未实跑，不承诺具体打印值。完整手工求导的纯 Python 训练版本在 [math_basics.py](examples/math_basics.py)，其训练和验证损失已核对。

这里的验证点也是同一人工构造规律的样本，不能由此推断现实泛化表现。实际业务应参考 [机器学习评估基础](../ml-evaluation/README.md) 决定时间、地点和标签边界。

## 7. 为什么要按样本数累计损失？

假设前一批 128 条，后一批 8 条。如果直接平均两批各自的平均损失，8 条数据与 128 条拥有相同权重，会改变整体统计口径。

默认 mean reduction 下，样本级损失结构一致时，可以将每批平均损失乘以样本数后累计，再除以总样本数。若任务有变长序列、忽略标签、类别权重等设置，要先确认 loss 的实际分母：有时应按有效 token 数或其他权重汇总，不能机械乘 batch_size。

上例训练损失是在一个 epoch 中不同参数状态下累计的；验证损失则使用该 epoch 结束时的固定模型。两者不完全是同一测量条件。

## 8. loss 降了但验证变差怎么办？

训练损失越来越小，验证损失先下降后上升，可能是过拟合。可检查数据切分、标签噪声、模型复杂度、正则化与早停。不能直接把训练轮次增加到分数变好。

训练和验证都不好，可能是欠拟合，也可能有特征尺度、学习率、实现或标签问题。先与简单基线比较，核对一小批样本是否能学到，再决定是否加大模型。

使用验证集选最佳 epoch，是合法的模型选择；最终测试集应保持独立。官方入门示例里的 test_loop 名字不代表反复用于挑选方案的数据仍是严格意义上的最终测试集。

## 9. 保存最佳模型的常见误区

保存“最后一轮”不一定保存了验证最佳的一轮。如果根据验证指标选择 checkpoint，要记录选择规则，并用选出的方案进行最终测试。

工程补充：只保存权重不足以保证能复现预测，还需要模型结构、特征预处理、类别映射与版本信息。恢复训练通常还需要优化器等状态。此篇不提供未经核验的持久化 API 实现，后续可专题展开。

## 10. 练习与答案

1. backward 会直接让 loss 变小吗？  
   答：它只计算梯度。更新在 step 中发生，而且一次更新也不保证所有数据上的 loss 都下降。

2. 对单标签分类先 Softmax，再传 CrossEntropyLoss 合理吗？  
   答：常规 logits 用法不合理，应让损失接收原始分数。

3. 1000 条数据，每批 128 条，一个 epoch 是否 1000 次更新？  
   答：通常是 8 次，不是每条更新一次；累积或丢弃尾批设置还会改变次数。

4. 已有 99% 训练准确率，为何还需测试？  
   答：训练集参与了学习，只能说明训练表现。新样本、未来时间和新地点可能不同。
 
## 来源与验证边界

核验日期：2026-10-04。固定来源提交：`11512db7cbbcc4b530ecfc63205d3fed13fa190d`。

- [官方网络构建教程](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/buildmodel_tutorial.py)
- [官方优化教程](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/optimization_tutorial.py)
- [BCEWithLogitsLoss 官方源码与文档](https://github.com/pytorch/pytorch/blob/e188cec401c09c3a41b9fa40d58724c3fd28d06f/torch/nn/modules/loss.py)，补充核验二分类/多标签损失的输入约定。
- [官方自动求导教程](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/autogradqs_tutorial.py)

中文解释、业务场景和合成数据代码独立编写。二分类/多标签搭配、统计口径、验证协议与保存建议属于工程扩展，不声称是上述教程逐条原文。来源仓库采用 [BSD 3-Clause](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/LICENSE)。PyTorch 片段未实跑，纯 Python 数学示例已实跑。
