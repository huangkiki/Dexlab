# physx-atlas 固定版本源码入口

阅读基线：`da950a3537927784951853c66618036f332ca0ce`。以下入口已核对官方 Git 树与文件内容身份；不是全仓审查或运行验收记录。

本阶段先理解引擎架构、建模、步进、控制、接触/求解、传感器/渲染、性能与扩展。独立实验、基准、训练和评分暂不开展，后续复用 DexLab。

| 源码文件 | 阅读目的 |
|---|---|
| [README.md](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/README.md) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/include/foundation/PxPhysicsVersion.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxPhysicsVersion.h) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/include/PxSceneDesc.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h) | 追踪构建、步进、数据更新与生命周期 |
| [physx/include/PxScene.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h) | 追踪构建、步进、数据更新与生命周期 |
| [physx/include/PxRigidBody.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/include/PxRigidDynamic.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/include/PxArticulationReducedCoordinate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/source/physx/src/NpScene.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp) | 追踪构建、步进、数据更新与生命周期 |
| [physx/source/lowleveldynamics/src/DyDynamics.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyDynamics.cpp) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/source/lowleveldynamics/src/DyTGSDynamics.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp) | 核对对象职责、数据布局、参数与版本约定 |
| [physx/snippets/snippethelloworld/SnippetHelloWorld.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippethelloworld/SnippetHelloWorld.cpp) | 理解官方最小使用顺序；本轮不执行 |
| [physx/documentation/fetchcontent/FetchContent.md](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/documentation/fetchcontent/FetchContent.md) | 核对对象职责、数据布局、参数与版本约定 |

## E1 增补阅读入口

[课程](modeling-state-time.md)给出对应结论与行号；文件身份清单记录于 [sources.json](sources.json)。头文件依赖的编译检查不等于这些文件的全部功能已审查。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/PxPhysics.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h) | 对象工厂、Shape 创建引用、资源生命周期 |
| [physx/include/PxShape.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h) | simulation/query/trigger 标志、局部位姿与质量更新边界 |
| [physx/include/PxRigidActor.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidActor.h) | Actor 世界位姿、附着引用计数、动态形状限制 |
| [physx/include/PxArticulationJointReducedCoordinate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationJointReducedCoordinate.h) | parent/child joint frame、关节类型与 motion |
| [physx/include/PxArticulationLink.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationLink.h) | 低层 link 索引与非 cache 更新后的速度查询 |
| [physx/include/PxArticulationFlag.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationFlag.h) | cache mask，尤其 eALL 不包含的控制和外力字段 |
| [physx/include/common/PxTolerancesScale.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxTolerancesScale.h) | 尺度参考值与单位转换的区别 |
| [physx/include/foundation/PxTransform.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxTransform.h) | 初始化、字段布局、旋转平移与复合顺序 |
| [physx/include/foundation/PxQuat.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxQuat.h) | xyzw 构造顺序、单位轴与弧度 |
| [physx/include/extensions/PxRigidBodyExt.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxRigidBodyExt.h) | 质量/惯量扩展接口与参数契约 |
| [physx/include/extensions/PxSerialization.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h) | 对象依赖闭包、格式兼容与序列化阶段限制 |
| [physx/include/cooking/PxCooking.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cooking/PxCooking.h) | triangle/convex descriptor 到 collision mesh 的 cooking 路径 |
| [physx/include/geometry/PxBoxGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxBoxGeometry.h) | 半边长与合法性 |
| [physx/include/geometry/PxTriangleMeshGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxTriangleMeshGeometry.h) | 三角网格几何与缩放引用 |
| [physx/include/geometry/PxConvexMeshGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxConvexMeshGeometry.h) | 凸网格几何与缩放引用 |
| [physx/source/physxextensions/src/ExtRigidBodyExt.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtRigidBodyExt.cpp) | 计算质心/对角化惯量与点速度的实现 |
| [physx/source/physx/src/NpRigidDynamic.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpRigidDynamic.cpp) | setGlobalPose/velocity 的运行阶段与 Direct GPU 限制 |
| [physx/source/physx/src/NpArticulationReducedCoordinate.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpArticulationReducedCoordinate.cpp) | root global pose 返回链与注释方向核对 |
| [physx/include/geometry/PxCapsuleGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxCapsuleGeometry.h) | X 轴和 halfHeight 的原生定义 |
| [physx/include/foundation/PxSimpleTypes.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxSimpleTypes.h) | PxReal 的实际 float 定义 |
| [physx/include/geometry/PxMeshScale.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxMeshScale.h) | mesh scaling 与刚性 Transform 的区别 |
| [physx/source/physx/src/NpSceneFetchResults.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneFetchResults.cpp) | 完成事件、fetch 前后处理与阶段切换 |
| [physx/include/solver/PxSolverDefs.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/solver/PxSolverDefs.h) | articulation 轴、motion、joint type 枚举 |
| [physx/source/physx/src/NpRigidActorTemplate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpRigidActorTemplate.h) | attachShape 的实际检查与 ShapeManager 调用 |
| [physx/source/physx/src/NpShape.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpShape.cpp) | Shape 标志修改限制与 SDF 材料分支 |
| [physx/source/physx/src/NpShapeManager.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpShapeManager.cpp) | 实际附着与重复 Shape 检查 |
| [physx/snippets/snippetsdf/SnippetSDF.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsdf/SnippetSDF.cpp) | SDF triangle mesh 动态 Actor、cooking 与 CPU/GPU 示例分支（未运行） |

## E2 增补阅读入口

[控制、机器人与任务接口](control-robotics.md)按 setter、数据映射、驱动参数准备与冲量限幅追踪。下列固定文件已做身份核对与对应段落阅读，不代表整个文件或引擎已全面审查。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/extensions/PxD6Joint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxD6Joint.h) | D6 隐式 drive、angular model、相对目标与 forceLimit |
| [physx/include/extensions/PxRevoluteJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxRevoluteJoint.h) | extension revolute velocity motor 与 drive flag |
| [physx/include/extensions/PxJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxJoint.h) | extension joint/constraint 的公共接口边界 |
| [physx/include/PxConstraint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraint.h) | constraint drive force/impulse flag 与版本迁移标记 |
| [physx/include/PxSimulationEventCallback.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h) | onContact/onAdvance 的阶段、写入与线程契约 |
| [physx/source/physx/src/NpArticulationJointReducedCoordinate.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpArticulationJointReducedCoordinate.cpp) | drive target/velocity/params 的实际入口检查与转发 |
| [physx/source/simulationcontroller/src/ScArticulationJointCore.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScArticulationJointCore.cpp) | 关节轴到有效 DOF target 数组映射、dirty 更新 |
| [physx/source/lowleveldynamics/include/DyArticulationJointCore.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/include/DyArticulationJointCore.h) | drive、target、joint frame 在低层 core 的存储 |
| [physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp) | 构造 drive、上限缩放/限幅与 dense Jacobian 布局 |
| [physx/source/lowleveldynamics/src/DyFeatherstoneForwardDynamic.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneForwardDynamic.cpp) | articulation 动力学接口衔接；E3 补充 contact impulse response 与 TGS 步进边界 |
| [physx/source/lowleveldynamics/include/DyFeatherstoneArticulationUtils.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/include/DyFeatherstoneArticulationUtils.h) | 低层空间量/关节工具入口；E3 说明接触树响应，未逐函数推导全部工具 |
| [physx/source/physxextensions/src/ExtD6Joint.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtD6Joint.cpp) | D6 参数保存、相对 joint frame 误差与 drive row |
| [physx/source/physx/src/NpRigidBodyTemplate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpRigidBodyTemplate.h) | 四种 force mode 的逆质量/逆惯量和累加器分支 |
| [physx/source/simulationcontroller/src/ScBodyCore.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScBodyCore.cpp) | Body core 与 simulation 状态接口的衔接 |
| [physx/snippets/snippetarticulationrc/SnippetArticulation.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetarticulationrc/SnippetArticulation.cpp) | 原生 robot link/joint frame、额外 D6 约束与目标提交（未运行） |
| [physx/source/lowleveldynamics/include/DyFeatherstoneArticulation.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/include/DyFeatherstoneArticulation.h) | articulation 与 CPU/GPU 共享驱动数据入口 |
| [physx/source/physx/src/NpArticulationJointReducedCoordinate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpArticulationJointReducedCoordinate.h) | scSetDrive/Target/Velocity 向 core 转发 |
| [physx/include/PxArticulationMimicJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationMimicJoint.h) | mimic ratio/offset/compliance 的公开入口 |
| [physx/source/lowleveldynamics/shared/DyCpuGpuArticulation.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpuArticulation.h) | force/acceleration 隐式 drive 公式、冲量计算与 envelope 限幅 |

## E3 增补阅读入口

[接触、求解器与力观测](contact-solvers.md)沿 CPU 接触管线追踪。以下是已核对文件身份和所引用段落的入口，不代表所有几何组合、GPU 或完整文件均已审查。E0/E1 已登记的 `DyDynamics.cpp`、`DyTGSDynamics.cpp`、Scene/Body/Shape 头文件继续用于本章；E2 的 callback/D6 来源用于观测边界。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/PxMaterial.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxMaterial.h) | 摩擦/柔顺材料、combine mode 与原生 flags |
| [physx/include/PxFiltering.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h) | 检测、求解、通知、CCD 与 filter 返回值 |
| [physx/include/PxContact.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContact.h) | friction anchor stream 的有效性与字段布局 |
| [physx/include/PxContactModifyCallback.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h) | 求解前修改 target、impulse、mass scale 与线程契约 |
| [physx/source/lowlevel/software/include/PxsMaterialCombiner.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/include/PxsMaterialCombiner.h) | 实际 combine 顺序、刚柔混合 damping 与静/动摩擦钳制 |
| [physx/source/lowleveldynamics/src/DyBodyCoreIntegrator.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyBodyCoreIntegrator.h) | 外力/阻尼预积分、PGS motion velocity 和闭式 quaternion 更新 |
| [physx/source/lowleveldynamics/src/DyContactPrep.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrep.cpp) | PGS 接触准备、冲量初始化、anchor 位置/切向冲量写回 |
| [physx/source/lowleveldynamics/src/DyContactPrepShared.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h) | unit response、恢复/偏置、force/acceleration compliant coefficients |
| [physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp) | TGS 位置增量更新、成对摩擦、torsion 与读回 |
| [physx/source/lowleveldynamics/src/DySolverConstraints.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp) | PGS constraint block 布局、摩擦钳制和冲量 writeback |
| [physx/source/lowleveldynamics/src/DySolverControl.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverControl.cpp) | position/conclude/motion/velocity/writeback 的实际循环与最少一遍语义 |
| [physx/source/lowleveldynamics/src/DyCorrelationBuffer.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyCorrelationBuffer.h) | contact/friction patch 相关性数据结构 |
| [physx/source/lowlevel/common/src/pipeline/PxcNpContactPrepShared.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/common/src/pipeline/PxcNpContactPrepShared.cpp) | 材料组合进入接触流、friction stream 分配与输出 |
| [physx/source/simulationcontroller/src/ScScene.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScScene.cpp) | CPU PGS/TGS/GPU context 选择与 scene 分步入口 |
| [physx/source/lowleveldynamics/src/DySolverConstraintsShared.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraintsShared.h) | 法向累计冲量、投影、立即更新速度的 CPU 行迭代 |
| [physx/source/simulationcontroller/src/ScShapeInteraction.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScShapeInteraction.cpp) | discrete 与 CCD 接触通知，CCD friction stream 缺项 |
| [physx/source/physx/src/NpConstraint.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpConstraint.cpp) | getForce 的阶段检查与 core 转发 |
| [physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp) | link 接触响应、CFM 与禁用/未使用 self-response 分支 |
| [physx/source/simulationcontroller/src/ScConstraintCore.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScConstraintCore.cpp) | 普通 joint constraint force 的 core/simulation 转发边界 |
| [physx/source/lowlevel/software/src/PxsNphaseImplementationContext.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/src/PxsNphaseImplementationContext.cpp) | CPU PCM/普通 narrow phase 的配置分支 |
| [physx/source/simulationcontroller/src/ScPipeline.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScPipeline.cpp) | simulate/collide/advance、岛/solver/积分/CCD 任务依赖 |

## E4 增补阅读入口

[传感、查询与调试显示](sensors-rendering.md)给出固定行号和责任边界；继续复用 E1–E3 的 scene、rigid body、articulation 和 fetch 源码。来源身份收录 [sources.json](sources.json)，不因接口或 snippet 存在而宣称运行验收。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/PxQueryFiltering.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryFiltering.h) | 静/动态与 hardcoded mask、pre/post filter、TOUCH/BLOCK/ANY/NO_BLOCK |
| [physx/include/PxQueryReport.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryReport.h) | hit callback/buffer、容量截断与 query cache 生命周期 |
| [physx/include/PxSceneQuerySystem.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h) | ray/sweep/overlap 契约、flush、独立 query system 与异步更新 |
| [physx/include/PxSceneQueryDesc.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQueryDesc.h) | pruner 与 build/commit 更新模式、新对象可见性取舍 |
| [physx/include/PxVisualizationParameter.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxVisualizationParameter.h) | master/对象可视化开关、scaled impulse 和 deprecated force 别名 |
| [physx/include/common/PxRenderBuffer.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxRenderBuffer.h) | world 调试点/线/三角形与借用数组，非 framebuffer |
| [physx/include/geometry/PxGeometryQuery.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryQuery.h) | 给定 geometry/pose 的查询，与 scene 发现/filter 责任分开 |
| [physx/include/omnipvd/PxOmniPvd.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/omnipvd/PxOmniPvd.h) | OVD 集成版本、writer 所有权/并发、采样与 stream/transport 生命周期 |
| [physx/include/pvd/PxPvd.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvd.h) | 调试 instrumentation、连接与 cached 状态 |
| [physx/include/pvd/PxPvdSceneClient.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvdSceneClient.h) | 调试 stream 开关、PVD viewer camera 与图元 |
| [physx/source/physx/src/NpSceneQueries.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneQueries.cpp) | scene 查询转发、读写检查、manual update/fetch 的配对 |
| [physx/snippets/snippetrender/SnippetRender.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrender/SnippetRender.cpp) | GLUT/OpenGL 显示、投影与 swap 的示例应用职责 |
| [physx/snippets/snippetrender/SnippetCamera.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrender/SnippetCamera.cpp) | 官方示例相机的坐标约定；不当作原生传感器 |
| [physx/include/geometry/PxGeometryHit.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h) | 位置/法向/UV 有效位、face index、重叠与 distance |
| [physx/source/scenequery/src/SqQuery.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp) | 实际 mask/default hit type/ANY/cache 路径和输入检查 |
| [physx/source/scenequery/src/SqManager.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqManager.cpp) | 脏数据 flush、锁、shape 更新与 pruner commit |
| [physx/snippets/snippetquerysystemallqueries/SnippetQuerySystemAllQueries.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetquerysystemallqueries/SnippetQuerySystemAllQueries.cpp) | 独立 query system 的示例组织；不执行 |
| [physx/snippets/snippetomnipvd/SnippetOmniPvd.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetomnipvd/SnippetOmniPvd.cpp) | writer/stream 与 Physics 连接、窗口/非窗口应用分支；不执行 |
| [physx/source/physx/src/omnipvd/NpOmniPvd.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/omnipvd/NpOmniPvd.cpp) | 编译支持、writer 获取、startSampling 快照与 callback 顺序 |
| [physx/include/pvd/PxPvdTransport.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvdTransport.h) | 默认 socket/file transport 工厂边界 |
| [physx/source/simulationcontroller/src/ScVisualize.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScVisualize.cpp) | 接触图元、impulse 缩放与 sleeping pair 缺项 |
| [physx/source/physx/src/NpScene.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.h) | scene 持有的 render/query/acceleration 数据与内部辅助入口 |
| [physx/include/PxSceneLock.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneLock.h) | 原生 scene read/write RAII，不代替物理完成事件 |
| [physx/source/physx/src/NpDebugViz.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpDebugViz.cpp) | 清空并重建对象调试图元的实际阶段 |

## E5 增补阅读入口

[批量、学习接口与数据](batch-learning-data.md)继续复用 E1–E4 的 Scene/cache/filter/材料源码；下列固定文件身份均收录 [sources.json](sources.json)。这里只证明来源与本章接口解释，不代表 GPU/序列化/学习宿主已经运行。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/PxDirectGPUAPI.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h) | Direct GPU 初始化/禁用 CPU readback、typed fields、scene-wide batch stride 和 CUDA events |
| [physx/include/cudamanager/PxCudaContextManager.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cudamanager/PxCudaContextManager.h) | CUDA context 获取/释放、driver API 边界、旧 helper deprecation |
| [physx/include/extensions/PxDefaultCpuDispatcher.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxDefaultCpuDispatcher.h) | worker 数量、零 worker 语义与等待模式 |
| [physx/include/common/PxCollection.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxCollection.h) | 对象集合、ID 与容器 release 的所有权 |
| [physx/include/common/PxSerializer.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxSerializer.h) | 自定义对象类型 serializer 契约与对象图依赖入口 |
| [physx/include/extensions/PxExtensionsAPI.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxExtensionsAPI.h) | 原生 extensions 初始化/关闭与库边界 |
| [physx/include/task/PxCpuDispatcher.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/task/PxCpuDispatcher.h) | SDK CPU task 的 submit/run/release 与 worker 计数契约 |
| [physx/include/task/PxTask.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/task/PxTask.h) | task run 的不可阻塞/线程安全要求与 continuation/reference 生命周期 |
| [physx/include/task/PxTaskManager.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/task/PxTaskManager.h) | SDK task 调度与 start/stopSimulation 管理入口 |
| [physx/snippets/snippetdirectgpuapiarticulation/SnippetDirectGPUAPIArticulation.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetdirectgpuapiarticulation/SnippetDirectGPUAPIArticulation.cpp) | 首个物理步初始化、low-level link index、GPU typed 读写；只阅读 |
| [physx/snippets/snippetrbdirectgpuapi/SnippetRBDirectGPUAPI.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrbdirectgpuapi/SnippetRBDirectGPUAPI.cpp) | 原生刚体 GPU buffer/索引和数据交换应用示例；不执行 |
| [physx/snippets/snippetmultithreading/SnippetMultiThreading.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetmultithreading/SnippetMultiThreading.cpp) | simulate/fetch 之间的 query worker 交叠与应用等待 |
| [physx/snippets/snippetsplitsim/SnippetSplitSim.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsplitsim/SnippetSplitSim.cpp) | collide/fetchCollision/advance/fetchResults 分阶段时序 |
| [physx/snippets/snippetserialization/SnippetSerialization.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetserialization/SnippetSerialization.cpp) | 共享资产/实例 collection、128-byte backing allocation 与最终释放 |
| [physx/source/physx/src/NpDirectGPUAPI.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpDirectGPUAPI.cpp) | 合法阶段/初始化/指针检查与 simulation controller 转发 |
| [physx/source/physxextensions/src/ExtDefaultCpuDispatcher.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDefaultCpuDispatcher.cpp) | 零 worker 同步 run/release 与线程队列路径 |
| [physx/source/physxextensions/src/serialization/Binary/SnBinarySerialization.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/serialization/Binary/SnBinarySerialization.cpp) | binary header/version/platform 与对象数据序列化实现 |
| [physx/source/physxextensions/src/serialization/SnSerialization.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/serialization/SnSerialization.cpp) | 完整对象图和可序列化条件实现 |
| [physx/include/PxAggregate.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxAggregate.h) | broad-phase 聚合与自碰撞，区别于环境隔离 |
| [physx/include/common/PxSerialFramework.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxSerialFramework.h) | serialization registry 的类型注册/反注册与生命周期 |
| [physx/include/extensions/PxCollectionExt.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCollectionExt.h) | 实际 createCollection API、可共享对象与 releaseObjects 引用前提 |
| [physx/include/extensions/PxCudaHelpersExt.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCudaHelpersExt.h) | 替代旧 context helper 的分配/拷贝扩展、context 锁与错误处理 |
| [physx/source/physxextensions/src/serialization/Binary/SnBinaryDeserialization.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/serialization/Binary/SnBinaryDeserialization.cpp) | header/GUID/platform 检查与提供内存内的对象构造 |

补充职责来源：[Isaac Lab 官方任务工作流](https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/task_workflows.html)。该可变页面于 2026-10-09 查阅，只用于说明 RL 环境类属于宿主；不是固定 SDK 身份、版本兼容或运行证据。

## E6 增补阅读入口

[原生扩展与能力边界](extensions-boundaries.md)沿 constraint/geometry contracts、CPU DistanceJoint 全链、GPU 分派和代表性 FEM/PBD kernel 展开。下列新增来源与此前的 Scene/Constraint/CPU solver/Direct GPU 文件共同构成阅读地图；所有身份记录在 [sources.json](sources.json)。GPU CUDA 实现公开可读，driver/toolchain、实际加载 binary 和宿主运行仍是独立证据。地图收录接口、深入追踪和补充入口，不表示逐行审计所有 GPU 内核。

| 源码文件 | 阅读目的 |
|---|---|
| [physx/include/PxConstraintDesc.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h) | 一维行/Jacobian/单位与 flags、solver-prep/connector 生命周期 |
| [physx/include/extensions/PxConstraintExt.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxConstraintExt.h) | 外部 constraint owner 类型 ID 的保留范围 |
| [physx/include/geometry/PxCustomGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxCustomGeometry.h) | geometry 的 callback 裸引用与碰撞/查询/质量/PCM 契约 |
| [physx/include/extensions/PxCustomGeometryExt.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCustomGeometryExt.h) | 现成 cylinder/cone 回调、尺寸/轴/margin 接口 |
| [physx/include/extensions/PxDistanceJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxDistanceJoint.h) | 距离上下限、spring 开关和原生 setter |
| [physx/source/physxextensions/src/ExtDistanceJoint.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp) | 配置/dirty、方向/死区/单边行、官方 shader table |
| [physx/source/physxextensions/src/ExtDistanceJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.h) | DistanceJointData 布局和 extension 类型关系 |
| [physx/source/physxextensions/src/ExtCustomGeometryExt.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtCustomGeometryExt.cpp) | convex 支持映射、cylinder bounds 与 margin 分支质量属性 |
| [physx/source/geomutils/src/contact/GuContactCustomGeometry.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/geomutils/src/contact/GuContactCustomGeometry.cpp) | 普通接触生成对 custom callback 的转发和法向翻转 |
| [physx/source/geomutils/src/pcm/GuPCMContactCustomGeometry.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/geomutils/src/pcm/GuPCMContactCustomGeometry.cpp) | PCM 失效/重用、geometry 交换与法向方向 |
| [physx/include/PxDeformableVolume.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableVolume.h) | GPU-only 体、collision/simulation 网格状态与 dirty/lifetime |
| [physx/include/PxDeformableSurface.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableSurface.h) | GPU-only 面、顶点状态与 collision update/substep 接口 |
| [physx/include/PxDeformableBody.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableBody.h) | 非刚体基类的 shape、迭代和状态参数契约 |
| [physx/include/PxDeformableVolumeMaterial.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableVolumeMaterial.h) | co-rotational/neo-Hookean 材料模型枚举 |
| [physx/include/PxDeformableSurfaceMaterial.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableSurfaceMaterial.h) | surface 厚度、弯曲刚度和阻尼接口 |
| [physx/include/PxPBDParticleSystem.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h) | 位置/速度迭代、phase/offset 与 particle stream callbacks |
| [physx/include/PxParticleSystem.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleSystem.h) | 旧粒子头文件的兼容入口，不从名称推断额外实现 |
| [physx/include/PxPBDMaterial.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDMaterial.h) | 粒子材料参数与 particle-cloth/rigids 等 deprecated 注释 |
| [physx/include/PxParticleBuffer.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleBuffer.h) | device 数组、active/capacity/flat index 和独立 buffer 生命周期 |
| [physx/include/PxDeformableAttachment.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableAttachment.h) | rigid/world/元素内 attachment 的坐标与固定拓扑 |
| [physx/source/physxgpu/src/PxgPhysXGpu.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxgpu/src/PxgPhysXGpu.cpp) | GPU PGS/TGS context 工厂与公开 GPU 实用对象入口 |
| [physx/source/compiler/cmakegpu/PhysXGpuDependencies.cmake](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/compiler/cmakegpu/PhysXGpuDependencies.cmake) | GPU 构建复用的公开 CPU/几何/foundation 对象依赖 |
| [physx/source/compiler/cmakegpu/PhysXGpu.cmake](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/compiler/cmakegpu/PhysXGpu.cmake) | GPU object targets 与平台链接/静态动态库组成 |
| [physx/source/physx/src/gpu/PxPhysXGpuModuleLoader.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/gpu/PxPhysXGpuModuleLoader.cpp) | GPU library/driver 装载、导出符号与版本兼容检查 |
| [physx/source/gpusolver/src/CUDA/solver.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/CUDA/solver.cu) | GPU articulation 约束批处理 kernel 入口，非完整后端证明 |
| [physx/source/gpusolver/src/CUDA/solverMultiBlockTGS.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/CUDA/solverMultiBlockTGS.cu) | GPU TGS 批量约束/接触求解及 writeback 分支 |
| [physx/source/gpusimulationcontroller/src/CUDA/softBody.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/softBody.cu) | deformable volume GPU 推进与顶点/碰撞状态路径 |
| [physx/source/gpusimulationcontroller/src/CUDA/softBodyGM.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/softBodyGM.cu) | 材料分支、ARAP/volume compliance 更新及 TGS multiplier 处理 |
| [physx/source/gpusimulationcontroller/src/CUDA/FEMClothConstraintPrep.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMClothConstraintPrep.cu) | surface–rigid 接触、重心数据与耦合 constraint prep |
| [physx/source/gpusimulationcontroller/src/CUDA/particlesystem.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/particlesystem.cu) | 粒子积分/接触/密度工作数组与缩放约束值 |
| [physx/source/gpuarticulation/src/CUDA/forwardDynamic2.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpuarticulation/src/CUDA/forwardDynamic2.cu) | GPU reduced-coordinate articulation 前向动力学实现入口 |
| [physx/source/gpusimulationcontroller/src/PxgSoftBodyCore.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/PxgSoftBodyCore.cpp) | GPU volume core 的 buffer/kernel 调度入口 |
| [physx/include/PxDeformableMaterial.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableMaterial.h) | Young/Poisson/friction/elasticity damping 的原生参数 |
| [physx/include/PxParticleGpu.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleGpu.h) | particle callback 暴露的 GPU 数据结构 |
| [physx/source/physx/src/NpDeformableVolume.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpDeformableVolume.cpp) | 公开 volume 操作到 core、shape 和设备状态的实现 |
| [physx/source/physx/src/NpPBDParticleSystem.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpPBDParticleSystem.cpp) | 原生粒子参数/phase/callback 到 core 的实现 |
| [physx/source/physxextensions/src/ExtJoint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtJoint.h) | createConstraint、数据块、COM/origin 更新与 connector 关系 |
| [physx/source/physxextensions/src/ExtConstraintHelper.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtConstraintHelper.h) | world attachment、力臂/force reporting 参考点及行帮助函数 |
| [physx/source/lowleveldynamics/src/DyConstraintSetup.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyConstraintSetup.cpp) | CPU PGS shader 调用、预处理/惯性响应、系数/输出标志 |
| [physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h) | 共享 force/impulse 限幅转换、PGS/TGS spring 系数和速度 bias |
| [physx/source/simulationcontroller/src/ScConstraintSim.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScConstraintSim.cpp) | constraint writeback 冲量除以 Scene dt 的 getter 路径 |
| [physx/source/gpunarrowphase/src/PxgNphaseImplementationContext.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpunarrowphase/src/PxgNphaseImplementationContext.cpp) | GPU pair 分派、custom/modify fallback 与受限 pair |
| [physx/source/gpunarrowphase/src/PxgShapeManager.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpunarrowphase/src/PxgShapeManager.cpp) | GPU shape/材料数据管理入口，不是宿主视觉材质 |
| [physx/include/PxParticleSystemFlag.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleSystemFlag.h) | particle phase group/behavior 与 device buffer dirty flags |
| [physx/source/compiler/cmakegpu/linux/PhysXGpu.cmake](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/compiler/cmakegpu/linux/PhysXGpu.cmake) | GPU object targets 与平台链接/静态动态库组成 |
| [physx/source/gpusimulationcontroller/src/CUDA/FEMCloth.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMCloth.cu) | surface membrane/bending 推进、位置修正与速度更新 |
| [physx/include/PxImmediateMode.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxImmediateMode.h) | 显式 bodies/contact/batch/solve/integrate 的低层扩展入口 |
| [physx/include/characterkinematic/PxController.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/characterkinematic/PxController.h) | CCT collide-and-slide 与内部 kinematic actor 的应用边界 |
| [physx/include/vehicle/PxVehicleComponentSequence.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/vehicle/PxVehicleComponentSequence.h) | 原生 vehicle component/substep group 调度契约 |
| [physx/include/geometry/PxConvexCoreGeometry.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxConvexCoreGeometry.h) | 原生 convex core 类型与 custom callback dispatch 的区别 |
| [physx/source/gpusimulationcontroller/src/CUDA/FEMClothUtil.cuh](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMClothUtil.cuh) | 三角膜能量/面积约束、thickness 与 Lamé/compliance 尺度 |
| [physx/source/lowlevelaabb/src/BpFiltering.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevelaabb/src/BpFiltering.cpp) | actor 类别交互过滤表的补充阅读 |
| [physx/source/gpusimulationcontroller/src/CUDA/deformableUtils.cuh](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/deformableUtils.cuh) | Lamé 参数计算与 GPU deformable 数值辅助函数 |
| [physx/source/lowlevelaabb/include/BpFiltering.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevelaabb/include/BpFiltering.h) | broad-phase actor type 过滤定义的补充阅读 |
| [physx/source/gpusolver/src/PxgDynamicsContext.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/PxgDynamicsContext.cpp) | 公开 GPU PGS context 与 solver core/stream 初始化 |
| [physx/source/gpusolver/src/PxgTGSDynamicsContext.cpp](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/PxgTGSDynamicsContext.cpp) | 公开 GPU TGS context 与对应 solver core 初始化 |
| [physx/source/gpusolver/src/CUDA/solverMultiBlock.cu](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/CUDA/solverMultiBlock.cu) | GPU PGS 刚体批量求解/写回 kernel |
| [physx/include/extensions/PxMassProperties.h](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxMassProperties.h) | 密度 1 的质量属性约定、密度线性缩放与 custom 调用 |
