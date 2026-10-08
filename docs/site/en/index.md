---
html_theme.sidebar_secondary.remove: true
---

<div class="lab-kicker">ROBOTICS · CONTACT DYNAMICS · REPRODUCIBILITY</div>

# DexLab

[Holiday findings and next steps](https://github.com/huangkiki/Dexlab/blob/main/docs/holiday-report.md)

<div class="lab-subtitle">A lab for robot contact dynamics</div>

From a single grasp to reproducible physical evidence. Studying how geometry, contact, solvers and drives shape robot manipulation.

<div class="lab-actions"><a class="lab-button" href="quickstart.html">Run an experiment <span>↗</span></a><a class="lab-link" href="results.html">Read the findings →</a><a class="lab-link" href="https://github.com/huangkiki/Dexlab">GitHub ↗</a></div>

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

<div class="lab-caption">APPLE STEM GRASP · OpenArm × Wuji · Continuous 14 s dynamics records</div>

:::::

Free rigid body, SDF fingertips and stem, scripted joint control. These default development scenes do not represent all test outcomes.

## What the experiments show

Findings first, with the data, failures and measurement limits alongside them.

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item-card} 01 / Apple stem grasp
:class-card: lab-finding
<div class="lab-score"><strong>1/10</strong><span>MuJoCo</span><strong>10/10</strong><span>SuperDex</span></div>

Ten paired regression scenes. Robustness of fixed configurations, not an engine-accuracy ranking.

[Per-scene metrics and failures](results.md)
:::
:::{grid-item-card} 02 / Robot cloth grasp
:class-card: lab-finding lab-finding-warning
<div class="lab-score"><strong>176/225</strong><span>historical intersecting frames</span></div>

Independent geometry checks detect cloth–table intersections, up to 3.00 mm interior depth. This historical failure is retained; a repaired 9 s development case now passes, with only 7.95 µm self-penetration margin.

[Failure analysis and repair](results.md)
:::
::::

:::::{div} lab-chart

![Per-scene apple grasp metrics](../../evidence/apple-metrics.svg)

:::::

Historical versions: MuJoCo 3.11.0 (0.5 ms) and SuperDex 1.0.0 FP64 (2 ms). Timesteps, friction and drives differ; wrist-relative displacement is not material slip. Intervals and acceptance criteria: [results report](results.md).

## From basic contact to robot manipulation

::::{grid} 1 1 3 3
:gutter: 3
:::{grid-item-card} Rigid grasping
:link: experiments
:link-type: doc
:class-card: lab-task
Apple stems, SDF contact, holding and support. Separate task success from physical validity.
:::
:::{grid-item-card} Cloth manipulation
:link: experiments
:link-type: doc
:class-card: lab-task
Grasping, drape and stretch. Inspect intersections, material response and solver limitations.
:::
:::{grid-item-card} Contact and actuation
:link: benchmark
:link-type: doc
:class-card: lab-task
Sliding, loading and transients. Use simple experiments to explain complex failures.
:::
::::

## Dexterous roadmap

Six research layers: tasks, actuation, physics, sensing, data and transfer. ManiSkill integration and in-hand rotation remain planned. [→ Dexterous roadmap](dexterity.md)

<div class="lab-note">MuJoCo 3.14.0 has scoped development and regression evidence; Genesis qualification remains pending. Current results do not establish hardware accuracy. <a href="engines.html">Versions and capability limits →</a></div>


```{toctree}
:hidden:
:maxdepth: 1

Quick start <quickstart>
Experiments <experiments>
Results <results>
Engines <engines>
Dexterous roadmap <dexterity>
Research ledger <research-ledger>
Benchmark <benchmark>
Contribute <contributing>
```

[Analytical incline friction: all18 cases, failures and limits](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-friction-results.md)

[Incline diagnosis: none of12 controls restored continuous support](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-diagnosis.md)

[Impact phase study: 36 cases, 2/9 complete phase groups pass; coarse endpoints remain near exact](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-phase-results.md)

[Discrete contact audit: 54 trace predictions pass; exact rebound endpoints do not ensure accurate transients](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-discrete-results.md)

[Stiffness and overlap: 24/27 final-state passes, 2/27 within the joint 1 mm budget](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.md)

[Elastic impact:18 final-state passes, with5–20mm contact overlap](https://github.com/huangkiki/Dexlab/blob/main/docs/elastic-impact-results.md)

[Standard cube pinch:3 pass,9 physical failures,6 consistency rejections](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md)

[Six-case pinch impulse findings](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-impulse-results.md): force-balance residual decreases, creep persists.
