# E1 · 模型、坐标、状态与时间

先修：[对象导读](guide.md)。应用路线读第 1–5、7–9 节；原理路线连同第 6、10 节一起读。本章完成 A1、A2，并交付 B0 的配置/空间量/惯量基础与 B4 的时间/积分基础。约束方程、完整求解过程和数值误差分析留在 E3，不把本章当作完整动力学课程。

阅读基线为 Newton **1.6.1**、固定提交 `713fecdc41caf0c9d726f5c016939f36e66e3dff`。Newton Python API、Warp 数组/内核运行时、具体 Solver 后端是三个层次；候选 Warp 1.18.0 不是本章实测环境。`SolverMuJoCo` 还涉及 MuJoCo/MuJoCo Warp 的单独身份。**本章仅核对官方源码、文件身份和片段语法，没有执行引擎、导入资产、仿真实验或性能测试。** 本文的数字算例是公式推导，不是测量结果。

## 1. 先决定谁描述结构、谁保存状态

Newton 将可编辑模型组装与设备数组分开。`ModelBuilder` 的 `add_link`、`add_joint_*`、`add_shape_*` 把结构写入构建器；`finalize(device=...)` 验证结构、组织索引并将模型数据转到指定 Warp 设备。修改构建器不会自动修改已生成 Model。固定拓扑的参数更新也需按相应 Solver 的通知协议处理，不能将 Model 理解为任意写入后自动传播的 Python 配置。

| 对象 | 本章关注的内容 | 创建/消费位置 | 所有权与边界 |
|---|---|---|---|
| `ModelBuilder` | body、shape、joint、articulation 与初始值 | 组装后 `finalize` | 构建阶段的 Python 数据；添加拓扑后重新 finalize |
| `Model` | 质量、惯量、形状、索引及初始 `joint_q/body_q` | Solver 构造、`state()`、`control()` | 设备数组；初始值与当前 State 是不同数组 |
| `State` | 粒子/刚体/关节位置、速度与力缓冲 | `model.state()`；传入/传出 `solver.step` | 新 state 克隆模型初值；没有通用仿真时钟字段 |
| `Control` | 目标、广义力等时变输入 | `model.control()` | 默认克隆；`clone_variables=False` 时引用 Model 的控制数组 |
| `CollisionPipeline` / `Contacts` | 碰撞生成和接触缓存 | `pipeline.contacts()`、`pipeline.collide(state, contacts)` | 接触几何是对某次状态采样的结果，不等于步后状态 |
| `Solver` | 推进、约束处理及后端内部数据 | `step(state_in, state_out, control, contacts, dt)` | 支持能力、权威状态表示和历史缓冲随 Solver 改变 |

依据：[finalize](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L12445-L12510)、[state/control 分配](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1809-L1946)、[官方双摆调用链](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_basic_pendulum.py#L66-L123)。Model 的 `set_gravity` 要求随后通知 Solver，见[参数更新入口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1948-L1972)。

### body、shape、joint 与 articulation

`add_body()` 是便利入口：它创建一个 link、一条连接 world 的 FREE joint，以及单体 articulation。多体机构用 `add_link` 加各条 joint，再用 `add_articulation` 组织。**body ID、shape ID、joint ID、坐标数组起始位置不是同一个编号空间。** `add_body(label="block")` 的返回值是 body ID，不是 `joint_q` 的下标。[实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L5104-L5169)

shape 的 `xform` 相对于所属 body；body 的 `xform` 是世界位姿。`body=-1` 的 shape 属于静态世界几何。`add_shape_box` 的 `hx/hy/hz` 是半边长，不是全尺寸。一个 body 可以有多个 shape；形状的视觉开关、碰撞开关和质量贡献需分别检查。[shape 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L7281-L7321)、[box 半边长](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L7730-L7761)

静态世界 shape、由 FIXED joint 约束的 body、`is_kinematic=True` 的 body 是不同建模方式。KINEMATIC 是用户指定运动、不受外力推进的刚体；公共积分 kernel 会把输入位姿/速度原样复制到输出，**仅赋一个非零速度不会自动生成 kinematic 轨迹**。本版本存储的 body flag 是 DYNAMIC 或 KINEMATIC，不能凭其他引擎经验猜一个 `STATIC` flag。`is_static=True` 是 shape 的零质量贡献选项，也不等于冻结它所属的动态 body。[flags](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/enums.py#L119-L145)、[kinematic 分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L133-L141)

## 2. 坐标与姿态：先写定义，再代数计算

本文定义 $T_{WB}=(R_{WB},p_{WB})$ 为将 body 坐标变到 world 的刚体变换：

$$
x^W=R_{WB}x^B+p_{WB},\qquad T_{WC}=T_{WB}T_{BC}.
$$

旋转矩阵满足 $R^TR=I$、$\det R=1$；向量只乘 $R$，点还要加 $p$。因此局部 shape 位姿要和 body 位姿组合，不能直接当作世界坐标。关节的 `parent_xform`、`child_xform` 分别在父/子 body 局部系中定义关节锚点；可运动变换夹在两者之间：$T_{WC}=T_{WP}T_{PJ_p}T_{J_pJ_c}(q)T_{CJ_c}^{-1}$。源码对应 `X_wpj * X_j * inverse(X_cj)`。[关节递推](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/articulation.py#L342-L386)

Newton 默认右手系、Z-up，`ModelBuilder(up_axis=...)` 可指定其他 up 轴。显式 `gravity=(gx,gy,gz)` 不受 up 轴约束；省略时才默认沿 up 的反向取 9.81 m/s²。换 up 轴时，要一起检查重力、地面、资产方向和相机，不只是改绘图。[轴系与重力](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst#L341-L415)、[构造参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L1480-L1498)

| 量 | Newton API 表示 | 单位/约定 |
|---|---|---|
| 位置、COM、形状长度 | `vec3`、transform 平移 | m；必须标注 frame |
| 旋转 | `wp.quat(x,y,z,w)` | 单位四元数，标量在最后；$q$ 与 $-q$ 表示同一旋转 |
| revolute 坐标/速度 | `joint_q` / `joint_qd` 的标量片段 | rad / rad·s⁻¹ |
| prismatic 坐标/速度 | 同上 | m / m·s⁻¹ |
| 质量、密度、惯量 | `body_mass`、shape density、`body_inertia` | kg、kg·m⁻³、kg·m² |
| 外力/力矩、时间步 | `body_f`、`dt` | N / N·m；s |

四元数为 $q=(\hat a\sin(\theta/2),\cos(\theta/2))$，其中 $\hat a$ 是单位轴，$\theta$ 用弧度。不能将 `[roll,pitch,yaw]` 塞进 quaternion 的前三项。MJCF 文件四元数采用 wxyz，Newton 导入器会显式重排为 xyzw；原生 `wp.quat` 调用则由使用者保证顺序。MJCF Euler 的角度单位还取决于 compiler，文件角度约定不是 State 的关节角单位。[四元数约定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst#L291-L339)、[MJCF 姿态解析](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_mjcf.py#L885-L917)、[compiler angle](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_mjcf.py#L425-L440)

## 3. 质量和惯量如何进入 Model

`body_com` 是 body 局部系中的质心位置 $c^B$；`body_q` 的平移是 body 原点的世界位置。世界质心为 $c^W=p_{WB}+R_{WB}c^B$。`body_inertia` 是绕 COM、在 body 局部方向表达的 $3\times3$ 惯量；公共积分函数将世界角速度/力矩旋回局部系后使用该矩阵。[字段](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1079-L1095)、[积分中的惯量坐标](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L79-L109)

对质量 $m$、COM 惯量 $I_C$ 的刚体，换表达方向 $R$、再从 COM 换到偏移为 $d$ 的平行轴：

$$
I_O=RI_CR^T+m\big((d^Td)I_3-dd^T\big).
$$

这是质量分布的几何关系；不是随意把每个对角元乘相同系数。组合多个 shape 时先用 $c=\sum_i m_i c_i/\sum_i m_i$ 得到新 COM，再将每个形状的旋转惯量平移到该点相加。Builder 的 `_update_body_mass` 正是这条路径。[惯量变换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/inertia.py#L570-L603)、[累加质量与 COM](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L11082-L11114)

默认 shape density 为 1000 kg/m³。shape 只有在非 static、密度大于零、附着于 body 且该 body 未锁惯量时才计算并累加质量。若你已经显式给定 body 的 mass/com/inertia，再添加有密度的 shape，会额外增加质量；`lock_inertia=True` 可禁止后续 shape 修改这三项，但它不阻止 fixed-joint 合并时的质量汇总。[默认密度](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L790-L799)、[累加条件](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L7487-L7496)、[lock 语义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L5019-L5053)

**手算检查。** 均匀实心 box 的全尺寸为 $(2h_x,2h_y,2h_z)$：

$$
m=8\rho h_xh_yh_z,\quad I_{xx}=\frac{m}{3}(h_y^2+h_z^2),
$$

其余对角项循环置换，COM 在 shape 中心。取半边长 $(0.10,0.05,0.025)$ m、密度 1000 kg/m³，则质量为 1 kg；COM 三个主惯量分别约为 $(0.00104167,0.00354167,0.00416667)$ kg·m²。若将 shape 放在 body 局部 `(0.10,0,0)`，COM 会随之偏移，但仅由该 shape 构成的 body 绕其 COM 惯量不因此增加平行轴项。算法参见[box 质量/惯量](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/inertia.py#L258-L297)。

物理上非退化三维刚体的惯量应对称正定，主惯量还满足三角不等式。不要用负惯量或乱填很小的数来“调稳定”。Builder 的 `balance_inertia`、`bound_mass`、`bound_inertia` 以及 finalize 的校正可能改变输入数据，因此应将导入前数据与最终 Model 字段分开记录；校正通过不等于测得了真实物体参数。[校正设置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L1572-L1590)、[finalize 说明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L12461-L12489)

## 4. 导入资产不是照搬文件名

原生入口是 `builder.add_urdf`、`add_mjcf`、`add_usd`。导入器把各自文件语义变成 Newton 的 bodies/shapes/joints；之后仍要检查所选 Solver 是否支持生成的字段。文件解析成功不能证明驱动、接触或闭环行为等价于原宿主。

| 入口 | 此版本要核对的选项/行为 | 读入后需要保留的记录 |
|---|---|---|
| [URDF](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L3878-L4000) | `scale`、`up_axis`、`ignore_inertial_definitions`、`parse_visuals_as_colliders`、fixed-joint collapse | 源单位、根连接方式、最终 body/joint 标签与索引；不要把 visual mesh 默认当 collider |
| [MJCF](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L4342-L4488) | compiler angle、inertiafromgeom、`ignore_inertial_definitions`、`scale`；四元数重排 | compiler 与显式 inertial 的优先关系、最终惯量、solver 不支持的属性 |
| [USD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L4024-L4150) | `apply_up_axis_from_stage`；stage 单位；碰撞/视觉导入分支 | stage 元数据、物理 schema、路径到实体映射及所有导入警告 |

### 缩放必须和质量假设一起说

几何相似、均匀缩放因子 $s>0$，**若保持密度**，理论上长度乘 $s$、质量乘 $s^3$、COM 惯量乘 $s^5$；**若保持质量**，惯量乘 $s^2$。这是两种不同假设。

v1.6.1 的 URDF 显式 `<inertial>` 路径将 COM 长度乘 `scale`、惯量乘 `scale**2`，显式 mass 原样读取；MJCF 显式 inertial 路径也是如此。不能以为对已有显式质量的机器人设置 `scale=2` 会自动令质量变为 8 倍。几何/密度推导走另一条路径。[URDF 处理](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_urdf.py#L646-L706)、[MJCF 处理](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_mjcf.py#L2293-L2358)

### USD 的版本限制必须保留

该版本对 legacy 刚体/collider 导入仍要求 `metersPerUnit=1.0`、`kilogramsPerUnit=1.0`；非单位元数据会触发警告。粒子分支存在 SI 转换，但与 legacy 刚体混合时采用不同路径。**不能把“读取了 metadata”写成“所有 USD 自动换算正确”**。对本章的刚体资产，应事先把几何与物理量统一到米/千克，并令元数据一致；仅改 metadata 而不转换内容同样错误。[实际分支与警告](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_usd.py#L631-L711)

资产维护记录至少包括原始 URL/提交、作者与许可、尺寸/单位、视觉和碰撞网格是否相同、质量来源、导入选项、坐标变换以及哪些属性被忽略。引擎的 Apache-2.0 许可不会自动覆盖外部机器人/网格；本仓示例只使用原创 primitive，不分发第三方资产。

## 5. 配置维度不等于速度维度

设配置是 $q\in\mathcal Q$，广义速度是 $v\in\mathbb R^{n_v}$。四元数用 4 个数表示 3 个旋转自由度，因此一般有 $\dot q=N(q)v$，而不是对所有关节都成立的 `q += dt * qd`。

| joint type | 配置坐标数 | 速度自由度数 | 解释 |
|---|---:|---:|---|
| PRISMATIC / REVOLUTE | 1 | 1 | 一条平移/转动轴 |
| BALL | 4 | 3 | quaternion 与角速度 |
| FREE / DISTANCE | 7 | 6 | 平移 + quaternion；DISTANCE 仍有额外约束语义，数组长度不表示无约束 |
| FIXED | 0 | 0 | 相对位姿固定；body 仍可随父体运动 |
| D6 | 所配置轴数 | 所配置轴数 | 不必恰好 6；查构建后 layout |

依据：[JointType 与 dof_count](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/enums.py#L178-L245)。ROD 的材料槽和 VBD 路径在 E6 讨论，不混入普通六维自由关节表。

每条关节分别使用 `model.joint_q_start[j:j+2]`、`joint_qd_start[j:j+2]` 定位；两个数组都有末尾 sentinel。`joint_coord_count` 与 `joint_dof_count` 才是全数组分配尺寸。不能用 joint ID 当 q 下标，不能拿 q 的切片切 qd，也不要在导入/合并/多 world 后假定旧索引仍有效。[起始表定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1191-L1205)

`State` 同时能容纳 `body_q/body_qd` 和 `joint_q/joint_qd`，但**存在数组不代表它是当前更新的权威状态**：

- XPBD 使用 maximal coordinates，即逐 body 位姿/速度加关节约束。`step` 推进 body 字段；要获取对应的 generalized joint 数值，显式用 `newton.eval_ik(model, state, state.joint_q, state.joint_qd)` 做状态重建。
- `eval_fk(model, joint_q, joint_qd, state)` 从关节输入更新 body 字段；它不是自动复制传入 q/qd 到 State 的万能同步器，也不是动力学步进。
- SolverMuJoCo/Featherstone 使用 generalized coordinates，不能把只改 body pose 当作有效机器人 reset。SolverMuJoCo 的同步周期和后端状态还需单独核查。

依据：[坐标表示分类](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst#L55-L64)、[FK 输出契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/articulation.py#L539-L572)、[IK 输入/输出契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/articulation.py#L958-L988)、[MuJoCo reset 同步说明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4198-L4216)。这里的 `eval_ik` 是从已有 body 状态重建关节数值，不是给末端目标求机器人的规划器；目标 IK 留给 E2。

## 6. 读懂六维速度与力：顺序、frame、参考点

| 字段 | 前三项 / 后三项 | 表达方向与参考点 |
|---|---|---|
| `State.body_qd[b]` | $v_C$ / $\omega$ | 都在 world 表达；线速度参考点是该 body COM |
| `State.body_f[b]` | $f$ / $\tau_C$ | world 力与绕 COM 的力矩；外部输入缓冲，不是总接触反力 |
| FREE/DISTANCE 的 `State.joint_qd` | 相对线速度 / 相对角速度 | child COM 参考的关节速度，表达在 joint parent frame；父体运动由递推另行加入 |
| FREE/DISTANCE 的 `Control.joint_f` | 力 / 力矩 | 本版本 API 指定 world 表达、child COM 参考；不能因数组与 qd 等长就假定可直接点乘算功率 |

依据：[State 字段](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L119-L175)、[关节递推实际换系](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/articulation.py#L358-L386)、[Control 的特殊约定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py#L32-L44)。Warp 的底层空间向量 helper 通常 angular-first；Newton 公共数组是 linear-first。应使用 Newton 对应转换 helper 的约定，或明确重排后再调用 Warp，不能直接把 `body_qd` 当作 Warp 的任意 twist 输入。[布局适配实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/math/spatial.py#L54-L134)

**同一刚体上的换点。** 所有量先表达在同一 world 方向，令 $r=p_{new}-p_{old}$，则：

$$
v_{new}=v_{old}+\omega\times r,\qquad
\tau_{new}=\tau_{old}-r\times f.
$$

力矩负号来自同一力作用点 $P$：$\tau_O=(P-O)\times f$，把参考点从 old 换到 new，力臂就减去 $r$。因此从 COM 速度取 body 原点速度，令 $r=-R_{WB}c^B$；得到 $v_B=v_C-\omega\times R_{WB}c^B$。从作用点 P 的力写入 COM wrench 时，则 $\tau_C=\tau_P+(P-C)\times f$。

**源码纠错记录。** 固定版本 [conventions primer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst#L19-L26) 对 `r=new-old` 打印了力矩加号，和上述参考点定义不一致；同文 [body/spatial mapping](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst#L195-L210) 的一条 twist 公式与前文定义也有符号冲突。本章不照抄这两条，而用明确的点定义推导，并对照 [XPBD joint force kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L1020-L1035) 的 `r_c=joint_point-COM` 及[实际 `r_c cross f` 累加](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L1106-L1110)。`transform_wrench` 的 `+p cross f` 使用的是 source frame 原点在 destination frame 中的位置，是另一种变换定义，不与上面的换点负号矛盾。

手算：COM 在原点，力 $f=(0,10,0)$ N 作用于 $P=(0.2,0,0)$ m，则绕 COM 的力矩为 $(0,0,2)$ N·m；把参考点移到 P 后力矩应为零。这比背诵一条未说明 r 方向的公式更可靠。

## 7. 时间步、子步和 Solver 迭代分清

调用者维护时间，`dt` 的单位为秒。若一帧物理时长为 $H$，分为 $N$ 个子步，则每次 `step` 传 $h=H/N$，一帧累计推进 $H$。渲染 FPS、控制更新周期、接触重算周期可以不同，必须分别记录。Solver 的 `iterations` 是一次 step 内部的约束迭代次数，**不会让物理时间推进 iterations 倍**。

例如设渲染/控制帧 $H=1/60$ s、$N=4$，则 $h=1/240$ s；若控制命令整帧保持，是 60 Hz 零阶保持输入。将控制器放到每个子步会改变为 240 Hz 更新的离散系统，不能只称作“同一控制”。这些是教学参数，不复用为 DexLab 的实测配置。[官方 frame/substep 定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_basic_pendulum.py#L23-L30)、[时间累计位置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_basic_pendulum.py#L105-L123)

原生 XPBD 示例的顺序为：

```text
state_in(t) → clear_forces → 写入本子步外力/控制
            → collide(state_in, contacts)
            → solver.step(..., h) → state_out(t+h)
            → 交换 Python 引用 → 更新调用者的时间
```

注意 `clear_forces()` 只清 State 的 particle/body 外力缓冲，不清 Control 的目标/关节力，不清 solver 历史，不重置位置。持续外力应在每次清理之后重新写入；写完马上 clear 会把输入擦掉。[实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L193-L205)

**采样必须标注阶段。** 步前 collide 得到的接触位置/法线属于输入位姿；步后 body pose 属于 $t+h$。把二者拼成一条观测而不标阶段会误判接触位置。需要步后几何时再次 collide；需要该次求解的接触冲量/力则走 solver 的观测接口，不能用重新生成的几何替代。本章只确定数据时序，接触 force/impulse 语义在 E3 完整展开。[XPBD step 输入契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L389-L407)

### 双缓冲与引用不是数据复制

`state_0, state_1 = state_1, state_0` 交换的是 Python 名称。保存 `old_pose = state_0.body_q` 只得到同一设备数组的另一个引用；后续这个 buffer 被写入时，所谓历史也会变化。保存 pose 应 `wp.clone(state_0.body_q)`；保存全部已分配 State 数组可 `snapshot=model.state(); snapshot.assign(state_0)`，前提是两者布局/扩展属性匹配。`State.assign` 会检查缺失数组，不拷贝 solver 或任意 Python 的控制器变量。[assign](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L206-L255)

CUDA graph 还捕获具体设备数组的使用关系；奇数子步的 Python 引用交换不能直接推广成 graph replay 的正确循环。该版本 `State.assign` 示例专门处理最后一步的复制。最小例子使用普通循环、不做 capture，graph 专题在 E5。

## 8. 重置和快照：选择你要恢复的层次

| 需求 | 要保存/恢复什么 | 能作出的承诺 |
|---|---|---|
| 只回放几何 | body/particle pose 与时间标签 | 能显示历史形状，不能从中恢复完整动力学 |
| 恢复公开 State | 相同布局的全部 State 数组，必要时 FK/IK 同步 | 公开物理状态恢复；不自动含控制器/RNG/后端历史 |
| 回到模型初始条件 | 新 `model.state()`、初始 Control、调用者时钟、派生几何、所选 solver reset 逻辑 | 是重新初始化；不等于任意时刻快照继续 |
| 完全相同的续算 | 上述状态 + 后端缓存/激活/历史 + 控制器/RNG/步数/调度/运行配置 | 必须依 Solver 的序列化契约与未来验证证明；本章未作此承诺 |

`SolverBase.reset(state, ...)` 默认只做 mask 规范处理、没有通用物理复位实现。SolverMuJoCo override 会把所选 joint state 设回 Model 默认并清理 warm-start、act、ctrl、外力等后端数组；因此“先恢复任意中途快照，再无条件调用 reset”可能把你恢复的关节状态覆盖掉。不要跨 Solver 发明统一 reset 语义。[base reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L538-L570)、[MuJoCo reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4181-L4234)

`body_q_prev` 已弃用，源码要求应用显式 clone 所需历史。Solver 内部自行管理前一姿态，公开 State 不能因此被当成所有内部历史的容器。[弃用说明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L12-L17)

本章的 [最小例子](../examples/e1_model_state.py) 选择简单可审查的语义：构造一个偏心 primitive 自由体，保存 **t=0 的 State**，展示一帧普通双缓冲循环，随后恢复两个 buffer、重建 Control/Contacts 和 XPBD Solver 并归零时钟。它展示冷启动式复位，不展示中途快照的逐位一致续算；文件仅做语法检查，所有原生调用均未执行。

## 9. 原生例子与故障定位

例子只有一个自由体与地面，没有外部资产、窗口、训练或评分器。主形状半边长、密度与第 3 节手算一致，局部 shape 偏移让 `body_com` 与 body 原点不同。预期 q/qd 尺寸 7/6 来自 FREE joint 构造规则，不是一次运行输出。

| 表面症状 | 首先读哪些量 | 典型错误与修改方向 |
|---|---|---|
| 模型尺寸差 1000 倍 | 文件单位、scale、shape 半边长 | 把 mm 当 m；避免同时修改文件和 importer scale 两次换算 |
| 静止模型 COM 不在几何中心 | `body_com`、shape xform、显式 inertial | COM 本来就相对 body 原点；先检查质量分布，不强行归零 |
| 新加碰撞壳后质量增加 | density、`lock_inertia`、导入惯量路径 | 手工质量与 shape 质量被叠加 |
| 设置 q 后渲染没变化 | 权威 q/body 字段、FK 调用及读取的 buffer | 改了 generalized q，但 maximal pose 未同步；或读取旧 buffer |
| q 和 qd 切片长度不同 | joint type、两套 start 表 | quaternion 冗余坐标；用同一下标切两套数组 |
| “保存的上一帧”跟着变化 | Python 引用、设备数组、clone | 别名不是快照 |
| kinematic body 有速度却不移动 | body flag、用户轨迹更新位置 | 用户指定运动分支只传递状态，需自己更新位姿和一致速度 |
| 换 solver 后 reset 无效 | solver reset 实现、权威状态和缓存 | base reset 不是通用复位；不要只清 body pose |
| 只加 iterations 后模拟变快 | 调用者时钟与 dt 累加位置 | 迭代次数被错误算作物理子步 |
| 力矩方向相反 | r 的方向、参考点、frame、linear/angular 顺序 | 区分换参考点与换坐标的 transform |

## 10. 从积分源码理解 B4 的起点

先限定 **无约束刚体预测阶段**。公共 `integrate_rigid_body` 把速度视为 world COM 线速度与 world 角速度；对质量非零的动态体，先更新速度再更新 COM：

$$
v_{n+1}=v_n+h(m^{-1}f_n+g),\qquad c_{n+1}=c_n+h v_{n+1}.
$$

这是半隐式 Euler 的速度后位置顺序。转动在 body 系计算陀螺项：

$$
\omega_B=R^T\omega_W,\quad
\widetilde\omega_W=R\left[\omega_B+hI_B^{-1}(R^T\tau_W-\omega_B\times I_B\omega_B)\right].
$$

随后用世界角速度左乘 quaternion 增量并归一化：

$$
q_{n+1}=\operatorname{normalize}\left(q_n+\tfrac h2(\widetilde\omega_W,0)\otimes q_n\right),\quad
p_{B,n+1}=c_{n+1}-R(q_{n+1})c^B.
$$

源码在计算新 quaternion **之后** 对输出角速度乘 `1-angular_damping*h`；所以上式中的 $\widetilde\omega$ 是阻尼前中间量。示例显式设 `angular_damping=0`，避免把该差别隐藏在默认值中。[逐行实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L65-L111)

XPBD 会在这个预测后进行约束修正，并进一步更新速度；**不能因其预测器是半隐式 Euler 就把整个 XPBD 算法等同于无约束 Euler，也不能把 XPBD 类说明中的 implicit 当作通用 Backward Euler/Newton 法实现证据**。完整约束和恢复系数路径在 E3 展开。[预测调用](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L507-L560)、[类与支持限制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L50-L100)

单位检查有助于发现错误：$hf/m$ 为 m/s，$hI^{-1}\tau$ 为 rad/s。时间步减小、迭代增多和浮点精度提高处理不同误差；没有“只增迭代就必然稳定准确”的结论。离散误差、约束残差、碰撞采样误差、接触模型差距需在 E3 分开讨论。本阶段没有进行时间步或求解器对照实验。

## 11. 阅读练习与参考答案

1. 一个 FREE 根和两个 REVOLUTE 关节，不计 padding，q/qd 各多少元素？为何不可逐项相加积分？
2. 第 3 节的 box 全部长度乘 2，若仍按密度生成惯量，质量和 $I_{xx}$ 变多少？若走显式 URDF inertial 路径呢？
3. $c^B=(0.1,0,0)$、姿态单位、$v_C=0$、$\omega=(0,0,2)$，body 原点速度是什么？
4. `saved=state_0` 后做双缓冲交换两次，为何 saved 不一定是历史？如何保存 State 的数组？
5. 为什么 XPBD 步后对 `state.joint_q` 的直接读取可能是旧值？`eval_ik` 在这里做什么？
6. 若一帧 0.02 s、5 个子步、每步 8 次迭代，一帧推进多久？外力在何时写？
7. 有一个 USD stage 声明厘米单位，本版本为什么不能仅依据 importer 返回成功就验收尺寸？
8. 想恢复 MuJoCo 后端中途快照，为什么不能无条件追加 `solver.reset(state)`？

<details>
<summary>参考答案与源码定位</summary>

1. q 为 $7+1+1=9$，qd 为 $6+1+1=8$；FREE quaternion 用 4 个数表示旋转，角速度只有 3 维，需相应姿态积分映射。看第 5 节。
2. 固定密度：质量 $8$ kg，惯量乘 $32$，$I_{xx}\approx0.0333333$ kg·m²；显式 inertial 路径的质量仍 1 kg，惯量乘 $4$，$I_{xx}\approx0.00416667$ kg·m²。两者对应不同缩放假设，不是导入器同一结果。
3. $v_B=v_C-\omega\times c^B=(0,-0.2,0)$ m/s。质心线速度为零不代表 body 原点静止。
4. saved 是同一个 State 对象；旧 buffer 会再成为输出并被覆盖。先分配同布局 State，再 `snapshot.assign(state_0)`；这仍不含 solver/private/controller 状态。
5. XPBD 推进 maximal body 数据，不自动保证 generalized 数组刷新；`eval_ik` 从 body pose/twist 重建 joint q/qd，不求给定末端目标的控制动作。
6. 每步 $h=0.004$ s，5 步合计 0.02 s；8 次迭代不增加物理时间。外力在每个子步 clear_forces 之后、step 之前写入。
7. legacy 刚体路径会警告非单位 stage metadata，粒子路径与刚体路径不同；必须检查已转换的资产数据、metadata、最终 shape/质量字段及警告，不能把成功返回当作正确 SI 单位的证据。
8. override 会把所选 joint state 置回 Model 初值并清 warm-start/act/ctrl 等后端数据；这会破坏任意中途状态的继续语义。先确定是初始化复位还是精确续算，并按具体后端的完整契约实现。

</details>

## 12. 本章验收与下一步

[验证记录](e1-validation.md)列出源码身份、链接锚点、原创 Python 文件和 Markdown 片段的语法检查。静态审查涵盖 A1/A2 的建模/资产、状态/时间契约，B0/B4 只交付本章声明的基础子集；未把任何物理或性能性质标成运行验收。

接下来 E2 从这些状态与布局进入 `Control`、原生驱动、机器人 FK/目标 IK 和任务时序；E3 延续空间量及积分基础，展开接触/约束/求解器/力观测。实验案例最终复用 [DexLab](https://github.com/huangkiki/Dexlab)，总入口见 [Sim Atlas](https://github.com/huangkiki/sim-atlas)。
