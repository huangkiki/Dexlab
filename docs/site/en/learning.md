# Understand simulation, starting with MuJoCo

Why does an object slip even as the fingers tighten? Does a smaller step always help? When simulation runs faster, has the controller changed too?

Follow one question: **how does an action pass through stepping, contact and numerical solving to become the next state?** Then use that chain to understand MuJoCo 4 and choose changes worth investigating in a real system.

**[Start with time: one step, several clocks →](mujoco-learning/step.md)**

## Build the complete chain

Control input → actuator forces → contact and constraint solving → state integration → observations → next control update.

A change anywhere can affect what follows. A dropped object in the last frame does not identify a solver defect; smooth rendering does not establish real-time physics.

This route covers time, contact, version 4, performance and an existing failure case. Each lesson starts with a question, then offers expandable explanations, a self-check and links to detailed courses.

## Connect learning to system optimization

For a robot system built on MuJoCo, start with three questions: how often does control update; which instant do the recorded forces and states describe; and where is time spent across physics, control, rendering and communication? The same questions help investigate MATRiX integration.

This course does not assume MATRiX's current version, defaults or performance. Browser timing diagrams are teaching calculations. Optimization claims need the actual version, model and measurements.

<details class="explanation"><summary>A running example</summary>
<p>A gripper receives a new target every 20 ms while physics advances every 2 ms. Ten physics steps occur between targets. Contact can form, carry a load or disappear during those steps.</p>
<p>Change the physics step to 1 ms but keep updating control every ten steps, and the control period becomes 10 ms. A changed result can no longer be attributed only to physical resolution. The next lesson makes this visible with an adjustable timeline.</p>
</details>

## Where MuJoCo 4 fits

The [version 4 lesson](mujoco-learning/mujoco4.md) connects changes to problems: speculative contacts to fast thin-object encounters, plasticity to history dependence, Studio to inspection, and batching to throughput. Understand the question before selecting a capability.

As checked on **2026-11-13**, the official stable release is [4.0.1](https://github.com/google-deepmind/mujoco/releases/tag/4.0.1). The existing [detailed courses](learn/mujoco/docs/curriculum.md) retain a **3.15.0** source-reading baseline. They are not relabeled as validated 4.0 runtime experiments.

(all-courses)=
## All courses

These six lessons are a guided entry. Continue into the existing courses for derivations, APIs and source code. **Those detailed courses are primarily Chinese; this introductory route is bilingual.**

- **Shared foundations:** [Physics-Based Simulation](learn/sim/docs/physics-based-simulation.md) · [Nine-part solver guide](learn/sim/docs/solver-guide/README.md) · [Term index](learn/sim/docs/solver-guide/term-index.md) · [Application and theory tracks](learn/sim/docs/learning-paths.md)
- **MuJoCo:** [Full contents](learn/mujoco/docs/curriculum.md) · [State and time](learn/mujoco/docs/state-and-time.md) · [Contact models](learn/mujoco/docs/contact-models.md) · [Versions and evidence](learn/mujoco/docs/versions.md)
- **Other engines:** [SuperDex](learn/superdex/docs/curriculum.md) · [Genesis](learn/genesis/docs/curriculum.md) · [Newton Physics](learn/newton/docs/curriculum.md) · [PhysX](learn/physx/docs/curriculum.md) · [Drake](learn/drake/docs/curriculum.md)

Courses come from Sim Learning and the independent engine-course repositories. Original text and provenance remain intact. Read here; find source and license information on each course page.

```{toctree}
:hidden:
:maxdepth: 1

mujoco-learning/step
mujoco-learning/contact
mujoco-learning/mujoco4
mujoco-learning/performance
mujoco-learning/diagnosis
Foundations and solver guide <learn/sim/README>
MuJoCo detailed courses <learn/mujoco/docs/curriculum>
SuperDex <learn/superdex/docs/curriculum>
Genesis <learn/genesis/docs/curriculum>
Newton Physics <learn/newton/docs/curriculum>
PhysX <learn/physx/docs/curriculum>
Drake <learn/drake/docs/curriculum>
```
