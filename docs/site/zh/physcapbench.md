# 物理 caption 怎样进入 DexLab：先评参考覆盖，再查视频事实

## TL;DR

**PhysCapBench 最值得借鉴的，不是一个新的“物理 caption 总分”，而是把物理过程写成可检查的参考记录，并在候选出现之前冻结“这一维是否有足够证据可评”。**

它适合诊断仿真数据、失败解释或视频描述漏掉了哪一层物理信息；不能替代接触力、状态轨迹、原生任务判据或真机结果。公开评测器目前主要是文本裁判比较候选与 Gold reference，并不是重新看视频核验全部事实。

## 从一个翻书过程开始

假设视频里左手按住书页，右手把右页翻到左侧，接触在翻页过程中保持，页面状态从右侧变为左侧，参考还记录了施加力矩导致姿态变化以及事件先后。

候选说“一个人翻书”，语义并不错，但没有说明：

- 哪只手固定，哪只手施力；
- 页面相对书本向哪个方向转动；
- 接触何时开始、维持或结束；
- 页面最终的物理状态；
- 哪条可见关系支持“施力导致翻转”；
- 各事件的前后顺序。

PhysCapBench 把这些信息拆成七个维度：事件覆盖、对象与角色、动作与运动、接触与交互、状态与结果、物理机制/因果和时间顺序。维度化不是为了拼出一个更长的 caption，而是让“听起来对、过程信息不够”变成可以定位的缺失。

## 真正值得复用的是评测契约

每个样本的参考不只包含一段短文本，而是实体、初始/最终状态、事件、角色、动作、接触、状态变化、机制、时序和证据帧。评测先在没有候选的情况下确定每个维度的参考证据是否充分，再让裁判读取候选和冻结证据。

这套顺序减少一种常见污染：看到某个方法只在某几个维度表现差，就删掉难评维度或重写 Gold。对 DexLab，等价的契约应是：

1. 先冻结任务、reference、applicability、评分器和失败分母；
2. 再运行被测系统；
3. 报告每个判据是否有原生测量支持；
4. 证据不足就保留“不足”，不强行给确定分数。

数据版本也要一起绑定。本轮核查固定了[论文 v2](https://arxiv.org/abs/2611.16424v2)、[GitHub `0858c69`](https://github.com/hfwang2001/PhysCapBench/tree/0858c694f6aa2fae247c5fc907fb60488f27c4b7)和[Hugging Face revision `4b18722`](https://huggingface.co/datasets/hfwang01/PhysCapBench/tree/4b1872201558c6fb5e231f5be2b843ed16b2e105)。发布 metadata 的 1,500 条 ID、reference、applicability 与哈希校验可以通过；这不等于已经验证 1,500 条 caption 的事实正确性。

## 它能证明与不能证明什么

论文报告 physical caption 使第三人称 reconstruction LPIPS 相对下降 8.6–9.5%，egocentric 下降 26.9–30.9%；两类生成器与 PVCS 指标方向一致。Policy instruction enrichment 在单任务 40 个共享场景上把成功率从 37.5% 提到 45.0%，四个 policy family 在两个 benchmark 上的平均成功率也有提升。

这些结果支持“更完整的物理描述作为整体，可能改善下游条件生成和训练指令”，但仍有三个边界：

- 单任务只多出 3 个成功案例，使用单训练 seed、每场景一次 rollout；没有报告多维描述消融或置信区间。
- 公开仓库包含 benchmark 评测器，未包含 reconstruction/policy 训练复现包；下游结果目前应按作者报告阅读。
- 当前文本评测对 Gold 中未记录、但候选额外加入的错误接触或因果关系不一定扣分。它主要度量 reference agreement / coverage，不是完整的视频事实核验。

论文也没有报告人工评分与 LLM judge 的一致性。把该分数直接作为 DexLab 的奖励或任务成功判据，会把“参考覆盖好”误当成“物理过程正确”。

## DexLab 的借鉴顺序

### 直接借鉴

1. **把过程写成事件链。** 失败解释至少包含主体/工具/目标、运动、接触开始/维持/结束、状态前后、可见机制和时间关系。
2. **候选前冻结适用性。** 先确定现有测量能否支持某一判据，再运行被测系统；不能因为某方法较弱就删除困难维度。
3. **按信息来源选辅助线索。** 视频场景、ego hand pose/HOI、夹爪多视角与轨迹各自解决不同问题；辅助 cue 只能帮助标注，不能自动成为 Gold。
4. **证据和版本一起保存。** reference revision、配置哈希、帧/时间窗、review status 与候选是否已见都应可追溯。

### 需要适配

迁移到仿真时，native contact force、接触建立/丢失、solver event、object pose/velocity 比视频 caption 更强。它们可以作为物理参考证据，但仍要保持 `command ≠ measurement`、`render ≠ physical control`。最终验收仍是第一次失效层、任务原生判据、完整任务成功和必要的真实测量。

### 暂不采用

- 不把七维等权平均当通用物理真实性分数；
- 不把单个 LLM judge 直接当 reward；
- 不用 caption 分数上升代替 sim-to-real 或任务成功。

## 第一个可验证问题

选 DexLab 已有 20–30 个 episode，覆盖稳定抓取、滑移/接触切换和状态恢复。比较短任务说明、通用视频 caption、结构化物理 caption 三种描述，并在七维 coverage 之外单独记录：

- 错误接触；
- 错误因果方向；
- 错误状态转移。

对 90–120 个候选做至少两人盲评，再比较两个文本或多模态 judge。最低成功标准不是“描述更长”，而是结构化描述让第一次失效层更容易定位，同时没有增加 false assertion。只有这两项同时成立，才值得进入更大数据清洗或训练指令生成流程。

## 继续阅读

- [PhysCapBench 论文](https://arxiv.org/abs/2611.16424v2)
- [官方评测代码](https://github.com/hfwang2001/PhysCapBench)
- [公开数据](https://huggingface.co/datasets/hfwang01/PhysCapBench)
- [DexLab 讨论 #378](https://github.com/huangkiki/Dexlab/discussions/378)

更广的共同进化评测边界见[模型评测](model-evaluation.md)。

## 证据范围

本页是论文与公开实现的机制整理，不是 PhysCapBench 排行榜复现，也不是新的 DexLab 物理实验。本轮执行了发布 metadata 校验和仓库契约测试，抽查了代表视频的哈希与帧内容；没有调用 judge endpoint，没有重跑 caption、reconstruction 或 policy 实验。所有下游数值均为作者报告。
