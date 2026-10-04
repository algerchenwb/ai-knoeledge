# 保存与恢复训练：权重、优化器、随机状态和数据位置

## “还能推理”和“接着训练”是两种目标

推理通常需要模型权重、架构、tokenizer及必要配置；继续训练还需要optimizer、scheduler、scaler、训练步数、随机状态及数据读取位置。

同样的参数w，若动量v不同，下一步就不同。只保存w可以得到相同起点，却不保证沿着原训练轨迹继续。

## 需要保存什么

| 状态 | 原因 |
| --- | --- |
| model state | 参数和相关buffer |
| optimizer state | 动量、Adam统计、step等 |
| scheduler/scaler | 学习率进度与精度缩放 |
| global_update/epoch | 计数、日志、边界判断 |
| RNG状态 | 抽样、dropout、增强等随机序列 |
| sampler/游标 | 从哪一条数据继续 |
| 数据/代码/配置版本 | 证明仍是相同实验 |

框架save_state通常覆盖其中若干项，定制对象可能需要注册。不能仅看到API叫save_state就推断业务游标、所有worker内部状态和远程数据版本都已保存。

## 何时保存最容易正确

在完整optimizer更新边界保存，通常更容易保证状态一致。梯度累积中途保存还可能需要保存已累积梯度、窗口内计数和相关数据状态，否则恢复后半个窗口被重复或遗漏。

分布式训练需要rank之间一致边界。仅rank0写文件适合某些完整副本配置；分片状态则需专用保存流程，不能只取一张卡就认为有完整模型。

## 读取位置不是跳过几条就一定解决

固定顺序、无随机增强的简单数据可以按保存索引继续。Shuffle、多个worker预取、数据增强和流数据让情况复杂：主进程已经“领取”的位置与真正完成更新的数据位置可能不同。

Accelerate提供skip_first_batches等机制，但精确复现还依赖sampler与随机状态、数据版本和框架约定。重复跑读取逻辑以跳过样本，也可能消耗随机数并改变后续增强。

## 最近、最佳与正式产物

latest用于故障恢复，best基于明确验证指标，export用于部署。三者可能不是同一步，建议分别标识。把最新checkpoint直接当最佳模型，会掩盖后期过拟合。

指标方向也要明确：loss越低越好，某些业务分数越高越好；改善阈值和评估噪声影响最佳选择。测试集不应反复参与选best。

## 文件完整性与原子写入

先写临时位置，验证文件完整和必要元数据，再发布为可恢复版本，可减少中断留下半份文件。远程对象存储的rename/一致性语义与本地文件系统不同，需按具体存储设计提交标记或manifest。

保存校验和、版本、大小与完成标志，加载前先做一致性检查。保留多个最近版本，有助回退；频率应根据单步成本、恢复成本和存储预算决定。

## 精确恢复的边界

即使状态完整，硬件、算子非确定性、依赖变化和分布式拓扑也可能改变数值。可以区分“恢复后可正常训练”“统计效果接近”与“逐步数值一致”，不要混称。

nanoGPT快照保存model/optimizer/iter_num/config等，但不能因此宣称它包含所有随机与scaler状态、实现精确续跑。阅读源码应指出这种实际范围。

## 如何验证恢复

在受控小任务比较连续跑N步，与跑M步→保存→重新创建对象→加载→再跑N-M步。核对参数、optimizer状态、步数、后续抽样和loss轨迹。再故意漏掉optimizer或RNG状态，看测试能否发现差异。

本专题的标准库实验会验证完整状态的轨迹一致，并演示漏状态导致不同结果。它不验证真实PyTorch序列化、多worker或分布式续跑。

## 来源

Accelerate checkpoint文档核对model/optimizer/RNG/GradScaler与注册对象；nanoGPT核对其实际保存字段。存储一致性与恢复验收独立编写。

核验日期：2026-10-04。固定来源：

- [huggingface/accelerate / docs/source/usage_guides/checkpoint.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/checkpoint.md)
- [karpathy/nanoGPT / train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
