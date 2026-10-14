# 豆腐状软块对半切

[English](README.md) | [简体中文](README.zh-CN.md)

依据 [BladeMaster v2](https://arxiv.org/abs/2609.27342v2) 独立实现单次切割 CPU TLMPM：刀具—材料反力反馈、撤刀后持久分离，以及单侧诊断冲量。参数为合成设置，首版不接机械臂，也未做真实豆腐标定。

[![豆腐表面回放](../../docs/evidence/cutting/tofu/surface-poster.png)](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html)

[方法、参数、验收、结果与受限复现命令](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html) · [协议源码](../../docs/site/zh/cutting.md)

- 运行：`python -m dexlab.tofu_cut --output 新目录`
- 负对照：`--mode partial` / `--mode uncut`
- 独立复算：`python -m dexlab.cutting_score 运行目录`
- 回放：`python -m dexlab.cutting_showcase 运行目录 --output 媒体目录`

物理与后处理均使用协议中的资源限额和共享执行锁。可选依赖为 `dexlab[cutting,cutting-render]`。每次运行保存状态、逐步原生观测、配置、源码哈希和独立评分。这是自定义参考任务，不计为第七个已准入引擎。

[原 v0.61.0 粒子回放](media/replay.gif)仍完整保留。[香蕉连续三刀切片](../banana-cut/README.md)扩展了持久多刀历史。
