# 共同基础：带着同一组问题读不同引擎

[回到首页](../README.md) · [学习路线](learning-paths.md)

推荐先读[Physics-Based Simulation 的前四章及接触主线](physics-based-simulation.md)，再结合[Solver 教程](solver-guide/README.md)使用本页查概念。

本页统一概念与记号，帮助你定位各仓章节。公式注明假设；字段顺序、坐标约定、默认数值和支持矩阵仍以所选引擎的固定源码为准。原生接口之间的差异正是课程要解释的内容。

## 1. 单位、坐标、姿态与参考点 · A1 / B0

采用 SI 时，长度为 m、质量为 kg、时间为 s，力为 N，力矩为 N·m，转动惯量为 kg·m²。角度输入是否需要 degree/radian 转换、网格文件使用何种长度单位，应在导入阶段明确记录。

定义 $R_{WB}$ 将 B 坐标中的列向量转换到世界 W，$p_{WB}$ 是 B 原点在 W 中的位置，则 B 中一点 $r_B$ 的世界位置为：

$$p_W=p_{WB}+R_{WB}r_B.$$

这里旋转矩阵正交，位置和向量必须使用同一长度单位。四元数的分量顺序并无跨库统一保证；`wxyz` 和 `xyzw` 不能直接互换。body 原点、质心、惯性主轴和 geom 原点也可能不同。

同一刚体上 O、P 两点，在相同表达坐标中有 $v_P=v_O+\omega\times(p_P-p_O)$。同一外力系统换取矩点时，$\tau_P=\tau_O-(p_P-p_O)\times f$。换参考点与旋转表达坐标是两步操作；先写清这两个定义，再使用空间向量 API。

阅读任务：找到一个状态数组，写下“分量顺序、表达坐标、参考点、单位”四项。只有“6 维向量”不足以说明含义。[Newton 的原生 State 字段](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py)与 [MuJoCo 的坐标说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst)可作为两个不同入口；涉及文档冲突时继续查实现。

## 2. 几何与惯量 · A1 / B0

视觉网格、碰撞表示和质量分布服务不同目的。设质量为 $m$，质心 C 相对原点 O 的位移为 $r$，两个惯量张量在同一轴系表达，则平行轴公式为：

$$I_O=I_C+m\big((r^Tr)\mathbf{1}-rr^T\big).$$

若主轴惯量为 $I_D$，转到另一表达轴系用 $I=RI_DR^T$。这些变换不会自动解决错误的原单位、重复计入质量或不合理的碰撞近似。

阅读任务：解释导入器是否使用资产内的惯量、根据几何/密度重新计算，或者覆盖缺失值；检查缩放对质量和惯量的影响。相关原生实例见 [MuJoCo 建模](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/modeling.rst)与 [PhysX 刚体接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h)。

## 3. 状态、输入与派生量 · A2 / B0

把数据分成至少四类：随时间推进的状态、用户输入、从状态计算的派生量、求解器工作缓存。配置 $q$ 和广义速度 $v$ 不总是同维；存在四元数等表示时，通常要用映射 $\dot q=N(q)v$，不能直接执行逐元素的 `q += dt * v`。

“快照”需要说明其覆盖范围：模型拓扑/参数、物理状态、输入、时钟、历史缓存、求解器状态、控制器记忆、随机数发生器是否一起保存。将数组赋给另一个变量也可能只是别名；保存历史读数应核对复制语义。

阅读任务：沿一个 reset 或 restore 调用找出实际写入字段，再指出未包含的状态。入口可选 [MuJoCo 状态枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h)、[Genesis Scene](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py)或 [Drake Context](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h)。

## 4. 时间、积分器与求解器 · A2 / B1 / B3 / B4

外部控制周期决定何时重新计算输入；物理步长决定一次推进覆盖的仿真时间；内部子步和迭代负责具体数值过程；显示刷新消费状态。它们可能有不同频率，迭代次数不是推进了多少个物理时刻。

在最简单的光滑二阶系统中，半隐式 Euler 可以写成 $v_{k+1}=v_k+h\,a(q_k,v_k,u_k)$，然后按新速度更新配置。实际引擎还可能隐式处理阻尼、耦合接触/积分，或使用四元数积分，因此这只是理解入口，不能直接替代原生更新式。

阅读任务：从 step 找到状态真正写回的位置，再找 solver 循环和终止条件。记录一步使用的 $h$、控制在哪个阶段生效、加速度的时间含义。固定源码入口：[MuJoCo forward](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c)、[SuperDex integration](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_integration.cpp)、[Drake Simulator](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h)。

## 5. 接触模型与数值近似 · A4 / B2 / B3

碰撞检测给出几何候选、距离或接触信息；接触模型决定法向和切向的作用关系；求解器处理形成的数值问题。刚性约束、柔顺接触、penalty 和不同摩擦近似会有不同参数语义，填入相同数字不等于相同物理模型。

例如在无黏附、各向同性 Coulomb 静摩擦模型下，切向合力满足 $\|f_t\|\leq\mu_s f_n$，其中 $f_n\geq0$。这是可行范围，不是说每个静止接触都取等号。真实引擎可能采用摩擦锥近似、速度正则化、接触柔顺或冲量形式，必须继续追实现。

阅读任务：查两种材料怎样组合、接触参数的量纲、摩擦的分支和实际返回量。入门依据：[Drake 接触模型说明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h)、[MuJoCo computation](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst)。

## 6. 观测、力与证据 · A6 / A9 / B5

力的单位为 N，冲量的单位为 N·s。给定明确时间窗 $[t,t+h]$ 的冲量 $J=\int_t^{t+h}f(s)\,ds$，可计算该窗平均力 $J/h$；它不自动等于某个时刻的瞬时力。控制命令、驱动输出、约束反力和传感器读数也需要分别说明。

日志应至少包含：仿真时间、采样阶段、引擎/后端身份、字段名称、单位、坐标及参考点。图像用于观察，回放用于呈现状态历史；支持物理结论的证据需要相应协议与独立读回。

阅读任务：从一个读回接口向上追踪生产者，判断它对应积分前、积分后、上一内部阶段还是某个平均窗口。然后进入 [DexLab 案例入口](dexlab.md)，核对报告是否具备你需要的版本与工况。

已发布的深入阅读：

| 引擎 | 动力学与数值迭代 | 材料与力观测 |
|---|---|---|
| MuJoCo | [流水线](https://github.com/huangkiki/mujoco-learning/blob/main/docs/dynamics-and-pipeline.md) · [求解与积分](https://github.com/huangkiki/mujoco-learning/blob/main/docs/solvers-and-integration.md) | [接触模型](https://github.com/huangkiki/mujoco-learning/blob/main/docs/contact-models.md) · [力观测](https://github.com/huangkiki/mujoco-learning/blob/main/docs/force-observations.md) |
| SuperDex | [隐式积分与求解](https://github.com/huangkiki/superdex-learning/blob/main/docs/contact-solvers-forces.md) | [接触、材料与 query](https://github.com/huangkiki/superdex-learning/blob/main/docs/contact-solvers-forces.md) |
| Genesis | [约束求解与积分](https://github.com/huangkiki/genesis-learning/blob/main/docs/contact-solvers-forces.md) | [接触、材料与采样](https://github.com/huangkiki/genesis-learning/blob/main/docs/contact-solvers-forces.md) |
| Newton Physics | [XPBD 与后端分支](https://github.com/huangkiki/newton-learning/blob/main/docs/contact-solvers-forces.md) | [材料、wrench 与读回缺项](https://github.com/huangkiki/newton-learning/blob/main/docs/contact-solvers-forces.md) |
| PhysX | [CPU PGS/TGS 与积分](https://github.com/huangkiki/physx-learning/blob/main/docs/contact-solvers.md) | [材料、法向点与切向 anchor](https://github.com/huangkiki/physx-learning/blob/main/docs/contact-solvers.md) |
| Drake | [动力学装配与 SAP](https://github.com/huangkiki/drake-learning/blob/main/docs/contact-solvers.md) | [几何材料](https://github.com/huangkiki/drake-learning/blob/main/docs/contact-models.md) · [力与采样](https://github.com/huangkiki/drake-learning/blob/main/docs/contact-observation.md) |

六仓 E3 专题均已发布。以上链接用于对照原生机制，不能组成性能或物理准确性排名。

六个引擎的传感、查询与图像专题均已展开：

- **MuJoCo：**[传感与采样](https://github.com/huangkiki/mujoco-learning/blob/main/docs/sensors-and-sampling.md) → [相机与几何查询](https://github.com/huangkiki/mujoco-learning/blob/main/docs/cameras-and-geometry-queries.md) → [渲染与 viewer](https://github.com/huangkiki/mujoco-learning/blob/main/docs/rendering-and-viewer.md)。从输出块和采样阶段理解 history，再区分投影、射线、像素及窗口资源。
- **SuperDex：**[传感器、渲染与可视化](https://github.com/huangkiki/superdex-learning/blob/main/docs/sensors-rendering.md)。区分相机元数据、物理查询与图像宿主，追踪 RGBA、读回缓存和帧延迟。
- **Genesis：**[传感器、渲染与可视化](https://github.com/huangkiki/genesis-learning/blob/main/docs/sensors-rendering.md)。区分普通传感器与相机缓存，理解轴向深度、射线距离、分割映射及触觉感知模型。
- **Newton Physics：**[传感、查询与渲染](https://github.com/huangkiki/newton-learning/blob/main/docs/sensors-rendering.md)。追踪观测存储与加速度产生者，区分共享几何树、相机通道及 viewer 的数据生命周期。
- **PhysX：**[传感、场景查询与调试显示](https://github.com/huangkiki/physx-learning/blob/main/docs/sensors-rendering.md)。理解过滤、最近命中与多命中完整性，再区分力和加速度、调试图元以及宿主图像管线。
- **Drake：**[相机与渲染](https://github.com/huangkiki/drake-learning/blob/main/docs/sensors-rendering.md) → [采样与延迟](https://github.com/huangkiki/drake-learning/blob/main/docs/sensor-timing.md) → [惯性与力传感](https://github.com/huangkiki/drake-learning/blob/main/docs/inertial-force-sensing.md)。沿系统端口追踪图像、捕获位姿和时间，再核对动力学输入的采样阶段。

阅读任务：为一项观测分别写下产生者、采样时间、坐标、单位、shape 和无效值，再解释为何一个 RGB 图像、接触力数组和当前关节状态可能并非同一时刻的观测。已有示例仅做源码与静态检查。

## 7. 批量、学习接口与数据归属 · A8 / A9 / B6

批量轴表示多个逻辑世界。执行它们的 CPU worker、设备线程和进程是调度资源，未必与世界一一对应。共享模型、复用工作区或共享一个 Scene 时，应分别检查哪些状态在每次调用前恢复、哪些参数仍共享、读回数组是否会被下一次调用覆盖。

自动 reset 的返回观测可能已经属于新 episode。先保存真实终态观测，再按任务定义区分终止、时间截断和无效数据，才能解释学习目标与回放。记录逻辑世界、episode、物理时间、采样阶段和随机流；保存一个 state 数组不自动覆盖模型、控制器、随机数及外部资源。

| 已发布专题 | 建议追踪的问题 |
|---|---|
| MuJoCo：[CPU 批量](https://github.com/huangkiki/mujoco-learning/blob/main/docs/cpu-batching.md) → [MJX 与设备](https://github.com/huangkiki/mujoco-learning/blob/main/docs/mjx-and-device-data.md) → [学习与随机化](https://github.com/huangkiki/mujoco-learning/blob/main/docs/learning-and-randomization.md) → [记录与回放](https://github.com/huangkiki/mujoco-learning/blob/main/docs/recording-and-replay.md) | 每个 worker 的 Data 怎样初始化？JAX/Warp 的状态和容量有何差异？state mask 没有保存什么？ |
| SuperDex：[批量、学习与数据](https://github.com/huangkiki/superdex-learning/blob/main/docs/batch-learning-data.md) | 两层 vector 如何传递 seed 和 reset？共享 Scene 的延迟读取属于哪个环境？诊断 JSON 能恢复状态吗？ |
| Genesis：[批量、学习与数据](https://github.com/huangkiki/genesis-learning/blob/main/docs/batch-learning-data.md) | 局部 reset 改变哪些时钟？官方 Go2 环境何时覆盖终态？记录器和轨迹回放分别拥有哪些数据？ |
| Newton Physics：[批量、学习与数据](https://github.com/huangkiki/newton-learning/blob/main/docs/batch-learning-data.md) | 多 world 如何分段和重置？策略循环的实际推进时间是什么？ViewerFile 保存了什么、没有保存什么？ |
| PhysX：[批量、学习与数据](https://github.com/huangkiki/physx-learning/blob/main/docs/batch-learning-data.md) | Scene 隔离与 Direct GPU 布局/事件怎样配合？重置应清哪些输入？序列化对象与 backing memory 由谁释放？ |
| Drake：[环境生命周期](https://github.com/huangkiki/drake-learning/blob/main/docs/batch-lifecycle.md) → [随机化与学习](https://github.com/huangkiki/drake-learning/blob/main/docs/randomness-learning.md) → [日志与回放](https://github.com/huangkiki/drake-learning/blob/main/docs/data-replay.md) | Context、Simulator 和外部资源怎样隔离？Python MonteCarlo 是否并行？logger 的时间和 trajectory 的有效域如何解释？ |

六仓批量、学习接口与数据专题均已发布。这些章节建立原生机制与数据契约，没有训练、性能测量或跨后端重现结果。

## 8. 扩展、多物理与可微边界 · B4 / B6 / B7

判断一项能力时，沿着“公开入口 → 实际消费者 → 状态更新 → 恢复或反向路径”追踪。同名材料、存在的配置项或可构造的类，都需要继续核对实际调用者、后端和支持条件。梯度接口还要说明求导变量、离散事件、求解误差及缺失路径；有反向函数不代表整个任务处处光滑。

| 已发布专题 | 建议追踪的问题 |
|---|---|
| MuJoCo：[回调与插件](https://github.com/huangkiki/mujoco-learning/blob/main/docs/extensions-and-callbacks.md) · [flex 与弹性](https://github.com/huangkiki/mujoco-learning/blob/main/docs/flex-and-elasticity.md) · [IPC](https://github.com/huangkiki/mujoco-learning/blob/main/docs/ipc-contact-mode.md) · [后端与微分](https://github.com/huangkiki/mujoco-learning/blob/main/docs/backends-and-differentiation.md) · [流体与源码追踪](https://github.com/huangkiki/mujoco-learning/blob/main/docs/multiphysics-and-source-trace.md) | 插件状态由谁拥有？材料与接触模式有哪些编译限制？有限差分、JAX 与 Warp 的状态及反向边界有何差异？ |
| SuperDex：[材料、扩展与可微](https://github.com/huangkiki/superdex-learning/blob/main/docs/extensions-boundaries.md) | 壳、杆、ROM 的状态和量纲是什么？隐式伴随实际解什么方程？构建开关、绑定和接触反向如何限制可用组合？ |
| Genesis：[多物理、可微与扩展](https://github.com/huangkiki/genesis-learning/blob/main/docs/extensions-boundaries.md) | material 怎样选择 solver？哪些材料函数被显式、隐式或外部耦合器消费？窗口重算、传感器历史和缺失反向怎样影响能力判断？ |
| Newton Physics：[求解、耦合与可微](https://github.com/huangkiki/newton-learning/blob/main/docs/extensions-boundaries.md) | 同一材料在不同 solver 中如何离散？MPM 如何隔离与重置？耦合迭代及 Tape 需要保存哪些状态？ |
| PhysX：[扩展与多物理](https://github.com/huangkiki/physx-learning/blob/main/docs/extensions-boundaries.md) | 自定义几何和约束行由谁拥有？FEM 乘子与刚体冲量如何区分？GPU buffer、stream 和 event 有哪些同步责任？ |
| Drake：[原生扩展](https://github.com/huangkiki/drake-learning/blob/main/docs/systems-extensions.md) · [标量与可微](https://github.com/huangkiki/drake-learning/blob/main/docs/scalar-capabilities.md) · [特色与综合追踪](https://github.com/huangkiki/drake-learning/blob/main/docs/engine-boundaries.md) | System 转换后 Context 怎样建立？几何、SAP 与 FEM 各支持哪些标量？优化模型和仿真图有哪些不同前提？ |

六仓扩展专题均已发布。新的先修路线与 Solver 教程正在推进；E7 全路线安装与综合审校继续暂停；最新状态见[交付进度](progress.md)。

阅读任务：从所选引擎找出一个“有入口但存在使用条件”的例子，分别写出源码版本、消费者、有效组合、状态所有者及未验证项。以上章节仅做源码与静态验证，没有进行梯度实验或物理资格测试。

## 到各引擎继续

[MuJoCo 课程](https://github.com/huangkiki/mujoco-learning/blob/main/docs/curriculum.md) · [SuperDex 课程](https://github.com/huangkiki/superdex-learning/blob/main/docs/curriculum.md) · [Genesis 课程](https://github.com/huangkiki/genesis-learning/blob/main/docs/curriculum.md) · [Newton 课程](https://github.com/huangkiki/newton-learning/blob/main/docs/curriculum.md) · [PhysX 课程](https://github.com/huangkiki/physx-learning/blob/main/docs/curriculum.md) · [Drake 课程](https://github.com/huangkiki/drake-learning/blob/main/docs/curriculum.md)

对照阅读时保留引擎差异，分别记录接口、源码与实验证据。各课程目录中的待开发项仍是待开发项，本页的概念地图不替代它们。
