# Uranus: a generative observation backend (candidate)

[English](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html) | [简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html)

> **Status: documented candidate backend. No DexLab runner exists and no formal cohort has included it.** This page defines the interface, evaluation method and evidence boundary; paper results are not DexLab reproductions.

## Original work

**Uranus: Building the Next-Generation Simulation Infrastructure for Embodied AI**

Wenkang Qin, Yukun Zhou, Noah Shen, Jisong Cai, Dongxiao Mao, Baicheng Li, Yue Zhang, Wei Sui<br>
D-Robotics · Peking University · Shanghai Jiao Tong University · arXiv 2026

[Paper](https://arxiv.org/abs/2609.24815) · [Project](https://d-robotics-ai-lab.github.io/large-model-team/blog/uranus/) · [Inference code](https://github.com/D-Robotics-AI-Lab/Uranus-OSS) · [SDK](https://github.com/D-Robotics-AI-Lab/Uranus-SDK) · [Weights](https://huggingface.co/collections/D-Robotics/uranus) · [Demo data](https://huggingface.co/datasets/D-Robotics/Uranus-Demo-Data)

Uranus is a roughly 1.3B-parameter robot video world model. It generates synchronized multi-view observations from reference images, generated history, a future joint-position (`qpos`) trajectory, robot description and camera calibration. Within DexLab, its value is not as a replacement for a contact solver but as a **learnable observation backend**.

```text
reference / generated history
        + future qpos
        + camera intrinsics & extrinsics
        + MJCF / URDF
        + optional text
                ↓
      causal autoregressive DiT
                ↓
       multi-view latent frame
                ↓
       streaming VAE decoder
                ↓
   four RGB frames per camera / step
```

## Position inside DexLab

| Layer | Responsibility | Uranus role |
| --- | --- | --- |
| Task and protocol | scene, initial state, seeds, budget, acceptance | Not provided; owned by DexLab |
| System under test | RoboAPI, VLA, WAM, policy | Not provided; Uranus only generates observations |
| Environment backend | advance the task and return observations | **Candidate generative backend** |
| Action execution | API actions to a controller/joint target | Requires an external IK/controller |
| Evidence and scoring | success, contact, failure attribution, cohort | Not provided; an independent task scorer owns it |

Uranus is not “another DexLab” and cannot directly replace MuJoCo, Newton, SuperDex or Genesis. The intended relationship is:

```text
DexLab task / protocol
        ↓
RoboAPI / VLA / policy
        ↓ (T, 8) end-effector targets
IK / controller / session adapter
        ↓ future qpos
Uranus observation backend
        ↓ generated RGB
task-specific observation + success evaluator
        ↓
DexLab score / evidence / cohort
```

## Interface semantics

Uranus is conditioned on a **future joint-position trajectory**, not torques, velocities, end-effector poses or raw torque actions. For the current eight-value Poke RoboAPI contract, integration needs an explicit action conversion:

```text
RoboAPI output (T, 8)
    [x, y, z, qx, qy, qz, qw, gripper]
                    ↓ IK / OSC / controller
Uranus input qpos[t:t+4]
```

Every turn also needs:

- four qpos values aligned with the four generated RGB frames;
- per-frame camera intrinsics and extrinsics;
- reference RGB, MJCF/URDF and the task instruction;
- the RoboAPI session, turn and tool feedback;
- an eight-value API state. Construct it from the commanded target, qpos and forward kinematics; do not claim that Uranus reliably recovers object state from RGB;
- task-specific `done` and `success` predicates. Uranus emits neither.

## Initial task candidates

These are pilot candidates, not tasks already opened or qualified for Uranus.

| Tier | Tasks | Main checks |
| --- | --- | --- |
| Interface smoke | `reach_cube`, `move_above_object` | action conversion, four-frame timing, session state |
| Basic rigid body | `pick_cube_to_basket`, `lift_pot` | grasp, lift, object state |
| Contact and displacement | `move_can_to_pot`, `push_box_to_target` | push direction, slip, stopping |
| Target placement | `put_bottles_dustbin`, `place_object_basket` | target region and post-release stability |
| Precision | `hanging_mug`, opening a drawer | alignment, articulated object, sustained contact |
| Stress tests | sponge wiping, cloth grasp | deformation and contact; diagnostic only before scoring |

The first version should not use cutting, fluids or high-precision insertion to claim that Uranus is a general physics simulator. The paper itself identifies contact, object-state transitions and long-horizon error as open gaps.

## How to evaluate an API

For every task, freeze scene, initial state, robot configuration, cameras, seeds, action rate and episode budget. Run both:

1. **Native reference backend:** a qualified MuJoCo, SuperDex, Newton, Genesis or similar configuration;
2. **Uranus candidate backend:** same initial observation, instruction and policy interface, with actions mapped through IK into qpos;
3. **Independent scorer:** a task-state or calibrated visual predicate that the model under test cannot read;
4. **Complete attempts:** retain interface errors, timeouts, invalid actions and visual/physical invalid runs separately.

With one API, do not calculate cross-model Pearson or MMRV. Report:

- `success_native`, `success_uranus` and Wilson intervals per task;
- paired-episode outcome accuracy;
- false-success and false-failure counts and cases;
- mean success-rate difference with bootstrap intervals;
- whether failures concentrate in grasp, retention, slip, placement, visual drift or the interface.

With multiple APIs, add success-rate correlation and ranking agreement while retaining the per-task matrix. Uranus visual-quality metrics are secondary and cannot replace task outcomes.

## What the paper reports

- Against GE-Sim 2.0 on 100 AgiBot G1 samples, the final 140–160 second head view is about `12.3 PSNR / 0.45 SSIM`, versus `7.1 / 0.20`;
- the WorldOlympiad robotics setting reaches Overall `0.722` and Interaction `0.730`, but 3D Consistency is `0.511`;
- five RoboTwin tasks and nine policies reach Pearson `0.98` and MMRV `0.01` for closed-loop success-rate correlation;
- human-rated real-world consistency on the held-out test split is `58%`, so visual continuity can still hide incorrect interaction outcomes.

These results justify further study of Uranus as a visual environment backend. They do not establish that it supplies native physical truth. The RoboTwin study also used task-domain fine-tuning and 7,891 failed trajectories.

## Current limits

- the public repository provides inference and an SDK, but not the complete training, data or serving stack;
- the paper's single-session example is about `535 ms/latent` for four frames; the `24 FPS` headline lacks a measurement definition in the main text;
- the model does not integrate torques or velocities or explicitly solve contact, friction and task state;
- multi-view synchronization and visual stability do not establish physical-state correctness;
- there is no built-in reward, termination, success or contact readback;
- DexLab currently has no Uranus adapter, runner, container, cohort or official score.

## What is still required

1. Define stable `reset`, `step`, `observe` and `close` backend interfaces;
2. provide an independent 8D EE action-to-qpos conversion for at least one UR5/Robotiq-style task;
3. freeze the same initial state and task protocol across native and Uranus backends;
4. implement and calibrate the task success predicate;
5. finish a pilot before moving the status from `documented candidate` to `local / unverified`.

Until then, the README and leaderboard must not call Uranus a verified backend or relabel paper metrics as DexLab scores.

## Upstream start

Standalone inference currently requires a separate download of about 17.5 GB of weights; it is not a dependency of the DexLab documentation environment.

```bash
git clone https://github.com/D-Robotics-AI-Lab/Uranus-OSS.git
cd Uranus-OSS
uv sync
uv run python main.py \
  --weights-dir /path/to/uranus-weights \
  --sample-dir /path/to/sample \
  --output-dir /path/to/output
```

This validates the upstream inference entry, not DexLab backend integration.
