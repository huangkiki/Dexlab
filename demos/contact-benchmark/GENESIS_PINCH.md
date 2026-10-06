# Genesis primitive pinch and release

[简体中文](GENESIS_PINCH.zh-CN.md)

**The development fixture passes its current criteria, not full backend qualification.** Official Genesis 1.4.3, CPU FP64, elliptic friction cone and a 0.5 ms step drive a three-joint gripper around a free box. Two reset trajectories match exactly; two open-pad controls remain on the table. This is not a statistical success rate, apple SDF, GPU or hardware result.

![Pinch and release](../../docs/evidence/genesis-pinch.png)

Complete-trajectory comparison: timestep and contact settings differ; this pair of curves is not a single-factor causal comparison.

## Protocol and criteria

The original fixture held the object but penetrated the table by 3.902 mm after release. Lift height alone or a video ending before impact would miss this failure.

The 40 mm box weighs 0.064 kg; friction is 0.5 and gravity 9.81 m/s². Gripper masses are 1/0.1/0.1 kg with explicit zero armature. Prismatic PD gains are 1000/500/500 and 50/20/20, with force bounds ±50/10/10 N. Scripted control is an explicit prior. Actual positions, velocities, orientations and contact forces are recorded; the object has no attachment or direct actuation.

Closing occurs during 0–0.5 s, lifting during 1–2 s, hold scoring during 2–3 s, opening at 3.2 s, and release scoring during 3.8–4 s. All 8000 physics steps are scored.

- Native and independent box–table penetration stay ≤1 mm, inherited from the engineering criterion in `contact_pinch.py`, not hardware tolerances.
- Hold center height ≥60 mm, both pads exert force, and other support ≤0.01 N.
- Release center height ≤30 mm and pad contact force ≤0.01 N. Open-pad controls stay ≤30 mm throughout.
- Pair-force ledger error ≤1e-8 N; per-step momentum residual divided by weight impulse ≤5%.
- Imported parameters and actual initial states are checked separately. Exact repeated trajectories establish reset reproducibility only in this environment.

Independent reference geometry covers the box and table plane only. Pad penetration still uses native contact depth, not an independent whole-surface bound.

## Diagnosis and refinement

An isolated drop from 85 mm center height used 3 timesteps × 3 time constants × 2 reset repeats (18 trajectories), showing the gripper is unnecessary to trigger the defect. Geometry `get_sol_params()` returns stored values; native `collider/contact.py` averages pair parameters then floors the time constant at twice the substep. A 2 ms geom readback therefore does not always mean a 2 ms effective contact value. This interpretation is source-derived, not an internal pair-parameter measurement.

The candidate changes only table and box geom time constants to 2 ms. All three joint time constants remain 10 ms on readback. Pads retain defaults, so pad–box and table–box mixed responses differ.

| Step | Native peak penetration | Independent table peak | 1 mm criterion |
|---|---:|---:|---|
| 1 ms | 0.044 mm | 0.032 mm | Pass |
| 0.5 ms | 0.665 mm | 0.665 mm | Pass |
| 0.25 ms | 0.758 mm | 0.758 mm | Pass |

**No convergence claim.** The 1 ms peak is sampling-sensitive. Earlier global 10 ms response at 2/1/0.5 ms steps produced 3.902/3.364/3.981 mm; global 4 ms produced 1.849/0.940/1.555 mm. The isolated passing case was not accepted as a stable repair. These are development cases, not held-out evaluations.

Both public-run pinch repeats maintain center height ≥83.701 mm and release height ≤19.999 mm, with zero force-ledger error and peak momentum residual weight ratio 2.61e-9. Open-pad controls never lift. [Complete scores](../../docs/evidence/genesis-pinch-score.json).

## Reproduction and limitations

Use the existing [Genesis environment](GENESIS_CONE.md), after resource admission:

```bash
python -m dexlab.genesis_pinch_probe /path/to/new-run --dt 0.0005
python -m dexlab.genesis_pinch_score /path/to/new-run
```

Output overwrite is refused. Source hash, model, readbacks and every physics-step record are retained. Scoring does not load the engine. Raw evidence remains a local candidate pending a new Release.

Issue #42 still requires continuous close-up media, GPU isolation/capacity, stage costs and broader qualification. Apple geometry, independent whole-contact reference surfaces, hardware friction calibration and learned control are outside this result.
