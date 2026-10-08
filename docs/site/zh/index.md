---
html_theme.sidebar_secondary.remove: true
---

<div class="lab-kicker">ROBOTICS · CONTACT DYNAMICS · REPRODUCIBILITY</div>

# DexLab

[假期阶段报告：结论与下一步](https://github.com/huangkiki/Dexlab/blob/main/docs/holiday-report.zh-CN.md)

<div class="lab-subtitle">机器人接触动力学实验室</div>

从一次抓取，到可复核的物理证据。研究碰撞几何、接触、求解器与驱动如何影响机器人操作。

<div class="lab-actions"><a class="lab-button" href="quickstart.html">开始实验 <span>↗</span></a><a class="lab-link" href="results.html">阅读实验结果 →</a><a class="lab-link" href="https://github.com/huangkiki/Dexlab">GitHub ↗</a></div>

<div class="lab-tags"><span>UniLab</span><span>MuJoCo</span><span>SuperDex</span><span>PhysX</span></div>

:::::{div} lab-showcase

::::{grid} 1 1 2 2
:gutter: 0
:::{grid-item-card} MuJoCo
:class-card: lab-demo
![MuJoCo SDF grasp](../../../demos/apple-stem-grasp/media/mujoco-sdf.gif)
:::
:::{grid-item-card} SuperDex FP64
:class-card: lab-demo
![SuperDex SDF grasp](../../../demos/apple-stem-grasp/media/superdex-sdf.gif)
:::
::::

<div class="lab-caption">APPLE STEM GRASP · OpenArm × Wuji · 连续 14 秒动力学记录</div>

:::::

自由刚体、SDF 指腹与苹果梗、脚本关节控制。以上是默认开发场景，不代表全部测试成功。

## 实验告诉了我们什么

先看结论，再检查数据。成功、失败与测量边界一起保留。

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item-card} 01 / 苹果梗抓取
:class-card: lab-finding
<div class="lab-score"><strong>1/10</strong><span>MuJoCo</span><strong>10/10</strong><span>SuperDex</span></div>

十个配对回归场景。固定配置的鲁棒性差异，不是引擎精度排名。

[逐场景指标与失败](results.md)
:::
:::{grid-item-card} 02 / 机器人夹布
:class-card: lab-finding lab-finding-warning
<div class="lab-score"><strong>176/225</strong><span>历史相交帧</span></div>

独立几何检查检出布—桌相交，最大内部深度 3.00 mm。保留该历史失败；修复后的 9 秒开发场景已通过，但自接触穿透余量仅 7.95 µm。

[失败分析与修复任务](results.md)
:::
::::

:::::{div} lab-chart

![苹果梗逐场景指标](../../evidence/apple-metrics.zh-CN.svg)

:::::

历史版本：MuJoCo 3.11.0（0.5 ms）与 SuperDex 1.0.0 FP64（2 ms）。步长、摩擦和驱动不同；腕部相对位移不是材料点滑移。完整区间与判据见 [结果报告](results.md)。

## 从基础接触到机器人操作

::::{grid} 1 1 3 3
:gutter: 3
:::{grid-item-card} 刚体抓取
:link: experiments
:link-type: doc
:class-card: lab-task
苹果梗、SDF 接触、夹持与支撑。区分任务成功和物理有效性。
:::
:::{grid-item-card} 布料操作
:link: experiments
:link-type: doc
:class-card: lab-task
夹布、下垂与拉伸。检查几何相交、材料响应和求解器限制。
:::
:::{grid-item-card} 接触与驱动
:link: benchmark
:link-type: doc
:class-card: lab-task
滑动、加载与瞬态。用基础实验解释复杂任务的失效。
:::
::::

## 灵巧操作路线

六层研究地图：任务、执行器、物理、感知、数据与迁移。ManiSkill 接入和手内旋转尚在计划中。 [→ 灵巧操作路线](dexterity.md)

<div class="lab-note">MuJoCo 3.14.0 已有限定范围的开发与回归证据；Genesis 资格仍待验收。当前结果不证明真机精度。 <a href="engines.html">版本与能力边界 →</a></div>


```{toctree}
:hidden:
:maxdepth: 1

快速开始 <quickstart>
实验 <experiments>
研究结果 <results>
引擎与模型 <engines>
灵巧操作路线 <dexterity>
研究证据账本 <research-ledger>
Benchmark <benchmark>
参与开发 <contributing>
```

[斜面摩擦解析评测：完整18工况、失败与限制](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-friction-results.zh-CN.md)

[斜面滑动诊断：12个对照均未恢复连续承载](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-diagnosis.zh-CN.md)

[碰撞相位评测：36 例、2/9 组全相位通过，粗步长近零末态误差仍保持](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-phase-results.zh-CN.md)

[离散接触审计：54条轨迹预测通过，精确反弹末态不保证瞬态准确](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-discrete-results.zh-CN.md)

[刚度与穿透联合评测：27 例中 24 例末态通过，2 例同时满足 1 mm 预算](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.zh-CN.md)

[弹性碰撞解析评测：18例末态通过，但接触重叠5–20mm](https://github.com/huangkiki/Dexlab/blob/main/docs/elastic-impact-results.zh-CN.md)

[标准方块夹持：3例通过、9例物理失败、6例一致性拒绝](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.zh-CN.md)
