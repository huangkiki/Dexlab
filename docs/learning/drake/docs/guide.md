# Drake 从 Systems 到接触求解

阅读基线：`1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，来源为官方固定源码。本篇是对象与关键机制导读，完整专题仍在开发；本轮仅做源码/文档核对，没有运行仿真实验。

## 1. 系统拓扑与运行上下文

[Diagram](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram.h) 连接系统和端口；[Context](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h) 保存运行时状态、参数、时间和缓存相关数据。一个系统对象与它的 Context 不可混为一体。读取子系统状态时要取得对应子 Context，不能随意把根 Diagram 的 Context 交给子系统接口。

[Simulator](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h) 推进系统的时间与事件；用户的控制器也是系统图的一部分。理解端口依赖、连续/离散状态、缓存和事件后，才能解释一次数据更新究竟发生在哪个阶段。

## 2. Plant、SceneGraph 与模型导入

[MultibodyPlant](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h) 描述多体动力学，[SceneGraph](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/scene_graph.h) 组织几何与查询；[Parser](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h) 导入模型。视觉、碰撞/接近查询与动力学惯量分别解释。

Finalize 是模型拓扑构建的重要边界；建模、端口连接、Context 创建与运行应按原生生命周期组织。关节、body/frame/model instance 的索引具有不同含义；资产导入后先核对坐标、惯量、限位和模型实例归属。

## 3. 连续与离散不是显示选项

Plant 的 time_step 控制离散或连续建模路径；本版本 C++ 与 Python 构造器均要求显式传值，只有 [MultibodyPlantConfig](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant_config.h) 提供 0.001 s 的默认配置。教程应显式说明所用构造入口和 time_step，详见[E1 状态与时间](state-time.md)。

连续动力学通常从加速度层解释；离散接触从时间步内的速度更新与约束问题解释。Simulator 的推进目标时间不等同于所有系统使用同一内部积分步长，离散更新与连续积分也要分开。

## 4. 接触几何、近似和 solver

本版本 ContactModel 列出 hydroelastic、point 和 hydroelastic-with-fallback 等接触表示；DiscreteContactSolver 枚举为 SAP；DiscreteContactApproximation 还区分 SAP、Similar、Lagged。它们回答不同问题，不能用一项取代另外两项。

从 [contact model 说明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h) 读几何与材料假设，再读 [compliant contact manager](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc) 和 [SAP solver](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.h)。追踪材料参数如何生成接触问题、正则化和时间离散如何进入求解、结果怎样回到 Plant。

此版本离散接触模型对摩擦系数的处理有具体限制，文档说明忽略静摩擦系数而使用动摩擦系数。不能以填入了一对静/动摩擦系数，就推断离散算法实现了同样的静动转换。

## 5. 控制、标量与优化边界

力输入端口、驱动器、状态反馈与直接状态设置分别解释。控制器的计算时刻和输出保持方式应与 Plant/Simulator 的离散时序一起理解。优化和运动学工具不代表得到的轨迹自动满足某个动态接触模型。

Drake 的 double、AutoDiff 和 symbolic 标量支持按组件与配置区分。E3 核对了 SAP 的 AutoDiff 隐函数实现与旧注释之间的差异，见[可微边界](contact-solvers.md)；不能把内部梯度路径写成所有接触仿真都可微。阅读相应函数的前置条件比只看模板类型更重要。

## 6. 可视化与下一步

[MeshcatVisualizer](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/meshcat_visualizer.h) 消费几何与位姿用于显示；它不负责求解多体动力学。相机/深度传感、几何查询、接触结果与外部数据接口各自有坐标和更新周期，后续专题分别展开。

阅读练习：画出 Plant、SceneGraph、控制器、Visualizer 的端口关系；指出每个状态由谁的 Context 保存；从一个接触参数追到 manager 与 SAP；说明选用的近似和不支持的标量路径。本仓源码学习不代表 DexLab Drake 运行资格已验收，完整课程见[路线](curriculum.md)。

实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 并保留原版本、配置和工况；当前不另建实验批次或评分器。

完整接触专题：[几何与材料](contact-models.md) → [SAP、时间离散与终止](contact-solvers.md) → [力与采样](contact-observation.md)。

E4 继续追踪[相机、图像与渲染](sensors-rendering.md)、[采样、延迟与所有权](sensor-timing.md)和[惯性/编码器/力观测](inertial-force-sensing.md)。显示事件与物理步进、图像深度与射线距离、加速度与比力分别解释；保持固定源码及未运行边界。

E5 将这些系统组成[独立环境与执行生命周期](batch-lifecycle.md)，再解释[随机化、MonteCarlo 与官方学习接口](randomness-learning.md)及[数据记录/回放](data-replay.md)。Context 隔离、线程、RNG、日志缓存和 GPU 边界各自核对固定实现，不能从多实例或学习接口名称推断性能与训练能力。

E6 展开[原生 System 扩展](systems-extensions.md)、[AutoDiff/symbolic 的实际方法边界](scalar-capabilities.md)与[优化、柔性体和综合源码链](engine-boundaries.md)。转换能力、方法实现和物理导数分开核对，固定 FEM/MPM/气动力模型的归属也与公开绑定、运行资格分别记录。
