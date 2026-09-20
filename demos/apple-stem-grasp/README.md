# Apple Stem Grasp

Apple manipulation with **SuperDex FP64**, OpenArm V20 dual arms, and two Wuji Hand 2 Beta1 hands.

[![Wuji thumb and index finger lifting an apple by its stem](media/stem-focus.gif)](media/stem-focus.mp4)

[Stem close-up](media/stem-focus.mp4) · [Full 40-second video](media/demo.mp4) · [High-resolution image](media/stem-focus.png) · [Validation](evidence/summary.json)

The close-up replays **3–14 seconds** of the native SuperDex trajectory: closing the fingers, pinching the stem, lifting, and holding. The left view is fixed; the right view follows the recorded apple. All robot and object poses come from the recording. The still image is from **12.0 seconds / frame 240 (zero-based)**; see [media provenance](media/stem-focus.json).

The right hand performs **stem pinch → lift → place → release → fruit grasp → lift**. The left arm remains parked.

Featured in [Awesome Astra Embodied AI · Case 7 — Dexterous Apple-stem Grasp in SuperDex](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex). Astra assisted with writing and debugging the controller. The videos and validation records on this page use the known-pose baseline.

## Run

After [installation](../../docs/installation.md), run from the repository root:

```bash
bash demos/apple-stem-grasp/run.sh
```

Results are written to this demo's `runs/latest/` directory. To independently verify the recording or render videos:

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_wuji_sequence.py demos/apple-stem-grasp/runs/latest
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_wuji_two_views.py demos/apple-stem-grasp/runs/latest
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py demos/apple-stem-grasp/runs/latest
```

- **Physics:** SuperDex. The apple and stem form one free rigid body, held through contact forces.
- **Rendering:** Official, unmodified MuJoCo; rendering only.
- **Control:** Known object poses, inverse kinematics, and joint targets. No model API at runtime.
- **Validation:** The [official PyPI FP64 runtime](evidence/pypi-check.json) passed 40 seconds, 20,000 steps, and all 23 independent checks, with 26 solver steps reporting `STOPPED` and no divergence. The videos and packaged historical recording in `evidence/` use the earlier UniLab source build; see its [validation record](evidence/release-check.json).

Stem bending and fracture are not modeled. Real-hardware calibration has not been performed. See [asset provenance](../../docs/ASSETS.md).

Thanks to [UniLab](https://github.com/unilabsim) and [Project SuperDex](https://github.com/unilabsim/project_superdex) for the simulation foundation, and to OpenArm and Wuji for their robot resources.

[Back to DexLab](../../README.md)
