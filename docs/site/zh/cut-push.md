# 仿真里，怎么知道豆腐和香蕉真的切开了？

屏幕上有一道切缝，最直接的检验是让最后一块动起来，看旁边几块会不会跟着走。豆腐两刀分成三块，香蕉三刀分成四块。最后一刀结束，刀刃稍微抬离砧板，留在切缝中，用刀面侧推末块，再撤刀。

```{raw} html
<div class="cutting-showcase cut-push-showcase"><div class="cutting-showcase-grid"><section class="cutting-player" aria-label="豆腐：两刀成三块，直接侧推"><header><h3>豆腐：两刀成三块，直接侧推</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-cut-push/surface-rtx.gif" aria-pressed="true">表面 · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-cut-push/particles.gif" aria-pressed="false">粒子</button></div></header><img src="_static/cutting/tofu-cut-push/surface-rtx.gif" alt="DexLab recorded replay" width="100%" loading="lazy"></section><section class="cutting-player" aria-label="香蕉：三刀成四块，直接侧推"><header><h3>香蕉：三刀成四块，直接侧推</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana-cut-push/surface-rtx.gif" aria-pressed="true">表面 · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana-cut-push/particles.gif" aria-pressed="false">粒子</button></div></header><img src="_static/cutting/banana-cut-push/surface-rtx.gif" alt="DexLab recorded replay" width="100%" loading="lazy"></section></div></div>
```

## 如何读画面

回放上面一行是刀对材料的实际接触力，下面一行是各块从初始状态起的位移。验收另以**最后一刀结束那一刻**为零，只计算侧推动作后的相对位移。

## 让最后一块自己走

一次可信的分离需要三项证据一起成立。材料内部的连通关系已经断开，刀面确实传入了推动方向的接触冲量，末块也相对其余块独立移动。只看整体平移，会把被刀带动的一团材料也算成分离。

| 展示样本 | 末块相对位移 | 沿推动方向的刀面净冲量 | 取消侧推后的相对位移 |
| --- | ---: | ---: | ---: |
| 豆腐，0.125 ms，合成黏性 | 11.001 mm | 0.092625 N·s | −0.240 mm |
| 香蕉，0.25 ms，纯弹性 | 10.209 mm | 0.021000 N·s | −0.247 mm |

各自的无侧推对照在最后一刀前复用相同状态与竖直动作，只取消横向驱动。这样仍然切过材料，但随后没有达到推动方向的 **1 mm** 相对位移和 **0.001 N·s** 净冲量门槛。负对照把「切成几块」和「确实由刀把最后一块推开」分成了两个可以检查的事件。

当前展示的豆腐还检验了撤刀后的抖动。在固定 **0.125 ms** 步长下加入合成黏性，撤刀后选定窗口的质心横向峰峰值从 **0.0711 降到 0.0384 mm**。这说明这个合成模型的晚期运动对黏性敏感。真豆腐的材料参数和刀力仍需实测。

```{raw} html
<span id="id5"></span>
<span id="id6"></span>
<span id="id7"></span>
```

## 实验记录

[完整实验报告、无推对照与复现](cut-push-report.md) · [表面重建与回放来源](cutting-surface.md)

[Paper Sharing：BladeMaster 原文与中文全译](blademaster-paper)
