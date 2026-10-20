# 香蕉连续三刀切片

**历史协议存档。最新连续切割与刀面侧推，以及逐帧接触力／位移，见[当前展示](cut-push.md)。下文数值与视频仍对应各自历史输入，不是最新任务。**

一把受力驱动的刀沿三个位置依次落下、撤回，将弯曲的去皮香蕉状软体切成四段。表面与粒子视图来自同一份仿真记录，可以暂停、拖动进度条或切换观察。

```{raw} html
<section class="cutting-player" aria-label="香蕉三刀切片">
<header><h3>香蕉三刀切片</h3><div class="cutting-view-switch" aria-label="视图"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana/surface.mp4" data-poster="_static/cutting/banana/surface-poster.png" aria-pressed="true">表面</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana/particles.mp4" data-poster="_static/cutting/banana/particles-poster.png" aria-pressed="false">粒子</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/banana/surface-poster.png" aria-label="香蕉三刀切片"><source src="_static/cutting/banana/surface.mp4" type="video/mp4"><a href="_static/cutting/banana/surface.mp4">观看视频</a></video>
<p>连续三刀，保留每一刀形成的分离。</p>
</section>
```

最后一段在 6.2 秒受到已知诊断冲量，用于检查切后独立运动；这不是机械臂推料策略。另见[豆腐对半切](cutting.md)。

当前回放使用新增 5 mm 网格、2,480 个原生粒子，最终四段，相对运动 2.350 mm。下方保留原 6 mm 主配置及历史对照；[新增细采样记录](tofu-comparison.md)单列。

## 实现与参数

这是基于 [BladeMaster v2](https://arxiv.org/abs/2609.27342v2) 的独立 CPU TLMPM 实现。三刀分别位于 x = −30、0、30 mm，每刀占用 2 秒，完整记录为 7 秒。刀具通过有力限幅的 PD 驱动运动，材料反作用力改变刀具速度；砧板支持冲量单独记录。

刀具厚 1 mm、宽 80 mm、高 40 mm，底部 5 mm 为对称斜面刀刃。碰撞查询计算该凸棱柱的实际最近点和法向；斜面几何同时用于渲染。原豆腐基线仍使用方盒刀具。

每个粒子用三进制保存历次切割的侧别。只要任意一次切割的已分配侧别相反，两者就不再交换网格动量；未分配的材料仍能形成连接。每次新切割重置接触功进度，保留之前的切割历史。独立评分器重建传递图，检查逐刀 2→3→4 个连通分量，而不是通过颜色或画面缝隙判断切开。

香蕉是自行构造的弯曲几何，长度 120 mm，最大直径约 24 mm；等体积粒子采样。密度 1,100 kg/m³、杨氏模量 6 kPa、泊松比 0.35；其余接触与驱动参数沿用[豆腐实验](cutting.md)，本任务的传递混合系数见下表与原始清单。**这些是合成参数，尚未标定真实香蕉。** 步长变化同时改变惩罚接触刚度，只能作为灵敏度检查。

## 验收记录

<!-- banana-results:start -->
默认配置：Δx=6 mm; dt=0.25 ms; FLIP=0.95; normal scale=0.1. 灵敏度：half-step: dt=0.000125 s; refined: Δx=0.005 m.

| Case / 案例 | Result / 任务 | Components / 分量 | Overlap / 重叠 (mm) | Probe / 相对位移 (mm) | Peak force / 峰值反力 (N) | Time / 记录 (s) |
|---|---|---:|---:|---:|---:|---:|
| `018-final-full` | Pass / 通过 | 4 | 0.754 | 3.807 | 0.03071 | 214.63 |
| `013-final-half-step` | Pass / 通过 | 4 | 0.531 | 4.034 | 0.05387 | 427.21 |
| `014-final-refined` | Pass / 通过 | 4 | 1.145 | 2.350 | 0.06982 | 363.93 |
| `015-final-uncut` | Rejected / 拒绝 | 1 | 0.616 | 0.464 | 0.00000 | 201.47 |
| `016-final-partial` | Rejected / 拒绝 | 3 | 0.733 | 0.740 | 0.03043 | 212.14 |
| `017-tofu-regression` | Pass / 通过 | 2 | 0.633 | 3.221 | 0.07661 | 24.63 |

完整切割的传递图逐刀为 2、3、4 个连通分量；默认最终质量比例为 32.78%, 32.78%, 17.22%, 17.22%。未切与第三刀浅切对照未通过四段任务，数值检查通过。阈值保持：动量误差 ≤10⁻⁹ N·s、det F≥0.05、重叠≤一个代理半径、独立相对位移≥1 mm、其他段横向漂移≤3 mm。

共 18 次有界调用，累计 3610.32 秒（含等待）；源码在最终批次中保持一致。开发尝试中的穿透与一次形变反转失败均保留。传递阻尼和接触系数属于开发选择，最终批次是数值与任务资格核验，不是独立食材泛化测试，也未建立切割力收敛。

[完整指标、配置与失败记录](https://github.com/huangkiki/Dexlab/blob/main/demos/banana-cut/evidence.json) · [原始数据与回放下载](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)。
<!-- banana-results:end -->

## 表面如何得到

去皮香蕉表皮贴合初始材料轮廓，包含纵向细脊、纤维色差和切面果肉纹理。回放从 `trace.npz` 读取每刀实际切割阶段的刀具位置，以中位数生成直线参考接缝；逐帧数值和完整任务评分使用同一组切面。原生切割历史冲突处随切割逐步暴露局部切面；同一原生机械分量中相容或尚未分配侧标记的接缝顶点保持焊接，保留未切透的下部连接。切面开启不由播放时钟或额外位移驱动。完整记录若缺少任一刀、切面重合或不是平行 x 法向直切，评分会拒绝；未完成短探针的计划切面只用于失败诊断。

当前参考 linked volume 在均匀主边上保存原始边界和记录刀面的 Hermite 点／法向；只有局部原生历史同时出现相反侧标记时才断边，未切材料继续形成连接。仍连通时，每单元连接分量解一个 QEF 对偶顶点；保存状态已经分成独立机械分量后，各分量分别用记录切面半空间重建闭合局部体，禁止三角形跨越不相容运动场。表面点继承原生分量／切割编码，并以固定三线性权重跟随由保存粒子位置与形变重建的相容 TLMPM 场。不增加显示开口，也不做几何平滑。当前仍只支持记录的 x／y 轴直切面，是 CPU 离线全量重建；不是扫描食材，也未复现作者在线 GPU 任意刀路更新。粗粒子形变可在外表面留下细小尖刺，粒子视图用于核对机械采样。[详细实现与验收边界](cutting-surface.md)。

数值 GIF 显示三条有符号切口及各段冲量后位移，下方给出刀具反力和内部四面体体积；[论文细节与测量定义](cutting-fidelity.md)说明口径和限制。媒体附带原始状态、渲染源码、输出哈希及实际帧映射。砧板、气孔／纤维颜色、灯光与刀柄属于场景外观。

## 复现

在现有 DexLab 环境安装 `.[cutting,cutting-render]`。通过仓库已有的有界执行与共享运行锁，在新的输出目录运行：

```bash
python -m dexlab.tofu_cut --task banana --motion-protocol impulse --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

上述为运行锁内部的命令；完整外层资源限制示例见[豆腐复现步骤](cutting.md)。`--mode uncut` 保留未切对照，`--mode partial` 仅将第三刀改为浅切。半步长与细网格参数见验收记录。运行器正常退出表示记录完成，任务是否通过需读取独立评分。渲染在单独的受限窗口进行。

[实现任务 #197](https://github.com/huangkiki/Dexlab/issues/197) · [源码与证据](https://github.com/huangkiki/Dexlab/tree/main/demos/banana-cut) · [切割讨论](https://github.com/huangkiki/Dexlab/discussions/191)
