# SuperDex 从对象到源码

阅读基线：`1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`，来源为官方固定源码。本篇是对象与关键机制导读，[E1 建模、状态与时间专题](modeling-state-time.md)、[E2 控制与机器人](control-robotics.md)、[E3 接触与求解器](contact-solvers-forces.md)、[E4 传感器与渲染](sensors-rendering.md)、[E5 批量与学习数据](batch-learning-data.md)、[E6 特色Actor与可微扩展](extensions-boundaries.md)已展开，A0及最终双路线审校仍待E7；本轮仅做源码/文档核对，没有运行仿真实验。

## 1. 先分清产品层

Physics 是底层物理接口；Robotics 提供机器人、控制器和传感器等组件。Studio 等上层工具负责自己的场景与交互工作。学习时先确定对象来自哪一层，避免把上层工具的默认值当成物理内核常量。官方 Python 例子使用 `import superdex.physics as physics`，接着 initialize、create_scene、创建 actor、设置场景并推进。

从 [官方 README](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/README.md) 和 [刚体示例](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_rigid_bodies.py) 开始，画出 initialize → Scene → Actor → geometry/material → step 的所有权关系。Physics 的该示例使用 Y 方向重力；使用 Robotics 场景时应重新核对坐标约定，不照搬其他引擎的 Z-up 假设。

## 2. 状态与配置的生命周期

模型/几何定义、当前 actor 状态、积分器内部历史和传感器输出是不同数据。需要回放时先确认快照包含什么，再讨论恢复的含义。[capture/restore 示例](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_state_capture_restore.py) 是入口；场景时间通过原生接口理解，不能把 viewer 帧率视为物理步长。

FP64 是独立构建/安装身份；`SUPERDEX_PRECISION=fp64` 应在导入前设置。Python 中的浮点数类型不能单独证明内核使用 FP64。教程源提交、wheel 版本、CPU/GPU 配置分别记录。

## 3. 从控制命令到动力学

机器人控制课应先读 [PD 控制器](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/controllers/controller_basic_jsc_pd.cpp)：哪些数组是目标、哪些是当前关节状态、比例/阻尼如何进入输出、输出施加在哪里。设置 pose 与施加力是不同操作；直接重写状态不能当成执行了一个真实控制过程。

关节坐标、关节轴、根节点自由度和关节索引都应随资产导入一起解释。阅读练习：沿一个 PD 输出追到物理接口，记录各层单位及索引的转换，不要求做新的跟踪实验。

## 4. 接触参数必须按本引擎解释

[ContactParams](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_params.h) 分别描述 penalty、摩擦、法向阻尼及正则化。本提交注释给出的摩擦/耗散组合采用几何平均；penaltyCoefficient 与 frictionFalloffVel 也通常使用几何平均，但 collider 静止时采用 colliding 一侧的值。教学中必须说明两侧角色，不能直接套用另一引擎的材料组合规则。

`penaltyCoefficient` 的标注单位为 Pa/m；它不是可直接填入的杨氏模量。接触检测阈值、平滑范围和摩擦速度正则化分别影响不同环节。接触几何、接触力律与数值求解需要分章理解。

这里描述的是固定官方源码的字段与注释；复用二进制时还须核对实际构建与执行路径。它不能直接补齐 DexLab 历史批次的算法/组合律证据。

## 5. 积分器、非线性求解和线性求解

[IntegrationParams](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/integration/integration_params.h) 与 [NewtonSolver 参数](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/newton_solver_params.h) 位于不同层：时间离散构造问题，非线性迭代求解该问题，线性求解器处理迭代内的子问题。Backward Euler 不是线性求解算法。

从 [scene](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp) 到 [integration](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_integration.cpp)，再读 [NewtonSolver](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/solvers/newton_solver.cpp)。逐步记录参数在哪验证、何时实例化、哪种路径启用；仅找到同名类不等于证明某次历史运行用了它。可微场景的积分方式还存在额外限制，应单独阅读构建校验分支。

## 6. 传感器、扩展与下一步

[camera sensor](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/sensors/camera_sensor.cpp) 只保存机器人层相机参数；它不在物理循环产生图像。[E4](sensors-rendering.md)分别追踪物理查询、CameraSensor 元数据与 Polyscope/Mochi/UE 宿主图像，记录坐标、实际返回格式、帧延迟与能力缺口。[E5](batch-learning-data.md)进一步展开 Lab 的进程/串行批量、共享 Scene 快照、Gymnasium seed/autoreset、CUDA 数据拷贝与记录回放。[E6](extensions-boundaries.md)已按实际接口/构建支持展开软体/壳/杆/ROM、可微装配及兼容边界，不从一个接口名称推断性能或所有能力均兼容。

阅读自查：能否解释 Scene 与 actor 的所有权、FP64 的构建身份、一个 PD 输出的去向、一个接触参数的量纲及积分/求解三层关系？已交付专题与仍待E7完成的A0及最终审校见[课程路线](curriculum.md)。

实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 并保留原版本、配置和工况；当前不另建实验批次或评分器。
