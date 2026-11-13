# 记录、回放与重现：把观测、状态和执行条件分开保存

本课覆盖A9及B6的数据边界。先读[状态与时间](state-and-time.md)、[传感采样](sensors-and-sampling.md)、[批量](cpu-batching.md)与[学习接口](learning-and-randomization.md)。目标是能判断一个文件支持“看回动作”“恢复积分”还是“审计实验”。本轮没有生成轨迹、图像或训练数据；下述字段是课程设计的记录契约。

## 1. 三种“回放”回答不同问题

| 目的 | 至少需要 | 不能据此证明 |
|---|---|---|
| 视觉回放 | 模型/资产、时间和配置，必要的姿态/相机 | 接触力、控制因果或动力学正确 |
| 恢复推进 | 同一模型与配置、完整相关状态/输入、隐藏/外部状态 | 跨版本/设备/后端逐位相同 |
| 数据与实验审计 | 源版本、模型hash、任务/随机化/采样契约、有效性记录 | 未执行的能力或未记录的工况 |

把qpos逐帧写回后渲染，是姿态序列显示。它可以帮助检查坐标、资产和轨迹，但碰撞接触、约束力和actuator内态未必与原始运行一致。即使再做`mj_forward`，计算的也是当前恢复状态与配置下的派生结果，不能把它冒充原始传感读数。

同样，MJB是编译后的model，不是一个运行中的Data快照；MJCF与资产描述建模输入，也不包含所有运行状态。`mj_saveModel`和`mj_getState`服务于不同对象。[公开模型/状态API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L227-L258)、[state API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L505-L518)。

## 2. 先记录一个转移，再决定序列格式

一个可审计的控制转移，除了动作和reward，还应保存采样阶段与终态标签：

$$
(x_t,u_t,\tau_t)\longrightarrow
(x_{t+1},o_{t+1},\tau_{t+1},r_t,\text{labels}).
$$

其中o不一定在τₜ₊₁即时采样；若有delay/history，另需measurement time或可推导它的采样契约。把数据放在同一行只说明存储关系，不能消除物理时间差。

| 类别 | 建议字段 | 原因 |
|---|---|---|
| 身份 | logical env_id、episode_id、step_id、chunk_id | 与CPU worker或GPU执行顺序脱钩 |
| 时间 | physics time、实际substep数、h、采样phase/time | 区分推进、读数、延迟与reset |
| 动作 | 原始policy action、实际ctrl/外加输入 | 保存缩放、限幅和执行器语义 |
| 观测 | 字段名、shape、dtype、单位、frame、有效mask | qpos/sensor/RGB/depth不能只看列数 |
| 终态 | terminated/truncated/invalid、reason、terminal observation | 防止自动reset覆盖学习目标 |
| 模型 | MJCF/mjSpec导出、资产hash、参数/随机化实例 | 仅seed不能恢复未保存的参数实现 |
| 执行配置 | solver、integrator、timestep、iterations、tolerance、flags | 当前默认值不能替代当时配置 |
| 状态布局 | state mask的数值与符号、引擎版本、布局宽度 | 枚举与history随版本改变 |
| 随机/外部状态 | PRNG实现及状态、controller/目标/阶段记忆 | 原生state mask不覆盖它们 |
| 数据有效性 | warning、NaN/Inf、容量问题、缺失/丢帧 | 正常shape不保证有效物理 |

图像还需要camera ID/pose、intrinsics、分辨率、renderer/backend和RGB/depth/分割的各自含义。depth不自动等于射线距离，分割也不自动等于geom ID；详见[E4渲染](rendering-and-viewer.md)。

## 3. 原生state mask的能力上限

3.15的组合应从枚举读取，不能由旧教程猜测：

| mask | 包含 | 对恢复的限制 |
|---|---|---|
| PHYSICS | qpos/qvel/act/history | 无time、输入、warmstart、plugin状态 |
| FULLPHYSICS | PHYSICS + time + plugin_state | rollout默认状态；仍无USER和warmstart |
| USER | ctrl、外加力、eq_active、mocap、userdata | 不含控制器闭包或任务目标 |
| INTEGRATION | FULLPHYSICS + USER + warmstart | 最宽的该枚举组合，仍不是全部内存/外部状态 |

[`mjtState`枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h#L507-L533)。State API按mask打包原生字段；数组长度通过`mj_stateSize`取得。四元数不能用普通欧氏差分替代其配置空间差分，shape一致也不说明跨模型有同样语义。[E1状态课](state-and-time.md)。

下列片段只演示**同模型、同进程的mask数组复制**；没有执行。函数名刻意描述数组而不称完整checkpoint。调用者必须保证model/目标Data匹配，必要的派生缓存刷新和外部状态恢复由其明确安排。

```python
import mujoco
import numpy as np


def pack_integration_fields(model, data):
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    values = np.empty(mujoco.mj_stateSize(model, spec),
                      dtype=mujoco.MJTNUM_DTYPE)
    mujoco.mj_getState(model, data, values, spec)
    return values


def restore_integration_fields(model, data, values):
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    expected = mujoco.mj_stateSize(model, spec)
    if values.shape != (expected,):
        raise ValueError("State width does not match this model and mask")
    mujoco.mj_setState(model, data, values, spec)
```

这里不自动调用`mj_forward`，因为“恢复字段”与“选择如何刷新、读取或继续推进”是两个契约，后者还可能触发callback。恢复后读取旧派生缓存是错误的；但无说明地刷新也可能改变原本希望保留的时序。按使用场景选择原生调用，并保留原始读数副本。

## 4. 完整内存复制也有生命周期边界

对于要求恢复sleep等完整Data内部信息的场景，同版本、兼容model下的 `mj_copyData` 比state mask覆盖更多。实现复制buffer/arena，并通过plugin copy callback处理相应资源；它还把目的Data的threadpool指针置空，保留/重建部分拥有资源的指针关系。它不是把一段带指针的内存写入文件以后跨进程直接恢复。[copy实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1144-L1279)。

sleep、IPC内部状态和外部插件资源并非都能由INTEGRATION数组重建。plugin_state有数组也不说明plugin_data背后的外部资源已经序列化；Python控制器、随机生成器、任务阶段、viewer输入与外部通信同样不在mask中。完整恢复必须列出每个状态所有者和恢复方法，否则只能声明保存了某组原生字段。

warmstart影响有限迭代求解从哪里开始。若保存了物理状态却把warmstart清零，下一步并不保证与原轨迹逐位一致，即使时间、qpos、qvel相同。记录“每段显式清零warmstart”是一种可审计执行协议，但不能把它称为原轨迹无损续跑。[E3 warmstart](solvers-and-integration.md)、[rollout实际初始化](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rollout.cc#L116-L130)。

## 5. 设备快照不能隐藏异步与后端差异

设备array可异步产生。持久化前需要完成相应等待/host传输，确保写入的是该次计算结果，而不是仅保存一次未完成提交的时间戳。`device_get`和`block_until_ready`不同：前者返回host数据，后者等待但不等于复制所有数据到host。[JAX传输](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L2894-L2937)、[等待](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L3096-L3135)。

MJX `get_state`提供同名mask拼接，但Data内部有backend特定布局；Warp还有共享contact池。通过`get_data`得到CPU Data也不证明实现了跨后端完全等价的动力学checkpoint。必须记录impl与支持范围，并按本课源版本审查所依赖状态。对batched state使用逐世界打包，避免把整个batch flatten成一个“单世界”状态。[MJX状态接口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L1712-L1812)。

保存JAX随机key时，应记录PRNG实现以及key数据，而不是只记一串无法解释的uint32；重建规则与版本一起保存。对本课派生key方案，root seed、ID与派生规则可重建入口key；若运行中任意split和消费顺序未固定，还需保存当前key状态/流程。[key_impl/key_data](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/random.py#L301-L339)。

## 6. 可重现性的声明应分层

“同seed”只固定随机入口，不固定模型资产、浮点计算次序、并行调度、后端或编译策略。跨CPU/GPU、FP64/FP32、solver/迭代次数、JAX/Warp版本的结果不能默认逐位一致；本课没有做任何等价性或漂移实验。

可以按已拥有的证据作较窄声明：记录了配置与来源；能重建相同输入；在某个固定环境下完成了数值复核；在某个误差定义下结果一致。这些层次需要各自验证，不能把成功加载NPZ或看到相似视频当作全部达成。未来引用DexLab时保持其版本、工况与验收边界，不把课程例子升级成新增对照实验。

对于长轨迹，应分块写入，并把每块的世界/episode/步范围、真实样本数与完整性hash放在索引里。最后一块不满长度、错误中止与自动reset边界要有显式记录，不能靠零填充猜有效长度。固定内存下限参见[CPU批量](cpu-batching.md)，图像与压缩另算。此处不指定新的共享数据框架。

## 7. 带答案阅读练习

1. **只有qpos视频回放，可以证明原接触力吗？** 不可以；显示的是配置序列，力需要当时的动力学状态、输入、求解条件与采样阶段。
2. **FULLPHYSICS为什么不是完整checkpoint？** 缺USER/warmstart，且最宽mask也不涵盖所有sleep/IPC/外部资源和任务状态。
3. **`mj_copyData`能直接写成二进制跨进程恢复吗？** 不能；它管理同进程内指针、buffer、arena和plugin复制，并非可移植序列化格式。
4. **恢复后qpos正确，立刻读site_xpos可靠吗？** 不可靠；派生缓存可能仍是旧状态，必须按已声明时序刷新。
5. **episode结束时只保存reset后的obs有什么损失？** 丢掉terminal observation，影响bootstrap、失败诊断和真实末状态回放。
6. **同seed但JAX抽样shape变化，能默认同样随机参数吗？** 不能；向量和分key抽样没有逐元素一致承诺，需记录派生和抽样协议。
7. **MJB里包含ctrl吗？** 它是model文件；运行时ctrl位于Data，应由适当state mask或单独输入记录保存。
8. **读回一个正常shape的rollout数组能称完整有效数据吗？** 不能；需检查warning填充、真实时间进展、有限值、阶段和终止/缺失标签。

E5到此完成A8/A9与B6的批量、编译/拷贝及数据主线。完整安装部署、插件/回调扩展、flex/IPC和后端内部综合能力由后续E6/E7继续，见[课程](curriculum.md)与[验收](validation/e5.md)。
