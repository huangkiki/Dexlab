# Learning 迁移、教材先修与九单元教程：验收范围

[当前工作](current-work.md) · [迁移任务 #1](https://github.com/huangkiki/sim-learning/issues/1) · [样章任务 #2](https://github.com/huangkiki/sim-learning/issues/2)

基线为 `d1dbd503f05473ad29b509675b96c617fa101e22`。本记录描述本批可审查内容及核对方法；合入状态以 PR 的实际 head、CI 与合并记录为准，不把本地文档存在算作已发布。

## 本批内容

- 八仓现行名称和导航统一到 Learning，总仓 SVG 与中英文入口同步。原 E0–E7 交付记录保留；只恢复本轮迁移、先修路线和 Solver 教程，E7 继续暂停。
- [Physics-Based Simulation 伴读路线](physics-based-simulation.md)作为先修主线，包含前两轮阅读、专题分流、五项原创自测，以及与原生引擎的差异提示。
- 两篇完整样章：[仿真一步](solver-guide/01-simulation-step.md)与[外层/内层求解](solver-guide/05-nonlinear-and-linear.md)。每篇包括图解、最小方程、配置解释、诊断与三个带答案练习。
- [教材来源](physics-based-simulation-sources.json)与[引擎版本对照](solver-guide/source-versions.md)分开记录。

## 检查与证据

本仓门禁为 `git diff --check`、`python3 scripts/check_docs.py`。这些命令检查差异格式和仓内文件链接，不能验证远程内容、公式或物理行为。

本批另外核对：

1. 教材官方目录中的 37 章顺序；16 个相关上游 Markdown/许可文件的 Git blob；15 个官方网页入口。固定源码与核对范围保存在来源 JSON。这里只核对路线所需文件与章节概览，没有宣称完整教材或实现已逐行审计。
2. MuJoCo 方程和求解器引文指向 `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`，核对文件内容与行范围；DexLab 配置角色和历史观察固定在 `7e4a0774efb4f8b332e866e1495e032b4969c8aa`。SuperDex 的字段与外层/内层限定同时对照原生导读和冻结报告。
3. 用有理数运算复算二维 CG 教学例子：两步得到 `(1/4, 2)`，线性残差为零；这是纸面数值验证，没有执行原生引擎。
4. 浏览器检查改名后的 SVG：1280×340 图中标题和六个标签无重叠或裁切。开发计划桌面首屏也完成目视检查；这不是六引擎运行界面验收。

## 九单元文字稿的续作验收

先对两篇样章完成来源、公式和教学结构审校，沿用“问题 → 直觉/最小公式 → 配置与诊断 → 练习答案 → 英文摘要/来源”的标准补齐七章。剧情原型的未决交互不阻塞可独立审校的文字章节。

- [全部术语索引](solver-guide/term-index.md)按冻结词表逐项核对 63 个 token；Newton 的一个别名合并后为 62 个展示项，另解释五项身份/资格标签。计数不代表独立算法或已运行配置。
- 新章节引用六仓本批固定提交，原生导读继续链接已核对的官方源码。跨仓 main 入口仍需按 PR 合入顺序验收。
- 根任务自审全部新增章节；AI 分工只读复核 Drake 接触/SAP、PhysX PGS/TGS/patch/时间与 Newton 实现/XPBD 量纲等相关部分。没有将这次分工复核写成外部维护者批准。
- 新的标量算例按精确分数或基础算术复算；没有运行引擎。仓内链接、差异和词表映射检查绑定本批实际提交；远端 CI 单独报告。
- [引用迁移记录](learning-migration.md)保留扫描范围、历史例外与未完成集成。

## 仍需独立完成

九单元文字稿及术语索引已在本分支补齐；单章剧情原型、DexLab 入口最终交付和跨仓合入仍由相应 Issue 跟踪。故事风格与交互两项仍待维护者答复。新增跨仓页面在对应 PR 合入后检查默认分支入口；不使用 HTTP 重定向替代内容验收。

本轮没有安装、import、JIT、原生步进、渲染、训练或性能基准。原生运行与 E7 的恢复仍需后续明确安排。过去的验证记录、模型标识和实验身份不因改名重写。

## English summary

This slice migrates current navigation to Learning and adds a book-led prerequisite route plus two solver-teaching pilot lessons. Source identity, chapter order, links, a rational-arithmetic example and the renamed hero graphic have distinct checks. Publication depends on the actual PR head and applicable CI. All nine text units and the frozen-term index are now included. The narrative prototype and final cross-repository integration remain open; native execution and E7 remain deferred.
