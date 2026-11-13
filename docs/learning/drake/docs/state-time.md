# E1 · 状态、Context 与时间

先读[建模与坐标](modeling-state-time.md)。本页继续使用 Drake 1.57.0 固定源码；所有例子未执行，仅做源码/语法核对。目标是回答“这份数值属于哪个系统、哪个 Context、哪个时刻、哪个采样阶段”。

## 1. Context 是状态容器，也是依赖图的一部分

一个 Diagram 的 Context 树与它的子系统树一一对应。根 Context 包含整个图的子 Context；Plant API 通常要求 **Plant 自己的 Context**，不能把根 Context 或另一棵不兼容系统的 Context 直接传进去。[一一对应关系](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.h#L28-L39)

```python
# 阅读片段；没有在本阶段执行。diagram 和 plant 来自同一次构建。
def locate_plant_context(diagram, plant):
    root_context = diagram.CreateDefaultContext()
    plant_context = plant.GetMyMutableContextFromRoot(root_context)
    return root_context, plant_context
```

同一 Context 树的时间必须一致，`SetTime` 只能在根 Context 上调用。[时间 setter 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L327-L333)

`root_context` 应一直存活；`plant_context` 是其中的子 Context。不要对图中的 Plant 单独 `CreateDefaultContext()`，再误以为它会保留原 Diagram 的 SceneGraph/控制器连接：新独立 Context 不具备原根 Context 中的连接求值环境。只做独立 Plant 运算时可按其输入要求创建单独 Context；两种用途应显式区分。[子 Context 访问](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.h#L1026-L1065)

Context 不只有一个浮点状态数组。它保存时间、连续/离散/abstract state、参数、accuracy、fixed input values 和缓存依赖。离散 Plant 默认还可能有动力学输出的抽样状态，因此 `GetPositionsAndVelocities` 返回的 `[q;v]` 并不是整个 Diagram 的完整状态。控制器积分器、滤波器和数据保持器也各有自己的 Context。[Context 值](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L44-L60)、[抽样状态](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L416-L477)

Simulator 的常用 C++ 构造入口持有 System 引用、拥有兼容 Context；System 生命周期应长于 Simulator。Python 绑定有自己的生命周期管理，仍建议保留 `diagram`、`plant`、`simulator` 的明确变量，不把 System、Context、Simulator 当成一个“环境对象”。[Simulator 所有权](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L255-L275)

## 2. q、v、q̇ 和索引映射

对光滑连续多体系统，配置和速度之间是

$$\dot q=N(q)v,\qquad M(q)\dot v+C(q,v)v=\tau.$$

这里 `q∈R^{nq}` 是配置参数，实际受配置约束；`v∈R^{nv}` 是广义速度，广义力 `τ` 与它配对，功率为 `τᵀv`。`N(q)` 是 `nq×nv` 的运动学映射；`M(q)` 是整个模型的广义质量矩阵，不是单刚体的 6×6 空间惯量。该表达只是连续动力学结构，不能当成离散接触更新算法；完整力项、约束和求解过程在 E3。[原生方程](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L382-L406)

| 关节/模型假设 | nq | nv | 位置与速度的含义 |
|---|---|---|---|
| weld | 0 | 0 | 固定相对位姿，不分配运动自由度 |
| 单转动关节 | 1 | 1 | 角度 rad、角速度 rad/s |
| 单移动关节 | 1 | 1 | 位移 m、速度 m/s |
| quaternion floating joint | 7 | 6 | q 为 wxyz + 平移；v 为角速度 + 线速度 |
| 浮动基座 + k 个独立单自由度关节 | 7+k | 6+k | 此计数假设无额外坐标、未改变基座参数化/拓扑 |

Quaternion floating joint 的 v 是 parent joint frame F 中测量、也在 F 中表达的 `[ω_FM_F; v_FMo_F]`。默认浮动基座的 F 对应 world，此时两部分都在 world 中表达；这不表示任意自由关节的 parent 都是 world。旋转的四元数有 4 项，但角速度只有 3 项，因此通常不能用 `(q_next-q)/h` 直接代替 `v`。请用 `MapVelocityToQDot` / `MapQDotToVelocity` 并尊重有效配置和维度。[浮动关节布局与 frame](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/quaternion_floating_joint.h#L20-L33)、[速度表达系](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/quaternion_floating_joint.h#L162-L184)、[速度映射](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L4528-L4581)

### 2.1 关节编号不是状态切片起点

先从 `GetJointByName(name, model_instance)` 找到关节，再在 Finalize 后查询 `position_start()/num_positions()` 与 `velocity_start()/num_velocities()`。两种 start 分别位于**全 Plant 的 q**和**全 Plant 的 v**，不是 `[q;v]` 中同一个偏移，也不是按实例抽取数组中的偏移。`JointIndex` 是身份索引，不能替代它们。[关节的状态偏移](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint.h#L219-L257)

```python
# 只演示地址映射；返回副本以便保存。尚未执行。
def read_joint_state(plant, plant_context, joint):
    q = plant.GetPositions(plant_context)
    v = plant.GetVelocities(plant_context)
    iq, iv = joint.position_start(), joint.velocity_start()
    qj = q[iq:iq + joint.num_positions()].copy()
    vj = v[iv:iv + joint.num_velocities()].copy()
    return qj, vj
```

若只关注某个机器人，用 `GetPositions(context, model_instance)`、`GetVelocities(...)` 获取该实例的紧凑数组，或用 `GetPositionsFromArray` 等进行原生映射；不要假定一组模型实例在全局数组中总是你猜想的连续切片。多实例共享 Plant 不等于批量隔离的多个世界。[实例访问](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3084-L3123)

### 2.2 Python getter 的别名不等于快照

固定绑定源码特意区分：`GetPositions(context)` / `GetVelocities(context)` 对 POD 标量路径返回现有数据引用；带 `model_instance` 的重载返回拷贝。AutoDiff/symbolic 等标量的转换策略不能由 double 路径推断。作为日志或前后对照数据，统一显式 `.copy()`，避免后来修改 Context 时“旧读数”跟着改变。[绑定中的引用与拷贝](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L595-L632)

修改状态优先使用 `SetPositions`、`SetVelocities`、`SetPositionsAndVelocities` 或关节自己的 setter。对借出的可变存储长期持有引用、绕过 setter 再写入，会使缓存依赖的失效通知难以保证。修改也不代表施加了力：把 q 从 A 设到 B 是初值/状态编辑，不是机器人走过该轨迹。[Context 变更与缓存通知](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L230-L283)

### 2.3 不能把 SetFreeBodyPose 一律叫作设置世界位姿

1.57.0 的 `SetFreeBodyPose(context, body, X_JpJc)` 对任意 free body 设置 **child joint frame 相对 parent joint frame 的位姿**。只有浮动基座的相应 frame 就是 world/body 时，它才是 `X_WB`。child frame 还可能偏离 body frame；仅改变量名字不会完成变换。同样，`SetFreeBodySpatialVelocity` 的输入也有对应 frame/点语义。[公开 API 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3733-L3794)

若确实要设置浮动基座的世界位姿，用名称更明确的 `SetFloatingBaseBodyPoseInWorldFrame`，并先核实 `HasUniqueFloatingBaseBody` 等条件。对一般关节，按 parent/child frame 关系换算相对位姿。内部实现仍有名为 `X_WB` 的局部参数，但会把它的旋转/平移直接传给该 body 的 mobilizer；不能仅凭内部变量名覆盖公开 API 的合同。[世界位姿入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3673-L3704)、[实现追踪](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/multibody_tree.cc#L1373-L1409)

## 3. 重置与快照：先列出要恢复的东西

| 操作 | 实际范围 | 不应推断的效果 |
|---|---|---|
| `SetPositions/SetVelocities` | 当前 Plant Context 的 q/v | 不重置控制器、抽样输出、时钟或全部参数 |
| `SetDefaultPositions` | 改变系统之后分配/重置状态所用的默认 q | 不立即修改既有 Context |
| `System.SetDefaultState` | 按该系统默认规则设置 State | 不等于重置 time、parameters、fixed inputs |
| `System.SetDefaultContext` | 本版本实现先重置 parameters，再重置 State | **不重置时间、accuracy 或 fixed inputs** |
| `CreateDefaultContext` | 为该系统分配并初始化新的 Context | 单独 Plant 的新 Context 不含原 Diagram 环境 |
| 根 `Context.Clone()` | 克隆整棵 Context 及其中按存储类型定义复制的值 | 不克隆 System、Simulator 或外部进程 |
| `CloneState()` | 只复制 State | 不包含时间、参数、固定输入和全套缓存/依赖 |
| `SetStateAndParametersFrom(src)` | 复制状态/参数，可用于子 Context；通知依赖变化 | 不复制时间/accuracy/fixed inputs |
| 根 `SetTimeStateAndParametersFrom(src)` | 另加时间/accuracy，要求根 Context | 本版本仍不复制 fixed inputs |

直接查看 [`System::SetDefaultContext` 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.cc#L99-L127)，避免按函数名想象“全部复位”。默认 q 的后续作用见 [SetDefaultPositions](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3182-L3206)；复制 API 的排除项见 [Context 复制合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L425-L461)和 [Clone 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L704-L712)。

对课程中的纯内存 Diagram，最清晰的独立初值副本是根 `snapshot = root_context.Clone()`，然后从 snapshot 重新取 Plant 子 Context。不要对已有子 Context 调用 Clone 来幻想得到整个图；该方法要求根 Context。若把快照值复制回现有根 Context，另行恢复 fixed inputs，检查初始化事件，再处理 Simulator 的运行状态。

“Context 深拷贝”也不是操作系统级 checkpoint：自定义 abstract value 按其类型的复制/Clone 语义复制；自定义类型内部的共享外部资源不会自动变成独立设备、网络连接或文件。Drake 的 `Value<T>` 要求 T 可复制或可克隆，但不替作者设计 T 的资源独立性。外部 Python 控制器变量、随机数发生器、日志游标、渲染器/硬件状态须另行纳入恢复协议。[Value 复制规则](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/value.h#L192-L200)、[存储策略](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/value.h#L618-L655)

Simulator 自身的积分器配置、统计与数值过程不是 Context.Clone 的对象。未来恢复运行时，应明确建立新 Simulator 还是复用旧对象，并记录配置；不能仅因 q/v 一样就承诺逐位相同的后续轨迹。**改了时间后必须重新 `Initialize()`**，这样才会重建时间事件安排；Initialize 默认还会触发初始化更新和发布，可能改变初始状态或产生外部输出。它不是无副作用的“清缓存”。需要抑制初始化事件时，调用者承担初始状态正确性的责任。[Initialize 行为](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L296-L339)

## 4. 缓存：何时重算，何时根本不属于缓存问题

Drake 通过依赖关系判断 `Eval` 的结果是否仍有效。改变 q 可能使位置运动学以及依赖它的量过期；安全 setter 发出通知，后续 Eval 按需更新。无需把“每次读取前手工刷新全部缓存”作为常规用法，也不能把曾经返回的借用引用当成永远固定的记录。[失效传播机制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L230-L283)

但是离散 Plant 默认的 dynamics 输出保存的是**抽样 State**，它不是“该失效但未失效的普通缓存”。设置 q 后 body pose 会改变，而 contact-results output 仍可能反映上次离散更新。盲目关闭 cache 无法把这样的语义改成实时输出。应先确认端口是否 sampled，再确认安全写入、输入来源和读取的 Context；最后才诊断缓存依赖是否有问题。下一节展开这个区别。

## 5. 四种时间尺度不要合并成 dt

| 量 | 控制什么 | 不控制什么 |
|---|---|---|
| `MultibodyPlant(time_step=h)` | h=0 选连续模型；h>0 选周期更新的离散模型 | 不是渲染帧率或 wall-clock sleep |
| Simulator 积分器的最大步长/accuracy | 连续状态的数值积分限制与误差控制 | 不改离散 Plant 的 h 或 SAP 配置 |
| `AdvanceTo(t_end)` | 推进到不超过给定的绝对仿真时刻，可能因事件提前结束 | 参数不是“再走这么多秒”或“只走一步” |
| 控制/观测/发布周期 | 由相应系统事件、输入信号或外部调用协议决定 | 不会因改了 viewer 刷新率自动同步 |

本版本 **C++ 和 Python 的 `MultibodyPlant` 构造器都要求显式 `time_step`**；`MultibodyPlantConfig.time_step` 才有默认 0.001 s。不要把旧示例中的缺省行为写成当前构造规则。例子始终显式给出 `time_step=0.001`，它只是教学配置，不代表推荐值或 DexLab 实测配置。[C++ 构造器](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1379-L1392)、[Python 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L206-L210)、[Config 默认](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant_config.h#L30-L39)

对连续 Plant，Simulator 的数值积分器计算连续状态变化；对离散 Plant，Plant 的事件更新自身状态，Simulator 调度这些事件。如果 Diagram 还含连续控制器，即使 Plant 离散，整个图仍是混合系统，积分器仍会处理那部分连续状态。因此“换 Simulator 积分器”不等于“换掉离散接触算法”。[模型与积分关系](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L372-L406)、[混合系统推进](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L149-L192)

积分器 target accuracy 服务于其支持的连续局部误差估计，不是最终位置误差的统一上界，也不是接触求解器残差阈值。`set_fixed_step_mode(True)` 也可能因事件边界缩短一步；模型离散步长、积分步长、内部 solver 迭代次数是三种不同概念。减小 h 不自动证明稳定、接触准确或参数合理；完整数值与接触假设在 E3 按算法展开。[accuracy 条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/integrator_base.h#L213-L234)、[fixed-step 与事件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/integrator_base.h#L320-L350)

一个具体能力边界：本版本连续 Plant 的仿真忽略关节限位并给出警告，不能因 URDF 写了 lower/upper 就声称连续仿真会执行限位。控制/优化使用的限位与动力学执行规则还需分别核对。[连续模式限位警告](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1380-L1389)

## 6. 采样时刻：当前 pose 和输出 force 可能不是同一阶段

离散 Plant 默认保存上次更新时计算的动力学样本 s。按源码的抽象记号：

$$s_{n+1}=g(t_n,x_n,u_n),\quad x_{n+1}=f(t_n,x_n,u_n),$$
$$y^{dynamic}_{n+1}=g_d(s_{n+1}),\quad y^{kinematic}_{n+1}=g_k(x_{n+1}).$$

这表明更新后的 Context 可同时含新的运动状态和用于该更新的旧阶段动力学样本。抽样状态初始没有有效样本；别把初始化前读取的动力学端口当成已经计算好的接触观测。端口合同的细节与后续力解释在 E3 继续核实。[离散状态与输出方程](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L416-L477)

| 读取方式 | 默认离散 Plant 的语义 |
|---|---|
| `state`、`body_poses`、`body_spatial_velocities` 输出 | live：当前 Context 中的 q/v |
| `generalized_acceleration`、`body_spatial_accelerations`、`net_actuation`、`reaction_forces`、`contact_results` 输出 | sampled：最近一步记录的动力学样本 |
| Plant 直接 `Calc...` / `Eval...` 方法 | 按当前时间、状态、输入计算；不使用上述输出采样状态 |
| 连续 Plant 的 dynamics 输出 | live，随当前状态/输入改变 |

可在 Finalize 前对离散 Plant `SetUseSampledOutputPorts(False)`，使 dynamics 输出也按当前输入/状态重算，代价是可能重复计算、改变 direct-feedthrough 关系并移除抽样状态。另一个入口 `ExecuteForcedEvents()` 会强制动力学更新，**连位置也可能改变**；它不是只读刷新函数。本阶段没有执行这些操作。[采样选项与 API 区别](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L480-L533)、[Finalize 前置条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1400-L1406)

还要区分事件的左右极限。同一个标量时刻 t 可以有更新前 `x⁻(t)` 和更新后 `x⁺(t)`。Simulator 的一步先处理起点更新，再积分到下个事件/目标边界并发布；在 `AdvanceTo(t)` 的终点可能还有该时刻待处理的离散/abstract update。`AdvancePendingEvents()` 在时间不前进的情况下处理这些 pending updates。它会改变状态，并可能触发发布/monitor；不要作为每次读取后的习惯调用。[事件顺序](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L149-L192)、[边界时刻与 pending events](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L369-L405)

未来做日志时，每项记录至少标明：仿真时间、模型/配置版本、状态所在 Context、更新前/后阶段、端口 sampled/live、坐标/参考点/单位。一个共享 timestamp 不能单独证明 pose 与 force 同步。本阶段只定义语义，实验与跨引擎对照后续引用 DexLab 的原协议。

## 7. 阅读练习与源码追踪

1. 一个默认四元数浮动基座带 6 个单转动关节，nq/nv 各是多少？在 `[q;v]` 中，关节的 `velocity_start()` 应怎样使用？
2. `old_q = plant.GetPositions(context)` 后修改 q，为什么 old_q 不一定保存旧值？如何写成明确快照？
3. 对 t=3 s 的 Context 调用 `SetDefaultContext`，是否会回到 t=0？fixed input 是否复位？从实现逐项回答。
4. 克隆根 Context 后，Python 函数闭包里的随机数发生器是否自然成为独立副本？积分器参数呢？
5. 离散 Plant 的 q 刚被 setter 改过，body pose 改了、contact-results output 没改。能否据此断定缓存出错？
6. `AdvanceTo(0.1)` 之后 `AdvanceTo(0.1)` 是否必然什么都不发生？说明 pending events 的影响。
7. h=1 ms 的离散 Plant 连接连续控制器；将 Simulator 积分器最大步长改为 0.2 ms，是否改变了 Plant 的接触更新周期？
8. 为一般 free body 调用 `SetFreeBodyPose(..., X_WB)`，为什么即使维度匹配也可能错误？指出应查的两个 joint frame。

<details>
<summary>答案与推理</summary>

1. nq=13、nv=12。velocity_start 是 v 的偏移；在 `[q;v]` 中应加 nq。更直接地先用 GetVelocities 拿 v，再按 velocity_start 切片；勿把相同偏移用于按实例压缩过的 v。
2. 固定绑定的 double 全 Plant getter 是引用路径。用 `old_q = plant.GetPositions(context).copy()`；此副本仍只是 q，不是完整 Context 快照。
3. 不会。该版本实现重置参数与 State，没有 SetTime，也没有重建 fixed inputs。需要显式的时间和输入恢复策略；若将修改后的 Context 用于已有 Simulator，改时间之后必须 Initialize。
4. 不会。闭包的外部资源和 Simulator 都不在 Context 树里；自定义 abstract value 的资源独立性取决于它的复制合同。Context 克隆不提供完整进程回放保证。
5. 不能。默认 dynamics 输出读取抽样 State，运动学输出读取当前 q/v。先核实 sampled/live，再检查 Context 与输入；清 cache 不能改变抽样语义。
6. 不必然。相同时间可处理上一次终点留待处理的更新事件，也可能发布和调用 monitor；时间不变不代表状态或外部输出不变。
7. 不改变。Plant 仍按 h 周期离散更新；更小积分步长用于连续部分和事件调度，不是替换 Plant 的离散算法。
8. 公开合同是 `X_JpJc`；Jp 不一定等于 world，Jc 不一定等于 body。需要从建模 frame 关系换算，或在确为 floating base 时使用显式世界位姿入口。

</details>

建议的源码追踪顺序：`Parser` → `Finalize` → `joint.position_start/velocity_start` → Plant 状态 setter → Context 失效通知 → `Simulator::Initialize/AdvanceTo` → Plant 的 sampled output 说明。此链解释建模/状态/时间；完整碰撞、约束装配、SAP 求解和力回写见已交付的[E3](contact-solvers.md)。返回[课程目录](curriculum.md)或[验证记录](evidence/e1-validation.md)。
