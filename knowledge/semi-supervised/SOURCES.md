# 开源来源与许可

核验日期：2026-10-04。以下为本轮实际读取的官方开源文件，固定到提交 `a442e4bb39551feb7b0af4c00075e2cb91cf9b77`，避免main变化后无法追溯。

- [scikit-learn 半监督学习文档](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/doc/modules/semi_supervised.rst)：未标注项编码、自训练筛选、概率校准要求与算法概览。
- [SelfTrainingClassifier源码](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/sklearn/semi_supervised/_self_training.py)：严格阈值、k_best、克隆估计器、标签轮次、停止条件与最终拟合。
- [BSD-3-Clause许可证](https://github.com/scikit-learn/scikit-learn/blob/a442e4bb39551feb7b0af4c00075e2cb91cf9b77/COPYING)。同一快照的[完整版权及许可文本](../applied-algorithms/licenses/scikit-learn.txt)已在仓库保留。

本专题为独立中文解释、虚构业务示例和原创实验，不是整篇翻译，不复制上游实现。算法与API说明基于上述文件；数据切分、审计、人工复核和业务流程属于独立工程扩展。与上游没有隶属或背书关系，许可证记录不重新许可本仓库全部内容。

实验实际调用本地scikit-learn 1.8.0；固定来源快照与已安装包不是同一版本声明。只核验[验证记录](VALIDATION.md)中的案例，不宣称运行了来源版本全部测试。无需外网、GPU或真实业务数据。
