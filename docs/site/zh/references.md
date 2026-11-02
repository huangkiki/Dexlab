# 外部参考资料

这些资料提供研究背景与评测方法参考。外部实验与 DexLab 自己的结果分别标注，不计入本站的引擎覆盖或通过数量。

## 使用 Newton 的研究论文

[分类导读](newton-reading-guide.md)按七个方向解释全部 35 篇论文，并提供接触与可微仿真、仿真校准、世界模型三条阅读路线。每篇附一句话说明和原始来源，阅读范围为摘要及作者页面。

[完整论文索引](newton-publications.md)收录 Newton 官方 `PUBLICATIONS.md` 截至 2026-11-02 核对的全部 35 项文献：34 项研究和 1 项仅用作对照基线的研究。保留题名、作者、日期和原始链接，注明 The Newton Developers 署名及 CC BY 4.0 许可。这是外部文献目录，不是 DexLab 的复现记录。

## Manda Robotics：物理引擎对比

同一任务在不同仿真配置下应该比较什么？[中文导读](manda-physics-engines.md)提供实验配置、阅读导航、关键术语和结论边界，并链接原文的图表与交互回放。

原文发布于 2026-10-05；导读核查于 2026-10-08。当前提供原创摘要与评论，未转载完整文章、图表或网页程序。

[英文原文](https://mandarobotics.com/blog/comparing-physics-engines/index.html) · [仓库参考目录](https://github.com/huangkiki/Dexlab/tree/main/docs/references)

## UniCross：连续技能过渡

[参考调研](unicross.md)讨论不重置物体的技能过渡能否补充已有手内旋转研究。阅读深度仅为项目页及 arXiv 摘要／元数据，源码、控制器、资产和原生参数均未准入；本文是参考与复用／暂缓决定，不是可运行基准，也不是 DexLab 复现结果。

## 对照 DexLab 自己的证据

- [引擎与模型](engines.md)：记录版本、求解配置和建模假设。
- [研究结果](results.md)：查看本项目的冻结协议、原始记录与失败工况。

将外部资料转化为可核查的问题：导入后模型是否匹配，反馈控制输入怎样产生，力与冲量何时记录，任务失败与数值无效怎样区分？文献中的参数与结果不会自动成为本项目的验收依据。

```{toctree}
:maxdepth: 1

Newton 论文分类导读 <newton-reading-guide>
Newton 研究论文 <newton-publications>
Manda 物理引擎比较导读 <manda-physics-engines>
UniCross 参考调研 <unicross>
```
