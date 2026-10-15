# 豆腐连续两刀

此目录保留历史初速度协议；当前首页的刀面推动使用[独立新记录](../tofu-knife-push/README.md)。

[English](README.md) | [简体中文](README.zh-CN.md)

[Three-column comparison / 三列对比](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-comparison.html)

![Two tofu cuts](../../docs/evidence/cutting/tofu-sequential/particles-poster.png)

长方体软块切两刀形成三块，撤刀后只给左块向左初速度。该任务对应 BladeMaster/CRESSim-MPM 原站对比；香蕉切片独立展示。任务与已知刀厚对齐，原作完整参数未对齐，不作同条件性能排名。

Use `python -m dexlab.tofu_cut --task tofu-sequential --motion-protocol impulse --output RUN` inside the repository resource guard. Score with `python -m dexlab.cutting_score RUN`; render with `python -m dexlab.cutting_showcase RUN --output MEDIA`.

[Evidence](evidence.json) · [Raw archives](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)
