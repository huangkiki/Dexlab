# 夹布评分复核：旧协议通过，几何证据不成立

[简体中文](SCORING.zh-CN.md) | [English](SCORING.md)

**结论：原 9 秒夹布记录不能作为物理有效抓取的成功证据。** `cloth-evidence-v2` 在 225 个保存帧中检出 176 帧的布三角面进入桌体。原生接触最大值很小、布料被抬起、自表面交叉数为零，这三项合起来仍不能排除桌体相交。此次修复的是评分和展示，控制、引擎和物理参数未改；物理修复见 [#32](https://github.com/huangkiki/Dexlab/issues/32)。

![历史记录桌体内部深度](media/table-diagnostic.zh-CN.svg)

## 相同记录的新旧结果

| 输入或检查 | 旧版 v0.14.2 | 新版 cloth-evidence-v2 |
|---|---|---|
| 原始记录的接触、抬升、释放协议 | 通过 | 协议通过，但整体为 `geometry_review_required` |
| 仅把一条轨迹测量改为 20 mm，保留原汇总 | 错误通过 | 拒绝：汇总未覆盖轨迹峰值 |
| 轨迹和汇总均为 20 mm | 穿透阈值失败 | 同一 1.5 mm 阈值失败 |
| 逐步汇总峰值大于 100 Hz 采样峰值 | 允许 | 仍允许，不能错误要求相等 |
| 合成合法记录、完整几何 | 有限协议通过 | `limited_protocol_pass` |
| 桌体几何缺失或不支持 | 未检查 | `geometry_review_required` |

注入只改变内存中的评分输入，未编辑原始轨迹或重新运行物理。合法对照检验评分器，不是另一次真实抓取成功。冻结的[旧评分源码与来源](evidence/legacy/source.json)、[完整新旧对比](evidence/grasp/scoring-comparison-v2.json)、[新版报告](evidence/grasp/verification-cloth-evidence-v2.json)均保留。原 [summary](evidence/grasp/summary.json) 和 [verification](evidence/grasp/verification.json) 不覆盖，其旧 `passed` 字段须按历史协议理解。

| 原始单场景观测 | 数值 | 含义 |
|---|---:|---|
| 材料点抬升 | 121.46 mm | 抬起不等于几何有效 |
| 双指接触采样覆盖率 | 100% | 依赖原生上报接触 |
| 原生桌体接触最大穿透 | 0.2004 mm | 每物理步扫描的接触距离 |
| 桌体内部几何最大深度 | 3.0000 mm | 零厚度三角面内部诊断 |
| 有桌体内部点的保存帧 | 176 / 225 | 25 Hz，最早在 0.00 s |
| 仅检查顶点得到的最大内部深度 | 0 mm | 顶点在外，三角面仍可穿过桌体 |
| 非相邻自表面交叉 | 0 / 225 帧 | 不覆盖与桌体、手部的相交 |

## 几何定义与复核

桌面由 96 个固定、轴对齐盒体组成。先验证内部不重叠、总体积填满包围盒，再把它们作为一个实心盒体。不能验证这些条件、发生旋转或移动时，报告“不支持/证据不足”，不返回安全结论。

对于三角形内的点 `p = p0 + s*(p1-p0) + t*(p2-p0)`，约束 `s,t ≥ 0`、`s+t ≤ 1`；求最大的 `d ≥ 0`，使 `lower+d ≤ p ≤ upper-d`。线性规划得到三角面内点到最近盒面的最大内部距离。**桌体厚 6 mm，因此该指标最多 3 mm；它不是竖直穿透深度，也不是把物体移出碰撞所需的最小平移量。** 零厚度、壳厚 0.5 mm、碰撞半径 1.2 mm 和原生接触距离是不同定义，不能混用原有 1.5 mm 阈值。`1e-8 m` 只是几何数值零容差。

另用多边形裁剪与二分法，在预先固定的第 0、56、112、168、224 帧独立计算同一量，最大差值约 `4.37e-14 m`。两算法共享记录几何和 MuJoCo 正运动学，因此这是算法交叉验证，不是独立物理引擎或真机验证。

[22 KB 参考样本](evidence/grasp/table-reference.npz)包含五帧的 169 个顶点、288 个三角面、桌体边界与源记录哈希，允许不下载机器人资产、不推进仿真就复核几何。它是固定采样的派生样本，不是完整 9 秒轨迹。原始模型、轨迹、测量、计划和失败记录继续保留；仓库仅打包报告、媒体与这个小样本，不能声称克隆仓库即可重评完整历史记录。

## 复现与输出

使用仓库安装环境，在根目录运行几何与评分回归：

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_offline_scoring.py'
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_grasp_evidence.py'
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_table_audit.py'
```

对自己保留的完整记录执行：

```bash
.venv/bin/python demos/cloth-folding/src/verify_cloth.py RECORD --output NEW_REPORT.json
# 原历史记录应退出 2：需要几何复核。输出必须在 RECORD 之外且不存在。
.venv/bin/python demos/cloth-folding/src/compare_scoring.py RECORD --output NEW_COMPARISON.json
.venv/bin/python demos/cloth-folding/src/render_cloth.py RECORD --output NEW_MEDIA_DIR
```

`compare_scoring.py` 专门回归本文这条历史坏记录；其退出 0 表示预期坏记录和负例被正确识别，不表示抓取成功。`verify_cloth.py` 退出码 0/1/2 分别表示有限协议通过、协议失败、几何待复核。原生运行汇总中的 `verified`/`validation.passed` 仅覆盖在线协议。

曲线可用 `src/plot_scoring.py evidence/grasp/scoring-comparison-v2.json --output NEW_PLOT.svg --language zh` 重建（路径相对本 demo；需要 Matplotlib，中文字体使用 Noto Sans CJK SC）。绘图不执行物理。报告记录输入与评分代码 SHA-256；读取前后核对完整输入，拒绝变化。媒体记录视频/GIF与输入哈希，连续回放 225 帧、25 fps、9 s，渲染执行的物理步数为零；[来源](media/grasp-provenance.json)。旧媒体仍可在 [v0.14.2](https://github.com/huangkiki/Dexlab/tree/v0.14.2/demos/cloth-folding/media) 查看。

## 尚未覆盖

- 没有独立的布—机器人三角面检查，不能用本报告证明指腹没有穿布。
- 25 Hz 保存帧不覆盖帧间瞬态或连续碰撞；100 Hz 接触轨迹和逐步汇总也不等价于全表面检查。
- 自表面审计排除共享顶点对，不保证有限厚度分离。
- 缺少材料实测标定和真机反馈；仍无双臂折叠成功或引擎精度排名结论。

这轮修复以“如实拒绝不完整成功证据”为验收目标。实际提交的远端完整门禁与源码树标识随 [版本发布](https://github.com/huangkiki/Dexlab/releases) 附件提供；本报告的历史物理轨迹没有重跑。
