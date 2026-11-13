# E3 · 接触几何、材料与物理模型

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · 先修 [E1 模型与坐标](modeling-state-time.md)、[E2 控制](control-robotics.md) · 后续 [离散求解](contact-solvers.md)、[力观测](contact-observation.md)

本专题使用 Drake **1.57.0** 官方固定提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，覆盖 A4、B1–B5，并补齐 B0 的动力学装配基础。本文先回答“两个几何为何产生什么接触”，再由下一篇解释如何求解。全部是源码教学与静态核验；没有安装/导入引擎、执行接触、积分或数值求解。[验证记录](evidence/e3-validation.md)

## 1. 几何查询、接触模型和 solver 是三个选择

| 层次 | 原生对象/入口 | 决定什么 |
|---|---|---|
| 几何与候选对 | `SceneGraph`、proximity role、`CollisionFilterManager` | 哪些形状参与查询，哪些对被排除 |
| 几何接触表示 | `ContactModel.kPoint / kHydroelastic / kHydroelasticWithFallback` | 单点穿透或带压力场的面片 |
| 离散接触近似 | `DiscreteContactApproximation.kSap / kSimilar / kLagged` | 柔顺、耗散和摩擦的离散方程 |
| 优化算法 | 当前 `DiscreteContactSolver.kSap` | 对所装配的凸问题执行 Newton/线搜索 |
| 时间推进 | `MultibodyPlant(time_step)`、连续系统的 `Simulator` 积分器 | 离散更新周期，或连续微分方程的积分 |

**当前三种离散近似均进入 SAP solver；`kSap` 近似不等于 SAP 算法的所有用法。** 默认几何接触模型是 hydroelastic with fallback，默认离散近似是 Lagged。TAMSI 在本固定版本的 solver 枚举及实际 getter 中已无入口；不能把历史教程的 `kTamsi` 或论文引用当成 1.57.0 配置。这里不拼接旧版 TAMSI 方程来伪造当前分支。[枚举](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L145-L246)、[实际 getter 与 setter](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L870-L892)、[固定默认值](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L6948-L6952)

`AddMultibodyPlantSceneGraph` 将 Plant 的 geometry poses 输出送到 SceneGraph，把后者 query 输出接回 Plant。必须在 Finalize 前注册几何；只创建一个与注册时不同的 SceneGraph 或孤立 Plant Context，不能得到正确查询环境。读取运行中的材料，应通过该 Plant 子 Context 的 `EvalSceneGraphInspector(context)`；`scene_graph.model_inspector()` 反映模型默认值，不会自动反映另一个 Context 的修改。[注册和连接合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L737-L764)、[Context inspector](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L2729-L2735)

### 1.1 看得见与碰得着

visual/illustration、perception、proximity 是不同 role。`RegisterCollisionGeometry` 添加 proximity geometry，并要求材料中含 `coulomb_friction`；视觉网格并不会自动成为碰撞网格。保存返回的 `GeometryId`，不要用名字猜几何身份；一个 body 可有多个碰撞几何，一个接触 surface 也不等于一个 body。[碰撞注册](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L2574-L2648)

候选对过滤先于接触求解。SceneGraph 固有排除包括自身、两个 anchored 几何、同 frame 的刚性几何；这些不能用 AllowBetween 恢复。Plant 在 Finalize 时还按拓扑施加相邻刚体等过滤。额外排除用原生 `CollisionFilterDeclaration().ExcludeBetween(GeometrySet(...), GeometrySet(...))` 等 API，分别通过模型或 Context 的 manager 应用。[固有过滤和生命周期](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/collision_filter_manager.h#L24-L102)、[Plant Finalize 工作](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L924-L943)、[原生过滤示例](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L2661-L2682)

过滤应用时只包含**当时已注册并具有 proximity role** 的几何，之后新增几何不会自动继承这次声明；模型上的修改也不会追溯改变已经创建的 Context。调试“没有接触”应依次核对 role、active/filtered 状态、注册对象和实际姿态，再核对接触模型，而不是直接加大刚度。

## 2. Point 与 hydroelastic：被离散的物理对象不同

### 2.1 Point：穿透深度、见证点和作用点

`PenetrationAsPointPair` 给 `id_A/id_B`、两个 world 见证点 `p_WCa/p_WCb`、指向 **B→A** 的 `nhat_BA_W` 和正穿透深度 x。它们满足 `x=(p_WCb−p_WCa)·nhat_BA_W`。深度是几何查询结果，不是广义位置，也不等于两个 body 原点的距离。[字段与符号](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_results/penetration_as_point_pair.h#L11-L48)

令法向分离速度 vn>0 表示远离，ẋ=−vn。连续 point 的法向力幅值为

$$f_n=k[x]_+[1-dv_n]_+,\qquad [a]_+=\max(0,a).$$

k 单位 N/m，d 单位 s/m，fn 单位 N；这是线性柔顺乘 Hunt–Crossley 耗散，不是 N·s/m 的线性阻尼常数，也不是直接设置 restitution。减小 d 往往减小耗散，但恢复速度还受质量、刚度、入射速度、摩擦及离散方式影响，不能跨引擎一比一替换“恢复系数”。[方程与参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h#L230-L258)

连续 point 路径使用两个见证点的中点作为作用点。离散路径会按双方刚度确定作用点，必须从结果读出 `contact_point()`；不要在后处理重新取一个“更好看”的中点并沿用旧力矩。单个最深穿透点无法完整表达平面接触的压力分布，特征切换也可能造成作用点跳变。[连续作用点](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L2417-L2435)、[离散接触点装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L671-L711)

### 2.2 Hydroelastic：刚体运动上的压力场接触

compliant hydroelastic 几何带体积压力场，表面为零压力、内部按 extent field 和 hydroelastic modulus E 增长；两个物体以相等压力的接触面连接。rigid hydroelastic 提供不随压力变形的接触边界。这里的 rigid/compliant 描述**接触表示**，并不自动添加有限元自由度；本课讨论刚性 Multibody bodies 上的 hydroelastic 几何。E 的单位 Pa，不能把它当成 point stiffness 的 N/m，或无需校准便认定等于真实 Young 模量。[压力场与模型](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h#L316-L465)

局部弹性压力 pe 和耗散后的压力 p 有

$$p=p_e[1-dv_n]_+,\quad f_A=\int_S t_A\,dA,\quad
\tau_{A,C}=\int_S(p_{WQ}-p_{WC})\times t_A(Q)\,dA.$$

压力/traction 单位 N/m²；积分后才是 N 和 N·m。可视化的 surface field 是弹性压力，不是已经包含所有耗散、摩擦和离散修正的最终力场。表面积、压力、摩擦分布和力臂共同决定合 wrench。[耗散作用在压力层](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h#L516-L539)、[连续牵引与积分](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/hydroelastic_traction_calculator.cc#L24-L76)

严格 `kHydroelastic` 要求被查询的对有可用表示，且至少一方 compliant；无法剔除的 rigid–rigid 对会抛错。fallback 先尝试 surface，再尝试 point；后者也不支持时仍会抛错。它不是“所有形状都支持”，而且同一场景可能同时返回 point 和 hydroelastic 结果。[支持表和失败条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L345-L405)、[fallback 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L412-L452)

| 原生几何属性 API | 单位与含义 | 易错点 |
|---|---|---|
| `AddRigidHydroelasticProperties` | resolution hint 为 m | HalfSpace 等不需 tessellation 的形状有无 hint 重载 |
| `AddCompliantHydroelasticProperties` | resolution hint 为 m；modulus 为 Pa | 网格分辨率会改变压力场离散，不是 solver 容差 |
| `AddCompliantHydroelasticPropertiesForHalfSpace` | slab thickness 为 m；modulus 为 Pa | compliant HalfSpace 使用专用的有限厚度场定义 |
| proximity `hydroelastic` margin | m | 只适用于 hydroelastic 的数值机制，不是 point 穿透 allowance |

属性名称、约束和重载见[原生属性](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/proximity_properties.h#L110-L188)。compliant `Mesh(.obj)` 使用 convex hull，而 `.vtk` 体网格可直接使用；rigid Mesh 的表示另有规则。凹视觉网格的图像相同，不证明实际接触表面相同。增加 resolution 不修复错误的 convex hull 选择。[形状表示](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L355-L369)

margin 扩展接触作用区域，以缓解固定步长的间歇接触问题；不能据此宣称连续碰撞检测、零穿透或任意高速物体不穿透。[margin 的适用范围与目的](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h#L637-L666)

## 3. 材料组合必须按具体字段分别读

设几何 1/2 的参数为 k1,k2,d1,d2,μ1,μ2,τ1,τ2。下式适用于非负参数且分母非零；原生实现对零/∞另有分支。

| 组合量 | 组合律 | 含义 |
|---|---|---|
| point 刚度 k | `k1 k2/(k1+k2)` | 两个柔顺体串联；两者相等时变一半 |
| Hunt–Crossley d | `(k2 d1+k1 d2)/(k1+k2)` | 更软的一侧耗散权重更高 |
| hydroelastic d | 同样加权，但把 k 换成两侧 E | rigid 方视作 E=∞，结果取 compliant 方的 d |
| μs 与 μd | 分别 `2 μ1 μ2/(μ1+μ2)` | 调和平均；相同材料保持原 μ，不是刚度的串联公式 |
| SAP relaxation time τ | `τ1+τ2` | 直接相加，单位 s；不是加权平均 |

源码：[刚度、耗散、relaxation time](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_properties.cc#L65-L166)、[摩擦组合](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/coulomb_friction.h#L110-L139)。例如 k1=k2=200000 N/m 得 k=100000 N/m；μ1=.6, μ2=.5 得 μ=6/11；τ1=.01 s, τ2=.02 s 得 .03 s。它们没有共同的“取最小值”法则。

`AddContactMaterial` 只写非空参数，不帮所有消费者填默认值。point stiffness、Hunt–Crossley d 的缺省可走 Plant 的 penetration-allowance 启发式；这不是从真实材料自动识别。`relaxation_time` 公开表格仍说缺失会异常，但当前离散装配实际给每侧 0.1 s fallback，并由 getter 相加；本课示例**显式写每侧参数**，不让这个注释/实现差异悄悄决定模型。[属性写入合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/proximity_properties.h#L110-L129)、[公开参数表](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L770-L803)、[当前默认读取](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L752-L768)

选 `kSap` 时使用 relaxation time，忽略 Hunt–Crossley d；选 Similar/Lagged 时使用 d，忽略 relaxation time；连续模型也使用 Hunt–Crossley。源码中“SAP solver”有时被旧注释用来代指 `kSap` 近似，读字段时必须分清两者。

## 4. 摩擦正则化不只有一种曲线

理想滑动 Coulomb 为 `ft=−μd fn vt/||vt||`，静摩擦满足 `||ft||≤μs fn`。速度为零处不能直接做除法；Drake 的不同路径用不同正则化。

- **连续 point**：用 s=||vt||/vs 和 quintic `S(s)=10s³−15s⁴+6s⁵`。0≤s<1 时 μ=μs S(s)；1≤s<3 时 μ=μs−(μs−μd)S((s−1)/2)；s≥3 时 μ=μd。因此零速下正则化摩擦趋零，“stiction tolerance”不是精确粘着的二值判定。[实际函数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L4738-L4759)
- **连续 hydroelastic**：实际 traction 路径用 `μeff=(2/π) μd atan(||vt||/vs)`，再在零速附近稳定计算 atan(x)/x。不能因为都叫连续接触，就把 point 的 Stribeck 曲线套在 hydro 上。[牵引公式](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/hydroelastic_traction_calculator.cc#L240-L280)、[Plant 传入动态摩擦](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L2628-L2671)
- **离散三种近似**：实际装配使用组合后的 μd，μs 不参与离散摩擦。kSap 用数值驱动的 Rt 正则化；Similar/Lagged 用 soft norm，下一篇给出精确表达。[离散摩擦读取](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_properties.cc#L166-L174)

减小 vs 会缩小近零速的过渡区，也可能让连续 ODE 更刚、更难积分；增加 Newton 迭代数不能把错用的 μs 变成真实静摩擦。摩擦系数、正则化速度、solver tolerance 和 time step 是不同参数。

## 5. 原创 API 阅读与练习

[contact_inspection.py](../examples/contact_inspection.py) 显式建立一个 1 kg、半径 0.05 m 的原创球、compliant hydroelastic sphere 和 rigid HalfSpace，设置两侧材料，构造 Diagram/Context，并提供原生结果字段读取函数。没有调用 Simulator、强制事件或接触 Eval，也没有运行模型构建。它是配置/读回方法说明，不是球落地实验。

1. 把两侧 point stiffness 都设成 100000 N/m，组合刚度是否仍是 100000？
2. 模型返回一个 hydro surface，是否可断言它有正的最终净法向力？
3. rigid–rigid 在严格 hydro 模式中发生未过滤相交时，能否自动变成 point？
4. 两侧 friction 都是 μ=.5，为何不能套刚度组合公式算成 .25？
5. 只改 μs 而保留 μd，能否期待本版本离散接触的摩擦变大？
6. 设置 E=1e6 Pa 与 k=1e6 N/m，是否表示同一硬度？
7. 连续 point 和连续 hydroelastic 是否使用相同的速度正则化函数？

<details><summary>答案</summary>

1. 不是，是 50000 N/m。串联柔顺不能按单体 stiffness 理解。
2. 不可。surface 描述弹性几何压力；耗散截断、离散求解及采样决定实际报告力，还可能存在零力面片。
3. 不能；严格模式会报错。只有显式选择 fallback 才尝试 point，而且 point 也须支持该几何对。
4. 摩擦组合有分子系数 2，为相同表面保持原值而定义，μ仍为 .5。
5. 不能。实际离散装配取 dynamic_friction；应查看当前配置而非只看参数对象有两个字段。
6. 不是，单位和几何依赖都不同；hydro 的离散局部 k 还由面片面积和压力梯度共同决定。
7. 不是。前者使用分段 quintic Stribeck，后者实际使用动态摩擦的 atan 正则化。

</details>

继续：[从动力学装配到 SAP 终止](contact-solvers.md)。
