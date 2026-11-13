# E6 多物理、可微与扩展边界

本章完成 B6 的内部扩展部分及 B7 的能力追踪专题。固定 Genesis **1.4.3**、提交 `216a708e06124595521a9d36a51fae5393fd4ff8`；先修 [E1](modeling-state-time.md) 的状态/单位、[E3](contact-solvers-forces.md) 的刚体/约束，再衔接 [E4](sensors-rendering.md) 的观测和 [E5](batch-learning-data.md) 的批量/数据。需要矩阵求导、离散时间、质量守恒与能量的基本概念；公式都注明适用假设。

这里沿着 **入口 → 实际消费者 → 写入状态 → 反向/恢复路径** 判断能力。存在类名或配置字段，只证明有入口；具有完整执行链仍不等于已运行验收。本轮没有 native import、模型编译、JIT、仿真、渲染、训练或实验。完整 A0 安装及双路线综合审校仍留 E7，实验继续复用 DexLab。

## 1. 从 material 到 solver：谁真的推进实体

[Simulator._add_entity][dispatch]遍历固定 `_solvers` 列表，选匹配 `material_cls` 中最派生的类。`Rigid` 派生自 `Kinematic`，必须由更具体的 RigidSolver 消费；不是按列表中第一个 isinstance 命中就停。`Hybrid` 特判，由 HybridEntity 自己创建其组成实体。没有匹配 solver 就抛错。

| 原生入口 | 实际实体/消费者 | 物理状态和主要边界 |
|---|---|---|
| `materials.Rigid` | RigidEntity / RigidSolver | q/v、刚体约束与积分；E1–E3 已展开 |
| `materials.Kinematic` | KinematicEntity / KinematicSolver | 运动学、视觉 ghost；不进入刚体碰撞/约束，视觉射线另有 opt-in |
| `materials.Tool` | ToolEntity / ToolSolver | 规定的 pos/quat/vel/ang，用 SDF 改变 MPM 网格速度；不是受反作用力推进的自由刚体 |
| `materials.MPM.*` | MPMEntity / MPMSolver | 粒子 x/v/F/C/Jp 和临时网格；本构、粒子与网格交换、Legacy grid operation |
| `materials.SPH.Liquid` | SPHEntity / SPHSolver | 粒子 x/v、邻居密度/压力；WCSPH 或 DFSPH |
| `materials.PBD.*` | PBD2D/3D/Particle/FreeParticleEntity / PBDSolver | 由 Cloth/Elastic/Liquid/Particle 分成不同离散拓扑，修正位置后回算速度 |
| `materials.FEM.Elastic/Muscle` | FEMEntity / FEMSolver，或 IPC 接管 | 四面体节点/单元状态；显式、隐式、外部本构须分别判断 |
| `materials.FEM.Cloth` | FEMEntity 的三角面元素 → IPCCoupler | 壳/膜物理在外部 uipc；不是原生体积四面体算法换个材料名 |
| `materials.Hybrid` | HybridEntity 创建 rigid + MPM | 固定实现只接受 MPM 软部、URDF/Mesh；不是任意 solver 的组合工厂 |
| `materials.SF.Smoke` / SFSolver | 普通 material 分派链有缺口 | SFSolver 未声明 material_cls/add_entity；实际由 `set_jets` 激活内部网格流程 |

证据：[Rigid 继承关系][rigid-material]、[Kinematic solver][kinematic-solver]、[Solver.material_cls 默认值][base-solver]、[Kinematic 定义][kinematic-material]、[Tool 运动与碰撞][tool-step]、[PBD 实体选择][pbd-add]、[FEM mesh/cloth 分支][fem-entity]、[Hybrid 构造][hybrid]及 [SF 实现][sf]。因此不能仅因 `SF.Smoke` 可构造就编造一段 `scene.add_entity(material=SF.Smoke(...))` 的完整可用教程。

默认初始化会创建多个 solver 对象，`is_active` 决定实际推进。MPM/SPH/PBD 依赖粒子数，FEM 依赖单元数，SF 依赖 jets。空对象存在不等于该 solver 在模拟什么，也不意味着它具备完整 checkpoint 或反向实现。

## 2. 一步多物理：共享时间，不是随意混合频率

[Simulator.build][sim-build]在分配前统一子步：显式指定的 solver dt 必须整数整除外步 dt；多个 solver 请求不同子步数会被拒绝；与显式 `SimOptions.substeps` 冲突也拒绝。没有显式指定 dt 的 solver 跟随统一子步。可微模式还不能在 tape 已按原 substeps 规划后偷偷推导不同窗口。

设外步 $\Delta t$、子步数 $N$，则实际公共交换间隔为 $h=\Delta t/N$，单位 s。不同物理状态虽然算法不同，coupler 每个 h 只交换一次。下面是 [实际顺序][step-order]，不是概念性的任意调度图：

```text
外步输入 process_input（每个 outer step 一次）
  对每个子步 f:
    coupler.preprocess(f)
    每个 active solver.substep_pre_coupling(f)
    coupler.couple(f)
    每个 active solver.substep_post_coupling(f)
    global substep 前进，必要时保存梯度窗口
外步末尾清刚体外力 → sensor manager.step
```

active solver 顺序固定为 Tool、Rigid、Kinematic、MPM、SPH、PBD、FEM、SF。刚体独占且无梯度、无 SAP/IPC 时可走优化的直接 substep 路径；不要将其当所有多物理一步的执行序列。MPM 的网格动量归一化、重力和边界/接触处理甚至发生在 **LegacyCoupler.mpm_grid_op**，所以只看 MPMSolver 会漏掉积分的重要一段。

多物理 operator splitting 在不同阶段更新速度与位置；它不等价于把所有物理量组成一个完全隐式大系统同时求解。接触力/热量/传感数据必须带阶段标签，不能假定来自相同子步或相同求解器状态。

## 3. MPM：粒子存历史，网格计算相互作用

[MPM 网格参数][mpm-build]、[build 条件][mpm-build-grad] / [p2g][mpm-p2g] / [pre/post coupling][mpm-step]揭示这些角色：x 为粒子世界位置 m，v 为 m/s，F 为无量纲变形梯度，C 是仿射速度场矩阵 s⁻¹，Jp 为塑性历史变量。网格间距 `dx=1/grid_density`，粒子尺寸控制采样/质量离散，两者不能互当。

在当前仿射速度近似下先计算

$$
F_{\mathrm{tmp}}=(I+hC_n)F_n,\qquad J=\det F_{\mathrm{tmp}}.
$$

之后不是直接把 F_tmp 存回：本构 `update_F_S_Jp` 可以投影奇异值并更新 Jp，`update_stress` 再产生用于 p2g 的应力量。粒子质量/动量和应力散到邻域网格；Legacy grid_op 归一化速度、施加重力/外场/耦合，再由 g2p 插值回粒子并推进位置和 C。一般形式

$$
m_i=\sum_p w_{ip}m_p,\qquad
(mv)_i=\sum_p w_{ip}\bigl(m_pv_p+A_p(x_i-x_p)\bigr).
$$

其中 $w_{ip}$ 是无量纲插值权，$A_p$ 汇合仿射动量和时间离散应力贡献；这是解释结构的简式，不把源码中的缩放/应力量误标成 Cauchy stress。p2g 里 material 返回的 `stress` 随具体表达式可能对应 $PF^T$ 型量，不能从变量名直接做传感器应力读数。

[MPM.Base][mpm-base]把 $E,\nu$ 换成 Lamé 参数：

$$
\mu=\frac{E}{2(1+\nu)},\qquad
\lambda=\frac{E\nu}{(1+\nu)(1-2\nu)}.
$$

$E,\mu,\lambda$ 单位 Pa，$\nu$ 无量纲，$\rho$ kg/m³；这些关系假设各向同性线弹性参数化，接近不可压缩极限会加大刚度，不是自动解决锁定/稳定性的开关。

| MPM 材料 | 实际本构分支 | 不能省略的条件 |
|---|---|---|
| [Elastic][mpm-elastic] | `corotation` 使用 SVD 的 R=UVᵀ；`neohooken` 使用 F_tmp 与 log J | 字符串拼写就是 `neohooken`；log J 需要正 J，不能因有 EPS 就当任意翻转安全 |
| [Liquid][mpm-liquid] | F_new 重置为 J^(1/3)I；non-viscous 将 μ 置零 | 不是 SPH 压力方程的另一个名称；viscous 分支依赖变形历史表达式 |
| [ElastoPlastic][mpm-plastic] | von Mises 对数应变投影，或上下界奇异值钳位 | 屈服面/钳位引入分段映射；并非处处光滑 |
| [Snow][mpm-snow] | 钳位奇异值并累计 Jp，以 exp(10(1−Jp)) 硬化 | 拒绝 `use_von_mises=True`；p2g 应力使用前一时刻 Jp |
| [Sand][mpm-sand] | 摩擦角转换为内部塑性系数，对数奇异值投影 | friction_angle 为度；不是刚体表面 Coulomb μ |
| [Muscle][mpm-muscle] | 被动应力上加 E·actu·F_tmp(mmᵀ)F_tmpᵀ | group、方向和 actuation 有专用实体 API；不是 DOF motor control |

forward-only 可在所有材料不需要 SVD 时跳过分解；`requires_grad=True` 强制保留 SVD 路径，并拒绝 CPIC。网格脏单元的前向清理优化也没有直接照搬到反向。设置更多子步可能缓解数值问题，但源码的 dt 警告不是一条适用于所有材料和碰撞的稳定性证明。

## 4. SPH 与 PBD：同为粒子，未知量和停止条件不同

### SPH

[SPH step][sph-step]先做空间重排和密度计算。WCSPH 使用 [压力内核][sph-pressure]与 [Liquid 参数][sph-material]：

$$
p_i=k\left[\left(\frac{\max(\rho_i,\rho_{0i})}{\rho_{0i}}\right)^\gamma-1\right].
$$

这里 k 为压力刚度尺度（按该压力表达式为 Pa），ρ 为 kg/m³，γ 无量纲；密度下夹到 rest density，使这条分支不产生负压。非压力力还处理粘性、表面张力、重力与外场；邻居核半径/采样决定离散误差，调 stiffness 不是单纯调接触精度。

DFSPH 则计算密度梯度相关因子，先做速度散度修正，再预测速度、修正下一时刻密度；[divergence/density loops][sph-df]有迭代上限与误差阈值。**固定实现的 density-error kernel 跨 particle×B 求和，调用者只除 n_particles，没有再除 B**。因此变量名 `avg_density_err` 不能解释成每环境平均误差，batch 数和其他行的误差会影响统一停止条件；这是算法迭代控制耦合，不是环境间发生了物理接触。warm start 在该段仍是 TODO，不能从刚体 warmstart 推广。

### PBD

[PBD.add_entity][pbd-add]按材料选面网格、体网格、液体粒子或自由粒子。实际外步中的子步顺序是：保存初始位置→外力预测→stretch/bending/volume→空间重排→density/viscosity/collision→由位置差回算有效速度→coupler→拷回粒子和边界处理。[PBD step][pbd-step]

以 [stretch kernel][pbd-constraints] 为例，两个粒子的长度约束 $C=\|x_1-x_2\|-\ell_0$，权重 $w_i=\mathrm{free}_i/m_i$：

$$
\Delta x_1=-\frac{w_1C}{w_1+w_2+\alpha/h^2}\,\hat n\,r,
\qquad
\Delta x_2=+\frac{w_2C}{w_1+w_2+\alpha/h^2}\,\hat n\,r.
$$

$\alpha$ 为 stretch compliance（m/N），r 为 relaxation，$\hat n$ 为连线方向。代码逐轮累计位置修正，没有在该 stretch 公式中保留跨迭代的 XPBD λ 历史；不能只看到注释“XPBD”就把标准论文的完整算法一字不差套进来。迭代次数、h、compliance 和 relaxation 一起决定离散表现。

体积和弯曲约束还需要单独核对量纲。[Elastic 选项][pbd-material]对 bending/volume compliance 给出文字单位，但 volume 内核先把 inverse mass×梯度范数平方合成 w_i，随后更新又使用 w_i×gradient；这与通常分开使用 inverse mass 和约束梯度的推导有差别。本章保留实际表达式的出处，**不把它认证为标准体积 XPBD，也不替这些字段给出已验证物理标定**。

SPH/PBD 的 `substep_pre_coupling_grad`、`substep_post_coupling_grad` 和 queried-state 梯度收集均仍有 pass；PBD 的输入反传也为空。看得到粒子位置不代表损失可反传到粒子动力学。第 8 节会把这类缺项与明确抛错分开。

## 5. FEM：网格能量、隐式求解与外部接管

[FEMEntity.sample][fem-entity]将网格焊接、生成或细分体四面体；Cloth 则保留表面三角形。渲染网格与 simulation mesh 通过索引关联，视觉平滑不能增加物理单元。

体积四面体用参考边矩阵的逆 B 和当前边矩阵 D 得到 $F=DB$。显式分支 [compute_vel][fem-explicit]调用 material.update_stress，按参考体积和 Bᵀ 将应力散成节点力，再推进速度、施加指数阻尼及重力；耦合后以新速度更新位置。F 无量纲、参考体积 m³、能量密度 Pa，梯度最终须成为 N，不能把每节点或每单元的数组名混成总力。

隐式分支把节点位置当未知量，惯性项与材料能量共同形成优化问题，可用

$$
\Phi(x)=\frac{1}{2h^2}(x-\widetilde x)^TM(x-\widetilde x)+\sum_e V_e\,\Psi(F_e(x))
$$

理解其单位：每项 J；$\widetilde x$ 是惯性/外力预测。具体约束、阻尼与 Hessian 缓存仍以 [惯性初始化][fem-inertia]和[Newton/PCG/线搜索调用][fem-implicit]为准，不能借这条简式宣称所有分支一致。Newton 更新采用材料 energy/gradient/Hessian 接口；显式应力函数和这些接口是两组消费者。

| FEM.Elastic model | 显式 update_stress | 原生隐式 energy/gradient/Hessian | 源码含义 |
|---|---|---|---|
| `linear` | 已实现 | 已实现，Hessian invariant | 小应变线性模型不因隐式求解就适合任意大旋转 |
| `stable_neohookean` | 已实现 | energy 有；gradient/Hessian 明确未实现 | 不能把显式可用名字塞到原生 implicit/SAP 就认定闭环 |
| `linear_corotated` | 明确 raise 未实现 | 有旋转预计算及能量导数 | 不可将 implicit 分支支持反推到 explicit |

证据：[FEM.Elastic 分派及函数体][fem-elastic]。`FEM.Muscle` 只覆写 [update_stress][fem-muscle] 添加沿肌肉方向的主动项，继承的隐式能量接口没有同步新增同一项；不能宣称每个 FEM 模式都执行相同肌肉 actuation。`use_implicit_solver=True` 的反向步进明确抛错，另见 [FEM pre/post coupling][fem-step]。

顶点 hard/soft constraint 又是一条状态修正链；显式 forward 里有 soft/hard 调用，所列 backward 并未逐一调用这些约束的反向函数。因此“显式 FEM 有梯度”必须进一步限定是否加入这些约束。实体的 [set_vertex_constraints][fem-constraints]也直接拒绝 IPC，implicit 下需打开相应选项。

### FEM.Cloth 与 IPC 的真实本构

[`FEM.Cloth`][fem-cloth] 类注释称 NeoHookeanShell，但 [IPC 实际消费者][ipc-fem]构造 **StrainLimitingBaraffWitkinShell**，可选 DiscreteShellBending；体积 FEM 统一应用 **StableNeoHookean**。这意味着外部 IPC 不按 `FEM.Elastic.model` 重用原生 stress/Hessian 分派，也不会因为 material 是 Muscle 就自动传递其 active stress。

[Cloth.Base 回退][fem-base]在没有本构时返回零 stress 以便编译，不是原生 FEM 布料物理已经实现的证据。IPC 从外部几何取回位置并调用 entity.set_pos；这段 [回传][ipc-retrieve]不能冒充外部完整节点速度/力遥测。不要把原生与外部两套状态拥有者混在同一“FEM支持”勾选中。

## 6. 耦合器是算法与所有权选择

### Legacy：按实际开关展开的速度/表面响应

[Legacy.build][legacy-flags]将 active solver 与 `rigid_mpm/rigid_sph/rigid_pbd/rigid_fem/mpm_sph/mpm_pbd/fem_mpm/fem_sph` 组合成有效标志。[couple][legacy-order]的消费表如下：

| 组合 | 实际交换位置 | 边界 |
|---|---|---|
| MPM–Tool | mpm_grid_op 内，Tool SDF 改网格速度 | Tool 轨迹是外部规定的，不反馈成自由刚体动力学 |
| MPM–Rigid | 网格速度响应；CPIC 另有 preprocess/p2g 路径 | SDF、coup_softness、摩擦/恢复和 active flags 与刚体-刚体约束不同 |
| MPM–SPH/PBD | mpm_grid_op 的邻域质量/动量交换 | 不是把两种粒子永久合成一种 solver |
| SPH–Rigid | sph_rigid，含碰撞速度修正和压力响应 | 静止流体压力也可能施力；固定 link 分支不同 |
| PBD–Rigid | kernel_pbd_rigid_collide，加可选附着粒子的单向跟随 | 位置约束/动画跟随不等于一个通用双向 joint |
| FEM–Rigid/MPM/SPH | fem_surface_force 的表面交换，再处理 rigid-link constraints | 某函数存在不等于couple调用，例如 fem_hydroelastic 不能只按名字认定当前入口已接线 |

[MPM 网格操作][legacy-mpm]同时处理自身重力和外场；[FEM 表面操作][legacy-fem]、[SPH–刚体压力分支][legacy-sph]读取的是各自存储与量纲。广义上由粒子速度改变 $\Delta v$ 可形成反作用 $-m\Delta v/h$，但源码还可能有压力项、过滤/软化和固定体特判。E3 已讲过 Legacy 刚体–粒子响应，不能把它与 Newton 刚体约束力相等同。

只有某些 forward 核被 [couple_grad][legacy-grad]反向调用：FEM surface force、MPM grid operation。SPH/PBD 自身反向缺失、附着/特殊校正未在此形成完整逆链；“Legacy 有 couple_grad”仍不等于所有打开开关的组合都可微。

### SAP：刚体/FEM 接触优化的另一条路径

[SAP 构建门槛][sap-build]要求 **FP64**；活动 FEM 必须 `use_implicit_solver=True`。接触选项区别顶点/四面体/禁用，刚体–刚体四面体、rigid–FEM、FEM self/floor 由不同 handler 装配；某些 joint equality 的单对象形式被拒绝。

[preprocess][sap-step]更新几何/BVH、接触及正则项，溢出会抛错；couple 在有约束时运行 SAP solve 并写速度。E3 已展开其 Newton/PCG/线搜索与终止参数。它不是给 RigidOptions.solver 换个枚举值，也不复用每一条 Legacy 交换。尤其 MPM 的网格操作和 SPH 的 `_rigid_sph` 缓存消费者依赖 Legacy，不能任意切成 SAP 后保留全部粒子组合并宣称仍被推进。SAP.couple_grad 明确抛错。

### IPC：Genesis 适配层与 libuipc 分开记身份

[IPCCoupler][ipc-import]导入外部 Python 模块 uipc，缺失时要求 pyuipc；[初始化][ipc-init]实际创建 `Engine("cuda", ...)`，这不是根据 `gs.backend` 自动切换的通用 CPU/Metal 算法。这里审读的是固定 Genesis adapter，没有固定外部 libuipc/pyuipc 的精确构建或运行环境，算法内部/性能不在本轮验收内。

[build 的限制][ipc-build]拒绝 rigid 的 batch_links_info、batch_dofs_info、batch_joints_info，并要求参与 solver 的初始 gravity 与 Scene 一致。随后建立每环境 subscene 禁止跨环境接触；它是一个外部 world 的批量隔离机制，不等于可以传入任意异构拓扑。运行时 `solver.set_gravity` 只改 Genesis 缓冲，源码自己指出 IPC world 不消费这次修改。

刚体 material 的 `needs_coup/coup_type/coup_links/enable_coup_collision` 决定哪些 link 交给谁。三种实际策略是 `two_way_soft_constraint`、`external_articulation`、`ipc_only`；external_articulation 要固定基座且存在关节 DOF，其他关节/同步限制还应读具体构建函数。[实体分类][ipc-classify]

[IPC.couple][ipc-step]保存 Genesis 状态→按模式准备→外部 world.advance/retrieve 一次→取回 FEM/刚体→按模式施加反作用或修正刚体配置。`couple_grad` 是 pass，`reset` 要求 `envs_idx is None` 并 recover(0)，E5 的普通 checkpoint 路径也拒绝 IPC。不能把物理状态已复制回来当成梯度、局部 reset、checkpoint 或同一时间帧上的全部观测也已经接通。

## 7. Hybrid、SF 与引擎特色：描述能力要到最后一个消费者

[Hybrid][hybrid]显式断言软部为 MPM.Base；URDF 与 Mesh 两种构造路径分别从 rigid 生成 soft 或反过来。默认 `use_default_coupling=False`，通过关联 group/link/geom 和 `soft_dv_coef` 等参数，在 MPM post-coupling 后追加更新；它在对象构造中包装 solver 方法，没有自动同步生成该包装的 backward。[Hybrid options][hybrid-options]

因此要分别解释 rigid控制、软部粒子输入、两者关联和耦合模式。不能把 Hybrid getter 的 rigid 返回值当软部完整状态；也不能把自定义 association 回调称为任意软体插件接口。MPM muscle group 的整数分配和几何采样属于离散结构，通常不会成为可优化的连续张量。

[SF][sf]实现半拉格朗日回溯/插值、inlet impulse、散度、Jacobi 压力投影和浓度衰减；网格为单位域，dx=1/res。给 jets 后 is_active 才为真；Simulator 明确拒绝 SF batching。该文件的 get_state/set_state、checkpoint、gradient collector 仍为空，普通 material 分派也不接它；这应标成内部、未完成的使用链，而不是“完整烟雾可微模拟”。使用其归一化网格变量时，还需自己建立物理长度/速度标尺，不能把 res 当 m。

## 8. 可微不是一个总开关：前向状态、桥接和反向逐级检查

### Torch 图与 Genesis tape 的连接

[gs.Tensor][tensor]是 torch.Tensor 子类，携带 scene 身份；运算尝试传播该身份，并拒绝混用不同 Scene 的张量。`get_state` 创建的查询对象挂入对应队列；[MPMEntity.get_state / add_grad_from_state][mpm-state]把位置等查询值的梯度写回 Quadrants 内部 adjoint。[`gs.tensor(..., requires_grad=True)`][tensor-creation] 的外部输入则通过实体 input target/buffer 与 `process_input_grad` 回到用户张量。[输入回传][particle-input]

`gs.Tensor.backward()` 先调用 Torch backward，再在有 scene 时调用 Scene._backward；普通 torch.Tensor 无这种自动 scene 回传行为。`detach()` 默认同时去掉 scene 身份；`sceneless()` 是 clone 后清 scene，**不等于 torch.detach**，不能用这两个名称随意替换。[Tensor 方法][tensor]

从现有 Torch 图转入时还要核对 `gs.from_torch`：默认 `detach=True` 会成为新的叶子；只有显式保留图的调用才试图连接原计算链。它按 gs.device 与当前精度转换并 clone，不是零拷贝承诺。创建器在固定实现中拒绝显式 device 参数，报错文字虽然写 GPU，实际目标由 gs.device 决定。[创建与转换实现][tensor-creation]

[Scene._backward][scene-backward]循环回卷外步，对 `gs.Tensor` 类型损失调用 `loss.backward()` 进入这条路径后将 forward/backward ready 置 False，需 reset 后重新进行前向。`Scene.backward(loss)` 是另一个原生便捷入口：先取 SimState/时钟快照，要求保留 Torch graph，显式反传，再恢复快照和 per-env steps。[snapshot 包装][scene-backward-api]沿用的是 SimState，不是 E5 的完整 checkpoint；传感器/控制/外部任务、全局 tape 游标的重启边界仍存在，不能宣称完整进程时间旅行。

### 子步反向和窗口重算

[Simulator 的反向顺序][sim-grad]与正向对应：post_coupling_grad → couple_grad → pre_coupling_grad，solver 循环逆序，最后 process_input_grad。`substeps_local` 是设备中保存的窗口，必须能被 substeps 整除；窗口不足时 load_ckpt 恢复窗口首帧并 `step(in_backward=True)` 重算前向，不能把“窗口只有一个外步”理解成只对最后一步求导。

[`SimOptions`][sim-options]默认可微窗口是一个外步的子步数；长 horizon 通过检查点和重算连接，代价不是零。与 E5 对外 `.gstraj` 文件不同，这些 solver save_ckpt/load_ckpt 保存的是反传所需窗口/输入；SPH/PBD/SF 的空实现不会被上层框架神奇补齐。重算还会调用普通 sensor manager.step，因此不要假设带副作用的任意观测回调都自动符合可重复 tape。

### 一条支持链至少要检查六处

| 检查点 | 正例或入口 | 本固定版本反例/缺口 |
|---|---|---|
| 配置/构建 | SimOptions.requires_grad、材料与积分器检查 | MPM CPIC 拒绝；刚体不支持 elliptic、noslip、扭转/滚动摩擦及其他积分器 |
| 输入 | MPM/Tool 的 target buffer、gs.Tensor输入 | 普通 Python float 材料 E/ρ 不因开启开关就成为可求导输入 |
| 前向 | 状态、投影和接触分支真正执行 | 离散 active/mask、接触拓扑、yield clamp 不处处光滑 |
| 子步反向 | MPM g2p→grid_op→p2g→SVD；刚体专门 adjoint | SPH/PBD/SF缺项；SAP抛错、IPC空实现 |
| 查询桥接 | MPM/FEM/rigid等get_state的梯度收集 | 普通拷贝getter、NumPy图像、sensor缓存不自动连接这条桥 |
| 窗口与恢复 | solver ckpt/replay及input_grad | 特殊约束/Hybrid追加更新无对应完整反向链；局部reset不是可微跳转 |

官方 [differentiable_push.py][diff-example]展示 Tool 输入张量→MPM→state loss→loss.backward 的调用方式，甚至含两次 reset 后重跑；这是固定源的阅读样例，**没有在此执行，也没有以样例存在证明梯度数值正确**。对于梯度正确性，未来应在固定分支/接触模式与适当尺度下进行有限差分等验证；本轮按用户要求不新增实验。

## 9. 刚体反传：解伴随系统，不是重放所有迭代的自动微分

[刚体构建检查][rigid-grad-options]限定 approximate_implicitfast，关闭/拒绝休眠相关路径，拒绝 SAP/IPC、noslip、torsional/rolling；[elliptic 另在初始化拒绝][rigid-grad-init]。实现资格与 E3 的默认 forward 性能选择不同。

[约束 backward][constraint-backward]在当前 active set 上构造隐式乘法

$$
A=M+J^T\operatorname{diag}(D\odot a)J,\qquad
Au=\frac{\partial L}{\partial\ddot q}.
$$

这里 a 是活动约束标志，D 是约束权重，J 是约束 Jacobian；M 与 JᵀDJ 的单位必须按广义坐标配对，不能把转动/平动行未经缩放都当同一 kg 标量。前向使用 Newton 且存在约束时，反传复用按 island 保存的 Cholesky 分解；无约束时转用直接读取 M 的 CG，避免使用该环境未更新的约束分解。前向为 CG 时也用 CG 解伴随系统。CG 使用相对 seed 范数的残差目标并受迭代上限约束；不是把前向 Newton 的每次线搜索都当普通 Torch 图节点逐一反传。

得到 u 后向外传播 mass/J/aref/D/force 梯度，再追溯约束装配、碰撞几何、质量/平滑动力学、积分和 FK。固定 active set 的局部导数在接触进入/离开、摩擦区切换、限位激活处不代表全局光滑性。`u` 的数值误差与前向求解未收敛都影响结果；“loss 有 grad”只能证明某条路径回传了值。

[RigidSolver 反向子步][rigid-backward]还会重建子步并依据 MuJoCo compatibility、constraint disabled 等分支选择不同内核；MPM 的 SVD 反传也有自己的显式实现。不能把这些全部称为同一种自动微分。将模型参数静态读取与针对状态/控制的梯度桥分开，是判断参数辨识接口是否存在的前提。

## 10. 温度与触觉：是物理模型，也可能只是感知模型

### TemperatureGrid 的四阶段与量纲检查

E4 已给出 API、shape、°C 输出与采样时序；这里读 [TemperatureGrid 的实际更新][temp-update]：使用**外步 dt**依次做扩散/内部热源、接触换热、温度钳位、辐射对流；测量侧再加一阶 RC 响应。它在 sensor manager 中演化温度状态，不是让 MPM/FEM 本构自动热膨胀或温度软化。

[扩散核][temp-diffusion]对镜像扩展的三维网格作 FFT，表示零通量边界，频域更新为

$$
\widehat T^{n+1}(k)=\frac{\widehat T^n(k)}{1+\Delta t\,\alpha\,|k|^2},\qquad
\alpha=\frac{\kappa}{\rho c_p}.
$$

κ 为 W/(m·K)，ρc_p 为 J/(m³·K)，α 为 m²/s，k 为 rad/m。传入 heat_generation 按 W/m² 除 dz 变成体热源，再作 ΔT=dt·Q_vol/(ρc_p)；不是直接把 W 当温升。镜像边界与随后加入的接触/表面通量是分裂处理。

[接触核][temp-contact]用刚体 contact patch 估计面积、深度修正、等效导热率 `2*k_a*k_b/(k_a+k_b+eps)` 与 volume/area 长度尺度换热；可选 link lumped temperature 对两个 link 施加相反功率。局部传感网格与 lumped link 并非同一个有限元全域温度场，不能据此宣称整场离散能量严格守恒。

[辐射/对流实现][temp-surface]计算 εσ(T_K⁴−T_amb,K⁴)+h_c(T−T_amb)，再直接除 ρc_p·volume；调用处没有显式乘暴露面积。[TemperatureProperties/TemperatureGrid 字段说明][temp-options]明确给出密度 kg/m³、比热 J/(kg·°C) 与对流系数 W/(m²·K)；[build][temp-build]直接以 density×specific_heat 保存 ρc_p。按这些 SI 单位，前者是面热流 W/m²，后者是热容 J/K，量纲还缺面积因子。因此本固定实现应保留这一**源码量纲疑点**，不能将其输出当已标定的热能守恒解。温度钳位到±1000°C也不构成稳定性/物理合法性证明。

[测量滤波][temp-filter]是显式 `T_meas += dt/tau*(T_raw−T_meas)`，tau≤0时直接取raw；没有把 dt/tau 自动夹到[0,1]。大于1可能过冲，更大的比值可能失稳。ground truth 跳过此RC，但仍是前述模拟温度，不是硬件真值。

### ElastomerTaxel 的几何→位移算子

E4 区分了 force taxel 与 marker displacement；[ElastomerTaxel][tactile-build]必须挂到有碰撞几何的 rigid link。先做 depth query，再把压入深度场 H 通过空间核扩散成切向/法向位移，并叠加接触锚点到当前位置的剪切贡献。这个路径不会因为类名 Elastomer 就让刚体碰撞网格发生完整 FEM 形变。

[FFT 核][tactile-kernel]的局部分支是 offset×exp(−λ_d r²) 与法向 Gaussian；`compressibility` 在局部和长程核间混合。给厚度 h 时，长程网格核使用无量纲 q=|k|h 的 bonded incompressible layer transfer：

$$
S(q)=\frac{2q^2}{\sinh(2q)-2q},\qquad
\widehat u_t=-i\widehat k\,S(|k|h)\,\widehat H.
$$

源码会对 q 限幅、小 q 用级数、对混合核作峰值归一化；其余法向指数/scale 是模型参数，不能把这个表达式当完整材料辨识结果。二维网格 FFT 做足够零填充防环绕；非严格规则的二维布局会使用平均间距/法向近似并警告；非网格走直接求和与正则化长程核，不能宣称两条路径在任意布局下严格同解。[直接核][tactile-direct]、[FFT 卷积][tactile-fft]与[更新分派][tactile-update]

[剪切][tactile-shear]依赖接触进入时锚点、深度/候选过滤和滞回状态，退出后需清理；同一 pose 不必给相同 marker 历史。回放若只存 rigid qpos，没有这些内部历史就不等于完整传感重放。FFT/Torch算子存在，也不证明前面的离散BVH/contact选择和整个 sensor cache 已接到 Scene 的动力学 adjoint。

## 11. 原生扩展点与外部身份

| 层 | 可直接追踪的入口 | 所有权/稳定性边界 |
|---|---|---|
| 任务编排 | Scene pre-step callback、原生 entity 控制 | E2/E5已展开；步进线程执行，不是新solver注册表 |
| 数据记录 | Recorder/RecorderManager.register_recording | E5已展开；CPU数据所有权、线程和cleanup明确 |
| 状态变化订阅 | Solver.subscribe(Subscriber)、StateChange、@mutates | Genesis内部 Python API；只通知打标签的状态变更，不是每个kernel或参数写入事件 |
| 材料本构 | MPM的F/应力dispatch，FEM显式stress与隐式能量导数 | 每组函数都要由实际solver消费；只填一组不代表其他模式支持 |
| solver/coupler | Simulator 固定构造列表与类型分派 | 没有通过一个任意类参数即自动添加新物理的承诺；需接state/build/step/backward/checkpoint/vis全链 |
| sensor | options类型→SensorManager具体class→更新/缓存/read | 必须明确shape/dtype/frame/timestep/history及梯度；E4的RGB特殊路径不能忽略 |
| IPC | Genesis adapter → pyuipc/libuipc CUDA world | 外部核心版本单列；Genesis版本不等于其版本 |
| 渲染 | Rasterizer / BatchRenderer(Madrona) / RayTracer(Luisa) | E4固定adapter与平台边界；不把外部二进制或可微支持计作本轮验收 |
| 学习 | 官方任务→TensorDict/RSL-RL | E5只有固定Genesis调用方；外部训练器下界版本不是精确锁定 |

[Subscriber/mutates][subscriber]区分 GEOMETRY、DYNAMICS；质量、摩擦、增益等模型参数不在该状态通知类别。嵌套 setter 合并通知，lazy subscriber 只累计 pending，消费者读完自行 clear；带 link filter 时用全局 link 索引及子树覆盖。绕过 setter 写内部 view 不会自动替你维护这些订阅和缓存。

[Scene.add_force_field][force-field-api] → [Simulator][force-field]虽然把对象放入各 solver 的 `_ffs`，实际消费者才决定作用范围：[SPH][sph-force-field]/[PBD][pbd-force-field] 在粒子加速度核中调用 get_acc，[MPM 在 Legacy grid_op][legacy-mpm] 调用；刚体/FEM/SF 不因此自动获得同样的外场消费。扩展时从实际 get_acc 调用点判断单位 m/s²、粒子/网格参数和时间，不能把一个登记操作当全引擎通用施力。

需要自定义 solver 时，最小完整契约包括 material分派、active与build、统一时间、状态/所有权、pre/post coupling、输入与输出梯度、reset与checkpoint、几何/传感可见性。Base Solver 的 data 默认直接抛“cannot be checkpointed yet”，所以继承基类并不实现恢复。这里提供原生结构的阅读方法，不新造插件框架或跨引擎 wrapper。

## 12. 原创最小接口片段

[extensions_api.py](../examples/extensions_api.py)提供两个未执行函数：

- `mpm_goal_loss` 从 native MPMEntity.get_state 取 pos，按固定目标及长度尺度构造无量纲标量损失；保留 gs.Tensor/scene 连接，不做 E5 的 detach/CPU copy。前提是实体粒子全部活动、已有可微前向、目标 shape=(3,) 且属于同一设备/无其他Scene身份。此教学目标不声称是控制器、任务成功或梯度验收。
- `watch_rigid_geometry` 直接创建内部 Subscriber 并注册到 native solver，返回 lazy handle；调用者读取 pending 后 clear。它只观察 @mutates 的几何变更，不能当每个物理step的事件总线。

没有 init/build/step/backward 主程序，没有模型下载或优化循环。调用方若未来选择 `loss.backward()` 与 `scene.backward(loss)`，必须按第8节分别处理前向继续和恢复边界；本仓没有运行任一条。

## 13. 组合能力表与审查办法

下表是固定源码证据，**不是运行通过矩阵**。

| 组合/操作 | 源码结论 | 审查落点 |
|---|---|---|
| Rigid forward + Legacy | 有完整刚体路径，E3详细展开 | solver/摩擦锥/积分器仍分开记录 |
| MPM + Legacy + Tool | 有前向、输入/状态桥和反向内核 | CPIC、特殊约束/材料非光滑处另限 |
| FEM explicit + Legacy | 有应力推进和基础反向 | material stress实现、hard/soft附加约束的反向缺项 |
| FEM implicit + SAP | 有兼容模型下的前向链，FP64 | stable_neohookean隐式导数缺失；无SAP梯度 |
| FEM Cloth/volume + IPC | 外部本构与状态回传 | CUDA外部身份、组合限制、无couple梯度/局部reset |
| SPH/PBD + Legacy | 有前向和若干耦合 | backward/checkpoint空实现；DFSPH全batch停止尺度 |
| MPM/SPH/PBD + 任意coupler | 不成立为通用承诺 | Legacy的必需grid/缓存消费者不在其他coupler中 |
| rigid batch异构 + IPC | rigid INFO批量构建检查拒绝 | E5的异构能力不是跨所有coupler的乘法组合 |
| SF普通material实体/批量/反传 | 分派缺口、批量拒绝、梯度状态接口不完整 | 不以SF类存在填“支持” |
| sensor/renderer + requires_grad | 不能总括成立 | 查询值来源、NumPy/caches/BVH以及实际adjoint消费者 |

批量状态也不能与批量拓扑画等号。以 [MPM fields][mpm-layout] 为例，x/v/F/C 等动态状态是 `(substeps_local+1, n_particles, B)`，active 也带 B；mass、material_idx、muscle_group/direction 则仅有 `n_particles` 维，材料回调列表共享。不同环境可有不同动态状态/活动掩码，但不能据此给每行任意不同的粒子数、材料拓扑或本构函数。E5 的 `morphs` 异构分支是**刚体**描述及共同结构检查；不能推广到所有粒子/网格实体。

渲染排列 `env_spacing` 不创造物理隔离；隔离要看物理数组及耦合器的环境索引。Legacy 核按同一个 i_b 交换，IPC用 subscene 禁止跨环境接触；DFSPH 的停止误差又是跨 B 的归约。物理状态分开、结构共享、数值停止共享是三种不同性质，需要分别记录。

读一个新能力时先找到创建入口和真正读取字段的函数，再检查初始化资格、每步调用、输出所有权、反向与恢复。注释写“支持”但函数pass/raise/没有调用点时保留缺项；注释过时但实际有路径时写清固定实现，如 E5 的多link异构。所有结论绑定 [sources.json](sources.json)，升级版本不能只换页顶版本号。

## 14. 阅读练习与答案

1. **Rigid 是 Kinematic 子类，为什么不进入 KinematicSolver？** 分派选择匹配 material_cls 中最派生的类，Rigid更具体。
2. **MPM与SPH各指定不同dt能各自多速率吗？** 当前build拒绝不同推导子步数；活动时间solver统一交换间隔。
3. **只审 MPMSolver 能找到完整重力推进吗？** 不能，Legacy.mpm_grid_op包含网格速度、重力/外场和耦合。
4. **MPM Sand.friction_angle=45 是刚体μ=45吗？** 不是，它是度数并转换内部压力相关塑性系数。
5. **DFSPH 增加B只增加吞吐，不变收敛条件吗？** 当前误差跨B求和但仅除n_particles，统一停止尺度随batch内容变化。
6. **PBD stretch有compliance就等于完整标准XPBD吗？** 不等于；要核对λ是否保存、relaxation和迭代更新，volume另有表达式差异。
7. **FEM stable_neohookean可直接用于原生implicit吗？** 不能据名称这样推断；其隐式gradient/Hessian明确未实现。
8. **FEM linear_corotated有energy实现就可走explicit吗？** 不行，explicit stress方法明确raise。
9. **FEM.Cloth由注释中的NeoHookeanShell执行吗？** 固定IPC消费者实际创建StrainLimitingBaraffWitkinShell及可选弯曲项。
10. **SPH有process_input_grad就说明流体可微吗？** 不说明，关键pre/post子步和输出梯度路径仍为空。
11. **sceneless与detach作用相同吗？** 不同；前者clone后清Scene身份，后者切Torch梯度且默认清Scene。
12. **substeps_local只容纳一外步，就截断整个horizon梯度吗？** 不是；支持的solver按窗口checkpoint/replay，空实现不能享受该保证。
13. **SAP和IPC的无梯度行为完全相同吗？** 不同：SAP明确抛错，IPC couple_grad为pass；刚体构建另有组合拒绝，不能将静默缺项当成功。
14. **温度传感器类意味着温度会影响FEM弹性模量吗？** 没有这样的消费者链；它演化sensor温度模型，且表面热流量纲疑点须保留。
15. **ElastomerTaxel的FFT结果可当FEM形变真值吗？** 不可，它是几何深度/剪切历史到位移的模型，布局近似和kernel参数不同。
16. **force_field登记到所有solver就对所有物体生效吗？** 不会；需查get_acc实际消费者，当前列出的原生路径在SPH/PBD及Legacy-MPM。
17. **订阅GEOMETRY会通知质量变化吗？** 不会；模型参数不属于该StateChange类别，内部数组直写也不会自动通知。
18. **刚体loss有梯度证明接触拓扑处处光滑吗？** 不证明；伴随系统按当前active set求局部导数，切换和求解误差仍有影响。

对应 [Issue #7](https://github.com/huangkiki/genesis-atlas/issues/7)，最终静态检查及限制见 [E6 验收记录](e6-acceptance.md)。下一项 E7 将完善 A0 安装、双路线整体审校和 DexLab 复用入口；不会把本章源码能力表换成未做过的实验结论。

[dispatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L77-L158
[base-solver]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/base_solver.py#L314-L388
[kinematic-material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/kinematic.py#L1-L18
[rigid-material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/rigid.py#L1-L35
[kinematic-solver]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L40-L155
[tool-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/tool_entity/tool_entity.py#L175-L211
[pbd-add]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py#L245-L324
[fem-entity]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/fem_entity.py#L450-L588
[hybrid]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/hybrid_entity.py#L51-L188
[sf]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sf_solver.py#L1-L304
[sim-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L164-L241
[step-order]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L428
[mpm-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L34-L74
[mpm-build-grad]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L205-L248
[mpm-p2g]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L303-L476
[mpm-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L550-L636
[mpm-base]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/base.py#L36-L102
[mpm-elastic]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/elastic.py#L1-L64
[mpm-liquid]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/liquid.py#L1-L52
[mpm-plastic]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/elasto_plastic.py#L1-L71
[mpm-snow]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/snow.py#L1-L74
[mpm-sand]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/sand.py#L1-L84
[mpm-muscle]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/muscle.py#L1-L53
[sph-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py#L704-L774
[sph-pressure]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py#L245-L381
[sph-material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/SPH/liquid.py#L1-L31
[sph-df]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py#L487-L649
[pbd-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py#L753-L842
[pbd-constraints]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py#L408-L520
[pbd-material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/PBD/elastic.py#L1-L45
[fem-explicit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py#L432-L493
[fem-inertia]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py#L496-L582
[fem-implicit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py#L936-L963
[fem-elastic]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/elastic.py#L61-L222
[fem-muscle]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/muscle.py#L1-L56
[fem-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py#L969-L1012
[fem-constraints]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/fem_entity.py#L955-L1023
[fem-cloth]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/cloth.py#L1-L69
[ipc-fem]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L321-L394
[fem-base]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/base.py#L67-L109
[ipc-retrieve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L1035-L1070
[legacy-flags]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L43-L104
[legacy-order]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L874-L939
[legacy-mpm]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L320-L465
[legacy-fem]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L499-L684
[legacy-sph]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L190-L252
[legacy-grad]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py#L941-L963
[sap-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/sap_coupler.py#L182-L319
[sap-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/sap_coupler.py#L619-L708
[ipc-import]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L1-L119
[ipc-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L268-L305
[ipc-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L184-L218
[ipc-classify]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L220-L266
[ipc-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py#L808-L870
[hybrid-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/hybrid.py#L1-L47
[tensor]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/grad/tensor.py#L1-L118
[tensor-creation]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/grad/creation_ops.py#L45-L105
[mpm-state]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/mpm_entity.py#L142-L347
[particle-input]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/particle_entity.py#L332-L481
[scene-backward]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1498-L1512
[scene-backward-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L967-L1036
[sim-grad]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L378-L485
[sim-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L20-L78
[diff-example]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/deformable/differentiable_push.py#L1-L145
[rigid-grad-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L740-L781
[rigid-grad-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L240-L265
[constraint-backward]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/backward.py#L11-L248
[rigid-backward]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1640-L1731
[temp-update]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L693-L793
[temp-diffusion]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L62-L129
[temp-contact]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L281-L395
[temp-surface]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L398-L454
[temp-filter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L457-L476
[tactile-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L1952-L2060
[tactile-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L959-L1049
[tactile-direct]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L1262-L1333
[tactile-fft]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L1794-L1870
[tactile-update]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L2223-L2402
[tactile-shear]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L1668-L1743
[subscriber]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/base_solver.py#L34-L193
[force-field]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L160-L162
[force-field-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L812-L828
[sph-force-field]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py#L290-L315
[pbd-force-field]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py#L373-L390
[mpm-layout]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L83-L154
[temp-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L402-L470
[temp-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L523-L590
