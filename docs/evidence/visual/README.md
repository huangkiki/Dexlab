# Recorded visual comparisons / 已有实验可视对照

These files replay historical measurements; the exporter never advances physics. Source configuration, original independent score, full-rate channels, force/state epochs and SHA-256 references are stored in every `*.json.gz` bundle. `sources.json` freezes the displayed profiles and conditions. The experience index selects the same files for both README languages and the website. No reliable coverage count changes.

这些文件展示已有测量。导出器只读取记录状态，不重新积分物理；每份压缩 JSON 保留配置身份、原独立评分、全速曲线、力／状态时刻及来源 SHA-256。`sources.json` 固定展示配置与条件，经验索引驱动 README 和双语网站。可视化不增加可靠覆盖计数。

## Reproduce / 复现

1. Follow the archive links in `sources.json` and the bundles, verify the recorded hashes, and extract the native records. Preserve each report's original directory layout. Pinch records and their verified videos already live in `docs/evidence/force-limit/`.
2. Create a **private** JSON input map from each `source_id` in `sources.json` to its extracted campaign directory. `normal` maps to the original `.tar.gz` archive, not an extracted directory. Do not commit host paths.
3. In the qualified Python environment with NumPy, MuJoCo, Pillow, Matplotlib and imageio/FFmpeg, run the following through the repository's bounded runner (rendering only). Chinese figure generation requires Noto Sans CJK.

```bash
python scripts/export_visual_research.py --input-map /private/input-map.json
python scripts/plot_visual_summary.py
```

After reviewing a regenerated artifact, update its `data.sha256` in `docs/research-experiences.json`; changed hashes are never silently accepted by the build. Then:

```bash
python scripts/visual_research.py
python scripts/build_visual_research.py
python -m unittest tests.test_visual_research
python scripts/build_docs.py
```

下载各来源归档并校验哈希后，用私有 JSON 将 `source_id` 对应到原生记录目录；`normal` 对应原始压缩包。生成器在现有资源约束下运行；审阅结果后才更新经验索引哈希。展示数据检验会拒绝身份、单位、时钟、帧索引、媒体或来源的变化。

## Playback interpretation / 回放解释

- Incline and normal videos use one display renderer and identical body-follow camera/scale within each comparison. They do not depict differences in native renderers. Pose quaternions are normalized for display only. A shared ruler and numerical coordinates retain world displacement.
- Historical Genesis videos retain their original camera and provenance. The frame map records the actual source sample index and time; force channels retain their own sampling epoch. The 2–3 s shading marks the original hold window.
- Full-rate curves are downloadable. Interactive drawing uses min/max envelopes to preserve peaks, while cursor readouts use the original samples. Invalid observations remain diagnostic and do not enter a physical-error ranking.
- Media load only after a user action. Static plots, all condition downloads and raw evidence remain usable without JavaScript or when media fails. No autoplay is used, including reduced-motion mode. A local preview server must support HTTP Range for video seeking.

斜面与法向回放统一使用显示渲染器、物体跟随相机及尺度；原始测量和评分保持不变。夹持复用原有视频及逐帧来源。力与状态采样语义分开记录；全速数据可下载。无效观测仅用于诊断；静态图表和各工况下载不依赖 JavaScript，视频从不自动播放。
