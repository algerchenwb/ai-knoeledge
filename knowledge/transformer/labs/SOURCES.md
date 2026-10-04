# 注意力实验来源与许可

核验日期：2026-10-04。本实验参考开源教材 *Dive into Deep Learning* 的注意力与位置编码机制，作者为 Aston Zhang、Zachary C. Lipton、Mu Li、Alexander J. Smola 及贡献者。署名依据：[固定版本 README](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/README.md)。本整理与官方项目没有隶属或背书关系。

固定提交为 `23d7a5aecceee57d1292c56e90cce307f183bb0a`，提交日期 2024-03-16。核验日期不表示上游最近发布日期。

| 已阅读的来源文件 | 对应内容 |
| --- | --- |
| [Queries, Keys, and Values](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/chapter_attention-mechanisms-and-transformers/queries-keys-values.md) | 匹配权重与加权汇总 |
| [Attention Scoring Functions](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/chapter_attention-mechanisms-and-transformers/attention-scoring-functions.md) | √dk 缩放与屏蔽机制 |
| [Self-Attention and Positional Encoding](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/chapter_attention-mechanisms-and-transformers/self-attention-and-positional-encoding.md) | 自注意力与正弦位置编码 |
| [Transformer Architecture](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/chapter_attention-mechanisms-and-transformers/transformer.md) | 自回归访问约束 |

中文实验说明重新组织；人工数值、标量参考公式、未来输入干预和置换等变检查独立编写，未复制上游图片或参考代码。实际运行的数值及验证边界见 [实验说明](attention-invariants.md)。没有实跑原教材的 PyTorch/MXNet/TensorFlow/JAX 示例。

原教材文字采用 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)，完整条款和无担保免责声明见 [原仓库 LICENSE](https://github.com/d2l-ai/d2l-en/blob/23d7a5aecceee57d1292c56e90cce307f183bb0a/LICENSE)。原参考代码另有 modified MIT 许可，本实验没有复制这些代码。

本次新增的 `labs/attention-invariants.md`、本来源文件和 `examples/attention_invariants.py` 同样按 **CC BY-SA 4.0** 提供。复用应保留署名与来源、标示修改并按相同许可分享改编内容。这不改变 Transformer 专题其他文件或仓库其他目录的许可。
