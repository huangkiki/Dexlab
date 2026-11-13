# E2 · 从控制输入到机器人运动

本课解释三个不同问题：**向哪个端口发送什么量、这些量怎样变成驱动、机器人目标怎样转为可追踪参考**。先修 [E1 模型与坐标](modeling-state-time.md)、[状态与时间](state-time.md)。后半部分的状态机见[任务接口](task-interfaces.md)。

覆盖 A3 驱动控制、A5 机器人运动学与 IK、A7 任务接口，基线仍为 Drake **1.57.0**，固定官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。C++ 核心与 pydrake 绑定分别核对；本轮没有导入或运行 Drake，也没有控制/抓取实验。示例是阅读用的原生 API，不是已验证机器人驱动或实机方案。[验收边界](evidence/e2-validation.md)

## 1. 四类输入不能互相替代

| 原生入口 | 输入量与排列 | 物理意义/限制 |
|---|---|---|
| `SetPositions` / `SetVelocities` | q / v，按各自维度 | 编辑当前状态；没有驱动机器人从旧状态走到新状态 |
| `get_actuation_input_port()` | `u∈R^nu`，按 actuator `input_start()` | 关节坐标下的力/力矩前馈，不是 motor-side 电流或转速 |
| `get_actuation_input_port(instance)` | 该实例 actuator 索引递增的紧凑向量 | 与全 Plant actuation 输入**相加** |
| `get_desired_state_input_port(instance)` | `[qd;vd]`，各按该实例 actuator 索引递增 | 供已配置的内建 PD 使用；不是任意 q/v 状态 setter |
| `get_applied_generalized_force_input_port()` | `τ_ext∈R^nv`，按广义速度排列 | 直接加入广义力，不等于经过 actuator 的输入 |
| `get_applied_spatial_force_input_port()` | `ExternallyAppliedSpatialForce` 列表 | 指定 body、作用点和 world 表达的空间力 |

转动关节的 u 单位为 N·m，移动关节为 N。Plant 的 actuation 输入和 effort limit 都是关节侧量，**不会再自动乘 actuator gear ratio**。转子惯量/传动比造成的反射惯量与命令单位是两回事。[驱动端口规则](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L535-L565)、[广义力和空间力端口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1169-L1186)

`ExternallyAppliedSpatialForce.body_index` 是刚体身份；`p_BoBq_B` 是 body 原点到作用点、在 body frame 中表达的向量；`F_Bq_W` 则是作用于该点、**在 world 中表达**的 `[力矩;力]`。同一个结构有两个表达系，不能因点坐标用了 B 就把力也按 B 填入。[字段定义](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/externally_applied_spatial_force.h#L10-L21)

### 1.1 从名字到命令位置

导入模型后保留 `ModelInstanceIndex`，用模型实例和关节名确认机器人映射，再检查 actuator 是否存在及它对应哪个 joint。`JointIndex`、`JointActuatorIndex`、`joint.position_start()`、`joint.velocity_start()` 和 `actuator.input_start()` 分别回答不同问题。即使某个两关节示例恰好全为 0/1，也不能将此当作普遍布局。

本课 URDF 只声明关节及其 limit，没有 transmission，随后用 `AddJointActuator` 显式添加驱动器和 20 N·m 限额。固定 URDF Parser 实现先暂存 joint effort，再在解析 transmission 时创建 actuator；不能仅看到 joint 的 effort 字段就认为已有驱动端口对应项。本版本该导入路径只支持 SimpleTransmission，其它类型会告警。[effort 暂存](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/detail_urdf_parser.cc#L591-L595)、[URDF 驱动装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/detail_urdf_parser.cc#L927-L1004)

全模型驱动映射是

$$\tau_u=B u,\qquad B\in\mathbb R^{n_v\times n_u}.$$

`MakeActuationMatrix()` 描述 u 到广义力的映射；对于欠驱动/浮动基座，不能因为有 B 就假定存在任意目标力的可实现逆映射。按模型实例填充全局 u 时可用 `SetActuationInArray`；读取反向子集可用 `GetActuationFromArray`。不要按 `q` 的 slice 去填 u。[映射与索引](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L4754-L4774)、[actuator 输入位置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint_actuator.h#L141-L157)

### 1.2 FixValue、Connect 与控制循环

`DiagramBuilder.Connect` 描述系统间的信号依赖；`InputPort.FixValue(context, value)` 在特定 Context 中固定输入值。**FixValue 可以覆盖已连接的上游源**，并复制传入向量；之后改变原 NumPy 数组不会自动更新端口。调试时遗留一个 FixValue，可能让新控制器接好了却始终不起作用。[FixValue 的覆盖与复制合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/input_port.h#L111-L150)

外部程序按周期提交命令时，要使用 Plant 对应子 Context，处理仿真时间、输入保持和读取阶段；不能以 Python `sleep` 决定物理控制周期。原生 Systems 图可以用 `LeafSystem` 的周期事件保存控制器状态，用输出端口供 Plant 求值。输出计算可能按需重复发生，不能把“输出计算被调用一次”当成“控制时间前进一步”。任务页给出实际的事件接口。

## 2. PD、限额和实际驱动

### 2.1 内建 PD 与外部 PD 的计算边界

内建 PD 的公开表达为

$$\tilde u=K_p(q_d-q)+K_d(v_d-v)+u_{ff},\qquad u=\operatorname{clip}(\tilde u,-e,e).$$

比例项 Kp：转动关节用 N·m/rad，移动关节用 N/m；微分项 Kd：对应 N·m·s/rad 或 N·s/m。这里 kd 乘的是速度误差，不是“误差差分后又除一次 dt”的任意替代。所有这些单位是力/力矩 PD 的单位；下面 inverse-dynamics controller 的加速度反馈增益单位不同。

通过 `JointActuator.set_controller_gains(PdControllerGains(...))` 配置非负有限增益，二者都为零会移除内建 controller。其公开合同承诺离散 Plant 的用法，本课只采用该模式；不要把内部出现连续净驱动函数或一段可编译配置当成其它模式已获运行验证。[增益与适用模式合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint_actuator.h#L291-L310)、[设置增益实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint_actuator.cc#L32-L42)

desired-state 端口包含所有 actuator 的 qd/vd；只使用启用 PD 且关节未锁定的条目。**desired-state 未连接会 disarm 该模型实例的内建 PD**；actuation 未连接按零前馈处理。锁定关节也会使其 PD 不起作用。配置了增益、`has_controller()` 为真，仍不证明此刻 PD 已在执行。[端口与 disarm 规则](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L603-L653)、[desired-state 排列](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1120-L1138)

外部 `PidController` 则是单独的 System，它读 estimated-state 和 desired-state 并输出控制量；带积分状态，允许状态/输出投影。基本构造器要求受控 q/v 和目标 q/v 均各有相同数量分量，不能把含四元数的整个浮动基座状态直接喂进朴素关节 PID。[PID 方程和维度](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/pid_controller.h#L18-L70)

Plant 内建 PD 在 SAP 路径中作为约束项与一步动力学联合处理；外部 PD 经端口提供某时刻算好的 u。这两者在有限 h、高增益、有饱和时一般不等价。不能把同一组 kp/kd 搬过去就声称同样闭环响应。[离散 PD 装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L720-L765)

### 2.2 限额应用在哪里

源码先收集各模型实例的 actuation，再加全模型 actuation；不是后者覆盖前者。限额路径按 actuator.input_start 逐项 clip。SAP 中启用 PD 的条目将**反馈加前馈的总表达式**交给带 effort limit 的约束处理，不能先夹住前馈就认为等效。例：e=5 N·m，反馈为 −8、前馈为 +10，总和是 +2；若先把前馈夹成 +5 再相加，会错误地得到 −3。[输入装配和限额](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L2937-L3001)、[SAP 前馈与总限额](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L724-L761)

`get_net_actuation_output_port` 是 actuator 的总驱动输出，不是接触力、手指夹持力，也不是任意外部广义力。SAP 从求解结果恢复 PD 对应驱动；无 PD 项以 effort-limited 输入为基线。读取时还要遵守 E1 的 sampled/live 区分。[SAP 净驱动读回](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L1206-L1255)

外部 `Saturation` 可显式限制控制器送出的信号，也可使用比模型 actuator limit 更紧的命令预算；它是逐元素硬限幅和 direct feedthrough。它不会自动给外部 PID 提供 anti-windup：若积分误差一直累积，解除饱和后的响应仍可能过冲。Ki 非零时需设计积分保持/回算等实际策略，重置时也要重置 controller Context，不能只重置 Plant。[Saturation 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/saturation.h#L10-L33)、[PID 积分状态入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/pid_controller.h#L148-L159)

### 2.3 三个周期和初始保持值

设 Plant h=1 ms、命令更新 H=5 ms、任务阶段更新 T=10 ms，它们分别定义动力学更新、控制信号保持、任务决策。H/h 是整数有助于说明，但不自动消除更新顺序、延迟和采样阶段问题。任务层根据上一次观察产生新参考，再由低层控制计算驱动，必须知道每一级何时可见。

`ZeroOrderHold(H, size)` 将端口值锁存在离散 State，中间时间输出不变；它的默认初值为零，offset=0 时首次周期更新在 t=0，Initialize 后仍可能先看到初值，第一步起点才采样输入。本例不实际运行，课程用该规则提醒：**建立连接不代表初始命令已经锁存**。[ZOH 状态与初始事件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.h#L24-L64)

若把 ZOH 放在 PID 输出之后，它保持的是驱动力；PID 的输入和其积分状态仍按原 System 语义演化。若只保持目标 qd/vd，则控制器仍可能持续重算驱动力。这两种拓扑不等价。示例 Ki=0，明确采用“PID → Saturation → ZOH → actuation”，没有声称 PID 变成离散积分器。

## 3. 机器人运动学：先对齐 frame，再看数值

### 3.1 FK、末端点和工具偏置

`CalcRelativeTransform(context, frame_A, frame_B)` 给出 `X_AB(q)`。工具末端可能不在 link 的 body 原点：需要 `FixedOffsetFrame` 或显式 `p_BoT_B`。`CalcPointsPositions` 计算 B 上固定点在 A 中的坐标，适合同时传多个点；不要用末端 link 的 body pose 代替实际 TCP pose。[相对位姿](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3970-L3985)、[固定点位置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L4025-L4059)

本课原创模型是两个长度 L1=L2=1 m 的平面转动杆，基座焊在 world，关节绕 +z，零角度两杆沿 +x，末端点在第二杆原点的 +x 方向 1 m。只对这个布局，有

$$p_x=L_1\cos q_1+L_2\cos(q_1+q_2),\quad p_y=L_1\sin q_1+L_2\sin(q_1+q_2).$$

q=(π/4,−π/2) 时几何推导得到 TCP=(√2,0,0) m；这是用于源码阅读的解析预期，**没有执行 Drake 来验证它**。如果忘记 TCP 偏置，得到的是 elbow/link2 原点，差一个完整杆长。

### 3.2 Jacobian 必须注明对什么速度求导

`CalcJacobianSpatialVelocity(..., JacobianWrtVariable.kV, frame_B, p_BoBp_B, frame_A, frame_E)` 返回 `6×nv` 的 J，满足 `V_ABp_E=Jv`，前 3 行角速度、后 3 行线速度。选择 `kQDot` 时返回 `6×nq`；两种雅可比通过 `q̇=N(q)v` 关联，不能仅因 shape 恰巧相同就忽略变量含义。`CalcJacobianTranslationalVelocity` 给多个点的 `3p×nv` 或 `3p×nq` Jacobian。[完整参数合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L4869-L4923)、[平移 Jacobian](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L5002-L5059)

对上述两杆且 v=q̇，二维平移 Jacobian 为

$$J=\begin{bmatrix}-L_1\sin q_1-L_2\sin(q_1+q_2)&-L_2\sin(q_1+q_2)\\L_1\cos q_1+L_2\cos(q_1+q_2)&L_2\cos(q_1+q_2)\end{bmatrix}.$$

`det J=L1 L2 sin(q2)`，伸直/折叠时奇异。因此 `J⁻¹` 不存在或条件很差；即使使用伪逆，也不能保证速度限额、位置限额或障碍约束。J 的转动关节列是米/弧度，乘 rad/s 才得到 m/s。六维空间速度同时包含 rad/s 和 m/s，优化代价中的旋转/平移权重需要明确尺度，不能将六项盲目当成同一量纲。

## 4. 位置 IK 是约束优化，不是动态控制

### 4.1 从 q 变量到约束

`InverseKinematics` 以整 Plant 的广义位置 q 为决策变量。构造时加入模型支持的运动学约束、关节限位和单位四元数等；`with_joint_limits=False` 只移除相应关节限位约束，不等于清掉一切模型约束。需要对一个子集做 IK 时，在专用 Context 中锁定其它关节并使用接收 Context 的构造入口。[IK 构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h#L12-L87)、[实际装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.cc#L25-L74)

| 约束/代价 | 含义 | 不能据此保证 |
|---|---|---|
| `AddPositionConstraint(B,p_BQ,A,lower,upper)` | B 上固定点 Q 在 A 中落入三维盒，单位 m | 末端姿态、路径无碰撞、动态可达 |
| `AddOrientationConstraint(...)` | 两指定 frame 的相对角度不超过 θ，单位 rad | 角速度/加速度或关节驱动力满足限额 |
| `AddMinimumDistanceLowerBoundConstraint` | 当前配置的候选几何对有最小 signed distance | 整条插值轨迹无碰撞、所有被过滤几何都被检查 |
| `AddQuadraticErrorCost(W,q_nominal,q)` | 偏好某个姿态/分支；权重应与变量尺度相符 | 必然全局最优或必然求到可行解 |

姿态角度约束可写为 `trace(R_AB) ≥ 1+2cos θ_bound`；它约束相对旋转角，不是对 roll/pitch/yaw 三项各做独立上下界。[位置参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h#L89-L108)、[姿态公式](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h#L153-L183)、[距离候选与前置条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h#L286-L302)

闭链并不意味着 IK 可以忽略模型约束：本版本的装配入口列出 coupler、distance、ball、weld 等；无限刚度 distance 可成为硬运动学约束，有限刚度的弹簧距离不会作为同样硬约束加入。存在不支持的注册约束时会抛错。需要逐个查看模型实际进入了哪些约束，不把“优化器返回一个 q”当作模型等价性证明。[模型约束装配合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/add_multibody_plant_constraints.h#L12-L34)

关节位置、速度、加速度和 effort 限额属于不同空间：分别对应 nq、nv、nv 和 actuator 输入。`GetPositionLowerLimits` 等 getter 返回模型元数据，不会替任意外部参考生成器做时间参数化或自动限幅。规划时应显式加入实际需要的约束，控制时检查参考变化率与可实现驱动力；E1 已说明连续 Plant 的位置限位仿真限制。[限位读取维度](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L5965-L6007)

### 4.2 Context、碰撞查询和结果验收

使用无 Context 的 IK 构造器时，它自己创建 Plant Context，该入口不支持碰撞相关约束。需要碰撞约束时，必须让 Plant 与 SceneGraph 在 Diagram 中连接，并传对应 Diagram 的 Plant 子 Context。IK 过程会修改这个 Context；本课先克隆根 Context，再从克隆取 Plant 子 Context，保留根对象生命周期，避免规划线程污染控制现场。[Context 与碰撞前置条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h#L30-L87)

非线性 IK 依赖初值、约束一致性和优化器能力。只在 `result.is_success()` 为真并重新检查目标/限位/距离残差后，才考虑使用 `GetSolution(ik.q())`；失败时返回的数值不应发给机器人。多初值可能找到不同肘部构型，但不能因此宣称全局穷举成功。对真实运行，还要生成满足速度/加速度/驱动力约束的连续参考并闭环追踪；直接 SetPositions 是编辑状态。[结果接口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program_result.h#L78-L91)、[变量解与约束诊断](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program_result.h#L179-L202)

本课例子只构造 IK 问题，不调用 Solve。它没有碰撞几何，也没有添加距离约束，不能表述成避障 IK；SceneGraph 的存在不自动添加障碍约束。

### 4.3 微分 IK 和 inverse dynamics 是两个后续环节

经典 `DoDifferentialInverseKinematics` 寻找下一速度 v，使 `Jv=αV_desired`，`0≤α≤1`，同时满足下一配置近似、速度、加速度和附加线性速度约束。其一步配置预测使用 `q_next≈q+N(q)v·dt`；dt 是优化合同的一部分，控制周期改变而 dt 没改会改变限位预测的物理含义。结果状态包括 solution found、no solution、stuck；小 α 表示无法按所需速度方向充分前进，不应默默当成任务成功。[优化结构与状态](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/differential_inverse_kinematics.h#L298-L345)、[stuck 阈值](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/differential_inverse_kinematics.h#L222-L228)

本版本还提供 `DifferentialInverseKinematicsSystem`：原生端口接收全模型位置、nominal posture 和目标 frame 的姿态或速度，输出 active dofs 的速度；它是无状态系统，需要按已知固定周期求值。该类明确要求 **v=q̇**，两个笛卡尔目标端口不能同时连接；不能把它的接口和经典函数的 N(q) 支持混写成同一个保证。其可选约束按实际构造配方添加。[Systems 形式及限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/differential_inverse_kinematics_system.h#L22-L96)

`InverseDynamicsController` 更靠近驱动层：PID 先构造期望广义加速度，再经 inverse dynamics 转成广义力和 actuation。对满足假设的模型，

$$a_{cmd}=\ddot q_d+K_p(q_d-q)+K_d(v_d-v)+K_i\int(q_d-q)dt,$$
$$\tau_{id}=M(q)a_{cmd}+C(q,v)v-\tau_g-\tau_{force\ elements},\quad u=B^{-1}\tau_{id}.$$

这里 M 是质量矩阵，Cv 是科氏/陀螺偏置项，τg 是重力广义力；最后一项指另列的阻尼、弹簧等模型力，不应再重复减一次重力。InverseDynamics 的计算本身不考虑 actuator effort limit，输出仍需按实际控制合同处理限额；补偿公式不是力矩可行性证明。

这里 Kp 的单位是 s⁻²，Kd 是 s⁻¹，Ki 是 s⁻³；不要照搬 torque-PD 的数值解释。本类要求完全驱动、nq=nv、无浮动基座，不为受约束 Plant 设计，也不考虑约束反力。控制模型与仿真模型的质量/阻尼等参数不一致时，补偿会有偏差；构造时传入的 model Context 会被复制，不会自动追踪之后的随机化参数。[控制器假设](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/inverse_dynamics_controller.h#L21-L61)、[参数 Context 生命周期](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/inverse_dynamics_controller.h#L73-L103)、[力项与重力补偿](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/inverse_dynamics.h#L20-L47)

## 5. 最小例子与带答案练习

- [arm_kinematics.py](../examples/arm_kinematics.py)：原创两杆 URDF、显式基座焊接和 actuator、FK/TCP Jacobian、独立 Context 中的 IK 问题。没有 Solve 或步进。
- [sampled_pd.py](../examples/sampled_pd.py)：明确关节/actuator 排列，搭建原生 PID → 限幅 → 保持 → Plant 的控制图；没有执行控制回路。
- [task_sequencer.py](../examples/task_sequencer.py)：周期事件维护任务 State，下一页解释每个 guard 的数据合同。

1. 同一 actuator 在实例端口给 3 N·m，全 Plant 端口给 4 N·m，effort limit 为 5，且没有内建 PD。原始输入和限额后的输入各是多少？
2. 为什么 gear ratio=100 不能令 actuation 输入 1 自然变成关节侧 100 N·m？
3. 内建 PD 已配置增益，但 desired-state 端口未连接，控制器是否一定在工作？
4. 两杆完全伸直时，为什么任意二维 TCP 速度不一定能用有限关节速度实现？
5. 为什么规划用 Context 不能直接借正在控制的 Context 给 IK 修改？
6. 把 ZOH 从驱动力输出移到参考 qd/vd，控制频率语义是否不变？
7. 静态 IK 可行，是否足以证明带质量、力限额和接触的机器人能完成该运动？

<details>
<summary>答案</summary>

1. 原始和为 7，限额路径为 5。两端口相加而非覆盖；此结论以题设无内建 PD 和指定限额路径为前提。
2. Plant 命令已经按 joint coordinates 解释；传动比影响反射惯量等建模量，不二次换算 actuation 单位。
3. 不一定。该实例的内建 PD 被 disarm；未接前馈则零。has_controller 只说明配置存在。
4. det J=L1L2 sin(q2)=0，列向量相关。伪逆不能凭空增加缺失的瞬时运动方向，也不会自动满足驱动限额。
5. IK 会修改该 Context 的状态并使用其查询环境；规划和执行需要独立状态副本与明确的结果接收时刻。
6. 不同。前者保持力，后者保持目标但仍允许低层反馈持续变化；积分状态和事件顺序也要单独分析。
7. 不能。静态姿态约束不包含整条路径、速度/加速度、驱动力和接触动力学；需相应轨迹和控制验收，实验后续复用 DexLab。

</details>

继续：[接近、闭合、保持、释放的任务接口](task-interfaces.md)。完整接触参数、力观测和 SAP 数值推导仍由 E3 交付。
