# E6：优化、柔性体与多物理边界的综合源码地图

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [原生扩展](systems-extensions.md) · [标量能力](scalar-capabilities.md)

本篇固定在 Drake 1.57.0 / `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，承接 E1–E5，完成 B7 从原生对象到具体能力与失败点的综合追踪。下文给出公开原生模块、内部实现与外部依赖的归属；不以目录、模板参数或论文名字充当运行验收。

## 1. 优化程序、接触 solver 与 Simulator 各解什么

`MathematicalProgram` 组织决策变量、目标和约束，例如：

$$
\min_z f(z),\qquad g(z)\le0,\qquad h(z)=0.
$$

`Solve` 根据问题属性及实际可用 solver 选择后端，或显式调用某个 SolverInterface；不是每个问题都由 SAP 解。SAP 是 E3 的离散接触速度问题，Simulator 则推进 System/事件/积分器。把三者都称为“求解器”会掩盖变量、容差和结果意义的差异，见[MathematicalProgram 归属](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program_doxygen.h#L5-L30)和[Solve 分派合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/solve.h#L14-L39)。

| 路径 | 决策量 / 结果 | 能力边界 |
|---|---|---|
| InverseKinematics | 某姿态的 q 与几何/运动学约束 | E2 已解释：姿态可行不等于控制可执行 |
| KinematicTrajectoryOptimization | B-spline 路径 r(s) 与时长 T，q(t)=r(t/T) | 轨迹导数是 qdot，不是所有模型的广义速度 v；动力学和碰撞约束需明确添加 |
| DirectCollocation | 连续状态和输入轨迹及时间间隔 | 原生假设 FOH 输入、三次状态曲线和配点动力学；不自动覆盖混杂接触/事件 |
| DirectTranscription | 采样状态/输入，一步更新约束 | 有特定单周期离散或显式 Euler 连续入口，不是任意完整仿真图 |
| GraphOfConvexSets | 图上的路径、每个凸集内连续变量、边成本/约束 | 凸松弛可能不紧；rounding/restriction 的可行路径不是任意问题的全局最优保证 |
| 原生 MultilayerPerceptron | 端口输入输出、Context 中权重/偏置、解析 backprop | 是具体网络 System，不是完整学习库、GPU 物理或训练服务 |

KinematicTrajectoryOptimization 的 s 无量纲、T 单位 s；对 T>0，有 $\dot q=r'(s)/T$、$\ddot q=r''(s)/T^2$。四元数模型里 `qdot=N(q)v`，不能把 qdot bounds 无条件叫关节速度/基座角速度限制，见[轨迹对象与 qdot 约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/kinematic_trajectory_optimization.h#L21-L43)。若只在有限 s 点添加非线性避障约束，也不能把它当成整个连续曲线碰撞自由的证明。

GCS 的原生选项区分 mixed-integer 问题、凸松弛和候选路径 rounding；固定源码明确说松弛不能解所有原始 NP-hard 实例。见[GCS 松弛与 rounding](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/optimization/graph_of_convex_sets.h#L42-L80)。这类算法的结果、初值、求解器与容差需要记录，不能仅看“路径画出来了”宣布可执行抓取。

MLP 以 $x_{i+1}=\sigma(W_i x_i+b_i)$ 组织层，权重保存在 Context；其 Backpropagation 使用解析梯度，预期 double，不要求 AutoDiff。见[原生 MLP 对象](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/multilayer_perceptron.h#L28-L54)和[解析 backprop API](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/multilayer_perceptron.h#L216-L249)。这补充 E5 的 Gym 接口边界：Drake 有具体学习相关组件，但 Gym 不因此变成训练器，MLP 的局部梯度也不自动穿过接触轨迹。

### 1.1 外部 solver 身份和成功状态

SolverInterface 的 `available()` 表示编译进当前 Drake，`enabled()` 表示运行配置允许使用，`AreProgramAttributesSatisfied()` 表示问题类型兼容；三者都不是“已经求得有效解”。商业/开源后端及实际构建配置属于另一层依赖，不能把源码里有接口写成此设备已安装/获许可。见[solver 可用性与属性](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/solver_interface.h#L24-L86)。

最后仍需检查 MathematicalProgramResult 的结果状态、残差和问题自身物理约束。局部非线性优化成功不证明全局最优；求解器容差不修复错误坐标、失真的惯量或漏掉的动力学。本轮既未检测本机 solver available/enabled，也未运行任何 Solve。

## 2. 三种容易混淆的“软”模型

| 模型 | 是否增加物体内部变形自由度 | 本版本归属 |
|---|---|---|
| 刚体 hydroelastic 接触 | 原有刚体 q/v；压力场用于接触表面与力，不把刚体变成 FEM 网格 | SceneGraph + MultibodyPlant 原生接触；见 E3 |
| DeformableModel / FEM | 固定体积网格的节点位置/速度/加速度，内部形状可变化 | 原生实验性功能，非空 model 限 double、离散 Plant、SAP |
| MPM 内部算法 | 粒子与背景网格的内部状态/能量计算 | 固定源码有 internal 实现和 private Bazel 目标，不能当作公开 Plant/Python 功能 |

DeformableModel 以固定拓扑体积网格和近似 signed distance field 描述柔性体，每个 body 建 FEM 模型，见[模型与注册合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.h#L38-L107)。这不是仅给 rigid geometry 填一个柔软材质；也不能从 volumetric FEM 推断已提供切割、拓扑断裂、壳/布料、绳索或通用流体模拟器。

## 3. FEM：字段、状态、离散与接触链

注册前取得 `plant.mutable_deformable_model()`，传 GeometryInstance、DeformableBodyConfig、model instance 和 resolution_hint；在 Plant Finalize 前完成。resolution_hint 单位 m，指导网格细化，近似对应 primitive 网格边长；它不是 dt 或求解容差。原生注册要求 double 和离散 Plant，见前述 RegisterDeformableBody 合同。Python 绑定明确注册 double 的 DeformableModel 及两种 RegisterDeformableBody 重载，见[模型注册绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L1783-L1816)；材料枚举和 Config 的实际 getter/setter 见[FEM 配置绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/fem_py.cc#L22-L88)。C++ 的 element_subdivision_count setter 并未在这段 Python Config 绑定中暴露；内部 integrator/parallelism 等方法也不能想象成普通 Python setter。

| DeformableBodyConfig 字段 | 单位 / 合法假设 | 固定默认值及解释 |
|---|---|---|
| Young's modulus E | Pa，E>0 | 1e8；体积材料刚度，不等于 point stiffness N/m |
| Poisson ratio nu | 无量纲，−1<nu<0.5 | 0.49；接近不可压缩时需考虑数值条件，不能设成恰好 0.5 |
| mass density rho | kg/m³，rho>0 | 1500；由体积积分形成质量 |
| mass damping alpha | s⁻¹，非负 | 0；Rayleigh 质量项 |
| stiffness damping beta | s，非负 | 0；Rayleigh 刚度项 |
| material model | 离散枚举 | kLinearCorotated；还列 kCorotated、kNeoHookean、kLinear |
| element subdivision count | 整数 0…4 | 0；细分外部体积力求积，不等于增加接触/时间子步 |

这些是固定源码默认值，未用于拟合真实材料或运行实验，见[字段与范围](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/deformable_body_config.h#L14-L77)。线性弹性适合小应变/小转动假设；corotated 等本构处理旋转的方式不同，不可把改枚举当作同一模型的纯加速选项。此处不对材料模型做准确度/速度排名。

Rayleigh damping 为 $D=\alpha M+\beta K$。若以模式频率 $\omega_n>0$ [s⁻¹] 线性化，阻尼比为：

$$
\zeta_n=\frac12\left(\frac{\alpha}{\omega_n}+\beta\omega_n\right).
$$

alpha 和 beta 分别在低/高频有不同作用，不是同一个“阻尼百分比”。刚体运动的零频极限不能直接除以零代入此式；源码说明质量阻尼会影响刚体运动，见[Rayleigh 模型](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/damping_model.h#L10-L33)。

**固定实现差异**：DeformableBodyConfig 的两个 damping setter 检查的是旧成员非负，然后才赋新值；并非立即检验传入参数。因此从默认 0 调用一次负值 setter，不应依据注释声称它已被该 setter 拒绝。下游构建 FEM 时把系数交给 DampingModel，后者确实对传入值做非负检查；校验只是可能推迟，不能理解为负阻尼合法。见[setter 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/deformable_body_config.h#L94-L104)、[材料构建调用](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/deformable_body.cc#L462-L471)和[下游入参检查](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/damping_model.cc#L9-L16)。没有在本机执行这个缺陷路径，也没有修改上游。

线性四面体单元和一阶基础求积在 DeformableBody 中选定；每个 body 声明长度为 `3*num_dofs` 的离散块，按 `[q,v,a]` 保存节点状态。q 是节点位置，不是刚体四元数/关节配置向量；num_dofs 对应节点平移自由度。见[单元与状态装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/deformable_body.cc#L427-L482)。不要只读 `plant.num_positions()` 或刚体 `[q;v]` 端口，就假定拿到了所有柔性节点状态。

| 原生柔性 API | 数据合同与生命周期 |
|---|---|
| `GetDiscreteStateIndex(id)` | Finalize 后取得该 body 所属离散块索引；不是刚体 position_start |
| `SetPositions(context,id,q)` / `SetVelocities(context,id,v)` | q、v 分别为 3×N 节点矩阵，单位 m、m/s；使用所属 Plant Context，节点数及有限值需合法 |
| `GetPositions` / `GetVelocities` | 各返回 3×N 值矩阵；不是 body pose 的 4×4 齐次变换 |
| `GetPositionsAndVelocities` | 返回 3×2N，前 N 列位置、后 N 列速度；不能误当 6×N 或完整 q/v/a |
| `AddFixedConstraint` | Finalize 前以 X_BA 和 X_BG 选择参考网格中受约束顶点，并固定到同一 Plant 的刚体；形状未选中任何顶点会抛错 |
| `AddExternalForce` | 注册体积力场；Python 绑定通过 Clone 保存，不能靠随后改原 Python 对象假定已更新 Plant |

上述矩阵/Context 合同见[节点状态接口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.h#L171-L302)，固定约束见[参考网格选点与前置条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.h#L130-L169)，Python 状态/外力绑定见[实际可调用入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L1817-L1856)。这些是 API 数据形状，不是本轮生成的节点数据。


内部 free-motion integrator 选择 VelocityNewmarkScheme(h,1.0,0.5)，源码明确写出位置中点规则：

$$
q_{n+1}=q_n+\frac h2(v_n+v_{n+1}).
$$

它属于柔性模型内部时间更新，不能等同刚体 E3 的 `q0+hN(q0)v_next`，也不由给 Simulator 换一个连续积分器来替代，见[柔性时间积分配置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.cc#L24-L35)。

有约束时，DeformableDriver 先求 free-motion FEM 状态和切线矩阵的 Schur complement；参与接触/约束的速度进入接触求解结果，再恢复未参与节点的速度增量，最后通过该内部 integrator 得到下一 FEM 状态。无参与节点时直接用 free-motion 状态。见[自由状态与 Schur 数据](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_driver.cc#L965-L984)和[求解后重建节点状态](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_driver.cc#L986-L1043)。因此“只有表面节点接触”不意味着内部节点完全不动；刚柔耦合也不是把刚体 contact force 矩阵按行贴到所有节点。

非空 DeformableModel 的系统资源声明再次检查 discrete/SAP；标量转换只允许空模型，详见[可微篇](scalar-capabilities.md)。固定源码允许 kSap、kLagged、kSimilar 对应的 SAP solver 条件，不能把“SAP”误写成只允许 kSap 近似，见[真实模式检查](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.cc#L439-L458)。

## 4. MPM 目录、气动力与真正的多物理范围

固定树确实有 `multibody/mpm`：`mpm::internal::MpmModel` 以粒子数据和网格速度增量描述 backward-Euler 弹性能量与残差，见[内部 MPM 方程与对象](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/mpm/mpm_model.h#L13-L57)。但该包的 Bazel 默认 visibility 和 package library 均是 private，并保留“等被 MbP 等使用后再公开”的 TODO，见[实际可见性](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/mpm/BUILD.bazel#L14-L23)。不能从这个目录推导存在 `pydrake.MpmSimulator`、可用流体/粒子场景或 GPU MPM。内部测试/算法存在、公开集成、绑定可达、实际运行是不同证据。

原生多物理相关入口还有外力模型。例如 Propeller 是无状态 System，将 command 乘 thrust_ratio 得到沿 propeller z 轴的 N、乘 moment_ratio 得到 N·m，通过 `ExternallyAppliedSpatialForce` 接到 Plant；默认 command 可解释为 N，但调整系数后命令单位需重新声明。它没有自动建电机电流、转子惯量或流体场，见[Propeller 原生合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/propeller.h#L28-L80)。

Wing 给出粗粒度平板气/水翼近似，使用 body pose、spatial velocity、可选 world wind 和流体密度输入，输出空间力。固定模型的 $C_L=2\sin\alpha\cos\alpha$、$C_D=2\sin^2\alpha$、$C_M=0$；surface area 单位 m²、density kg/m³。这是特定力模型，不是 Navier–Stokes 网格求解或完整流固耦合，见[Wing 方程与端口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/wing.h#L16-L60)及[构造参数量纲](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/wing.h#L76-L96)。

自定义热/流/电模型可以通过 Systems 状态、事件与外力端口耦合，但“可以扩展”只说明存在编程接缝，不意味着当前 Plant 已内建温度场、电路、燃烧或通用 CFD。外部引擎/学习框架/消息桥的时钟、单位、线程、数据复制和许可由实际适配层负责；E5 已解释 host/GPU 和外部 RNG 边界。本课程不虚构一个统一跨引擎/多物理 wrapper。

## 5. 从一个问题走完整条源码链

以“离散机械臂受力后，记录末端受力并研究对控制输入的局部敏感度”为阅读任务，下面每一步均有独立合同，不需要先运行实验才能理解。

| 步骤 | 原生链 / 对应课程 | 此处应回答的问题 |
|---|---|---|
| 建模与身份 | Parser → body/joint/actuator → Finalize；[E1](modeling-state-time.md) | 资产单位、nq/nv、惯量和 model instance 是否一致？Finalize 后哪些结构已冻结？ |
| 系统拓扑 | Plant ↔ SceneGraph；controller/reference → actuation；[E2](control-robotics.md) | 哪些输入直通，哪些是状态；几何 QueryObject 属于哪个 Context？ |
| 配置与时间 | h、contact model、approximation、sampled outputs；[E1](state-time.md)/[E3](contact-solvers.md) | 控制周期、Plant 更新和 Simulator 内部步如何区分？ |
| 碰撞/材料 | query → point/hydro 数据 → 组合材料；[E3](contact-models.md) | 接触 pair/shape/scalar 是否支持；材料单位和组合律是什么？ |
| 约束与求解 | manager → SapDriver → free motion / contact problem → SAP | vstar、J、R、gamma 和终止条件各代表什么？失败在哪里抛出？ |
| 输出与采样 | ContactResults / generalized forces / sensors；[E3](contact-observation.md)/[E4](sensor-timing.md) | 力在哪一侧、哪个点、哪个 frame、哪个物理时间？是否保持的旧输出？ |
| 标量/优化 | System converter →新 Context/seed→几何→SAP→评价量；[本阶段](scalar-capabilities.md) | 研究的是输入、初态还是参数导数；哪段抽取 double 或不可微？ |
| 数据与复现 | logger trigger → 副本 → 元数据；[E5](data-replay.md) | 发布时刻是否等于观测时刻；reset/RNG/失败样本保存什么？ |

若加入柔性体，第三至第五步改为含独立 FEM `[q,v,a]` 状态及 DeformableDriver，标量能力也被非空 DeformableModel 收紧；不能只把 rigidity 标志换成 false，继续沿用刚体 AD 结论。若用优化器规划轨迹，规划模型还要满足优化方法的状态/输入假设，不能以仿真图能构造代替可优化性。

推荐阅读顺序是先看公开调用的前置条件，再看实际 `if constexpr`/throw 分支和 driver 装配，最后回到绑定与数据拥有者。对注释/实现差异保留两者的固定出处；不要用最新版文档或不同语言绑定补填本版本的空白。

## 6. 易错点与带答案练习

1. **MathematicalProgram Solve 和 SAP 是否同一个 solver？** 答：不是；前者针对用户优化程序分派后端，后者求当前离散接触速度问题，Simulator 则推进系统时间。
2. **KinematicTrajectoryOptimization 的 qdot bounds 是否总等于 v bounds？** 答：否；qdot=N(q)v，含四元数等模型尤其不同，必须按原生坐标映射解释。
3. **GCS 凸松弛返回结果是否保证原图全局最优可执行路径？** 答：不保证松弛紧或 rounding 完美；还需实际路径可行性和模型执行约束。
4. **把刚体改成 hydroelastic 是否新增节点变形状态？** 答：没有；刚体 hydro 接触与固定体积网格 FEM 是不同模型，后者显式维护节点 q/v/a。
5. **两个 damping setter 接受一次负的新值是否说明负阻尼合法？** 答：不是；固定实现先误查旧成员，但下游 DampingModel 对传入系数检查非负，可能在材料构建时拒绝。
6. **MPM 源码目录存在，能否宣称公开 Python 流体引擎已经可用？** 答：不能；此版本是 internal 对象/private 包，尚无由这里证明的公开 Plant/绑定集成。
7. **加入柔性体后刚体 SAP 的 AD 结论能否原样保留？** 答：不能；非空 DeformableModel 限 double，Finalize 会移除 AD/symbolic 转换，必须重新审整条链。

本阶段完成源码课程，不改变 DexLab [#117](https://github.com/huangkiki/Dexlab/issues/117) 的 Drake 运行资格。后续实验仍复用 DexLab；E7 留给两条路线的全文审校及证据入口整合。[静态验收](evidence/e6-validation.md)。
