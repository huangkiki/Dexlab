# Upstream task cards and selection rationale

[English](upstream.md) | [简体中文](upstream.zh-CN.md)

**Ten task cards from eight pinned repositories; all are source reviews, with no claim of installation, execution or reproduction this round.** [Source manifest](upstream-sources.json) records the 41 files read on 2026-09-30, full commits, URLs and SHA-256. No upstream source/assets are redistributed. Entry points are upstream commands/registered classes; dependencies, weights and assets are unqualified, not a tested one-command installation.

Cards follow the existing research-note separation of task/contact mode, embodiment/drives, physics, sensing, policy/data and hardware calibration. They evaluate usefulness to DexLab experiment design, separating upstream capability from delivered DexLab behavior. Cost is **unmeasured** for every card; source-license labels do not cover third-party assets.

## U1 — DexGraspBench: grasp, hold and perturbation

[JYChen18/DexGraspBench@d9ea6cf282de](https://github.com/JYChen18/DexGraspBench/tree/d9ea6cf282de1f463c20fa54b4f68d7025bad40e) · [eval.yaml](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/config/task/eval.yaml); [tabletop_mocap.py](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/src/task/eval_func/tabletop_mocap.py); [fc_mocap.py](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/src/task/eval_func/fc_mocap.py); [example.sh](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/script/example.sh)

**Entry and prerequisites:** `bash script/example.sh`; requires upstream hand/object assets.

**Model / control / observations:** MuJoCo; pregrasp → grasp → squeeze → 0.1 m lift. Candidate poses and mocap hand motion are explicit priors. Current mass 0.1 kg and friction 0.6/0.02 differ from the paper baseline branch.

**Success definition, gaps and use:** Initial penetration and post-perturbation translation/rotation checks; force-closure metrics are separate from dynamics. Mocap does not validate a complete arm drive. Reuse negative controls and load tests, not thresholds as material-accuracy standards.

**License snapshot:** No standalone root LICENSE identified in this tree.

## U2 — IsaacLab: Allegro in-hand reorientation

[isaac-sim/IsaacLab@9c572e483959](https://github.com/isaac-sim/IsaacLab/tree/9c572e48395943279f78dfbc81eb19b92d37487c) · [__init__.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/__init__.py); [allegro_hand_direct_env_cfg.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/allegro_hand_direct_env_cfg.py); [allegro_hand_common.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/allegro_hand_common.py); [reorient_direct_env.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/reorient_direct_env.py)

**Entry and prerequisites:** Registered entry `Isaac-Reorient-Cube-Allegro-Direct`; upstream training launcher and robot assets require separate installation.

**Model / control / observations:** Cube in hand and orientation goal; 16 actions, 124 full-state observations, 10 s episodes, dt=1/120 s; joint targets and object/goal state, not image-only input. This pin declares PhysX and Newton/MJWarp presets, so older PhysX-only descriptions do not apply.

**Success definition, gaps and use:** Orientation tolerance 0.2 rad and task reward/reset criteria are not independent contact-validity certificates. Candidate for contact switching/rolling; needs separate penetration, load and material-slip scoring. Not implemented in DexLab.

**License snapshot:** BSD-3-Clause (source).

## U3 — IsaacLab Factory: precision assembly

[isaac-sim/IsaacLab@9c572e483959](https://github.com/isaac-sim/IsaacLab/tree/9c572e48395943279f78dfbc81eb19b92d37487c) · [__init__.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/__init__.py); [factory_env.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/factory_env.py); [factory_tasks_cfg.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/factory_tasks_cfg.py)

**Entry and prerequisites:** Registered entries `IsaacContrib-Factory-PegInsert-Direct`, `...-GearMesh-Direct`, `...-NutThread-Direct`.

**Model / control / observations:** Franka with fixed/held assets; PhysX-specific configuration; pose increments through task-space control, distinct actor/critic state. Task configurations specify mass, friction and contact offsets.

**Success definition, gaps and use:** Success checks xy distance <2.5 mm and relative height, optionally rotation for threading. This alone does not establish wall separation or reasonable forces. Reuse tolerance/jamming controls first; FORGE randomization was not separately traced in this audit.

**License snapshot:** BSD-3-Clause (source).

## U4 — ManiSkill: cube pushing

[haosulab/ManiSkill@62ff3a5896b4](https://github.com/haosulab/ManiSkill/tree/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3) · [push_cube.py](https://github.com/haosulab/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/push_cube.py)

**Entry and prerequisites:** Registered entry `PushCube-v1`; SAPIEN/PhysX and upstream robot control modes.

**Model / control / observations:** Tabletop cube and target region; robot state and optional vision, with extra object/goal truth in state mode; action semantics depend on selected control mode.

**Success definition, gaps and use:** Success is xy inside the goal radius and z<cube half-size+5 mm; no independent friction identification. Connect to R1 sliding for push-force/displacement tests, with added physical scoring.

**License snapshot:** Apache-2.0 (source).

## U5 — ManiSkill: drawer opening

[haosulab/ManiSkill@62ff3a5896b4](https://github.com/haosulab/ManiSkill/tree/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3) · [open_cabinet_drawer.py](https://github.com/haosulab/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/mobile_manipulation/open_cabinet_drawer.py)

**Entry and prerequisites:** Registered entry `OpenCabinetDrawer-v1`; requires PartNet-Mobility assets.

**Model / control / observations:** Random cabinet and movable link; robot actions depend on control mode; cabinet joint and handle state are read. Engine constraints and asset friction are not a measured slide rail.

**Success definition, gaps and use:** Target opening plus handle angular speed≤1 rad/s and linear speed≤0.1 m/s. Completion does not constrain force/penetration throughout; candidate for joint/contact transfer, with no DexLab entry yet.

**License snapshot:** Apache-2.0 (source).

## U6 — DexMimicGen: bimanual tray

[NVlabs/dexmimicgen@940e8a1b3ad7](https://github.com/NVlabs/dexmimicgen/tree/940e8a1b3ad70eb1925ada6b364b197de6bb2af9) · [README.md](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md); [environments.md](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/environments.md); [two_arm_lift_tray.py](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/dexmimicgen/environments/two_arm_lift_tray.py)

**Entry and prerequisites:** `TwoArmLiftTray` environment class; README provides `scripts/demo_random_action.py --env ...` launcher.

**Model / control / observations:** robosuite / MuJoCo; two arms, tray and two payload objects; optional camera observations, controller-dependent actions. Demonstration/data generation capability does not imply a trained DexLab policy.

**Success definition, gaps and use:** Actual `_check_success` requires tray and both objects >0.1 m above the table, with both contacting its base. Reward tilt weighting is not the same success condition. Reuse the load-sharing task with added support/stability measurements.

**License snapshot:** NVIDIA Source Code License; LICENSE §3.3 limits use to research/evaluation; data terms are separate.

## U7 — DexGarmentLab: folding and garment contact

[wayrise/DexGarmentLab@e4e298e696ba](https://github.com/wayrise/DexGarmentLab/tree/e4e298e696bae5d866ded3b31e0ae27becea5376) · [README.md](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md); [Fold_Tops_Env.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_StandAlone/Fold_Tops_Env.py); [Particle_Garment.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_Config/Garment/Particle_Garment.py); [Deformable_Garment.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_Config/Garment/Deformable_Garment.py)

**Entry and prerequisites:** `isaac Env_StandAlone/Fold_Tops_Env.py` (`isaac` is upstream’s Isaac Sim 4.5 Python alias); garment assets/models download separately.

**Model / control / observations:** Bimanual UR10e dexterous manipulation. The inspected FoldTops instantiates Particle_Garment, not the repository’s Deformable_Garment; point-cloud manipulation points drive end-effector targets and hand-state commands.

**Success definition, gaps and use:** Code uses `judge_pcd(..., threshold=0.12)` for the final state and sets gravity_scale to 10 during some settling stages, then restores 1. The full grasp/attachment chain was not qualified; do not claim natural frictional holding throughout. Reuse task decomposition after C1/C2 physical checks.

**License snapshot:** No standalone root LICENSE identified in this tree.

## U8 — DexScrew: tool-rotation prior

[x-robotics-lab/dexscrew@3bde4e3a4d97](https://github.com/x-robotics-lab/dexscrew/tree/3bde4e3a4d973743921c75719ca88167de144e83) · [README.md](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md); [XHandHoraScrewDriver.yaml](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/configs/task/XHandHoraScrewDriver.yaml); [xhand_hora.py](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/dexscrew/tasks/xhand_hora.py)

**Entry and prerequisites:** `scripts/screwdriver_teacher.sh 0 42 output_name` (upstream training); no DexLab entry.

**Model / control / observations:** IsaacGym/PhysX; XHand with 12 actions, dt=5 ms; privileged teacher → proprioceptive student → real demonstrations with tactile fine-tuning are separate stages. Configuration randomizes mass/friction/scale.

**Success definition, gaps and use:** Rotation policy/reward alone does not establish thread engagement, axial advancement or calibrated torque. Later candidate for rolling/tool use; real torque and coupled geometry need separate definitions. Training/hardware results were not reproduced.

**License snapshot:** MIT (source).

## U9 — Taccel: tactile soft contact

[Taccel-Simulator/Taccel@cb23bc251b53](https://github.com/Taccel-Simulator/Taccel/tree/cb23bc251b531ba6908a3788c2f91423cd543149) · [README.md](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md); [peg.py](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/examples/peg.py)

**Entry and prerequisites:** `python examples/peg.py` (requires upstream Taccel/Warp IPC and meshes); no DexLab adapter.

**Model / control / observations:** `ASRModel` + `IPCIntegrator` GPU path; soft sensors follow interpolated kinematic targets, hole is affine kinematic. Example exports meshes and step timings.

**Success definition, gaps and use:** The inspected peg script has no independent grasp-success scorer; kinematic boundaries are not full robot actuation. Candidate for soft-pad contact research, not evidence of equivalence or drop-in replacement for current rigid SDF tasks.

**License snapshot:** MIT (source).

## U10 — HydroShear: tactile observation model

[MMintLab/hydroshear@f815b82fdf34](https://github.com/MMintLab/hydroshear/tree/f815b82fdf3451852acd918933020a82cede1f3b) · [README.md](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md); [training.md](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/training.md); [vec_task.py](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/rl/tasks/base/vec_task.py); [hydrosoft.py](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/rl/demo_utils/hydrosoft.py); [hydroshear.yaml](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/configs/sensor/hydroshear.yaml)

**Entry and prerequisites:** Upstream `scripts/experiments/hydroshear/play_hydroshear.py --ckpt_path CHECKPOINT`; prepare weights and IsaacGym separately.

**Model / control / observations:** IsaacGym RL loop and SDF/history-driven HydroSoft sensor model are different layers; code computes normal/tangential fields and tactile marker displacement.

**Success definition, gaps and use:** Sensor and base stepping interfaces were read; force-feedback coupling across every task was not established. Better tactile observations do not establish better rigid contact solving. Sensor accuracy needs measured tactile references; not integrated into DexLab.

**License snapshot:** MIT (source).

## Consequences for benchmark design

1. Retain sliding, controlled indentation and hold/overload/release first: they separate friction, normal response and drive errors. Apple grasp is one transfer task.
2. Establish observable cloth extension, sag and collision before repairing robot cloth grasp; a correct final fold cannot cancel penetration during manipulation.
3. In-hand reorientation, assembly and bimanual cooperation add contact switching and coupled constraints. Select minimal representatives after defining common evidence.
4. Tools and touch need explicit observation/coupling assumptions; missing measurements remain unknown. Upstream task rewards stay separate from independent physical acceptance.

These are selection recommendations, not additional authorized implementation scope. Metrics work is [#31](https://github.com/huangkiki/Dexlab/issues/31); hardware measurement protocol is [#33](https://github.com/huangkiki/Dexlab/issues/33). [Inventory](README.md)
