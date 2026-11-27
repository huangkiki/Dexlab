# RoboSimStudio: trace scene edits to contact outcomes

| At a glance | Details |
| --- | --- |
| Work | RoboSimStudio, UC Berkeley and NVIDIA, arXiv:2610.18835v2 |
| Input → output | Physical task video, a task description and available robot and object assets → an executable, editable multiphysics scene and structured rollout feedback |
| Release scope | Apache-2.0 tools and public examples, with separate terms for external dependencies. The paper's hardware pilot and the open wiping demo supply different evidence |
| Source scope | Project entry checked at `81f38a3`. The parameter code and DexLab's paired replication below are pinned to `23417de` |
| DexLab decision | Reuse replay, native readback, and independent scoring. Make the effect of a parameter change visible in the same case |

[Paper v2](https://arxiv.org/html/2610.18835v2) · [Project page](https://robosimstudio.github.io/) · [Current source reference](https://github.com/robosimstudio/robosimstudio/tree/81f38a35c385bf8dc67485a61f7d1311d434ebe5)

## What does one wiping video turn into?

One hand holds a sponge and the other holds a bar. Given a phone video, a coding agent builds a scene in which the robot can grasp and wipe while someone inspects the contact. The scene needs a sponge that can deform, a grasp that can survive a wiping load, and supports that can move if the forces overcome their constraints. These are separate properties to check. RoboSimStudio puts scene editing, direct manipulation, and rollout feedback in one loop. A person can try an action and inspect the result. An agent can read the rollout, change a modeling choice, and execute the task again. [Paper §§1 and 3](https://arxiv.org/html/2610.18835v2#S3)

![Paper Figure 2 showing assets, robot interfaces, physics solvers and both interaction paths](https://arxiv.org/html/2610.18835v2/figures/architecture3.png)

*Figure 2. The asset, physics and interaction layers meet in one scene. Evidence from a reference observation is still needed to evaluate how that scene represents a physical task.*

### What the shared scene exposes

1. **Robot and scene description.** An object defines its geometry and properties. The scene assigns its solver, collision representation and coupling. The robot interface covers Panda, UR5e, and single- or dual-arm YAM, with joint and Cartesian motion and guarded contact. The policy observation can stay separate from privileged simulator state.
2. **Solver and feedback path.** Newton composes the physics. MuJoCo-Warp can handle articulation, Vertex Block Descent handles cable or cloth, and the sponge uses a SuperDex finite-element backend. Depending on the path, the solvers exchange forces or share poses and contact wrenches. The evidence needs to identify whether and when a reaction reaches the hand. The pinned DexLab wiping cohort uses 60 Hz control, 16 rigid-body substeps and two SuperDex steps per period. These settings describe that experiment.
3. **Direct interaction and effective parameters.** A person can select, drag and inspect objects in Viser. The pinned material code distinguishes three application paths. Writing a cloth constitutive array can take effect on the next substep. A captured CUDA graph embeds a by-value contact scalar until recapture. Build-time properties, such as geometry and density, require rebuilding the model. Some contact settings are model-wide, even when the interface shows adjacent material panels.
4. **Feedback tied to robot motion.** The agent receives target error, object motion, contact, grasp or slip observations, and task progress for motion primitives. It can pair these outputs with views and logs. For a missed wipe, inspect whether the original command reached the bar and which contact was reported before deciding whether to edit the geometry or the motion.

[Paper §3](https://arxiv.org/html/2610.18835v2#S3) · [Interactive commands at the pinned revision](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/examples/live/REFERENCE.md) · [Parameter application code](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/robosimstudio_studio/tuning/apply.py)

## What did the evaluations measure?

| Author study | Result | Evidence boundary |
| --- | --- | --- |
| Visual refinement | **18** rigid, articulated, cable, cloth, and soft-body task simulations. A towel example shows bending and stretch settings during the same fold | Demonstrates construction and inspection. Table 1 compares built-in workflow support. It supplies no quantitative hardware-accuracy ranking |
| Force-feedback interaction | A Gello leader arm drives a simulated robot. The command-to-simulation configuration difference produces feedback, with a speed-dependent deadband to reduce lag artifacts | Supports feeling a modeled obstruction when hanging a tool. Agreement with the actual load requires a separate comparison |
| Agent-built wiping | Two coding agents built scenes in about an hour, with one verified construction reported at **56 minutes**. The study generated **30 layouts**, varied sponge stiffness, and reported **0% to 100%** simulated wiped area over **14 Graph-as-Policy iterations**. A hardware pilot followed | Supports feasibility for one manipulation task. The paper gives no total hardware trial denominator or hardware regression result after the scene revision |

The case studies use several kinds of feedback. The visual study gives examples of geometry and deformation. In the force-feedback example, pausing the simulation releases feedback, and the gripper uses its actual aperture to distinguish a physical obstruction inside the simulator from an unobstructed close. This is useful to an operator even before there is a calibrated force reference. The policy result in the wiping study comes from a separate simulation loop. [Paper §4](https://arxiv.org/html/2610.18835v2#S4)

## Two failures, at different layers

![Paper Figure 7h showing the movement of a real support during wiping](https://arxiv.org/html/2610.18835v2/figures/wipe_failure.jpg)

*Figure 7h. A hardware rollout moved a support that the original simulated scene constrained to the environment.* [Paper Figure 7](https://arxiv.org/html/2610.18835v2#S4.F7)

**In the paper, the first identifiable defect was the support constraint.** The original simulation fixed the supports. A wiping contact applied load to a movable physical support, it shifted, and the sponge lost contact with the bar. Wiping a loose board on a table gives the intuition: a sideways load can move the board. The analogy supplies no friction or tipping threshold. The authors released the simulated support as a free rigid body. Loads or off-center motions could then move or tip it in simulation. A matched hardware comparison would need the same commanded wipe, support pose, contact location, and load over time to distinguish sliding from tipping and establish the benefit of the revision. [Paper §4.3](https://arxiv.org/html/2610.18835v2#S4.SS3)

**In DexLab's paired public-demo replication, the earliest supported failure was retention under wiping load.** Both conditions used matching compiled collision geometry and the same grasp-readiness check. The original adds compliant position constraints to one patch of the sponge after readiness, updates targets relative to the measured hand, and releases the constraints at active opening. All records in the no-assistance condition kept zero such constraints. The two groups entered wiping around **14.35 s**. In the no-assistance group, the material patch moved **237–242 mm** relative to the hand during wiping, and the controller exited after losing pressing contact around **28.48 s**. Cleaning was **39.92–41.15%** and **0/3** passed. The original held the patch centroid near **0.061 mm** displacement during retention, cleaned **95.47–95.89%**, and passed **3/3**. Think of a soft spring holding the patch in place while the rest can deform. The comparison identifies the contribution of this assistance in the pinned configuration. Isolating friction, reaction transfer, or control requires time-aligned contact and motion at the onset of relative patch movement. [DexLab trial records, videos and offline rescore](rss-wiping.md)

## What to reuse in DexLab

The existing wiping entry has replay, an independent rescore, trajectories, and parameter records. The next UI comparison can reuse one existing normal load/unload case and answer a concrete question: can a reader change one parameter, verify the effective value, and compare the resulting force traces from the same entry? The display needs the requested and effective values, which update path ran, and which run produced the measurement. If the existing path already provides that evidence, reuse it. Cross-cohort wiping differences and the remaining coupling attribution are tracked by the existing issue. [DexLab case selection](selection.md) · [Original Discussion #220](https://github.com/huangkiki/Dexlab/discussions/220) · [Open evidence issue #247](https://github.com/huangkiki/Dexlab/issues/247)
