# E5：批量、学习接口与数据

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [课程](curriculum.md) · [E2 控制](control-robotics-tasks.md) · [E4 观测](sensors-rendering.md)

本章回答三个实际问题：如何让许多 Newton world 共用设备数组而不混淆；一个 episode 结束后究竟要重置什么；怎样把状态变成有时序、可追溯的数据。先修是 E1 的 q/qd 与所有权、E2 的控制消费者、E4 的观测 producer。本章覆盖 A8/A9 和 B6 的批量、内存、JIT/graph 与数据扩展入口；专用 solver 扩展及完整可微链留给 E6。

Newton 阅读基线仍是 **1.6.1 / `713fecdc41caf0c9d726f5c016939f36e66e3dff`**。Warp 单独固定官方 **v1.18.0 / `f2eaed82d8d03b37bf1014cc975954067fefcf16`**，见[独立来源清单](e5-warp-sources.json)。这是两个明确的源码阅读身份，未证明本机安装、二进制组合或运行兼容性。所有例子仅做 AST/源码检查；未导入原生引擎、JIT、运行物理、渲染或训练。

## 1. world 是实体归属，不是 Python 环境对象

`ModelBuilder` 在宿主侧组织数据，`finalize` 才生成设备上的 `Model`；多个 world 可以装进同一个 Model，每个 State 又包含这个 Model **全部 world** 的动态数组。`model.state()` 两次通常是在申请输入/输出缓冲，不是在申请两个彼此独立的世界。Control 和 Contacts 同样可以服务整个批次。[world 定义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L9-L82)、[State 工厂](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1809-L1849)、[Control 工厂](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1893-L1934)

原生入口各有含义：

| 构建操作 | 固定实现的含义 | 需要留意 |
|---|---|---|
| `begin_world()` / `end_world()` | 接下来添加的实体归到新 local world | 不能嵌套打开 world |
| `add_world(template)` | begin → add_builder → end | 适合同一机器人/场景的多份实例 |
| `replicate(template, B, spacing=...)` | 一次批量合并 B 份并建立 world ID | 不调用子类覆写的 `add_world/add_builder`；旧 builder 列表引用可能失效 |
| world `-1` | global 实体，不属于 local world `0..B-1` | 仍受 collision group 和 solver 能力约束 |

`replicate` 可共享 mesh 等对象引用；应在 template 上完成 mesh 近似，再复制。它不是每个 world 一次深拷贝整个 Python 对象图。`spacing=(0,0,0)` 允许物理世界重叠；用 viewer 的 world offsets 做显示分离，可以避免人为把大量机器人放到很远处而放大浮点误差。[replicate 实现与生命周期](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L3130-L3220)、[add_world](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L4631-L4680)

碰撞隔离首先看实体的 world。不同 local world 的 shape pair 被过滤；global shape 可以参与多个 local world 的碰撞，但仍需通过其他过滤条件。因此共享地面是常见设计，共享可动 body 则可能产生耦合且受后端限制，不能把 global 理解成“完全不参与物理”。[实际 pair 过滤](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/broad_phase_common.py#L234-L282)

数据结构可表达异构 world，不等于所有 solver/selection 都接受异构批次。固定 `SolverMuJoCo(separate_worlds=True)` 要求对应 body/joint/shape/约束数量和类型、关节 DOF 等一致，global 只允许静态 shape，不允许 global body/joint/约束；native MuJoCo CPU 路径持有单个 template-world `MjData`，不能仅凭 Model.world_count 宣称它执行了 B 份独立后端状态。[world 能力提示](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L16-L29)、[MuJoCo 验证器](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L9445-L9520)、[CPU reset 的 world 0 所有权](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4275-L4295)

## 2. flat buffer 如何变成按 world 索引

`body_world[i]`、`shape_world[i]` 等给出每个实体的归属。`*_world_start` 则给出连续 local 分段，长度是 **B+2**。对于 local world w：

$$
I_w=[s_w,s_{w+1}),\qquad n_w=s_{w+1}-s_w,\qquad 0\leq w<B.
$$

global 可以同时位于数组前端 `[0,s_0)` 与尾端 `[s_B,s_{B+1})`。例如 shape world `[-1,0,0,1,1,-1]` 对应 starts `[1,3,5,6]`。`shape_count=6`，local 总数为 4；直接 reshape 成 `(2,3)` 会把地面塞进机器人数据。[布局与具体例子](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L95-L219)

| 数据 | 索引/形状 | 单位与含义 |
|---|---|---|
| `body_q` / `body_qd` | body_count 个 transform / spatial vector | m、xyzw quaternion；世界轴质心线速度 m/s 在前，角速度 rad/s 在后，详见 E1 |
| `joint_q` / `joint_qd` | joint_coord_count / joint_dof_count | 位置坐标和切空间速度，FREE 为 7/6；不能用一个 stride 同时切二者 |
| `joint_coord_world_start` / `joint_dof_world_start` | 各自 B+2 | 用对应边界分段，不从 body 数推导关节数组 |
| `Control.joint_target_q` | 当前 target layout 的坐标或 DOF 布局 | 用 `joint_target_q_start` 与关节语义；本章例子显式使用 coord layout |
| `Model.gravity` | 显式多 world 时 B+1 个 vec3 | m/s²，最后一项给 global；旧式隐式单 world 数组只有一项 |
| `world_mask` | B+1 个设备 bool | 前 B 项选择 local，最后选择 global；不是实体数量大小的 mask |
| `Contacts` | 有容量的全局接触列表及计数 | 没有通用的 `(B,K)` 等长接触布局；shape ID 可追溯 world |

依据：[joint 各类 starts](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L120-L150)、[gravity](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L346-L388)、[reset mask](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L324-L341)、[Contacts 存储](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L225-L277)。原生 `wp.launch(dim=(B,max_entities))` 只给线程分组；异构时仍需检查局部下标是否小于该 world 的数量，global 另处理。[二维线程示例](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L391-L444)

即使机器人同构，Camera、Contact sensor 与关节数组也不必采用同一轴顺序。E4 已说明 camera 输出 B/C/H/W 与变换输入 C/B、接触 sensor 的 flat row；把它们接到策略前，分别建立实体 ID、关节名、坐标系和 batch 轴映射。

## 3. episode reset 是多个所有者的协作

重置不能只写 `q=0`。要逐一确定权威状态、下一步要读的缓冲，以及缓存由谁维护。

| 所有者 | 重置责任 | 不能误认的行为 |
|---|---|---|
| `State` 输入/输出缓冲 | 选定世界的位置、速度、力；必要时 FK/IK 同步另一个表示 | `clear_forces()` 只清外力；`assign()` 复制数组但没有 episode/time 概念 |
| `Control` | 力、位置/速度目标、激活量、外部驱动器内部状态 | `model.control(clone_variables=False)` 与 Model 默认控制共享数组；不是独立初值备份 |
| solver | warm start、内部后端输入、接触/约束历史 | 基类 `reset()` 除验证 mask 外是 no-op；各 solver 的 flags 语义不同 |
| Contacts / collision | 使旧集合失效，按新 pose 重建几何；之后由 solver 产生新的力 | 清 count 不等于擦除旧数组，也不等于获得新力观测 |
| sensor / policy / task | 传感缓存、前一动作、RNN hidden、episode step、延迟队列、累计回报 | 引擎 reset 不知道这些应用量 |

[State.clear_forces/assign](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L189-L255)、[Control 复制选项](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1893-L1934)、[基类 reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L538-L569)。`Control.clear(model)` 会把 `joint_target_q` 恢复到 Model 默认目标，防止 FREE/BALL/DISTANCE 的 quaternion 被全零破坏；其他控制量清零。它没有 world mask。只结束一个 episode 时不能用全批次 clear 顺便抹掉其他 world 的动作；应按相应实体/DOF 分段写入，并处理 namespaced 控制量。[真实 clear 分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py#L76-L117)

**Newton 的 `SolverMuJoCo.reset`** 恢复选中世界的 `joint_q/joint_qd` 默认值；MuJoCo-Warp 分支清选中后端世界的 `qacc_warmstart/qfrc_applied/xfrc_applied/act/ctrl`，即使 `flags=0`。native CPU 分支只有 world 0 的一份 `MjData`，只有选中 world 0（或 mask=None）才清这份后端缓存；选择其他 world 不会产生或清除另一份 CPU `MjData`。BODY/粒子 flags 不起作用；body 状态要由 FK 派生。默认数据同步在下一步发生，稀疏同步或 sleeping 路径会即时同步/重建适用的后端数据。[完整分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4180-L4312)

**VBD** 相反，以 maximal body 和 particle 状态为主；JOINT flags 被忽略。它清刚体约束历史，下一步按新输入 rebaseline；reset 不跑 collision，也不即时重建粒子自接触 BVH。大位移后可用 `rebuild_bvh` 改善结构质量。**XPBD 没有覆写 reset**，继承基类 no-op，不能拿同名调用当作恢复 pose 或清除上次 contact impulse 的证据。[VBD reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L2370-L2425)、[XPBD 完整类](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py)、[XPBD 旧 impulse 消费](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L1060-L1116)

对已初始化的同构 MuJoCo 批次，下面是**完整 Python 语法、依赖现有对象的阅读片段**。它只处理 solver-owned joint/state 和 FK；Control、任务、观测和 contact 的重置仍按上表另外处理，没有运行它：

```python
# model, solver, state_0, state_1 already exist; solver is SolverMuJoCo.
import newton
import warp as wp

mask_values = [False] * (model.world_count + 1)
mask_values[0] = True
world_mask = wp.array(mask_values, dtype=wp.bool, device=model.device)
solver.reset(state_0, world_mask=world_mask)
solver.reset(state_1, world_mask=world_mask)
newton.eval_fk(model, state_0.joint_q, state_0.joint_qd, state_0)
newton.eval_fk(model, state_1.joint_q, state_1.joint_qd, state_1)
```

`None` 与全 true mask 选择同样的实体，但前者仍是“全 reset”形式，某些 solver 可以额外清除无 world 归属的 bookkeeping，不能保证内部效果完全相同。`Contacts.clear()` 默认只清全批次 counters 并增加 generation；`clear_buffers` 是对象配置，不是 clear 方法的参数。局部 episode reset 后若清整个 Contacts，其他 world 的接触也要重新生成/更新，不能继续读之前的 force。[mask 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L324-L341)、[clear 实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L469-L514)

## 4. 原生最小例子：两根独立转轴与一次选择性恢复

[examples/e5_world_reset_snapshot.py](../examples/e5_world_reset_snapshot.py) 直接构建一个单 revolute link，复制为两个 world，以设备 kernel 恢复 world 0 的公共 joint/control 数组并对两份 State 做 FK，最后制作拥有独立内存的 host 快照。它不构造 solver、不推进时间、不生成接触、不保存文件，也不是完整学习环境。

例子刻意只用**每 world 一关节、一坐标、一 DOF、无 global joint**，kernel 仍通过 starts 找区间，不把这个条件偷偷推广到 FREE joint。`Control` 仅覆盖本例存在的三个字段；肌肉、软体、额外 actuator 或 namespaced 控制需要补充自身 reset。调用 `contacts.clear()` 会使整个批次接触失效；新 force 要等碰撞和求解更新，不能从清空后的旧存储取值。日后把例子接到 solver 时，必须加入第 3 节的 solver-owned reset，最大坐标后端还需确认 joint 数组已从权威 body 状态重建。

例子没有 `.step()`，因此记录时间为 `0 s`，记录的是 **reset 后/FK 后公共状态**。它说明数据所有权，不声称物理仿真或 episode 恢复已验收。

## 5. 策略循环的时钟、动作与终止

对固定时长的学习循环，定义物理小步 h（秒）、一次低层调用内子步 S、每次策略动作重复 D 次。假设所有 world 每轮推进相同数量小步、没有自适应 dt，则：

$$
\Delta t_{\mathrm{policy}}=DSh,\qquad
f_{\mathrm{policy}}=\frac{1}{DSh},\qquad
 t_{k+1}=t_k+\Delta t_{\mathrm{policy}}.
$$

这些是应用时序定义，不是 Newton 的隐式调度。Newton 的 solver 入口接收一次 `dt`；框架要自行定义动作尺度/饱和、hold 时长、控制器更新频率、观测阶段和结束条件。[step 签名](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L571-L585)

固定官方 `example_robot_policy.py` 是很具体的实例：使用外部 `warp_nn.runtime.OnnxRuntime` 读预训练 ONNX，observation 是 `(1,12+3n)`，不是已经通用批量化的 B-world 环境。它把 base 线/角速度与单位重力方向旋转到 base frame，加入命令、相对初始关节角、关节速度和前一动作；通过 PhysX/MJWarp 关节名映射适配策略顺序。这里角度 rad、速度 rad/s，单位重力方向无量纲，不能把 `-1` 改成 `-9.81` 而仍沿用同一权重。[依赖与观测](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L20-L33)、[字段与布局](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L75-L170)、[名字映射校验](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L172-L223)

对转动关节，该例的动作映射为：

$$
q^{\mathrm{target}}_j=q^0_j+\alpha a_{\pi(j)}.
$$

如果动作无量纲，`action_scale` 的单位是 rad；映射没有额外 clamp，是否饱和需追到控制/solver 消费者。该 kernel 在 root 的前 7 个 target 槽写零；这是其自由基座不驱动的具体用法，不能复制给需要有效 quaternion 目标的通用控制器。[动作 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L115-L131)、[调用与前一动作](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L389-L417)

**这个固定示例的时钟有可见差异：** `fps=200`、`frame_dt=0.005`、S=1、D=4，单次 `step()` 实际提交四次 h=0.005 s 的物理推进，即 0.020 s；末尾 `sim_time` 只加 0.005 s。另有 `cycle_time=0.020` 字段，不能因此认为 `sim_time` 已自动修正。本章由代码控制流推导这个差异，未运行测量；若采用该例采集数据，要以实际提交的 dt 计算时间并核对展示/任务时钟。[时间设置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L225-L234)、[simulate/step](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L337-L417)

应用应区分：任务自然结束 `terminated`（成功/失败等定义）、时间预算导致 `truncated`、求解发散/容量溢出导致 `invalid`。后者应记录原因，不把坏样本悄悄当成正常终点。自动 reset 前先保留该 episode 的最后观测和结束原因，再写新初值；否则一条 transition 会把新 episode 首帧误作旧 episode 的末帧。是否对截断做 value bootstrap 由学习算法及任务的时间建模决定，Newton 不替训练器决定。

## 6. 原生物理接口与外部学习组件的界线

| 层 | 本基线可核对内容 | 没有由它证明的能力 |
|---|---|---|
| Newton Model/State/Control/solver | 批量物理数据、原生 step、后端 reset、设备数组 | 完整 reward、episode manager、PPO trainer |
| 官方 ONNX policy 示例 | 上述观测、映射、外部推理 runtime、动作写入 | 通用 Gymnasium API、训练收敛或 B-world 策略批处理 |
| Kamino RL 示例 | 外部 Torch 策略推理，`torch.inference_mode()`，内部 sim wrapper/observation | 所有 solver 共用同一学习语义、梯度穿过物理 |
| Isaac Lab 集成文档 | 固定树指向外部 experimental integration 文档 | 本仓锁定/安装/验收了外部框架版本 |

来源：[ONNX 初始化](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L133-L170)、[Kamino 推理入口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/examples/rl/example_rl_bipedal.py#L313-L351)、[Isaac Lab 指针](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/lab/isaac-lab.rst#L1-L8)。本章不引入跨引擎 wrapper；迁移到外部框架时，应逐项对齐原生数组、实体顺序、动作单位、时钟和 reset 契约。读取预训练策略不等于训练，也不等于已有 sim-to-real 成功证据。

## 7. CPU/GPU、复制、视图与流

Warp kernel 的参数应位于 launch 目标设备；Python 标注的 kernel 会经 C++/CUDA 中间表示 JIT 到动态库/PTX。固定文档说明 CPU kernel launch 当前串行、CUDA launch 并行；不能由 Python 层 B-world 维度推断 CPU 多线程加速，也不能把整个 solver 的外部库并行行为归于这一条说明。[Warp runtime](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L12-L65)

| 操作 | 固定 Warp 1.18 行为 | 数据管线中的后果 |
|---|---|---|
| `wp.clone(a)` / `wp.copy(dst,src)` | 前者另有数组存储；后者覆盖已有目标 | 覆盖不改变旧 tensor view 的地址，但会改变其值 |
| `a.to(device)` | 同设备直接返回 a，跨设备 clone | `.to(a.device)` 不是快照 |
| `a.numpy()` | CPU 可别名；GPU 做同步 D2H 再生成 NumPy view | 要保留不可变样本用 `.numpy().copy()`；CUDA 热循环里频繁调用会读回/同步 |
| `wp.to_torch` / `wp.from_torch` | 兼容布局时零拷贝共享数据，保留底层所有者引用 | 不独立保存历史；State buffer 复用时 tensor 内容也会变 |
| `wp.copy(..., stream=...)` | 元素大小须匹配；默认优先目标 CUDA 当前流，否则源 CUDA 当前流 | “提交 copy”不是跨流消费者已经可安全读取的证明 |

[clone](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/context.py#L10168-L10214)、[copy 实现](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/context.py#L14342-L14412)、[numpy](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/types.py#L4521-L4559)、[to](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/types.py#L4640-L4646)、[Torch 共享与引用](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/torch.py#L189-L216) / [实现](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/torch.py#L292-L400)。本例 host 快照用 `.copy()`，所以即使设备是 CPU，后续数组复用也不会改写已记录数据。

CUDA 异步任务还需要明确 stream 依赖。Warp/PyTorch 共享缓冲时，使用相同有效流或显式事件/同步建立 producer→consumer 顺序；只共享指针不能保证先写后读。固定 Torch/Warp 联合 capture 文档要求同一 CUDA stream，并说明 PyTorch 默认流不适合 capture，应先创建合适的新流。[流互操作](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/interoperability/pytorch.rst#L44-L97)、[显式同步 API](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/context.py#L12316-L12379)

零拷贝也不会自动让训练 loss 穿过整个 Newton solver。可微 kernel、Tape、梯度 buffer 生命周期及 PyTorch autograd 对接需要额外契约，接触/solver 的可微限制见 E3，深入实现留 E6。固定文档特别禁止把外部 `grad_output` 直接挂到可被清零/复用的 Warp `.grad`；保留的梯度 view 也需 clone。[梯度所有权](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/interoperability/pytorch.rst#L226-L264)

## 8. JIT、graph 与双缓冲的地址不变量

应分开理解五类成本：构建/导入模型；finalize 和 solver 缓冲分配；首次 JIT/后端编译；重复步进；观测、D2H、序列化和渲染。Warp module hash 缓存减少重复编译，并不使这些阶段成为同一件事。这里没有计时、吞吐或 CPU/GPU 排名。[JIT 缓存边界](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L50-L65)

graph 记录受支持操作及其参数/数组，不重放任意 Python 执行。普通 `if`、Python list 追加、对象引用交换和 `sim_time += h` 在 capture 时发生，不能指望每次 replay 重新执行。修改已捕获数组的内容通常是希望的输入更新；替换 Python 属性为一个新数组则不能假设 graph 的旧指针随之改变。[capture 语义](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L1536-L1606)

若捕获奇数次 `state_0,state_1=state_1,state_0`，Python 名称在 capture 后翻转，而记录中的读写地址没有跟着每轮 replay 翻转。Newton 的 State.assign 文档及 policy 示例使用最后一步 copy 回固定输入缓冲，或使用偶数步让地址关系恢复。capture 后须同时核对**下一次 graph 读谁**与**观测从谁读**，不能只看变量名。[State.assign 原生说明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L202-L233)、[policy 的奇数步分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L325-L352)

**Warp 1.18 不只支持 CUDA graph。** CPU APIC graph 已提供实验性记录/重放：支持的 kernel/copy/zero/refit 等被延后到 `capture_launch`，C++ 循环减少 Python dispatch；操作集合、文件格式和 API 仍可变化。非连续 copy/fill 等有独立限制，不能由支持 CPU 就推导任意 Newton/宿主调用都可捕获。[CPU graph 支持与限制](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L1850-L1952)

Newton 固定 policy 示例的 capture 条件是 `device.is_cpu or device.is_mempool_enabled`；实际只捕获 `simulate()`。ONNX 推理、观测组装与 action target kernel 在 `step()` 的 capture 外调用。因而不能称它捕获了整个策略循环，也不能拿捕获成功替代数值或控制正确性验收。[capture](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L325-L335)、[策略调用顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L378-L417)

## 9. 随机化：参数、索引和 RNG 都要有身份

随机化至少分三层：初始 State（pose/velocity）；Model 参数（质量、惯量、材料、重力、驱动）；观测/动作/延迟等应用数据。修改其中一层不会自动同步其他层。质量/惯量还必须保持正值、逆量和物理一致性；改几何不能假设缓存惯量、AABB、后端常数都已自动更新。

`notify_model_changed(flags)` 是通知入口，不是所有后端统一支持任意修改的承诺。XPBD 对 BODY/BODY_INERTIAL 刷新有效质量/惯量，对开启 restitution 的 SHAPE 更新相应缓存，其他 flags 被忽略；MuJoCo 按类别更新后端属性，失效 contact fast path，并重算相关常数。随机化要沿实际消费者确认：写入了哪些 Model 数组、对应什么 flag、是否重新建立 collision/图结构、是否影响 graph 中地址。[XPBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L231-L252)、[MuJoCo](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4766-L4832)、[ModelFlags](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/enums.py#L8-L53)

`Model.set_gravity(g, world=w)` 支持显式 world，但后端镜像/缓存是否也需通知要按所用 solver 检查。改变质量后只更新 `body_mass` 而保留旧 `body_inv_mass` 是不一致的数据；改变 world 数量、拓扑或数组容量通常需要重建 Model/solver/graph，不能用一个 PROPERTY flag 冒充结构编辑。

RNG 也没有一个能支配全系统的“Newton seed”。官方 recording 示例显式建立 NumPy `default_rng(123)`，用于资产初始姿态和每份关节值；这不设置 Warp 或外部策略框架的 RNG。[官方初始化](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_recording.py#L33-L65)

Warp 的 `wp.rand_init(seed, offset)` 用 PCG 混合 seed/offset 得到 uint32 状态，后续随机调用更新该局部状态。每次 launch 若用同样 seed/offset 重新初始化，就会重放同一序列。不同 kernel 用同一组合也会引入相关性。[原生 RNG 实现](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/native/rand.h#L29-L81)、[跨 kernel/launch 相关性说明](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L3388-L3454)

学习任务可把 master seed、episode ID、稳定 world ID、随机量类别组合成可记录的 stream 标识，再映射到所用 RNG 的有限位宽输入；这是一项应用设计，应明确碰撞/溢出策略，不承诺 32-bit hash 永无碰撞。world 重新排序或仅部分 reset 时，不能用“本次 reset 列表里的第几个”代替稳定 world ID。保存采样后的参数值比只写一个 seed 更利于重放；即使 RNG 相同，也没有由这些源码推导跨设备/求解顺序的整条轨迹逐位相同。

## 10. 状态记录、观察数据与继续仿真是三种交付

Newton `ViewerFile` 是原生记录入口，`set_model` 保存 Model **引用**，`log_state` 每次克隆 State 直接属性里的 `wp.array` 到 history；`.json` 或 `.bin`（CBOR2）保存 model 与 states。它既没有遍历 namespaced State 容器，也没有自动记录 Control、Contacts、solver warm start、RNG、policy hidden 或每帧时间戳。[记录实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1163-L1233)、[Model 引用与文件 payload](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1251-L1297)

这产生三个容易忽略的结果：

1. State 的直接数组快照独立，但 Model 后续修改会反映到最终序列化的 Model 引用，无法自动表达每个历史帧的随机化参数；应单列参数事件或逐 episode 元数据。
2. `playback(state, frame_id)` 用 `setattr` 将历史数组放进 State，而不是复制进独立 destination；对回放 State 做原地仿真可能修改 history，或令既有 graph 继续使用旧地址。显示回放不要混同继续求解。
3. `max_history_size=None` 时 history 无上限且 clone 保留设备存储；设定容量则只留最近 N 项。`_save_recording` 捕获异常，只在 `verbose=True` 时打印；公开 `save_recording` 默认 `verbose=False`，失败可能没有提示，自动 log_state 保存则沿用内部默认 True。调用返回不等于文件写入已验证。[构造参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1125-L1161)、[save/record/playback](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1201-L1249)

官方 replay viewer 新建 State、load frame 后调用 viewer.log_state 做显示，没有调用 solver 验证可从中恢复同一后续轨迹。[回放消费者](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_replay_viewer.py#L174-L180)

设计采集格式时至少区分以下字段；这是本课程的数据契约建议，不声称 ViewerFile 已实现：

| 类别 | 建议保存的内容 | 为什么不能省略 |
|---|---|---|
| 身份 | Newton/Warp/后端/宿主版本、资产和配置哈希、joint/body/shape 名称映射 | 相同数组长度不证明语义相同 |
| 时间 | 累计物理 dt、episode ID、world ID、episode step、采样阶段、必要的墙钟 | viewer frame index 不等于物理时间；wall clock 用于延迟，不代替 dt |
| 动作 | 策略原值、限幅/缩放后的 target/effort、重复次数、控制器状态 | 输入命令不等于实际力/力矩 |
| 观测 | 值、单位、坐标、producer、valid 标志、hit/overflow 状态 | 空/旧 buffer 不等于有效零观测 |
| 随机化 | RNG 身份、实际采样参数、应用时刻、后端刷新动作 | seed 不能恢复未记录的采样顺序 |
| 结束 | terminated/truncated/invalid 及原因、reset 前 final observation | 防止跨 episode 接错 transition |

接触集合通常采在步前几何，力可能对应该步冲量/平均力，camera 或 IMU 又有各自更新时间。需要在一行样本里保存各量的时间/阶段或明确已对齐协议，不能因为在同一次 Python loop 读出就称“同一时刻”。细节沿 E3/E4 的 producer 契约。记录的数据可支持后续系统辨识、延迟/噪声建模；随机化本身不能证明已缩小真实差距。正式 sim-to-real/抓取实验最终复用 DexLab 的版本和协议。

## 11. 扩展数据的原生入口

`ModelBuilder.add_custom_attribute(CustomAttribute(...))` 提供 `frequency`、`dtype`、`assignment`、默认值和 namespace。frequency 决定按 BODY/SHAPE/JOINT/JOINT_DOF/JOINT_COORD 等分配，assignment 决定归 Model/State/Control/Contacts；二者不能互换。默认 namespace 下字段直接在对象上，命名空间则位于 `state.my_namespace.field` 等容器中。[声明契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/custom_attributes.rst#L25-L55)

批量合并时，存储 shape/body 等 ID 的自定义字段需声明 `references`；`references="world"` 会由 builder 按当前归属重映射，而不是保留模板 world 编号。普通浮点 observation 不应误标成实体引用。扩展字段申请只负责存储，不提供生产、重置或观测语义；例如 contact force/body acceleration 仍需特定 solver 写入。[多 world 重映射](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/custom_attributes.rst#L858-L923)、[按需扩展字段](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/extended_attributes.rst#L10-L24) / [State 扩展](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/extended_attributes.rst#L80-L125)

`State.assign()` 能处理 `Model.AttributeNamespace` 中的数组，但 ViewerFile.record 只看顶层数组，所以新增 namespaced 状态时还需检查记录消费者；不能因前者支持就推断后者保存完整。自定义 attribute 是现有数据机制，通常比另建通用 wrapper 更直接；更深层 solver/coupling 扩展由 E6 继续解释。

## 12. 易错点与阅读练习

易错点集中在边界：把多个 State 当成多 world；把全局地面计入每世界 stride；partial reset 清掉全批次 Control；只 reset q 忘记后端历史；CPU NumPy view 当快照；replay 只改 Python 引用；照搬官方示例时钟；把 ViewerFile 当完整 checkpoint；把 ONNX inference/zero-copy 当训练和可微物理。这些错误都可能在数组形状“看起来正确”时发生。

1. 两个 local world 各有两个 shape，另有前后各一个 global shape，starts 是什么？为什么 reshape `(2,3)` 不成立？
2. `world_mask=[True,False,False]` 对 B=2 选择谁？它与 None 有何差别？
3. 为什么 `solver.reset(...,flags=0)` 在 MuJoCo 仍有作用，在基类却不能恢复状态？
4. 为何 quaternion target 不可统一全零？partial reset 能否直接 `control.clear(model)`？
5. 同设备 `.to()`、CPU `.numpy()`、`.numpy().copy()`，哪个适合保留值快照？
6. 一次动作 D=4，S=1，h=5 ms，策略动作覆盖多少秒？固定官方 policy 的 `sim_time` 每轮加多少？
7. graph 捕获奇数次 State 交换后，只把 Python 属性重新赋给新 State，是否足以改变 replay 输入？
8. 同样 seed/offset 每轮 `rand_init` 是否得到新的 episode 随机数？如何避免 reset 次序影响 world 身份？
9. 为什么 ViewerFile 的状态 clone 不足以成为严格续算 checkpoint？回放后原地修改又有什么风险？
10. 自定义字段位于 `State.my_data` namespace；`assign` 与 ViewerFile.record 对它有何不同？

### 参考答案

1. `[1,3,5,6]`；每 world 两项，global 位于两端。reshape 把 global 混进局部数据，应该按 starts/实体 ID 选择。
2. 只重置 local 0，不选择 local 1 或 global。None 选择全部实体，并允许 solver 处理没有 per-world 归属的全局 bookkeeping。
3. Newton 的 SolverMuJoCo 在 Warp 分支清选定后端 world 的 warm start/外加力/激活/控制缓存，flags 只控制公共 joint 状态恢复；native CPU 仅在选中 world 0 时清唯一 MjData。基类仅规范/验证 mask，没有恢复实现。
4. `(0,0,0,0)` 不是旋转。clear(model) 保留有效默认目标，但会清所有世界；局部 reset 要按 target/DOF 布局选段，并处理其他控制状态。
5. 前两种可能别名；`.numpy().copy()` 给独立 host 值快照，GPU 情况还包含同步读回成本。快照仍不包括未选择的元数据/缓存。
6. 0.020 s，即理想策略频率 50 Hz；源码 `sim_time` 只加 0.005 s。采集时必须修正/独立累计真实提交的物理时间，不能用展示字段代替。
7. 不足。graph 引用 capture 时的数组；需维持固定读写地址、正确 copy 回，或按新地址重建/合法更新图，并核对观察缓冲。
8. 不会，相同初始化重放同一序列。使用稳定 world ID、episode ID 和随机量类别构造记录过的 RNG 输入，处理有限位宽映射并保存实际参数。
9. 缺少控制/后端历史/随机与应用状态/时间，Model 只是最终引用。playback 直接挂历史数组，继续修改可能污染 history；显示回放与精确续算应分开。
10. assign 会下探 AttributeNamespace 数组；record 只克隆顶层 wp.array。必须显式设计该字段的记录与重置，不能由存储扩展推断完整 lifecycle。

## 13. 本章验收与后续

[静态验收记录](e5-validation.md)逐项记录来源身份、行号、AST、源码语义审查和保留限制。没有把这些结果称为 runtime、训练或性能验收。下一阶段 E6 承接专用 solver、耦合/扩展和完整可微机制；E7 再审校双路线并整理 DexLab 复用入口。
