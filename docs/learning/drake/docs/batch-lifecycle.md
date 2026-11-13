# E5：多环境的 Context、Simulator 与执行边界

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [随机化与学习接口](randomness-learning.md) · [日志与回放](data-replay.md)

先修：[E1 状态与时间](state-time.md)、[E2 原生任务事件](task-interfaces.md)、[E4 传感器时间](sensor-timing.md)。阅读基线为 Drake 1.57.0，官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。本篇完成 A8 的环境隔离与 B6 的线程、回调、存储和执行边界；源码与语法核对不代表运行或吞吐验收。

## 1. “一个环境”由哪些对象组成

一个 Diagram 描述连接好的系统拓扑，Context 保存该拓扑的一次运行实例，Simulator 管理其中一次时间演化。批量的首要问题是哪些对象可以共享，哪些对象有独立的可变历史；不能把 `contexts = [context] * N` 当成 N 个环境。

| 对象 | 典型内容与所有权 | 多环境合同 |
|---|---|---|
| System / Diagram | 端口、声明的状态结构、固定拓扑、系统成员、子系统；Diagram 拥有子系统 | 可考虑共享只读拓扑，但成员可变对象、回调闭包、外部资源须另审；有 N 个 Context 不构成线程安全证明 |
| 根 Context | 时间、状态、参数、固定输入、子 Context、依赖追踪与计算缓存 | 每个活跃 worker 独立一份；从根取匹配的子 Context，不跨环境复用子 Context |
| Simulator | 当前 Context、积分器、初始化标记、事件推进及统计 | 每条正在演化的轨迹独立一份；Context 和 System 必须匹配 |
| Python / 外部资源 | NumPy 数据、策略对象、网络连接、文件、Meshcat、renderer、回调捕获变量 | 不在 Context 的对象不会因为多建 Context 自动隔离；逐项决定独享、只读共享或显式同步 |

C++ Simulator 的引用式构造器要求 System 存活得更久，另一重载可接管 System。Python 绑定保持相关对象寿命，却直接共享传入的 Context 包装对象，源码明确警告不要让多个 Simulator 使用同一个 Context；它不会替你 `Clone()`。见[构造合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L260-L291)与[Python 构造绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/analysis_py.cc#L294-L334)。

`const Context&` 也不是完全不写内存：缓存可以在 `Eval` 时更新。因此“两个线程只读同一状态”仍不足以证明同时 Eval 安全。原生 logger 将数据放入每份 Context 的 cache，也正是为了独立日志和每线程 Context 的使用方式。见[可变缓存](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.h#L140-L148)与[日志缓存设计](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h#L124-L137)。

## 2. 复制、默认化与重新建回合不是同一件事

定义一次环境配置为拓扑 S，运行上下文 C，推进器内部状态 I，外部状态 E。能够复现某时刻的完整执行，至少需要说明 `(S,C,I,E)` 中保存了什么；仅有 q/v 数组或 RNG 种子不是完整 checkpoint。

| 原生操作 | 实际改变 | 没有自动完成的事 |
|---|---|---|
| `system.CreateDefaultContext()` | 分配匹配拓扑的新 Context，再设置默认参数/状态 | 不建立 Simulator、不生成历史传感数据、不替应用修复未连接输入 |
| `system.SetDefaultContext(context)` | 默认参数先于默认状态，结构大小不变 | 不改时间、不清固定输入、不清 logger 的独立缓存历史、不复位 Simulator |
| `system.SetRandomContext(context, generator)` | 先随机状态，后随机参数；没有覆盖的虚函数回落到默认实现 | 不随机全部模型字段、不改时间或固定输入、不替 Simulator 初始化 |
| `context.SetStateAndParametersFrom(other)` | 复制状态/参数并通知依赖失效 | 不复制时间/精度或固定输入 |
| `context.SetTimeStateAndParametersFrom(other)` | 根 Context 的时间/精度、状态/参数复制 | 仍不复制固定输入；原生 `FixInputPortsFrom` 是另一个动作 |
| `root_context.Clone()` | 克隆整棵 Context，复制缓存/依赖图并修复内部指针 | 不克隆 System 或 Simulator，不保证任意 abstract 值所引用外部对象深拷贝；复制的 logger 历史也不是新空日志 |
| `simulator.ResetStatistics()` | 清积分/事件/时间统计基准 | 不重置系统状态、时间、输入、日志或 RNG |

对应[默认与随机 Context 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.cc#L99-L165)、[状态复制范围](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h#L425-L474)、[根 Context 克隆实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.cc#L11-L28)及[缓存复制合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.h#L254-L259)。所有权的深浅还要追踪具体 AbstractValue 类型，不能把 C++ `Clone` 名称解释为外部文件、GPU allocation、网络连接、策略模型的完整快照。

原生状态访问器负责依赖失效；绕过它写旧 NumPy 视图、私自修改输出缓存或在 System 成员里藏回合状态，会破坏缓存推理和环境隔离。Task 的 phase、累计量、过滤器历史应按其语义声明为连续、离散或 abstract 状态，见 E2 状态机；不可把 Python `self.phase` 当成每 Context 自动独立的物理状态。

对教学和将来的回合构建，一个容易审查的顺序是：创建新根 Context → 设置时间 → 默认/随机参数与状态 → 应用合法的回合参数和初始 q/v → 固定必要输入 → 给该 Context 建立 Simulator（或 `reset_context`）→ 按约定配置积分器/monitor → `Initialize()` → 推进。若选择复用原 Context，必须另外处理旧固定输入、日志、外部状态和初始化事件。本轮只解释顺序，不执行任何一步。

## 3. Initialize、AdvanceTo 与事件边界

`Initialize()` 初始化积分器、统计与事件处理，可能执行初始化更新、发布与 monitor；它不是零副作用的状态检查，也不会自动把任意非法 q/v 投影到约束流形。首次 `AdvanceTo` 可以隐式调用它，但明确初始化更容易定义第一次观测发生在哪个阶段。见[Initialize 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L296-L345)。

设策略在时刻 $t_k$ 给出动作 $a_k$，应用以零阶保持把它固定在区间内，策略周期为 $\Delta t_\pi>0$，单位 s。外层调用的目标是：

$$
t_{\mathrm{target}} = t_k + \Delta t_\pi.
$$

`AdvanceTo(t_target)` 的参数是**绝对仿真时间**，不是“再走多少秒”。内部可以有多个连续积分步、离散 Plant 更新、传感事件和发布；策略周期、Plant time_step、logger 周期、相机捕获周期均需分别记录。提前终止时实际 Context 时间可能小于目标时间，不能仍用外层计数乘周期伪造时间戳。见[AdvanceTo 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L349-L380)。

在边界 $t$，`AdvanceTo(t)` 返回时可能还有待处理的离散/abstract 更新；`AdvancePendingEvents()` 在不推进时间的情况下处理这些更新，把边界的 $x^-(t)$ 转到 $x^+(t)$，还可能发布或调用 monitor。它不是“刷新输出缓存”，更不是幂等的通用读传感器函数。需要明确数据集选择边界前还是边界后的状态，见[边界事件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L382-L405)和 E3/E4 的 sampled 输出解释。

Simulator monitor 在内部步及初始化等规定阶段调用，不保证恰好每个策略步一次；若奖励按内部步累计，需要定义实际积分规则，而不是在 monitor 中无条件加一个策略周期。返回终止状态和抛出异常也是不同控制流。见[monitor 时机](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L409-L481)。

把 Context 时间从 $t$ 改回 0 后直接再次 AdvanceTo 会触发显式检查，要求重新 Initialize。`reset_context` 会替换 Context 并令初始化标记失效；ResetStatistics 只清统计。见[时间回退检查](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.cc#L294-L309)和[reset_context / ResetStatistics](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.cc#L879-L895)。如果先 Initialize、后随机化状态，初始化处理面对的是旧状态；固定 Gym 包装器正有这个顺序，需要阅读[下一篇](randomness-learning.md)，不能用理想重置流程代替其实际实现。

## 4. 并行实际发生在哪里

原生批量并行不是给单个 Diagram 增加一个 batch 维。q、v、BasicVector、端口维度属于一个 System 的约定；把状态拼成 N 倍数组并不能生成 N 个动力学世界。每个实例是否共用只读 System、是否各自建 System，取决于具体系统的可变成员、外部依赖和绑定合同。

| 路径 | 固定版本执行方式 | 能够据此判断什么 |
|---|---|---|
| C++ `MonteCarloSimulation(..., parallelism)` | 支持多 worker；factory 与随机 Context 设置在主线程串行，AdvanceTo/output 在 worker | 已提供明确的独立 Simulator/Context 轨迹并行路径；不等于接触 kernel 的 GPU 批量 |
| Python `MonteCarloSimulation` | 绑定内部传 `Parallelism::None()`，不暴露 parallelism 参数 | 本版本该 Python helper 串行；设线程环境变量不会改变此绑定 |
| Python `Simulator.AdvanceTo` | 绑定用 `gil_scoped_release` 释放调用期间的 GIL | 纯 native 部分可以脱离 GIL；Python 回调仍受 Python 解释器同步限制，不保证任意 Diagram 线程安全或线性加速 |
| 应用层多进程 | 需要应用各进程建立原生对象、管理 IPC 与种子 | 属于外部编排；本课不假设 Context 可 pickle，也不提供未经验证的进程/GPU向量环境 |

源码见[MonteCarlo worker 路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.cc#L61-L128)、[Python 串行绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/analysis_py.cc#L531-L548)、[AdvanceTo 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/analysis_py.cc#L335-L356)。结果存入预先分配的 sample_num 位置；完成先后顺序不改变结果索引，但共享 output 回调若修改全局容器仍需线程安全。

`Parallelism` 表达一个接受它的操作的线程意图：默认 1，`Max()` 根据硬件/环境配置，首次访问后锁存。`DRAKE_NUM_THREADS` 的优先级及仅在未设置它时使用 `OMP_NUM_THREADS` 的规则，见[线程数合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/parallelism.h#L11-L48)。这不是给所有算法打开线程的全局开关；显式线程数过大会竞争 CPU，多层并行还可能超额订阅。此处没有测吞吐或推荐线程数。

## 5. CPU 数据、GPU 与成本分解

此处的 Systems 状态、Eigen 向量与 NumPy 日志走 host 内存接口。学习框架把这些数组转成 GPU tensor，是另一个库的内存/同步动作；它不能使 MultibodyPlant 的这条 CPU 执行链自动成为 GPU 物理批量器。GPU 图形 backend、相机 Async worker 和 GPU 策略推理也各有职责，不能互相代替证明。

原生返回值按**具体 API**判断：[Python OutputPort.Eval](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L49-L70) 对 vector 输出先复制 Eigen 向量再转 Python；abstract 输出可以持有 Context 内值的引用。`EvalBasicVector` 是另一种借用接口；`VectorLog.data()` 的 double 绑定及图像 `.data` 又可以是视图。不能用一个“所有 Python 输出零拷贝/全拷贝”的规则覆盖它们，详见[数据篇](data-replay.md)。

对顺序执行的一次 rollout，可把 wall time 的账本写为：

$$
T = T_{\mathrm{build}} + T_{\mathrm{initialize}} + T_{\mathrm{native\ advance}} + T_{\mathrm{policy}} + T_{\mathrm{copy}} + T_{\mathrm{I/O}}.
$$

这是成本分类，不是测量结论：若 native advance 内触发了 renderer 或 Python 回调，其时间不能再重复加在另一个栏里；异步执行有重叠，更不能直接把各线程 wall time 相加当端到端延迟。区分 C++ 源码构建、Python wheel 加载、Diagram.Build/Plant.Finalize 的拓扑工作、Context 分配、首次事件和稳态步进；不要统称“JIT”。本课没有实现自动学习编译器或声称 Drake 原生 step 被某策略框架 JIT 编译。

`set_target_realtime_rate(r)` 通过等待限制过快的推进，不能让慢于目标的系统加速，也不给硬实时保证。它不应充当性能测试的加速开关，见[实时节流](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h#L498-L522)。

## 6. 原生扩展接缝与正确的状态位置

`LeafSystem` 是扩展系统行为的原生入口。先声明输入/输出类型及依赖，再声明状态/参数与事件；用连续导数描述连续变化，用离散/非受限更新写下一状态，用 publish 输出外部消息。事件分派在源码中明确区分只读 publish、离散更新、非受限更新，见[LeafSystem 事件合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L225-L245)；Python 的回调通过绑定进入虚函数或事件 handler，见[Python callback 包装](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L148-L202)。

例如学习控制器的循环网络隐藏状态、观测滤波器历史和 task phase 都会影响未来行为，应放在对应 Context 状态或明确由每环境独享的外部策略对象管理。输出 `Eval` 可能因为缓存而不执行回调，也可能因失效而重复执行；不要在其中随机抽样、增加 episode step、写状态或推进策略隐藏状态。输出回调应计算当前输入/状态对应的值，采样更新放在显式事件中；[RandomSource](randomness-learning.md) 正展示这一设计。

C++ 自定义系统可以进一步选择标量转换及原生性能实现；Python LeafSystem 方便接外部策略，但必须处理 GIL、异常、数组生命周期、每环境状态与单位。renderer 的插件式工厂、消息通信、用户 force element 等具体扩展不能因为本课讲过回调就宣称兼容；E6 再审引擎特色和能力边界。本篇 B6 完成的是系统层扩展与执行合同，不包含新插件实现或兼容性运行报告。

[isolated_records.py](../examples/isolated_records.py) 用 RandomSource 和原生 logger 展示两个独立 Context/Simulator 与种子、日志副本；没有自造统一环境封装，文件没有自动执行入口。本轮连构建函数也未调用。

## 7. 易错点

- 两个 Simulator 收到同一 Python Context，不会自动复制；两个 Context 也不会隔离共用的 Python 可变闭包。
- SetDefaultContext、SetTime、Clone、reset_context、Initialize、ResetStatistics 各有不同范围，不能只选一个就宣布回合清空。
- 每步只读 `Eval` 也会使用缓存；同一 Context 的跨线程访问须有明确同步设计。
- 外层步长不能证明内部控制/感知同频；边界事件前后与提前终止的实际时间必须记录。
- 调用 native 时释放 GIL、GPU 渲染可用、安装 GPU 学习库，均不是 GPU 物理或并行吞吐验收。

## 8. 阅读练习与答案

1. **`[context] * 8` 后各建 Simulator 得到八个环境吗？** 答：只是八个同一引用；Python 构造不克隆。应各自创建根 Context，并审查共享 System 与外部对象。
2. **SetDefaultContext 后 time=3、action 已固定、日志 50 帧会怎样？** 答：状态/参数默认化，时间和 fixed action 保留，logger 缓存历史保留；随后 Initialize 还可能追加记录。
3. **Clone 能完整恢复积分器步长选择历史吗？** 答：Context clone 不克隆 Simulator/积分器内部状态或外部资源；它不是全执行 checkpoint。
4. **t=1.2 s，策略周期 20 ms，应调用什么目标？** 答：AdvanceTo(1.22)。若 monitor 在 1.213 终止，数据应记录实际 1.213，而非伪造 1.22。
5. **Python MonteCarlo 设置 DRAKE_NUM_THREADS=8 会八线程吗？** 答：此固定绑定强制 Parallelism::None，仍串行；不能从环境变量推导调用行为。
6. **在输出回调中 `self.count += 1` 用作回合步数有什么问题？** 答：共享 System 的多个 Context 共用成员，且 Eval 的缓存/重算不等于时间更新；应以事件维护 Context 中的状态。
7. **AdvancePendingEvents 为何会改变同一时间戳下观测？** 答：它可处理待定离散/abstract 更新，使边界状态由 x⁻ 到 x⁺，没有推进时间；记录必须注明采样阶段。

[静态验证与未执行范围](evidence/e5-validation.md)。
