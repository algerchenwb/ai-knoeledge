# 实验验证记录

执行日期：2026-10-04。环境：Python 3.12.14，NumPy 2.3.5，scikit-learn 1.8.0；无GPU。下面列出的脚本均实际运行，退出码0，无stderr。

| 轮次 | 脚本 | 已检查内容 |
| --- | --- | --- |
| 1 | [01_tfidf.py](examples/01_tfidf.py) | IDF公式、L2归一化、词表冻结、未知词 |
| 2 | [02_hashing.py](examples/02_hashing.py) | 强制碰撞、维度、分批一致、负值 |
| 3 | [03_nmf.py](examples/03_nmf.py) | 非负、重构、尺度不唯一、拒绝负输入 |
| 4 | [04_rules.py](examples/04_rules.py) | 二至四项候选与穷举一致；规则指标手算 |
| 5 | [05_als.py](examples/05_als.py) | 精确子更新目标下降、方程残差、重现 |
| 6 | [06_ranking.py](examples/06_ranking.py) | API与手算、增益约定、零相关、并列、RR |

这些检查针对确定的小案例，未测生产规模、线上收益、随机噪声误报率或所有异常输入。来源快照固定，但实际集成运行的是上述安装版本。第4、5、7、8、10篇不使用对应上游包，不能把数学演示通过解读为上游API已验证。
