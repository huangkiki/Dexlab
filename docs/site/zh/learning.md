# 从 MuJoCo 读懂仿真

机器人明明收紧了手指，物体为什么还会滑？把步长调小就会更准吗？仿真变快了，控制是否也跟着变了？

沿着一个问题学习：**动作怎样经过时间步进、接触和数值求解，变成下一刻的状态。** 再用这条链理解 MuJoCo 4 的变化，判断哪些值得进入实际系统的优化。

**[从时间开始：一步仿真，几种时间 →](mujoco-learning/step.md)**

## 先建立一条完整的链

控制输入 → 执行器产生力 → 接触与约束求解 → 积分更新状态 → 采样观测 → 下一次控制。

其中任一环节变了，后面的现象都可能改变。看到末帧掉落，还不能定位到求解器；看到画面流畅，也不能判断物理计算赶上了实时。

这条路线从时间开始，接着看接触、4.0 新能力与性能，最后把知识用在一个已有失败案例上。每课先回答一个问题，再提供可展开的解释、自测和深入课程。

## 把学习连接到系统优化

对于以 MuJoCo 为物理底层的机器人系统，可以先问三件事：控制多久更新一次；力和状态来自哪个时刻；耗时落在物理、控制、渲染还是通信。这些问题同样适用于分析 MATRiX 的集成路径。

本路线不预设 MATRiX 当前使用的版本、默认参数或性能。浏览器内的时间图是教学计算；实际优化结论需要回到对应版本、模型和测量。

<details class="explanation"><summary>一个贯穿课程的小例子</summary>
<p>设夹爪每 20 ms 接收一次目标，而物理每 2 ms 推进一步。夹爪在两条目标之间经历 10 个物理步；这些步里接触可以建立、承载，也可以丢失。</p>
<p>如果只把物理步长改成 1 ms，同时仍每 10 步更新控制，控制周期也会变成 10 ms。结果变了，便不能只归因于物理精度。下一课用可调时间轴把这件事展开。</p>
</details>

## MuJoCo 4 从哪里看

[MuJoCo 4 更新课](mujoco-learning/mujoco4.md)把发布变化与旧知识连接起来：speculative contacts 对应高速薄物体，塑性对应历史依赖，Studio 对应观察与调试，批量执行对应吞吐量。先理解问题，再选择能力。

截至 **2026-11-13**，官方稳定版为 [4.0.1](https://github.com/google-deepmind/mujoco/releases/tag/4.0.1)。现有[深入课程](learn/mujoco/docs/curriculum.md)仍保留 **3.15.0** 的固定源码阅读基线；它们不会被标成已完成 4.0 运行验证。

(all-courses)=
## 全部课程

这六课是一条导学路线。需要完整推导、API 与源码时，进入已有课程继续阅读。

- **共同基础：** [Physics-Based Simulation 伴读](learn/sim/docs/physics-based-simulation.md) · [九单元 Solver 教程](learn/sim/docs/solver-guide/README.md) · [术语索引](learn/sim/docs/solver-guide/term-index.md) · [应用与原理路线](learn/sim/docs/learning-paths.md)
- **MuJoCo：** [完整目录](learn/mujoco/docs/curriculum.md) · [状态与时间](learn/mujoco/docs/state-and-time.md) · [接触模型](learn/mujoco/docs/contact-models.md) · [版本与证据](learn/mujoco/docs/versions.md)
- **其他引擎：** [SuperDex](learn/superdex/docs/curriculum.md) · [Genesis](learn/genesis/docs/curriculum.md) · [Newton Physics](learn/newton/docs/curriculum.md) · [PhysX](learn/physx/docs/curriculum.md) · [Drake](learn/drake/docs/curriculum.md)

课程来自 Sim Learning 与各引擎的独立课程仓库，保留原始内容和来源。阅读留在本站；源码与许可见各课程页。

```{toctree}
:hidden:
:maxdepth: 1

mujoco-learning/step
mujoco-learning/contact
mujoco-learning/mujoco4
mujoco-learning/performance
mujoco-learning/diagnosis
共同基础与 Solver 教程 <learn/sim/README>
MuJoCo 深入课程 <learn/mujoco/docs/curriculum>
SuperDex <learn/superdex/docs/curriculum>
Genesis <learn/genesis/docs/curriculum>
Newton Physics <learn/newton/docs/curriculum>
PhysX <learn/physx/docs/curriculum>
Drake <learn/drake/docs/curriculum>
```
