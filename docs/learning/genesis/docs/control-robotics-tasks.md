# E2 · 驱动、机器人与任务接口

本章解决一个具体问题：给机械臂一个末端目标，如何分清“求一个姿态解”“写控制目标”“产生关节驱动力”“实际到达目标”。沿 **joint 名字 → 配置/DOF 索引 → FK/IK → 控制缓冲 → 限幅驱动 → 步后观测 → 任务转移** 阅读，覆盖 A3、A5、A7。

先修 [E1](modeling-state-time.md)，知道 q 与 v 不同维、世界/作者/求解 frame 不同，以及外层 dt、子步 h 和 reset 的意义。阅读固定于 Genesis 1.4.3 提交 `216a708e06124595521a9d36a51fae5393fd4ff8`；Python 接口、Rigid/Kinematic solver、资产解析器及物理步进分别说明。公式按 SI；机器人演示限定固定基座、标量 revolute/prismatic 关节，不把所有多物理材料当成有 `control_dofs_*`。

**本章是源码课程：源文件身份、原生调用路径、Python语法和原创URDF结构已检查；未 import/build/step 运行引擎、未验收抓取效果。** 源码发现不是运行复现。实验仍复用 DexLab，见 [验收记录](e2-acceptance.md)。

## 1. 四类操作的效果不相同

| 意图 | 原生入口 | 本次调用的效果 |
|---|---|---|
| 放置/重置机器人 | `RigidEntity.set_qpos`、`set_dofs_position` | 直接改状态；Rigid版本默认 `zero_velocity=True`，并非连续驱动 |
| 发出驱动命令 | `control_dofs_force/velocity/position/position_velocity` | 写所选 DOF 的模式与目标，后续物理步才消费 |
| 求末端配置 | `inverse_kinematics`、`inverse_kinematics_multilink` | 在独立 scratch 上求配置，返回候选 q，不推动真实机器人 |
| 生成几何路径 | `plan_path` | 采样/碰撞检查得到 q waypoints；还需时间安排、控制执行和观测 |

`RigidEntity` 覆盖 `KinematicEntity` 的 setter 默认值：基类的 `zero_velocity=False` 不能直接当成动态机器人的契约。Rigid 的 setter 还检查 IPC `external_articulation`；`control_dofs_*` 检查 IPC `ipc_only` 并拒绝该类型。看签名后应继续追派生类、solver和kernel，不能只摘基类注释。[Rigid setter][rigid-setter]、[控制入口][control-api]

力控制也不是调用后立即获得接触力。`control_dofs_force` 将模式改为 FORCE；velocity 写 VELOCITY；position及position_velocity写 POSITION。`control_dofs_position` 会把选中DOF的目标速度清零，而 `control_dofs_position_velocity` 同时写两个目标。对不重叠的臂/指关节可混用模式；对同一DOF后写入的模式生效，不会自动将两次调用相加。[solver写入][control-write]、[kernel写入][control-kernel]

控制目标保存在缓冲中，通常持续到后续命令或reset改变它；每步末清零的 `external_force` 属于另一类施力字段。不要把“外力每步清除”误读成必须每子步重发所有DOF目标。reset后的模式与驱动力需重新确认，E1的基础状态恢复将它们设为FORCE/零力。[步尾清理][sim-step]、[reset写回][reset]

## 2. 名字、资产和关节索引构成控制契约

### 2.1 先建立映射，再构造数组

导入后用 `robot.get_joint(name)`、`get_link(name)` 查询实际对象；不存在的名字会报错并列出可用名字。每个joint有两套**列表**属性：`qs_idx_local` 索引实体q，`dofs_idx_local` 索引实体DOF。旧的单数 `q_idx_local/dof_idx_local` 仍经过弃用回调，返回值还可能是int/list/None；新教程使用复数属性，并检查任务期望的 `n_qs/n_dofs`。[名字查询][names]、[新索引][indices]、[旧属性兼容][old-indices]

自由根占7个q槽但只有6个DOF；球关节4/3；固定joint是空列表。不能将“第三个执行器”“XML第三个joint”“q[2]”“dof[2]”视为同一东西。URDF固定link默认合并；TCP虚拟link若要保留，用 `links_to_keep` 或明确关闭merge。引用已解析的link对象后，还应记录模型文件、导入选项和joint名顺序。[导入规则][import-options]

执行器子集也是模型契约。`control_dofs_force`的内核按所选DOF写输入，实际FORCE分支没有“这个joint在资产里是否配了真实电机”的判断。对浮动基座直接控制全部DOF，可能给基座添加任务本来没有的驱动；应按明确的驱动joint名字构造子集，而非默认 `range(robot.n_dofs)`。[写入内核][control-kernel]、[FORCE分支][control-force]

例如本文 [two_joint_arm.urdf](../examples/assets/two_joint_arm.urdf) 有两个标量转动joint `shoulder`、`elbow`，每个各占一个q/DOF槽，初始参考角为0；本例才可用相同顺序的两角数组驱动。通用机器人仍应分别收集两个索引列表。

### 2.2 qpos解不是任意情况下都能直接当位置目标

FK把标量关节的 `dofs.pos` 定义为 `qpos-qpos0`；位置控制对比的是这个DOF位置。若资产带非零参考值，IK返回q后要按命名映射取对应标量q，再减去相应参考q，才能形成PD目标。对本章固定拓扑的标量关节，可从 `robot.init_qpos`/joint初始配置取得建模参考；若运行中修改模型参考或重建，必须重新核实映射，不能永久缓存旧数组。[初始q接口][initial-q]、[FK赋值][fk-dof]

free的q里包含四元数，而位置控制的六维目标中旋转部分使用三角度；球关节也不能用“删掉四元数最后一个分量”进行转换。本章片段先限制全是标量joint，避免把成立于固定基座示例的 `control_dofs_position(ik_result)` 推广成万能方法。

### 2.3 导入的执行器和限额从哪里来

| 来源 | 该版本解析内容 | 不能据此推断的能力 |
|---|---|---|
| URDF `limit.effort` | 生成对称DOF力/力矩范围；未给时可为无穷 | 不等于设置了运行速度限幅或电机电流模型 |
| URDF `dynamics` | damping、friction进入被动/摩擦参数 | 不等于PD的kv；二者可能同时作用 |
| URDF `safety_controller` | k_position/k_velocity可覆盖默认控制增益 | 不是完整硬件安全控制器 |
| URDF `mimic` | 解析为joint equality，保留比例/偏移和尺寸缩放 | 不等于IK或规划自动消去从动关节 |
| MJCF actuator | fixed gain、none/affine bias、传动与范围映射 | internal dynamics、非支持gain/bias/tendon等有警告或近似 |

MJCF解析器按原文件给出的范围组合约束；motor的ctrlrange经gear、actuator forcerange、joint actuatorfrcrange进入DOF范围。组合发生在导入阶段，不意味着 Genesis `control_dofs_force` 接收的是 MuJoCo 原始ctrl：Genesis FORCE分支直接使用传入的广义力/力矩再限幅。不要重复乘gear，或忽略解析警告。[URDF字段][urdf]、[MJCF映射][mjcf]、[实际驱动分支][control-force]

## 3. 从位置目标到驱动力：公式、限幅与单位

### 3.1 标量DOF的实际公式

令x=`dofs.pos`，v=`dofs.vel`，uₚ/uᵥ为位置/速度目标，g为`act_gain`，b₀/b₁/b₂为`act_bias`。非free旋转的POSITION分支可展开为：

$$
f_{raw}=g u_p+b_0+b_1x+b_2(v-u_v).
$$

源码写成 `g*(u_p-x) + b0 + (g+b1)*x + b2*(v-u_v)`，在PD可化简时避免大数相消。使用 `set_dofs_kp(kp)` 后g=kp、b₀=0、b₁=−kp；`set_dofs_kv(kv)`设置b₂=−kv，因此：

$$
f_{raw}=k_p(u_p-x)+k_v(u_v-v),\qquad
f_{applied}=\operatorname{clamp}(f_{raw},f_{min},f_{max}).
$$

VELOCITY分支是 `kv*(u_v-v)`，不使用位置误差；FORCE分支是传入力，再受相同range限制。`set_dofs_act_gain/bias` 可改变一般仿射执行器；此时 `get_dofs_kp/kv` 会检查是否满足PD可化简条件，不满足就报错，不能从“有kp接口”推断所有导入驱动器都是PD。再次 `set_dofs_kp` 会改gain和两个bias项，是模型语义修改。[驱动力][control-force]、[增益写入][gain-write]、[可化简检查][gain-read]

| DOF | 位置/速度 | f | kp | kv |
|---|---|---|---|---|
| revolute | rad、rad/s | N·m | N·m/rad | N·m·s/rad |
| prismatic | m、m/s | N | N/m | N·s/m |

数组混有转动和平移时，不应对全数组使用同一个“力单位”。这些是一般控制公式的量纲说明，具体gain值还依赖资产惯量、时间步、耦合与接触；原生示例中的数值不具有跨机器人的调参结论。

### 3.2 三种限额不是一回事

1. `set_dofs_force_range(lower, upper)` 限制驱动广义力/力矩，FORCE模式也会被裁剪。上下界可以不对称，应逐DOF记录并读回；不能默认±同一标量。
2. `set_dofs_limit` 与 `RigidOptions.enable_joint_limit` 对应位置约束。控制目标写入路径不等于自动裁剪目标到位置范围；动力学限位通过约束求解响应，不能解释成状态数组永不越界的硬赋值。
3. `inverse_kinematics(..., respect_joint_limit=True)` 控制的是候选解更新/重采样的限位行为；`plan_path`也有目标范围检查。它们不为轨迹自动安排速度、加速度或力矩约束。[控制写入][control-write]、[限位约束装配][limits]、[IK更新][ik-increment]

纸上算例：某revolute轴kp=20 N·m/rad、目标误差0.4rad、kv=2 N·m·s/rad、速度0.5rad/s、目标速度0。raw=8−1=7 N·m；若range=[−3,3]，驱动为3 N·m。增加kp只会保持饱和，不证明末端已到达，更不等于夹爪对物体施加3N法向力。

对于孤立标量二阶模型 `I*ẍ=kp*(u−x)−kv*ẋ`，自然频率约为 `sqrt(kp/I)`，阻尼比约为 `kv/(2*sqrt(kp*I))`。这是惯量常数、无耦合/接触/饱和且连续时间的近似。实际Genesis有关节耦合、隐式处理与离散h，不能直接把该公式当成所有关节临界阻尼配置；本章不运行增益搜索。

### 3.3 控制读数不是末端力传感器

| 读数 | 实际来源 | 应怎样解读 |
|---|---|---|
| `get_dofs_control_force()` | accessor kernel按**当前**模式、目标、状态重新计算并限幅 | 是当前控制请求对应的重算值，不是缓存的上一次子步施力；步后查询可能已经换了状态 |
| `get_dofs_force()` | 读取 `dyn_state.dofs.force` | 动力学路径先组装passive−bias+applied，约束求解后加约束广义力；包括多个来源，不能当电机输出或接触法向力 |
| `get_dofs_acc()` | 读取保存的DOF加速度 | 按积分/求解阶段解释，不能用control_force简单除某个质量得到全部关节加速度 |

[重算getter][control-getter]、[平滑力组装][force-assembly]、[约束写回][constraint-force]、[公开读取的solver实现][force-read]。休眠DOF在约束写回可保留此前awake的force，所以必须同时记录采样阶段和休眠设置。

一个具体边界：free根旋转的**步进**POSITION分支把三角度目标转成四元数误差/旋转向量，重算getter却按标量仿射公式计算。故不能承诺这类关节的 `get_dofs_control_force()` 与步进实际 `qf_applied` 一致。本章用标量关节解释控制读数，E3将继续分析力观测。[步进特例][control-force]、[getter分支][control-getter]

## 4. 批量目标：环境维和模型参数维分开

设本次选中E个环境、D个DOF。推荐显式传 `(E,D)` 的目标或 `(D,)` 的共享目标；一维D数组会按所选环境广播。`envs_idx=[3,1]` 时第0行对应环境3、第1行对应环境1；`dofs_idx_local=[5,2]` 时列顺序是DOF5、2。两组索引表示环境×DOF的矩形选择，而不是逐对配对。对特殊shape不要依赖猜测性broadcast，明确保留两个维度。[输入整形][shape]、[广播][broadcast]、[写入][assign]

`scene.build(n_envs=0)` 与 `n_envs=1` 的返回维度差异见E1。动态控制缓冲按环境保存，不代表kp/kv/range也按环境保存：`RigidOptions.batch_dofs_info=False` 是默认值，模型参数共享；要给不同环境不同增益/限额，应在build前设True。getter对共享参数携带envs_idx会报错，而部分setter路径仅按共享DOF写；不要把envs_idx当成不存在的模型参数隔离。[选项][options]、[默认值][options-default]、[模型参数写入][gain-write]、[getter限制][gain-read]

同一步可先控制臂，再控制手指，只要索引互斥。可微目标记录的key也包含方法、DOF子集与环境子集，避免不同子集互相覆盖；这只证明该记录路径的设计，不证明任意材料、IK、规划或Python任务状态机均可微。[tracked包装][diff-track]

下面两种方式不能混为一谈：

```text
dynamic target: 每环境有自己的 ctrl_pos/ctrl_vel/ctrl_mode
model parameter: batch_dofs_info=False → 所有环境共享 gain/bias/range
```

## 5. FK、Jacobian和TCP：位置正确还要参考点正确

对固定基座串联标量关节，FK组合从根到link的变换 `T_WL(q)`。给link局部点r（例如TCP），其世界位置为 `p_WTCP=p_WL+R_WL*r`。`robot.get_links_pos/quat(relative=False)` 读当前求解link frame；`get_jacobian(link, local_point=r)` 对这个局部点求导；IK的 `local_point` 也作用于该link局部frame。若资产有offset/align，不能拿E1的作者frame默认getter坐标未经转换就当IK目标。[Jacobian API][jac-api]、[IK frame说明][ik-api]

此版本没有 `robot.forward_kinematics(q)` 这个实体便捷接口。原生solver提供 `robot.solver.forward_kinematics_query(robot, q_candidate, envs_idx=...)`，返回该实体的世界link位置/姿态，q最后一维是n_qs。实现临时写入q、FK、收集结果，再恢复原q并重做FK；它不推进时间，但不是与live状态完全不相干的纯函数，不能同时在另一线程step或改场景。[查询入口][fk-query]、[暂存恢复实现][fk-query-kernel]

`get_jacobian`读取当前link/anchor缓冲。若刚改了状态并使用`skip_forward=True`，先恢复一致的FK状态再查询；刚体 `scene.get_state()` 的刷新语义见E1，不把旧缓存上的J与新q混合。

对标量revolute轴，世界轴a、joint anchor c和TCP p给出Jacobian一列：

$$
J_j=\begin{bmatrix}a\times(p-c)\\a\end{bmatrix};
\qquad
\text{prismatic: }J_j=\begin{bmatrix}a\\0\end{bmatrix}.
$$

**Genesis该接口行顺序为线速度3行在前、角速度3行在后**，列为本实体DOF，shape为`(6,n_dofs)`或`(B,6,n_dofs)`。这与E1自选数学空间向量记号 `(ω,v)` 不同；不能将两者直接拼接。对于这里的标量joint，`[v_TCP;ω]=J*v_dof`。[列装配][jac-kernel]

不要把上式无条件外推：FREE旋转列使用世界轴增量，而动力学free角速度是局部轴量；IK更新也用左乘世界增量。若要与raw自由关节速度相乘，需要先核对并换系。SPHERICAL在该Jacobian函数没有专门分支，scratch积分也没有四元数球关节专用更新；本章不宣称球关节IK/Jacobian已正确支持。多joint-per-link、特殊关节组合也应逐执行分支审查，普通URDF示例不能证明它们。[Jacobian分支][jac-kernel]、[IK增量][ik-increment]

## 6. IK返回候选，不返回“任务完成”

### 6.1 原生调用契约，以执行语句为准

| 参数/返回 | 固定版本真实语义 |
|---|---|
| `link`、`pos`、`quat` | link对象；目标世界位置m、世界姿态wxyz；只给pos即不要求姿态 |
| `local_point` | link局部TCP点；默认原点；不是世界坐标 |
| `init_qpos` | 当前q或用户初值；实际广播为`(E,n_qs)`，不是注释里的n_dofs |
| `dofs_idx_local` | 本次可优化的实体DOF子集；返回仍覆盖实体全部n_qs |
| `envs_idx` | 求解环境子集；目标可共享或逐选中环境提供 |
| `return_error=True` | 单目标返回`q,error[...,6]`；多目标返回`q,error[...,n_targets,6]` |
| `pos_tol`、`rot_tol` | 签名默认5e−4m与5e−3rad；函数参数说明中的1e−4未同步 |
| `max_samples`、`max_solver_iters` | 最多重采样次数与每次迭代预算，默认50和20；不是物理步数 |
| `damping`、`max_step_size` | DLS正则0.01、每DOF增量裁剪0.5；数值参数，不是关节阻尼和秒 |
| `pos_mask`、`rot_mask` | 位置分量屏蔽；旋转mask可选0/1/3轴，2轴会报错；单轴内部取补mask |

实际n_qs广播、mask校验和返回截取见 [实体实现][ik-sanitize]；默认值见 [签名][ik-api]；solver将qpos_best按n_qs截取见 [返回路径][ik-solver]。不要从过时Returns注释复制shape。

`inverse_kinematics_multilink` 接收links和每link的poss/quats/local_points列表；空poss表示全不约束位置，空quats表示全不约束姿态。目标数受 `IK_max_targets` 限制，默认6，需build前配置；各目标并非独立求解，而是共享同一组关节自由度。[列表与mask][ik-sanitize]、[目标数限制][ik-solver]

### 6.2 从误差到候选配置

对标量机械臂，位置误差 `e_p=p_target−p_TCP`，姿态误差为目标相对当前的旋转向量，按mask保留要求的分量。DLS在线性化 `e≈JΔq` 下求：

$$
\Delta q=J^T(JJ^T+\lambda^2 I)^{-1}e.
$$

源码按多目标堆叠J和误差，加入`damping**2`对角，再求解并逐DOF裁剪增量；之后更新scratch配置，重新做FK。λ减小不保证更准确：奇异位形、不可达目标和离散迭代预算仍影响结果。位置m与旋转rad堆叠包含量纲/尺度选择，本接口没有自动保证物理最优权重；不要把数值最小二乘误差称为能量或物理残差。[误差构造][ik-error]、[DLS实现][ik-dls]

在标准约束轴mask下，检查每目标位置误差范数≤pos_tol、旋转误差范数≤rot_tol。被mask掉的分量为零，故小residual只说明**所求分量**满足，未约束的yaw或高度不能被算进成功。`return_error`返回的是这些残差分量，不是百分比准确率。

求解在scratch中完成，不改变live q；失败时返回按源码规则保存的候选，而不是自动抛“无解”异常。必须检查residual，再决定是否使用。多目标失败候选更新规则要求各目标的位置/旋转误差均不劣于已存值，不是简单所有项平方和最小；不宜概括成“全局最优解”。有限限位的revolute/prismatic可在失败后重采样，seed默认内部0；固定seed不等于跨版本/设备的完整仿真确定性。[候选选择与重采样][ik-result]

### 6.3 能力边界

- IK只求指定frame/关节的几何关系，执行链没有接触、碰撞或mimic/equality残差，不能据此保证无碰撞、满足闭链或可承受负载。
- `respect_joint_limit=True` 约束IK更新，不保证任何初值、所有关节类型和失败返回均满足任务要求；先核对支持的joint，再验残差和限位。
- IK可改变候选q不等于机器人已经运动。接受候选后，对标量joint生成PD目标或路径，按时序step并观测。
- 不用 `set_qpos(ik_result)` 充当路径执行。它绕过驱动响应并默认清速度，只适合明确的初始化/重置用途。

## 7. 原生路径规划：路径、有效标记与执行时钟

`RigidEntity.plan_path` 选择原生 `RRT` 或 `RRTConnect`；默认RRTConnect、max_nodes=2000、resolution=0.05、max_retry=1、num_waypoints=300。参数说明仍写100个waypoint，实际按签名300。路径shape无batch时`(N,n_qs)`，有batch时`(N,E,n_qs)`。设置 `return_valid_mask=True` 返回的布尔值是 **True=有效**，尽管Returns注释保留`is_invalid`名称，包装层实际取了反。[调用与返回][plan-api]

规划器构造时直接拒绝FREE和SPHERICAL；这是比一般IK更窄的关节集合。`ignore_joint_limit`旧参数仅警告，不能据此取消限位。路径是关节空间采样点，resolution混合角/长坐标时没有自动变成统一笛卡尔距离；waypoint数也不是运行秒数。[构造限制][plan-limits]、[公开参数][plan-api]

碰撞检查有重要范围：规划先收集起点和终点已有接触geom pair并排除它们，检查还忽略低于穿透阈值的接触。因而即使 `ignore_collision=False`，返回valid也不能被概括成“所有碰撞均被排除”。`with_entity`与`ee_link_name`只为规划时带着单link物体检查相对姿态，不能证明物体真实被夹持、焊接或抓稳。[排除集合][plan-exclude]、[碰撞检查][plan-collision]、[附带物体参数][plan-api]

规划在live状态上试探并在正常返回路径恢复机器人q；这会调用状态setter和碰撞检测，不能把它当成与实时步进可并发的纯查询。完整求解缓存/传感器历史恢复不由“恢复q”证明。应在暂停推进的时点规划，检查valid mask和路径后，再发控制；异常返回后检查场景状态而不是盲目继续。[规划恢复][plan-restore]

若每个waypoint恰好执行一个外层step，N次命令推进NΔt；若每个保持m步，则NmΔt。但这只描述命令时钟，不能承诺机器人在这些时间内准确到达点，也没有自动满足速度/加速度/jerk或力矩约束。轨迹跟踪应使用期望位置/速度随时间的定义，并以实际步后误差判定到达；路径和轨迹是不同交付物。

## 8. 任务接口：接近、闭合、保持、释放

以下是**任务逻辑设计**，不是新抓取实验；阈值、保持时间和成功定义最终取自DexLab对应工况，不能从动画或本章示例中生成评分规则。任务保存的最小字段：每环境phase、phase进入仿真时间、已接受目标、臂/指DOF列表、控制模式/限额、最新输入序号、失败原因。碰撞/力/触觉信号的测量语义在E3/E4展开。

| 阶段 | 原生控制动作 | 转移依据 | 超时/失败处理 |
|---|---|---|---|
| 初始化 | reset；明确重设增益/range和臂/指模式 | 模型映射和任务初态已确认 | 记录初始化错误并停止该次任务推进 |
| 接近 APPROACH | 接受的IK/路径→臂`control_dofs_position_velocity`；指保持打开 | 步后TCP误差与速度满足任务条件 | IK残差/规划valid不合格则不执行；跟踪超时进入FAIL |
| 闭合 CLOSE | 臂保持；指写位置或受限FORCE命令 | 使用任务规定的接触/间距/物体状态组合，不能只看目标已写入 | 达到截止时间仍不满足则FAIL |
| 保持 HOLD | 延续指定模式与限额 | 实际物体相对姿态/速度及持续时间 | 滑移、丢失或观测无效进入FAIL |
| 释放 RELEASE | 指切回打开位置模式；臂按协议保持/退出 | 步后打开和物体状态满足条件 | 超时记录失败；不将命令发送当成已释放 |
| 完成/失败 | 停止本次状态机推进并记录最后状态、输入与原因 | 外部显式reset或新episode开始 | 不隐式重试成无限循环 |

任务每tick的顺序应明确：读已完成步的状态→判断转移→写本tick命令→推进一次→读下一状态并记录时间。将同一批DOF从FORCE切回POSITION时必须真的调用相应模式setter；只改一个Python `phase`字符串不会改变引擎输入。

`scene.register_pre_step_callback(callback)` 在步进线程上、recorders和物理step之前调用；任一callback返回True会暂停本次物理推进，但可视化仍刷新。因此callback中按 `get_time()` 或实际推进数安排控制周期，不按“函数被调用次数”假定Δt已过去；外部消息过期可以另看墙钟，不能混成仿真时间。[回调顺序][step]

外部控制器接入需约定：joint名字顺序、位置/速度/力模式、单位和frame、时间戳所用时钟、期望控制周期、过期命令处理。用callback或同一驱动循环把最新已校验命令写入原生API，不从另一个线程同时改同一Scene。每m个真实step更新一次输入，控制周期才是mΔt；substeps不会自动多次调用Python控制器。

批量任务维护逐环境phase和进入时间；用互斥envs_idx写输入。不同环境处于不同phase不要求它们有独立solver dt。结束环境的局部reset仍受E1列出的多物理限制，不能将纯刚体任务代码直接套到Rigid+MPM混合场景。

## 9. 多物理与可微边界

本章原生驱动路径属于 `RigidEntity`。`KinematicEntity` 可做运动学/可视化状态设置，但不因此产生电机动力学；粒子实体另有 `set_position/set_particles_pos/set_velocity` 等粒子/实体状态接口，不能把它们拼成关节控制器。材料内部驱动、软体机器人和混合耦合由E6按各自物理变量展开。[粒子接口][particle]

可微的 `tracked` 控制目标路径与“整个机器人任务可微”不同。IK含重采样/候选选择/裁剪，规划含碰撞判断，任务状态机含离散转移；这些函数的存在不证明Torch梯度贯通。本章不承诺IK、RRT或任务成功信号可微。需要对具体solver、模式和损失逐链核对，而非仅设置 `requires_grad=True`。[控制目标记录][diff-track]、[IK分支][ik-result]

## 10. 原创阅读片段、排错与练习

[control_kinematics.py](../examples/control_kinematics.py) 使用本仓原创 [two_joint_arm.urdf](../examples/assets/two_joint_arm.urdf)，展示名字/两套索引、逐环境增益/目标、FK/Jacobian、IK完整q与残差，以及把标量q映射为PD目标。它**没有step循环、抓取场景或训练**，已做Python语法和XML结构检查，未运行；其中增益、目标、限额仅为读API的示意值，不是硬件参数或已验证控制方案。

官方 [control_your_robot.py][official-control]、[IK_motion_planning_grasp.py][official-ik]、[batched_IK.py][official-batch] 可帮助追调用顺序；本轮只读，未复制资产或运行。官方注释也需对照实现，例如FORCE输入仍受range裁剪，IK结果默认不代表任务成功。

| 症状 | 先检查 |
|---|---|
| IK返回后机器人不动 | 是否只求解，没有发控制和实际step |
| 位置一设置就速度归零 | 调用的是Rigid setter默认True，而非PD目标 |
| 切换位置后目标速度丢失 | `control_dofs_position`清ctrl_vel；需要位置+速度接口 |
| kp getter报错 | 导入驱动不满足PD可化简条件，读gain/bias |
| 某环境改增益影响全部环境 | build时batch_dofs_info是否True |
| IK返回数组比动作长 | n_qs与n_dofs、四元数和子集优化仍返回完整q |
| 末端位置偏一个工具长度 | local_point的link frame与目标world frame是否混用 |
| Jacobian速度次序错误 | 此接口linear在前；自由根旋转增量还需换系 |
| valid path仍碰撞或抓不稳 | 排除接触pair、离散几何检查和动态执行/抓取资格的区别 |
| callback反复执行而deadline不前进 | 是否返回True导致暂停，仿真时间与墙钟是否混用 |

1. 一条free根加2个revolute的链，IK返回多少配置值？能直接传到8维DOF位置控制吗？
   **答案：** 9个q值、8个DOF；不能直接传，free四元数/角目标表示不同，并应核对IK的世界旋转增量。本文片段因此限制固定基座标量关节。
2. `control_dofs_position_velocity(p,v)` 后对同一DOF调用 `control_dofs_position(p2)`，最终目标速度是多少？
   **答案：** 0；第二次写POSITION和p2，同时清ctrl_vel，并不继承v。
3. FORCE命令10 N·m、range=[−2,3]，getter可否直接标“真实接触力10N”？
   **答案：** 不可。重算控制值被裁剪为3 N·m；它是转动DOF广义力矩，不是法向接触力，更不是10N。
4. `envs_idx=[3,1]`、`dofs_idx_local=[5,2]`、目标`[[a,b],[c,d]]`分别写到哪？
   **答案：** env3的DOF5/2写a/b，env1的DOF5/2写c/d。模型增益是否独立还取决于batch_dofs_info。
5. 某标量关节qpos0=0.2rad、IK解q=0.7rad，控制使用何位置目标？
   **答案：** 在已确认该模型reference未改的前提下，DOF目标为0.5rad；不要把q绝对槽位值与dofs.pos直接混用。
6. 为什么IK的error很小不证明指定姿态全部满足？
   **答案：** 被mask或未指定的分量不进入误差；还需检查所求目标、残差范数、支持关节与限位。它也没有证明碰撞或闭链条件。
7. 规划返回第二项True代表失败还是成功？它保证无任何碰撞吗？
   **答案：** `return_valid_mask=True`时True是有效，包装层反转内部is_invalid；不保证排除所有碰撞，起/终点已有接触pair会被排除。
8. 100个waypoint、每点2个真实step、dt=0.005秒，名义执行时长？若callback每次都暂停呢？
   **答案：** 推进200步则1秒；一直暂停则仿真时间不变，不能把调用次数当已执行。
9. 对SPHERICAL关节看到 `get_jacobian`方法存在，为什么不能直接宣称支持？
   **答案：** 实际Jacobian和scratch更新没有对应完整球关节分支；继承的API名不证明执行路径完整。
10. “控制力已达到range上限”为什么不能作为CLOSE→HOLD的唯一条件？
    **答案：** 饱和也可能源于未到目标、错误frame或障碍；保持需要任务规定的实际接触/物体运动观测，不能从控制命令推断抓取效果。

下一步建议 [E3 接触、求解器与力观测](roadmap.md)：本章已经定位了 `qf_applied`、smooth force、constraint force和重算getter的边界，可继续追约束行、力/冲量时点与材料组合。E4另展开传感与渲染。完整课程仍待后续阶段，不把未运行片段当成仿真实证。

[rigid-setter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L2569-L2590
[control-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L2784-L2878
[control-write]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2757-L2844
[control-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/accessor.py#L974-L1041
[control-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1441-L1540
[control-getter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/accessor.py#L1185-L1212
[force-assembly]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py#L1705-L1735
[constraint-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5784-L5804
[force-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3043-L3093
[gain-write]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2599-L2685
[gain-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3095-L3154
[indices]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_joint.py#L227-L304
[old-indices]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_joint.py#L28-L41
[names]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L655-L721
[initial-q]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L1188-L1201
[fk-dof]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_kinematics.py#L392-L435
[urdf]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/urdf.py#L394-L469
[mjcf]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/mjcf.py#L407-L479
[import-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/morphs.py#L1022-L1041
[options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L444-L499
[options-default]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L594-L611
[limits]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L1786-L1855
[shape]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L948-L983
[broadcast]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L1023-L1108
[assign]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L1152-L1185
[jac-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L1440-L1470
[jac-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L193-L260
[fk-query]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L1494-L1530
[fk-query-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L753-L806
[ik-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L1472-L1580
[ik-sanitize]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L1661-L1764
[ik-solver]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L1567-L1642
[ik-increment]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L299-L361
[ik-error]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L392-L468
[ik-dls]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L485-L546
[ik-result]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py#L591-L653
[plan-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L2027-L2165
[plan-limits]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/path_planning.py#L16-L28
[plan-exclude]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/path_planning.py#L112-L150
[plan-collision]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/path_planning.py#L177-L265
[plan-restore]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/path_planning.py#L1034-L1062
[step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1052-L1098
[sim-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L375
[reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1796-L1895
[diff-track]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L35-L68
[particle]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/particle_entity.py#L470-L563
[official-control]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/control_your_robot.py
[official-ik]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/IK_motion_planning_grasp.py
[official-batch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/batched_IK.py
