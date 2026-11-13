# E3 · 从动力学装配到 SAP 终止

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · 前篇[几何与材料](contact-models.md) · 后篇[力观测](contact-observation.md)

这里的“solver”指固定 Drake 1.57.0 源码中的 SAP 算法。`kSap`、`kSimilar`、`kLagged` 是它接收的不同接触近似。本篇从 q/v 的动力学出发，追踪一步离散更新的方程、矩阵和停止条件；所有实现结论对应固定源码，没有运行求解器。

## 1. 力、广义速度与动力学装配

对刚性多体，令 q∈R^nq、v∈R^nv，`q̇=N(q)v`。惯性坐标、独立自由度与关节约束已由模型拓扑决定；不能把六维 body 力逐项填入 q 数组。动力学可按本课符号写为

$$M(q)\dot v+c(q,v)=B u+\tau_g+\tau_{elements}+\tau_{ext}
 +\sum_i J_i(q)^T f_i.$$

M 包含由模型质量/惯量产生的广义质量与相关转子反射惯量；c 含速度偏置。J 把 v 映射为对应接触相对速度，所以 `vᵀJᵀf=(Jv)ᵀf` 保持功率一致。旋转自由度广义力单位 N·m，平移自由度为 N；不能把 mixed generalized vector 的普通欧氏范数称为“总夹持力”。连续接触映射实现使用逆动力学收集 `ΣJᵀF`，在传入零加速度、关闭速度项的调用中先得到负号，再显式取反。[广义接触力装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L3325-L3365)

空间惯量的串接、广义速度与配置维度见 E1；控制输入到 B u 见 E2。这里的接触力是独立力源。切勿把 actuator effort limit 当成所有外部/接触广义力的统一限额。

## 2. 同一个 Context 出发，一步发生什么

```text
CalcStepDiscrete / CalcStepUnrestricted
  → DiscreteUpdateManager::CalcDiscreteValues
  → CompliantContactManager / SapDriver
      → geometry contact data + material + contact Jacobians
      → free-motion v* + dynamics matrix A
      → contact constraints, limits, PD, coupler/distance/ball/weld/... constraints
      → locked-DOF reduction → SAP SolveWithGuess(v0)
      → impulses / contact velocities / v_next → forces and sampled memory
  → MapVelocityToQDot(context0, v_next) → q_next
```

这是一条依赖链，不是每次 API Eval 都无条件从头执行。缓存依赖于 Context 的状态、输入、参数等；合法 setter 使依赖失效。`CalcStepUnrestricted` 还保存 sampled dynamics memory；普通状态读回与 sampled contact 输出属于不同时间合同。[两个事件入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L3553-L3576)、[更新和 memory](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L30-L55)、[完整问题装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L913-L969)

### 2.1 Free motion 不是完整接触解

在刚体路径中，非约束力在旧状态 x0 计算，但线性关节阻尼 `−D v` 使用下一速度。于是

$$A=M(q_0)+hD,\qquad A(v^*-v_0)=h\,k(x_0),$$

其中 k(x0) 已含旧状态下的非约束总广义力，含 `−Dv0`；不要再减一次阻尼。源码使用 articulated-body algorithm 计算这一自由运动加速度，并在 ABA 的对角项中加反射惯量与 hD；`SapDriver` 按运动学树提取 A 的块，用 `v*=v0+h a0` 得到自由速度。启用内建 PD 的驱动和关节限位由之后的约束处理，不能同时计入 free motion 与 constraints 两次。[阻尼拆分与 ABA](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc#L115-L180)、[A 与 v* 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L134-L203)

h 单位 s，D 的平移条目单位 kg/s，hD 因而与质量一致。A 不是一个任意数值预条件矩阵；它来自此次时间离散。普通显式外部弹簧仍可能因 h 太大而不稳定，即使接触优化收敛，也不证明整套时间积分稳定。

### 2.2 Hydroelastic 由面片变成离散约束

离散 hydro 对每个 surface face 使用面心的一阶求积。设面片面积 a [m²]、弹性压力 p0 [Pa]，两侧沿法向的压力梯度 gM,gN [Pa/m] 合成为 `g=1/(1/gM+1/gN)`；rigid 方取无限梯度。局部装配

$$f_{e0}=a p_0,\quad k=a g\ [N/m],\quad \phi_0=-p_0/g\ [m].$$

这解释了“一个 hydro surface 为何可贡献多个 solver contacts”，也解释了 E 不能直接与 point k 比较。近零梯度等数值分支会跳过无效约束；面片数不必等于最终报告的正力点数。[面心规则](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L805-L823)、[梯度与接触坐标](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L914-L963)、[力/刚度装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L1005-L1055)

接触 frame C 的 z 轴为 A→B，`vc=Jv+vb=[vt1,vt2,vn]`；vn>0 表示分离，vb 可承载 moving-surface bias。它与几何字段 `nhat_BA_W` 的方向相反。下述公式都沿这个约定，静止表面时 vb=0。

## 3. 三种近似的实际法则

### 3.1 kSap：线性柔顺、relaxation time 与锥投影

忽略摩擦耦合和数值刚度截断时，法向模型是 Kelvin–Voigt：

$$\gamma_n/h=[-k\phi_{next}-k\tau_d v_n]_+,\quad
\phi_{next}\approx\phi_0+h v_n.$$

γ 是接触冲量 [N·s]；τd 是两侧 relaxation time 之和 [s]；kτd 才是 N·s/m 的线性阻尼。Hunt–Crossley d [s/m] 不在此方程中。[模型合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_friction_cone_constraint.h#L103-L139)

**真正执行时**还包括正则化和摩擦锥投影。令 `R=diag(Rt,Rt,Rn)`，接触 Delassus 量来自 `J A⁻¹Jᵀ` 的尺度估计 w，代码定义

$$R_n=\max\left(\frac{\beta^2}{4\pi^2}w_n,\frac{1}{h k(h+\tau_d)}\right),\quad
R_t=\sigma w_t,\quad \hat v_n=-\frac{\phi_0}{h+\tau_d}.$$

$$y=-R^{-1}(v_c-\hat v),\qquad
\gamma=\arg\min_{z\in\mathcal F_\mu}\frac12(z-y)^T R(z-y),\quad
\mathcal F_\mu=\{z_n\ge0,\|z_t\|\le\mu z_n\}.$$

实际 wt/wn 还以 w 的 RMS 下界防止零尺度；σ在驱动中固定为 1e−3，β由 Plant 的 near-rigid threshold 进入。`ProjectImpulse` 按 stiction/sliding/no-contact 做解析投影；这不是把圆锥离散成任意边数的金字塔。[R、bias 与投影](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_friction_cone_constraint.cc#L46-L143)、[装配参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L207-L268)

法向 Rn 的 max 可把过硬接触变成数值上的 near-rigid 近似。因此把 E/k 增大十倍不保证解中力增加十倍，也不保证穿透按十倍下降。锥投影还会耦合滑动与法向，导致文档所说 gliding；前面的纯法向式不能代替完整投影。静摩擦区存在 `γt=−vt/Rt` 的小残余滑动，这是模型正则化，不是 Newton 未收敛的同义词。

### 3.2 Similar 与 Lagged：Hunt–Crossley 的两个凸近似

以旧几何的弹性法向力 fe0、k、d 为参数，定义任意法向速度 z 上的冲量函数

$$n(z)=h[f_{e0}-hkz]_+[1-dz]_+.$$

令 `s(vt)=sqrt(||vt||²+ε²)−ε`，`tsoft=vt/sqrt(||vt||²+ε²)`。源码分别取

| 近似 | 法向 | 切向 |
|---|---|---|
| Similar | `z=vn−μ s(vt)`；`γn=n(z)` | `γt=−μ n(z) tsoft` |
| Lagged | `z=vn`；`γn=n(vn)` | `γt=−μ n0 tsoft` |

其中 $n_0=h[f_{e0}]_+[1-dv_{n0}]_+$ 是由**旧状态的弹性力与法向速度重新计算**的量，不是读取上一轮优化的 γn。Lagged 的切向限额对应 μn0，不能用当前 μγn 检查它再宣称“solver 违反自己的锥”。[n0 与 ε 构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc#L31-L75)、[z、cost 与冲量分支](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc#L164-L232)、[法向冲量函数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc#L125-L141)

正则化并非永远等于用户 vs：`ε=max(vs, μσ wt n0)`，碰撞瞬态可由数值项主导。若 N(z) 是 n(z) 的反导数，单约束势能为 Similar 的 `−N(z)` 或 Lagged 的 `−N(vn)+μn0 s(vt)`；γ=−∂ℓc/∂vc，这使它们进入同一个凸优化框架。[参数量纲](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.h#L125-L154)

Similar 保留更强的法向/摩擦耦合，但有随 h 变化的 gliding；Lagged 避免这个 gliding，却弱化冲击瞬态耦合。它们是不同近似，不能以“都用 SAP”合并成同一模型，也不能用一次收敛状态给三者排精度名次。[官方近似取舍](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L192-L225)

## 4. SAP 解的是速度上的凸问题

令所有接触/约束的 J 堆叠为总 Jacobian，γ为对应冲量，A 为对称正定动力学矩阵。目标为

$$\ell(v)=\tfrac12(v-v^*)^T A(v-v^*)+\sum_i\ell_{c,i}(J_i v+v_{b,i}),$$
$$g=\nabla\ell=A(v-v^*)-J^T\gamma,\quad
H=A+J^T GJ,\quad G_i=-\partial\gamma_i/\partial v_{c,i}.$$

接触势能与动量项均具有 Joule 量纲；在固定模型和有效正则化假设下 H 为正定。Newton 搜索解 `H Δv=−g`，再通过线搜索取 v←v+αΔv。源码不会显式计算 H⁻¹；默认用 block sparse Cholesky 因子化，另有 dense 分支。[模型方程](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_contact_problem.h#L27-L55)、[cost/gradient/Hessian 装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc#L272-L338)、[线性系统求解](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L701-L715)

### 4.1 稀疏图、warm start 与约束种类

clique 是 A 中一个动力学块的自由度集合，刚体 driver 通常以运动学树为块；constraint cluster 是连接同一组一/两个 clique 的约束集合。图保存参与集合，SapModel 排除不参与的自由度并重排，joint locking 还有专用的已知 DOF 消元/恢复。不能把一个 clique 直接叫“接触岛”，也不能从稀疏图推断代码已经并行执行独立岛。[图与 cluster](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/contact_problem_graph.h#L14-L95)、[参与自由度](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc#L66-L101)

warm start 的 driver 输入是当前 Context 的 v0，而不是一份永久积累的 contact impulse 数组。无约束时直接返回 v*，无需 Newton。PD、关节限位及闭链约束与 contact 同在问题中，**总 γ 不能整体叫接触冲量**；driver 把接触放在最前，再按该范围提取报告力。[初值与求解](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L1040-L1101)、[无约束快捷路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L111-L130)

### 4.2 默认值、终止与失败

以下是 `SapSolverParameters` 的固定源码默认值，不代表 DexLab 的实测参数，也不是未经核验的 pydrake setter。

| 字段 | 本版本默认值 | 含义 |
|---|---|---|
| `abs_tolerance` | 1e−14 √J | 缩放动量残差的绝对阈值 |
| `rel_tolerance` | 1e−6 | 相对动量残差 |
| `cost_abs_tolerance` | 1e−30 J | cost 变化绝对阈值 |
| `cost_rel_tolerance` | 1e−15 | cost 变化相对阈值 |
| `max_iterations` | 100 | Newton 上限，不是子步数 |
| `line_search_type` | `kExact` | 一维导数求根，必要时用二分，不是精确接触物理 |
| `linear_solver_type` | `kBlockSparseCholesky` | Hessian 线性系统 |

参数定义见[固定参数结构](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.h#L30-L169)。外部读取/修改内部参数需要具体 C++ 接口与构建路径，普通 `MultibodyPlant` 的公开配置不能凭字段名想象出 Python setter；本阶段不加 solver 调参封装。

实际缩放是 `D=diag(A)^(-1/2)`，不是 header 注释误写的正 1/2。记 p=Av、jc=Jᵀγ，判定

$$\|Dg\|_2\le\epsilon_a+\epsilon_r\max(\|Dp\|_2,\|Djc\|_2).$$

代码通过 `Ac.diagonal().cwiseInverse().cwiseSqrt()` 构造 D，因此各项转为 √J 的一致尺度；这也解释了混合平移/转动不能直接用一个未缩放的 N 容差。[构造 D](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc#L88-L100)、[残差计算](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L88-L108)

另一个成功条件是

$$|\ell_m-\ell_{m-1}|<\epsilon_{ca}+\epsilon_{cr}(|\ell_m|+|\ell_{m-1}|)/2,
\quad\alpha>0.5.$$

`α>0.5` 是实现中额外防止“小线搜索步导致假停滞”的条件，不能只抄 header 的 cost 描述。**动量条件或 cost 条件任一满足即可成功**；达到 max iterations 且未满足则 failure，driver 抛出收敛失败异常。`optimality_criterion_reached` 与 `cost_criterion_reached` 应分别记录；“返回 success”不必然表示动量容差满足，更不代表没有建模误差。[循环和真实终止](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L237-L350)、[driver 失败处理](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L1102-L1127)

诊断应先看输入是否发散、质量/惯量和尺度、外部刚性弹簧的显式时间离散，再看残差、cost、线搜索和迭代上限。减小优化容差只处理当前离散问题的求解误差；不会修复过粗网格、错误材料、错时观测或过大的 h。

## 5. 离散推进与连续积分不能互换名字

离散刚体位置更新实际是

$$q_{next}=q_0+hN(q_0)v_{next},\qquad x_{next}=[q_{next};v_{next}].$$

这是旧配置映射、新速度的位置更新，加上前述阻尼隐式和接触隐式处理；不能整体写成“全系统 Backward Euler”或照搬论文里的所有离散细节。nq≠nv 时先 MapVelocityToQDot；四元数也不能按三个欧拉角积分。[实际位置更新](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L1089-L1112)

连续 Plant 的接触力在当前 q,v 上计算，再由连续动力学与 Simulator 的积分器推进；其内部 Newton（若选择隐式积分器）与 SAP 的接触 Newton 是不同层次。连续系统支持的拓扑约束也有边界：当前源码拒绝注册的多体 constraints，并警告连续模型的 joint limits 未按离散方式处理。[连续力装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L3510-L3534)、[连续约束限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L3450-L3508)

连续积分器误差控制、最大步长、离散 Plant h、控制保持 H、Newton tolerance 各自约束不同误差。缩短 H 不自动缩短 h；增加迭代不增加时间分辨率。接触刚度上升通常缩短物理接触时间尺度，显式外力也可能带来稳定性约束；数值稳定不等于物理保真。积分器 API 和事件左/右极限继续按 [E1](state-time.md) 理解。

### 5.1 可微能力：实现与旧注释要一起核对

当前 `SapSolver<AutoDiffXd>::SolveWithGuess` 已有独立实现：先解 double 问题，再对最优性 `g(v;θ)=0` 用隐函数定理求

$$H\,\partial v/\partial\theta=-\partial g/\partial\theta.$$

这是线性系统解，不是对全部 Newton 迭代逐步反传。公开 solver 注释仍保留“有 constraints 就不支持 AutoDiff”的旧说明，与这一实现不一致；课程据源码确认内部梯度路径存在，**不把它升级为任意模型/几何/接触切换的端到端梯度保证**。[当前 AutoDiff 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc#L133-L232)、[有冲突的公开注释](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L168-L174)

几何查询只支持特定 scalar/形状组合，hydro 查询的导数由 pose 引入，不能求任意形状半径等几何参数的导数；接触创建/消失、模式切换和网格拓扑变化也可能不可微。仅在固定分支、适用可微条件及非奇异 H 下解释局部导数。源码支持、绑定可达、实际梯度正确三个层次需分别验证，本轮没有运行任何梯度检查。[几何 scalar 边界](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L392-L398)

## 6. 阅读练习与答案

1. 同样选择 SAP solver，为什么 relaxation_time 在 Lagged 中不决定 Hunt–Crossley 耗散？
2. 当 k 很大，Rn 的 near-rigid 下界生效时，继续增大 k 是否仍按原 Kelvin–Voigt 刚度执行？
3. Lagged 的 `||γt||` 超过当前 `μγn`，是否必然是求解失败？
4. SAP success，但 `optimality_criterion_reached=False`，是否矛盾？
5. 把 100 次 Newton 迭代改为 200 次，会把 1 ms 的 h 变成 0.5 ms 吗？
6. 为什么 D 应是质量尺度的负平方根而非正平方根？
7. 论文采用的时间离散和当前 `q0+hN(q0)v_next` 不同，课程该写哪一个？
8. 内部 AutoDiff 实现存在，能否立即宣称球半径到抓取成功分数可微？

<details><summary>答案</summary>

1. solver 是算法；近似选择决定材料字段。Lagged 用 d [s/m]，kSap 才用 τ [s]。
2. 不能。max 使 Rn 不再随 k 下降，实际数值柔顺被截断；还须考虑摩擦投影的耦合。
3. 不是。Lagged 的切向界使用旧状态计算的 μn0，非当前 μγn。
4. 不矛盾。cost 停止条件也可以产生 success，须同时记录两类 flag。
5. 不会。迭代数改变同一步优化的求解预算，h 仍由 Plant 定义。
6. 动量除以质量平方根得到 √J；正平方根不满足该量纲，且当前实现确为 inverse square root。
7. 写当前执行路径并注明与论文的差异，不把论文公式当作这一版本实现。
8. 不能。还要满足几何导数支持、接触分支、端到端接口和评分定义；本轮只确认源码路径。

</details>

继续：[ContactResults 的力、冲量、坐标与时间](contact-observation.md)。
