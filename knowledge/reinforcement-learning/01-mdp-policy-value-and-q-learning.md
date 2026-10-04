# 强化学习：状态、动作、奖励、策略与Q-learning

## 与普通监督学习有什么不同

监督学习通常给出输入和目标标签；强化学习中，智能体选择动作、环境变化、获得奖励，目标是提高累积回报。当前动作会改变后续经历，反馈也可能延迟到很多步之后。

“智能体”在此是学习决策的算法角色，不一定是聊天LLM。一个带工具调用的LLM工作流，也不自动代表其权重正在通过强化学习更新。

## 用MDP描述任务

Markov Decision Process通常由状态S、动作A、转移规则、奖励与折扣因子γ构成。Markov假设认为当前状态已包含预测后续所需的信息；现实系统如果只观察到部分信息，可能需要历史、状态估计或POMDP建模。

以虚构小网格导航为例：状态是格子位置，动作是上下左右，到终点得奖励，撞墙不移动。若状态遗漏“门是否已打开”，相同位置可能产生不同未来，就需要补充状态。

## 奖励与回报

即时reward是某步反馈；return是从当前开始的一串奖励：G_t=r_t+γr_(t+1)+γ²r_(t+2)+…。γ控制对未来奖励的折扣，不是正确率。

γ接近1会更重视长远，同时可能增加估计难度；γ=0只看即时奖励。奖励的尺度与设计会改变学习，不能随意改后还把结果与原实验直接比较。

## Policy、V与Q

Policy告诉智能体在状态s选择哪些动作，可以确定或随机。V(s)表示在某策略下从该状态出发的预期回报；Q(s,a)则先执行动作a再按策略继续的预期回报。

模型中的Q函数与Transformer的Query符号Q同名，但不是同一概念。状态价值高也不代表所有动作都好。

## Q-learning的更新

表格型Q-learning的简式：

```text
target = reward + gamma * max_a Q(next_state,a)
Q(state,action) += learning_rate * (target - Q(state,action))
```

若是真正终止状态，则通常不继续bootstrap，target=reward。例：旧Q=2，reward=1，下个状态最大Q=4，γ=0.9，学习率=0.5，则target=4.6，新Q=3.3。

它用“下一步可达到的最佳估值”更新当前估值；估值本身也可能错，需要多次数据积累。Q-learning是off-policy方法的一种；并非所有RL算法都使用这条更新。

## 探索与利用

只选当前估值最高动作可能永远不知道别的动作更好。epsilon-greedy以一定概率探索，其余选当前最佳。探索太少容易困在已知策略，太多则长期随机。

训练探索和最终评估应分开，评估还要多seed、多episode。单次恰好到终点不能证明稳定学会。随机策略基线是有价值的对照。

## 从表格到DQN

状态太多时，可以用神经网络近似Q。DQN常结合经验回放和目标网络缓和样本相关与目标漂移。但函数近似、bootstrap与off-policy结合可能不稳定，不能把表格算法收敛条件直接搬到深度网络。

## 业务应用的判断

若问题只是从固定标签选择接口，监督学习或明确规则可能更直接。只有动作影响后续状态、存在多步回报并能获得反馈时，才值得认真评估RL建模。上线探索可能付出真实成本，通常先在受控环境验证。

## 练习

运行数学示例核对普通与终止状态Q更新。为某个任务列出状态、动作、奖励；若你找不到可靠奖励和反馈循环，先别把它称为已经可训练的RL系统。

## 来源

Gymnasium README提供环境交互契约；CleanRL dqn.py核对Q目标、经验回放与目标网络。MDP、回报与表格Q-learning为独立基础讲解，示例未使用Gymnasium训练智能体。见[来源清单](../expansion-2026-10/SOURCES.md)。下一篇：[环境边界](02-environment-termination-and-evaluation.md)。

核验日期：2026-10-04。对应固定快照：

- [Farama-Foundation/Gymnasium / README.md](https://github.com/Farama-Foundation/Gymnasium/blob/b415c420377c3a3fee3b7617e4d5f48c8d9d3b31/README.md)
- [vwxyzjn/cleanrl / cleanrl/dqn.py](https://github.com/vwxyzjn/cleanrl/blob/fe8d8a03c41a7ef5b523e2e354bd01c363e786bb/cleanrl/dqn.py)
