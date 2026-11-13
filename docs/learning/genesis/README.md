# Genesis Atlas

**理解 Genesis 的建模、控制、物理机制与源码实现。**

[English](README.en.md) · [入门导读](docs/guide.md) · [完整课程路线](docs/curriculum.md) · [源码地图](docs/source-map.md) · [版本](docs/versions.md) · [开发任务](docs/roadmap.md) · [系列学习首页](https://github.com/huangkiki/sim-atlas) · [六仓总看板](https://github.com/users/huangkiki/projects/2)

这是 **[Sim Atlas · 仿真图谱](https://github.com/huangkiki/sim-atlas)** 的独立社区学习仓库，重点覆盖 Scene/Simulator/Entity、刚体与多物理求解器、批量环境、渲染与可微限制。

提供两条完整路线：**A 应用路线**从对象与建模走向控制、机器人、传感器、学习接口与数据；**B 原理与源码路线**解释动力学、接触模型、求解器、积分、观测及扩展。当前已交付首篇导读、固定版本源码地图，[E1 建模、坐标、状态与时间](docs/modeling-state-time.md)、[E2 驱动、机器人与任务接口](docs/control-robotics-tasks.md)、[E3 接触、求解器与力观测](docs/contact-solvers-forces.md)、[E4 传感器、渲染与可视化](docs/sensors-rendering.md)、[E5 批量、学习接口与数据](docs/batch-learning-data.md)及 [E6 多物理、可微与扩展边界](docs/extensions-boundaries.md)专题；完整课程仍在开发。

## 从这里开始

1. 阅读[导读](docs/guide.md)，建立对象与调用关系。
2. 学习 [E1 专题](docs/modeling-state-time.md)，理解资产、惯量、状态、reset 与时间步，并查看[验收与限制](docs/e1-acceptance.md)。
3. 学习 [E2 专题](docs/control-robotics-tasks.md)，把关节映射、FK/IK、限幅驱动与任务时序串起来；[验收记录](docs/e2-acceptance.md)列明源码边界。
4. 学习 [E3 专题](docs/contact-solvers-forces.md)，追踪材料、约束装配、Newton/CG、积分与接触力；[验收记录](docs/e3-acceptance.md)区分源码结论与运行证据。
5. 学习 [E4 专题](docs/sensors-rendering.md)，区分RGB、轴深度/射线距离、分割ID、力/触觉与缓存时序；[验收记录](docs/e4-acceptance.md)保留渲染和可微边界。
6. 学习 [E5 专题](docs/batch-learning-data.md)，理解环境隔离、终止观测、随机化、张量所有权与记录回放；[验收记录](docs/e5-acceptance.md)区分源码、语法与未进行的训练/性能验证。
7. 学习 [E6 专题](docs/extensions-boundaries.md)，沿实体分派、材料消费者、耦合顺序与反向路径判断多物理组合；[验收记录](docs/e6-acceptance.md)区分执行链、缺项和未做的运行验证。
8. 跟随[源码地图](docs/source-map.md)，在固定提交中核对原生字段、配置和执行路径。
9. 按[课程路线](docs/curriculum.md)选择应用或原理专题；需要环境时看[安装说明](docs/installation.md)。

当前先完成引擎知识体系与源码课程。最小 API 片段服务于理解，运行状态逐项注明；本轮没有新增仿真实验、训练、基准或独立评分器。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的版本、配置和工况记录。

## 维护与来源

每章保留原生 API、版本化来源、易错点和阅读练习。各 Atlas 仓库独立，不需要安装其他 Atlas 或 DexLab。教程进度和 DexLab 实验证据覆盖分别记录，不据此给引擎排名。

[官方源码基线](https://github.com/Genesis-Embodied-AI/genesis-world/tree/216a708e06124595521a9d36a51fae5393fd4ff8) · [贡献](CONTRIBUTING.md) · [来源与许可](THIRD_PARTY.md)
