# 02｜梯度、反向传播与自动求导

> 目标：知道 backward 计算什么、step 修改什么，并能手算一次参数更新。

## 1. 模型为什么会学习？

考虑最简单模型：预测值 ŷ=w×x+b。w 决定输入对输出的影响，b 是偏置。开始时它们通常不是正确答案，需要根据数据不断调整。

定义一个样本的平方损失 L=(ŷ−y)²：预测与真实值越远，损失越大。训练的目标是找到使训练损失较小的参数；这不保证在新数据上一定更好，需要独立验证。

梯度告诉我们：在当前位置，轻微增加某参数会使损失怎样变化。它不是“正确参数值”，而是局部变化率。

## 2. 从一组数字手算

取 x=2、y=5、w=1、b=0：

- 预测 ŷ=1×2+0=2。
- 误差 e=2−5=−3。
- 损失 L=(−3)²=9。
- 对 w 的梯度为 2×e×x=−12。
- 对 b 的梯度为 2×e=−6。

梯度下降更新为：参数新值=参数旧值−学习率×梯度。学习率 η=0.1 时：

- w 从 1 变成 2.2。
- b 从 0 变成 0.6。
- 新预测 2.2×2+0.6=5，损失恰好为 0。

这组数字特意便于手算，一步归零不是一般训练现象。梯度也受损失定义影响：如果使用 L=0.5×(ŷ−y)²，梯度会减半。

## 3. 链式法则为什么能训练多层网络？

损失先依赖预测，预测再依赖参数：

∂L/∂w = (∂L/∂ŷ) × (∂ŷ/∂w)。

多层网络包含更多中间步骤，链式法则沿着计算路径组合各步导数。若一个参数通过多条路径影响最终损失，各条路径的贡献会相加。

反向传播是在计算图上有效组织这些导数计算的方法。它与梯度下降不是同一件事：反向传播算梯度，优化器利用梯度更新参数。

## 4. PyTorch 分别负责什么？

```python
import torch

w = torch.tensor(1.0, requires_grad=True)
b = torch.tensor(0.0, requires_grad=True)
x = torch.tensor(2.0)
y = torch.tensor(5.0)

pred = w * x + b
loss = (pred - y).square()
loss.backward()

print(loss.item(), w.grad.item(), b.grad.item())  # 9, -12, -6
optimizer = torch.optim.SGD([w, b], lr=0.1)
optimizer.step()
print(w.item(), b.item())  # 约 2.2, 0.6
```

requires_grad=True 表示希望追踪此张量相关的求导计算。前向运算产生预测和损失，也建立可求导操作之间的关系。loss.backward() 计算梯度，通常把叶子参数的梯度累加到 .grad。optimizer.step() 才会修改参数。

输入 x 不需要学习，因此没有必要为了训练参数把所有输入都设成 requires_grad=True。某些研究任务要计算输入梯度，但那是另一个明确目的。

## 5. 为什么每次要 zero_grad？

PyTorch 默认累加梯度。假设两次独立前向计算都产生同样的 w 梯度 −12，如果中间没有清理，w.grad 就可能变为 −24，而不是被覆盖成 −12。

常用顺序：

```python
optimizer.zero_grad()
pred = model(X)
loss = loss_fn(pred, y)
loss.backward()
optimizer.step()
```

梯度累积也可有意用于分多个微批处理较大有效批量。但要正确缩放损失、处理最后不足一组的微批，以及理解 BatchNorm 等行为不一定等价。不能仅凭“不清梯度”就说实现了正确的大批训练。

zero_grad 可能将 .grad 设为 None，而不是一个全零数组，具体取决于版本和选项。教学中“清梯度”描述的是功能，排错时不要要求所有 .grad 都必须显示零。

## 6. 为什么 loss.item() 不能继续反传？

loss 是带有求导关系的张量。loss.item() 得到 Python 数字，适合日志，却不保留用于反向传播的计算图。

错误思路是把所有预测变成 Python 列表，再用普通函数拼成损失，最后希望 backward 自动追踪。框架只追踪支持的张量运算，不能凭空推断普通 Python 数字如何依赖参数。

同样，detach() 会断开求导关系。应该明确区分“仅记录结果”和“参与损失计算”的数据路径。

## 7. eval 与 no_grad 不是一回事

| 操作 | 主要作用 | 不会自动做什么 |
| --- | --- | --- |
| model.eval() | 将模块切到评估模式，影响 Dropout/BatchNorm 等 | 不自动关闭梯度追踪 |
| torch.no_grad() | 在上下文中停止记录求导历史 | 不自动把模块切到评估模式 |
| tensor.detach() | 得到与该求导关系分离的张量 | 不保证复制存储 |
| optimizer.zero_grad() | 清理已有参数梯度 | 不计算新梯度，也不更新参数 |

常规验证通常需要 model.eval() 与 no_grad() 配合。之后继续训练，要重新 model.train()。

冻结参数与关闭整个前向求导也不能无条件等同：如果希望通过一个冻结层向它前面的可训练层传播梯度，把整个冻结层前向放进 no_grad 可能断开必要路径。

## 8. 同一图能 backward 两次吗？

常见训练中每次重新执行前向，建立新图，再做一次反传。反传后，为梯度计算保存的许多中间数据会释放。

需要对同一图再次反传时，某些场景要 retain_graph=True。它不是修复所有 backward 报错的通用按钮；保留大量图会增加内存占用。先检查是否应该重新前向，是否意外缓存了带梯度的旧损失。

中间结果默认通常不会填充 .grad。需要查看非叶子张量梯度时可使用 retain_grad；“它的 .grad 是 None”不等于梯度无法通过它传播。

## 9. 数值差分能核对梯度吗？

可以用中心差分近似：g≈[L(w+h)−L(w−h)]/(2h)。它不需要符号推导，但每个参数都要重复计算，训练大模型非常昂贵，主要用于小规模检查。

h 过大会有近似误差，过小会受浮点误差影响。它帮助核对自动求导，不是高效替代方案。配套 [纯 Python 演示](examples/math_basics.py) 使用此方法核对上例 w 梯度。

## 10. 练习与答案

1. backward 后参数没变化，是否说明框架故障？  
   答：不一定，可能只算了梯度，没有 step；也要检查参数是否被优化器管理。

2. 学习率从 0.1 改成 1 是否一定学得更快？  
   答：不一定，可能跨过低损失区域，震荡或发散。

3. eval 是否让所有参数的 requires_grad 变成 False？  
   答：不是，它改变模块模式，不自动禁用自动求导。

4. loss 下降是否证明模型记住了正确业务规律？  
   答：不是，还需检查验证表现、泄漏和业务指标。

## 来源与验证边界

核验日期：2026-10-04。固定来源提交：`11512db7cbbcc4b530ecfc63205d3fed13fa190d`。

- [PyTorch 官方开源教程：autogradqs_tutorial.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/autogradqs_tutorial.py)
- [PyTorch 官方开源教程：optimization_tutorial.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/optimization_tutorial.py)

本篇为独立中文整理，例子、业务类比和练习自行编写，并非官方逐字翻译。来源仓库采用 [BSD 3-Clause](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/LICENSE)。当前执行环境未安装 PyTorch，因此本篇 PyTorch 片段未实跑；相关手算结果通过配套纯 Python 示例核对。实际 API 行为以安装版本为准。
