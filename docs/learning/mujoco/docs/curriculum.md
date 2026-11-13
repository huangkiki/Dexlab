# MuJoCo 两条学习路线

[首篇导读](guide.md)已经建立对象关系和核心入口；它不代表下面全部专题已经完成。[源码地图](source-map.md)提供固定提交入口。

应用路线无需先学求解器源码；原理路线建议先理解 A0–A4，并具备线性代数和基础动力学知识。两条路线都完整规划，当前以讲解、源码与最小 API 片段为交付物。

| 单元 | 主题 | 必须讲清的内容 | 状态 |
|---|---|---|---|
| A0 | 安装与对象地图 | 支持环境、包/核心/宿主身份、构建入口、核心对象及生命周期 | 专题待开发 |
| A1 | 模型、坐标与资产 | 单位、坐标、姿态、惯量、碰撞/视觉、导入器、资产许可 | [E1 已交付](modeling-and-frames.md)，源码/静态验收 |
| A2 | 状态与时间 | 配置/速度维度、时间步/子步、reset、快照、所有权、采样阶段 | [E1 已交付](state-and-time.md)，源码/静态验收 |
| A3 | 驱动与控制 | 状态设置与控制命令、驱动器、饱和、PD、回调与控制频率 | [E2 已交付](actuation-and-control.md)，源码/静态验收 |
| A4 | 接触 API | 碰撞过滤、接触观测、摩擦/恢复/柔顺参数的原生语义 | [E3 已交付](contact-models.md)，含[力读数](force-observations.md)；源码/静态验收 |
| A5 | 机器人与运动学 | 模型导入、关节映射、FK/IK、限位、约束、外部控制集成 | [E2 已交付](robotics-and-kinematics.md)，含 E1 导入基础；IK 片段未运行 |
| A6 | 传感器与渲染 | RGB/depth/分割/射线/力/触觉、坐标/单位/更新阶段、GUI/headless | [E4 传感采样](sensors-and-sampling.md)、[相机查询](cameras-and-geometry-queries.md)、[渲染/viewer](rendering-and-viewer.md)已交付；源码/静态验收，无图像或设备运行验收 |
| A7 | 任务编排 | 接近/闭合/保持/释放的控制接口与状态机设计，后续引用 DexLab 案例 | [E2 接口设计已交付](task-interfaces.md)；无抓取实验，后续复用 DexLab |
| A8 | 并行与学习接口 | CPU/GPU、批量隔离、reset/step、终止/截断、随机种子和官方学习接口 | [E5 CPU批量](cpu-batching.md)、[MJX设备数据](mjx-and-device-data.md)、[学习契约](learning-and-randomization.md)已交付；原生接口与应用任务层分开，无训练/设备运行验收 |
| A9 | 数据与 sim-to-real | 状态/观测导出、时间戳、元数据、回放、随机化及模型差距 | [E5随机化](learning-and-randomization.md)与[记录/回放](recording-and-replay.md)已交付；不宣称sim-to-real或跨后端重现已实测 |
| B0 | 动力学与数据结构 | 配置空间、广义速度/力、惯量、约束、空间向量及内存布局 | [E1 基础](state-and-time.md) + [E3 动力学/稀疏装配已交付](dynamics-and-pipeline.md) |
| B1 | 一步仿真的源码 | 公开入口到执行分支、碰撞/装配/求解/积分/更新顺序 | [E3 已交付](dynamics-and-pipeline.md)，原生 CPU 分支 |
| B2 | 接触模型与组合律 | 几何表示、法向/摩擦律、材料组合、柔顺/正则化与量纲 | [E3 已交付](contact-models.md)，核心软接触主线 |
| B3 | 求解器与线性代数 | 目标/方程、残差、迭代、线性求解、warm start、岛与终止条件 | [E3 已交付](solvers-and-integration.md)，PGS/CG/Newton 与 NoSlip |
| B4 | 积分与数值语义 | 积分器/solver/子步的区别、精度、容差、稳定性假设及可微限制 | [E1 基础](state-and-time.md) + [E3 metric/收敛/积分推导已交付](solvers-and-integration.md) |
| B5 | 力与冲量观测 | 广义/空间/约束量、坐标转换、平均力、采样时刻与近似 | [E3 已交付](force-observations.md)，无峰值/冲量实测 |
| B6 | 性能、并行与扩展 | 编译/JIT/步进/拷贝/渲染边界、插件/回调、线程与扩展接口 | [E5批量/线程](cpu-batching.md)、[JIT/设备/拷贝](mjx-and-device-data.md)及E4渲染边界已交付；[E6插件](extensions-and-callbacks.md)、[flex](flex-and-elasticity.md)、[IPC](ipc-contact-mode.md)、[后端/导数](backends-and-differentiation.md)已交付；无运行或性能实测 |
| B7 | 源码综合导读 | 从模型字段到控制/接触/求解/观测的完整追踪、限制及 DexLab 证据索引 | [E6多物理/综合追踪已交付](multiphysics-and-source-trace.md)；E1–E6链接成执行链，DexLab证据索引及全路线审校留E7 |

本引擎特别关注：MJCF、mjSpec/mjModel/mjData、驱动器与约束、flex/IPC、原生与 GPU 后端。各课需提供先修、概念/公式、原生接口与固定源码、易错点、阅读练习和适用边界。实验不作为本阶段先决条件；后续复用 DexLab，避免重新建设一套评分和基准系统。

E3 交付的是原生核心的动力学、软接触、三类求解器与五种积分器主线；本版 flex/IPC 兼容性有明确入口，但其弹性/IPC 内循环和 GPU 后端实现已在 B6/E6 独立展开，不能仅用E3兼容性表代替这些课程。

E4 完成 A6 主线，包含 history 时序、contact/tactile 布局、版本特定相机差异和 classic 资源生命周期；Filament 仅交代其独立原生接口，不把它的完整后端实现、设备支持或性能研究提前计入 E6。E5已独立交付学习与数据主线，范围如下。

E5完成A8/A9及B6的批量/JIT/数据部分，包含rollout工作区复用与warning、MJX静态字段/后端支持、随机流归属、参数派生量、终态观测和恢复边界。32道练习与原创CPU片段仅做源码/静态验收；JAX外部源码单独固定，不冒充运行依赖锁。E6独立承担扩展机制；E7继续承担完整安装/综合审校及DexLab复用入口。

E6完成B6扩展与B7源码追踪，五篇40道带答案练习，从callback/plugin生命周期到flex材料、IPC求解/CCD、实际后端/导数链、多物理力与恢复证据。原创flex片段仅AST/XML结构审查；A0完整安装、全路线审校和DexLab证据索引仍未交付，见[E6验证](validation/e6.md)。
