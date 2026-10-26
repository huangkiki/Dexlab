# Wuji sphere pinch: more grip force did not qualify holding

**This experiment has not established a qualified solver failure.** The fixed-wrist Wuji hand kept contact with the sphere in the last two attempts, but maximum displacement was **2.459 mm and 2.734 mm**, above the prospectively frozen **2 mm** criterion. Two point contacts also leave a rotational direction without a contact-moment reaction. The evidence calls for further grasp/contact-model diagnosis, not a general engine ranking.

![Complete 4.4-second v3 saved-state replay; sphere orientation markings are visual only](../../evidence/wuji-contact/v3.gif)

The real-time replay includes preparation, failed holding and opening. Crosses were **added as a visual orientation texture during replay**; collision geometry and the physical trajectory are unchanged. Do not estimate angular speed from this GIF. Raw observations are 2 kHz, video is 30 fps and GIF is 15 fps. [Full video](../../evidence/wuji-contact/v3.mp4) · [Provenance and frame map](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/v3-render.json).

## Rescore the existing record first

Run from the DexLab checkout root with [uv](https://docs.astral.sh/uv/getting-started/installation/). This uses isolated Python 3.12.12 with NumPy and Matplotlib dependencies; no simulation engine, GPU, hardware or model API key is required. The first command downloads dependencies and the [immutable raw bundle](https://github.com/huangkiki/Dexlab/releases/tag/wuji-contact-evidence-v1); the second runs offline.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/evidence-bundle.json \
  --destination downloads/wuji-contact-v1
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py downloads/wuji-contact-v1/runs/02-v3-hold-release \
  --output results/wuji-contact-v1-rescore
```

Open `measurements.png` for motion, native contact force and actual actuator effort. CSV retains the complete series; JSON separates outcomes and identifies inputs by hash. Expect `record_integrity_pass: true`, `numerical_balance_pass: true` and **`hold_pass: false`**. That is the retained experiment failure, not a failed rescore. Select `00-hold-release` or `01-v2-hold-release` for earlier attempts and use a new output directory each time.

![Independent full-record v3 rescore; green denotes the scored hold](../../evidence/wuji-contact/v3-measurements.png)

## What the three attempts establish

The synthetic sphere has radius 10 mm, mass 20 g and inertia `2mr²/5`. The wrist is fixed. Close during 0.2–0.8 s, remove all preparation forces at 1.0 s, score 1.2–3.2 s, then open and observe through 4.4 s. Displacement always refers to the **1.0 s** state. Neither the reference nor the threshold moved. The 2 mm bound is 10% of sphere diameter: a declared task tolerance, not a universal accuracy standard.

| Cohort | Prospectively defined setting | Maximum hold displacement | Outcome and first known problem |
| --- | --- | ---: | --- |
| v1 | Convex wrist, explicit sampled PD | 24.422 m | Initial wrist/thumb-root overlap was already 4.981 mm; the unconstrained controller linearization was also unstable. Invalid inputs cannot establish solver failure. |
| v2 | Same-source native SDF wrist and implicit sampled PD; 2 ms control | 2.459 mm | Continuous bilateral contact, but failed 2 mm holding. Two input corrections do not isolate one algorithmic cause. |
| v3 | Only shorten v2 control period to 0.5 ms; native step remains 0.5 ms | 2.734 mm | Grip force increased without improving displacement; this control-rate hypothesis was not supported. |

Each cohort executed one complete positive control and stopped before its five remaining cases. **Individual unloading, open-hand, contact-disabled and nominal zero-friction controls remain unqualified in this round.** Not-run cases are not passes. The original v1 report counted falling clear as successful release. It remains preserved alongside a corrected report requiring a qualified preceding hold. [All attempts, not-run cases and cost](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/results.json).

## Contact structure exposed by the saved trajectory

This is **post-hoc diagnosis**, without changing acceptance or collecting new physics.

| Hold observation | v2 | v3 |
| --- | ---: | ---: |
| Bilateral effective contact | 100% | 100% |
| Mean pad normal forces | 0.265 / 0.280 N | 0.758 / 0.772 N |
| Tangential/normal force ratio, nominal friction coefficient 1.0 | 0.321–0.472 | 0.101–0.240 |
| Actuator saturation / other-body support | Both zero | Both zero |
| Maximum fixed pad-reference midpoint motion, sampled every 10 ms | 0.186 mm | 0.093 mm |
| Sphere motion relative to that midpoint, same sampling | 2.345 mm | 2.696 mm |
| Active contact count / force-only wrench-map rank at every hold step | 2 / 5 | 2 / 5 |

All 4,000 hold steps in each record have exactly two effective pad contact points and zero intrinsic native contact moment. Arbitrary forces at two points cannot supply moment about their connecting line. With contact points `p1,p2`, center `c` and radius `r`, the map is:

```text
G = [ I                  I               ]
    [ skew(p1-c) / r     skew(p2-c) / r  ]
```

After length normalization by radius, G has rank 5 throughout both records. Center-to-contact-line distance is 0.298–0.774 mm and 0.310–0.985 mm respectively. Gravity has nonzero moment about that line, with peak magnitude about 0.119 and 0.154 mN·m. **Increasing normal force does not create the missing moment direction.** Recorded sphere orientation also changes substantially; an untextured sphere can conceal this motion visually.

Rank 5 does not imply every such grasp must fail: special gravity alignments can still balance. Contacts migrate and fingers move, so this does not uniquely explain all displacement, prove a fixed-pivot pendulum model or validate real compliant pads. [Executable diagnosis and equations](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/diagnose.py) · [Results](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/diagnosis.json).

## Numerical consistency is separate from task and hardware validation

The independent scorer reconstructs world forces from native contact frames and checks `mΔv = Δt(Fcontact + mg + Fprep)`. Maximum v2/v3 residual is about `1.65e-17 N·s`. An additional isotropic-sphere angular-impulse audit has residual about `1.4e-20 N·m·s`. Free-joint angular velocity is converted from body to world coordinates using the convention in the [official MuJoCo documentation](https://mujoco.readthedocs.io/en/stable/overview.html#floating-objects).

These checks target units, frames, signs and observation epochs; they do not validate real contact materials. No numerical warnings were recorded and v3 used at most five solver iterations, but those observations do not replace termination-reason or convergence studies. The measured failure is the fixture's declared holding stability criterion.

## Reproduction, corrected entry points and remaining scope

[Native reproduction instructions](https://github.com/huangkiki/Dexlab/tree/main/demos/wuji-contact) cover pinned dependencies, asset checks, exclusive output, scoring and replay. The unmodified native engine is MuJoCo 3.17.0, CPU/float64. Friction and control gains are synthetic. Hand inertias, joints and effort caps come from the pinned Wuji assets; the native SDF wrist and convex finger meshes are disclosed collision approximations.

The entry now checks **all initial hand contacts** and rejects penetration beyond the original 1 mm tolerance before any physics step. It also corrects active-release qualification, repairs the asset-download manifest and separates state/force epochs and actual control periods. V3 records core/binding versions and native binary hashes; those new fields are absent from earlier records and cannot be retroactively claimed as observed then.

The three native processes consumed 740.956 s. The original 12-start / 7,200-second package retains 9 starts and 6,459.044 s; there is no new allowance. V3's outer observer exited while the bounded native service continued and completed; accounting was recovered from actual final telemetry without a duplicate run. Operational and physical outcomes remain separate.

Only this native development path has run. The [applicability matrix](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/applicability.json) retains other engines and historical configurations as not-run here. This result does not complete [#251](https://github.com/huangkiki/Dexlab/issues/251)'s positive and negative controls, or begin [#48](https://github.com/huangkiki/Dexlab/issues/48)'s contact switching, controlled rotation and ten post-development conditions.
