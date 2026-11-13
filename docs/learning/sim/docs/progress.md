# 课程交付进度

[返回学习首页](../README.md) · [完整学习路线](learning-paths.md) · [开发看板](https://github.com/users/huangkiki/projects/2/views/2)

2026-10-14 更新：Learning 改名、[Physics-Based Simulation 先修路线](physics-based-simulation.md)与 [Solver 教程](solver-guide/README.md)已启动，详见[当前工作](current-work.md)。下表保留原 E0–E7 交付范围，E7 继续暂停；新增课程按实际 PR/提交单独验收。

课程以两条阅读路线组织；下列 E 编号用于开发和交付跟踪。路线目录已经规划完整，章节完成情况按实际发布内容核实。

| 阶段 | 交付内容 | 当前覆盖 |
|---|---|---|
| E0 | 导读、双路线目录、固定源码地图 | 六仓已发布 |
| E1–E2 | 建模、状态与时间；驱动、机器人和任务接口 | 六仓已发布 |
| E3–E4 | 接触、求解器、积分与力观测；传感器与渲染 | 六仓已发布 |
| E5 | 批量、学习接口与数据 | 六仓已发布 |
| E6 | 引擎特色、扩展、多物理与可微边界 | 六仓已发布 |
| E7 | A0 完整安装、两条路线逐单元审校与 DexLab 案例衔接 | 六仓待完成；暂停，未启动 |

**历史暂停记录（2026-10-09）：**按维护者要求完成本批 E6 后暂停开发。48 个任务中 42 项 Done、6 项 Todo、0 项 In Progress。E7 保留待办，不自动领取新任务。恢复时先核对各仓 main、未提交修改、Issue/PR 与 E2–E6 依赖；本记录不把未完成课程标为完成。

特色扩展的已发布入口见[共同基础第 8 节](foundations.md)。各引擎课程目录维护具体单元的完成范围，不能把一个开发阶段替代整条路线的验收。

本阶段交付原生接口讲解、固定源码追踪、练习答案和静态检查过的例子。例子没有因语法检查通过而成为已运行案例；没有新仿真实验、训练或性能基准。未来实验复用 [DexLab](dexlab.md) 的协议、版本和证据。

## Delivery progress

[English home](../README.en.md) · [Project tracker](https://github.com/users/huangkiki/projects/2)

The E codes track development slices; A0–A9 and B0–B7 organize reading. All six repositories have published E0–E6. At the 2026-10-09 pause, 42 tasks were Done, 6 were Todo and none were In Progress. The Learning migration, prerequisite book route and solver teaching work resumed separately on 2026-10-14; see [current scope](current-work.md). E7, including full installation lessons and integrated unit-by-unit review, remains incomplete and has not started. E7 will not be picked up until explicitly resumed; check current branches, local changes, issues/PRs and the actual E2–E6 dependencies.

Published scope means reviewed lessons, pinned source references, answered exercises and static checks. Native examples remain unexecuted unless explicitly recorded otherwise. No new experiments, training or benchmarks are part of this phase; experimental material will reuse DexLab.
