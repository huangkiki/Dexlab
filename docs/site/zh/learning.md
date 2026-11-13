# 仿真学习

从一个研究结论出发，读懂背后的物理和引擎实现。共同基础、Solver 教程和六个引擎的现有课程都可以在这里连续阅读，无需安装环境。

## 从哪里开始

- **先建立直觉：**[Physics-Based Simulation 中文伴读](learn/sim/docs/physics-based-simulation.md)，把状态、时间、动力学和优化连起来。
- **带着接触问题读：**[九单元 Solver 教程](learn/sim/docs/solver-guide/README.md)，从仿真一步到接触、摩擦、约束和求解。
- **查一个概念：**[共同基础](learn/sim/docs/foundations.md)和[术语索引](learn/sim/docs/solver-guide/term-index.md)。
- **选一条主线：**[应用与原理两条路线](learn/sim/docs/learning-paths.md)，按自己的基础和问题继续。

## 选择一个引擎

每个目录都通向完整章节。应用路线解释模型、状态、控制与观测；原理路线解释动力学、接触、求解与源码。课程目录保留已交付和待开发的区别。

| 引擎 | 从这里深入 |
| --- | --- |
| [MuJoCo](learn/mujoco/docs/curriculum.md) | MJCF、状态与驱动器、软接触、求解与积分 |
| [SuperDex](learn/superdex/docs/curriculum.md) | Scene / Actor、接触几何、隐式求解与力观测 |
| [Genesis](learn/genesis/docs/curriculum.md) | Scene / Entity、多物理、批量状态与控制 |
| [Newton Physics](learn/newton/docs/curriculum.md) | ModelBuilder、State / Control、Warp 与各 Solver 的边界 |
| [PhysX](learn/physx/docs/curriculum.md) | Scene / Actor / Shape、articulation、PGS / TGS |
| [Drake](learn/drake/docs/curriculum.md) | Systems / Context、MultibodyPlant、接触与优化 |

## 把知识带回研究

[摩擦与接触力矩](learn/sim/docs/solver-guide/03-friction.md) → [Wuji 抓持对照](wuji-contact.md) · [变形体与耦合](learn/sim/docs/solver-guide/07-representations.md) → [布料实验](cloth-comparison.md) · [状态与观测](learn/sim/docs/solver-guide/01-simulation-step.md) → [LIBERO 记录检查](libero-workflow.md)

课程正文来自 Sim Learning 及六个引擎的独立社区课程，保留原文、版本和验证边界。每篇文末提供来源与许可；需要检查源码时可再进入 GitHub。[关于课程](learn/sim/README.md) · <a href="index.html#blog">回到研究 Blog</a>

```{toctree}
:hidden:
:maxdepth: 2

共同基础与 Solver 教程 <learn/sim/README>
MuJoCo <learn/mujoco/docs/curriculum>
SuperDex <learn/superdex/docs/curriculum>
Genesis <learn/genesis/docs/curriculum>
Newton Physics <learn/newton/docs/curriculum>
PhysX <learn/physx/docs/curriculum>
Drake <learn/drake/docs/curriculum>
```
