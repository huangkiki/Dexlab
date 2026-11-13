# E5：随机化、MonteCarlo 与原生学习接口

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [环境生命周期](batch-lifecycle.md) · [数据与回放](data-replay.md)

先修 E1 状态/参数与 E2 驱动/事件接口。本篇基于 Drake 1.57.0 固定官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，完成 A8 随机化/学习接口和 A9 随机化证据边界。没有安装 gymnasium 或执行 pydrake、采样、仿真与训练。

## 1. 三种随机性要放在不同位置

| 随机化对象 | 例子 | 应记录和保存什么 |
|---|---|---|
| 一次建模/拓扑选择 | 物体数量、资产、连接图、相机数量 | factory 配置、资产身份、抽样前 RNG；不同拓扑需要匹配的新 Context |
| 一次回合的初始状态/参数 | 初始 q/v、质量与惯量、传感偏置 | 合法分布、抽样值、每环境种子/流、设置 API 与坐标/单位 |
| 随时间变化的随机输入 | 离散噪声、扰动、随机命令 | RNG 的运行状态、采样事件、保持方式、量纲；不能每次 Eval 任意重抽 |

`System.SetRandomContext` 调用随机状态再随机参数；基类没有专门实现时调用默认状态/参数。因此名字中的 Random 不代表质量、摩擦、光照和所有资产都已经随机化，见[原生分派](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.cc#L129-L165)。尤其是用户随机状态依赖参数时，要留意随机参数尚未更新，不能把该顺序假定为“先参数再状态”。

关节初态分布可由原生 symbolic 随机表达式表达，如 `RevoluteJoint.set_random_angle_distribution` 将角度分布交给 mobilizer；它配置的是模型的随机化规则，不是给某个现有 Context 立即赋值。见[关节角分布入口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/revolute_joint.h#L183-L187)。角度单位 rad，速度 rad/s；在有闭环或几何限制时，独立随机 q 不自动满足约束/无碰撞条件。

回合中的质量/惯量可通过匹配 Plant Context 的 `RigidBody.SetMass`、`SetSpatialInertiaInBodyFrame` 等 API 设置。SetMass 维持单位惯量参数，因此质量改变也按比例改变旋转惯量；任意独立乱填质量、COM、惯量可能失去物理一致性。完整空间惯量的参考点为 body origin、表达于 body frame，质量 kg、COM m、旋转惯量 kg·m²，详见[质量及惯量参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/rigid_body.h#L624-L709)和 E1。不能用只改视觉尺寸、只换摩擦数值或大范围均匀采样来宣称 sim-to-real 已覆盖。

## 2. RandomGenerator、种子与流

`RandomGenerator` 包装可复制的 `std::mt19937`；默认构造使用确定的默认种子，调用取数推进内部状态，复制会复制当时的生成器状态。见[RNG 定义](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/random.h#L20-L53)。Python 的分布枚举及带 seed 构造器见[common 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/common/module_py.cc#L334-L373)。相同 seed 不是“自动独立”：复制同一 RNG 状态后使用同样调用顺序，会得到相同流；每次 reset 都新建同一 seed 也会重复相同初始样本。

课程建议显式记录 `(master seed, environment id, episode id, derived seed, RNG 类型, 抽样顺序/规则版本)`，但这是应用的数据合同，不是 Drake 已内建的 seed 分配器。若使用分流算法，需要固定该算法并检测 seed 重复；仅保存一个 master seed 不能补回未知的回调、系统构造顺序和第三方 RNG 状态。Gym/NumPy、Drake、策略库和 worker 的随机源应分别管理。

原生 RandomDistribution 定义均匀 $U[0,1)$、标准正态 $N(0,1)$ 和 rate=1 的指数分布，见[分布参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/random.h#L58-L65)。这些输出先是无量纲。若定义物理噪声 $\eta_k=\sigma z_k$，$z_k\sim N(0,1)$，则 $\sigma$ 与观测具有同一单位；零阶保持噪声的方差不是连续白噪声谱密度。改变采样周期并保持同一 sigma，会改变时间统计，不应视为同一硬件噪声模型。

## 3. RandomSource 如何将抽样纳入状态和事件

RandomSource 把**当前样本**存入离散状态，把生成器及分布对象存入 abstract 状态；周期 unrestricted update（offset=0）推进 RNG 并写新样本，输出只是读取保持的离散状态。见[状态与周期事件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc#L16-L90)和[更新样本实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc#L109-L142)。这保证同一状态下重复读取不会因为 Eval 次数而多消费随机数。

若采样周期为 $T_s>0$、单位 s，保持输出可记为：

$$
u(t)=u_k,\qquad t\in[kT_s,(k+1)T_s).
$$

这是事件更新之后的保持语义；在 $kT_s$ 的事件前后可能不同，初始化与边界处理要服从 Simulator 合同。SetDefaultState/SetRandomState 自身也生成一组初始样本，之后 t=0 的周期事件可以再次更新，不能只用 `floor(t/T_s)` 猜测 RNG 消费次数。

默认 seed 由 **System 实例**的构造顺序分配，所有使用该 System 的默认 Context 会重用该实例 seed；创建多个默认 Context 不等于独立噪声。SetRandomContext 会用传入 generator 给 RandomSource 生成新 seed。C++ `set_fixed_seed` 影响后续默认/随机 Context 设置，而非立即改现有状态；实现即便采用 fixed seed，也先从外部 generator 取一次 seed，不能假定完全不消耗它。见[实例和固定 seed 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.h#L26-L105)、[分配和重置实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc#L70-L74)及[先取 fresh seed](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc#L109-L130)。

固定 Python 绑定只暴露 RandomSource 构造器，没有 `set_fixed_seed/get_fixed_seed`，不要把 C++ 教程直接翻译为不存在的 Python 方法。见[Python RandomSource 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L870-L882)。本课程的 Python 示例使用显式 `RandomGenerator(seed)` 和 `diagram.SetRandomContext`。

`AddRandomInputs` 只为标记为 random 且未连接、未导出的输入端口添加 RandomSource，见[自动接线边界](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc#L146-L168)。它不会识别“看起来像噪声”的普通输入，也不会自动建立设备相关性、空间偏置或滤波；各元素独立分布不能替代相关噪声模型。

## 4. MonteCarlo 的真正输出与重放信息

原生 `RandomSimulation` 依次调用 `make_simulator(generator)` → `SetRandomContext` → `AdvanceTo(final_time)` → `output(system, context)`，返回一个 **double 标量**。factory 必须保证 System 生命周期，且若要复用 RNG snapshot 重放，应只使用所给随机源，见[回调合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.h#L15-L87)和[串行实际调用](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.cc#L16-L47)。

`final_time` 是绝对时间边界；factory 若预设非零起始时间，剩余时长要另算；monitor 提前终止时 output 观察实际结束状态。helper 不会替你定义成功率、奖励累计、风险指标或记录完整轨迹。`output` 可以计算一个物理量，但单位由应用明确，例如落点 m、末端误差 m、末态能量 J，不能因返回 double 就把不同指标混成排名。

`MonteCarloSimulation` 返回每个样本的 `{output, generator_snapshot}`；snapshot 是**调用 factory 之前的 RNG 状态**，不是物理 Context、积分器或完整 checkpoint。复制 snapshot 后交给同一 factory/配置，可重建同样随机抽样流程；若消费顺序、构造代码或外部随机源变了，就失去这层保证，见[RandomSimulationResult 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.h#L89-L111)。

并行版本在主线程串行运行 factory 和 SetRandomContext，再把该样本 Simulator 交给 worker 推进并计算 output；索引 sample_num 预先决定结果位置，future.get 传播异常。不存在多个 worker 同时消费这个共享 generator 的设计。见[并行调度与结果存放](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.cc#L61-L128)。output 回调本身可能并行执行，因此不得写未保护的共享副作用。

C++ 默认不并行，Python helper 更明确固定 `Parallelism::None()`，见[C++ 参数与重复性边界](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.h#L130-L158)和[Python helper](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/analysis_py.cc#L531-L548)。未传 generator 时新建默认生成器会导致多次调用重复相同序列；想继续新样本需有意保留并推进 generator。这里没有开展 MonteCarlo 运行，也没有产出统计置信区间。

## 5. DrakeGymEnv 接的是什么接口

固定官方实现是 `pydrake.gym.DrakeGymEnv`，依赖 Python **gymnasium** 与 NumPy，连接 Simulator 和 System 原生端口。它不是策略算法、经验池、GPU tensor环境或训练器。源码入口见[类与构造签名](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L1-L46)。

| 项目 | 原生合同与数据含义 | 应用必须明确的事 |
|---|---|---|
| simulator | 实例，或接收 Drake RandomGenerator 的 factory | 图/Context 的生命周期；实例复用与每 reset 重建的差别 |
| `time_step` | 外层每 step 希望推进的正时间间隔，单位 s | 与 Plant time_step、控制/传感周期分开；不是固定积分子步 |
| action | 通过指定输入端口 FixValue；可用端口名字明确选择 | 维度、actuator 顺序、N/N·m/目标值的含义、限幅与安全逻辑 |
| observation | 通过指定输出端口 Eval | shape/dtype、坐标、物理/传感时间、归一化、是否有 action 直通 |
| reward | `(system, context)` 回调或输出端口首元素 | 末态奖励还是区间积分；单位/尺度和任务定义 |
| termination | Simulator monitor 等返回的 termination status | 何种任务终止；与异常或外部时间上限截断分开 |
| rendering | human ForcedPublish、RGB image 端口或文本分支 | 显示不是物理更新，图像数据和 log 可能有额外发布/引用行为 |

构造器缺省向量 spaces 为无界 float64 Box，源码并没有在 step 自动执行 action space contains、裁剪、单位转换或驱动力限制。应显式给 spaces 并在原生控制链定义限额；传入 spaces 只是描述，不构成 actuator 饱和。实现见[spaces 与端口设置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L197-L257)。该版本构造器 action_port_id 实际检查支持端口 index 或字符串名字；教学中优先命名端口，别仅凭类型注解传 InputPort 对象。

对有控制代数直通的观测，固定实现注释希望避免 action→observation 直通，但没有启用相应断言；新 action 固定后读到的“步前观测”可能已受 action 影响。定义观测应来自明确保持或状态端口，不能假定 step API 自动消除直通。

## 6. 逐行读 step/reset，而不是补写理想合同

### step：一次动作和异常路径

[实际 step](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L259-L307) 先固定 action，读 `prev_observation`，再 `AdvanceTo(time + time_step)`。正常返回 `(observation, reward, terminated, truncated, info)`，terminated 来自原生 termination reason；该路径没有自动 episode 长度上限，若外部配置 Gym TimeLimit，需单独记录它。

它捕获 AdvanceTo 抛出的 **RuntimeError**，发警告、reward=0、terminated=False、truncated=True，并返回推进前的 prev_observation；这不是只识别 contact solver failure 的分类器，也不会回滚可能已部分推进的 Context。动作 FixValue、推进前 Eval 或奖励计算等其他位置的异常不因此被全部包住。故障记录应保留异常、目标时间、实际时间和有效样本掩码，不将失败默默写成成功的等长轨迹。

这里还需核对绑定所有权：[OutputPort.Eval 的 vector/abstract 分支](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L49-L70) 对 vector 先复制成 Eigen 向量再转 Python，因此 vector prev_observation 是 FixValue 后、AdvanceTo 前的值副本；abstract 返回则可能引用 Context 所有的对象。它不是整个世界的 checkpoint，也不保证任意 abstract 观测故障后保持原值。

### reset：实际顺序与固定源码差异

[实际 reset](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L309-L348) 先管理 Gym seed 和 Drake generator（只有显式 seed 才重建 Drake generator），必要时由 factory 重建 Simulator。之后为 `SetTime(0)` → `Initialize()` → 自定义 reset_handler 或 `SetRandomContext`，**改变状态后没有再次 Initialize**。若提供 handler，先 SetDefaultContext，再调用 handler；hardware=True 只跳过无 handler 分支的随机化，不代表整个 reset 没有副作用。

因此不能把本版本 reset 宣称为“新状态先完整准备好，再开始初始化事件”的实现。初始化发布/monitor 可能看到旧或默认状态；旧 fixed action 不由 SetDefaultContext/SetRandomContext 清除；logger 缓存也不会因此自动清空。向量/abstract 状态依赖会按 API 失效，但初始化事件和外部资源并未自动重新执行一遍。自己设计外部适配时应明确所需顺序，并另做未来运行验收；本课只记录现状，没有修改上游或声称验证了替代 Gym 包装器。

| 固定代码差异 | 源码位置 | 对使用者的影响 |
|---|---|---|
| reset_handler 注解为二参数，调用实际传 `(simulator, context, seed)` 三参数 | 构造签名 L44；reset L335–336 | 仅按二参数注解实现 handler 不能匹配实际调用；按调用链审查签名 |
| `if info_handler is callable(info_handler)` 使用对象与 bool 的身份比较 | L176–180 | 普通函数不会与 True 是同一对象，落入默认空 dict；不能把 info 当作可靠导出的自定义诊断 |
| metadata 默认列 `ascii`，render 实际分支检查 `ansi` | L159；L370 | 声明和实现不一致；不能仅照 metadata 认为该文本模式可用 |
| reset 在状态重设之前 Initialize | L331–341 | 初始化事件的观察对象与期望回合初态可能不同，须保留此版本限制 |

这些是固定源码层面的差异，不是本机运行错误报告。对应[handler / metadata 设置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L147-L180)、[reset](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L331-L341)及[render](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py#L365-L378)。`rgb_array` 返回 `image.data[:, :, :3]`，需要长期保存时复制；human ForcedPublish 也可能触发含 forced trigger 的 logger，详见数据篇。

## 7. 易错点与外部学习边界

- 不把 seed、RNG snapshot、Context clone、模型/积分器/外部策略 checkpoint 混为一件事；重放要求明确每一层。
- domain randomization 的参数范围、相关性和有效域由应用定义；SetRandomContext 不自动实现硬件标定或覆盖所有参数。
- observation/reward/action 是端口与回调合同，不附带训练库、GPU batch、自动微分反向链或策略稳定性保证。
- 固定 DrakeGymEnv 差异意味着必须读实现；本轮不通过“修正后的伪代码”冒充其运行行为。
- 本仓只完成源码课程，未来学习任务的实际配置、版本和结果仍复用 DexLab，不另起训练/排名系统。

## 8. 阅读练习与答案

1. **同一个 RandomSource 的两份默认 Context 是否默认不同噪声？** 答：实例 seed 相同，默认化会重用它；显式随机 Context 配置和流规划才是区分回合的动作。
2. **把高斯 sigma=0.01 的噪声周期由 10 ms 改为 1 ms，是否同一个传感器模型？** 答：点值方差可相同，时间统计已变；需要明确保持、频谱和单位，不能仅凭 sigma 宣称相同。
3. **输出 Eval 十次会消费十次 RandomSource RNG 吗？** 答：输出读取离散状态；抽样发生在初始化状态设置/周期 unrestricted update，不由读取次数决定。
4. **MonteCarlo RNG snapshot 能直接恢复一半的机器人轨迹吗？** 答：它是 factory 前的 RNG，用于重建抽样流程；没有中途 Context/积分器/外部状态，不能直接续接轨迹。
5. **Python MonteCarlo 的 output 会在多个 worker 同时运行吗？** 答：该绑定强制串行；C++ 开启并行时才有此合同，此时 output 需线程安全，factory/随机 Context 设置仍在主线程。
6. **DrakeGymEnv 的 RuntimeError 分支返回旧向量观测，是否已恢复物理状态？** 答：没有；vector Eval 的副本保存的是推进前读数，但原 Context 可能已部分推进。抽象观测还须核对对象引用。
7. **普通 info_handler 不返回诊断且二参数 reset_handler 不匹配，应先检查哪里？** 答：固定源码的 `is callable(...)` 身份比较和实际三参数调用；不能先归因训练器，也不能宣称这些差异已在运行中修复。

[静态验证与未执行范围](evidence/e5-validation.md)。
