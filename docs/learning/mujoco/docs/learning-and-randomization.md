# 学习接口与随机化：先建立时间、终态和参数契约

本课覆盖 A8/A9，先读[E2任务接口](task-interfaces.md)、[E4采样](sensors-and-sampling.md)、[CPU批量](cpu-batching.md)与[MJX设备数据](mjx-and-device-data.md)。这里给出应用应定义的学习契约，逐项映射到MuJoCo原生状态和参数；没有实现通用环境框架，也没有运行策略、训练或随机化实验。外部RL库未作为已验证适配器引入。

## 1. 原生 step 不包含一个完整环境

MuJoCo 的 `mj_step` 定义一个物理步；MJX 的 `step` 返回设备状态。两者都不替任务定义 reward、成功、失败、time limit 或下一episode。原生 `reset`、`MjData` 和一个学习系统常说的 `reset()/step()` 契约属于不同层次。

| 层 | MuJoCo原生内容 | 应用额外负责 |
|---|---|---|
| 物理状态 | qpos/qvel/act/history/time及选定输入 | 目标、阶段、episode与控制器记忆 |
| 动作输入 | ctrl/外加力/mocap等 | 策略输出到原生输入的单位、缩放、限幅 |
| 观测 | 状态字段、sensordata、图像/查询 | 选取、时序对齐、历史、噪声、归一化 |
| 推进 | 固定模型的一个物理步 | action hold、decimation、终止检查频率 |
| reset | 原生状态与派生量初始化 | 参数采样、目标、RNG、控制器、buffer与episode ID |
| 输出标签 | 没有任务语义标签 | reward、terminated、truncated、invalid及原因 |

策略向量长度也不应硬编码为关节数。3.15 actuator可以有多输入/输出，`nu`、`nactuator`、`nv`不同，控制范围不等于输出力范围；映射应复用[驱动课](actuation-and-control.md)的原生字段。对 slider 的 motor，控制可按声明的传动/gain解释；对position actuator，同样一个数是目标位置而不是直接力矩。

## 2. 物理步、控制步、采样步必须有三份定义

设物理步长h秒，每个策略动作保持k个物理步，正常无中途退出时环境步长为：

$$
\Delta t_{\rm env}=kh.
$$

改变k会改变控制闭环频率、可见的中间接触、奖励积分和最大episode物理时长。它不是单纯“加速训练”。例如h=0.002s、k=5对应10ms动作周期；若限时200个环境步，计划时长是2s。出现中途物理错误或提前终止时，要记录实际执行子步数，不能仍把时间增量写满10ms。

在一个环境步中，可以每物理步检查不安全状态，也可以只在动作边界检查任务成功，二者必须写进契约。原生传感器的history、delay与interval具有自己的时序；策略拿到的读数不一定是当前qpos的直接函数。MJX JAX的history同名数组又不等于CPU时序实现，见[MJX限制](mjx-and-device-data.md)。

以下是课程设计的时序，不是已有框架API：

```text
保存逻辑 env_id / episode_id / step_id 与输入动作
将动作按原生 actuator 契约转成 ctrl，保持 k 个物理步
  每个物理步推进后检查数值故障，并按约定采样/累计代价
得到 terminal_state；按注明的阶段得到 terminal_observation
计算 reward、terminated、truncated、invalid 和实际 dt
先记录 terminal_observation，再按结束原因决定是否 reset
返回给策略的 next_observation 可以来自 reset；训练 target 仍保留终态观测
```

`mj_forward`能在不推进time的情况下刷新派生量，但会执行相应流水线/回调，不是纯粹复制观察器。使用它补post-step观测前，要说明对传感阶段和控制回调的影响；不能为了“统一shape”额外运行一遍后却不给数据标注。[E1状态课](state-and-time.md)、[E3一步执行链](dynamics-and-pipeline.md)。

## 3. reward 的单位与离散化

若定义代价密度ℓ具有“代价/秒”的单位，用物理子步累积的近似是：

$$
r_t=-\sum_{j=0}^{k_t-1}\ell(x_{t,j},u_t)h+r_{\rm event}.
$$

其中kₜ是实际完成子步数，event项是一次性事件奖励。只在动作边界采样再乘kh是另一种近似，不能与逐子步积分混称等价。若原先ℓ就是每步无量纲惩罚，再乘h则改变了目标；记录定义比只记权重重要。

例如平方位置误差量纲为m²、平方控制量可能是N²或(rad)²，权重必须相应消去单位，才能解释不同项的相对贡献。这里没有推荐“通用reward权重”，也不把motor、position和SO3输入混成同一种物理量。

若每物理步折扣为γₕ，保持同一每秒折扣含义时，k步折扣是：

$$
\gamma_{\rm env}=\gamma_h^k.
$$

这条等式假设固定h与k以及同一时间折扣定义；更改k却保留γ，会改变有效规划时间尺度。中途退出使用的实际持续时间也要有一致规则。它是时间语义推导，不是任何学习库的默认实现说明。

## 4. terminated、truncated 与无效物理

本课建议把三类标签分开：`terminated` 表示任务定义的终态；`truncated` 表示采样过程因时间/预算边界停止；`invalid` 表示数值错误、容量溢出或数据契约失败。是否把任务失败算terminated由任务定义，不能把原生warning当作抓取成功。

以一类继续任务的价值目标为例，若time-limit只截断采样而非任务吸收态，则通常仍用终态观测做bootstrap；真正的任务终态不bootstrap。抽象写法是：

$$
y_t=r_t+\gamma_t b_t V(o^{\rm terminal}_{t+1}),
$$

bₜ由任务和数据有效性定义。它不应无条件写成 `1 - (terminated or truncated)`，也不应拿自动reset后的新episode观测代替 `terminal_observation`。无效物理应被明确过滤、终止或专门处理，而不是默认允许训练从损坏状态bootstrap。

批量自动reset应只改变已结束世界的状态、RNG与episode计数；不能因为一个世界结束就重置整个batch。对JAX，用同结构、单世界scalar mask再vmap；Warp共享池另循其后端规则。该机制只解决选择，不能补齐任务目标、控制器记忆、history与外部状态。[Data.where](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/types.py#L1176-L1206)。

## 5. 随机数按逻辑世界归属，不按调度线程归属

CPU worker可以连续处理不同世界，因此用worker ID决定某个episode参数会让线程调度影响数据分布。应保存稳定的 `env_id`、`episode_id` 和随机流用途，例如模型参数、初始状态、观测噪声、策略采样各自一条流。

JAX key是显式不可变值；重复使用同一个key生成同形状随机数，会重复结果。`split`返回新keys，`fold_in`把一个32位scalar标识混入key；都不会原地“消耗”旧key。不同用途/世界/episode要显式派生新key。[key/split/fold_in API](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/random.py#L202-L299)、[重复key与分流](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/docs/random-numbers.md#L153-L221)。

下面为原创建议：明确选用threefry实现，按三个非负、32位范围的稳定ID依次派生。只做AST检查；没有import/JIT/抽样。若ID可能超过范围，应制定有版本的编码规则，不能默默截断导致碰撞。

```python
import jax


def episode_stream_key(seed, env_id, episode_id, stream_id):
    ids = (env_id, episode_id, stream_id)
    if any(not 0 <= value < 2**32 for value in ids):
        raise ValueError("Identifiers must be unsigned 32-bit values")
    key = jax.random.key(seed, impl="threefry2x32")
    for value in ids:
        key = jax.random.fold_in(key, value)
    return key
```

此辅助函数用于host侧整数ID，含Python判断，不是可直接对tracer调用的JIT函数。设备侧batch可在单世界key函数上按scalar ID做vmap，并由调用者先保证范围。episode内逐步噪声还要继续split或混入step ID，不能每步复用episode根key。

固定seed也不保证改变batch划分后完全相同：向量抽样与把key拆开逐个抽样没有逐元素一致的承诺。记录PRNG实现、key派生版本、采样shape、流划分与调用顺序，才有机会重建同一随机化过程。CPU NumPy等另有自身生成器状态；本课不把它与JAX的key互换。

## 6. 物理随机化必须维护派生量与约束

域随机化应从假设出发：哪些参数存在制造差异、识别误差或传感噪声；采样范围依据什么；参数相关性是否合理。随机化不是“所有数字加独立高斯噪声”，也不是sim-to-real成功的证据。

| 变化 | 物理/实现要求 | 原生处理方向 |
|---|---|---|
| 固定形状均匀改变密度 | 质量与惯量同步按密度因子缩放 | 修改兼容的质量/惯量，重算常量 |
| 几何尺寸/关节结构 | 惯量、碰撞BVH、地址/shape可能变化 | 优先mjSpec/MJCF重新编译，重建匹配Data |
| 摩擦与柔顺参数 | 非负性、组合规则、维数/单位遵循E3 | 核对pair覆盖与solver参数，不只改某一个geom |
| actuator gain/阻尼/限幅 | 输入/输出量纲及派生项不同 | 依据E2具体类型逐项处理 |
| 初始姿态/速度 | 四元数归一化、关节限位、无效穿透风险 | 按E1状态API设置并定义有效性策略 |
| 观测噪声/延迟 | 与真实传感单位、采样和滤波相关 | 应用层与原生history分开记录 |

固定形状、密度乘α且α>0时，可同时令质量和惯量乘α。若做形状均匀缩放s且密度不变，则理想刚体有：

$$
m'=s^3m,\qquad I'=s^5I.
$$

这只是形状相似且质量分布相似时的物理关系；不授权直接在线改 `geom_size`。主惯量还必须为正且满足刚体三角不等式，例如I₁+I₂≥I₃；任意独立采样可能产生不可能的刚体。

原生文档区分可安全直接修改、需 `mj_setConst` 重算、以及必须谨慎重编译的字段。尤其 `geom_size/pos/quat`、静态body位置等牵涉BVH，不能以“调用setConst了”保证碰撞数据一致。[模型修改表](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L636-L767)。

`mj_setConst(model, data)`使用Data作计算工作区，会设置qpos为参考/弹簧配置并更新派生内容；它不是保持当前episode状态的只读工具。模型更新应在无worker使用它的边界进行，使用匹配的独立scratch Data，然后按新模型语义reset/刷新真正的世界数据。不要一边共享model推进，一边改质量并调用setConst。[入口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_setconst.c#L1535-L1573)、[参考配置写入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_setconst.c#L858-L880)、[弹簧配置写入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_setconst.c#L1339-L1355)。

## 7. GPU随机化的两层限制

第一层是结构：改变nq、nv、约束布局或其他静态metadata可能引发重新编译/分配，不能混入固定shape的reset循环。第二层是派生参数：`model.replace(body_mass=...)`只替换一个字段，未必更新所需的惯量/常量；上传新的native模型也需要明确同步和分配成本。

CPU `mj_setConst`不能直接对MJX model调用。vendored Warp另有自己的 `set_const`，其恢复和更新范围也与CPU不相同，例如不是默认替你重算所有执行器参考长度。以实际使用后端的支持范围设计参数随机化，必要时预先在host构建一组兼容模型，而不是假设字段同名就通用。[Warp常量更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/set_const.py#L850-L920)、[静态/动态字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/dataclasses.py#L65-L143)。

## 8. 带答案阅读练习

1. **h不变、k从5变10，只有吞吐变化吗？** 控制周期翻倍，观测/终止粒度、积分reward和每秒折扣都会受影响，必须重新声明时间契约。
2. **time-limit的最后观测被自动reset覆盖，能用新观测bootstrap吗？** 不可以；先保存terminal observation，再执行reset，并按任务定义决定bootstrap。
3. **相同seed为什么worker从2改4后可能不同？** 如果随机流依赖worker调度或抽样顺序，episode和随机序列的对应会改变；应绑定逻辑ID与固定派生规则。
4. **一次性奖励也乘h吗？** 不能机械处理；本课定义event为一次性无量纲项，代价密度才按时间积分。
5. **质量翻倍、惯量不变是否合理？** 对固定形状均匀密度变化不合理；若确实改变质量分布则需另外建模和说明。
6. **改geom_size后setConst就保证碰撞正确吗？** 不保证BVH等依赖一致，优先通过mjSpec/MJCF重编译并重建Data。
7. **随机化可以证明sim-to-real吗？** 不能；它是模型差距假设，实际转移证据还需要实物和任务验证。本阶段只建立可审计配置，未来复用DexLab相应证据。
8. **原生step返回数值就算有效转移吗？** 还要检查warning、有限值、容量与任务时序；尤其rollout会在warning后填充重复帧，不能只验shape。

继续：[记录、回放与重现](recording-and-replay.md)。
