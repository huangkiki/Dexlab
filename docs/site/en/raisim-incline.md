# RaiSim's nine incline cases

**RaiSim 2.16.0 passed 6/9 cases. All nine records were valid.** It passed the three 15° static and three 15° nominal-zero-friction cases. On the 35° frictional incline, the cube crossed the rotation limit at about 55 ms at every timestep and turned about 48° at peak. {ref}`Ten-engine matrix and curves <incline>`

| Shared protocol condition | 2 ms | 1 ms | 0.5 ms |
| --- | --- | --- | --- |
| 15° static, μ=0.5 | Pass | Pass | Pass |
| 35° sliding, μ=0.5 | Fail | Fail | Fail |
| 15° nominal zero friction, μ=0 | Pass | Pass | Pass |

## Setup and validity

The 40 mm, 64 g cube starts flush with the incline and at rest. Only gravity and contact act on it during the 2 s run. Cases, references and scoring limits come from the frozen protocol. The native path uses the RaiSim C++ `World::integrate()` on Linux x86-64, CPU double precision, with a rigid box and tilted slab. Static and dynamic friction use the same μ. Restitution, rolling friction and spinning friction are zero. The default contact solver reports a 150-iteration cap and a 10⁻⁸ row tolerance. Sleeping is disabled. [Original incline protocol](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-protocol.md) · [RaiSim World API](https://raisim.com/api/raisim/World.html)

Each step retains pose, linear and angular velocity, contact position, contact-frame impulses and the object they act on. The scorer transposes the contact frame, applies the sign for the cube and checks the impulses against that step's momentum change. The maximum single-step residual across the nine cases was 2.1×10⁻¹⁶ N·s, below the original 10⁻⁷ N·s limit. The separate no-floor control at 1 ms had zero contacts. The cube fell freely through the original incline location and the control was correctly rejected. [RaiSim Contact API](https://raisim.com/api/raisim/Contact.html)

## How the three sliding cases failed

The cube starts at rest and the first step has no contact impulse. The second step has four contacts in every run. Their tangential impulses already yield a net angular impulse about the incline normal. Imagine a book sliding on a slanted board with friction pulling unevenly at its corners. The book can turn in the plane of the board. The analogy describes the direction of rotation. The measured impulses and angles come from the native records.

| Timestep | First contact time and normal-axis angular speed | First angle above 0.01 rad | Peak rotation and time | Position / speed RMSE |
| --- | --- | --- | --- | --- |
| 2 ms | 4 ms, −0.01283 rad/s | Step 28, 56 ms, 0.01071 rad | 0.83464 rad, 0.814 s | 16.85 mm / 26.50 mm/s |
| 1 ms | 2 ms, −0.00761 rad/s | Step 55, 55 ms, 0.01025 rad | 0.83398 rad, 0.815 s | 16.05 mm / 26.32 mm/s |
| 0.5 ms | 1 ms, −0.00381 rad/s | Step 110, 55 ms, 0.01016 rad | 0.83374 rad, 0.815 s | 15.69 mm / 26.29 mm/s |

At the first contact step the angular impulse about the incline normal was −0.2190, −0.1299 and −0.0650 μN·m·s, respectively. For each step, take the cross product of each contact's offset from the pre-step center of mass and its world-frame impulse. Summed angular impulse matches the cube's angular momentum change to within 3.5×10⁻²⁰ N·m·s in all three runs. The first measured mechanism is in-plane rotation driven by tangential impulses. The cube remained supported and the force-balance check passed. Rotation, position RMSE and speed RMSE exceeded their respective limits of 0.01 rad, 10 mm and 10 mm/s. Reducing the timestep fourfold left the rotation in place.

The records locate the asymmetry in the tangential contact impulses. Its origin within the solver remains unresolved. To distinguish geometry-dependent and solver-order effects, hold the 35° incline, initial state and timestep fixed, mirror the contact geometry or vary contact order independently, and compare the signed angular impulse at first contact. These results apply to this profile and protocol. [Attribution and controls in #431](https://github.com/huangkiki/Dexlab/issues/431)

## Download and reproduce

```{raw} html
<p><a href="_static/incline-extension/raisim-native-v1.zip">Native records ZIP</a> · <a href="_static/incline-extension/raisim-results.json">Scores and negative-control result JSON</a> · <a href="_static/incline-extension/manifest.json">Frozen protocol JSON</a></p>
```

The archive includes per-step states, contacts and impulses, solver iterations, native settings readbacks, score and file digests. [Rescore or regenerate the records](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/INCLINE_EXTENSION.md#raisim-2160) · [RaiSim installation](https://raisim.com/sections/Installation.html)
