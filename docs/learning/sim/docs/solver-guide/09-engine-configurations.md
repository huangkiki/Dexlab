# 9. 把六引擎配置表逐行读成问题

[教程目录](README.md) · [上一章：后端与身份](08-backends-and-identity.md) · [完整术语索引](term-index.md) · [版本与来源](source-versions.md)

这一章把前八章合起来。目标不是背完名字，而是面对一行配置，能说清它表示什么、还缺什么、下一步查哪里。先修为[仿真一步](01-simulation-step.md)与[外层/内层](05-nonlinear-and-linear.md)，其余单元按需回查。

## 先读角色，再读数字

用如下顺序还原实验身份：

```text
对象与任务 → 引擎/core/运行路径 → 物理模型
          → 离散与求解层级 → 设备、精度、预算
          → 有效读回 → 观测、协议与结果
```

例如 `SuperDex / Newton / GMRES / C1_REGULARIZED / FP64` 可以读为：指定引擎中请求 Newton 外层、GMRES 线性子求解、相应摩擦正则化和精度身份。还缺版本、构建、对象、材料、步长、停止条件与实际执行证据。它没有声明已经通过哪项物理验收。

## 六张配置阅读卡

| 引擎 | 这一行首先要拆开什么 | 最容易漏掉的边界 | 固定导读 |
|---|---|---|---|
| MuJoCo | CG/Newton/PGS 约束方法；cone；Euler/implicitfast | CG 是非线性方法；旧 3.11/3.14 与本课 3.15 不能共用默认值补历史配置；SolverMuJoCo 路径仍需身份 | [MuJoCo][mujoco] |
| SuperDex | 外层 Newton/BFGS/SR1、13 个线性选项、AUTO、摩擦、壳与 FP64 | 配置标签不是执行分支；assembly period=1 的已测 BFGS/SR1 有 Newton 等价限定；五个 CUDA 选项有特定 wheel 的准入拒绝 | [SuperDex][superdex] |
| Genesis | PBD 柔性路径；CG/Newton、cone、Signorini/convex；积分与耦合 | 合法组合有约束；PBD、刚体接触与 rigid coupling 不是同一个求解问题 | [Genesis][genesis] |
| Newton Physics | Featherstone/SemiImplicit/XPBD/VBD/Kamino 系统；DVI/PADMM；柔性路径；Euler 与 sweeps | Newton 是项目名；VBD 分支需显式记录；1.6.1 与历史 dev 版本分开 | [Newton Physics][newton] |
| PhysX | PGS/TGS；patch friction；surface cloth；两个更新开关 | 课程头文件 5.11.0、新斜面 SDK 5.9.0 与旧宿主 core 未知属于不同身份；旧缺项不能由新默认值补齐 | [PhysX][physx] |
| Drake | SAP；point/hydroelastic；kSap/kSimilar/kLagged | 接触近似和 solver 不同级；严格 hydroelastic 与 fallback 分开；not qualified 不等于从未运行 | [Drake][drake] |

这些固定链接指向本批已推送的课程提交，各原生导读包含官方源码和冻结 DexLab 报告。PR 待合并状态与课程内容存在分开记录。实验版本完整列在[来源页](source-versions.md)，全部词表条目在[术语索引](term-index.md)。

## 如何选择第一份候选配置

先提出任务所需能力：是关节刚体接触、布料、自接触还是体材料？控制需要力、力矩、位置目标还是逐节点输入？输出需要哪些状态、接触冲量或反作用？排除无法表达任务输入/观测的路径后，再看原生模型与可用配置。

选择一份有清楚版本和证据的起点，写下需要改变的因素及预期观察。若没有相同任务与协议的证据，就将其标为候选，而非推荐排名。本课不提供某引擎在全部抓取任务最优的结论。

| 你想回答的问题 | 可比较的单位 | 应保持或说明的条件 |
|---|---|---|
| 为新任务选一个系统 | 一整套版本化配置 | 能力、模型、成本和证据边界允许不同，但要明确 |
| 判断一种算法是否改善求解 | 尽量固定的问题与受控方法变化 | 模型、离散、输入、停止/误差定义和观测；不可控差异单列 |
| 判断策略迁移为何退化 | 任务、环境、控制与策略共同路径 | 动作尺度、控制频率、观测时刻、随机化、模型与训练协议 |

## 联合诊断案例：抓住以后滑落

已有日志只有 `mu=0.5, iterations=100`，两个引擎结果不同。先收集四组信息：

1. **输入与模型：** 物体尺度、质量/惯量、碰撞形状、夹爪控制模式、实际驱动力和接触材料组合。
2. **时间：** 动作保持、物理步长、内部子步和观测阶段，确认同一物理时长。
3. **求解：** 算法角色、实际分支、预算/容差、停止原因，区分哪一个循环的 100 次。
4. **证据：** 独立位移/保持结果、力与冲量有效性、未观测项，以及原失败记录。

随后才选择有限对照。比如在控制和模型固定时检查预算敏感性；若实际力不足以产生法向支撑，优先解释控制和模型。以上是诊断程序，没有执行新实验，也没有提前规定失败来自哪个 solver。

## 练习与答案

1. **SAP、kLagged、hydroelastic 三种 solver 各跑一次，应如何重写？** SAP 是 solver，kLagged 是离散接触近似，hydroelastic 是接触模型；先组合成明确配置，再声明要比较的因素。
2. **AUTO、CG、CUDA_CG 三个标签能算三种已执行算法吗？** 不能。AUTO 是选择规则，CUDA_CG 带实现路径；需读回实际分支与构建准入，重复执行身份不能凭标签增计。
3. **某引擎九个正例六 PASS 三 FAIL，能否写支持六种任务？** 不能；工况数、任务家族、准入与结果分别计数，原协议的分母不可改写。
4. **后续复现应首先写哪份记录？** 冻结任务/配置/版本、输入与观测协议、验收和预算，然后保留所有通过、失败、未运行及阻塞原因。

## English summary

Read each row as a versioned configuration with distinct implementation, model, solver, integration, precision and evidence roles. The six cards connect shared lessons to pinned native guides. System selection, controlled algorithm attribution and policy-transfer diagnosis answer different questions. The frozen vocabulary is fully indexed; source/static coverage does not establish new physical qualification.

[mujoco]: https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md
[superdex]: https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
[newton]: https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md
[physx]: https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md
[drake]: https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md
