# 先学 Physics-Based Simulation，再读引擎配置

[学习首页](../README.md) · [Solver 教程](solver-guide/README.md) · [引擎双路线](learning-paths.md)

本系列以 **[Physics-Based Simulation](https://phys-sim-book.github.io/)** 作为物理仿真先修主线。这是 Chenfanfu Jiang、Minchen Li 等人合著的开放在线教材；[Jiang 的个人主页](https://www.math.ucla.edu/~cffjiang/index.html)直接链接此书，完整作者名单见[前言](https://phys-sim-book.github.io/)。2026-10-14 核对时，在线前言标注版本 1.0.3（2026/3）。

面向已有 VLA、WAM、RL 经验的工程师与硕博，建议先建立“状态和方程怎样变成计算”的理解，再进入 solver 名称和引擎参数。**本页提供中文学习路线、原创自测与课程衔接；正文阅读使用原书。** 书中的优化式固体仿真与 IPC 是重要主线，六引擎仍需按各自模型和源码解释。

## 第一轮：先把一步仿真读懂

按书中前四章顺序阅读；每次读完一个环节，再用本系列样章检查能否解释机器人场景。无需先安装六个引擎。

| 顺序 | 原书入口 | 阅读时抓住的问题 | 本系列衔接 |
|---|---|---|---|
| 1 | [第 1 章：空间与时间的离散化][ch1] | 几何、位置和速度怎样表示？连续运动如何变成一次更新？显式和隐式的未知量在哪里？ | [仿真一步](solver-guide/01-simulation-step.md)，再看引擎 A1/A2、B0/B1/B4 |
| 2 | [第 2 章：优化框架][ch2] | 惯性、势能、边界与接触怎样进入所研究的离散问题？目标函数的变量是什么？ | 标注模型、离散化和求解方法各自负责什么 |
| 3 | [第 3 章：Projected Newton][ch3] | 为什么不能只写一个 Newton 更新式？局部矩阵和线搜索分别处理什么问题？ | [外层非线性与内层线性](solver-guide/05-nonlinear-and-linear.md) |
| 4 | [第 4 章：二维质点弹簧][ch4] | 沿一个小模型追踪能量、梯度、矩阵、状态写回与显示 | 阅读官方实现；画出一步的数据流 |

碰到线性系统不熟时，按需穿插[第 37 章][linear]，再返回第 3–4 章。这里把它作为数学补充，是本系列为机器人学习读者安排的顺序；原书目录仍保留它在 Special Topics 中的位置。

本阶段的交付是可解释的方程、源码调用链和纸面算例。原书提供 CPU Python 与 GPU 实现入口，但本轮不把下载、阅读或语法检查记录为运行成功。运行教程示例和各引擎原生验收留在后续执行阶段。

## 第二轮：接触与摩擦

沿原书第 5–11 章的边界处理顺序阅读，重点串起：约束边界 → [距离屏障（第 7 章）][barrier] → [过滤线搜索与 CCD（第 8 章）][ccd] → [摩擦（第 9 章）][friction] → [斜面案例（第 10 章）][slope]。第 5–6 章和第 11 章的入口在[原书完整目录](https://phys-sim-book.github.io/toc.html)。

每读完一节，写下四件事：要约束的物理量、采用的近似、影响近似的参数、怎样观察误差。然后回到[共同基础第 5 节](foundations.md#5-接触模型与数值近似--a4--b2--b3)，辨认 Coulomb 摩擦、摩擦锥、接触柔顺和数值正则化的角色。

原书斜面案例提供阅读和分析线索；[DexLab](dexlab.md)有自己的版本、模型与实验协议。两个案例的几何、材料、驱动、采样和验收条件没有对齐之前，不能合成一组比较或把书中演示当作 DexLab 的复现证据。

## 第三轮：按研究对象深入

前两轮完成后可选择一条专题线；需要连续介质背景时，先补齐对应前置章节。下表是本系列的阅读安排，不是原书对六引擎的支持矩阵。

| 研究对象 | 原书章节 | 进入引擎课程前的自查 |
|---|---|---|
| 弹性体与有限元 | 12–15 超弹性 → 16–18 控制方程 → 19–24 有限元及接触；从[运动学][elastic]开始 | 能区分变形、材料本构、空间离散和非线性求解吗？ |
| 刚体与降阶 | 补足所需弹性/离散背景后读[25 刚体与仿射体][rigid] → 26 模态降阶 | 减少的是哪类自由度？与机器人关节坐标有什么不同？ |
| 大变形、塑性与粒子网格 | 补足材料与离散背景后读[27–31 MPM][mpm] | 能画出粒子到网格、网格更新、回传的阶段，以及材料历史的归属吗？ |
| 布料与位置约束 | [32 PBD/XPBD][pbd] → 33 布料 → 34 网格 → 35 流体 → 36 其他约束 | 能区分预测位置、约束投影、柔顺参数和迭代预算吗？ |

随后进入[六引擎原生课程](learning-paths.md)：本书帮助形成问题和数学语言，各引擎仓回答具体字段、默认值、分派和版本限制，Robot Learning 负责环境与策略训练流程。

## 从书到 solver 表，需要保留的差异

| 书中建立的概念 | 读 DexLab 配置表时继续核对 |
|---|---|
| 非线性优化与 Newton 局部步 | MuJoCo 的 Newton/非线性 CG 与 SuperDex 的外层/内层并不解同一个问题；Newton Physics 还是项目名称 |
| 线性系统与 CG | 线性 CG 的矩阵假设、非线性 CG 的目标与线搜索分别是什么 |
| IPC、距离屏障与摩擦近似 | 原书公式不直接替代 Signorini、MuJoCo 接触模型、Drake hydroelastic 或 PhysX patch friction |
| PBD/XPBD、MPM、有限元 | 这些方法对应的状态、材料和耦合路径；不是只凭名称就可互换的刚体 solver |
| 一份可阅读的 CPU/GPU 实现 | 算法、实现后端、精度、有效配置、实际运行与物理资格各有哪些证据 |

原书没有承担本系列全部专有枚举的说明；BFGS/SR1、TGS、SAP、Kamino/DVI/PADMM、CUDA 变体等继续由[Solver 教程](solver-guide/README.md)与固定引擎源码补齐。[版本对照](solver-guide/source-versions.md)保留教材版本、课程源码与 DexLab 历史运行身份的区别。

## 学完前两轮，用五个问题自测

以下问题和答案是本系列原创的阅读检查，不是原书习题答案。

1. **步长减半、每步迭代上限翻倍，是否表示相同计算量？** 不表示；物理时间覆盖、每轮工作和提前停止都要分别计算。先说明控制周期内执行多少物理步。
2. **Newton 外层调用线性 CG，为什么不是二选一？** 外层更新非线性状态，内层近似求局部方向；线性系统小残差不等于更新后的非线性问题已经收敛。
3. **两个时刻的物体都未穿透，能否排除中间穿过障碍？** 不能；端点检查没有覆盖其间轨迹，需分析所用轨迹和连续碰撞检测条件。
4. **摩擦系数相同，两个引擎的接触响应就等价吗？** 不能；还须对齐法向模型、摩擦近似、参数单位、几何和时间离散，并取得相应响应证据。
5. **读懂书中 MPM 或 XPBD，能否直接确认某引擎某版本的选项可用？** 不能；还需查原生材料/对象支持、配置限制、实际分支和运行记录。

能解释答案后进入 solver 配置解读；若只能记住名称，返回对应原书章节补齐推导。实践阶段另记录运行环境与结果，本轮仍是来源核对和静态学习。

## 来源版本与许可

本次路线根据 2026-10-14 读到的[在线目录](https://phys-sim-book.github.io/toc.html)和官方 Markdown 仓库建立。固定源码为 [`18c637eb6a7016814ac2a04e98798be0ed9b82b1`](https://github.com/phys-sim-book/mdbook-src/tree/18c637eb6a7016814ac2a04e98798be0ed9b82b1)，[SUMMARY.md](https://github.com/phys-sim-book/mdbook-src/blob/18c637eb6a7016814ac2a04e98798be0ed9b82b1/src/SUMMARY.md)用于追溯章节映射；在线书可能继续更新。核对范围与 Git blob 见[来源记录](physics-based-simulation-sources.json)。

原书许可证为 [CC BY-NC-SA 4.0](https://github.com/phys-sim-book/mdbook-src/blob/18c637eb6a7016814ac2a04e98798be0ed9b82b1/LICENSE)。本仓提供链接、独立学习安排和原创衔接材料；原书正文、图像及其许可保留在上游，不随本仓 Apache-2.0 改授许可。未复制整书，也未将本系列标为官方课程。详见[来源与许可](../THIRD_PARTY.md)。

## English reading guide

Start with *Physics-Based Simulation*, coauthored by Chenfanfu Jiang, Minchen Li and colleagues. Read chapters 1–4, using chapter 37 when linear algebra needs reinforcement, then chapters 5–11 on boundaries and frictional contact. Continue with elasticity/FEM, rigid and reduced models, MPM or PBD according to your research problem. This is Sim Learning's independent study route, with original checkpoints and links to native engine lessons. The book's optimization/IPC formulation does not define every engine's contact model. Reading and static checks remain distinct from execution and qualification.

[ch1]: https://phys-sim-book.github.io/simulation-with-optimization/discrete-space-and-time/discrete_space_time.html
[ch2]: https://phys-sim-book.github.io/simulation-with-optimization/optimization-framework/opt_framework.html
[ch3]: https://phys-sim-book.github.io/simulation-with-optimization/projected-newton/projected_Newton.html
[ch4]: https://phys-sim-book.github.io/simulation-with-optimization/case-study-2d-mass-spring/2d_mass_spring.html
[linear]: https://phys-sim-book.github.io/special-topics/linear-system/linear_sys.html
[barrier]: https://phys-sim-book.github.io/boundary-treatments/distance-barrier-for-nonpenetration/dist_barrier.html
[ccd]: https://phys-sim-book.github.io/boundary-treatments/filter-line-search/filter_line_search.html
[friction]: https://phys-sim-book.github.io/boundary-treatments/frictional-contact/friction.html
[slope]: https://phys-sim-book.github.io/boundary-treatments/case-study-square-on-slope/square_on_slope.html
[elastic]: https://phys-sim-book.github.io/hyperelasticity/kinematics-theory/kinematics.html
[rigid]: https://phys-sim-book.github.io/spatial-reductions/rigid-body-simulation/rigid_body_sim.html
[mpm]: https://phys-sim-book.github.io/material-point-method/spatial-and-temporal-discretization/mpm_disc.html
[pbd]: https://phys-sim-book.github.io/position-based-simulations/position-based-dynamics-pbd/position_based_dynamics.html
