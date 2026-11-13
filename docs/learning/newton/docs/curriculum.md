# Newton Physics 两条学习路线

[首篇导读](guide.md)已经建立对象关系和核心入口；[E1 专题](modeling-state-time.md)已展开建模与状态基础；[E2 专题](control-robotics-tasks.md)已展开控制、机器人和任务接口；[E3 专题](contact-solvers-forces.md)已展开接触、求解器与力观测；[E4 专题](sensors-rendering.md)已展开传感器、几何查询与渲染显示；[E5 专题](batch-learning-data.md)已展开批量、学习接口与数据；[E6 专题](extensions-boundaries.md)已展开特色 solver、耦合、可微和完整源码追踪；A0 与全课审校仍待 E7。[源码地图](source-map.md)提供固定提交入口。

应用路线无需先学求解器源码；原理路线建议先理解 A0–A4，并具备线性代数和基础动力学知识。两条路线都完整规划，当前以讲解、源码与最小 API 片段为交付物。

| 单元 | 主题 | 必须讲清的内容 | 状态 |
|---|---|---|---|
| A0 | 安装与对象地图 | 支持环境、包/核心/宿主身份、构建入口、核心对象及生命周期 | 专题待开发 |
| A1 | 模型、坐标与资产 | 单位、坐标、姿态、惯量、碰撞/视觉、导入器、资产许可 | [E1 已交付](modeling-state-time.md)（源码/静态） |
| A2 | 状态与时间 | 配置/速度维度、时间步/子步、reset、快照、所有权、采样阶段 | [E1 已交付](modeling-state-time.md)（源码/静态） |
| A3 | 驱动与控制 | 状态设置与控制命令、驱动器、饱和、PD、回调与控制频率 | [E2 已交付](control-robotics-tasks.md)（源码/静态） |
| A4 | 接触 API | 碰撞过滤、接触观测、摩擦/恢复/柔顺参数的原生语义 | [E3 核心已交付](contact-solvers-forces.md)（源码/静态） |
| A5 | 机器人与运动学 | 模型导入、关节映射、FK/IK、限位、约束、外部控制集成 | [E2 已交付](control-robotics-tasks.md)（源码/静态） |
| A6 | 传感器与渲染 | RGB/depth/分割/射线/力/触觉、坐标/单位/更新阶段、GUI/headless | [E4 已交付](sensors-rendering.md)（源码/静态；触觉与宿主能力边界明确） |
| A7 | 任务编排 | 接近/闭合/保持/释放的控制接口与状态机设计，后续引用 DexLab 案例 | [E2 已交付](control-robotics-tasks.md)（源码/静态） |
| A8 | 并行与学习接口 | CPU/GPU、批量隔离、reset/step、终止/截断、随机种子和官方学习接口 | [E5 已交付](batch-learning-data.md)（源码/静态；外部训练组件边界明确） |
| A9 | 数据与 sim-to-real | 状态/观测导出、时间戳、元数据、回放、随机化及模型差距 | [E5 已交付](batch-learning-data.md)（源码/静态；未开展 sim-to-real 实验） |
| B0 | 动力学与数据结构 | 配置空间、广义速度/力、惯量、约束、空间向量及内存布局 | [E1](modeling-state-time.md) 与 [E3](contact-solvers-forces.md) 核心已交付；[E6 特色材料/动力学已交付](extensions-boundaries.md)（源码/静态） |
| B1 | 一步仿真的源码 | 公开入口到执行分支、碰撞/装配/求解/积分/更新顺序 | [E3 核心已交付](contact-solvers-forces.md)（源码/静态） |
| B2 | 接触模型与组合律 | 几何表示、法向/摩擦律、材料组合、柔顺/正则化与量纲 | [E3 核心已交付](contact-solvers-forces.md)（源码/静态） |
| B3 | 求解器与线性代数 | 目标/方程、残差、迭代、线性求解、warm start、岛与终止条件 | [E3 核心已交付](contact-solvers-forces.md)（源码/静态） |
| B4 | 积分与数值语义 | 积分器/solver/子步的区别、精度、容差、稳定性假设及可微限制 | [E1](modeling-state-time.md) 与 [E3](contact-solvers-forces.md) 核心已交付；[E6 完整可微链与边界已交付](extensions-boundaries.md)（源码/静态） |
| B5 | 力与冲量观测 | 广义/空间/约束量、坐标转换、平均力、采样时刻与近似 | [E3 核心已交付](contact-solvers-forces.md)（源码/静态） |
| B6 | 性能、并行与扩展 | 编译/JIT/步进/拷贝/渲染边界、插件/回调、线程与扩展接口 | [E5 批量/数据核心已交付](batch-learning-data.md)；[E6 原生 solver/耦合扩展已交付](extensions-boundaries.md)（源码/静态） |
| B7 | 源码综合导读 | 从模型字段到控制/接触/求解/观测的完整追踪、限制及 DexLab 证据索引 | [E6 完整追踪已交付](extensions-boundaries.md)（源码/静态）；DexLab 原始证据索引与全路线审校留 E7 |

本引擎特别关注：ModelBuilder/Model/State/Control/Contacts、Warp、solver 支持矩阵和多 world。各课需提供先修、概念/公式、原生接口与固定源码、易错点、阅读练习和适用边界。实验不作为本阶段先决条件；后续复用 DexLab，避免重新建设一套评分和基准系统。
