# 豆腐交叉浅切：底部仍然相连

```{raw} html
<section class="cutting-player" aria-label="豆腐交叉浅切：底部仍然相连"><header><h3>豆腐交叉浅切：底部仍然相连</h3>
<div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-scoring/surface.mp4" data-poster="_static/cutting/tofu-scoring/surface-poster.png" aria-pressed="true">表面</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-scoring/particles.mp4" data-poster="_static/cutting/tofu-scoring/particles-poster.png" aria-pressed="false">粒子／历史</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu-scoring/surface-poster.png" aria-label="豆腐交叉浅切：底部仍然相连"><source src="_static/cutting/tofu-scoring/surface.mp4" type="video/mp4"></video></section>
```

刀具先浅切一刀，完全撤出后转过 90°，再做第二刀。两条划痕交叉，下面仍是一整块。表面和粒子回放来自同一份保存状态，画面同时显示两条切口的有符号宽度、刀刃深度、连通块数和底部状态。

## 这个动作检验什么

这是 [BladeMaster 划痕展示](https://jango6324.github.io/blademaster/)启发的独立任务：切割历史应在换向后保持，部分切割应保留底部材料连接。它与[平行两刀后独立运动](cutting-comparison.md)分开验收。

本项目采用引导刀具的两次正交浅切，换向仅发生在刀刃完全离开材料之后；没有复现原作完整的刀尖横向轨迹或自由旋转动力学。刀具平移由驱动力、材料反力和积分共同决定；划痕由原生切割历史暴露，显示层没有画裂纹或人为拉开材料。

## 为什么撤刀后表面线条很细

当前纯弹性材料会回弹。4.2 s 时，两刀仿射材料面的平均开口约为 0.277／0.276 mm；显示网格在顶部交点处的开口仅约 0.039／0.005 mm，低于许多画面的像素宽度。二者是不同位置与采样口径。粒子视图按真实切割历史着色，上部的两次侧标记持续存在，未切底部保持米白；颜色不表示更大的缝隙。

[同状态表面诊断](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/surface-closure.json)记录参考交点 (0,0,30 mm) 的分裂顶点。没有人工扩大开口或画裂纹。要得到与真实食材一致的残余划痕，需要材料模型与实验标定；本任务没有建立这项结论。

## 输入与数值口径

软块 45×45×30 mm，5 mm 网格、3,888 个原生粒子，刀厚 0.5 mm、刃口高 5 mm。目标刀刃从 42 mm 降至 24 mm，再撤回；第二刀重复相同高度轨迹，绕竖直轴转过 90°。持续 4.2 s，名义步长 0.25 ms，半步长对照 0.125 ms。合成材料沿用 E=6 kPa、ν=0.35、ρ=1,100 kg/m³；未做真实豆腐标定。

第一、二刀的切口分别沿 x、y 法向，从两侧粒子的局部仿射材料面测量；负值表示估计面重叠。刀刃深度相对于初始上表面 30 mm，不能解释为相对于瞬时变形表面的局部切深。底部指参考高度低于 15 mm 的固定材料集合。

独立评分要求：完整记录、历史标签不回退、两次均有相反切面标签，实测刀刃最大深度各为 2–12 mm；在 0、1.2、2、3.2、4、4.2 s 的原生传递图均只有一个连通分量，底部全程未标记且连通。同时沿用动量误差≤10⁻⁹ N·s、det F≥0.05、代理重叠≤一个粒子半径及非零材料反力门槛。表面看起来相连不能替代这项检查。

<!-- scoring-results:start -->
## 验收结果

| Case | Result | Components | Scoring depths (mm) | Peak reaction (N) | Worker time (s) |
| --- | --- | ---: | --- | ---: | ---: |
| `physics-001-cross` | 通过 | 1 | 5.977 / 5.967 | 0.007879 | 342.98 |
| `physics-002-cross-half` | 通过 | 1 | 5.966 / 5.964 | 0.008680 | 680.83 |
| `physics-003-cross-uncut` | 负对照拒绝 | 1 | — (knife clear) | 0.000000 | 343.00 |
| `physics-004-sequential-regression` | 通过 | 3 | — | 0.032504 | 178.50 |

前三条是浅切任务；最后一条是原有连续两刀回归。全部案例、失败与成本均保留。两个步长的任务通过不代表力值收敛。

半步长的峰值反力相对默认变化 +10.16%；按灵敏度结果阅读。

<!-- scoring-results:end -->

## 复现与原始记录

在[共享锁与资源限制](cutting.md#复现)内执行；运行前冻结的[协议](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/protocol.json)保留了全部案例、预算和验收口径。

```bash
python -m dexlab.tofu_cut --task tofu-scoring --output RUN
python -m dexlab.cutting_score RUN
python -m dexlab.cutting_showcase RUN --output MEDIA
```

半步长加入 `--dt 0.000125`；未切负对照加入 `--mode uncut`。负对照应被切割任务拒绝，同时保持一块与数值一致性。原始状态、源码和资源成本见[实验记录](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-scoring/evidence.json)，[v0.65.0 归档](https://github.com/huangkiki/Dexlab/releases/tag/v0.65.0)保留本批全部记录。

<a href="_static/cutting/tofu-scoring/measurements.json">逐帧数值</a> · <a href="_static/cutting/tofu-scoring/surface.gif">带数值表面 GIF</a> · <a href="_static/cutting/tofu-scoring/particles.gif">带数值粒子 GIF</a>
