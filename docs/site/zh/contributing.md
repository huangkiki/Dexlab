# 添加实验与维护报告

```{toctree}
:maxdepth: 1
:caption: 本栏目录

高质量轨迹回放 <studio-rendering>
```

## 从问题到实验

开发从一个能改变判断的问题开始：**问题 → 评分语义审计 → 最小对照 → 失败归因 → 结论**。先复用已有记录，验证正例、反例和必要观测，再决定是否运行新实验。Discussion #302 的首选是评分语义审计，短连续接触序列仍待设计；CHORD 与模型工作先解决重复性和动作响应证据。

[完整研究流程](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md#research-loop) · [当前选择与恢复入口](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.zh-CN.md)

## 一项实验的交付

1. 在 Issue 写清假设、官方版本、参数来源、近似、预算、对照和验收。
2. 代码、配置与运行入口放入对应 `demos/` 实验目录；共享评分留在 `src/dexlab/`。
3. 保存实际初态、动作、轨迹、接触和所有结局。评分器独立于控制器，失败不能删。
4. 更新本站的实验卡与报告：结论、设置、指标图表、失败、局限和复现入口，中英同步。
5. PR 中说明读者入口的变化。新能力、实验结论、重要失败与复现变化先更新网站对应页面；改变项目定位、架构、代表性预览、推荐起点或交付重要里程碑时，同步 README。

## README 与文档站的分工

README 按“用途 → 结论及适用条件 → 代表性实验 → 关键研究节点 → 推荐起点”组织。结论应说明它改变了什么开发选择，就近链接证据与限制；架构与完整研究细节放网站。研究节点从已合并提交中挑选：能带来新结论、可复算证据或必要研究入口才收录，准备工作明确标为准备。抓娃娃等 toy、界面润色和逐次提交留在演示页与历史记录，不列为研究进展。

| 内容 | 维护位置 |
| --- | --- |
| 项目用途、主要结论与条件、关键研究节点、代表性预览和最短上手命令 | 中英文 README；结论和预览链接到证据，准备项不写成已完成实验。 |
| 按读者目标找页面 | 网站首页“从这里开始”、导航与目录。 |
| 完整方法、参数、结果、失败与复现 | 对应实验或使用页面；实验目录提供入口。 |
| 外部论文 | 参考目录、分类导读与完整书目；注明来源、核查日期和阅读深度。 |
| 计划、阻塞与逐次进展 | Current Work、Issue、PR 和 Releases。 |

Newton 导读正文维护在 `docs/references/newton-reading-guide*.md`，书目在 `newton-publications*.md`；网站语言页面直接包含这些正文。更新上游快照时核对完整书目、七类导读的条目集合和中英对应关系，保留“仅作对照”的标记；摘要核对不能写成全文评审或复现。

发布前同时检查来源页、网站导航、语言切换和 README 入口。合并后确认线上版本与页面内容。代码保持可运行，文档不复制私有服务器路径或实验账号。

每张图给出版本、单位、样本量、窗口、区间定义及来源。对比图同时保留失败；不要把不同标定、几何或调参预算的结果称为公平引擎排名。

顶栏固定为开始使用、实验案例、结果与诊断、引擎与模型、研究导读、参与开发六个入口。新增页面放进对应栏目页的目录树；切割案例归入“切割与推动”。每页只保留一个目录树父级，中英文使用相同层级和文件名，已有页面地址保持稳定。

## 文档发布

本站使用 Sphinx、MyST 和 PyData Sphinx Theme；参考 [RLinf 的信息组织](https://rlinf.readthedocs.io/zh-cn/latest/)，不复用其研究结论。两种语言共用主题与构建脚本，默认中文，支持搜索和深色模式。

`scripts/build_docs.py` 严格构建中英站点；GitHub Actions 对 PR 构建检查，合并到 main 后可部署 GitHub Pages。仓库包含 Read the Docs 构建配置，导入项目需相应服务账号。配置存在不代表站点已上线；发布后必须检查实际页面、语言切换、搜索、图表及移动端。

[贡献与自动研究流程](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md) · [Issue 队列](https://github.com/huangkiki/Dexlab/issues)

## 执行与恢复

实验优先使用通过资源准入的本机，远端可选。选项前复审优先级与活跃任务，保留中断证据，同一队列只有一个执行者。[完整工作流](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md) 说明强制限额、测速/归档互斥及交付条件。持续目标在定时恢复检查之间继续推进；克隆仓库不会安装调度器。

[实际交付与中断恢复审计](https://github.com/huangkiki/Dexlab/blob/main/docs/autonomous-delivery.zh-CN.md)
