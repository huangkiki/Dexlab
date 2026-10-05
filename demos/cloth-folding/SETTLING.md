# Cloth collision and release investigation

[English](SETTLING.md) | [简体中文](SETTLING.zh-CN.md)

**Current conclusion:** the complete 9 s development case with adjusted floor-contact and edge-constraint time constants passes the v3 native protocol and saved-frame geometry checks, including pinch, lift and complete release. This is scripted known-state control with uncalibrated material. Self-contact penetration is only **7.95 µm** below its limit: this is not a robustness or held-out benchmark claim. Official engines and acceptance thresholds are unchanged.

![Continuous grasp and complete release close-up](media/compliance-grasp.gif)

[Continuous 9 s video](media/compliance-grasp.mp4) · [Media provenance](evidence/settling314/compliance-media-provenance.json)

![Strain and contact-force history](media/compliance-diagnostic.svg)

| Metric | Current development case | Fixed criterion |
|---|---:|---:|
| Maximum edge strain across every physics step | 3.5161% | <5% |
| Maximum native hand/table/floor/self penetration | 0.311 / 0.284 / 1.100 / 1.492 mm | Each <1.5 mm |
| Material-point lift | 123.92 mm | >80 mm |
| Two-pad coverage during hold | 100% | ≥95% |
| Maximum material-anchor distance | 4.32 mm | <10 mm |
| Maximum hand/cloth force in final 0.5 s | 0 N | <0.001 N |
| Saved-frame table/robot/floor midsurface intrusion | Each 0/225 frames | Sampled geometry only |
| Settling table intrusion | 0/4,001 states | Sampled geometry only |

All 72,000 physics steps completed. The simulation loop took 618.86 s; service time including preparation and recording was 642.18 s. This resource-limited run is not an engine-throughput benchmark. Extrema scan every physics step, plots use 100 Hz observations and geometry uses 25 Hz states; plotted peak strain is therefore 3.0891%, below the per-step maximum. Saved-frame clearance does not prove continuous-time separation. Injected robot intrusion is detected and the separated control passes.

[Native metrics](evidence/settling314/compliance-summary.json) · [Independent protocol/table/floor/self](evidence/settling314/compliance-protocol-table-self.json) · [Robot audit](evidence/settling314/compliance-robot.json) · [Negative controls](evidence/settling314/compliance-robot-negative-controls.json) · [Settling audit](evidence/settling314/compliance-settling.json) · [Plot provenance](evidence/settling314/compliance-plot-provenance.json)

## Historical control: corrected phase still fails complete release


![Corrected-phase strain and normal-force history](media/phasefixed-diagnostic.svg)

| Metric | Corrected phase, 8 cm release withdrawal | Fixed criterion |
|---|---:|---:|
| Maximum absolute edge-length strain, all physics steps | 2.7121% | <5% |
| Maximum native hand/table/self penetration | 0.325 / 0.164 / 0.407 mm | Each <1.5 mm |
| Material-point lift | 124.90 mm | >80 mm |
| Two-pad contact coverage during hold | 99.33% | ≥95% |
| Maximum material-anchor distance | 6.10 mm | <10 mm |
| Maximum final robot/cloth normal force | **0.0558 N** | **<0.001 N — failed** |
| Independent table/robot midsurface intrusion | 0/225 saved frames | Report sampled coverage |
| Independent initialization/table intrusion | 0/4,001 saved states | Report sampled coverage |

The final-force window is the last 0.5 s. Its contacts are predominantly the ring and pinky pads; continuous recorded-state replay confirms the cloth resting on those fingers. Opening the pinch is therefore not complete release. Robot injected controls detect deliberate intrusion and accept the separated control.

[Protocol, table and self checks](evidence/settling314/phasefixed-protocol-table-self.json) · [Robot geometry](evidence/settling314/phasefixed-robot.json) · [Robot negative controls](evidence/settling314/phasefixed-robot-negative-controls.json) · [Plot provenance](evidence/settling314/phasefixed-plot-provenance.json)

Strain/penetration extrema scan every physical step. Force, hold and release statistics and the plot use 100 Hz observations; full-grasp geometry uses 25 Hz states. The latter checks zero-thickness midsurfaces, not finite-thickness or continuous-time nonintersection. End-to-end service time for this development run was 533 s, including preparation/recording; this is not isolated engine throughput.

## What changed, and what did not work

All runs use the official, unchanged MuJoCo 3.14.0 runtime. Development candidates are not held-out benchmarks. Controls retain their failures; rows with different initialization, planning or geometry must not be interpreted as engine-accuracy comparisons.

| Control | Measured result | Interpretation |
|---|---|---|
| Original 96 table boxes | First intrusion at 21.5 ms, triangle 28; previous clear sample at 21.0 ms | Failure begins during passive settling, before grasping |
| Same solid union, 768 boxes (8× X partition) | First intrusion at 90.5 ms, triangle 22 | Delays intrusion; does not repair it |
| Rest-node row aligned with table edge | First intrusion at 92 ms | Changing this discretization does not repair it |
| Same 96 cuboids as convex meshes | No intrusion in 4,001 settling samples | Selects the general convex/flex collision path with the same table envelope |
| Mesh, inset 0.3; then inset 0.1 | Pregrasp failure; then lift-path failure | Neither trial completes a grasp |
| Mesh, inset 0.1, pre-lift clearance 8 cm | Complete run; strain 11.0095% at 7.55 s fails | Saved table/robot geometry improves; physical acceptance still fails |
| Manipulation step halved to 0.125 ms | Complete run; strain 21.7683% fails | Settled state changes too: not fixed-state convergence evidence |
| Phase constants refreshed, original 0.25 ms step | Strain 2.7121% passes, release fails | Numerical initialization repaired; release clearance remains unresolved |

[Original onset](evidence/settling314/baseline-onset.json) · [Partition onset](evidence/settling314/partition-x8-onset.json) · [Edge-aligned onset](evidence/settling314/edge-aligned-onset.json) · [Original complete grasp](evidence/settling314/grasp-verdict.json) · [Mesh complete-grasp failure](evidence/settling314/mesh-full-protocol.json)

Static partition factors 1/2/4/8/16 improve some near-onset contacts but still miss the deep final witness; translated-clear negative controls pass ([static evidence](evidence/settling314/static-partition.json)). The same-shape mesh control preserves all eight cuboid corners to a maximum bidirectional compiled discrepancy of 1.795 nm ([geometry/contact evidence](evidence/settling314/mesh-table-control.json)). It changes collision representation, not the table envelope or official engine.

## Independent geometry, initialization and provenance

The shared auditor validates fixed, axis-aligned cuboid meshes: eight corners, twelve triangles, closed edges, full cuboid surface and all eight corners retained by the native collision hull. Arbitrary mesh bounding boxes, reduced `maxhullvert=4` hulls, unsupported rotations, moving supports, material gaps and overlaps are rejected. Adjacent plane quantization of at most 1.789 nm is explicitly recorded under the existing 10 nm geometric numerical zero; no physical threshold changes. [Direct actual-mesh audit](evidence/settling314/mesh-independent-onset.json).

[Six native initialization controls](evidence/settling314/initialization-controls.json) isolate a script defect. Two compiled manipulation steps produce settling endpoints differing by 1.916 mm, despite a common settling timestep. Configuring before forward alone does not remove this difference. Configuring the phase and calling official `mj_setConst` with scratch data makes final qpos and qvel bitwise-identical. Both phase transitions now refresh model constants without resetting live state. The cached bending factor is a preconditioner; this does not establish an incorrect upstream physical operator or justify an engine patch.

The optional recorder saves initialization before arm planning and the deliberate velocity/time reset. It copies every initial/stepped qpos and qvel without contact queries or modifying live state. A native 4,000-step replay with recording disabled produced bitwise-identical final state for the tested original configuration ([endpoint comparison](evidence/settling314/native-recording-equivalence.json)); this is not a universal noninterference claim.

## Parameters and approximation boundary

| Parameter | Value and source |
|---|---|
| Cloth | Demo's original 20×20 cm single-layer panel, 169 vertices, 15 g total mass |
| Material | Nominal Young's modulus 100 kPa, Poisson ratio 0, 0.5 mm thickness; inherited uncalibrated demo settings |
| Collision radius | 1.2 mm, distinct from nominal shell thickness |
| Table | Original 96 cuboid tiles; optional eight-corner convex-mesh representation, identical envelope within reported quantization |
| Robot collision | Existing surface meshes used as native convex colliders; this cloth demo is not SDF/SDF contact |
| Contact | `condim=3`, `solref=(.002,1)`, `solimp=(.99,.999,.001)`; declared cloth/hand sliding friction 1, table 0.6, subject to native pair mixing |
| Initialization | 2 s, CG, 100 iterations, 0.5 ms step; refreshed model constants |
| Manipulation | Discrete integrator, Newton, 100 iterations, 0.125 ms for the current candidate (historical control: 0.25 ms) step, tolerance 1e-8, pyramidal cone |
| Position drives | Arm kp/kv=1000/40 with ±60 torque limit; finger 15/0.15 with ±1 limit; nominal exporter/demo settings, not measured actuator identification |
| Control | Known-state IK, explicit pinch prior, smooth joint targets; no cloth actuator, weld, adhesion or state overwrite to hold the cloth |

The withdrawal control increases post-opening clearance from 8 to 16 cm. Its failure and subsequent compliance controls are retained below.

## Reproduce and inspect

Use the qualified official 3.14 environment (`DEXLAB_MUJOCO_PROFILE=qualification-3.14.0`), the existing robot export and the repository resource guard. The default `box` mode preserves the historical failed representation. Select the explicit candidate and a fresh data-volume output:

```bash
DEXLAB_MUJOCO_PROFILE=qualification-3.14.0 bash demos/cloth-folding/run.sh \
  --task grasp --table-contact convex-mesh --grasp-inset .1 \
  --pre-lift-retreat .08 --release-retreat .16 --timestep .000125 \
  --floor-time-constant .0005 --edge-time-constant .0005 \
  --record-settling --no-video --output "$RUN_OUTPUT"
```

Set `DEXLAB_PYTHON` and `DEXLAB_ROBOT_MODEL` to the qualified interpreter and existing model export. Recording is optional and adds overhead. It saves the initialization model, complete state grid, topology, hashes and engine identity. A Python exception preserves the successful prefix plus failed state; process termination/disk failure may leave an incomplete record. This is not a restart journal.

```bash
"$DEXLAB_PYTHON" demos/cloth-folding/src/settling_trace.py "$RUN_OUTPUT/settling" \
  --output "$ANALYSIS_OUTPUT/settling.json"
"$DEXLAB_PYTHON" demos/cloth-folding/src/render_cloth.py "$RUN_OUTPUT" \
  --output "$MEDIA_OUTPUT"
```

Analysis outputs must be outside immutable raw records. The onset audit validates hashes/time grid, inspects until first intrusion, reports the preceding sampled-clear state, and leaves later frames unassessed after a failure. Incomplete recordings cannot establish a pass. Exit code zero from an analysis means it completed, not that the physics passed.

## Follow-up: floor impact was missing from contact coverage

The 16 cm withdrawal achieves zero final robot/cloth force but still fails maximum strain (11.5644%). The peak saved frame at 7.64 s is a **floor impact**: independent plane distance gives 0.694 mm midsurface crossing and 1.894 mm collision-radius penetration, matching native floor contacts. The previous contact scanner omitted the floor; table/robot checks cannot establish full environment validity.

`cloth-evidence-v3` now requires per-step floor penetration in the trace/maximums, applies the existing 1.5 mm native penetration limit to the floor, and adds an independent saved-frame plane audit. Old recordings without floor extrema remain incomplete under v3; their v2 reports and frozen verifier source are preserved, not overwritten or backfilled from sparse frames. Solver iteration telemetry is recorded without changing control or dynamics; reaching the iteration budget alone does not establish solver error.

The fixed-initial-state half-step follow-up is reported below; it remains development evidence.

The [repeated six-control result](evidence/settling314/initialization-controls-reproduced.json) records official engine identity, inputs, source and final-state hashes. Its [standalone reproducer](src/probe_phase_initialization.py) intentionally retains the old phase ordering instead of calling the corrected settling helper. Run it under the resource guard with the same qualified profile:

```bash
"$DEXLAB_PYTHON" demos/cloth-folding/src/probe_phase_initialization.py "$RUN_OUTPUT" \
  --output "$PHASE_CONTROL_OUTPUT"
```

[Historical release trajectory rescored with v3 floor coverage](evidence/settling314/release16-floor-review-v3.json): floor intrusion is detected independently; missing per-step floor measurements are not inferred from 25 Hz samples.

## Fixed-initial-state timestep and compliance controls

The 0.125 ms full grasp has exactly the same settled qpos bytes and all planned pose arrays as the 0.25 ms trial, yet still fails: strain12.966%, floor penetration2.612mm and self penetration1.738mm. All72,000 steps ran; maximum solver iterations47/100, zero steps reached the budget. Halving the step is insufficient here; iteration-budget saturation is not observed.

A separate [tilted-panel drop](evidence/settling314/tilted-drop-compliance.json) retains the original cloth/floor/options but removes robot/table, rotates the planar rest panel45 degrees and releases it at center height0.6m with zero velocity. Each runs1s at0.125ms. It is a minimal development case, not a replay or validated full grasp.

| Time-constant control | Max strain | Floor penetration | Self penetration |
|---|---:|---:|---:|
| Original2ms | 11.02% | 2.455mm | 0.362mm |
| Floor0.5ms only | 9.37% | 0.685mm | 0.441mm |
| Edge0.5ms only | 1.91% | 2.413mm | 1.282mm |
| Both0.5ms | 2.04% | 0.685mm | 0.991mm |

These are nominal effective-compliance changes, **not measured material parameters**. Young's modulus, cloth mass, geometry and acceptance limits remain unchanged. Explicit floor priority1 makes its selected solref authoritative instead of mixing; other contact fields retain original values. Native reference-safety clamping remains enabled: effective time constants are at least twice the phase timestep (1ms during0.5ms settling,0.25ms during0.125ms manipulation). The complete result at the top uses `--floor-time-constant .0005 --edge-time-constant .0005`.

Playback now fits all measured cloth vertices with a4cm context margin; the old midpoint-to-hand camera could crop the floor impact out of frame. This is display-only. Original videos and their frozen renderer source remain preserved.

Parameter semantics follow the [official solver-parameter documentation](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters) and [contact mixing rules](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters).

The [public reproducer](src/probe_drop_compliance.py) reproduces all four peak-metric dictionaries exactly ([repeated evidence](evidence/settling314/tilted-drop-compliance-reproduced.json)). Run under the resource guard:

```bash
"$DEXLAB_PYTHON" demos/cloth-folding/src/probe_drop_compliance.py "$BASELINE_RECORD" --output "$DROP_OUTPUT"
```
