# MuJoCo 4: which problems do the changes address?

**Ask what the current model lacks before choosing a new capability.** This lesson follows official releases, checked on 2026-11-13. The current stable release is [4.0.1](https://github.com/google-deepmind/mujoco/releases/tag/4.0.1). These are upstream capabilities, not a validated DexLab or MATRiX migration.

## Fast objects can cross thin obstacles

Version 4.0.0 adds **speculative contacts** for fast convex geoms that could cross a thin obstacle within one step. Compare motion per step with obstacle size before studying candidate contacts and conservative advancement.

Distinguish missed detection, contact response, numerical convergence and time discretization. The feature does not establish non-penetration for every model and timestep. [Official mechanism and scope](https://mujoco.readthedocs.io/en/4.0.0/computation/speculative.html)

<details class="explanation"><summary>A scale check you can do by hand</summary>
<p>At a constant 1 m/s and a 20 ms step, an object travels 20 mm. Against a 2 mm obstacle, checking positions only at step endpoints can miss a crossing. This illustrates a sampling problem; it is not a reproduction or measurement of MuJoCo's collision algorithm.</p>
<p>A concrete evaluation would compare the feature on and off under matched geometry, initial state and inputs, retaining native contacts and trajectories. Examine the resulting contact response as well as penetration.</p>
</details>

## Materials can remember deformation

Version 4.0.0 adds elasto-plasticity to joint/tendon springs and 2D/3D flexes. Plastic state lives in `mjData.plastic`, identified by `mjSTATE_PLASTIC`. Residual deformation after unloading therefore involves internal material state, not only positions and velocities. [4.0.0 changelog](https://mujoco.readthedocs.io/en/4.0.0/changelog.html#version-4-0-0-november-6-2026)

For recovery and persistent tasks, identify exactly which states are saved and reset. Supporting plasticity does not calibrate a model to a real material.

## Inspect simulation beyond its appearance

In MuJoCo 4, **Studio** leaves experimental status, bringing Filament rendering, composable inspection tools and browser viewing. Python distributions separate `mujoco-core` and `mujoco-studio`; `mujoco` installs both by default. Explore the [official browser demos](https://mujoco.org/) or [online viewer](https://live.mujoco.org/) without installing an environment for this lesson. [Official announcement](https://github.com/google-deepmind/mujoco/discussions/3773)

Inspection tools help reveal state. Rendering quality alone does not validate contact physics or control.

## Separate the 4.0 delta from the 3.x journey

The new `mujoco.batch` API arrived in **3.17.0**. MJX, MuJoCo Warp, multi-point contacts and sleeping also have their own 3.x histories. A “3.0 to 4.0” overview does not mean every capability debuted in 4.0.0. The next lesson separates batch throughput from single-instance latency. [Per-release changelog](https://mujoco.readthedocs.io/en/4.0.0/changelog.html)

<details class="explanation"><summary>Compatibility changes worth reading before migration</summary>
<p>Python 3.10 is no longer supported. Upgrading the old monolithic package involves moved files; follow official installation instructions. Flexcomp replaces the old composite/cable path, and Studio import paths changed. Version 4.0.0 also corrected RK4 orientation integration for ball/free joints and changed tendon sidesite semantics, potentially changing existing trajectories.</p>
<p>Version 4.0.1 fixes a sparse Cholesky defect introduced in 4.0.0. With sparse constraint Jacobians, it could give Newton an incorrect Hessian factor, affecting accelerations and convergence. This is a specific implementation-path fix, not evidence that Newton methods are generally unreliable.</p>
<p>Source: the <a href="https://github.com/google-deepmind/mujoco/blob/4.0.1/doc/changelog.rst">official changelog pinned to 4.0.1</a>. This lesson performs no upgrade; historical experiments retain their frozen version.</p>
</details>

## Self-check: choose the problem first

<details><summary>If the current problem is delayed control messages, should speculative contacts be the first change?</summary><p>There is no direct basis for that choice. Measure message timing, control updates and physics steps first. Speculative contacts becomes relevant when evidence points to within-step crossings or its corresponding collision mechanism. Connect a new feature to the actual bottleneck.</p></details>

Read more: [Version and evidence baseline](../learn/mujoco/docs/versions.md) · [Flex and elasticity](../learn/mujoco/docs/flex-and-elasticity.md) · [Recording and replay](../learn/mujoco/docs/recording-and-replay.md)
