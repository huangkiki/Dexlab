# 读懂物理引擎、接触与 Solver

[Sim Learning 首页](../../README.md) · [共同基础](../foundations.md) · [当前开发范围](../current-work.md)

你可能已经在训练 VLA、研究 WAM 或用 RL 控制机器人，却仍会遇到这些问题：策略在仿真里成功能证明什么？物体滑落该先改摩擦、控制器还是 solver？为什么配置里同时有 Newton 和 GMRES？

这组课程从这些问题出发。读完应能把一条配置拆成物理模型、数学问题、求解方法和执行实现，提出可以用证据检验的诊断假设，并沿引擎原生课程继续。先掌握向量、矩阵、导数和机器人状态的基本含义即可；用到的物理与数值概念在相应章节解释。

## 先学物理仿真，再解读配置

先按[Physics-Based Simulation 伴读路线](../physics-based-simulation.md)读第 1–4 章，遇到线性系统问题穿插第 37 章；再沿第 5–11 章学习接触与摩擦。下面九单元是连接教材、机器人诊断和原生配置的教程，教材的 IPC/优化主线与每个引擎的具体问题分别核对。

## 建议顺序与实际范围

| 单元 | 你将学会什么 | 当前入口 |
|---|---|---|
| 1. 仿真一步 | 将动作、驱动力、接触、求解、积分与观测分开 | [完整样章](01-simulation-step.md) |
| 2. 接触如何产生响应 | 区分几何、接触模型、离散近似与参数 | [接触与响应](02-contact.md) |
| 3. 摩擦为什么不只是一个系数 | 理解摩擦锥、patch 与正则化 | [摩擦与正则化](03-friction.md) |
| 4. 约束问题怎样求解 | 解释 PGS、TGS、非线性 CG、Newton、SAP 的角色 | [约束求解](04-constraints.md) |
| 5. 外层与内层 | 解释 Newton/BFGS/SR1、线性 CG/GMRES/分解与 AUTO | [完整样章](05-nonlinear-and-linear.md) |
| 6. 时间与预算 | 区分步长、子步、迭代、容差和更新选项 | [时间与预算](06-time-and-budget.md) |
| 7. 刚体、布料与软体 | 区分动力学算法、变形体方法与耦合 | [对象与实现](07-representations.md) |
| 8. 后端、精度与身份 | 区分 CUDA/并行实现、FP64 和运行路径 | [后端与身份](08-backends-and-identity.md) |
| 9. 六引擎逐行解读 | 把全部登记名称对应到原生接口与证据 | [六引擎配置卡](09-engine-configurations.md) · [术语索引](term-index.md) |

完成教材第一轮伴读后，可先读 1 → 5 建立层级，再按 2 → 3 → 4 → 6 → 7 → 8 → 9 展开。九单元文字稿已齐；[术语索引](term-index.md)覆盖冻结词表全部 63 个 token 和表中五项身份/资格说明。当前 PR、跨仓集成和单章剧情原型仍有待办，见[验收范围](../learning-migration-acceptance.md)。已有深入课程可从[六引擎目录](../learning-paths.md)访问。

## 每章如何使用

每章包含一个实际问题、图解或纸面算例、最小公式、配置解读、诊断练习与答案，以及固定版本来源。进阶推导用折叠段落提供，便于先读主线。

练习有两条线：**配置理解**要求解释改变了哪个层次；**案例诊断**要求说明准备检查什么、该检查能排除什么，以及还不能得出什么结论。猜中引擎名字或完成剧情不等于完成物理验证。

目前仅做来源与静态检查。纸面数值是教学构造，引用的实验来自原报告；原生代码片段、重跑命令和模型加载若未执行会明确说明。真实复现与 E7 完整安装仍属后续范围。

## English reading guide

For engineers and graduate researchers familiar with VLA, WAM or RL, this course explains how to interpret simulation configurations and diagnose failures from evidence. Begin with the [Physics-Based Simulation study route](../physics-based-simulation.md#english-reading-guide), then read [a simulation step](01-simulation-step.md), then [outer nonlinear and inner linear solving](05-nonlinear-and-linear.md). All nine text lessons and a complete frozen-term index are present in this branch; publication, cross-repository integration and the narrative prototype have separate remaining acceptance. Full lessons are Chinese, with English terminology and summaries. Source review and static checks do not establish native execution or physical qualification.
