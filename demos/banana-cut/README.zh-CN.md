# 香蕉连续三刀切片

[English](README.md) | [简体中文](README.zh-CN.md)

[表面／粒子交互回放与完整实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html)

![香蕉表面回放](../../docs/evidence/cutting/banana/surface-poster.png)

连续三刀、四段材料，持久三进制切割历史，以及刀具—材料双向反力闭环。几何和参数为合成设置；尚未做真实香蕉标定，不含机械臂或学习策略。

表面直线切缝和逐帧开口数值从同一份记录刀路生成，不再内置三条固定切面；这仍是平面近似，不是 Hermite／局部对偶轮廓重建。

在仓库的资源限额与共享运行锁内执行 `python -m dexlab.tofu_cut --task banana --motion-protocol impulse --output RUN`，用 `python -m dexlab.cutting_score RUN` 独立评分，再用 `python -m dexlab.cutting_showcase RUN --output MEDIA` 渲染保存状态。参数、负对照、资源限制与复现步骤见上面的实验页。

[完整证据，包含失败尝试](evidence.json) · [原始记录](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)

[Latest continuous knife-face push / 最新连续刀面推动](../cut-push/README.md).
