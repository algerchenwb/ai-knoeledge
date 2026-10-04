# DDP：数据分片、梯度同步与全局指标

## 多卡不是自动把大模型切开

普通DistributedDataParallel给各rank放模型副本，让每份副本处理不同数据，随后同步梯度并更新。它主要做数据并行；若完整模型和必要状态一张卡就放不下，单纯加DDP副本不能解决。

模型分片、张量并行、流水线并行及optimizer分片有不同目的和通信方式。可以组合，但不能把所有“多卡训练”都叫作同一机制。

## rank、local_rank、world_size

rank是全局进程编号，local_rank通常用于本机设备选择，world_size是进程总数。一机4卡常使用4个进程，每个绑定自己的GPU；多机环境还需正确的通信地址和一致配置。

不要用local_rank判断“全局只做一次”的任务，否则每台机器的local_rank=0都可能重复写同一日志或文件。常见全局任务使用rank=0，但分片checkpoint并不一定只由它保存。

## 数据不会因包装DDP自动分开

需要合适sampler或输入分片方案。相同数据被每个rank全部重复读取时，计算重复且实际有效数据量与预期不同。Map数据常使用DistributedSampler；流数据需要考虑rank及worker联合分片。

某些sampler在数据数量不可整除时会补齐重复索引，以保持各rank同样数量；配置drop_last可能改为丢弃。不要把“DistributedSampler”直接当作每epoch绝无重复的保证。

Shuffle时常需在每epoch设置sampler.set_epoch，使顺序按epoch变化且各rank一致协调；否则可能每轮重复同一顺序。具体用法按实现核对。

## 梯度如何合并

普通DDP通常平均各rank梯度。若两rank各自有效样本一样多、loss为mean，那么平均局部梯度对应全局样本平均。

若rank0有2个有效token且均值梯度1，rank1有8个且均值梯度3，简单平均得到2，而正确全局token平均为2.6。应累计全局分子分母并调整归一化，不能忽略不同rank的有效量。

Accumulation、loss reduction及框架自动缩放也会参与最终比例。修改一处之后，需要用受控小任务核对实际梯度，而不是只看程序是否运行。

## 全局指标也要加权

rank0评估1条、全正确；rank1评估9条、全错误。平均两rank准确率得到0.5，真实全局准确率是1/10=0.1。

可归约正确数和总数再计算；平均loss归约loss_sum与有效项数。nDCG等按query定义的指标，则应按对应query数量汇总。分布式sampler补齐的重复评估样本也要处理，必要时按ID去重。

## 为什么有时挂住

通信操作需要各rank按兼容顺序参与。如果只有一部分rank调用collective，其余先退出或抛错，可能等待超时。数据长度不一致、条件分支、只在rank0验证却意外调用同步forward等，都需要分析。

barrier能同步时点，但不是万能修复；在某rank已崩溃时再加barrier仍会等。先找最早失败日志、rank对应输入和通信顺序。

## 性能与no_sync

更多设备也增加通信和调度；小模型、小batch或网络较慢时，扩卡不一定线性加速。梯度累积期间可在非更新micro-step使用no_sync减少通信，并保证对应forward/backward都处于合适上下文。

统计吞吐时写明总有效token/秒、每rank还是全局、是否包含加载与同步。只加总理论卡数不能得到实际速度。

## 练习

数学示例验证全局指标0.1与错误平均0.5，并验证两rank的token梯度归一化。本文没有启动真实进程组，无法验证通信、死锁或多卡性能。

## 来源

PyTorch DDP教程、DistributedSampler源码与Accelerate梯度累积文档。异常场景与业务指标例子独立编写。

核验日期：2026-10-04。固定来源：

- [pytorch/tutorials / intermediate_source/ddp_tutorial.rst](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/intermediate_source/ddp_tutorial.rst)
- [pytorch/pytorch / torch/utils/data/distributed.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/data/distributed.py)
- [huggingface/accelerate / docs/source/usage_guides/gradient_accumulation.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/gradient_accumulation.md)

[专题入口](README.md) · [验证记录](VALIDATION.md)
