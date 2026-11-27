# 翻花绳 Opening A

先把一根闭环绳套在两边，再把双手向外分开。绳从松弛下垂变成上下两股近水平的线。libuipc 求解绳的拉伸、弯曲、自接触和手掌接触。绳用 160 个顶点表示，固定点数为 0。视频逐帧投影求解器读回的绳中心线，手掌插画跟随实测导向件中心。

```{raw} html
<video controls playsinline preload="metadata" width="1280" height="720"
       style="width:100%;height:auto" poster="_static/rope-opening-a/opening-a.png"
       aria-label="由 libuipc 绳轨迹生成的翻花绳 Opening A 回放">
  <source src="_static/rope-opening-a/opening-a.mp4" type="video/mp4">
  <a href="_static/rope-opening-a/opening-a.mp4">下载 Opening A 回放</a>
</video>
```

## RTX 4090 实跑结果

libuipc 0.0.30 按 120 Hz 跑了 240 个物理步。绳用胡克定律计算轴向拉伸，用 Kirchhoff 杆模型计算弯曲。两只手的碰撞部分用带槽的仿射体导向件表示，接触和摩擦由 IPC 求解。导向件在 1.2 秒内分开，随后保持。独立评分检查 1.6 至 2.0 秒之间的 49 帧，包含两个端点。

| 检查项 | 开启绳和导向件接触 | 门槛 |
| --- | --- | --- |
| 绳拓扑 | 单一闭环 | 一个连通闭环 |
| 导向件最小间距 | 490.0 mm | ≥ 440 mm |
| 绳越过两侧导向件中心的最小距离 | 27.7 mm | ≥ 18 mm |
| 9 个竖直截面各自穿过的绳股数 | 两股 | 保持阶段每帧均为两股 |
| 两股垂直间距 | 79.91–79.96 mm | 45–100 mm |
| 绳股偏离端点连线的最大距离 | 1.46 mm | ≤ 6 mm |
| 全程绳单段最大绝对应变 | 0.79% | ≤ 10% |

对照只关闭绳和手掌导向件之间的接触，复用同一初始绳形、重力、双手命令和绳自接触。手继续向外张开，绳在重力下坠落。到 0.217 秒，双手间距为 388.7 mm，关闭组的绳最高点已低于导向件初始中心 50.0 mm。同一时刻，开启组的绳最高点仍高于该中心 40.0 mm。关闭组因此脱离支撑，保持阶段没有形成两股绳。

这次复现的是预穿绳之后的展开定型，手掌运动由脚本给定。逐指挑绳、手指关节运动和真实绳材标定属于后续验证范围。

{download}`下载 MP4 <../../evidence/rope-opening-a/opening-a.mp4>` · {download}`指标与文件哈希 <../../evidence/rope-opening-a/metrics.json>` · [原始轨迹和场景配置](https://github.com/huangkiki/Dexlab/releases/tag/milestone-2026-11-27-libuipc-opening-a)

## 复现

在 DexLab 仓库根目录执行。需要 Python 3.12、兼容的 NVIDIA CUDA 驱动以及带 libx264 的 FFmpeg。可选包依赖为 `dexlab[uipc]`，下面的方式可单独安装演示依赖。

```bash
uv venv --python 3.12 .venv-uipc
uv pip install --python .venv-uipc/bin/python 'pyuipc==0.0.30' 'Pillow>=10.1'
.venv-uipc/bin/python demos/rope-opening-a/simulate.py rope-contact-on
.venv-uipc/bin/python demos/rope-opening-a/evaluate.py rope-contact-on/trajectory.npz
.venv-uipc/bin/python demos/rope-opening-a/render.py rope-contact-on/trajectory.npz rope-replay
.venv-uipc/bin/python demos/rope-opening-a/simulate.py rope-contact-off --no-guide-contact
.venv-uipc/bin/python demos/rope-opening-a/evaluate.py rope-contact-off/trajectory.npz
```

使用新的输出目录。最后一条命令预期返回退出码 1，表示对照没有通过双股绳保持验收。

[演示源码](https://github.com/huangkiki/Dexlab/tree/main/demos/rope-opening-a) · [libuipc 0.0.30](https://github.com/spiriMirror/libuipc/releases/tag/v0.0.30)
