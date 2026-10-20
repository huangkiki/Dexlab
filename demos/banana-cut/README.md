# Banana slicing

[English](README.md) | [简体中文](README.zh-CN.md)

[Surface and particle replay / 表面与粒子回放](https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html) · [English experiment](https://huangkiki.github.io/Dexlab/en/latest/banana-cutting.html)

![Recorded banana surface](../../docs/evidence/cutting/banana/surface-poster.png)

Three guided cuts, four pieces, persistent ternary cut history and a dynamic blade/material reaction loop. Synthetic geometry and parameters; no real-food calibration, arm or learned policy.

Surface seams and frame-wise opening measurements derive from the same recorded blade path instead of three built-in planes. This remains a planar approximation, not Hermite/local dual contouring.

Use `python -m dexlab.tofu_cut --task banana --motion-protocol impulse --output RUN` inside the repository's bounded execution guard. Independently score with `python -m dexlab.cutting_score RUN`, then render the saved states with `python -m dexlab.cutting_showcase RUN --output MEDIA`. See the linked experiment for frozen parameters, negative controls, resource limits and complete reproduction instructions.

[Evidence, including failed development attempts](evidence.json) · [Raw archives](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)

[Latest continuous knife-face push / 最新连续刀面推动](../cut-push/README.md).
