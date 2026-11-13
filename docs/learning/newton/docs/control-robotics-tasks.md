# E2 · 从控制输入到机器人与任务

先修：[E1 模型、坐标、状态与时间](modeling-state-time.md)。本章覆盖 A3 驱动与控制、A5 机器人与运动学、A7 任务接口。读完应能回答：一个末端目标如何变成原生 Control，哪个实现消费它，什么量只是命令，什么量是实际状态。

固定阅读版本为 Newton **1.6.1**，提交 `713fecdc41caf0c9d726f5c016939f36e66e3dff`；Warp 1.18.0 仍是候选依赖记录。Newton、Warp、SolverMuJoCo 所用的后端身份分开记录。本章不运行引擎、目标 IK、控制回路、实验、训练或基准；所有例子只做源码与语法核对。完整接触/约束求解与力观测在 E3。

## 1. 先区分设置状态、给目标和施加努力

`state.joint_q` 是当前配置；写它相当于修改状态。`control.joint_target_q` 是希望驱动到达的目标；写它不会立刻改变物体位置。`control.joint_f` 是广义努力输入，对标量转动关节为 N·m，对平移关节为 N。控制器输出需要经过实际消费者才能影响物理。

```text
任务阶段 → 工具/关节参考 → 轨迹或 IK → 关节目标
                              ↓
当前状态 → 控制器/Actuator → Control → Solver → 新状态
            ↑ 采样周期                   ↓
            └──── 带时间与 frame 的观测 ──┘
```

这是本章的读代码顺序，不新增统一控制框架。Newton 的原生接口已经足够表达各层；每一层的更新频率、数组布局和重置状态都要明确。

| 写入/调用 | 语义 | 下一位消费者 | 常见误读 |
|---|---|---|---|
| `state.joint_q/qd` + 必要 FK | 修改配置/速度 | generalized solver 或 `eval_fk` | 把瞬移当作有力限额的闭环运动 |
| `control.joint_target_q/qd` | 位置/速度参考 | solver 内置 drive 或显式调用的 Actuator | 认为 target 数组非空就有驱动力 |
| `control.joint_act` | actuator 的 feedforward 输入 | 默认 Actuator/Drive 读取 | 把它当作所有 solver 都会直接执行的 torque |
| `control.joint_f` | 本步关节力/矩输入 | XPBD、Featherstone、MuJoCo 等的实际映射路径 | 认为由任意来源写入的力都自动受 model effort_limit 限制 |
| `state.body_f` | world 表达、COM 参考的外部 wrench | solver 的外力路径 | 把它当作接触传感器输出或关节内部反力 |
| `controller.step(...)` | 写 controller 的输出 port | 使用者连接到 Control 或状态 | 认为 controller 自动注册到 physics step |

原生定义：[Control](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py#L17-L66)、[Actuator 输入/输出属性](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/actuator.py#L232-L286)。FREE/DISTANCE 的 `joint_f` 是 world、child COM 参考的六维 wrench；不能将其与 parent-frame 的 joint_qd 不经变换直接点乘算功率，见 E1。

## 2. 四张索引表比“第几个关节”更重要

保留模型导入后的 `joint_label`、`body_label`、`articulation_label` 和工具 site 的 `shape_label`。URDF/MJCF collapse、根连接方式、多 world 复制都可能改变数量或顺序；不要把另一资产的末端 body 编号、指关节编号复制过来。

| 需要索引的量 | 起点/布局 | 自由根后的第一个 1-DOF 关节示意 |
|---|---|---|
| 当前配置 `state.joint_q` | `model.joint_q_start[j]` | 根占 7 个数，后一个标量从 7 开始 |
| 当前速度、`joint_f/joint_act/target_qd` | `joint_qd_start[j]` | 根占 6 个数，后一个标量从 6 开始 |
| 目标位置 `control.joint_target_q` | `model.joint_target_q_start[j]` | 取决于目标布局，不能假设必为 qd start |
| controller 的 compact 输出 | `controller.q_start/qd_start` 对应的受控集合 | 可能仅选择若干关节，不等于全 Model 数组 |

本版本的 `newton.use_coord_layout_targets` 决定目标位置用 coordinate layout 还是旧 DOF layout。需在构建模型/actuator **之前**确定；之后切换全局开关不会重新生成已有索引。建议教学代码显式选择 coordinate layout，仍用 `joint_target_q_start` 表达意图。只含标量关节时 q 与 qd 长度相同，容易掩盖浮动根错误。[目标数组生成](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L13659-L13684)、[Model 的目标起点属性](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1613-L1622)

`builder.add_actuator(..., index=...)` 的 index 是 velocity/effort 空间；`pos_index=...` 单独指定 position 空间。其 docstring 把 pos_index 也称为 DOF index，但随后明示访问 `joint_q`；本章按实际位置数组理解为**配置坐标索引**。示例总是分别传两个起点。[注册接口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L2730-L2764)、[finalize 创建映射](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L13818-L13865)

公开 controller 构造器的 `articulations` / `joints` 支持标签选择，内部由 `select_joints` 等 helper 解析；`select_joints` 并未从本版本 `newton.controllers` 公开导出，不应按公共 API 导入。默认只选恰好 1-coordinate/1-DOF 的可控关节；明确指定不支持的多自由度关节会由相应 controller 拒绝，不能把一个 BALL 关节当成三条独立标量角来做 `q_des-q`。返回值每条选中关节各有一个 q/qd 起点，**不是逐 DOF 展开的全局切片表**。选中关节顺序受选择参数影响，跨机器人按 robot 分组。[内部选择契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/joint_selection.py#L34-L132)、[公开导出列表](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/controllers.py#L13-L33)

## 3. 内置 joint drive：字段相同，消费算法不同

构建标量关节时可设置 `target_ke/kd`、`target_pos/vel`、`damping`、`limit_lower/upper`、`limit_ke/kd`、`effort_limit`、`velocity_limit`。这些是描述字段；不能由字段存在推断 solver 实现。`damping` 是被动速度阻尼，`target_kd` 是相对目标速度的驱动阻尼，两者可能同时作用。[JointDofConfig](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L1057-L1115)

| 此版本路径 | 目标如何起作用 | 限位和努力边界 | 需要保留的限制 |
|---|---|---|---|
| `SolverXPBD` | `solve_body_joints` 将 target/gain 组织成位置/速度约束修正 | 关节位置限位为硬位置约束；不使用 limit_ke/kd | 不支持 model effort/velocity limit、armature、joint friction、target_mode；不要把每次修正当作普通显式 PD 力 |
| `SolverSemiImplicit` | maximal body 关节力；标量 `joint_force` 求目标弹簧/阻尼 | 位置越界时关闭该内置 target 项、改用 limit 弹簧/阻尼 | effort/velocity limit、target_mode 等不支持；BALL 目标 drive 在该 kernel 中未实现 |
| `SolverFeatherstone` | generalized 坐标路径，将标量 drive 力与 `joint_f`、动力学项组合 | 使用相同 `joint_force` 计算软限位；支持 armature | target tracking 仅 PRISMATIC/REVOLUTE/D6；BALL/FREE/DISTANCE 不施加目标 drive；不支持 effort/velocity limit、target_mode 等 |
| `SolverMuJoCo` | 将 target/mode 编译为后端 actuator，运行时映射到后端 ctrl；joint_f 是另一条输入路径 | 支持部分模型驱动/限位/努力设置，但限制作用于指定的后端路径 | free joint 不创建目标 actuator；后端、导入 actuator、ctrl source、坐标转换需单列 |

依据：[XPBD 支持限制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L90-L101)、[XPBD target 消费](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L1732-L1753)、[SemiImplicit 声明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/solver_semi_implicit.py#L32-L56)、[BALL 的实际路径](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_body.py#L226-L245)、[Featherstone 限制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py#L85-L99)、[广义力装配](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/kernels.py#L431-L459)、[MuJoCo free-joint 警告](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L6766-L6777)。这张表用于阅读控制边界，不是完整 solver 能力矩阵。

对上述 `joint_force` 的标量、限位以内分支，公式为：

$$
\tau_{drive}=k_p(q^*-q)+k_d(v^*-v)-b v.
$$

越过上下界后，此函数把目标 PD 设为零，采用 $k_l(q_{bound}-q)-d_l v$ 的限位恢复项，并保留被动阻尼。**这个切换只发生在该内置函数，外部额外写入的 joint_f 不会因此消失。** XPBD 的约束分支与 MuJoCo 后端并不等于这条函数。[函数全体](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_body.py#L18-L52)

## 4. 显式 Actuator：每个调用的输入和输出都可追踪

本版本 `newton.actuators` 与 `newton.controllers` 都标注为**实验性 API**。原生构成是 `Actuator(Drive, Delay?, Clamping[])`，使用 `DrivePD` / `DrivePID` 等名称。旧 `Controller*` actuator 名称是兼容别名；它们与 `newton.controllers.ControllerDifferentialIK` 这类机器人控制器不是同一层。[官方构成与限制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/actuators.rst#L8-L95)

该组合 actuator API 的文档限定为 SISO（一个输入/输出对应一个 DOF），没有内建齿轮/连杆 transmission，也不自动建模电机惯量、摩擦或热过程。不要把某个字段名或神经 drive 支持误认为完整真实电机模型；这也不等于断言 MuJoCo 后端所有原生 actuator 都具有相同限制。

正常调用链是：

```text
builder.add_actuator(DrivePD, index, pos_index, ...)
  → finalize: model.actuators
  → 调用者清 control.joint_f
  → actuator.step(state, control, [actuator states], dt)
  → Delay 读入 → Drive 计算 → Clamping → 写入/累加 joint_f
  → 更新 actuator 内部状态 → physics solver.step
```

注册后不会自动运行。`Actuator.step` 默认读 State 的 joint_q/qd、Control 的 target_q/qd 和 joint_act；计算努力后按 effort indices 写入 `joint_f`。同一输出缓冲会累加，因此在**一轮所有 actuator 之前**清零一次，不要在每个 actuator 后清零，也不要完全不清。每个并行 actuator 组内保持输出索引唯一，不将重复映射误认为已保证原子累加。[实际五阶段 step](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/actuator.py#L425-L539)、[累加 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/actuator.py#L29-L44)

### PD、PID 与量纲

对一个标量关节，显式 DrivePD 在当前采样状态上计算：

$$
\tau_{raw}=\tau_{const}+\tau_{ff}+k_p(q^*-q)+k_d(v^*-v).
$$

其中 joint_act 默认提供 $\tau_{ff}$，不是归一化 action；DrivePD 不负责 action 到物理单位的缩放。[实际 effort kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/drives/drive_pd.py#L29-L66)

| 参数 | revolute | prismatic |
|---|---|---|
| $q,q^*$；$v,v^*$ | rad；rad/s | m；m/s |
| $k_p$ | N·m/rad | N/m |
| $k_d$ | N·m·s/rad | N·s/m |
| $\tau_{ff},\tau_{raw}$ | N·m | N |
| PID 的 $I_e=\int(q^*-q)dt$ | rad·s | m·s |
| PID 的 $k_i$ | N·m/(rad·s) | N/(m·s) |

DrivePID 使用本次位置误差更新积分：$I_{e,n+1}=\operatorname{clip}(I_{e,n}+h_a e_n,-I_{max},I_{max})$，再将 $k_iI_{e,n+1}$ 加到努力中。这里的 $h_a$ 是**actuator 调用周期**。积分裁剪不等于输出反算式 anti-windup，也不等于电机热/摩擦/惯量模型。[PID kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/drives/drive_pid.py#L64-L107)、[参数单位](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/drives/drive_pid.py#L177-L189)

### 饱和与双重驱动

`ClampingMaxEffort` 对单个 actuator 的输出做 $\tau=\operatorname{clip}(\tau_{raw},-\tau_{max},\tau_{max})$。默认无限上限不能当作实际电机额定力矩；应明确配置。多个 actuator、内置 drive、外部 body force 和接触约束的总效果不是该单一 clamp 的承诺。[clamp](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/clamping/clamping_max_effort.py#L29-L58)

若显式 Actuator 和 solver 内置 target drive 同时读取同一目标/拥有非零增益，会形成两个驱动来源。最小例子将内置 `target_ke=target_kd=0`，只通过 DrivePD + clamp 生成 joint_f；不是仅设 `target_mode=NONE`，因为 XPBD/Featherstone 等并不消费这个 mode 来开关所有 target 项。

MuJoCo 映射尤其要区分：target 进入 ctrl/actuator 路径，标量关节的 `joint_f` 进入 `qfrc_applied` 路径；FREE/DISTANCE 的 COM wrench 经独立 kernel 进入 `xfrc_applied`。编译 actuator 的 forcerange 不能被解释为对任意 `qfrc_applied` 的全局饱和。若外部 Drive 输出也需限额，应在写入 joint_f 前明确执行相应 clamp。[两条控制映射](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L5014-L5076)、[joint_f 直接映射 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L1732-L1817)

### 状态、延迟与 reset

纯 PD 无 delay 时是无状态的，可直接 `actuator.step(state, control, dt=h_a)`。PID、Delay 或带历史的神经 drive 则需要 `a0=actuator.state()` 与 `a1=actuator.state()`，每次传入/传出并交换；`a0/a1` 与物理 `state_0/state_1` 是两套不同缓冲。reset 时两套 actuator state 都按需要 `.reset()`，并处理 Control/物理/任务时钟。actuator reset mask 长度是该组 actuator 数量，不是 world 数量。[状态契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/actuator.py#L193-L220)

Delay 用 actuator 调用次数计数，不是渲染帧数。历史为空或 delay 为零时直接用当前命令；不足指定历史长度时退到最旧可用项，所以启动阶段并非自动输出零。若每 0.004 s 调 actuator 一次，delay=5 稳态对应 0.020 s 的命令延迟；改为每个 0.001 s 物理子步调用，延迟也随之改变。[读缓冲分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/delay.py#L52-L93)

## 5. “implicit effort”与物理求解器的 implicit 分开

Actuator 默认显式：在当前状态计算努力，本步保持。它也支持 `set_effort_mode_implicit(response=JointSpaceResponse(model))`，每步先刷新关节空间响应。该模式在**预测的步末状态**评价 drive/clamp，并在同一 articulation 内耦合求努力；这不是将整个 physics solver 切换成一种新积分器。

用单关节、恒定有效惯量 $J>0$、无其他力、无饱和、固定目标的简化推导，令步长 $h$，预测 $v'=v+h\tau/J$、$q'=q+h v'$，把它们代入 PD：

$$
\tau=\frac{\tau_{const}+\tau_{ff}+k_p(q^*-q-hv)+k_d(v^*-v)}{1+(h^2k_p+hk_d)/J}.
$$

这解释了增益/步长大时努力会被分母压低；不是“完全相同力矩但无限稳定”。实际实现按 impulse $p=h\tau$ 求残差 $r=p-hf(q',v')$，并把 clamp 放进求解；上述闭式只用于说明简化假设。[实际预测与残差](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/effort_mode_implicit.py#L236-L287)

官方明确预测不包括重力、其他外力、其他 actuator 与独立 joint drive。`JointSpaceResponse.refresh` 的响应还不含接触、摩擦、限位、阻尼、约束正则化和闭环耦合等完整效果。不能用该模式替代接触丰富任务的动力学验证，也不能称其输出符合完整系统的精确 Backward Euler 解。[模式与响应边界](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/actuators.rst#L290-L355)。本章例子采用显式模式，完整数值分析留 E3/E6。

## 6. 从关节到工具：FK、Jacobian 和参考点

E1 已定义 `eval_fk` 与 `eval_ik`。此处再区分三个不同问题：

| 原生接口 | 输入 → 输出 | 是否在求目标动作 |
|---|---|---|
| `newton.eval_fk` | joint q/qd → body pose/twist | 否，给定配置求几何 |
| `newton.eval_ik` | 已有 body pose/twist → joint q/qd | 否，这是 maximal 状态重建 |
| `newton.ik.IKSolver` | 当前 seed + 目标 objective → 候选 joint q | 是，数值优化目标误差 |
| `ControllerDifferentialIK` | 当前 joint 状态 + world 工具目标 → velocity/position target | 是，每次给一个局部控制更新 |

控制工具点要显式建立 TCP。`builder.add_site(body, xform=T_BT, label=...)` 创建无碰撞、零质量贡献的参考标记，内部以 shape 存储，返回的是 shape/site ID；它不是一个具有新自由度的 body。工具世界位姿 $T_{WT}=T_{WB}T_{BT}$，不能把 wrist body 原点、COM 与 TCP 混成一点。[site 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L8191-L8222)

`eval_jacobian` 的 body 行以 COM 为速度参考点。对同一 world 表达的第 $j$ 列，从 COM 移到 TCP，$r=p_T-p_C$：

$$
J_{v,T}^{(j)}=J_{v,C}^{(j)}+J_{\omega}^{(j)}\times r,\qquad J_{\omega,T}^{(j)}=J_{\omega}^{(j)}.
$$

原生模型型 controller 会执行 FK、Jacobian、COM→TCP 换点，然后求控制。不能仅在误差里使用 TCP、却仍拿 COM Jacobian 求解。[换点 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/_common.py#L100-L156)、[模型型 controller 调用链](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/model_based.py#L552-L609)

`tool_sites` 对每个受控机器人必须恰好匹配一个 site；world-fixed site 或没有对应运动 body/Jacobian 的 site 不可用作工具。该约束防止一个标签模式意外选中左右两个指尖或误把固定参考架作为末端。[解析与错误条件](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/tool_selection.py#L42-L80)

## 7. 目标 IK：优化结果不是执行结果

`IKSolver` 可用 LM 或 L-BFGS，默认 LM；配置 Jacobian 方式、目标列表、seed/多 seed 采样。输入/输出 q 数组形状为 `[n_problems, joint_coord_count]`，不是控制器 compact DOF 数组。`step` 输出最佳候选配置；一次返回不提供接触可行、动力学可行或任务成功证明。[前端与约束](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_solver.py#L196-L276)、[step 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_solver.py#L348-L403)

常用 objective 的含义是：

- `IKObjectivePosition(link_index, link_offset, target_positions, weight)`：$e_p=w_p(p^*_W-T_{WB}p^B_{offset})$，target 为 world 点，offset 为 link 局部点。[位置 residual](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_objectives.py#L160-L180)
- `IKObjectiveRotation`：将 `body_rot * link_offset_rotation` 与目标旋转比较。此 objective 的 residual 从 **actual × inverse(target)** 构造轴角，再配套自己的 Jacobian；不要擅自换成另一个控制器的 desired-minus-current 符号而保留原 Jacobian。[旋转 residual](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_objectives.py#L766-L808)
- `IKObjectiveJointLimit`：对标量越界给 residual，界内为零。它是优化惩罚项，**不是硬约束投影**；大 weight 也不能保证数值结果完全在范围内。源码按 DOF→coord 映射访问标量坐标，不可将其泛化成球关节旋转锥或任意 quaternion 的合法性约束。[限位 residual](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_objectives.py#L499-L525)、[坐标映射](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_objectives.py#L607-L630)

权重乘的是 residual/Jacobian 行，所以平方误差中的贡献随 $w^2$ 变化。位置误差 m 与姿态误差 rad 混合时要先声明尺度；不能把同一个数字 weight 当作“两个物理量同样重要”的充分定义。

LM 对 residual Jacobian $J_r$ 求：

$$
(J_r^TJ_r+\lambda I)\Delta v=-J_r^Tr,
$$

再沿模型的配置积分映射更新 q，比较实际/预测代价变化来调整阻尼。本实现对角加的是 $\lambda$，不是下面 differential IK 公式中的 $\lambda^2$。正定分解、步长缩放、seed、mask 与迭代数都会影响候选；有限迭代到达的是某个候选，不能称作全局逆解。[实际 LM 线性系统](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_lm_optimizer.py#L750-L779)

对候选至少检查残差、限位、资产碰撞/闭环条件，再经平滑轨迹交给执行 drive。不要直接覆盖动态 State 来冒充受限控制。官方 [Franka IK 示例](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/ik/example_ik_franka.py#L73-L123) 用 q 输出与 FK 做运动学展示；其中硬编码 `ee_index` 是该示例资产的局部约定，不能照抄到任意机器人。

本章的[原创二连杆候选 IK 例子](../examples/e2_target_ik.py)用 primitive、显式 link ID 和局部 TCP 偏移，不下载机器人资产，不推进物理。它仅展示目标/seed/候选的 API，未求解运行，也没有宣称收敛。一般浮动根/球关节、多 seed 与闭环模型需要额外核对配置空间处理；本例刻意限定两个标量 revolute 关节。

## 8. Differential IK 与关节阻抗的输出怎么接

`ControllerDifferentialIK` 的 model-based 版本接收全 Model q/qd 和每个受控 robot 的 world 工具目标。它在内部更新运动学，输出的是**compact 的 joint_qd_target/joint_q_target**。只控制 1-coordinate/1-DOF 关节；未控制关节仍会影响 FK，因此输入不能裁成只有受控关节的短数组。[接口与范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/model_based.py#L32-L75)、[输入输出形状](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/model_based.py#L198-L231)

默认 DLS 的等价表达为：

$$
\dot q^*=B J_w^T(J_wJ_w^T+\lambda^2I)^{-1}e_w,
\qquad q^*_{next}=q+h_c\dot q^*.
$$

其中 $J_w=\operatorname{diag}(w)J$、$e_w=\operatorname{diag}(w)e$，$B$ 为逐 DOF bandwidth。API 的零 axis weight 会结构性移除对应任务轴；非零 weight 作为软权重。实际实现通过 **单边 Jacobi SVD** 计算阻尼伪逆，不直接照公式构造一个显式逆矩阵。DLS 的 $\lambda$ 与目标 IK LM 的 lambda_initial 不是可互换参数。[DLS/方法定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/_common.py#L36-L65)、[SVD 实现选择](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/_common.py#L606-L644)、[目标位置积分](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/_common.py#L596-L605)

这个 pose error 的方向是 **desired × inverse(current)**，并选短弧，与上一节优化 objective 的 residual 定义不同；两者各自有匹配的求解符号，不能拆换。[控制误差 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/_common.py#L40-L96)

模型型 controller 可用原生 indexed arrays 将 compact 输出接到 Control 对应索引；本版本选择 coordinate target layout 时位置目标映射可使用 controller.q_start，速度使用 qd_start。若保持旧 target layout，位置端不能直接套用 q_start。输出给 Control 后仍要 actuator/solver 消费。官方 differential IK 示例把输出绑定到 **State** 再 FK，是纯运动学展示，源码明确没有 physics solver，不能将该示例作为带力矩限制的机器人执行证据。[官方输出绑定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/controllers/example_controller_differential_ik.py#L310-L335)、[实际 simulate](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/controllers/example_controller_differential_ik.py#L556-L561)

`ControllerJointImpedance` 则输出关节努力。其模型型版本可选惯量解耦、科氏/重力补偿：

$$
\tau=\big[M(q)\ \text{或}\ I\big]\left(\ddot q^*+K_p\Delta q+K_d\Delta\dot q\right)
+\big[C(q,\dot q)\dot q\big]_{enabled}+\big[g(q)\big]_{enabled}.
$$

启用惯量解耦时，$K_p/K_d$ 单位是 s⁻²/s⁻¹；未启用时是普通努力型增益单位。因此不能把 DrivePD 的一组数字不改含义地抄到解耦模式。实际质量/重力来自模型，模型误差会进入补偿；这不是硬件力矩、接触力或估计器的自动校准。[方程与端口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/joint_impedance/model_based.py#L34-L120)

最小完整端口连接片段如下；**仅语法检查，调用者提供当前固定版本创建的 model/state/control**。它说明输出去哪里，不替代闭环采样调度或参数资格验证。

```python
from newton.controllers import ControllerJointImpedance


def connect_joint_impedance(model, control, articulation_label, joint_labels):
    controller = ControllerJointImpedance(
        model,
        articulations=[articulation_label],
        joints=joint_labels,
        stiffness=25.0,
        damping=5.0,
        use_gravity_compensation=True,
        use_coriolis_compensation=False,
        use_inertia_decoupling=False,
        has_qdd_feedforward=False,
    )
    inputs = controller.input()
    outputs = controller.output()
    outputs.joint_f = control.joint_f[controller.qd_start]
    return controller, inputs, outputs
```

调用时每个实际控制采样点重新绑定 `inputs.joint_q/qd` 到当前物理 buffer，给 `joint_q_des/joint_qd_des` 写入 compact 目标，然后 `controller.step(inputs=inputs, outputs=outputs, dt=h_c)`。此 controller 的 dt 仅为 API 兼容参数、实现不使用它，采样周期由应用调用频率决定，见 [step 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/joint_impedance/model_based.py#L380-L393)。这里 outputs 写 port，不是 Actuator 的自动累加协议；若同一通道还有其他控制来源，应显式定义合成次序与最终饱和。不要把 controller 输出的 feedforward 力再交给另一层同增益 PD 而不说明额外反馈。

## 9. 外力、关节命令与三层限制

在 world 点 P 对 body 施加力 $f^W$ 与绕 P 的附加力矩 $\tau_P^W$，写 COM wrench 前需：

$$
\tau_C^W=\tau_P^W+(p_P^W-p_C^W)\times f^W.
$$

`State.body_f` linear-first，为 $(f^W,\tau_C^W)$。如果外部装置给出 tool-frame wrench，先旋到 world，再换到 COM；不要只旋转三个力分量却保留原参考点的 torque。持续外力要在每步 `state.clear_forces()` 后重写；该函数不清 control.joint_f。[State 外力定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L150-L169)、[清理范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L193-L205)

三层限制要分别设计与记录：

1. **参考限制**：目标位置、速度、加速度/jerk 的规划边界；clip 一个 endpoint 不会自动产生平滑轨迹。
2. **执行器限制**：例如 ClampingMaxEffort/DC motor 的努力包络；命令饱和后实际状态可以继续因惯性/外力变化。
3. **模型约束**：joint limits、闭环、接触在 solver 中如何处理；可能硬约束或软力，未必是控制器的目标裁剪。

闭环机器人不能只检查 FK。Newton 的 loop-closing joint 可在 builder 中创建但不加入 articulation tree；`eval_fk/eval_ik` 只走 tree，闭环条件需由支持它的 solver 处理。XPBD/SemiImplicit 按 pairwise joint 处理但仍受各自功能限制；Featherstone 不强制闭环；MuJoCo 仅支持部分闭合类型且丢弃闭合关节某些 drive/limit 属性。资产可解析与闭环被执行是不同验收。[闭环约定与 solver 边界](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/articulations.rst#L996-L1050)

## 10. 采样、回调与外部控制集成

Newton 的物理 `solver.step`、机器人 `controller.step`、`actuator.step` 是由应用显式编排的不同调用；`Example.step/render` 是应用示例方法，不是自动改变控制频率的通用物理 callback。外部 ROS/策略/设备消息同样先被应用接收，再转到原生 Control。当前阶段只定义这一接口，不连接真实机器人或跑策略。

设物理步 $h=1$ ms、外层参考更新 $h_c=10$ ms、actuator 更新 $h_a=1$ ms：外层每十个物理步更新目标，PD 每步用新状态追踪被保持的目标。如果 actuator 也改为 10 ms，它的努力将在十个物理步内保持，形成另一个离散系统；PID 积分/Delay 的 dt 与步数也必须跟着改变。这些是调度说明，不是推荐的实测参数。

| 阶段 | 最少需要的记录 | 操作 |
|---|---|---|
| 接收外部参考 | 命令序号、时间戳/时钟域、单位、frame、关节标签 | 处理过期/越序/缺失；做 frame 与 q/qd/target layout 映射 |
| 控制采样 | 当前物理时间、phase、状态 buffer | maximal solver 先 `eval_ik` 得到新 generalized 状态，控制器读取该次采样 |
| 目标/努力写入 | 控制周期与 actuator 周期、限幅前后值 | 明确清 joint_f、驱动调用、额外努力合成顺序 |
| 物理子步 | dt、采样的 contacts、输入 Control | clear body forces 后重写外力，collide，再 solver.step，交换物理 buffer |
| 观测发布 | 测量所属步、采样阶段、frame、是否新鲜 | 步前 contact 几何不可冒充步后测量；不把命令复制成观测 |
| reset | 任务计时器、物理/Control/actuator/controller 历史 | 停用旧命令、恢复一致状态；未承诺中途快照逐位续算 |

[显式原生 PD 例子](../examples/e2_scalar_drive.py)展示一条 revolute 关节的布局、clamp 和逐步反馈；动力学仍使用 Newton 的 Model/State/Control/XPBD，不引入 wrapper。示例没有 GUI、外部资产、指标或训练。限幅后的 joint_f 仍只是输入，不能据此推断实际关节反力已测得。

## 11. 接近、闭合、保持、释放：把任务语义接到原生对象

任务阶段决定参考，而不是直接覆盖物理状态。可使用以下契约组织未来 DexLab 案例；表中事件都是需要从实际观测计算的条件，当前没有生成实验结果。

| phase | 写入的参考/原生通道 | 转移必须依赖的观测 | 失败或超时处理 |
|---|---|---|---|
| APPROACH | world TCP pose → IK/轨迹 → arm target_q/qd | TCP 位置/姿态误差持续满足要求；观测新鲜 | 不可达、限位/碰撞检查未通过或时间预算耗尽 → FAILED |
| CLOSE | 手指关节目标/速度与明确努力限幅；手臂保持 | 闭合条件与接触证据按协议成立，不能只看 target 已写入 | 超时、模型状态异常、命令过期 → FAILED |
| HOLD | 保持参考与允许的反馈/努力 | 物体相对工具位姿/速度在连续窗口中满足协议，不能只看指关节误差 | 滑移使确认条件失效时重置稳定计时；观测过期或超时失败 |
| RELEASE | 打开指关节，手臂按计划保持/撤离 | 实际开度/物体状态满足释放条件 | 超时失败 |
| DONE / FAILED | 显式冻结或撤销当前输出，由应用选定最终策略 | 终态只记录相应事件 | reset 前不得隐式重启下一轮 |

“闭合”不等于“稳定抓持”，“接触存在”不等于“无滑移”，“努力输入为 2 N·m”不等于“夹持力为 2 N”。条件要记录 frame、量纲、采样阶段与持续窗口；具体阈值、接触/力读取及最终成功定义应沿用将来所引用 DexLab 的冻结协议。本章不给这些占位条件填入虚构验收数据。

[原创任务阶段函数](../examples/e2_task_phases.py)只接受上游已计算的带新鲜度条件与仿真 dt，管理连续 dwell/phase timeout/终态。它不接管模型、控制器、传感器，也不充当评分器；返回 phase 后由上表选择各原生目标。示例中 `dwell_s` 与 `timeout_s` 必须由调用者提供，不把任意常数包装成抓取标准。

## 12. 常见失配与阅读练习

| 现象 | 检查方向 |
|---|---|
| 目标更新但物体不动 | target_gain 是否非零、Actuator 是否 step、Solver 是否支持该 joint/drive、Control 是否真传入 |
| 力矩随帧数累加 | Actuator 输出是累加，检查 joint_f 清零位置；clear_forces 只清 State |
| 开 actuator 后力突然翻倍 | 内置 target_ke/kd 与显式 PD 是否同时启用；joint_act 是否重复加入 |
| 浮动根模型控制错关节 | 分别核 q_start、qd_start、target_q_start、compact selection，禁止复制硬编码 slice |
| 力限额看似不起作用 | 限额属于哪个来源/后端路径；外部 qfrc、接触、其他 actuator 不自动受同一个 clamp 限制 |
| FK 看起来对但末端控制偏移 | 是否使用 TCP 而非 wrist/COM，Jacobian 是否同步换参考点 |
| IK 返回了但目标不可达 | 读残差/限位/seed/选轴；有限优化输出不等于成功 |
| reset 后第一步动作异常 | actuator 两个状态、delay、Control、任务时钟、当前 buffer 是否同时恢复 |
| 模型位置变化却没有真实控制响应 | 是否将 controller 输出直接绑定 State；区分运动学演示与动力学执行 |

1. 自由根后第一个 revolute 的 q 起点为 7、qd 起点为 6，注册 DrivePD 时 index/pos_index 应如何填？coordinate target layout 又影响哪项？
2. $q^*-q=0.2$ rad，$v^*-v=-0.3$ rad/s，$k_p=20$、$k_d=2$、feedforward=0.4 N·m、const=0，max_effort=3 N·m，raw 与 applied 是多少？这是接触反力吗？
3. 为什么在每个 actuator 的 step 后清 joint_f 会抹掉贡献？为什么只清 state.body_f 也不够？
4. SemiImplicit 的内置 target 在越限时被关掉，外部 DrivePD 是否也会因此停止施力？
5. TCP 比 COM 多偏移 $(0.1,0,0)$ m，某 Jacobian 列 $J_v=0$、$J_\omega=(0,0,1)$，TCP 线速度列是什么？
6. `IKObjectiveJointLimit(weight=1000)` 是否意味着关节硬限位？位置 objective 的 weight 翻倍对平方代价贡献如何变化？
7. 两种 IK 的 lambda 为什么不能对表互换？官方 controller 示例直接写 State 能证明限力跟踪吗？
8. HOLD 条件先连续满足 0.08 s、失败一个采样、再满足 0.03 s，若 dwell=0.1 s，能转 RELEASE 吗？

<details>
<summary>参考答案</summary>

1. index=6，pos_index=7；coordinate layout 令目标位置也用相应 q 起点，但仍应读取 target_q_start。旧 DOF layout 的 target 位置从 6 开始，不能仅凭 pos_index 推断。
2. raw=$20\times0.2+2\times(-0.3)+0.4=3.8$ N·m，applied=3 N·m。它是驱动命令，不是已测得的反力或接触力。
3. 清零应在一轮累加前；每次之后清会连刚产生的努力也擦掉。body_f 和 control.joint_f 是不同数组，前者清理不影响后者。
4. 不会。内置 joint_force 的分支只控制自身 target 项；外部 joint_f 仍被装配，需由外部控制逻辑/限幅单独管理。
5. $J_{v,T}=0+(0,0,1)\times(0.1,0,0)=(0,0.1,0)$。此处各量都在 world 方向表达。
6. 不能，它是 residual penalty；结果需再检查。weight 翻倍会令相同原始误差的平方代价贡献乘 4。
7. LM 在 $J_r^TJ_r$ 上加 $\lambda I$；DLS 等价公式使用 $\lambda^2$，目标、残差与求解变量也不同。直接写 State + FK 只演示运动学，不证明电机/物理限制。
8. 不能。连续 dwell 在条件失败时归零，后续只累计 0.03 s；把两段相加会掩盖中途滑移或观测失效。

</details>

## 13. 交付与后续边界

[验证记录](e2-validation.md)覆盖来源身份、链接锚点、脚本/Markdown 语法和人工语义审查。A3/A5/A7 的概念与原生接口专题已展开；E3 的接触/求解与力观测、E4 的传感/渲染、E5 的批量/学习仍有独立任务，未被本章示例替代。下一项优先 E3，解释任务观测与 solver 能力表背后的约束/接触计算，实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab)。系列导航见 [Sim Atlas](https://github.com/huangkiki/sim-atlas)。
