# CPU 批量：模型共享、工作区隔离与 rollout 的真实契约

本课覆盖 A8 与 B6 的 CPU 部分。先读[状态与时间](state-and-time.md)、[任务接口](task-interfaces.md)和[传感采样](sensors-and-sampling.md)。目标是能从原生对象、数组形状和 C++ 循环判断一次批量计算到底隔离了什么。所有片段仅做源码与语法审查；没有运行模型、批量仿真或计时。

## 1. 并行的单位首先是数据所有权

一个只读 `mjModel` 可以被多个线程共同使用；每个同时执行动力学的线程必须有独立 `mjData`。后者包含状态，也包含碰撞、矩阵分解、约束与 scratch 工作区，因此“各线程写不同的 qpos 行”不足以保护同一个 `mjData`。原生说明把跨样本并行与单步内部线程池分开讨论：[simulation.rst](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L560-L633)。

两种并行解决不同的问题：跨样本把多个世界分给工作线程；单步内并行把一个世界的内部工作拆开。线程数相乘可能导致竞争，不能将两个选项都开大就声称吞吐更好。此处没有性能测量，也没有根据 GPU 是否存在推断加速。

| 对象 | 可以共享的前提 | 本课中的所有者 |
|---|---|---|
| `mjModel` | 工作者只读，模型参数在调用期间不变 | 主线程持有一个固定模型 |
| `mjData` | 同一时刻只能有一个推进者 | 每个 rollout worker 一份 |
| 初始状态/控制数组 | 传入期间不被其他线程改写 | 调用者；必要时显式复制 |
| `Rollout` 对象及线程池 | 不被多个调用者并发使用 | 一个调用者通过 context manager 管理 |
| Python 控制器、回调闭包 | 需要另外设计隔离，MuJoCo 不替你隔离 | 不由 `FULLPHYSICS` 保存 |

`[mujoco.MjData(model)] * workers` 重复的是同一个引用。正确构造方式是列表推导，每次调用构造器。Python 绑定进入原生函数时释放 GIL，Python 回调又需要取得 GIL；因此 Python 侧复杂回调既有共享状态问题，也不等同于无开销的原生并行。[绑定与 GIL](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L299-L314)、[Python callbacks](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L462-L478)。

## 2. rollout 是开环轨迹计算，不是学习环境

`mujoco.rollout.Rollout` 将一批初始状态与预先给定的控制序列送入原生循环；它不定义 reward、episode、成功、截断或自动 reset，也不在每步把观测交给 Python 策略。需要闭环策略时，必须另行设计策略与物理的执行边界，见[学习与随机化](learning-and-randomization.md)。

令批量大小为 B、每条轨迹物理步数为 T，默认控制状态为 `mjSTATE_CTRL`。核心形状如下，最后一维用原生 API 取得，不能把旧版固定公式抄进代码。

| 输入/输出 | 完整形状 | 含义 |
|---|---|---|
| `initial_state` | `(B, Nfull)` | `mj_stateSize(model, mjSTATE_FULLPHYSICS)` |
| `control` | `(B, T, Ncontrol)` | `mj_stateSize(model, control_spec)`；默认是 `nu` |
| `initial_warmstart` | `(B, nv)` | `qacc_warmstart`，广义加速度估计 |
| 返回 `state` | `(B, T, Nfull)` | 每次 `mj_step` 后打包的状态 |
| 返回 `sensordata` | `(B, T, nsensordata)` | 该步留下的传感数组，时点另见下文 |

Python 接受单例 batch/time 轴并广播，也支持推断 B/T；这种方便不代表零复制。`_ensure_*` 要求数值数组并转为连续 `MJTNUM_DTYPE`，单例扩展使用 `np.tile`，因此传入的非连续视图或其他 dtype 可能产生副本。预分配输出也应使用原生 dtype、连续布局，并以函数返回数组为准。[参数与检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L48-L224)、[连续化与广播](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L375-L433)。

3.15 的 `FULLPHYSICS` 包含 `time`、`qpos`、`qvel`、`act`、`history`、`plugin_state`，不包含控制和 warmstart。`PHYSICS` 也已包含 history。`control_spec` 必须是 `mjSTATE_USER` 的子集，因而可以显式传外加力、mocap 或 userdata；这时最后一维不再等于 `nu`。[枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h#L507-L533)、[mask 检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L129-L134)。

Python 的 `initial_warmstart` 注释有 `qfrc_warmstart` 字样，但 C++ 实际写的是 `d->qacc_warmstart`。应按字段和单位解释，不能把它当作上一步广义力。[实际写入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L116-L130)。

## 3. 按一条轨迹追踪 C++ 循环

原生循环顺序值得逐行读；它说明文档中的“stateless”需要一个明确范围。[rollout.cc](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L71-L181)。

1. 对未列入 `control_spec` 的 ctrl、外加广义力和空间力做清零；mocap 与 equality 激活状态按模型默认值补齐。
2. 对每条轨迹设置 `FULLPHYSICS`，从参数恢复 `qacc_warmstart` 或清零；清除 warning 计数。
3. 每个 t 开始时检查 warning。若已有任意 warning，将当前 state/sensor 复制到余下所有输出位置，然后停止这条轨迹。
4. 若提供 control，按 `control_spec` 写入这一帧的控制状态。
5. 调用 `mj_step`；打包当前 `FULLPHYSICS`，复制当前 `sensordata`。

这里没有对每条轨迹调用完整 `mj_resetData`。尤其有一个容易漏掉的组合：**默认 `control_spec=CTRL`，但 `control=None` 时，ctrl 不会被上述清零分支处理，也不会被逐步控制分支覆盖。** 它可以继承工作区现有值。要表达零输入，就传明确的零控制数组；要表达中性输入，应按 actuator 类型构造，SO3 的中性四元数也不是全零。[条件分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L82-L96)、[逐步控制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L133-L178)、[原生 reset 的中性 ctrl](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1653-L1663)。

如果把 CTRL 从 mask 排除，C++ 的默认行为确实是全零，也不等于所有 actuator 的原生中性控制。控制的“未提供”“零”“中性”是三个不同契约。原创 slider 例子只有一个普通 motor，明确的零才有预期意义。

同样，未指定的 userdata、外部回调闭包、插件外部资源，以及不在该 mask 中的 sleep/IPC 内部状态不能凭 `FULLPHYSICS` 推断被重新初始化。对于依赖这些状态的模型，需要额外生命周期设计或适用性审查；不能借一个“stateless”标签宣称任意模型完全可恢复。完整状态边界见[记录与回放](recording-and-replay.md)。

## 4. 两个输出的索引相同，采样时点不一定相同

设输入状态为 x₀，每个步长为 h。无 reset、无错误且每步推进的前提下，输出 state 的第 t 行（从零计）应对应 xₜ₊₁，时间为初始时间加 `(t+1)h`。

$$
x_{t+1}=F_h(x_t,u_t),\qquad \tau_{t+1}=\tau_0+(t+1)h.
$$

`sensordata[t]` 是 `mj_step` 内部传感阶段留下的数组，并没有在积分后的 state 上自动再做一次 `mj_forward`。Euler 与其他积分分支的执行链、带 history 的 delay/interval 都可能改变读数对应阶段；不能把二者拼在同一行就给 sensor 写上“精确 post-step”标签。先依据[E3 执行链](dynamics-and-pipeline.md)与[E4 采样契约](sensors-and-sampling.md)定义标签，再设计学习观测或数据记录。

状态中的时间停止增长，可能是 warning 分支复制输出的迹象。若 warning 在最后一次推进才出现，窗口里甚至没有余下的重复帧。因此时间单调性是必要的诊断之一，不能代替 warning 和有限数值检查，也不能把符合 shape 的数组自动视为有效轨迹。原生 batch 输出没有每条轨迹的完整 warning 历史；worker 的最终 `MjData` 只留下它最后处理的轨迹状态。需要逐条详细故障记录时，应选择能保存该契约的执行方式，而非从 pooled worker 事后猜轨迹 ID。

## 5. 线程池与多模型的边界

线程池按 chunk 分配轨迹，worker ID 选择它自己的 `MjData`；B 可以远大于 worker 数。每个工作区依次复用，最终状态对应哪个轨迹受调度影响。[worker 分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L182-L237)。

`Rollout(nthread=workers)` 建立持久对象，通过 `with` 释放资源。模块函数 `rollout(..., persistent_pool=True)` 还维护一个全局持久池；该全局模式不支持并发调用。多个并发调用者应持有各自的 `Rollout` 和独立 data 列表；不要共享同一个实例。[类生命周期](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L29-L46)、[全局池](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L318-L347)、[官方线程说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L904-L936)。

Python 支持按轨迹传 model 列表，但兼容性检查只比较 `FULLPHYSICS` 长度、control 长度、`nv`、`nsensordata`。C++ 还使用第一个 model 的 `nbody/neq` 来恢复其他模型的 mocap/equality 等数据；这些四项相等并不足以保证不同拓扑模型的工作区兼容。课程建议同一结构的模型副本、匹配分配的工作区，且逐个核查涉及字段；不要把检查通过扩张为“任意结构模型都可混跑”。[Python 比较](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L195-L207)、[C++ 对首模型的依赖](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L82-L114)。

`skip_checks=True` 直接进入原生调用，连形状推断、广播与输出分配都跳过。它不是让不兼容模型变得兼容的办法，也不适合首次建立数据契约。[直接入口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.py#L108-L127)。

## 6. 原创片段与拷贝成本

[slider 示例](../examples/batch-learning-data/README.md)展示四条轨迹、两个独立工作区、显式控制与 warmstart、原生 state API、返回时间和传感阶段标签；只进行语法/XML 结构检查。它不是环境框架或训练代码。

输出内存至少随 B×T 增长。若仅存 state、control 和 Nobs 个同 dtype 标量，标量字节数为 s，则粗略下界是：

$$
M_{\rm payload}=BT\,(N_{\rm full}+N_{\rm control}+N_{\rm obs})s.
$$

这不包括模型、每 worker 的工作区、广播副本、images、allocator 和 Python 对象。只需要终态却保留整段轨迹，会改变内存与传输负担。图像更应单独设计采样频率和存储分块，不能以标量轨迹容量估计 RGB 数据。

## 7. 易错点与带答案练习

1. **B=128、worker=4，需要128份 Data吗？** 原生 rollout 需要4份独立工作区；128份初始状态是数组。若应用要求128个长期存活的闭环世界，则另外设计其持久状态保存/恢复。
2. **四个线程拿同一个只读 model，但每个在线修改 body_mass，安全吗？** 不安全，model 已不再只读。按 episode 预先生成独立兼容模型，或在无工作线程访问的边界修改、重算派生量，见随机化课。
3. **`control=None` 表示零输入吗？** 默认 CTRL mask 下不保证；例子必须显式传控制。排除 CTRL 会全零，也不保证 SO3 中性。
4. **为什么 `initial_warmstart` 末维是 nv，而不是 nu？** 它是广义加速度估计 `qacc_warmstart`；控制输入维数 nu 与广义速度维数 nv 没有相等保证。
5. **state/sensor 都是 `(B,T,...)`，能直接用同一个 post-step 时间标签吗？** 不能；state 在积分后打包，sensor 沿其内部采样阶段/history 产生，需记录各自时序。
6. **warning 后返回的后半段 shape 正常，可以当静止轨迹吗？** 不可以；实现复制最后状态来填满输出，应按失败/无效数据处理，而非任务成功或静止物理证据。
7. **不同 model 的四项尺寸相同，为什么还不够？** 检查未覆盖 nbody/neq、拓扑和所有工作区布局；C++ 仍依赖首模型的部分尺寸。
8. **`MJTNUM_DTYPE` 和 `float64` 可以永久互换吗？** 不可以；用本构建的原生 dtype。FP64 报告是某个构建/运行配置，不能替代当前绑定检查。

继续阅读[MJX 与设备数据](mjx-and-device-data.md)，把批量轴、静态结构与设备传输分开。
