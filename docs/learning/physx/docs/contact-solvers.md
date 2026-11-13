# E3：接触、求解器与力观测

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [课程路线](curriculum.md) · [源码地图](source-map.md) · [E3 检查与限制](validation/e3.md)

先修：[E1](modeling-state-time.md) 的 Actor/Shape/COM、惯量和步进边界；[E2](control-robotics.md) 可帮助区分 drive 输入与求解后的接触响应。本章连接 A4 与 B1–B5，并补足 B0 的约束行/求解数据基础。应用读者可先读第 1–3、7–9 节，源码读者按顺序阅读。

**阅读身份**：官方标签 `ovphysx-0.6.3`，提交 `da950a3537927784951853c66618036f332ca0ce`，对应 SDK 头文件 **5.11.0**。这是本文的原生 C++ 源码基线，不能证明历史 Isaac Sim 5.1 / UniSim 1.7.10 内置的 PhysX 二进制、补丁、PGS/TGS、迭代或材料参数。历史批次仍以 [DexLab #126](https://github.com/huangkiki/Dexlab/issues/126) 的实际配置证据为准；绝不把本章默认值回填成历史实测值。新源码出现的 API 也不能直接套给旧宿主。

本章只做源码与公式核对、原创 C++ 片段的语法/类型检查。没有链接或运行 PhysX，没有接触实验、基准或训练，也没有得出引擎排名。后续观测验证与实验复用 [DexLab](https://github.com/huangkiki/Dexlab)。

## 1. 一次 simulate 到底解决什么

接触不是一个选项，而是有顺序的职责链：

| 阶段 | 原生对象与产物 | 不应混淆的概念 |
|---|---|---|
| 几何与过滤 | Shape geometry、局部位姿、材料、filter data；候选 shape pair | 视觉网格与 collision geometry 可以不同；overlap 不等于接触冲量 |
| 碰撞检测 | narrow phase 生成/维护法向、接触点、separation 与 patch | PCM 是接触生成/缓存路径，不是 PGS 的另一种名字 |
| 约束准备 | 材料组合、rest distance、有效质量、恢复/柔顺、摩擦 anchor；solver rows | 同一接触模型可进入不同求解器；恢复系数不是数值容差 |
| 岛与求解 | 相互耦合的刚体、articulation、contact/joint rows；迭代冲量与速度 | `positionIterations` 不是直接调用一遍碰撞检测的次数 |
| 积分与更新 | 位姿、速度、缓存、sleep/CCD/完成任务 | PGS/TGS 是 solver；不能把它们直接当作 Euler/Backward Euler 积分器标签 |
| 读回 | `fetchResults`、接触回调、状态查询 | 一个回调中的 contact impulse 也不是全量六维力传感器 |

从 [`NpScene::simulate`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L2999-L3003) 进入（下列为固定源码入口，而非执行日志）：

1. [`NpScene::simulateOrCollide`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L2886-L2916) 检查阶段与正时间步，向 scene 提交任务。
2. [`Sc::Scene::simulate/collideStep`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScPipeline.cpp#L84-L126) 把碰撞任务接到 advance；[`advanceStep`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScPipeline.cpp#L1371-L1426) 再组织 narrow phase、island、solver、post-solver、after-integration 与可选 CCD/finalization。`setContinuation` 写的是依赖边，阅读时不要把设置顺序当成执行顺序。
3. [`PxsNphaseImplementationContext`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/src/PxsNphaseImplementationContext.cpp#L475-L493) 依 `getPCM()` 分支调用 PCM 或普通 discrete narrow phase。几何 cooking 与 SDF 动态三角网格例外见 E1；并非所有 mesh pair 在所有后端都有同一路径。
4. [`ScScene` 构造分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScScene.cpp#L848-L894) 在 CPU dynamics 下按 `desc.solverType` 建立 `DynamicsContext` 或 `DynamicsTGSContext`；GPU dynamics 另建 context 并传入 solverType。本文跟踪 CPU 实现，不能用这张 CPU 调用图证明 GPU 内核完全相同。
5. [`updateDynamics`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScPipeline.cpp#L2049-L2101) 将 contacts、岛、`dt` 与重力交给选中的 dynamics context。PGS/TGS 的实际迭代与积分见第 5–6 节。
6. [`fetchResults` 的完成与回调处理](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneFetchResults.cpp#L484-L538)承接 E1：提交工作、工作完成、回调送达和应用拿到一致状态是不同时间点。

## 2. 过滤、距离与法向约定

### 2.1 检测、响应、通知分别打开

[`PxPairFlag`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L163-L247) 中，`eCONTACT_DEFAULT = eSOLVE_CONTACT | eDETECT_DISCRETE_CONTACT`，**并不默认要求接触点通知**。要接收普通离散接触，应用的 filter shader/callback 应在保留自己的过滤规则后，给目标 pair 加上 `eNOTIFY_TOUCH_FOUND/PERSISTS/LOST` 和 `eNOTIFY_CONTACT_POINTS`；scene 还要注册 `PxSimulationEventCallback`。`eNOTIFY_CONTACT_POINTS` 单独存在不会凭空产生事件。Trigger 默认只有检测与 found/lost，不施加接触响应。

`eKILL` 与 `eSUPPRESS` 的重新过滤条件不同；[`PxFilterFlag` 定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L260-L298)应与应用 filter data 生命周期一起读。不要把 mask 过滤、joint collision 禁用、trigger、sleep 与“solver 没算出力”合并成一个故障。

Sweep CCD 还需 scene `eENABLE_CCD`、参与动态 body 的 `eENABLE_CCD` 和 pair `eDETECT_CCD_CONTACT`；`eNOTIFY_TOUCH_CCD` 才报告相应 CCD passes。[CCD 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L100-L117)、[三层开关](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L181-L194)。这与 TGS 的内部时间小步不是同一机制，也不能由更大 contactOffset 替代。

### 2.2 contactOffset 不是刚度，restOffset 不是容差

令几何表面 separation 为 $s$，单位长度；负值表示穿透。令两 shape 的 restOffset 总和为 $r$，contactOffset 总和为 $c$。生成接触的距离范围由 $c$ 控制，期望静止距离由 $r$ 控制，求解准备使用的间隙是：

$$
g=s-r.
$$

每个 shape 的 contactOffset 应为正且大于其 restOffset。默认 contactOffset 为 `0.02 * scale.length`，restOffset 为 0；这是当前 SDK 的尺度约定，不是所有模型都应使用的米制调参建议。[Shape 接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L351-L394)、[实际 separation−restDistance](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h#L311-L328)。增加接触生成距离不等于改变 penalty stiffness，也不能证明更准确。

[`PxContactPairPoint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L436-L466) 的 normal 从 **shape 1 指向 shape 0**，position/normal/impulse 均在 world；separation 是几何距离。求合力前固定 actor/shape 身份和取力对象，不按“机器人总在 pair[0]”猜符号。`eINTERNAL_CONTACTS_ARE_FLIPPED` 在 extraction 中用于 face index 交换，不应由应用再次无条件翻转 normal；看[实际提取实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L629-L678)。

### 2.3 影响接触响应的不同旋钮

| 字段 | 单位与对象 | 真实含义 |
|---|---|---|
| static/dynamic friction | 无量纲，Material | 摩擦上限参数，经 pair combine 后进入 patch；不是速度阻尼 |
| restitution ≥ 0 | 无量纲，Material | 恢复速度目标；低于 bounce threshold 时不反弹 |
| restitution < 0、damping | 力型分别质量/时间²、质量/时间；Material | 本版重载为隐式柔顺弹簧刚度的负值与阻尼；acceleration spring 改为 1/时间²、1/时间 |
| bounceThresholdVelocity | 长度/时间，Scene | 抑制小碰撞反弹；默认 `0.2*scale.speed`，不是位置误差阈值 |
| frictionOffsetThreshold | 长度，Scene | 分离较大的点不产生摩擦的距离条件 |
| frictionCorrelationDistance | 长度，Scene | friction anchor 的空间相关/合并距离 |
| maxDepenetrationVelocity | 长度/时间，RigidBody | 接触纠正穿透的速度限额，不能当作 force limit |
| maxContactImpulse | 质量·长度/时间，RigidBody | 每个 contact 的冲量上限；动态/运动学 pair 取两侧较小值，静态 pair 用动态侧值；不是全物体总力或驱动上限 |

来源：[Material](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxMaterial.h#L124-L205)、[Scene 距离与速度阈值](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L721-L761)、[Body 两种限额](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L694-L730)。这里的量纲以一致的质量/长度/时间单位制为前提；`PxTolerancesScale` 不会自动把输入毫米变米。接触修改器还能改 normal、target velocity、max impulse、inv mass/inertia scale；这些是动力学改动，不能在“观测函数”里悄悄启用。[修改接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h#L95-L174)、[线程契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxContactModifyCallback.h#L407-L450)。

## 3. 材料不是取任意一面的系数

### 3.1 刚性 pair 的组合规则

两边分别声明 combine mode，但 pair 采用的是 **枚举值较大的 mode**：AVERAGE=0、MIN=1、MULTIPLY=2、MAX=3。先选规则，再算系数。它不表示总是选择较大的材料系数。[枚举定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxMaterial.h#L75-L110)、[实际 combiner](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/include/PxsMaterialCombiner.h#L13-L112)。

| mode | 标量组合 $C(a,b)$ | 阅读例：$a=0.2,b=0.8$ |
|---|---|---|
| AVERAGE | $(a+b)/2$ | 0.5 |
| MIN | $\min(a,b)$ | 0.2 |
| MULTIPLY | $ab$ | 0.16 |
| MAX | $\max(a,b)$ | 0.8 |

例：一边 MIN、另一边 MULTIPLY，实际用 MULTIPLY，得到 0.16。静/动摩擦分别组合，然后实现约束 `muDynamic=max(combinedDynamic,0)`、`muStatic=max(combinedStatic,muDynamic)`。任一材料 `eDISABLE_FRICTION` 会使 pair 静/动摩擦都为 0，并禁用 strong friction。系数不限定必须 ≤1。[组合后的钳制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/include/PxsMaterialCombiner.h#L86-L117)。

这是一套 SDK 规则，不是由各材料单独的“物理摩擦系数”推导出真实表面配对摩擦的普适定律。mesh face material 的身份来自 Shape/face index，见 [E1](modeling-state-time.md) 和 [`getMaterialFromInternalFaceIndex`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L333-L349)。

### 3.2 负 restitution 的特殊分支

本版 `restitution < 0` 表示柔顺接触刚度 $k=-e>0$；damping 为 $d\ge0$。这是接触模型的选择，不是“负反弹系数”。实现具体顺序：

- 仅一侧柔顺时，restitution 强制用 MIN，从而保留负值，不服从用户的普通 combine mode。
- 两侧柔顺且一侧 force spring、另一侧 acceleration spring 时，后者的 restitution 和 damping 优先。
- 两侧柔顺用 MULTIPLY 时，结果额外取负，避免两个负数相乘意外回到刚性分支。
- **damping 的注释/实现差异**：头文件概述说刚柔混合取柔顺侧 damping；实际 [`PxsCombineMaterials`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowlevel/software/include/PxsMaterialCombiner.h#L35-L83) 在恰有一侧柔顺时使用 `max(d0,d1)`。若刚性侧保存了更大的 damping（即使它单独作为刚性材质时该值不起作用），不能按概述断言它会被忽略。本文记录实现，不用未运行的例子宣称测得缺陷。

力型的一维、固定有效质量说明模型可写成：

$$
f_n=-k g-d v_n,\qquad
v_n^+=v_n^-+w p_n,\qquad p_n=h f_n^+.
$$

这里 $v_n<0$ 为接近，$p_n$ 为法向冲量，$w=1/m_{eff}$；在把 $g^+=g+h v_n^+$ 代入的隐式离散里，出现分母 $1+h(d+hk)w$。若输出按 acceleration 解释，$k,d$ 单位改为 $s^{-2},s^{-1}$，分母为 $1+h(d+hk)$，随后用有效质量转换成冲量。此推导帮助读懂系数，假定无摩擦/恢复/其他约束、单一有效质量，并非完整 PhysX 算法。

实际 [`computeCompliantContactCoefficients` 与 TGS 版本](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h#L214-L269)明确构造 `a=h*(d+h*k)`，force/acceleration 使用不同 response；当分离且本步不预计闭合时抑制 damping。最终还受实际累计冲量更新、impulse cap、offset、solver 耦合与迭代影响。因此不能把“隐式弹簧”扩写成“整个 PhysX 一律 Backward Euler penalty 接触”。

## 4. 从接触点到约束行

### 4.1 一个可手算的法向行

先假定两个普通刚体、单位法向 $n$、世界 COM 惯量 $I_i$、无质量缩放/锁轴/gyro/柔顺，$r_i=x_c-x_{COM,i}$。法向相对速度与 unit response 为：

$$
v_n=n^T(v_0+\omega_0\times r_0-v_1-\omega_1\times r_1),
$$

$$
w=\frac1{m_0}+\frac1{m_1}
 +(r_0\times n)^T I_0^{-1}(r_0\times n)
 +(r_1\times n)^T I_1^{-1}(r_1\times n).
$$

$w$ 的单位是质量的倒数，法向冲量增量 $\Delta p_n$ 的单位是质量·长度/时间。速度响应为 $\Delta v=M^{-1}J_n^T\Delta p_n$。无限质量/运动学物体在相应响应项中贡献零，运动学目标速度仍影响相对速度。实际刚体准备使用逆惯量平方根、dominance/mass scale 和 offset slop，见 [`constructContactConstraint`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h#L275-L367)。

固定本行几何与其他行当前结果，理想刚性单边条件可写为 $p_n\ge0$、$v_n^+-v_{target}\ge0$、$p_n(v_n^+-v_{target})=0$。一种说明性的投影更新为：

$$
p_n^{new}=\operatorname{clip}\left(p_n^{old}+\frac{v_{target}-v_n}{w},\,0,\,p_{max}\right).
$$

若设置有限 $p_{max}$，即使已到上限，非穿透条件仍可能不满足；不能仍宣称解满足未限幅的互补条件。`v_target` 还会包含恢复目标、接触 target velocity 与位置纠正，真实分支见下节。公式中的 $w=0$ 不能直接相除；源码显式处理 response 非正情况。

**Articulation 不可用“两块独立 link 刚体”公式代替。** link 接触冲量通过 articulation 的树响应计算；不能只读该 link 的质量和惯量。实际 PGS [`getImpulseResponse_`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp#L153-L181)分别调用参与 link 的 `getImpulseResponse` 并组合响应，随后用 `1/(unitResponse+cfm)` 准备行。[法向准备](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp#L235-L299)。

同一 articulation 两个 link 在理论上有交叉响应，但必须追到当前调用路径，不能仅见函数名就宣称已完整计入：该文件另一个 scalar helper 的 self-response 分支被 `allowSelfCollision=false` 和 `&&0` 禁用；上述 SIMD helper 没走它。[禁用分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp#L105-L147)。TGS 虽有 scalar self-response 分支，其 SIMD overload 忽略该 bool，已查的 contact prep 调用传入 false。[TGS overload](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L270-L331)、[contact 调用](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L871-L887)。这是具体 response 近似路径的边界，不据此否定所有 articulation 自碰撞，也不把理论全耦合矩阵冒充此实现。

这里的 CFM 是对 response 的正则化，不是 contactOffset、时间步或收敛 tolerance。原生 `PxArticulationLink::setCfmScale` 默认 0.025、范围 0–1；源码先按场景长度尺度赋值，再乘 link 的测试冲量响应比例，接触准备取双方的较大 CFM。它随模型响应缩放，不能把公开 scale 数字直接当成接触弹簧的 N/m。[公开入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationLink.h#L110-L135)、[初始缩放](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp#L3699-L3709)、[响应缩放](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneForwardDynamic.cpp#L843-L854)、[其余 link 缩放](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneForwardDynamic.cpp#L895-L904)、[pair CFM](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyArticulationContactPrep.cpp#L372-L378)。增加正则化改变响应及约束误差，不能称为“同一物理问题只算得更快”。

### 4.2 恢复、偏置和实际数据布局

准备代码先算 $g=s-r$ 与接近速度；只有恢复系数为正、接近速度超过 bounce threshold 且预计本步闭合时才添加 $-e v_n^-$ 恢复目标。内部传入的 bounce threshold 带其约定符号；公开 API 是正速度大小。穿透位置误差经 $1/h$ 与 bias coefficient 转为速度纠正，再受 max depenetration bias 限制。[刚性/柔顺分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h#L316-L359)。

PGS 的每个 contact block 不是一个密集全局矩阵：header 包含法向、质量/摩擦等共享量；接着是各法向行、对齐的累计法向冲量数组、friction rows。每行携带 $r\times n$ 经逆惯量平方根变换后的量、velocity multiplier、biased/unbiased error 和 max impulse。读取与写回布局见 [`solveContact`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L188-L230)；准备时[法向冲量清零](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrep.cpp#L150-L181)。虽然局部变量叫 `forceBuffer/appliedForce`，其数值是 **impulse**，不可直接标 N。

多约束写成 $A=JM^{-1}J^T$ 可以帮助理解行耦合与病态质量比；此处不是说 CPU contact solver 显式组装并 Cholesky 分解完整 $A$。PGS 用各行 response 的倒数与即时速度更新处理耦合；articulation response 由树动力学计算。小 response、长链、几乎冗余约束、质量/惯量尺度差与 finite precision 都可能影响有限迭代的误差。

### 4.3 Patch friction、strong friction 与 warm start

本固定版本 [`PxFrictionType`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L28-L52) **只剩 ePATCH**，frictionType 已 deprecated；不要抄旧教程列举 one-directional/two-directional 选项让读者配置不存在的枚举。一个 patch 最多选择两个 friction anchors，每个 anchor 有两个切向约束。接触点数、patch 数、anchor 数不是同一量。

理想各向同性 Coulomb 写为 $\|p_t\|_2\le\mu p_n$；这只是参照模型。PGS 实现按切向行分别检查静摩擦界、越界后投影到动摩擦范围；TGS 把一个 anchor 两个方向的累计冲量合成长度后钳制，减小方向分开处理的非对称性。法向容量来自 patch 的 accumulated normal impulse，并含 anchor 缩放，不能给每个 contact point 都复制一份完整摩擦圆。[PGS 行钳制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L230-L306)、[TGS 成对切向计算](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1646-L1772)。

Strong friction 保留跨步的 friction error/anchor 相关性；它不等于无限静摩擦。`eDISABLE_STRONG_FRICTION` 去掉这种跨步记忆，但不自动令摩擦系数归零。[材料说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxMaterial.h#L27-L61)、[上一帧 patch 相关性读取](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrepShared.h#L51-L101)。设置接触 target velocity 的准备路径还会禁用 strong friction，[TGS extract 路径](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1474-L1499)。

“有缓存”不能推导成“把上帧所有法向/切向 lambda 原值 warm start”。已跟踪的 CPU PGS 法向 buffer 在准备时清零，TGS 切向 row 的 `appliedForce` 也初始化为零；接触流/PCM、anchor 记忆、单次 solve 内累计冲量是三个层次。[TGS 初始化](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L752-L795)。本文不由这几处推出所有 joint/GPU 路径均没有 warm start。

TGS 某些单 anchor 情况还可用 torsional patch radius 构造绕法向的纯角向摩擦行；它近似压缩表面的转动摩擦。[Shape 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L429-L471)、[TGS 半径和行准备](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L800-L833)。这会影响第 7 节“仅由点力重建 wrench”的完整性。

## 5. PGS 与 TGS 的迭代、终止与误差

### 5.1 PGS：带投影的顺序冲量更新

[`solveDynamicContacts`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraintsShared.h#L26-L78)从当前 body velocity 得到本行误差，使用已准备的 multiplier 算冲量增量，限制累计冲量，再立即更新两 body 的线/角速度供后续行使用。柔顺分支还有 impulse multiplier，所以第 4 节的简单刚性投影式不能覆盖所有行。

[`solveV_Blocks`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverControl.cpp#L191-L283)执行 position iterations，最后一遍做 conclude，然后保存 motion velocities，再做 velocity iterations 和 writeback。这里的“position”主要指包含位置纠正 bias 的速度约束阶段，不是每轮直接调用 `setGlobalPose`。[conclude 的实际写入](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L478-L498)将相应行切换到 unbiased 项，降低纠正穿透造成的最终离开速度；摩擦默认只在最后三次 position iterations 及全部 velocity iterations 执行。Scene flag `eENABLE_FRICTION_EVERY_ITERATION` 可改变前者。[Scene flag](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L245-L259)。

**零 velocity iteration 的细节**：公开 setter 允许 `minVelocityIters=0`；但这个有接触约束的 CPU PGS 路径会至少执行一次 velocity/writeback，平行路径亦如此。不能根据用户填写 0 就标“实际完全不做 velocity pass”。[串行保障](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverControl.cpp#L244-L283)、[平行保障](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverControl.cpp#L662-L715)。无约束路径单独处理，不把该结论扩到所有分支。

### 5.2 TGS：位置迭代推进内部时间

TGS 收集岛中 body 的位置/速度迭代需求上界，也纳入 articulation；[`SetStepperTask`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L1624-L1630)明确令：

$$
h_{internal}=h/N_{position}.
$$

body count 汇聚见[preIntegrateBodies](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L746-L773)，articulation 汇聚见[setupArticulations](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L1421-L1453)。因此提高岛内一件物体的 iteration 请求可能影响整岛，而非只让该物体独立算更多次。

每轮位置迭代求解后调用 `integrateBodies/stepArticulations`，累计 `elapsedTime`。后续 constraint evaluation 使用自准备以来的线/角位移，更新原始 separation/bias 与 target motion；无需把它描述成每个内部小步都重新跑一次完整 narrow phase。最后 velocity iterations 不再推进位姿，之后独立 writeback。[实际循环](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L2386-L2460)、[动态 separation 与冲量钳制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1509-L1581)。

TGS 对每个 position/velocity iteration 都处理摩擦，与 PGS 默认不同。这些差异意味着“PGS 4 次 = TGS 4 次 = 另一个引擎 4 次”没有成立的数值依据。

### 5.3 终止不是 tol=某个数字

`PxRigidDynamic::setSolverIterationCounts` 的当前默认是 4 position、1 velocity，范围分别 1–255、0–255；articulation 有自己的同名设置。[公开契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidDynamic.h#L368-L394)。上面已追踪的 contact loops 按预算计数结束，**不是以用户输入的绝对/相对 residual tolerance 作为提前退出条件**。不应为表格整齐而替 PhysX 填一个 `1e-9`。

可以在纸上定义互补/速度残差或沿当前数据做诊断，但残差量纲、归一化、接触状态、bias 与 friction projection 都必须先固定。没有实际实现与导出，就不要宣称某个“误差值”是 SDK 原生报告。更高 iteration budget 不是更高浮点精度；这里的 `PxReal` 仍是 float。有限迭代也不是精确满足刚性约束的保证。PGS/TGS 的迭代顺序和离散化会影响误差，文档不据理论期望宣布某个模型已稳定。

## 6. 积分、外力与三种“子步”

PGS 普通刚体的 unconstrained velocity 先计入重力，乘 `max(1-damping*h,0)`，再做速度上限处理。[bodyCoreComputeUnconstrainedVelocity](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyBodyCoreIntegrator.h#L18-L62)。接触求解后，位置按保存的 motion velocity 推进；最终存储 velocity 还会计入 velocity iterations 的更新，两者不能总写成同一个 $v_{k+1}$。旋转使用常角速度段的闭式 quaternion 更新并归一化。[integrateCore](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyBodyCoreIntegrator.h#L102-L153)。

只在无接触、无阻尼、无 gyro、恒外加速度的简化情况下，可用 semi-implicit 关系解释平移：

$$
v_{k+1}=v_k+h a,\qquad x_{k+1}=x_k+h v_{k+1}.
$$

对 world angular velocity 为常量的一小段，姿态更新为 $q^+=\Delta q\otimes q$，其中 $\Delta q=(\hat\omega\sin(\|\omega\|h/2),\cos(\|\omega\|h/2))$，零角速度取恒等。不能把四元数四个分量分别当独立角坐标积分；实际限制、inertia transform 和 articulation 路径仍需按源码区分。

TGS 的 [`integrateCoreStep`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L1153-L1222)每内部小步推进 position/quaternion 并累积 delta motion。外力默认在一次 `simulate(h)` 开头施加；`eENABLE_EXTERNAL_FORCES_EVERY_ITERATION_TGS` 则按内部小步分配。这个开关会改变自由落体的位移，且岛的 iteration 数影响结果。[公开说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L262-L275)。

一个不运行引擎即可推导的例子：初速度为零、恒加速度 $a$、无阻尼/接触。整步预施加外力后以 $ah$ 运动，位移是 $ah^2$；若 $N$ 次先加速再积分，则

$$
\Delta x=a(h/N)^2\sum_{j=1}^{N}j
=\frac{N+1}{2N}ah^2.
$$

[无约束分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L2379-L2383)与[先外力后积分循环](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSDynamics.cpp#L1277-L1286)支撑上述简化。它说明为什么换开关/岛迭代数会换离散结果；不是自由落体实验结果，也不覆盖约束或非恒力。

| 名称 | 会重新进入什么 | 读回与控制边界 |
|---|---|---|
| 应用外层小步 | 调用多次 `simulate(h_s)/fetchResults` | 每次可重新提交控制、重新碰撞检测、读回；普通外力需要按 E2 的累加/清理规则重新提供 |
| TGS 内部位置小步 | 同一 solve 的约束更新和积分 | 不是独立 public step，没有每小步自动执行应用控制器或重新发布传感器帧 |
| CCD passes | 同一 public step 的连续碰撞处理 | 可能额外产生接触通知；不等于 TGS 迭代数，也不保证普通离散报告已涵盖所有碰撞 |

单位尺度、dt、iteration count、位置 bias、柔顺参数和接触几何必须一同记录。把步长减半也会改变每步 impulse cap 所对应的平均力上限。GPU 与宿主的同步/批量机制留待 E5/E6；本文没有证明对接触切换、投影或缓存路径存在可用梯度，PGS/TGS 名称本身不代表可微。

## 7. 从 solver impulse 到可解释的观测

### 7.1 法向、切向和纯力矩分开看

PGS [`writeBackContact`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DySolverConstraints.cpp#L504-L556)把累计 normal impulse 写入 contact force buffer；TGS 也有[对应 writeback](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1860-L1909)。对应用而言，本版至少要分清：

| 数据 | 来源 | 能说明什么 |
|---|---|---|
| `PxContactPairPoint.impulse` | `extractContacts()` | 实现为 `normal * scalarImpulse`，**只有法向冲量**；未提供 impulse 时 extractor 写零，不能据零认定测得零力 |
| `PxContactPairFrictionAnchor.impulse` | `extractFrictionAnchors()` | world 切向冲量，位置是 friction anchor；它不是与 contact point 数组一一对应的另一列 |
| contact force threshold event | pair 通知/Body threshold | 事件筛选机制，不是完整 wrench 数值或驱动饱和证据 |
| `PxConstraint::getForce(linear,angular)` | 普通 joint 的 underlying constraint | 最近维持该约束的力/力矩，不是碰撞点列表，也不等于 articulation cache 输入 jointForce |

[公开字段与 extraction](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L436-L481)、[法向提取](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L629-L678)、[anchor 提取](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L681-L706)、[constraint 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxConstraint.h#L144-L153)。D6 drive 默认不把 drive 力加进 `getForce` 总量；`PxD6JointDriveFlag::eOUTPUT_FORCE` 会改变报告总量，连带影响 break 判断。[D6 flag](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxD6Joint.h#L157-L176)。

**完整性限制需要保留在数据里。** normal stream 存在、has impulses、friction stream 存在、实际提取条数、事件类型/步编号，应分别记录。CCD 通知路径将 `frictionPatches=NULL`，[ScShapeInteraction 分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScShapeInteraction.cpp#L430-L481)；因此 CCD 报告没有 anchor 不证明摩擦为零。Lost/sleep/过滤不报告也不能补成“本步真实零接触力”。删除 actor/shape 的标志需要单独处理，不能在回调中解引用已经移除的对象。

本版 [`writeBackContactFriction`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyContactPrep.cpp#L677-L698)只合并成对的切向行；在三行的“一个 anchor 加 twist”情况下，不把额外纯 torsional row 写成 anchor 的点冲量。**所以即使法向点与切向 anchor 都收集了，用 $r\times p$ 得到的也只是已报告点冲量的力矩，不能无条件宣称完整 contact wrench。** GPU、宿主传感器的聚合与遗漏需另行核实，不能从 CPU 接口存在推断运行覆盖。

### 7.2 平均力、坐标与采样

对一个明确的 public step，长度为 $h>0$，把法向点冲量 $p_i$、可用切向 anchor 冲量 $t_j$ 都按同一作用对象和 world 方向整理。所报告线冲量与关于 world 参考点 $o$ 的点冲量矩为：

$$
P_{reported}=\sum_i p_i+\sum_j t_j,\qquad
L_{reported,o}=\sum_i(x_i-o)\times p_i+\sum_j(a_j-o)\times t_j.
$$

$$
\bar F_{reported}=P_{reported}/h,\qquad
\bar\tau_{reported,o}=L_{reported,o}/h.
$$

这是时间区间平均量，不是碰撞瞬时峰值；单位分别为质量·长度/时间²与质量·长度²/时间²。若观测覆盖 $K$ 个 public steps，应先汇总各步冲量，再除以覆盖时间 $\sum h_k$；不能重复累计同一报告，不能按渲染帧时长或 TGS 内部 $h/N$ 误除整个 public-step 冲量。CCD 多次碰撞还需依据事件/额外数据分清同一步的多个贡献；本章片段不承诺完成 CCD 聚合。

若传感器 frame 的 world 姿态为 $R_{WS}$、原点为 $o_S$，先在 world 对 $o_S$ 求矩，再令 $F_S=R_{WS}^T F_W$、$\tau_S=R_{WS}^T\tau_{W,o_S}$。只旋转 torque 却不平移参考点会漏掉杠杆项。若要 articulation generalized contact effort，还需在正确 COM/tool frame 及 DOF 顺序下使用 $J^T$；不能把三维 world 接触力直接填入 `cache.jointForce`。该 cache 字段是 E2 的输入契约，而非传感器读数。

接触事件用当前 step 的显式编号与配置快照绑定，回调复制数据后在合适的 `fetchResults` 边界消费。`onContactModify` 是求解前的响应修改，`onContact` 是通知；不要互换。[回调写入与线程限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSimulationEventCallback.h#L806-L823)。质量缩放、dominance、impulse cap、D6 输出 flag 和纯角向摩擦均可能改变解释；这些元数据比笼统列名“force”更重要。

## 8. 原生 C++ 阅读片段

[`examples/e3_contact_readback.cpp`](../examples/e3_contact_readback.cpp)只定义 pair flags 和复制报告的函数，没有 `main`，不初始化、链接或运行引擎。调用方在自己的合法 filter 和 `onContact` 中使用，负责稳定 actor/shape 身份、回调同步、生命周期与整数 step 编号。示例刻意分别保存 normal points 与 friction anchors，保留“stream/impulse 是否可用”，不把缺失项伪造成零测量。

匹配头文件的 `-fsyntax-only` 能检查当前 API 名称、字段与类型；它不验证回调是否发生、方向是否与宿主包装一致、冲量是否完整、实际力学或性能。详细结果见 [E3 验收记录](validation/e3.md)。

## 9. 易错点与排查顺序

1. **有可视化重叠，没有报告**：依次核对 collision geometry、shape flags、pair 过滤、detect/solve/notify 三类开关、scene callback、sleep 与 removed 标志，最后才追 solver；不能先把“0”解释成真实力。
2. **改 friction 不影响现象**：先查 pair combine 规则、另一材料的 disable flag、static 被抬升到 dynamic、anchor/距离条件、是否走到实际宿主内核。当前源码不替历史配置背书。
3. **改迭代数位置也变了**：TGS 的 $h/N$ 和外力分配、本岛最大请求、位置 bias/积分都可能参与；不是单独“收敛更好了”的证明。
4. **感觉有力，但 contactPoints 只有 normal**：本版 extraction 确实这样做；另看 anchors，并记录 CCD/纯 torsion 缺项。不要靠范数从法向重建切向。
5. **把 drive 上限当抓持力上限**：drive effort、joint constraint reaction、接触冲量以及力矩是不同量；不能只靠 `maxForce` 推出接触 $F_n$。
6. **换 h 后报告 force 变了**：先核对除数/重复聚合/采样区间，再核 impulse cap、离散恢复/柔顺和迭代；没有固定条件不能作引擎差异结论。
7. **宣称数值稳定或可微**：源码分支与片段语法只说明算法和接口；复杂接触的运行稳定性、重复性、梯度与准确度均未验收。

## 10. 阅读练习与答案

**题 1**：A 的 friction mode=MIN、B=MULTIPLY，系数 0.2/0.8；为什么 pair 不是 0.2？

**答案**：先按枚举最大值选 MULTIPLY，再相乘得 0.16。若 static 组合小于 dynamic，还会被抬到 dynamic；只看单侧数字不够。

**题 2**：刚性材质 `restitution=0,damping=10` 与柔顺材质 `restitution=-100,damping=2` 接触，是否能根据头文件概述说 damping 一定为 2？

**答案**：不能。当前 combiner 在恰一侧柔顺时 restitution 用 MIN 得 −100，damping 用 MAX 得 10。这里是代码阅读结论，没有运行证明或更改官方 SDK。

**题 3**：两普通刚体质量均为 2，法向穿过 COM，无其他响应因素。$w$ 和让 $v_n=-1$ 变为 0 所需的理想冲量是多少？

**答案**：$w=1/2+1/2=1$（质量单位的倒数），$p_n=(0-(-1))/w=1$（质量·长度/时间）。若换成 articulation links，不能继续套独立 body 公式。

**题 4**：TGS `simulate(0.01)`，岛请求 5 次 position iteration。内部步是多少？是否等价于应用调用 5 次 `simulate(0.002)`？

**答案**：内部 $h_s=0.002$；不等价。外层重新碰撞检测、控制/force 提交、回调与缓存边界不同，内部使用累计 delta motion 更新准备好的约束。

**题 5**：公开 API 允许 PGS velocity count=0，为何仍能在源码看到一遍 velocity solve？

**答案**：有约束的 CPU PGS 路径为 writeback 保证至少一遍；应读实际循环，不只转录 setter 范围。这不是所有后端/无约束路径的统一承诺。

**题 6**：法向报告冲量为 $(0,0.02,0)$，public step $h=0.001$，能否写“瞬时总接触力 20 N”？

**答案**：在米/千克/秒制下，只能得到这段时间的已报告平均法向力 $(0,20,0)$ N；切向 anchor、纯 torsional row、缺失报告与事件聚合仍需核对，且不是瞬时峰值。

**题 7**：报告一个法向点和一个切向 anchor 后，$\sum r\times p/h$ 是否必然等于真实完整 contact torque？

**答案**：不必然。参考点/坐标/作用对象先要一致；当前 friction writeback 没把额外纯 twist row 放入 anchor 点冲量，CCD friction stream 还可能缺失。结果只能按数据覆盖称“reported point-impulse moment”。

**题 8**：PCM、strong friction、累计 lambda 都保留一些信息，是否意味着同一种 warm start？

**答案**：不是。PCM 属接触生成缓存，strong friction 保留 anchor/friction error，累计 lambda 用于本次 solve 的投影更新。已查的法向 buffer/部分切向 row 在准备阶段清零；不能由缓存存在推断上帧全部冲量被重用。

**题 9**：能否将 SDK 当前默认 PGS/4+1/patch friction 写入 DexLab 历史 Isaac Sim 5.1 那一行？

**答案**：不能。必须找历史原生 PhysX binary/补丁、宿主转换与 scene/body/material 实际配置；本源树只证明本章阅读基线。#126 未核实部分继续保持未知。

## 后续边界

E3 交付的是原生接触、CPU PGS/TGS、积分与观测的源码课程。运行态通知完整性、宿主版本/传感器映射、GPU 内核逐路径一致性、各种几何组合和硬件稳定性未验收。E4 继续传感器/渲染，E5 处理学习/数据，E6 展开后端与扩展特色，E7 再把完整课程与 DexLab 的已有实验索引连接起来。没有新增独立评分器或声称这些后续专题已完成。
