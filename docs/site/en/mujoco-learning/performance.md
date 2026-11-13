# Performance: latency before throughput

**Finishing one robot update on time and generating many environment samples per second are different problems.** One concerns latency and jitter; the other concerns aggregate throughput.

## Separate the cost of an update

Break an update into physics, control, observation generation, rendering, data movement and communication. Establish the measurement boundary before calling something faster.

In a teaching example, physics takes 1 ms and rendering takes 7 ms. Halving physics time only changes the serial total from 8 ms to 7.5 ms. With concurrency and asynchronous queues, follow the critical path instead of simply adding component timings.

<details class="explanation"><summary>Simulation time, wall time and real-time factor</summary>
<p>Real-time factor can be expressed as simulated duration divided by wall duration. Advancing one simulated second in half a wall second gives an average factor of two. It says nothing about the slowest step and does not guarantee every control deadline.</p>
<p>For closed-loop operation, inspect the latency distribution, missed deadlines and queue backlog. For training samples, specify whether reset, observations, transfers and learner waits are included. These are measurement principles, not measured MATRiX performance.</p>
</details>

## Choose an execution path for the question

- **Single-instance closed loop:** measure physics and end-to-end control latency. Batching does not automatically remove communication waits or blocking rendering.
- **CPU multi-instance sampling:** understand shared models, per-thread workspaces and state isolation before studying `mujoco.batch`. It arrived in 3.17.0; the older `rollout` contract cannot simply stand in for it.
- **GPU batching:** examine model support, precision, compilation and transfers in MJX / MuJoCo Warp. Choose with task evidence and actual outputs, not package names.

Sources: [Official batch introduction](https://mujoco.readthedocs.io/en/4.0.0/changelog.html#version-3-17-0-october-22-2026) · [Existing CPU batching course, version 3.15](../learn/mujoco/docs/cpu-batching.md) · [MJX and device data](../learn/mujoco/docs/mjx-and-device-data.md)

## Make the comparison interpretable

Fix the model, simulated duration, control period, inputs and required outputs. Change one clearly identified factor. If disabling rendering helps, describe a rendering-free path. If both the step and control rate change, do not attribute everything to the solver.

Retain task outcomes and key physical quantities. Dropped contacts, missing observations or changed control semantics mean the workload is no longer equivalent.

## Self-check: is a GPU necessarily faster?

<details><summary>You advance one small model and copy state between CPU and GPU every step. Must the GPU be faster?</summary><p>No. Launch, synchronization and transfer costs can dominate. Batch size and compute density also matter. Measure the complete path under comparable models, control and outputs.</p></details>

## The first MATRiX question

In one actual scene, determine whether physics, control updates and rendering share a blocking path. Distinguish computation, waiting for data and display latency before choosing the next optimization.

Read more: [Sensors and sampling](../learn/mujoco/docs/sensors-and-sampling.md) · [Rendering and viewers](../learn/mujoco/docs/rendering-and-viewer.md) · [Backends and differentiation](../learn/mujoco/docs/backends-and-differentiation.md)
