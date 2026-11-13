# E1 · 状态、所有权、快照与一步时间

本篇基于 **MuJoCo 3.15.0 原生 C 核心与官方 Python 绑定**，固定提交 `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`。先修为[建模与坐标](modeling-and-frames.md)、线性代数和基本微分方程；覆盖 A2，以及 B0/B4 的状态与积分基础。目标是解释“谁拥有状态、数组代表什么、何时才是新观测、怎样恢复”，不是通过跑通脚本证明物理模型正确。

[原创阅读片段](../examples/modeling-state-time/README.md)未执行；本轮不运行物理实验、基准或训练。接触目标函数、求解器推导和完整力观测已在 [E3](dynamics-and-pipeline.md)展开，GPU 后端支持差异留给 E5/E6。

## 1. 配置空间与速度空间不是同一个数组

令 $q$ 为配置，$v$ 为广义速度。铰链/滑轨上可以把 $v$ 看作标量配置的时间导数；自由或球关节用四元数存姿态时，$q$ 的存储维度大于 $v$ 的维度。单位四元数属于 $S^3$，并以 $Q$ 与 $-Q$ 的二重覆盖表示 $SO(3)$；不能把旋转群直接认成四维欧氏空间。

| joint 类型 | `qpos` 分量数 | `qvel` 分量数 | 语义 |
|---|---:|---:|---|
| slide | 1 | 1 | 沿关节轴的位移 m、速度 m/s |
| hinge | 1 | 1 | 关节角 rad、角速度 rad/s |
| ball | 4 | 3 | 相对参考姿态的单位四元数、局部旋转切空间速度 |
| free | 7 | 6 | body 世界位置 3 + 世界姿态四元数 4；世界平移速度 3 + body 局部角速度 3 |

free 的角速度与平移速度甚至不在同一表达轴系。源码中平移直接加到世界位置；旋转则右乘由局部角速度产生的增量四元数。这个表描述 free joint 的 **qvel**，不是任何六维空间向量的通用布局。[配置积分实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L693)、[局部四元数增量](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_util_spatial.c#L232)。

模型中的 `njnt` 是 joint 个数，`nq` 是 qpos 标量数，`nv` 是速度/广义力维度。3.15.0 还单列 `nactuator` 与 `nu`：前者是 actuator 数，后者是 ctrl 标量数；多维 actuator 下二者不必相等。`na` 是 activation state 数，不能从 nu 推出。[模型尺寸定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L242)。

使用名字找到 joint ID，再查 `jnt_qposadr[jid]` 与 `jnt_dofadr[jid]`。Python 的 `data.joint(name).qpos/qvel` 按 joint 类型给出对应长度视图。不能用 `qpos[jid]` 代表某关节位置，也不能把 qpos 地址拿去索引 qvel。编译/重编译后重新绑定名称与地址。[地址字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L412)、[Python 命名访问](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L368)。

### 配置的差分和积分

`mj_differentiatePos(model, out_v, dt, q1, q2)` 从两个 nq 维配置得到 nv 维平均切空间速度。`mj_integratePos(model, q, v, dt)` 原位更新 q；它根据**给定速度**计算配置增量，并不求动力学、更新 data.time 或保证碰撞/关节约束成立。四元数在旋转流形上处理，别写 `qpos += dt * qvel`。[差分与积分函数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L659)。

差分时 dt 必须非零，两个配置必须来自同一模型/编译坐标定义；有限姿态差得到的是对应增量的角速度表示，不等同于恢复中间真实轨迹。接近 180° 的旋转差还存在表示分支问题。优化中“沿切向扰动配置”与“施力让系统运动”是两种不同操作。

## 2. 从动力学方程到数组

对于本版本传统连续时间路径，写成

$$M(q)\dot v+c(q,v)=\tau_{\mathrm{passive}}+\tau_{\mathrm{actuator}}+\tau_{\mathrm{applied}}+J(q)^Tf.$$

$M$ 是 nv × nv 广义惯量，不是把每个 body 的三个主惯量拼成对角阵；关节耦合、质量分布和配置都会参与。$c$ 包含偏置力，$f$ 属于活跃约束空间，$J^Tf$ 才能与 nv 维广义力相加。$J$ 的列数是 nv，不是 nq。标量关节上功率为 $\tau^Tv$，但混合平移和旋转的广义向量每个分量有各自量纲，不能把其欧氏范数不加单位解释为“总力”。[计算章节的尺寸与运动方程](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L202)。

| 字段 | 尺寸 | 身份与注意点 |
|---|---|---|
| `qpos` / `qvel` | nq / nv | 配置/速度输入 |
| `act` / `act_dot` | na / na | 动态 actuator 的内部状态/导数；不是 ctrl 的副本 |
| `ctrl` | nu | 持续存在的控制输入；单位由 actuator 定义 |
| `qfrc_applied` | nv | 用户额外广义力；不自动在每步清零 |
| `xfrc_applied` | nbody × 6 | 用户施加于 body 质心、世界轴表达的 force:torque 输入；不同于 objectVelocity 的 rot:lin |
| `qacc` | nv | 前向结果；`discrete` 下语义变为速度差除以步长 |
| `qfrc_bias` / `qfrc_passive` / `qfrc_actuator` / `qfrc_constraint` | nv | 动力学阶段产生的不同广义量 |
| `history` | nhistory | 含时间戳的延迟控制/传感样本；3.15 的物理状态组成 |
| `sensordata` | nsensordata | 传感输出，各传感器更新阶段不同 |

`xfrc_applied` 的前 3 项作为 force、后 3 项作为 torque，作用点使用 `xipos`；这是 [mj_xfrcAccumulate](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L497) 调用 `mj_applyFT` 的实际顺序，不能套用其他六维量的顺序。

这一课不把 `ctrl` 解释成统一力矩，也不展开约束求解近似；E2 追踪 transmission/gain/bias/activation，E3 追踪 $J,f$、接触与求解器。刚体字段表不覆盖所有 flex/IPC 状态。[状态定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L258)。

### 六维空间量要同时注明顺序、原点和轴系

`mj_objectVelocity(..., objtype, id, out, flg_local)` 输出顺序是 **角速度在前、线速度在后**，与 free qvel 的平移在前不同。`flg_local=0` 使用世界轴，1 使用对象轴。原点由 objtype 决定：`mjOBJ_BODY` 用质心 `xipos`，局部轴用惯性主轴 `ximat`；`mjOBJ_XBODY` 用 body 原点 `xpos`，局部轴用 body `xmat`。geom/site 类似地用各自原点与轴。BODY 与 XBODY 的数值 ID 对应同一个 body，但选出的参考 frame 不同。[API 声明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L632)、[实际 frame 选择](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L835)。

原点从 A 改到 B 时，线速度按 $v_B=v_A+\omega\times(p_B-p_A)$ 转换；只旋转六个数不能完成参考点变换。`cvel` 的原点是树的质心参考，不能直接当 body 原点速度。本版本 `simulation.rst` 末尾声称该函数把平移放在旋转之前，与 API 的 rot:lin 声明及实际实现不一致，本课以 API 声明与函数实际分支为依据，记录为上游文档冲突而非悄悄统一说法。

## 3. 数据所有权：视图、副本与可变模型

Python 数组通常直接暴露 C 内存。`sample = data.qpos` 和 `data.qpos[3:7]` 是视图；`mj_step` 或状态写入后，旧变量看到的内容也会改变。日志要使用 `.copy()`，并将时间戳和阶段作为同一条采样元数据。`data.body(name).xpos` 同样是视图，不因按名字取出就变成快照。[绑定的零拷贝语义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L244)。

一个 model 可以配多份 data；每份 data 有独立状态/缓冲，但 model 的参数是共同的。多个工作线程各用 data，并将共享 model 视为只读；如果运行时改质量、选项或模型常量，就必须重新考虑同步与实例隔离。绑定在执行 C 函数时释放 GIL，不会因此保护同一 data 的并发写操作。[线程组织说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L570)、[GIL 边界](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L299)。

状态修改不会触发完整的自动依赖更新。直接写 qpos/qvel 后，通常调用 `mj_forward` 得到当前完整前向派生量；只需运动学可用更窄的原生函数，但必须满足对应前置阶段。`mj_forwardSkip` 是“这些阶段已有效”的承诺，不是“请引擎智能判断哪些值变了”。没有核对依赖时跳过位置阶段会继续使用陈旧碰撞、Jacobian 和惯量。

## 4. reset、keyframe 和快照三种需求

### 从模型参考配置重置

`mj_resetData` 不等于对整个对象 `memset(0)`：qpos 来自 `model.qpos0`，mocap pose 来自模型 body pose，`eq_active` 来自 `eq_active0`；四元数姿态不能清成全零。qvel、act、施加外力等按重置逻辑初始化。3.15 还初始化 history 的负时间样本与缓冲元数据；`mj_resetCtrl` 对四元数控制写单位四元数，其他控制写零。[reset 实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1391)、[中性控制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1653)。

因此，旧文档“除 mocap 外所有输入默认零”的概述不能直接推广到本版本。重置后读取派生量前执行所需前向计算；若控制回调依赖外部积分器/滤波器，应用还需重置这些外部状态。MuJoCo 不知道你的 episode 计数、Python RNG、控制器积累误差和日志缓冲。

`mj_resetDataKeyframe` 先重置，再在 key ID 有效时覆盖 time、qpos、qvel、act、mocap pose、ctrl。它不是所有 data 字段的序列化文件；无效 key ID 的实现会保留普通 reset 结果，不应把这一行为当作拼错名称的容错策略。[keyframe 重置字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1680)。

### 保存用于继续演算的输入

状态 mask 是 bitfield，由 `mj_stateSize` 计算长度，`mj_getState` 复制到平坦数组，`mj_setState` 按同一 mask 恢复。不要自己假设 qpos、qvel 在 C 内存中紧邻；不同数组可能有对齐填充。

| mask | 3.15.0 实际组成 | 尚未包含 |
|---|---|---|
| `mjSTATE_PHYSICS` | qpos、qvel、act、history | time、ctrl、外力、plugin 等 |
| `mjSTATE_FULLPHYSICS` | PHYSICS + time + plugin_state | 用户输入、warmstart |
| `mjSTATE_USER` | ctrl、两种外力、eq_active、mocap pose、userdata | 物理状态、warmstart |
| `mjSTATE_INTEGRATION` | FULLPHYSICS + USER + qacc_warmstart | 完整派生缓冲、sleep 潜在状态、IPC 额外状态、外部程序状态 |

以枚举定义为准，不能复用旧版本 bit 数值。[mjtState 的确切组合](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h#L507)。`mj_setState` 只复制指定字段，不会替你运行前向计算；恢复后重新计算需要的派生量。[setState 实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L282)。

在无 sleep、无 IPC 等额外状态的普通模型中，完整 integration 输入加相同模型/算法/控制逻辑支持复现后续计算。warmstart 虽不是机械状态，却会影响有限容差、有限迭代下的数值路径。不能用两个状态 qpos/qvel 一致就断言逐位轨迹一致；还要冻结模型、版本、精度、输入、回调与外部随机状态。

### 紧凑快照的两个重要边界

1. **Sleeping：** 休眠岛把其派生位置/速度量当作潜在状态缓存。只保存 `tree_asleep` 或 integration mask 不足以完全保存休眠仿真；官方要求完整 `mj_copyData` 才能恢复这一语义。紧凑状态重建仍可用，但会隐式唤醒休眠岛。sleep 还改变阶段读取依赖，RK4 不支持该功能。[sleep 的快照与阶段限制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L1386)。
2. **IPC flex：** `flexvert_lambda/flexvert_conage` 在源码中标为跨步状态，却不在 `mjtState` 中；因此 `INTEGRATION` 不能被宣传成覆盖全部 3.15 模式的完整 checkpoint。IPC、插件外部资源与回调状态须另查生命周期，E6 展开。不在本例中启用它们，也不声称已验证 IPC 重放。[IPC 状态字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L249)。

保存 checkpoint 至少附模型/资产校验值、核心/绑定版本、mask、积分和 solver 设置、步长、外部控制/RNG 状态、采样阶段。没有这些信息的数组只是数据，不是可复现承诺。

## 5. forward、step 与观测的时间标签

`mj_forward` 在当前输入上计算派生量及动力学，不负责完整时间推进；但是它会执行控制回调、传感器/插件等计算，有外部副作用时不能当成任意次数的纯函数。`mj_step` 先做状态检查和 forward，再按 integrator 分派，最后推进状态。[源码主入口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L2017)。

以下时间表用于普通单步积分路径；RK4 有内部多次评估，discrete/IPC 的加速度语义另述，sleep 可保留部分旧派生量。

| 调用点 | qpos/qvel/time | 位置/速度/力派生量 | 合理的日志标签 |
|---|---|---|---|
| 写入 qpos 后、尚未 forward | 用户新输入 | 可能对应旧配置 | 不把派生量标为新状态 |
| `mj_forward` 返回 | 输入时刻 t | 本次前向评估对应当前输入 | `phase=forward, time=t` |
| `mj_step1` 返回 | 仍为 t | 位置/速度阶段已计算；本步新控制引起的力尚未完成 | `phase=pre_control, time=t` |
| `mj_step2` 或 `mj_step` 返回 | 通常为 t+h | 部分派生量仍来自本次积分前或内部阶段 | 标明 `phase=post_step`，不要假定全部是 t+h |
| 对 post-step 状态再 `mj_forward` | t+h | 在新状态上重新评估 | `phase=forward_at_new_state`，注意回调额外执行 |

如果只要新状态的 body/site pose，可在满足前置条件下重新做运动学；若要同步读取完整传感和力，需选择并记录完整前向计算时点。不能给上一阶段 contact/force 随手贴上新的 data.time；也不能用额外 forward 得到的“新状态力”替代刚才那一步实际使用的力。

`mj_step1` 更新到位置/速度阶段，允许随后写 ctrl 与外力；`mj_step2` 做执行器、加速度、约束和积分。在这一间隙改 qpos/qvel 会使前半段结果失效。sleep 开启时位置阶段还会读速度/外力用于唤醒判断，不能将分阶段接口理解成绝对独立的两块。[step1/step2 实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L2070)。

**RK4 特别容易误用：** 3.15 的 `mj_step2` 遇到 RK4 设置会调用 Euler。需要 RK4 内部阶段重新计算反馈时，使用 `mj_step` 与合适的控制回调；回调可能每个物理步被调用多次，不能每次都把外部计数当作跨过一个 h。该差异直接来自分支，不能靠 XML 写了 `integrator="RK4"` 就断言实际执行 RK4。[实际分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L2125)。

## 6. 物理步长、控制周期与墙钟

`model.opt.timestep=h` 是单次物理步的模拟时间增量；通常一步完成后 data.time 增加 h。solver 的迭代次数不是物理子步，RK4 的内部评估也不是多次外部控制周期。Python `mj_step(model,data,nstep=k)` 只是重复 k 次原生 mj_step，以减少 Python 边界开销，并非让一次积分精度自动提高为高阶。[Python nstep](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L304)。

例如教学设定 h=0.002 s，控制周期为 5h=0.01 s，则名义物理频率 500 Hz、控制频率 100 Hz。保持同一 ctrl 五步是零阶保持；每步重新计算反馈或回调是另一种控制系统。渲染可以每若干步执行，墙钟是否跟得上不改变 h 的单位。`sleep()` 只控制程序等待，不能作为推进物理时间的方法。

下面仅是**未执行**的循环片段，假设 `model/data` 已建立、一个标量 motor 位于 ctrl[0]、无控制回调、无 sleep/IPC、采用普通单步积分；E2 才推导控制律与限幅。

```python
# Source-reviewed loop, not executed in this repository phase.
for control_tick in range(10):
    data.ctrl[0] = 0.0  # a motor input here, not a universal actuator meaning
    for physics_tick in range(5):
        mujoco.mj_step(model, data)
    state_sample = (float(data.time), data.qpos.copy(), data.qvel.copy())
```

这里只采输入状态数组，未声称派生力/传感值同步。若发生数值异常，默认 autoreset 可能重置状态，data.time 未必继续单调增加；诊断要读取 warning/日志并记录 reset 事件，而不是忽略它继续计算“成功时长”。[autoreset 选项](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L649)。

## 7. 积分器解决哪个问题

solver 在给定配置/速度与输入下解力/加速度或离散步问题；integrator 决定沿时间更新状态的方法。`Newton` 是约束求解算法名称，`implicitfast` 是积分器，`iterations/tolerance` 控制代数求解，h 控制时间离散。更多 solver 迭代不能消除一个过大 h 引入的离散误差。

为说明一阶方法，暂限无四元数的局部坐标、平滑力与有限有效惯量。半隐式 Euler 为

$$v^+=v+h\,a(q,v),\qquad q^+=q+h\,v^+.$$

四元数情形把第二个加法换成配置流形上的 integratePos。MuJoCo 的 `Euler` 默认还对关节 damping 做隐式处理，不能简单当作所有项完全显式的课堂 Euler。

对速度依赖力做一次线性化，令 $D=-\partial(\tau-c)/\partial v$（本式没有约束力导数），有

$$(M+hD)(v^+-v)=hM a(q,v).$$

这解释为什么“隐式”可能来自求解一个修正惯量系统，而非执行许多更小的物理步。若阅读旧来源采用 $D=+\partial(\tau-c)/\partial v$，相应写作 $M-hD$；符号约定必须和定义一起保留。[本版本积分推导](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L492)。

| integrator | 本版本关键语义 | 不能推出的结论 |
|---|---|---|
| `Euler` | 半隐式更新；默认隐式关节 damping，可由 eulerdamp flag 关闭 | 不是所有力的后向 Euler |
| `implicit` | 速度线性化，忽略约束力导数，限制导数稀疏模式 | 不是对所有位置/速度/接触非线性求完全隐式解 |
| `implicitfast` | 简化 RNE 导数并对称化；独立自由体另有局部 gyroscopic 处理 | 不是去掉一切旋转效应；与 implicit 不普遍等价 |
| `RK4` | 固定步长、多次内部动力学评估的四阶方法 | 高阶阶数依赖平滑假设，不能保证刚性接触/大阻尼最稳定 |
| `discrete` | 约束与隐式速度/位置更新在有效 metric 中联合求解，`qacc=(v⁺−v)/h` | 不再遵循普通路径的连续瞬时加速度解释 |

`discrete` 以正阻尼/刚度约定构造 $\widehat M=M+hD+h^2K$，但并非所有导数都无条件进入该矩阵。PGS 下 tendon/actuator metric 项被排除；flex 与 PGS/noslip 等组合有错误或限制；sleep 需 islands，sleep+flex 不支持。Newton 与某些插值 flex 的兼容性也有限。这里建立阅读边界，E3 详细追踪 metric/约束，E6 追踪 IPC；不能直接把这个新分支套入历史 DexLab 的 Euler 实验。[五种积分器与限制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L632)。

精度与稳定性不是同义词：隐式方法可能稳定却有数值耗散，刚度引入更短时间尺度，碰撞切换破坏平滑假设。缩小 h、收紧迭代容差、改变接触正则化分别影响不同误差。没有同工况数值证据，本课不推荐“某配置必定更准”，也不把语法检查当稳定性评测。

可微性也不是“数组可求导”就结束：有限差分的 transition 导数依赖同一状态、步长和求解路径；接触切换处可能不光滑，sleep 下官方有限差分导数接口不支持。原生 C、MJX 和其他后端的导数能力要分开记录，E5/E6 再展开实现。

## 8. 常见错误的最短诊断路径

| 表现/错误写法 | 先检查 | 正确理解 |
|---|---|---|
| `qpos[jid]` 得到不相关的数 | `jnt_qposadr`、joint 类型 | ID 不是数组地址 |
| 历史位置列表最后全一样 | 是否 `.copy()` | 日志保存了活动内存视图 |
| reset 后四元数为零 | 是否手动全数组清零 | 应由原生 reset 恢复合法参考配置 |
| 改 qpos 后画面/位置不变 | 派生量是否重新计算 | qpos 写入不自动更新 xpos |
| 恢复 qpos/qvel 后轨迹不同 | ctrl/history/warmstart/模型/外部状态 | 紧凑状态选择不完整或版本/逻辑不同 |
| 六维速度互换或质心有偏差 | 顺序、BODY/XBODY、local flag | 轴旋转与原点变换是不同操作 |
| 配置 RK4，分步行为像 Euler | step2 的分支 | 分步 API 改变实际积分方法 |
| solver 迭代增加仍不稳定 | h、力的刚度、单位、模型条件 | 代数收敛不等于时间积分稳定 |

## 9. 阅读练习与答案

**练习 1：** 一个 free、一个 ball、两个 hinge 的模型 nq/nv 各多少？为何 Jacobian 有 nv 列？

答案：nq=7+4+2=13，nv=6+3+2=11。Jacobian 映射速度切空间到 Cartesian 速度，列对应自由度而非四元数四个存储分量。

**练习 2：** 为何保存 `mjSTATE_FULLPHYSICS` 仍可能不能复现下一步？

答案：它没有 ctrl、用户外力、eq_active、mocap/userdata 与 warmstart；外部控制器、随机数及 sleep/IPC 额外状态也不由该 mask 完整表达。先定义恢复目标，再选 mask 或完整 data，不能只看名字中的 full。

**练习 3：** 对 frames.xml 的 free body，qvel 的最后三项与 `mj_objectVelocity(... BODY ..., 0)` 的前三项是否总相同？

答案：不总相同。两者均涉及角速度，但 qvel 在 body 局部轴，objectVelocity 的 flag=0 在世界轴。质心和 body 原点偏移不会改变刚体角速度，却会改变对应线速度。

**练习 4：** `mj_step` 后记录 `(data.time, data.site('tip').xpos)`，为什么时间标签可能不准确？

答案：time/qpos 已推进，site_xpos 可能还来自积分前或内部评估。明确采样阶段；如需新时刻 pose 则重算相关运动学，并在日志复制数组。额外 forward 可能调用控制回调，不能无视其副作用。

**练习 5：** h=1 ms、控制每 10 步更新，solver 迭代上限 100。模拟 1 s 名义上有多少物理步和控制更新？

答案：1000 步、100 次控制更新（不计初始化及额外回调，假设无 reset/步长变化）。100 次 solver 迭代上限不能乘入模拟时长；实际迭代还可提前终止。

**练习 6：** 在 `discrete` 下两个相同状态、不同 h 得到不同 qacc，能否直接判定核心错误？

答案：不能。该分支的 qacc 是一步速度差除以 h，求解 metric 和约束离散化都依赖 h；它不保证同一状态下与连续路径的瞬时加速度相同。

E1 的完成范围是这些基础契约。现可继续读 [E2 驱动与机器人接口](actuation-and-control.md)，以及 [E3 接触/约束求解、力和积分推导](dynamics-and-pipeline.md)。验收边界与本版本上游文档冲突见 [E1 验证记录](validation/e1.md)。
