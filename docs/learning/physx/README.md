# PhysX Atlas

**理解 PhysX 的建模、控制、物理机制与源码实现。**

[Sim Atlas 系列首页](https://github.com/huangkiki/sim-atlas) · [English](README.en.md) · [入门导读](docs/guide.md) · [完整课程路线](docs/curriculum.md) · [源码地图](docs/source-map.md) · [版本](docs/versions.md) · [开发任务](docs/roadmap.md) · [六仓总看板](https://github.com/users/huangkiki/projects/2)

这是 **[Sim Atlas · 仿真图谱](https://github.com/huangkiki/sim-atlas)** 的独立社区学习仓库，重点覆盖 C++ SDK、Scene/Actor/Shape/Material、articulation、PGS/TGS 与宿主边界。

提供两条完整路线：**A 应用路线**从对象与建模走向控制、机器人、传感器、学习接口与数据；**B 原理与源码路线**解释动力学、接触模型、求解器、积分、观测及扩展。已交付首篇导读和 [E1 建模、坐标、状态与时间](docs/modeling-state-time.md)：从原生对象/资产到质心惯量、articulation 缓存与步进边界。[E2 驱动、机器人与任务接口](docs/control-robotics.md)已补齐原生输入、隐式 drive、资产/关节映射、FK/Jacobian 与任务调度。[E3 接触、求解器与力观测](docs/contact-solvers.md)继续追踪材料组合、PGS/TGS、积分与法向/切向冲量读回。[E4 传感、查询与调试显示](docs/sensors-rendering.md)讲清查询过滤/更新时间、力与加速度观测、PVD/OmniPVD 以及宿主 RGB/depth/分割的职责。[E5 批量、学习接口与数据](docs/batch-learning-data.md)继续解释 Scene 隔离、任务调度、Direct GPU 布局/同步、reset、随机化和对象序列化。[E6 原生扩展与能力边界](docs/extensions-boundaries.md)补齐自定义几何/约束/回调、配置到求解输出的追踪、公开 GPU/FEM/粒子实现与可微边界。A0 安装专题和 E7 双路线审校仍待完成；源码课程完成与实际运行验收分别记录。

## 从这里开始

1. 阅读[导读](docs/guide.md)，建立对象与调用关系。
2. 阅读 [E1 专题](docs/modeling-state-time.md)，对照 [C++ 片段](examples/e1_state_boundary.cpp)理解 Actor/Shape/COM、关节状态和采样阶段。
3. 继续 [E2 控制专题](docs/control-robotics.md)，区分状态、目标、力输入以及应用任务判断。
4. 阅读 [E3 接触专题](docs/contact-solvers.md)，辨清接触模型、求解器、内部小步与观测缺项。
5. 阅读 [E4 传感与显示专题](docs/sensors-rendering.md)，区分几何命中、动力学观测、调试图元与图像管线。
6. 阅读 [E5 批量与数据专题](docs/batch-learning-data.md)，理解学习应用如何组织原生对象、动作/观测和数据生命周期。
7. 阅读 [E6 扩展与能力边界](docs/extensions-boundaries.md)，从原生扩展协议追到约束行、GPU 与非刚体状态。
8. 跟随[源码地图](docs/source-map.md)，在固定提交中核对原生字段、配置和执行路径。
9. 按[课程路线](docs/curriculum.md)选择应用或原理专题；需要环境时看[安装说明](docs/installation.md)。

当前先完成引擎知识体系与源码课程。最小 API 片段服务于理解，运行状态逐项注明；本轮没有新增仿真实验、训练、基准或独立评分器。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的版本、配置和工况记录。

## 维护与来源

每章保留原生 API、版本化来源、易错点和阅读练习。各 Atlas 仓库独立，不需要安装其他 Atlas 或 DexLab。教程进度和 DexLab 实验证据覆盖分别记录，不据此给引擎排名。

[官方源码基线](https://github.com/NVIDIA-Omniverse/PhysX/tree/da950a3537927784951853c66618036f332ca0ce) · [贡献](CONTRIBUTING.md) · [来源与许可](THIRD_PARTY.md)
