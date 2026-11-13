<div align="center">

<img src="assets/hero.svg" alt="Sim Learning: six engines, two learning tracks, from native APIs to physics and source code" width="100%">

**Learn to use simulation engines—and explain how they work.**

[中文](README.md) · [Start with Physics-Based Simulation](docs/physics-based-simulation.md#english-reading-guide) · [Solver guide](docs/solver-guide/README.md) · [Learning paths](docs/learning-paths.md) · [Shared foundations](docs/foundations.md) · [Project tracker](https://github.com/users/huangkiki/projects/2) · [Experimental cases](docs/dexlab.md)

</div>

Sim Learning is an independent community learning series for **MuJoCo, SuperDex, Genesis, Newton Physics, PhysX and Drake**. This repository is the course home. Each engine repository owns its detailed lessons, native examples, pinned source references and version records.

## Start with the physics

Begin with [Physics-Based Simulation](https://phys-sim-book.github.io/), coauthored by Chenfanfu Jiang, Minchen Li and colleagues. Read discrete space/time, optimization and Newton, mass-spring implementation, then contact and friction before comparing engine configurations. Our [Chinese study route and original checkpoints](docs/physics-based-simulation.md#english-reading-guide) connect the book to the [solver guide](docs/solver-guide/README.md) and native engine lessons.

This branch contains [nine Chinese text lessons](docs/solver-guide/README.md), English summaries, answered exercises and a [complete frozen-term index](docs/solver-guide/term-index.md). [Acceptance](docs/learning-migration-acceptance.md) distinguishes readable content, pending integration and deferred native execution.

## Choose a track

| Applications · A0–A9 | Physics and source · B0–B7 |
|---|---|
| Objects and setup, modeling, state and time, control, robotics, sensing, batching and data. | Dynamics and data structures, stepping, contact, solvers, integration, force observation and extensions. |
| Start with programming basics and use the shared concept map as needed. | Start with linear algebra and rigid-body mechanics, after the engine's A0–A4 foundations. |

Both tracks are fully planned. All six engines have Chinese lessons on modeling, state, control, robotics, contact, solvers, sensing, rendering, batching and data. All six also have extension, multiphysics and differentiation lessons. **The Learning rename, prerequisite reading route and solver tutorial are in progress.** E7 full installation lessons and the integrated track review remain paused. See [current work](docs/current-work.md). See [delivery progress](docs/progress.md#delivery-progress) for stage details; source review, syntax checks and executed validation have distinct statuses.

## Choose an engine

| Repository | Reading focus | Course entry |
|---|---|---|
| [MuJoCo Learning](https://github.com/huangkiki/mujoco-learning) | MJCF, model/data ownership, actuation, constraints and integration | [Curriculum](https://github.com/huangkiki/mujoco-learning/blob/main/docs/curriculum.md) · [Callbacks and plugins](https://github.com/huangkiki/mujoco-learning/blob/main/docs/extensions-and-callbacks.md) |
| [SuperDex Learning](https://github.com/huangkiki/superdex-learning) | Physics/Robotics boundaries, Scene/Actor, contact geometry and implicit solving | [Curriculum](https://github.com/huangkiki/superdex-learning/blob/main/docs/curriculum.md) · [Materials and differentiation](https://github.com/huangkiki/superdex-learning/blob/main/docs/extensions-boundaries.md) |
| [Genesis Learning](https://github.com/huangkiki/genesis-learning) | Scene/Entity, multiphysics, batched state and differentiability boundaries | [Curriculum](https://github.com/huangkiki/genesis-learning/blob/main/docs/curriculum.md) · [Multiphysics and differentiation](https://github.com/huangkiki/genesis-learning/blob/main/docs/extensions-boundaries.md) |
| [Newton Physics Learning](https://github.com/huangkiki/newton-learning) | ModelBuilder/State/Control, Warp arrays and solver-specific support | [Curriculum](https://github.com/huangkiki/newton-learning/blob/main/docs/curriculum.md) · [Solvers, coupling and differentiation](https://github.com/huangkiki/newton-learning/blob/main/docs/extensions-boundaries.md) |
| [PhysX Learning](https://github.com/huangkiki/physx-learning) | Native C++ SDK, articulations, PGS/TGS and host integrations | [Curriculum](https://github.com/huangkiki/physx-learning/blob/main/docs/curriculum.md) · [Extensions and multiphysics](https://github.com/huangkiki/physx-learning/blob/main/docs/extensions-boundaries.md) |
| [Drake Learning](https://github.com/huangkiki/drake-learning) | Systems/Diagram/Context, MultibodyPlant, SceneGraph, contact and optimization | [Curriculum](https://github.com/huangkiki/drake-learning/blob/main/docs/curriculum.md) · [Extensions and scalar conversion](https://github.com/huangkiki/drake-learning/blob/main/docs/systems-extensions.md) |

Read [the learning paths](docs/learning-paths.md) for the complete unit map and [the foundations](docs/foundations.md) for shared questions about frames, inertia, state, time, contact and observations. Detailed content is currently Chinese; this English entry reports the same scope.

## Follow development and evidence

[Delivery progress](docs/progress.md#delivery-progress) records published coverage. [GitHub Projects](https://github.com/users/huangkiki/projects/2) manages the cross-repository queue. Engine-specific changes belong in their engine repository; navigation and shared terminology belong here. [Contributing](CONTRIBUTING.md) explains the review contract.

This phase focuses on understanding the engines. It does not add simulation campaigns, benchmarks, training or a new scoring system. Experimental lessons will reuse [DexLab](https://github.com/huangkiki/Dexlab), retaining each report's version, workload and evidence boundaries. A source-reading baseline is distinct from a tested binary or historical host version.

Original material: [Apache-2.0](LICENSE). Upstream software and assets retain their own licenses. [Attribution](THIRD_PARTY.md).
