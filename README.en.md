# DexLab

[简体中文](README.md) | [English](README.en.md)

**Reproducible experiments in robot contact dynamics and cloth simulation.**

DexLab organizes experiments with UniLab to study how collision geometry, friction, actuation and numerical solvers affect simulation. Parameter provenance, independent acceptance and computational cost connect simple contact tests to robotic manipulation.

[Run](#run) · [Benchmark protocol](docs/benchmark.md) · [Backend implementation](docs/sdf-backends.md) · [Issues](https://github.com/huangkiki/Dexlab/issues) · [Releases](https://github.com/huangkiki/Dexlab/releases)

## Apple-stem grasp

OpenArm dual arms with Wuji hands. The right thumb and index finger pinch the stem, lift and hold. The apple and stem form one free rigid body; both pads and the apple use SDF collision geometry. No attachment constraint or engine source modification is used. Control consumes known object pose and scripted joint targets.

### MuJoCo

![MuJoCo grasp close-up](demos/apple-stem-grasp/media/mujoco-sdf.gif)

### SuperDex

![SuperDex grasp close-up](demos/apple-stem-grasp/media/superdex-sdf.gif)

Continuous 14-second physics trajectories: approach, close, lift and hold. Both recordings are replayed with MuJoCo rendering; the display camera does not control the robot. [Videos and provenance](demos/apple-stem-grasp/README.md)

## Experiments and backends

| Experiment / backend | Current delivery |
|---|---|
| MuJoCo 3.11.0 · native SDF | Complete single-scene grasp acceptance; frozen-case and timestep study |
| SuperDex 1.0.0 FP64 · native SDF | Complete single-scene grasp acceptance; frozen-case and timestep study |
| PhysX / IsaacSim | [Integration and physics qualification #5](https://github.com/huangkiki/Dexlab/issues/5) |
| Newton and other UniSim backends / solvers | [Runtime and capability qualification #11](https://github.com/huangkiki/Dexlab/issues/11) |
| Contact: indentation, sliding, pinch, release | [Mechanistic benchmark #10](https://github.com/huangkiki/Dexlab/issues/10) |
| Cloth: extension, sag, obstacle drape | [Separate experiment family #12](https://github.com/huangkiki/Dexlab/issues/12) |

MuJoCo constructs soft constraints from SDF contact searches; SuperDex integrates smooth penalty and friction forces over surface samples. Timesteps, drives and contact parameters are configured separately. Existing apple results are task acceptance records, not an engine-accuracy ranking. [Parameters, measurements and approximations](docs/sdf-backends.md)

The apple task uses the UniLab lifecycle while DexLab owns its native scenes. UniSim built-in adapter equivalence is qualified separately; linked work items above do not imply a backend has passed these experiments.

## Run

Linux x86_64, with [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
bash demos/apple-stem-grasp/run.sh --backend superdex
```

Add `--headless` on servers. No model API key is required. [Installation](docs/installation.md) · [Task and independent acceptance](demos/apple-stem-grasp/README.md)

```bash
# Evaluate the same frozen cases; preserve failures and raw evidence
.venv/bin/python -m dexlab.benchmark run --split regression \
  --output demos/apple-stem-grasp/runs/regression-v1
```

## Evaluation

- Simple experiments check expected behavior: support a load, slip under overload, and release when opened.
- Task experiments use frozen development, regression and test cases; all successes and failures remain in reports.
- Penetration, hold drift, contact support, numerical stability and cost are reported separately. Cloth has its own deformation and contact metrics.
- Parameter sources, runtimes, cases and scoring versions are fixed. Analytic references, numerical convergence and physical measurements are distinct evidence.

No hardware material calibration or autonomous visual grasp is claimed. [Protocol and commands](docs/benchmark.md) · [Model audit](docs/model-audit.md) · [Jitter diagnostics](docs/jitter.md)

## Development and credits

Issues track research. Autodev implements, verifies and reviews each task, then merges and releases eligible changes. [Workflow](docs/autoresearch.md)

Thanks to [UniLab / UniSim](https://github.com/unilabsim/UniLab), [SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [OpenArm](https://github.com/enactic/openarm) and [Wuji](https://github.com/wuji-technology). The grasp demo is included in [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex).

Code: [Apache-2.0](LICENSE). [Third-party assets and terms](docs/ASSETS.md).
