# 豆腐连续两刀与独立运动

本任务对应原站两段参考视频：长方体软块连续两刀，撤刀后检验左块能否独立运动。[香蕉连续切片](banana-cutting.md)独立展示。

```{raw} html
<section class="cutting-player" aria-label="豆腐连续两刀与独立运动"><header><h3>DexLab · 豆腐两刀</h3>
<div class="cutting-view-switch" aria-label="视图"><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-sequential/particles.mp4" data-poster="_static/cutting/tofu-sequential/particles-poster.png" aria-pressed="true">粒子</button><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-sequential/surface.mp4" data-poster="_static/cutting/tofu-sequential/surface-poster.png" aria-pressed="false">表面</button></div></header>
<video controls muted playsinline preload="metadata" poster="_static/cutting/tofu-sequential/particles-poster.png" aria-label="豆腐连续两刀与独立运动"><source src="_static/cutting/tofu-sequential/particles.mp4" type="video/mp4"></video>
<p>两刀分三块，撤刀后只给左块向左的初速度。</p></section>
```

[BladeMaster／CRESSim-MPM／DexLab 三列播放](cutting-comparison.md)

## 输入与比较范围

本实验使用独立 CPU TLMPM 实现；刀具受驱动力和材料反力共同影响。软块长宽高 90×30×30 mm，切割位置依次为 x=+15、−15 mm，每刀包括下切与撤出。刀厚 0.5 mm，与论文该对比所述厚度一致；5 mm 对称刃口为本项目声明的几何选择。

默认网格 7.5 mm，步长 0.25 ms，密度 1,100 kg/m³、杨氏模量 6 kPa、泊松比 0.35、FLIP=0.95、法向比例 0.1。两刀各 2 s；4.2 s 时仅对参考坐标 x<−15 mm 的左块施加 Δv=(−0.12,0,0) m/s，记录至 5 s。该探针是预先声明的初速度条件，不是机械臂推块动作。

**三列任务一致，但尚未声称完整参数一致。** 原论文/视频没有给出足以逐项重建该组对比的所有尺寸、接触、驱动及初速度参数；以上未明确对应原作的数值均为 DexLab 合成设置。原作切口宽度/四面体体积收缩与本项目代理重叠/连接图指标不能互换，不作同条件精度或速度排名。

## 验收记录

<!-- tofu-comparison-results:start -->
| Case | Task | Components | Overlap (mm) | Relative motion (mm) | Peak reaction (N) | Record time (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `019-tofu-comparison-full` | Pass | 3 | 0.102 | 2.799 | 0.03250 | 155.01 |
| `020-tofu-comparison-half` | Pass | 3 | 0.023 | 3.076 | 0.04065 | 307.25 |
| `021-tofu-comparison-refined` | Pass | 3 | 0.145 | 2.624 | 0.03001 | 298.99 |
| `022-tofu-comparison-uncut` | Rejected control | 1 | 0.101 | 0.328 | 0.00000 | 151.38 |
| `023-tofu-comparison-partial` | Rejected control | 2 | 0.121 | 0.624 | 0.03036 | 153.54 |
| `024-banana-regression` | Pass | 4 | 0.754 | 3.807 | 0.03071 | 213.17 |
| `025-tofu-regression` | Pass | 2 | 0.633 | 3.221 | 0.07661 | 24.87 |

默认实验最终三块各占 1/3 质量；施加初速度后左、中、右三块的 x 位移分别为 -2.851, -0.075, -0.029 mm。三组完整切割均按 2→3 分离，负对照保持一块或两块。香蕉与豆腐对半切的回归也通过。

全任务共享账本包含 25 次调用、累计 5114.87 秒（包含失败与等待）；本表 7 条记录使用相同冻结源码。前 18 次香蕉开发/资格记录保留原始源码，不改写为本批次结果。未建立真实豆腐标定或切割力收敛。

[Evidence JSON](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-comparison/evidence.json) · [Raw archives](https://github.com/huangkiki/Dexlab/releases/tag/v0.62.0)
<!-- tofu-comparison-results:end -->

评分从保存的参考传递图、切割历史、位置、速度和外部冲量独立计算。完整任务须按顺序形成 2→3 个连通分量，每块质量与初始切割区域相符；撤刀后左块相对其余块向左移动至少 1 mm，中、右块各自横向漂移不超过 3 mm。数值门槛延用已冻结协议：动量误差≤10⁻⁹ N·s、det F≥0.05、代理重叠≤一个粒子半径，且存在非零材料反力。未切与第二刀浅切分别应保留一个、至多两个连通分量。

## 显示与复现

粒子视图使用实际代理尺寸，便于与原站粒子视频并列观察。表面视图提取材料单元的外露面，按保存的形变梯度与切割历史嵌入；没有增加缝隙或手工移动块体。白色底板、灯光和刀柄为场景美术；显示不是食材标定。

在[已有资源限制与共享锁](cutting.md#复现)内运行：

```bash
python -m dexlab.tofu_cut --task tofu-sequential --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

使用 `--mode uncut` 或 `--mode partial` 运行负对照；半步长为 `--dt 0.000125`，细网格为 `--grid-spacing 0.006`。记录器正常退出不等于通过任务，应检查独立评分。所有失败、预算与原始数据保留在[实验记录](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-comparison)。
