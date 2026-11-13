# E5 批量、学习接口与数据

本章覆盖 A8、A9、B6，基线为 Genesis **1.4.3**、官方提交 `216a708e06124595521a9d36a51fae5393fd4ff8`。这是源码阅读与原创 API 片段的静态交付：没有导入原生引擎、构建模型、推进物理、渲染、训练或性能测量。先读 [E1 状态与时间](modeling-state-time.md)、[E2 控制与任务](control-robotics-tasks.md)和 [E4 观测](sensors-rendering.md)。需要理解张量维度、刚体 q/v、离散时间和基本条件概率；不要求先实现 PPO。

应用路线可按 1–6、8–10 节阅读；源码路线再追 7、11 节的存储分类、线程与执行边界。学习目标是能回答：某一行属于哪个环境、哪个 episode、哪一时刻，谁拥有它的内存，以及重新加载它能恢复什么。

## 1. 批量场景：独立状态，共同的推进调用

[Scene._parallelize][parallel] 设置 `n_envs`，内部容量 `B=max(1,n_envs)`；公开 API 的 batch 轴由是否 `n_envs>0` 决定。`n_envs=0` 时 qpos 通常为 `(n_qs,)`，`n_envs=1` 时为 `(1,n_qs)`。四元数使自由基座的 `n_qs` 与 `n_dofs` 不同，不能用速度长度裁剪配置数组。

| 层次 | 原生含义 | 隔离边界 |
|---|---|---|
| 状态行 | 刚体 q/v、控制输入按环境保存 | `envs_idx` 选择写哪些行；同一环境里的机器人仍会相互接触 |
| 时间推进 | 一次 `Scene.step()` 调用所有子步 | `Simulator.step` 对全部环境的 steps 加一；没有这里可用的逐环境 masked step |
| 模型参数 | links/dofs INFO 可共享或按环境展开 | 必须检查 `batch_links_info` / `batch_dofs_info`，不能由 qpos 有 batch 轴推断参数也有 |
| 场景结构 | 构建时确定 solver、实体、容量和拓扑 | 不是每一行各持一个 Python Scene；不能在 step 中随意改关节数 |
| 显示布局 | `env_spacing` 产生可视偏移 | 不加到物理 qpos、相机标定或学习目标中 |

执行证据是 [Simulator.step][sim-step]：全批推进、结束时清理外力并更新 sensor manager。图像是否只渲染第 0 环境是另一个选择；见 E4，不改变其他环境的物理推进。刚体各环境的碰撞空间独立，不靠把几何摆到很远来隔离；记录器线程、全局随机数发生器、梯度游标和部分缓存则不具有逐环境独立的生命周期。

### 索引是选择集合，不是另一种 batch 轴

[Scene 的索引入口][env-index]在非批量 `n_envs=0` 下拒绝显式环境索引。批量下 `envs_idx=2` 仍保留长度为 1 的选择；布尔张量/数组应有 `(B,)`，推荐把整数索引规范化为唯一的 `[0,B)` 索引；原生也接受 `[-B,-1]` 并回绕。不要把 Python `[True, False]` 当 mask：[`sanitize_index`][index-helper] 的布尔识别只覆盖 Torch/NumPy 的 bool，普通列表会走整数转换。也不要依赖越界索引总会在 Python 层报出友好错误，该辅助函数中面向容器的通用范围检查被注释掉，而 Scene 的标量 int 路径仍显式检查范围。

对选中的 K 个环境、D 个 DOF，控制目标显式组织成 `(K,D)` 最容易审查。广播规则见 [sanitize_indexed_tensor][broadcast]；若维度恰巧相等，形状可广播不代表语义正确。DOF 索引使用实体本地地址；环境×DOF 子集是矩形选择，不能想当然地当成配对索引。原生示例沿用 E2 的名字映射，不再创建一层跨引擎接口。

### 异构环境不是任意模型列表

`Scene.add_entity(morph=[...])` 的 docstring 仍写“rigid only, single-link”，但本固定版本的 [description.resolve][hetero-types] 和 [_load_heterogeneous_morphs][hetero-check] 已包含多 link 的 URDF/MJCF 分支。实际检查的是：所有 morph 都属于支持的 Primitive/Mesh/URDF/MJCF 类型，不能混用“机器人”与“基本几何”两组；不能多根；机器人变体要有相同 link 数、逐 link joint 数、joint 名、类型和 DOF 数。它不是任意拓扑打包机制，检查通过也不替代关节轴、父子结构和惯量的语义审查。

[实体装配][hetero-entity]把变体几何挂到共享 link 结构；[RigidSolver 分派][hetero-dispatch]把每环境几何范围和变体惯量写入对应行，使用平衡映射分配变体。这个构建期分配不等于每 episode 自动重抽资产，也不等于让所有变体几何同时参与每个环境的碰撞。[异构实体的 attach][hetero-attach] 明确被拒绝。读源码时应同时记录这些检查和过时注释，不能只摘支持口号。

## 2. reset 要分三层，时间也有三种

[Scene.reset][scene-reset] 调用 solver 状态恢复，重启梯度/耦合/传感器相关状态并重置可视缓存。它不认识用户自己建立的 episode buffer。反过来，`robot.set_qpos(..., zero_velocity=True)` 只处理实体状态，没有调用 Scene.reset 的整个生命周期。

| 层次 | 应明确保存/重置的内容 | 固定实现提示 |
|---|---|---|
| 物理层 | q/v、接触缓存、外力、控制模式、随机参数 | 刚体 `set_state` 恢复摩擦比例，清外加力/控制力并将模式置 FORCE；唤醒所选环境中的休眠体 |
| 任务层 | episode ID/长度、目标、累计奖励、动作历史、控制器积分量、RNN hidden state | Genesis Scene 不会替外部任务/策略重置这些数组 |
| 观测层 | 当前观测、延迟环、图像缓存、终止观测 | 普通 sensor reset 与 RGB lazy cache 的差别见 E4；新增 sensor 后不能照搬一个无 sensor 的任务 reset |

[刚体 get_state/set_state][rigid-state]并不把模型 INFO、所有控制历史和所有求解器缓存组成一个完整检查点。`SimState` 恢复与完整 `.gstraj` checkpoint 的用途见第 7 节。多物理 `set_state` 的字段与 `envs_idx` 消费差异已在 E1 逐项列出；MPM/SPH/PBD/FEM/SF/Tool 的批量布局或局部恢复不能由刚体路径推断。Scene 的 emitter 重置和梯度重启还有全局影响，因此本章没有宣称“任意多物理场景局部 reset 完全隔离”。

[Simulator.reset/_restart][sim-reset]揭示三个时钟：

1. **采集序号**：由调用者拥有，每生成一条记录递增。用于文件中的唯一顺序，不从 Genesis 游标推导。
2. **每环境时间**：`scene.sim.steps` 与 `scene.get_time(envs_idx=...)`。Scene.reset 只把选中环境的 steps 清零，时间单位为秒。
3. **全局 tape 游标**：`scene.sim.cur_step_global` 从 `_cur_substep_global` 推导；任何 Scene.reset 都会重置这个游标，不能当跨 episode 的单调时间戳。

[`steps` 属性][clock-fields]直接返回内部张量，不应原地改写；需要留存就 clone。`get_time` 用每环境 steps 乘以外步 `dt`。在一个全部用 Scene.reset 开始的 episode 内，

$$
t_e = n_e\,\Delta t.
$$

其中 $e$ 是环境，$n_e$ 是该环境自 Scene.reset 后推进的次数，$\Delta t$ 单位 s。如果任务用 `robot.set_qpos` 开始新 episode，$n_e$ 不归零，任务时间应另用 episode 计数。Go2 正是后一种情况。

安全的任务时序是：发命令 → step → 读取终止前的状态/观测 → 算奖励及两类结束标记 → 复制 transition → 重置选中环境及任务缓冲 → 构造下轮 reset 观测。这个顺序是数据契约，不是本章新增的训练循环。普通 recorder 自动采样处于 step **之前**，无法自动代替“step 后、reset 前”的终止记录。

## 3. CPU、GPU、Torch：设备相同不等于没有拷贝

[`gs.init`][init]设置进程级 backend、device、precision。`precision` 是 `"32"` / `"64"`，与学习网络使用的 dtype 分别记录；Metal 不接受 64 位配置。`backend=gs.gpu` 会按可用后端选择并可能退回 CPU，不能从请求字符串认定实际用上 GPU。`get_device` 选择一个 Torch 设备；这不是自动分布到多张 GPU 的训练调度器。

`GS_TORCH_FORCE_CPU_DEVICE` 可以改变 Torch 侧设备安排，零拷贝是否可用还取决于 native backend、Torch device、数组模式及平台。`performance_mode` 改变内部数组/编译相关选择，不是跨工作负载的提速保证。`Scene.build` 还会为了编译执行一次 Simulator.step 再 reset；因此“只 build 看看 shape”也不属于本章的静态验证。[初始化与构建实现][build]

| 接口/操作 | 本版本实际行为 | 保存数据时的处理 |
|---|---|---|
| `robot.get_qpos()` / `get_dofs_velocity()` | 继承 getter 经 `qd_to_torch(..., transpose=True, copy=True)` | 得到复制读数；shape 按 batch 模式，不能当内部状态写入口 |
| `scene.sim.steps` | 内部 Torch 张量直接暴露 | 禁止原地用作用户计数器；保存时 clone |
| `qd_to_torch(copy=False)` | 内部辅助；支持时返回共享存储视图，无法满足零拷贝会拒绝 | 不是所有后端都成立的公开无成本状态 API |
| `tensor.detach()` | 切断自动微分关系，未承诺独立存储 | 若下游会覆盖原张量，仍需复制 |
| `tensor.detach().cpu()` | GPU→CPU 需要传输；已有 CPU tensor 可继续共享 | 交给异步记录者前再 `.numpy().copy()` |
| `data_to_array` | 递归转换 Torch；已有 NumPy 数组直接返回 | 它不是深拷贝/所有权转移保证 |

固定证据：[公共 getter][getters]、[qd_to_torch][qd-torch]、[CPU/NumPy 转换][array-convert]。内部布局可能是 `(D,B)`，API 转置为 `(B,D)`；转置、非连续 stride、索引选择和 `.contiguous()` 分别会影响复制，不能仅由 tensor.device 判断。强制CPU读回、`.item()`/`.tolist()`、文件保存等会把设备计算与主机消费连接起来；一个 Python 后台 writer 并不消除此前的设备传输。

本章的原创 [batch_data_api.py](../examples/batch_data_api.py)把交给记录器的数据显式转换为独立 CPU 数组。它提供“step 后、reset 前复制 transition”和“build 前注册状态日志”两个入口，没有 init/build/step 主程序，也没有学习 wrapper。前者的 reward、obs、flags 由任务提供，不能假装 Scene 原生返回这些值。

## 4. 官方 Go2 学习例子：任务代码与引擎边界

这里审读的是同一固定 Genesis 提交里的 [go2_env.py][go2-all]、[go2_train.py][train]和 [go2_eval.py][eval]，不是一次已经运行成功的训练。训练器来自外部 `rsl-rl-lib`；脚本检查 major 至少为 5，并给出 `>=5.0.0` 安装要求，**没有固定外部实现的精确版本/提交**。本章只追踪 Genesis 侧调用，不推断 PPO、timeout bootstrap、网络 checkpoint 内部或外部库兼容性已经验证。`TensorDict` 同样是外部类型，不是 Genesis 的 Scene 状态类。

### 一次 step 的真实顺序

[Go2.step][go2-step]按以下顺序运行：

1. clip 当前动作，选择上一轮动作作为实际命令，将关节目标交给 PD 驱动，然后 `scene.step()`。
2. episode 长度加一，读 base pose、base 系线/角速度、投影重力、关节位置/速度。
3. 使用这些状态计算奖励，再按周期重采样命令。
4. 计算 reset mask：超时、俯仰/横滚越界或 solver error；填 `extras["time_outs"]`。
5. `_reset_idx(reset_buf)`，然后拼接观测、更新动作历史，返回 **四个值** `(observations, reward, reset_buf, extras)`。

`observations` 是 `TensorDict({"policy": obs_buf}, batch_size=[B])`。这不是核心 Scene 的返回契约，也不是五返回值的 Gymnasium Env。已经结束的环境返回的是 reset 后的观测，源码没有在这里单独保留 `final_observation`。奖励却来自 reset 前，因此直接把返回观测当作同一 episode 的 $o_{t+1}$ 会错误连接两个 episode。

[观测拼接][go2-reset]为 45 维：base 角速度 3、投影重力 3、命令 3、相对默认关节角 12、关节速度 12、当前动作 12。各组有自己的 scale；关节角为 rad、角速度 rad/s，运动命令中的线速度 m/s、偏航角速度 rad/s。base 线速度用于奖励但不直接出现在这份 actor 观测里。所谓“状态全部可见”不能由能调用 getter 推出，策略只看到选入输入的字段。

### 几处特别容易沿注释读错

| 固定实现 | 含义 |
|---|---|
| `simulate_action_latency=True` 在构造函数中硬编码 | train 配置虽有同名字段，Go2Env 没消费它；“一拍真实机器人延迟”是此示例的假设 |
| `dt=0.02`，`substeps=2` | 策略命令以外步更新，子步不会自动增加策略调用次数 |
| motor joint 的 `dof_start` 直接作为 getter/setter 索引 | 这里用到了全局地址；平面无 DOF、机器人前无其他 DOF 的布局使其可与实体本地地址重合 |
| 控制调用固定 `slice(6,18)`，动作再按索引排序 | 假定自由基座 + 12 个关节，不能直接复用给另一机器人或变更实体顺序 |
| clip 限额配置为 100，action_scale 为 0.25 | 动作不是自动归一化到 `[-1,1]`；角度目标与力限额仍是两层 |
| `episode_length > max_episode_length` | 20 s / 0.02 s 得到 1000，但第 **1001** 步才超时 |
| `reward_scales` 引用传入 dict 并原地乘 dt | 重复用同一配置 dict 构造环境会再次缩放；每实例应持有独立配置深副本，保存原始配置身份，不能把变异后的数值当原输入 |
| `_reset_idx` 只重设 robot qpos 与任务缓冲 | 没有 Scene.reset；scene 时间继续前进，也没有自动执行新增 sensor 的完整 reset |
| episode reward 报告除以配置中的 episode_length_s | 提前终止的 episode 并非按实际存活秒数归一化 |

证据：[初始化、关节地址与奖励缩放][go2-init]、[训练配置][train-config]及[重置代码][go2-reset]。命令重抽时先为全 batch 抽样再 where 选择，随机数消耗不只发生在结束行。`HoverEnv` 的奖励/重置顺序又不同：它先做自动 reset 再计算奖励，且当前动作执行分支没有消费保存的 latency 开关；不能把一个 demo 的时序概括为引擎统一 RL API。[另一任务实现][hover]

训练入口会创建/清理自己的日志目录、序列化配置并交给 `OnPolicyRunner.learn`；评估入口加载外部模型、以 CPU 配置建场景并调用推理策略。它们是学习集成的阅读入口，本仓没有运行这些脚本或安装外部训练器。[train main][train-main] / [eval main][eval]

## 5. 终止、截断与 episode 数据完整性

设任务隐藏状态 $s_t$，观测 $o_t=h(s_t)$，策略动作 $a_t$，实际施加命令 $u_t$。如果有一拍动作延迟，$u_t=g(a_{t-1})$；只保存 $a_t$ 无法解释本步力的来源。PD 内部实际输出还受状态、限幅和接触影响，参见 E2/E3。

在继续型任务被人为时间上限切断、且允许 value bootstrap 的假设下，一步目标可以写成

$$
y_t=r_t+\gamma(1-d_t)V(o_{t+1}^{\mathrm{final}}),
$$

其中 $d_t$ 只表示任务意义上的 terminated，$\gamma$ 为无量纲折扣，$r_t$ 为此 transition 的奖励；truncated 单独保存，不自动把该因子置零。真正终止则不 bootstrap。有限时域任务若把期限本身定义成终止，要把剩余时间/终止定义纳入状态与任务规范。这是学习数据的概念约定，**不是对未固定 RSL-RL 内部实现的声明**。

Go2 的 `reset_buf` 合并多种原因，`time_outs` 只是“超时条件为真”，可能同时跌倒和超时；solver error 更需要单独记录 invalid/failure 原因，不能无条件视为合法终点奖励。重建两类标记时要保留原始条件，不能只用 `terminated = done & ~timeout` 抹掉同时发生的失败。

一条可解释的 transition 至少需要：episode ID、环境 ID、episode 内步号、采集序号、命令发出与实际生效时点、$o_t$、动作 $a_t$、实际命令 $u_t$、奖励、terminal 前的 $o_{t+1}$、terminated、truncated、错误原因和 reset 后的下一轮初始观测。外部 RNN hidden state 在结束行复位，其他行保留。Go2 的 `rew_buf`、`extras` 是会被后续调用修改的对象，不能把它们的引用直接 append 成历史。所有存入 replay/文件的数组需有明确所有权；引用同一可变 buffer 多次 append 不是多份历史。

## 6. 随机化：区分初始状态、模型参数与观测模型

随机化可以改变初始 q/v、命令、惯量/摩擦/驱动参数、视觉与传感误差。这些入口的单位、存储位置和 reset 语义不同。[官方 domain_randomization 示例][random-demo]只提供 API 使用线索，不是已经标定的真实机器人参数分布。

| 参数 | 原生路径 | 单位、存储及恢复边界 |
|---|---|---|
| 初始配置/速度 | entity `set_qpos` / `set_dofs_velocity` | m/rad、m/s/rad/s；自由基座姿态仍按 E1；只改变对应状态 |
| link 质量 | solver `set_links_mass(..., scale_inertia=False)` | kg；INFO。默认不同比例缩放惯量；正有限性是调用者前提 |
| link COM | `set_links_COM` | link 局部坐标偏移，m；INFO。不可把世界坐标直接写入 |
| link 惯量 | `set_links_inertia` | 局部惯性系，kg·m²；要求对称正定，源码没有替调用者完整验证物理合法性 |
| geom 摩擦倍率 | `robot.set_friction_ratio` → `set_geoms_friction_ratio` | 无量纲乘子；按 link 展开到 geom；属于动态 STATE，被 RigidSolverState 捕获/恢复 |
| PD/限额/阻尼 | entity/solver 的 DOF setter | 增益与 E2 力/位移量纲对应；逐 env 参数需 `batch_dofs_info=True` |
| 观测误差 | 原生 sensor 选项/读数流水线 | 噪声、延迟、采样率及坐标区别见 E4；不是修改物理真值 |

证据：[link INFO setter][link-info]、[惯量/摩擦 setter][random-api]、[entity 摩擦展开][friction-api]、[DOF INFO 分支][dof-info]。`batch_links_info=False` 时 link setter 拒绝带 envs_idx；DOF setter 的 zero-copy 分支在未 batch 时只用 DOF mask，因此不要指望传 envs_idx 就自动获得逐环境增益。先配置批量 INFO，再读回确认其 shape 与选择语义。

运行时改 COM/惯量还受到对齐约束：构建时锚定 COM/主惯性轴的实体不能任意改变这些量；源码为文件 morph 指向 `align=False` 的路径。不要绕过 setter 直接改内部数组，setter 还会刷新反质量/惯量等派生量。质量改变与几何尺度改变也不同：均匀密度、各向同性尺度 $s>0$ 的实体满足

$$
m'=s^3m,\qquad I'=s^5I.
$$

这是相似几何与密度不变的假设；单独增加质量、独立乱改三个主惯量不满足它。实物惯量还应满足主惯量三角不等式，不只是矩阵可逆。采样后的 mass/COM/inertia/摩擦、相关性与单位都要随 episode 保存；一个 seed 不能代替实际参数记录。

模型 INFO 的质量等不会随普通 SimState reset 自动恢复，摩擦比例 STATE 则会恢复为所用 state 的值。这意味着“先随机化再 reset”可能保留质量却覆盖摩擦倍率。先确定基准恢复顺序，再在其后设置该 episode 参数；完整 checkpoint 恢复 INFO 是另一条路径。

[`gs.init(seed=...)`][seed]经[随机种子辅助函数][seed-helper]播种 Python、NumPy、Torch，并把 seed 传给 Quadrants 初始化。它不是给每个环境建立互不影响的 RNG 流。Go2 的全 batch 抽样加 mask、环境数变化、重置顺序和新增随机调用都会改变后续样本。`use_deterministic_algorithms` 与 `debug` 也是不同入口：前者影响 Genesis 选择，后者还设置 Torch 的确定性选项；不能据此宣称跨 CPU/GPU、精度、依赖版本的逐位一致性。复现元数据应同时保留输入 seed、随机状态/参数样本、后端与依赖身份。

## 7. 状态导出、检查点、轨迹与视频分别恢复什么

[Scene 导出检查][export-check]拒绝没有 description 的实体、emitters 和 force fields；camera、sensor、pre-step callback 等对象会被告知省略。IPC coupler 还在 [Simulator.data / 序列化][sim-serialize]入口拒绝该存储路径。不要把“支持 RigidEntity 的恢复”推广成所有多物理对象通用的存档。

| 产物 | 保存内容与读回入口 | 不应推断的能力 |
|---|---|---|
| `scene.get_state()` / `scene.reset(state=...)` | solver 专用 SimState；E1 列明字段和逐环境限制 | 完整控制器、随机数、传感器或求解器所有缓存 |
| `scene.export(...)` / `Scene.load(...)` | description、配置与打包资源；load 得到未 build 的 Scene | 当前动态状态/外部任务 episode 的恢复 |
| `scene.save_checkpoint(...)` / `Scene.load_checkpoint(...)` | `.gstraj` 单个末状态；加载/构建后恢复 | 外部策略、优化器、任务缓冲及所有被省略对象 |
| `scene.start_recording(...)` / `Scene.load_trajectory(...)` | description + 一组有时钟的状态帧；seek/play | 从动作重新积分得到相同轨迹的实验结论 |
| CSV/NPZ | 自定义 data_func 选中的数值 | 足够继续物理推进的完整内存 |
| camera 视频 / VideoFile | 图像及编码时间尺度 | 接触状态、控制输入、世界真值或真实 sensor 时钟 |

[Scene API][save-load]会在 load checkpoint/trajectory 内部重建场景；重建涉及 build，因此本章连这个“读取示例”也没有执行。`Scene.__setstate__` 校验 layout、description 和 solver/数组结构，再恢复 simulator、重启关联生命周期。[恢复检查][restore]

### exact 是存储策略，不能省略其前提

[DataKind][data-kinds] 区分 CONFIG、CONSTANT、INFO、STATE、WARMSTART、DERIVED、SCRATCH；[轨迹字段集合][trajectory-kinds]具体是：

- 普通 compressed 帧：INFO + STATE；其他内容需要重算。
- 普通 exact 帧：INFO + STATE + WARMSTART + DERIVED；并不是所有 SCRATCH 都在每帧中保存。
- 末尾 checkpoint frame：除 CONFIG/CONSTANT 外的种类，包含 SCRATCH，附加 steps 和前向更新标记。

[TrajectoryFileWriter.build][trajectory-write] 在 `exact=None` 时按 `sim.n_envs<=1` 选择 exact；`n_envs=1` 虽有 batch 轴，仍走 exact，不能只套用 options docstring 的“batched=compressed”。帧按字段顺序打包成字节，XOR 差分和分块压缩；完整 chunk 有校验，末尾不完整 chunk 不算完整帧。写入线程最多与当前 chunk 并行，等待前一块写完的背压机制不同于普通 CSV/NPZ 的队列丢旧策略。

[Trajectory.frame/time/seek/play][trajectory-read]返回解码字段、每环境 steps×dt；普通帧数组可为缓存字节块的视图，需修改或独立持有时 copy。`seek` 按 exact/compressed 所选字段恢复，末帧虽然提供额外 scratch 供读取，seek 仍按所选集合恢复。`play` 是连续 seek 并按需要刷新 viewer/节拍等待，**不是重新提交历史动作并调用物理积分**。

文件头记录 [version/source_digest/backend/precision/dt/layout][trajectory-header]，但 `source_digest` 是包内 Python 文件内容的截短摘要；[实现][digest]不是 Git SHA，也不覆盖所有 native 二进制、驱动或外部资产环境。[加载器][serialization-load]对来源差异会警告，不意味着拒绝所有不同版本，也不意味着跨版本运行一致。固定 backend、依赖、资产和外部任务状态之后，仍需未来运行验证才能声明可重复续跑；本轮只验证实现和身份链。

## 8. 记录器：采样时点、拷贝、线程和结束落盘

[Scene.add_recorder/start_recording][add-recorder]在 build 前注册，build 后由 manager 启动。原生 options 使用 `gs.options.recorders.CSVFile/NPZFile/TrajectoryFile`；[recorders namespace][recorder-registry]也重导出这些 options。普通 data_func 在步进线程采样，经 `data_to_array` 变成主机对象，然后才交给后台 process。readback 的时间不因后台写文件而消失。

[Scene.step/stop_recording][scene-step] 的顺序为：pre-step callback → recorder → physics/sensors → visualizer → camera recording。停止时还强制记录最后状态，不受采样频率筛选；全场景 reset 前也会记录终点，局部 reset 则不自动添加这样一个全场景终点。最终步和 reset 周围可能存在相同时间戳的不同采样阶段，不能仅用 timestamp 去重。

普通记录器的频率由 [Recorder.__init__/step][recorder-sampling] 量化为

$$
k=\max\left(1,\operatorname{round}\frac{1}{f_{\mathrm{requested}}\Delta t}\right),\qquad
f_{\mathrm{actual}}=\frac{1}{k\Delta t}.
$$

这里频率单位 Hz，$\Delta t$ 是外步长，`hz=None` 表示每步。`global_step % k == 0` 决定采样；生成的 timestamp 是 tape 游标×dt，可能随着 Scene.reset 回退。它不是每个环境自 episode 开始的时间，也不是壁钟或硬件同步时间。日志应另存 capture ID、每环境时间、episode ID 和阶段标签。

[普通队列][recorder-queue]在满时等待 `buffer_full_wait_time`，仍满就丢弃最旧采样；[默认选项][recorder-options] `buffer_size=0` 是无界队列。没有“后台线程保证不丢帧且内存不涨”的机制。[reset][recorder-reset]主要等待已有任务处理，并不会让 CSV/NPZ 自动按 episode 换文件；[manager.reset][recorder-manager]也没有自动创建新文件名。

[CSVFileWriter][file-writers]把数组展平成一行；没有额外 schema 就丢失 B×D 的形状解释。NPZ 保留每个 key 的序列，直到 cleanup 才 `np.savez_compressed`，内存随总数据量增加；即使队列很小也不限制 `all_data` 的增长。不同帧 shape 变化还可能退到 object 数组。它按引用存储传入数组，CPU tensor 转 NumPy 未复制时仍可能被调用者覆盖。使用原创例子的显式 CPU copy；对长期日志应先制定分块/文件生命周期，不能把短教学例子当采集系统。

调用方在结束路径执行 `scene.stop_recording()`，等待处理和 flush，并处理在 step/sync/stop 才冒出的后台错误。`.gstraj` 自己分块且有 max_size 机制；越过限额会封存已有记录并在后续推进报告错误，不能把“文件存在”当成计划帧全部保存。第 7 节的身份、帧数和时间序列检查仍然需要。

## 9. 原生最小例子与数据契约

[batch_data_api.py](../examples/batch_data_api.py)是原创、未执行的函数式教学片段，只做语法检查：

- `copy_transition_before_reset` 供已有任务在 **step 后、任何自动 reset 之前**调用，接收调用者的 obs/action/reward/next_obs/flags，连同 native qpos/v 和每环境时间做独立 CPU 副本。它不自动发现终止，也不能补回 Go2Env.step 已经丢掉的终止观测。
- `register_state_log_before_build` 给已有 Scene 注册 NPZ 状态记录器，闭包里的 capture index 单调递增，记录 per-env time/qpos/v。它故意只是状态日志，没有把自动 pre-step 采样伪装成 RL transition。调用者仍需提供场景/关节 schema、episode 信息和结束落盘。

对固定 B、固定机器人，建议把文件 schema 写成下表；不同机器人/任务另存 schema，不靠列序猜测。

| 元数据 | 必须解释的内容 |
|---|---|
| 来源身份 | Genesis 版本/固定 Git SHA、native/binding/依赖版本、backend/device、precision、资产内容摘要/许可、导入选项 |
| 数值配置 | dt/substeps、solver/integrator/contact/friction 配置、容差/限额实际值；不能只保存配置类名 |
| 数组 schema | B、q/DOF/joint/link 名字与本地索引、dtype、每列单位、坐标系、四元数顺序 |
| 时间与 episode | 单调 capture index、env ID、episode ID、episode step、per-env time、采样阶段、壁钟来源及偏差 |
| 输入与观测 | 请求动作/实际延迟动作/原生目标/实际驱动力的区别；传感器校准、曝光/采样/延迟模型 |
| 结束与恢复 | terminated/truncated/错误条件原值、terminal obs/reset obs、采用的 reset 和恢复范围 |
| 随机性 | seed、实际参数样本、RNG/外部控制器状态是否保存；未保存就明确缺项 |

原始数据、渲染视频、策略 checkpoint 和物理 checkpoint 分别链接，避免把其中一个文件当成其他三个的证明。本轮没有产出这些运行数据。

## 10. sim-to-real：原生可配置与实物已标定是两件事

一拍延迟、摩擦范围、质量扰动、图像噪声都是模型假设。真实系统还包括 actuator 动态/饱和/迟滞、网络抖动、传感曝光与时间同步、柔性和装配偏差。E2 的目标与实际驱动力区分、E3 的材料组合律、E4 的测量 frame/延迟边界要进入同一数据 schema：例如逐 link 摩擦倍率不是直接测到的一对表面摩擦系数，触觉估计也不是校准后的硬件力读数。

随机化分布应来自后续辨识或测量，并记录相关性：质量与惯量、相机内参与分辨率、延迟与控制周期不能任意拆散。训练分布更宽不构成稳健性证明；相同数值 seed 也不证明实机对应。这里仅提供接口和失配分析，外部硬件标定、训练效果和 sim-to-real 性能均未验收。后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab) 的原版本/工况/配置，不用本章默认值补其历史实验，也不新增评分体系。

## 11. 性能与扩展：先明确边界，再解释数字

[Scene.timings][timings] 和 [FPSTracker][fps]按主机 `perf_counter` 记录分阶段墙钟。`ProfilingOptions.timings_window` 指定最近窗口；每个 phase 只对实际运行过该 phase 的步骤取平均，暂停/被 veto 的步骤不等同正常 physics step。[ProfilingOptions][profile]

| 阶段 | 会包含什么 | 常见错误读法 |
|---|---|---|
| 初始化/build | 资产处理、分配、JIT/试步与 reset、renderer 初始化 | 用一次冷启动总时长当稳态每步成本 |
| physics | native solver 的外步/子步调用 | GPU 上主机发起 kernel 的时间当成独占设备执行时间 |
| sensors/rendering/video | sensor 更新、viewer、camera 编码各自路径 | 关闭 viewer 就当所有渲染/图像传输都消失 |
| recorders | 步进线程采样与设备读回/排队 | 后台文件 IO 不在该计时内就当没有开销 |
| policy/任务代码 | 通常在 Scene.step 之外 | Scene.timings.total 代表完整训练一轮 |

CPU 阶段计时可按执行位置解释；GPU kernels 异步完成，tracker 没用设备事件替每个阶段同步测量。发生 readback 的 total 包含相应等待，但不能因此把每个 phase 当GPU kernel profile。嵌套 phase（例如 sensors 与某一 sensor 类）不能全部相加。任何性能结论都需未来明确同步点、计时范围、冷/热阶段、B、模型/接触密度和图像输出；这里没有性能数字。

若一次批量外步墙钟为 $T_{\mathrm{wall}}$ 秒，可区分

$$
\mathrm{throughput}=\frac{B}{T_{\mathrm{wall}}}\ \text{environment-steps/s},\qquad
\mathrm{RTF}_{\mathrm{per\ env}}=\frac{\Delta t}{T_{\mathrm{wall}}}.
$$

总环境步吞吐不能当成单环境实时倍速。内存则至少随 batch 状态与容量增长；简单状态 float 数组 N 个元素、B 个环境、每元素 w 字节需要 NBw 字节，尚未计接触/约束容量、梯度缓存、图像、Torch副本和日志。这是量纲估计，不是显存测量。

[CPU/GPU 并行选择][parallel]在 CPU 默认 `PARA_LEVEL.NEVER`，GPU 小 batch/大 batch 选择不同级别，可受环境变量覆盖；它表达 native 调度选择，不是 Python 多线程、进程或多 GPU 扩展自动完成。场景独立进程仍需明确全局 init、设备分配与数据同步，不能让多个线程无约束写同一 Scene。

已有扩展点应直接使用：[pre-step callback][callbacks]在步进线程执行，可返回 True veto 本次推进，viewer 仍能刷新；适合明确的控制/交互生命周期，不是并行物理线程。自定义记录器可用 [register_recording][recorder-manager] 关联 options 类型和 Recorder，分别实现采样/处理/cleanup；后台 process 只处理已交付的主机数据，不跨线程查询/修改 GPU 仿真。添加新 solver、耦合器、可微算子是更深的内部扩展，需要单独证明状态与梯度契约，留 E6，不能由一个回调推出“任意模块可插拔”。

学习也分两条：外部策略优化通过 task step 收集数据，不要求可微物理；通过 Genesis tape 对动力学反传则受 E3 的材料/约束与 E4 的 sensor/rendering 边界限制。导出为 NumPy、离散 reset/终止选择、uint8 图像都不能直接当成保持端到端梯度的算子。B6 在此完成执行、数据、性能解释及现有扩展入口；多物理/可微内部推导仍待 E6。

## 12. 阅读练习与答案

1. **B=1 可以去掉所有 batch 轴吗？** 不可以；`n_envs=1` 是 `(1,...)`，只有 `n_envs=0` 的公开读数才按非批量返回。
2. **只 reset 第 3 个环境，其他环境是否“完全没变”？** 刚体选定状态行/每环境 steps 可局部恢复，但全局 tape 游标、可视缓存及梯度生命周期有变化；任务 buffer 是否局部处理另查代码。
3. **用 `[True, False]` 选第一个环境可以吗？** 不作为布尔 mask 使用；改为形状 B 的 Torch/NumPy bool 或明确整数索引。
4. **Go2 中 20 s 的 episode 到哪步超时？** max_episode_length=1000，严格大于在第1001步为真；同时失败不能被 timeout 原因覆盖。
5. **Go2 返回 done=True 时，返回 obs 是否就是撞地瞬间？** 不是，它先 reset 再构造 obs；需在自动 reset 之前另存 terminal obs。
6. **把 latency 配置改 False 就关闭 Go2 延迟吗？** 这个固定版本不行；构造函数硬编码 True。Hover 的同名开关也不证明实际执行分支用它。
7. **为什么保存动作和 seed 仍不足以复现？** 还缺初始/模型状态、动作延迟、控制器/任务/RNG状态、版本/资产/数值配置；同 seed 的抽样调用顺序也会改变。
8. **CPU tensor.detach().cpu().numpy() 可直接交异步 NPZ 吗？** 仍可能共享存储，原地更新会污染历史；应交独立 copy，并控制总缓冲规模。
9. **Scene.reset 后 mass 和 friction_ratio 都回默认吗？** 普通 SimState 不恢复质量 INFO，而刚体 state 包含 friction_ratio；恢复的是所选 state 的值，不必是默认值。
10. **质量乘 2 后惯量自动乘 2 吗？** `set_links_mass` 默认 scale_inertia=False；即使显式同比例缩放，也要说明几何不变、质量分布同比例的假设。
11. **exact 轨迹每帧都包含全部 SCRATCH 吗？** 普通 exact 帧没有，末 checkpoint 包括；seek 仍按其 exact/compressed 集合恢复，外部策略/任务状态也不在其中。
12. **play 回放一致证明重新积分一致吗？** 不证明；play 连续 seek 已记录状态，没有用控制输入重跑求解器。
13. **dt=.02 s、要求 30 Hz，普通 recorder 实际频率是多少？** round(1/(30×.02))=2，每2步采样，25 Hz；停止附加末帧可能不在该周期上。
14. **队列容量 10 能把 NPZ 总内存限制成 10 帧吗？** 不能；NPZ.all_data 仍累计到 cleanup；满队列还可能丢旧帧。
15. **所有 Scene.timings 相加是否得到训练耗时？** 不能，phase 可嵌套、GPU异步，外部策略/任务代码在 step 之外。
16. **异构 morph 支持不同 DOF 数的机器人吗？** 不支持该用法；固定 description 检查同 link/joint/DOF结构并拒绝多根，变体几何和惯量不是任意拓扑替换。

对应 [Issue #6](https://github.com/huangkiki/genesis-atlas/issues/6)，检查与剩余边界见 [E5 验收记录](e5-acceptance.md)。来源身份统一收录 [sources.json](sources.json) 与[源码地图](source-map.md)；E6 继续多物理、可微与特色子系统，E7 再审校完整课程及 DexLab 复用入口。

[parallel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L894-L944
[sim-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L376
[env-index]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1825-L1850
[index-helper]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L938-L1005
[broadcast]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L1023-L1109
[hetero-types]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/description.py#L326-L360
[hetero-check]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/description.py#L409-L475
[hetero-entity]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L136-L190
[hetero-dispatch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1011-L1064
[hetero-attach]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L320-L332
[scene-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L947-L994
[rigid-state]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L1765-L1934
[sim-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L246-L267
[clock-fields]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L524-L604
[init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py#L57-L289
[build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L831-L892
[getters]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py#L1388-L1398
[qd-torch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L765-L826
[array-convert]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L434-L460
[go2-all]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_env.py#L1-L277
[go2-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_env.py#L155-L207
[go2-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_env.py#L207-L277
[go2-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_env.py#L15-L146
[train]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_train.py#L1-L61
[train-config]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_train.py#L64-L139
[train-main]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_train.py#L142-L172
[eval]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_eval.py#L1-L52
[hover]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/drone/hover_env.py#L15-L206
[random-demo]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/rigid/domain_randomization.py#L1-L98
[link-info]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2273-L2431
[random-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2433-L2452
[friction-api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L3267-L3291
[dof-info]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L2599-L2700
[seed]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py#L239-L289
[seed-helper]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py#L162-L169
[export-check]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1538-L1634
[sim-serialize]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L269-L308
[save-load]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1694-L1777
[restore]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1788-L1823
[data-kinds]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/array_class.py#L120-L145
[trajectory-kinds]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/trajectory.py#L53-L155
[trajectory-write]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/trajectory.py#L210-L355
[trajectory-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/trajectory.py#L474-L567
[trajectory-header]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/trajectory.py#L157-L185
[digest]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/serialization.py#L326-L341
[serialization-load]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/serialization.py#L608-L674
[add-recorder]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L618-L663
[recorder-registry]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/__init__.py#L1-L6
[scene-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1060-L1104
[recorder-sampling]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/base_recorder.py#L25-L49
[recorder-queue]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/base_recorder.py#L219-L267
[recorder-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/base_recorder.py#L81-L100
[recorder-manager]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/recorder_manager.py#L94-L152
[file-writers]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/file_writers.py#L89-L180
[recorder-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/recorders.py#L21-L40
[profile]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/profiling.py#L1-L25
[timings]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1872-L1888
[fps]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/tools.py#L191-L302
[callbacks]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1053-L1091
