# 来源与核验范围

核验日期：2026-10-04。主要来源为 scikit-learn 开发者的官方开源仓库，固定提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`。

- [cross_validation.rst 的 Time Series Split](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/cross_validation.rst)：顺序评估、等间隔要求、训练折扩展。
- [plot_time_series_lagged_features.py](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/examples/applications/plot_time_series_lagged_features.py)：滞后特征、先 shift 再 rolling、随机拆分与时间拆分、gap 和 max_train_size。

官方示例采用自行车数据，本文人工门店场景、序列、标签可用时间讨论、实体分组检查和评价汇总独立编写，不复制官方示例代码或图片，也未执行官方数据集实验。

来源采用 BSD 3-Clause，Copyright (c) 2007-2026 The scikit-learn developers；完整许可与无担保免责声明见 [COPYING](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。本整理与官方没有隶属关系。

源码阅读快照与本地 scikit-learn 1.8.0 安装版本分别记录，不声称逐行一致。已运行结果和未验证范围见 [README](README.md)。
