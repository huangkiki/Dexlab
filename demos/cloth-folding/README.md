# Frictional cloth manipulation — experimental

[简体中文](README.zh-CN.md) | [English](README.md)

OpenArm and Wuji manipulate passive MuJoCo cloth through joint actuation and
frictional contact. There are no hand–cloth attachments, cloth actuators, mocap
grippers, or cloth-state edits during the recorded episode.

- `grasp`: pinch a rectangular panel, withdraw, lift, release, and move away.
- `fold`: attempt a lower-hem fold on a single-layer T-shaped panel using both
  hands. This is not a sewn garment or a complete garment-folding system.

![Wuji cloth pinch, lift and release close-up](media/grasp.gif)

The complete, uncut 9 s episode. The display camera follows saved hand/cloth states and never feeds the controller. [MP4](media/grasp.mp4) · [Media provenance](media/grasp-provenance.json)

**The original success claim is withdrawn:** the table-interior audit detects intrusion in 176/225 saved frames. This recording requires geometry review. [Scoring comparison, curve and limits](SCORING.md). Physical repair is separate in [#32](https://github.com/huangkiki/Dexlab/issues/32).

[Static table-edge counterexample and parameter audit](TABLE-CONTACT.md): a concrete mismatch between native contact distance and surface intrusion; dynamics repair remains unvalidated.

[Independent cloth/robot audit](ROBOT-CONTACT.md): no midsurface intrusion into 79 robot collision hulls in 225 saved frames; injected counterexamples are detected. This does not clear the table failure or certify finite-thickness/inter-frame separation.

## Run and verify

[Passive-settling observation](SETTLING.md): optionally record every initialization step before planning and locate the first sampled table intrusion offline. Synthetic tests are complete; new remote dynamics validation is pending.

Use the repository's `bash scripts/setup.sh` environment. Generate an apple
robot model first, or set `DEXLAB_ROBOT_MODEL` to an existing `model.xml`:

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless
bash demos/cloth-folding/run.sh --task grasp --timestep .00025
.venv/bin/python demos/cloth-folding/src/verify_cloth.py demos/cloth-folding/runs/latest
```

The offline verifier returns 0 for a limited protocol pass, 1 for protocol failure, and 2 when geometry review is required. It reads the recording without modifying it; use `--output /path/to/new-report.json` outside the recording for a new report. Rendering writes a new sibling directory named `<run>-media-cloth-evidence-v2`; an existing destination is rejected. Explicit replay: `render_cloth.py RECORD --output NEW_MEDIA_DIR`. The episode summary's `verified`/`validation.passed` covers online protocol measurements only; use the offline assessment for geometry.

`DEXLAB_PYTHON` selects a Python environment; `--no-video` skips rendering.
Use a fresh `--output` directory for each experiment. To reproduce the
experimental fold attempt, use `--task fold --hand-friction 2 --timestep .0005`.
A completed trajectory or video is not evidence of successful folding.

## Model and controller

The controller uses known simulator state, IK, scripted joint targets, and robot
bias compensation. Cloth receives no compensation. The episode starts at a
collision-checked pregrasp after passive cloth settling, with velocities reset
to zero. Reaching that pregrasp from a home position is outside this episode.

Cloth uses a 2D flex with internal edge equalities, bending elasticity, and
self-contact. Nominal shell thickness is 0.5 mm; collision radius is 1.2 mm.
Robot/cloth collision uses convex mesh proxies, not the apple SDF/SDF path.
Materials and drives are uncalibrated. The table is split into fixed bodies to
avoid MuJoCo's per-body-pair flex contact limit; this does not remove self-contact
limitations. Hand sliding friction is explicit; the effective cloth/table value
is 1.0 under the configured mixing rule.

MuJoCo's Newton constraint solver, pyramidal friction cone, and a 0.25 ms default
step handle manipulation. This is **not the Newton physics engine**. CG at
0.5 ms is used during initial passive settling only.

## Evidence and current limits

This experiment was imported from unpublished DexLab research; original file
hashes are in [import-provenance.json](import-provenance.json). The historical single-hand run passed the old protocol, but the new independent table audit detects geometric intrusion. Zero nonadjacent self-crossings did not establish collision validity against the table or robot. The historical bimanual fold failed strain, release and
final-placement checks; successful bimanual folding is not established here.

| Single nominal configuration | Result |
|---|---:|
| Material-point lift | 121.46 mm |
| Maximum material-to-hand anchor offset | 3.98 mm |
| Two-pad contact sample coverage during hold | 100% |
| Maximum edge strain | 4.47% |
| Maximum reported hand penetration | 0.376 mm |
| Final robot–cloth normal force | 0 N |
| Nonadjacent surface crossings in 225 saved frames | 0 |

[Unchanged historical summary](evidence/grasp/summary.json) · [Historical verifier output](evidence/grasp/verification.json) · [Current versioned assessment](evidence/grasp/verification-cloth-evidence-v2.json).
The repository packages reports and media. Each new run retains the full model,
trajectory, 100 Hz measurements and source snapshot under `runs/`; the commands
above regenerate them.

The verifier requires complete 100 Hz traces, explicit complete contact scans,
finite measurements, and the correct hand plans before scoring. It checks two-pad
contact coverage, material-anchor error, lift, strain, reported penetration,
and release from every robot geometry. Recorded maxima must not exceed the per-step summary; a denser per-step summary may legitimately be larger. Missing or unsupported table geometry requires review, rather than silently counting as safe. Offline verification also inspects the
compiled model for cloth actuation and external attachment constraints.
Thresholds remain 95% two-pad coverage, 1 cm anchor error, 8 cm lift, 5% maximum
edge strain, and 1.5 mm reported penetration. Final robot/cloth normal contact
force must be below 1 mN. The fold adds hem placement and far-panel checks.

Per-step maxima, 100 Hz contact measurements and 25 Hz saved complete states have
different coverage. Contact distances cover engine-reported contacts. Offline
verification additionally reconstructs cloth surfaces from 225 saved states and
checks nonadjacent triangle crossings. Shared-vertex pairs are excluded; this
does not guarantee continuous inter-frame separation or finite-thickness separation.
Material fidelity, perception uncertainty, layer selection,
damage, and hardware transfer are unverified. See the separate
[cloth benchmark](../cloth-benchmark/README.md) for prescribed-load and obstacle
experiments across solvers.
