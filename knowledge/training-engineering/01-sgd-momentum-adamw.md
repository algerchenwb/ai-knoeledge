# 优化器：SGD、Momentum、Adam 与 AdamW

## 梯度告诉方向，优化器决定怎么走

梯度是损失对参数的局部变化率；优化器用它及历史状态决定下一次参数更新。可以把梯度理解为当前坡度，把学习率理解为步幅，把动量理解为保留过去移动趋势。但损失面是高维且随抽样变化的，不能将比喻当作一定找到全局最优的保证。

最基本的梯度下降写成w_new=w-lr×g。SGD通常使用抽样batch估计梯度，减少每步成本，同时引入抽样噪声。全批量、随机单样本和小批量更新需要明确区分。

## SGD手算

设L(w)=(w-3)²，梯度g=2(w-3)。从w=0、lr=0.1开始，g=-6，新w=0.6，损失从9下降到5.76。若lr=1.1，同一初值会得到w=6.6，损失变成12.96，已经越过目标且更差。

梯度计算正确不等于学习率正确。这个凸二次例子也不能直接给出深度网络的通用学习率。

## Momentum保留历史方向

采用无dampening、无Nesterov的教学约定：

```text
v_t = μ * v_(t-1) + g_t
w_t = w_(t-1) - lr * v_t
```

μ控制历史保留。持续一致的梯度会累积，来回变化的部分可能被缓和。它有助某些任务中的优化，但在陡峭区域也可能冲过目标。

PyTorch SGD对首次动量buffer、dampening和Nesterov有明确实现；另一种把(1-μ)乘在梯度上的教材约定不是同一数值公式。比较代码前必须先对齐约定。

## Adam维护两类统计

Adam用梯度的一阶与二阶滑动统计：

```text
m_t = β1*m_(t-1) + (1-β1)*g_t
v_t = β2*v_(t-1) + (1-β2)*g_t²
m_hat = m_t / (1-β1^t)
v_hat = v_t / (1-β2^t)
w_t = w_(t-1) - lr*m_hat/(sqrt(v_hat)+ε)
```

从零初始化时做偏差校正。二阶项帮助调整不同参数的更新尺度，ε用于数值稳定。它不等于Hessian，不是精确二阶优化方法。

如果第一次梯度g=2、β1=0.9、β2=0.999，则m=0.2、v=0.004；校正后分别为2和4，忽略ε，更新大小约等于lr。后续梯度变化时则不能简单理解成每步只取梯度符号。

## AdamW为什么要分开权重衰减

给损失增加L2项会产生额外梯度λw。在普通SGD、对应系数约定下，它与乘法权重衰减有关；在Adam中，这部分会进入动量和二阶统计，因此不再等价于独立收缩权重。

AdamW将衰减与自适应梯度更新分离。简式为w←(1-lr×λ)w，再按Adam统计更新。w=10、lr=0.1、λ=0.01、有效梯度为0时，衰减后w=9.99。

有效零梯度与grad=None还要区分：某些实现会跳过没有梯度的参数，不能据此说所有未参与计算的权重都自动衰减。参数组可以为bias/norm等设置不同规则，具体是否排除要按实验设计决定。

## 优化器状态也占内存

SGD无动量状态较少；Momentum需要buffer；Adam通常存一阶与二阶统计。状态dtype、参数副本、分片和具体实现改变内存预算，不能统一宣称“Adam永远固定占几倍权重”。

恢复训练必须保存状态，否则即使w相同，下一步也可能不同。调学习率、换优化器与继续同一训练过程是不同实验。

## 怎么选择与诊断

先建立可靠基线，固定数据与验证集，再比较验证指标、达到目标所需计算量及稳定性。AdamW不是所有任务必胜，SGD也不是天然更泛化。loss异常时先看输入、梯度、学习率与有效监督数量，不要直接把优化器当唯一原因。

## 练习

运行[训练数学实验](examples/training_math_checks.py)，核对一次SGD、动量状态与Adam偏差校正。想一想：只加载参数、不加载momentum，会不会保持后续轨迹？下一篇的恢复实验会给出具体反例。

## 来源

PyTorch的sgd.py、adam.py、adamw.py；具体快照链接见本文末尾与[来源清单](SOURCES.md)。数学例子与选择方法独立编写，未运行PyTorch优化器集成。

核验日期：2026-10-04。固定来源：

- [pytorch/pytorch / torch/optim/sgd.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/sgd.py)
- [pytorch/pytorch / torch/optim/adam.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/adam.py)
- [pytorch/pytorch / torch/optim/adamw.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/adamw.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
