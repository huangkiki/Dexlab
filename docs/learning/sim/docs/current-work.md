# 当前工作：Learning 迁移与 Solver 教程

[首页](../README.md) · [课程工作看板](https://github.com/users/huangkiki/projects/2) · [学习入口](solver-guide/README.md)

2026-10-14，维护者明确启动本轮 autodev。面向有 VLA、WAM、RL 经验的工程师与硕博，同时帮助读者理解配置、选择候选方案和诊断案例。总仓提供共同概念，各引擎仓保留原生实现，Robot Learning 负责学习流程。正文为中文，维护英文术语、摘要和导航。

最新学习顺序：按维护者要求，先沿 Chenfanfu Jiang、Minchen Li 等人合著的 [Physics-Based Simulation](physics-based-simulation.md) 学习物理仿真，再进入 Solver 配置和六引擎原生实现。教材是共同基础主线，专有 solver/模型差异仍由固定引擎源码补充；本轮交付伴读路线与自测，不把路线加入等同于整书翻译或运行完成。

## 当前范围与顺序

1. [八仓改名和引用迁移 #1](https://github.com/huangkiki/sim-learning/issues/1)：统一使用 Learning，保留原仓身份与历史证据，逐仓检查现行引用。
2. 先完成[教材伴读路线](physics-based-simulation.md)，再交付[两篇教学样章 #2](https://github.com/huangkiki/sim-learning/issues/2)：仿真一步、外层与内层求解。正文直觉和最小公式，进阶补充推导与固定源码。
3. [完整九单元与术语覆盖 #3](https://github.com/huangkiki/sim-learning/issues/3)：样章审校后已补齐九单元文字稿和全部登记术语索引；当前推进审校、PR 与跨仓集成，覆盖 DexLab 已登记版本和名称。
4. [单章 Galgame 原型 #4](https://github.com/huangkiki/sim-learning/issues/4)：先在一篇样章验证形式，再决定是否扩展。故事风格和交互能力两项仍待答，依赖它们的实现暂缓，其他工作继续。
5. [DexLab 双向衔接 #5](https://github.com/huangkiki/sim-learning/issues/5)与[总体验收 #6](https://github.com/huangkiki/sim-learning/issues/6)：修改展示生成源，核对真实入口及当前提交。

## 证据与暂停边界

本轮做来源核对、公式/配置审校、文档和示例静态检查；若开发剧情原型，另验收其显示和交互。没有新原生仿真、JIT、训练、性能基准或物理资格实验。案例复盘使用 DexLab 原报告与既有证据，不能写成新复现成功。

六引擎 E7 完整安装、全路线审校继续作为独立待办；Robot Learning 原生运行与训练也未因本轮改名恢复。旧阶段状态见[进度页](progress.md)。不启动后台调度或默认归档 Obsidian。

Project 管实际状态，Issue 管范围、依赖和验收，PR/提交证明交付。此页不复制任务状态历史，也不授予额外发布或合并权限。

## English summary

The maintainer resumed the Learning rename and solver-teaching work on 2026-10-14. The audience already works with VLA, WAM or RL. Chinese lessons combine configuration literacy and evidence-based diagnosis; English terminology, summaries and navigation remain available. Physics-Based Simulation now supplies the prerequisite study route. Two pilot lessons bridge it to the full nine-unit solver course. One lesson will receive a narrative teaching prototype after its remaining design choices are answered. Native engine execution, training, benchmarks and the six E7 tasks remain deferred.
