# E6：AutoDiff、symbolic 与物理路径的支持边界

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [原生系统扩展](systems-extensions.md) · [特色与综合追踪](engine-boundaries.md)

固定基线 Drake 1.57.0 / `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。先修 E3 接触/SAP 和 E6 原生转换。本篇把“能转换”“能调用”“导数有正确物理含义”分开，属于 B6/B7；没有运行 AD、symbolic 求值、优化或梯度检查。

## 1. 先确定求的究竟是什么导数

设 $y=f(z)$，$z\in\mathbb R^m$，$y\in\mathbb R^n$，在一个合法状态和固定计算分支附近，AutoDiff 标量保存数值与一组方向导数。若播种矩阵 $S\in\mathbb R^{m\times p}$，输出导数为：

$$
D_y=J_f(z)S,\qquad J_f\in\mathbb R^{n\times m}.
$$

播种单位阵得到完整 Jacobian；只播种一个方向得到方向导数。输入变成 AutoDiff 而没有非零 seed，不会凭空得到对所有模型参数的导数。若 y 单位 m、z 单位 rad，则对应列量纲 m/rad；不能把混合量纲的列直接相加当物理敏感度。

本版本 `AutoDiffXd` 已别名到 Drake 自己的 `drake::ad::AutoDiff`，不是直接的 Eigen AutoDiffScalar typedef；它保持 double 数值及动态长度的 double 偏导，某些 API 名称为了兼容 Eigen 保留。见[当前别名](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/autodiff.h#L12-L19)、[值与导数存储合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/ad/auto_diff.h#L12-L72)。这是前向局部数值导数，不是自动构建跨任意外部库的反向训练图。

`InitializeAutoDiff` 设置独立变量导数；对矩阵需注意储存展开顺序和导数列编号，不能只看二维数组外形。`ExtractValue` / `ExtractGradient` 是计算末端的提取接口，见[播种约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/autodiff.h#L105-L151)和[Python 辅助绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/autodiffutils/autodiffutils_py_everything.cc#L105-L136)。

在[一阶滞后例子](../examples/scalar_lag.py)中，tau=0.05 s、u=0.5 m、x=0.2 m，解析式给出 xdot=6 m/s；只对 x 播种时偏导为 −20 s⁻¹。它是教学算式，不是引擎输出。若想求对 u 的导数，必须给输入的导数方向，不能把常量 FixValue 自动当优化变量。

## 2. symbolic 是表达式，不是所有分支都能符号执行

`symbolic::Expression` 可以保存未绑定变量和代数关系；具体方法必须能处理这些表达式。涉及比较决定拓扑、碰撞对、整数索引、迭代停止或外部数值求解器的路径，不能因类模板存在便推断支持符号执行。转换 traits 明确说明：未绑定 Expression 降为数值可能抛错，向低信息标量转换也可能丢掉导数，见[值转换限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/scalar_conversion_traits.h#L87-L98)。

对于一个仅依赖代数运动学的查询，表达式可以保留；对于“是否接触”和滑动/黏着分支，则需读具体函数的标量支持表。symbolic 与 AutoDiff 也不同：前者保留关系，后者在当前数值分支上传播局部导数；二者都不自动处理任意事件时间的跳变敏感度或非光滑优化目标。

## 3. 按实际路径列支持矩阵

以下是固定源码支持边界，不是本仓运行矩阵。double 本身也有模型/几何/配置前置条件，“支持”不代表任意输入合法。

| 路径 | double | AutoDiffXd | symbolic::Expression |
|---|---|---|---|
| 兼容 System 的 scalar conversion | 原型/原生数值 | 需 converter 支持；Diagram 为子系统交集 | 同左；成功转换不保证所有方法 |
| 刚体运动学与其他明确支持查询 | 按 API | 可用对应 AD 方法，需匹配 Context/seed | 可查询明确支持的运动学/结构，不能据此推断接触更新 |
| 连续 Plant 接触力 | 按 point/hydro 及几何支持 | 仍受具体几何查询和局部分支限制 | 注册了 collision geometry 后，连续接触装配路径显式抛错；并不等待确认该时刻已碰撞 |
| 离散 SAP 接触更新 | 原生路径 | 内部存在当前隐式导数实现，仍需整个模型链支持 | manager 可以保留 symbolic 对象供其他查询，但 SAP 离散更新显式拒绝 |
| hydro contact surface | 支持的形状/表示 | double/AD 查询支持，导数由 pose 引入 | 不支持 |
| DeformableModel 含 body 或外部力密度 | 离散 Plant、SAP 路径 | 非空 model 不支持转换；Finalize 移除该 converter | 同样不支持；空 model 是特例 |
| 任意 renderer / Python / 第三方库 | 查该模块 | 不能从 Plant AD 推断它支持 | 不能从 System 泛型推断它支持 |

连续接触入口先判断 collision geometry 数量，为零即返回；否则 symbolic 分支抛错，见[连续接触的实际拒绝点](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L3407-L3447)。这与“把物体摆远就能在 symbolic 下推进接触模型”不同。

离散 manager 在 symbolic 时不构造 SapDriver，让 introspection/kinematics 可以使用转换后的对象；但求离散接触结果、更新力和 actuation 的相关路径会抛错。见[允许转换与推迟拒绝](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc#L245-L265)、[求解结果拒绝](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc#L191-L203)和[其他更新拒绝](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc#L291-L318)。无接触的特殊构型不能绕过这些显式 symbolic update 分支。

DeformableModel 的 `is_empty` 同时检查 body 数和 force_densities；只删掉 body、留下登记的外力场，并不满足空模型的 AD 条件。Plant Finalize 会据 physical model 的能力移除转换对，见[柔性模型转换判定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.h#L499-L511)、[Finalize 移除不支持类型](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L1638-L1646)及[converter 过滤实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L4663-L4676)。FEM 某些配置/内部材料模板支持 AD，不等于整个柔性 Plant 支持 AD。

## 4. 几何：unsupported 有时抛错，有时直接忽略

QueryObject 明确以 query、shape/shape pair 和 scalar 的组合报告支持；不同查询的行为不一致。点对穿透查询的固定表中，AD sphere–sphere 和 sphere–box 有支持，而 AD box–box 不支持；需要接触时会按函数合同抛错。见[point penetration AD 表](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L275-L311)。表内精度数字是官方特定几何尺寸/工况下的观测，不是本仓实测或任意模型误差界。

`ComputeSignedDistanceToPoint` 则对不支持的形状/标量组合**忽略该几何，不返回对应结果**。固定表中 AD 的 Convex/Cylinder/Ellipsoid/Mesh 标作不支持，Expression 全部标作不支持。见[点到形状距离的忽略合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L758-L775)。空结果不能统一解释为“离所有物体都很远”，还可能是该查询/标量没有覆盖它们。

hydro `ComputeContactSurfaces` 支持 double 与 AutoDiff，但导数只能由几何 pose 引入，不能对半径/长度等 shape 参数求导；fallback 还需同时满足 point 和 hydro 组成查询的能力。见[hydro 导数范围](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L391-L396)及[fallback 组合](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L420-L444)。非凸网格、几何滤除、接触生灭和表面剖分还带来不同分支；不能把一个 pose 的局部导数升级为 mesh topology 的全局导数。

柔性几何接触 `ComputeDeformableContact` 明确仅 double，见[柔性接触标量限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L455-L466)。此限制与上层 DeformableModel 的双精度/离散限制一致，不应拿刚体 hydro AD 证明柔性 FEM 的端到端可微。

## 5. SAP 的当前 AD 路径与数学条件

E3 已给出 SAP 的最优性方程 $g(v;\theta)=0$，$θ$ 表示进入该固定离散问题的参数。若在当前有效分支上可微，且 $H=\partial g/\partial v$ 可逆，隐函数关系给出：

$$
H\frac{\partial v^*}{\partial\theta}
=-\frac{\partial g(v^*;\theta)}{\partial\theta}.
$$

当前 `SapSolver<AutoDiffXd>::SolveWithGuess` 先建立/解 double 问题，再设置对参数的偏导并解隐式线性系统；不是把 Newton 全部迭代展开为反向图。见[实际 SAP AD 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L133-L232)。Plant header 仍有“有约束不支持 AutoDiff”的旧注释，不能仅据它否定现存实现；也不能仅据这一个实现把所有上游参数、几何和求解模式都判为可微。

该公式描述**所选接触/正则化模型的离散解导数**，不自动等于连续理想刚性接触或真实物体轨迹的导数。接触 active set 改变、max/锥投影的分段点、接触对生灭、退化几何、非光滑代价、未收敛求解都会影响解释。即使某分支输出了有限梯度，也不能把“返回值非 NaN”当作端到端梯度已验证。本轮没有有限差分、AD 对照或优化运行。

完整链要逐项回答：theta 怎样进入 Context 或固定模型；几何查询是否传播这些导数；材料组合/约束装配是否保留标量；SAP 该约束分支是否支持转换/导数；输出是否仍是期望时刻/坐标的数值；最后评价函数是否连续。任一段提取 double 或转到外部不可微模块，都会改变链的含义。

## 6. 把可微系统送给优化器还有一层合同

`DirectCollocation` 只优化连续状态，要求 System 支持 ToAutoDiffXd；它克隆给定 Context 的参数和相关固定输入，之后修改原 Context 不会更新已建立的问题。`assume_non_continuous_states_are_fixed=True` 只是让调用者承担“其他状态的变化不影响连续动力学”的假设，不会优化离散事件。见[直接配点前置条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_collocation.h#L18-L75)以及[运行构造检查](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_collocation.cc#L120-L134)。

`DirectTranscription` 的离散入口要求简单单周期更新和仅离散状态；连续入口采用显式 Forward Euler 约束。它不是让一个含多频传感器、abstract task、renderer、外部 I/O 的任意 Diagram 自动成为可优化轨迹模型。见[离散 transcription 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_transcription.h#L27-L64)和[连续离散化入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_transcription.h#L102-L122)。

离散 Plant 的 sampled 输出会引入记忆状态；原生文档对运动规划/优化建议连续 Plant 或 `use_sampled_output_ports=false` 获得更小状态表示，见[原生分析模式提示](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L519-L533)。这只是前置建模选择，不解决上面所有几何、solver 或 optimizer 限制，更不是把仿真模式静默更改后仍声称优化同一任务。

## 7. 易错点与带答案练习

“泛型类存在 → 转换注册 → 方法有实现 → 当前分支可微 → 完整任务梯度正确”是逐层增加的要求，任何一层都不能代替下一层。

1. **把 x 包成 AutoDiff(0.2) 而不播种，能得到对 x 的导数吗？** 答：只是一个常量值，导数为空/零；需显式独立变量方向。
2. **一阶滞后只播种 x，tau 固定为 0.05 s，xdot 对 x 的偏导是多少？** 答：−1/tau=−20 s⁻¹；对 tau 的导数没有在这个设置中计算。
3. **symbolic Plant 能成功转换，是否可调用 SAP 更新？** 答：不能据此推断；manager 特意允许其他查询，而 SAP 更新显式拒绝 Expression。
4. **symbolic 连续 Plant 的碰撞物体当前不相交，接触装配会自动跳过吗？** 答：源码先看已注册 collision geometry 数量，非零时会进入 symbolic 拒绝分支，不先证实实际碰撞。
5. **AD 点距离查询返回空列表是否证明无障碍？** 答：不一定；不支持的几何/标量组合会被忽略，必须核对支持表与几何覆盖。
6. **SAP 的隐式导数能直接求球半径到成功率的导数吗？** 答：不能；hydro 几何导数只由 pose 引入，成功率也可能不连续，完整链未因此成立。
7. **没有 deformable body 但登记了力密度场，是否算空 DeformableModel？** 答：不是；is_empty 同时要求 force_densities 为空，AD/symbolic 转换条件不满足。

[静态验收](evidence/e6-validation.md)。
