# 来源与核验范围

核验日期：2026-10-04。本专题主要来源为 [scikit-learn-contrib/MAPIE](https://github.com/scikit-learn-contrib/MAPIE)，固定提交 `3b84b8212db2bba452ef5a09ae06a0dd545869ae`。

| 已阅读文件 | 使用范围 |
| --- | --- |
| [split-cross-conformal.md](https://github.com/scikit-learn-contrib/MAPIE/blob/3b84b8212db2bba452ef5a09ae06a0dd545869ae/doc/content/conformal-prediction/split-cross-conformal.md) | 训练/校准/测试角色、可交换性、split 与 cross 工作流区别 |
| [regression.md](https://github.com/scikit-learn-contrib/MAPIE/blob/3b84b8212db2bba452ef5a09ae06a0dd545869ae/doc/content/conformal-prediction/regression.md) | 绝对残差区间、训练残差乐观、方法假设区别与后续方法范围 |

有限样本秩修正与边际覆盖定义补充核验 Anastasios N. Angelopoulos 与 Stephen Bates 的原理论文：[A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification，arXiv:2107.07511v6](https://arxiv.org/html/2107.07511v6)，重点为第 1 节及边际覆盖说明。仅以独立文字说明公式和前提，未复制论文文字、图片或代码。

MAPIE 采用 BSD 3-Clause。Copyright (c) 2021, Vianney TAQUET, Grégoire MARTINON, Nicolas BRUNEL, Issam IBNOUHSEIN, François DEHEEGER and MAPIE contributors。完整许可与无担保免责声明见 [LICENSE](https://github.com/scikit-learn-contrib/MAPIE/blob/3b84b8212db2bba452ef5a09ae06a0dd545869ae/LICENSE)。本整理与项目和论文作者没有隶属或背书关系。

中文组织、区间显示建议、人工分组算例和标准库模拟独立编写。本实现取明确的第 k 个顺序统计量，k>n 时返回无穷，不承诺与 MAPIE 对不可达到置信水平的具体 API 处理相同。

阅读开源源码不等于集成运行：本环境未安装 MAPIE，未运行上游库示例。验证结果与边界见 [README](README.md)，只覆盖独立的教学实现。
