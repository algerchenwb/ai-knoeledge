# 半监督学习

当人工标签少、未标注样本多时，怎样安全地利用额外数据。

- [自训练与伪标签](01-self-training-and-pseudo-labels.md)：学习方式区别、严格阈值与k_best、确认偏差、标签轮次、独立评估、实际scikit-learn实验。
- [开源来源与许可](SOURCES.md)
- [已运行实验与结果](VALIDATION.md)

前置阅读：[逻辑回归](../classical-ml/02-logistic-regression.md)、[概率校准](../classical-ml/11-probability-calibration.md)、[数据泄漏与管线](../ml-evaluation/01-data-leakage-and-pipelines.md)。

运行：先在Python 3.12虚拟环境中安装 `python -m pip install -r knowledge/semi-supervised/examples/requirements.txt`，再执行 `python knowledge/semi-supervised/examples/self_training_checks.py`。全部数据在本地合成，不下载数据集。
