# 当前工作与执行状态

[English](current-work.md) | [简体中文](current-work.zh-CN.md)

**更新：2026-11-11。当前采用“问题 → 评分语义 → 对照 → 归因 → 结论”的开发流程；定时开发保持 PAUSED。** 本页是研究选择与恢复的唯一当前入口。本次更新采纳设计顺序，不启动训练或物理实验，不修改队列标签、已有协议、科学阈值或执行权限。[完整流程](autoresearch.zh-CN.md#research-loop)

## 从已有结论出发

Wuji 合成抗扭接触使两秒保持最大位移由 2.734 mm 降到 1.025 mm，但尚无合格 solver failure 或真机标定；RSS 对照说明辅助保持会决定任务成败；接触响应基线降低位移误差却仍漏报接触丢失。[结论与证据](../README.md#findings)因此决定下一轮先查“测对没有、失败在哪”，再选择扩展。

## 恢复与设计顺序

| 方向 | 已有入口与当前证据 | 下一步及出口 |
| --- | --- | --- |
| **先恢复在手候选** | CHORD 准备切片 [#283 / PR #284](https://github.com/huangkiki/Dexlab/pull/284) 已合并。[PR #292](https://github.com/huangkiki/Dexlab/pull/292) 于本次核查仍为草稿，公开记录报告有限训练／checkpoint 重载，但 off/on 和 off/off 一致性失败；完整迁移仍为 0/3。 | 在 [#285](https://github.com/huangkiki/Dexlab/issues/285) 恢复原句柄、记录和累计预算，先定位重复性与记录问题；不能从 off/on 差异单独断言记录器有因果影响。取得合格记录后再独立评分，沿用原交付门禁。 |
| **首选的新设计：评分语义审计** | [Discussion #302](https://github.com/huangkiki/Dexlab/discussions/302) 建议先用已有 Wuji 证据；该审计尚未实现或执行。 | 先列出必要事件与任务意图，再设计区域／容差、事件顺序、idle、隐藏支撑与状态注入反例，说明各项应由哪一层识别。先修语义误判或缺失观测，再解释实验收益。 |
| **条件性后续：短连续接触序列** | 现有单回合通过不证明跨 job 状态继承可靠；reset／不 reset 对照仍是提案。 | 评分语义明确后，围绕保持、卸载／重建、释放设计最短序列；冻结 job 边界、carry state 与 run 级统计。正例不稳、负例误通过或没有可解释差异时停止扩展；不改变 [#48](https://github.com/huangkiki/Dexlab/issues/48) 的原验收。 |
| **有兼容输入才推进：学习与动作响应** | [#261](https://github.com/huangkiki/Dexlab/issues/261) 的离线基线已交付，原生动作干预与兼容模型仍缺；CHORD 父项 [#282](https://github.com/huangkiki/Dexlab/issues/282) 保留三个原生任务。 | 依 [#281](https://github.com/huangkiki/Dexlab/discussions/281)、[#293](https://github.com/huangkiki/Dexlab/discussions/293)，先固定策略比较动作／物理变化。物理调整有独立依据后才考虑重训及交叉评估，分别报告任务与物理收益。 |

这是恢复优先与研究设计顺序，不是一条串行硬依赖链。评分审计可以利用现有证据独立准备；CHORD 恢复不等待新序列。新设计未建立执行任务或预算，Discussion 也不授予启动权限。后续原生实验仍按原规则冻结完整适用矩阵、具体案例、协议和有限资源计划，不以最小案例为由缩小既有验收范围。

## 保留的范围与阻塞

- **Wuji #48：** 接收指／滚动路线与新切换协议仍待决定；合格抓持之后的有符号旋转、无隐藏支撑与十个新条件等原义务保留。连续序列不代替手内操作验收。
- **CHORD #282：** 先纸巾盒、后两项 ARCTIC；合法数据／许可与运行条件继续约束后两项。有限训练成功不等于独立任务成功，未合并候选不计入主线成果。
- **已有失败与证据缺口：** AMP #259 的记录一致性、RSS #247 的来源／raw 缺口、LIBERO #181 的完整范围及 #198 的公开解释、切割 #200 的同条件输入、硬件 #6 的实测缺失继续保留。缺真机不阻塞有独立依据的数值分析。
- **已交付工程基础：** 输出隔离 #243、安装保护 #245、作者准入／暂停 #244、离线包 #250、Wuji 抓持 #251、SDF 工程 #211 已交付；不重新排作待办。SDF 原生研究、布料、适用引擎矩阵及 UniSim 迁移的父项义务不因此关闭。
- **暂缓扩展：** 生成式资产／世界、七任务工厂、全引擎可微接口和扩大任务库。浏览器抓娃娃保留为 toy 展示，不能替代主线研究结果或自动进入 README 里程碑。

各项详细验收、历史优先级与累计范围保存在 [11 月 3 日主线快照](https://github.com/huangkiki/Dexlab/blob/4c3dafc1cd96b90c09a36f0c178c6eeab9bd015b/docs/current-work.zh-CN.md)及各自 Issue。快照用于追溯，旧排序不是新派发指令；本次不关闭任务、不变更它们的范围或状态。

## 执行与交付入口

[Project 4](https://github.com/users/huangkiki/projects/4)与 Issue 保存实时执行范围、依赖、预算和阻塞；恢复时读回真实状态。沿用 [UniSim #142](https://github.com/huangkiki/Dexlab/issues/142) 的所有权边界：DexLab 管实验、记录和独立评分，生产适配缺口由 UniSim 承担，已合格原生参考保留。

遵守[操作指南](autoresearch.zh-CN.md)与 [AGENTS](../AGENTS.zh-CN.md)：单执行者，保留未提交工作、失败与累计预算；机器派发状态缺失或损坏时默认暂停。`next --dry-run` 只检查候选，不恢复定时器。优先级、讨论或文档计划不能绕过作者、依赖、资源与授权检查。

每次交付更新相应报告中的结论、适用范围和下一步；README 只保留能改变读者判断的发现与关键节点。沿用已授权的精确 head 审查、适用门禁、合并及部署读回；部分交付不关闭父项。Obsidian 提交／推送仍暂停。
