# 批量、学习接口与数据：从 Scene 隔离到可复现轨迹

本章覆盖 A8、A9 和 B6 的并行、数据移动、学习接口及扩展责任。先读 [E1 状态与时间](modeling-state-time.md)、[E2 控制与机器人](control-robotics.md)、[E4 传感与渲染](sensors-rendering.md)；涉及原生收敛与 CUDA 线性求解时参照 [E3](contact-solvers-forces.md)。先修是数组维度、进程/线程、概率分布和基本控制。阅读后应能说明一个批次中每个环境究竟拥有什么、每条 transition 在哪个时刻采样，以及哪些文件足以支持哪一种回放。

SuperDex 基线仍为 `1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。[Lab 包定义][package]为 `superdex-lab==1.0.0`，依赖 Physics/Robotics 1.0.0 与 `gymnasium>=1.1.1`；本章为了精确解释外部 vector 行为，另固定 [uv.lock][lock] 所选 Gymnasium 1.3.0 的官方提交 `53bf3e9a884783eb72ad3fc8b15780914c97c3e1`。最低依赖约束不等于锁定版本，读者换版本后必须重新核对契约。

**所有例子仅经源码与语法核对，未 import 原生包、创建模型、步进、渲染或训练。** 没有吞吐、学习收敛、跨机器确定性或 sim-to-real 成功率结果。[验收记录](validation-e5.md)逐项区分这些边界；实验后续复用 DexLab。

## 1. 学习接口属于哪一层

| 层 | 本章实际入口 | 不应从名称推断的能力 |
|---|---|---|
| Physics | `Scene.step`、状态 capture/restore、原生查询、HDF recording、`diffsim` | 不是直接接受 `[N, ...]` GPU tensor 的 Gym 环境或训练器 |
| Robotics | Bot、控制器、传感器元数据及资源生命周期 | 没有把策略、奖励、自动 reset 变成物理内核功能 |
| Lab | `MochiEnv`、具体任务、`HybridVectorEnv`、RLlib/数据应用样例 | 进程/串行批量组织不等于内核 GPU 多世界并行 |
| Studio / viewer | 资产、调试和图像宿主，详见 E4 | GUI 画面、视频与物理状态 checkpoint 含义不同 |
| 外部学习组件 | Gymnasium 协议；样例导入 Ray RLlib、Torch、LeRobot | 不属于 SuperDex Physics；本章没有验收它们的可安装组合或训练结果 |

[Lab README][lab]明确 benchmark 资产不随 `pip install superdex-lab` 打包；官方仓库资产及 `SUPERDEX_ASSETS_PATH` 等解析入口仍需配置。这里沿用官方任务作阅读对象，不新增任务框架或跨引擎接口。[包声明][package]要求 Python `>=3.12,<3.13`；Ray/Torch/LeRobot 不在这份核心依赖列表中，不能因为样例存在便假定最小安装已经带齐训练依赖。

## 2. 一个 Lab step 究竟产生什么

### 2.1 控制周期和物理子步

[MochiEnv][env]检查仿真频率 $f_s$ 是控制频率 $f_c$ 的正整数倍。单位均为 Hz，设 $h$ 为物理步长、$H$ 为控制周期：

$$
h=1/f_s,\qquad H=1/f_c,\qquad M=f_s/f_c\in\mathbb{N}_{>0},\qquad H=Mh.
$$

一次 `step(action)`：Box clip → `to_structured_action` → 恢复共享场景状态（若启用）→ 重复 $M$ 次 `_apply_action(action)` 与 `Scene.step(h)` → 保存场景状态 → 增加控制计数 → `_make_observation` → `_compute_reward_terms` → `_check_stop_criteria` → 缓存/可选 render → 返回 `StepResult`。`get_control_to_simulation_ratio()` 名字容易误读，实际返回 $M=f_s/f_c$，不是其倒数；`get_control_frequency()` 的一条 docstring 把整倍关系写反，应以构造校验为准。

令 $x_{k,j}$ 为第 $k$ 个控制周期、第 $j$ 个子步开始时的完整动力学状态，包含所需积分历史；$a_k$ 是本次结构化动作。教学表示为：

$$
x_{k,j+1}=F_h(x_{k,j},u_{k,j};\theta),\quad
u_{k,j}=C(a_k,x_{k,j}),\quad j=0,\ldots,M-1.
$$

其中 $u_{k,j}$ 是原生控制输入，$\theta$ 是持续模型配置。`_apply_action` 每个子步重新调用，所以 PD 控制器可以根据更新后的状态重算驱动力；只能说策略动作保持，不能保证驱动力恒定。直接力任务则可能重复同一力命令。下一观测为 $o_{k+1}=G(x_{k,M})$，不是输入动作前的 $o_k$。

### 2.2 CartPole 把空间、量纲、奖励串起来

[官方 CartPole][cartpole]配置 $f_c=25$、$f_s=50$，所以 $H=0.04\,\mathrm{s}$、$h=0.02\,\mathrm{s}$、$M=2$；这只是源码默认配置，不是本仓运行记录。`control` 的 Box 为 `[-3,3]`，`force_scale=100`，通过 `set_external_forces_on_dofs` 作用在选定 DoF。默认平移 DoF 的广义力是 N；选择杆的旋转 DoF 后是 N·m，不能因变量名叫 `force` 就继续标 N。动作空间的数值本身不是统一 SI 力单位。

四个观测字段是 `position`（m）、`vertical_ang`（rad）、`linear_vel`（m/s）、`angular_vel`（rad/s）。它们各自声明 float32 Box。Lab 通过普通 dict 构造 Gymnasium Dict；固定版本 [Dict][dict] 对可比较的键排序，[flatten][flatten]按 space 顺序转换并拼接，因此实际扁平向量顺序为：

```text
[angular_vel, linear_vel, position, vertical_ang]  shape=(4,), float32
```

不能按 `_setup_observation_space` 的书写顺序解码。用原生 `to_structured_observation` / `to_observation` 保留既定映射，并把字段、顺序、shape、dtype、单位一起存档。`mochi_helpers` 使用 `DynamicArrayReal` 接收原生数据，再 `np.array(buffer)` 复制；即使内核是 FP64，CartPole 的 Box flatten 仍转 float32。策略观测 dtype 不能证明内核精度。[helpers][helpers]、[types][types]给出这两层契约。

基类用 `np.clip`处理范围，没有将NaN修复成合法动作；正常返回一组Gym结果也不是物理收敛声明。该路径没有自动读取E3的solver状态来定义任务失败，派生环境需要按原生求解状态和数据有限性制定明确策略；不能把无效状态继续混入普通训练transition。

CartPole 在 $|\alpha|\leq0.2\,\mathrm{rad}$ 时每个控制步奖励 1，否则 0。基类返回 `sum(reward_terms.values())`，不是对子步自动积分。若目标是累计“直立秒数”，应用应有意识地使用 $H r_k$；改变 $f_c$ 而保持“每步 1”会改变同一物理时长的回报。该说明解释量纲，没有修改官方任务。

### 2.3 reset 有物理推进，终止与截断是两个位

`reset(seed)`先调用 Gymnasium 基类种子逻辑，重置 Python episode/step/flags，恢复初始原生状态并施加 reset 噪声，然后执行 **`Scene.step(1e-5)` 秒** 初始化接触等依赖步进的数据，最后采样初始观测。于是 `get_step_count()==0` 不证明 native 时间为零。$kH$ 只表示 reset 后已经完成的控制时长，不能代替 `Scene` 的物理时间，更不能代替墙钟或图像曝光时点。

基类 `_check_stop_criteria` 在计数等于 `steps_per_episode` 时置 `truncated=True`，CartPole 倒下置 `terminated=True`。达到时间限制且倒下时，两位可以同时为真。`-1` 表示不设这个步数限制。终止后继续调用裸环境 `step` 不会获得规范自动 reset；基类判断是等号，也不能依赖它持续替应用重复报告时间边界。

价值目标的常见教学形式（只用于解释标志，不是新增训练实现）是：

$$
y_k=r_k+\gamma(1-d_k)V(o_{k+1}^{\mathrm{terminal}}),
$$

其中 $d_k$ 表示真实任务终止，$\gamma$ 为每个控制步的无量纲折扣。若 truncation 只是采样时间限制且任务仍可继续，一般需要 bootstrap；若任务本身就是有限时域，应把剩余时间纳入状态并按该任务定义终止。无论采用哪种算法，不能把下一 episode 的 reset 观测替代上式本次转移的末端观测。[Gym Env 契约][gymcore]与下节 autoreset 分支一起阅读。

## 3. 三种隔离不是同一回事

### 3.1 独立 Scene

`use_shared_scenes=False` 时，每个环境创建自己的 Scene/Actor，保存自己的初始快照。相互没有刚体接触不等于线程安全：[Physics API][api]规定 Scene 同时只由一个线程访问，读写同步；不同场景可交给不同线程。进程全局 Physics context、Robotics context、文件缓存和 viewer 仍有自己的作用域，不随每个环境复制。

[跨线程官方例子][cross]先把源状态复制成字节，再让每个 worker 创建自己的兼容 Scene 并恢复；它没有让两个线程并发读写同一个 Scene。`StateHandle` 属于捕获它的 Scene，不能直接拿到另一 Scene；跨场景/进程要用 `capture_state_to_bytes` 等明确的数据接口，并满足同 build、相同 Actor/constraint 创建顺序和布局等兼容要求。

### 3.2 共享 Scene 的时间复用

`use_shared_scenes=True` 是 Lab 默认。每个进程中的 [SceneManager][manager]按环境类名字找到 manager，再按派生环境给出的 `scene_name` 找 Scene。同组环境共享 Scene、Actor 和初始快照，每个环境单独持有当前 `StateHandle`、Python 计数、RNG 和上次 observation/action 等缓存。第一个环境步进完保存状态，第二个恢复自己的状态后继续；逻辑上像多个环境，执行上是同一场景依次切换。

正确隔离要求完整状态可写为：

$$
z_i=(x_i,p_i,\rho_i),\qquad \theta_i=\theta_{\mathrm{shared}},
$$

$x_i$ 是 capture 覆盖的原生可变状态，$p_i$ 是环境私有 Python 任务状态，$\rho_i$ 是各自 RNG 状态，$\theta$ 是共享的持续配置。这里不是宣称 `capture_state` 序列化整个 $z_i$；恰恰是把三者区分开。

[API][api]说 capture 包含 Actor solution/transform/velocity、当前和历史 controller/constraint targets、external forces；restore **不创建/销毁 Actor/constraint，不恢复 shape/material/Scene 参数**。Python reward 累计、任务阶段、噪声生成器、策略隐藏状态、viewer、文件句柄也不由这个 Physics 快照管理。ROM 场景不支持该 capture。模型配置变动、非快照缓存或回调闭包共享都可能破坏隔离。

SceneManager 的 key 没有自动校验整个 cfg。CartPole 仅将 damping/gravity/free_pole 三项组成场景 key；这是该任务对哪些字段会改变 Scene 的决定，不是通用配置指纹。派生任务若增加质量/摩擦随机化，要让不同持续配置拥有独立 Scene，或在**每次切换**完整恢复相应配置并核对所有相关缓存；仅在 reset 时改共享 material 会影响之后恢复状态的其他环境。修改 topology 则不能沿用旧快照。禁用共享往往更容易保证清楚的所有权，本章不据此给性能建议。

还有两个采样陷阱：`get_last_step()`返回本环境的缓存结果，而任意时刻直接读取共享 Scene 可能是最后一个执行者的状态。在基类 `MochiEnv.render()`路径中没有恢复当前环境快照，默认 `_update_renderer()`为空；CartPole 沿用这一条 render 路径，没有重写该 hook 来恢复快照。因此共享 CartPole 的 A.step → B.step → A.render，或批量全部 step 完后再逐个环境直接读 Actor，不能自动得到各自状态。human 模式在每个环境自身 step 尾部 render，此时仍是它刚推进的 Scene，是不同的调用时序。这个风险由所读具体路径推出，不推广到自行重写 render 的所有派生类，也没有执行验证。需要明确的场景切换和 render 调度，或独立 Scene；不应从外部偷偷改私有 `_state_snapshot`。

### 3.3 资源销毁也是隔离的一部分

manager 使用 refcount；只有最后一个使用者关闭时才销毁 Scene。可登记的 scene-owned cleanup callbacks 逆序执行，适用于 Bot 等外部 owner。若 cleanup 失败，`destroy_scene_with_cleanup` 会保留 Scene 并报错，避免销毁仍被引用的 Actor；不能把异常吞掉当成正常释放。视觉注册也要清理，避免回收的 handle 指向旧模型。[共享测试][sharingtest]覆盖创建者先关闭等预期；其中批量确定性测试只检查发现到的任务，且无 `agent_pose` 的任务会跳过。本仓仅阅读测试，没有执行，也不宣称它证明所有任务隔离。

`MochiEnv.close()`先关 renderer，再在 Physics context 仍存在时释放 Scene；它没有关闭进程全局 Physics context。应用应先停止采样/关闭 env 和 viewer，再由 context owner 在初始化线程 `shutdown`，不要关闭一个 env 就销毁其他 env 使用的全局 context。

## 4. HybridVectorEnv 的真实批量结构

[官方 wrapper][vector]把 $N$ 个环境分为 $P=N/K$ 个进程，每进程 $K$ 个环境串行运行；要求正的 $N,K$ 且 $N$ 可被 $K$ 整除。外层 `AsyncVectorEnv` 通过 `spawn` 建 worker，内层 `SyncVectorEnv`依次执行每个环境，内层才负责 autoreset。强制 `spawn` 是为了避免复制已有 native 线程引起的 fork 死锁；这不是用户可任意替换的性能开关。

```text
parent: actions[N,d_a] / observations[N,d_o]
  └─ AsyncVectorEnv: P worker processes, outer autoreset DISABLED
       └─ each SyncVectorEnv: K sequential MochiEnv instances
            └─ private Scene, or SceneManager + K state snapshots
```

逻辑环境索引 $g=pK+j$，其中 $0\leq p<P$、$0\leq j<K$。wrapper 将 `[P,K,...]` reshape 为 `[N,...]`，假设所有环境有相同 bounds 的 Box observation/action space；它不是任意嵌套 Dict 的通用批处理器。`step`要求 NumPy 数组和精确 batch shape；reward/terminated/truncated 都是 `[N]`。info 通过定制 `_add_info` 展开，`_字段名`为有效掩码，缺失字段不能按零或旧缓冲值解释。

Gymnasium 的 [Async 构造][async]还会在父进程临时创建第一个 factory 的环境以检查 space，再关闭它；因此 factory 不能假设只在 worker 中调用。它可能初始化父进程的 Physics context，关闭 dummy env 也不会自动 shutdown 全局 context。初始化、配置环境变量、`if __name__ == "__main__"` 保护、异常时 close 都需要明确所有权。不要在 factory 中依赖父进程活的 Scene/Actor、相机连接或原生句柄。

### 4.1 NEXT_STEP 与 transition 对齐

[SyncVectorEnv 1.3.0][sync]有三种模式；Hybrid 默认内层 NEXT_STEP、外层 DISABLED。

| 内层模式 | 本次结束步返回 | 下一次调用对该槽做什么 | 数据集责任 |
|---|---|---|---|
| NEXT_STEP | 最后观测、真实 reward 和 done flags | reset，返回初始观测、reward=0、flags=False，本次给它的 action 不执行 | 用前一次 done 掩码识别 reset-only 槽，不能把它作为动作 transition |
| SAME_STEP | done flags/reward 属于旧 episode；主 observation 已是新 episode 初始值 | 正常处理新 episode 动作 | 旧末端观测取 `final_obs`，额外信息取 `final_info`，核对对应有效掩码 |
| DISABLED | 最后观测与 done flags | 若未 reset 就继续 step，会拒绝 | caller 自己 reset；Hybrid 不支持 `options['reset_mask']`，不能凭空只重置单槽 |

对 NEXT_STEP，设 $D^{\mathrm{prev}}_i$ 是上次调用该槽的 terminated 或 truncated，$v_i$ 表示本次确实执行了动作：

$$
v_i=1-D^{\mathrm{prev}}_i.
$$

先用**旧**掩码决定本次是否收 transition，再以本次 flags 更新掩码。首次显式 reset 后全部槽有效；刚结束的本次 transition 仍然有效，排除的是下一次 reset-only 调用。`HybridVectorEnv.metadata`来自外层，可能显示 DISABLED；不能仅看它推断内层实际模式，应存构造时的内层 `autoreset_mode`。带 RNN 的策略还要在 episode 边界重置隐藏状态，重置槽本次推理动作即使算了也不会被执行。

### 4.2 seed 两级展开会怎样

Hybrid 收到 seed list 时，按 worker 切成长度 $K$ 的列表交给 Async；int 则直接透传。[Async][async]将整数 $s$ 展开为 worker 的 $s+p$，各内层 [Sync][sync]再展开成 $s+p+j$。因此两个维度相加会碰撞：$N=4,K=2,s=100$ 得到 `[100,101,101,102]`，而非 `[100,101,102,103]`。这是固定版本代码的推导，没有运行采样。

明确传入按逻辑环境顺序排列的列表如 `[100,101,102,103]`，才能避免这个展开造成的重复。不同 seed 只是不同初始化，不是数学独立性证明。`reset(seed=None)`延续已有环境 RNG 序列；每个 episode 都重新传同一整数会重新开始相同序列。[Gym core][gymcore]的 env RNG 不会替 `action_space.sample()`、Python random、外部策略或自建生成器统一播种；官方[共享测试][sharingtest]也单独调用 `action_space.seed`。

下面是原创的最小原生阅读片段，依赖官方 Lab 资产、正确安装和 `spawn` 可导入脚本。**本轮不执行，调用构造/reset/step 都会运行物理。** 片段只读一个有效批次，不隐藏后续 autoreset 规则；precision 环境变量应在这些 import 前由启动环境设置。此独立脚本拥有父进程 context，嵌入已有应用时不能照搬最后的 shutdown 所有权。

```python
import numpy as np
import superdex.physics as physics
from gymnasium.vector import AutoresetMode
from superdex.lab.gym.envs.benchmarks.cartpole_env import CartPoleEnv
from superdex.lab.gym.utils.vector import HybridVectorEnv


def make_cartpole():
    return CartPoleEnv({"render_mode": None, "use_shared_scenes": True,
                        "num_worker_threads": 0})


def main():
    try:
        with HybridVectorEnv([make_cartpole] * 4, num_envs_per_worker=2,
                             autoreset_mode=AutoresetMode.NEXT_STEP) as envs:
            initial_obs, reset_info = envs.reset(seed=[100, 101, 102, 103])
            actions = np.zeros(envs.action_space.shape,
                               dtype=envs.action_space.dtype)
            next_obs, reward, terminated, truncated, info = envs.step(actions)
            # This first post-reset call applies all four actions.
            # Save copies before later calls; track done masks for NEXT_STEP.
            batch = {"observation": initial_obs.copy(), "action": actions.copy(),
                     "next_observation": next_obs.copy(), "reward": reward.copy(),
                     "terminated": terminated.copy(), "truncated": truncated.copy()}
            return batch
    finally:
        if physics.is_initialized():
            physics.shutdown()


if __name__ == "__main__":
    main()
```

## 5. CPU、GPU 与拷贝：沿数据路径分账

### 5.1 Gym batch 不等于 GPU resident state

[Async][async]默认 shared_memory/copy 都为 True。共享的是 CPU 观测缓冲，actions/控制消息仍经进程管道；外层等 worker 回复，不能由名字 Async 推断 Python `step()`无阻塞。`copy=False`可让返回 observation 借用会被下次调用覆盖的缓冲；保存长期轨迹必须拥有自己的副本。内层 Sync 默认也复制 observation，Hybrid reshape 本身不保证重新分配。不能把返回数组的一个 view 当成冻结记录。

[helpers][helpers]的原生输出缓冲→NumPy copy、[flatten][flatten]的 dtype 转换/拼接、共享内存读写和外部学习框架的 device transfer 是不同成本。策略在 GPU 并不能推出物理状态在 GPU；把 NumPy 观测送到外部 tensor device 也没有自动生成从策略 loss 到 Scene.step 的梯度图。

### 5.2 原生 CUDA 是具体线性子问题分支

[LinearSolver::CudaIterativeSolve][linear]在 `MOCHI_USE_CUDA` 且 matrix 类型支持时，将 $A$ 转成 CUDA 矩阵，将 $b,x$ 转成 `CudaVector`，建立 CUDA preconditioner，运行 CudaCG 或 CudaGMRES，最后 `x = xCuda` 拷回 CPU。实验性稀疏直接解法也有自己的 CUDA/cuDSS 构建条件，详见 E3。不能由枚举存在宣称安装 wheel 包含该后端或全场景 GPU 求解。

[CudaPCG][pcg]中还可见 device-to-device 临时拷贝、host-to-device 常量和 device-to-host 状态读回；[cuda_api][cuda]里的通用 copy 用 `cudaMemcpy`。[CSR 实现][csr]根据 `Scalar`选择 CUDA float/double 描述符。这些来源说明设备/同步边界，未测占比或速度。

单个线性子问题的教学成本拆分是：

$$
T_{\mathrm{linear}}\approx T_{A,b,x\rightarrow GPU}+T_{\mathrm{prec}}+
T_{\mathrm{Krylov}}+T_{x\rightarrow CPU}+T_{\mathrm{sync}}.
$$

各项是墙钟时间（秒），不是求解迭代数。host/device 数据量与 dtype、矩阵稀疏结构、迭代分支有关；增大 batch 不能保证摊薄这一内部每次 solve 的开销。不要把渲染 GPU、策略 GPU 和物理线性求解 GPU 合并写成“GPU 后端”。

### 5.3 批量成本、线程、回调和扩展点

若进程并发、每进程串行，理想化批次时长可写为：

$$
T_{\mathrm{batch}}\approx T_{\mathrm{dispatch}}+
\max_p\sum_{j=0}^{K-1}
(T_{\mathrm{restore}}+M T_{\mathrm{physics}}+T_{\mathrm{capture}}+
T_{\mathrm{obs/reward}}+T_{\mathrm{render}})+T_{\mathrm{gather}}.
$$

这是解释瓶颈的模型，忽略争用、通信重叠和非均匀子步，不能当成预测结果。共享 Scene 可减少重复模型常驻量，但每环境快照与 capture/restore 有代价；独立 Scene 则重复模型及缓存。worker 数、每 worker 的 env 数、Physics 内部 worker threads 是三个不同参数；多进程各自开大量线程会竞争同一 CPU。Lab 默认0线程、Physics负值自动选择等属于初始化配置；同进程后创建 env 不会因新的 cfg 重建已存在 context。

[Scene.step][scene]按顺序调用 pre callbacks、动力学/query 更新、post callbacks、recording；同一 Scene 的回调在 step 调用线程顺序执行。把额外控制/记录放进回调会增加该步耗时，不能解释成异步插件。Python task hook `_apply_action` / `_make_observation` / `_compute_reward_terms`属于 Lab 扩展；C++ solver/backend 扩展需要相应构建，本章所读调用链没有提供一个把任意后端热插进已装 wheel 的通用插件 API。

初始化、动态库载入、资产解析、预计算、首个 step、稳定 step、capture、CPU/GPU copy、viewer 和文件 I/O 应分开理解。本路径没有一个“把全部 Lab 环境 JIT 到 GPU”的调用；不能把外部策略编译时间归为物理 JIT。Lab profiler 将原生秒数乘1000放入 `cpp_*` 项（毫秒）；`cpp_total_step`包含内部 solve/回调/录制子项，不能把总项再与子项相加。读取计时字段只是认识边界，本轮没有采集性能样本。

## 6. 学习算法、原生求导与外部 checkpoint

[RLlib 应用][rllib]扫描随任务提供的 `*.train.json` recipe，环境配置来自可命名的 cfg variant；recipe 拒绝另写 `env_config`，以免训练了不可追踪的隐藏配置。它使用 RLlib PPO/SAC、env runners、learners 和 connector；[TrainCfg][traincfg]明示 PPO 是推荐工作流，SAC 是未调优/未验证的实验基线，不能把两者并列为本仓验收结果。

策略学习可以只依赖数值 transition，不需要对物理求导。其随机策略目标可抽象为 $J(\phi)=\mathbb{E}_{\pi_\phi,F}[\sum_k\gamma^k r_k]$；这里 $\phi$ 是策略参数，$\theta$ 是模型参数，两者不同。Gymnasium 返回 NumPy 数组只建立环境交互协议；它不自动连接 Torch autograd，也不暴露一条从动作到整段轨迹的统一 tensor graph。

Physics 确有独立的 [diffsim API][diff]，不是因缺少 Gym autograd 就否定原生求导。`make_scene_differentiable`限定 rigid/articulated actors、Backward Euler，建议 double precision，并会调用 improved-convergence 配置、可能覆盖原设置。反向过程需要 `reset_back_propagation`、对同一原生步的 `prepare_back_propagate(state_new,state_old)`、输出 backward 累加和 `back_propagate`，再提取输入梯度。它对 variable time-stepping 仍有未测试注记。Lab 的每控制步末端快照不自动提供所有 $M$ 个原生子步的相邻状态对，不能直接塞给这条逐步反向链。

数学上，若收敛后的离散残差满足 $R(x^+,x,u;\theta)=0$，可微且 $R_{x^+}$可逆，则隐式函数关系给出：

$$
\frac{\partial x^+}{\partial u}=-R_{x^+}^{-1}R_u.
$$

这说明求导需要离散问题、收敛状态和对应输入，不能对任意 STOPPED/DIVERGED、接触分支切换、clip 边界或 topology 变化承诺同一导数。配置空间还涉及 Lie/quaternion 参数化，不能把4维四元数当成4个独立旋转自由度。此处完整界定学习接入责任；具体 adjoint 装配、梯度转换和特色兼容矩阵仍由 E6 展开。

[CheckpointPolicy 样例][policy]同时恢复 RLModule 和 env-to-module/module-to-env connector，后者包含观测归一化、动作采样与缩放流程。只保存网络权重会漏掉运行统计与动作协议；该文件还有无 connector 的降级路径，不能笼统说任何 checkpoint 都等价恢复。这里描述的是固定 SuperDex 应用代码的意图和分支；没有新增 Ray/Torch 外部实现审查，没有声称某个已安装版本可运行它。训练复现仍须独立记录外部依赖版本、policy schema、normalizer、探索设置、RNN 状态和优化器/采样器状态。

## 7. 随机化必须与模型和量纲对齐

基类 reset 的实现只有 agent 初始关节 pose/velocity 噪声：

$$
q_0=\operatorname{clip}(\bar q+\sigma\,\epsilon_q,q_{\min},q_{\max}),\quad
\epsilon_q\sim\mathcal{U}([-1,1]^n),\qquad
v_0=\bar v+\sigma\,\epsilon_v,\quad\epsilon_v\sim\mathcal{N}(0,I).
$$

一个 `reset_noise_scale`数值同时作用于混有 m/rad 的 pose 和 m/s、rad/s 的 velocity，属于便捷实现，不能解释成一个有统一 SI 单位的物理分布。clip 后在边界可能堆积概率质量，已经不是简单截断后重新归一化的均匀分布。姿态扰动还应按本地参数化和 DoF 语义理解，不能随意对四元数4分量加同一噪声。

下列任务责任应显式拆开：初始状态随机化（$q,v$）、模型参数随机化（质量、惯量、接触、驱动器）、观测噪声/偏置/延迟、渲染外观/相机、任务分布。基类没有把这些全部实现成通用 domain-randomization 管线。若在应用中设计质量或惯量分布，应保持正质量、惯量正定/几何一致；摩擦/耗散按 E3 的材料量纲与**几何平均**组合理解。不要给 stiffness、摩擦系数、阻尼共用一个无单位百分比再宣称模型合理。

以观测延迟为例，可以在应用模型中定义

$$
o_k=G(x(t_k-\delta_k);\theta_{\mathrm{sensor}})+b+\eta_k,
$$

其中 $\delta_k\geq0$ 的单位为秒，偏置 $b$ 和噪声 $\eta_k$ 按各观测分量的单位定义。这个公式是假设的测量模型，不是Lab基类已实现的功能；还要说明噪声是每物理步还是每相机帧抽样、有无时间相关性，以及动作延迟是否另有队列。将旧帧重新标成当前时间会同时污染策略输入和sim-to-real延迟解释。

一次 episode 的持久参数应在 reset 边界确定，随后保存**采到的实际数值**及分布定义/seed，不只保存随机数种子。共享 Scene 尤其要遵守第3节的持续配置不被 capture 覆盖这一点。噪声 RNG 与 reset RNG 可分流，避免新增一项相机随机数后改变所有关节噪声的序列；分流仍是应用责任，不是给现有 API 添加不存在的开关。

sim-to-real 的模型差距包括几何/惯量、接触/摩擦、驱动力与限幅、控制延迟、传感坐标/滤波/采样相位。增大随机范围不等于校准，也不能证明真实分布包含在其中。E2/E3/E4 已有原生接口与量纲，当前课程把它们接到数据契约；后续证据保留 DexLab 原工况，而非以本章随机化假设重新解释历史二进制。

## 8. 保存产物与两种“回放”

| 产物 | 能保存/支持什么 | 明确不保证什么 |
|---|---|---|
| Physics `StateHandle` / bytes capture | 与兼容模型一起恢复支持的动力学可变状态 | 模型、材质、Scene params、Python任务/RNG、跨 build 长期格式 |
| Physics `capture_state_to_file` JSON | 输出状态快照供人工检查 | 固定公开API没有相应JSON restore入口，不能当作可直接恢复的checkpoint |
| 原生 HDF recording | 选定 Actor/query/target 的事件和每步记录 | 完整重建场景、训练 transition schema、逐位重复运行 |
| 学习数据集 / transition | 观测、动作、奖励、done、元数据及媒体引用 | 积分器内部历史、可反向求导状态、可复原全场景 |
| 策略 checkpoint / 视频 | 策略组件/优化状态，或可视结果 | 前者不等于环境快照；视频没有完整状态与控制量 |

`capture_state_to_file`的文件名并不代表通用可恢复存档：[公开stub][api]明确其JSON用于人工检查，`SceneImpl::CaptureStateToFile`调用`CaptureStateToJson`；本章不提供不存在的JSON restore命令。

**播放记录**是展示/分析保存的 pose 或图像；**重新仿真**是用同一模型/状态/控制链再次推进。后一种需要更多身份和状态，不能只凭前者画面相似宣称可复现。

### 8.1 Physics recorder 实际写什么

`Scene.start_recording(path, RecordingParams)`会创建或替换文件，需要 HDF5 支持构建；已有 recording 会先停止。`RecordingParams`可选 dynamic/static state、target state、meshes、local/global map、mass matrix、contact points/node forces/SDF 等。[API][api]注明格式可能变化；`is_recording()`只说明录制会话存在，写入失败不会自动结束会话，因此不能作为文件完整性验收。

[SceneRecorder][recorder]在 `events` group 下按事件序号写 CreateActor/DestroyActor/Step。Step 保存 `timeTotal`、`timeStep`、gravity，Actor 子组按 handle 标识；变换取 `worldFromLocal` 的 translation/rotation，单位/xyzw 需沿 E1 的原生表示解释。选定数据来自物理 step；[Scene.step][scene]先执行 post callbacks，再 `OnStepEnd` 写记录，因此 post callback 若修改状态，文件里的姿态不能自动认作纯 solver 输出。额外 query 的支持也可能因 Actor 类型而被跳过，缺字段不是零值。

[recorder header][recorderheader]的 `_timeTotal`从0开始，`OnStepBegin`累加本次 `h`；它是**本次录制累计时间**，不直接读取 `Scene.get_time()`。中途开始录制、restore、Lab dummy reset 步、`step(0)`、共享 Scene 交错环境都会让“第几条 Step = 某 episode 第几帧”的猜测不成立。录制共享 Scene 会按实际物理调用串行混入各逻辑环境的步骤；HDF 没有自动替你加 Lab logical_env_id/episode_id。应由应用明确关联或使用独立录制场景，不能靠 handle 当成稳定环境ID。

CreateActor 处明确保留“补足 replay 创建信息”的 TODO；meshes 等可选数据也不能补足所有配置。因此原生 recorder 是诊断数据来源，不能宣传为完整场景序列化。recording 结束需 `stop_recording()`关闭文件；检查错误和产物完整性属于将来的实际运行验收，本轮没有创建 HDF 文件。

### 8.2 官方 dataset 样例的适用域

[dataset.py][dataset]导入 LeRobotDataset、其 cache metadata 和 Torch DataLoader，是应用样例，不是原生文件格式契约。`parse_h5`硬编码 robot=76、box=2、lid=4、shape=6，读取特定 Actor 的 translation/rotation 和 robot `targetPose`，还将部分值 round 到5位；其返回结构和注解也不能替代完整 schema。换资产后不能沿用这些 handle；target pose 更不等于一般任务的 action、真实力矩或控制周期输入。该路径没有证明可无损转成任意 LeRobot 数据集，也没有证明所有外部版本兼容。

[采样 runner][runner]组织交互、策略调用及可选视频，并不因此具备完整 checkpoint/replay 语义。图像的 exposure/render/readback 阶段、RGBA、宿主依赖和延迟见 E4；墙钟到达时刻不是物理采样时刻。物理50Hz而相机25Hz时应记录 image capture ID 与原始时间，不用重复帧伪造50Hz独立曝光。

### 8.3 最小原生缓存读取例

[copy_lab_step.py](../examples/copy_lab_step.py)只用 `MochiEnv.get_last_step()`与公开计数/频率接口复制**已经完成的一步**，不推进、reset、渲染或访问私有 Scene。它在 reset 后拒绝伪造 action/reward；调用者在单线程且 env 静止时读取，提供自己的 logical_env_id。输出 `nominal_control_elapsed_s=kH`明确不是 Scene 物理时间。它不含 $o_k$，故单独不是完整 transition；调用者必须另存上一个正确 episode 的 observation，再按 autoreset 规则拼接。

`deepcopy`用于切断上次结果中可复制的 Python/NumPy 缓冲别名；若自定义 `info`混入原生 handle、socket 等不可复制资源，应先在任务中定义数据字段契约，不能靠本例序列化这些对象。本例是教学读取函数，不是数据格式、记录系统或通用 wrapper。

## 9. 可复现契约与 B6 验收边界

一条 transition 至少要能解释以下并列信息：

- **身份**：upstream SHA、wheel/build/precision、Lab/Gym/学习组件版本；模型及资产内容 hash、cfg variant、持续参数实际值。
- **索引**：logical_env_id、episode_id、control step、有效 transition 掩码、字段/DoF 顺序；Actor handle 仅作本次运行内关联。
- **时间**：$h,H,M$，native/episode时间与记录起点的关系、reset dummy 步、图像 capture time 和读取 time；不能只给墙钟字符串。
- **控制与输出**：策略原始 action、经 connector/clip 后 action、原生控制单位/限幅，$o_k,o_{k+1}$、reward terms、termination/truncation 原因；需要实际力时用 E3 查询。
- **随机与状态**：reset/action/模型/观测/策略各自 seed 或可恢复 RNG state，任务状态机、RNN/normalizer、必要的 compatible native snapshot。
- **调度与边界**：进程/线程数、shared scene、autoreset/copy模式、求解器和收敛状态、CPU/GPU/backend与文件完整性记录。

这些是课程中的信息契约，没有新建数据管线或评分器。任务式可复现（能解释相同配置和输入）、数值容差内轨迹一致、逐位一致是不同主张；相同 seed 不控制浮点规约顺序、编译器、backend、线程调度或异步媒体。未运行时只能证明源码/配置身份，不能宣布任何一种轨迹一致性。若未来有运行失败，应保留 DIVERGED/restore失败/缺字段而不是裁掉它们后展示剩余轨迹；restore 失败非事务性，可能已部分改变 Scene，应恢复已知有效状态或重建。

B6 的 CPU/GPU、进程/线程、复制/资源、profiling、hook 与构建扩展入口已在本章形成课程。E6 仍承担可微求解内部、特色 Actor/复杂几何与兼容边界；本章没有提前标记这些实现已讲完。E7 将联合审校两条路线，并引用 DexLab 已有实验而不新建一套实验框架。

## 10. 易错点诊断

| 现象/写法 | 先检查什么 |
|---|---|
| 两个 env 总在同一点初始化 | seed 是否经两级 int 展开重复；是否每 episode 反复同 seed |
| 换 worker 分组后轨迹不同 | seed list、共享 key、context线程数、外部 RNG、调度及精度身份 |
| observation各项看起来数值正常却控制失灵 | Gym Dict排序、单位、动作缩放/clip、normalizer checkpoint |
| 结束后多出零奖励动作 | NEXT_STEP reset-only 槽是否被当成有效 transition |
| 训练在 time limit 学不到末端价值 | terminated/truncated是否混用；bootstrap是否用了reset observation |
| 回看旧数组内容发生变化 | copy=False、NumPy view、`get_last_step`引用是否被复用 |
| 随机摩擦改变了其他 env | material不在capture覆盖内；共享Scene的持久配置被修改 |
| A的截图像B | 独立render未恢复A状态，或E4宿主缓存/延迟未关联frame |
| `is_recording`为真却缺数据 | 仅会话标志，检查写入失败/Actor查询支持/字段选择 |
| HDF时间无法对上Gym episode | 录制相对时间、dummy步、共享Scene交错、post callback修改 |
| CUDA选项存在但“GPU不快” | build/矩阵分支、往返拷贝、同步、preconditioner及测量口径；本章不作性能结论 |
| 恢复策略后动作范围不对 | connector/normalizer与raw/env action区别，别只取网络权重 |

## 11. 带答案的阅读练习

1. **$f_s=600$Hz、$f_c=40$Hz，单次Gym step几次物理推进？** 答：$M=15$，$h=1/600$s，$H=0.025$s；reset还有单独的dummy步，不能计入这15次。
2. **重复同一动作15个子步，力一定恒定吗？** 答：不一定，`_apply_action`每步执行；闭环控制可随状态重算力，CartPole直接力任务才有固定缩放这一具体路径。
3. **为什么FP64原生状态可能返回float32学习观测？** 答：helpers先复制native real，CartPole Box规定float32，Gym flatten转换；两者是不同表示层。
4. **CartPole第0个扁平观测是位置吗？** 答：在固定Gym1.3.0不是，是按键排序的angular_vel；用结构转换接口而非猜顺序。
5. **reset后control count为0，是否没有做物理？** 答：已做1e-5秒dummy step；计数、native时间和录制时间不同。
6. **4环境、每worker2个、seed=100，得到哪些seed？** 答：按pK+j顺序是100、101、101、102；显式list避免两级相加重叠。
7. **给reset种子就控制随机动作了吗？** 答：没有，env np_random和action_space RNG各自管理，外部策略等也独立。
8. **NEXT_STEP本次done=true是否丢掉本次transition？** 答：不丢；它是真实末端转移，下一次该槽reset-only才排除，不能用本次done直接屏蔽本次。
9. **SAME_STEP返回的主obs能用于截断bootstrap吗？** 答：通常是新episode初始obs，应取final_obs及有效掩码，并遵循任务的终止/截断定义。
10. **Hybrid外层metadata显示DISABLED说明无自动reset吗？** 答：不能；内层默认NEXT_STEP，需记录构造参数；reset_mask也未获支持。
11. **只改变共享Scene的material后capture足够隔离吗？** 答：不够，capture不恢复material；要隔离持久配置或完整管理切换，不能把快照当整个模型。
12. **两个线程各持一个env对象就安全了吗？** 答：共享Scene时仍是同一原生对象；API要求单线程访问，manager假设顺序执行。独立Scene也要核对context/viewer资源。
13. **`copy=False`返回后立即存list，为什么旧观测会变？** 答：list保存的是缓冲引用，后续调用可覆盖；需要自己的copy并保留shape/dtype。
14. **CudaCG是否代表批量环境常驻GPU？** 答：没有；固定分支搬A/b/x到GPU、结果回CPU，Gym组织与GPU线性子问题是不同层。
15. **HDF的timeTotal等于Scene时间吗？** 答：不保证，recorder从0累加每次h，不读Scene时间；restore/中途开始/共享切换都影响对应关系。
16. **把parse_h5读出的targetPose当action是否通用？** 答：不是，样例固定Actor ID与特定目标字段，且舍入部分值；一般action还包括缩放、控制模式和时间结构。
17. **策略权重与Physics快照一起存就完整复现了吗？** 答：仍缺模型/持续参数、RNG、任务/RNN状态、normalizer/connector、依赖与调度身份等，且不能未经运行宣称数值一致。
18. **能用每个控制步末尾的两个状态直接反传所有子步吗？** 答：不能，diffsim要求相邻原生步的匹配state pair和输入/输出顺序；M>1时需要相应中间状态与梯度链。
19. **共享测试写了assert_array_equal，能据此宣称所有任务确定吗？** 答：不能，测试本身有限范围且有skip；本仓未执行，跨build/backend也不在该结论内。
20. **把cpp_total_step、cpp_solve_step和cpp_recording_step相加得到总耗时吗？** 答：会重复计数，总项包含子项；先核对秒/毫秒和采样范围，再定义口径。

## 固定来源

下列 reference 链接全部指向固定提交；Git blob 身份见 [sources.json](sources.json)，入口及新增依赖归属见 [source-map](source-map.md) 和 [THIRD_PARTY](../THIRD_PARTY.md)。本章不使用源码默认值补写 DexLab 历史 #124。

[lab]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/README.md
[package]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/pyproject.toml
[lock]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/uv.lock
[env]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/envs/mochi_env.py
[types]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/envs/types.py
[cartpole]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/envs/benchmarks/cartpole_env.py
[helpers]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/utils/mochi_helpers.py
[manager]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/envs/scene_manager.py
[vector]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/utils/vector.py
[sharingtest]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/test/envs/test_scene_sharing.py
[cross]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_cross_thread_capture_restore.py
[api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[scene]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp
[linear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/linear_solver.h
[pcg]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/linear_algebra/cuda/cuda_pcg.cpp
[cuda]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/linear_algebra/cuda/cuda_api.cpp
[csr]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/linear_algebra/cuda/cuda_csr_matrix.cpp
[diff]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/diffsim/__init__.pyi
[rllib]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/apps/rllib/train_samples.py
[traincfg]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/superdex/lab/gym/utils/train_cfg.py
[policy]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/apps/rllib/checkpoint_policy.py
[recorder]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene_recorder.cpp
[recorderheader]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene_recorder.h
[dataset]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/apps/envs/utils/dataset.py
[runner]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_lab/apps/envs/sample_runner.py
[gymcore]: https://github.com/Farama-Foundation/Gymnasium/blob/53bf3e9a884783eb72ad3fc8b15780914c97c3e1/gymnasium/core.py
[dict]: https://github.com/Farama-Foundation/Gymnasium/blob/53bf3e9a884783eb72ad3fc8b15780914c97c3e1/gymnasium/spaces/dict.py
[flatten]: https://github.com/Farama-Foundation/Gymnasium/blob/53bf3e9a884783eb72ad3fc8b15780914c97c3e1/gymnasium/spaces/utils.py
[sync]: https://github.com/Farama-Foundation/Gymnasium/blob/53bf3e9a884783eb72ad3fc8b15780914c97c3e1/gymnasium/vector/sync_vector_env.py
[async]: https://github.com/Farama-Foundation/Gymnasium/blob/53bf3e9a884783eb72ad3fc8b15780914c97c3e1/gymnasium/vector/async_vector_env.py
