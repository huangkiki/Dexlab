# 当前工作与执行状态

[English](current-work.md) | [简体中文](current-work.zh-CN.md)

**决策日期：2026-10-12。当前交互式开发已获授权，定时开发继续 PAUSED。** 本页是 AGENTS 与操作指南引用的唯一当前顺序入口。阅读本页、克隆仓库或创建 Issue，不会启动 worker、恢复调度或授予凭据。

## 当前范围与顺序

1. 先恢复已有执行者、工作树和 PR。处理可执行的 P0 记录一致性与交付缺口，再完成[分类 #177 / PR #180](https://github.com/huangkiki/Dexlab/pull/180)。[#183 / PR #186](https://github.com/huangkiki/Dexlab/pull/186) 已交付 LIBERO 接触汇总一致性修复；[#184 / PR #187](https://github.com/huangkiki/Dexlab/pull/187) 已交付现有 PR 分支恢复能力。各项仍按自己的完整条件验收。
2. [LIBERO #181](https://github.com/huangkiki/Dexlab/issues/181) 负责**官方全部 130 项原生任务及全部预期示范**：Object 10、Spatial 10、Goal 10、LIBERO-10 10、LIBERO-90 90。先完成[输入与全部示范清单 #185](https://github.com/huangkiki/Dexlab/issues/185)、任务感知执行器，以及多目标、关节和长序列记录评分资格，再按上述顺序完成有界批次。静态清单、代表性资格或 40 项子集不能关闭全量父项。
3. 基础资格阶段即开展[视觉策略评测 #182](https://github.com/huangkiki/Dexlab/issues/182)，不等待全部原生基线。冻结评测问题和参考，先准入一个公开 checkpoint，正式兼容矩阵目标为 2–3 个；完成受控配对干预、独立参考、冻结修正、留出验证和复现报告。原生回放、重评分和策略闭环分别计数，分别说明结论边界。
4. [SDF #178](https://github.com/huangkiki/Dexlab/issues/178) 与[布料 #179](https://github.com/huangkiki/Dexlab/issues/179) 从既有数据的参数和来源审计开始，依次验证几何或材料响应、接触耦合和完整任务。它们约束使用相应机制的结论，不为无关的基础几何任务新增依赖。保留已声明的有限预算；从短探针扩展到完整任务前，明确用例与预算。
5. 先修复会使下一批无效的问题，再继续该批。候选冻结后独立验证，回归受影响任务，公布完整失败、成本与来源报告。缺失或无效证据仍未完成；记录完整的否定结果可以完成其声明的研究用例。不强求正效果，不悄悄缩减 130 项范围。

## 不变量与保留工作

保持单执行者、既有实测资源准入、不可改写的失败和累计预算，保全脏工作树。[操作指南](autoresearch.zh-CN.md)与 [AGENTS](../AGENTS.zh-CN.md) 保留依赖核实、隔离环境、完整适用门禁、当前 head 审查和授权交付。优先级不能越过准入。交互式授权不恢复定时调度，也不授权修改引擎源码、训练、付费资源或真机运动。

官方兼容的 LIBERO/robosuite 路径与最新稳定原生引擎分别准入。130 项参考路径是原生 LIBERO，不是已经准入的六引擎 LIBERO 矩阵。记录一致性和数值诊断不能证明真实材料准确性或 sim-to-real 表现；已暴露样例不能重新称为新留出。

保留 #157/#159/#163/#165 的观测问题、#152/#145 的框架与惯量工作、#121 六引擎范围、已采纳的 [UniSim 收敛 #142](https://github.com/huangkiki/Dexlab/issues/142)，以及 #130–#134 原有 594 回合夹持范围与依赖。它们若成为当前验收的真实阻塞则提升顺序，否则保留后续执行。#47/#48/#52/#28/#3 与硬件 #6 各有原范围，局部参考证据不能关闭父项。[PR #176](https://github.com/huangkiki/Dexlab/pull/176) 仍是参考审查。

## 状态与决策历史

[Project 4](https://github.com/users/huangkiki/projects/4) 管理队列，关联 Issue 管理协议、依赖、预算与验收，PR 和冻结记录证明实际完成状态。本页不复制实时状态表，也不向 AGENTS 追加竞争的当前顺序；改变优先级时同步两种语言。

[不可变 AGENTS 快照](https://github.com/huangkiki/Dexlab/blob/e3561c8def027f777df25ad41e67a2aea3b21144/AGENTS.md)和[保留的操作快照](autoresearch-2026-10-10.zh-CN.md)保存早期决定与复现流程。其中带日期的当前顺序与 heartbeat 表述属于历史，不是恢复指令。当前顺序和暂停状态以上文为准，更严格的证据、资源与合并约束继续有效。
