# SuperDex Atlas

**理解 SuperDex 的建模、控制、物理机制与源码实现。**

[English](README.en.md) · [入门导读](docs/guide.md) · [完整课程路线](docs/curriculum.md) · [源码地图](docs/source-map.md) · [版本](docs/versions.md) · [开发任务](docs/roadmap.md) · [六仓总看板](https://github.com/users/huangkiki/projects/2) · [系列学习首页](https://github.com/huangkiki/sim-atlas)

这是 **[Sim Atlas · 仿真图谱](https://github.com/huangkiki/sim-atlas)** 的独立社区学习仓库，重点覆盖 Physics/Robotics/Studio 的边界、Scene/Actor、接触几何、精度与可微求解。

提供两条完整路线：**A 应用路线**从对象与建模走向控制、机器人、传感器、学习接口与数据；**B 原理与源码路线**解释动力学、接触模型、求解器、积分、观测及扩展。当前已提供首篇导读、[E1 建模/坐标/状态/时间专题](docs/modeling-state-time.md)、[E2 驱动/机器人/任务接口专题](docs/control-robotics.md)、[E3 接触/求解器/力观测专题](docs/contact-solvers-forces.md)、[E4 传感器/渲染专题](docs/sensors-rendering.md)、[E5 批量/学习/数据专题](docs/batch-learning-data.md)、[E6 特色Actor/可微/能力边界专题](docs/extensions-boundaries.md)和固定版本源码地图；A0安装专题及双路线最终审校仍待E7。

## 从这里开始

1. 阅读[导读](docs/guide.md)，建立对象与调用关系。
2. 阅读[E1 专题](docs/modeling-state-time.md)，理解原生坐标、惯量、URDF 限制、状态所有权、快照和积分时间；[验证范围](docs/validation-e1.md)单独记录。
3. 阅读[E2 专题](docs/control-robotics.md)，区分 JSC/OSC、隐式 pose tracking、IK、驱动力限额及应用任务调度。
4. 阅读[E3 专题](docs/contact-solvers-forces.md)，核对材料组合、隐式积分、残差终止与接触力采样；[验证边界](docs/validation-e3.md)明确区分源码和运行证据。
5. 阅读[E4 专题](docs/sensors-rendering.md)，区分 CameraSensor 元数据、物理查询与宿主图像，核对 RGB/depth/分割/射线/力/触觉边界、坐标和帧延迟；[验收记录](docs/validation-e4.md)注明未运行渲染。
6. 阅读[E5 专题](docs/batch-learning-data.md)，追踪独立/共享 Scene、两级 vector、seed 与 autoreset、CPU/GPU 拷贝、学习/求导边界及录制回放；[验收记录](docs/validation-e5.md)注明未运行或训练。
7. 阅读[E6 专题](docs/extensions-boundaries.md)，理解软体/薄壳/杆/ROM、构建与绑定门限、有限差分HVP/adjoint及完整Jacobian的不同支持范围；[静态验收](docs/validation-e6.md)明确未求解梯度。
8. 跟随[源码地图](docs/source-map.md)，在固定提交中核对原生字段、配置和执行路径。
9. 按[课程路线](docs/curriculum.md)选择应用或原理专题；需要环境时看[安装说明](docs/installation.md)。

当前先完成引擎知识体系与源码课程。最小 API 片段服务于理解，运行状态逐项注明；本轮没有新增仿真实验、训练、基准或独立评分器。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的版本、配置和工况记录。

## 维护与来源

每章保留原生 API、版本化来源、易错点和阅读练习。各 Atlas 仓库独立，不需要安装其他 Atlas 或 DexLab。教程进度和 DexLab 实验证据覆盖分别记录，不据此给引擎排名。

[官方源码基线](https://github.com/facebookresearch/project_superdex/tree/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6) · [贡献](CONTRIBUTING.md) · [来源与许可](THIRD_PARTY.md)
