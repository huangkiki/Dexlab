# Static SDF construction-path observability

[简体中文](SDF_CONSTRUCTION.zh-CN.md)

Question: does an official precomputed grid reproduce sampled distances from an automatically constructed collider? This is a geometry-construction question, not a dynamic grasp or material-calibration test.

Fixed protocol: a closed 40×30×20 mm box, requested 2 mm grid spacing, static native SDF actors, z rotation 0.7 rad and translation [0.1,0.2,0.3] m. Query a fixed 9×9×9 interior lattice after step(0). Compare both native distance arrays and independently compute analytic-box distances. Save the complete explicit baked grid and actual native transforms. No outside-bounds queries, where the API documents only an upper bound.

The 1e-12 coordinate comparison tolerance checks serialized FP64 configuration. It is not a physical accuracy tolerance. Report exact sampled equality and absolute discrepancy separately; complete evidence can establish a negative result.

```bash
python demos/contact-benchmark/probe_sdf_construction.py --output NEW_DIRECTORY --wheel-dir OFFICIAL_WHEEL_DIRECTORY
```

Run inside the repository's measured resource envelope. Official stable native/wheel admission precedes construction. The output must be new. No changes to the apple demo or engine source. A precomputed grid is observable output of the official bake function; it is not direct readback of the automatic actor's internal grid.

Initial private development probe: explicit grid 27×22×17, 10,098 values; 729 sampled distances differed by up to 0.129771 mm. Analytic-box maximum discrepancies were 0.273479 mm (automatic) and 0.293555 mm (precomputed). These preliminary records used requested transforms; the reproducible program additionally reads actual transforms. The actual-pose qualification is reported below; public archive delivery remains pending. Do not attribute the discrepancy to a particular algorithm without further evidence.

## Qualified program result

One new static execution reads and validates both actual native poses. The729-point discrepancies reproduce the preliminary record; all10,098 grid values are retained. Frozen-source verification passes and independent offline rescoring agrees. This validates evidence and discrepancy, not accuracy or equivalence. [Result](../../docs/evidence/sdf-construction-v1.json)

```bash
python -m dexlab.sdf_observability RECORD_DIRECTORY
```

The command checks raw arrays, report and source-snapshot hashes, then recomputes the analytic reference and maximum discrepancies. Missing data, tampered summaries and invalid paths are rejected. Public archive delivery and full publication gates remain pending.

The offline checker also verifies archived grid dimensions, value-array shape, finite bounds, spacing and the closed input-box mesh against the declared geometry. This checks representation consistency, not interpolation accuracy or the hidden automatic grid.

## Verified evidence package

The locally verified package `dexlab-sdf-construction-v1.tar.gz` contains 128 hashed files (370,217 bytes), including unchanged raw arrays, frozen runtime sources and the separate final scorer. Extraction and offline rescoring agree. SHA-256: `71e46662e788d1cf820f8d6ae3fa2dd14b61fa9ccbf7cc008f966357cb80fce1`. Publication is pending the repository gates.

The earlier goal of reading back the automatic collider's complete cooked grid is **not satisfied** by the explicit bake output. The tested static recording path did not expose that grid either. The negative sampled-equivalence result rules out treating the explicit grid as an interchangeable readback. Likewise, documented parameter-combination laws are not measurements of effective per-contact parameters. These remaining observability limits stay explicit in Issue #10; this package does not close the broader contact-diagnosis task.

## Runtime migration during publication

MuJoCo 3.15.0 was published during the original 3.14.0 delivery gate. Both 3.14.0/SuperDex grasp verifiers passed, but latest-stable admission rejected that environment; this failure is retained. A separate 3.15.0 environment passes all 486 tests and official wheel/installed-code identity checks. Historical 3.14.0 compatibility also passes 486 tests. Full 3.15.0 grasp publication gates remain pending.

The explicit candidate profile does not grant formal qualification. For 3.15.0, cloth XML omits the removed `internal` attribute; the elastic-cloth adapter uses the same `discrete` integrator already selected for 3.14.0. Older profiles retain their XML and integrator. The first test round had five XML errors; after that repair, two errors exposed the missing discrete-profile selection. Both failures are retained. These are interface fixes, not evidence of unchanged cloth dynamics or a new cloth benchmark. See the [official release notes](https://github.com/google-deepmind/mujoco/releases/tag/3.15.0).

The static SDF archive preserves its original runtime source and separate scorer; it is not rewritten to appear generated under a later runtime.
