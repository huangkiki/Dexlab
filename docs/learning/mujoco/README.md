# MuJoCo Atlas

**理解 MuJoCo 的建模、控制、物理机制与源码实现。**

[English](README.en.md) · [系列学习首页](https://github.com/huangkiki/sim-atlas) · [入门导读](docs/guide.md) · [完整课程路线](docs/curriculum.md) · [源码地图](docs/source-map.md) · [版本](docs/versions.md) · [开发任务](docs/roadmap.md) · [六仓总看板](https://github.com/users/huangkiki/projects/2)

这是 **[Sim Atlas · 仿真图谱](https://github.com/huangkiki/sim-atlas)** 的独立社区学习仓库，重点覆盖 MJCF、mjSpec/mjModel/mjData、驱动器与约束、flex/IPC、原生与 GPU 后端。

提供两条完整路线：**A 应用路线**从对象与建模走向控制、机器人、传感器、学习接口与数据；**B 原理与源码路线**解释动力学、接触模型、求解器、积分、观测及扩展。已交付首篇导读、E1 建模/坐标/状态/时间、E2 驱动/机器人/任务、E3 动力学/接触/求解/力观测、E4 传感器/相机/渲染、E5 批量/学习/数据、E6 插件/flex/IPC/后端专题与固定版本源码地图，完整课程仍在开发。

## 从这里开始

1. 阅读[导读](docs/guide.md)，建立对象与调用关系。
2. 阅读 [E1 建模与坐标](docs/modeling-and-frames.md)、[状态与时间](docs/state-and-time.md)，完成带答案的阅读练习；[原创片段](examples/modeling-state-time/README.md)尚未运行。
3. 阅读 [E2 驱动与控制](docs/actuation-and-control.md)、[机器人运动学](docs/robotics-and-kinematics.md)、[任务接口](docs/task-interfaces.md)，从控制输入追到原生执行与可靠阶段转移。
4. 阅读 [E3 动力学执行链](docs/dynamics-and-pipeline.md)、[接触模型](docs/contact-models.md)、[求解与积分](docs/solvers-and-integration.md)、[力观测](docs/force-observations.md)，把配置、算法与读数契约连起来。
5. 阅读 [E4 传感与采样](docs/sensors-and-sampling.md)、[相机与几何查询](docs/cameras-and-geometry-queries.md)、[渲染与 viewer](docs/rendering-and-viewer.md)，区分读数、射线、图像、窗口及其时序与资源。
6. 阅读 [E5 CPU批量](docs/cpu-batching.md)、[MJX与设备数据](docs/mjx-and-device-data.md)、[学习与随机化](docs/learning-and-randomization.md)、[记录与回放](docs/recording-and-replay.md)，明确世界隔离、任务时序、随机参数与恢复边界。
7. 阅读 [E6 回调与插件](docs/extensions-and-callbacks.md)、[flex与弹性](docs/flex-and-elasticity.md)、[IPC](docs/ipc-contact-mode.md)、[后端与可微边界](docs/backends-and-differentiation.md)、[多物理/源码追踪](docs/multiphysics-and-source-trace.md)，从扩展状态追到求解与实际支持范围。
8. 跟随[源码地图](docs/source-map.md)，在固定提交中核对原生字段、配置和执行路径。
9. 按[课程路线](docs/curriculum.md)选择应用或原理专题；需要环境时看[安装说明](docs/installation.md)。

当前先完成引擎知识体系与源码课程。最小 API 片段服务于理解，运行状态逐项注明；本轮没有新增仿真实验、训练、基准或独立评分器。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的版本、配置和工况记录。

E1 的验收与限制见[验证记录](docs/validation/e1.md)：仅源码核对、文档链接、Python 语法及 XML 结构检查；未编译模型或开展仿真。A1/A2 已交付；B0/B4 的基础在 E3 继续完成。

E2 已展开 A3/A5/A7，包括多输入 actuator、限幅顺序、原生 Jacobian、带失败返回的局部 IK 和任务时序；[验证记录](docs/validation/e2.md)明确未运行模型、IK 或抓取。

E3 已完成 A4/B0–B5 的主线课程，包括本版材料组合、三类 solver 的实际终止与 warmstart、五种积分器/有效 metric、净接触力与 frame/时点；[验证记录](docs/validation/e3.md)仅为源码与静态验收，无接触/求解实验。Flex/IPC 内循环与 GPU 后端扩展在 E6 继续展开。

E4 已完成 A6 原生传感、history、相机投影/几何查询、classic RGB/depth/分割与 viewer/headless 生命周期；附固定版本差异和 Filament 接口边界。[验证记录](docs/validation/e4.md)与[原创片段](examples/sensing-rendering/README.md)仅为源码和静态验收，没有 import 引擎或创建渲染 context。

E5 已完成 A8/A9 与 B6 的批量/JIT/传输/数据主线，明确原生CPU、MJX JAX、MJX Warp与外部学习系统的身份；含32道带答案练习。[验证记录](docs/validation/e5.md)和[原创批量片段](examples/batch-learning-data/README.md)仅为源码与静态验收，没有运行批量、JIT、随机化、训练或数据生成。JAX另固定阅读来源，不宣称依赖组合已运行验证；插件/flex/IPC与后端内部机制继续见E6。

E6 已完成 B6 扩展与 B7 源码综合追踪：插件状态/生命周期、flex 材料与有效metric、IPC的AL/CCD和部分推进、CPU有限差分/MJX实际AD边界、流体近似与外部多物理归属；含40道带答案练习。[验证记录](docs/validation/e6.md)与[原创flex片段](examples/extensions-boundaries/README.md)仅做源码与静态验收。A0完整安装和全路线审校/DexLab证据入口仍留E7。

## 维护与来源

每章保留原生 API、版本化来源、易错点和阅读练习。各 Atlas 仓库独立，不需要安装其他 Atlas 或 DexLab。教程进度和 DexLab 实验证据覆盖分别记录，不据此给引擎排名。

[官方源码基线](https://github.com/google-deepmind/mujoco/tree/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5) · [贡献](CONTRIBUTING.md) · [来源与许可](THIRD_PARTY.md)
