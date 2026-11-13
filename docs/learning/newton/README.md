# Newton Physics Atlas

**理解 Newton Physics 的建模、控制、物理机制与源码实现。**

[English](README.en.md) · [Sim Atlas 系列首页](https://github.com/huangkiki/sim-atlas) · [入门导读](docs/guide.md) · [完整课程路线](docs/curriculum.md) · [源码地图](docs/source-map.md) · [版本](docs/versions.md) · [开发任务](docs/roadmap.md) · [六仓总看板](https://github.com/users/huangkiki/projects/2)

这是 **[Sim Atlas · 仿真图谱](https://github.com/huangkiki/sim-atlas)** 的独立社区学习仓库，重点覆盖 ModelBuilder/Model/State/Control/Contacts、Warp、solver 支持矩阵和多 world。

提供两条完整路线：**A 应用路线**从对象与建模走向控制、机器人、传感器、学习接口与数据；**B 原理与源码路线**解释动力学、接触模型、求解器、积分、观测及扩展。现已提供首篇导读、固定版本源码地图，以及 [E1：模型、坐标、状态与时间](docs/modeling-state-time.md)、[E2：控制、机器人与任务接口](docs/control-robotics-tasks.md)、[E3：接触、求解器与力观测](docs/contact-solvers-forces.md)、[E4：传感器、渲染与可视化](docs/sensors-rendering.md)、[E5：批量、学习接口与数据](docs/batch-learning-data.md)、[E6：特色求解、可微路径与原生扩展](docs/extensions-boundaries.md)。完整课程仍在开发；章节交付与运行验收分开记录。

## 从这里开始

1. 阅读[导读](docs/guide.md)，建立对象与调用关系。
2. 阅读 [E1 专题](docs/modeling-state-time.md)：从原生建模、资产与惯量，走到状态维度、双缓冲、采样和重置；配有 [API 例子](examples/e1_model_state.py)和[静态验收记录](docs/e1-validation.md)。
3. 阅读 [E2 专题](docs/control-robotics-tasks.md)：贯通 Drive/Control/solver、关节映射、目标 IK、工具坐标与任务阶段，附[验收记录](docs/e2-validation.md)。
4. 阅读 [E3 专题](docs/contact-solvers-forces.md)：从材料组合与碰撞生成，追到 XPBD/其他 solver 的迭代、积分与力读回；先看各后端的观测限制和[静态验收](docs/e3-validation.md)。
5. 阅读 [E4 专题](docs/sensors-rendering.md)：理解位姿/IMU/接触传感器、射线与相机的坐标、维度、更新时间和显示后端；附[静态验收](docs/e4-validation.md)。
6. 阅读 [E5 专题](docs/batch-learning-data.md)：理解多 world 分段、公共/后端 reset、Warp 复制与 graph、策略时序和原生记录回放；附[最小例子](examples/e5_world_reset_snapshot.py)和[静态验收](docs/e5-validation.md)。
7. 阅读 [E6 专题](docs/extensions-boundaries.md)：对照 VBD/Style3D/MPM/Kamino，理解原生耦合、完整梯度链和 B7 端到端源码追踪；附[阻力例子](examples/e6_differentiable_drag.py)和[静态验收](docs/e6-validation.md)。
8. 跟随[源码地图](docs/source-map.md)，在固定提交中核对原生字段、配置和执行路径。
9. 按[课程路线](docs/curriculum.md)选择应用或原理专题；需要环境时看[安装说明](docs/installation.md)。

当前先完成引擎知识体系与源码课程。最小 API 片段服务于理解，运行状态逐项注明；本轮没有新增仿真实验、训练、基准或独立评分器。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的版本、配置和工况记录。

## 维护与来源

每章保留原生 API、版本化来源、易错点和阅读练习。各 Atlas 仓库独立，不需要安装其他 Atlas 或 DexLab。教程进度和 DexLab 实验证据覆盖分别记录，不据此给引擎排名。

[官方源码基线](https://github.com/newton-physics/newton/tree/713fecdc41caf0c9d726f5c016939f36e66e3dff) · [贡献](CONTRIBUTING.md) · [来源与许可](THIRD_PARTY.md)
