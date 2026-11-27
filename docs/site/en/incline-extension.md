# Incline comparison with Chaos, Bullet and SOFA

Each backend completed the nine original conditions and one disabled-collision control. **Chaos passed all three nominal-zero-friction cases. Bullet passed two static cases and one nominal-zero-friction case. SOFA's nine records passed the momentum check and all exceeded at least one physical limit.** {ref}`Ten-engine matrix and overlaid curves <incline>`

| Frozen configuration | Static | Sliding | Nominal zero friction | Pass / fail / invalid |
| --- | ---: | ---: | ---: | --- |
| Chaos / UE 5.7.1, Linux Editor | 0/3 | 0/3 (3 invalid) | 3/3 | 3 / 3 / 3 |
| Bullet / PyBullet 3.2.7, CPU DIRECT | 2/3 | 0/3 | 1/3 | 3 / 6 / 0 |
| SOFA 26.06.00, rigid OBB / block Gauss–Seidel | 0/3 | 0/3 | 0/3 | 0 / 9 / 0 |

(incline-invalid-records)=
## Why a record is marked invalid

**A failure means the record passed the consistency checks and the measured motion or force exceeded an experiment limit. An invalid record did not pass the checks that precede scoring.** All three Chaos sliding runs reached two seconds. The scorer checks the whole trace. Any step where impulse and momentum change disagree beyond tolerance invalidates the record.

Think of each step as having two ledgers. The velocity ledger uses the velocities before and after the step to compute the momentum change, `m × (v_after − v_before)`. The force ledger adds the gravity and contact impulses over that same interval. Both quantities have direction. The check measures the length of the three-dimensional difference. The analogy corresponds to two sets of measured quantities on one physics step. The recorded values include numerical rounding, and the frozen limit allows a difference of up to **0.100 µN·s (1e-7 N·s)** on each step. Chaos uses the native velocity impulse and the position correction converted over the same interval.

Take **step 1597 of the 1 ms run**. The numbers below show horizontal x and vertical z. The y component is negligible. The velocity ledger gives **(295.00000, −206.56250) µN·s**. The contact and gravity ledger gives **(295.04451, −206.47272) µN·s**. The difference is about **(−0.04451, −0.08978) µN·s**, with a length of **0.100204 µN·s**. The adjacent steps give **0.093713** and **0.096117 µN·s**. These digits are shown for reproduction.

All three cubes start at rest, flush to the 35° incline, with contact friction μ=0.5. On step one, the tangential force is **−0.136 N** at 2 ms and near zero at 1 and 0.5 ms. The cubes then accelerate downhill. At the first exceedance, each run still reports four contact points and about **0.514 N** of normal support. Tangential force remains below **3e-8 N** in magnitude. The ideal Coulomb sliding reference would give about **−0.257 N** in the tangential direction. The weak tangential resistance is visible before the consistency gate is crossed and remains diagnostic evidence.

| Timestep | First step over the limit and its end time | Downhill speed at start of that step | First / maximum residual (µN·s) | Steps over the limit / total |
| --- | --- | ---: | ---: | ---: |
| 2 ms | 811 / 1.622 s | 7.779 m/s | 0.101099 / 0.110414 | 4 / 1000 |
| 1 ms | 1597 / 1.597 s | 8.980 m/s | 0.100204 / 0.110195 | 152 / 2000 |
| 0.5 ms | 3175 / 1.5875 s | 8.930 m/s | 0.103196 / 0.103613 | 28 / 4000 |

The first scoring gate crossed is **state–impulse consistency**. All three records retain their invalid status, and their trajectories remain available for diagnosis. The engine's particle velocity array stores single-precision values. At the first exceedance, one representable increment in a larger velocity component corresponds to about **0.0391 µN·s** of momentum, enough to affect this check. Rounding the force-predicted end velocity once in the engine's centimeter units takes the 0.5 ms diagnostic below the limit, while steps at 2 and 1 ms still exceed it. The full error budget remains unresolved. A discriminating check needs the gravity update, position correction, velocity impulse and velocities before and after writeback in the same step. The separate {ref}`disabled-collision control <incline-no-floor-control>` crossed the free-fall velocity limit.

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

At 1 and 0.5 ms the static case reads back 0.5 friction, yet its tangential force stays below 1.2e-8 N in magnitude throughout the scoring window. The traces nearly coincide with the frictionless controls. Logging tangential impulse in each first-step solve phase would distinguish friction anchors, iterations and phase selection.

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

(incline-no-floor-control)=
### Disabled-collision control

All three cubes crossed the incline with no contact records. Bullet and SOFA passed the stepwise free-fall velocity check. Chaos first exceeded the 1e-4 m/s limit at 1.431 s and ended near −19.61966 m/s. Replaying the velocity update with single-precision centimeter-unit accumulation tracks the complete native velocity to a maximum error of 2.4e-9 m/s. The strict check retains this control as invalid.

## Data and reproduction

```{raw} html
<p><a href="_static/incline-extension/native-v1.zip">Download the three-engine native archive</a> · <a href="_static/incline-extension/chaos-results.json">Chaos scores</a> · <a href="_static/incline-extension/bullet-results.json">Bullet scores</a> · <a href="_static/incline-extension/sofa-results.json">SOFA scores</a> · <a href="_static/incline-extension/manifest.json">Exact manifest</a></p>
```

The ZIP contains 30 records, stepwise states and impulses, native readbacks, source hashes and the batch receipt. Its SHA-256 is `cb254c4048d2dc8d17737d5b809ee1ca30c73dce174e009e5414da01bfd0b174`. [Run and plot commands](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/INCLINE_EXTENSION.md)
