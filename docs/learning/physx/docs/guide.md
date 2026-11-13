# PhysX 从 C++ SDK 到求解器

阅读基线：`da950a3537927784951853c66618036f332ca0ce`，来源为官方固定源码。本篇是对象与关键机制导读，E1–E6 源码专题已展开；A0 安装与 E7 全路线审校仍待完成。交付只做源码/文档和片段语法核对，没有运行 SDK 或仿真实验。

## 1. 三个版本身份

本导读使用固定源码标签 ovphysx-0.6.3；其中 [PxPhysicsVersion.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxPhysicsVersion.h) 定义 SDK 头文件版本 5.11.0。标签名称、SDK 头文件和 Isaac Sim/其他宿主版本是不同身份。本轮没有构建和读回原生运行版本，不能从头文件推断 DexLab 历史宿主使用的核心版本。

[HelloWorld](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippethelloworld/SnippetHelloWorld.cpp) 展示原生 C++ 初始化与资源释放；[FetchContent 文档](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/documentation/fetchcontent/FetchContent.md) 是当前源码构建入口。Python requirements 文件不安装 PhysX C++ SDK。

## 2. 对象关系与生命周期

按 Foundation/Physics → Scene → Actor → Shape/Material 理解场景。刚体位姿、形状局部位姿、质心与惯性坐标有不同职责。静态 actor、动态 actor 与 articulation 也不能仅靠同一位置接口视为等价对象。

阅读 [PxRigidBody](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h)、[PxRigidDynamic](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h) 与 [PxArticulationReducedCoordinate](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h)。记录对象的拥有关系、释放顺序、质量惯量、力的施加方式与关节驱动接口。

## 3. simulate 与 fetchResults 成对

[PxScene](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h) 描述 simulate/fetchResults 协议；两者负责启动推进与取回/完成结果，不是两个独立物理步。异步运行期间访问或释放数据受 API 限制，不能把任意读写插在二者之间。

状态、接触回调和显示帧的时间关系需按调用顺序解释。沿 [NpScene](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp) 追踪入口，标出任务调度、同步和回调所在阶段。应用的 wall time 与 simulate 输入的物理时间也应分开。

## 4. PGS/TGS 与接触建模

[PxSceneDesc](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h) 中 ePGS 与 eTGS 是求解器选择；该源码的默认 solverType 是 ePGS。宿主可以覆盖它，不能根据宿主名称推断实际选择。

[DyDynamics](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyDynamics.cpp) 与 [DyTGSDynamics](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp) 提供不同执行入口。position/velocity iterations、关节/接触约束、warm start、摩擦及接触偏移需拆开理解。算法的迭代次数不能直接和另一个引擎的非线性迭代次数比较。

材料摩擦组合、恢复系数、接触生成、接触/静止偏移和求解器是不同环节，[E3 接触专题](contact-solvers.md)已沿原生声明与分支展开。本篇不从 SDK 导读推出已完成历史接触实验溯源。

## 5. 机器人、传感器与宿主

关节驱动与 reduced-coordinate articulation 对机器人建模尤为重要。阅读时检查自由基座、关节轴、限位、驱动增益、力限制及外部控制循环的实际接口。

PhysX 核心物理 SDK 与宿主渲染不是同一层：raycast/overlap 等几何查询、接触报告、相机图像和触觉模型应分别归属。Isaac Sim/UniSim 的相机、资产工具或任务 API 不应写成独立 SDK 自带能力。

## 6. GPU、扩展与阅读练习

[E5](batch-learning-data.md)解释 GPU/Direct GPU 的数据、初始化与同步，[E6](extensions-boundaries.md)继续解释公开 CUDA 实现、CPU fallback、自定义几何/约束/回调以及 FEM/PBD 状态和数值边界。源码中的 Jacobian 或 GPU arrays 不自动构成端到端可微仿真接口；原生能力与宿主职责分别归属。本阶段不构建/运行 SDK，不做性能或接触实验。

自查：能否正确区分三个版本身份，画出 actor/shape/scene 关系，说明 simulate/fetchResults 的访问限制，并找到实际 solver 的选择点？建模与时间的深入课已在 [E1](modeling-state-time.md) 展开，驱动、机器人与任务调度见 [E2](control-robotics.md)；[E3](contact-solvers.md)贯通接触/求解/力读回，[E4](sensors-rendering.md)解释传感与显示，[E5](batch-learning-data.md)组织学习与数据，[E6](extensions-boundaries.md)连接扩展和综合源码追踪。完整先修与剩余 A0/E7 见[课程路线](curriculum.md)。

实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 并保留原版本、配置和工况；当前不另建实验批次或评分器。
