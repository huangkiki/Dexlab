# Dexterous manipulation: research into runnable tasks



**The gap is task and mechanism coverage, not only engine count.** Apple-stem holding cannot stand in for in-hand rotation, finger gaiting, handover, tool contact or deformable manipulation.

This page turns the six-layer research framework into a task roadmap. On 2026-10-05, ten official repository READMEs and commit identities were refreshed. This is source-entry review, not runtime reproduction. The earlier 38-paper/19-repository survey is historical; its remaining entries are not claimed revalidated and remain under #46. See the [source manifest](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-sources.json). Repository license metadata is a lead, not asset redistribution permission.

## Six experimental contracts

| Layer | Question | Required evidence |
|---|---|---|
| Task/contact | Hold, slide, roll, change fingers or release? | Contact phases, first success, sustained success and failure time |
| Embodiment/actuation | Did measured state execute the command? | Coupling, actual/target joints, saturation, rates, delay, wrist constraints |
| Physics | Which error changes behavior? | Intrusion, supporting force, slip onset, temporal/spatial sensitivity |
| Sensing | Which inputs exist at deployment? | Privilege audit, occlusion, noise, calibration, tactile history/reset |
| Data/policy | Does added data cover new contact strategies? | Generation/execution/validity rates, filtered failures, splits, total cost |
| Calibration/transfer | Does simulation predict real failure? | Independent measurements, fitting error, held-out objects and rankings |

## First reuse decisions

These are proposed DexLab experiments, not upstream matched comparisons or claims of implemented support.

| Work | Reuse | Falsifiable minimal experiment | Boundary | Task |
|---|---|---|---|---|
| [ManiSkill 1/2/3](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/README.md) | Task cards, generalization splits, native execution and action replay | PushCube integration → PickCube hold/release → in-hand rotation; verify reset and failure separately | MS2 MPM is not MS3 thin cloth; start with upstream robots | #47 / #48 |
| [BODex](https://github.com/JYChen18/BODex/blob/06b9a3c90870d33bde9d6c665d4ed2819471407e/README.md) | Grasp feasibility and loading protocol | Apply fixed directional loads to the same grasp and record first loss | Separate noncommercial and cuRobo terms; no mass-generation pipeline copy | #10 |
| [DexGraspBench](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | Grasp evaluation and control sensitivity | Freeze objects/grasps; compare retention under mass/gain changes | Do not mix historical baseline and main; not in-hand skill evaluation | #3 / #10 |
| [DexMachina](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md) | Embodiment and functional-retargeting design | Hold object goal fixed; vary wrist constraints and drive limits separately | Audit customized dependencies; floating-wrist results are not arm performance | #48 |
| [Taccel](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md) | Rigid-soft contact and tactile cost breakdown | Indent, shear and unload; compare net force, deformation and stage costs | Validate gel and rigid solver separately; defer primary ranking | 候选 / candidate |
| [TacEx](https://github.com/DH-Ng/TacEx/blob/adceed41afb7cb48f9ec1f66a662fb8e5a06627f/README.md) | Tactile interfaces and observation fidelity | Compare net force, geometric depth and tactile images for one trajectory | README pins older Isaac versions and preview status; reference only under stable policy | 暂缓 / deferred |
| [HydroShear](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md) | History-dependent tactile observation and reset | Compare direct arrival, slide-and-return, and detach/recontact at one final pose | Qualify observation model first; do not claim replacement rigid dynamics | 候选 / candidate |
| [DexMimicGen](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md) | Demonstration augmentation and filtering audit | Small demo batch: generation, execution, physical validity and contact coverage | Separate code/data terms; more trajectories do not prove new contact strategies | 候选 / candidate |
| [DexGarmentLab](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md) | Garment task decomposition and deformable-contact failure | Qualify single-layer grasp/release and self-contact before folding | Older Isaac dependencies are not a ready port; appearance is not nonpenetration | #28 / #32 |
| [DexScrew](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md) | Skill versus real feedback boundary | Declare pre-inserted start; record rotation progress, load and termination | Historical IsaacGym reference; progress ratio is not success rate | #6 / future tool task |

## Task support matrix

Planned/reference entries are not supported capabilities. Every implementation separately qualifies the latest stable release and actual native solver.

| Family | Current status | Next acceptance |
|---|---|---|
| Apple-stem holding | Historical native MuJoCo/SuperDex evidence | Keep candidate and historical profiles separate |
| Cloth grasp/folding | Diagnostics exist; overall physical validity unresolved | #32 collision repair; animation is not acceptance |
| ManiSkill cube push/pick | Planned; no runnable support yet | #47 native execution, recording, reset isolation and independent scoring |
| Multifinger in-hand rotation | Planned; no runnable support yet | #48 rotation, drops, contact switching and hand-only-rotation negatives |
| Insertion/tools/handover | Research candidates | Define starts, freedoms, loads and failures before implementation |
| Tactile history/data/garments | References and candidates | Qualify small probes before training or real-world claims |

## Bringing ManiSkill into code

ManiSkill 1 object generalization, ManiSkill2 task diversity and ManiSkill3 parallel task management offer different reference dimensions. Start with upstream-supported robots and native tasks; record ManiSkill, SAPIEN and actual PhysX identities. Reuse current UniLab experiment management instead of adding another scheduler.

The [official task documentation](https://maniskill.readthedocs.io/en/latest/tasks/index.html) places soft-body tasks in MS2, not fully integrated in MS3. Volumetric MPM is also not the current triangle-based thin cloth.

1. **M1 / #47:** PushCube checks integration/reset, then PickCube checks grasp, support, hold and release. Record upstream reward/success separately from independent physical scoring; unavailable contacts remain missing data.
2. **M2 / #48:** Verify the actual registered rotation environment and hand. Reproduce an available controller/trajectory first; unavailable policy is a blocker, not permission to label random actions successful. A Wuji port needs separate drive/asset qualification.
3. **Frozen evaluation:** Separate development from ten preregistered held-out cases. Retain every failure. Action replay differs from state injection; equal seeds do not prove matched initial states. Record continuous contact close-ups.

Experiments prefer a qualified local machine; remote execution remains optional. Verify enforced memory, CPU, process and runtime limits with experiment swap disabled, preserve desktop headroom, and store bulk outputs on the configured data volume. Qualify isolation on one GPU before scaling. Report preparation, stepping, rendering and end-to-end costs separately; stop transfers during timing. Missing real measurements must not block simulation integration but preclude hardware-accuracy claims.

## Remaining research review

Dexonomy, Dex1B, SPIDER, CHORD, Dex4D, Tacmap, PTLD, Dex-X, Labimus/LabDex, TeleOpBench, tendon MPC and morphology/actuation work remain historical candidates. Paper revisions, source, licenses, observations and executable entrypoints need individual checks. Preserve unavailable/incompatible entries and rejection reasons. This list is not a reproduction claim.

Before creating tactile, data and tool implementation tasks, specify fixed inputs, success/failure, budget and exit conditions. Current sequence: [#46](https://github.com/huangkiki/Dexlab/issues/46) → [#47](https://github.com/huangkiki/Dexlab/issues/47) → [#48](https://github.com/huangkiki/Dexlab/issues/48). Existing cloth/contact repair remains in scope.

## Validation and reproduction boundary

The strict bilingual site build passed. In the base `setup.sh` environment, the 309-test suite reported a PhysX contact-details import error because the optional UniSim adapter patch was absent; that failure log is retained. All 309 tests passed after installing adapter source verified byte-for-byte against the disclosed `scripts/patches/unisim-1.7.10-physx-adapter.patch`. This changes the adapter, not official physics engines. Patched-environment results are not a claim that the base installation passes the full suite. This page contains no ManiSkill runtime result.
