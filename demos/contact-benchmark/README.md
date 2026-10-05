# Contact-mechanics development experiments

[English](README.md) | [简体中文](README.zh-CN.md)

Three UniLab tasks measure planar sliding, normal loading/unloading, and two-pad cylinder loading/release. MuJoCo 3.11.0 and SuperDex 1.0.0 FP64 use official native APIs; PhysX uses the qualified UniSim/Isaac Sim 5.1 adapter. Engine sources and binaries are unchanged.

**These are uncalibrated development experiments, not held-out results or engine-accuracy rankings.** Failures are retained. New [synthetic response–cost](RESPONSE_COST.md) and [prospective paired transfer](TRANSFER.md) studies preserve all failures. Complete internal cooking/combined-law readback remains unobservable. Real-material calibration belongs to #6, the apple suite to #3; #10 still requires its full acceptance audit.

Normal response now has a separate [force-loading protocol and transfer report](NORMAL_RESPONSE.md): 17 completed development runs, 11 passes and 6 retained failures. Static response matching and settling are scored separately.

![Normal response, drift, load onset, temporal and spatial refinement](media/development-v2.png)

## Experiments and outcomes

| Development experiment | MuJoCo | SuperDex | PhysX |
|---|---:|---:|---:|
| Rest, forward/reverse sliding, zero friction | 4/4 | 4/4 | 4/4 |
| Indentation and complete unloading | 1/1 | 1/1 | 1/1 |
| Original cylinder surface: hold, overload, zero friction and load ramp; each ends with release | 0/4 | 1/4 | 4/4 |
| Refined cylinder surface (4,096 triangles): the same four conditions | — | 4/4 | — |

These counts combine different physical checks and are not a task success rate. Four timestep refinements, one iteration-cap probe and one intermediate mesh refinement failed; an additional material-readback check passed. Of **38 completed experiments, 25 passed and 13 failed**. The [per-run report](evidence/development-v2.json) retains original outcomes, additional offline checks, source/run hashes and timing. These are not independent random trials; no binomial confidence interval is attached.

- **MuJoCo hold:** the 0.2 kg cylinder drifted 1.145 mm, exceeding the original 1 mm limit. Negative controls dropped and eventually entered free fall, but continuing inward pad forces after the object left caused 2.70–3.26 mm pad–pad penetration. The fixture has no travel stop; this declared boundary remains part of the complete score.
- **SuperDex edge contact:** as negative controls left the lower pad edge, object penetration reached 1.38–2.27 mm and peak linear-momentum residuals reached 0.84–7.04 times weight. The overload peak coincided with `STOPPED` status. Reducing 0.5 ms to 0.25/0.125 ms, or increasing the nonlinear iteration cap from 100 to 400, did not remove the failures. These observations do not establish an engine root cause.
- **PhysX:** all four cylinder conditions passed. Peak reference-surface penetration of 0.5275 mm occurred during the first 6 ms of approach and remains included. This does not establish more accurate physical fingertip material.

**Surface discretization:** splitting planar triangles preserves the prism surface, mass/inertia, force commands, 0.5 ms timestep, 100-iteration cap and score thresholds. Increasing triangles from 256 to 1,024 to 4,096 reduced overload peak penetration from 2.267 to 0.858 to 0.481 mm, and momentum residual/weight from 7.036 to 0.216 to 0.000993. The intermediate mesh still failed; the finest mesh passed hold, overload, zero-friction and ramp controls. Defaults retain the original profile; refined cases have separate names. This demonstrates sensitivity to surface discretization for these cases, not a general fix.

Load ramps triggered the motion detector near 2.499, 2.493 and 2.516 N total downward load, respectively. Detection requires COM downward speed above 5 mm/s for 20 ms; inertia and detection delay prevent interpreting this as the exact static-friction limit.

## Physical and control contract

- Plane: 40 mm cube, 0.2 kg; 0.2 s settling followed by 0.5 s measurement. No runtime drive; the declared initial velocity is assigned once at measurement start. The analytical reference assumes a horizontal, non-tipping body with Coulomb friction and no additional dissipation.
- Indentation: the same frictionless cube receives a vertical COM force using actual height/velocity feedback, at a fixed 1 ms control period and 40 N limit. Approach, two loading levels and unloading are recorded. Contact offsets affect signed geometric indentation; its force–displacement secant is not a fingertip material modulus.
- Cylinder: a **64-sided regular prism**, radius 10 mm and half-height 30 mm, with maximum radial faceting error about 12.05 micrometres. It is not an SDF or capsule substitution. Each 0.1 kg pad has one x translation DOF; actual native states are recorded. The object is free, with explicit gravity compensation only before 0.3 s for preparation.
- Each pad receives 4 N inward force; actual normal contact load is checked separately. Nominal friction is 0.3; masses are 0.2 kg for hold and 0.4 kg for overload. Separate controls use zero friction or a 0–4 N added downward ramp. Outward actuation/braking starts at 1.5 s, followed by zero force. There is no object attachment or runtime pose rewriting.
- Baseline timestep is 0.5 ms. Refinement preserves the 1 ms controller period with zero-order-held commands. MuJoCo soft constraints, SuperDex smooth penalties and PhysX TGS use distinct native profiles; matching friction numbers does not establish equivalent full responses.

## Measurements and evidence limits

A common separating-axis evaluator measures regular-prism/box and box/box overlap, including pad–pad collisions. Native contact separation, cooked surfaces and reference geometry remain distinct; full cooking equivalence is unproven.

Each run archives actual poses/velocities, commanded forces, normal/total contact forces, complete native contact observations, solver status, source snapshots and hashes. Offline checks reconcile force ledgers and linear momentum, measured mass/inertia, recorded friction parameters, PhysX worker exit and pre-run source hashes. Legacy SuperDex records mainly cover object friction; new runs read every pad/plane/object friction coefficient and check normal-force consistency with native normals and total forces. Complete contact-combination and cooking coverage remain future work. Contact observations use lossless gzip with legacy JSON support.

Tangential-speed diagnostics evaluate `v + omega × r` for both bodies at native normal-contact locations and project their relative velocity into the tangent plane. Twists/COM poses are actual post-step states; MuJoCo contact points/normals belong to the just-completed solve and may lag by one step. Missing records remain unknown; unloaded samples are not zero slip. Contact IDs are not tracked across frames, so accumulated material-point slip is not reported. PhysX normal contacts and friction anchors remain separate.

Experiments shared a machine with an apple batch. Recorded time includes stepping, observations and IPC; it is not an isolated performance result. PhysX exposes neither a native convergence residual nor clock readback here; time counts synchronous completed steps. Unavailable values are not replaced by zero. Historical adapter construction/query failures and the first cylinder sensor-initialization failure remain in the development directories, outside the completed-physics counts above.

## Run and verify

Complete the repository [installation](../../docs/installation.md). PhysX additionally needs its [adapter and Isaac Sim environment](../physx-contact/README.md). Run from the repository root, using a fresh output directory each time.

```bash
.venv/bin/python -m dexlab.contact_plane_native --engine mujoco \
  --case demos/contact-benchmark/cases/dev-slide.json --output runs/contact-plane
.venv/bin/python -m dexlab.contact_indent_run --engine superdex \
  --case demos/contact-benchmark/cases/dev-indent.json --output runs/contact-indent
.venv/bin/python -m dexlab.contact_pinch_run --engine physx \
  --case demos/contact-benchmark/cases/dev-cylinder-overload.json --output runs/contact-cylinder
.venv/bin/python -m dexlab.contact_pinch_run --verify runs/contact-cylinder
```

Select any of the three backends with `--engine`; other controls are in [cases](cases). Registered tasks are `DexLab-ContactPlane-v0`, `DexLab-ContactIndent-v0` and `DexLab-ContactCylinder-v0`. Only `dev-` cases are admitted until calibration and suite freezing are complete.

Exit code 1 may represent failed physics checks; distinguish it from runtime errors using `summary.json` and `run.json`. The summary alone cannot replace raw arrays/contact ledgers for independent rescoring. The implementation passes 207 project unit tests; release submission additionally requires both complete 14 s grasp regressions for the current source.

## Reproduce the released evidence offline

The [v0.12.0 raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.12.0/v0.12.0-contact-development-evidence.tar.gz) contains all 38 completed runs and three admission failures, native/source snapshots, per-file hashes and plot scripts (136,594,576 bytes). Use the matching DexLab version and its installed Python environment; rescoring does not launch engines or require Isaac Sim.

```bash
gh release download v0.12.0 --repo huangkiki/Dexlab \
  --pattern v0.12.0-contact-development-evidence.tar.gz --dir runs/contact-evidence-v012
tar -xzf runs/contact-evidence-v012/v0.12.0-contact-development-evidence.tar.gz \
  -C runs/contact-evidence-v012
.venv/bin/python demos/contact-benchmark/rescore_results.py runs/contact-evidence-v012
.venv/bin/python demos/contact-benchmark/plot_results.py runs/contact-evidence-v012 \
  --output runs/contact-evidence-v012/development.png
```

Archive SHA-256: `5a836c146ed5b726d29f60813322e68e4cb03a1ba7f9c8f301c379ec4e003279`. The batch rescoring command exits zero only when every recorded summary is reproduced, including the 13 physical failures. It does not reclassify those failures as successful physics.

## Updated evidence and remaining scope

[Synthetic response–cost](RESPONSE_COST.md) and [prospective paired mass/size transfer](TRANSFER.md) now retain all measured failures. Full internal cooking/combined-law readback remains unobservable. Real-material calibration belongs to #6 and the apple held-out suite to #3; #10 still requires its explicit completion audit. Earlier development data are not retroactively labeled held-out.
