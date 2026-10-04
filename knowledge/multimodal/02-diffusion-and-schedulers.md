# 扩散模型：加噪、去噪、潜空间与调度器

## 先忘掉“模型在素材库拼图”

典型扩散模型学习从噪声状态逐步恢复数据结构的规律，生成时从噪声出发，反复预测与更新状态，最终得到图像等数据。这里是概率建模，不应把所有输出解释成检索已有图片后直接拼接。

记忆训练数据、相似内容和授权问题需要另行评估；机制介绍不能反推所有生成内容一定原创。

## 训练中的正向加噪

经典DDPM的一种表示：

```text
x_t = sqrt(alpha_bar_t) * x_0
      + sqrt(1-alpha_bar_t) * epsilon
epsilon ~ 标准高斯噪声
```

x_0为干净数据，x_t为某个时刻的噪声状态，alpha_bar_t控制信号保留程度。越接近0，原始信号贡献通常越小。Diffusers的DDPMScheduler.add_noise实现可直接找到这两个系数。

它们使用平方根以匹配方差尺度，不是简单把“80%图片+20%噪声”按线性比例混合。实际噪声日程通过各步alpha的累积形成alpha_bar。

## 模型学习的目标

常见训练目标预测噪声epsilon，也有预测干净样本或velocity等参数化。网络读取x_t、时间步和可选条件，损失让预测接近相应目标。

训练通常采样时间步，不必对每个样本把完整去噪链都反向跑一遍。生成时则多步迭代，因此训练与推理过程不能看作逐步镜像复制。

## Scheduler和网络不同

网络预测某个目标；scheduler根据日程与更新规则，把当前状态变成下个状态。Diffusers将模型、scheduler、pipeline分成组件，这方便替换，但要保持预测类型与配置兼容。

用错误scheduler配置接入相同网络，可能使更新公式与模型目标不匹配。减少推理步数能减少计算，但质量变化取决于模型和采样方法，不保证步数越少越差或越多越好。

## 潜空间扩散

潜空间方案先用编码器把图片压缩成较小表示，在潜空间做生成，再由解码器还原。这样降低直接处理高分辨率像素的成本，但编码/解码会有自己的信息损失与成本。

图像尺寸、latent通道、压缩倍率与模型架构有关；不能把某个Stable Diffusion例子的尺寸规则当作所有模型通用标准。现代扩散系统也可能使用Transformer等网络，不全是UNet。

## 文本条件与CFG

文本通常经编码器得到条件表示，再通过网络相应机制影响生成。一种常见classifier-free guidance形式为pred=uncond+s×(cond-uncond)，增强条件方向。

s增大可能强化提示约束，也可能带来饱和、伪影或多样性下降。不同模型不一定采用同样的CFG方案或参数范围。负向提示也不是可靠的内容过滤器，更不能保证图中文字准确。

## Seed与编辑强度

固定seed帮助复现初始噪声，但运行时、scheduler、模型版本、硬件和随机数使用方式都可能影响最终输出。仅保存seed不足以复现。

图生图常在输入图编码后加一定噪声再去噪。改变强度通常会影响对原图的保留程度，但确切语义依pipeline实现。局部编辑还需要mask与尺寸处理。

## 业务验收

宣传图可检查主体、布局、品牌和可用尺寸；精确图表和指标图应使用确定性绘图工具。生成一张“看起来像趋势图”的图片，不代表数据点正确。

保存模型revision、提示、预处理、seed、scheduler、步数、guidance与尺寸，以便追溯和迭代。

## 练习

数学示例验证已知epsilon时反推x_0的代数关系。真实模型只有预测epsilon，误差会影响后续迭代，所以该演示不是完整图像生成器，也没有图像质量测评。

## 来源

Diffusers README与DDPMScheduler源码；潜空间与CFG为原创通用机制补充，未声称所有pipeline都采用这些配置。固定链接见[来源清单](../expansion-2026-10/SOURCES.md)。

核验日期：2026-10-04。对应固定快照：

- [huggingface/diffusers / README.md](https://github.com/huggingface/diffusers/blob/8b33bfc04b6b5e8bb58a58e55f68746c1bbee4cd/README.md)
- [huggingface/diffusers / src/diffusers/schedulers/scheduling_ddpm.py](https://github.com/huggingface/diffusers/blob/8b33bfc04b6b5e8bb58a58e55f68746c1bbee4cd/src/diffusers/schedulers/scheduling_ddpm.py)
