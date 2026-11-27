# Latest stable incline retest

Versions were checked on 2026-11-27. Each engine reran nine conditions with its frozen profile and one control with support collision disabled.

The same 4 cm, 64 g cube starts at rest for each 2 s run. Timesteps are 2, 1 and 0.5 ms. On a 15° incline it should stay put at friction 0.5 and accelerate freely at friction zero. On a 35° incline at friction 0.5 it should slide.

The scorer verifies that the measured state and force agree before testing motion and load against the limits. Each pass earns one point. Valid failures and invalid records earn zero. Disabled-collision controls are scored separately.

{ref}`Ten-engine ranking <incline>` · [Native time series and checksums](https://github.com/huangkiki/Dexlab/releases/download/milestone-2026-11-27-incline-stable-versions/dexlab-incline-native-2026-11-27.zip)

## Results by condition

| Engine version | Static | Sliding | Nominal zero friction | Score |
| --- | --- | --- | --- | ---: |
| SuperDex 1.0.1 | Pass / Pass / Fail | Pass / Pass / Pass | Pass / Pass / Pass | 8/9 |
| PhysX 5.9.1 | Pass / Pass / Pass | Invalid / Pass / Pass | Pass / Pass / Fail | 7/9 |
| Genesis 1.5.0 | Pass / Pass / Pass | Pass / Pass / Pass | Fail / Fail / Fail | 6/9 |
| Drake 1.59.0 | Pass / Pass / Pass | Fail / Fail / Fail | Pass / Pass / Pass | 6/9 |
| RaiSim 2.18.1 | Pass / Pass / Pass | Fail / Fail / Fail | Pass / Pass / Pass | 6/9 |
| Chaos 5.8.4 | Fail / Fail / Fail | Fail / Pass / Pass | Pass / Pass / Pass | 5/9 |
| MuJoCo 4.0.1 | Fail / Fail / Fail | Fail / Fail / Fail | Pass / Pass / Pass | 3/9 |
| Bullet 3.2.7 | Pass / Pass / Fail | Fail / Fail / Fail | Fail / Pass / Fail | 3/9 |
| Newton Physics 1.8.0 | Fail / Fail / Pass | Invalid / Invalid / Invalid | Invalid / Invalid / Invalid | 1/9 |
| SOFA 26.06.00 | Fail / Fail / Fail | Fail / Fail / Fail | Fail / Fail / Fail | 0/9 |

Within each column, entries follow 2, 1 and 0.5 ms.

Chaos moved from 3/9 on UE 5.7.1 to 5/9 on UE 5.8.4. All three 35° sliding traces now pass the state–impulse check. At 1 and 0.5 ms the cubes also meet the physical limits. At 2 ms the cube still has four contact points at 0.5 s. Its normal support is 0.48458 N, and the measured tangential force is −0.24229 N. The contact-force residual over the scoring window is 0.03337 N RMS against a 0.01 N limit. Resolving the origin of the support deficit requires the per-contact velocity impulse and position correction at the same solver step.

## Disabled-collision controls

Nine engines' controls were rejected as expected. The Chaos cube starts at rest on a 15° incline, reports zero contacts over 2,000 steps, and ends at −19.61037 m. The velocity check first exceeds its limit at step 1,431. The maximum difference at 2 s is 0.00034517 m/s against the frozen 0.0001 m/s limit.

Chaos stores velocity in single precision at each step. Replaying the update with the native timestep and centimeter units matches the full native velocity trace within 3.6e-15 m/s. The state and contact CSVs are byte-identical in 5.7.1 and 5.8.4, and both control records retain their invalid verdict.

## First observed discrepancies

An instantaneous threshold crossing locates the deviation in time. The final verdict uses the full scoring window specified by the protocol.

The six invalid Newton Physics traces first exceed the allowed difference between one position increment and the reported closing velocity times the timestep. Contacts and force are already present at those steps. A check of the solver's position and velocity writeback at the same substep would locate the remaining source of that difference. The PhysX record first fails at 0.938 s. Its impulse's largest orthogonal component is 0.10090 nN·s against the analytic plane normal and 0.01505 nN·s against the measured native normal. The native-vs-analytic normal angle is about 2.19e-7 rad.

Genesis reads back friction of 0.01 on the first supported step of each requested-zero case. The corresponding tangential force points uphill. Over the scoring window, the loss of downhill acceleration is about 0.09476 m/s², consistent with friction of 0.01 on the 15° plane.

### MuJoCo

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 2 ms | 1.472 | Static displacement | 1.00082 / 1 mm | 4 contacts · Fₙ 0.606447 N · Fₜ -0.162497 N | Fail |
| 15° · μ=0.5 · 1 ms | 1.508 | Static displacement | 1.00023 / 1 mm | 4 contacts · Fₙ 0.606447 N · Fₜ -0.162497 N | Fail |
| 15° · μ=0.5 · 0.5 ms | 1.5265 | Static displacement | 1.00024 / 1 mm | 4 contacts · Fₙ 0.606447 N · Fₜ -0.162497 N | Fail |
| 35° · μ=0.5 · 2 ms | 0.196 | Rotation | 0.011904 / 0.01 rad | 2 contacts · Fₙ 0.507276 N · Fₜ -0.253638 N | Fail |
| 35° · μ=0.5 · 1 ms | 0.273 | Rotation | 0.0102801 / 0.01 rad | 1 contacts · Fₙ 0.703488 N · Fₜ -0.338388 N | Fail |
| 35° · μ=0.5 · 0.5 ms | 0.2055 | Rotation | 0.0102052 / 0.01 rad | 1 contacts · Fₙ 0.36362 N · Fₜ -0.18045 N | Fail |

### SuperDex

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 0.5 ms | 1.5865 | Static displacement | 1.00006 / 1 mm | 6 contacts · Fₙ 0.606447 N · Fₜ -0.162497 N | Fail |

### Genesis

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0 · 2 ms | 0.004 | Effective contact friction | 0.01 / 0 | 4 contacts · Fₙ 0.727736 N · Fₜ -0.00727736 N | Fail |
| 15° · μ=0 · 1 ms | 0.002 | Effective contact friction | 0.01 / 0 | 4 contacts · Fₙ 0.657257 N · Fₜ -0.00657257 N | Fail |
| 15° · μ=0 · 0.5 ms | 0.001 | Effective contact friction | 0.01 / 0 | 4 contacts · Fₙ 0.623247 N · Fₜ -0.00623247 N | Fail |

### Newton Physics

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 2 ms | 0.5 | Static speed | 1.17761 / 1 mm/s | 4 contacts · Fₙ 0.606354 N · Fₜ -0.162484 N | Fail |
| 15° · μ=0.5 · 1 ms | 1.698 | Static displacement | 1.00002 / 1 mm | 4 contacts · Fₙ 0.605837 N · Fₜ -0.161957 N | Fail |
| 35° · μ=0.5 · 2 ms | 0.002 | Position–velocity consistency | 59.228 / 53.775 nm | 4 contacts, z change -3991.65 vs -3932.42 nm | Invalid |
| 35° · μ=0.5 · 1 ms | 0.003 | Position–velocity consistency | 55.753 / 53.771 nm | 4 contacts, z change -2987.68 vs -2931.93 nm | Invalid |
| 35° · μ=0.5 · 0.5 ms | 0.001 | Position–velocity consistency | 61.931 / 53.771 nm | 4 contacts, z change -495.464 vs -433.532 nm | Invalid |
| 15° · μ=0 · 2 ms | 0.046 | Position–velocity consistency | 57.261 / 55.994 nm | 4 contacts, z change -60457.7 vs -60400.5 nm | Invalid |
| 15° · μ=0 · 1 ms | 0.002 | Position–velocity consistency | 57.342 / 56.571 nm | 4 contacts, z change -1315.03 vs -1257.69 nm | Invalid |
| 15° · μ=0 · 0.5 ms | 0.001 | Position–velocity consistency | 59.763 / 56.571 nm | 4 contacts, z change -329.688 vs -269.925 nm | Invalid |

### PhysX

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 35° · μ=0.5 · 2 ms | 0.938 | Normal-impulse direction | 0.100897 / 0.100000 nN·s | 4 contacts, native normal (0.5735766, 0, 0.8191519) | Invalid |
| 15° · μ=0 · 0.5 ms | 0.921 | Force balance (instantaneous) | 0.0104006 / 0.01 N | 4 contacts · Fₙ 0.596046 N · Fₜ -2.68976e-08 N | Fail |

### Drake

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 35° · μ=0.5 · 2 ms | 0.5 | Force balance (instantaneous) | 0.867641 / 0.01 N | 1 contacts · Fₙ 1.22585 N · Fₜ -0.753624 N | Fail |
| 35° · μ=0.5 · 1 ms | 0.5 | Force balance (instantaneous) | 0.198963 / 0.01 N | 1 contacts · Fₙ 0.335636 N · Fₜ -0.169587 N | Fail |
| 35° · μ=0.5 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.207688 / 0.01 N | 1 contacts · Fₙ 0.326262 N · Fₜ -0.168959 N | Fail |

### Chaos

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 2 ms | 0.224 | Rotation | 0.0100792 / 0.01 rad | 4 contacts · Fₙ 0.606444 N · Fₜ -0.162498 N | Fail |
| 15° · μ=0.5 · 1 ms | 0.312 | Static displacement | 1.00094 / 1 mm | 4 contacts · Fₙ 0.606432 N · Fₜ -0.162509 N | Fail |
| 15° · μ=0.5 · 0.5 ms | 0.623 | Static displacement | 1.00019 / 1 mm | 4 contacts · Fₙ 0.606511 N · Fₜ -0.162445 N | Fail |
| 35° · μ=0.5 · 2 ms | 0.5 | Force balance (instantaneous) | 0.0332199 / 0.01 N | 4 contacts · Fₙ 0.484584 N · Fₜ -0.242292 N | Fail |

### Bullet

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.014463 / 0.01 N | 3 contacts · Fₙ 0.613046 N · Fₜ -0.151681 N | Fail |
| 35° · μ=0.5 · 2 ms | 0.242 | Rotation | 0.0100975 / 0.01 rad | 1 contacts · Fₙ 0.963964 N · Fₜ -0.481931 N | Fail |
| 35° · μ=0.5 · 1 ms | 0.335 | Rotation | 0.0101218 / 0.01 rad | 2 contacts · Fₙ 0.503738 N · Fₜ -0.25186 N | Fail |
| 35° · μ=0.5 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.38519 / 0.01 N | 2 contacts · Fₙ 0.858786 N · Fₜ -0.429335 N | Fail |
| 15° · μ=0 · 2 ms | 1.18 | Force balance (instantaneous) | 0.221127 / 0.01 N | 1 contacts · Fₙ 0.38532 N · Fₜ 2.77556e-17 N | Fail |
| 15° · μ=0 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.45985 / 0.01 N | 1 contacts · Fₙ 0.146596 N · Fₜ 6.93889e-18 N | Fail |

### SOFA

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 15° · μ=0.5 · 2 ms | 0.182 | Static displacement | 1.00201 / 1 mm | 1 contacts · Fₙ 0.771246 N · Fₜ -0.385623 N | Fail |
| 15° · μ=0.5 · 1 ms | 0.363 | Static displacement | 1.00428 / 1 mm | 1 contacts · Fₙ 0.76908 N · Fₜ -0.38454 N | Fail |
| 15° · μ=0.5 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.27513 / 0.01 N | 1 contacts · Fₙ 0.443916 N · Fₜ 0.059495 N | Fail |
| 35° · μ=0.5 · 2 ms | 0.502 | Force balance (instantaneous) | 0.213765 / 0.01 N | 1 contacts · Fₙ 0.323099 N · Fₜ -0.161549 N | Fail |
| 35° · μ=0.5 · 1 ms | 0.5 | Force balance (instantaneous) | 0.300926 / 0.01 N | 1 contacts · Fₙ 0.24514 N · Fₜ -0.12257 N | Fail |
| 35° · μ=0.5 · 0.5 ms | 0.5 | Force balance (instantaneous) | 0.611096 / 0.01 N | 1 contacts · Fₙ 1.06088 N · Fₜ -0.530439 N | Fail |
| 15° · μ=0 · 2 ms | 1.076 | Force balance (instantaneous) | 0.36373 / 0.01 N | 1 contacts · Fₙ 0.242717 N · Fₜ 6.93889e-18 N | Fail |
| 15° · μ=0 · 1 ms | 1.346 | Force balance (instantaneous) | 0.363333 / 0.01 N | 1 contacts · Fₙ 0.243114 N · Fₜ 6.93889e-18 N | Fail |
| 15° · μ=0 · 0.5 ms | 1.6655 | Force balance (instantaneous) | 0.361772 / 0.01 N | 1 contacts · Fₙ 0.244675 N · Fₜ -6.93889e-18 N | Fail |

### RaiSim

| Initial condition | Time (s) | First observation | Measured / limit | Synchronized state or force | Verdict |
| --- | ---: | --- | ---: | --- | --- |
| 35° · μ=0.5 · 2 ms | 0.056 | Rotation | 0.0107059 / 0.01 rad | 4 contacts · Fₙ 0.514293 N · Fₜ -0.253814 N | Fail |
| 35° · μ=0.5 · 1 ms | 0.055 | Rotation | 0.0102451 / 0.01 rad | 4 contacts · Fₙ 0.514298 N · Fₜ -0.253824 N | Fail |
| 35° · μ=0.5 · 0.5 ms | 0.055 | Rotation | 0.0101602 / 0.01 rad | 4 contacts · Fₙ 0.514295 N · Fₜ -0.253822 N | Fail |
