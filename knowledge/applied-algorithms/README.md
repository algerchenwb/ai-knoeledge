# 应用算法：文本、推荐、图与数据流

从已有机器学习基础继续深入：每篇提供直觉、公式、手算、工程边界、练习与开源来源。建议按下面顺序学习；第6篇深入已有检索指标的计算口径。

| 轮次 | 知识点 | 可运行实验 |
| --- | --- | --- |
| 1 | [TF-IDF](01-tfidf.md) | [示例](examples/01_tfidf.py) |
| 2 | [特征哈希](02-feature-hashing.md) | [示例](examples/02_hashing.py) |
| 3 | [NMF主题模型](03-nmf-topics.md) | [示例](examples/03_nmf.py) |
| 4 | [Apriori与关联规则](04-association-rules.md) | [示例](examples/04_rules.py) |
| 5 | [隐式反馈ALS](05-implicit-als.md) | [示例](examples/05_als.py) |
| 6 | [排序指标深入](06-ranking-metrics.md) | [示例](examples/06_ranking.py) |
| 7 | [PageRank](07-pagerank.md) | [示例](examples/07_pagerank.py) |
| 8 | [图消息传递](08-message-passing.md) | [示例](examples/08_messages.py) |
| 9 | [在线学习](09-online-learning.md) | [示例](examples/09_online.py) |

## 运行与来源

环境记录：Python 3.12.14、NumPy 2.3.5、scikit-learn 1.8.0。建议新建虚拟环境，再运行 `python -m pip install -r knowledge/applied-algorithms/examples/requirements.txt`，然后运行所选章节给出的命令。仅依赖标准库的第4、10篇可以不安装额外依赖。

小实验分别验证机制，不代表完成生产训练。实际调用scikit-learn与独立数学实验的范围见[来源清单](SOURCES.md)；已执行的断言见[验证记录](VALIDATION.md)。全部使用合成数据、无需GPU或线上凭据。
