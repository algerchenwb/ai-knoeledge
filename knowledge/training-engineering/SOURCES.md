# 训练工程：来源与版本

核验日期：2026-10-04。本专题8篇正文参考下列4个开源项目。使用固定提交，不将分支最新状态当作永久不变的SDK契约。

中文讲解、数学反例、训练恢复实验和工程建议独立编写；没有整段复制源码或文档。文末链接用于核对具体机制，不代表所有额外建议都是上游项目的结论。本专题与上游没有隶属关系。

## pytorch/pytorch

提交：`496340f06ef7bda2800522429ba3f4e3473a92fa`。上游[许可：BSD-style，含第三方许可声明](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/LICENSE)。

- [torch/optim/sgd.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/sgd.py)
- [torch/optim/adam.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/adam.py)
- [torch/optim/adamw.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/optim/adamw.py)
- [torch/utils/data/dataloader.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/data/dataloader.py)
- [torch/utils/data/distributed.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/data/distributed.py)
- [torch/utils/checkpoint.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/checkpoint.py)

## pytorch/tutorials

提交：`11512db7cbbcc4b530ecfc63205d3fed13fa190d`。上游[许可：BSD 3-Clause](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/LICENSE)。

- [beginner_source/basics/data_tutorial.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/data_tutorial.py)
- [recipes_source/recipes/amp_recipe.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/recipes_source/recipes/amp_recipe.py)
- [intermediate_source/ddp_tutorial.rst](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/intermediate_source/ddp_tutorial.rst)

## huggingface/accelerate

提交：`01c73fbdb9a7cdbf3c750c22160e7568f2c339c0`。上游[许可：Apache-2.0](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/LICENSE)。

- [docs/source/usage_guides/gradient_accumulation.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/gradient_accumulation.md)
- [docs/source/usage_guides/checkpoint.md](https://github.com/huggingface/accelerate/blob/01c73fbdb9a7cdbf3c750c22160e7568f2c339c0/docs/source/usage_guides/checkpoint.md)

## karpathy/nanoGPT

提交：`3adf61e154c3fe3fca428ad6bc3818b27a3b8291`。上游[许可：MIT](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/LICENSE)。

- [train.py](https://github.com/karpathy/nanoGPT/blob/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/train.py)

## 核验范围

- PyTorch optimizer源码：SGD动量、Adam状态与校正、AdamW解耦衰减。
- PyTorch数据教程和源码：样本/collate/worker；分布式sampler补齐或丢尾，以及set_epoch。
- PyTorch AMP recipe：autocast、scale、unscale与clip顺序；同步计时边界。
- PyTorch checkpoint源码：激活重计算、实现变体、随机状态与重算限制。
- Accelerate文档：梯度累积中的token分母；训练状态保存、注册对象与DataLoader位置。
- nanoGPT训练代码：调度、累积、AMP裁剪与实际checkpoint字段。

只运行本专题标准库实验，未运行上述库的训练流程。上游示例可能包含历史API写法，本专题不承诺复制它们即可在所有依赖版本运行。模型权重和训练数据许可需独立于库许可核查。

机器可读记录：[sources.json](sources.json)。
