# 豆腐连续两刀与刀面推动

**历史协议存档。最新连续切割与刀面侧推，以及逐帧接触力／位移，见[当前展示](cut-push.md)。下文数值与视频仍对应各自历史输入，不是最新任务。**

当前视频用实际刀具接触解释切后位移：切完后先回到左侧切缝，再横向推开左块。刀具由驱动力和材料反作用共同积分；材料速度没有直接修改。香蕉与交叉浅划保持各自任务。

```{raw} html
<section class="cutting-player" aria-label="豆腐连续两刀与独立运动"><header><h3>DexLab · 豆腐两刀</h3>
<div class="cutting-view-switch" aria-label="视图"><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-sequential/particles.mp4" data-poster="_static/cutting/tofu-sequential/particles-poster.png" aria-pressed="true">粒子</button><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-sequential/surface.mp4" data-poster="_static/cutting/tofu-sequential/surface-poster.png" aria-pressed="false">表面</button></div></header>
<video controls muted playsinline preload="metadata" poster="_static/cutting/tofu-sequential/particles-poster.png" aria-label="豆腐连续两刀与独立运动"><source src="_static/cutting/tofu-sequential/particles.mp4" type="video/mp4"></video>
<p>两刀形成三块；刀具回到左侧切缝，以刀面接触向左推，再撤刀。材料没有直接施加速度增量。</p></section>
```

**比较边界：** 原作者片末尾给左块初速度；当前 DexLab 片采用刀面接触推动。相同切割问题不等于相同末尾输入，不能比较这一步的位移、力或成本排名。下面保留旧初速度协议的数据与下载，不能把其位移数值套到新视频。

## 动作与验收

90×30×30 mm 合成软块，先在 x=+15、−15 mm 切两刀，每刀 2 s。前 4 s 与历史细采样记录逐数组相同。新动作从 4.00 s 开始：刀刃 z=36→2 mm（到 4.80 s），刀面 x=−15→−27 mm（到 6.00 s），撤至 z=36 mm（到 6.60 s），7.00 s 结束。推动阶段关闭切割，底层材料与接触求解器不改。

图中 Fx 为刀对材料的真实接触力（负值向左），排除驱动和板支撑力；dx 以 4.00 s 为基准。独立评分要求三块拓扑保持、左块相对位移至少 1 mm、其余块 |dx|≤3 mm、净向左刀接触冲量≥0.001 N·s，且外力账本中没有材料速度冲量。原有动量、重叠、正 Jacobian 门槛不变。

展示网格 5 mm、步长 0.25 ms、刀厚 0.5 mm，刀刃斜面高 5 mm；密度 1100 kg/m³、E=6 kPa、ν=0.35、FLIP=0.95。全部为既有合成参数，未做真实豆腐标定。

## 新刀推协议结果

| Case | Result | Components | Relative motion (mm) | Leftward knife impulse (N·s) | Worker time (s) |
| --- | --- | ---: | ---: | ---: | ---: |
| `physics-001-push` | 通过 | 3 | 11.102 | 0.105801 | 736.02 |
| `physics-002-half` | 通过 | 3 | 11.234 | 0.104222 | 1467.43 |
| `physics-003-no-push` | 负对照按预期拒绝 | 3 | 0.007 | 0.000000 | 729.26 |
| `physics-004-legacy` | 通过 | 3 | 2.799 | — | 155.91 |

半步长是敏感性检查，不等于收敛证明。无推动对照保留三块，但不能通过运动与刀推冲量门槛；旧 impulse 回归按原门槛通过。全部运行及成本保留。

[完整记录](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-knife-push/evidence.json) · [协议](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-knife-push/protocol.json) · [原始记录与媒体下载](https://github.com/huangkiki/Dexlab/releases/tag/v0.66.0)

## 历史初速度协议：更细采样（v0.64.0）

这是 #203 的独立批次，原 v0.62.0 记录与失败保持不变。显示用网格为 5 mm，评分器与物理源码未改变；半步长、未切与第二刀浅切均在运行前冻结。

| Case | Result | Particles | Components | Relative motion (mm) | Peak reaction (N) | Worker time (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `physics-001-tofu-fine` | 通过 | 5184 | 3 | 2.398 | 0.02472 | 532.79 |
| `physics-002-tofu-half` | 通过 | 5184 | 3 | 2.939 | 0.03088 | 1040.47 |
| `physics-003-tofu-uncut` | 负对照拒绝 | 5184 | 1 | 0.234 | 0.00000 | 513.70 |
| `physics-004-tofu-partial` | 负对照拒绝 | 5184 | 2 | 0.717 | 0.02472 | 523.23 |
| `physics-005-banana-fine` | 通过 | 2480 | 4 | 2.350 | 0.06982 | 363.60 |

本批共 5 次物理调用，累计工作进程 2973.79 秒；等待运行锁的时间单独记录。细网格与半步长的差异仍是灵敏度结果，不宣称力收敛。

[完整新记录](https://github.com/huangkiki/Dexlab/blob/main/demos/cutting-refinement/evidence.json) · [测量口径与论文审计](cutting-fidelity.md)

[新增原始记录与数值回放下载](https://github.com/huangkiki/Dexlab/releases/tag/v0.64.0)。

## 历史初速度协议验收（v0.62.0）

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

## 复现

在[既有资源限制和共享锁](cutting.md#复现)内运行：

```bash
python -m dexlab.tofu_cut --task tofu-sequential --grid-spacing .005 --motion-protocol knife-push --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

`--motion-protocol no-push` 是同时间无推动对照；`--motion-protocol impulse` 恢复历史 5 s 初速度协议；`--dt .000125` 做半步长。默认网格仍为 7.5 mm；上面的命令明确指定展示用 5 mm。以独立评分而非录制器退出码判断成功。
