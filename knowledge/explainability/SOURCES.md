# 可解释性来源与核验范围

核验日期：2026-10-04。本专题为独立中文组织与说明，与上游项目没有隶属或背书关系。人工门店场景、手算、练习答案和演示代码独立编写，未复制原图、参考代码或完整原文。

## scikit-learn

官方仓库：[scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)。固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。

| 已阅读文件 | 使用范围 |
| --- | --- |
| [permutation_importance.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/permutation_importance.rst) | 置换定义、评估集、指标、相关性与树不纯度重要性 |
| [partial_dependence.rst](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/partial_dependence.rst) | PDP/ICE 数学定义、brute 平均、中心化、相关字段与递归方式边界 |

来源采用 [BSD 3-Clause](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)，Copyright (c) 2007-2026 The scikit-learn developers。完整条件与无担保免责声明见上述 COPYING 链接。

## SHAP

官方仓库：[shap/shap](https://github.com/shap/shap)。固定提交 `fc3e290e97ce12f76d1175d24c6e3023b4ca7d69`。

| 已阅读文件 | 使用范围 |
| --- | --- |
| [README.md](https://github.com/shap/shap/blob/fc3e290e97ce12f76d1175d24c6e3023b4ca7d69/README.md) | 加性贡献、局部与全局摘要、Tree/Kernel 等方法区别 |
| [_tree.py](https://github.com/shap/shap/blob/fc3e290e97ce12f76d1175d24c6e3023b4ca7d69/shap/explainers/_tree.py) | TreeExplainer 的背景、特征依赖处理及 model_output 参数说明 |

来源采用 [MIT License](https://github.com/shap/shap/blob/fc3e290e97ce12f76d1175d24c6e3023b4ca7d69/LICENSE)，Copyright (c) 2018 Scott Lundberg。完整条件与无担保免责声明见上述 LICENSE 链接。

本专题的精确两特征 Shapley 使用明确的背景替换游戏定义，不是 TreeExplainer 的源码移植，不承诺与不同缺失特征处理选项的数值一致。说明中的因果边界、成组置换建议、报告记录项是独立工程补充。

## 阅读与运行不是同一回事

两套原创示例已运行，具体结果见 [README.md](README.md)。真实库集成使用本地 scikit-learn 1.8.0 与 NumPy 2.3.5，并且仅覆盖脚本中的 permutation_importance 与 brute partial_dependence 行为；不声称穷尽验证上游快照。

本环境没有 SHAP 库，未运行 SHAP 的官方示例或 Tree SHAP；没有训练真实门店模型，也没有验证任何业务收益或因果结论。没有把固定快照中的接口支持范围表述为所有未来版本的保证。
