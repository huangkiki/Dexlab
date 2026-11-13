# Drake 两条学习路线

[首篇导读](guide.md)已经建立对象关系和核心入口；它不代表下面全部专题已经完成。[源码地图](source-map.md)提供固定提交入口。

应用路线无需先学求解器源码；原理路线建议先理解 A0–A4，并具备线性代数和基础动力学知识。两条路线都完整规划，当前以讲解、源码与最小 API 片段为交付物。

| 单元 | 主题 | 必须讲清的内容 | 状态 |
|---|---|---|---|
| A0 | 安装与对象地图 | 支持环境、包/核心/宿主身份、构建入口、核心对象及生命周期 | 专题待开发 |
| A1 | 模型、坐标与资产 | 单位、坐标、姿态、惯量、碰撞/视觉、导入器、资产许可 | [E1 已交付](modeling-state-time.md)，未运行 |
| A2 | 状态与时间 | 配置/速度维度、时间步/子步、reset、快照、所有权、采样阶段 | [E1 已交付](state-time.md)，未运行 |
| A3 | 驱动与控制 | 状态设置与控制命令、驱动器、饱和、PD、回调与控制频率 | [E2 已交付](control-robotics.md)，未运行 |
| A4 | 接触 API | 碰撞过滤、接触观测、摩擦/恢复/柔顺参数的原生语义 | [E3 已交付](contact-models.md)，未运行 |
| A5 | 机器人与运动学 | 模型导入、关节映射、FK/IK、限位、约束、外部控制集成 | [E2 已交付](control-robotics.md)，未运行 |
| A6 | 传感器与渲染 | RGB/depth/分割/射线/力/触觉、坐标/单位/更新阶段、GUI/headless | [E4 已交付](sensors-rendering.md)，含[时间](sensor-timing.md)和[惯性/力](inertial-force-sensing.md)；未运行 |
| A7 | 任务编排 | 接近/闭合/保持/释放的控制接口与状态机设计，后续引用 DexLab 案例 | [E2 已交付](task-interfaces.md)；实验案例后续复用 DexLab |
| A8 | 并行与学习接口 | CPU/GPU、批量隔离、reset/step、终止/截断、随机种子和官方学习接口 | [E5 生命周期](batch-lifecycle.md)及[随机化/学习](randomness-learning.md)，未运行 |
| A9 | 数据与 sim-to-real | 状态/观测导出、时间戳、元数据、回放、随机化及模型差距 | [E5 数据/回放](data-replay.md)与[随机化](randomness-learning.md)，未运行 |
| B0 | 动力学与数据结构 | 配置空间、广义速度/力、惯量、约束、空间向量及内存布局 | [E1 基础](modeling-state-time.md) + [E3 动力学装配](contact-solvers.md)，未运行 |
| B1 | 一步仿真的源码 | 公开入口到执行分支、碰撞/装配/求解/积分/更新顺序 | [E3 已交付](contact-solvers.md)，未运行 |
| B2 | 接触模型与组合律 | 几何表示、法向/摩擦律、材料组合、柔顺/正则化与量纲 | [E3 已交付](contact-models.md)，未运行 |
| B3 | 求解器与线性代数 | 目标/方程、残差、迭代、线性求解、warm start、岛与终止条件 | [E3 已交付](contact-solvers.md)，未运行 |
| B4 | 积分与数值语义 | 积分器/solver/子步的区别、精度、容差、稳定性假设及可微限制 | [E1 时间](state-time.md) + [E3 数值与可微边界](contact-solvers.md)，未运行 |
| B5 | 力与冲量观测 | 广义/空间/约束量、坐标转换、平均力、采样时刻与近似 | [E3 已交付](contact-observation.md)，未运行 |
| B6 | 性能、并行与扩展 | 编译/JIT/步进/拷贝/渲染边界、插件/回调、线程与扩展接口 | [E5 系统层合同](batch-lifecycle.md) + [E6 原生扩展](systems-extensions.md)与[标量边界](scalar-capabilities.md)，未运行 |
| B7 | 源码综合导读 | 从模型字段到控制/接触/求解/观测的完整追踪、限制及 DexLab 证据索引 | [E6 综合源码链](engine-boundaries.md)已交付；E7 审校及 DexLab 复用入口待完成 |

本引擎特别关注：Systems/Diagram/Context、MultibodyPlant、SceneGraph、SAP、控制与优化。各课需提供先修、概念/公式、原生接口与固定源码、易错点、阅读练习和适用边界。实验不作为本阶段先决条件；后续复用 DexLab，避免重新建设一套评分和基准系统。

E1 的“已交付”指源码教学及静态验证，不代表原生运行；证据见[验收记录](evidence/e1-validation.md)。E1 的 B0/B4 仅是基础，现由 E3 补充动力学装配、接触离散、求解与数值边界。

E2 完成原生控制、运动学/IK 与任务事件接口讲解；三个示例只做静态验证，未执行控制、优化或任务。接触/传感的实际观测语义分别由 E3/E4 深入，DexLab 案例整合留在 E7。[E2 证据](evidence/e2-validation.md)。

E3 已交付 A4、B1–B5 及 B0 装配基础，包含 22 道练习与原生配置/读回例子。实际物理、梯度与实验验收没有开展；原生传感器的采样、图像与理想惯性模型现由 E4 展开。[E3 证据](evidence/e3-validation.md)。

E4 完成 A6：RGB-D/label/点云、QueryObject 与 renderer、三种相机时间模型、Meshcat/headless、Accelerometer/Gyroscope/RotaryEncoders，以及力/触觉边界，含 21 道有答案练习。射线与触觉明确说明当前原生链提供什么、缺少哪些硬件模型；没有用历史 API、消息类型或压力截图代替实现。示例只做静态检查。[E4 证据](evidence/e4-validation.md)。

E5 完成 A8/A9 与 B6 系统层讲解，包含 21 道有答案练习和独立 Context/日志的原生阅读例子。固定 Python MonteCarlo 串行、Gym handler/reset/render 差异、vector Eval 副本、日志 cache 与采样时间逐项对照实现；没有将源码能力变为 GPU 物理、训练吞吐或 sim-to-real 验收。[E5 证据](evidence/e5-validation.md)。

E6 完成 B6 具体扩展与 B7 综合源码追踪：原生 LeafSystem/TemplateSystem、依赖与标量转换、几何/SAP/FEM 的 AD/symbolic 边界、优化前置条件及原生力模型。三篇含 21 道有答案练习；原创一阶滞后例子只做 AST 与绑定核对。MPM 内部目录不当作公开仿真入口；非空柔性模型不当作可微 Plant。[E6 证据](evidence/e6-validation.md)。E7 尚需对双路线全文审校并整理 DexLab 入口，A0 安装/环境专题的剩余范围也须明确收口。
