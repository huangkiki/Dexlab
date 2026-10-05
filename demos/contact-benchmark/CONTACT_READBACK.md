# Contact parameter readback

[English](CONTACT_READBACK.md) | [简体中文](CONTACT_READBACK.zh-CN.md)

Development validation: all eight frozen native runs passed the original physics checks. The new recorder reads MuJoCo contact friction, dimension, solref, solimp and include margin at the solved-force epoch. The independent diagnostic checks the equal-material analytic box/plane fixture only, including compiled geom type/size and mixing inputs. It does not prove general mesh cooking or material accuracy. MuJoCo3.14 headers define mjMINMU=1e-5; inactive torsion/rolling parameter slots also have this clamp. Parameter values are not friction forces.

SuperDex1.0.0 FP64 actor parameters are read from both actors. Its public ContactPoint exposes force, points and velocities, but no combined pair-law parameters. Those values and cooked-geometry equivalence remain unknown; matching actor parameters is not an equivalence pass.

```bash
python -m dexlab.contact_readback RECORD_DIRECTORY
```

The command verifies complete archive hashes, source snapshots, limits and force ledger before diagnosis. Physical acceptance remains separate. Missing readbacks stay incomplete. Exit zero requires both physical acceptance and complete consistent observed readbacks; SuperDex unobservable pair law returns nonzero without changing its original physics score. Do not overwrite historical records or infer new fields from old data.

[Official MuJoCo mixing semantics](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters). Frozen development matrix: `benchmarks/contact-readback-v1.json`, eight native runs,600s maximum; not a held-out benchmark.

## Measured development controls

All four MuJoCo recordings had complete, consistent readbacks (3,660 / 4,000 / 4,000 / 7,340 contacts). All four SuperDex recordings had matching actor profiles; combined pair parameters remain unobservable. Against the corresponding previous friction cases, all eight state arrays and pre-existing contact fields were exactly unchanged. This is a scoped recording check, not a general noninterference guarantee.

Six additional MuJoCo static controls matched their preregistered expectations: weighted equal priority, higher plane priority, direct-format solref minimum, explicit anisotropic pair, global override, and a separated negative control. The five positive controls each produced four contacts; the negative produced none. They call `mj_forward` without advancing simulation time and do not establish dynamic stability. Reproduce with `probe_contact_mixing.py OUTPUT --wheel-dir OFFICIAL_WHEEL_DIRECTORY`.

Raw evidence has been packaged and verified offline; final native grasp regression gates and release publication remain pending. General mesh cooking equivalence and real material calibration remain unproven.

[Readback JSON](evidence/contact-readback-v1.json) · [Mixing JSON](evidence/contact-mixing-v1.json)

```bash
python demos/contact-benchmark/report_contact_readback.py READBACK_RECORDS --previous FRICTION_RECORDS --output REPORT.json
```

Prepared raw artifact: `dexlab-contact-readback-evidence-v1.tar.gz`, 2,403,074 bytes, SHA-256 `ba59bd8beca7fab3091df52759070febcdb9bce35344bc31fb0e1e26c63e3b02`. All 186 file hashes and eight rescored diagnoses verified after extraction using archived source. Native state/contact bytes unchanged; only private source-map keys redacted with before/after hashes. Originals retained.
