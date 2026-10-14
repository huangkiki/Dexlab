# Genesis 斜面：接触模型会改变结果

[English](genesis-incline-results.md) · [协议与运行命令](genesis-incline-protocol.zh-CN.md)

在冻结的原生 Genesis 1.4.3／Quadrants 1.3.3、CPU FP64 协议下，Newton／elliptic／Signorini 通过六个非零摩擦工况，三个名义零摩擦工况全部失败。Newton／elliptic／convex 只通过三个静态工况，其余三组配置均为 0/9。五个禁用接触负例全部有效并被正确拒绝。这是固定条件下的工况计数，不是成功概率或引擎总排名。

| Solver / cone / contact model | 正例通过 | 无效正例 | 负例 |
|---|---:|---:|---|
| Newton / elliptic / signorini | 6/9 | 0 | 有效，拒绝 |
| Newton / elliptic / convex | 3/9 | 0 | 有效，拒绝 |
| Newton / pyramidal / convex | 0/9 | 0 | 有效，拒绝 |
| CG / elliptic / convex | 0/9 | 4 | 有效，拒绝 |
| CG / pyramidal / convex | 0/9 | 3 | 有效，拒绝 |

## 输入为零，有效接触摩擦仍不为零

官方材料构造器拒绝 μ=0；官方几何 setter 可以设零并读回零，但接触生成实际采用 **max(μA·ratioA, μB·ratioB, .01)**。逐接触读回证实名义零摩擦工况的有效值均为 .01。输入、有效模型与原零摩擦目标分别保留。[固定源码的组合律](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L433-L463)。

Signorini 下，名义零摩擦的加速度差约为 **0.0947573 m/s²**，与 μ=.01 时的 μg cos(15°) 相符。单独标注的三个有效 μ=.01 诊断通过相同数值限制，但不能替换原失败或增加覆盖。Convex 接触在这些参数下还出现支撑中断；减小步长没有使完整任务通过。Pyramidal 静态工况则超过位移限制。评分文件保留全部指标与判断，包括转动、穿透和支撑失败。

## 七条 CG 记录未通过力与状态一致性

CG／elliptic 的三个静态工况和 2 ms 滑动工况共四条无效；CG／pyramidal 的三个名义零摩擦工况无效。最大动量残差范围为 **1.50305e-7～1.23691e-6 N·s**，超过原有 1e-7 限制。原生错误位均为零，几何、时钟、位置／速度、逐接触力与净力账本检查均通过。API 没有报错不等于物理证据合格。

独立诊断逐条精确复现了七个出错状态／力前缀。原生平动梯度乘步长与动量残差在 1e-15 N·s 内一致。六个停止状态满足源码的改进量阈值，但梯度仍未收敛；2 ms 滑动样本达到配置的 100 次上限时仍有 `improved=true`。这是观测字段与源码共同支持的停止原因，不是假造的原生迭代计数。1 ms 静态样本把上限从 100 增至 1000 后，106 步前缀完全不变：改进量 1.8551521e-10 已低于缩放阈值 1.9205120e-10。没有修改引擎、放宽评分或用新运行替换原记录。

[诊断读回](evidence/genesis-incline/stopping-diagnosis.json) · [原生梯度与循环](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5136-L5160) · [停止条件](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L568-L616)。

## 范围、不支持项与成本

五种适用的刚体 solver／cone／接触组合完成 **45 个正例＋5 个负例，共 115,000 次原生更新**。Signorini 与 Newton／pyramidal、CG／elliptic、CG／pyramidal 的组合，在推进时间前即被官方 API 拒绝。这是当前版本的不支持结果；支持它们的官方新版本仍需重新准入。本批不扫描积分器、设备或调参空间。原生路径与既有带补丁框架的夹持记录分开；Isaac／MJWarp 对照仍由 [#152](https://github.com/huangkiki/Dexlab/issues/152) 承接。

采集冻结为 16 GiB、四核配额、一个 Quadrants 执行／编译线程、禁用 swap，启动另留 8 GiB。实测峰值 **623.391 MiB**，后续同类任务可用最低 8 GiB 档；没有内存超限或 OOM，CPU 限流两次共 223.285 ms。两个采集服务段总计 **83.878 秒**，包括离线验证，以及发现 CG 无效证据后的主动暂停。准备／原生步进／观测累计为 **17.801／15.312／12.583 秒**。诊断另计：三个进程、九个前缀、2,217 次更新、21.467 秒。带完整观测的正确性成本不能用于跨引擎速度排名。[逐例时间](evidence/genesis-incline/timing.json)。

原始轨迹、有效选项／内核开关、接触账本、错误位、失败的准备尝试与冻结源码均保留。在核查的 manifest、release 和历史双引擎归档中，没有找到协议兼容的 Genesis 斜面九例；历史遥测缺失不被补写。本批不声称 coverage-v1 可靠准入、共同调参预算或冻结留出比较已经完成。五种配置与三个拒绝组合仍只是一种任务类型。

[Complete scores and protocols](evidence/genesis-incline/profiles.json) · [Official identity](evidence/genesis-incline/official-proof.json) · [Native unsupported combinations](evidence/genesis-incline/unsupported.json) · [Resource records](evidence/genesis-incline/resources.json) · [History audit](evidence/genesis-incline/history-reuse-audit.json)

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.52.0/dexlab-genesis-incline-v1.tar.gz) · [Archive SHA256](evidence/genesis-incline/archive.json)
