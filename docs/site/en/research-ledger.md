# Dexterous manipulation evidence ledger

**Decisions:** prioritize native ManiSkill integration (#47) and independent in-hand rotation scoring (#48). Reuse evaluation and input-audit protocols from other methods; defer unqualified runtimes, custom engine forks and hardware-dependent training. Two optional, budgeted follow-ups cover [action replay (#52)](https://github.com/huangkiki/Dexlab/issues/52) and [synthetic tactile history (#53)](https://github.com/huangkiki/Dexlab/issues/53). Neither precedes core contact/cloth repair.



On 2026-10-05, refreshed **38 historical paper abstract pages and19 repository entrypoints**. This is not38 full method reviews or19 reproductions. Unknown source, drive, observation and asset-license fields remain explicit in the [paper ledger](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-papers.json) and [repository ledger](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-sources.json).

## Paper revisions and review depth

The table lists paper identities. Selected method/source audits and abstract-only defer decisions are distinguished below. Unresolved implementation and asset fields block adoption, not the recording of a research decision.

| 论文 / Paper | 版本 / Revision | 更新日期 / Revision date |
|---|---|---|
| [ManiSkill3: GPU Parallelized Robotics Simulation and Rendering for Generalizable Embodied AI](https://arxiv.org/abs/2410.00425v2) | v2 | 2025/05/30 |
| [DexGraspNet 2.0: Learning Generative Dexterous Grasping in Large-scale Synthetic Cluttered Scenes](https://arxiv.org/abs/2410.23004v1) | v1 | 2024/10/30 |
| [DexMimicGen: Automated Data Generation for Bimanual Dexterous Manipulation via Imitation Learning](https://arxiv.org/abs/2410.24185v2) | v2 | 2025/03/06 |
| [TacEx: GelSight Tactile Simulation in Isaac Sim -- Combining Soft-Body and Visuotactile Simulators](https://arxiv.org/abs/2411.04776v1) | v1 | 2024/11/07 |
| [Sampling-Based Model Predictive Control for Dexterous Manipulation on a Biomimetic Tendon-Driven Hand](https://arxiv.org/abs/2411.06183v3) | v3 | 2025/08/04 |
| [BODex: Scalable and Efficient Robotic Dexterous Grasp Synthesis Using Bilevel Optimization](https://arxiv.org/abs/2412.16490v3) | v3 | 2025/09/03 |
| [MuJoCo Playground](https://arxiv.org/abs/2502.08844v1) | v1 | 2025/02/12 |
| [Sim-to-Real Reinforcement Learning for Vision-Based Dexterous Manipulation on Humanoids](https://arxiv.org/abs/2502.20396v2) | v2 | 2025/09/01 |
| [ManipTrans: Efficient Dexterous Bimanual Manipulation Transfer via Residual Learning](https://arxiv.org/abs/2503.21860v1) | v1 | 2025/03/27 |
| [Taccel: Scaling Up Vision-based Tactile Robotics via High-performance GPU Simulation](https://arxiv.org/abs/2504.12908v2) | v2 | 2025/09/12 |
| [Dexonomy: Synthesizing All Dexterous Grasp Types in a Grasp Taxonomy](https://arxiv.org/abs/2504.18829v2) | v2 | 2025/09/03 |
| [A Survey of Robotic Navigation and Manipulation with Physics Simulators in the Era of Embodied AI](https://arxiv.org/abs/2505.01458v2) | v2 | 2026/06/09 |
| [DexGarmentLab: Dexterous Garment Manipulation Environment with Generalizable Policy](https://arxiv.org/abs/2505.11032v3) | v3 | 2025/10/12 |
| [TeleOpBench: A Simulator-Centric Benchmark for Dual-Arm Dexterous Teleoperation](https://arxiv.org/abs/2505.12748v2) | v2 | 2025/09/15 |
| [DexMachina: Functional Retargeting for Bimanual Dexterous Manipulation](https://arxiv.org/abs/2505.24853v1) | v1 | 2025/05/30 |
| [Dex1B: Learning with 1B Demonstrations for Dexterous Manipulation](https://arxiv.org/abs/2506.17198v1) | v1 | 2025/06/20 |
| [HumanoidGen: Data Generation for Bimanual Dexterous Manipulation via LLM Reasoning](https://arxiv.org/abs/2507.00833v2) | v2 | 2025/11/16 |
| [In-Hand Manipulation of Articulated Tools with Dexterous Robot Hands with Sim-to-Real Transfer](https://arxiv.org/abs/2509.23075v3) | v3 | 2026/03/05 |
| [SPIDER: Scalable Physics-Informed Dexterous Retargeting](https://arxiv.org/abs/2511.09484v3) | v3 | 2026/09/26 |
| [Learning Dexterous Manipulation Skills from Imperfect Simulations](https://arxiv.org/abs/2512.02011v2) | v2 | 2026/02/25 |
| [Dexterous Manipulation Policies from RGB Human Videos via 3D Hand-Object Trajectory Reconstruction](https://arxiv.org/abs/2602.09013v2) | v2 | 2026/02/11 |
| [FlowHOI: Flow-based Semantics-Grounded Generation of Hand-Object Interactions for Dexterous Robot Manipulation](https://arxiv.org/abs/2602.13444v1) | v1 | 2026/02/13 |
| [Dex4D: Task-Agnostic Point Track Policy for Sim-to-Real Dexterous Manipulation](https://arxiv.org/abs/2602.15828v1) | v1 | 2026/02/17 |
| [Grasp to Act: Dexterous Grasping for Tool Use in Dynamic Settings](https://arxiv.org/abs/2602.20466v1) | v1 | 2026/02/24 |
| [Tacmap: Bridging the Tactile Sim-to-Real Gap via Geometry-Consistent Penetration Depth Map](https://arxiv.org/abs/2602.21625v2) | v2 | 2026/05/12 |
| [HydroShear: Hydroelastic Shear Simulation for Tactile Sim-to-Real Reinforcement Learning](https://arxiv.org/abs/2603.00446v1) | v1 | 2026/02/28 |
| [Structural Action Transformer for 3D Dexterous Manipulation](https://arxiv.org/abs/2603.03960v1) | v1 | 2026/03/04 |
| [PTLD: Sim-to-real Privileged Tactile Latent Distillation for Dexterous Manipulation](https://arxiv.org/abs/2603.04531v3) | v3 | 2026/06/18 |
| [UltraDexGrasp: Learning Universal Dexterous Grasping for Bimanual Robots with Synthetic Data](https://arxiv.org/abs/2603.05312v1) | v1 | 2026/03/05 |
| [Grounding Sim-to-Real Generalization in Robotic Manipulation: An Empirical Study with Vision-Language-Action Models](https://arxiv.org/abs/2603.22876v2) | v2 | 2026/06/29 |
| [Blind Dexterous Grasping via Real2Sim2Real Tactile Policy Learning](https://arxiv.org/abs/2606.11767v2) | v2 | 2026/06/11 |
| [Labimus: A Simulation and Benchmark for Humanoid Dexterous Manipulation in Chemical Laboratory](https://arxiv.org/abs/2606.31037v2) | v2 | 2026/07/01 |
| [Learning Dexterous Manipulation Using Contact Wrench Guidance From Human Demonstration](https://arxiv.org/abs/2607.00033v2) | v2 | 2026/08/14 |
| [TouchWorld: A Predictive and Reactive Tactile Foundation Model for Dexterous Manipulation](https://arxiv.org/abs/2607.07287v2) | v2 | 2026/07/09 |
| [LabDex: A Hierarchical Benchmark for Dexterous Manipulation in Laboratories](https://arxiv.org/abs/2608.18618v1) | v1 | 2026/08/19 |
| [Does Imitation Learning Preserve Temporal Robustness in Dexterous Manipulation? An Expert-Learner Comparison Across Task Execution Speeds](https://arxiv.org/abs/2609.01453v1) | v1 | 2026/09/01 |
| [Morphology and actuation as inductive biases in robotic hand manipulation](https://arxiv.org/abs/2609.05206v1) | v1 | 2026/09/04 |
| [Dex-X: Learning Visual-Tactile Dexterous Manipulation From Human Videos with Simulated Interaction](https://arxiv.org/abs/2609.07747v3) | v3 | 2026/10/01 |

## Repository and license evidence

A pinned SHA identifies a source entrypoint, not a paper-matched runnable release. License metadata does not grant asset redistribution rights; absence of a root license does not exclude terms elsewhere.

| 仓库 / Repository | 固定源码 / Source | 审查 / Review |
|---|---|---|
| mani-skill/ManiSkill | [62ff3a5896](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/README.md) | README / metadata |
| JYChen18/BODex | [06b9a3c908](https://github.com/JYChen18/BODex/blob/06b9a3c90870d33bde9d6c665d4ed2819471407e/README.md) | README / metadata |
| JYChen18/DexGraspBench | [d9ea6cf282](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | README / metadata |
| NVlabs/dexmimicgen | [940e8a1b3a](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md) | README / metadata |
| MandiZhao/dexmachina | [adae5bf620](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md) | README / metadata |
| Taccel-Simulator/Taccel | [cb23bc251b](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md) | README / metadata |
| MMintLab/hydroshear | [f815b82fdf](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md) | README / metadata |
| DH-Ng/TacEx | [adceed41af](https://github.com/DH-Ng/TacEx/blob/adceed41afb7cb48f9ec1f66a662fb8e5a06627f/README.md) | README / metadata |
| wayrise/DexGarmentLab | [e4e298e696](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md) | README / metadata |
| x-robotics-lab/dexscrew | [3bde4e3a4d](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md) | README / metadata |
| Genesis-Embodied-AI/genesis-world | [02908fe647](https://github.com/Genesis-Embodied-AI/genesis-world/blob/02908fe6474d8b073b662347a8794614fa250658/README.md) | README / metadata |
| InternRobotics/UltraDexGrasp | [e0f9784a9b](https://github.com/InternRobotics/UltraDexGrasp/blob/e0f9784a9bf3030995b635c21ef8621ca3477ea8/README.md) | README / metadata |
| cyjdlhy/TeleOpBench | [4cc410d149](https://github.com/cyjdlhy/TeleOpBench/blob/4cc410d149ce63c86f485b257cba3b3e0ec031d6/README.md) | README / metadata |
| dexx-code/dexx-code | [88728c83c9](https://github.com/dexx-code/dexx-code/blob/88728c83c983b623ed1da0e2a203dc983fd8866b/README.md) | README / metadata |
| facebookresearch/project_superdex | [1d7150946f](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/README.md) | README / metadata |
| google-deepmind/mujoco | [07dfe91655](https://github.com/google-deepmind/mujoco/blob/07dfe91655630418a39bf863e454b0ad9fb8fbc0/README.md) | README / metadata |
| google-deepmind/mujoco_playground | [ef4fefc130](https://github.com/google-deepmind/mujoco_playground/blob/ef4fefc13033c0468af4ef651847f5348af0c7d7/README.md) | README / metadata |
| isaac-sim/IsaacLab | [a710e671a2](https://github.com/isaac-sim/IsaacLab/blob/a710e671a2a28492ebdbc433972190b7d7730670/README.md) | README / metadata |
| newton-physics/newton | [009158e62b](https://github.com/newton-physics/newton/blob/009158e62b862b3b9d829397d6db583515ae1271/README.md) | README / metadata |

## Remaining work

#46 remains open until this research delivery passes review and release. Runtime adoption still requires each record’s unresolved solver, source and asset checks. #47/#48 remain unimplemented.

## ManiSkill source audit: upstream success is not physical acceptance

Pinned source: `62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3`. Static inspection only; no new task is running yet. ManiSkill1 [v5](https://arxiv.org/abs/2107.14483v5) emphasizes object generalization; ManiSkill2 [v1](https://arxiv.org/abs/2302.04659v1) extends task/controller diversity. Neither makes current MS3 assets or solvers paper-matched by default.

- [PickCube](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/pick_cube.py): goal proximity plus robot static defines success. Hold/release and physical support need separate scoring. Non-state extra observations still include grasp status and goal position; RGB selection alone does not prove vision-only input.
- [PushCube](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/push_cube.py): planar proximity and an upper height bound are insufficient to reject below-table penetration. Add that explicit negative.
- [Rotation](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/dexterity/rotate_single_object_in_hand.py): registered Level0–3 use AllegroHandRightTouch. Angle accumulation is unsigned. A mathematical128-step oscillation crosses4π with zero net rotation; this is a formula counterexample, not an executed physics exploit. Score signed palm-relative progress, drops and contact transitions independently. Report its clipped PD effort estimate separately from measured torque.
- [Hand controller](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/agents/robots/allegro_hand/allegro.py): PD position/delta targets differ from actual joint state. [Touch observations](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/agents/robots/allegro_hand/allegro_touch.py) expose contact impulse magnitudes; they are not calibrated tactile images. Audit all observation keys.

[Source audit](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/maniskill-task-audit.json) · [Algebraic negative](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/maniskill-angle-counterexample.json). #47/#48 must retain upstream success alongside independent scoring, and test reset isolation. Installed solver identity and asset terms remain qualification requirements.

## Synthesis, retargeting and data: reuse decisions

The [method ledger](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-method-decisions.json) records the candidates, source locators, unknowns and proposed budgets. None has been reproduced here.

| Method | Verified boundary | Reuse and falsifiable probe |
|---|---|---|
| Dexonomy | Historical MuJoCo3.3.3; six-axis loads differ from final-pose checks. Default5cm/15deg is not DexLab acceptance. The hard-mode comment conflicts with execution: noslip2/impratio10 remain; friction decreases. | Reuse grasp taxonomy/loading protocol; compare3 grasp types with fixed object/hand/loads and record directional failures plus effective parameters. |
| Dex1B | Scale does not establish executable trajectories or contact coverage; implementation/solver/asset audit pending. | Defer bulk data; count generated, executable and independently valid samples, retaining rejected cases. |
| SPIDER | Pinned README distinguishes saved-state replay from control-replay equivalence; code/data terms separate. | Reuse replay audit: compare free dynamics under fixed actions against pose playback; prohibit object state injection during scoring. |
| CHORD | AppendixB includes object/contact observations and internal object assistance; whole-body observations differ. Reset warm-up matters even when assistance has zero policy-action dimensions. | Reuse wrench/assistance logging; record every phase and exclude undisclosed assistance from independent acceptance. |

Protocol research only: no training or bulk assets. Proposed probes are capped at10 cases, one qualified worker and30min; stop for missing provenance or failed physical scoring. Add separate executable Issues/dependencies before running optional expansions.

## Tactile models are not interchangeable physics backends

| Work / inspected revision | Reuse boundary | Minimal disproof test |
|---|---|---|
| [HydroShear v1](https://arxiv.org/html/2603.00446v1) | Path-dependent shear observation, flat elastomer and compliant-contact assumptions; teacher/student inputs differ. | Same pose through different paths and detach/recontact: check history/reset independently from rigid dynamics. |
| [Tacmap v2](https://arxiv.org/html/2602.21625v2) | Geometric tactile map; sensing geometry is distinct from physical collision geometry. | Vary sensing resolution only; compare map error and net force separately. |
| [PTLD v3](https://arxiv.org/html/2603.04531v3) | Requires privileged real-world data collection before tactile deployment; not zero-data transfer. | Audit teacher/critic/collector/actor input keys; remove prohibited pose information from deployment replay. |
| [TacEx v1](https://arxiv.org/html/2411.04776v1) | Gel physics, optical rendering and marker synthesis are separate modules; historical slipping observations do not indict current PhysX. | Compare force/deformation and optical signals under the same imposed trajectory. |
| [Taccel v2](https://arxiv.org/html/2504.12908v2) | ABD/FEM IPC and kinematic constraints require separate contact and actuation qualification. | Fixed-mesh indentation/shear/unload; record residuals, force, penetration and stage costs. |

A restricted independently implemented geometric occupancy observer now has [three bounded experimental batches](https://github.com/huangkiki/Dexlab/blob/main/docs/synthetic-tactile.md). This does not adopt or qualify upstream tactile runtimes, shear memory or hardware precision. Upstream input/solver/licensing boundaries remain in the [method ledger](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-method-decisions.json).

## Grasp evaluation and bimanual generation

| Method | Evidence boundary | Decision and falsifiable probe |
|---|---|---|
| [BODex v3](https://arxiv.org/html/2412.16490v3) | Paper gravity-hold limits are5cm/15deg above3s; geometric penetration and synthesis speed are distinct metrics. | Reuse loading protocol, retain DexLab thresholds; compare identical grasps under frozen physical parameters. |
| [DexGraspBench source](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | README changes mass30g→100g and kp1→5 relative to BODex. | Record both configurations; isolate mass and drive effects before comparing methods. |
| [DexMimicGen v2](https://arxiv.org/html/2410.24185v2) | Transformed segments execute open-loop; only successful complete episodes enter the generated dataset. | Preserve attempted, executed and retained counts; score failed trajectories too. |
| [DexMachina source](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md) and [paper](https://arxiv.org/html/2505.24853v1) | Installation requires custom Genesis/rl-games forks; training uses decaying virtual object assistance. | Defer direct runtime adoption; reuse assistance logging, with zero auxiliary wrench during independent evaluation. |

These are research decisions, not newly supported tasks. Official stable-engine qualification, executable-source review and asset permissions remain prerequisites. Optional probes retain the10-case/30-minute cap; no training has started.

## Cloth and tool use: what successful videos do not establish

[DexGarmentLab v3](https://arxiv.org/html/2505.11032v3) uses particle PBD and adhesion/friction tuning. Its lack of attachment blocks does not establish friction-only grasping; AppendixI still discusses particle gaps, penetration and jitter. Reuse the task taxonomy, but test adhesion separately: fixed mesh/drive, independently varied adhesion/friction, open-hand release and residual attraction. The pinned README targets IsaacSim4.5.0, not our latest-stable qualification.

[DexScrew v2](https://arxiv.org/html/2512.02011v2) separates a privileged simulation oracle, proprioceptive student, real teleoperation and tactile behavior cloning. This is the paper linked by the repository, not the separate articulated-tools paper. Reuse stage-specific input audits and separate signed rotation, axial progress and full completion. Defer hardware reproduction until real data is available; progress ratio must not be relabeled task success.

Both remain reference-only, with asset and runtime qualification pending. No cloth or tool training has been run for this audit.

## Embodiment and actuation

[Tendon-hand MPC v3](https://arxiv.org/html/2411.06183v3) distinguishes joint targets, tendon commands and estimated joint state. Its VLM tunes objective weights from video while MPC uses measured object state; this is not direct RGB-only control. Reuse that interface audit and test estimation delay and actuator limits separately, recording deadline misses as well as retention.

[The morphology study v1](https://arxiv.org/html/2609.05206v1) separates kinematics, actuation and their composition. It reports historical MuJoCo3.10.0; its ACBH model and experiment code are available on request, so a full public reproduction is not established. Reuse finite-difference checks of actuator-to-joint and joint-to-tip maps on already licensed models. Structural conditioning cannot substitute for dynamic task acceptance.

Both remain protocol references. Exact source, asset permissions and independent runtime evidence are unresolved; no additional hand model or training is introduced.

## Precision, composition and point-based policies

- [Labimus v2](https://arxiv.org/html/2606.31037v2): reuse separate completion, precision and stage diagnostics. Its dry-powder approximation uses rigid micro-elements; this does not qualify our granular physics. Test a completed but out-of-tolerance negative in an existing task.
- [LabDex v1](https://arxiv.org/html/2608.18618v1): reuse atomic/compositional boundaries and action/state provenance. Shared real/sim task labels do not prove matched dynamics; exact solver remains unverified. Test a two-stage episode whose second stage fails.
- [Dex4D v1](https://arxiv.org/html/2602.15828v1): teacher/full geometry and student/partial paired-point inputs differ. Reuse visibility auditing, not a raw-RGB claim. Test target loss without ground-truth replacement.

All three remain reference-only; proposed probes use existing assets with the same10-case/30-minute cap. Full laboratory, granular and policy-training adoption is deferred.

## Remaining candidates: screened, not reproduced

These entries were screened from pinned abstracts only. They remain references or deferred implementations; the probes are our proposals, not reported experimental results. Detailed unknowns are retained in the method ledger.

| Candidate / 候选 | Decision / 决策 |
|---|---|
| [MuJoCo Playground](https://arxiv.org/abs/2502.08844v1) | reference runtime design; defer another task integration until ManiSkill qualification |
| [Physics simulator survey](https://arxiv.org/abs/2505.01458v2) | reference taxonomy only; not an engine qualification source |
| [TeleOpBench](https://arxiv.org/abs/2505.12748v2) | reuse operator/interface timing protocol; defer complete benchmark |
| [HumanoidGen](https://arxiv.org/abs/2507.00833v2) | reuse explicit annotation provenance; defer generation stack |
| [Articulated-tool refinement](https://arxiv.org/abs/2509.23075v3) | reuse articulation sensitivity protocol; defer hardware-dependent learning |
| [VIDEOMANIP](https://arxiv.org/abs/2602.09013v2) | reuse reconstruction-versus-execution audit; defer training |
| [FlowHOI](https://arxiv.org/abs/2602.13444v1) | reference HOI representation; defer generative pipeline |
| [Grasp-to-Act](https://arxiv.org/abs/2602.20466v1) | reuse dynamic-load retention protocol; defer learned controller |
| [Structural Action Transformer](https://arxiv.org/abs/2603.03960v1) | reference joint-role representation; defer policy training |
| [UltraDexGrasp](https://arxiv.org/abs/2603.05312v1) | reuse grasp-strategy grouping; defer bulk dataset |
| [Sim-to-real generalization study](https://arxiv.org/abs/2603.22876v2) | reuse factorial calibration design; defer hardware ranking |
| [Blind tactile grasping](https://arxiv.org/abs/2606.11767v2) | reuse contact-event calibration protocol; defer absent hardware data |
| [TouchWorld](https://arxiv.org/abs/2607.07287v2) | reference separate planning/feedback clocks; defer foundation-model stack |
| [Temporal robustness study](https://arxiv.org/abs/2609.01453v1) | reuse speed-conditioned paired evaluation; defer training |
| [Dex-X](https://arxiv.org/abs/2609.07747v3) | reference tactile-supervision provenance; defer executable adoption |

## Three selected visual/data methods

| Source | Reuse decision and boundary |
|---|---|
| [DexGraspNet2.0](https://arxiv.org/html/2410.23004v1), §3.2–3.3 | Reuse object/clutter splits and proposal accounting. Single-view depth produces a grasp pose, followed by lift evaluation; no continuous RGB-control claim. Compare collision rejection, lift and sustained hold separately. |
| [ManipTrans](https://arxiv.org/html/2503.21860v1), §3–4 | Reuse effective gravity/friction/threshold logging. Training relaxes physics and termination; freeze nominal evaluation before scoring. Defer training. |
| [Humanoid vision RL](https://arxiv.org/html/2502.20396v2), perception setup | Reuse fixed calibrated-camera and tracked-feature provenance. Head depth and third-view segmented3D features are not raw RGB-only inputs. Test occlusion without replacing lost features with simulator truth. |

These targeted paper audits do not establish source or asset clearance, installed solver versions or runtime reproduction.
