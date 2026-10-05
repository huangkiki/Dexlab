---
html_theme.sidebar_secondary.remove: true
---

<div class="lab-kicker">ROBOTICS · CONTACT DYNAMICS · REPRODUCIBILITY</div>

# DexLab

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
<div class="lab-score"><strong>176/225</strong><span>相交帧</span></div>

独立几何检查检出布—桌相交，最大内部深度 3.00 mm。评分已修正，物理修复尚未通过。

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

<div class="lab-note">新批次须使用官方最新稳定版，运行资格尚待验收；Genesis 已列入计划。当前结果不证明真机精度。 <a href="engines.html">版本与能力边界 →</a></div>


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
