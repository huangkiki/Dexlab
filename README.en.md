# DexLab

[简体中文](README.md) | [English](README.en.md)

**OpenArm + Wuji hands pinch an apple stem, lift the apple, and hold it in MuJoCo and SuperDex.**

## MuJoCo

![MuJoCo stem-grasp close-up](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex stem-grasp close-up](demos/apple-stem-grasp/media/superdex-sdf.gif)

Each GIF shows the continuous 14-second approach, pinch, lift, and hold. Only the grasp close-up is shown. The presentation camera follows the recorded apple and is not a control input. Both recordings replay actual physics poses using MuJoCo's renderer. [MuJoCo video](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex video](demos/apple-stem-grasp/media/superdex-sdf.mp4)

## Grasp details

- The right thumb and index finger pinch the stem; the left arm stays parked. The apple and stem form **one free 0.2 kg rigid body**.
- The apple and both fingertip pads use **SDF collision geometry**. There are no attachment constraints, direct object position drives, or engine source patches.
- Control uses **known object poses, inverse kinematics, and scripted joint targets**. This is not a visual policy or a learned skill; no model API key is needed.
- The engines are tuned separately. MuJoCo uses SDF contact-point search and soft contact constraints with a **0.5 ms** timestep. SuperDex uses surface-sample integration and smooth penalty energy with a **2 ms** timestep. The same SDF geometry does not imply the same contact-force law.

Independent checks cover clearance, two-finger support, penetration, wrist-relative motion, and momentum balance during a continuous three-second hold. Fruit-body contact is allowed during approach. This is one tuned scene, without stem bending, fracture, or demonstrated hardware accuracy.

[MuJoCo acceptance](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex acceptance](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [Parameters and engine internals](docs/sdf-backends.md)

## Run

Linux x86_64; install [uv](https://docs.astral.sh/uv/getting-started/installation/) first.

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# or
bash demos/apple-stem-grasp/run.sh --backend superdex
```

The viewer opens after SDF preparation and planning; add `--headless` on a server. Both commands step the registered **UniLab task `DexLab-AppleStem-v0`**. DexLab currently owns the native SDF scenes; these have not been replaced by UniSim's built-in backends.

[Installation](docs/installation.md) · [Task API and reproduction](demos/apple-stem-grasp/README.md) · [Autoresearch and issues](docs/autoresearch.md)

## Acknowledgments

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [OpenArm](https://github.com/enactic/openarm), and [Wuji](https://github.com/wuji-technology). The SuperDex grasp appears in [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex); Astra assisted development and debugging.

Code: [Apache-2.0](LICENSE). Third-party assets retain their own terms; see [asset sources](docs/ASSETS.md).
