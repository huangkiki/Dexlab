# E3 · 接触、求解器与力观测

本章从一个问题出发：`get_contacts()` 给出的力，究竟经过哪些模型、方程和数值选择才得到？沿 **材料与过滤 → 几何接触 → 约束行 → 加速度求解 → 积分 → 力读回** 追踪 Genesis 1.4.3 的实际执行路径，覆盖 A4、B1–B5，并补齐 B0 的刚体动力学。

先修 [E1 状态与时间](modeling-state-time.md)、[E2 驱动与机器人](control-robotics-tasks.md)：会区分q/v、DOF与link frame，知道Δt与子步h、驱动力与状态setter不同。数学先修为矩阵乘法、二次型、梯度和牛顿第二定律。这里固定官方提交 `216a708e06124595521a9d36a51fae5393fd4ff8`，不是当前最新版的通用承诺。

**验收是源码、公式、链接与Python语法检查；未运行Genesis、接触实验或性能测试。** 本章完整展开原生刚体路径，并给出其他物理/耦合分支的入口和不适用边界；MPM/SPH/PBD/FEM/IPC内部专门推导留给E6。后续实证复用DexLab。[DexLab #125](https://github.com/huangkiki/Dexlab/issues/125) 的历史批次算法仍待核实，不能用此提交的默认值倒填历史记录。

## 1. 先确定究竟运行哪个求解路径

### 1.1 三类选择各司其职

| 层 | 原生字段 | 决定什么 |
|---|---|---|
| 几何与接触模型 | `enable_collision`、`use_gjk_collision`、`friction_cone`、`contact_resolution`、材料friction/sol_params | 有没有约束，约束方向及法向/摩擦如何耦合 |
| 约束数值求解 | `constraint_solver`、`iterations/tolerance`、`ls_*`、`noslip_*` | 如何逼近当前子步的约束解、何时停止 |
| 时间离散 | `integrator`、`SimOptions.dt/substeps` | 由力/加速度更新q与v的方法及步长 |

`elliptic`不是求解算法；`Newton`不是积分器；`noslip_iterations=0`只关闭后处理。枚举写入 `RigidOptions` 后，还要读 `RigidSolver.__init__ → build → _build_static_config` 的条件解析，以及 `ConstraintSolver.resolve/func_solve_body` 的执行分派。[选项][options]、[解析][resolve]、[静态配置][config]、[主求解分派][dispatch]

本提交字段默认：Newton、25次主迭代、pyramidal、approximate_implicitfast、noslip=0。`tolerance=None` 到build时才变成FP32的1e−6或FP64的1e−9（非MuJoCo兼容）；兼容模式分别1e−5/1e−8。它们是**条件默认值**，不是某次报告的实测配置。[默认字段][defaults]、[build解析][build]

| friction_cone / solver / compatibility | `contact_resolution=None` 的结果 | `impratio=None` 的结果 |
|---|---|---|
| elliptic + Newton + 非兼容 | signorini | 100 |
| elliptic + CG + 非兼容 | convex | 100 |
| pyramidal，或任一兼容模式 | convex | 1（兼容或pyramidal） |

显式要求signorini但不满足第一行条件会报错。elliptic+noslip也被拒绝；rolling必须同时启用torsional。不能先改一项，再假定其余默认仍与旧场景一样。[条件解析][resolve]、[组合检查][defaults]

### 1.2 原生最小配置片段

以下是**未执行**的配置阅读例，数值仅为说明字段，未为任何任务调参。真正记录一个场景时还须保存资产、材料、耦合器、精度/后端和build后的解析结果。

```python
import genesis as gs

rigid_options = gs.options.RigidOptions(
    constraint_solver=gs.constraint_solver.Newton,
    friction_cone=gs.friction_cone.elliptic,
    contact_resolution=gs.contact_resolution.signorini,
    integrator=gs.integrator.approximate_implicitfast,
    iterations=50,
    tolerance=1e-8,
    ls_iterations=50,
    ls_tolerance=1e-2,
    noslip_iterations=0,
    impratio=100.0,
    constraint_timeconst=0.01,
    use_hibernation=False,
)
```

Python层组织Scene/Entity/solver；实际数值kernel使用Quadrants。CPU/GPU、精度、约束稀疏性、是否可微及场景拓扑还决定执行布局：CPU或可微路径偏向monolith；适合的GPU路径可在monolith与decomposed graph之间分派。两者共享模型/迭代逻辑，不能把GPU graph叫成第三种物理算法，也不能从源代码存在推断某次运行实际选择哪一臂。[配置][config]、[monolith][dispatch]、[graph臂][decomposed]

`sparse_solve`的实际值还受CPU gate约束；GPU会忽略请求的稀疏选项。岛、稀疏Jacobian、Hessian分解和设备kernel布局是不同概念。[实际稀疏选择][config]

## 2. 一子步做了什么：从动力学到接触解

`Scene.step()` 的callback/recorders顺序见E2；`Simulator.step()` 再循环substeps。纯刚体且不求梯度时走刚体快路径；其他情况按coupler preprocess → 各solver pre → couple → 各solver post。外层结束才清刚体外力并更新传感器。[Simulator][sim-step]

对普通原生刚体约束路径，每个h的顺序为：

1. 按缓存失效标记刷新FK/速度；由惯量、关节与速度构造质量矩阵和自由动力学。
2. 清约束、加入equality；几何检测生成接触。
3. 建岛与接触排序；按 **equality → DOF frictionloss → contact → joint limit** 布置约束行。
4. warm start初始化，Newton/CG迭代；写回qacc与约束广义力，必要时noslip，再还原接触世界力。
5. 更新笛卡尔加速度；按积分器处理隐式阻尼；更新速度/q。通常刷新新姿态/速度，兼容模式可推迟刷新。

来源：[刚体substep][substep]、[装配次序][assembly-order]、[求解后处理][post-solve]、[积分前后][step-halves]。`enable_collision=False`不等于禁用equality/限位；`disable_constraint=True`则绕过这组约束响应。仅做collision detection得到几何信息，也不等于已经求出有效接触力。

### 2.1 B0：广义动力学与数据字段

在一个子步冻结q、v及几何，示意写为：

$$
M(q)a=f_{smooth}+J^T\lambda,
\qquad f_{smooth}=f_{passive}-f_{bias}+f_{applied}.
$$

M是广义质量矩阵，a是广义加速度，λ是约束行的力变量。标量平移DOF的广义力单位N，标量旋转DOF为N·m；矩阵块的量纲随坐标组合改变，不能把整矩阵每格都标kg。四元数配置仍由广义速度映射积分，不是q所有槽位直接相加。[质量矩阵][mass]、[自由力/加速度][smooth]

| 数学量 | 原生存储/函数 | 阅读要点 |
|---|---|---|
| 惯量与运动子空间 | `dyn_info.links`、`dyn_state.dofs.cdof_ang/cdof_vel` | E1的惯量frame、root COM空间量，不能与E2 Jacobian行序混用 |
| M与分解 | `rigid_info.mass_mat/mass_mat_L/mass_mat_D_inv` | composite-rigid-body装配；按运动树/质量块LDLᵀ分解与回代，不在每步显式求逆 |
| 自由驱动力 | `qf_applied/qf_passive/qf_bias/qf_smooth`、`acc_smooth` | applied含E2驱动限幅；外部/耦合wrench也经link力与bias链参与，不只是一列电机力 |
| 约束 | `constraint_state.jac/aref/diag/efc_D/efc_force` | J、参考加速度、正则R及D=1/R、行力 |
| 解与warmstart | `qacc/qacc_ws`、`qfrc_constraint` | qfrc=Jᵀλ；qacc_ws是上次求解加速度，不是接触ID到冲量的字典 |

M还包含armature。`approximate_implicitfast`在**约束求解前**向质量矩阵对角加h乘被动阻尼，以及相应控制模式的−h·act_bias[2]。因此该路径求解使用的是被修改的有效矩阵；不能把所有模式里的 `mass_mat`无条件看成仅由几何惯量决定的M。[前向动力学][dynamics]、[armature/阻尼项][mass-correction]、[LDLᵀ回代][mass-solve]

## 3. 碰撞不是接触力：表示、过滤和容量

### 3.1 表示与检测

可视mesh和collision geom可不同。刚体collider先更新AABB，做broad phase，再按几何种类执行narrow phase，最后压缩/裁剪/排序接触。broadphase的sweep-and-prune与all-vs-all选择只筛候选，不生成摩擦力。此处SAP意为 **sweep and prune**，与第10节的 **SAPCoupler** 不是同一个算法。[检测流水线][detection]、[broadphase分派][broadphase]

通用凸体有GJK/MPR分支及精修/多接触；plane/box等有专用路径，非凸体可走顶点对SDF，terrain另有路径。`ccd_algorithm`在此源码注释指convex collision detection，不能因缩写CCD就宣称做了连续碰撞时间求解或防穿透保证。非凸SDF的分辨率、碰撞网格近似和接触patch都可能改变有效接触位置与数量。[collider配置][collider-config]、[凸体分支][narrow-convex]、[非凸/terrain入口][narrow-other]

接触点是几何算法给出的代表点，不是实测压强分布。pruning会改变点集合和约束行；`max_collision_pairs`、候选接触容量、post-pruning `max_contacts` 是不同预算。不能靠提高主迭代数修复丢失的几何约束；超出受检查预算会走错误处理，必须保留错误，不能把被截断集合当全接触。[容量计算][capacity]、[约束预算][constraint-init]

### 3.2 过滤的实际条件

公共入口包括morph的 `collision`、原生primitive的 `contype/conaffinity`，以及RigidOptions的self/adjacent/neutral collision选项。[morph字段][morph-filter]

普通全局mask通过条件为：

$$
(c_A\mathbin{\&}a_B)\;|\;(c_B\mathbin{\&}a_A)\ne0.
$$

但源代码还区分导入资产的local mask：仅同entity或不存在local mask的pair应用该拒绝条件；跨entity的local mask不应被误解为全场景隔离层。build时也排除同link、两固定link、weld以及特定IPC委派pair；self关闭、adjacent检查、neutral初始重叠检查可继续删pair。动态weld还有运行期过滤。[build过滤][filter]、[运行期过滤][runtime-filter]

排错顺序是：确认collision几何存在 → 实际pair是否被过滤 → AABB/narrow phase是否给接触 → 接触是否进入约束 → force是否为本次求解值。把friction调大无法恢复一个已过滤pair。

## 4. 材料组合与柔顺：不是一个“硬度”旋钮

### 4.1 每个接触怎样合成参数

设A、B几何的基础滑动摩擦为μ_A/μ_B，每环境friction_ratio为s_A/s_B，原生 `func_set_contact` 为所有接触写：

$$
\mu=\max(\mu_As_A,\mu_Bs_B,0.01),\qquad
\mu_{spin}=\max(\mu_{spin,A}s_A,\mu_{spin,B}s_B),
$$

rolling同样取最大值。七个 `sol_params`先逐分量均值，接着将混合timeconst下限设为2h。不是几何平均、相乘或较软一方优先。[组合实现][mix]

滑动μ无量纲；torsional与rolling系数单位为**m**，使 `μ_spin*f_n`成为N·m。只设材料值还不够，场景必须启用相应维度。`set_friction()`范围[0.01,5]；`set_friction_ratio()`作用于选中link的所有geom且可逐环境变化，组合中也作用于spin/rolling。[材料定义][material]、[原生setter][friction-api]

纸上例子：A基础μ=.2、ratio=2；B基础μ=.6、ratio=1；接触μ=.6而非.4、.12或.5。只改A到.1不会把pair降到.1，因为B仍主导。即使ratio使两者滑动摩擦为0，原生pair仍有.01下限。

`coup_friction/coup_softness/coup_restitution`是跨solver耦合字段，不能代替这里的刚体摩擦/sol_params；普通刚体接触的回弹不能通过把 `coup_restitution` 当成原生刚体恢复系数来解释。[材料分工][material]、[Legacy响应][legacy-response]

### 4.2 七个参数对应什么方程

`sol_params=(timeconst, dampratio, dmin, dmax, width, mid, power)`。针对法向位移，timeconst单位s、width单位m；其余无量纲。旋转/关节约束的width必须随其误差坐标解释，不把同一数值当统一米制距离。[参数函数][impedance]

以下推导假设timeconst、dampratio、width均正，且 `0<dmin≤dmax<1`、`0<mid<1`、power≥1；调用方仍应核实参数相互关系，不能仅凭单个字段被合法化就认定模型合理。令d≥0为penetration、r=−d，速度u=Jv；阻抗I(r)由 `x=|r|/width` 进入以mid/power构成的分段曲线，在dmin与dmax间截断，x>1取dmax。参考加速度为：

$$
b=\frac{2}{d_{max}t_c},\quad
k=\frac{1}{d_{max}^2t_c^2\zeta^2},\quad
a_{ref}=-b u-kI(r)p.
$$

法向行p=−d；elliptic切向/旋转摩擦行p=0，仅保留速度项，同时沿用法向深度的阻抗。这里ζ是字段 `dampratio`：按执行公式它改变k，而b不含ζ。不能仅按名字说“减小dampratio就是减小速度阻尼”；实际回弹还受时间离散、正则化、质量与接触集合影响。width宜严格为正以使上式有定义，不把被允许输入的边界值自动当可靠模型。[公式实现][impedance]、[接触装配][contact-rows]

几何timeconst先按默认/合法化处理，**混合后**才floor到2h；joint/equality不混合，在setter就floor。负timeconst的直接刚度参数化在此版本不支持，会警告并回到默认语义。dmin/dmax/mid被限制在[.0001,.9999]，power下限1；dampratio必须正。记录输入值还不够，还应记录实际生效值。[合法化][sanitize]、[定向setter][sol-setter]

原生入口是 `scene.rigid_solver.set_sol_params(..., geoms_idx=...)`，或用joints_idx/eqs_idx，三类一次只选一类；不是 `entity.set_contact_stiffness()`。geom参数共享、不按环境batch；joint参数取决于batch_joints_info，equality参数按环境保存。`set_global_sol_params`更宽，不能把它当只改所选接触。[setter契约][sol-setter]

## 5. 从接触点到约束行与摩擦锥

对每个点，源码normal由B指向A。选两个单位切向t₁/t₂，J通过接触点速度与角速度投影构成，并沿两个link的祖先DOF链累加；共同祖先要合并支持索引。不能把每个接触当独立的两粒子弹簧：多个点共享机器人DOF，Jᵀλ把它们耦合起来。[行方向/投影][contact-rows]

### 5.1 Pyramidal与elliptic

| 形式 | 默认滑动接触的行 | 加spin / 再加rolling | 含义 |
|---|---|---|---|
| pyramidal | 4条 `−n ± μt₁`、`−n ± μt₂` 混合行 | 6 / 10行 | 每条非负行力共同产生法向和切向力 |
| elliptic | normal、t₁、t₂共3行 | 4 / 6行 | 坐标行不混合，求解时按接触块耦合 |

无spin/rolling时，pyramid的可行切向截面是 `|f_t1|+|f_t2|≤μf_n`，elliptic为圆盘 `||f_t||₂≤μf_n`；两者方向依赖不同。pyramid不只是把椭圆锥的名字换掉，行数、Jacobian和正则都变了。零spin/rolling系数对应的额外行在源码中被清零，避免产生虚构法向支撑。[方向分支][row-directions]

### 5.2 正则化R不是残差阈值

elliptic法向行以两个link的平移invweight和W构成 `R_n=W*(1−I)/I`，切向 `R_t=R_n/impratio`；再做EPS下限，`efc_D=1/R`。convex分支的spin/rolling还按μ²/μ_spin²等调整正则。pyramid的滑动行则用 `μ_reg²=μ²/impratio`，`R=2 μ_reg² W(1+μ_reg²)(1−I)/I`。这些关系按原生公式成立，不是用户材料Young模量。[正则装配][contact-rows]

因此提高impratio在elliptic中主要改变摩擦行，在pyramid中会同时影响混合法向；改变invweight、质量或armature也会影响收敛后的柔顺解。`get_links_invweight()`是正则化相关权重，不是某一接触方向精确的 `J M⁻¹Jᵀ`。[invweight说明][invweight]

### 5.3 “signorini”与“convex”仍须分开

理想刚性非穿透常写gap≥0、f_n≥0、gap·f_n=0。这里的 `signorini` **不是宣称逐步严格满足这个硬互补条件**：它仍使用前述软参考加速度与正则化，名字区分的是摩擦与已发展法向力之间的数值处理。

- **convex**：接触是一个耦合锥程序；elliptic按top/bottom/middle三区计算力、cost与Hessian，中区含法向—切向交叉曲率。切向需求可影响法向解；不能将normal先固定，再单独clamp摩擦，仍称为同一算法。
- **signorini**：法向按自己的单侧二次项产生力；每轮锁存法向载荷ℓ，滑动、spin、rolling各块的半径分别为μ_block·ℓ。每个块为粘着二次段和饱和段：若D||e_t||≤半径，则f_t=−De_t；否则f_t=−半径·e_t/||e_t||。半径在该轮线搜索中固定，下一次行更新重锁存，非收缩振荡时用半步。它是逐次更新的近似，不能用一次固定凸目标的收敛直觉替代。

signorini的各摩擦块分别限幅；convex的旋转与平移在同一椭球块中耦合。这也是相同μ、相同行数仍可能产生不同响应的原因。有限迭代下ℓ可能尚未等于最终法向力，不能宣称始终精确满足以最终f_n为半径的极限条件。[cone分类与块公式][cone]、[重锁存][relatch]

## 6. Newton、CG与迭代停止：求的不是零穿透

设a₀=`acc_smooth`、e=Ja−a_ref，R为上一节正则、D=R⁻¹。冻结该子步M/J/R后，普通凸路径的加速度目标可示意为：

$$
\Phi(a)=\tfrac12(a-a_0)^TM(a-a_0)+\phi(e),\qquad
\nabla\Phi=Ma-f_{smooth}-J^T\lambda.
$$

φ不是所有行同一个平方：equality用二次项，普通单侧行用负半轴二次项，DOF frictionloss用饱和的Huber型项，elliptic以接触块处理。`active`在这里指**逐行二次项是否活动**；椭圆锥中区有力但active=False，因为它由块代价处理。用active计数当“真实接触数”会错。[cost/力更新][objective]、[分段行力][row-force]、[梯度][gradient]

这是数值加速度目标，量纲可表现为能量/时间²，不能直接叫系统势能、耗散功或接触深度平方。signorini只在锁存半径的一轮内使用相应目标，跨轮目标会变。

### 6.1 每次迭代做什么

**Newton**从梯度求方向 `p=−H⁻¹g`。无耦合锥的活动二次行有 `H=M+Jᵀdiag(D·active)J`；椭圆锥中区另加块Hessian，不能只用这条对角公式。Cholesky求解按岛做；active翻转时可rank-1更新/降阶，退化时重新分解，signorini等分支会直接重建。名称为Newton不代表执行了全系统非线性隐式时间步。[迭代与因子维护][iteration]

**CG**是非线性共轭梯度方向更新，`Mgrad=M⁻¹g`由质量矩阵分解回代，方向带Hager–Zhang系数和保护下限。它不是用CG解Newton的Hessian，也不是简单的逐接触投影迭代。[梯度预条件][gradient]、[系数/终止][exit]

共同线搜索先沿方向括住导数换号区间，再做三候选细化，受 `ls_iterations` 与导数容差限制；`ls_tolerance`结合主tolerance、搜索方向长度、梯度/惯量尺度和舍入噪声，不是直接的米或牛顿阈值。不要把主迭代50×线搜索50理解成2500个物理子步。[线搜索状态机][linesearch]、[初始容差][ls-init]

### 6.2 Warm start、岛与终止的真实含义

非兼容模式有约束且 `is_warmstart=True`时使用qacc_ws，否则a₀；兼容模式比较两者cost再取更低者。初始化可通过证书直接判断岛已收敛并执行0次迭代。reset会清相应warmstart语义；仅保存q/v与保留全部求解缓存不是同等恢复。[初始化][warmstart]、[reset][constraint-reset]

岛按可动树、接触与约束连接关系分组，固定地面不等于把全部独立物体合成一个巨岛；每岛有自己的方向、线搜索及收敛状态。已收敛岛停止，其他岛继续，batch中“最难的环境”不要求所有环境一直改解。CPU sparse和GPU tiled只是利用这些块的不同方式。[建岛][islands]、[每岛迭代][iteration]

令S为该岛质量块的trace、τ=S·tolerance，g为梯度，d=g·Mgrad，ΔΦ为线搜索正改进：

| 分支 | 迭代继续条件的核心 |
|---|---|
| 常规退出基线 | 既非 `||g||≤τ`，也非 `0<ΔΦ<τ` |
| 非兼容Newton凸路径 | 基线还要求 `max(d/2,0)≥τ` |
| signorini | 必须同时达到 `||g||≤τ` 与 `d/2≤τ` 才因该判据停止；不沿用小改进就停 |
| 其余停止原因 | 线搜索无法推进、预算耗尽、无约束/无awake工作等执行条件 |

实际S由岛的M对角累加；不要照抄build附近“free-motion cost”注释，把它当停止函数真正使用的尺度。初始化证书还要求对应decrement条件，Newton/signorini另查梯度。表中是代码判据，不是穿透量/力误差上界；转动和平移坐标混用时尤其不能将tolerance当统一物理精度。[S的装配][island-scale]、[实际退出与证书][exit]、[预算/空工作][dispatch]

源码中的 `iterations` 是上限，达到上限不保证满足判据。提高到更多次只能更充分求同一离散/正则模型，不能消除网格近似、材料不准或模型柔顺本身造成的穿透。

### 6.3 Noslip是独立后处理

开启noslip后，在主解之后对约束力做矩阵自由的Gauss–Seidel型扫行，使用 `A=J M⁻¹Jᵀ` 的局部块和 `qacc=a₀+M⁻¹Jᵀf` 更新；并行颜色仅把互不共享质量块的行放一起。停止用按meaninertia和岛DOF数归一的改进与noslip_tolerance，另有noslip_iterations上限，再写回加速度/广义力。它是抑制漂移的另一阶段，不是将μ设无穷；此版本不允许elliptic或可微路径配noslip。[扫行/停止/写回][noslip]、[选项检查][defaults]、[可微检查][diff-limits]

## 7. 积分器、子步与精度：时间推进另有假设

令h=Δt/substeps。对常规非休眠标量joint，最终更新使用 `v_next=v+h*a`，再 `q_next=q+h*v_next`；FREE/SPHERICAL姿态通过旋转向量到四元数的组合更新。这个位置使用新速度的结构是半隐式更新，不能仅看到枚举名Euler就写成 `q_next=q+h*v_old`。[积分内核][integrate]

| 原生枚举 | 本提交对阻尼/质量的处理 | 容易误读之处 |
|---|---|---|
| `Euler` | 先以未加速度阻尼修正的质量矩阵求约束，之后仍有被动阻尼的隐式处理 | 不等于所有项都显式 |
| `implicitfast` | 约束后对含被动阻尼及对应控制速度bias的树做隐式修正 | 不等于完整Backward Euler重算未来接触几何 |
| `approximate_implicitfast` | 约束前把h乘被动/控制阻尼加到有效M，后面不再调用同一阻尼修正 | 接触求解看到的M已经改变，不能只改更新公式描述差异 |

非兼容Euler/implicitfast的后处理按 `a'=a−(M+hD_v)⁻¹(hD_v a)` 修正当前解；兼容分支可从force重新求解。主约束迭代未完全收敛时，“修正已得到的a”和“由总force重新解”未必等价。D_v是速度阻尼矩阵，区别于第5节约束D=R⁻¹。[调用条件][step-halves]、[后处理实现][implicit]

### 7.1 不能忽略的自由体midpoint分支

非Euler、非可微、非backward时，**本子步无约束、独立质量块的free body**可用implicit midpoint；有接触、connect/weld或DOF后代等会退出该资格。固定子link组成复合体在非兼容模式可参与；兼容模式对固定子link另有限制。[资格判断][midpoint-gate]

其旋转核心在固定惯量frame写为：

$$
I\frac{\omega_{new}-\omega}{h}
=\tau-\omega_{mid}\times(I\omega_{mid}),\qquad
\omega_{mid}=\tfrac12(\omega+\omega_{new}).
$$

实现以Newton+回溯求中点角速度，先用中点量更新姿态，再恢复真实next速度；COM偏离joint原点时平移也有耦合处理。无外力矩的连续模型具有能量/角动量不变量，源码采用该结构保存二次不变量，但本章没有实测误差，不能据此给所有接触场景“能量守恒”标签。这里的Newton是**自由体积分内循环**，与 `constraint_solver=Newton` 并不是同一次求解。[中点方程][midpoint]、[更新调用][integrate]

### 7.2 步长改变了什么

增加substeps不仅使h变小：碰撞检测/约束集合更频繁更新，timeconst的2h下限也变化，离散阻尼与warmstart频率随之变化。因此“相同外层Δt、不同substeps”仍是不同数值工况。纸上例：Δt=.004s、substeps=4，则h=.001s，混合timeconst=.0015s会被提高到.002s；substeps=8时floor=.001s，原输入可保留。不能把两次差异全部归因于求解迭代数。

FP64减小舍入误差，不修复错误单位、极端质量比、缺失接触、非法惯量或错误采样。默认tolerance随精度改变，更不能只记录“CPU FP64”就称配置冻结。高刚度、小timeconst、大增益、饱和和接触切换共同影响稳定性；隐式处理也不构成任意h稳定、无穿透或物理正确的保证。[timeconst floor][sanitize]、[精度默认][build]

## 8. 力与冲量观测：对象、方向、时刻必须同时对齐

### 8.1 返回字段及符号

`entity.get_contacts(with_entity=..., exclude_self_contact=..., is_padded=...)`来自最近一次物理步的collider/constraint数据。返回全局geom/link索引、position、normal、penetration，以及实体包装后的force_a/force_b；A未必就是调用者。[实体包装][contact-api]、[collider读回][contact-getter]

| 字段/接口 | 单位、frame、范围 |
|---|---|
| `position` / `penetration` | 世界接触点m / 几何penetration m；不代表压强场 |
| `normal` | 世界单位向量，由B指向A；与力重建一致 |
| `force_a` / `force_b` | 世界N，作用在对应geom上的力，二者相反；需按global link/geom归属选择 |
| `valid_mask` | batch/padded时标识有效槽位及实体筛选；不是成功评分 |
| `get_links_net_contact_force()` | `(n_links,3)`或`(B,n_links,3)`，直接接触线力的代数和，世界N |
| `get_dofs_force()` | E2所述广义smooth+constraint，含多类约束；转动项N·m，不能直接当接触线力 |

elliptic力重建使用前三行 `f_B=−n λ_n+t₁λ₁+t₂λ₂`，再f_A=−f_B；pyramidal先合成所有相应混合方向。spin/rolling有独立力矩，但公开contact dict和net-contact-force只返回三维**线力**；不能把它们当完整六维wrench。[力重建][contact-force]

无batch且未padded时，只保留筛选后的条目，不额外给valid_mask；batch或 `is_padded=True` 时必须使用mask，哪怕只有一个环境。无效整数槽、0力值都不能代替mask。padded避免部分裁剪带来的host同步，不保证所有后端零拷贝/零同步。[实体shape与mask][contact-api]、[后端读回][contact-getter]

若要在某世界参考点O计算点力的力矩，`τ_O=Σ(p_i−O)×f_i`，再用 `R_WLᵀ`分别把线力与力矩转入L frame。该公式只重建**点力作用臂矩**，不含未导出的spin/rolling纯偶矩。把末端力转换成关节广义力还需对应Jacobian与参考点，不能只按数组长度拼接。仅相加每点力的模长会丢掉方向；例如两侧各1N夹力，对整个物体的净力可为0。

### 8.2 “step之后”仍包含不同阶段的数据

普通原生路径中，contact位置/normal与force属于**最后子步检测与约束求解时的几何**；随后q/v已积分到子步末。非兼容模式更新新的link姿态不等于重新计算接触。link笛卡尔加速度又在积分前更新，因此不能拿步后pose、积分前acc和最后contact混成严格同一时刻的观测。[顺序][step-halves]、[force写回][post-solve]

此外 `get_dofs_control_force()` 是E2所述当前状态重算，并非最后施加力缓存；noslip可再改变qacc，隐式阻尼/midpoint可继续改变积分用加速度。不要根据步后几个getter要求所有量恰好满足同一组冻结M/J的等式。

get_contacts有缓存和后端相关的view/clone路径；字典 `.copy()` 不是tensor快照。采样后若要跨step保留，显式 `detach().clone()`并记录仿真step、h/substeps、查询阶段、模式与休眠状态。直接setter、规划中的临时碰撞查询或手工detection之后，不能未经核实就把残留数据称为新状态的动态接触解。[读回所有权][contact-getter]

### 8.3 冲量与时间平均力

对固定单位/世界frame，子步接触力f_k可以作冲量近似 `P≈Σ h_k f_k`，单位N·s；窗口平均力为P/Σh_k。角冲量同理为N·m·s，但需完整力矩来源和一致参考点。

`get_contacts()`一次step后只读到最新接触集合/力，**不是所有子步冲量的累计器**。一般不能以 `f_last*Δt` 替代整步积分，也不能把公开力再除h。若原协议只记录末子步力，结论应写“末子步采样”，不得改名“窗口平均”。示意：两子步等长.001s，力依次0N与10N，则窗口冲量.01N·s、均值5N；只读末值10N再乘Δt会高估一倍。这是纸上单位核对，不是本章新增实验。

### 8.4 休眠保留的是旧支撑解

休眠按岛进行，相关速度/加速度归零，接触保留最后awake解的force并继续汇总支撑力。此后读到非零接触力不说明又执行了一次约束求解；DOF force也可保留旧值。静止不等于无力，缓存非零也不证明当前外界变化已被响应。[休眠动作][hibernate]、[接触缓存][contact-keep]、[force保留][contact-force]

休眠阈值检查把旋转DOF速度乘swept radius得到线速度尺度，并要求连续子步满足；非零驱动会使其不满足休眠条件。新的awake碰撞/外部输入等有唤醒路径。必须保存实际是否启用和实体状态，不把该性能机制当物理摩擦模型的一部分。[settled条件][settled]、[唤醒/过滤][runtime-filter]

## 9. 原生观测阅读例与排错

[contact_readback.py](../examples/contact_readback.py) 接收调用方已有的、已完成一步的RigidEntity，展示padded mask、A/B归属、tensor快照与点力矩。文件本身**不创建Scene、不step、不做实验或评分**，只通过语法检查，未执行原生API。它的力矩明确排除spin/rolling纯偶矩，也不替代力传感器。实际运行应使用未来复用的DexLab工况，在其约定采样阶段调用。

| 现象 | 先查什么 |
|---|---|
| visual相交但没有force | collision表示、pair过滤、是否已求解、是否被其他coupler接管 |
| 降低一侧μ却没变化 | max组合、另一侧值和friction_ratio、.01下限 |
| 只改substeps，回弹/穿透也变了 | timeconst floor、接触更新频率、离散阻尼和积分特例 |
| tolerance很小却仍有穿透 | 正则化模型允许的柔顺，与数值收敛不是同一误差 |
| active=False但有接触力 | elliptic中区由块代价处理，active不是接触存在标志 |
| Newton配置但输出像另一套模型 | coupler分派、contact_resolution、compatibility、noslip与实际字段 |
| 接触合力为0却受到夹持 | 两侧线力相消；不能以净力0判断无接触 |
| 有torsional摩擦却读不到力矩 | dict只给线力，点力矩不含纯偶矩 |
| step后力与pose看似不对时 | 接触在积分前求解、pose已更新、acc另有阶段、getter可能重算 |
| 物体休眠但仍报告支撑力 | 保留最后awake力，不是持续重新测量 |

## 10. 多物理与可微边界必须写进算法身份

`Simulator.add_entity`按最派生material类选solver，Rigid继承Kinematic也不会因此被误送成仅运动学。SimOptions的coupler类型又改变跨solver执行，不能把以下所有路径统称“Genesis Newton刚体接触”。[材料分派][material-dispatch]

| 路径 | 此提交入口与已核查边界 | 不能套用的本章结论 |
|---|---|---|
| Kinematic | 只做运动学；E1/E2 setter/查询 | 没有因为名字/mesh相同就产生动态接触力 |
| 原生Rigid + Legacy（无其他物理时走快路径） | 本章完整的约束与积分链 | 仍须具体标明cone/resolution/integrator等 |
| Legacy刚体–粒子耦合 | SDF距离给影响权重，入射相对速度按coup_friction/restitution修改；反作用为 `−mΔv/h` 写入耦合wrench | 不是同一个刚体contact矩阵或friction max组合；coupling力不等于get_contacts逐点力 |
| SAPCoupler | 刚体pre只做自由动力学/速度更新，约束由coupler处理，post回推加速度再积分；内部SAP迭代、PCG与线搜索 | 不能用RigidOptions.iterations/tolerance给耦合算法贴标签 |
| IPC | 外部IPC world advance/retrieve；按ipc_only/external_articulation/two_way_soft_constraint分配控制权，部分刚体路径改到post并排除委派pair | Genesis包版本不等于libuipc核心版本，也不能由此确认外部核心算法/容差 |
| MPM / SPH / PBD / FEM / SF / Tool | E1已列各solver状态与step入口；MPM粒子/网格、SPH流体、PBD位置约束、FEM元素等有自己的变量和内力/约束 | Rigid的q/v、M/J、sol_params、力getter与迭代上限不能直接推广 |

Legacy入射粒子的一个具体执行式是 `v_n'=−e v_n`（v_n<0）、切向速度长度截为 `max(0,||v_t||+μ v_n)`，再与旧相对速度按SDF影响权重混合，最后把粒子动量变化反向除h施加到刚体。这里e来自coup_restitution，与第4节刚体柔顺弹回不是同一个模型。SPH等耦合另有压力项，不能把该简式概括为全部流体力。[Legacy实现][legacy-response]

SAP实际迭代函数还以按质量加权的**平方范数累加量**比较gradient_norm与 `atol+rtol*max(momentum_norm,impulse_norm)`，各batch单独失活；不是原生刚体的每岛trace判据。本章标出此差别和入口，FEM/hydroelastic接触handler与完整SAP推导留E6。[SAP迭代/停止][sap]

IPC调用外部world，当前仅冻结Genesis侧源文件，未验收外部libuipc安装版本或内部求解；Options中None让外部默认生效，不能用参数注释代替实际运行manifest。[IPC推进][ipc]、[IPC配置][ipc-options]

`requires_grad=True`也有真实边界：elliptic被拒绝；刚体要求approximate_implicitfast，SAP/IPC、noslip、torsional/rolling不支持，休眠被禁用；自由体midpoint分支不走可微路径。接触narrowphase有专门可微入口，几何/活动集切换依然需要逐具体损失解释。能够调用backward不是精确可微硬接触的证明，E6再展开adjoint与可微碰撞，不把本节边界调查标成全部梯度推导已完成。[刚体可微检查][diff-limits]、[elliptic gate][resolve]、[可微检测入口][diff-collision]

## 11. 阅读练习与答案

1. 只知道“CPU FP64、elliptic、noslip=0”，能确定是Newton+signorini吗？
   **答案：** 不能。还缺solver、compatibility、显式contact_resolution和coupler；elliptic+CG可走convex。不能用新版本条件默认补历史#125。
2. A的μ=.2、ratio=2，B的μ=.6、ratio=.5，pair的滑动系数是多少？spin值是否也乘ratio？
   **答案：** max(.4,.3,.01)=.4；spin/rolling也乘各geom同一ratio后取最大。
3. Δt=.006s、substeps=3，混合timeconst=.003s，最终至少多少？
   **答案：** h=.002s，floor=2h=.004s；仅输入文件中的.003不能作为生效值。
4. 为什么elliptic中active=False仍可能有force？
   **答案：** active控制逐行二次项，中区cone的力/cost/Hessian由块函数处理，不等于“无接触”。
5. Newton与CG分别用什么计算搜索方向？
   **答案：** Newton用含约束曲率的Hessian Cholesky解；CG用M⁻¹g预条件梯度及Hager–Zhang历史方向。CG不是Newton内部线性解器。
6. 把iterations从25调到100是否把柔顺接触变成硬接触？
   **答案：** 否；它只提高数值预算，sol_params/R仍定义同一柔顺模型，几何近似也没变。
7. 哪个Newton可能出现在无接触自由体积分里？是否等同constraint_solver？
   **答案：** 非Euler且满足资格的独立free body中点积分Newton；这是另一个局部方程，不是接触约束Newton。
8. 两接触点分别向+X和−X施1N，net_contact_force=0说明什么？
   **答案：** 只说明线力相消，不说明无接触或无夹持；力矩还取决于作用点和未导出的纯偶矩。
9. 读到force_b后能直接说它作用在调用者吗？
   **答案：** 不能；A/B是全局pair顺序，须按geom/link所属entity选force_a或force_b，batch/padded还要mask。
10. 两子步各.001s，接触力0N、10N，末值10N等于整步平均吗？
    **答案：** 不等于；积分近似冲量.01N·s、平均5N。getter未提供前一子步，不能仅由末值恢复真实累计量。
11. 休眠物体继续报告支撑力，能否认定该时刻重新求解完成？
    **答案：** 不能；缓存保留最后awake力，速度/加速度归零且求解可被跳过，应标记休眠状态。
12. `coup_restitution=.5`为何不证明原生刚体碰撞恢复系数=.5？
    **答案：** 它属于耦合速度响应；普通刚体用自己的参考加速度/正则与约束模型，需查真正执行分支。

下一项建议 [E4 传感器、渲染与可视化](roadmap.md)，沿本章采样frame/时点继续解释观测。E5仍依赖E4；E6将展开本章明确保留的多物理/可微内部细节。完整双路线仍待E4–E7，不以本章源码审查替代实验或全课程验收。

[options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L438-L591
[defaults]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L592-L671
[resolve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L238-L299
[build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L334-L344
[config]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L474-L750
[dispatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5568-L5663
[decomposed]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver_breakdown.py#L282-L340
[sim-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L427
[substep]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1260-L1377
[assembly-order]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L1523-L1550
[post-solve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5747-L5808
[step-halves]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3479-L3553
[mass]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L160-L375
[mass-correction]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L353-L375
[smooth]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1705-L1760
[dynamics]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L100-L130
[mass-solve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1023-L1080
[detection]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py#L1081-L1213
[broadphase]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/broadphase.py#L396-L430
[collider-config]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py#L172-L216
[narrow-convex]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/narrowphase.py#L3040-L3215
[narrow-other]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/narrowphase.py#L3482-L3556
[capacity]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py#L672-L720
[constraint-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L102-L142
[morph-filter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/morphs.py#L100-L221
[filter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py#L388-L502
[runtime-filter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/broadphase.py#L18-L58
[mix]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L413-L463
[material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/rigid.py#L25-L115
[friction-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L3267-L3353
[legacy-response]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L160-L311
[impedance]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/geom.py#L649-L666
[sanitize]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L161-L213
[sol-setter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2526-L2597
[contact-rows]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L666-L840
[row-directions]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L605-L663
[invweight]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L2431-L2456
[cone]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L4149-L4376
[relatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L4661-L4740
[objective]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L4816-L4916
[row-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L4919-L4965
[gradient]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5128-L5172
[iteration]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5502-L5564
[exit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L567-L617
[linesearch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L383-L563
[ls-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L317-L365
[warmstart]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5307-L5498
[constraint-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L220-L279
[islands]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L1397-L1491
[island-scale]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/island.py#L300-L435
[noslip]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/noslip.py#L438-L546
[integrate]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L2064-L2197
[implicit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L2261-L2328
[midpoint-gate]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1764-L1803
[midpoint]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1850-L1896
[contact-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L3161-L3261
[contact-getter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py#L873-L1060
[contact-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5668-L5743
[hibernate]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/misc.py#L123-L204
[contact-keep]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L182-L263
[settled]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L2200-L2231
[material-dispatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L88-L153
[sap]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/sap_coupler.py#L836-L909
[ipc]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L812-L860
[ipc-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L200-L332
[diff-limits]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L752-L769
[diff-collision]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/narrowphase.py#L3284-L3373
