# 外部参考资料

这些资料提供研究背景与评测方法参考。外部实验与 DexLab 自己的结果分别标注，不计入本站的引擎覆盖或通过数量。

## Manda Robotics：物理引擎对比

同一任务在不同仿真配置下应该比较什么？[中文导读](manda-physics-engines.md)提供实验配置、阅读导航、关键术语和结论边界，并链接原文的图表与交互回放。

原文发布于 2026-10-05；导读核查于 2026-10-08。当前提供原创摘要与评论，未转载完整文章、图表或网页程序。

[英文原文](https://mandarobotics.com/blog/comparing-physics-engines/index.html) · [仓库参考目录](https://github.com/huangkiki/Dexlab/tree/main/docs/references)

## 对照 DexLab 自己的证据

- [引擎与模型](engines.md)：记录版本、求解配置和建模假设。
- [研究结果](results.md)：查看本项目的冻结协议、原始记录与失败工况。

将外部资料转化为可核查的问题：导入后模型是否匹配，反馈控制输入怎样产生，力与冲量何时记录，任务失败与数值无效怎样区分？文献中的参数与结果不会自动成为本项目的验收依据。

```{toctree}
:maxdepth: 1

Manda 物理引擎比较导读 <manda-physics-engines>
```
