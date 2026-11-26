# Understand simulation, starting with MuJoCo

Why does an object slip even as the fingers tighten? Does a smaller step always help? When simulation runs faster, has the controller changed too?

Follow one question: **how does an action pass through stepping, contact and numerical solving to become the next state?** Then use that chain to understand MuJoCo 4 and choose changes worth investigating in a real system.

**[Start with time: one step, several clocks →](mujoco-learning/step.md)**

## Build the complete chain

Control input → actuator forces → contact and constraint solving → state integration → observations → next control update.

A change anywhere can affect what follows. A dropped object in the last frame does not identify a solver defect; smooth rendering does not establish real-time physics.

This route covers time, contact, version 4, performance and an existing failure case. Each lesson starts with a question, then offers expandable explanations, a self-check and links to detailed courses.

(solver-fundamentals)=
## Solver and simulation fundamentals

- [One step, several clocks](mujoco-learning/step.md): use a physics step to distinguish the simulation step, control period and display rate.
- [Contact, friction and solving](mujoco-learning/contact.md): follow an object onto a table to see when contact activates and how friction limits sliding.
- [Why does a sliding block lift off after the contact solve converges?](complementarity-contact-models.md): use a sliding block to see what the solver is solving and how the contact model changes the answer.
- [How do multiple solvers stay in sync, and what does preCICE do?](solver-coupling.md): see how solvers exchange state and forces within one scene.
- [Sim-to-real failure atlas](failure-root-cause-atlas.md): follow the evidence in time to find where a simulation first goes wrong.

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

Continue from the guided MuJoCo route into native APIs and source code, or choose an engine and start with its exercises.

- **Shared foundations:** [Physics-Based Simulation](learn/sim/docs/physics-based-simulation.md) · [Nine-part solver guide](learn/sim/docs/solver-guide/README.md) · [Term index](learn/sim/docs/solver-guide/term-index.md) · [Application and theory tracks](learn/sim/docs/learning-paths.md)
- **MuJoCo:** [Full contents](learn/mujoco/docs/curriculum.md) · [State and time](learn/mujoco/docs/state-and-time.md) · [Contact models](learn/mujoco/docs/contact-models.md) · [Versions and evidence](learn/mujoco/docs/versions.md)
- **Other engines:** [SuperDex](learn/superdex/docs/curriculum.md) · [Genesis](learn/genesis/docs/curriculum.md) · [Newton Physics](learn/newton/docs/curriculum.md) · [PhysX](learn/physx/docs/curriculum.md) · [Drake](learn/drake/docs/curriculum.md) · [Chaos Physics](chaos-learning/index.md) · [Bullet Physics](bullet-learning/index.md)

Sim Learning and the independent courses retain their original text, primarily in Chinese, and their licenses. DexLab’s Chaos and Bullet modules offer bilingual exercises that use the same box drop to explore both native workflows.

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
Chaos Physics <chaos-learning/index>
Bullet Physics <bullet-learning/index>
```
