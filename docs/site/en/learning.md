# Learn simulation

Follow a research finding into the physics and engine implementation behind it. Read the shared foundations, solver guide and existing courses for six engines here, without installing an environment.

**The course text is primarily Chinese, with English terminology and summaries.** Both language entrances preserve the original course content.

## Choose a starting point

- **Build intuition:** the [Physics-Based Simulation study route](learn/sim/docs/physics-based-simulation.md) connects state, time, dynamics and optimization.
- **Understand contact:** the [nine-part solver guide](learn/sim/docs/solver-guide/README.md) covers stepping, contact, friction, constraints and solving.
- **Look up a concept:** explore the [shared foundations](learn/sim/docs/foundations.md) and [term index](learn/sim/docs/solver-guide/term-index.md).
- **Choose a route:** follow the [application or physics/source track](learn/sim/docs/learning-paths.md).

## Explore an engine

Each contents page leads to the full chapters. The application track explains models, state, control and observations; the physics track follows dynamics, contact, solvers and source code. Course directories distinguish delivered material from planned units.

| Engine | Reading focus |
| --- | --- |
| [MuJoCo](learn/mujoco/docs/curriculum.md) | MJCF, state and actuators, soft contact, solving and integration |
| [SuperDex](learn/superdex/docs/curriculum.md) | Scene / Actor, contact geometry, implicit solving and force observations |
| [Genesis](learn/genesis/docs/curriculum.md) | Scene / Entity, multiple physics models, batched state and control |
| [Newton Physics](learn/newton/docs/curriculum.md) | ModelBuilder, State / Control, Warp and solver boundaries |
| [PhysX](learn/physx/docs/curriculum.md) | Scene / Actor / Shape, articulations, PGS / TGS |
| [Drake](learn/drake/docs/curriculum.md) | Systems / Context, MultibodyPlant, contact and optimization |

## Connect knowledge to research

[Friction and contact torque](learn/sim/docs/solver-guide/03-friction.md) → [Wuji grasp comparison](wuji-contact.md) · [Deformation and coupling](learn/sim/docs/solver-guide/07-representations.md) → [Cloth experiments](cloth-comparison.md) · [State and observations](learn/sim/docs/solver-guide/01-simulation-step.md) → [LIBERO record checks](libero-workflow.md)

Courses come from Sim Learning and the six independent community course repositories. Original wording, version references and validation limits are preserved. Each page includes its source and license; GitHub remains available for inspecting source code. [About the courses](learn/sim/README.en.md) · <a href="index.html#blog">Back to the research Blog</a>

```{toctree}
:hidden:
:maxdepth: 2

Foundations and solver guide <learn/sim/README>
MuJoCo <learn/mujoco/docs/curriculum>
SuperDex <learn/superdex/docs/curriculum>
Genesis <learn/genesis/docs/curriculum>
Newton Physics <learn/newton/docs/curriculum>
PhysX <learn/physx/docs/curriculum>
Drake <learn/drake/docs/curriculum>
```
