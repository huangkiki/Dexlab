# E5：批量场景、学习接口与数据

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [完整课程](curriculum.md) · [源码地图](source-map.md) · [本章检查](validation/e5.md)

先修 [E2 控制与机器人](control-robotics.md)和 [E4 观测与显示](sensors-rendering.md)；reset 的 frame/cache 基础见 [E1](modeling-state-time.md)。本章完成 A8/A9 和 B6 的批量组织、数据传递、调度与扩展接口课程。具体 GPU 内核、特色几何和自定义约束的完整实现仍由 E6 展开。

阅读基线：`ovphysx-0.6.3`，固定 SHA `da950a3537927784951853c66618036f332ca0ce`，SDK 头文件 5.11.0。该身份不证明已安装 binary、Isaac Sim/Isaac Lab/UniSim 内置版本、硬件或学习宿主已经可运行；尤其不能用当前默认值补齐 DexLab #126 的历史未知配置。本次只读源码与检查 C++ 语法，不链接/执行 SDK，不做训练、仿真、渲染或基准；后续实验复用 [DexLab](https://github.com/huangkiki/Dexlab)。

## 1. 批量不等于一个额外的 PhysX 环境类

原生 SDK 的单位是 `PxPhysics` 创建的 `PxScene`、actors/shapes/materials 和 articulations；`env_id`、episode、reward、policy/action tensor 是应用组织。先选择物理世界的边界，再定义学习 batch：

| 组织方式 | SDK 对象与好处 | 需要自己保证的隔离 |
|---|---|---|
| 每环境一个 Scene | 每个 Scene 有独立 actors、碰撞、gravity/solver 配置与步进序列；物理时间由应用分别累计 | 每个 scene 独立配对 simulate/fetch；全局共享材料/mesh、应用 RNG、日志/任务资源仍可能共享 |
| 一个 Scene 放多个环境 | 同一 scene 的宽相位/任务/GPU 批量管线处理多组对象 | 排除跨环境碰撞、query 可见性、控制/状态索引、reset 集合；全体共享 scene 的 dt/gravity/solver 选项 |
| 多进程/多设备 | 由应用创建多个 SDK/context/进程并交换数据 | 进程生命周期、设备分配、通信/同步、配置一致性；不是 PxScene 自带的分布式训练器 |

同一个 actor/articulation 不能同时属于两个 Scene；复制一个 C++ 指针不会创建另一个环境。[Actor 插入契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L307-L326)、[articulation 插入契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L271-L284)。可以共享的是适合共享的资产/对象，例如 mesh 和 material；[`PxCollectionExt::createCollection(PxPhysics&)`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCollectionExt.h#L52-L67)就明确收集跨 scene 可共享对象。共享意味着改变材料参数可能影响全部引用者，不能把“Scene 独立”误写成“所有参数天然独立”。

`PxAggregate` 把空间接近的 actors 合并为一个 broad-phase entry，并可配置内部自碰撞；它不是 episode 容器，也没有不同 aggregate 之间默认不碰撞的承诺。[原生定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxAggregate.h#L48-L66)。不要把机器人、aggregate、碰撞 island、学习环境和 GPU batch row 当成同一种索引。

### 1.1 同 Scene 中需要四类隔离

1. **物理相互作用**：给每个 shape 的 simulation filter data 编入环境身份，原生 filter shader 对跨环境 pair 返回 SUPPRESS/KILL 等明确策略。空间平移只是布局，物体飞出区域仍可能碰到其他环境；共同地面必须是有意共享的静态对象，不能用一个共享动态物体把环境重新耦合。
2. **查询可见性**：E4 的 `queryFilterData/preFilter` 另行排除其他环境。simulation shader 不会自动把相机射线/距离 query 隔离；标签和语义 ID 也独立管理。
3. **状态和动作**：应用保存 `env_id → actor/articulation → low-level link/DOF → GPU index → batch row` 映射。创建顺序、`getLinks()` 枚举顺序与内部 link index 不相同；GPU index 也不是紧凑环境编号。
4. **可变资源与任务历史**：per-env reset、drive target、effort、滤波历史、RNG/episode counter、终止状态及日志 buffer 不共享可变存储；共享 material/shape 参数必须采用明确的共享策略。

过滤函数应无状态，只根据传入属性、filter data 和 constant block 决策，不查询外部对象或依赖回调顺序。[shader 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L527-L572)。复杂 filter callback 可来自不同线程，应自己保证线程安全，不在回调里修改 SDK 状态。[callback 限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxFiltering.h#L580-L596)。更改过滤策略要理解原有 pair 的重新评估；`resetFiltering` 会丢弃既有 interaction 状态、可能生成 lost/new 事件并唤醒对象，不是零成本的“更改 env_id”。[具体边界](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L882-L911)。

## 2. Scene 并行、SDK 任务与完成边界

### 2.1 分发物理任务不等于创建环境线程

`PxSceneDesc.cpuDispatcher` 指向负责调度 SDK CPU tasks 的 dispatcher；`PxCpuDispatcher::submitTask` 收到任务后安排 `run()`，运行后必须 `release()` 并丢弃指针。[dispatcher 接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/task/PxCpuDispatcher.h#L16-L49)。`PxBaseTask::run` 明确要求线程安全、适合栈使用并且**不能阻塞**。在 PhysX worker 内等待另一个需要相同 worker pool 才能完成的工作，会有死锁风险；磁盘写入、网络和训练等待放到应用自己的完成队列。[task 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/task/PxTask.h#L19-L57)。

原生 `PxDefaultCpuDispatcherCreate(numThreads,...)` 可以供多个 scene 的应用配置使用；对象要活到所有使用者和挂起任务结束。不要为每个小环境机械创建一套“物理线程数=CPU 核数”的池，再叠加 rollout/渲染线程。worker 数为 0 是同步执行任务的有效模式，不是停止物理。[工厂和等待模式](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxDefaultCpuDispatcher.h#L53-L90)、[零 worker 的实际分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/ExtDefaultCpuDispatcher.cpp#L110-L143)。是否共享池、任务粒度和性能收益需后续测量，本章没有吞吐结论。

多个独立 Scene 可以由应用组织为“逐个提交本轮 simulate → 各自完成 fetch → 聚合观测”，或由多个应用线程调度。每个 Scene 同时只能有它允许的在途步骤；不能对同一 Scene 连续调用两次 simulate 而没有相应 fetch。每个 scene 的读写锁也不能保护另一 scene 或全局共享应用状态。[配对与参数](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L956-L988)、[读写锁](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1454-L1506)。上述组织是 API 可表达的应用方案，不是本轮已经跑过的多场景实现。

### 2.2 完成有不同层次

| 边界 | 完成了什么 | 不能推断什么 |
|---|---|---|
| simulate 返回 | 成功启动/提交一次 step；零 worker 等配置下可能已执行大量工作 | 所有公开数据已 fetch、应用传感器/渲染帧可读 |
| `checkResults(true)` 或 completion task | 计算到可 fetch 的状态 | 不会代替 fetch 的 callback/buffer 更新 |
| `fetchResults(true,&errorState)` | 处理相应结果，成功返回且硬件 errorState 为 0 才可按约定继续 | 另行发起的 GPU copy、渲染、日志保存已完成 |
| Direct GPU finish event | 对应数据传递/计算完成 | 数据已经复制到 CPU，或下一条不同 stream 自动按顺序消费 |

[`checkResults/fetchResults`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1023-L1064)明确区分状态检查与结果更新。传入 `completionTask` 时 SDK 增减其 reference count，应用也须释放自己的 reference，不能以普通 callback 的生命周期理解它。`controlSimulation=true` 默认让 Scene 管理 task manager；只有自己正确管理 `start/stopSimulation` 的应用才改变它。临时 `scratchMemBlock` 要 16-byte 对齐、大小为 16 KiB 的倍数，fetch 完成前不能复用；不同在途 Scene 不共享同一可写 scratch。[原生参数](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L974-L988)。

Split simulation 的顺序为 `collide → fetchCollision → advance → fetchResults`，不是四个独立物理步。Split fetch 则为 `fetchResultsStart → 处理报告/processCallbacks → fetchResultsFinish`；中间禁止写 simulation，Finish 后返回的 contact stream 指针失效。[split 接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L990-L1020)、[split fetch](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1066-L1103)、[官方 split snippet](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetsplitsim/SnippetSplitSim.cpp#L259-L315)。

官方 `SnippetMultiThreading` 在 simulate 与 fetch 之间运行 raycast worker，并在 fetch 前等待 query 完成；这说明特定合法读操作可以与物理计算交叠，不说明所有 getter/setter 都可并行，也不说明射线读到了本次尚未 fetch 的新状态。[例子实际顺序](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetmultithreading/SnippetMultiThreading.cpp#L160-L182)。学习观测仍按 E4 的明确采样边界组织。

## 3. CPU、GPU dynamics 与 Direct GPU 是三个契约

| 路径 | 控制与状态入口 | 重点 |
|---|---|---|
| CPU scene | 原生 actor/joint API、articulation cache | 应用复制值构造 batch；状态 getter 不自动产出 tensor |
| GPU dynamics + 常规 CPU API | scene CUDA context/GPU dynamics 配置，仍有 CPU 公开数据路径 | 存在同步/拷贝；某些 acceleration getter 还有 lazy copy，见 E4 |
| GPU dynamics + Direct GPU API | GPU index buffer、GPU data buffer、typed get/set/compute 和 CUDA events | 对有 Direct GPU 对应项的数据停止常规 GPU→CPU readback；旧 CPU API 不再是正确访问路径 |

Direct GPU 要在 scene 创建时同时满足 `eENABLE_DIRECT_GPU_API`、`eENABLE_GPU_DYNAMICS` 和 `PxBroadPhaseType::eGPU`，这些选择不可事后切换；本版 Direct GPU 还关联 `eDISABLE_SLEEPING`。这会改变睡眠行为，不能把它仅当成拷贝优化开关。[scene flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L277-L296)、[sleeping flag](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L349-L359)。GPU dynamics 的 flag 存在不证明编译产物、驱动、context 和所有几何组合可用，具体后端覆盖留到 E6。

Direct GPU 在**第一次 simulation step 后才初始化**；创建模型时用相应 CPU setup API，初始化后切换到正确的 GPU 通道。这个启动步具有物理时间和状态变化，不是一个无副作用的 API import。应用必须决定它属于 episode 前准备还是初始状态的一部分，必要时再按 GPU reset 协议重设状态。[总契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L220-L240)、[官方首步与索引整理](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetdirectgpuapiarticulation/SnippetDirectGPUAPIArticulation.cpp#L443-L490)。本章没有运行这个启动步。

`NpDirectGPUAPI` 的 get/set/compute 路径会检查 scene 是否在模拟、Direct GPU 是否初始化以及必需指针，再转发到 simulation controller。一个 `void*` 参数不是“CPU/GPU 指针随便都行”，公开签名明确要求 GPU memory。[实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpDirectGPUAPI.cpp#L42-L121)。CPU getter 可能陈旧、报错或像 E4 加速度那样返回零；不要只检查它“有没有返回值”。只有没有 Direct GPU 对应项的既有 API 才按其单独契约继续使用。

GPU broad phase 与 GPU dynamics 是不同配置项：`broadPhaseType` 选择碰撞宽相位，`eENABLE_GPU_DYNAMICS` 选择动力学路径；Direct GPU 的前提才明确要求两者都选 GPU。不要只看到其中一个开关就报告整个管线已在 GPU 上。[宽相位字段](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L665-L692)。

### 3.1 CUDA context、事件和所有权

`PxCudaContextManager` 管理一个 CUDA context 的访问；文档说明其基础是 CUDA driver API，不是一个 CUDART 包装。手写 CUDA 调用需要遵守 acquire/release context，递归获取必须配对。context 锁、scene 读写锁和 CUDA 完成事件解决不同问题；拥有其中一个不代表另外两个已满足。[context 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cudamanager/PxCudaContextManager.h#L184-L195)、[获取与释放](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cudamanager/PxCudaContextManager.h#L378-L407)。本版旧 context manager 的分配/拷贝 helper 已标 deprecated，替代入口在 `physx::Ext::PxCudaHelpersExt`。[旧接口提示](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/cudamanager/PxCudaContextManager.h#L197-L255)、[原生新 helper](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCudaHelpersExt.h#L119-L225)。

Direct GPU 每次操作的 `startEvent` 表示开始前等待的依赖；`finishEvent` 非空时由 SDK 在末尾记录，调用方必须等它完成后再消费/复用 buffer。`finishEvent=NULL` 的契约是返回前等待操作完成；不是“自动得到 CPU tensor”。返回 bool 也可能不包含异步 CUDA 错误。[get/set 事件说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L252-L279)。

一条应用数据依赖应明确为：policy 写 action buffer → producer event → Direct GPU set → set 完成 → simulate/fetch → Direct GPU get → get 完成 → observation consumer。接口没有提供 `simulate(startEvent)` 供任意外部 stream 自动接入，因此应用必须在启动物理前确保所需 set 已完成；不要只在另一个 stream 发起等待就立刻推进 CPU 场景。若要 CPU 日志，再增加显式 D→H 拷贝及完成边界。GPU指针、索引数组和事件在消费结束前不能释放或被下一 batch 覆盖。

此接口有利于减少不必要的 GPU→CPU 往返，但不等于全流程零拷贝、任意学习库 tensor 自动兼容或有可微 autograd。dtype/结构体布局、stride、设备/context、stream 和所有权必须匹配；原生 SDK 不替应用创建 PyTorch/JAX/Gymnasium 的绑定。

## 4. Direct GPU batch 布局与读取语义

### 4.1 请求行序与对象身份

`gpuIndices` 本身位于 GPU。刚体的 index 由 `PxRigidDynamic::getGPUIndex()` 得到；articulation 使用自己的 GPU index。请求数组位置 $i$ 决定结果的第 $i$ 个块，**不是 GPU index 数值决定偏移**。刚体 pose 每项一个 `PxTransform`，速度每项一个 `PxVec3`；不要以打印的 ID 为最大值分配一个稀疏“env tensor”。[刚体入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L252-L279)。稳定 dataset ID 由应用维护，不能保存原始指针或将短期 GPU index 当永久资产身份。

对请求的 $N$ 个 articulation，定义 scene-wide $D_{max}$ 和 $L_{max}$，由 `getArticulationGPUAPIMaxCounts()` 取得。关节位置输出为：

$$
B_q=N D_{max}\,\mathrm{sizeof}(PxReal),\qquad
q_{i,j}\leftrightarrow data[iD_{max}+j],\quad 0\le j<D_i.
$$

请求子集也按**整个 Scene** 的最大计数取 stride，不是对子集重新求最大值；每个实例的有效 $D_i$ 和 link 索引需另存，padding 不当有效观测。新增更大 articulation 后要重新核对 max counts、buffer 和映射。[布局规则](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L282-L305)、[scene-wide max counts](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L388-L399)。读取位置不意味着控制目标、力和 link 状态使用相同元素类型。

| 数据 | 每请求 articulation 的块大小 | 语义 |
|---|---|---|
| JOINT_POSITION / VELOCITY | $D_{max}$ 个 PxReal | 有效部分按 low-level DOF；转动用 rad/rad·s⁻¹，平移用模型长度/长度·s⁻¹ |
| JOINT_FORCE / TARGET_POSITION / TARGET_VELOCITY | $D_{max}$ 个 PxReal | 读回先前 set 的输入/目标；**不是 simulation 更新的实际执行量** |
| ROOT_GLOBAL_POSE | 1 个 PxTransform | root pose 的 API frame，不是把任意 link pose 当 root |
| LINK_GLOBAL_POSE | $L_{max}$ 个 PxTransform | 包含 root，按 low-level link index；不是创建列表顺序 |
| LINK_INCOMING_JOINT_FORCE | $L_{max}$ 组，每组 2 个 PxVec3 | 先 force 后 torque，child joint frame；延续 E4 的参考点/单位与 root 零契约 |

字段来源：[枚举和具体块布局](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L20-L104)。向量组成的数据不能默认是调用方习惯的 AoS/SoA 或带 16-byte padding 的学习框架布局；按真实 `sizeof` 和公开结构解释，不手写“7 个 float 就等于所有 pose ABI”。

Jacobian 和 mass matrix 也可通过 `computeArticulationData` 批量计算。Jacobians 的预留块为 $(6+D_{max})\,[6+6(L_{max}-1)]$ 个 float，实际矩阵行列依 fixed/floating base 与本 articulation 的 DOF/link 数决定；实际矩阵按 `nCols*row+column` 解释。mass matrix 预留 $(D_{max}+6)^2$ 个 float，实际 fixed base 是 $D_i^2$、floating base 是 $(D_i+6)^2$。不能把块最大容量当实际数学矩阵形状。[compute 枚举](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L116-L146)。这里是动力学数值入口，不是网络反向传播接口。

### 4.2 Contact batch 不是长期保存的完整报告

`copyContactData` 接受 `maxPairs` 容量，实际写入数也在 GPU buffer；返回数据含指向内部 state 的指针，**只到下一次 simulate 前有效**，并有 pair 类型范围。浅拷贝最外层结构到 CPU 文件后不能延长内层数据生命。[原生契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L343-L357)。记录时须在有效期内抽取需要的值、复制到自己拥有的存储并保留完整性/容量标记，不能将“写了 maxPairs 条”解释为没有更多 pair。它也不自动等同 E3 的 CPU callback/CCD/friction-anchor 报告全集。

容量不只是 batch tensor：`PxGpuDynamicsMemoryConfig` 的 temp/heap 可增长语义与 contact/patch/pair 等容量字段不同；contact 与 patch stream 还是双缓冲，不能将单边字节数当总分配。[字段定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L444-L511)。CPU contact data block 的不足也可能明确导致 contact 被丢弃。[CPU 限额说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L831-L855)。不要把所有内存不足统一标成“性能变慢”，也不要在未运行时宣称当前容量足够。

## 5. Reset 是一份协议，不是把数组清零

### 5.1 CPU articulation reset

在非运行阶段，对已加入 Scene 的同一个 articulation 使用匹配 cache。先定义 reset 后要保留和要重设的内容：

| 层 | reset 要处理的内容 | 常见遗漏 |
|---|---|---|
| 广义状态 | root pose/线角速度、有效 DOF position/velocity | root 的 COM/actor frame 混用；全部字节置零使 quaternion 无效 |
| 控制与外力输入 | joint force、drive target position/velocity、link force/torque | 只改 q/v，下一步仍由上一 episode 的目标驱动 |
| 模型/参数 | 当前随机化参数、关节 motion/limits/drive、质量惯量/材料 | 默认 cache 不包含所有配置；拓扑变更使 cache/索引失效 |
| 引擎阶段 | 合法 apply、kinematic 更新、wake/sleep 与 contact/query 同步 | 在 simulate 未 fetch 时修改；以为 reset 等于撤销整个 solver history |
| 应用历史 | episode id、步数、控制器积分、滤波、动作延迟、RNG、终止信息 | 首帧混入上一回合数据，或 terminal observation 被 reset 覆盖 |

`zeroCache` 只清 cache 的规定数据区，不更新引擎，不清 user-provided/scratch/version。`eALL` 也不包括 FORCE、JOINT_TARGET_*、LINK_FORCE/TORQUE 等全部可写输入。应按 mask 明确填入合法 root transform、q/v 和需要清除的持久输入，再调用 `applyCache`；不能把 cache 的零 quaternion 直接应用。[zero/apply 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L748-L801)、[真实 flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationFlag.h#L19-L41)。

`NpArticulationReducedCoordinate::applyCache` 检查 Scene、cache version、Direct GPU 禁止条件和完整步骤阶段；位置/root transform 更新会让 link body pose/shape 与 contact manager 相关缓存相应更新。这不等于恢复全部内部 solver 历史。[实际路径](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpArticulationReducedCoordinate.cpp#L119-L163)。通过非 cache setter 批量改 joint/root state 后要按契约 `updateKinematic`；`applyCache` 对相应 flags 已处理传播，不能无脑重复执行再把加速度输出当真实测量。[更新契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L1403-L1423)。

普通刚体 reset 也必须处理 pose/velocity、正在累积的 force/acceleration、kinematic target、sleep 状态和应用历史；具体输入模式见 E2。reset 的目标是定义一个新初态，不是保证与某个早先时间点逐位相同的完整 rewind。

### 5.2 Direct GPU reset 与部分环境重置

Direct GPU 初始化后不能用 `applyCache/copyInternalStateToCache` 替代 GPU API。选择要 reset 的 articulation GPU indices，为这些请求行填写 scene-wide stride 的 q/v/root state、targets/effort 及 link 输入，然后分数据类型 `setArticulationData`，按事件保证写入完成。[GPU 写类型](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L81-L104)、[写布局](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L308-L328)、[CPU cache 禁用](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L782-L801)。

如果 reset 后立即读取 link pose/velocity，调用 `computeArticulationData(...eUPDATE_KINEMATIC,...)` 传播 root/joint 变化；如果等下一次 simulate，其入口会自动传播。这项操作会清掉 link acceleration、incoming joint force 和 joint acceleration 等 simulation 输出；不能把这些零当作 reset 后已经测量出的物理状态。[具体语义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxDirectGPUAPI.h#L116-L123)。

同 Scene 的一批环境中，只向 reset 集合写状态和应用 history。下一次 simulate 仍推进整个 Scene；未 reset 环境的时钟继续，已 reset 环境的 episode clock 从自身零点重算。不要为了一个环境 reset 偷偷多跑一整步而让其他环境多前进一步。共同 world time 与各自 episode time、episode id 应同时保存。

## 6. 随机化、种子和可复现性

随机化属于应用采样策略；原生接口负责接收合法物理参数，不替你定义概率分布。可以在 setup/reset 阶段随机 initial q/v、质量/惯量、摩擦/恢复、drive 参数等，但要满足原生取值范围与物理一致性；视觉/传感噪声在对应宿主或 E4 应用模型中。改变几何尺寸不自动等于正确改变质量属性；更新 mass/inertia 要回到 E1 的 native mass-properties 路径。

| 参数类别 | 原生/应用入口 | 隔离与记录 |
|---|---|---|
| root/q/v 与目标 | cache、joint setters 或 Direct GPU typed set | 保留实际样本、单位、DOF map；遵守合法阶段 |
| mass/inertia/COM | PxRigidBody setters、PxRigidBodyExt mass 工具 | 有限质量随机化使用正质量/有效惯量，形状尺度与 COM 一致；当前后端是否支持对应修改另核实 |
| friction/restitution/drive | PxMaterial、原生关节参数 | 共享 material/shape 会同步影响引用者；需独立资源或明确共享分组 |
| gravity/solver/backend | Scene 配置 | 同 Scene 的环境不能各自调用一次 setGravity 就获得不同全局重力；后调用覆盖 scene 配置 |
| 图像/IMU/动作延迟 | 宿主 renderer/sensor/应用控制 | 不归 core SDK 自动实现；保存时间模型和随机化版本 |

`setMass` 不自动更新惯量，也不自动唤醒对象；普通 RigidDynamic 的 mass=0 表示无限质量，articulation link 不允许该值。它不能被当作“很轻”的随机样本。[原生 mass 语义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L232-L252)。

种子记录至少包含 RNG 算法/版本、全局 seed、env id、episode id、stream id 和实际采样结果。可采用应用明确的 $s_{i,e,c}=H(s_0,i,e,c)$ 分流规则，使一个环境提前终止不改变其他环境的随机序列；这是设计建议，不是 PhysX 的 seed API 或已测试的随机性算法。只记一个整数无法恢复隐含的调用顺序或跨语言随机采样差异。

`eENABLE_ENHANCED_DETERMINISM` 的范围也有限：默认要求相同 scene/actor 创建顺序和时间步方案；增强模式在不互相干扰的附加 actors 加入时提供更强稳定性，但仍要求每次新 scene 中一致的插入顺序和步进方式，且当前不支持 GPU。[原生约束](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L223-L243)。它不保证跨 CPU/GPU、编译器、平台、宿主版本或任意线程回调的逐位复现。相同 seed、统计一致、轨迹容差一致和 bitwise 一致是不同验收级别，本章没有做任何一种运行验收。

## 7. 学习接口属于哪一层

PhysX 提供状态/控制/接触/动力学与批量 GPU 数据接口；它不替任务定义 reward、成功条件、episode 长度、终止/截断或 policy optimizer。原生 shader/callback 的存在也不意味着 SDK 自带一个 Gymnasium `reset/step` 环境。

官方 Isaac Lab 文档将 actions、observations、rewards、reset 等组合在 manager-based 或 direct task workflow 中；这是**Isaac Lab 层**的环境组织，不能把 `ManagerBasedRLEnv/DirectRLEnv` 当 PhysX SDK 原生类。[官方任务工作流](https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/task_workflows.html)仅作为职责归属参考：它是 2026-10-09 查阅的可变文档，不是本章固定 SDK 的兼容性矩阵，未验证其当前安装或所嵌入 PhysX 版本。Isaac Sim/UniSim 的资产、渲染、绑定与学习适配同样须按各自版本核实，不能由 SDK 源码代替宿主验收。

### 7.1 一次 policy step 与物理步

假设 application 每 $r$ 个固定物理步更新一次动作，单步时长 $h$，则：

$$
\Delta t_{policy}=rh,\qquad f_{policy}=\frac{1}{rh}.
$$

动作在区间内如何保持必须按 E2 的原生语义：drive target/关节 effort 可持久，普通刚体 force accumulator 有自己的清理时机，impulse 不能每个子步无意重复施加。若 $r$ 改变，动作区间、reward 积分、折扣与观测时间都可能变化；不是只调速而保持同一个任务。

应用可按以下次序定义一条 transition：固定 env/episode/step → 写入 $a_k$ → 完成 $r$ 次合法 step/fetch → 采样 $o_{k+1}$ 与本区间事件 → 计算 reward/termination/truncation → 保存 terminal observation → reset 指定环境 → 返回新 episode 的初始观测并明确标记。SDK 不替应用选择这套顺序，自动 reset 的宿主返回语义必须逐项核实。

### 7.2 终止、截断与无效数据

- **terminated**：任务定义的终态，例如成功/失败；由任务逻辑决定，不能直接用 actor sleeping 代替。
- **truncated**：外部限制导致采样终止，例如 rollout time limit；不能自动等同物理失败。若时间上限本身就是 MDP 的终态定义，应按该定义处理。
- **invalid/engine error**：输入不合法、硬件错误、buffer 不完整等技术无效；应保留原因并按数据策略隔离，不能假装负 reward 的有效 transition。

对“持续任务因外部时间限制被截断”的假设，TD 目标可写为：

$$
y_k=r_k+\gamma(1-\mathrm{terminated}_k)V(o^{final}_{k+1}).
$$

truncated 并不在该假设下直接屏蔽 bootstrap；实际算法与任务要自行约定。关键是 $o^{final}_{k+1}$ 必须属于旧 episode 的终端采样，不能替换成 auto-reset 后的下一回合 $o_0$。这条式子解释数据契约，没有训练任何 policy，也不声称 SDK 实现了 TD 学习。

## 8. 数据记录、回放与 serialization 分层

### 8.1 面向数据集的最小记录契约

| 类别 | 必须明确的字段 | 防止什么混淆 |
|---|---|---|
| 身份 | SDK source/binary/宿主/绑定版本、模型与 cooked asset hash、配置 schema | 固定源码 SHA 被误当实际运行 binary |
| 索引 | env/episode/step、稳定对象 ID、DOF/link/GPU 请求行映射版本 | GPU index、数组顺序、名字/指针失效 |
| 时间 | scene step、实际 $h$、policy decimation、采样/区间时间、sensor/render 时间 | wall FPS、物理时间、episode 时间混成一个 frame |
| 状态/动作 | root frame、q/v、target/effort、单位、分量顺序/shape/stride/dtype | 控制输入当实际执行，padding 当 DOF |
| 观测 | 值、validity、frame/作用点、接触容量/缺项、图像格式 | 缺失数据填零，局部 wrench 当完整 wrench |
| 任务/随机化 | reward、terminated/truncated/invalid、terminal obs、参数样本/RNG | reset 覆盖终端状态、不能重现采样顺序 |
| 存储 | schema 版本、字节序/压缩、完成标记、校验与丢包/丢帧记录 | 半写文件或浅拷贝被当完整数据 |

`PxScene::getTimestamp` 是完成 step 后增加的内部 `PxU32` 计数，不是秒数，也不适合作为永不重复的跨 scene/episode 全局 ID。[声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L234-L240)。time 用实际 timestep 累加并定义原点；指针/userData 只用于当时的应用映射，导出时转换成稳定值。consumer 线程必须消费自己拥有或有明确租期的 buffer，不能异步存储已被下一步重用的 contact/query 内部数组。

### 8.2 三种回放不能混为一谈

| 回放目标 | 需要的数据 | 不能自动保证 |
|---|---|---|
| 轨迹/可视化回放 | 已记录 pose、标签、观测和时间，宿主重绘或展示 | 再次计算的力、碰撞和像素与原运行一致 |
| 输入重演 | 初始模型/参数/RNG、动作和 timestep/调用顺序 | 不同后端或缺少内部状态时完全相同的轨迹 |
| 完整计算检查点恢复 | 引擎支持范围内状态 + 所有应用历史/资源/同步状态 | 普通 cache、PVD 文件或 collection 就是完整 checkpoint |

E4 的 OmniPVD 是调试对象/属性记录；它的 stream 生命周期与 reader/viewer 是另一契约。不能因为录制能显示，就宣称 solver caches、GPU events、policy/RNG 已恢复。

### 8.3 原生 Collection 是对象图的序列化入口

当前原生流程是 `PxCollectionExt::createCollection(scene)` 或手工 `PxCreateCollection()+add` → `PxSerialization::complete` → `isSerializable` → 序列化 → 管理容器与对象生命周期。`PxCollectionExt` 收集 Scene 中的 actor/aggregate/articulation/PxJoint，并明确不包括其他 PxConstraint 类型；头文件旧示意中的 `PxSerialization::createCollection` 不应照抄成当前 API。[实际 collection 工厂](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCollectionExt.h#L69-L86)、[complete/可序列化条件](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L61-L117)。

对象图依赖包含 actor→shape→material/mesh、articulation→link/joint、aggregate→actor；`followJoints` 扩展 jointed chain。跨 collection 的共享依赖需要有效且唯一的 `PxSerialObjectId`，避免悬空引用和 subordinate orphan。可以复用共享资产集合再实例化 actor 集合，这和“所有环境共享一个可变状态对象”不同。[官方集合构造](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetserialization/SnippetSerialization.cpp#L72-L79)。

Binary 输入要求 **128-byte 对齐**，binary 格式身份要兼容。实际 reader 验证 header、binary GUID 兼容性与 platform tag；不能只比较主版本或扩展名。[公开契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L143-L160)、[实际 reader](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/serialization/Binary/SnBinaryDeserialization.cpp#L42-L77)。对象在提供的可写内存中构造并解析引用，不能加载后立即释放或把同一块内存当作两个独立可变实例。[原地构造](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physxextensions/src/serialization/Binary/SnBinaryDeserialization.cpp#L210-L239)。

`collection->release()` 只释放容器，不释放其中对象。反序列化 backing memory 必须保留到对象释放之后；官方 snippet 在 physics 对象销毁后才 free 这些块。[容器所有权](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxCollection.h#L214-L226)、[官方销毁顺序](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetserialization/SnippetSerialization.cpp#L234-L252)。若用 `PxCollectionExt::releaseObjects`，还要遵守引用计数与 exclusive shape 的前提，否则可能重复 release。[具体警告](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxCollectionExt.h#L22-L39)。

本版 XML/RepX serialization 已标 deprecated，头文件指向 USD Physics 作为另一系统；这不等于 SDK 在本章已经提供/验收了任意 USD 场景导入、宿主传感器或完整 runtime checkpoint。Binary/XML 都禁止对同时被模拟的 scene 对象做序列化。[XML 状态与边界](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L124-L180)、[binary 序列化契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxSerialization.h#L184-L209)。policy、RNG、任务 FSM、文件句柄、事件/线程、宿主图像管线需另行保存；不要以 object graph 序列化成功代替完整恢复证明。

### 8.4 Sim-to-real 的数据边界

面向真实机器人使用数据时，先对齐可观测量与控制接口，再讨论随机化覆盖。joint target 不等于电机电流/实测扭矩，solver contact impulse/h 是指定区间的平均力，刚性 body acceleration 也不是带偏置/频响的 IMU 输出。E2–E4 已定义这些差别，数据集应保留原始语义，而不是在导出时统一改名为“真实传感器读数”。

| 差距来源 | 应记录/对齐的内容 | 当前不能推断的结论 |
|---|---|---|
| 几何、质量、惯量与接触 | 实际测量/建模来源、单位、cooking/简化、材料参数与不确定范围 | 一组能稳定求解的参数就是实物标定值 |
| 执行器和控制 | 原生 force/drive 模式、限幅、控制周期、命令保持、外部驱动器映射 | 目标轨迹相同就有相同带宽/电机饱和/能量 |
| 传感和标定 | frame、外参、采样/曝光区间、噪声/偏置/带宽、validity | 干净几何测距或无噪声状态已经等同实物观测 |
| 时序与通信 | command/measurement 时间、延迟分布、丢帧、采样保持、reset/启动过渡 | GPU 计算快就等于控制回路延迟小或符合实时时限 |

随机化参数分布与种子应和实际抽到的参数一起保存；这些分布是否覆盖真实系统，必须另有实物数据、标定或明确文献证据。无来源的范围只能标为设计假设，不能从 PhysX 默认值推导成“真实世界分布”。状态/输入重演、数据 schema 一致与最终策略迁移效果分别验收；本章只交付接口和记录方法，不做实物标定、迁移训练或新实验。

## 9. 扩展接口与性能成本放在哪一层

| 需求 | 原生接点 | 当前课程边界 |
|---|---|---|
| 应用 task scheduler | PxCpuDispatcher/PxBaseTask/PxTaskManager | 生命周期、不可阻塞和配对；不自行实现线程框架 |
| pair 可见性/报告 | simulation shader/filter callback、query filter、simulation event callback | 线程与采样契约；E3/E4 已展开 |
| 批量 GPU 前后处理 | PxDirectGPUAPI + CUDA events/context + 自有 buffers | 数据传递和布局；不增加 autograd 或学习绑定 |
| joints、质量工具、scene query helper、serialization | PhysXExtensions 原生库 | 区分扩展 API 与 core；保留各类对象生命周期 |
| 自定义可序列化类型 | PxSerializationRegistry/PxSerializer | 类型注册和反注册；自定义类型完整 serializer/metadata 在 E6 深入 |
| 自定义几何/约束/后端 | 对应原生扩展与实现 | E6 专题，不能由一个 callback 的存在推断全引擎可替换 |

`PxInitExtensions` 应在使用需要分配的 extensions API 前调用，`PxCloseExtensions` 按契约释放其 foundation 使用；并非每个 `Px*` API 都只需链接 core 库。[扩展生命周期](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/extensions/PxExtensionsAPI.h#L44-L64)。`PxSerializationRegistry` 的注册/反注册与对象 `release` 各有责任，不能在仍被调用时销毁自定义 serializer。[registry](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxSerialFramework.h#L249-L286)。

分析未来的 wall time 时，至少拆成 setup/cooking/加载与可能的后端初始化、物理 step/fetch、GPU copies/同步、观测/渲染、policy、日志。CPU-only binary 的编译、运行初始化与宿主网络/JIT 成本也不同；原生 C++ SDK 不是 Python JIT 循环。理论上若 $N$ 个环境、每次 policy step 含 $r$ 个物理步，完成 $K$ 次 policy step 用 wall time $T$：

$$
\mathrm{physics\ transitions/s}=\frac{NKr}{T},\qquad
\mathrm{policy\ transitions/s}=\frac{NK}{T}.
$$

这些式子只是定义计数口径；变长/失效环境要按实际有效完成数统计。异步 submit 时间不是完整 wall time，隐藏同步和数据拷贝也要纳入对应测量边界。PVD/debug instrumentation 会改变成本，E4 已说明；本章没有给任何性能数字或 GPU 加速结论。

## 10. 原生片段与常见误区

[`e5_batch_boundaries.cpp`](../examples/e5_batch_boundaries.cpp)包含两个独立阅读函数：原生 simulation filter shader 按应用约定的 env_id 与共享静态 world flag 隔离 pair；Direct GPU 关节位置读取根据 scene-wide maxDofs 检查容量并使用原生事件参数。没有初始化 scene/context、分配 GPU 内存或执行入口；不是环境框架或可运行训练示例。[检查与限制](validation/e5.md)。

- **空间摆开就以为独立**：还要隔离碰撞、query、共享可变材料、控制/RNG/history；共用动态物体可耦合多个环境。
- **filter 回调里加锁等磁盘**：先分清无状态 shader、可并发 callback 与不可阻塞 task；把持久记录移到拥有数据的应用队列。
- **CPU getter 仍能调用就以为 Direct GPU 生效**：检查 scene 模式、初始化、对应 typed API、device buffer 和事件；返回值不等于有效新数据。
- **请求两个机器人就按这两个的最大 DOF 分配**：articulation stride 使用整个 Scene 最大值，且实际有效维度仍逐实例保存。
- **reset 后 q/v 对了但机器人突然动**：查旧 target/effort/link force、kinematic/drive 状态、action delay/history 和 reset 集合。
- **同 seed 就宣称可复现**：记录 RNG 流、实际参数、创建/调用顺序与后端；明确要复现的证据级别。
- **collection/PVD 文件当完整 checkpoint**：检查 backing memory、对象依赖、版本/平台以及未包含的应用/内部状态。
- **把 auto-reset 的下一帧写入旧 transition**：先保存 terminal observation 和原因，再写新 episode 初态；技术 invalid 不伪装任务终止。

## 11. 阅读练习与答案

**题 1**：两个环境在同 Scene 相隔 100 m，且各自放入 aggregate，能保证完全隔离吗？

**答案**：不能。aggregate 是 broad-phase 分组；距离不是碰撞/查询策略，飞出物体仍可能相互影响。还需 simulation/query 过滤、状态索引、可变资产与任务历史隔离。

**题 2**：3 个 Scene 共用一个 scratch buffer，同时提交后逐个 fetch，正确吗？

**答案**：不正确。每个在途 simulation 可写 scratch，须独立存储或等相关 fetch 完成后再复用；共用 dispatcher 也不使 scratch 自动隔离。

**题 3**：Direct GPU get 返回 true，finishEvent 非空，CPU 能立即读取 data 指针吗？

**答案**：不能。data 是 GPU buffer，操作还需等 finishEvent；CPU 读还需合法 D→H/mapping 与同步。bool 不保证包含异步 CUDA 错误。

**题 4**：整个 Scene 的 maxDofs=12，选取两个分别为 3/7 DOF 的 articulation，关节位置需预留几个 PxReal？

**答案**：24 个，第二块从偏移 12 开始；只使用每块的前 3/7 个有效 DOF。不是 10 个，也不是按子集最大值得到的 14 个。

**题 5**：JOINT_FORCE 读回 2.0，可以当作接触时测得的执行扭矩吗？

**答案**：不可以。该枚举读回之前 set 的关节 force/torque 输入，simulation 不更新它；需要使用与物理问题对应的观测字段和 frame/采样约定。

**题 6**：调用 zeroCache，再 applyCache(eALL)，就重置所有目标和力了吗？

**答案**：没有。zeroCache 不更新引擎，eALL 不包括全部目标/力字段，且全零 root quaternion 无效。需要合法填值、明确 mask 与应用历史 reset。

**题 7**：GPU reset 后为了获取新 link pose 调用 UPDATE_KINEMATIC，incoming joint force 变为零意味着没有外载荷吗？

**答案**：不是。这项操作明确清掉相关 simulation 输出；该零的原因是更新/有效性边界，不是完成新一步求解后的无载荷测量。

**题 8**：外部 time limit 导致 truncated 后，bootstrap 使用 auto-reset 后的初始观测有何问题？

**答案**：它跨到了下一个 episode。按持续任务可 bootstrap 的假设，应保存旧 episode 的 final observation；是否 bootstrap 仍由具体任务和算法决定。

**题 9**：binary collection 加载成功后，release 容器并 free 输入内存能保留 actor 吗？

**答案**：不能这样做。release 容器不释放 actor，反序列化对象仍占用 backing memory；先按依赖/引用规则释放对象，再释放输入内存。

**题 10**：增强 determinism 和相同 seed 能保证 CPU 与 GPU 逐位相同吗？

**答案**：不能。该 flag 的范围有限且本版不支持 GPU；种子不涵盖后端/创建顺序/线程时序和完整内部状态。必须明确复现级别并另行验收。

## 后续边界

A8/A9 的核心 SDK 与应用/宿主责任，以及 B6 的任务、GPU 数据、同步和扩展入口已作为源码课程交付。GPU 内核/特色几何/自定义求解扩展留到 E6；宿主学习环境、传感器/renderer、训练、吞吐、bitwise replay 和 sim-to-real 效果均未验收。实际运行证据最终复用 DexLab，E7 再统一双路线审校与证据入口。
