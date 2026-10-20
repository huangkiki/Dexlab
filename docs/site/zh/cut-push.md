# 最后一刀切完，直接用刀面推开

豆腐两刀成三块，香蕉三刀成四块；最后一刀后，刀刃稍抬离砧板，保持在切缝内直接侧推，再撤刀。画面逐帧显示刀对材料的接触力，以及每块材料从初始位置起的 x 位移。

```{raw} html
<div class="cutting-showcase cut-push-showcase"><div class="cutting-showcase-grid"><section class="cutting-player" aria-label="豆腐：两刀成三块，直接侧推"><header><h3>豆腐：两刀成三块，直接侧推</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-cut-push/surface.mp4" data-poster="_static/cutting/tofu-cut-push/surface-poster.png" aria-pressed="true">表面</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-cut-push/particles.mp4" data-poster="_static/cutting/tofu-cut-push/particles-poster.png" aria-pressed="false">粒子</button></div></header><video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu-cut-push/surface-poster.png"><source src="_static/cutting/tofu-cut-push/surface.mp4" type="video/mp4"></video></section><section class="cutting-player" aria-label="香蕉：三刀成四块，直接侧推"><header><h3>香蕉：三刀成四块，直接侧推</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana-cut-push/surface.mp4" data-poster="_static/cutting/banana-cut-push/surface-poster.png" aria-pressed="true">表面</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana-cut-push/particles.mp4" data-poster="_static/cutting/banana-cut-push/particles-poster.png" aria-pressed="false">粒子</button></div></header><video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/banana-cut-push/surface-poster.png"><source src="_static/cutting/banana-cut-push/surface.mp4" type="video/mp4"></video></section></div></div>
```

力和位移来自保存的仿真状态；没有直接给材料速度增量。合成材料参数，未做真实食材标定。

## 如何读画面

第一行显示刀对材料的接触力模长 |F|、世界坐标 Fx、Fz（N），排除刀具驱动力和砧板支撑力。第二行显示从左到右各材料区域的质心 x 位移（mm），以初始状态为零；切开前这些区域仍相连。时间为原生物理时间，GIF 统一慢放以便读数。

显示位移与验收位移分开：验收以最后一刀结束时（豆腐 3.30 s、香蕉 5.30 s）为基准，检查活动块相对其余块的运动。不会把切割过程的压缩位移算成侧推成功。

## 动作与参照

豆腐为 90×30×30 mm 软块、5 mm 网格、0.5 mm 刀片；香蕉沿用弯曲合成几何、6 mm 网格、1 mm 刀片。上方豆腐回放采用 0.125 ms 步长，香蕉为 0.25 ms；0.25 ms 豆腐记录保留为敏感性基线。材料密度 1100 kg/m³、E=6 kPa、ν=0.35；不是食材实测值。

当前豆腐在固定共旋弹性应力上增加 **Newtonian viscosity（牛顿黏性），η=5 Pa·s**；香蕉保留 η=0 的弹性基线。黏度是预先声明的合成参数，未按真实食材或视频外观拟合。默认 `--viscosity 0` 保持旧路径；此次展示显式指定 `--viscosity 5`。

采用空间速度梯度 `L=grad_X(v) F⁻¹`、应变率 `D=(L+Lᵀ)/2`，黏性 Cauchy 应力 `σᵥ=2ηD`，再转换为 `Pᵥ=JσᵥF⁻ᵀ` 加入材料内力。这里选择第二黏度系数为零，对应体积黏度 `2η/3`。梯度来自施加本步内外力之前、按切割历史过滤的 P2G 网格速度；使用显式积分。已分离的切割历史不交换黏性作用。

[BladeMaster §III-B](https://arxiv.org/html/2609.27342v2)提到可选 Newtonian viscosity；上式及 η=5 是本项目明确声明的实现选择，不是作者公开的豆腐标定值。PIC/FLIP（FLIP 比例 0.95）、接触切向阻尼和刀具驱动阻尼保持原配置，均与材料黏性分开记录。

逐步记录 `dt Σ V₀ Pᵥ:grad_X(v) = dt Σ 2ηV₀J D:D`。这是本构黏性耗散，不等同于包含重力、接触、驱动和数值传递的总机械能变化。刚体平移和旋转的对称应变率为零；不能假定材料黏性会消除砧板上的刚体摇摆。

最后一刀结束后，刀刃用 0.20 s 从 −4 mm 目标高度提至 2 mm，保持在材料内；用 1.20 s 侧推 12 mm；用 0.60 s 撤至 36 mm。豆腐向左推、共 6 s；香蕉向右推、共 8 s。以上是驱动目标，画面用实际积分得到的刀具姿态。推动阶段关闭切割，材料位置与速度由求解器推进。

## 豆腐抖动检查

撤刀后 5.4–6.0 s，左块存在重复往复运动；这段刀接触力为零。将步长从 0.25 ms 减半到 0.125 ms 后，20 Hz 回放采样的质心横向峰峰值由 **0.199 mm 降至 0.071 mm**，粒子逐帧二阶差分 RMS 由 **0.133 mm 降至 0.032 mm**。表面与原生粒子同步改善，早先的纯弹性展示选用后者，没有平滑帧、改写位置或添加材料速度。

这两次完整记录均通过原有机械验收。整次 worker 耗时从 **627.38 s 增至 1254.22 s**，包括初始化、记录与评分，不是纯 solver 计时。初始状态尚未在重力下预平衡，开头的沉降仍保留。接触罚函数和每秒传递耗散也随步长改变，因此这里只报告敏感性改善，不能当作收敛或真实豆腐阻尼标定。

[选择记录](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/showcase-selection.json) · [原始数组诊断](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/motion-sensitivity.json)

## 加入材料黏性后的同条件检查

<!-- viscosity-results:start -->
固定 0.125 ms 步长，只把 η 从 0 改为 5 Pa·s。在相同的撤刀后 5.4–6.0 s 窗口，质心横向峰峰值 **0.0711 → 0.0384 mm**；粒子二阶差分 RMS **0.0323 → 0.0140 mm**（降低）；质心额外往复路程 **0.1820 → 0.0713 mm**。没有平滑、删帧或修改原生位置。末段最大刀接触力为 **0 N**。

当前豆腐在完整 6 s 内通过全部 18 项检查；相同黏度的无侧推对照仅按预期未通过相对运动与刀接触冲量两项。正例与对照在 3.30 s 前的材料、刀具、外力与黏性耗散数组逐项一致。切推结束时三块相对于最后一刀的 x 位移为 **-11.096 / -0.137 / -0.053 mm**。全部案例与短探针分列如下：

| Case | 结果 | η (Pa·s) | Δt (ms) | Relative dx (mm) | Knife impulse (N·s) | Viscous dissipation (J) | Worker (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `viscosity-001-probe` | 短探针，非完整验收 | 5 | 0.250 | -0.000 | 0.000000 | 0.000161584 | 121.11 |
| `viscosity-002-tofu` | 通过 | 5 | 0.250 | 10.905 | 0.095026 | 0.000170974 | 726.92 |
| `viscosity-003-tofu-half`（当前展示） | 通过 | 5 | 0.125 | 11.001 | 0.092625 | 0.000135789 | 1445.54 |
| `viscosity-004-tofu-half-control` | 按预期拒绝 | 5 | 0.125 | -0.240 | -0.001006 | 0.000133319 | 1449.93 |

18 组零黏性材料步进与原实现逐位一致；7 份纯弹性完整记录及 2 份旧协议离线重评分不变。黏性应力经过剪切、体积变化、客观性、刚体运动、动量和离散耗散测试。独立核对器从每份记录的保存状态重建速度梯度及本构耗散，并核对所有子步耗散有限且非负。

本构耗散不是系统总能量损失；本次改善或退化仅属于声明的合成模型与窗口。每次 worker 包括初始化/JIT、记录与评分。初始重力沉降仍保留，未证明真实豆腐阻尼、力值收敛或刀接触模型准确。

[Viscosity protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-protocol.json) · [Evidence](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-evidence.json) · [Matched sensitivity](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-sensitivity.json)
<!-- viscosity-results:end -->

## 保留的纯弹性配对验收

每种材料包含默认步长、半步长、无侧推对照；原半步长豆腐另补相同步长的无侧推对照。无侧推保留相同竖直动作与切割，只取消横向驱动。独立评分核对原生传递图、逐刀分块、质量、正 Jacobian、接触重叠与完整动量／外力账本。推动方向净接触冲量须 ≥0.001 N·s，活动块相对位移 ≥1 mm，其他块 |dx|≤3 mm；阈值沿用原协议。

<!-- cut-push-results:start -->
| Case | 结果 | Δt (ms) | Pieces | Relative dx (mm) | Knife impulse (N·s) | Worker (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `physics-001-tofu` | 通过 | 0.250 | 3 | 10.906 | 0.094646 | 627.38 |
| `physics-002-banana`（展示） | 通过 | 0.250 | 4 | 10.209 | 0.021000 | 249.66 |
| `physics-003-tofu-half`（纯弹性基线） | 通过 | 0.125 | 3 | 11.043 | 0.091680 | 1254.22 |
| `physics-004-banana-half` | 通过 | 0.125 | 4 | 10.629 | 0.020038 | 495.36 |
| `physics-005-tofu-control` | 负对照按预期拒绝 | 0.250 | 3 | -0.240 | -0.004750 | 634.95 |
| `physics-006-banana-control` | 负对照按预期拒绝 | 0.250 | 4 | -0.247 | -0.018299 | 249.55 |
| `physics-007-tofu-half-control` | 负对照按预期拒绝 | 0.125 | 3 | -0.236 | -0.002326 | 1248.61 |

Worker 时间包括初始化/JIT、录制与评分，不是纯 solver 耗时。同任务正例与无侧推对照在推动前逐数组完全一致；旧豆腐协议离线重评分保持不变。原始大体积 NPZ 已保存并记录哈希，本 PR 提供紧凑证据与复现命令，未发布新数据 Release。
<!-- cut-push-results:end -->

半步长只说明时间步长敏感性，不证明收敛。表面是原生状态驱动的重建外观；香蕉已由记录刀路生成直线切面，但 Hermite／局部对偶轮廓与材料资格仍由 [#204](https://github.com/huangkiki/Dexlab/issues/204) 跟踪。本任务不是六原生引擎切割对比，也不是与原作者完整配置对齐的精度排名（[#200](https://github.com/huangkiki/Dexlab/issues/200)）。

## 复现与历史

```bash
python -m dexlab.tofu_cut --task tofu-sequential --grid-spacing .005 --dt .000125 --viscosity 5 --motion-protocol cut-push --output TOFU
python -m dexlab.tofu_cut --task banana --motion-protocol cut-push --output BANANA
python -m dexlab.cutting_score TOFU
python -m dexlab.cutting_showcase TOFU --output TOFU_MEDIA
```

按[资源限制](cutting.md#复现)运行；`--motion-protocol cut-no-push` 为无侧推对照，需保留对应正例的步长和黏度。`--viscosity 0 --dt .00025` 复现保留的纯弹性豆腐基线；香蕉用 `--dt .000125` 复现半步长。旧 `knife-push`（撤出后重新入缝）和 `impulse` 记录保留各自协议。

[Protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/protocol.json) · [Evidence](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/evidence.json) · [Historical tofu](tofu-comparison.md) · [Historical banana](banana-cutting.md)
