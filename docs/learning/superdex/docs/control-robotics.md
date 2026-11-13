# E2 · 驱动、机器人、运动学与任务接口

本章覆盖 A3/A5/A7：把 joint/link/DoF 映射接到控制输入，沿原生实现分清状态设置、外力控制、隐式 pose tracking、transmission 和 IK，最后设计由应用负责的任务状态机。先读 [E1](modeling-state-time.md) 的 frame、状态所有权与采样时刻；需要向量、叉积、Jacobian 和基础反馈控制知识。

阅读基线为 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。候选包版本 `1.0.0` 不能代替 Physics/Robotics 实际构建身份。**本章只做官方源码阅读与语法检查，示例未 import/运行，未做仿真、训练、性能基准或评分。** 后续实验复用 DexLab。

## 1. 控制功能分别在哪一层

| 层 | 本版本的原生对象/入口 | 它负责什么 |
|---|---|---|
| Physics | `Scene`、articulated `Actor`、约束、`set_external_forces_on_dofs` | 存储与推进物理状态、广义外力和约束 |
| Physics pose controller | `add_articulated_pose_controller`、`set_articulated_target_pose` | 将 link/joint tracking 约束加入步内求解 |
| Physics experimental | `create_ik_solver`、transmission/actuator API | 准静态 IK、传动及其致动力；不应称作稳定跨版本统一接口 |
| Robotics | `BotPrefab`、`Bot`、`RoboticsContext`、三种内建 controller | 资产和组件生命周期，状态→控制输出或物理目标的组合 |
| Robotics 用户组件 | `register_python_controller/sensor/actuator` | 注册/查找/销毁/reset 契约；用户自行驱动控制链 |
| Studio | 资产转换与场景编辑 | 本章不把其导入流程等同 runtime，也不把编辑器行为写成 Physics API |
| 用户应用 | 轨迹、控制频率、任务阶段、接触判据、终止/reset | 原生对象的调度，多个控制源合成，业务成功条件 |

公开 [RoboticsContext::RegisterBuiltinTypes][context] 注册 `MOCHI_ARTICULATED_POSE`、`BASIC_JSC_PD`、`BASIC_OSC_PD` 和相机 sensor；具体内建 Actuator 不在该公开注册清单中，内部构建另有 `MOCHI_INTERNAL` 分支。不能由 `ActuatorBase` 的存在推断已经提供电机电流环/PWM模型。不过 Physics experimental 确实有 transmission actuator，不能反过来说 SuperDex 完全没有执行器。

[官方自定义组件例子][custom]明确把传感、controller、servo actuator 的计算放在应用 loop；框架约定的 `reset()` 不会替你每帧调用自定义 `compute_effort()`。其 `MyVelocityServoActuator` 是示例中的 Python PI servo，不是可直接用名称创建的内建硬件驱动器。Python 的公开用户入口是 `superdex.robotics`，由[模块转发][robot-entry]导出；阅读时见到生成 stub 内的 `bots` 命名空间，不代表需要改写示例的 import。

## 2. 从资产到关节和 DoF 映射

先加载/校验 prefab，再实例化：`load_bot_prefab_from_file` 或 `load_bot_prefab_from_urdf_file` → 修改根关节等模型设置 → `create_bot(scene,prefab,context)` → `bot.get_articulated_actor()`。URDF 的 mesh/inertial 局限已在 E1 讲清，这里不重复将“导入成功”视作控制模型正确。

`BotPrefab.joints[i]` 对应 `links[i]` 的父连接，link 顺序需满足父先于子。`RebuildBotData`/排序会重建缓存和 default pose；不要把创建前手工保存的序号当成永远稳定的 joint ID。创建后读 `actor.get_articulated_shape_info()` 的 `joint_names`、`joint_types`、`dof_info` 和 `parents`，明确每个关节的 `offset`、`trans_size`、`rot_size`。绑定维度见 [ArticulatedDofInfo][api]；构建逻辑见 [bot_utils.cpp][bot-utils]。

| 关节 | 对 actor DoF 的贡献 | 映射提醒 |
|---|---|---|
| `HARD` | 0 | 固定连接仍占 link/joint 索引，不占驱动坐标 |
| `REVOLUTE` / `PRISMATIC` | 1 | 分别 rad / m；不能把 prismatic gain 当 Nm/rad |
| `SPHERICAL` | 3 个转动 DoF | 同一个 joint 名对应三个 slot，增量遵守旋转流形语义 |
| `FREE` 根 | 6（3 平移+3 旋转） | actor space 包含，Robotics bot space 排除 |
| cycle 连接 | 不能当普通独立驱动槽位追加 | closed-loop 约束与 pose controller 支持范围需分开看 |

本 Robotics prefab 校验只接受 Hard/Free 根关节，Free 只能位于根；Physics 更广的 actor 能力不能直接外推为 Bot 接口支持。`BotPrefab.default_pose` 和 `GetEffortLimitsPerDof` 属于 **bot space**，不含 free root 的 6 个 DoF。原生 `build_articulated_pose_from_bot_pose(prefab,src_pose,num_actor_dofs)` 把 bot pose 转成 actor 长度，Free 根槽位补零；它不负责“保留当前 root pose”。有非零自由根目标时，应根据 root frame 和实际接口显式构造，不能以补零覆盖后再称为机器人保持原位。[构造实现][bot-utils] 1240–1277 行。

因此官方 [JSC hand 示例][jsc-example]按 revolute 个数递增索引，只在它先焊住 root、其余运动关节都是单 DoF 的已知资产上成立。通用应用应查原生 `dof_info`，不复制这个简化索引法。

## 3. 状态改写、外力命令与隐式目标是三种操作

| 操作 | 直接变化 | 是否代表执行了一段动力学控制 |
|---|---|---|
| `set_articulated_pose_from_joints/links` | 改实际 pose，更新派生变换/Jacobian，清多步历史；速度不自动归零 | 否；适用于初始化/reset 或运动学副本 |
| `set_external_forces_on_dofs` | 设置下一步使用的广义外力 | 是动力学输入，但不自动限制为某机器人可实现的 effort |
| `set_articulated_target_pose/link_transforms` | 改 pose tracking 的目标 | 要有相应原生 controller/约束；实际状态由后续求解产生 |
| Robotics JSC/OSC `compute_output` | 返回 effort buffer | 应用还须把输出写入 Physics |
| Robotics pose `compute_output` | 在 actor 内设置 tracking 目标，返回空 span | 不是 torque 数组；不能再把返回值当外力施加 |

`set_external_forces_on_dofs` 的 articulated 数值是 joint-DoF 基中的广义力，平移 N、转动 N·m。它**替换整套外力**，包括此次 indices 中未列出的旧值；两个控制器顺次调用不是叠加。[API 契约][api] 10578–10665 行，原生 [Actor 实现][actor]均可核对。若 JSC、重力补偿、任务控制等确实需要合成，应先在同一 DoF/frame/单位下求和、执行最终限幅，再一次写入；实验性 transmission 或 pose tracking 的内力是另一条路径，不能用外力 getter 代表它们的总输出。

## 4. Joint-space PD 的真实计算

先 `bot.create_controller("BASIC_JSC_PD")`，再提供与 actor DoF 数完全一致的 `ControllerBasicJscPdParams.kp/kd/saturation/deadband`。`get_current_observations_from_mochi()` 读取 pose 和 velocity，**不替应用填控制周期**；应设置 `obsv.dt` 为距上次 `compute_output` 的物理时间，随后创建 `ControllerBasicJscPdTarget(target_pose=...)`。计算路径在 [controller_basic_jsc_pd.cpp][jsc]，字段单位在[头文件][jsc-header]。

对于它适用的标量坐标，第 i 个分量按以下顺序计算：

$$e_i=q_i^*-q_i,\quad \bar e_i=\operatorname{sign}(e_i)\max(|e_i|-d_i,0),$$
$$\dot q_i^*=\begin{cases}(q_{i,k}^*-q_{i,k-1}^*)/H,&H>0,\\0,&H\le0,\end{cases}\qquad
u_i=K_{p,i}\bar e_i+K_{d,i}(\dot q_i^*-\dot q_i).$$

首次计算先把 previous target 设为当前 target，因此首次目标速度为零。若 `saturation[i]>=0`，再把 u 限到 ±该值；负值表示不限制。deadband 只作用于位置项，阻尼仍执行。转动的 Kp/Kd 为 N·m/rad、N·m·s/rad；平移为 N/m、N·s/m。这里没有积分项，也没有自动重力补偿。不要因名字包含 PD 而额外宣称摩擦补偿、feed-forward inverse dynamics 或电机动态。

该实现用逐分量减法，未对连续 revolute 自动 wrap，也未调用 E1 的旋转流形差分 API。对跨 ±π 的 setpoint 跳变、spherical/free 根必须特别处理表示和控制设计；本章最小片段只接受固定根、其余 Hard/单 DoF joints。不要以“数组长度正确”证明多 DoF 旋转误差语义正确。

目标突然跳变会在第二次以后形成约 `(q*_new−q*_old)/H` 的速度目标，产生 derivative kick；把物理 substep h 错当控制周期 H 会放大它。episode reset 除 Scene 快照外应 `jsc.reset()` 清 previous target，再设置一致初始目标；单独 restore actor 不会复原 Robotics C++ 对象的所有私有历史。

### effort limit 的三个容易混淆的位置

[BotJointPrefab.effortLimit][model] 定义：负数无界、零表示不驱动、正数有限额，并明确是**建议元数据，不复制到 Physics articulation 自动执行**。`BASIC_JSC_PD` 只读取自己的 saturation，不会自动继承 prefab limit。应用如要遵守模型限额，应将 bot/actor 索引对齐后对最终 effort 处理：正数 clip，零强制零，负数按业务允许的策略处理。

`BASIC_OSC_PD` 的可选最大 effort 归一化只让正限额参与比例计算，跳过 ≤0；因此零限额不保证该控制器输出该槽位为零。多个 effort 合成后只检查其中一个分量的限幅也不够。模型 limit 是关节驱动限额，不代表接触力限额，更不能把它写成夹持实验已经满足力限额。

## 5. Operational-space PD：Jacobian 转置，而非动态解耦控制

创建 `BASIC_OSC_PD` 后调用 `initialize(base_link_name,ee_link_name)`，名字需要匹配 live nested link actor 的完整名称，且 base 是 EE 的祖先。它沿 parent 链选出控制关节，从整个 articulation 的观测中提取相应列，最后将输出放回完整 DoF 向量，未控制槽位为零。[Initialize/ComputeOutput][osc]说明了这条路径。

末端目标 `ControllerBasicOscPdTarget.root_from_target_ee` 在 articulation root frame；IK target 则在 world frame，二者不能交换。源码先构造 `T_root,EE = inverse(T_world,root) * T_world,EElink * T_EElink,EE`，位置误差为目标减当前，旋转误差来自 `q_target * conjugate(q_current)` 的 rotation vector。Jacobian 的 world 线速度/角速度行分别乘 root-from-world 旋转。

其核心是 `u = Jᵀ[Kp e − Kd J v]`：平移行在前、旋转行在后；目标没有速度字段，阻尼使用当前末端速度。它没有构造 `Λ=(J M⁻¹ Jᵀ)⁻¹`、没有逆动力学补偿，也不求 Jacobian 逆。所谓 operational-space 是控制量所在空间，不能把名称当成完整动态一致 OSC 的证据。源码还可统一缩小位置/姿态误差，并对正 effort limits 用共同缩放因子限幅，而非各分量独立 clip。[参数][osc-header]含各开关及单位。

作用点也必须一致：在同一坐标系内，把速度 Jacobian 从参考点 O 移到 P，有 `J_v(P)=J_v(O)−[p_P−p_O]× J_ω`，不是仅旋转三行。此版本 OSC 对 Jacobian 做坐标旋转，但未根据 `EELinkFromEE.translation` 添加作用点偏移；getter 直接取内部 link 的刚体块，内部状态与 root 原点又有质心偏移。**源码所支持的判断是：不能把非零工具偏置下的该控制器直接当作已核实的任意 TCP 控制器。** 应核对参考点并显式构造匹配的 Jacobian/控制实现；本章未运行偏置误差实验。[观测收集与计算][osc]、[Actor getter][actor]、[关节 Jacobian 构造][jac]是审查入口。

## 6. 隐式 pose tracking 与 transmission 驱动

### pose controller 路径

`MOCHI_ARTICULATED_POSE` 是 Robotics 对 Physics 原生 pose controller 的连接。先设置 params，再 `initialize(remove_existing)`；actor 上只能有一个此类原生 pose controller，替换是显式操作。`compute_output` 要求 `local_to_parent_transforms` 与 `pose_dofs` **恰好提供一项**。前者按 parents 组合，后者长度是非根 DoF 数，配合 `world_from_root` 组成目标；不能把完整 actor pose 在自由根情况下原样交给 `pose_dofs`。[实现][pose]包含尺寸及根类型检查。

`PoseControllerParams.link_pos_tracking/link_rot_tracking/joint_tracking` 是 **link-indexed** 数组，空、单元素广播、或等于 link 数；不是随意长度的 joint-DoF gain 向量。cycle joints 不受此 pose controller 控制。每个 `PoseTrackingParams` 的 stiffness/damping 单位随平移/旋转区分，目标成为约束参与步内求解。

它的 `saturation` 是 **距离/角度**，不是 N/N·m；仅平滑限制弹性项到约 `stiffness*saturation`，阻尼项不受此饱和限制。因此不能把该参数直接宣称总驱动力严格上限。原生[PoseTrackingParams 文档][api] 7445–7557 行与外部 JSC 的 effort saturation 完全不同。

`pose_controller.reset()` 把下一次计算改用 `ResetArticulatedTarget*`，设置当前/旧目标一致以避免目标速度跳变；普通 `SetArticulatedTarget*` 则保留目标随步变化的语义。reset 后应在下一步前送入初始目标，不要混合旧目标和新 episode 状态。它不返回 effort，也不能用于无 live Physics actor 的真实机器人。

### transmission 和 actuator 是不同对象

Physics experimental 的线性 transmission 把选定关节位移映射为一个标量 s：`s = Σ a_i q_i`（相对 rest pose）。系数是 `ds/dq_i`；当 s 是绳长时，revolute 的系数单位 m/rad，prismatic 对应 m/m。能量共轭关系给 `Q_i = (ds/dq_i) F_s`，符号随传动方向，不是简单把同一个力复制到所有 joints。

原生顺序是 `experimental.add_linear_transmission` 或 `add_spatial_tendon` 取得 transmission index，再 `attach_displacement_control_actuator` / `attach_force_control_actuator` / `attach_mc_kibben_actuator`（Python 精确拼写以[生成绑定][experimental-binding]为准），最后用 `set_transmission_actuator_state_variables` 更新相应 state。每种 actuator 的 state 数量需查 `get_num_transmission_actuator_state_variables`，不要套用同一个位置命令。

[参数声明][experimental]区分 displacement 的目标/刚度/阻尼、force 的广义力、McKibben 的压力 Pa 与几何参数。rope-like 默认不允许压缩，`allow_compressive_force` 描述能否双向传力，不是“反转电机”按钮。Robotics prefab 的 linear transmission/spatial tendon 可在构建时接到这条 Physics 路径；它与 Robotics 自定义 `ActuatorBase` 注册体系不同。详细材料/能量装配归 E3/E6，本章先把输入和所属层对齐。

## 7. FK、Jacobian 与独立 IK scene

### FK 读取与离线构型

当前状态的 link world poses 可通过 `get_articulated_link_transforms(out)` 或 nested link 的 `get_root_transform()` 读取。`set_articulated_pose_from_joints` 沿 `UpdateDerivedStateFromPose` 重建 full pose、link transforms 和 Jacobian，因而可以在单独运动学副本上设姿态后读 FK，而无需正时间动力学推进。**不应在受控的 live scene 上反复 set pose 来冒充已执行运动**。[实现][articulated] 143–237 行。

对串联支链，教学关系是 `T_W,L(q)=T_W,root Π T_parent,child(q_j)`。joint axis 所在 frame、joint origin 与 child link offset 决定每一项；这解释了为什么同样 q 在不同导入原点下得到不同末端位置。general closed-loop 的有效构型还要满足闭环约束，不能把任意 joint 向量与单纯树乘积当成已解闭环。

`nested_link.get_articulated_jacobian()` 返回 world frame 的 `6×n` row-major span，translation 三行在前、rotation 三行在后；列是 owning actor 的完整 DoF。它是借用视图，记录时复制；不能按机器人名称隐式丢掉 free base 六列。内部 [UpdateJacobianState][articulated-header]调用[核心 Jacobian][jac]，再由 [Actor getter][actor]截取 link 块。单纯 `reshape(n,6)` 会改变语义。

### IK 确实存在，但不是 live scene 的普通 getter

原生 `physics.experimental.create_ik_solver(ik_scene)` **取得 scene 所有权并修改它**：重力归零、强制单 island、接触摩擦清零、关节摩擦/惯量系数清零。它只接受 articulated/rigid actor。销毁 solver 会销毁其 scene；不要另行 `destroy_scene(ik_scene)`。因此为机器人建独立副本，完成 link handle 查找后再交给 IK，主动力学 scene 保持自己的物理配置。[IK 实现][ik] 33–106 行及[官方 IK+pose 示例][ik-example]。

IK 用 `create_position_target(actor_handle,local_position,target_position,weight)` 和 rotation 对应入口构造软约束。位置目标在 world，局部作用点在 link local；rotation 以旋转向量表示，不能传 xyzw。每个 actor 在 position/rotation target map 中各只有一项，新建会清掉该类旧目标；不能以重复调用在一个 link 上增加任意多个同类独立目标。位置权重对应 N/m，旋转权重 N·m/rad，权重比决定不可同时满足时的取舍。

`solve_ik()` 内部不是固定步长轨迹优化：它调用特殊的 `Scene::Step(infinity)` 做准静态求解，再检查目标 deviation 每分量的最大绝对值是否超过位置/旋转阈值，返回 bool。此内部约定**不改变 E1 对普通动态步长应有限的要求**；IK scene 的时钟不能当作机器人运动时长。非线性 residual tolerance 与位置/旋转阈值是不同验收项。[SolveIK][ik] 215–240 行。

应用必须处理 False、异常、非有限输出及超限目标。True 仅说明这些目标误差通过当前判断，不证明关节限位严格无穿越、无碰撞路径、全局最优或可执行 effort。即使静态终点可达，两点间的运动路径仍需轨迹/规划。把 IK pose 送给 JSC 或隐式 pose target，然后由主 scene 的动力学执行，才区分了几何求解与控制跟踪。

### 限位不是一种统一裁剪

`get_articulated_dof_limits(out)` 给 DoF 限位读数；原生还提供 single-DoF/3D rotation range constraints。先在模型中正确配置，再在目标生成层处理有效范围。连续关节、spherical 旋转区间与 closed-loop 不能全部按逐元素 `clip` 理解。力限额属于驱动输出，位置限位属于构型/约束；两者都可能被一个不正确的 state setter 绕过。约束刚度、阻尼、饱和的实际数值语义将在 E3 展开。

## 8. 控制回调、任务状态机与外部控制集成

Physics `register_pre_step_callback(debug_name,callback,priority)` 和 post 对应入口按优先级小到大顺序在 step 调用线程执行，同优先级相对顺序未指定。要依次采样→计算→单次写入力，应使用不同 priority 或一个明确调度点；callback 不应增删 actor/constraint。[回调契约][api] 13766–13844 行和 [Scene::Step][scene]可对读。`step(0)` 也触发 callback，应显式区分查询刷新与控制推进。

物理步长 h、控制周期 H、传感更新周期和墙钟延迟分别记录。若 H=m h，目标可保持，但 JSC `obsv.dt` 应等于相邻 compute 调用间隔；每个 substep 是否保持 effort、重新计算阻尼或更新隐式目标由所选控制路径决定。外部 ROS/网络控制器应传入带 frame、DoF 名/版本、仿真时间戳和有效期限的命令，在唯一写入点应用；异步线程先复制观测/命令，不并发读写正在步进的 actor。这里是应用集成设计，不声称内核原生提供了 ROS action server 或实时保证。

下面是本仓库原创的任务设计表，**不是 SuperDex 的内建 task/grasp API**，也未执行新的抓取实验。每次状态迁移使用 post-step 的观测并带进入时间；阈值与最大保持时长由未来 DexLab 具体协议提供，不能凭一个演示常数定义成功。

| 应用阶段 | 原生控制输入 | 迁移依据与失败出口 |
|---|---|---|
| 接近 | world 目标经 IK 得到 joint pose，或转 root 目标给 OSC | 位姿误差连续满足要求→闭合；IK失败/超时→失败与撤离策略 |
| 闭合 | 指关节 target 或有限 effort | 注册的接触观测、位置/速度与命令限幅共同判断；仅“关节到位”不等于夹住 |
| 保持 | 保持目标或更新受限 effort | 监测物体相对位姿/速度、接触有效性及持续时间；失去接触/越界→失败 |
| 释放 | 平滑回到张开目标 | 释放条件与物体状态满足→结束；避免位置跳变引发 JSC 目标速度冲击 |
| reset | 同拓扑快照恢复或模型重建；组件 `.reset()` | 同步任务计时器、命令缓冲、controller 历史及查询视图后再开始 |

接触 force query 须预先注册并在有效采样阶段读取，具体种类/方向及“命令 effort≠接触力”由 E3/E4 接续。任务中还应保存原始命令、最终限幅命令、控制器类型/参数、root pose、完整 joint map、阶段切换原因及异常；这些是解释后续结果的元数据，不是新建评分器。

最小[原生 JSC 片段](../examples/command_fixed_base_jsc.py)展示固定基座标量关节的状态采集、控制周期、输出复制、最终 effort 限额和一次性写入；不创建资产，不步进，不运行。它不包含 task framework 或跨引擎接口。

## 9. 带答案的阅读练习

1. **URDF 有 7 个 revolute，free root，共有多少 actor 与 bot DoF？** actor 13，bot 7；根焊死后 actor 7。gain/目标采用哪种长度取决于接口，JSC 以 actor 长度为准，pose controller 的 `pose_dofs` 排除根。
2. **两个控制器分别给关节 0 和 1 调两次 `set_external_forces_on_dofs`？** 第二次替换完整外力集合，关节 0 的上一命令消失。先合成，再单次写入。
3. **模型 effortLimit=0，JSC saturation=-1，会自动禁用关节驱动吗？** 不会。模型只是 metadata，JSC负值无界；应用最终输出必须显式归零。
4. **deadband 使位置误差归零，运动中的关节还受力吗？** 是。JSC damping 独立保留，速度误差仍产生输出。
5. **控制每 20 ms 算一次，物理每 2 ms 步进，obsv.dt 应是多少？** 0.02 s。填 0.002 会把 target finite difference 放大十倍；若实际调用频率变化，应按仿真时间计算真实间隔。
6. **pose stiffness=100 N/m、saturation=0.01 m，总力一定≤1 N吗？** 不能。该饱和只限制弹性项，阻尼项另计；也未包括其他约束和接触。
7. **为什么 OSC 不等于 inverse dynamics？** 源码为 Jacobian 转置乘误差/阻尼，未形成操作空间惯量或重力补偿。名称不能补出不存在的项。
8. **改 `EELinkFromEE.translation` 后可以忽略 Jacobian 吗？** 不可以；作用点变了，需要对应平移行的叉积偏移。当前源码未自动实现这一补偿，须核对/构造一致参考点。
9. **IK 返回 True 就把主机器人 state 直接设成结果？** 那只是 teleport。控制执行应写 target/effort 后推进主 scene，并保留动力学状态、限额和失败逻辑；True也不证明整条无碰撞路径。
10. **为什么不能把 IK solver 建在主 scene？** 它接管并修改重力/摩擦/求解设置，销毁时还销毁 scene；应使用独立副本，IK时间也不是动态运动时间。
11. **把自定义 servo 注册后框架会每步调用 `compute_effort` 吗？** 不会；官方示例声明该方法是应用自己的 API，loop 负责调度，注册契约主要管理生命周期/reset。
12. **只 restore Scene 后为何第二个 episode 的控制首步不同？** Robotics JSC previous target、用户 PI 积分器、任务计时器不一定在 Physics snapshot 中，需同步 reset，并在下一步前设置初始目标。

[验证记录](validation-e2.md)区分源审、语法与未运行项。下一项优先 E3：沿本章的外力、pose tracking 和 transmission 入口解释接触、非线性求解及力观测，避免把驱动命令当成接触结果。E4 继续传感；E5 仍需等待 E4 后才能完成闭环数据专题。

[api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[robot-api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/pybind/stubs/public/superdex_robotics/bots/__init__.pyi
[robot-entry]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/superdex/robotics/__init__.py
[model]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/superdex_robotics.h
[bot-utils]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/utils/bot_utils.cpp
[bot-header]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/utils/bot_utils.h
[jsc]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/controllers/controller_basic_jsc_pd.cpp
[jsc-header]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/controllers/controller_basic_jsc_pd.h
[osc]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/controllers/controller_basic_osc_pd.cpp
[osc-header]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/controllers/controller_basic_osc_pd.h
[pose]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/controllers/controller_mochi_articulated_pose.cpp
[context]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/core/context.cpp
[custom]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/examples/advanced/example_custom_components.py
[jsc-example]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/examples/control/example_jsc_control.py
[ik-example]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/examples/control/example_ik_pose_control.py
[actor]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_actor.cpp
[articulated]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_articulated_body.cpp
[articulated-header]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_articulated_body.h
[jac]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/articulated_body/articulated_body.cpp
[experimental]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/mochi_physics_experimental.h
[experimental-binding]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/src/generated/mochi_physics_pybind_experimental.generated.cpp
[ik]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_ik.cpp
[scene]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp
