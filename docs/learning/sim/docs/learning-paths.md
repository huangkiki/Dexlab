# 两条路线，一张阅读地图

[回到首页](../README.md) · [共同基础](foundations.md) · [实验案例](dexlab.md)

先沿[Physics-Based Simulation 伴读路线](physics-based-simulation.md)建立共同基础，再用[Solver 教程](solver-guide/README.md)练习配置解读。选定一个引擎后，在它的课程目录中按下列单元阅读。应用路线侧重建立正确的使用习惯；原理路线侧重解释输入、方程、实现和输出之间的关系。课程是学习地图，各仓目录才是具体章节及完成状态的来源。

## 应用路线 A

| 单元 | 要学会什么 | 学完时能够回答 |
|---|---|---|
| A0 · 安装与对象地图 | 辨认包、核心、后端与宿主；理解主要对象及生命周期 | 我安装和调用的是哪一层？谁拥有模型和状态？ |
| A1 · 模型、坐标与资产 | 单位、pose、惯量、关节、视觉/碰撞资产、导入与许可 | 同一个网格为何会有不同碰撞体和惯量？ |
| A2 · 状态与时间 | 配置/速度维度、状态写入、重置、快照、步进与采样 | 改了状态以后，哪些派生量需要重新计算？ |
| A3 · 驱动与控制 | 控制输入、驱动力、PD、饱和、回调与控制周期 | 我写的是目标、力还是状态？限制在何处生效？ |
| A4 · 接触 API | 碰撞过滤、接触读回、摩擦和柔顺参数的原生语义 | 这个接触量是哪两个对象之间、在哪个坐标系下？ |
| A5 · 机器人与运动学 | 导入与索引、FK/IK、限位、约束、外部控制接口 | 关节名称、配置地址、速度地址、驱动地址如何对应？ |
| A6 · 传感器与渲染 | 几何查询、物理传感器、相机、显示与离屏路径 | 输出的形状、单位、参考点和更新时间是什么？ |
| A7 · 任务编排 | 控制接口与状态机、进入/退出条件、日志时序 | 接近、闭合、保持、释放分别由谁推进、怎样判定？ |
| A8 · 并行与学习接口 | 批量隔离、设备数据、reset/step、终止/截断、随机种子 | 重置一个环境会影响谁？一步接口实际做了几次物理推进？ |
| A9 · 数据与 sim-to-real | 时间戳、元数据、回放、随机化与模型差距 | 这份数据足够解释或复现什么，哪些条件还缺失？ |

A0–A2 是使用基础；A3–A5 建立机器人与接触接口；A6–A9 组织观测、任务与数据。A7 可以先用纸上状态机和代码阅读学习，当前不要求新的抓取实验或策略训练。

## 原理与源码路线 B

| 单元 | 重点 | 应当追到的源码证据 |
|---|---|---|
| B0 · 动力学与数据结构 | 配置空间、广义速度/力、惯量、约束、空间向量、内存布局 | 字段定义、维度/地址生成和实际消费者 |
| B1 · 一步仿真的源码 | 入口、碰撞、装配、求解、积分、更新顺序 | 一条从公开 step 到状态更新的调用链 |
| B2 · 接触模型与组合律 | 几何、法向/摩擦、材料组合、柔顺与正则化 | 参数如何组合、进入哪条力律或约束式 |
| B3 · 求解器与线性代数 | 目标/方程、残差、线性子问题、warm start、岛与终止 | solver 分派、迭代循环、收敛判断、实际预算 |
| B4 · 积分与数值语义 | 积分器/求解器/子步、精度与稳定性假设、可微边界 | 状态更新公式、导数近似和配置限制 |
| B5 · 力与冲量观测 | 广义/空间/约束量、换坐标与换参考点、采样时刻 | 返回量的产生位置、单位、平均窗口与近似 |
| B6 · 性能、并行与扩展 | 编译/JIT、拷贝、批量、线程、回调与插件 | 所有权、同步点、扩展入口和支持边界 |
| B7 · 源码综合导读 | 把模型、输入、求解与观测连起来 | 一条能逐段解释的完整路径，以及 DexLab 对应证据 |

建议先熟悉所选引擎 A0–A4，再按 B0 → B1 → B2/B3/B4 → B5 → B6/B7 阅读。B4 的时间基础会提前在 A2 出现；同一单元可以由多个专题共同完成，课程目录会保留剩余部分。

## 去哪个仓库读？

| 引擎 | 双路线目录 | 固定版本与源码入口 |
|---|---|---|
| MuJoCo | [课程](https://github.com/huangkiki/mujoco-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/mujoco-learning/blob/main/docs/source-map.md) |
| SuperDex | [课程](https://github.com/huangkiki/superdex-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/superdex-learning/blob/main/docs/source-map.md) |
| Genesis | [课程](https://github.com/huangkiki/genesis-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/genesis-learning/blob/main/docs/source-map.md) |
| Newton Physics | [课程](https://github.com/huangkiki/newton-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/newton-learning/blob/main/docs/source-map.md) |
| PhysX | [课程](https://github.com/huangkiki/physx-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/physx-learning/blob/main/docs/source-map.md) |
| Drake | [课程](https://github.com/huangkiki/drake-learning/blob/main/docs/curriculum.md) | [源码地图](https://github.com/huangkiki/drake-learning/blob/main/docs/source-map.md) |

每个课程单元使用本引擎的 API、数据结构和限制；本系列不要求安装其他 Learning 仓库，也没有跨引擎运行封装。

## 课程单元与开发阶段怎样对应？

A/B 是读者路线，E0–E7 是维护者拆分的交付阶段。E1 交付建模和状态基础；E2 交付驱动、机器人与任务；E3 深入接触数值；E4 交付观测；E5 交付批量与数据；E6 深入特色与扩展；E7 对照全部单元审校。阶段依赖见各仓 roadmap 和 [总看板](https://github.com/users/huangkiki/projects/2)。

看到“源码核对通过”时，它意味着固定版本中的定义/路径已阅读；看到“语法检查通过”时，它意味着片段能被解析。模型编译、运行结果、性能和物理可靠性必须另有相应证据。当前路线允许通过静态阅读练习前进，实验以后对接 DexLab。
