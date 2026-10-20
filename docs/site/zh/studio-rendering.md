# 重渲染已有实验

Studio 回放让接触部位、材料表面和物体运动更清楚。它使用已保存的状态：渲染不会推进物理仿真、改变评分或修复失败的抓取。

首页将实验汇总成一张预览表。切割沿用连通体表面重建，布料使用记录网格的 Studio 视图；刚体场景采用 MuJoCo 官方 USD 导出器与 OVRTX 路径追踪，RSS 则使用单独固定版本的上游 RTX 回放。各路径保留自己的来源，不能据此声称所有任务使用同一种物理模型。

## 实际回放效果

这 13 条完整回放保留来源时间和实际比例。苹果使用两条独立验收通过的 14 s 回归记录，其余场景沿用已公开的历史记录。六引擎斜面采用相同的物体跟随机位，底部保留世界坐标位置，避免跟随画面掩盖平移。

```{raw} html
<table><tr><th>实验</th><th>回放</th><th>视频</th></tr>
<tr><td>苹果抓梗：MuJoCo / SuperDex</td><td><a href="_static/studio/apple.mp4"><img src="_static/studio/apple.gif" width="500" alt="苹果抓梗：MuJoCo / SuperDex"></a></td><td><a href="_static/studio/apple.mp4">MP4</a></td></tr>
<tr><td>Genesis：0.4 N / 0.8 N 限额</td><td><a href="_static/studio/pinch.mp4"><img src="_static/studio/pinch.gif" width="500" alt="Genesis：0.4 N / 0.8 N 限额"></a></td><td><a href="_static/studio/pinch.mp4">MP4</a></td></tr>
<tr><td>LIBERO demo 0</td><td><a href="_static/studio/libero.mp4"><img src="_static/studio/libero.gif" width="500" alt="LIBERO demo 0"></a></td><td><a href="_static/studio/libero.mp4">MP4</a></td></tr>
<tr><td>六引擎斜面</td><td><a href="_static/studio/incline.mp4"><img src="_static/studio/incline.gif" width="500" alt="六引擎斜面"></a></td><td><a href="_static/studio/incline.mp4">MP4</a></td></tr>
<tr><td>法向接触：初始／调整后</td><td><a href="_static/studio/normal.mp4"><img src="_static/studio/normal.gif" width="500" alt="法向接触：初始／调整后"></a></td><td><a href="_static/studio/normal.mp4">MP4</a></td></tr></table>
<p><a href="_static/studio/manifest.json">13-scene manifest</a></p>
```

[切割表面重建](cutting-surface.md)与[布料 Studio 对比](cloth-comparison.md)保留各自的几何和来源记录；另有 [RSS 同机位默认／RTX 对照](rss-wiping.md)。

## 回放刚体场景

可选渲染环境需要 Python 3.12、MuJoCo 3.12.0、OpenUSD、NumPy、Pillow、imageio/FFmpeg、OVRTX `0.4.0.346409`，以及支持 RTX 的 NVIDIA GPU 和驱动。这些是显示依赖；原始记录仍保留实际物理引擎版本。首次渲染包含着色器和渲染器初始化耗时。

```bash
PYTHONPATH=src python scripts/prepare_studio_replays.py apple PATH_TO_VERIFIED_RUN OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py pinch dev-cap-0.4 OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py incline INPUT_MAP_JSON OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py normal INPUT_MAP_JSON OUTPUT
```

苹果记录目录包含 `trajectory.npz`、`display.xml`、引擎身份、通过独立验收的摘要及引用的资产。输入映射指向现有画面对照来源清单中的不可变发布记录；已有读取器核对哈希与公开评分。输出必须使用新目录；加 `--pilot` 可只输出首、中、末帧。

LIBERO 额外核查版本兼容性。先在原有 MuJoCo 2.3.7 环境冻结所有记录帧的原生几何：

```bash
python scripts/studio_libero_reference.py RAW_DIRECTORY REFERENCE.npz
```

再在 RTX 环境运行：

```bash
PYTHONPATH=src python scripts/prepare_studio_replays.py libero RAW_DIRECTORY OUTPUT \
  --reference REFERENCE.npz
```

适配器逐帧、逐顶点核对新旧运行时的世界坐标，最大容差为 10 µm；不一致就停止渲染。和历史显示一样，隐藏 robosuite 的碰撞几何组。

## 画面改变了什么

三盏大面积灯和环境照明替换显示光源。几何、纹理和尺寸来自已记录场景，机位沿用近景或物体跟随方式。每帧只选择已有时间点，不插值生成运动；着色材质描述外观，不代表实测摩擦或柔顺性。

每次输出包含 `replay.mp4`、三张截图、USD 场景和 `provenance.json`，记录输入／输出哈希、帧索引与原生时间、相机变换、渲染设置、实测耗时和运行时变换读回。每个渲染帧均核对全部导出物体与相机矩阵；运动学计算中的四元数归一化舍入差限制在 `1e-14` 内，原始状态数组及文件保持不变。每帧重置路径追踪历史，并关闭运动模糊。

表面重建、照明、降噪和 20 fps 采样属于展示选择。细微穿透、力的时序和任务有效性应结合原始全采样率记录与报告判断；渲染耗时不等于物理吞吐率或实时性能。
