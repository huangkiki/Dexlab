# Real2Worlds2Real: verify collision geometry before scaling training worlds

| At a glance | Details |
| --- | --- |
| Work | Real2Worlds2Real, UC Berkeley, NVIDIA, UIUC, CMU, arXiv:2611.31098v1 |
| Input → output | RGB views or video, a task description, and available calibration and interaction evidence → executable twins, checked variants, candidate policies, and handoff records |
| Public materials | MIT-licensed general tools, reconstructed examples, and hardware demos. Public reproduction of the paper tasks still lacks task-specific implementations, training artifacts, and the real-robot workers |
| DexLab verdict | **`pilot`**. Start with a test of whether asset validation catches a change that blocks insertion while leaving the rendered image intact |

[Paper v1](https://arxiv.org/html/2611.31098v1) · [Project page](https://real2worlds2real.github.io/) · [Source at 576cbd5](https://github.com/real2worlds2real/real2worlds2real/tree/576cbd561ad1853ee90b9a4c331d3029ee499687)

## What comes out of one capture?

Start with “stack the blue cup onto the white cup.” The cup colors and positions are only part of what the simulator needs. The blue cup's outside wall, the white cup's inside wall, the opening clearance, the table, and the robot's approach space determine whether the objects can nest. The agent builds an editable, executable **digital twin** of the captured scene. It can also change cup shapes, layouts, or backgrounds to make **digital cousins**. Each variant gets feasibility checks of its own. Background variation and collision geometry test different things.

![Paper Figure 1, from real observations through world and policy development to hardware evaluation](https://arxiv.org/html/2611.31098v1/astra_teaser.png)

*Figure 1. Evidence can send the agent back to refine either the world or the policy. The hardware outcome comes from a separate final evaluation.* [Paper Figure 1](https://arxiv.org/html/2611.31098v1#S0.F1)

### How the agent constructs the world

1. **Separate manipulated assets from their surroundings.** The agent writes Blender scripts for editable objects. Where available, calibrated silhouettes, depth, known dimensions, and camera poses constrain scale and placement. The background can be a mesh, Gaussian splats, or both. A table still needs a collider. A manipulated asset is removed from the static splat background and represented separately.
2. **Preserve the structures that govern motion.** Variants retain relevant joints, deformable attachments, stable support, functional relations, and enough room for manipulation. Rigid and articulated objects use PhysX. Cloth, ropes, and soft bodies use appropriate particle, rod, or volume representations with compatible PhysX or Newton simulation, with deformation driving the rendered surface. Reference views, support checks, and task-specific execution probes inspect different aspects of the result.
3. **Bind evidence to the asset it checked.** Reference views expose visual or geometric discrepancies. Execution reveals contact and joint problems. The agent can revise upstream work and repeat affected checks. Successful procedures become skills with triggers, steps, and evidence. The public implementation pins observations and assets by hash in a delivery record, and the policy station checks the dependencies against those pins. [Paper §§3.1–3.2](https://arxiv.org/html/2611.31098v1#S3) · [Scene delivery code](https://github.com/real2worlds2real/real2worlds2real/blob/576cbd561ad1853ee90b9a4c331d3029ee499687/real2sim/src/real2sim_harness/delivery.py)

An interaction video lets the agent estimate parameters that affect the observed motion. It specifies candidate ranges and matching initial conditions and controls. For each trial it resets the simulator, applies candidate values, checks their effective readback, and compares the aligned simulated and observed trajectories. The expression below summarizes the procedure. The paper does not prescribe one objective implementation or optimizer.

$$
\widehat{\theta}\in\operatorname*{arg\,min}_{\theta\in\Theta}
D(\operatorname{Align}(\tau_{\mathrm{sim}}(x_0,u;\theta)),\tau_{\mathrm{obs}})
$$

Here $\theta$ is a candidate parameter vector in $\Theta$, $x_0$ is the initial state, $u$ is the control, $\tau_{\mathrm{sim}}$ and $\tau_{\mathrm{obs}}$ are simulated and observed motion, and $D$ measures discrepancy. Matching one slide can constrain friction in that condition. If an incorrect contact shape and an incorrect coefficient cancel each other's effects, an independent trial or excitation is needed to tell them apart. [Paper §3.2.4](https://arxiv.org/html/2611.31098v1#S3.SS2.SSS4)

### How the agent develops a policy

The agent can assemble BODex-style grasp optimization and cuRobo motion planning, use model predictive control, or train reinforcement learning from simulated state and task rewards. The resulting executor can run the task itself or generate demonstrations for ACT or Diffusion Policy. With an expert that can act in the states the current policy visits, DAgger adds corrective examples. An RL decorator instead freezes the base policy and learns residual actions from simulated reward. Rollout failures help choose where to refine the result. The public handoff binds the frozen checkpoint, normalization, I/O, and evaluations to the accepted artifacts. Its generic package marks `real_validation: pending`, where a human provides a separate hardware result. [Paper §3.3](https://arxiv.org/html/2611.31098v1#S3.SS3) · [Handoff documentation](https://github.com/real2worlds2real/real2worlds2real/blob/576cbd561ad1853ee90b9a4c331d3029ee499687/end_to_end/docs/delivery_package.md)

## What did the authors measure?

| Comparison | Result | Interpretation |
| --- | --- | --- |
| Table 1a, world construction | Hardware gear insertion **28/30** for Real2Worlds2Real, **18/30** PolaRiS, **12/30** SimFoundry, **26/30** real-world refinement. Peg insertion **30/30**, **25/30**, **22/30**, **26/30**, respectively | Shared ACT initial policy from 60 real demonstrations and the same refinement budget. The three Real2Sim methods build twins from the same video. Each world-building method still changes multiple properties |
| Table 1b, policy development | Hardware nut tightening **22/30**, **19/30**, **16/30** for Real2Worlds2Real, ASPIRE, ENPIRE. Cup stacking **30/30** versus **24/30** and **24/30** | Same simulated worlds and access to the same 60 demonstrations, each development system using its own strategy |
| Table 2, world quality and ablations | Full method, fixed pipeline, and no adaptive refinement yield visible-surface F-score at 1 cm **0.108**, **0.002**, **0.012**. Stability **0.63**, **0.10**, **0.24** and support recall **0.58**, **0.47**, **0.23** | Visibility, settling, penetration, and support have different meanings. The fixed pipeline has higher support recall than no refinement. These factorial choices were not isolated per tool |
| Table 3, single RGB video calibration | Seven friction, restitution, and pendulum-length tasks. Parameter error **4.2%**, held-out motion error **2.6%**, bound violations **0.0%**. A 2D tracking plus analytic method reports **24.4% / 13.1%** for the first two | Author-reported results on the specified tasks, with differing baseline coverage. The main text refers to supplementary metric details |
| Figure 5, skill reuse | Held-out lemon scene **28.1M → 13.9M** tokens with SSIM **0.925 → 0.929**. For LIBERO-Pro Long, 20 tasks × 50 states and 0 → 136 skills give **52.9% → 82.2%** overall and **44.1% → 69.1%** across all candidate programs | Build efficiency and program quality are different outcomes. Both are measured within the stated task sets |

Hardware trials use Dexmate, Sharpa hands, and Orbbec RGB-D. Every cell in Table 1 has 30 trials. Table 2 uses PyBullet for settling and penetration. The public main text lacks per-trial failure traces and refers to supplementary metric definitions for which this review found no public link. [Table 1 and §4.1](https://arxiv.org/html/2611.31098v1#S4.SS1) · [Table 2](https://arxiv.org/html/2611.31098v1#S4.T2) · [Table 3 and Figure 5](https://arxiv.org/html/2611.31098v1#S4.SS3)

![Paper Figure 4, adding demonstrations and adding worlds in two separate simulation comparisons](https://arxiv.org/html/2611.31098v1/cup_scaling_row.svg)

*Figure 4. The learner is Diffusion Policy. The left adds demonstrations on a fixed set of worlds, then adds DAgger corrections after the curve plateaus. The right fixes 1,000 demonstrations and increases training worlds from 10 to 1,000. Success rises from 17% to 71% on 100 unseen simulated cup-stacking scenes. Object variants, layouts, and backgrounds are varied together.* [Paper §4.2](https://arxiv.org/html/2611.31098v1#S4.SS2)

## What do the hardware counterexamples identify?

- **SimFoundry gear insertion.** The same input capture yields a task asset with missing teeth and inaccurate shaft spacing. The collision boundaries that guide alignment and insertion differ from the physical assembly, so a residual learned in simulation sees different contact feedback after deployment. The authors report 12/30 successes, versus 28/30 for the full method. The first evidenced defect is in task geometry. Missing teeth and shaft spacing both differ, and the relative contribution remains unresolved. Think of testing a press fit after sanding the tabs off one of the parts. That explains why contact can change, while identifying the actual cause requires freezing initial states and actions, correcting each geometric factor independently, and measuring first contact, insertion depth, and load.
- **ASPIRE and ENPIRE nut tightening.** The bolt is fixed and initial nut placement can vary. Both baselines use scripted turning. The authors identify sensitivity to placement, while their combined scripted and closed-loop approach can correct from feedback. Success is 19/30 and 16/30 for the baselines, compared with 22/30. The first layer supported by the report is the execution strategy's response to placement. The published evidence leaves the first disengagement, slip, or alignment error unresolved. Fix initial offsets, action budget, and target rotations in a feedback on/off control, then inspect six-axis pose, axial advance, torque, and cumulative turns at the first divergence. [Paper §4.1](https://arxiv.org/html/2611.31098v1#S4.SS1)

## What should DexLab borrow first?

The existing [native LIBERO records](libero-workflow.md) already pin the Panda, controller, assets, and native success predicate, with actions and contacts available. The useful addition is to **bind an independent check of task-critical geometry to the asset revision**. Basket clearance, for example, governs whether a cream-cheese package fits on the recorded insertion path. A visually identical derivative can still change the physical opening.

The smallest pilot uses one existing development episode as the reference and changes a single opening collider in an offline copy. Leave the render mesh identical. Freeze the units, frames, poses, action sequence, and score definition. Predeclare a clearance-changing offset and test it against the saved object poses and collision geometry. The same check must accept the reference, detect the negative control, name the first affected sample and collider pair, and reject reuse of the previous receipt after a geometry hash change. Static evidence establishes the sensitivity of this probe. If the installed collision shape cannot be recovered, record the result as unknown and stop at the static boundary. Only a separate native comparison can measure degradation in task completion.

This review used the published v1 main text, pinned source, examples, and author results. The repository provides a general pipeline and handoff, and explicitly excludes the paper-task policy implementations and hardware workers. The reported evaluations are the authors' evidence. DexLab registers the offline slice as a candidate. [Upstream release scope](https://github.com/real2worlds2real/real2worlds2real/blob/576cbd561ad1853ee90b9a4c331d3029ee499687/README.md#scope-and-limits)
