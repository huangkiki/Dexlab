# Newton Physics autodev 路线

一个阶段对应一个可恢复的 GitHub Issue；总看板统一管理六仓，仓库保留本引擎的原生设计。先查同题 Issue/PR 和实际合入状态，再继续工作。

| 阶段 | 交付切片 | 依赖 | 状态 |
|---|---|---|---|
| E0 | 双路线导航与固定版本源码导读 | 无 | 首批导读已交付 |
| E1 | 建模、坐标、状态与时间专题 | E0 | [专题已实现](modeling-state-time.md)，[源码/静态验收](e1-validation.md) |
| E2 | 驱动、机器人与任务接口专题 | E1 | [专题已实现](control-robotics-tasks.md)，[源码/静态验收](e2-validation.md) |
| E3 | 接触、求解器与力观测源码专题 | E1 | [专题已实现](contact-solvers-forces.md)，[源码/静态验收](e3-validation.md) |
| E4 | 传感器、渲染与可视化专题 | E1 | [专题已实现](sensors-rendering.md)，[源码/静态验收](e4-validation.md) |
| E5 | 批量、学习接口与数据专题 | E2、E4 | [专题已实现](batch-learning-data.md)，[源码/静态验收](e5-validation.md) |
| E6 | 引擎特色、扩展与能力边界专题 | E3 | [专题已实现](extensions-boundaries.md)，[源码/静态验收](e6-validation.md) |
| E7 | 双路线课程审校与 DexLab 复用入口 | E2–E6 | 待开发 |

E0 交付的是导读与导航，不是所有专题。E1–E6 逐个展开目录中的知识点，E7 按完整课程契约审校。依赖必须以实际文档或合入提交核实，不能仅凭 Issue 关闭。

每个 Issue 记录目标、范围、先修、固定版本/来源、交付文件、易错点、验收命令和剩余问题。本轮验收为文档链接、源码/公式核对及最小片段的语法检查；明确区分未运行、源码核对和运行验收。无新实验、训练、性能基准、跨引擎框架或评分器。

有可执行任务时按依赖推进；阻塞时记录原因和恢复条件。没有用户要求不创建定时任务。研究数据与实验最终引用 DexLab。

## E1 后的任务复审

A1/A2 的内容与源码验收已经具备；B0/B4 的剩余约束/求解/数值专题仍由 E3 承接。合入后优先 E2：利用本章已经明确的 q/qd、Control 布局和权威状态讨论驱动、FK/目标 IK 与任务时序；E3、E4 也满足 E1 依赖，但尚未实现。E5 等待 E2/E4，E6 等待 E3，E7 等待全部专题；不以本章取代这些任务。外部交付/合入状态以 [Issue #2](https://github.com/huangkiki/newton-atlas/issues/2) 和实际提交为准。

## E2 后的任务复审

E2 已展开 A3/A5/A7，控制输入、模型约束与任务观测仍保持分层。下一项优先 E3：补齐本章 solver 差异背后的接触/约束/积分计算，以及任务状态机未来需要的力与冲量观测；E4 也可独立推进。E5 虽已具备 E2，但仍等待 E4；E6 等待 E3，E7 等待 E2–E6。E1 正文与示例保留原交付内容，其验收记录是当时提交的快照；本次新增来源与检查在 E2 记录中单列。外部交付以 [Issue #3](https://github.com/huangkiki/newton-atlas/issues/3) 和实际合入提交为准。

## E3 后的任务复审

E3 已展开 A4/B1–B5 与 B0 的核心动力学装配链；XPBD 的权重/恢复读回限制、固定 MuJoCo-Warp 的 torque 参考点缺口均保留在课程和验收中。静态身份与语法通过不构成物理运行验收。后续优先 E4，以满足 E5 的剩余依赖；E6 已具备 E3 前置，承接专用材料、DVI 深层求解、耦合/扩展与可微实现细节。E7 仍等待 E4–E6；不把 SensorContact 的线性力消费说明当作 A6 全面交付。发布状态以 [Issue #4](https://github.com/huangkiki/newton-atlas/issues/4) 与实际合入提交为准。

## E4 后的任务复审

E4 已展开 A6 的四种公开 sensor、射线查询、七类相机通道和 viewer/宿主边界，保留 qdd producer/采样阶段、默认 miss 值、空场景不写输出及 BVH 共享等限制。没有 native import、渲染、物理执行或视觉 QA。E5 已具备 E2/E4 前置，下一项可推进批量与学习/数据接口；E6 仍承接特色扩展，E7 等待 E5/E6。E1–E3 验收是历史交付快照，当前来源清单与检查以 E4 为准。发布状态以 [Issue #5](https://github.com/huangkiki/newton-atlas/issues/5) 及实际合入提交为准。

## E5 后的任务复审

E5 已展开 A8/A9 与 B6 的批量/内存/graph/数据核心，保留 solver reset 差异、官方 policy 示例时钟差异、CPU graph 实验性和 ViewerFile 非完整 checkpoint 的限制。Warp 1.18.0 另列固定官方源码身份，不代表安装或组合运行验收。未执行原生导入、JIT、物理、渲染或训练。E6 已具备 E3 前置，下一项承接专用 solver、耦合、扩展及完整可微实现；E7 等待 E6 后进行全课审校。旧验收保持其交付时快照，本次检查见 E5。发布状态以 [Issue #6](https://github.com/huangkiki/newton-atlas/issues/6) 与实际合入提交为准。

## E6 后的任务复审

E6 已展开 B0/B4 的特色材料与可微边界、B6 原生 solver/耦合扩展和 B7 完整字段到观测的源码追踪。VBD/SemiImplicit 材料差异、Style3D 输入原地修改、MPM 隔离/历史、Proxy/ADMM ownership 与被跳过/拒绝的约束均按固定实现保留。阻力梯度例子只有 AST/API 源审，没有原生运行。Warp Tape 两个来源独立记录，不冒充已安装版本。E7 仍待开展 A0 完整安装专题、双路线总审校和 DexLab 原始版本/工况证据索引；本任务没有启动 E7。既有验收保持历史快照，本次检查见 E6。发布状态以 [Issue #7](https://github.com/huangkiki/newton-atlas/issues/7) 与实际合入提交为准。
