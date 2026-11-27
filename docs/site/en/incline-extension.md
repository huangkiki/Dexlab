# Incline comparison with Chaos, Bullet and SOFA

Each backend completed the nine original conditions and one disabled-collision control. **Chaos passed all three nominal-zero-friction cases. Bullet passed two static cases and one nominal-zero-friction case. SOFA's nine records passed the momentum check and all exceeded at least one physical limit.** {ref}`Nine-engine matrix and overlaid curves <incline>`

| Frozen configuration | Static | Sliding | Nominal zero friction | Pass / fail / invalid |
| --- | ---: | ---: | ---: | --- |
| Chaos / UE 5.7.1, Linux Editor | 0/3 | 0/3 (3 invalid) | 3/3 | 3 / 3 / 3 |
| Bullet / PyBullet 3.2.7, CPU DIRECT | 2/3 | 0/3 | 1/3 | 3 / 6 / 0 |
| SOFA 26.06.00, rigid OBB / block Gauss–Seidel | 0/3 | 0/3 | 0/3 | 0 / 9 / 0 |

## Matched inputs

A uniform 40 mm, 64 g cube starts at rest with its base flush against the incline. Runs use 9.81 m/s² gravity and last 2 s. The conditions are 15° with μ=0.5 for static support, 35° with μ=0.5 for sliding, and 15° with μ=0 for nominal frictionless sliding. Each runs at 2, 1 and 0.5 ms. The nine cases, scoring window and limits come from the frozen incline manifest. The added disabled-collision control is outside the nine-case denominator. [Original incline protocol](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-protocol.md)

- **Chaos** advances the world once per Editor frame and records solver time, pose and velocity in a post-solve callback. Contact impulse includes the velocity impulse and the position correction divided by the actual step interval. The scorer checks it against momentum. The recorder reads the combined static and dynamic friction values at each contact.
- **Bullet** uses an analytical plane and reads the normal and both lateral forces at each contact. The scorer reconstructs interval impulse. The plane and cube have friction coefficients 1 and μ respectively. Native friction combines them by multiplication. The binding exposes the individual body settings.
- **SOFA** uses oriented-box collision and `FrictionContactConstraint`. The recorder saves solver multipliers and rigid-body world-space `lambda`. The scorer checks interval momentum before interpreting force. Constraint row presence indicates support records. Geometric contact count was unavailable. The friction setting is read from the contact manager.

Chaos and SOFA use finite slabs whose top faces contain the complete cube motion. Shared penetration measurements are reconstructed from native poses and the analytical plane. Each configuration retains its native contact law, collision margins, solver budget and precision. The positive cases use the original 1e-7 N·s momentum consistency limit.

## First observed failures

### Chaos

| Condition | From the first step to the outcome |
| --- | --- |
| Static, 2 ms | Step one supplies −0.149 N tangential force. Rotation exceeds 0.01 rad at about 0.034 s, drift exceeds 1 mm at 0.068 s, and final downhill displacement reaches 1.461 m. |
| Static, 1 ms | Step one supplies about 0.606 N normal force and near-zero tangential force. Drift exceeds 1 mm at 0.028 s and reaches 5.081 m. |
| Static, 0.5 ms | Step one also supplies normal support with near-zero tangential force. Drift exceeds 1 mm at 0.028 s and reaches 5.079 m. |
| Sliding, 2 ms | After downhill acceleration, the momentum residual first exceeds its limit at step 811, ending at 1.622 s. The maximum is 1.104e-7 N·s. The record is invalid. |
| Sliding, 1 ms | The first step has normal support and near-zero tangential force. During acceleration, the momentum check first fails at step 1597 (1.597 s). The maximum is 1.102e-7 N·s. The record is invalid. |
| Sliding, 0.5 ms | The first step has normal support and near-zero tangential force. During acceleration, the momentum check first fails at step 3175 (1.5875 s). The maximum is 1.036e-7 N·s. The record is invalid. |

At 1 and 0.5 ms the static case reads back 0.5 friction, yet its tangential force stays below 1.2e-8 N in magnitude throughout the scoring window. The traces nearly coincide with the frictionless controls. Logging tangential impulse in each first-step solve phase would distinguish friction anchors, iterations and phase selection. The sliding residuals cross the limit as velocity grows. Rounding accounts for part of the discrepancy. Distinguishing the remaining contributions requires reading the solved and stored velocities over the same intervals.

### Bullet

| Condition | Support evolution and outcome |
| --- | --- |
| Static, 0.5 ms | The cube stays nearly at rest and retains three contacts. Normal load varies from 0.600 to 0.613 N in the scoring window. Total-force RMSE reaches 0.01446 N, above 0.01 N. |
| Sliding, 2 ms | Sliding after flush initialization leads to excess rotation at 0.242 s. The scoring window has one contact record per step and 0.128–1.180 N normal force. Total-force RMSE is 0.34731 N. |
| Sliding, 1 ms | Rotation exceeds the limit at 0.335 s. The scoring window has one contact record per step and 0.131–1.166 N normal force. Total-force RMSE is 0.35226 N. |
| Sliding, 0.5 ms | Rotation stays within its limit. Normal support still varies from 0.135 to 1.398 N and total-force RMSE is 0.33972 N. |
| Nominal zero friction, 2 ms | The trajectory stays close to the analytical reference. Single-step force deviation first exceeds 0.01 N in the window at 1.180 s. Total-force RMSE is 0.01026 N. |
| Nominal zero friction, 0.5 ms | The trajectory stays close to the analytical reference. Windowed normal force ranges from 0.147 to 1.066 N and total-force RMSE reaches 0.08128 N. |

The earliest observed departures are force oscillation and rotation. Impulse and state momentum remain consistent. Contact positions, lifetimes and impulse components on the same clock would distinguish contact-point changes from changes in the response at a persistent point.

### SOFA

| Condition | Support evolution and outcome |
| --- | --- |
| Static, 2 ms | Drift exceeds 1 mm at 0.182 s, rotation crosses its limit at 1.732 s, and solver rows first disappear in the window at 1.842 s. Total-force RMSE is 0.46190 N. |
| Static, 1 ms | Drift exceeds 1 mm at 0.363 s and rotation crosses its limit at 1.697 s. Solver rows disappear at 1.850 s. Total-force RMSE is 0.64137 N. |
| Static, 0.5 ms | Drift exceeds 1 mm at 0.7225 s and rotation crosses its limit at 1.787 s. Solver rows persist through the window. Total-force RMSE is 0.47658 N. |
| Sliding, 2 ms | Normal support fluctuates, solver rows disappear at 1.160 s, and rotation crosses its limit at 1.182 s. Total-force RMSE is 0.78530 N. Velocity error also exceeds its limit. |
| Sliding, 1 ms | Sliding position and velocity pass. Near 1.574 s solver rows disappear and rotation exceeds its limit. Total-force RMSE is 0.66807 N. |
| Sliding, 0.5 ms | Sliding position and velocity pass. Rotation crosses its limit at 1.383 s and solver rows disappear at 1.392 s. Total-force RMSE is 0.73502 N. |
| Nominal zero friction, 2 ms | The trajectory passes. Single-step force deviation in the scoring window exceeds 0.01 N from 1.076 s. Total-force RMSE is 0.27914 N. |
| Nominal zero friction, 1 ms | The trajectory passes. Step force departs from the reference at 1.346 s. Total-force RMSE is 0.09261 N. |
| Nominal zero friction, 0.5 ms | The trajectory passes. Step force departs from the reference near 1.666 s. Total-force RMSE is 0.08400 N. |

The earliest observed departures are contact support and static retention. Solver rows and state increments agree through the momentum check. Native OBB contact positions and constraint gaps would distinguish collision generation, constraint response and contact-distance effects. Single-step force deviations locate the onset of a departure. The pass criterion uses windowed RMSE.

### Disabled-collision control

All three cubes crossed the incline with no contact records. Bullet and SOFA passed the stepwise free-fall velocity check. Chaos first exceeded the 1e-4 m/s limit at 1.431 s and ended near −19.61966 m/s. Replaying the velocity update with single-precision centimeter-unit accumulation tracks the complete native velocity to a maximum error of 2.4e-9 m/s. The strict check retains this control as invalid.

## Data and reproduction

```{raw} html
<p><a href="_static/incline-extension/native-v1.zip">Download the three-engine native archive</a> · <a href="_static/incline-extension/chaos-results.json">Chaos scores</a> · <a href="_static/incline-extension/bullet-results.json">Bullet scores</a> · <a href="_static/incline-extension/sofa-results.json">SOFA scores</a> · <a href="_static/incline-extension/manifest.json">Exact manifest</a></p>
```

The ZIP contains 30 records, stepwise states and impulses, native readbacks, source hashes and the batch receipt. Its SHA-256 is `cb254c4048d2dc8d17737d5b809ee1ca30c73dce174e009e5414da01bfd0b174`. [Run and plot commands](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/INCLINE_EXTENSION.md)
