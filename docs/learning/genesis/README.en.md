# Genesis Atlas

Understand Genesis through native APIs, physics concepts and versioned source code.

[中文](README.md) · [Introductory guide](docs/guide.md) · [Curriculum](docs/curriculum.md) · [Source map](docs/source-map.md) · [Versions](docs/versions.md) · [Roadmap](docs/roadmap.md) · [Series home](https://github.com/huangkiki/sim-atlas) · [Project tracker](https://github.com/users/huangkiki/projects/2)

Part of **[Sim Atlas](https://github.com/huangkiki/sim-atlas)**, an independent community learning series with two complete planned tracks: applications (modeling, control, robotics, sensing and data) and principles/source (dynamics, contact, solvers, integration and extensions).

The initial guide, pinned source map and [E1 modeling, frames, state and time lesson](docs/modeling-state-time.md) are available in Chinese. E1 covers rigid and multiphysics state layouts, asset and inertia conventions, reset versus checkpoint, and step/substep semantics. [Acceptance and limitations](docs/e1-acceptance.md) distinguish pinned-source review and syntax checks from unperformed runtime validation.

The [E2 control, robotics and task-interface lesson](docs/control-robotics-tasks.md) traces named-joint mapping, batched targets, actuator clipping, FK/Jacobian/IK contracts, native planning and task timing. Its [acceptance record](docs/e2-acceptance.md) lists source limitations and the unexecuted original two-joint example.

The [E3 contact, solvers and force-observation lesson](docs/contact-solvers-forces.md) connects material mixing, contact rows, Newton/CG, stopping rules, warm starts, integration and force sampling. It distinguishes rigid, multiphysics and coupler branches, including limitations of contact readback. Its [acceptance record](docs/e3-acceptance.md) documents source and syntax checks; native execution remains unperformed.

The [E4 sensors, rendering and visualization lesson](docs/sensors-rendering.md) separates visual cameras, lazy RGB camera sensors, ray/depth queries, contact/joint effort, IMU and tactile models. It covers frames, units, shapes, sampling/cache timing, segmentation-ID decoding, GUI/headless and renderer/differentiation limits. The [acceptance record](docs/e4-acceptance.md) lists pinned implementation gaps and the unexecuted native API example.

The [E5 batching, learning interfaces and data lesson](docs/batch-learning-data.md) explains batch isolation, reset clocks, CPU/GPU tensor ownership, the actual Go2 task contract, termination versus truncation, domain randomization, recorders, checkpoints and playback. It distinguishes Genesis task code from the unpinned external RL trainer and documents profiling and sim-to-real limits. The [acceptance record](docs/e5-acceptance.md) covers pinned-source and syntax checks; no native execution, training or benchmark was performed.

The [E6 multiphysics, differentiation and extension lesson](docs/extensions-boundaries.md) follows material dispatch, MPM/SPH/PBD/FEM/SF consumers, Legacy/SAP/IPC coupling, hybrid entities, gradient bridges/checkpoint replay, rigid adjoints, thermal/tactile models and native extension points. It separates batched state from shared topology and identifies incomplete or rejected combinations. Its [acceptance record](docs/e6-acceptance.md) documents source/AST checks and original unexecuted interface functions; no gradient experiment or external uipc runtime was verified.

The full course is in development. A0 installation and the integrated two-track review remain for E7. This phase prioritizes understanding engine subsystems. Minimal snippets support explanation and are explicitly marked when unexecuted. No new simulation campaigns, benchmarks, training or scoring are included; later experimental material will reuse [DexLab](https://github.com/huangkiki/Dexlab) with its original version and workload boundaries.

[Pinned upstream source](https://github.com/Genesis-Embodied-AI/genesis-world/tree/216a708e06124595521a9d36a51fae5393fd4ff8) · [Attribution](THIRD_PARTY.md)
