# E1 · 建模、坐标、状态与时间

[首页](../README.md) · [课程地图](curriculum.md) · [源码地图](source-map.md) · [本章验证](validation/e1.md)

学完本章，应能从一份模型说明构造原生对象，解释几何、惯量和状态分别存在哪里，并在正确的时间边界读取它们。先修是[对象导读](guide.md)与基本向量/矩阵运算。应用路线读第 1–7 节与示例；源码路线同时完成公式推导、实现追踪和最后的练习。

本章固定阅读 `ovphysx-0.6.3` 对应提交 `da950a3537927784951853c66618036f332ca0ce`，其中 SDK 头文件是 **5.11.0**。标签、头文件、实际链接二进制和 Isaac Sim/UniSim 宿主版本分别记录，不能相互替代。以下使用普通 CPU 场景的 C++ SDK 接口；启用并初始化 Direct GPU API 后，若干 CPU 状态访问接口不适用，不能照搬本章片段。[版本定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxPhysicsVersion.h)与[状态接口限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidActor.h#L60-L106)是核对入口。

交付范围是 A1、A2 以及 B0 的刚体数据/坐标基础、B4 的时间边界。接触装配、PGS/TGS 的方程与完整积分路径属于 E3；可微、GPU、完整机器人导入及运行安装验收不由本章替代。这里没有进行物理实验。

## 1. 先把模型拆成对象和职责

`PxPhysics` 创建资源，`PxScene` 管理一次仿真的对象集合、重力、调度及求解配置。`PxRigidActor` 提供世界位姿并引用 Shape；`PxShape` 描述碰撞/查询几何、局部位姿、材料和过滤标志。视觉网格、相机材质、USD/URDF 文件名和任务状态不是这些接口的同义字段。

| 层 | 原生入口 | 存储什么 / 不应混入什么 |
|---|---|---|
| 物理实例 | `PxPhysics` | SDK 对象工厂；创建时的 tolerances scale |
| 场景 | `PxPhysics::createScene(PxSceneDesc)` | 重力、CPU dispatcher、filter shader、求解配置；不是渲染窗口 |
| 静态刚体 | `createRigidStatic(PxTransform)` | 静态几何的 Actor 世界位姿；不积分动态质量/速度 |
| 动态刚体 | `createRigidDynamic(PxTransform)` | 质量、惯量、速度、力、睡眠等；默认创建对象不等于已添加到 Scene |
| 运动学刚体 | `PxRigidDynamic` + `eKINEMATIC` | 由应用给目标位姿；不由施加的力决定运动 |
| 碰撞形状 | `createShape(geometry, material, isExclusive, flags)`，`attachShape` | 几何、Actor 内的局部位姿、材料；不会自动刷新刚体质量惯量 |
| 关节树 | `createArticulationReducedCoordinate()` → `createLink(parent, pose)` | 根连杆和树状子连杆、入关节；不要把它当作独立动态 Actor 数组 |
| 材料 | `createMaterial(staticFriction, dynamicFriction, restitution)` | 物理接触参数；不是渲染颜色/PBR 材料 |

来源：[对象创建](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h#L409-L481)、[材料工厂](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h#L742-L764)、[articulation 创建](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L574-L622)。本章只用这些原生层次，不建立统一跨引擎模型类。

### 生命周期不是“把指针交给 Scene 就不用管”

`createShape` 返回的 Shape 有一份引用；`attachShape` 成功后增加一份引用；`detachShape` 减少引用。常见顺序是创建 → 检查附着成功 → 释放应用的创建引用，由 Actor 保留附着引用。要继续修改局部位姿，优先创建 exclusive Shape；**已附着的 shared Shape 不可修改**。Actor/Shape/Material 的 SDK 指针不是值快照，释放后应用保存的裸指针会失效。[创建引用与可变性](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h#L457-L477)、[附着与拆卸](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidActor.h#L112-L142)。

按依赖关闭：先结束尚未取回的物理步，再释放使用中的对象/场景及资源，最后释放 Physics 和 Foundation；不要在 `simulate` 与 `fetchResults` 之间释放 Scene。本章示例把 Scene、Physics、Material 的创建和销毁交给宿主，明确返回 Actor 的释放责任，避免隐含的全局所有者。[Scene 释放限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L173-L191)、[Physics 与 Foundation 生命周期](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h#L66-L84)。

## 2. 几何、cooking 与资产边界

### 原生几何尺寸

`PxBoxGeometry(hx, hy, hz)` 使用**半边长**。`PxCapsuleGeometry(radius, halfHeight)` 的圆柱段长度为 `2 * halfHeight`，本地长轴是 **X**；加上两端半球后全长为 `2 * (halfHeight + radius)`。把“Z-up 场景”误写成“胶囊沿 Z”会得到旋转了 90° 的碰撞体。[Box](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxBoxGeometry.h#L18-L35)、[Capsule](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxCapsuleGeometry.h#L16-L35)。

Shape 的 `eSIMULATION_SHAPE` 与 `eSCENE_QUERY_SHAPE` 分别控制参与物理碰撞和 raycast/overlap/sweep 等查询。一个只参与查询的几何能被射线命中，不代表能支撑物体。`eTRIGGER_SHAPE` 与 simulation 标志不能同时打开；需要两者时建立两个 Shape。`eVISUALIZATION` 是 SDK 调试绘制标志，不是宿主视觉模型。[Shape flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L36-L91)。

### Mesh 数据怎样进入碰撞系统

一条可审计的资产路径是：

1. **宿主/应用解析资产**：把源文件的顶点、索引、单位、朝向和变换解释成数组；保留文件哈希、许可、尺度、碰撞近似方法。
2. **选择碰撞表示**：primitive、convex hull 或 triangle mesh。视觉三角形不一定适合作为动态碰撞表示。
3. **填原生 descriptor**：例如 `PxTriangleMeshDesc` 或 `PxConvexMeshDesc`；数组元素数、步幅、索引格式、退化几何都属于输入契约。
4. **Cooking**：`PxCookTriangleMesh` / `PxCookConvexMesh` 转成供碰撞查询使用的数据，检查 bool 和 cooking result；再由 Physics 创建 mesh。也可用 `PxCreateTriangleMesh` / `PxCreateConvexMesh` 直接创建，调用方提供 insertion callback。
5. **建立 Shape 并附着**：geometry 引用 mesh，Shape 再引用 geometry/材料；核对 local pose 与 collision/query flags，最后显式计算或设置质量属性。

Cooking 的职责是处理碰撞数据，不是自动理解 URDF link/joint、USD stage、视觉材质或机器人执行器。宿主导入器可能做缩放、凸分解、关节映射和惯量替换，这些必须另记导入器版本与参数，不能统称为“PhysX 默认”。[Cooking 原生声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cooking/PxCooking.h#L456-L505)、[triangle mesh 路径](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cooking/PxCooking.h#L565-L621)。

**不要从旧的形状限制推出“一切动态三角网格都不支持”。** 本基线的 [attachShape 注释](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidActor.h#L117-L122)仍列出非运动学动态 Actor 的 triangle mesh/heightfield/plane 限制；但同一固定树的官方 [SnippetSDF](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsdf/SnippetSDF.cpp#L33-L57)在 cooking descriptor 中提供 SDF，并[创建带三角网格的动态刚体](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsdf/SnippetSDF.cpp#L90-L108)。它还区分 [CPU/GPU 场景分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsdf/SnippetSDF.cpp#L163-L196)。所以普通碰撞网格与 SDF 碰撞数据要分别核对；SDF 的构造质量、分辨率、接触路径和具体限制留到 E3/E6，本章只用 primitive。几何路径适用、cooking 成功、模型物理合理性是三个不同检查，视觉导入成功不能替代其中任何一个。

`PxMeshScale` 是网格几何的缩放表达；`PxTransform` 是刚性旋转/平移，不含任意缩放。资产换单位时需一致修改几何和质量属性，不能仅缩放渲染节点。不要把 mesh/shape 指针复制当作复制 mesh 数据或转移资源所有权。[网格尺度](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxMeshScale.h#L21-L57)、[Transform 字段](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxTransform.h#L24-L54)。仓库示例使用原创 primitive，没有新增第三方模型文件；引入资产时在 `THIRD_PARTY.md` 记录许可和修改。

## 3. 单位、轴系和姿态

### 一个场景选一套一致量纲

本章采用米、千克、秒（m/kg/s），角度为 rad。若基本长度、质量、时间单位分别是 L、M、T，则速度为 L/T，加速度为 L/T²，密度为 M/L³，惯量为 ML²，力为 ML/T²，力矩为 ML²/T²。对于相同物理物体，米改成厘米、质量和秒不变时：位置、速度、重力的数值乘 100；惯量乘 10⁴；密度除 10⁶。若是**真的把物体放大**且保持密度，质量又要随尺寸的三次方变化，不要与单位换算混为一谈。

`PxTolerancesScale.length` 和 `.speed` 用来建立若干容差/阈值的参考尺度，**不替你转换模型、质量或重力**。默认 length=1、speed=10；厘米尺度的 length 通常设 100。`PxSceneDesc` 在这份源码中重力默认是零；官方 HelloWorld 自己设置了重力。因此不能以为创建 Scene 后就自动得到地球重力。[尺度定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxTolerancesScale.h#L17-L66)、[Scene 默认构造](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L1058-L1083)。

世界“向上”由建模与应用共同约定；选 Y-up 就配 `(0, -9.81, 0)`，选 Z-up 就配 `(0, 0, -9.81)`，并转换资产、相机和控制坐标。primitive 的固有轴线与世界上方向独立。C++ `PxReal` 在本基线是 `float`，不能因某个宿主 Python 数组是 float64 就宣称物理核心 FP64。[标量类型](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxSimpleTypes.h#L35-L49)。

### PxQuat 与变换方向

`PxQuat(x, y, z, w)` 把实部放在最后；单位四元数为 `(0,0,0,1)`。轴角构造器输入 rad 和单位轴。四元数需保持单位长度，`q` 与 `-q` 表示同一旋转；四元数有四个存储分量但只有三个旋转自由度，不能把四个分量分别当欧拉角速度积分。[构造器](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxQuat.h#L46-L71)。

约定 `T_WA` 把 Actor 坐标的点变换到世界，`T_AS` 把 Shape 坐标的点变换到 Actor，`T_AC` 把质心惯性坐标的点变换到 Actor，则：

$$
 x_W=R_{WA}x_A+p_{WA},\qquad
 T_{WS}=T_{WA}T_{AS},\qquad T_{WC}=T_{WA}T_{AC}.
$$

| 数学量 | C++ 原生读取 | 返回语义 |
|---|---|---|
| `T_WA` | `actor.getGlobalPose()` | Actor 在世界中的位姿 |
| `T_AS` | `shape.getLocalPose()` | Shape 在 Actor 内的位姿 |
| `T_AC` | `body.getCMassLocalPose()` | 质心及惯性主轴在 Actor 内的位姿 |
| `T_WS` | `actor.getGlobalPose() * shape.getLocalPose()` | Shape → 世界的复合变换 |
| `T_WC` | `body.getGlobalPose() * body.getCMassLocalPose()` | 质心惯性坐标 → 世界 |

`PxTransform::transform(point)` 做 `q.rotate(point) + p`，复合变换按“先右边，后左边”。位置使用 transform；方向/速度只做旋转时使用 rotate，不要把平移加到方向上。默认 `PxTransform()` **不初始化为单位变换**，显式写 `PxTransform(PxIdentity)`。[实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxTransform.h#L24-L38)、[点和变换复合](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/foundation/PxTransform.h#L105-L145)。

源码阅读注意：个别注释方向不够一致，例如 `setLocalPose` 的参数句和 `getRootGlobalPose` 的摘要。这里按 getter 的对象语义、变换乘法和实际实现核对：root getter 返回根连杆 `getGlobalPose()`，没有取逆。不要仅凭一句“world to actor”自行把根位姿反转。[Shape getter](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L181-L190)、[root 实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpArticulationReducedCoordinate.cpp#L426-L447)。

## 4. 质量、质心和惯量是独立参数

`setCMassLocalPose` 改变质量坐标相对 Actor 的位置和方向，**不会移动 Actor**。`setMass` 只改质量，不会连带重算惯量；`attachShape` 或修改 Shape 局部位姿也不会自动重算它。[质量 API](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L204-L295)、[Shape 位姿与惯量](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L158-L179)。

SDK 存 `getMassSpaceInertiaTensor()` 的三个对角值 `I_x,I_y,I_z`，它们定义在以质心为原点、按惯性主轴定向的质量坐标中。若从 CAD 得到 Actor 坐标下、关于质心的完整惯量矩阵，应先检查对称性、物理合理性和单位，再对角化：

$$
 I_C^{(A)}=R_{AC}\,\operatorname{diag}(I_x,I_y,I_z)R_{AC}^{T},\qquad
 I_C^{(W)}=R_{WC}\,\operatorname{diag}(I_x,I_y,I_z)R_{WC}^{T}.
$$

`R_AC` 的朝向放到 `setCMassLocalPose` 的旋转部分，三个特征值放到 `setMassSpaceInertiaTensor`；不能直接丢弃非对角元素。若输入惯量是关于 Actor 原点 O，需先用平行轴定理转换到质心 C，且全部在同一坐标系表示：

$$
 I_O=I_C+m\big((r^Tr)\mathbf{1}-rr^T\big),\quad r=p_C-p_O.
$$

这两式是刚体质量几何的关系，不是 PhysX 接触求解器方程。本章假设普通有限质量刚体；API 中质量 0 对 `PxRigidDynamic` 表示无限质量，惯量某项 0 表示该轴无限惯量，**不是无质量/自由转动**。`PxArticulationLink` 不允许这些 0 值。[惯量接口特殊值](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L234-L308)。

由几何构造均匀密度刚体时可调用 `PxRigidBodyExt::updateMassAndInertia(body, density)`；默认只纳入 simulation Shape，可选纳入非 simulation Shape。它会写质量、质心和惯量，应检查 bool。实现先合成各 Shape 质量矩，再计算质心并对角化；不提供 `massLocalPose` 时使用计算得到的质心，而不是强制 Actor 原点。源码能纠正“参数注释里的默认 `(0,0,0)` 就是最终质心”的误读。[扩展接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxRigidBodyExt.h#L32-L81)、[质心与对角化实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtRigidBodyExt.cpp#L33-L54)、[最终写回](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtRigidBodyExt.cpp#L233-L280)。

以均匀长方体半边长 `(a,b,c)` 为例，体积 `8abc`，质量 `m=8ρabc`，质心惯量 `I_x=m(b²+c²)/3`，其余循环置换。边长 1 m、密度 1 kg/m³ 时，质量 1 kg，三项惯量均为 1/6 kg·m²。这是理解参数的解析例子，**没有作为物理运行结果**。

### 为什么 Actor 原点速度不等于 getLinearVelocity

线速度 getter 返回质心速度，以世界方向表达；角速度也用于世界方向下的刚体速度关系。对世界点 P：

$$
 v_P=v_C+\omega\times(p_P-p_C).
$$

`PxRigidBodyExt::getVelocityAtPos` 先把质心局部位置变到世界，再用上式求点速度。因此不能用 Actor 原点位置的差分直接检查质心速度，除非原点与质心重合或转动项为零。改了质心局部位姿，SDK 也不会自动调整已经保存的线速度。[getter](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L378-L402)、[点速度实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtRigidBodyExt.cpp#L416-L430)。

## 5. 状态维度与 articulation 索引

### 刚体不是一条 SDK 统一 q 数组

一个自由刚体的姿态可以保存 3 个位置分量和 4 个四元数分量；速度是 3 个线速度加 3 个角速度。**7 个姿态标量不意味着 7 个机械自由度**。质量、惯量和 Shape 几何是模型属性；力、kinematic target、睡眠状态又不能由这 13 个数推回。`PxTransform` 内部字段顺序是 q 再 p，勿对对象直接 `memcpy` 成自己约定的 `[p,q]` 数组。

| 对象 | 配置/状态表达 | 读取/设置注意事项 |
|---|---|---|
| `PxRigidStatic` | 世界位姿；不作为动态速度状态 | 移动静态 Actor 可能重建优化结构，不适合连续移动障碍 |
| 普通 `PxRigidDynamic` | Actor 位姿、COM 线速度、角速度 | `setGlobalPose` 是瞬时设姿，不是运动轨迹；`setLinearVelocity` 会直接覆盖速度 |
| kinematic dynamic | 当前位姿 + 待执行的 target | `setKinematicTarget` 给下个物理步的世界目标，多次调用会覆盖旧目标 |
| fixed-base articulation | `n=getDofs()` 个关节位置和 `n` 个速度；根位姿是放置参数 | 基座没有额外自由运动 DOF，但根位姿仍需有明确坐标 |
| floating-base articulation | 上述关节量 + 根 Actor 位姿 7 个分量 + 根 COM 线/角速度 6 个分量 | `getDofs()` **不计入自由基座的 6 个 DOF** |

来源：[瞬时设姿](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidActor.h#L76-L106)、[kinematic target](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h#L63-L97)、[DOF 定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L711-L735)。这个 `n` 是关节状态数组的长度，不是以每根 link 各 7 个分量拼接得到的大小。

### Tree、joint frame 与 cache 排列

一个 articulation 是以 root 为起点的连杆树。每条非根 link 的 inbound joint 有 parent/child 两个局部关节坐标，分别相对各自的 **Actor frame**；不能把它们填成世界位姿或质心位姿。关节类型与各轴 motion 在入 Scene 前配置，默认关节类型为 undefined、motion 为 locked。`eTWIST/eSWING1/eSWING2` 分别对应局部 X/Y/Z 旋转，`eX/eY/eZ` 对应平移；锁住的轴不应当被当作自由状态槽位。[joint frame/type/motion](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationJointReducedCoordinate.h#L34-L124)、[axis/type 枚举](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/solver/PxSolverDefs.h#L245-L285)。

`jointPosition`/`jointVelocity` 的长度都是 `getDofs()`；旋转用 rad/rad·s⁻¹，平移用 L/L·s⁻¹。球关节缓存使用原生按轴的位置量，本版要求每轴位置在 `[-π, π]`，不是每个球关节追加四元数。revolute 与 revolute-unwrapped 的绕圈表示也不同。[cache 字段](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L201-L235)、[joint type](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/solver/PxSolverDefs.h#L274-L285)。

**加入 Scene 后**读取 `getLinkIndex()` 和 `getInboundJointDof()`；低层 link 索引按广度优先生成，可能不同于创建顺序。按低层 link 顺序累加各入关节 DOF，再在关节内按 `PxArticulationAxis::Enum` 排列有效轴。举例：低层 link 0,1,2,3 的 DOF 数为 0,1,2,1 时，关节数组偏移分别为“无”、0、1、3；link 2 占槽位 1、2。保存模型名称→link→轴→DOF 的显式映射，不能排序名称后直接写 cache。[link index](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationLink.h#L81-L95)、[cache 索引规则](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L201-L215)。

### Cache 是有生命周期的数据缓冲，不是模型本身

| 字段 / 操作 | 数据与权限 | 易错点 |
|---|---|---|
| `createCache()` / `cache->release()` | articulation 在 Scene 中才创建有效 cache；调用方负责释放 | 改结构后应释放重建，不能沿用旧大小/索引 |
| `copyInternalStateToCache(cache, flags)` | 把指定状态复制到 cache | 只更新 flags 选中的内容；不能假定所有数组有效 |
| `applyCache(cache, flags)` | 将指定可写状态应用回 articulation | 不能在物理步运行中调用；会按约定触发唤醒 |
| `rootLinkData->transform` | root **Actor** 世界位姿 | 不是 COM 位姿 |
| `rootLinkData->worldLinVel/worldAngVel` | root COM 的世界线/角速度 | 与 actor origin 不同 |
| `linkVelocity` | 每 link 的 COM 速度，世界表达，读取用 `eLINK_VELOCITY` | `PxSpatialVelocity` 含 linear、padding、angular、padding，不是紧密的六元素数组 |
| `zeroCache` | 清 cache 指定的数据区域 | 不直接修改 articulation，也不把 root 四元数设成单位旋转 |

`eALL` 只包含其枚举定义中的状态位；本版**不包含** joint force、joint target、link force/torque。目标和外力等字段有自己的读写权限，不能把 `eALL` 当作整个控制系统快照。[flags 定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationFlag.h#L24-L40)、[空间量/根数据](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L25-L67)、[cache 生命周期与读写](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L724-L801)。

## 6. 重置、快照与“状态已经刷新”

重置是一份应用契约：将哪些对象恢复成什么状态，控制器与时间如何同步。SDK 中瞬移一个 Actor 不等于重置整个环境。

对于本章示例限定的**普通、已在 Scene 中、启用 simulation 的独立动态刚体**：在上一轮 `fetchResults` 完成后，设初始 Actor 位姿、COM 线速度与角速度；按使用的 force mode 清理力/力矩累加器；明确睡眠/唤醒策略；再重置应用控制器、计时器和观测缓存。持续外力标志 `eRETAIN_ACCELERATIONS` 会影响跨步清理，不能仅关闭该标志就假定下一步外力为零。刚体的 `putToSleep()` 会清速度、力和 wake counter；若目标初始速度非零，就不能拿它作为“通用 reset 最后一步”。[保留外力语义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L124-L134)、[累加器清理](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L574-L619)、[睡眠](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h#L239-L252)。

Kinematic 的 target 与当前 pose 分开；`setGlobalPose` 不能自动表达本轮目标轨迹。articulation 应恢复根状态和 reduced joint state，而不是逐 link 强行覆盖位姿。两条原生路径要分开：

- **Cache 路径**：创建/读取合法 cache；只覆盖自己想恢复的字段；用 `ePOSITION | eVELOCITY | eROOT_TRANSFORM | eROOT_VELOCITIES` 等明确 mask 应用。`applyCache` 负责对应连杆状态更新。
- **Non-cache 路径**：批量调用 root / joint setters 后，用 `updateKinematic(ePOSITION)` 更新位置和速度；若只改速度，则用 `eVELOCITY`。完成后再查询 link 状态或启动下一步。

不要零填整个 cache 后直接用 `eALL` 应用：既可能生成非法 root 四元数，也把你未打算修改的量清掉。模型结构、关节轴顺序、cache 版本必须与保存时一致。[更新语义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L365-L374)、[applyCache 等价关系](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L760-L801)。

可以区分三种保存物：

| 保存物 | 应用需要记录的内容 | 能支持什么 |
|---|---|---|
| 状态记录 | 位姿、速度、关节数组、root、稳定对象/轴 ID、采样时间 | 可解释的观测或指定状态重置 |
| 环境恢复记录 | 上述状态 + model/hash、所有相关控制目标/外力、睡眠策略、控制器状态、随机数状态、步计数 | 定义清楚的应用重启；仍需验证恢复行为 |
| SDK 对象序列化 | 完整 `PxCollection` 及依赖、格式/SDK版本；兼容资源 | 对象图恢复，不自动包含宿主控制器、相机或应用时钟 |

`PxSerialization::complete` 会补齐 shape/material/mesh、joint/actor 等依赖。二进制输入还要求内存对齐和兼容的序列化格式；不支持序列化正在仿真的 Scene 中的对象。不能仅凭一个 collection 或 cache 宣称接触历史、内部缓存与外部程序状态都恢复，并保证逐位相同的后续轨迹。本阶段未作这类运行验证。[依赖规则](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L89-L116)、[二进制兼容与阶段要求](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L147-L164)、[序列化限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L188-L210)。

## 7. 一个物理步的时间与访问边界

先定义物理时钟 `t_k`、固定步长 `h>0`，以及由应用维护的整数步计数 k。一次成功提交并取回的 `simulate(h)` / `fetchResults(true)` 推进一次物理步；`fetchResults` 不是又推进一次。物理时间可按 `k*h` 计算，wall time 是执行所耗的时间，渲染帧率与二者都不同。[配对协议](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L954-L987)。

| 阶段 | 本章采用的保守访问约定 | 输出属于什么时刻 |
|---|---|---|
| 上一轮 fetch 已完成 | 读取状态 `x_k`，计算控制，设置输入/重置 | 控制使用 `t_k` 的状态 |
| `simulate(h)` 返回成功 | 计算任务已启动；执行与物理数据无关的应用工作 | 不把“函数返回”当作 `x_{k+1}` 已可读 |
| `checkResults(false)` | 仅查询是否完成计算 | 不交换/公开最终读取状态，不能替代 fetch |
| `fetchResults(true, &errorState)` | 等待、交付结果/回调；检查返回、错误回调和 errorState | 成功且无错误后读 `x_{k+1}` |
| 应用复制观测 | 复制需要保存的值，标注 k+1、h、坐标与对象 ID | 渲染/记录消费这份观测，不长期持有临时数组 |

不要把“用 lockRead/lockWrite 包住”理解为可以在任意物理阶段读写：线程互斥与 SDK 阶段限制是两回事。具体 API 有 split simulation 和回调阶段例外；本章统一在 fetch 完成后访问，例外留给后续扩展专题。[check/fetch 区别](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1023-L1064)、[锁契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1455-L1506)、[getter 阶段限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L378-L402)。

源码路线按以下路径读，而不是仅搜索 API 名字：

1. `NpScene::simulate` 转发 `simulateOrCollide(..., eADVANCE)`。
2. `simulateOrCollide` 检查上轮阶段是 complete、dt 为正，建立当前任务；非法重复 simulate 会报错。
3. `NpScene::checkResults` 只等待完成事件。
4. `NpScene::fetchResults` 核查阶段、等待完成、处理接触回调和前后同步，然后结束这一轮访问阶段。

入口：[simulate](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L2886-L2916)、[转发](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L2999-L3003)、[完成事件](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneFetchResults.cpp#L63-L70)、[fetch 实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneFetchResults.cpp#L484-L538)。此处只审查公开时间/状态协议，没有把调度入口冒充接触求解与积分算法的完整追踪。

### 时间步、子步与求解迭代是三种控制量

若控制周期为 H，一个控制周期分成 n 个外部物理子步时，`h=H/n`；应用执行 n 次完整的 `simulate(h)` / `fetchResults`。控制器可以每 H 更新一次并按契约保持输入，也可以每 h 更新一次，两者得到不同的闭环系统。kinematic target 是单步目标，外力也有跨步清理/保留语义，因此“保持输入”要按原生接口重新施加，不能只把 n 改大。

`setSolverIterationCounts(position, velocity)` 是约束求解预算；它不会把应用时钟变成 n 个独立 step。TGS 的 position iterations 有自己的时间处理方式，还存在每迭代施加外力的 scene flag；它仍不等价于外部重新调用多轮碰撞与 fetch。后续 E3 要沿 PGS/TGS 分支核实这些差异，当前不把某个迭代数换算成另一引擎的求解次数。[迭代入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h#L368-L387)、[TGS 外力时机选项](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L260-L277)。

固定步长只让协议明确，不自动保证稳定或精确。碰撞几何尺度、质量比、驱动增益、初始穿透、接触正则化及 solver 都会影响结果；本章不提供未经运行验证的“安全 dt”。若显示循环落后，应用应明确积累剩余 wall time、限制每显示帧可做的物理步数，并记录是否丢弃时间；不能悄悄把大 wall delta 直接当物理步长。

## 8. 最小 C++ 阅读片段

[examples/e1_state_boundary.cpp](../examples/e1_state_boundary.cpp) 包含三个独立函数：创建均匀 Box（展示 Shape 引用与质量设置）、读取 Actor/COM/Shape 世界位姿、配对推进一次物理步。它假设调用方已建立 SDK、Scene、dispatcher、filter shader 与 material，并保持这些对象有效；使用普通 CPU Scene，未启用 Direct GPU API。

示例是原生 API 教学片段，不是可直接启动的程序或 reset 框架；没有 `main`、没有循环试验或评分。片段已用匹配固定提交的公开头文件通过 `g++ -fsyntax-only`，未链接/运行 SDK；命令和范围见[验证记录](validation/e1.md)。语法/类型检查即使通过，也不验证 SDK 链接、资源销毁、运行错误或物理结果。

## 9. 易错点与定位顺序

| 现象或误读 | 先核对的边界 |
|---|---|
| 看起来接触，实际穿过去 | visual geometry 与 simulation Shape 是否同一表示；flags、cooking 是否成功 |
| 盒子尺寸大一倍、胶囊方向不对 | Box 半边长；capsule 本地 X 轴；shape local pose |
| 改质量后运动异常 | setMass 是否同时配套了正确惯量；单位与 COM 主轴是否一致 |
| 改 shape 后重心不变 | Shape 操作不自动更新质量属性，显式计算/指定 |
| reset 后第一帧 link pose 是旧的 | non-cache articulation setters 后是否 updateKinematic |
| cache 写错关节 | 是否用入 Scene 后低层索引和有效轴映射；不是创建顺序 |
| 下一步仍有力或突然移动 | 外力保留标志、累加器、旧控制目标、kinematic target 与控制器状态 |
| 看似线程安全仍报访问错误 | 互斥锁不能替代 fetch 和 SDK 阶段规则 |
| 状态坐标不一致 | Actor pose、COM 速度、Shape local pose 是否混装为同一 frame |
| 只看到 float64 Python 数据 | 宿主数组类型不能证明原生 PxReal 或求解精度 |

## 10. 阅读练习与答案

1. 世界 Actor 位姿为 `(1,0,0)` 且无旋转；Shape local pose 为 `(0,2,0)` 且无旋转；COM local pose 为 `(0,0,0.5)`。三个世界原点在哪里？哪个用作 `getLinearVelocity` 的参考点？
2. 把同一个米制模型改为厘米制而质量单位不变：为什么惯量不是乘 100？为何只设置 tolerances scale 不够？
3. `setMass(2)` 之后读出的 inertia 仍与之前相同，是错误吗？`setMass(0)` 能代表无质量传感器吗？
4. 一个 floating-base articulation 有两个单自由度关节。`getDofs()` 为多少？root pose 和 root velocity 应存多少标量？能否按两个 link 的创建顺序复制 cache？
5. 调用 `zeroCache` 再 `applyCache(eALL)` 能否得到单位 root pose、零控制目标、无外力的完整环境重置？
6. `checkResults(true)` 返回 true 后立刻读位姿，和 `fetchResults(true)` 后读位姿等价吗？若把 H=0.02 s 分成 4 步，时钟和目标更新怎样记录？
7. 定位源码中的两个注释歧义：默认 massLocalPose 和 root global pose 方向，如何用实现判断？

<details>
<summary>答案与源码核对点</summary>

1. Actor 原点 `(1,0,0)`，Shape 原点 `(1,2,0)`，COM 原点 `(1,0,0.5)`。线速度对应最后一个点；其他点速度还需要角速度叉乘位移。
2. 惯量量纲是 ML²，长度数字乘 100 时惯量乘 10⁴；密度数字除 10⁶。scale 只影响若干参考阈值，几何、重力、密度、惯量仍需应用一致换算。
3. 不是错误，`setMass` 不更新 inertia；若希望相应改变质量分布，调用合适的扩展函数或自己提供一致值。0 是该 API 的无限质量特殊值，不能表示无质量。
4. `getDofs()==2`，不含基座 6 DOF。root pose 存位置 3 + quaternion 4，root velocity 存线 3 + 角 3。缓存要用低层 link index 和轴映射；创建顺序没有这个保证。
5. 不能。zeroCache 只清缓冲，零四元数也不是单位旋转；eALL 不含所有控制/外力字段，应用控制器和时钟更不在其中。应使用合法 root pose、明确 mask 和环境重置契约。
6. 不等价，check 只检查完成，没有完成 fetch 的结果交付过程。四轮完整 simulate/fetch 的 h=0.005 s，总计推进 0.02 s；写清控制是在 H 更新保持还是每 h 更新，kinematic target/力如何按子步提交。
7. `computeMassAndDiagInertia` 在未锁定 COM 时调用 `getCenterOfMass()`；root getter 返回 root 的 `getGlobalPose()`。分别以它们和 PxTransform 的组合语义为准，保留歧义说明，不照搬相冲突的短注释。

</details>

## 下一步

E2 在这些对象、坐标与采样约定之上展开驱动、关节映射、机器人接口和任务控制；E3 展开接触/材料组合、约束和 PGS/TGS 的积分数值语义。两者都保留 native C++ 入口和宿主边界。未来实验案例链接到 [DexLab](https://github.com/huangkiki/Dexlab)，本章没有产生新实验结果。
