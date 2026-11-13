# E3：接触、求解器与力观测

本章把“检测到接触”一直追到“这个数究竟是什么力”。先修 [E1：模型、状态与时间](modeling-state-time.md) 和 [E2：控制与机器人](control-robotics-tasks.md)；完成 A4、B1–B5 的核心接触/数值专题，并补足 B0 的动力学装配入口。重点是刚体 XPBD，同时沿 SemiImplicit、Featherstone、MuJoCo、VBD、Kamino 的实际分支比较。软体/粒子在本章说明接口与适用边界，专用材料、耦合和扩展留 E6。

阅读对象为 Newton **1.6.1**，固定提交 `713fecdc41caf0c9d726f5c016939f36e66e3dff`。这是源码课程，**没有 import、step、仿真或运行本章示例**。公式的算例是纸面推导，不是测量。正文不复原 DexLab 历史参数，不把不同 solver/版本拼成排名。返回 [Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas)。

## 1. 三个层次和一个离散动力学问题

接触模型规定怎样从间隙、相对运动和材料得到约束或力；积分器规定状态如何跨过时间步；数值 solver 规定离散方程如何近似求解。`SolverXPBD`/`SolverMuJoCo` 是包含若干层的公开对象，不能由类名推出积分阶数、摩擦模型或收敛精度。

在一个固定接触集合、局部线性化 Jacobian 的时间步中，可用下面的**解释模型**组织符号：

$$
M(v_{n+1}-v_n)=h f_{ext}+J^T p,\qquad
q_{n+1}=\operatorname{Integrate}(q_n,hv_{n+1}).
$$

$v$ 是广义速度，$p$ 是约束冲量，$Jv$ 是约束速度；平动/转动分量的单位分别为 m/s、rad/s，冲量为 N·s、N·m·s。$J M^{-1}J^T$ 是约束空间的逆有效质量（Delassus 算子）。固定接触法线、忽略配置更新对 $J$ 的变化只是本式的局部假设；球关节姿态不能直接用普通向量相加。

无黏附、无恢复、理想单边接触的速度级理想化写成 $0\le p_n\perp u_n\ge0$，摩擦冲量满足 $\|p_t\|\le\mu p_n$。其中 $u_n$ 可以包含穿透修正或偏置；并非所有实现都精确解这个互补问题。Penalty 在有限穿透时产生弹簧/阻尼力；XPBD 在位置层修正；MuJoCo 采用后端正则化约束；Kamino 有硬接触的对偶迭代。下文以实际 kernel 决定含义。

## 2. 从 Shape 到 Contacts：碰撞生成没有输出“已测接触力”

原生调用边界是 `pipeline = newton.CollisionPipeline(model, ...)`、`contacts = pipeline.contacts()`、`pipeline.collide(state, contacts)`。常见显式调度为：

```text
当前 State → clear/更新 AABB → world/group/排除对过滤
          → broad phase 候选 → narrow phase 几何 → reduction/可选 matching/sort
          → Contacts → solver.step → solver.update_contacts → 观测消费者
```

`collide` 使用传入 State，而不是自动等待 solver 的步后状态。它刷新计数、AABB，调用 broad phase，再将候选送入 narrow phase。检测可使用 `nxn`、`sap`、`explicit`；它们是候选生成方式，不是三个接触力求解器。[构造与容量](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L1166-L1250)、[碰撞主路径](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L2233-L2433)。

几何路线有三类：primitive/convex 的 GJK/MPR；无预计算 SDF 的 mesh BVH 距离查询；带 SDF 的距离查询或 hydroelastic 路线。接触 reduction 将大量面/点压缩为有限约束，改变离散接触集合；它不是 solver 迭代，也不是免费保留所有分布信息。双方 hydroelastic/SDF 条件、体积几何和分辨率都必须满足；平面/heightfield 的 hydroelastic flag 会被关闭。[几何路线](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/collisions.rst#L27-L91)、[ShapeConfig 条件](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L840-L869)。

### 过滤、margin 和 gap

| 配置 | 固定实现含义 | 易错解释 |
|---|---|---|
| `shape_world` | 两个非负且不同 world 不碰撞；`-1` 是共享实体，仍需通过组过滤 | “所有负数都共享”不成立 |
| `collision_group` | 0 禁用；正组只与同正组或负组；负组与除同一负组外的组相交 | 它不是位掩码，也不是 MuJoCo contype/conaffinity |
| same body / filter pair | 同一个非静态 body 的 shapes 被过滤；显式排除对独立生效 | 视觉相交不证明已进入求解 |
| `margin` [m] | 表面向外偏移；两侧相加，参与有效表面间隙 | 不是仅检测范围 |
| `gap` [m] | 表面之外提前保留候选的距离；默认可来自 `builder.rigid_gap` | 有正间隙的 record 不一定施力 |
| speculative gap | 可选按速度/碰撞更新 dt 扩大检测，带上限 | 不等于完整连续碰撞检测或自动防穿透 |

[world/group 判定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/broad_phase_common.py#L209-L282)、[字段与单位](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L796-L831)、[speculative 参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L1322-L1337)。

令 $n$ 从 shape0 指向 shape1；$p_0,p_1$ 是用 body transform 还原的 support 点，$m_0,m_1$ 是 contact record 的有效 thickness（包含 primitive 有效半径与 margin）：

$$d=n^T(p_1-p_0)-(m_0+m_1).$$

$d<0$ 表示有效表面穿透。不能再把 radius/margin 重复扣一次。检测 writer 在 $d\le gap_0+gap_1$ 时接受候选；XPBD 的刚体位置分支则在 $d\ge0$ 直接返回，因此 **record 存在与法向响应是两回事**。[间隙函数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L69-L92)、[writer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L181-L222)、[XPBD 激活](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2242-L2280)。

### Contact record 与生命周期

| 字段 | 形状/单位/参考系 | 使用要求 |
|---|---|---|
| `rigid_contact_count` | 单元素设备计数 | 不是数组容量 |
| `rigid_contact_shape0/1` | shape ID | 再经 `model.shape_body` 得 body；静态 body 可为 -1 |
| `rigid_contact_point0/1` | 各自 body 局部坐标，m | 静态 shape 使用 world；不是两个 world 点 |
| `rigid_contact_normal` | world 单位向量，0→1 | 不是力的朝向承诺 |
| `rigid_contact_offset0/1` | body 局部表面偏移 | 摩擦锚点需要随旋转更新 |
| `rigid_contact_margin0/1` | 有效 thickness，m | 不等同只读 `shape_margin` |
| `rigid_contact_stiffness/damping/friction` | 接触级 override 或 scale | 零可能代表“未设置”，不是物理零 |
| `force` | 可选 spatial vector，N / N·m | 要预请求、等实际 producer 写入；各后端差异见第 8 节 |

[存储及 writer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L130-L169)、[Contacts 数组](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L253-L330)、[扩展 force](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L421-L432)。

默认 `clear()` 只清计数，不清整块数据；不能遍历数组长度读旧行。更关键的是 writer 先增加计数、再在容量外跳过写入，所以 **计数超过容量时不是完整记录**。应把 overflow 当作无效采样/配置不足，增大容量后再验收，不能仅 `min(count, capacity)` 后声称完整力。`verify_buffers=True` 发诊断 warning，不自动重分配或回滚。[clear](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L469-L506)、[容量保护](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L130-L145)、[计数递增](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L210-L222)、[诊断](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L1322-L1329)。

`contact_matching="latest"/"sticky"` 是帧间几何对应机制；非 disabled 会启用排序。sticky 可重放以前的几何，reset 时要处理 matcher。它不会自动让 XPBD 使用跨步法向乘子 warm start，更不能用数组下标当永久 contact ID。[matching 参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L1300-L1321)、[匹配/排序/重放顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L2435-L2535)。

## 3. 材料组合必须沿消费者确认

`ShapeConfig` 存储通用数据，不保证每个 solver 都使用。法向 `ke` 为 N/m，`kd` 与切向 `kf` 为 N·s/m；`mu` 与 restitution 无量纲；`ka` 是黏附距离 m；`mu_torsional/mu_rolling` 是 **m**，因为它们将法向力/冲量变成力矩/角冲量限额。`kh` 为 N/m³，不是 Young 模量 Pa。[字段声明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L784-L866)。

下面以两个有效 shape 的**刚体接触**为范围；粒子、内部后端 pair override 等不能照搬：

| 消费路径 | 两侧材料组合 | 实际使用/限制 |
|---|---|---|
| XPBD 位置接触 | `mu`、torsional、rolling 算术平均 | 不消费 shape `ke/kd/kf/ka`；法向是位置修正，无接触级 stiffness override |
| XPBD 恢复 pass | restitution 算术平均 | 还需 `enable_restitution=True`；有速度阈值与有限 manifold 迭代 |
| SemiImplicit / Featherstone 刚体 penalty | `ke/kd/kf/ka/mu` 算术平均 | 接触级正 stiffness/damping 覆盖，正 friction scale 乘到 mu；0 scale 意为未设置 |
| VBD 刚体 | `ke/kd` 算术平均；`mu=sqrt(mu0*mu1)` | compliant ALM 和 legacy AVBD 的数值参数、历史不同 |
| MuJoCo 的 Newton-contact adapter | 高 priority 胜出；同优先级摩擦取分量最大、condim 取最大；solmix 决定响应混合权重 | 正 solref 加权、否则逐分量 min；还有 shape mode 和接触级覆盖 |
| Kamino 经 Newton contacts | friction 默认 average；restitution 默认 min | 两项独立配置为 average/multiply/max/min；不是 XPBD 的恢复组合律 |

依据：[XPBD 摩擦](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2304-L2323)、[XPBD 恢复](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L136-L158)、[penalty 组合](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L413-L459)、[VBD 组合](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/rigid_vbd_kernels.py#L995-L1011)、[MuJoCo 组合](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L123-L187)、[Kamino 配置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/config.py#L1144-L1162) 与[实际转换参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/solver_kamino.py#L1043-L1058)。

纸面例子：两侧 $\mu=0.2,0.8$，上述 XPBD/penalty 得 0.5，VBD 得 0.4，MuJoCo 同优先级且无覆盖得 0.8。这只说明组合代码不同，不是摩擦精度或抓取效果排名。

### Hydroelastic 是生成和求解之间的另一层

压力面经 reduction 得到 $F_{agg}=\sum_i A_i p_i n_i$；本实现导出的等效 contact stiffness 可由 $\|F_{agg}\|/\sum_j depth_j$ 构造，单位仍是 N/m；双方 `kh` 的辅助有效刚度采用 $k_a k_b/(k_a+k_b)$。这里的压力采样、法线合并、anchor 和有限接触数都影响最终记录。它不是把每个 shape 变成完整可变形体，也不是“任意 solver 读取 kh 就支持同一 hydroelastic 响应”。[有效刚度](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/contact_reduction_hydroelastic.py#L296-L302)、[reduction 的力目标](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/contact_reduction_hydroelastic.py#L983-L1017)。

官方支持表将生成结果的有效消费者列为 SemiImplicit/Featherstone，以及 `use_mujoco_contacts=False` 的 MuJoCo；XPBD 刚体 kernel 不接收 contact stiffness，所以不能因它读到了同一 Contacts 就宣称等价压力响应。[支持范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst#L164-L201)。

## 4. XPBD 的一步：预测、位置投影、速度后处理

刚体主链可在 `SolverXPBD.step` 中按顺序核对：

1. 可选分配本步 contact impulse / joint impulse 缓冲，起始为零。
2. 外部 body_f 与 joint_f 进入预测；joint_f 先写临时 body wrench，避免永久累加输入 State。
3. 调 `integrate_bodies` 预测 COM 与姿态。
4. 固定 `iterations` 次：清 delta → 刚体接触 kernel → 按接触数加权并应用 → joint kernel → 应用。
5. 保存本步位置修正等效 impulse，转换可选 body_parent_f；必要时复制最终数组。
6. 若开启 restitution，再按 body-pair manifold 求速度约束；最后恢复 kinematic bodies 的规定状态。

[预测与缓冲](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L442-L569)、[位置迭代](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L710-L856)、[恢复调用](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L937-L1058)。

### 预测不是“全系统 Backward Euler”

公共刚体预测器在线性部分做 $v^*=v_n+h(f_n/m+g)$、$x_C^*=x_{C,n}+hv^*$；角速度先转 body frame，加入 $I^{-1}(\tau-\omega\times I\omega)h$，再用归一化 quaternion 增量更新姿态，最后扣回 COM 偏置。角阻尼采用乘子 $1-\gamma h$，这不是指数阻尼的精确离散。XPBD 再以约束修正预测结果，所以文档称其 implicit integrator，不意味着预测器在隐式求整套接触动力学。[预测积分](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L67-L120)。

### 单个法向位置约束的实际单位

假定两刚体当前局部线性化，$d<0$，法线单位化，定义

$$w=m_A^{-1}+m_B^{-1}+(r_A\times n)^TI_A^{-1,W}(r_A\times n)
 +(r_B\times n)^TI_B^{-1,W}(r_B\times n).$$

$w$ 是逆有效质量 kg⁻¹。以下公式要求 $w>0$，并使用 solver 将 kinematic 的有效逆质量/逆惯量置零后的数值。此 kernel 返回的法向变量是

$$p_n=\omega_r\frac{-d}{h w},$$

其中 $\omega_r$ 是 relaxation，无量纲；$p_n$ 是 **N·s**，而不是教科书某些 XPBD 写法中 N·s² 的位置乘子。A 收到 $-np_n$，B 收到 $+np_n$。`apply_body_deltas` 用它更新速度，再乘 h 更新位置；角分量还带陀螺修正和 quaternion 归一化。[有效质量与除 h](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2091-L2124)、[法向装配](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2325-L2343)、[应用 delta](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L869-L942)。

因此记录中已累计的这类 impulse 转平均力只除一次 h，不能盲套“所有 XPBD lambda 都除 h²”。上式仅对应这个刚体法向分支，不可拿它替代有 compliance/damping 的 joint correction。该 joint helper 的分母包含 $(h+\alpha b)w+\alpha/h$；刚体 contact 分支没有 shape.ke 提供的柔顺项。[joint helper](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2128-L2167)。

### 摩擦、relaxation 与迭代终止

切向修正来自接触锚点的切向位移；动态表面运动已包含在位移中，只为 kinematic surface 额外加规定速度的 $h v_t$。切向增量限制在**本次法向增量**的 $\mu p_n$ 内；注释也将其称为对总摩擦限额的近似。torsion 用 $\mu_{torsion}p_n$ 限制绕 n 的角冲量，rolling 限制切平面角冲量。[切向与旋转摩擦](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2345-L2442)。

`iterations` 默认 2 是固定循环次数；这条位置主链没有用户 tolerance、残差判据或提前收敛出口。contact/joint 的 Jacobi 式并行累加使用 atomics，relaxation 分别作用于对应 correction。增加次数是在同一时间步内重访约束，不等于增加物理子步或重新检测碰撞。contacts 的法线/集合来自之前的碰撞调用，局部点会随当前 pose 还原。[默认配置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L117-L192)、[循环边界](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L569-L580)。

跨步 warm start 也要看实际数据：刚体 `_contact_impulse` 是本步重新分配的观测累计量，没有作为下一步 contact correction 的初始 multiplier 输入。`contact_matching` 与 `requires_grad` 数组分支都不能证明 XPBD 已实现持久乘子或完整可微；官方当前矩阵将 XPBD 标为不可微。[缓冲初始化](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L442-L479)、[迭代输入](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L738-L772)、[能力矩阵](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst#L83-L162)。

### 权重会改变动量与力读回

默认 `rigid_contact_con_weighting=True`，每个 body 的 correction 除以该轮活跃接触数 $N$。两侧的 $N$ 不同就不再按同一个成对冲量更新，所以文档明确不保证接触动量守恒。force 读回另用一个对称 scale：只有一侧有计数时 $1/N$，两侧都有计数时 $2/(N_A+N_B)$。它是**倒数计数的调和平均**，不能称作两侧实际 correction 的精确公共力。[官方限制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L63-L86)、[实际加权](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2446-L2504)。

还有一个源码与文字需分开的细节：统计/读回 kernel 按 `body_id>=0` 计数，没有按有效质量过滤 kinematic body；所以注释“dynamic 与 kinematic 时只用 dynamic 的 N”不能覆盖所有附着 kinematic body 的情况。world 静态侧 `body=-1` 与有 body ID 的 kinematic 侧不同。本章按照上述实际分支记录，不把它作为已复现实验缺陷。有效逆质量归零发生在另一条路径，不会因此移除 body ID。[kinematic 有效质量](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L176-L190)、[计数位置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2330-L2334)、[读取计数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2477-L2498)。

## 5. Restitution 的速度层与有限 manifold

只有开启 `enable_restitution` 才走恢复路径。它记录预测、投影前速度和位置，标记位置接触，再按 body pair 分组；单个 manifold 最多选 **12** 个 contact，较多候选通过确定性几何选择保留子集。每个外层迭代内部固定 **8** 次 Gauss–Seidel sweeps，外层 `rigid_contact_restitution_iterations` 默认 2；每 body 的 manifold velocity delta 再按参与 manifold 数平均。[数量与分组](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L58-L130)、[子集选择](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L267-L288)、[内外迭代配置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L188-L192)。

在本步固定约定下，取有 body ID 的两侧所属 world 重力范数最大值为 $g_*$（m/s²）；若旧相对法向速度低于 $-2g_*h$，目标分离速度为 $-e v_{n,old}$；超过正阈值时锚定旧分离速度，阈值内目标为零。不是“只要接触就把速度乘 -e”。求解是带累计下界的 PGS：首轮允许有界负增量去掉位置投影造成的过分离，后续外层改为非负下界，避免把别的 manifold 产生的分离当成应撤销的冲量。[目标分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L177-L233)、[PGS 语义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L416-L438)、[实际 sweeps](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L493-L565)。

**力观测边界：**位置循环结束就保存 `_contact_impulse`；之后 restitution kernel 只输出 body velocity deltas 与 manifold counts，没有回写这个 contact impulse buffer。故本版本 `update_contacts()` 读到的是位置修正累计的等效平均力，**不包含此后独立恢复 pass 的额外冲量**。即使 e=0，启用的 velocity pass 也可能调整投影后的速度。本结论是固定实现的数据流核对，没有运行冲击实验。[保存位置累计](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L831-L856)、[恢复输出](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L1003-L1055)、[读回](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L1060-L1116)。

## 6. 其他主要刚体 solver：同字段不能当同方程

### SemiImplicit 与 Featherstone：penalty 和动力学装配

两者刚体接触调用同一 `eval_body_contact`。以 kernel 的内部 B→A 法线 $n_i$、间隙 d 和接触点相对速度 $v$ 为准，穿透分支的 scalar 为

$$a_n=k_e d+k_d\min(v_n,0),\quad
s=\operatorname{norm\_huber}(v_t,\delta),\quad
f_t=\frac{v_t}{s}\min(k_f s,-\mu a_n)\quad(s>0).$$

它再按 body side 写入 $\mp(n_i a_n+f_t)$ 及力臂矩；$d\ge k_a$ 直接跳过，切向仅在 $d<0$ 时生效。上式限定穿透、正材料参数；`ka>0` 时存在吸引范围，不能把整个函数解释为硬单边互补。`friction_smoothing` 改变低速正则化，不是静/动摩擦自动识别。[力律与写入](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L461-L556)。

SemiImplicit 在当前 State 上一次装配弹性、joint、contact 等力，再调用半隐式积分器，没有 contact 迭代收敛循环。高 stiffness 与过大 h 可以产生离散不稳定；线性无阻尼单自由度弹簧的半隐式 Euler 例子有 $h\sqrt{k/m}<2$ 的线性稳定范围，这只是该简化系统的推导，不能当接触/关节/多体场景统一安全阈值。[完整 step](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/solver_semi_implicit.py#L122-L215)。

Featherstone 使用 generalized coordinates：当前 q/qd 经 FK 与刚体力装配，把空间 wrench 投到广义力；形成 $H=J_b^T I_b J_b$，加 armature 后 Cholesky 分解/三角求解得到 qdd，再积分关节坐标。这里的矩阵求解不是 contact complementarity iteration；关节 tree 的约束由坐标表示保证，接触仍是 penalty。质量矩阵更新间隔可配置，默认每步刷新，调大后使用缓存矩阵是额外近似。[矩阵装配与求解](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py#L765-L940)、[积分](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py#L954-L982)、[缓存参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py#L139-L156)。

两者当前未 override 通用 `update_contacts`，基类抛 `NotImplementedError`；接触 kernel 写 body force 缓冲，没有写 `contacts.force`。已分配的零数组不能当作零接触力结果。Featherstone 的 `body_parent_f` 是另一类 joint wrench，不能拿它替代每对 shape 的接触力。[接触输出目的地](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L601-L648)、[基类契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L625-L634)。

### MuJoCo：明确后端、接触来源和固定依赖

`SolverMuJoCo.step` 分 CPU `mj_step` 与 MuJoCo-Warp 两支；Warp 可用自身碰撞，也可消费 Newton contacts。相同类名不能隐去 `use_mujoco_cpu/use_mujoco_contacts`、solver、integrator、cone。默认解析值也不是 DexLab 历史配置。[实际分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4152-L4179)、[构造参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L3691-L3768)。

固定 Newton `pyproject` 的 sim extra 为 `mujoco~=3.12.0` 与 `mujoco-warp~=3.12.0`，uv.lock 锁 MuJoCo-Warp 3.12.0。为核对实际后端 helper，本章额外固定官方 MuJoCo-Warp tag v3.12.0 的 commit `087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7`，核验其三个源码文件与锁定 sdist 完全一致。它是**源码依赖身份**，不证明本机安装该版本或历史批次运行此版本；Warp 1.18.0 仍只是既有学习候选。[依赖声明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/pyproject.toml#L29-L41)、[锁定包和摘要](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/uv.lock#L3341-L3357)；具体 blob 与 sdist SHA-256 见独立的 [E3 外部依赖清单](e3-dependency-sources.json)。

在已核对 MuJoCo-Warp 路径中，CG 和 Newton 是约束优化方法；Newton 分支使用 Cholesky 系列求 search direction，CG 分支更新搜索方向。停止依据经 `_rescale` 缩放的 cost improvement / gradient；Newton 还可看预测 improvement，或达到 iteration 上限。这里的 tolerance **不是穿透深度 m、也不是接触力误差 N**。warm start 从 `qacc_warmstart` 开始；后端还有 active DOF/island 相关分支，不等于 XPBD 的逐 contact atomics。CPU C++ 内部算法本章未逐行审查，不把 Warp 的终止实现直接套到 CPU。[缩放定义](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/solver.py#L116-L120)、[Newton 线性求解](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/solver.py#L2568-L2599)、[CG/Newton 终止](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/solver.py#L3432-L3496)、[warm start 与循环](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/solver.py#L3669-L3733)。

**积分器是独立选择。**Newton adapter 接受 `euler/rk4/implicit/implicitfast`，未由参数或模型属性指定时取 `implicitfast`；这既不是所有 MuJoCo 场景的默认，也不是历史实验配置。后端 `step` 先 `forward`（含约束求解），再按 integrator 分支推进状态；优化器名 Newton 与积分器 implicit 不能混为一项。[枚举解析](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L569-L571)、[adapter 默认](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L5792-L5801)、[后端 forward/step](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L1342-L1381)。

| integrator | 固定 MuJoCo-Warp 实际路径 | 要保留的边界 |
|---|---|---|
| `euler` | 先更新速度，再用新速度积分位置；未禁用 EULERDAMP/DAMPER 时，对 joint damping 的局部速度导数做隐式处理 | 不是所有力都显式，也不是对下一时刻所有变量求非线性解 |
| `rk4` | 初始 forward 加 3 个中间态 forward，以经典四阶权重累积速度/加速度和 activation 导数 | 平滑 ODE 的四阶条件不能直接推广到碰撞事件、切换摩擦或外部固定 contact 集合 |
| `implicit` | smooth velocity derivative 后额外调用 RNE velocity derivative，组装矩阵并用 LU 路径求修正加速度 | 对速度隐式；不是重新求解下一时刻的完整非线性几何/接触系统 |
| `implicitfast` | 保留 smooth velocity derivative 分支，以对称 factor-solve 求修正加速度，未调用上述 RNE derivative；有关力全禁用时直接推进已有 qacc | 与 implicit 的矩阵及计算量不同；不能用 faster 推出某场景同精度或更稳定 |

[Euler 及 damping 分支](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L353-L416)、[RK4 阶段](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L524-L557)、[implicit/implicitfast 分支](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L579-L612)。这里核对调用的导数类型及矩阵求解路径，未把 derivative 内每一种力分支都审查完。

用平移自由度的局部线性化说明“速度隐式”：设 $M$ 为本次质量矩阵（kg），$D=\partial f/\partial v$ 为该分支保留的力导数（kg/s），$r$ 为已装配的总力项（N），则 $(M-hD)\Delta v=h r$，$\Delta v$ 单位 m/s。线性阻尼 $f=-Bv$ 给出 $M+hB$；这解释了 damping 为什么进入矩阵，而非证明其他非线性项也被精确隐式处理。广义转动自由度有对应力矩/惯量单位，不能逐元素都叫 kg。除 RK4 传入加权速度外，公共 `_advance` 先改 v 再推进 q；旋转按 joint 类型更新 quaternion，不用 q 的四元数分量直接加角速度。[状态推进](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L276-L343)。

`ke/kd` 到 MuJoCo 的映射不是普遍的 $f=k_ed+k_dv$ 等价替换。Newton-contact 的 FORCE_SPACE 双方模式先乘 $(1-d_{max})(invweight_A+invweight_B)$ 再转 solref；该 invweight 只是后端 body 平移逆权重，不是任意偏心 articulated contact 的完整 $(JM^{-1}J^T)$。RAW/MJCF-default、CPU/内置碰撞路径不同。接触级 stiffness 优先于 shape 覆盖。`kf` 只有 Warp + Newton contacts + elliptic 条件下映射到 solreffriction，解析后 `kf=0` 可使 condim=1；不能将其作用推广到所有后端。[实际覆盖顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L553-L651)、[模式与边界](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/mujoco.rst#L213-L317)。

### VBD：物理刚度与迭代罚参数分开

VBD/AVBD 针对 particle/rigid block 做隐式求解，固定 `iterations` 循环，之后由 pose 历史更新速度。新 `rigid_compliant_alm=True` 路径用有限材料刚度 k 与数值 metric rho，$k_{eff}=k\rho/(k+\rho)$，lambda 保存反力历史；legacy AVBD 的 penalty ramp / hard-mode 另有语义。不能把增加 rho 当作修改材料 k，或将旧默认当未来保证。[两种 formulation](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L144-L174)、[固定循环与历史](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L2272-L2366)。

它有 contact matching/history、Dahl 等分支，reset 会处理持久历史；通用 `update_contacts` 不是此版本的读回入口。应使用 `collect_rigid_contact_forces(body_q, body_q_prev, contacts, dt)`，返回 **force_on_body1**，方向与 `Contacts.force` 的 body0 契约相反。previous pose 必须是该步实际使用的历史，不能在 step 后随便取已更新的 `solver.body_q_prev`。[读回契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L3705-L3762)、[reset 历史](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L2370-L2396)。

### Kamino：迭代状态有原生物理量单位

Kamino 是实验性 maximal-coordinate rigid solver，默认 PADMM，另有 DVI。默认配置的 friction/restitution 组合与 XPBD 不同。选内部 detector 时外部 Contacts 被忽略；外部路径则转换后作为求解输入。Euler 先解前向动力学再更新速度/pose；Moreau-Jean 需要内部中间阶段检测，不满足时实现退回 Euler。[接触来源](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/solver_kamino.py#L1012-L1078)、[积分选择](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/solver_kamino_impl.py#L288-L302)、[Euler 更新](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/integrators/euler.py#L46-L87)。

PADMM 求正则化 Delassus 问题，在 projection/dual 更新后检查 primal、dual、complementarity 的 infinity-norm；默认三个 tolerance 为 $10^{-6}$，max_iterations=200。检查要求 iterations>1 且三个 residual 均达标；耗尽预算也停止，**停止不等于 converged**。可配置 LLT 或 CR 系列内层线性解法。默认 warmstart_mode 为 containers、scale=0.9，reset/snapshot 需要保留或清理对应历史。[配置与单位](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/config.py#L470-L611)、[求解循环](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/solvers/padmm/solver.py#L381-L420)、[收敛判定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/solvers/padmm/kernels.py#L1343-L1367)。

公开 `solver.status` 每 world 有 converged/iterations/r_p/r_d/r_c；PADMM 的 primal 单位为 impulse、dual 为 velocity、complementarity 为 J。DVI 同名字段的定义不同，不能把它的 projected-update tolerance 与 PADMM 三阈值互换。返回 numpy 会同步设备；观察 status 不需要 `collect_solver_info=True`。本章核对 PADMM 主链，DVI 更深的投影/稀疏路径留特色扩展 E6。[状态与 residual 定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/kamino.rst#L75-L116)。

### 范围总结表

| 路径 | 接触/积分核心 | 主要停止/缓存 | 本章可用读回 |
|---|---|---|---|
| XPBD | 预测 + 位置约束；可选恢复速度层 | 固定位置次数与恢复次数；刚体 contact multiplier 不跨步输入 | update_contacts：位置累计等效力，权重近似，恢复增量未含 |
| SemiImplicit | 当前态 penalty + 半隐式 Euler | 单次力装配，无接触 residual 迭代 | 通用 contact force producer 未实现 |
| Featherstone | reduced-coordinate 质量矩阵/Cholesky + penalty | 直接线性解，质量矩阵可缓存 | joint wrench 与 per-contact 力分开；通用后者未实现 |
| MuJoCo-Warp | 后端约束优化 + 所选积分器 | 目标/梯度等条件或上限；acceleration warm start | update_contacts；六维 torque 参考点缺口见下 |
| VBD | block 迭代，compliant ALM / legacy | 固定 iterations，持久 contact/pose 历史 | collect_rigid_contact_forces，力在 body1 |
| Kamino PADMM | 硬接触对偶问题 + Euler/Moreau | 三类 residual 或上限，容器 warm start | update_contacts(contacts, state)，COM world wrench |

Style3D、ImplicitMPM 是另有材料/离散模型的专用路径，不适合在这张刚体表中补成“未测但等价”。它们的深层实现与耦合留 E6；当前能力索引见[官方矩阵](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst#L70-L162)。

## 7. 数值设置：时间精度、约束误差和可微是不同验收

- **h 与 iteration：**h 改变预测、离散刚度、冲量到平均力换算和恢复阈值；iteration 主要改变固定 h 的约束残差。十次约束迭代不产生十个新物理时刻。
- **碰撞频率：**每个子步重建几何与保持一帧 contact 集合是不同离散模型；重算 world 点不等于更新法线/接触集合。VBD 的可选内部重检测也不能外推成 XPBD 会自动重检测。
- **float 与 tolerance：**公开数组常见 float32；请求低于舍入噪声的阈值不创造 float64 精度。固定源码并未证明某次 runtime backend、精度/JIT 路径或确定性配置。
- **稳定与准确：**relaxation、contact weighting、小速度归零、有限 manifold 与 damping 都会影响结果；“没有爆炸”不是动量守恒或正确接触力。XPBD apply-body kernel 对小于 $10^{-4}$ 的速度范数直接清零，也应计入低速行为解释。[小速度处理](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L931-L942)。
- **确定性与导数：**固定排序/atomic mode 不是跨平台逐位相同保证。`eval_rigid_contact_kinematics` 可将梯度传到 pose，但接触集合和 normal 冻结，只有局部 tangent approximation；它不能让离散碰撞、friction branch 或整个 XPBD 自动可微。[kinematics 梯度边界](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contact_kinematics.py#L35-L78)。

B4 在这里完成核心数值语义；自动微分、专用材料和性能行为的全面实现审查仍是 E6 的独立范围。没有用“静态检查通过”取代这些限制。

## 8. 力、冲量、wrench：先认 producer、参考点和时间

### 四个容易混淆的对象

| 对象 | 物理含义 | 不能冒充 |
|---|---|---|
| `Control.joint_f` | 广义驱动输入 | 实际接触力、机械传感器测量 |
| `State.body_f` | 外部 world COM wrench；某些 solver 用作装配工作缓冲 | 统一纯接触反力数组 |
| `State.body_parent_f` | parent 经 inbound joint 对 child 的 COM world wrench，含 joint_f 对应贡献 | 只有约束的无驱动反力，或某一 shape 接触力 |
| `Contacts.force` | 通用契约为 body1 对 body0 的 COM world spatial wrench | 所有 solver 均已实现/所有组成均被包含 |

[State wrench](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L150-L185)、[XPBD joint wrench 含义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L73-L86)、[Contact 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L421-L432)。

XPBD 需在创建 Contacts **之前** `model.request_contact_attributes("force")`，并在同一个 Contacts 上 `step → update_contacts`，中间不做 collide、排序、clear 或覆盖。update 的运行防护只检查 force 是否分配、上次是否有 impulse、capacity 是否相同，**不会证明是同一对象/同一 generation**；调用者仍须维持这一生命周期。[实际检查](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L1079-L1116)。

### 空间换点不是只换三个符号

把 body0 在 COM $C_0$ 的 world wrench $(f_0,\tau_{C_0})$ 移到 world 点 O：

$$\tau_O=\tau_{C_0}+(C_0-O)\times f_0.$$

若转为 body1 在它的 COM $C_1$ 上的反作用，在同一成对作用点模型下应先换点再取负：

$$f_1=-f_0,\qquad
\tau_{C_1}= -\tau_{C_0}-(C_0-C_1)\times f_0.$$

不能只给六个分量全部乘 -1 并称其已经位于另一个 COM。若原 wrench 处于工具坐标，旋转力和力矩后还要处理参考点；存在 torsional/rolling 自由力矩时不能只由 $r\times f$ 重建。上述是明确点约定下的力学推导，和 [E1 的空间量约定](modeling-state-time.md)一致。

XPBD 累加 torque 来自各轮各接触当时的 COM 力臂及 torsion/rolling；有限 pose correction 后将其视为最终 COM 的精确连续时间测量仍是近似。Kamino 转换则显式依据提供 State 的 COM 换点，检查了 A/B remap 和符号；要传对应 step 的 State。[XPBD torque 装配](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2325-L2343)、[Kamino wrench 转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/geometry/contacts.py#L1265-L1296)、[已有 contact 的 remap](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/geometry/contacts.py#L1317-L1389)。

### 固定 MuJoCo adapter 的 torque 契约缺口

已核对的 MuJoCo-Warp 3.12.0 `contact_force_fn` 解码单个 contact 的 force/torque；`to_world_frame=True` 只分别旋转两个三维向量，仍保留 contact 参考点。Newton 的 adapter 直接将结果取负写入 `contacts.force`，未把 contact torque 移到 body0 COM。因此在这两个固定实现的组合中，**前三维是已核对的 world 方向/shape0 符号，后三维不能无条件按通用 COM 契约解释**。[锁定 helper](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/support.py#L352-L391)、[Newton 调用及缺少换点](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L1497-L1534)。

若从后端拿到 contact 作用点 P，转换后的 shape0 wrench 应满足 $\tau_{C_0}=\tau_P+(P-C_0)\times f_0$；本章只解释缺口及所需换点，未修改上游、未运行验证修复。也不把此结论外推到其他 MuJoCo-Warp 版本。CPU 分支 `update_contacts` 本身抛 `NotImplementedError`。[读回 CPU 边界与容量](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L5497-L5515)。

### SensorContact 和时间平均

`SensorContact` 构造会请求 force，故应先 sensor 后 contacts；`sensor.update` 只聚合 `contacts.force` 的**线性**部分，body0 加、body1 减，分解出 world 切向力。它不是六轴 F/T sensor，不会补回 XPBD restitution impulse 或 MuJoCo 缺失的换点矩；position_matrix 是按力模长加权的接触中点，不是压力中心/净 wrench 等效点的通用保证。[构造顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L321-L329)、[聚合算法](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L90-L155)。

对每个子步已有的平均力 $\bar f_k=p_k/h_k$，若要报告时段 T 的平均：$\bar f_T=\sum_k h_k\bar f_k/T$。单位不同的峰值力、平均力与冲量不能互换；不等长步长不能直接对各步平均力取普通均值。XPBD 当前读回组成不完整时，再正确做时间平均也不会补出漏掉的恢复冲量。

跨子步 COM 在动，平均 torque 前先移到同一固定 O：$\bar\tau_O=T^{-1}\sum_k h_k[\tau_{C,k}+(C_k-O)\times f_k]$。这样定义的是固定参考点的离散平均；不是对“每一刻不同 COM 上的数字”直接求和。

## 9. 一个只供阅读的原生 API 片段

[最小读回例子](../examples/e3_contact_readback.py)使用 primitive sphere、显式 material/capacity、XPBD（恢复关闭）及 SensorContact，展示预请求、单步、读回顺序与带单位的 snapshot。**文件未执行，只通过 AST**。这里的一步用于讲 API 生命周期，没有采集实验数据、判断稳态或给参数做资格验证。

**读回限制就在这个例子中成立：**开启 contact-count weighting 后，报告力是两侧修正的近似对称表示；角力矩累计于各轮 COM，不能称为最终 COM 的精确连续时间测量。例子关闭 restitution，是因为当前读回不包含其独立速度修正；以后打开它也不能把返回值改称总冲击力。

片段特意在 solve **之前**检查 overflow，并在新 collide 前复制观测；`numpy()` 明确是同步读取，不伪装成零成本 GPU telemetry。它保留 source time、dt、solver/readback 组成说明，没有用 command 值填观测，也没有自行定义 DexLab 的抓取评分阈值。

若只需几何，可用下面的独立完整 Python 函数；它仍然未执行：

```python
import newton
import warp as wp


def snapshot_contact_geometry(model, state, contacts):
    count = int(contacts.rigid_contact_count.numpy()[0])
    if not 0 <= count <= contacts.rigid_contact_max:
        raise ValueError("Contact overflow: geometry snapshot is incomplete")
    distance = wp.empty(contacts.rigid_contact_max, dtype=float, device=model.device)
    point0 = wp.empty(contacts.rigid_contact_max, dtype=wp.vec3, device=model.device)
    point1 = wp.empty_like(point0)
    newton.eval_rigid_contact_kinematics(
        model, state, contacts,
        out_distance=distance,
        out_point0_world=point0,
        out_point1_world=point1,
    )
    return {
        "count": count,
        "distance_m": distance.numpy()[:count].copy(),
        "point0_world_m": point0.numpy()[:count].copy(),
        "point1_world_m": point1.numpy()[:count].copy(),
        "normal_world": contacts.rigid_contact_normal.numpy()[:count].copy(),
    }
```

这里的距离是提供 State 下重建出的间隙，但 normal 和集合仍来自最近的 collide；记录前后时刻时应注明这个混合采样契约。[原生 API](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contact_kinematics.py#L35-L78)。

## 10. 易错点与带答案阅读练习

| 现象/说法 | 源码检查方向 |
|---|---|
| 调大 shape.ke，XPBD 刚体更硬 | kernel 根本没有 shape.ke 输入；检查是否实际换了 solver 或 joint 参数 |
| contact_count>0 就有压力 | gap 可保留分离接触，solver 激活条件不同 |
| 改摩擦为零却仍有摩擦 | 双方组合、后端下限、contact scale=0 的 sentinel 与 kf 映射分开 |
| iteration=100 表示推进 100 个 h | 固定一个 h 内的约束迭代；不能据此更新时间戳 |
| 六维 contact force 换 side 直接取负 | 另一个 COM 还需要换点；MuJoCo adapter 还有固定版本缺口 |
| 已分配 force 数组就是已更新 | producer、后端支持、step/update/collide 顺序逐一查 |
| 冲击读回积分不等于动量变化 | XPBD 权重非动量守恒，恢复后处理增量未进入读回 |
| index 相同就是上一帧同一 contact | 可能重排、增删、匹配失败；不把 slot 当唯一标识 |
| tolerance 很小所以物理误差很小 | 先认 residual 定义与量纲，再看上限是否耗尽 |
| requires_grad=True 所以可优化碰撞事件 | 冻结 contact 集合的一阶 tangent 不包含离散检测导数 |

1. 两个 shape 的 mu 为 0.25 与 1.0；XPBD、VBD、MuJoCo 同优先级的基础组合分别是多少？
2. d=-0.002 m、h=0.001 s、w=2 kg⁻¹、relaxation=0.8；不加接触数权重，XPBD 法向返回变量和其等效平均力是多少？
3. 若该轮 A/B 接触数为 2/4，报告 scale 是多少？为什么不能同时精确代表两边的速度修正？
4. gap 之内但 d=+0.003 m 的 record 对当前 XPBD 法向位置 kernel 有什么结果？
5. body0 COM=(0,0,0)、body1 COM=(1,0,0)，body0 wrench 为 f=(0,2,0) N、tau=(0,0,1) N·m；body1 COM 处反作用 torque 是多少？
6. 子步为 0.001/0.003 s，所读平均力同方向分别 10/2 N；该 0.004 s 的平均是多少？它一定是包含恢复冲量的物理平均吗？
7. PADMM status 显示 iterations=max_iterations、converged=false；是否可以只报告“完成求解”？XPBD iterations 相同能否比较精度？
8. MuJoCo-Warp helper 已设 to_world_frame=True，为什么还不能宣布 body0 COM torque？SensorContact 会修复吗？
9. Contact matching 已打开，是否意味着 XPBD 的 position multiplier 已跨步 warm start？
10. 同一动态 body 的接触数为 2；对侧分别为 world 静态 shape（body=-1）和有 body ID 的 kinematic shape（计数为 4）。当前 kernel 的报告 scale 分别是多少？为什么“静止不动”不足以判断两者相同？

<details>
<summary>参考答案</summary>

1. 0.625、0.5、1.0；均以表中固定路径和无其他 override 为前提。
2. $p_n=0.8\times0.002/(0.001\times2)=0.8$ N·s；$p_n/h=800$ N。它是该线性化 correction 的等效量，不是运行结果或材料资格。
3. $2/(2+4)=1/3$。实际两边分别除 2 与 4，一个共同 scalar 无法同时等于 1/2 与 1/4。
4. record 可被检测保留，但当前 kernel 的 d>=0 分支返回，不产生该位置法向 correction。
5. $-\tau_0-(C_0-C_1)\times f_0=(0,0,1)$ N·m；力为 (0,-2,0) N。力矩没有简单变成 -1。
6. $(0.001\times10+0.003\times2)/0.004=4$ N。时间权重正确不意味着 producer 包含所有冲量；XPBD 的恢复增量仍缺失。
7. 应报告未收敛且预算耗尽。两者 residual/算法/迭代单位不同，不能比较相同次数代表的精度。
8. world 只改变表达轴；helper 只旋转两个三维向量，未做力臂换点。SensorContact 只聚合线性力，不修复 torque。
9. 不意味着。matcher 保存几何对应，XPBD contact correction 没有读取前一步累计量作为起始 multiplier。
10. 静态 -1 侧没有 body 计数，报告 scale 为 1/2；有 ID 的 kinematic 侧仍进入计数，报告 scale 为 2/(2+4)=1/3。kernel 依 body_id 而非速度或有效质量决定计数，虽然 kinematic 的有效逆质量为零、不会接受同样的动态 correction；不能依据外观静止就省略该分支。

</details>

## 11. 验收与下一步

[e3-validation.md](e3-validation.md) 与 [来源清单](sources.json)记录核对范围、源码身份、静态检查和保留问题。A4、B1–B5 及 B0 的核心动力学链已展开；E4 的传感/渲染、E5 的并行/学习与 E6 的专用 solver/扩展仍独立推进。SensorContact 在本章仅用于力数据消费，不能替代完整 A6。

后续优先 E4，以满足 E5 的依赖；E6 也已具备 E3 前置。实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab)，引用时保留实际版本、配置和证据缺口，不能用本章默认值补填过去的运行记录。
