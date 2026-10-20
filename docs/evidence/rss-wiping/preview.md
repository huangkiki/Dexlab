# RSS homepage preview / RSS 首页预览

The [synchronized preview](preview.gif) is derived from the first paired recordings, [original.mp4](original.mp4) and [no-latch.mp4](no-latch.mp4). It shows the same simulation interval, **10 ≤ t < 30 s**, in both panels at **2× playback speed**. The original retains the sponge; no-latch loses it during wiping. Full recordings remain available, including the original's later return and release.

[同步预览](preview.gif)来自第一组配对记录：[original.mp4](original.mp4) 与 [no-latch.mp4](no-latch.mp4)。两侧展示相同仿真时段 **10 ≤ t < 30 s**，以 **2 倍速**播放。原版保持海绵，无 latch 组在擦拭中滑脱。完整录像保留全部后续过程，包括原版的归位与释放。

## Source and processing / 来源与处理

| Property / 属性 | Value / 内容 |
| --- | --- |
| Runs / 记录 | `controlled-original-01`, `controlled-no-latch-01` |
| Source / 来源 | Existing annotated recordings from the RSS native tiled collision renderer / 已有 RSS 原生 tiled 碰撞几何录像及实测标注 |
| Input frames / 输入帧 | Zero-based frames 100, 102, …, 298 from each 10 fps recording / 每侧 10 fps 录像中从零计数的第 100、102、…、298 帧 |
| Processing / 处理 | Resize each 960 × 544 frame to 720 × 408; stack horizontally; add titles and timing caption; encode a 256-color GIF / 等比例缩放并排，添加标题与时间说明，编码为 256 色 GIF |
| Output / 输出 | 1440 × 478, 100 frames, 10 fps, 10 s, loop / 100 帧、10 秒循环 |
| Preserved / 保留 | Camera, simulation timestamps, phases and measured annotations / 相机、仿真时间、阶段与实测标注 |

Frames are sampled every 0.2 simulation seconds; no interpolation, motion smoothing, spatial crop, re-rendering or changes to the saved state are applied. The panels share a single animation clock. This excerpt is a visual entry point; all six runs and their task outcomes remain in the [complete report](../../site/en/rss-wiping.md).

每 0.2 秒仿真时间取一帧；未插帧、平滑运动、裁剪场景、重新渲染或修改保存状态。两侧共用一个动画时钟。片段用于直观展示，六次完整记录和任务结论见[完整报告](../../site/zh/rss-wiping.md)。

| Input / 输入 | SHA-256 |
| --- | --- |
| `original.mp4` | `40b74c0e5fbd159dc03b7ffa2d6b2a59ed87ad78264ceac324cb3379298c7abe` |
| `no-latch.mp4` | `0008ea5661501c5ad8259b3804729d4634ee4516cccc7f27aeac4366892df9d1` |
