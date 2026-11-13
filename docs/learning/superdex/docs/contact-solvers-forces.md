# E3 · 接触、隐式积分、求解器与力观测

本章覆盖 A4、B1–B5，并补齐 B0 的动力学残差与装配。先读 [E1 的坐标、状态、惯量和时间](modeling-state-time.md)，再读 [E2 的外力、控制器和 IK](control-robotics.md)。先修是向量/矩阵、微分、虚功、刚体动力学和基础数值迭代；下面把教学方程与具体实现分开标明。

阅读对象是 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。这里只审查官方代码和最小片段语法，**未 import 或运行引擎，未执行实验、benchmark、训练或评分**。候选包 `1.0.0` 不等于此 commit 的实际构建；DexLab 历史批次的求解配置仍须由 [#124](https://github.com/huangkiki/Dexlab/issues/124) 和原批次材料确认。本章的默认值与算法分支不能填补该历史证据缺口。

## 1. 先分清四个问题

| 问题 | 原生入口/实现 | 不能互相替代的含义 |
|---|---|---|
| 两个物体在哪里发生相互作用 | `ColliderType`、表面 quadrature samples、SDF/点云、contact filters | 可视 mesh、检测几何和积分采样是不同对象 |
| 接触施加什么力 | `ContactParams`、`ComputeBatchContact*` | 罚接触、平滑 Coulomb、黏性摩擦、法向耗散是力模型 |
| 怎样离散时间 | `SolverParams.integration_method` | Backward Euler、BDF、DIRK 决定离散方程/stage/历史 |
| 怎样解该离散方程 | `non_linear_solver`、`linear_solver` | Newton/BFGS/SR1、线性分解/Krylov、line search 和终止条件 |

这些功能属于 **Physics**。Robotics 导入/构建 actor、提供驱动目标；Studio 提供资产和编辑工作流，均不能单独证明某次 Physics 使用了何种接触或求解设置。沿 `scene.get_solver_params()`、每个 actor 的 `get_contact_params()`、实际 collider 与 query 记录读取原生配置；不要从编辑器截图或 Python 包版本猜配置。[Python 契约][api]与[配置到求解器的映射][simulation]是两个核对层。

## 2. 从连续动力学到实际装配

对选择好坐标和广义速度的刚体/机器人，连续力平衡可用教学式表示：

$$M(q)\dot v+c(q,v)=Q_{\rm ext}+Q_g+Q_{\rm elastic}+Q_{\rm damping}+\sum_i J_i(q)^T f_i.$$

这里 `q` 可能含 quaternion，不能直接令 `q̇=v`；应使用 E1 的运动学映射或局部旋转增量。`M` 是惯性算子；平移质量单位 kg、转动惯量 kg·m²，混合 DoF 的广义力分量分别为 N/N·m。`J_i v` 必须得到与 `f_i` 同一 frame、同一作用点的速度。由虚功 `δW=fᵀδx=fᵀJδq` 可得 `Q=Jᵀf`，这就是接触从空间力进入广义残差的原因，而不是把三个世界力分量直接写入任意三个 joint slot。

这不是 SuperDex 内核逐项复制的一条统一公式。原生 `AssembleIslandProblem` 收集 actor 项、constraint 项和 contact interaction 项；刚体有 7 个 pose 标量但 6 个增量/残差槽，关节系统会把 link 的 full-space 项投影到 reduced coordinates，柔体/壳/杆另有有限元变量与材料装配。Dirichlet boundary conditions 通过清零对应 residual 和处理矩阵行列实施；它们与有限刚度的 target/range constraint 不是同一种“硬度”。[装配入口][solve]、[刚体实现][rigid]、[关节系统投影][articulated]和[E2](control-robotics.md)的约束参数需一起读。

刚体惯性还有明确分支：[GetRigidInertiaFn][inertia]按 `useNewtonEuler` 选择 merit-based 惯性或 Newton–Euler 残差。后者旋转部分包含 `I_W Δω/h + ω×(I_Wω)`，源码说明其 merit/Hessian 是近似；前者使用二阶质量矩和旋转矩阵构造 merit。`experimental.enable_newton_euler_inertia` 的绑定见[生成入口][experimental-binding]。不能只写“Newton 求解”就假定惯性形式：**Newton 非线性算法、Newton–Euler 惯性模型是两个配置层**。本章覆盖动力学装配框架，柔体材料与可微实现的详细推导留 E6。

## 3. 检测几何、积分采样与有方向的接触

### colliding 与 collider

`colliding` 提供受测的表面/中心线采样点，`collider` 提供距离或邻近几何。`ColliderType.NONE` 只表示别的 actor 不能以它为 collider 检测，并不自动关闭它主动检测别人的能力；是否生成 colliding samples、接触 pair 的过滤开关也须与 collider type 分开看。静态 actor 可以作为 collider，却不作为需要动力学更新的 colliding actor。[类型定义][contact-params]和[候选对构建][contact] 3928–4055 行提供证据。

| collider | 该版本含义 | 主要边界 |
|---|---|---|
| `AUTO` | 按 actor/shape 选择；初始化后 getter 返回实际类型 | 不能把 Auto 当固定算法名 |
| `SPHERE` / `BOX` | 来自形状 bounding volume 的球近似或局部 AABB | 适合相应几何，复杂 mesh 会丢细节 |
| `PLANE` | 无限平面 | 只支持带 implicit plane shape 的静态刚体 |
| `SDF` | 网格 signed distance field；必要时初始化构建 | 分辨率、闭合性、映射误差影响距离和梯度；不是原始三角面精确接触 |
| `MESH` | 表面 mesh collider，实验性 | 只适用于支持的刚体/link，源码文档标注较慢 |
| `POINT_CLOUD` | colliding/collider 采样点邻近查询 | 特殊点云对路径；不能假设能作为任意 SDF actor 的 collider |

SDF 的 `d<0` 表示在内部；精确距离的 `∇d` 是单位外法向，但近似/映射 SDF 的梯度不一定单位长。法向罚力使用梯度，摩擦平面则会归一化或使用指定的 colliding normal。这解释了“画出来的法向正确”为什么不充分证明压力幅值正确。[SdfInfo][contact-types]、[摩擦法向选择][contact-law]。

contact samples 是 quadrature nodes，每个带积分权重。表面权重单位 m²；杆中心线权重 m；取决于表示，不应把采样点数当接触面积。点云路径通过 spatial hash 寻找 `radius + threshold` 范围内邻居，构造 `d=‖p_a−p_b‖−radius` 和梯度，支持符合条件的 self-contact 排除；这个 radius 是点云接触参数，不是一般机器人 link 半径。[点云实现][point-cloud] 24–52、321–350 行。低维与 collider-side quadrature 的尺度修正在下一节说明。

### 过滤、双向与同步

`scene.enable_layer_contact_symmetric(...)` / `enable_actor_contact_symmetric(...)` 处理两个检测方向，`*_asymmetric` 只处理给定 colliding→collider。**layer 与 actor 两层开关必须同时允许**；打开 actor 对不能覆盖禁用的 layer 对。`include_nested_actors=physics.IncludeNestedActors.YES` 是否应用到 links 是显式选择，不能默认 parent handle 就涵盖全部 link。[原生过滤表][filters]、[官方例子][filter-example]。

内部 `ContactType::Async` 用 collider 上一步状态，只把力加到 colliding；`Sync` 用双方当前状态，装配两边的作用/反作用。在本固定实现的候选对路径，动态对静态走 Async，动态对动态按各允许方向走 Sync，点云对单独走 Sync。这里的 Async/Sync 描述力学耦合，不表示 Python step 是异步返回。双向检测、双方 query、self-contact 都可能使“把所有列表直接相加”产生重复计数，必须按检测方向和 actor 身份解释。[ContactType][contact-header]、[候选对][contact]。

更新的 conservative bounds 用于筛候选和分岛，且随重力、当前速度等扩张；它不是对任意高速穿越、薄层或任意控制跳变给出的连续碰撞无穿透保证。检测阈值、sample 分辨率与步长仍需共同理解；本章没有用运行结果替代这些限制。

## 4. 材料组合：逐字段核对，而非一个 combine mode

实际分支是 [CombineContactParams][combine]。先复制 collider 的全部参数，再覆盖下表；用 A 表示 colliding、B 表示 collider：

| 字段（Python 为 snake_case） | 两个动态 actor | B 是静态 collider | 单位 |
|---|---|---|---|
| `coulomb_friction_coefficient` | `sqrt(μ_A μ_B)` | 同样几何平均 | 1 |
| `viscous_friction_coefficient` | `sqrt(c_A c_B)` | 同样几何平均 | s/m |
| `normal_viscous_damping_coefficient` | `sqrt(cn_A cn_B)` | 同样几何平均 | s/m |
| `penalty_coefficient` | `sqrt(k_A k_B)` | **取 k_A** | 基础值 Pa/m |
| `friction_falloff_vel` | `sqrt(v0_A v0_B)` | **取 v0_A** | m/s |
| threshold、smoothing、normal 选择/对齐等其他字段 | 取 B | 仍取 B | 分字段 |

所以 μ=0.2 与 0.8 得到 0.4，**不是 min=0.2，也不是算术均值 0.5**。任一方某种摩擦/耗散系数为零，该种机制即为零；一边只开 Coulomb、另一边只开 viscous 不会混成某个非零摩擦。静态平面的 penalty 值没有直接控制这条接触的 k，但其 smoothing/threshold 仍会影响响应。

基础 k 之后还乘 `L_A^(2−d_A) L_B^(−d_B)`。`d_A` 是 colliding 积分维数，通常表面 2、中心线杆 1；`d_B=0` 表示标准 collider 无额外积分，点云 collider 可有自身积分维数并用其 radius 作尺度。`L_A` 来自 colliding 的 `colliding_penalty_length_scale`，不是 collider 复制值。维数修正确保最终积分得到力；不能把低维 penalty 数字当作同一面积弹簧直接比较。

建议阅读时对每个方向画出 A/B、静态标志、积分维数，再抄配置。配置组合属于此固定源码，DexLab 历史运行 wheel 是否匹配这些分支仍待原批次证据。

## 5. 法向罚接触与耗散：力密度到合力

### 平滑 penalty 的方程与量纲

作为对照，理想刚性单边点接触常写成 `g≥0, λ_n≥0, g λ_n=0`：间隙与法向反力满足互补关系，λ_n 是待求反力。这里的原生分支则从距离和平滑 penalty 计算力密度，允许有限压入来平衡负载；不应把它改述为求解无穿透 LCP，也不应把 penalty coefficient 当成反力乘子。

先限定常规二维表面积分、精确 SDF、合法相向法线、同一 frame，暂不带低维修正。设阈值 `d0` [m]、平滑半宽 `s≥0` [m]、`z=d0−s−d`，源码用 `ψ=PolyReLU(-d,s,s−d0)`：

$$\psi(z)=\begin{cases}0,&z\le-s,\\
\frac{3s}{16}+\frac z2+\frac{3z^2}{8s}-\frac{z^4}{16s^3},&|z|<s,\\
z,&z\ge s.\end{cases}$$

`s=0` 按非平滑 `max(d0−d,0)` 极限解释。每单位面积的 penalty energy 为 `W=kψ²/2` [J/m²]，法向 traction（单位面积力）为

$$t_n=k\psi\psi'\nabla d \quad[\mathrm{Pa}],\qquad F_i=w_i t_{n,i}\quad[\mathrm N].$$

`k` 的单位是 **Pa/m=N/m³**，不是一个点弹簧的 N/m；对于固定面积 w，才得到有效斜率 `w k` [N/m]。力从 `d=d0` 开始出现，在 `d≤d0−2s` 进入线性区域。阈值可以非零甚至负数；“零几何穿透时有力”本身不证明算法出错。`penalty_threshold_extra_padding` 只在 colliding 为 None/PointCloud 等指定分支添加，不是所有 contact margin 的同义词。[法向装配][contact-law] 498–618 行、[PolyReLU][activations] 92–132 行。

`max_alignment_normals` 比较双方 normal 点积，超过阈值禁用对应 sample 的 penalty，目的是避免深嵌几何被错误方向的力困住；没有合法表面 normal 的低维表示另走分支。若启动 `fade_friction`，耗散还乘 `(a_max−a)/(a_max+1)`；`a_max=-1` 用单独保护分支。不能拿这套防困住启发式当成任意深穿透的真实材料定律。

源码 dforce 使用 `−k(ψ'²+ψψ'')∇d∇dᵀ`，未在这个局部表达式里保留完整 SDF 曲率 Hessian 项；更上层还会经过 Jacobian 映射、PSD 投影等近似。因此“求解器名叫 Newton”不等于每个模型项都采用未经修改的精确二阶导数。

### 两种 Coulomb 正则化

设 stage 有效时长 `h_s`，在接触参考系中的相对位移 `Δp`，单位摩擦法向 n，切向位移 `u=(I−nnᵀ)Δp`，`r=‖u‖`、`ε=v0 h_s`。固定 normal 和耗散基准法向强度 `p_ref` 时，平滑 Coulomb traction 为

$$t_C=-\mu p_{\rm ref}\,g'(r)\frac{u}{r},$$

零位移按源码的稳健 `g'(r)/r` 分支取极限；不是直接除零。该式以正则化位移的方向确定阻力，`p_ref` 可能使用 stage-start 或当前 penalty，不能不看配置就写成当前查询的全部法向合力。

| `CoulombFrictionModel` | 实际 `g'(r)` | 含义 |
|---|---|---|
| `C1Regularized` | `2r/ε−(r/ε)²`（0≤r<ε）；1（r≥ε） | 有限区间达到 Coulomb 幅值；源码不是在整段内简单线性 ramp |
| `CinfRegularized` | `r/sqrt(r²+ε²/4)` | 渐近达到幅值；ε=0 内部钳到机器 epsilon |

在这两个模型中，平滑尺度非零时零速度对应零摩擦，微小位移产生过渡响应；它们不是能在严格零滑移处任选 `|t|≤μp` 的理想静摩擦互补约束。`friction_falloff_vel` 越小，局部斜率越陡；改变它既改变数值条件，也改变低速响应。这里没有凭空引入独立 static/dynamic friction 两个 contact 字段。关节 Stribeck 模型是别的路径，不能混到接触材料表。[摩擦装配][contact-law] 620–947 行、[两种 activation][activations] 134–213 行。

### 黏性项、恢复与 stage-start 近似

在上述局部假设下，附加项为

$$t_{\rm visc}=-c_t p_{\rm ref}\frac{u}{h_s},\qquad
 t_{\rm damp}=-c_n p_{\rm ref}\frac{n n^T\Delta p}{h_s}.$$

两种系数均为 s/m；都乘 penalty 强度，所以不是任意常数 N·s/m 的弹簧阻尼器。Coulomb、切向黏性、法向黏性可同时开启。组合后切向力不一定受纯 Coulomb 的 `μp` 上限约束，因为黏性项额外存在；恢复阶段法向黏性反向于速度，也不要把总法向项无条件写成严格非负的互补乘子。

原生 experimental 提供 `calibrate_normal_viscous_damping_coefficient` 和 `effective_coefficient_of_restitution`。前者使用拟合 `c_n v=(1−e)(1+4.5e)/(e(1+8e/3))`，要求 `0<e≤1`、特征碰撞速度 v>0；e→0 发散。它不是直接设置速度无关 restitution 的冲量定律。离散步长、实际速度、接触分布仍影响结果；法向耗散还可对滚动区域产生阻力。[拟合实现][contact] 4324–4368 行。

`experimental_eval.explicit_normals` 决定摩擦 normal/对齐使用 stage-start 还是当前几何；法向 penalty 的 SDF 梯度仍用当前值。`implicit_normal_force_for_dissipation` 决定耗散强度使用当前 penalty，还是 stage-start（若 normal 非显式则由当前梯度近似估计）的 penalty；启用它时力的导数仍丢弃部分 `d(p_ref)` 以保持所用对称近似。`implicit_normal_force_for_dissipation=True` 与 `explicit_normals=True` 的组合被 `SetSolverParams` 拒绝。具体 branches 见 [contact-law][contact-law] 1035–1188 行和[评估参数][eval]。

当 residual 不是某个所记录 merit 的精确梯度时，不能把它概括成“最小化一个凸能量所以必收敛”。源码明确指出 implicit normal force、implicit normal alignment fading 等会引入非可积项；Newton–Euler 惯性也有相同的 merit 限制。E6 才进一步展开可微支持条件，本章先保留这种数学边界。

## 6. Backward Euler：隐式不等于无误差

只为推导，取欧氏平移坐标 x、常质量矩阵 M、有限正步长 h，忽略旋转流形和时变质量。在步末求力：

$$x_{n+1}=x_n+h v_{n+1},\qquad
M(v_{n+1}-v_n)=hF(x_{n+1},v_{n+1}).$$

消去速度得到位置残差：

$$R(x)=\frac{M}{h^2}(x-x_n-hv_n)-F\!\left(x,\frac{x-x_n}{h}\right)=0.$$

平移分量单位 N。若 `F=−∇U+F_ext` 且外力固定、无非可积耗散，可写目标

$$\Phi(x)=\frac{1}{2h^2}\|x-x_n-hv_n\|_M^2+U(x)-F_{\rm ext}^T x.$$

这是解释惯性 `1/h²` 缩放、contact stiffness 和求解条件的简化式，不是对全引擎含摩擦、关节、旋转和柔体的“完整能量证明”。刚体 stage 结束速度确实由 stage 两端 pose 差分恢复；旋转通过原生 quaternion 增量组合/归一化处理，而不是七维数组相加。[rigid::ComputeVelocityAtStageEnd/EntityPostNewIncrement][rigid]和[惯性装配][inertia]。

对线性测试方程 `y'=λy`，BE 的放大因子是 `1/(1−hλ)`；左半平面稳定和高频衰减解释了其 A/L 稳定特性。**这个线性离散结论不保证非线性迭代成功、不穿透、不丢接触、不耗散过量，也不保证较大 h 的运动轨迹准确。** 扩大 k 能减少某些接触压入，但恶化条件数；减小 tolerance 只能降低已离散方程的求解误差，不能消除几何、采样或时间离散误差。

[TimeIntegratorParams][integration]中 BE 是 1 step/1 stage，BDF2/3 使用历史，DIRK 使用多个隐式 stage。`dtStage = beta*A(i,i)*h`；stage 不是应用自行切出的多个完整子步。每个 stage 有自己的非线性 solve；高阶积分器不意味着只多更新一次速度。BDF 冷启动按 island 内最少可用历史回退：BDF2→BE，BDF3→BDF2/BE；reset/state setter 清历史的影响见 E1。[CreateIslandTimeIntegrationParams][solve] 931–1009 行。

普通物理 h 与 E2 的控制周期 H、wall time、line-search 步长 α 分别记录。line search 的 α 是状态增量比例，单位 1，不是减少物理 h；solver max iterations 也不是接触子步数。固定源码的 `make_scene_differentiable` 要求 BE，并强制使用 explicit normals；设置不支持的耗散组合会报错，Newton–Euler 惯性也不支持该导数路径。这些是本章核实的可微前提，不是梯度质量证明；完整 backward/参数导数实现留 E6。不能把可选择的所有积分器都宣称可微。[Scene 校验][scene] 3015–3028 行、[评估配置][eval]和[惯性分派][inertia]可相互核对。

## 7. 一步仿真的源码路径

从 [SceneImpl::Step][scene] 和 [mochi_step.cpp][step] 开始，沿下表读到 [mochi_solve.cpp][solve]。这是固定提交中的逻辑依赖顺序；内部有任务并行，表中相邻系统不都意味着串行 CPU 调用。

| 阶段 | 真实工作 | 阅读重点 |
|---|---|---|
| pre-step callback | 应用读取旧观测/设置控制 | 在时间推进和预处理之前；保持 E2 单次外力写入语义 |
| `PreStepEcs` | 外部速度/包围盒，历史 shift，等待 SDF，目标历史，candidate pairs，compound/island 更新 | 候选对影响分岛；不是先各自积分再补接触 |
| 每个 island 准备 | 定 DoF offsets、装配函数、preconditioner、积分方案 | `force_single_island` 可改变实际划分，不等于增加并行 |
| 每个 stage | 设 `dtStage`，算 stage-start state，必要时检测 stage-start contacts | explicit normals 与耗散基准来自这里 |
| Newton/拟 Newton | 更新当前配置→Jacobian/当前碰撞→actor/constraint/contact residual 和矩阵→线性 solve→line search | 候选几何与力在迭代中更新，不能用一次 broad phase 代替整条链 |
| stage 结束 | 分发解和收敛状态、恢复速度/历史；处理发散 | 未收敛停止可保留近似解；Diverged 有回退路径 |
| 最后 stage / post-step | 最终状态、query 更新、速度/old target 更新、统计聚合、post callback | 力数据属于该步/该 stage 的装配，不自动成为整个控制周期的平均力 |

`step(0)` 跳过 `PreStepEcs/StepEcs/PostStepEcs`，只更新 query 并清 scene solver stats，然后照常调用 post callback。其 contact 查询更新读取已有 active collision/force 数据，**不会重新执行 contact solve**。因此 E1 所说“刷新 query”不能被解释为“任意 teleport 后得到了新接触力”；新注册但从未装配的 contact query 或旧 contact cache 不能作为新力学证据。

island 是有物理耦合的 DoF/interaction 子问题，不是“每个机器人天然一个独立环境”。动态 contact 与约束会把对象连接到同一 solve；batch 环境的隔离和实际并行接口留 E5，当前不以 source 分岛结构宣称吞吐成绩。

## 8. 非线性算法、线性算法与 warm start

### 非线性层

[NonLinearSolverParams][nonlinear]暴露 Newton、BFGS、SR1。概念上求 `R(x)=0`：`H_k Δx=−R_k`，然后 `x←x⊕αΔx`；这里 `H` 可是精确导数、重用矩阵、拟 Newton 更新或投影近似。源码先解 `H dx=R` 再取负增量，不存在符号冲突。[NewtonSolver::Solve][newton] 625–867 行。

- Newton 的 `d_residual_assembly_period>1` 会跨迭代复用导数。
- BFGS/SR1 从真实装配矩阵起步，随后低秩更新，并按周期或失败重启；这不等于选择另一个接触模型。
- `psd_proj_mode` 决定总是、永不或失败重试时投影；`fitted_saturation_hessian` 可分别作用于 contact friction、joint friction、constraint saturation。
- 线性失败或 line search 无改善可触发重新装配、fitted Hessian、PSD 重试；可选 gradient descent fallback。最后一次重试仍可能接受最后的 line-search iterate，不能把“已启用线搜索”写成严格保证每次下降。

line search 的 ResidualNorm 比较 residual norm；Simple/Armijo/Wolfe 使用 merit 或其条件；ArmijoOrResidualNorm 接受两类条件之一。只在真实梯度和适当光滑性/方向等假设下，经典能量线搜索结论才适用。本固定源码默认 enum 是 Newton、ResidualNorm、PSD Always；这说明**源码默认配置**，不证明某个运行对象仍保持默认。

### 线性层

[GetIslandNewtonParams][simulation]的 `AUTO` 规则是 **island DoF≤50 选 LDLT 并取消 preconditioner，否则选 CG**，没有在这里自动选择 GPU。手工 solver 必须符合矩阵性质和构建能力：

| 方法 | 理解重点/适用条件 |
|---|---|
| CG | 要求 SPD；迭代中做矩阵向量乘，配合预条件器 |
| GMRES | 可处理非对称系统；有 restart 子空间大小 |
| MINRES | 对称系统，可用于对称不定情况 |
| LDLT / LU | 直接分解；此实现文档明确无 pivoting，病态/不定情形有稳定性边界；不是由迭代 tolerance 控制精度 |
| CUDA、AugmentedCG、AsyncCG、ParallelCG 等 | 构建、依赖、矩阵/预条件器有附加限制；部分 experimental，ParallelCG 明确非确定性 |

实际分派和限制见 [LinearSolverParams][linear-params]、[LinearSolver][linear]及[Scene 配置校验][scene]。不要从有 CUDA enum 就推断当前 binary 启用 CUDA，更不要推断整个接触/装配/渲染都在 GPU。

`PerActor` 预条件器利用 actor 分块；Jacobi/BlockJacobi/SSOR 等是不同近似。对迭代方法，令线性 residual `ρ=b−Az`，可按 `‖ρ‖₂`、`‖P⁻¹ρ‖₂` 或 `sqrt(ρᵀP⁻¹ρ)` 检查；P 是预条件器，别与动力学质量 M 混淆。norm 配置只作用于声明支持的 CG 类；GMRES/MINRES/AugmentedCG 使用 residual L2，直接分解没有迭代 stop criterion。

非线性层的 `linear_tolerance_strategy` 可采用 Constant 或 Eisenstat–Walker。EW1/2 会覆盖配置的固定 linear `rel_tol`，EW3 将它作为下界；内层不必每次同样精确，目标是让外层有效收敛。不能只记录“容差 1e-9”而省略它属于哪个层、哪个 norm、哪个 strategy。

“warm start”需拆开说：stage 的状态/历史是非线性初值来源；island 保存 preconditioner recycling manager；BFGS/SR1 在一次 solve 内保留更新。但该 Newton 循环每次线性求解前明确 `dxSolve.SetZero()`，不是直接把上步线性增量当初值，更不是经典约束冲量 solver 的 λ 缓存热启动。改变拓扑、state setter 或重新分岛后，历史和预条件器是否有效不能凭同一个 scene 名判断。

## 9. 残差、终止、发散与可报告证据

非线性收敛不是“已跑 max_iter 次”。固定源码有两种 convergence mode：

- **Global**：每个 island 的未加权 `‖R‖₂ ≤ abs_tol`，或迭代后 `‖R‖₂ ≤ rel_tol ‖R0‖₂`。混合 force/torque 或模型尺度变化时，raw norm 没有单一普适的“牛顿”量纲。
- **PerActorWeighted**：每个 actor 的 `‖R_a‖_W=sqrt(Σ w_i R_i²)` 分别满足绝对或相对条件，且全部 actor 满足才收敛。权重按惯性/特征负荷归一化；刚体平移特征力为 `m a_ref`，`a_ref=max(‖g‖,1 m/s²)`，转动特征力矩使用世界惯量平方根。零惯性 fallback 用单位权重，失去这种物理归一化；准静态问题源码建议 Global。[权重实现][weights]、[收敛判断][newton] 45–173 行。

因此 “abs_tol=1e-9” 在不同模式下含义不同；相对 tolerance 还依赖本次 solve 的初始 residual。源码默认 PerActorWeighted，与某历史报告写的 tolerance 数字仍不是同一证据。

| `ConvergenceStatus` | 触发/含义 | 读者应该保留的信息 |
|---|---|---|
| `CONVERGED` | 先检查 residual 收敛准则，满足则返回 | 配置、初值、mode、实际 residual；不等于连续物理真值 |
| `STOPPED` | max iterations、时间预算、raw 线性增量过小、可选无改善等 | 这是未达到所选残差收敛条件的停止，仍可有近似状态 |
| `DIVERGED` | explosion control 下 raw L2 超绝对/相对阈值或非有限 | 刚体 stage 回到上一步 pose、velocity 清零；不能当成功积分 |
| `NONE` | 尚未求解、零步刷新、没有动态 actor 等 | 不能把 residual=0 视为通过物理解算 |

检查顺序是 residual → iterations → elapsed → raw step norm → 可选 no improvement；`rel_step_tol` 用线搜索缩放前的线性增量，发散和停滞的 norm 也不会随加权收敛 mode 自动改成 weighted。时间预算在迭代检查点判断，不能当严格 realtime 截止期。[停止条件][newton] 175–248、302–316 行；[刚体回退][rigid] 344–359 行。

`scene.get_solver_stats().residual_norm` 是跨 islands、stages 的汇总：各 stage 的 per-island residual norms 做 L2，再跨 stage RMS；它不是最大 actor weighted residual。`convergence_status` 是动态 actor 最坏状态，`max_non_linear_iters` 是所有 stage/island 最大值。不要拿一个 scene 汇总 scalar 与 per-actor abs_tol 直接比较来替代原生状态。`actor.get_convergence_status()` 有单 actor 的状态入口；详细线性 iteration 与 stop reason 存在内部 `NewtonSolverStatus`，不应虚构 Python `get_stop_reason()`。[统计 API][api] 7326–7374 行、[内部状态][solver-status]。

## 10. 力、冲量和采样时点

### 注册什么，得到什么

以下都按 [QueryType/Actor/Constraint][api] 的实际对象使用；query 需在对应步之前注册、保持 handle，有支持限制，用完取消。force/contact 类不支持立即重新装配；`register_query_and_compute` 仍可注册，但不支持的即时计算会跳过。[query 注册实现][query]。

| query / getter | 返回量与基准 | 常见误解 |
|---|---|---|
| `CONTACT_POINTS` / `get_contact_points_world()` | 每个 sample 的 actor_a/b、world positions/normal、force [N]、distance [m]、int_weight | force 已乘积分权重，不能再乘面积 |
| `TOTAL_CONTACT_FORCE` / `get_contact_force_world()` | 作用在该 actor 的接触合力 [N]，world frame | 不包含重力、控制命令或所有 constraint 力 |
| 同一 query / `get_contact_torque_world()` | 刚体或 articulated link 的 world 力矩 [N·m]，**关于质心** | 不是关于 URDF link/root 原点 |
| 同一 query / `get_contact_force_from_actor_world(other)` | other 对该 actor 的合力 [N] | other 必须对应原生 actor 身份，不能把 parent 当所有 links 的隐式聚合 |
| `NODE_CONTACT_FORCES` | world 节点力，按离散插值分配 | 不支持杆等列出的类型；不能按 sample index 直接匹配 mesh node |
| `CONSTRAINT_FORCE` / constraint `get_force()` | 按 actor，再按其受约束 DoF 排列的广义力 | 单个数组可混 N 与 N·m，不能直接当三维 world wrench |
| `ARTICULATED_CONTROLLER_FORCE` | pose controller 的广义力 | 不是 JSC 命令、不是接触合力 |

contact force queries 需要 contact sample points，far-SDF 模式等不支持；先 `actor.is_query_supported(...)`。只拿到一个合法 collider 不保证所有观测都存在。query span 与对象仍需遵守 E1 的借用/复制规则。

`ContactPoint.force` 始终是 **B 对 A**，normal 指向 B 外部；当前被查询 actor 可能是 A 或 B，返回列表没有为调用方自动把每条 force 翻成同一方向。内核 total-force 路径会按 colliding/collider role 取正/反力，保留 other entity 分组；自己合成须同样核对角色，避免双计。`int_weight` 是 sample 的空间 quadrature 权重，不是时间权重。[world 查询装配][force-query]。

### 世界力矩、传感器 frame 与冲量

对作用在位置 p_i 的世界力 F_i，质心 c 处 `τ_c=Σ(p_i−c)×F_i`。转到原点 o、姿态 R_WS 的传感器坐标：

$$F_S=R_{WS}^T F_W,\qquad
\tau_{o,S}=R_{WS}^T\left(\tau_{c,W}+(c-o)\times F_W\right).$$

这是同一瞬时/离散采样点的 wrench 转换；不能只旋转 torque 而遗漏移点项，也不能给没有唯一刚体质心的柔体对象套用同一 getter。内部 total query 正是用 `sample_position−rigid_state.translation` 积分力矩。[UpdateQueryActorContactForces][force-query] 2921–3049 行。

这里读出的单位是力，不是 impulse。冲量 `J=∫F dt` [N·s]；BE 下可用该步离散力与 h 构造相应的离散近似，但 `h F_end` 不等于已知连续真实冲量。多个子步/控制周期的平均力需明确采样权重 `F̄=Σ h_j F_j/Σ h_j`；多 stage 高阶积分的最终查询也不能未经证明当作整个步长的积分平均。源码 query 从最近 contact assembly 的 `forcePerUnitArea` 乘空间权重并变换，没有另做时间积分。

### 有力值不等于有有效结果

正时间 `step` 完成后、下一次修改/步进前复制数据，并同时记录 scene/actor status、时间、h、积分方案和 query 何时注册。已知固定实现遇到 `DIVERGED` 时清空 contact force query，而原生 API 文档也提醒结果可能 unavailable/stale；因此**零接触力既可能代表无接触，也可能代表回退/清空**。不要把清空值写成“发散后接触自然消失”。[query 清空分支][force-query] 2694–2723、2921–2943 行。

[read_contact_after_step.py](../examples/read_contact_after_step.py) 是原创原生读取片段：它要求调用者提前注册 CONTACT_POINTS/TOTAL_CONTACT_FORCE，并由已有应用完成正时间步；只复制 force/torque/角色/统计，无 scene 创建、无 step、无实验。片段拒绝 NONE/DIVERGED，保留 STOPPED 标签而不冒充收敛。示例的返回字典只是本次教学快照，不是跨引擎 schema。

## 11. 从异常现象定位到配置层

| 读者看到的问题 | 优先核对的链 | 不能直接得出的结论 |
|---|---|---|
| 接触有可见压入 | 单位/scale→SDF/samples→threshold/smoothing→组合 k→h→残差状态 | 不能只凭穿透截图给引擎排名 |
| 摩擦设了却不生效 | 两边同一机制的系数→几何平均→normal/alignment→falloff→实际相对运动 | 一方参数非零不代表组合非零 |
| 总 force 比“μFn”大 | 力的方向/法向基准→viscous 附加项→多方向/多 sample 聚合 | 不能把纯 Coulomb 上限套到全部接触力 |
| 调小容差仍有偏差 | tolerance 层/mode→FP精度→离散模型与 h→geometry | solver tolerance 不是全部建模误差 |
| 物体突然停住/力归零 | actor/scene DIVERGED→刚体回退→query 清空 | 不能用平稳图像证明稳定通过 |
| GPU solver 选不了 | binary 构建能力→设备→矩阵/预条件器条件 | API 有枚举不代表当前构建能力 |
| step(0) 后有旧力 | active collision/force cache→是否真正正时间装配 | query refresh 不是重新求接触 |

这些是源码驱动的阅读诊断，不是本仓库新增的实验计划或评分器。后续用 DexLab 的原始配置、失败记录和工况复用材料，再判断具体运行现象。

## 12. 带答案的阅读练习

1. **μ_A=0.2、μ_B=0.8 的组合值是多少？B 静态会改成 A 吗？** 0.4；静态例外作用于 penalty/falloff，不作用于 μ。
2. **A 的 Coulomb 非零、viscous=0；B 正好反过来，得到什么摩擦？** 两个几何平均分别为零，不会自动把不同机制相加配对。
3. **改静态地面的 k 没有预期效果，应先查哪里？** `CombineContactParams` 静态分支取 colliding k；再查地面的 threshold/smoothing 等仍继承 collider 的字段。
4. **k=10⁹ Pa/m、有效接触面积 10⁻⁴ m²，对应线性区的平移斜率是多少？** 10⁵ N/m。还需考虑 smooth ψ、距离梯度、sampling 和低维修正；不能直接称每点 stiffness=10⁹ N/m。
5. **`C1Regularized` 在 r=ε/2 时的 Coulomb 幅值比例是多少？** `2(1/2)−(1/2)²=3/4`；不是 1/2，也不是严格 sticking 的任意力。
6. **normal damping 系数能当 restitution=0.5 直接填吗？** 不能；单位 s/m，CoR 需给特征速度做原生拟合，结果仍依赖速度和离散情况。
7. **BE、Newton、CG 三个名字分别控制什么？** 时间离散、外层非线性迭代、内层线性系统；单独改其中一个不等于另外两个一起改变。
8. **80 DoF island 的 linear AUTO 是 LDLT、CG 还是 CUDA？** 该固定源码选 CG；≤50 才选 LDLT，不按有 GPU 自动选 CUDA。
9. **设置 linear rel_tol 后为何不等于每轮阈值？** EW1/2 自适应策略覆盖固定值，EW3 用其作下界；还需查 norm 与 solver 类型。
10. **max_iter 到达但 residual 未达标，应记 Converged 吗？** 不，应记 STOPPED，并保留近似状态与误差。DIVERGED 另外可能回退。
11. **Global abs_tol 与 PerActorWeighted abs_tol 能直接横比吗？** 不能；前者混合 raw 分量，后者按 actor 特征负荷归一化，零惯性又有 fallback。
12. **ContactPoint.force 还要乘 int_weight 或除 h 吗？** 都不要；它已是权重后的 N。冲量需要时间积分；int_weight 是空间面积/长度。
13. **查询 actor 恰好是 B，ContactPoint.force 是作用在 B 上吗？** 不是，字段固定为 B 对 A；需要角色换号或使用原生 total getter。
14. **τ_COM 转 wrist sensor 时为什么仅旋转不够？** 两个原点不同时还需 `(c−o)×F` 移点项，然后统一旋转。
15. **step(0) 后 scene residual=0 可以用来宣布收敛吗？** 不可以，该分支把 stats 清成 NONE，且没有新 contact solve。
16. **源码默认 Newton 和几何平均能否关闭 DexLab 历史 #124？** 不能；还需要历史 wheel/core/binding 身份、实际配置与执行链证据。源码课程与原批次验收是两个范围。

[本章验收记录](validation-e3.md)列出检查和限制。下一项优先 E4 传感器/渲染，补足 A6 并承接本章 B5 的力观测；E6 已获得本章先修，可另行展开特色、可微和扩展；E5 仍等 E4。暂不开展新的原生实验。

[api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[simulation]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_simulation.cpp
[scene]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp
[step]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_step.cpp
[solve]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_solve.cpp
[rigid]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_rigid.cpp
[inertia]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/rigid_body_assembly.h
[experimental-binding]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/src/generated/mochi_physics_pybind_experimental.generated.cpp
[contact-params]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_params.h
[contact]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.cpp
[contact-header]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.h
[combine]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.h#L867-L934
[contact-types]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_types.h
[contact-law]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h
[point-cloud]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_point_cloud_contact.cpp
[filters]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact_filter.h
[filter-example]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_contact_filtering.py
[activations]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/activations.h
[eval]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/eval_params.h
[integration]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/integration/integration_utils.h
[nonlinear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/nonlinear_solver_params.h
[newton]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/solvers/newton_solver.cpp
[linear-params]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/linear_solver_params.h
[linear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/linear_solver.h
[weights]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_actor_convergence.cpp
[solver-status]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/newton_solver_status.h
[query]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_query.cpp
[force-query]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.cpp#L2694-L3049
[articulated]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_articulated_body.cpp
