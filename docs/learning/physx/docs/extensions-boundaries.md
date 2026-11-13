# E6：原生扩展、GPU 与能力边界

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [完整路线](curriculum.md) · [源码地图](source-map.md) · [本章验收](validation/e6.md)

先修：[E1 对象/COM/时间](modeling-state-time.md)、[E2 驱动](control-robotics.md)、[E3 接触与求解](contact-solvers.md)；GPU 所有权和同步可先看 [E5](batch-learning-data.md)。本章完成 B6 的原生扩展/后端边界与 B7 综合追踪，也补充 B0/B4 的非刚体状态和数值语义。

固定基线仍是 `ovphysx-0.6.3`、提交 `da950a3537927784951853c66618036f332ca0ce`、SDK **头文件** 5.11.0。以下结论来自公开源码和契约，不是运行验收。没有构建、链接或执行 SDK，没有 CUDA 编译/JIT、仿真、渲染、训练或基准。历史 Isaac Sim 5.1 / UniSim 1.7.10 所用核心 binary/config 仍须由 [DexLab #126](https://github.com/huangkiki/Dexlab/issues/126) 的原批次证据确定，不能用本章默认值补齐。

## 1. “扩展 PhysX”具体扩展哪一层

| 需求 | 原生入口/实现位置 | 扩展者承担的责任 |
|---|---|---|
| 增加关节或自定义运动关系 | `PxPhysics::createConstraint`、`PxConstraintConnector`、`PxConstraintSolverPrep` | 用原生一维行描述几何误差和速度关系；管理数据块、COM/origin 变化和 release |
| 增加碰撞几何 | `PxCustomGeometry::Callbacks` | bounds、接触、query、质量属性和缓存一致；不能只返回一个视觉 mesh |
| 修改已有接触 | `PxContactModifyCallback` / `PxCCDContactModifyCallback` | 在允许的线程/阶段改 contact set；不能添加任意数量的接触，也不是替换整个求解器 |
| GPU 数据/额外计算 | `PxDirectGPUAPI`、particle/deformable callbacks | 设备指针、容量、事件和阶段；回调中的自定义 CUDA 工作属于应用 |
| 使用已提供的扩展 | Character Controller、Vehicle components、Immediate Mode | 按该扩展的状态/更新契约组织程序，不把它们混成一个通用机器人 API |
| 改算法本身 | 修改公开 C++/CUDA 实现并维护自己的 build | 接口/数值/版本责任转移到该派生实现；公开源码不等于运行时可注册任意 GPU solver 插件 |

[`createConstraint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPhysics.h#L593-L609) 接收两 actor、connector、shader table 和数据块大小；这里的 shader 是**约束行准备函数**，不是图像 shader。Character Controller 的 [`move`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/characterkinematic/PxController.h#L645-L656) 是 collide-and-slide 位移接口，底层使用 [kinematic actor](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/characterkinematic/PxController.h#L393-L420)，不能据此声称它是有执行器动力学的人形机器人。Vehicle 的 [`PxVehicleComponentSequence`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/vehicle/PxVehicleComponentSequence.h#L43-L110) 支持组件与 substep group；该局部更新次数不自动等于 Scene 的物理步数。

[Immediate Mode](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxImmediateMode.h#L79-L243) 公开构造 solver bodies、生成 contacts、batch/求解约束及积分函数。这让调用者显式组织数据与阶段，同时也把 contact cache/allocator 生命周期、对象索引及一致步长的责任交给调用者；不是一行替换 `simulate` 就能得到完整 Scene 服务。本章读这些原生接缝，不另建统一 wrapper。

## 2. 自定义几何：碰撞、查询、质量必须一致

### 2.1 回调是共享对象引用，不是拥有数据的网格

[`PxCustomGeometry`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxCustomGeometry.h#L197-L258) 仅保存 `Callbacks*`；复制 geometry 也只是复制该指针，`isValid()` 只检查类型和非空指针。它既不证明几何算法正确，也不延长回调对象生命周期。应用应保证回调及其依赖数据晚于所有使用它的 shapes/queries 释放；不要把栈上 callback 的地址留在长期 shape 内。

| 回调 | 输入/输出契约 | 常见误用 |
|---|---|---|
| `getCustomType` | 用官方宏产生应用侧 type ID；SDK 不用它替换 dispatch 类型 | 把运行时 ID 当跨进程资产 ID |
| `getLocalBounds` | geometry **局部坐标** AABB | 返回 world AABB；或小于实际碰撞支持集，造成 broad phase 漏检 |
| `generateContacts` | 两 geometry/world poses、contactDistance、margin、toleranceLength → `PxContactBuffer` | 只实现相交测试，没有一致的法向/分离量/接触点 |
| `raycast` | 单位方向、最大距离、hit flags、maxHits、**stride** | 连续紧密写 `PxGeomRaycastHit[]`，忽略传入 stride；把未填字段宣称有效 |
| `overlap` / `sweep` | 本几何与另一几何；sweep 中移动的是 `geom1` | 几何对和运动方向写反 |
| `computeMassProperties` | 动态使用时提供局部质量、COM、惯量 | 可碰撞即假定质量正确；忽略密度或几何 margin |
| `visualize` / `usePersistentContactManifold` | 调试图元；PCM 是否可复用及失效阈值 | 把 debug 画面当 renderer；几何变了却继续复用旧接触 |

逐字段见 [Callbacks 声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxCustomGeometry.h#L74-L194)。即使 `visualize` 注释写 optional，它在基类仍是纯虚函数，可提供空实现，而不是省掉所有 override。查询与碰撞可能由不同调用线程使用同一 callback；本章建议数据在一个模拟/查询阶段内保持只读、临时量放栈上，应用自行同步形状修改。其依据是指针共享以及 E4/E5 的并发调用边界，而非声称 SDK 会替应用加锁。

### 2.2 用 cylinder 读懂 support、margin 与惯量

官方 [`PxCustomGeometryExt::CylinderCallbacks`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCustomGeometryExt.h#L62-L123) 给出现成实现，axis 的 `0/1/2` 分别为局部 X/Y/Z，height 是**全高**。对局部 X 轴、无 margin 的圆柱，支持点可写为：

$$
s(\mathbf d)=\left(\operatorname{sign}(d_x)H/2,\ R\frac{d_y}{\sqrt{d_y^2+d_z^2}},\ R\frac{d_z}{\sqrt{d_y^2+d_z^2}}\right).
$$

假设方向非零；纯轴向需要单独处理，不能除以零。源码 [`supportLocal`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtCustomGeometryExt.cpp#L604-L639) 包含这个分支，并将 bounds 按 margin 扩张。对密度为 $\rho$ 的实心圆柱：

$$
m=\rho\pi R^2H,\qquad I_{xx}=\tfrac12mR^2,\qquad I_{yy}=I_{zz}=\tfrac1{12}m(3R^2+H^2).
$$

长度量纲为 $L$、密度 $ML^{-3}$、惯量 $ML^2$。原生质量构造约定是[密度 1，质量/惯量随密度线性缩放](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxMassProperties.h#L50-L59)。[`computeMassProperties`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtCustomGeometryExt.cpp#L642-L665) 的 margin=0 分支正是上述圆柱式；margin 非零转入分片计算，不能继续套裸圆柱惯量后称为同一几何。

这个例子展示扩展协议，不表示新版只有 custom geometry 才能表达圆柱：[`PxConvexCore`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxConvexCoreGeometry.h#L24-L41) 已定义 point/segment/box/ellipsoid/cylinder/cone。原生 convex core 和虚函数 custom geometry 是不同 dispatch 身份，需分别核对支持矩阵。

### 2.3 PCM 与 GPU 回退

[`GuPCMContactCustomGeometry`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/geomutils/src/pcm/GuPCMContactCustomGeometry.cpp#L17-L105) 先判断 PCM 缓存是否失效；有效时可复用 manifold，不保证每步调用 `generateContacts`。交换 geometry 顺序后还会[翻转输出法向](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/geomutils/src/pcm/GuPCMContactCustomGeometry.cpp#L108-L115)。修改 callback 内部参数时，不能假定 SDK 自动知道所有 shape/query/contact cache 已过期；在安全阶段更新原生 shape 几何并处理质量/查询更新，具体变化需按使用路径验证。

GPU Scene 也不会把 C++ 虚函数自动编译成 CUDA。固定源码的 sphere/custom 等 pair 被送往 [`eFallback`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpunarrowphase/src/PxgNphaseImplementationContext.cpp#L1328-L1348)，GPU dispatcher 将其交给 [CPU fallback context](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScScene.cpp#L851-L905)。cloth/custom 的分支还明确写有[过滤限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpunarrowphase/src/PxgNphaseImplementationContext.cpp#L1170-L1182)；因此刚体 pair 能回退不等于 deformable/particle 与任意 custom geometry 都支持碰撞。

## 3. 自定义约束：把关系写成一维行

### 3.1 行的物理含义与单位

原生 [`Px1DConstraint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h#L93-L208) 把两个刚体的世界坐标速度组合为：

$$
\mathbf u=[\mathbf v_0,\boldsymbol\omega_0,\mathbf v_1,\boldsymbol\omega_1]^T,\qquad
J=[\mathbf l_0,\mathbf a_0,-\mathbf l_1,-\mathbf a_1],\qquad
v_c=J\mathbf u.
$$

注意后两个分量的负号由 SDK 定义；不能在 `linear1/angular1` 再额外取负，除非你的几何约束本身如此。对一个 world 单位轴 $\mathbf n$ 上的点间关系，$\mathbf l_i=\mathbf n$、$\mathbf a_i=\mathbf r_i\times\mathbf n$，$\mathbf r_i$ 从该 body COM 指向 attachment。这样 $v_c$ 是 $L/T$，角 Jacobian 分量有长度量纲，不能把“angular 字段”一律理解为无量纲旋转轴。

硬约束的位置阶段以几何误差 $g$、target $v_t$ 表达 $J\mathbf u+\beta g/h-v_t=0$；$\beta$ 是内部稳定化系数。velocity 阶段通常移除 bias，`eKEEPBIAS` 有例外。spring 则定义隐式力或加速度：

$$
f=-k\,g_{new}+c\,(v_t-v_{c,new}).
$$

线性 **force spring** 中 $f$ 为力，$k$ 是 $M/T^2$（SI: N/m），$c$ 是 $M/T$（N·s/m）；**acceleration spring** 的 $k,c$ 分别为 $T^{-2},T^{-1}$。纯旋转 force row 的输出改为力矩，刚度相应为 N·m/rad。公式以一致的单位制、固定行方向和本步线性化为前提，不能据“隐式”二字保证任意刚度、步长和接触切换稳定。

| 字段/标志 | 作用 | 必须留意 |
|---|---|---|
| `geometricError` / `velocityTarget` | 本行位置误差/速度目标 | 线性和角向行的量纲不同；target 不是求解后的速度 |
| `minImpulse` / `maxImpulse` | 允许的累计行冲量区间 | 默认按冲量；force-limit 转换有两重条件 |
| `eSPRING` / `eACCELERATION_SPRING` | spring 模型/质量归一化加速度模型 | acceleration 位仅对 spring 有效；与 restitution 模型区分 |
| `eOUTPUT_FORCE` | 此行参与 constraint 总输出和断裂判断 | 未设时仍可参与求解，但不进入该报告 |
| `eANGULAR_CONSTRAINT` / `solveHint` | 类型与预处理提示 | 不保证行一定保留；退化响应和预处理仍影响结果 |
| `PxConstraintInvMassScale` | 此 constraint 的逆质量/逆惯量缩放 | 不是修改 body 实际质量；会影响观测的物理解释 |

原生标志见 [row flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h#L29-L90)。一个值得实际追源码的冲突：该文件 `eHAS_DRIVE_LIMIT` 短注释写的 `unless` 与执行条件相反；[共享 CPU/GPU helper](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h#L34-L57) 实际是 **hasDriveLimit 和 driveLimitsAreForces 都为真时乘 `simDt`**，否则原值当 impulse。`eDRIVE_LIMITS_ARE_FORCES` 在[当前公开 flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraint.h#L27-L40) 已标 deprecated，本文按固定实现讲解，既不删掉历史分支，也不把未来行为当现在行为。

### 3.2 从接口实现到生命周期

1. 应用定义可按字节复制的 constant block，保存参数和 body-local attachment frames；不要在 shader 中追踪随时可变的外部状态。
2. 实现 `PxConstraintConnector`，向 SDK 返回 `prepareData()` 和 shader/constant 指针；修改数据后 `markDirty()`。SDK 会在步开始复制[数据块](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpConstraint.cpp#L301-L334)，不是每行执行时重新调用应用的 setter。
3. 实现 `PxConstraintSolverPrep`：只访问传入参数，返回不超过 `maxConstraints` 的行数，并完整填写所用行、inverse-mass scales、anchor 输出和 `bodyAWorldOffset`。该函数[必须可重入](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h#L234-L264)。输入 transform 是 COM frame；static/null actor 对应 identity，应用的数据需正确承担 world anchoring。
4. 用 `PxConstraintShaderTable` 和 `createConstraint` 接入。actor-local frames 与 COM-local frames 是不同层；COM 变化需要 [`onComShift`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h#L397-L420)，world origin shift 可能也需改数据并重新标 dirty。
5. 释放应从 `PxConstraint::release()` 进入，等 [`onConstraintRelease`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraintDesc.h#L384-L395) 回调再释放 connector 资源。serialization、debug/PVD 和 owner ID 各有自己的 hook，并非创建成功就自动完成应用资产序列化。

本章原创 [C++ row-prep 片段](../examples/e6_constraint_row.cpp) 描述一个**固定 world 轴、双 attachment、对称冲量限幅的双向弹簧**。它完整实现一个原生 solver-prep 签名，且把 force spring 和 raw impulse cap 分开。没有 `main`、connector 或资源创建；它是行构造阅读片段，不是可加载的完整插件。语法/类型检查见[验收记录](validation/e6.md)，还没有验证约束实际收敛、受力或 GPU 行为。

### 3.3 CPU / GPU / Direct GPU 不是同一扩展契约

一般 Scene 的公开 custom constraint 路径允许 CPU row preparation；GPU dynamics 还有自己的数据准备和受支持关节路径。不能凭 shader table 含一个函数指针，就推断 CPU callback 可在 GPU 执行。

[`eGPU_COMPATIBLE`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraint.h#L27-L40) 是内部位，[公开 setter 明确拒绝](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpConstraint.cpp#L269-L290)；Direct GPU Scene 的 [constraint 加入逻辑](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L4669-L4683) 拒绝非兼容项并建议 D6。固定源码 [`D6`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtD6Joint.cpp#L1193-L1197) 的官方 shader table 有该位，而 [`DistanceJoint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L258-L269) 没有。学习下一节 CPU DistanceJoint 路径不等于它可直接迁移到 Direct GPU；更不能伪设内部位绕过真实数据布局要求。

## 4. B7 综合追踪：一个距离弹簧怎样产生报告力

选择**原生 DistanceJoint、两个普通刚体、CPU PGS、非退化 attachment 距离**，不包含 articulation 的 extended response、不含 inverse-mass scaling、不把接触混入关节报告。TGS 和 GPU 分支另列，避免拼成一条不存在的执行链。

### 4.1 配置与数据块

[`PxDistanceJointCreate`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L262-L269) 检查 frames 和 actors，经 [`createJointT`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtJoint.h#L48-L65) 创建 extension 对象，再调用 `physics.createConstraint(..., sizeof(DataType))`。`setMinDistance/setMaxDistance/setStiffness/setDamping/setDistanceJointFlags` [写入数据并 markDirty](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L32-L123)。`ExtJoint::prepareData()` [返回 mData](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtJoint.h#L475-L505)，随后进入上一节的 SDK 复制路径。

设置相等 min/max 且同时启用两限位才能表达定距目标；只开 max 是单边“绳长上限”。默认只开 max、tolerance 为 `0.025 * scale.length`，stiffness/damping 为 0；不能以默认 joint 宣称已启用弹簧。[默认初始化](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L14-L25)

### 4.2 几何到行

[`DistanceJointSolverPrep`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L193-L254) 从两个 world joint frame 得到 $d=\|\mathbf p_A-\mathbf p_B\|$、$\mathbf n=(\mathbf p_A-\mathbf p_B)/d$。当 d 很小时采用固定 X 轴，这只是确定一个数值方向，不是证明重合 attachment 的距离梯度唯一。相等上下限的几何误差为：

$$
g=\begin{cases}
d-d_0-\epsilon,&d-d_0>\epsilon,\\
d-d_0+\epsilon,&d-d_0<-\epsilon,\\
0,&|d-d_0|\le\epsilon.
\end{cases}
$$

$\epsilon$ 是 joint tolerance，量纲 $L$，它是几何死区，不是“求解残差小于 epsilon 就停止”。只开 min 时 `minImpulse=0`；只开 max 时 `maxImpulse=0`，符号与 $\mathbf n$ 一起决定拉/推；两限位不相等时 shader 生成两行，因为此时没有速度用于预先判断哪边即将激活。[行填充及单边区间](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDistanceJoint.cpp#L156-L191)

`ConstraintHelper` 当前以 joint B 点作为两侧力臂的共同参考点；对距离行，因为 $\mathbf p_A-\mathbf p_B$ 平行 $\mathbf n$，用 A/B 点算 body A 的 $\mathbf r\times\mathbf n$ 等价。[具体 frame/offset 实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtConstraintHelper.h#L123-L146) 解释了为什么不能只看变量名推测 torque 的参考点。

### 4.3 行准备、隐式系数与迭代

CPU PGS 的 [`DyDynamics`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyDynamics.cpp#L2280-L2337) 取 constant block、COM poses、writeback pool，并尝试四约束批处理；失败/不适用时逐项调用 [`SetupSolverConstraint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyConstraintSetup.cpp#L803-L835)。因此下面的标量链是该 fallback 准备/求解路径的解释，不声称所有 joint 每次都绕过 SIMD。

row prep → 预处理/惯性转换 → unit response $w=JM^{-1}J^T$ → solver constants。对本节的线性 force spring，令 $h$ 是 Scene step，$v_t$ 为 target、$g$ 为行误差：

$$
a=h^2k+hc,\qquad b=h(cv_t-kg),\qquad x=\frac{1}{1+aw}.
$$

对应 PGS [`compute1dConstraintSolverConstantsPGS`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h#L174-L208) 先产生 `constant=xb`、`velMultiplier=-xa`、`impulseMultiplier=1-x`，随后[加上初始速度 bias](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h#L230-L234)，使最终 `constant=xb-xa*v_pre`。$w$ 对该线性行是 $M^{-1}$，$a$ 是 $M$、$b$ 是冲量 $ML/T$，所以 $aw$ 无量纲；若切到 acceleration spring，源码会引入 `recipUnitResponse`，不能沿用上述刚度单位。

[`solve1D`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L44-L128) 计算累计候选冲量并投影到上下限：

$$
\Lambda_{new}=\operatorname{clip}\left((1-x)\Lambda_{old}-xa\,v_c+xb,\Lambda_{min},\Lambda_{max}\right),\quad
\Delta\mathbf u=M^{-1}J^T(\Lambda_{new}-\Lambda_{old}).
$$

这里将 $v_c=v_{pre}+\Delta v_c$ 写成当前总行速度：原生 `normalVel` 是 solver 累计的速度增量，初始项已进入 `constant`，不能重复加减。该式限定为前述普通刚体 force-spring 行；不能当任意离线 state 的通用一步公式。solver 内部 angular state 采用惯性平方根变换，源码注释称 momocity。内部变量 `appliedForce` 实际累积的是**冲量**。位置/速度迭代上限和积分顺序接 [E3](contact-solvers.md)，不是在这里额外添加一个 epsilon 收敛检测。

### 4.4 writeback 到原生 getter

[`writeBack1D`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L578-L603) 只求和带 `eOUTPUT_FORCE` 的行，先得 body 0 的线/角冲量，再把角冲量从 COM 平移至 `body0WorldOffset` 对应点：

$$
\mathbf P=\sum_i\mathbf l_{0i}\Lambda_i,\quad
\mathbf L_{ref}=\sum_i\mathbf a_{0i}\Lambda_i-\mathbf r_{ref}\times\mathbf P,\qquad
\bar{\mathbf f}=\mathbf P/h,\quad\bar{\boldsymbol\tau}=\mathbf L_{ref}/h.
$$

世界坐标分量分别为 $ML/T$、$ML^2/T$，除以 step 后是 N 和 N·m（SI）。[`Sc::ConstraintSim::getForce`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScConstraintSim.cpp#L148-L154) 用 Scene 的 `oneOverDt` 转换；[`NpConstraint::getForce`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpConstraint.cpp#L292-L299) 检查读取阶段再进入 core。推荐在成功 `fetchResults` 后采样，不把 getter 调用时间误写成新的物理时刻。

断裂阈值也先[乘 simDt](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyConstraintSetup.cpp#L658-L664) 成冲量，再比较线/角冲量范数。报告只覆盖被标记的 constraint 行；未启用输出、休眠/未激活、退化行、断裂或未在 Scene 等状态必须另外解释。它不是 actor 所有接触/重力/驱动总 wrench，也不是 E4 的 articulation incoming joint force。

TGS 使用 [`DyTGSDynamics`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L948-L978) 和 [TGS 行系数](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/shared/DyCpuGpu1dConstraint.h#L398-L434)，含 `stepDt`、位置增量及不同 bias 更新；不能把 PGS 的 h 原样套到所有 TGS 内部变量。GPU 是下一节的独立调度/布局，CPU trace 不构成 GPU 数值等价或性能结论。

## 5. GPU 后端：公开了什么，仍需什么

固定树公开 GPU 代码。说“PhysX GPU 后端一概闭源”不符合本章版本；反过来，文件存在也不代表本机已安装匹配 GPU library、driver 或测试过全部 pair。

| 层次 | 固定源码证据 | 不能推出的结论 |
|---|---|---|
| Scene/backend 选择 | [`ScScene`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScScene.cpp#L851-L914) 根据 useGpuDynamics 分 CPU/GPU，并建立 CPU narrowphase fallback | GPU broad phase = GPU dynamics = Direct GPU 三者等价 |
| GPU solver 选择 | [`PxgPhysXGpu::createGpuDynamicsContext`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxgpu/src/PxgPhysXGpu.cpp#L208-L225) 根据 solverType 构造 PGS/TGS context | 所有宿主固定使用 TGS；当前设置能填历史批次 |
| 刚体/约束内核 | [`solverMultiBlock.cu`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/CUDA/solverMultiBlock.cu)、[`solverMultiBlockTGS.cu`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusolver/src/CUDA/solverMultiBlockTGS.cu#L78-L153) 的约束/接触写回分支 | 与 CPU bitwise 相等或任意 custom shader 支持 Direct GPU |
| articulation | [`forwardDynamic2.cu`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpuarticulation/src/CUDA/forwardDynamic2.cu) | 所有 CPU cache/getter 在 Direct GPU 下仍有效，详见 E5 |
| FEM 与粒子 | 本章第 6–7 节的公开 CUDA 实现 | 图像、RL、autograd、任意多物理模型自动具备 |
| 构建/装载 | [`PhysXGpu.cmake`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/compiler/cmakegpu/PhysXGpu.cmake#L27-L38) 汇集多个 GPU object targets；[Linux loader](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/gpu/PxPhysXGpuModuleLoader.cpp#L169-L212) 依赖 libcuda 与匹配 GPU library 导出符号 | 仅有 C++ 头文件即已构建或运行 GPU；驱动实现属于本仓源码 |

“GPU scene”仍可能包含 CPU 工作。[`registerContactManager`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpunarrowphase/src/PxgNphaseImplementationContext.cpp#L1609-L1638) 要求 PCM、无 contact modification、离散检测等条件才查 GPU pair table；其余走 fallback。故 contact modification 开关、cooking 是否生成相应数据、mesh/geometry 类型与 pair 支持都会改变执行路径。同步、GPU index、首步初始化、device events、scene-wide padded stride 的细节仍按 [E5](batch-learning-data.md) 执行，不能只记录一个 `device=cuda` 字符串。

**公开范围与外部范围分开记：**上表的 SDK CPU/CUDA 与扩展实现在固定官方树内可读；CUDA driver/toolchain、目标机器实际加载的 binary、宿主 importer/renderer/RL 版本和用户自定义插件不由这些文件证明。本章没有为整个仓库全部 GPU 内核作形式正确性审计，没有下载或执行任何 GPU 二进制。

## 6. Deformable volume / surface：不是换一个刚体 shape

### 6.1 对象、拓扑和状态

[`PxDeformableVolume`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableVolume.h#L43-L49) 与 [`PxDeformableSurface`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableSurface.h#L49-L55) 明确仅支持 GPU，要求 GPU dynamics 和 GPU broad phase。它们继承 `PxDeformableBody`，不使用 rigid body 的单一 pose、COM 和 6D 速度来完整表示形变。

| 对象/数据 | 原生意义 | 容量、所有权和更新时间 |
|---|---|---|
| volume collision mesh | 接触几何的四面体网格；`getPositionInvMassBufferD` / rest buffer | collision vertex count；attachShape 分配、detachShape 释放 |
| volume simulation mesh | 形变求解自由度；`getSimPositionInvMassBufferD` / `getSimVelocityBufferD` | simulation vertex count；与 collision count 可不同，不能混索引 |
| surface mesh | 三角形顶点的位置/速度/rest 数据 | 三角 mesh vertex count；由 shape 生命周期约束 |
| per-vertex `PxVec4` | xyz 位置/速度，位置 w 为 inverse mass，速度 w 未使用 | device 地址；每顶点 16B 对齐，不是 CPU 可直接解引用数组 |
| 应用修改 | volume `markDirty(eSIM_POSITION_INVMASS/...)` 或 surface 对应 flag | dirty 只通知引擎，不替应用拷贝数据、等待 CUDA 或构造有效初态 |

[Volume 完整 buffer 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableVolume.h#L106-L242) 和 [surface 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableSurface.h#L135-L223) 明确：从 simulate 开始到 fetchResults 返回不得写；读取必须等 PhysX tasks 完成，文档特别允许 completion task 读。需要在 GPU 合法时间读取并完成 D→H 拷贝，CPU 才有自己的快照。`markDirty` 不能消除这些同步条件。固定 [`NpScene`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L1527-L1617) 还检查 shape/simulation mesh 前置条件，不能把空 actor 成功分配当“软体创建完成”。

### 6.2 材料、FEM 与数值分支

[`PxDeformableMaterial`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableMaterial.h#L28-L93) 提供 Young's modulus $E$、Poisson ratio $\nu$、dynamic friction、elasticity damping；volume 另有 [`eCO_ROTATIONAL` / `eNEO_HOOKEAN`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableVolumeMaterial.h#L16-L49)。这里 E 量纲为压力 $ML^{-1}T^{-2}$（Pa），不是刚体 contact stiffness 的 N/m；$\nu$ 无量纲。质量通过网格顶点 inverse mass 参与求解，不能用一个外观材质替代力学参数。

对各向同性材料、$E>0$ 且 $0\le\nu<0.5$，源码 [Lamé 参数](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/deformableUtils.cuh#L116-L123) 为：

$$
\lambda_{L}=\frac{E\nu}{(1+\nu)(1-2\nu)},\qquad \mu=\frac{E}{2(1+\nu)}.
$$

不要把 $\lambda_L$ 和约束乘子同名混用。公开 API 允许 $\nu=0.5$，但上式在端点奇异；实际 kernel 的体积项有单独分支，不能由连续公式替实现做除零。

以 [`softBodyGM.cu` 的 co-rotational 分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/softBodyGM.cu#L914-L1004) 为例，rest 边矩阵 $D_m$ 和变形后边矩阵 $D_s$ 给出无量纲 $F=D_sD_m^{-1}$，tet rest volume $V$，rotation R。该路径先处理 ARAP 形变项，再处理 $\det(F)-1$ 体积项；[ARAP 代码](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/softBodyGM.cu#L717-L758) 在范数中还加了数值 epsilon。不能将它描述为“每步一次精确解线性 FEM”，也不能把 neo-Hookean 路径的含义直接替成此分支。

在无阻尼、单个无量纲约束 C、未触发 `abs(denom) < 1e-15` 保护的分母条件下，[对应更新](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/softBodyGM.cu#L553-L593) 是：

$$
\Delta\ell=\frac{-C-\tilde\alpha\ell}{\sum_i w_i\|\nabla_i C\|^2+\tilde\alpha},\qquad
\Delta\mathbf x_i=w_i\nabla_i C\,\Delta\ell.
$$

$w_i=1/m_i$；ARAP 分支 $\tilde\alpha=1/(2\mu Vh^2)$。因此 $\tilde\alpha$ 和分母量纲均为 $M^{-1}L^{-2}$，$\ell$ 为 $ML^2$，$\Delta x$ 为长度。这里的乘子不是刚体行冲量，不可直接除以 h 叫作 Newton。带阻尼分支会改变分母和分子；TGS/non-TGS 对 multiplier 初始化/复用也不同，见上述具体行。表面上都出现“迭代”，不意味着其迭代和 E3 刚体行求解可等量比较。

surface 有厚度、弯曲刚度/阻尼的[材料接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableSurfaceMaterial.h#L28-L77)。[`FEMClothUtil`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMClothUtil.cuh#L420-L486) 使用 `area * thickness` 构造体积尺度并解膜/面积项；[`FEMCloth.cu`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMCloth.cu#L594-L650) 将位置修正按 `delta / dt` 写入速度，另有 triangle-pair bending 路径。厚度是 $L$，不能把它当接触 offset；弯曲/阻尼数值也不能未经该模型的实现/单位转换就照抄材料手册或其他引擎。本章不为这些值提供未验证的实物标定配方。

### 6.3 耦合、attachment 与 callback

[`PxDeformableAttachmentData`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDeformableAttachment.h#L39-L74) 要求至少一方是 deformable：surface 使用 vertex/triangle，volume 使用 **simulation mesh** vertex/tetrahedron，rigid 使用局部笛卡尔点，world 使用世界点；元素内位置由重心坐标表示。对 tetrahedron 内点 $\mathbf p=\sum_{i=0}^3b_i\mathbf x_i$，$\sum b_i=1$，位于元素内部时 $b_i\ge0$，b 无量纲。拓扑创建后固定，变更 attachment 点需重建；rigid/world pose 可更新。这与“每步把所有顶点强行写到目标”是不同约束。

公开 [cloth-rigid contact prep](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/FEMClothConstraintPrep.cu#L33-L109) 使用接触位置、重心信息、刚体/顶点响应准备耦合约束。原生存在这些特定耦合，不等于支持任意几何 pair、断裂、热传导、电磁、流固材料模型或工程认证精度；每一种额外物理都要明确方程、耦合接口、实现者和验证范围。

Scene 的 [`PxPostSolveCallback::onPostSolve(CUevent)`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L138-L150) 只给出 solver 完成事件；用户 stream 应等待它后才读结果。它不意味着 CPU 已同步，也不承诺引擎自动等待你另一个 stream 后续任意写入；应用需在下一次引擎访问前建立正确依赖。注册入口见[deformable callbacks](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1657-L1667)。

## 7. PBD 粒子：phase、邻域和数据协议

[`PxPBDParticleSystem`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L187-L218) 提供位置迭代和速度迭代；源码 [`NpScene::addParticleSystem`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L1699-L1716) 限制 GPU scene。接口概述列举多种粒子用途，但本章只把读到的 granular/fluid buffer、phase 和密度/接触路径作为具体证据，不从概述词汇推断所有布料/充气体对象或功能都已实现、验收。`PxPBDMaterial` 的 [lift/drag 注释](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDMaterial.h#L183-L225) 还明确将 particle-cloth、particle-rigids、attachments、volumes 标为 deprecated；这不能混同本章独立的 FEM surface/volume，也不等于禁用流体粒子与普通刚体的接触。

[`PxParticleBuffer`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleBuffer.h#L30-L111) 与 Scene/particle system 分离，在步间可添加/移除/转移；位置和 inverse mass 是 `PxVec4(x,y,z,1/m)`，速度是 `PxVec4(vx,vy,vz,0)`，phase 为每粒子 `PxU32`。active count 不超过创建时 capacity；`getFlatListStartIndex()` 只有加入 system 且至少 simulate 一次后才有效。buffer 内部设备地址不能直接当 NumPy/CPU 指针，释放会回收其内存。

[`createPhase(material, flags)`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L428-L436) 将材料与 group/behavior 编码结合；[`PxParticlePhaseFlag`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleSystemFlag.h#L41-L56) 区分同组自碰撞、基于 rest pose 的邻近过滤、fluid 密度约束。它不是刚体 `PxFilterData.word0` 的 env_id；同 scene 的多环境粒子隔离不能机械照搬 E5 rigid shape shader。修改位置/速度/phase 后按 [`PxParticleBufferFlag`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxParticleSystemFlag.h#L17-L35) raise dirty flags，并履行复制和同步协议。

五个长度参数要拆开：[rigid/deformable restOffset、contactOffset、particleContactOffset、solidRestOffset](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L324-L389)，以及 [fluidRestOffset](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L525-L531)。粒子–刚体的静止距离涉及两边 restOffset 之和；两 solid 或 solid/fluid 静止间距是 `2 * solidRestOffset`；两 fluid 是 `2 * fluidRestOffset`。particleContactOffset 决定邻域接触尺度，必须大于后两者，不能把它叫作唯一的“粒径”。

密度求解也不是名字相同就等于通用 SPH Navier–Stokes 离散。固定 [`particlesystem.cu`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/particlesystem.cu#L2708-L2763) 在邻域里以内部 kernel/尺度累积 rho，片段里的 `mass` 明确设为 1，再将：

$$
c=\max(\rho-\rho_0,-0.005\rho_0)\,s_\lambda
$$

存入名为 `mDensity` 的工作数组。此式描述**内部归一化/缩放后的约束值**；该数组不是无需转换即可导出的 kg/m³ 测量。后续 [`ps_solveDensityLaunch`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/gpusimulationcontroller/src/CUDA/particlesystem.cu#L2801-L2836) 消费这些工作量，另有 contact、viscosity、surface tension、velocity 路径。PBD 材料接口的[cohesion/viscosity/surface tension 等参数](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDMaterial.h#L115-L226) 必须按实现尺度解释，不能把它们一律当 SI 连续介质系数。

[`PxParticleSystemCallback`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L34-L84) 的 onBegin/onAdvance/onPostSolve 接收 mirrored pointers 与 CUstream；“host/device mirror”只是调用者应该满足的关系，类型本身不保证同步。按所给 stream 排序工作；[`fetchResultsParticleSystem`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1105-L1108) 才是相关 particle data copies 的同步入口，callback 文档也将其作为完成保证。自建其他 stream 的依赖仍由应用承担。callback 不应在 simulation 正在执行时更换，[setter 注释](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxPBDParticleSystem.h#L452-L461) 明确这些调用会被忽略。

## 8. 回调、可微与宿主：能力归属的最后一层

### 8.1 回调阶段不能互换

| 接缝 | 能做什么 | 不应该由它承担什么 |
|---|---|---|
| simulation filter shader / callback | 按 pair/属性筛选及请求 flags，见 E3/E5 | 任意读写正在推进的 scene；假定 query filter 一并生效 |
| custom geometry callbacks | 在 narrow phase/query 定义几何答案 | 修改 Scene 或依赖一份无锁可变全局临时缓存 |
| constraint solver-prep | 由传入数据生成约束行，需可重入 | 直接积分 body、调用控制器副作用或替换后续所有 solver 阶段 |
| contact modify | 改现有接触点属性或 ignore | 添加新 contact 数量、当最终力报告或常规 update loop |
| simulation event / contact report | 取回事件与报告，见 E3/E4 | 把某次 callback 当独立物理步或完整传感器 |
| particle / deformable GPU callback | 在提供的 stream/event 契约上排自定义 GPU 工作 | 宣称 CPU 可直接读 D 指针；把排队完成当执行完成 |

[Contact modify 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h#L415-L450) 要求线程安全/必要时可重入、pair 开 `eMODIFY_CONTACTS`、actor 保持 awake；仅移除 callback 并不能清除 pair flag 对性能路径的影响。普通 modification 与 CCD 的 [独立接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h#L456-L497) 也不可混为一谈。`PxContactSet` 暴露 point/normal/target velocity/impulse cap 等[修改入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h#L42-L202)，这些是模型干预，不是测得同名物理量。

### 8.2 Jacobian、GPU array 和 autograd 是三个概念

E2/E5 的 articulation Jacobian 解决速度映射、惯性矩阵和逆动力学等具体问题；本章的 $\nabla C$ 是内部约束空间导数。二者都不自动构成可训练 rollout 的反向接口。端到端可微仿真需定义：

$$
s_{t+1}=\Phi_h(s_t,a_t,\theta),\qquad
\frac{\partial L}{\partial\theta}\ \text{需要}\ \frac{\partial\Phi_h}{\partial s},\frac{\partial\Phi_h}{\partial a},\frac{\partial\Phi_h}{\partial\theta}
$$

以及接触拓扑变化、clamp/限幅、休眠、迭代截断、缓存历史和非光滑点的导数约定。公开 [`PxArticulationReducedCoordinate`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h)、[`PxDirectGPUAPI`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h) 与本章 constraint/deformable/particle contracts 没有为上述完整 Scene step 提供通用 tape/backward 契约。本章结论限定为**这些已核对的原生接口不能据此宣称端到端 autograd 支持**；不把负面结论扩大成“外部研究或派生实现永远不能求梯度”。

CUDA 内核源码可读、zero-copy/interoperability 或把数组交给 PyTorch/Warp，都不会自动为 PhysX step 注册梯度。若另写有限差分、可微代理或 custom backward，应记录它自己的方程、实现、版本及与原仿真是否等价；当前没有实现或验证这类系统。RL 本身也不要求 simulator 可微，学习任务/奖励/优化器仍是 [E5 的宿主层](batch-learning-data.md) 职责。

### 8.3 多物理“有耦合”不等于“所有物理”

本章有源码证据的 native 能力是刚体/约束、reduced-coordinate articulation、特定 FEM 体/面、PBD 粒子，以及受支持对象间的接触/attachment。它们有不同状态维度、材料 law、buffer 和同步边界，不能把所有物体装进一套 `pose, velocity` 就认为完整。

相机 RGB/depth/segmentation、材质光照、任务 reward、数据集 schema 和 sim-to-real 标定仍需宿主/应用实现；见 [E4](sensors-rendering.md) 与 [E5](batch-learning-data.md)。光学 mesh 变形可消费物理顶点结果，但不是 FEM kernel 自己产生图像。热/电磁/化学或未核实的专用流体模型，应明确标“本课程未找到所需原生接口/未覆盖”，不能用“multiphysics”宣传语补成已验收功能。

## 9. 易错点

- 同一名称对应不同层：`shader`、`density`、`appliedForce`、`lambda`、`substep` 都须沿类型/量纲/调用者解释。
- 复制 `PxCustomGeometry` 不复制 callback 对象；返回有效 geometry 不保证 bounds/contact/query/mass 一致。
- 未计 geometry margin 的 inertia、混用 actor/COM frame、把 body1 Jacobian 重复取负，都会改变约束模型。
- 改数据块不 markDirty，或 callback 内违反阶段改 scene，不能靠提高 solver iterations 修复。
- force limit 与 impulse cap、几何 tolerance 与求解残差、constraint getForce 与 total wrench 不能互换。
- GPU Scene 有 CPU fallback；GPU library 有源码也仍需要外部 CUDA 运行环境。不得手动伪设内部兼容标志。
- deformable collision/simulation vertex 索引可能不同；particle phase 也不是 rigid env_id。
- device pointer/dirty flag/mirrored pointer 都不是已同步 CPU 快照；post-solve event 不自动回收应用异步任务。
- FEM E、关节 k、粒子材料参数和渲染材质不具有统一数值含义；先核量纲、状态和 law。
- Jacobian、梯度形函数和训练可微 rollout 是不同证据；当前源码身份也不能替代历史宿主 binary 身份。

## 10. 阅读练习与参考答案

1. **把临时 CylinderCallbacks 传给 PxCustomGeometry，再复制 geometry 给长期 shape，是否安全？**

   不安全。geometry 复制保留同一个裸 callback 指针；临时对象释放后悬空。需由应用保持回调及依赖数据活着，直到所有使用者结束；之后还要核对并发和缓存更新。

2. **cylinder 高度从 H 变为 2H，只更新碰撞支持点够不够？**

   不够。bounds、query、接触 cache 和质量/COM/惯量需要一致更新；固定密度下质量翻倍，横向惯量含 H² 项，不是简单所有分量乘 2。margin 非零还有另一质量计算路径。

3. **`linear1=-n` 再交给 Px1DConstraint，是否描述两个 attachment 的相对速度？**

   通常不是。原生 J 已含负的 linear1/angular1；本章相对点速需两个 linear 字段都填 n，再各填 r×n。重复取负会变成速度相加。

4. **row 的 maxImpulse=10，hasDriveLimit=true，driveLimitsAreForces=true，simDt=0.002，最终上限是多少？**

   按实际 helper 是 0.02（线性行为 N·s）；缺任一 flag 时为 10 N·s。不能照 `eHAS_DRIVE_LIMIT` 短注释的反向 unless 理解，也不能把 TGS 内部 h 随意替换 simDt。

5. **distance joint 的 tolerance=0.01 意味着残差小于 0.01 就退出 solver 吗？**

   不是。它用于构造几何死区和单边误差；迭代预算另设。还需检查 min/max flags、spring flag 和刚度，默认 joint 不能称为已配置弹簧。

6. **一行没开 eOUTPUT_FORCE，但仍修正了速度。getForce 为零是否说明无约束作用？**

   不能。writeback 只累计带输出标志的行，断裂判断也使用这部分；还需辨清 scene/激活/断裂状态和采样阶段。报告不含所有外力。

7. **custom geometry 在普通 GPU scene 可用，因此也能和 cloth 碰撞、并完全在 GPU 跑？**

   不成立。rigid custom pair 有 CPU fallback，cloth/custom 分支有过滤限制；具体 pair、PCM、contact modification 都影响路径。CPU 虚函数不会自动成为 GPU kernel。

8. **为了 Direct GPU，把 custom constraint 的 eGPU_COMPATIBLE 打开是否够了？**

   不够且公开 setter 禁止。官方 D6 的内建路径和数据格式才有相应支持；DistanceJoint/custom solver-prep 的 CPU 链不能据此迁移。

9. **FEM volume 有 400 个 collision 顶点、120 个 simulation 顶点，复制哪个长度作为完整求解状态？**

   两者分别有自己的缓冲/语义；simulation position/velocity 用 120，collision position/rest 用 400，不能互换。完整恢复还要初态/拓扑/参数/同步，单一位置数组不是完整 checkpoint。

10. **把无量纲 FEM C 的乘子 ell 除以 dt 能直接得力吗？**

    按本章无阻尼 co-rotational 更新，ell 量纲是 ML²，除以 T 不是力。它还需通过梯度/具体离散方程解释，不能仿照刚体冲量读回。

11. **粒子数组叫 mDensity，是否可直接当 kg/m³ 传感器输出？**

    不能。所引 kernel 写入的是截断密度误差乘预计算 scale；局部 mass=1。必须追溯内部归一化、用途和对外 API，名称不足以证明物理单位。

12. **接到 post-solve event，能立即在 CPU 读取 GPU buffer，或让下个 step 自动等自己的 kernel 吗？**

    都不能这样推断。先让用户 stream 等事件，再安排读/拷贝，CPU 等拷贝完成；应用额外写入还须在下次引擎访问前建立依赖。particle callbacks 另有提供 stream 与 fetchResultsParticleSystem 的契约。

13. **Direct GPU Jacobian 可读，是否完成可微仿真？**

    没有。它不提供整步状态/动作/参数的反向传播及非光滑点约定。外部代理/有限差分/custom backward 是另一个实现和验证对象；当前只完成源码课程。

## 11. 本章完成范围与后续入口

B6/B7 已建立扩展协议、CPU DistanceJoint 从配置到输出的完整追踪、公开 GPU 调度/内核地图、FEM/particle 状态与代表性数值路径，以及宿主/可微/多物理边界。此处“源码课完成”不表示逐行证明所有后端或已运行任何示例。新的原生片段只有 syntax/type 检查；公开源码与实际硬件/运行能力分开记录。

E7 仍待完成 **A0 安装专题与双路线整体审校**，包括统一先修、术语、未决项和 DexLab 原批次复用入口；当前不自动开展安装/原生构建。本仓先解释引擎，实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab)，保留原版本、配置与工况，不新增评分器或比较排名。
