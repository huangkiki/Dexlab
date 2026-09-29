# Apple Stem Grasp

[English](README.md) | [简体中文](README.zh-CN.md)

**OpenArm dual arms + Wuji hands · MuJoCo / SuperDex · SDF–SDF contact**

The right hand approaches the apple, pinches its stem, lifts it, and holds it for three seconds. The left arm remains parked. Both backends simulate a free 0.2 kg apple with SDF colliders on the apple, thumb pad, and index pad.

| MuJoCo 3.11.0 | SuperDex 1.0.0 FP64 |
|:---:|:---:|
| [![MuJoCo stem grasp](media/mujoco-sdf.gif)](media/mujoco-sdf.mp4) | [![SuperDex stem grasp](media/superdex-sdf.gif)](media/superdex-sdf.mp4) |
| [▶ Watch demo](media/mujoco-sdf.mp4) · [Validation](evidence/sdf-mujoco/summary.json) | [▶ Watch demo](media/superdex-sdf.mp4) · [Validation](evidence/sdf-superdex/summary.json) |

Both GIFs show a continuous 14-second close-up, rendered by MuJoCo from recorded physics poses. The presentation camera follows the apple and is not a control input. Control uses known object poses, inverse kinematics, and scripted joint targets. Contact forces support a free apple, with no attachment or direct object drive.

## Run

After [installation](../../docs/installation.md), run either command from the repository root:

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco
bash demos/apple-stem-grasp/run.sh --backend superdex
```

The viewer opens after SDF preparation and planning. Add `--headless` to disable it, or `--output demos/apple-stem-grasp/runs/my-run` to preserve a separate recording. Default outputs are `runs/latest-mujoco-sdf/` and `runs/latest-superdex-sdf/` within this demo.

## Verify and render

Each run executes physical checks automatically. To repeat the independent checks and export a video:

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

Use `latest-superdex-sdf` for the other backend. Video export needs FFmpeg and OpenGL / EGL. Failed or incomplete physical checks return a nonzero exit code.

The checks cover clearance, continuous two-pad stem support, penetration, wrist-relative motion, and momentum balance over the full 11–14 s hold. Fruit contact is allowed during approach; fruit-body support is excluded during the hold.

For offline position/velocity/force RMS, peaks and per-pad low-load intervals, use the [jitter diagnostics](../../docs/jitter.md). Missing records remain unknown rather than becoming zero contact.


## UniLab task API

UniLab 1.3.3 discovers `DexLab-AppleStem-v0` via the installed `unilab.tasks` entry point. The task implements the real `ABEnv`/`NpEnvState` lifecycle; `step` advances one native physics step. It owns the SDF scene and contact recorder rather than using UniSim's built-in adapters. That migration is tracked in [issue #4](https://github.com/huangkiki/Dexlab/issues/4).

```python
from unilab.base import registry

registry.ensure_registries(packages=["dexlab.tasks"])
env = registry.make("DexLab-AppleStem-v0", sim_backend="mujoco")
try:
    state = env.init_state()  # creates, settles, and plans a fresh scene
    while not state.terminated[0]:
        state = env.step(state.info["scripted_target"])
finally:
    env.close()
```

`obs["obs"]` is a `(1, number_of_joints + 8)` array: **actual joint positions**, privileged apple position/quaternion (`xyz`, `xyzw`), and episode time. Joint order is `info["joint_names"]`. Actions are `(1, number_of_joints)` absolute targets in radians. The scripted target is an explicit control prior, not an observation or a learned action. Rewards are zero; terminal acceptance is `info["summary"]`. Invalid/nonfinite actions fail before physics advances. Reset rebuilds the scene; there is no automatic reset. One scene per process is supported. This task does not claim RL-training or visual-policy support.

`unilab.json` records task/runtime identity and resolved parameters. The evidence writer records every physics step independently of the environment observation. Final and early exit both close native resources. Interactive display is configured at creation; video export replays the recorded poses separately.

## Implementation

- [MuJoCo model conversion and SDF setup](src/mujoco_model.py), [dynamics and controller](src/mujoco_grasp.py).
- [SuperDex setup and controller](src/wuji_stem_grasp.py), [per-step evidence recorder](src/superdex_evidence.py).
- [Independent verifier](src/verify_sdf_grasp.py).
- [Engine internals, exact settings, results, and limits](../../docs/sdf-backends.md).

Both use official PyPI runtimes without engine source patches. The MuJoCo path uses SuperDex for asset loading and initial planning, then runs its episode dynamics through MuJoCo. Apple and stem form one rigid body; stem deformation, fracture, and hardware accuracy are outside this demo's validation.

[Back to DexLab](../../README.en.md) · [Asset provenance](../../docs/ASSETS.md)
