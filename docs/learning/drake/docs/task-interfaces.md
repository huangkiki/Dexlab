# E2 · 任务状态如何进入 Drake 控制图

先读[驱动与机器人](control-robotics.md)。本页将接近、闭合、保持、释放表达为原生 `LeafSystem` 的离散状态与事件。目标是讲清接口与时序；示例没有执行、没有机器人接触结果，所有阈值只是教学占位值，不是 DexLab 的协议或抓取成功标准。

## 1. 任务、参考、驱动与物理观测分层

一个任务状态机负责“现在应该做什么”；轨迹/参考模块负责“用什么连续目标去做”；控制器负责把误差变成 actuation；Plant 才负责动力学。每层需要输出对应的时间和 frame 语义。

```text
目标/任务阶段 → 轨迹或参考 qd, vd → 控制器 → 有限额的 actuation → Plant
      ↑                 ↑                 ↑                         │
      └────────── 带时间与有效性标记的状态/传感观测 ────────────────────┘
```

将 IK 的 q 直接 SetPositions 不会验证轨迹或控制；将夹爪位置目标称作“夹持力”也不成立；任务到达 Hold 阶段不意味着已证实物体稳定。本轮可以完整定义这些接口，实验数据最终复用 DexLab，保留其版本、对象、坐标、采样与判定边界。

外部 ROS/硬件/策略进程接入时至少显式处理：关节名称到本 Plant 的状态/actuator 映射、SI 单位、时间戳及 clock domain、参考有效期、失联/乱序策略、命令限额与接收确认。Plant 无法从一个等长 NumPy 向量识别关节顺序错了。不要把网络线程到达消息的次数当成仿真步数；适配层在确定事件边界接收/锁存数据，运行状态进入 Context，而不是放在多个线程共享的可变变量里。

## 2. 用事件改 State，用输出计算读 State

`LeafSystem.DeclareDiscreteState` 声明状态组；`DeclarePeriodicDiscreteUpdateEvent(period_sec, offset_sec, update)` 声明周期更新，回调读旧 Context 并写传入的 next-state 容器；`DeclareVectorOutputPort` 描述输出求值。输出计算应是从当前 Context 得出结果，不能顺便推进阶段、计数或执行外部命令，因为 Eval 可能重复发生，也可能被缓存省略。[离散状态声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L1029-L1048)、[事件合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L319-L354)

若输出仅依赖离散 State，应声明相应 `prerequisites_of_calc`，如 `{self.all_state_ticket()}`；默认会保守认为所有输入都直接影响输出，可能让原本延迟闭环被判成代数环。不能为了过检查随便删掉输入依赖；只有计算确实不读取输入时，才能声明只有状态依赖。[direct feedthrough 与依赖声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L1190-L1224)

Python 周期更新签名为 `(context, discrete_state)`；本例返回 `EventStatus.Succeeded()`，通过 `discrete_state.set_value(...)` 写下一状态。`EventStatus.Succeeded()` 只表示这次框架更新成功写入，任务本身仍可进入 Fault；不能把该返回值当作抓取成功。Python 绑定保存回调生命周期，但不会替回调保证量纲、传感新鲜度或任务逻辑。[Python 回调入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L992-L1003)、[下一状态写入](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L1249-L1274)

任务计时使用 `context.get_time()`，进入阶段的时刻和稳定持续时间也保存为离散 State。这样 Clone/复位整棵 Context 才包含任务进度；若只把 `self.phase` 存在 Python 对象上，多 Context 共用同一 System 时会互相污染。重置 Plant 不会自动重置任务、PID 积分器或 ZOH，参见 [E1 的恢复范围](state-time.md)。

## 3. 一个可审查的接近—闭合—保持—释放合同

[task_sequencer.py](../examples/task_sequencer.py) 定义六个阶段：Approach、Close、Hold、Release、Done、Fault。State 包含阶段编号、进入时刻、稳定起始时刻和夹爪宽度参考。输入与输出是课程明确约定的数值，不是假定 Drake 自带统一的“grasp”传感器。

| 输入字段 | 单位 / 含义 | 必须满足的来源合同 |
|---|---|---|
| approach_error | m，接近目标的非负位置误差范数 | 明确 TCP/目标 frame；由 FK/感知产生 |
| aperture | m，定义好的两指间距 | 多关节夹爪需显式做几何映射，不能直接当作单关节 q |
| normal_force | N，约定为非负的闭合相关法向力观测 | 来源/符号/采样窗口在 E3/E4 核实，不使用 actuator torque 冒充 |
| slip_speed | m/s，物体相对指定接触/夹爪 frame 的速度标量 | 不是 world 中物体平移速度的任意替代 |
| sample_time | s，与当前 Context 同一仿真时钟 | 若来自硬件 wall-clock，先做明确同步/映射 |
| abort | 0 或 1，外部取消请求 | 约定 1 为请求终止任务推进 |

该示例把六项看作同一组有效观测，使用 `0≤now−sample_time≤0.02 s` 检查新鲜度；未来多速率传感不能借用同一个 timestamp 隐藏通道间不同采样。所有值需有限，误差/间距/法向力非负，abort 必须为 0/1。既不允许 NaN 穿过 guard，也不将未来时间戳当成新数据。

| 阶段 | 输出参考的含义 | 离开阶段的 guard | 失败/滞回安排 |
|---|---|---|---|
| Approach | 夹爪保持打开；机械臂由独立参考模块接近 | approach_error≤5 mm | 当前阶段超过 3 s 转 Fault |
| Close | 发出较小间距参考 | normal_force≥2 N 且 aperture>1 mm | 这里只表示闭合观测条件满足，不是抓取成功 |
| Hold | 保持闭合参考 | normal_force≥2 N 且 \|slip_speed\|≤1 mm/s 连续 1 s | 任一条件中断则重置稳定计时；3 s 超时转 Fault |
| Release | 发出打开参考 | aperture≥70 mm 且 normal_force≤0.1 N | 不用“打开命令已经发送”代替释放观测 |
| Done | 保持打开参考，不自动重启 | 外部显式重置 | 只表示本状态机走完，不构成独立评分 |
| Fault | 保留最后参考并报告 Fault | 外部处理或显式重置 | 低层降级/制动/释放策略必须由具体应用定义 |

示例还有教学用 normal_force>20 N 的 Fault 条件；这是为了展示异常 guard，不是任何夹爪的安全载荷结论。Fault **没有通用安全动作**：继续保持、断扭矩或释放可能各有风险，课程不猜测硬件策略。实际接口应把 Fault 明确传给负责低层处置的系统，并对过期的输出参考设置有效期；不能把这个例子直接接到实机。

同一时刻只允许一次阶段跳转，避免一帧数据同时满足 Close/Hold/Release 时直接穿过多阶段。Hold 使用持续时间过滤瞬时抖动；更复杂系统可按真实传感噪声加入不同进入/退出阈值，但不能为得到成功结果临时放宽标准。

## 4. 计划、采样和闭环交付

### 4.1 把路径点变成原生参考信号

静态 IK 只给 q。对本课固定基座两转动关节，`v=q̇`，可以用 `PiecewisePolynomial` 把已经检查的关节路径点和时间点组成连续轨迹；`TrajectorySource(..., output_derivative_order=1)` 按当前 Context 时间输出 `[q_d;q̇_d]`，正好对应本例 PID 的 `[q_d;v_d]`。它不是通用浮动基座转换器，含四元数时仍需正确的 N(q) 映射。[三次轨迹的端点导数与连续性](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.h#L318-L352)、[TrajectorySource 输出合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.h#L17-L61)

下面是可替换 `sampled_pd.py` 中常值参考的独立阅读片段：两关节从 `[0,0]` rad 在 2 s 内到 `[0.4,−0.6]` rad，起止速度为零。没有执行这个函数，也没有验证其驱动力可行性。

```python
import numpy as np
from pydrake.systems.primitives import TrajectorySource
from pydrake.trajectories import PiecewisePolynomial


def make_joint_reference():
    trajectory = PiecewisePolynomial.CubicWithContinuousSecondDerivatives(
        breaks=[0.0, 2.0],
        samples=[[0.0, 0.4], [0.0, -0.6]],  # Columns are joint waypoints.
        sample_dot_at_start=np.zeros((2, 1)),
        sample_dot_at_end=np.zeros((2, 1)),
    )
    return TrajectorySource(
        trajectory, output_derivative_order=1,
        zero_derivatives_beyond_limits=True,
    )
```

由 `builder.AddSystem(make_joint_reference())` 加入图，再把其 `get_output_port()` 连到 PID desired-state。矩阵每列是一组关节位置，不能把两个时间点误当两个关节。[Python 三次轨迹重载](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/trajectories_py.cc#L646-L666)、[TrajectorySource Python 构造参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L721-L727)

时间点使用 **Context 的绝对仿真时间**；若在 t=5 s 才开始 Approach，不能照搬 `[0,2]` 期待它自动从阶段起点计时。`zero_derivatives_beyond_limits=True` 只把区间外的导数输出归零，位置值仍交给轨迹本身的 `value(t)` 规则；它不是通用的整向量饱和器。`UpdateTrajectory` 修改的是 System 内保存的轨迹，不能把它当成某个 Context 的私有重规划状态；多个 Context 共用 System 时尤其要区分两者。[时间、输出排列与区间外处理](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.cc#L149-L198)、[轨迹的所有权](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.h#L60-L79)

三次插值的光滑性不会保证速度、加速度、力矩或碰撞约束。需要检查整段轨迹的极值与几何路径，必要时重新规划/拉长时长；只检查两端的 IK 可行性不足。初始机器人状态也要与参考起点一致或有受控过渡，不能用一次瞬时 SetPositions 掩盖起始误差。

### 4.2 多速率交付

任务事件 T=10 ms、控制信号保持 H=5 ms、Plant h=1 ms 是示例的三个独立约定。若任务和控制在同一时刻更新，不能按 Python callback 注册顺序假设新任务命令立即被另一事件消费；同阶段更新通常读取更新前的 Context，再应用更新结果。明确允许一个控制周期延迟，或通过系统设计/事件阶段组织所需顺序，不靠“多 Eval 一次”改变物理时序。[Simulator 更新顺序](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L149-L192)

将状态机连接到机器人还需要完成三个明确映射，而不是引入跨引擎框架：

1. **arm reference**：Approach 阶段的目标 TCP → 合适 IK/轨迹 → qd/vd；检查 IK 成功、限位和路径约束后，在约定的控制事件接收参考。
2. **gripper reference**：物理间距目标 → 夹爪原生关节目标或力目标；考虑平行夹爪的半宽/总宽、传动结构、符号与 actuator 顺序。
3. **observation**：原生状态/传感器 → 上表带单位/时间的观测；force/slip 的定义与采样阶段在 E3/E4 落实后，才能当作真实闭环 guard。

本例输出 `[width_target_m, phase_code]`，故它只给夹爪参考与任务阶段，不产生 arm trajectory，不伪造接触传感，也不提供完整抓取系统。A7 的交付是状态、接口、时序、异常和原生实现方法；实际 DexLab 案例整合在 E7，新的抓取实验不在本轮范围。

保存日志时建议并排保留 request（任务/目标）、command（送入驱动端口）、net actuation（原生读回）和 observation（物理量）以及各自 timestamp/phase。它们常常不同，不能用一条“action 成功发送”日志证明物理目标达到。模型、规划和控制版本要能关联；旧版限额或采样配置不能从当前默认值补写。

## 5. 阅读练习与答案

1. 为什么输出 callback 里 `self.phase += 1` 不是合格的任务推进实现？
2. 正在闭合时收到 normal_force=3 N、sample_time 比 now 晚 0.1 s，是否应进入 Hold？
3. 指令宽度 30 mm，是否能直接发 `q_d=0.03` 到所有夹爪？
4. Hold 需要连续 1 s 稳定，中途一帧 slip 超限，为什么不能继续沿用旧 stable_since？
5. 整个任务保存在 Python 属性中，而只 Clone Context，会发生什么恢复缺口？
6. Fault 输出维持上次宽度目标是否可以直接称为“安全停机”？
7. `TrajectorySource` 的导数区间外归零选项，是否同时保证参考位置保持在任意给定的位置限位内？

<details>
<summary>答案</summary>

1. Eval 由依赖求值和缓存驱动，调用次数不是物理时间；多次查询可能改变任务，缓存又可能跳过更新。应在有明确周期的状态更新事件写下一 State。
2. 不应。时间戳未来且不满足输入合同，应走 Fault/异常策略，而不是把“超过力阈值”当成足够条件。
3. 不能。0.03 m 是两指总间距；有的模型用每指位移、角度、连杆或耦合坐标，必须按原生运动学映射。
4. 连续稳定条件已中断。重置计时后，下一段稳定才重新累计；否则短暂稳定片段会被错误拼成连续保持。
5. Python 状态不在 Context 树中，不会随其克隆/重置，多个 Context 也可能共享它；恢复后的任务阶段与机器人状态可能不一致。
6. 不能。它只是此教学状态机停止改变参考的策略；低层执行器仍可能施力，具体应用必须定义并验证降级处置。
7. 不保证。该选项只控制导数输出；位置由轨迹的求值规则决定，轨迹区间内外的位置限位都应按实际轨迹检查。

</details>

下一步：[E3 接触、求解器与力观测](roadmap.md)。E2 的来源/语法/模型静态核验见[验证记录](evidence/e2-validation.md)；未运行项保持公开。
