# PhysX 两条学习路线

[首篇导读](guide.md)已经建立对象关系和核心入口；它不代表下面全部专题已经完成。[源码地图](source-map.md)提供固定提交入口。

应用路线无需先学求解器源码；原理路线建议先理解 A0–A4，并具备线性代数和基础动力学知识。两条路线都完整规划，当前以讲解、源码与最小 API 片段为交付物。

| 单元 | 主题 | 必须讲清的内容 | 状态 |
|---|---|---|---|
| A0 | 安装与对象地图 | 支持环境、包/核心/宿主身份、构建入口、核心对象及生命周期 | 专题待 E7 |
| A1 | 模型、坐标与资产 | 单位、坐标、姿态、惯量、碰撞/视觉、导入器、资产许可 | [E1 已交付](modeling-state-time.md)；[E2 资产/关节映射](control-robotics.md)，宿主导入运行未验收 |
| A2 | 状态与时间 | 配置/速度维度、时间步/子步、reset、快照、所有权、采样阶段 | [E1 已交付](modeling-state-time.md)，未做运行验收 |
| A3 | 驱动与控制 | 状态设置与控制命令、驱动器、饱和、PD、回调与控制频率 | [E2 源码课程已交付](control-robotics.md)，未运行控制器 |
| A4 | 接触 API | 碰撞过滤、接触观测、摩擦/恢复/柔顺参数的原生语义 | [E3 源码课程已交付](contact-solvers.md)，未运行仿真；CPU 路径与观测缺项明确 |
| A5 | 机器人与运动学 | 模型导入、关节映射、FK/IK、限位、约束、外部控制集成 | [E2 源码课程已交付](control-robotics.md)，IK/导入器责任与运行边界明确 |
| A6 | 传感器与渲染 | RGB/depth/分割/射线/力/触觉、坐标/单位/更新阶段、GUI/headless | [E4 源码课程已交付](sensors-rendering.md)，原生查询/观测与宿主图像职责分开；未运行传感器或渲染 |
| A7 | 任务编排 | 接近/闭合/保持/释放的控制接口与状态机设计，后续引用 DexLab 案例 | [E2 接口与状态机已交付](control-robotics.md)，未做任务实验 |
| A8 | 并行与学习接口 | CPU/GPU、批量隔离、reset/step、终止/截断、随机种子和官方学习接口 | [E5 源码课程已交付](batch-learning-data.md)，Scene/数据/线程隔离与宿主 RL 责任明确；未运行学习环境或训练 |
| A9 | 数据与 sim-to-real | 状态/观测导出、时间戳、元数据、回放、随机化及模型差距 | [E5 源码课程已交付](batch-learning-data.md)，记录/随机化/回放与证据范围明确；无 sim-to-real 效果验收 |
| B0 | 动力学与数据结构 | 配置空间、广义速度/力、惯量、约束、空间向量及内存布局 | [E1 刚体/状态基础已交付](modeling-state-time.md)；[E2 广义输入/Jacobian 基础已交付](control-robotics.md)；[E3 约束行/CPU 接触求解布局已交付](contact-solvers.md)；[E6 非刚体状态与扩展边界已交付](extensions-boundaries.md) |
| B1 | 一步仿真的源码 | 公开入口到执行分支、碰撞/装配/求解/积分/更新顺序 | [E3 源码课程已交付](contact-solvers.md)，未运行仿真；CPU 路径与观测缺项明确 |
| B2 | 接触模型与组合律 | 几何表示、法向/摩擦律、材料组合、柔顺/正则化与量纲 | [E3 源码课程已交付](contact-solvers.md)，未运行仿真；CPU 路径与观测缺项明确 |
| B3 | 求解器与线性代数 | 目标/方程、残差、迭代、线性求解、warm start、岛与终止条件 | [E3 源码课程已交付](contact-solvers.md)，未运行仿真；CPU 路径与观测缺项明确 |
| B4 | 积分与数值语义 | 积分器/solver/子步的区别、精度、容差、稳定性假设及可微限制 | [E1 时间边界已交付](modeling-state-time.md)；[E3 CPU PGS/TGS 积分与数值限制已交付](contact-solvers.md)，[E6 可微与 FEM 数值边界已交付](extensions-boundaries.md)，无可微实现或运行稳定性验收 |
| B5 | 力与冲量观测 | 广义/空间/约束量、坐标转换、平均力、采样时刻与近似 | [E3 接触源码课](contact-solvers.md)与 [E4 关节传力/加速度观测](sensors-rendering.md)已交付，未运行仿真；参考帧与有效性边界明确 |
| B6 | 性能、并行与扩展 | 编译/JIT/步进/拷贝/渲染边界、插件/回调、线程与扩展接口 | [E5 调度/数据/同步](batch-learning-data.md)与 [E6 自定义扩展/GPU 源码边界](extensions-boundaries.md)已交付，无性能实测 |
| B7 | 源码综合导读 | 从模型字段到控制/接触/求解/观测的完整追踪、限制及 DexLab 证据索引 | [E6 DistanceJoint 配置到输出追踪已交付](extensions-boundaries.md)，串联 E1–E5；全路线审校与 DexLab 入口待 E7，未运行 SDK |

本引擎特别关注：C++ SDK、Scene/Actor/Shape/Material、articulation、PGS/TGS 与宿主边界。各课需提供先修、概念/公式、原生接口与固定源码、易错点、阅读练习和适用边界。实验不作为本阶段先决条件；后续复用 DexLab，避免重新建设一套评分和基准系统。
