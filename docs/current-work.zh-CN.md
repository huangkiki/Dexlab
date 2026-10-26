# 当前工作与执行状态

[English](current-work.md) | [简体中文](current-work.zh-CN.md)

**决策日期：2026-10-26。维护者已授权按下面顺序交互式推进 autodev；定时开发保持 PAUSED。** 本页是 AGENTS 和操作指南引用的唯一当前排序入口。持续推进具备条件的切片，完成验收与交付。新物理实验仍须先冻结协议和有限资源预算；不启动训练或后台派发。

## 本轮要交付什么

以 **Wuji 手的抓持、卸载和接触切换** 为主线，得到一个别人能重跑、能检查失败原因的起步案例。先证明抓持正例与负例成立，再研究切换时的失效。没有找到 solver failure 也是可报告结果；任务失败、接近/控制失败、几何问题和求解器不收敛分别归因。

[已发布复盘](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-failure-audit.html)没有证明合格的 Wuji 手内 solver failure：RSS 擦拭说明固定配置对辅助保持的依赖；Proxy 布料先在 acquisition 阶段失败。新计划据此补充判别条件，不预设统一多物理系统就是答案。[Discussion #222](https://github.com/huangkiki/Dexlab/discussions/222)的接触要求与反馈分离，以及 [#189](https://github.com/huangkiki/Dexlab/discussions/189)的任务起步入口，在下面的一个具体案例中落实；[首个原生 Wuji 案例](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)现已在合成抗扭接触下通过六项开发对照，明确保留两秒保持窗口和缓慢漂移的限制；尚未测量用户上手时间的改善。

## 执行顺序与验收出口

| 顺序 | 现有/新任务 | 完成时应该能证明什么 |
| --- | --- | --- |
| 1 | [输出记录隔离 #243](https://github.com/huangkiki/Dexlab/issues/243) | 重复启动、中断和 reset 不覆盖旧产物，不把新 manifest 与旧成功摘要混在一起；完整回归通过。 |
| 2 | [安装环境保护 #245](https://github.com/huangkiki/Dexlab/issues/245)；自动派发前解决 [作者准入与暂停 #244](https://github.com/huangkiki/Dexlab/issues/244) | wheel/source 安装入口在副作用前拒绝不兼容环境；新派发遵守受信作者、依赖和唯一暂停依据。#244 不阻塞已授权的独立交互式工作。 |
| 3 | [公开复算包 #250](https://github.com/huangkiki/Dexlab/issues/250) | 从可下载资产离线重建一组既有 latch/no-latch 结果和曲线；原始观测、失败索引、许可与 hash 可核验。完整 RSS raw 的缺口仍归 #247。 |
| 4 | [Wuji 抓持资格 #251](https://github.com/huangkiki/Dexlab/issues/251) | 固定手腕的简单物体正例成立，保持/卸载/释放指令产生可检查的实际接触效果，负例能被拒绝；正例不成立就停在该层诊断。复用输出入口先依赖 #243。 |
| 5 | [Wuji 手内操作父项 #48](https://github.com/huangkiki/Dexlab/issues/48) | 在合格抓持上完成受控接触切换与有符号旋转，排除手掌旋转、摇摆累计、隐藏支撑和状态注入；冻结后验证 10 个新条件。 |

这是一条交付顺序，不把所有前项设为技术硬依赖。#250 可独立利用现有记录；#251 的静态准备可先做。原生实验前，须在对应 Issue 冻结配置、指标依据、完整适用矩阵、具体案例与测得的有限资源预算。#251 的事前冻结批次、实际结果和累计预算保存在对应 Issue 与证据包中。没有新增云算力、训练、引擎源码修改或硬件动作。

## 本次整理与保留范围

复盘起点为 36 个开放 Issue、1 个草稿 PR，并核对相关源码、合并证据及 Discussion #189/#220/#222；这是任务和证据审计，没有重新运行全部历史实验。

- [#246](https://github.com/huangkiki/Dexlab/issues/246)跟踪本次实际状态修复：已交付的 #177/#183/#184 不再排在待办首位；#174 的依赖语法修正；#6 明确当前无真机；#223 不再重复派发。验收、合并、部署和回读之后才关闭 #246。
- [#223](https://github.com/huangkiki/Dexlab/issues/223)八项擦拭复现已由 PR #225 交付。跨批次数值解释的未完成义务转到 [#247](https://github.com/huangkiki/Dexlab/issues/247)，原 cohort、指标与恢复条件全部保留；关闭复现项不代表差异已解释。#247 的 18 个论文场景输入、Proxy 归因和未公开 raw 仍开放。
- LIBERO [#181](https://github.com/huangkiki/Dexlab/issues/181)保留全部 **130 项原生任务及全部官方示范**，#185/#188/#174/#198 与视觉策略 #182 后移。#198 的公开解释缺口仍为 P0；#185 的下载失败和累计额度保持真实阻塞。部分 Object/Spatial 结果不关闭父项，不恢复下载或权重获取。
- SDF #178/#211、布料 #28/#179、六引擎斜面 #121 及 #157/#159/#163/#165、夹持 #130/#132/#133/#134、UniSim #142/#145、ManiSkill #47、数据审计 #52 和物性基准 #3 保留原验收与候选代码。本轮后移到 P2；无实际执行者的旧 In Progress 回到 Todo，真实外部/依赖阻塞仍为 Blocked。#28 与 #179 是父子关系，不作重复关闭。594+24 回合范围与累计预算不变。
- [#249](https://github.com/huangkiki/Dexlab/issues/249)限定先做 Newton SolverMuJoCo 与 direct MuJoCo Warp 的身份/封装对照，列 P2；#152 的 Isaac Sim 路径与其他任务范围仍独立保留。libuipc #218 为候选评估。#200 缺原作者同条件切割输入，保留 P0/needs-input；硬件 #6 保留 Blocked，纯数值工作不依赖它。
- 草稿 [PR #199](https://github.com/huangkiki/Dexlab/pull/199)仍需解决与 main 的冲突、当前树完整文档门禁及链接核验。保留原 PR 和已有工作树；旧 CI 通过不代表当前可合并，本轮不重复新建阅读路线 PR。

本轮计划项不授予自动派发。旧 `auto:approved` 已按排期清除；这不撤回会话中的交互式授权。**runner 的持久派发状态缺失或损坏时默认暂停；只有显式 resume 才能放行新自动任务。** 具体命令与交互式继续规则见[操作指南](autoresearch.zh-CN.md#作者准入与持久暂停)。 恢复自动执行前必须通过受信作者检查、暂停/依赖验证和实际 `next --dry-run`；不可仅凭本页派发。

## 恢复与交付入口

[Project 4](https://github.com/users/huangkiki/projects/4)管实时队列，Issue 管范围、依赖、协议、预算、验收和阻塞，PR/冻结记录证明结果。保留 [UniSim #142](https://github.com/huangkiki/Dexlab/issues/142)的所有权边界：实验直接使用已合格原生参考时披露路径；新增生产适配缺口由 UniSim 承担，不为本轮搭新框架。

沿用[操作指南](autoresearch.zh-CN.md)和 [AGENTS](../AGENTS.zh-CN.md)的单执行者、不可覆盖证据、显式 runtime profile、资源与完整适用门禁。小切片按既有授权完成审查、精确 head 合并、部署/附件回读；完整验收后才关闭，不停在 PR 创建。

上一轮优先级保存在 [2026-10-21 main 快照](https://github.com/huangkiki/Dexlab/blob/af788be6be4a265edb1ec1b95671e11f05d1d1d2/docs/current-work.zh-CN.md)。更早规则见 [AGENTS 历史快照](https://github.com/huangkiki/Dexlab/blob/e3561c8def027f777df25ad41e67a2aea3b21144/AGENTS.md)与[操作历史](autoresearch-2026-10-10.md)。历史排序不是当前启动指令；科学验收与数据保留义务继续有效。
