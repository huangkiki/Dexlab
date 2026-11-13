# E1 · 建模、坐标、状态与时间

本章把“模型是什么”“此刻状态是什么”“一次 step 推进多久”连接起来。完成后应能读懂资产到原生字段的映射，选择正确坐标与状态接口，并判断 reset 能恢复什么。应用路线覆盖 A1、A2；原理路线交付 B0 的状态/惯量基础、B4 的时间/积分基础。接触方程、求解器收敛与多物理离散化细节由 E3、E6 继续展开。

先修：[导读](guide.md)，向量、矩阵乘法、牛顿第二定律。公式采用 SI 单位与右手旋转；推导中的刚体、定密度和无接触条件会分别标明。阅读基线为 Genesis 1.4.3 官方提交 `216a708e06124595521a9d36a51fae5393fd4ff8`，不是当前最新版保证，也不能反推 DexLab 历史运行配置。Genesis Python API、物理 solver、编译后端和用于资产解析的 MuJoCo 是不同层，导入 MJCF 不会把 Genesis 的物理步进换成 MuJoCo。

**验证状态：固定源码已阅读并核对 Git blob；教学片段仅语法检查，未运行 Genesis、未做物理实验。** [验收记录](e1-acceptance.md)给出可复查范围；后续实验复用 DexLab。

## 1. 从资产到状态：生命周期和责任

`gs.init()` 选择设备、精度与全局类型；`gs.Scene` 持有 Simulator、各 solver、传感与可视化管理器。`scene.add_entity(morph=..., material=..., surface=...)` 的三个参数职责不同：Morph 描述几何、初始姿态及资产导入选项，Material 决定力学表示与参数，Surface 决定外观。相同 Mesh 可以进入刚体、MPM 或 FEM，不能看到 Mesh 就假定有刚体关节。

`Simulator._add_entity` 根据 material 类型选择最具体匹配的 solver；`Rigid` 派生自 `Kinematic`，因此不是“第一个 isinstance 匹配即胜出”。Hybrid 另走组合实体路径。`scene.build()` 才分配批量布局、solver 缓冲、耦合器与传感器，并建立初始状态。build 前读模型描述，build 后通过 getter 读动态状态；修改 `morph.pos` 不等于更新已构建实体。[分派源码][dispatch]、[构建源码][build]

| 对象/字段 | 所有者与用途 | 不应混淆的量 |
|---|---|---|
| `Morph.pos/quat` | 创建时资产姿态描述 | 运行中的 `entity.get_pos/get_quat()` |
| `entity.joints/links` | 导入后拓扑及索引对象 | 原始 XML 文件的行号或枚举顺序 |
| `entity.n_qs/n_dofs` | 配置维度与切空间维度 | 四元数有四个分量但只有三个旋转自由度 |
| `scene.sim.*_solver` | 各求解器的状态和算法 | `Scene` 不是一个统一物理状态向量 |
| `SimState.solvers_state` | 按 solver 组织的查询结果 | 不是包含全部控制器、随机数和传感器历史的进程快照 |

`gs.init(precision="32")` 和 `"64"` 使用字符串。该版本设置对应 NumPy/Torch/内核浮点类型；Metal 路径拒绝 64 位。精度描述的是所选数值类型，不能据此承诺任意 solver、外部解析器和渲染管线都同精度，更不能当成物理正确性结论。[参数校验][precision]、[类型赋值][precision-dtype]

## 2. 单位、姿态与三个容易混淆的坐标系

### 2.1 先写量纲，再传参数

| 量 | 本章采用的原生约定 | 常见错误 |
|---|---|---|
| `Morph.pos`、Box `size`、Mesh 长度 | m；Box `size` 是完整边长 | 将 mm 网格直接当 m；把半边长当完整尺寸 |
| `Morph.euler/offset_euler` | **度**；SciPy extrinsic x-y-z | 将机器人关节的弧度习惯直接套入 morph |
| `Morph.quat/offset_quat` | `(w, x, y, z)`，单位四元数 | 将 `(x, y, z, w)` 原样传入 |
| 转动关节配置/速度 | rad、rad/s | 与 Morph.euler 的单位混用 |
| 平移关节配置/速度 | m、m/s | 用一个统一“角度数组”描述全部 DOF |
| 质量、密度、转动惯量 | kg、kg/m³、kg·m² | 把惯量当质量或无量纲矩阵 |
| `SimOptions.dt`、重力 | s、m/s²（等价 N/kg） | 将 viewer FPS 当物理步长 |

位置和姿态约定见 [Morph][morph]；重力默认 `(0, 0, -9.81)`，对应通常的 Z-up 场景，[SimOptions][sim-options]。输入资产可能 Y-up，文件导入的 `file_meshes_are_zup=False` 会作 `(X,Y,Z) → (X,-Z,Y)` 转换；不要再在模型上重复旋转一次。[文件选项][file-morph]

**文档与实现冲突要读校验器。** Morph 的参数说明仍写“给 quat 后忽略 euler”，但 `_resolve_orientation` 实际对同时非空的二者抛错。本教程只设置其中一个。默认 quat 是 `(1,0,0,0)`。[实际分支][morph]

### 2.2 世界、作者原点、内部求解原点

设世界系为 W，资产作者使用的 link 原点为 A，求解器内部原点为 S。`offset_pos/quat` 在 A 系表达；不含额外惯量对齐时：

$$
{}^W T_S={}^W T_A\,{}^A T_S,\qquad
p_{WS}=p_{WA}+R_{WA}p_{AS},\quad R_{WS}=R_{WA}R_{AS}.
$$

这是父子变换，offset 随主体旋转，不是简单世界平移。自由根若启用 `align`，内部 frame 还包含质心/主惯量轴对齐；`align=None` 对普通单自由根刚体与关节机器人解析出的默认值不同，不能一律当 False。启用后该自由根的质心和惯量不能在 build 后随意重写。[Morph offset][morph]、[align 规则][file-morph]

`entity.get_pos()/get_quat()` 的 `relative=True` 默认值意为“恢复作者原点”，**并不表示在父坐标系表达**。`relative=False` 报内部求解原点；自由关节 `get_qpos()` 总是内部原点的世界姿态，未作作者 offset 的逆转换。即使实体静止，二者位置也可能不同。[姿态 API][poses]、[配置 API][states-api]

线速度还与取样点有关。若 S 相对 A 的世界位移是 d，则刚体运动满足：

$$
v_S=v_A+\omega_W\times d.
$$

`get_vel(relative=True/False)` 两种结果均在世界轴下表达，分别对应两个原点；不能仅旋转一下速度就消除取样点差异。`get_ang()` 从世界空间角速度字段读取。自由关节的前三个 DOF 速度是内部原点的世界线速度，后三个是局部旋转速度；其四元数更新为右乘局部增量，不能直接当成世界 `get_ang()`。[速度 API][poses]、[getter 实现][getters]、[积分源码][integrate]、[四元数乘法][quat-product]

单位四元数 r 与 −r 表示同一旋转。因此姿态差不宜逐分量相减；先构造相对旋转，再映射到旋转向量。小角度线性化只适用于接近零的误差，接近 π 时还需约定轴和分支。此处是旋转几何说明，不是本章新增的控制器实现。

## 3. 资产导入、视觉几何、碰撞几何与惯量

### 3.1 “同一个文件”不保证“同一个物理模型”

| 入口 | 源码中必须追踪的决策 | 教程中的处理 |
|---|---|---|
| `gs.morphs.Box/Sphere/...` | 尺寸、固定/自由、初始姿态 | 优先用原创简单几何解释字段 |
| `gs.morphs.Mesh` | scale、坐标轴、凸化/分解、视觉和碰撞表示 | 记录转换选项，不从渲染外观推断碰撞体 |
| `gs.morphs.URDF` | 固定 link 合并、惯量 frame、joint 类型和限位 | 导入后按名字取 joint，再读实际索引 |
| `gs.morphs.MJCF` | MuJoCo 解析结果如何映射到 Genesis 的 joint/material/actuator | 对不支持或近似项保留警告，不宣称模型全等 |

URDF 的 `merge_fixed_links=True` 是此版本默认值，`links_to_keep` 可保留指定 link。合并可改变 link 数量、名字到索引的关系以及合成惯量，不能硬编码“第六个数组元素就是第六个 XML joint”。MJCF 映射明确区分 free、hinge、slide、ball；导入分支对 free joint stiffness、ball joint limit、actuator internal dynamics 等有拒绝或警告。[URDF 解析][urdf]、[MJCF 类型映射][mjcf]、[导入限制][mjcf-limit]；完整选项见 [源码地图](source-map.md) 的 morphs.py。

`visualization=False` 与 `collision=False` 是独立开关，但 Morph 校验器不允许两者同时为 False，且对应描述明确限定刚体用途。凸化/分解改变实际接触形状；质量属性则还可能来自资产显式 inertial 或几何估计。读者应分别记录视觉 mesh、碰撞表示、质量来源，不将“看起来相同”当成惯量相同。[Morph 校验][morph]、[文件选项][file-morph]

### 3.2 惯量不是三个随便填写的数

对于密度 $\rho$、体积 V 的刚体，质量 $m=\int_V\rho\,dV$，质心 $c=m^{-1}\int_V\rho x\,dV$。关于质心、在某指定轴系表达的转动惯量为：

$$
I_C=\int_V\rho\big(\|x-c\|^2\mathbf 1-(x-c)(x-c)^T\big)dV.
$$

对长度 a,b,c 的均匀长方体，$I_{xx}=m(b^2+c^2)/12$，另两项循环置换；不是 a²/12。把一个部件旋转 R，并将其质心相对组合质心平移 d，组合时使用：

$$
I_{\mathrm{combined}}=\sum_i\left(R_i I_i R_i^T+m_i(\|d_i\|^2\mathbf1-d_i d_i^T)\right).
$$

这是假设各部件刚性绑定的平行轴定理，不能把不同 frame 下的惯量直接逐元素相加。`compose_inertial_properties` 先变换各质心、求总质心，再积累平移旋转后的惯量；`finalize_inertial` 合并显式资产值与几何估计。如果只有 mass 显式给出，会按质量比例缩放几何估计惯量；显式惯量但缺少 COM 时，回退到 link 原点，而非自动选几何 COM。[组合实现][inertia]、[最终解析][inertia-resolve]

均匀缩放 s 且**密度不变**时，长度乘 s、质量乘 s³、惯量乘 s⁵。URDF 解析器正是这样缩放显式 mass/inertia；这不同于“保持质量，只把尺寸放大”的 s² 惯量缩放。不能把 `scale=0.001` 视为只改视觉尺寸。非均匀缩放不能直接套 s⁵，需重算几何和惯量。[缩放源码][scale]

检查惯量时至少看对称性、非负主惯量及量纲；普通有体积的动态刚体应有正质量、正主惯量，并满足主惯量三角关系。算法中的最小质量下限用于避免奇异数值，不会补回资产缺失的真实物理参数。`Rigid.rho` 可提供几何估计密度；显式惯量优先与 `recompute_inertia` 的作用需同时记录。[密度来源][material]、[解析与下限][inertia-resolve]、[重算选项][file-morph]

资产许可与数值建模分别验收：记录原始下载地址/提交、许可证、mesh 附件和修改；没有明确许可的第三方资产不放入教程仓库。本章仅使用原创 Box 片段，未引入外部资产。

## 4. 配置 q 与广义速度 v：维度、索引、frame

对关节系统可写 $M(q)\dot v+c(q,v)=\tau+J(q)^T\lambda$，这是刚体动力学记号，约束项在 E3 展开。q 在配置流形上，v 在其切空间中；一般有 $\dot q=N(q)v$，而不是总有 $\dot q=v$。M 的行列数由自由度数决定，不能拿 `n_qs` 直接分配质量矩阵。τ 的分量与对应 DOF 功率共轭：平移 DOF 用 N、旋转 DOF 用 N·m；混合关节向量没有一个统一的“力单位”。q 的四元数分量无量纲，也不是四个独立力矩通道。

| joint | `n_qs` | `n_dofs` | 配置与速度解释 |
|---|---:|---:|---|
| FIXED | 0 | 0 | 固定关系属于模型拓扑，不是“值为零的可控关节” |
| REVOLUTE | 1 | 1 | 角配置和轴上角速度 |
| PRISMATIC | 1 | 1 | 位移和轴上线速度 |
| SPHERICAL | 4 | 3 | 单位四元数和三维角速度 |
| FREE | 7 | 6 | 世界位置3 + `(w,x,y,z)`4；平移速度3 + 旋转速度3 |

该表直接对应 [MJCF 原生映射][mjcf]；实体维度由其 joints 求和。`joint.q_start/q_idx_local` 与 `joint.dof_start/dof_idx_local` 分别服务配置与 DOF，scene 级起点不可直接传给实体的 `*_idx_local`。多自由度关节的索引可为集合，按 `n_qs/n_dofs` 处理，不能假定 `dof_idx_local` 永远是单个整数。[索引属性][joint]

例如一个 free 根加两个 revolute joint，`n_qs=9`、`n_dofs=8`；第二个 revolute 的 q 槽与 v 槽相差 1。给四元数增加一个标量速度既破坏单位约束，也丢失三个旋转自由度的几何意义。

内部空间速度还拆成 `cd_ang` 与 `cd_vel`，并以树的 `root_COM` 为参考点；公开 link 速度通过角速度叉乘位移换到指定取样点。教程若写六维空间向量，应先声明排列和取样点，不能把 free joint 的六维 DOF 数组直接标成所有 link 的世界 twist。这里约定数学记号 twist 为 `(ω, v)`、功率配对 wrench 为 `(τ, f)`，满足 `P=τ·ω+f·v`；Genesis 内部是两个独立三维字段，外部数组需自行遵守接口约定。[字段换点][getters]、[刚体参考点接口][rigid-position]

`get_dofs_position()` 也不只是 `get_qpos()` 的缩短版本：FK 对 revolute/prismatic 写入 `qpos-qpos0`，对 free/spherical 将姿态转换成三角度形式。后者有姿态参数化的分支与奇异性，不能用来无损替代 qpos 快照；非零 reference 配置时两个标量 getter 也可能不同。[FK 字段赋值][fk]、[getter][getters]

### 4.1 应用 API 对照与所有权

| 操作 | 原生接口 | 效果与边界 |
|---|---|---|
| 查询配置 | `entity.get_qpos()` | 本实体配置；默认无 batch 时 `(n_qs,)` |
| 查询广义速度 | `entity.get_dofs_velocity()` | 本实体 DOF；默认无 batch 时 `(n_dofs,)` |
| 直接改配置 | `entity.set_qpos(q, zero_velocity=...)` | 改状态，不是施加力；`RigidEntity` 默认清零速度，`KinematicEntity` 默认保留速度 |
| 直接改 DOF 位置/速度 | `set_dofs_position`、`set_dofs_velocity` | 分别使用 DOF 索引，不能用 q 索引替代 |
| 设置驱动目标 | `control_dofs_position/velocity/force` | 改控制输入，经过后续步进才产生动力学响应；E2 详解 |
| 查询全场景基础状态 | `scene.get_state()` | 返回各 solver 的 SimState，未激活 solver 可为 None |

`RigidEntity` 覆盖了 `set_pos/set_quat/set_qpos/set_dofs_position`，将 `zero_velocity` 默认值设为 `True`；基类 `KinematicEntity` 则默认 `False`。要保留动力学刚体的速度，必须显式传 `zero_velocity=False`。即使清零速度，单独改配置仍不恢复控制输入、时间与求解器历史。[基类 setter][kinematic-setters]、[刚体覆盖实现][dynamic-setters]

上述刚体 `get_qpos/get_dofs_velocity/get_links_pos/get_links_quat` 路径通过 `qd_to_torch(..., copy=True)` 读取；修改返回 tensor 不会自动写回物理场。要重置配置，显式调用 setter。内部零拷贝数组不享有此接口保证，不应把直接写 `_solver` 私有 buffer 作为教程方案。[getter 实现][getters]、[刚体位置getter][rigid-position]

求解器内部常用 DOF/link 在前、batch 在后的存储；用户 getter 转成 batch 在前。`scene.build(n_envs=0)` 返回接口省略 batch 维，`n_envs=1` 仍保留长度1的 batch 维。`RigidSolverState` 查询类内部却总保留 `_B=max(1,n_envs)`：`qpos` 为 `(B,n_qs)`，`dofs_vel/acc` 为 `(B,n_dofs)`。不要因为实体 getter 是一维，就给 SimState 的字段去掉第0维。[build 约定][build]、[状态类][state-types]

`env_spacing` 只改变可视化排列，不改变 solver 内的真实环境坐标。批量布局、异构模型及模型参数是否按环境保存留给 E5，但本章的 shape 与 frame 规则应先固定。

## 5. 多物理状态不是刚体 qpos 的别名

令 B 为内部 batch 大小、P 为粒子数、V 为顶点数、E 为单元数。下面是**查询状态类实际携带的字段**，不是全部求解器内存或完整恢复能力声明。[状态定义][state-types]、[Tool 状态][tool-state]

| solver | 主要状态/shape | 物理含义和恢复边界 |
|---|---|---|
| Rigid | qpos `(B,n_qs)`；dofs_vel/acc `(B,n_dofs)`；links_pos/quat；friction_ratio | 广义坐标、导出姿态和部分动态参数；不含完整控制输入与求解历史 |
| Kinematic | qpos、dofs_vel、links_pos/quat | 仅运动学，不能以有 velocity 字段为由宣称参与动力学；该类注释称省略 velocity，但构造器实际分配 dofs_vel |
| MPM | pos/vel `(B,P,3)`；C/F `(B,P,3,3)`；Jp/active `(B,P)` | C 是局部仿射速度场、F 是形变梯度，Jp 属于材料历史；只保存位置会丢失下一步所需信息 |
| SPH | pos/vel `(B,P,3)`、active `(B,P)` | 粒子运动和活动标记；密度/邻居等算法量另有内部生命周期 |
| PBD | pos/vel `(B,P,3)`、free `(B,P)` | 位置约束粒子；free 是自由/固定标记，不是刚体 free joint |
| FEM | pos/vel `(B,V,3)`、active `(B,E)` | 顶点状态与单元活动标记，不能把 active 当成逐顶点 mask |
| Tool | 每实体 pos/quat/vel/ang，带 B 维 | 按实体组成的 ToolSolverState，无刚体 joint 向量等价关系 |
| SF | `get_state/set_state` 为 `pass` | 不能承诺经 SimState 完整保存/恢复；此版本还显式拒绝 SF batch |

F 的定义为 $F=\partial x/\partial X$，无量纲；C 对局部速度近似 $v(x)\approx v_p+C_p(x-x_p)$ 中的线性项，量纲 s⁻¹。这解释为何两个粒子云即使位置相同，也可能有不同材料状态与后续演化。具体本构关系和每种离散化由 E6 展开，不把这张状态表当成全部多物理算法已完成。

**按环境 reset 必须逐 solver 核查。** `Scene.reset(envs_idx=...)` 接口存在，不表示所有 solver 都正确隔离所选环境：该版本 MPM/SPH/PBD/FEM 的 `set_state` 接收参数却没有传给写入 kernel，kernel 遍历全部 B；Tool 也未把 envs_idx 传给实体 setter。Rigid 分支则有 mask/index 写入。混合场景不能沿用“只重置结束环境”的刚体假设。[MPM][mpm-reset]、[SPH][sph-reset]、[PBD][pbd-reset]、[FEM][fem-reset]、[Tool][tool-reset]、[Rigid][restore]、[SF][sf-reset]、[SF batch 检查][rates]

这是固定源码暴露的限制，尚无本章运行复现。应用端保守地全场景 reset，或在后续正式验证中逐 solver 验证隔离；不要在本章用隐藏 wrapper 掩盖不一致。

## 6. reset、基础状态和 checkpoint 的不同承诺

`scene.get_state()` 为各 solver 构造/查询状态，刚体捕获前会调用 `update_forward_pos()`，避免 qpos 与 links pose 相差一个积分阶段。查询对象保留供梯度收集的关系，不能视作永久只读、与所有缓存独立的纯 NumPy 文件。保存日志时从所需 tensor 明确复制，并记录引擎/模型/索引与时间。[捕获实现][capture]

`scene.reset()` 恢复已登记的初态；`scene.reset(state)` 既恢复这个 SimState，**又将其登记为以后无参数 reset 的初态**。因此“临时回滚”之后再 reset 不会自动回到最初 build 状态。需要最初状态时自行保留引用且不修改其内容，或重新构建模型。reset 会清零选定环境的步数、重启耦合器/梯度带/传感器，清除可视化缓存并重启 emitters；它并不恢复任意外部 Python 控制器、随机数生成器或用户日志的时间。[Scene reset][scene-reset]、[Simulator reset][sim-reset]

对于刚体，`RigidSolver.set_state` 还清理碰撞/约束状态、清零外施力、把控制模式设为 FORCE 且控制力归零，并处理休眠状态。这说明只用 SimState 回滚，不等于从原驱动命令与 warm start 精确续跑；恢复后要明确重设控制输入。[状态写回][restore]

| 需要 | 该版本提供的入口 | 限制 |
|---|---|---|
| 将基础物理状态设为新初态 | `scene.reset(scene.get_state())` | 时间归零；不保持完整输入/求解历史；改变登记初态 |
| 进程内完整 scene checkpoint | `scene.__getstate__()` / `__setstate__()` | 属于底层序列化契约；相同描述摘要、环境布局、solver 集合和数组结构；数组复制，描述按引用携带 |
| 文件 checkpoint | `scene.save_checkpoint(path)`、`gs.Scene.load_checkpoint(path)` | `.gstraj` 格式；加载创建/构建 scene，并 seek 到记录末帧；导出与 solver 能力有约束 |

Checkpoint 恢复会带回每环境步数，与基础 reset 不同。但梯度 tape、传感器、recorders 等周边仍按重启处理；不能称为整个训练程序的 bitwise checkpoint。IPC coupler 会明确拒绝此 checkpoint；基础 Solver.data 默认抛“不支持”，MPM/SPH/PBD/FEM/SF/Tool 在本章读取文件中没有覆盖该接口，不能因 Rigid 可用就承诺这些 solver 可序列化。文件保存/加载更不是跨 Genesis 版本或跨硬件确定性保证。[Scene checkpoint][checkpoint]、[Simulator 限制][sim-reset]、[Solver 基类][solver-checkpoint]

## 7. 一个 step 究竟代表多久

### 7.1 三种“次数”必须分开

设 Scene 的外层时间步为 $\Delta t$，子步数 N，则每子步 $h=\Delta t/N$。`SimOptions.dt` 默认0.01秒、`substeps` 默认1。一次实际推进的 `scene.step()` 完成 N 次物理子步；constraint solver iterations 是一个子步内部解代数问题的次数，增加它不会让物理时钟额外前进。[时间配置][sim-options]

该版本可显式设置 solver 的 `dt`，但不是任意多速率系统：该间隔必须整数分割 Scene dt，各主动请求间隔的 solver 必须得到同一 N；若显式 `SimOptions.substeps` 冲突，build 抛错。最终所有活动积分 solver 使用协商后的同一子步间隔。在 `requires_grad=True` 时，不允许 solver dt 推导出与已分配梯度窗口不同的 N。[build 协商][rates]

纸上示例（未执行）：`SimOptions(dt=0.01, substeps=4)` 意味 h=0.0025秒；求解器迭代100次仍只推进0.01秒。若显式 solver dt=0.003，它不能整数划分0.01；若 dt=0.005 而显式 substeps=4，也冲突。不能默认为框架会自行插值或异步调度。

`scene.get_time()` 对应每环境整数步数乘 dt；批量部分 reset 后各环境时钟可以不同。内部 `_cur_substep_global` 还服务于梯度带/局部窗口，reset 会重启它，不能拿它替代所有环境的 episode 时间。`SimState.s_global` 也不是完整的逐环境时钟记录。[时钟实现][time]、[reset][sim-reset]

### 7.2 积分器与 solver 各做什么

在无接触的简单标量系统里，显式 Euler 使用旧速度更新位置；半隐式 Euler 先更新速度再用新速度更新位置：

$$
v_{k+1}=v_k+h a_k,\qquad q_{k+1}=q_k+h v_{k+1}.
$$

此式仅直接适用于欧氏配置，不可把四元数 q 当成标量数组套用。Genesis `func_integrate` 的通常路径先计算 `vel_next`，自由平移与标量 joint 使用它推进；旋转取局部旋转向量 `h*angular_velocity` 转成四元数，右乘原姿态并归一化。[积分代码][integrate]、[乘法定义][quat-product]

`RigidOptions.integrator` 支持 Euler、implicitfast、approximate_implicitfast（默认）；名字不能单独描述所有执行路径。速度隐式方法的一个教学模型是线性阻尼 $M\dot v=f-Dv$：若 M、D 在当前步冻结，隐式处理阻尼需要解 $(M+hD)v_{k+1}=Mv_k+hf$。实际引擎还有执行器导数、约束与模式分支，不能宣称等于完整 Backward Euler。此版本 damping correction 和兼容分支见 [源码][damping]，详细推导在 E3。

尤其对满足条件的独立 free body，非 Euler、非可微的路径会使用隐式中点更新覆盖部分 `vel_next/acc`，位置积分后再恢复真实下一步速度；可微路径排除了这段无 adjoint 的迭代。因此同一 integrator 枚举并不意味着所有物体、梯度模式都走完全相同的公式。[分支与更新顺序][integrate]、[选项说明][integrator-options]

减小 h 可改善时间离散误差，但不修复错误惯量、轴系、接触参数或未收敛线性/非线性求解；FP64 也不替代模型验证。对振子 $\ddot x=-\omega^2x$，hω 是无量纲步长尺度，刚度越大，同一 h 的离散行为越敏感；这里不给所有系统统一“稳定步长”或精度排名。

### 7.3 采样顺序与控制频率

固定版本的外层顺序可用下面的源码导航表示，不是新框架：

```text
Scene.step
  pre_step_callbacks → 任一返回 True 可暂停本次推进
  recorder 读取步前状态及已写入的输入
  Simulator.step
    环境步数 +1
    N 次子步（刚体快速路径或多求解器耦合路径）
    清零刚体 external force
    sensors.step
  可选 visualizer 更新
  camera recording 更新（仅实际推进时）
```

多求解器子步还依次经过 coupler.preprocess、solver pre-coupling、couple、post-coupling；刚体快速路径受 coupler 与可微条件限制。[外层源码][scene-step]、[内层源码][sim-step]

由此得到四条接口约定：

1. 步前 getter 读取 $t_k$ 的状态，写入控制后，本次推进才产生 $t_{k+1}$；recorders 与步后手工日志的时点不同，元数据必须标明。
2. `update_visualizer=False` 不关闭物理推进；viewer 的墙钟刷新率不是物理频率。callback 暂停时调用 step 也可能不推进。
3. 默认 setter 更新 FK；使用 `skip_forward=True` 或直接访问内部 buffers 后，派生的 links pose/velocity 可能未刷新。需要一致基础快照时用 `scene.get_state()` 的刚体刷新路径，不能把私有数组缓存当公共观测。
4. 每 m 个外层 step 更新一次控制，其名义控制周期是 mΔt；仅增大 substeps 不会自动提高 Python 控制器调用次数。传感器在物理步骤后更新，其内部采样规则由 E4 展开。

## 8. 最小阅读片段与排错

[examples/state_layout.py](../examples/state_layout.py) 只演示原生对象、q/v shape、复制、reset 的调用关系；默认无 viewer，只有原创 Box，没有接触任务、控制评测或训练。**已做 AST 语法检查，未 import/build/step 运行；输出数字未验收。** 安装入口见 [installation.md](installation.md)。

| 症状 | 先核查 | 原因 |
|---|---|---|
| 盒子旋转角很小/很大 | Morph.euler 度 vs joint rad | 两类 API 单位不同 |
| get_pos 与 qpos 前3项不等 | relative、offset、align | 作者原点与求解原点不同 |
| free body 配置和速度无法拼同一长度 | n_qs=7、n_dofs=6 | 配置流形与切空间不同 |
| 改 getter 返回 tensor 后实体不动 | getter copy=True；是否调用 setter | 查询不是共享可写状态 |
| reset 后控制器失效/时间变零 | 是否重设输入；是否误用 SimState 当 checkpoint | reset 有明确副作用 |
| 某个环境结束却其他材料也被重置 | 各 solver 是否消费 envs_idx | 多物理 reset 隔离尚不统一 |
| 渲染已变化但碰撞不合预期 | visual/collision、凸化和惯量来源 | 外观不定义完整物理模型 |
| 改 solver dt 后 build 失败 | 整数分割、各 solver 的 N、显式 substeps | 此版本不支持任意独立求解速率 |

## 9. 阅读练习（含答案，不要求运行）

1. 一个自由根加三个 revolute joint 的机器人，q/v 各多少维？第二个关节能用同一个 q 与 DOF 索引吗？
   **答案：** 10与9维。自由根占7/6，故随后关节的两套索引相差1；读取 joint 的实际 local index，不能复用数组槽位。
2. 作者原点在世界 `(0,0,0)`，绕 Z 旋转90°，offset_pos=`(1,0,0)` 且无 align。内部原点在哪里？默认 get_pos 是什么？
   **答案：** 内部原点 `(0,1,0)`；默认 getter 恢复作者原点 `(0,0,0)`。offset 不是世界 X 向平移。
3. 定密度资产 scale=2，质量与惯量倍率分别是什么？若人为固定总质量呢？
   **答案：** 定密度8和32；固定质量时惯量为4。URDF 导入代码采用前一种，不能只按长度倍率猜质量。
4. 为什么 `q=get_qpos(); q[0]=...` 不够？为何 set_qpos 后仍可能保留速度？
   **答案：** getter 返回复制的 tensor，要显式 setter。`RigidEntity.set_qpos` 默认 `zero_velocity=True`，显式设为 `False` 才保留速度；`KinematicEntity` 默认 `False`。两者的位置重置都不是完整状态重置。
5. `snapshot=scene.get_state(); scene.reset(snapshot); scene.reset()` 最后恢复什么？时间是否保留？
   **答案：** 第二次仍恢复 snapshot，因它已登记为新初态；基础 reset 清零环境步数，不能用 snapshot 的 s_global 代替 checkpoint 时钟。
6. 为什么不对混合 Rigid+MPM 场景直接承诺 `reset(envs_idx=[0])` 隔离？
   **答案：** 固定版本 Rigid 消费所选索引，而 MPM 的写状态 kernel 遍历所有环境。必须分别验证，不能由 Scene 的签名推断能力。
7. Scene dt=0.02、substeps=5，控制每3 step更新，solver迭代50次。h 与控制周期各是多少？
   **答案：** 0.004秒、0.06秒。求解迭代不增加仿真时长；若 callback 暂停，要按实际推进计数。
8. 同一刚体的 get_vel(relative=False) 与默认结果相差什么？
   **答案：** 两取样点间的 $\omega_W\times d$，不能简单用旋转矩阵把一个当另一个。还应区分世界角速度 getter 与局部自由关节角速度。
9. 为什么“Genesis 全部 solver 支持场景快照”不由 get_state 接口证明？
   **答案：** 基础状态字段不同；SF 函数为空，完整 checkpoint 需要 Solver.data，IPC 明确拒绝，reset 也会清理输入/历史。接口名字不是能力证据。

完成阅读后转 [E2 驱动与机器人任务](roadmap.md)。E3 会从本章 q/v、惯量和 h 接上接触与求解，E6 补各多物理 solver 的方程与扩展限制。本章没有新增实验结论，所有性能或物理资格仍需以后引用 DexLab 的对应版本和工况。

[morph]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/morphs.py#L68-L169
[file-morph]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/morphs.py#L500-L605
[urdf]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/urdf.py#L157-L221
[scale]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/urdf.py#L416-L429
[mjcf]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/mjcf.py#L315-L353
[mjcf-limit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/mjcf.py#L375-L442
[inertia]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/inertial.py#L88-L127
[inertia-resolve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/inertial.py#L194-L228
[material]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/rigid.py#L1-L33
[dispatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L124-L157
[build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L831-L889
[poses]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L724-L805
[states-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L1003-L1126
[joint]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_joint.py#L160-L296
[fk]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_kinematics.py#L392-L435
[getters]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L1291-L1400
[capture]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1765-L1794
[restore]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1796-L1895
[state-types]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/states/solvers.py#L69-L326
[tool-state]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/states/entities.py#L5-L28
[mpm-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py#L824-L880
[sph-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py#L775-L801
[pbd-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py#L821-L845
[fem-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py#L1101-L1111
[sf-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sf_solver.py#L280-L297
[tool-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/tool_solver.py#L72-L85
[scene-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L947-L999
[sim-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L246-L308
[checkpoint]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1672-L1824
[solver-checkpoint]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/base_solver.py#L363-L389
[rates]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L164-L235
[time]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L596-L613
[sim-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L19-L78
[integrator-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L467-L502
[integrate]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L2063-L2185
[damping]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L2267-L2305
[quat-product]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/geom.py#L423-L431
[scene-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1060-L1098
[sim-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L414
[precision]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py#L60-L79
[precision-dtype]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py#L150-L163

[rigid-position]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2881-L2978

[kinematic-setters]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L939-L1064
[dynamic-setters]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L2467-L2590
