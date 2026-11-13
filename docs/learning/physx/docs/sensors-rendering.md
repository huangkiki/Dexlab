# E4：传感、场景查询与调试显示

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [完整课程](curriculum.md) · [源码地图](source-map.md) · [本章检查](validation/e4.md)

先修 [E1](modeling-state-time.md) 的 frame、状态所有权与 `simulate/fetchResults`；力观测接续 [E3](contact-solvers.md)。本章完成 A6 的原生能力与应用边界：先识别要观测的量，再选择查询、动力学数据或宿主图像管线。它不是相机/雷达产品实现或运行验收。

**阅读基线**：`ovphysx-0.6.3`，固定提交 `da950a3537927784951853c66618036f332ca0ce`，SDK 头文件 5.11.0。此身份只约束本文的原生 C++ API 和实现；不代表历史 Isaac Sim 5.1 / UniSim 1.7.10 的内置 binary、宿主传感器实现或当前安装状态。实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab)，本次不运行仿真、渲染、基准或训练。

## 1. 先问观测来自哪一层

| 目标 | 本版原生入口 | 输出与责任边界 |
|---|---|---|
| 几何距离/遮挡/相交 | `PxScene::raycast/sweep/overlap`，或 `PxGeometryQuery` | 碰撞几何的命中信息；没有自动的激光扫描周期、噪声、强度或像素图 |
| 刚体/关节状态 | pose/velocity、articulation cache | 物理状态，需要显式 frame、索引、采样阶段；不是已经标定的编码器/IMU |
| 受力与加速度 | contact point/anchor impulse、incoming joint force、body/link acceleration | 数值与有效性各不相同；见第 5 节及 E3 |
| 碰撞形状/法向/约束图示 | `PxVisualizationParameter`、`PxRenderBuffer` | world 调试点/线/三角形，绘制由应用完成；不返回 RGB/H×W 深度图 |
| 状态调试、录制与远端查看 | PVD、OmniPVD | 调试协议/对象与属性流；viewer、transport 和显示管线另有职责 |
| RGB、光学 depth、instance/semantic segmentation | 应用或宿主 renderer/sensor pipeline | 视觉资产、相机内外参、光照、材质、像素格式、曝光/时间戳、GPU readback 与标签映射均须宿主定义 |

原生 SDK 可以作为自建传感器的几何和动力学基础。所谓“PhysX 支持某宿主 RGB 相机”必须区分核心物理、绑定/资产适配、renderer、sensor 扩展版本，不能反向把宿主能力写成核心 `PxScene` 的原生像素接口。[查询接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L135-L221)、[调试 buffer](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxRenderBuffer.h#L44-L133)、[PVD scene client](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvdSceneClient.h#L54-L108)。

## 2. 三类几何查询的输入与结果

### 2.1 Raycast、sweep、overlap 不是三个传感器

**Raycast** 对一条有限射线求交：

$$
x(t)=o+t d,\quad \|d\|=1,\quad 0\le t\le D.
$$

$o$ 为 world 原点、$d$ 为 world 单位方向，$D$ 和 hit.distance 都用模型长度单位。归一化不是装饰：非单位方向会使参数不再等于几何距离。头文件的 range 描述包含零，但本固定 CPU `multiQuery` 对 raycast 实际检查 `distance>0`；原创示例使用有限正数。[公开声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L135-L161)、[实际输入检查](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L757-L793)。从物体内部发射的行为依几何而异；不要统一假定返回出口面。

**Sweep** 将一个支持的 geometry 以固定姿态沿方向平移，回答“这一段平移先遇到什么”。不是对物体施力，也不执行动态碰撞响应。查询几何支持 box/sphere/capsule/convex core/convex mesh；不能直接以任意三角网格作为扫掠体。`inflation` 扩大扫掠几何，相应命中距离不能冒充未膨胀表面的距离。`eASSUME_NO_INITIAL_OVERLAP` 只适用于确知初始不重叠的条件；`eMTD` 的重叠 distance 可为负。[sweep 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L163-L193)、[hit flags/初始重叠](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h#L30-L57)、[distance 语义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h#L91-L112)。

**Overlap** 在给定 pose 判断相交对象集合，没有沿射线的最近距离排序，也不返回像 raycast 一样的 position/normal。普通 overlap 应提供 touch buffer，并将过滤结果设为 TOUCH 或用 `eNO_BLOCK`；需要“有没有任何一个”时可用 `eANY_HIT`。不要由 `PxQueryHitType` 的一般说明推断 overlap 的 BLOCK 是可靠的“最近对象”，本接口明确不建议它。[overlap 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L195-L221)、[实际 buffer 检查](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L784-L787)。

`PxGeometryQuery` 则直接对调用方给定的 geometry/pose 求交，不负责 scene 中 actor/shape 的发现和 queryFilterData。它适合明确对象对的局部计算，不能自动代替 scene 的空间索引。支持的几何组合逐项列在[原生声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryQuery.h#L39-L110)，不要据某种 geometry 可以 raycast 就断言它也支持所有 sweep/overlap 组合。

### 2.2 Hit 字段是带有效位的数据

| 字段/类型 | 形状/单位 | 使用条件 |
|---|---|---|
| `PxRaycastHit` / `PxSweepHit` | 单个 location hit + actor/shape 指针 | 不是图像 tensor，也不是 SDK 代管的长期观测对象 |
| `position`, `normal` | `PxVec3`，world；长度/单位方向 | 查返回的 `hit.flags` 是否含 POSITION/NORMAL，不能只看请求 flags |
| `distance` | 标量长度 | ray 为沿单位方向的距离；sweep 初始重叠/MTD 需特殊处理 |
| `u,v` | ray 的无量纲重心坐标 | 只在支持的 mesh/heightfield 等几何及 UV 有效位下使用；不是像素坐标 |
| `faceIndex` | cooked geometry 的面索引 | 可能为 `0xffffffff`；mesh cooking 可重映射；不是类别 ID |
| `actor`, `shape` | 原生对象指针 | 只在对应对象仍活着时有效；复制 hit 不延长对象生命 |
| `PxOverlapHit` | face index 基类 + actor/shape | 无 location hit 的 position/normal/distance 字段 |

来源：[数据继承和指针](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryReport.h#L25-L45)、[face index/有效位](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h#L67-L133)、[overlap hit](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h#L135-L143)。图像分割若要稳定标签，应在对象仍有效的同步边界用应用映射转换成稳定 ID，并保存 ID→语义定义；不能把内存地址或 faceIndex 原样当跨设备类别。

## 3. 过滤、最近命中与多命中完整性

### 3.1 三层过滤不要串用

1. **Shape 是否参与查询**：`eSCENE_QUERY_SHAPE` 独立于 `eSIMULATION_SHAPE`。一个 trigger 也可参与 scene queries，不能靠“它是 trigger”保证传感射线忽略它。[Shape flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L41-L90)。
2. **查询选哪些候选**：`PxQueryFlag::eSTATIC/eDYNAMIC`、Shape 的 `queryFilterData` 与传入 `PxQueryFilterData.data`。Simulation filter data 是另一套字段；改了碰撞 mask 不自动改射线可见性。[两套 filter data](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxShape.h#L196-L232)。
3. **具体命中决策**：启用 PREFILTER/POSTFILTER 并提供 callback，分别在精确相交前/后决定 NONE、TOUCH、BLOCK。preFilter 只允许修改 `eMODIFIABLE_FLAGS` 中的 hit flags；postFilter 可以覆盖前面的 hit type。[callback 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryFiltering.h#L130-L173)。

默认硬编码 mask 规则是四个 32-bit word 对应 AND 后 OR。若 query data 全零则不做这个筛选；否则：

$$
keep=\bigvee_{i=0}^{3}(q_i\mathbin{\&}s_i),\qquad keep=0\Rightarrow skip.
$$

它先于用户 callback 执行，所以 callback 不一定看得到已被 mask 排除的对象。`eDISABLE_HARDCODED_FILTER` 与 legacy batch flag 在本版共用 bit 6，可显式跳过该规则；不能靠只提供 callback 达到同样效果。[flags](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryFiltering.h#L31-L57)、[实际方程与 prefilter 顺序](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L312-L352)。

过滤“自身”通常要排除机器人全部相关 actors/shapes，而不是只排除传感器挂载的那个 link；哪些支架/玻璃/外壳可见属于模型约定。并发 ray queries 的 filter callback 不应修改 scene 或共享可变状态；每次查询的输出 buffer 独立管理。

### 3.2 ANY 不等于 closest，bool 不等于 hasBlock

默认无 touch buffer、无用户 filter 时，单 raycast 返回最近 BLOCK；有 touch capacity 时，候选默认按 TOUCH 处理。以源码的 `maxNbTouches` 判断为准，避免把头文件概述中 `nbTouches` 的措辞误读为“查询前要手工填写已命中数量”。[默认分类实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L481-L500)。

`PxQueryFlag::eANY_HIT` 是整次 scene query 的提前退出：遇到任何被接受的交点就放入 `block`，**不保证最近**；`PxHitFlag::eANY_HIT` 则用于单个多 primitive 几何内的求交行为。两者名字近似，作用层次不同，测距不能为性能随意打开。[query flag](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryFiltering.h#L40-L45)、[hit flag](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/geometry/PxGeometryHit.h#L37-L43)、[实际提前退出](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L563-L586)。

API 的 bool 表示找到某种命中，不保证 `hasBlock=true`。如果全是 TOUCH，必须读 touches；只有 `hasBlock` 为真才读 `block`。有 BLOCK 时，只报告不远于最近 BLOCK 的 TOUCH；若要沿途全部可见命中，应明确返回 TOUCH/使用 NO_BLOCK，并处理多 primitive flags 和 buffer 完整性。命中序列不保证按距离排序。[结果契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryReport.h#L68-L122)、[分类说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryFiltering.h#L69-L96)。

**固定 buffer 不是完整性保证**：`PxHitBuffer` 满后会丢弃任意一部分 touches，不保证保留最近 N 个；溢出不自动给 warning/error。`count==capacity` 只能说明“可能截断”，不能区分恰好装满和实际超出。需要全量时可继承 native callback 分块复制，在 `processTouches` 返回 true 继续，并按自己的内存/停止策略记录是否完整；不能只增大数组一次就宣布 all hits。[buffer 截断定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryReport.h#L128-L181)。

`PxQueryCache` 的已缓存 shape **跳过过滤并被当成 BLOCK**，且只用于不带 touch buffer 的相应查询。更换 mask、排除自身、删除对象时必须考虑缓存失效；否则“上一帧有效”会绕开这一帧的可见性策略。[缓存契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxQueryReport.h#L214-L246)。本章示例不使用 cache，避免混入这层状态。

## 4. 更新时间、调用链与线程边界

### 4.1 Scene query 并非直接扫描最新 C++ 对象

当前源码链为 `PxScene` → [`NpScene::raycast/sweep/overlap`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneQueries.cpp#L515-L539) → 本 scene 的 query system → [`SceneQueries::multiQuery`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqQuery.cpp#L757-L814) → pruner 候选、过滤、具体 geometry 求交、hit callback。查询对象具有自己维护的 bounds/树；源码还支持独立 query system，不能假定所有调用都经过相同的 `PxScene` 生命周期。[独立 query system 示例入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetquerysystemallqueries/SnippetQuerySystemAllQueries.cpp#L304-L333)。

默认 query 更新与 `fetchResults` 相接。`PxSceneQueryUpdateMode` 分成 build+commit、只 build、都不做；同步 changed bounds 是必需阶段，build/commit 控制树构建和提交。只 build 时，refit/commit 可延迟到下一 query 或显式 flush；手动模式则由应用按文档完成 `sceneQueriesUpdate/fetchQueries`，不能调用 query 后假定所有手动工作已自动完成。[更新模式](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQueryDesc.h#L82-L114)。

`multiQuery` 的逻辑 const 内部会 `flushUpdates()`；[`PrunerManager::flushUpdates`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/scenequery/src/SqManager.cpp#L396-L418)在有脏数据时取锁、更新 shape 并 commit。这解释了“查询是读接口”为什么仍可能产生维护工作。需要大量并行查询时，可在合法写阶段显式 `flushQueryUpdates()`，减少首个 query 的维护停顿；这不是零成本或加速幅度的实测承诺。[公开说明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L120-L133)、[NpScene 写检查](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneQueries.cpp#L595-L603)。

`sceneQueriesUpdate()` 启动树构建，与 `fetchQueries()` 配对；后者等待并提交，不是 `fetchResults()` 的替代品。[接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQuerySystem.h#L307-L361)、[实际 fetchQueries 检查](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneQueries.cpp#L744-L768)。选 `PxDynamicTreeSecondaryPruner::eNONE` 时，新插入对象还可能在构建完成前暂时不可查询；这是被明确记录的可见性取舍，不应报告为传感器“随机漏检”。[secondary pruner](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneQueryDesc.h#L47-L76)。

### 4.2 建议采用一个明确的采样边界

本章的应用约定：`simulate(h_k)` → 成功 `fetchResults` → 必需的 query 同步 → 在一致的状态读取 sensor pose 和 query → 复制值/稳定 ID → 交给后续线程。记录已完成物理步编号 $k$、$t_k=\sum_{j\le k}h_j$、采样 pose、query flags/mask 和 range；不要把渲染 FPS 当物理采样率。

若传感器外参 $T_{AS}$ 固定在 Actor 上：

$$
T_{WS}=T_{WA}T_{AS},\qquad o_W=T_{WS}o_S,\qquad d_W=R_{WS}d_S.
$$

先用 Actor/COM 的正确约定构造 $T_{WS}$，不要把 COM 偏置重复乘进去。多束扫描若全部使用同一 $T_{WS}$，就是同一状态的理想快照；滚动扫描必须给每束独立时间/pose 并定义世界运动的采样方法。单次 `raycast` 不会自动模拟转速、发射时差、返回波形或运动畸变。

`eREQUIRE_RW_LOCK` 启用时，scene 读取前要取得 read lock；多个 readers 可以并发，reader/writer 互斥，禁止 read→write 锁升级。原生 `PxSceneReadLock/PxSceneWriteLock` 提供 RAII。[锁契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1454-L1506)、[RAII](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneLock.h#L20-L92)。锁不是物理完成事件，不能因为持锁就跳过 `fetchResults` 或解除某个 API 的运行阶段禁令。query buffer/cache/callback 的生命周期和线程安全仍由应用负责。

示例接受调用方提供的 pose 快照。调用方必须在相同状态边界取得它，并阻止该 pose 所属场景在准备与 query 之间被其他线程推进；函数内部的 query read lock 不能追溯修复已经过期的外参。

## 5. 力、加速度与理想 IMU 的边界

### 5.1 哪个数组才是观测

下表 $M,L,T$ 分别表示模型的质量、长度与时间单位。数据项的参考帧、作用点、有效位和采样区间必须随观测一起保存。

| 数据 | 索引/参考帧/单位 | 限制 |
|---|---|---|
| contact points / friction anchors | 各自 world 点与冲量，质量·长度/时间 | 见 E3：两数组不一一对应，CCD/torsion 有缺项；不是完整触觉阵列 |
| `cache.jointForce` | 有效 DOF 顺序，力或力矩 | E2 的关节 effort 输入/计算输出字段，不能自动当实测电机扭矩 |
| `cache.linkIncomingJointForce` | N=getNbLinks，low-level link index；child joint frame；力 $ML/T^2$、力矩 $ML^2/T^2$ | 父 link 传给子 link 的总空间力；root 为零，不等于 root 完全不受力 |
| `cache.linkAcceleration` / `getLinkAcceleration` | COM，world，经典线/角加速度 | 第一物理步前零；不是把 `PxSpatialVelocity` 名字中的 velocity 当单位 |
| `PxRigidBody::getLinear/AngularAcceleration` | COM/world 对应状态，长度/时间²、弧度/时间² | RigidDynamic 需 scene creation flag；Direct GPU 普通 CPU getter 有额外限制 |

[`linkIncomingJointForce` 声明](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L278-L300)使用 `eLINK_INCOMING_JOINT_FORCE` 读取，不能靠 cache 创建后直接读未刷新的数组。CPU [`copyInternalStateToCache` 的对应路径](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp#L383-L444)综合惯量×加速度、内部/外部项和 solver impulse/h，把作用点移到 joint，再旋转到 child joint frame；GPU 路径读已经计算的数据。它是求解状态导出的合成传力，不能按名字猜“仅接触”或“仅 drive”。

若用 public child actor pose 与 `getChildPose()` 构造 $T_{WJ}$，将 joint force 转到 world 后，关于目标点 $o$ 的力矩是：

$$
F_W=R_{WJ}F_J,\qquad
\tau_{W,o}=R_{WJ}\tau_J+(p_{WJ}-o)\times F_W.
$$

两边观测 frame/作用方向/时间区间必须一致才可比较，不能将 joint torque 与某个 contact normal 的大小直接相减。

### 5.2 “返回零”可能只是未启用

本版 RigidDynamic 加速度默认不计算，需要在 `PxSceneDesc` 创建 scene 时开启 **不可运行时修改**的 `eENABLE_BODY_ACCELERATIONS`。未启用则普通 getter 返回零；articulation links 不以该 flag 为前提。[flag 定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxSceneDesc.h#L297-L320)、[公开 getter](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxRigidBody.h#L470-L497)。

当前 CPU ordinary-body 实现在模拟任务中按上一状态速度差除本步时间计算，遇 reset flag 则置零并重置历史。因而接触冲量、硬设速度和 reset 都会影响解释，不是连续瞬时加速度仪。[实际差分/重置](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L3805-L3836)。非 Direct-GPU 的 GPU dynamics 路径可在第一次 getter 时触发 lazy copy；Direct GPU CPU getter 则警告后返回零，应使用匹配的 Direct GPU API 数据入口。[具体分支](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpRigidDynamic.cpp#L181-L221)。本文未执行 GPU，也不把此数据入口存在视为 GPU 观测验收。

Articulation CPU cache 加速度会把 motion acceleration 与 solver delta velocity/h 合并，GPU 分支使用已经完成的值；首次参与仿真前为零。[cache 实现](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp#L346-L380)、[getLinkAcceleration 阶段/COM 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxArticulationReducedCoordinate.h#L1253-L1270)。默认状态、首次有效、禁用、Direct GPU 不支持当前 getter、缺失报告应分别编码，而不是都混成零测量。

### 5.3 从经典加速度构造理想 IMU

以下是应用层数学模型，**不是本 SDK 已提供的 IMU sensor 类**。假设传感器刚性固定在 body、使用 world 经典 COM 加速度 $a_C$、角速度 $\omega$、角加速度 $\alpha$，世界偏移 $r=p_S-p_C$：

$$
a_S^W=a_C^W+\alpha^W\times r+\omega^W\times(\omega^W\times r),
$$

$$
f_S=R_{WS}^{T}(a_S^W-g_W),\qquad
\omega_S=R_{WS}^{T}\omega_W.
$$

$f_S$ 是理想加速度计的 specific force，单位长度/时间²；静止支撑且 $a=0$ 时为 $-R^Tg$，自由落体 $a=g$ 时为 0。不能把“经典 world acceleration”直接贴上“IMU 三轴读数”。若模型禁用重力、存在额外 fictitious force 或外参时变，需重新定义模型。偏置、噪声、带宽、采样保持、积分/抗混叠、饱和、延迟和时间戳都由应用提供，本章没有仿真这些特性。

“触觉图”同样需要接触点到 taxel/软层的映射、面积/压力定义和时间滤波；SDK contact point/anchor 数量随接触流变化，不是固定 H×W 触觉阵列。E3 的 reported impulse completeness 标记必须随数据保留。

## 6. 几何测距与 RGB/depth/segmentation

### 6.1 射线距离不等于相机轴向 depth

为便于推导，此处**自行约定**光学坐标 x 向右、y 向下、z 向前，像素中心 $(u+0.5,v+0.5)$，针孔模型无畸变、全局快门。这个约定不是 SDK 的强制相机坐标系。内参 $f_x,f_y,c_x,c_y$ 用像素单位：

$$
a=\left(\frac{u+0.5-c_x}{f_x},\frac{v+0.5-c_y}{f_y},1\right)^T,
\qquad d_S=a/\|a\|.
$$

将 $d_S$ 转到 world 后，raycast 给 range $\rho$，轴向深度为：

$$
z=\rho(d_S)_z,\qquad p_S=\rho d_S.
$$

离主光轴越远，$z$ 与 $\rho$ 的差别越大；仅在中心方向重合。未命中应有 invalid mask，不能无声填 0 让算法理解为物体贴在镜头上。近远裁剪、背面、透明度、视觉/碰撞网格差异也会使几何测距不同于宿主深度产品。

原生 flags `eMESH_BOTH_SIDES`、`eMESH_MULTIPLE` 等控制几何求交；材质 restitution/friction 不会自动变成光学反射率或透射率。SDK raycast 的一个布尔/距离结果不含 LiDAR 强度、多回波、RGB radiance 或光学散射模型。

### 6.2 宿主必须给出的图像契约

下表是**设计/验收时应固定的契约示例**，不是声称 PhysX 某 API 已按该 tensor 返回：

| 产品 | 推荐明确的结构 | 必须记录 |
|---|---|---|
| RGB | H×W×3 或明确的 RGBA/BGRA、dtype | 色彩空间/线性或编码值、通道序、行 pitch、曝光/色调映射、视觉材质/光照 |
| depth | H×W float + valid mask | 轴向 z 或 ray range、长度单位、near/far、无效值、投影/畸变定义 |
| instance/semantic segmentation | H×W 整数标签 + ID 映射表 | instance 与 class 的区别、背景/未知 ID、透明/遮挡/抗锯齿策略、稳定标签版本 |
| ray scan | B 束 range/valid，可选位置/法向 | 每束方向、时间/pose、可见性 mask、返回数量规则、query geometry 版本 |
| force/IMU | 明确分量顺序的定长向量 + validity | frame/作用点、单位、区间或瞬时定义、滤波/延迟、物理步与采样时刻 |

接入 Isaac/UniSim 等宿主时逐一核实这些字段属于哪个 renderer/sensor 扩展、用哪个视觉资产以及何时从 PhysX 状态同步；没有查明版本和实现，就标未知。不要从某张 viewer 截图推断像素缓冲、标签或 depth 已可导出。将宿主图像帧和物理状态配对也需要显式同步/完成信号；GPU 提交完成不等于 CPU 已拿到本帧像素。

## 7. 调试绘制和 PVD/OmniPVD

### 7.1 PxRenderBuffer 不是 framebuffer

本版 `PxRenderBuffer` 暴露 points、lines、triangles 的数量和指针。`PxDebugPoint/Line/Triangle` 保存 world 位置和 32-bit ARGB debug color；不是彩色相机像素或光照材质。虽然同一头文件还定义 `PxDebugText`，这个 buffer 接口没有相应 getTexts；PVD scene client 另外有 `drawText`。[实际结构/接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/common/PxRenderBuffer.h#L23-L133)。

可视化要同时考虑 master `eSCALE`、具体参数的非零值，以及 actor/shape 的 eVISUALIZATION 标志；`setVisualizationCullingBox` 是 world 裁剪。长度为 1 的法向线经过显示 scale 后不再表示“1 单位力”。[master/对象标志](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxVisualizationParameter.h#L39-L64)、[scene 接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1288-L1341)。`eCONTACT_FORCE` 已 deprecated 且等于 `eCONTACT_IMPULSE`；箭头源码直接把 impulse 乘显示 scale，没有自动除 dt。[枚举](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxVisualizationParameter.h#L105-L131)、[实际 contact 绘制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScVisualize.cpp#L43-L99)。

`getRenderBuffer()` 禁止在 simulation running 时调用。完成 fetch 后读取/复制值，不能保留内部数组指针跨下一次更新，更不能在另一个线程边模拟边读它。[公开限制](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/PxScene.h#L1330-L1341)。图元的采样还存在阶段差异：step 入口调用 `visualize()`，清空上帧并生成对象图示；finalization 在接触/CCD 冲量完成后 `visualizeContacts()`，fetch 再把 scene 图元 append 进公开 buffer。因此“fetch 后安全可读”不等于“所有图元在一个后积分时刻采样”。[step 入口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpScene.cpp#L2926-L2931)、[清理/生成](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpDebugViz.cpp#L1012-L1043)、[contact 时机](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/simulationcontroller/src/ScPipeline.cpp#L2810-L2818)、[fetch 合并](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/NpSceneFetchResults.cpp#L153-L158)。

### 7.2 官方 snippet 的窗口也属于应用

`SnippetRender.cpp` 创建 GLUT/OpenGL 窗口，`startRender` 配置 `gluPerspective/gluLookAt`，`finishRender` swap buffers。这是官方示例 renderer，不是 PhysX 核心解算器在 `simulate()` 内输出 RGB。[窗口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrender/SnippetRender.cpp#L483-L508)、[投影与交换](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrender/SnippetRender.cpp#L698-L732)。SnippetCamera 的矩阵含 `-mDir`，不能把这个显示约定与上节选择的 +Z 光学坐标混用。[相机 transform](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetrender/SnippetCamera.cpp#L71-L81)。

如果目标只是碰撞几何是否合理，调试图元/示例绘制就有价值；若目标是光学传感训练数据，需另有像素输出、视觉材质和传感时间模型。本章没有构建或启动窗口，也没有验证 offscreen renderer。

### 7.3 PVD：调试连接不是传感器总线

原生 `PxPvd` 由应用创建/持有，以 `connect(transport,flags)` 连接；transport 可以是默认 socket 或文件实现。Instrumentation 的 DEBUG/PROFILE/MEMORY 控制不同数据，DEBUG 有明确开销，不能一边全量调试一边宣称测到未扰动性能。[PVD 顶层接口](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvd.h#L20-L115)、[transport factory](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvdTransport.h#L82-L95)。

Scene client 的 `eTRANSMIT_CONTACTS/SCENEQUERIES/CONSTRAINTS` 默认关闭，且依赖 instrumentation DEBUG。`updateCamera` 指的是 PVD 应用的显示窗口，不是创建一个物理相机。[flags 与显示方法](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/pvd/PxPvdSceneClient.h#L34-L104)。`isConnected` 的 cached 与底层状态有不同检查成本/延迟；“连上了”也不证明目标 scene 数据、所有流和 viewer 图形都已经正确显示。当前构建是否启用 `PX_SUPPORT_PVD`、接收端与版本兼容均须实际核实。

### 7.4 OmniPVD：录制状态、writer 与 transport 分开

当前 `PxOmniPvd` 的 OVD integration 版本为 3.1，它描述流中对象/属性的集成 schema，不是 SDK 版本。`getWriter()` 归 `PxOmniPvd` 所有，不能由应用交给 destroyOmniPvdWriter；裸 writer 访问不是线程安全。需要并发写时用 exclusive access 或 `ScopedExclusiveWriter`；注册/注销 event callback 仍有单线程要求。[版本与 writer 契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/omnipvd/PxOmniPvd.h#L13-L134)。

正确理解录制生命周期：绑定 write stream → 在合法 scene 边界 `startSampling()` → 先记录现有状态再记录后续变化 → `stopSampling()`。重新 start 是新快照，不是 resume；stop 不替应用 flush/close transport。重新绑定 stream 会重置 writer session，但已打开 transport 可继续追加 versioned segment；若要可从 byte 0 独立读取的录制文件，应用必须管理新/reset transport 和文件边界。[完整契约](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/include/omnipvd/PxOmniPvd.h#L137-L198)。

[`NpOmniPvd::startSampling`](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/source/physx/src/omnipvd/NpOmniPvd.cpp#L108-L147)检查 sampler 和重复 start，调用 `snapshotAll` 后再给模块回调；`PX_SUPPORT_OMNI_PVD` 未启用时 writer/start 可返回 NULL/false。拥有 API 对象不证明成功录制，更不证明显示兼容。官方 snippet 展示 writer/stream 与 `PxCreatePhysics(...,omniPvd)` 的连接，不能把它当作已执行结果。[snippet 设置](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetomnipvd/SnippetOmniPvd.cpp#L76-L140)。

OmniPVD 记录对象状态/属性及变化；它不是相机视频编码器，也不保证可直接恢复 solver 的所有内部缓存。录制可读、viewer 可显示、状态可重放、精确恢复仿真是不同验收问题，后者延续 E1 的快照边界。

## 8. Headless 与多速率观测的应用契约

| 路径 | 是否需要显示窗口 | 核心责任 |
|---|---|---|
| Native physics + query/state export | 不需要窗口 | scene 生命周期、物理完成与值复制；本章未执行 |
| Debug primitives + 应用 viewer | 由 viewer 决定 | SDK 生成图元，应用投影/绘制；不同阶段图元不可冒充统一传感帧 |
| PVD/OmniPVD file/socket capture | 录制端不必开 viewer 窗口 | stream、flush/close、schema 与 reader 边界 |
| Headless RGB/depth renderer | 不开交互窗口，不代表不需要图形设备/上下文 | 宿主的 offscreen backend、像素格式与 GPU 同步仍要单独配置/验收 |

官方 OmniPVD snippet 的 `RENDER_SNIPPET` 条件区分 render loop 与非窗口循环，说明绘制是可拆开的应用路径；本文只阅读，不执行该循环。[编译条件](https://github.com/NVIDIA-Omniverse/PhysX/blob/da950a3537927784951853c66618036f332ca0ce/physx/snippets/snippetomnipvd/SnippetOmniPvd.cpp#L225-L259)。

对于 $h=1$ ms 的物理时钟和 10 ms 的理想 query sensor 周期，可每 10 个已完成步取一次状态；这是调度例子，没有实测。若周期比值不是整数，记录实际采样步/time 与策略，不默默用取整后频率代替目标频率。相机曝光覆盖一个区间、ray scan 可能每束不同时间、contact impulse 则对应物理步区间；一个全局“frameId”不能自动使这些数据时间一致。

reset 后应同时管理 sensor 历史：清空差分/滤波历史、失效 query cache、更新稳定标签映射与 epoch、重新定义第一帧有效性。跨线程/设备交付要复制值并注明所有权；需要零拷贝时则显式提供 buffer 有效期与完成同步，不从 `const` 或一个指针推断安全。

## 9. 原生示例与易错点

[`e4_scene_query.cpp`](../examples/e4_scene_query.cpp)是一个单束几何 range 的原创阅读函数：明确世界变换、有限正 range、按原生 preFilter 排除提供的自身 actors、使用最近 BLOCK、检查 hit 有效位并复制数值。没有 `main`、没有 SDK 初始化/链接/运行，既不合成 RGB 也不模拟噪声/时间扫描。原生 filter callback 的继承用于 SDK 既有接口，没有新封装框架。[语法检查与限制](validation/e4.md)。

排查时按数据来源顺序检查：

- **射线穿过模型**：核对 query flag/mask、shape 是否参与 SQ、碰撞与视觉几何是否一致、方向/距离、背面/初始内部命中、pruner 同步；不要先怀疑 renderer。
- **测距偶尔不是最近**：查 QueryFlag/HitFlag 的 ANY_HIT、cache 跳过滤、touch buffer/default hit type；bool true 并不总给有效 block。
- **多命中数量总等于容量**：保留可能截断标记，使用分块 callback 或适当容量协议；不要称“所有障碍物”。
- **IMU 永远零**：检查 RigidDynamic 的 creation flag、Direct GPU getter 边界、第一步/reset；再区分 world 经典 acceleration 与 specific force。
- **关节力坐标对不上**：检查 child joint frame、root 零的契约、作用点力矩平移和 low-level link index；不要换成 cache.jointForce 猜数值。
- **调试箭头长短像力大小**：实际可能是 scaled impulse；需回到 E3 的冲量单位和 interval，不从截图读牛顿。
- **headless 没窗口但拿不到 RGB**：物理、debug recording 与宿主 offscreen 图形管线分别验证；一个 `simulate/fetchResults` 成功不是相机输出完成。

## 10. 阅读练习与答案

**题 1**：对 30° 离轴射线，hit.distance=2 m，按本章 +Z 光学约定，轴向 depth 是多少？

**答案**：$z=2\cos30^\circ\approx1.732$ m；2 m 是 ray range。除非产品明确采用 range，否则不能原样写 depth。

**题 2**：为最近距离打开 `PxQueryFlag::eANY_HIT` 后得到某个 hit，能否保证它比其他目标近？

**答案**：不能。它提前返回任意被接受命中；用于遮挡布尔判定有意义，不能充当 closest 的加速开关。

**题 3**：应用提供 preFilter，为什么目标完全没有进入回调？

**答案**：先检查 PREFILTER 是否启用及 callback 是否非空，再查 Shape SQ flag、静/动态筛选和更早的硬编码 query mask；后者可在 callback 前排除目标。simulation mask 是另一套数据。

**题 4**：固定 touch buffer 容量 16，返回 16 个 hit，是否表示世界中恰好有 16 个？

**答案**：不是。可能刚好装满，也可能截断，且丢弃不保证按距离。需要另有完整性协议或分块 callback。

**题 5**：旧 query cache 命中的 shape 已被新 mask 排除，这次仍可能报告它吗？

**答案**：会有这种风险：cache 跳过滤且按 BLOCK 处理。策略变化要失效缓存，删除对象还必须使缓存指针失效。

**题 6**：桌上静止的理想 IMU，world 经典加速度为 0；为什么理想 accelerometer 不为 0？

**答案**：specific force 是 $R^T(a-g)$，静止支撑下为 $-R^Tg$。若实际 SDK getter 是因 flag 未开而返回零，则连有效的 $a$ 也尚未取得。

**题 7**：root 的 linkIncomingJointForce 返回零，是否能证明机器人底座没有外力？

**答案**：不能。root 没有 incoming joint，本字段按契约为零；应选取与观测目标一致的其他数据，不能将缺少父关节当平衡证明。

**题 8**：fetch 后复制了 debug buffer，能否作为严格同步的 RGB、深度和接触力帧？

**答案**：不能。它是点/线/三角形，而且对象图示和 contact 图元有不同生成阶段；RGB/depth 另需 renderer，力观测应读取带单位/时段的数值。

**题 9**：OmniPVD stop 后再次 start 是否继续原录制？是不是自动生成一个独立文件？

**答案**：再次 start 生成新的当前状态快照；writer/transport 边界分开。旧 stream 可追加 segment，stop 不替应用 flush/close，也不自动创建独立文件。

## 后续边界

A6 的核心能力、原生数据契约和宿主责任已作为源码课程交付。宿主 RGB/depth/segmentation API、实际 GPU 导出、图像与物理同步误差、窗口/headless 可运行性、传感噪声和标定均未验收。E5 可在 E2/E4 实际合入后继续学习/数据接口，E6 深入后端与扩展，E7 再结合 DexLab 整理已有实验；没有新建传感实验或独立评分系统。
