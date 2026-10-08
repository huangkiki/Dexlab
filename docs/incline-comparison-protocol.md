# Paired engine incline protocol

[English](incline-comparison-protocol.md) | [简体中文](incline-comparison-protocol.zh-CN.md)

Compare official MuJoCo 3.15.0 and SuperDex 1.0.0 FP64 on one free cube. Reuse the nine published #95 impedance=0.9 records and add nine SuperDex records. The uniform cube is 40 mm, 64 g, under 9.81 m/s² gravity, initially at rest with its bottom flush against the incline. No controller or state writes after initialization. Three timesteps: 2, 1 and 0.5 ms; duration 2 s each.

The [frozen manifest](evidence/incline-comparison/manifest.json) retains every #95 tolerance: static 15°/μ=0.5, sliding 35°/μ=0.5 and nominally frictionless 15°/μ=0. Static reference: |f|≤μN and tanθ≤μ; continuous, nonrotating sliding reference: a=g(sinθ−μcosθ). Sources and assumptions follow the [original protocol](incline-friction-protocol.md).

Contact parameters are not equivalent: MuJoCo retains its original solref/solimp; SuperDex uses the published native penalty parameters, fixed friction smoothing speed and the 1e-9 absolute/relative solver tolerances used by contact_tangent_run. No outcome-dependent tuning. Equal μ is not material calibration. SuperDex exposes actor parameters but no combined contact law; disclose that observability gap and report motion/force errors independently.

Before physics, zero-step admission verifies geometry, coordinates, quaternion ordering, mass, inertia, contact settings, solver and initial state. MuJoCo forces are from the preintegration solve; SuperDex forces are queried after the completed step. Each belongs to the interval producing the measured velocity increment. Archive all poses, velocities, forces, contact distances and native solver statuses. Keep the original 1e-7 N·s impulse-consistency limit; failures remain invalid records rather than accuracy claims.

Publish original thresholds, absolute errors, support loss, rotation and all three timesteps. Separate violated reference assumptions from invalid numerical records. Conclusions cover these fixed numerical profiles only. Existing MuJoCo timings are historical evidence; record new preparation, stepping and observation costs separately, without a speed ranking. One bounded serial nine-case campaign, retaining all failures. Follow-up work is tracked in #113.
