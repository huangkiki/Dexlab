# Drake Atlas

Understand Drake through native APIs, physics concepts and versioned source code.

[中文](README.md) · [Series home](https://github.com/huangkiki/sim-atlas) · [Introductory guide](docs/guide.md) · [Curriculum](docs/curriculum.md) · [Source map](docs/source-map.md) · [Versions](docs/versions.md) · [Roadmap](docs/roadmap.md) · [Project tracker](https://github.com/users/huangkiki/projects/2)

Part of **[Sim Atlas](https://github.com/huangkiki/sim-atlas)**, an independent community learning series with two complete planned tracks: applications (modeling, control, robotics, sensing and data) and principles/source (dynamics, contact, solvers, integration and extensions).

Chinese lessons currently available:

- E1: [modeling, frames and inertia](docs/modeling-state-time.md), [state, Context and time](docs/state-time.md), and an original native API example. [E1 checks](docs/evidence/e1-validation.md).
- E2: [actuation and robot kinematics](docs/control-robotics.md), [task events and references](docs/task-interfaces.md), and three original API examples. [E2 checks](docs/evidence/e2-validation.md).
- E3: [geometry, materials and contact laws](docs/contact-models.md), [dynamics assembly and SAP](docs/contact-solvers.md), and [forces, impulses and sampling](docs/contact-observation.md), with an original native configuration/field reader and 22 answered exercises. [E3 checks](docs/evidence/e3-validation.md).
- E4: [camera geometry and rendering](docs/sensors-rendering.md), [sampling and latency](docs/sensor-timing.md), and [inertial, encoder and force observations](docs/inertial-force-sensing.md), with an original native depth-camera/ZOH example and 21 answered exercises. [E4 checks](docs/evidence/e4-validation.md).
- E5: [Context/Simulator isolation and execution](docs/batch-lifecycle.md), [randomization and learning interfaces](docs/randomness-learning.md), and [logging, ownership and replay](docs/data-replay.md), with an original native context/logging example and 21 answered exercises. [E5 checks](docs/evidence/e5-validation.md).
- E6: [native System extensions](docs/systems-extensions.md), [AutoDiff/symbolic and physics-path boundaries](docs/scalar-capabilities.md), and [optimization, FEM and the integrated source chain](docs/engine-boundaries.md), with an original scalar-convertible LeafSystem example and 21 answered exercises. [E6 checks](docs/evidence/e6-validation.md).

E3 separates contact representation, discrete approximation, solver and integrator. It traces the actual fixed-version implementations, including discrepancies in older comments about SAP residual scaling, AutoDiff and material defaults. TAMSI is not a selectable solver in this pinned version. The lessons cover A4 and B1–B5, extending the E1 B0 dynamics foundations.

E4 completes A6 at the source-study level, covering image types, frames and units, renderer/QueryObject ownership, headless versus Meshcat, explicit capture/output timing, and ideal inertial sensing. It documents the pinned RgbdSensorDiscrete image_time export discrepancy and sampled-plant acceleration timing instead of relying on API names alone.

E5 completes A8/A9 and the Systems-level B6 execution/extension contract. It distinguishes C++ parallel MonteCarlo from the serial Python binding, RNG snapshots from physics checkpoints, and logging triggers from sensor timestamps. It documents fixed DrakeGymEnv handler/reset/render discrepancies and the actual vector-copy versus abstract-reference Eval bindings. E6 now completes the specific extension and integrated source topics; E7 remains planned.

E6 distinguishes conversion registration from method support and meaningful derivatives. It traces empty-only deformable-model conversion, geometry query support, current SAP implicit derivatives, optimization prerequisites, FEM state/integration, private MPM targets and native force models. The pinned damping setters check the old member; downstream material construction checks the actual coefficient. No runtime reproduction or upstream fix is claimed.

All examples are source-reviewed and syntax-checked; none was executed in this phase. No engine import, native model construction, contact query, solver, gradient check, simulation, renderer, browser, sensor event, random sampling, MonteCarlo, Gym rollout, replay, benchmark or training was run. These lessons do not qualify Drake for DexLab's runtime acceptance. Later experimental material will reuse [DexLab](https://github.com/huangkiki/Dexlab) with its original version and workload boundaries.

[Pinned upstream source](https://github.com/RobotLocomotion/drake/tree/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d) · [Attribution](THIRD_PARTY.md)
