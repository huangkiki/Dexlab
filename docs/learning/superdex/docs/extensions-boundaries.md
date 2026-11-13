# 特色 Actor、可微求解与扩展边界

本章深化 B4 的可微实现、补齐 B6 的原生特色/构建扩展，并提供 B7 从模型到输出的两条综合源码追踪。E7 仍保留 A0 安装身份专题与全路线最终验收。先读 [E1](modeling-state-time.md)的状态/惯量/精度、[E2](control-robotics.md)的控制/FK、[E3](contact-solvers-forces.md)的接触和求解，再用 [E4](sensors-rendering.md)、[E5](batch-learning-data.md)区分媒体、学习与数据责任。数学先修是弹性势能、矩阵微分、线性求解和三维旋转。

固定官方源码仍是 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`；候选包1.0.0、Python binding、C++ build、Studio/viewer宿主分别记录。**本文只有源码、文档链接和语法检查；没有 native import、模型编译、JIT、模拟、渲染、训练、实验或数值梯度检验。** [验收记录](validation-e6.md)与[来源清单](sources.json)可独立核对。下面的“支持”若未另说，指固定代码路径存在且其限制已读，不是已安装二进制或物理正确性验收。

## 1. 先看对象、语言接口与构建身份

| 能力 | 原生入口/层 | 固定源码边界 |
|---|---|---|
| 刚体与关节体 | Physics `Scene.create_rigid_actor` / `create_articulated_actor` | RIGID/ARTICULATED；FK/约束/隐式跟踪见E2，不能从关节数量推断完整状态大小 |
| 体积软体 | Physics `create_soft_actor(SoftActorParams)` | 四面体FEM；普通入口自身有表面采样，但默认不提供被其他Actor查询的collider |
| 薄壳/布料 | Physics `experimental.create_shell_actor` | SHELL明确experimental；三角表面、面密度、膜/弯曲能；不是任意3D体材料直接输入 |
| 弹性杆 | Physics `experimental.create_rod_actor` | ROD明确experimental；位移、扭转和frame历史；不能当无质量tendon |
| 骨架+软组织 | Physics `create_soft_skinned_actor` | 关节骨架和嵌套软体/skin；能量配置和参考frame有限制，当前可微不支持skinning |
| ROM/超降阶/Deep Flow | 主要C++ experimental接口、资产和内部装配 | 构建开关、资产和互斥条件；部分C++字段未绑定Python，neural CROM直接模型分支已deprecated |
| 一步反向求导 | Physics `diffsim` | rigid/articulated、Backward Euler、相邻原生状态、支持的输入/输出backward函数 |
| 完整 step Jacobian | Physics `diffsim.get_step_jacobian` | 实现比通用描述更窄：只接受独立rigid Actor，不接受articulated；三连续状态、column-major输出 |
| 机器人/学习/GUI扩展 | Robotics / Lab / Studio及外部依赖 | Bot/控制器/任务/媒体分别拥有资源，不因装在同仓就成为一个内核API |

[Actor/API定义][api]、[experimental头][exp]、[生成Python绑定][expbind]和[Scene实现][scene]一起读。不要只读C++ struct便写出一个不存在的Python构造参数，也不要把 `experimental` 当作“已经实验验证”。

## 2. 体积软体：从材料到节点残差

### 2.1 四面体、位移与本构

[SoftActorParams][api]要求TetrahedralMeshShape。[初始化][softinit]把体网格、边界网格、可选visual embedding分别注册，并为节点位移建立局部到全局映射。视觉面数不是FEM自由度数；根transform也不是整个软体形变状态。固定/受限节点、ROM和skinning会进一步改变有效变量，必须读Actor实际DoF/pose接口。

令参考坐标为 $X$（m）、位移为 $u(X)$（m），现坐标 $x=X+u$，形变梯度 $F=\partial x/\partial X$ 无量纲。局部能量密度 $\Psi(F)$ 的单位为Pa，离散内能和节点内力可写成：

$$
E_{\mathrm{int}}(u)=\sum_e\sum_a w_{ea}\,\Psi(F_{ea}(u)),\qquad
f_{\mathrm{int}}=-\frac{\partial E_{\mathrm{int}}}{\partial u}.
$$

$w_{ea}$包含参考体积/求积权重（m³），所以能量是J、节点力N，位移Hessian的单位N/m。这里是解释FEM装配的形式，不宣称所有元素/材料使用同一求积规则。[soft装配][soft]选择本构响应、惯性与重力项，[FEM stress][femstress]在求积点构造F、应力与切线并累加节点残差；[deformable公共实现][deformable]负责接触/边界条件等共享部分。它们与E3步进链组成同一个离散问题；接触penalty的Pa/m不等于材料Young模量Pa。

一个可以直接核对的本构例是[线弹性实现][linear]:

$$
\varepsilon=\tfrac12(F+F^T)-I,\qquad
\Psi=\mu\|\varepsilon\|_F^2+\tfrac12\lambda(\operatorname{tr}\varepsilon)^2,\qquad
P=2\mu\varepsilon+\lambda\operatorname{tr}(\varepsilon)I.
$$

$P=\partial\Psi/\partial F$是第一Piola应力（Pa），$\lambda,\mu$是Lamé参数（Pa）。小应变/小转动假设在这里很重要：大刚体转动下该线性应变未必为零，不能把线弹性材料当成任意大转动下的客观超弹性模型。参数接口和有效范围见[linear参数][linearparams]及[材料验证][materialcheck]。

### 2.2 材料名称与数值修改

公开枚举包含 LinearElastic、StVenantKirchhoff、NeoHookean、ARAP、ActiveNeoHookean、ActiveShapeTargetingARAP。StVK基于非线性应变，压缩下仍可能有不良数值行为；ARAP类惩罚局部偏离旋转；active材料引入纤维或shape-target输入，**不自带生物神经激活、温度或流体控制系统**。应逐项按原生参数而非“软”这个词选择模型。[API][api]给出语义，[batched材料入口][materials]显示多种实现共存；存在多个Neo-Hookean实现时，不把同名论文公式直接套到任意分支。

这里可以查清公开 NeoHookean 的具体分派：[公开参数][materialparams]将 `NeoHookeanMaterialParams` alias 为 `SmithNeoHookeanMaterialParams`；[soft装配][soft]的 `SetMaterialParams`选中 `neoHookean`，再经按参数类型分派的 `MakeBatchedConstitutiveResponse`，由[Smith factory][smithfactory]调用[Smith实现][smith]。其能量是：

$$
\hat\mu=\tfrac43\mu,\quad\hat\lambda=\lambda+\tfrac56\mu,\quad
\alpha=1+\frac{3\hat\mu}{4\hat\lambda},\quad
I_c=\|F\|_F^2,\quad J=\det F,
$$

$$
\Psi(F)=\frac{\hat\mu}{2}(I_c-3)
+\frac{\hat\lambda}{2}(J-\alpha)^2
-\frac{\hat\mu}{2}\log(I_c+1).
$$

$\lambda,\mu,\hat\lambda,\hat\mu$及能量密度为Pa，其余上述量无量纲。重参数化使小变形极限与线弹性参数相容；常数能量偏移不影响力。这里没有 $\log J$，因此不能把教科书中 $J\le0$ 的对数奇点套到这个分支；它仍不保证单元永不反转或Newton必收敛。这条身份只针对该固定提交的公开 NeoHookean 分支，active材料及别的Neo-Hookean实现须各自追踪。[对应参数][smithparams]与PSD策略仍要单独核对。

`MaterialPsdStrategy`控制材料切线的PSD处理，支持集合与默认值按材料核对。PSD projection/FAST一类策略修改求解用切线，不等于修改或验证了真实材料，也不保证整场景严格正定：刚体模态、约束、接触和时间离散仍参与。前向求解为了稳健采用的近似矩阵，与反向梯度要逼近的实际残差导数不能混为同一对象。

同类型的per-element material数据可以覆盖uniform material；PSD策略仍按Actor统一，并检查两边明确指定时是否一致。`has_inertia=False`用于准静态选择，`has_stress=False`关闭弹性项；两者会改变问题而不是单纯提速。mass damping与stiffness damping的系数分别是1/s和s；质量或应力项被关闭时对应阻尼也可能不生效。[soft初始化][softinit]含这些验证与警告。

尤其不要仅凭参数名套用全局 Rayleigh 阻尼。[材料参数注释][materialparams]把 stiffness damping 定义为 total-Lagrangian Kelvin–Voigt 形式：$S_{\mathrm{visc}}=\beta C_0:\dot E_G$，其中 $E_G=\tfrac12(F^TF-I)$、$C_0$是零形变处对Green应变的材料切线，$\beta$为s。因此黏性应力为Pa，理想刚体运动的Green应变率为零，不产生这一黏性应力。`stiffness_damping_include_geometric_term`改变Newton切线是否包含几何项；源码明确不改变残差或收敛解，不宜把它描述成更强阻尼。

## 3. 薄壳、杆与三种tendon建模

### 3.1 薄壳不是给体材料去掉一维

`ShellMaterialParams`用膜Lamé参数（N/m）、弯曲系数（N·m）、面密度（kg/m²）。[shell conversion][shell]的 `shell_material_params_from3d_isotropic(E,nu,rho,t)`在各输入有限、$E,\rho,t>0$、$-1<\nu<0.5$时，以平面应力与板弯曲假设转换：

$$
\mu_m=\frac{tE}{2(1+\nu)},\quad
\lambda_m=\frac{tE\nu}{1-\nu^2},\quad
D=\frac{Et^3}{12(1-\nu^2)},\quad
\alpha_b=D\nu,\quad\beta_b=D(1-\nu),\quad\rho_A=t\rho.
$$

这里 $t$ 为m，$\rho$为kg/m³；弯曲随厚度三次方变化，不能拿体积密度直接填到shell density。该方便转换不是完整工程壳理论适用性的证明，原生注释明确膜模型和图形学式弯曲项可以独立组合。[shell初始化][shellinit]建立三角膜与弯曲stencil，而非四面体内部体积网格。

[官方T-shirt例][tshirt]展示 `ShellActorParams`、该转换、point-cloud self-contact及solver设置。它的交互默认值不是收敛保证，本章不运行也不建议据此量化性能。self_contact是高度experimental选项，点距与半径关系见第5节。

### 3.2 杆保留扭转与frame历史

[Rod实现][rod]每节点有3个位置位移加1个扭转槽，pose还保存每段frame axes；源码布局为 `4*numNodes + 3*numElements`，velocity/DoF布局是 `4*numNodes`。开杆末端的一个twist槽是块结构padding并被固定，闭环杆则不是；不能把4N全部当作独立的物理扭转自由度。材料frame的运输、recenter和历史参与积分，只保存中心线位置不足以恢复状态。

对均匀圆截面小应变弹性杆，以半径 $r$（m）解释[原生字段][exp]：

$$
A=\pi r^2,\quad I=\pi r^4/4,\quad J_p=\pi r^4/2,\quad
\rho_\ell=\rho A,\quad I_\ell=\rho J_p,\quad
k_a=EA,\quad k_b=EI,\quad k_t=GJ_p.
$$

线密度kg/m、轴向旋转惯量每长度kg·m、axial_stiffness为N，flexural/torsional_stiffness为N·m²。对非圆截面扭转常数不能一律用极面积矩；源码头明确指出这个限制。`axial_stiffness`不是整根杆的平移弹簧N/m；长度 $L$ 下的轴向结构刚度才近似 $EA/L$。弯曲/扭转可以设零形成某些cable-like模型，但旋转惯量与扭转刚度不能同时为零，约束还必须消除相应零模态。

[悬挂质量例][rodsample]从材料/截面积构造rod，末端用node-to-rigid及rod-element-rotation约束接刚体。它说明的是弹性中心线及角度耦合，不是把多条刚体铰链包装成杆；资产含frame/连接关系，视觉管道只是一层可视网格。

### 3.3 Rod、spatial tendon、linear transmission各自保留什么

[官方对照例][tendon]的三条建模路径适合作静态比较，不是本仓新实验：

| 路径 | 原生变量与力映射 | 省略的物理 |
|---|---|---|
| Elastic rod Actor | 位置、扭转、frame、分布质量/弹性，可设接触 | 成本和约束更多，不能假定它等价任意真实绳索 |
| Spatial tendon | 按link-local waypoint和linear-joint元素构成长度 $\ell(q)$ | 不产生一条分布质量的软体中心线；并非通用绳索自碰撞/滑轮求解器 |
| Linear transmission | $s(q)=\sum_i c_i(q_i-q_i^0)$、常数Jacobian | 固定moment arm/gear ratio，无法自动表达任意姿态相关绕线几何 |

若一维广义力 $f_s$ 与位移 $s$功共轭，则虚功一致性给出 $\tau=J_s^T f_s$。若 $s$是长度，$f_s$为N、旋转关节对应项为N·m；系数是m/rad而非始终无量纲。Displacement/Force actuator各有 `allow_compressive_force`，默认为rope-like单向语义；McKibben参数提供压力/编织几何到驱动力的原生模型入口，但压力Pa不是CFD状态场。[experimental定义][exp]和E2的控制链界定实际责任。

## 4. Skinning、ROM和Deep Flow

### 4.1 软组织与骨架的耦合

`SoftSkinnedActorParams`由skeleton和嵌套soft params组成，soft形状必须在骨架参考frame中，nested `world_from_local`为identity，整体摆放由骨架 `world_from_root`给出。若有skin，接触采样使用skin表面及blending数据，不再简单等于每个软体独立外表面。nested soft名称参与映射，不只是UI标签。[API][api]、[soft-skinned实现][skin]与[官方软皮肤例][skinsample]给出配置链。

应避免能量重复：嵌套项的gravity关闭，由组合配置决定；惯性/应力可在unposed软体或skinned组合上定义，不能同时重复计入同一项。每个软体必须通过节点约束或ROM子空间限制一部分DoF，否则可能留下不必要零模态；有skin时dynamic hyper-reduction被限制。视觉blendshape并不自动拥有这些力学项；反过来，物理skinning也不代表每个output都支持可微。

### 4.2 ROM的降维与近似从哪里来

线性ROM的教学模型是把全节点位移 $u\in\mathbb{R}^{3n}$写为 $u=Bz$，$z\in\mathbb{R}^{r}$、$r\ll3n$；$B$的归一化决定 $z$的单位，不能强行给所有ROM坐标标m。对常基矩阵有：

$$
r_z=B^T r_u,\qquad K_z=B^T K_u B.
$$

[ROM装配][romsystems]通过 `CRomJacobian`投影full residual和dResidual，支持Actor-level或element-level投影；后一种可以避免显式形成完整FOM残差/矩阵。对于非线性映射 $u=g(z)$，$J=\partial g/\partial z$随状态变，精确Hessian还含映射二阶项，不能把上述常基公式无条件当作整个实现。原生还有rigid transform和投影策略，具体使用哪些近似必须看分支。

超降阶则近似求积：从全部体/边界元素换成活跃样本及权重。它减少装配范围，不是只减少未知量，也不意味着接触细节原样保留。[RomParams][exp]指定asset内的source及hyperReduction，部分策略根据接触改变活跃元素；[初始化][rominit]验证活跃节点数与reduced dimension，欠定配置会报错。接触变化、采样更新、ROM/FOM切换都是额外分支，不能从FOM稳定推断所有ROM轨迹或梯度相同。

### 4.3 实际可达性的四道检查

1. **C++功能开关**：[physics config][pconfig]的 `MOCHI_ENABLE_ROM_ACTORS`和`MOCHI_ENABLE_DEEP_FLOW_ACTORS`默认取 `MOCHI_INTERNAL`；[core config][config]未覆盖时该值为0。关闭时ROM-bearing资产可能仍能加载，但不代表可创建ROM Actor；Deep Flow创建也有独立门限。自定义构建可以覆盖，因此不能把header默认值当成任何已装wheel的事实。
2. **资产/分支**：[ROM初始化][rominit]从asset ROM group按source查找，或解析 `polynomial_crom_order_N`。Polynomial CROM仅接受阶数0–4，已含rigid transform，不能再重复加rigid DoF。直接 `NeuralNetCromData`模型分支返回“deprecated”错误；其他neural/adaptive源码仍存在，不等于这个被拒绝入口可用。
3. **Python绑定**：[生成绑定][expbind]中 `ExperimentalSoftActorParams`只暴露collider_type、sdf、flow、use_recentering；C++ `rom`字段没有对应公开Python绑定，也没有这里可直接调用的 `RomParams`构造类。不要写 `ExperimentalSoftActorParams(rom=...)`教程。C++路径存在和Python入口可达是不同结论。
4. **组合限制**：标准tetrahedral-map SDF不能与ROM组合；Deep Flow允许另一种映射，但强制单一island，并不等于更快。ROM adaptivity不支持Deep Flow或recentering组合，ROM/FOM switching也不支持Deep Flow；有skin时还有额外限制。以真实初始化error/assert为准，而非枚举或参数字段列表。

### 4.4 Deep Flow里的“flow”不是流体

[experimental API][exp]把Deep Flow描述为由神经网络近似的shape mapping；[soft SDF初始化][softinit]把它用于reference/current映射与碰撞查询，所有相关actor被强制放入单island以合并查询。某些计算类型要求libtorch，但模型文件、计算类型与build仍需分别取证；本章不引入外部Torch实现或下载权重。

因此不能把Deep Flow、active elasticity或McKibben pressure字段解释成原生Navier–Stokes、热传导、电磁或流固耦合求解器。在本章所核对的公开Actor创建API、experimental定义和初始化路径中，没有这些场方程的完整接口与闭环求解证据。若应用外接此类求解器，需要明确交换状态/载荷、时间同步、迭代耦合和能量一致性；当前没有虚构一个多物理插件API填补缺口。

## 5. 接触几何与精度要独立核对

E3已讲接触律与几何平均材料组合；这里针对特色Actor补足几何身份。`colliding`提供求积样本，`collider`提供被查询的几何，两个角色不对称。普通soft可把自己的样本送到rigid collider；它的默认ColliderType None并不等于“完全没有接触”，但不能因此保证另一个soft能查询它。

[soft初始化][softinit]的experimental collider只接受None或Auto/Sdf，Sphere/Box/Mesh/Plane/PointCloud分支拒绝；Auto在这里走SDF，不能借用rigid的Auto推断。非Deep-Flow soft使用tetrahedral map回到参考形状，且设置接触threshold/default extra padding为0；ROM与此map不兼容。网格SDF分辨率、映射误差和参考网格质量是独立误差来源。

[PointCloudColliderParams][exp]的radius是点对penalty相互作用长度m，不是随便增大就更准确的“物体厚度”。求积点间距远大于radius时可能穿过点之间；增加接触采样密度与增加半径改变的几何效果不同。源码还用 `radius^(-integralDim)`作collider侧接触penalty的量纲修正，曲线/表面分别对应不同积分维度。self-contact排除参考配置相近点，exclusion ratio要求大于1；薄壳默认PointCloud，杆默认None、Auto转PointCloud，均不该套用一张通用collider兼容表。

FP64、几何分辨率、求积密度、solver容差、步长、材料模型是不同精度轴。`MOCHI_USE_DOUBLE_PRECISION`决定 `real`；部分能量累加可用double而状态仍float，因此“某处有double”不证明FP64核心。E1的 `SUPERDEX_PRECISION`必须在import前选择匹配payload；本章没有导入确认。较高精度减少舍入，不补回未建模的薄壁、自碰撞、迟滞或不正确的坐标尺度。

原生 `use_recentering`把软体局部位移保持在较小尺度，改善远离初始位置时的数值条件，但会改变根transform/局部坐标分解；不应把recenter后的局部位移直接与此前世界位移相减。soft-skinned忽略该选项，ROM adaptivity组合又有约束。跨引擎或DexLab数据复用仍须保留原frame/units/config，不能用当前默认值修补历史 #124。

## 6. 可微场景的前提与输入/输出契约

### 6.1 启用会改变配置，不是贴一个autograd标签

[MakeSceneDifferentiableInternal][scene]先检查Backward Euler，再验证现有Actor；rigid支持，articulated调用[ValidateDifferentiabilitySupport][articulated]，存在skinning则拒绝。随后启用components/island adjoint状态，并调用 `ApplyImprovedConvergenceSettings`。该函数把frictionWithColliderNormal设为true、Newton–Euler惯性关闭、implicitNormalForceForDissipation设false、explicitNormals设true、line search设Armijo且至少一次迭代。用户原设置可能被覆盖并警告；求导前后的前向配置身份不能无记录地混用。

public stub建议double precision；变量步长仍有未测试注记。reverse BackPropagate再次检查Actor类型，不能仅凭enable阶段跳过static的实现细节推断任意static soft可参与完整反向流程。可微scene支持范围是rigid/articulated；soft、shell、rod、ROM、skinning不因它们能前向仿真就支持本条反向链。

[constraint differentiability][adjoint]还检查受约束target数量及 `hasMixedLinks`，拒绝某些articulated link与外部Actor之间的target求导组合。支持一个Actor类别不等于每种约束、actuator、接触输出和材料参数都可微。公开backward函数中没有一个“对任意Python cfg字段求梯度”的接口。

### 6.2 先固定一原生步的操作顺序

前向应是：设置本步输入 → capture old → `Scene.step(h)` → capture new → 读取输出。两次capture之间不能夹入其他输入设置，状态对必须属于同一Scene且保留完整前后步历史。E5的Lab控制步可能含 $M$ 个原生步，仅存控制边界不足以直接喂给逐步反传。

反向一次pass的顺序是：`reset_back_propagation(scene)`一次 → 按反时间顺序对每步 `prepare_back_propagate(scene,state_new,state_old)` → 累加输出的 `*_backward` → `back_propagate(scene)` → 提取该步输入梯度。不能每个时间步都reset adjoint，否则会清掉未来损失的传播；也不能在同一step连续prepare两次。[Scene实现][scene]用prepared tag检查顺序，BackPropagate后清除tag并恢复旧状态的一部分，同时特意保留adjoints。因此这是一条**会改变Scene当前状态**的过程，不是只读查询。

| 输出或输入 | 原生backward入口 | 维度/范围 |
|---|---|---|
| COM/root transform输出 | `get_center_of_mass_transform_backward` / `get_root_transform_backward` | 输入梯度7项：平移3+quaternion XYZW4；rigid含link，内部转Lie并在link上投影到父关节体 |
| contact force输出 | `get_contact_force_world_backward` / `get_contact_force_from_actor_world_backward` | 世界力梯度3项；rigid、需注册对应query，需prepare后、back_propagate前 |
| articulated pose输出 | `get_articulated_pose_backward` | 按原生pose参数化映射，不任意替换欧拉角序列 |
| target pose/velocity输入 | `set_articulated_target_pose_backward` / `set_articulated_target_velocity_backward` | 读取指定控制输入梯度，时序与前向目标设置及继承关系一致 |
| DoF力输入 | `set_external_forces_on_dofs_backward` | indices须唯一且与前向相同，out长度匹配；articulated/独立rigid，不用于nested link |
| 初始速度/姿态输入 | `set_velocity_backward` / `set_center_of_mass_transform_backward` | 独立rigid的具体setter反向，不是任意Actor状态导数 |

表格源自[diffsim stub][diffapi]与[Actor实现][actor]，不是所有可微字段的扩张清单。caller负责跨调用累加某些input gradients，原生setter backward不会替优化器维护参数共享关系。一个恒定控制参数重复用于多步时，各步贡献要按链式法则相加；一个目标沿多个step继承时，又需核对 `UpdateTargetPoseGrad`记录的step ownership，不能重复计算继承贡献。

## 7. 从离散残差推导原生adjoint

### 7.1 隐式导数与符号

以局部坐标 $q^+$表示下一步姿态，$s$包含上一姿态及derived-step历史（例如位移增量），$a$为本步输入，收敛后的残差满足 $R(q^+,s,a)=0$。在固定接触分支、残差可微且 $H=R_{q^+}$可逆时：

$$
\frac{\partial q^+}{\partial a}=-H^{-1}R_a,\qquad
H^T\lambda=g,\qquad
\frac{\partial L}{\partial a}=-R_a^T\lambda+
\left.\frac{\partial L}{\partial a}\right|_{\mathrm{direct}},
$$

其中 $g=\partial L/\partial q^+$包括未来step贡献和当前输出贡献。$L$的单位由应用定义，若 $L=\tfrac12\|p-p_*\|^2$为m²，则平移输出梯度为m，对力的梯度为m²/N，不能把梯度误称为力。刚体旋转用3维局部切空间，存储四元数4项不意味着4个独立旋转自由度。

[BackPropagationSolveIslandAsync][adjoint]从container取rhs后取负，解 $Hz=-g$，再把force gradient写成 $-z$，并沿Previous、PreviousDelta、CurrentInput、PreviousInput组装传播。这与上式 $z=-\lambda$的符号选择一致，不能看到两个负号便删掉一个。其Hessian路径利用配置后的势能/残差结构；一般非对称外部残差不能未经证明沿用H代替 $H^T$。

derived-step项解释了为何不仅保存 $q_k$即可：惯性与速度依赖前后姿态差，反向需要先投影当前derived adjoint，再shift到旧step、恢复旧状态下的Jacobian、继续投影到旧姿态。关节体将link空间贡献通过FK Jacobian的转置聚合；旋转还需要局部frame上的梯度运输。[Scene.BackPropagate][scene]给出这三段更新，不能把它简化成对每个位置独立乘一个常数。

### 7.2 HVP实际通过有限差分构造

`GetHessianVectorProduct`重用forward assembly，只装需要的残差/梯度，用局部增量改变solution，中心差分后还原；Current旋转分支要把梯度transport回同一个局部参数化。教学表达式为：

$$
Hv\approx\frac{\mathcal{T}_{+\epsilon}g(q\oplus\epsilon v)
-\mathcal{T}_{-\epsilon}g(q\oplus(-\epsilon v))}{2\epsilon},\qquad
\epsilon=\frac{\sqrt n\,\epsilon_{\mathrm{FD}}}
{\|v\|+\mathrm{min}_{\mathrm{real}}}.
$$

$\oplus$表示原生局部位移/旋转增量，$\mathcal T$表示所需transport，不是直接相加quaternion；$n$为island DoF数。该公式描述源码缩放策略，混合平移/旋转坐标没有一个统一的物理长度单位，`eps_finite_diff`不能任意理解为“接触距离精度”。有限差分截断误差、舍入消减、残差不够收敛、接触分支变化都可能影响结果。

`validate_finite_diff`实际比较同一HVP在 $\epsilon,2\epsilon,0.5\epsilon$下的稳定性，按相对差阈值记录 `finiteDiffValid`；并非每次都拿一个“完整解析真梯度”作金标准。stub的简短描述应服从这个具体实现。`finite_diff_valid=True`在该检查未启用时只是默认值，也不能解释成整条loss gradient已验收。

### 7.3 Krylov和Newton两条外层路径

默认Krylov路径先装PSD近似Hessian $\widehat H$作为预条件子，用Scene线性solver近似求 $\widehat H^{-1}r$；真正算子乘法仍调用上述HVP。外层先PCG，`abortIfNotSpd=true`。如果**未收敛且在outer最大迭代数之前退出**，重置z为零后回退MINRES；源码注释说likely non-SPD，不等于此分支只可能由已证明非SPD触发。PCG到达最大迭代数时并不满足这个回退条件。

PCG检查L2 residual；MINRES使用内部隐式残差范数（预条件度量）。在特定verbosity且启用FD诊断时，还额外重算HVP true residual对比，发现很大差距会warning；这不是自动修复。FD噪声或秩亏都可能导致隐式残差看似小而真实方程不满足。`BackPropagationSceneStats`暴露最大outer迭代数、残差、FD状态、total/solve秒数，没有可替代所有数学判据的“梯度正确”布尔值。

`use_newton_outer_solver=True`切到 `NewtonSolveZ`，但它解的仍是adjoint线性问题：目标近似 $\tfrac12 z^THz-z^Tb$，残差 $Hz-b$，HVP仍有限差分；不是再向前模拟一步物理。它复用近似dResidual并按backprop专属abs/rel tolerance、convergence mode、inner tolerance配置。前向E3的残差、outer adjoint残差和inner preconditioner误差是三层，不用一个容差数字概括全部。

### 7.4 接触力输出的VJP与前向近似

[contact adjoint实现][contactdiff]显式关闭PSD projection与fitted Hessian，使用实际query force law的导数，而非用于稳健迭代的近似切线。它把输出世界力adjoint转换到collider frame、乘每个colliding sample的求积权重、按sync/async角色累加；通过collider端贡献时有反作用力符号。相关query必须存在，空接触和far-SDF不可报告分支有各自处理。

这条VJP只证明固定检测结果/分支下实现如何传播，不为接触拓扑突然改变、SDF不光滑点、friction分支切换或有限差分跨越分支提供全局光滑保证。soft collider的变形Jacobian也不能自动塞进rigid-only路径。接触力N、冲量N·s、求积密度与损失梯度单位仍须按E3分别记录。

## 8. 完整Jacobian和最小原生反向例

### 8.1 public描述与实现不一致时以执行分支为准

[diffsim stub][diffapi]说明 `get_step_jacobian(scene,state_new,state_curr,state_old,out_jac_curr,out_jac_old)`输出column-major的 $\partial q_t/\partial q_{t-1}$和 $\partial q_t/\partial q_{t-2}$，按Scene Actor顺序组织。但[SceneImpl::GetStepJacobian][scene]实际检查**所有Actor必须rigid，且排除articulated nested-link路径**，并检查Backward Euler和两份 $n^2$输出buffer长度。这比reverse支持的rigid/articulated范围小。

它先恢复new/curr对，按行解Jacobian并保存derived-state项，再恢复curr/old对做shift/project。返回后Scene不是“依旧在new”的只读状态；跨前后状态island分组变化需要按保存的group去重，不能用当前island枚举替换。[实现][adjoint]的 `StepJacobianShiftAndProject`有明确说明。完整Jacobian有 $O(n^2)$输出存储，而一个loss的反向VJP可避免显式输出整张矩阵；这只是算法结构，不是本仓性能测量。

### 8.2 一个已有原生step的反向读取

[backward_one_force_step.py](../examples/backward_one_force_step.py)展示唯一一原生步、独立动态rigid Actor的调用顺序：caller已启用可微、设置DoF力后capture old、step、capture new，并计算COM输出梯度；函数reset一次adjoint，prepare、积累7维COM输出梯度、back_propagate，再读与前向indices对应的力梯度和stats。**例子未执行，调用它会实际进行数值求解并改变Scene状态。** 它不是Torch wrapper，也不创建场景/step/训练循环。

预先保存的7维grad是对平移3+quaternion XYZW4的导数；如果loss仅为COM位置二次误差，前3项为 $p-p_*$，后4项为0。不要用3维旋转向量梯度去冒充4维quaternion梯度。使用 `DynamicArrayReal`输出适配当前原生real；调用者仍须确保物理build精度、snapshot身份及forward收敛，并按需要在后续恢复已知状态。函数返回的FD字段只有启用诊断时才有意义。

多步反向应把reset放在循环外，保留每个原生步的state pair和对应输入/输出关系，按反序调用并累加共享参数贡献；本例故意仅处理一对，避免一个短脚本伪装成通用可微训练系统。失败非事务性，不能假设异常后state/adjoint未改变。[上游函数测试][difftest]与[Jacobian测试][jactest]提供差分/输入输出组合的检查意图，本轮没有执行它们，也没有把测试存在当成通过证据。

## 9. B7：把两条完整源码链走通

### 9.1 软体接触的字段到输出

| 环节 | 固定源码入口 | 应写下的契约 |
|---|---|---|
| 配置 | `SoftActorParams` + experimental params | shape是tet mesh、材料类型/场覆盖、has_inertia/stress、collider方向与frame |
| 创建 | Scene `CreateSoftActor` → `InitSoftActor` | entity、nodes、边界/visual、local-to-global、材料验证、ROM/build门限 |
| 接触准备 | `EmplaceSoftActorContact`与E3 detection | 谁提供samples、谁提供SDF，哪些类型拒绝，阈值和map怎样改变 |
| 数值求解 | E3 Scene/Island/Integration/assembly链 | $h$、时间积分、材料内力+接触残差、近似切线、收敛/停止状态 |
| 读回 | Actor节点位移/速度、注册query、E3力接口 | 世界/局部frame、sample权重、cache时点、不能由visual位姿替代节点状态 |
| 上层 | E4 viewer、E5数据记录 | 展示/日志/训练transition分别采样，不把渲染或HDF当完整物理快照 |

相关源为[Scene][scene]、[soft init][softinit]、[soft本构装配][soft]、[FEM stress][femstress]、[deformable][deformable]、[Actor][actor]及E3固定入口。这个链条告诉读者新增材料/Actor要触及哪些真实模块，而不是给一个假想“注册插件即可”的API。

### 9.2 关节目标到末端损失的反向链

从E2的target pose出发：明确joint/DoF顺序与控制矩阵 → 配置后capture相邻原生状态 → BE forward solve → rigid link的COM/root输出 → loss对7维transform的导数 → prepare → output backward将link梯度经FK Jacobian转置投影到父articulated DoF → adjoint solve与derived-state传播 → target pose backward输出输入梯度。目标被继承/被重设的step ownership决定向上一输入传播哪些项；仅设置target velocity而没有对应target pose时，源码会给出梯度可能不正确的警告。

链上所有frame/单位来自E1/E2，接触/forward收敛来自E3，输入输出采样来自E5，VJP/隐式假设来自本章；缺任意一项不能称作完整梯度契约。一个raw input gradient也不是已校准的真实机器人控制性能。DexLab未来引用应保留原引擎二进制、配置、任务与工况，不用这一源码链为历史批次补证。

## 10. 原生扩展、宿主扩展与未覆盖能力

Physics的C++ ECS components、Actor初始化、材料response、assembly pipeline和diffsim是内核扩展点；需配套构建与语言binding。Physics Python binding的generated文件是契约证据，不建议把用户逻辑写进自动生成产物；上游generator/schema、C++实现和绑定暴露要一致。`mochi_core`中的batched material是元素/SIMD批处理，不是E5的多world Gym批量。

Robotics负责Bot/控制器/传感器元数据和资源，Lab负责任务/奖励/终止/学习协议，Studio负责资产/交互/视图。E4的Polyscope、Mochi renderer、UE/UnrealCV与E5的Gym/RLlib/Torch/LeRobot都有单独身份；不能因需要某个render/learning依赖便推断内核支持同名数据或设备。原生CMake及[feature config][pconfig]表明compile-time门限，公开API不能证明任意wheel带全部内部feature。

本章没有核验流体/热/电磁完整场求解、任意用户材料Python热加载、任何对象端到端autograd、ROM/DeepFlow公开wheel可用性或所有feature同时组合的正确性。对这些需求的诚实入口是“补固定实现与binding/build证据”，不是填一个不存在的便捷调用。E7将补齐A0安装身份专题并做整套双路线审校；本章B7交付的是上述综合追踪与明确能力边界，不提前把E7的完整发布审校标完成。

## 11. 易错点与带答案练习

| 易错点 | 源码级纠正 |
|---|---|
| shell density填kg/m³ | 原生字段是kg/m²；使用thickness conversion并核对假设 |
| rod stiffness照填弹簧N/m | axial是N、bending/torsion是N·m²，结构刚度需结合长度 |
| soft ColliderType None等于无接触 | 区分自己的samples与作为collider被查询，两方向不同 |
| 有C++ rom字段就写Python参数 | 当前generated binding未暴露该字段，build还另有门限 |
| neural相关源文件在就能创建neural CROM | 直接NeuralNetCrom模型构造分支已报deprecated |
| Deep Flow等于流体 | 此处是shape mapping/collision路径，不是流体PDE |
| enable differentiability不改变仿真 | improved convergence会覆盖多个配置，必须重新记录身份 |
| full Jacobian支持所有reverse Actor | 该实现只接受rigid，articulated reverse是另一条范围 |
| HVP是纯解析Hessian | 当前路径中心有限差分残差并做Lie梯度运输 |
| finite_diff_valid默认true就梯度可靠 | 诊断关闭时无此含义；启用也只检查HVP尺度一致性 |
| 每个反向step都reset | 会清掉跨step adjoint，只在整个pass开始reset |
| reverse后仍处在最终state | 内部恢复旧状态且保留adjoints，需明确后续生命周期 |

1. **一个四面体单元能量密度为Pa，乘什么得到J？** 答：参考体积/求积权重m³；对节点位移求导给N，接触penalty Pa/m不能替代Young模量。
2. **线弹性应变公式能用于任意大刚体转动吗？** 答：不能，一般大旋转下对称位移梯度不为零；应按小应变/小转动假设或选合适有限应变模型。
3. **厚度加倍，shell膜和弯曲系数如何变？** 答：同E/nu时膜乘2、弯曲乘8、面密度乘2；不是全都乘2。
4. **N节点开杆是否有4N个不受约束物理DoF？** 答：4N是布局大小，末端twist含固定padding，另有BC；pose还多存每段axes。
5. **rod与spatial tendon都传拉力，为何不是等价模型？** 答：rod有分布质量/扭转/弯曲/接触状态，spatial tendon用routing长度映射广义力，省略这些场状态。
6. **active材料是否自动模拟肌肉电激活？** 答：没有；active constitutive需要外部fiber/target输入，不等于电生理或神经控制模型。
7. **ROM为什么可能快但丢细节？** 答：子空间限制可达位移，hyper-reduction又近似积分/接触样本；这是两个独立近似而非吞吐结果。
8. **加载带ROM信息的asset成功说明可创建ROM吗？** 答：不说明，feature gate可关而加载仍允许；Python还缺对应rom字段。
9. **soft的Auto collider能自动变成Sphere吗？** 答：本提交soft初始化的Auto走SDF，Sphere等分支拒绝，不能借用rigid规则。
10. **增大point-cloud radius只是更严格检测吗？** 答：会改变相互作用范围与penalty量纲缩放；采样间隙和self-contact排除也变化。
11. **为什么make_scene_differentiable后应重存配置？** 答：它设置接触/惯性/normal/line-search等参数；这些会影响前向问题，不只是额外保存梯度。
12. **刚体7维transform输出的loss梯度如何进入6维切空间？** 答：COM/root backward转换quaternion梯度为Lie，link还经FK Jacobian转置到关节体；不能删一个分量凑维度。
13. **HVP为何要transport旋转梯度？** 答：q±增量对应不同局部切空间，不运输便相减会混frame，不是同一线性空间中的中心差分。
14. **PCG用满迭代数未收敛是否必进MINRES？** 答：不会；回退还要求numIterDone小于outer max，具体判断不等于“凡失败必回退”。
15. **finite_diff_valid究竟验证什么？** 答：启用时比较多种epsilon的HVP一致性；关闭时默认true，没有全轨迹梯度正确含义。
16. **state pair可以在输入设置前后随便捕获吗？** 答：不可以，前向先设置输入，再紧邻step前后capture，中间不改输入，且同Scene兼容完整状态。
17. **get_step_jacobian能给articulated actor完整矩阵吗？** 答：该固定实现拒绝articulated，尽管reverse支持部分关节体；不能靠宽泛stub跳过实现检查。
18. **一个恒定力参数作用多step，拿最后step梯度够吗？** 答：不够，按反向时间链传播并汇总共享参数贡献；整个pass只reset一次adjoint。
19. **contact force backward可以复用前向PSD近似切线吗？** 答：此实现特意关闭PSD/fitted Hessian，求实际query force law的导数；仍受接触分支光滑性限制。
20. **此章能证明DexLab历史二进制支持哪种ROM/梯度吗？** 答：不能，固定源码、已装build和历史工况是三类证据，本章没有运行或历史二进制取证。

## 固定来源

所有新增文件与下载字节按Git blob核对，见[source-map](source-map.md)；上游测试仅阅读。每个链接固定SHA，不把`main`的新变化混入本章。

[api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[exp]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/mochi_physics_experimental.h
[expbind]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/src/generated/mochi_physics_pybind_experimental.generated.cpp
[scene]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp
[actor]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_actor.cpp
[softinit]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_soft_init.cpp
[deformable]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_deformable.cpp
[linear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/materials/batched_linear_elastic.cpp
[linearparams]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/materials/linear_elastic_params.h
[materialcheck]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/materials/material_params_utils.cpp
[materials]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/materials/batched_materials.h
[smith]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/materials/batched_smith_neo_hookean.cpp
[smithparams]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/materials/smith_neo_hookean_params.h
[shell]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_shell.cpp
[shellinit]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_shell_init.cpp
[tshirt]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_tshirt_on_plane.py
[rod]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_rod.cpp
[rodsample]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_mass_on_rod_spring.py
[tendon]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_tendon_comparison.py
[skin]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_soft_skinned.cpp
[skinsample]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_articulations_soft_skinned_double_pendulum.py
[romsystems]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_soft_rom_systems.cpp
[rominit]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_soft_rom_init.cpp
[pconfig]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/mochi_physics_config.h
[config]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/mochi_config.h
[articulated]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_articulated_body.cpp
[adjoint]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_differentiable.cpp
[diffapi]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/diffsim/__init__.pyi
[contactdiff]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_differentiable_contact.cpp
[difftest]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/private/diffsim/test/mochi_differentiable_functions_test.cpp
[jactest]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/private/diffsim/test/mochi_step_jacobian_test.cpp
[materialparams]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/materials/material_params.h
[smithfactory]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/materials/batched_smith_neo_hookean.h
[soft]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_soft.cpp
[femstress]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/element_operations/fem_stress.h
