# DexLab

**DexLab investigates how contact and friction shape robotic grasping, using reproducible experiments grounded in established physical laws and empirical relations to assess the reliability of physics simulation.**

We use inclined-plane friction, one-dimensional collisions and pinch experiments to examine simulated forces, motion and contact against analytical solutions, conservation laws and sourced empirical relations. This repository provides **findings, reproducible code and raw data** to investigate measurable factors that affect grasping performance and identify the conditions under which each conclusion applies.

[简体中文](README.md) · [Documentation (中文)](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [Experiment reports](docs/site/en/results.md) · [Installation](docs/installation.md) · [Releases and data](https://github.com/huangkiki/Dexlab/releases)

## Engine comparison: one cube, two fixed profiles

Official **MuJoCo 3.15.0** and **SuperDex 1.0.0 FP64**: the same 40 mm, 64 g cube, initial state and gravity; three timesteps (2/1/0.5 ms), 2 s per case. Published MuJoCo records are reused; nine SuperDex cases are new.

| Case | MuJoCo (impedance=0.9) | SuperDex (fixed penalty profile) |
|---|---|---|
| 15° static friction, μ=0.5 | **1.301–1.336 mm** drift; 0/3 pass | **0.708–1.132 mm** drift; 2/3 pass |
| 35° sliding, μ=0.5 | Rotation and intermittent support; 0/3 pass | Stable sliding in the scoring window; 3/3 pass |
| 15° nominal zero friction | Velocity RMSE **8.21×10⁻⁵ m/s**; 3/3 pass | Velocity RMSE **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s**; 3/3 pass |

**Contact settings change drift and stability; engine names alone do not predict the outcome.** SuperDex meets more criteria under these fixed profiles, but its static drift increases with timestep refinement. Existing MuJoCo impedance=0.99 records drift only **0.141–0.179 mm**, less than these SuperDex results. The zero-friction difference also involves MuJoCo's native friction floor. Velocity errors use the 0.5–2 s window; the report retains initial transients, every failure and the conditions of the different contact models.

[Full comparison, parameters and raw data](docs/incline-comparison-results.md). These counts describe fixed-case tolerance checks, not real-material accuracy or a universal engine ranking.

## What we have learned

### 1. Correct post-impact velocity does not establish an accurate collision process

In one-dimensional elastic-impact experiments with official MuJoCo 3.15.0, all 18 cases passed the final-state criteria while contact overlap reached **5–20 mm**. After varying stiffness and timestep, **24 of 27 cases passed the final-state criteria, but only 2 also met the predefined 1 mm overlap budget**. Collision evaluation therefore needs velocity, energy and contact history together.

[Elastic-impact results](docs/elastic-impact-results.md) · [Stiffness and penetration](docs/impact-stiffness-results.md) · [Discrete contact explanation](docs/impact-discrete-results.md)

### 2. A more accurate solve does not necessarily produce a steadier grasp

In the MuJoCo 3.15.0 standard-block pinch diagnostic, tighter solver tolerances substantially reduced the residual between force and motion records, yet the block still slipped about **2 mm during one second of loading**. Numerical force balance and object retention are separate outcomes that need separate measurements.

[Pinch load and slip](docs/pinch-load-results.md) · [Six-case residual diagnostic](docs/pinch-impulse-results.md)

### 3. Gripper force limits change grasp outcomes

Across 16 cases in the fixed Genesis standard-block fixture, **0.2/0.4 N limits failed retention, while 0.8/10 N held and released the object**. The result persisted at ±2 mm initial offsets, establishing a reproducible boundary for this fixture.

[Every case, failure and raw record](docs/force-limit-results.md)

![Standard-block closing, lifting and release](demos/contact-benchmark/media/genesis-pinch.gif)

*Continuous close-up replay of measured Genesis states, displayed by MuJoCo. This illustrates one fixed configuration; the report contains every force-limit case.*

### 4. Contact parameters tuned for one scene are not general material parameters

Transferring three fixed contact configurations across ten mass/size combinations produced **30 runs that all missed the combined target for a prescribed synthetic dynamic response**. These parameter mappings have limited applicability and need checks across loads and sizes.

[Parameter-transfer experiment and all outcomes](demos/contact-benchmark/TRANSFER.md)

Each finding applies to the engine version, model and conditions frozen in its report. These are analytical-model and numerical-experiment findings; real-material accuracy requires measured references. The results cannot be pooled into an engine ranking.

## Start here

- **Read findings and figures:** [Full experiment reports](docs/site/en/results.md) and the [stage report](docs/holiday-report.md).
- **Recompute results:** Each report links its frozen protocol, scorer and raw records; public archives are available in [Releases](https://github.com/huangkiki/Dexlab/releases).
- **Run a demo:** Follow the [installation guide](docs/installation.md), then try the apple-stem grasp below.

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# Or --backend superdex; add --headless without a display
```

The viewer opens after SDF preparation and planning. No model API key is needed. Use each research report's recorded versions and commands for its experiments.

Future work, unfinished tasks and blockers are tracked in [Issues](https://github.com/huangkiki/Dexlab/issues).

## Code and sources

Experiments use official physics engines and retain parameter provenance, failures and independent scoring. [Experiments](demos/) · [Development workflow](docs/autoresearch.md) · [Asset sources and licenses](docs/ASSETS.md)

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [Genesis](https://github.com/Genesis-Embodied-AI/Genesis), [Newton](https://github.com/newton-physics/newton), [OpenArm](https://github.com/enactic/openarm) and [Wuji](https://github.com/wuji-technology). Code is licensed under [Apache-2.0](LICENSE).
