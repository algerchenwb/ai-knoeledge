# 训练排障：显存、激活重计算、性能测量与可复现记录

## OOM先看在哪个阶段

加载时OOM多与权重和加载副本有关；forward可能与激活、序列长度和临时算子有关；backward涉及梯度和保存信息；第一次optimizer.step可能新建状态，显存突然上涨。

这些只是定位线索，不是绝对诊断。记录阶段、张量形状、有效token和峰值，再决定减batch、改dtype、减少激活还是分片。

## 训练内存是多项之和

```text
权重 + 梯度 + optimizer状态 + 保存的激活
+ 临时工作区 + 运行时/通信开销
```

还有CPU端数据、预取队列和文件缓存。显存不足与进程CPU内存不足是不同问题；容器OOMKilled也不自动代表GPU显存满。

参数量固定，但长序列、batch和中间表示改变激活规模。某些attention实现避免显式保存大矩阵，因此不能只用T²推断全部真实显存。

## 意外保留计算图

把每步loss tensor或outputs直接追加到长期列表，可能保留本应释放的图或GPU数据。若只需要日志数字，使用合适的标量读取或detach并转CPU；但loss.item也可能触发CPU/GPU同步，频繁调用影响吞吐。

detach只解除梯度关系，不自动把GPU数据移走。若仍保存大量detach后的GPU张量，显存仍会增长。缓存与日志都要明确生命周期和容量。

## 激活checkpoint与训练checkpoint不同

训练checkpoint把状态持久保存以便恢复；activation checkpointing减少forward保存的中间激活，backward时重新计算部分前向，以额外计算换内存。

它不能让optimizer状态消失，也不一定解决参数放不下。重算区域的随机操作与副作用会影响一致性。PyTorch checkpoint提供相关RNG处理，但多设备、设备迁移和全局状态需要核对限制。

use_reentrant不同实现有不同限制，应显式选择并按版本验证。若重算时走了不同条件分支，可能产生错误梯度；不能只看峰值显存下降就算验收成功。

## allocated与reserved

分配给活跃张量的内存，与缓存分配器保留的内存是不同指标；系统工具看到的进程显存又可能包括其他开销。reserved较高不一定泄漏，持续增长也要结合活跃张量和负载分析。

empty_cache通常释放某些未使用缓存，不会释放仍被引用的张量。每步调用不一定提升训练容量，可能增加分配开销。先定位持有者与峰值阶段。

## 性能测量要考虑异步

GPU工作常异步提交；CPU函数返回不表示kernel已经结束。测GPU耗时需要合适的event或同步边界。一次完整训练计时与算子计时要区分，预热、编译和数据缓存也会影响结果。

PyTorch AMP recipe在测量边界使用cuda.synchronize，说明这种差异。不能只拿一次墙钟结果证明所有规模都快几倍。

吞吐应使用有效样本或有效监督token，padding不应被当成业务有效数据。记录输入长度分布、batch、累积、dtype、硬件、版本和测量窗口。

## 复现不是只设seed

保存数据快照及划分、代码提交、依赖、模型revision、所有随机源、sampler顺序、训练计数和状态。确定性选项也可能改变性能，某些算子没有完全确定路径。

区分数学小任务的精确一致、相同环境训练的可重放、跨机器的统计接近。报告容差或多seed分布比一句“结果可复现”更明确。

## 最小排障顺序

先用少量已知样本验证输入与标签；用FP32小batch确认loss/梯度有限；查看参数是否真正更新；再逐步启用AMP、累积、worker和分布式。一次改变多项，很难知道是哪项引入问题。

训练loss很低但验证差，还应回到数据泄漏、分布与指标定义，不应只优化GPU占用。

## 练习

列出你的训练任务每种状态的生命周期及保存位置。数学示例验证半精度、累积与恢复机制，但本篇没有GPU profiler、内存测量或激活checkpoint集成结果。

## 来源

PyTorch checkpoint源码、AMP recipe及DataLoader源码。OOM定位、日志生命周期与复现记录为独立工程补充。

核验日期：2026-10-04。固定来源：

- [pytorch/pytorch / torch/utils/checkpoint.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/checkpoint.py)
- [pytorch/tutorials / recipes_source/recipes/amp_recipe.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/recipes_source/recipes/amp_recipe.py)
- [pytorch/pytorch / torch/utils/data/dataloader.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/data/dataloader.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
