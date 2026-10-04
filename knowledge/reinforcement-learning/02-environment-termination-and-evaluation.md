# 强化学习环境：reset、step、终止、截断与评估

## 环境API不是训练算法

Gymnasium提供统一交互方式，使不同算法能与环境沟通。env.reset通常返回observation与info；env.step(action)返回observation、reward、terminated、truncated、info。

环境负责规则和反馈，算法负责学习。一个能随机走1000步的示例，只证明交互循环跑通，不能证明策略有进步。

## terminated与truncated为何要分开

terminated表示任务定义中的终止，比如到达目标或失败状态；truncated表示因外部条件截断，比如达到训练器设置的步数上限。二者都可能需要reset，但价值目标处理不一定相同。

对于外部时间限制，若MDP本身本可继续，通常还应bootstrap：target=r+γV(next_state)。真正终止状态通常target=r。把两者统一当done后全部清零未来价值，可能系统性低估时间上限附近的状态。

如果时间限制本身就是任务定义的终点，应相应建模，并将所需剩余时间信息纳入状态。不能机械地说“所有truncated都应该bootstrap”，必须核对环境语义、算法和采样实现。

## 自动reset容易产生错位

向量化环境可能在episode结束后自动提供下一局初始观察。如果算法把新一局观察当上一局的next_state，就会计算错误目标。应核对final observation等信息的保存方式，具体字段随API版本与包装器变化。

保存transition时需要知道：当前状态、动作、reward、对应的真实下一观察、终止标志与必要的截断信息。仅存一个含义不清的done可能不够。

## Observation与隐藏状态

observation可能不是完整state。例如屏幕截图只显示当前位置附近，历史动作影响隐藏门锁；策略若需要记忆，要通过历史堆叠、循环网络等方案处理，不能假设当前画面足够。

对观察做归一化、裁剪或奖励缩放，训练和评估应使用一致的处理。归一化统计是否冻结，也影响复现。

## Seed不是只有一个

环境reset seed、动作空间随机seed、Python/NumPy/框架随机源，以及GPU算子行为都可能影响实验。一次seed跑好不意味着普遍稳定；不同seed的回报曲线和分布能揭示方差。

环境ID和版本也需要记录。规则变了、难度变了，不能把两个实验当同一基准。Gymnasium的环境版本后缀正是复现信息的一部分。

## 评估该看什么

报告平均回报之外，记录成功率、失败类别、episode长度、约束违规、多个seed和置信范围。训练回报常来自探索策略，评估回报来自固定或较少探索策略，应清楚区分。

任务可能出现“回报高但目标失败”：例如奖励每走一步+1，智能体可能学会拖延而不是抵达终点。奖励塑形要与真实目标核查，避免鼓励捷径或漏洞。

## 向量化与采样量

多个环境并行可提高采样吞吐，但统计步数时应区分每环境步与总transition数。训练1000次循环、每次32个环境，可能收集32000条transition；报告“1000步”容易误导。

速度比较还需包含环境计算、策略推理和参数更新。环境慢时升级GPU不一定解决瓶颈。

## 与LLM-agent结合

若让agent操作模拟工具环境，应定义状态、工具动作、反馈、回合终止和任务奖励。只有日志记录与工具循环，没有权重更新或其他学习过程，不能直接声称完成强化学习训练。

## 练习

同一个transition：r=1，γ=0.9，V(next)=4。真正终止target=1；可继续任务的外部截断target=4.6。运行数学示例验证差异，再检查你的环境是否提供了正确next observation。

## 来源

Gymnasium README的reset/step与环境版本说明；CleanRL dqn.py核对真实next observation处理与终止时bootstrap屏蔽。API差异、评估方法与工程例子独立编写。本文没有真实环境训练结果。固定链接见[来源清单](../expansion-2026-10/SOURCES.md)。

核验日期：2026-10-04。对应固定快照：

- [Farama-Foundation/Gymnasium / README.md](https://github.com/Farama-Foundation/Gymnasium/blob/b415c420377c3a3fee3b7617e4d5f48c8d9d3b31/README.md)
- [vwxyzjn/cleanrl / cleanrl/dqn.py](https://github.com/vwxyzjn/cleanrl/blob/fe8d8a03c41a7ef5b523e2e354bd01c363e786bb/cleanrl/dqn.py)
