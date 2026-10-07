# Discrete contact prediction results

[中文](impact-discrete-results.zh-CN.md)

All 54 unique historical records pass both frozen full-rollout and one-step prediction limits; zero new native collision runs. Full prediction initializes once. Maximum position, velocity and force errors are 4.34e-15 m, 7.30e-15 m/s and 1.39e-11 N. One-step maxima are 6.94e-18 m, 8.88e-16 m/s and 1.25e-12 N. Limits remain 1e-10 m, 1e-9 m/s and 1e-6 N respectively.

The source-derived isolated undamped contact and velocity-first Euler map explain these records. At s h²=1 the active matrix cubed equals −I, preserving near-exact rebound endpoints across the four selected entry phases. This supports a specific discrete mechanism, not real-material accuracy or a universal timestep recommendation.

Across the 12 z=1 cases, sampled deviations from the continuous spring reference reach 0.4597 m/s in velocity, 158.53 N in force and 1 J in kinetic-plus-spring-energy drift. Group extrema can come from different records; every case is shown below. These are discretization diagnostics against a declared continuous compliant model, not measured force errors. For grasping, endpoint retention/load support and transient load/slip require separate acceptance; rebound endpoints alone cannot qualify the entire contact response.

[Frozen derivation and protocol](impact-discrete-protocol.md) · [Complete JSON](evidence/impact-discrete/results.json). Protocol code5b32b4a15dbdec1c658d82eef99061696513df0c was frozen before scoring; Issue105 preregistration6048854594. This is a retrospective audit motivated by known endpoints, not a held-out or hardware test. Scoring took0.7461 s; bounded service1.463 s,16 GiB/two CPUs/128 tasks/no swap/1800-second limit. Costs are observational, not a speed ranking.

The table gives absolute maximum rollout residuals and continuous-reference diagnostics. JSON retains one-step residuals, contact durations and historical endpoint verdicts. Repository validation is tracked in [Issue #105](https://github.com/huangkiki/Dexlab/issues/105) and the versioned release validation attachment.

| Case | s (s⁻²) | h (ms) | Phase | Rollout Δx (m) | Rollout Δv (m/s) | Rollout ΔF (N) | Continuous Δv (m/s) | Continuous ΔF (N) | Energy Δ (J) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| impact-01 | 10000 | 1 | 0 | 2.776e-17 | 2.22e-16 | 1.249e-12 | 0.01234 | 0.0338 | 0.003289 |
| impact-02 | 10000 | 0.5 | 0 | 6.939e-18 | 1.804e-16 | 1.249e-12 | 0.00621 | 0.008444 | 0.001603 |
| impact-03 | 10000 | 0.25 | 0 | 6.939e-18 | 3.678e-16 | 1.249e-12 | 0.003115 | 0.002111 | 0.000791 |
| impact-04 | 10000 | 1 | 0 | 2.776e-17 | 5.291e-16 | 1.249e-12 | 0.02469 | 0.06759 | 0.01316 |
| impact-05 | 10000 | 0.5 | 0 | 6.939e-18 | 3.886e-16 | 1.249e-12 | 0.01242 | 0.01689 | 0.00641 |
| impact-06 | 10000 | 0.25 | 0 | 6.939e-18 | 4.441e-16 | 1.249e-12 | 0.00623 | 0.004221 | 0.003164 |
| impact-07 | 10000 | 1 | 0 | 5.204e-18 | 3.331e-16 | 1.249e-12 | 0.04937 | 0.1352 | 0.05262 |
| impact-08 | 10000 | 0.5 | 0 | 3.469e-18 | 2.22e-16 | 1.249e-12 | 0.02484 | 0.03378 | 0.02564 |
| impact-09 | 10000 | 0.25 | 0 | 1.388e-17 | 4.441e-16 | 1.249e-12 | 0.01246 | 0.008442 | 0.01266 |
| stiffness-01 | 100000 | 1 | 0 | 0 | 1.11e-16 | 4.974e-14 | 0.03836 | 1.088 | 0.01158 |
| stiffness-02 | 100000 | 0.5 | 0 | 0 | 5.551e-17 | 2.132e-14 | 0.01941 | 0.2682 | 0.005354 |
| stiffness-03 | 100000 | 0.25 | 0 | 0 | 1.11e-16 | 3.197e-14 | 0.009786 | 0.06682 | 0.002571 |
| stiffness-04 | 100000 | 1 | 0 | 0 | 2.22e-16 | 7.105e-14 | 0.07672 | 2.176 | 0.04633 |
| stiffness-05 | 100000 | 0.5 | 0 | 0 | 1.11e-16 | 7.816e-14 | 0.03882 | 0.5364 | 0.02142 |
| stiffness-06 | 100000 | 0.25 | 0 | 0 | 1.11e-16 | 5.684e-14 | 0.01957 | 0.1336 | 0.01028 |
| stiffness-07 | 100000 | 1 | 0 | 0 | 4.441e-16 | 1.137e-13 | 0.1534 | 4.351 | 0.1853 |
| stiffness-08 | 100000 | 0.5 | 0 | 0 | 2.22e-16 | 1.137e-13 | 0.07765 | 1.073 | 0.08566 |
| stiffness-09 | 100000 | 0.25 | 0 | 0 | 2.22e-16 | 8.527e-14 | 0.03915 | 0.2673 | 0.04114 |
| stiffness-10 | 1000000 | 1 | 0 | 0 | 1.943e-16 | 3.126e-13 | 0.1149 | 39.63 | 0.0625 |
| stiffness-11 | 1000000 | 0.5 | 0 | 1.388e-17 | 6.939e-15 | 1.381e-11 | 0.06044 | 8.439 | 0.02051 |
| stiffness-12 | 1000000 | 0.25 | 0 | 0 | 1.11e-16 | 1.421e-13 | 0.03045 | 2.135 | 0.008782 |
| stiffness-13 | 1000000 | 1 | 0 | 0 | 4.996e-16 | 3.979e-13 | 0.2298 | 79.26 | 0.25 |
| stiffness-14 | 1000000 | 0.5 | 0 | 1.388e-17 | 7.3e-15 | 7.418e-12 | 0.1209 | 16.88 | 0.08203 |
| stiffness-15 | 1000000 | 0.25 | 0 | 6.939e-18 | 1.776e-15 | 6.992e-12 | 0.06089 | 4.269 | 0.03513 |
| stiffness-16 | 1000000 | 1 | 0 | 0 | 1.11e-15 | 7.958e-13 | 0.4597 | 158.5 | 1 |
| stiffness-17 | 1000000 | 0.5 | 0 | 8.604e-16 | 3.997e-15 | 7.105e-12 | 0.2418 | 33.76 | 0.3281 |
| stiffness-18 | 1000000 | 0.25 | 0 | 0 | 2.22e-16 | 2.558e-13 | 0.1218 | 8.539 | 0.1405 |
| phase-01 | 1000000 | 1 | 0.25 | 0 | 1.665e-16 | 1.137e-13 | 0.1071 | 32.92 | 0.03516 |
| phase-02 | 1000000 | 1 | 0.5 | 0 | 5.551e-17 | 1.99e-13 | 0.1073 | 24.62 | 0.03125 |
| phase-03 | 1000000 | 1 | 0.75 | 0 | 3.053e-16 | 1.137e-13 | 0.1087 | 12.75 | 0.03516 |
| phase-04 | 1000000 | 0.5 | 0.25 | 6.939e-18 | 1.665e-16 | 1.705e-13 | 0.05683 | 7.481 | 0.01691 |
| phase-05 | 1000000 | 0.5 | 0.5 | 6.939e-18 | 2.29e-16 | 1.137e-13 | 0.05823 | 6.853 | 0.01489 |
| phase-06 | 1000000 | 0.5 | 0.75 | 1.499e-15 | 1.11e-16 | 1.421e-13 | 0.05944 | 4.736 | 0.01537 |
| phase-07 | 1000000 | 0.25 | 0.25 | 0 | 1.11e-16 | 9.948e-14 | 0.0301 | 1.852 | 0.007959 |
| phase-08 | 1000000 | 0.25 | 0.5 | 0 | 6.245e-17 | 1.279e-13 | 0.03025 | 2.049 | 0.007799 |
| phase-09 | 1000000 | 0.25 | 0.75 | 4.337e-15 | 5.218e-15 | 1.387e-11 | 0.03034 | 1.905 | 0.008074 |
| phase-10 | 1000000 | 1 | 0.25 | 0 | 1.527e-16 | 1.563e-13 | 0.2141 | 65.83 | 0.1406 |
| phase-11 | 1000000 | 1 | 0.5 | 0 | 5.274e-16 | 3.979e-13 | 0.2146 | 49.24 | 0.125 |
| phase-12 | 1000000 | 1 | 0.75 | 0 | 2.776e-16 | 1.137e-13 | 0.2173 | 25.51 | 0.1406 |
| phase-13 | 1000000 | 0.5 | 0.25 | 1.388e-17 | 2.22e-16 | 3.411e-13 | 0.1137 | 14.96 | 0.06763 |
| phase-14 | 1000000 | 0.5 | 0.5 | 0 | 1.249e-16 | 3.411e-13 | 0.1165 | 13.71 | 0.05957 |
| phase-15 | 1000000 | 0.5 | 0.75 | 1.388e-17 | 1.665e-16 | 3.411e-13 | 0.1189 | 9.472 | 0.06148 |
| phase-16 | 1000000 | 0.25 | 0.25 | 0 | 1.11e-16 | 2.274e-13 | 0.0602 | 3.703 | 0.03183 |
| phase-17 | 1000000 | 0.25 | 0.5 | 0 | 2.637e-16 | 2.842e-13 | 0.06049 | 4.098 | 0.0312 |
| phase-18 | 1000000 | 0.25 | 0.75 | 0 | 2.22e-16 | 1.99e-13 | 0.06068 | 3.811 | 0.03229 |
| phase-19 | 1000000 | 1 | 0.25 | 0 | 1.416e-15 | 4.547e-13 | 0.4282 | 131.7 | 0.5625 |
| phase-20 | 1000000 | 1 | 0.5 | 0 | 1.277e-15 | 4.547e-13 | 0.4293 | 98.47 | 0.5 |
| phase-21 | 1000000 | 1 | 0.75 | 0 | 6.661e-16 | 2.558e-13 | 0.4347 | 51.02 | 0.5625 |
| phase-22 | 1000000 | 0.5 | 0.25 | 0 | 3.331e-16 | 7.39e-13 | 0.2273 | 29.93 | 0.2705 |
| phase-23 | 1000000 | 0.5 | 0.5 | 0 | 3.886e-16 | 1.023e-12 | 0.2329 | 27.41 | 0.2383 |
| phase-24 | 1000000 | 0.5 | 0.75 | 0 | 5.829e-16 | 9.095e-13 | 0.2378 | 18.94 | 0.2459 |
| phase-25 | 1000000 | 0.25 | 0.25 | 0 | 4.441e-16 | 5.116e-13 | 0.1204 | 7.406 | 0.1273 |
| phase-26 | 1000000 | 0.25 | 0.5 | 0 | 2.22e-16 | 2.842e-13 | 0.121 | 8.195 | 0.1248 |
| phase-27 | 1000000 | 0.25 | 0.75 | 0 | 2.22e-16 | 5.684e-13 | 0.1214 | 7.622 | 0.1292 |

## Reproduction / 复算

Retrieve `elastic-impact-raw-v1.zip` from [v0.44.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.0), `impact-stiffness-raw-v1.zip` from [v0.44.1](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.1), and `impact-phase-raw-v1.zip` from [v0.44.2](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.2). 核验[刚度归档哈希](evidence/impact-stiffness/archive.json)和[相位归档哈希](evidence/impact-phase/archive.json)，分别解压到包含manifest.json的baseline、stiffness、phase目录。Verify the linked archive hashes, then extract into those separate directories containing manifest.json.

```bash
python -m dexlab.impact_discrete --baseline baseline --stiffness stiffness --phase phase --evidence docs/evidence --output audit.json
```

No engine import/run is required. Scientific fields must match; wall time varies. 无需启动物理引擎；科学字段应一致，耗时随运行环境变化。原始归档沿用既有发布，不重复打包。
