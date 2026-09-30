# Cloth scoring reassessment: protocol pass, invalid geometry evidence

[简体中文](SCORING.zh-CN.md) | [English](SCORING.md)

**The original nine-second cloth recording does not establish a physically valid grasp.** `cloth-evidence-v2` detects triangle interiors inside the table in 176 of 225 saved frames. Small native contact distances, successful lifting and zero self-crossings together still fail to exclude table intersection. This change repairs scoring and presentation; controls, engines and physical parameters are unchanged. Physical repair is tracked in [#32](https://github.com/huangkiki/Dexlab/issues/32).

![Historical table interior depth](media/table-diagnostic.svg)

## Old and new results on the same record

| Input or check | v0.14.2 | cloth-evidence-v2 |
|---|---|---|
| Original contact/lift/release protocol | Pass | Protocol pass, overall `geometry_review_required` |
| One trace value replaced by 20 mm, summary unchanged | Incorrect pass | Reject: summary fails to bound the trace peak |
| Trace and summary both contain 20 mm | Penetration failure | Same 1.5 mm threshold fails |
| Per-step summary peak exceeds 100 Hz sampled peak | Allowed | Still allowed; equality would be incorrect |
| Valid synthetic record with complete geometry | Limited protocol pass | `limited_protocol_pass` |
| Missing or unsupported table geometry | Not checked | `geometry_review_required` |

Injections modify in-memory scoring inputs only; no raw trajectory is edited and no physics is rerun. Valid controls test the evaluator, not another successful physical grasp. The [frozen legacy source provenance](evidence/legacy/source.json), [full comparison](evidence/grasp/scoring-comparison-v2.json) and [new report](evidence/grasp/verification-cloth-evidence-v2.json) are retained. Original [summary](evidence/grasp/summary.json) and [verification](evidence/grasp/verification.json) are not overwritten; their old `passed` fields refer to the historical protocol.

| Original single-scene observation | Value | Interpretation |
|---|---:|---|
| Material-point lift | 121.46 mm | Lifting does not establish geometric validity |
| Two-pad contact sample coverage | 100% | Depends on native contact reporting |
| Maximum native table-contact penetration | 0.2004 mm | Contact distance scanned every physics step |
| Maximum geometric table interior depth | 3.0000 mm | Zero-thickness triangle-interior diagnostic |
| Saved frames containing table interior points | 176 / 225 | 25 Hz, first at 0.00 s |
| Maximum depth from vertices alone | 0 mm | Exterior vertices can span the solid table |
| Nonadjacent self-surface crossings | 0 / 225 frames | Does not cover the table or hand |

## Geometry definition and cross-check

The table has 96 fixed, axis-aligned boxes. The audit verifies disjoint interiors and a summed volume filling their bounding box before treating the union as one solid box. Failed coverage checks, rotation or motion produce unsupported/insufficient evidence, never a safe result.

For triangle points `p = p0 + s*(p1-p0) + t*(p2-p0)`, constrain `s,t ≥ 0` and `s+t ≤ 1`. Maximize `d ≥ 0` subject to `lower+d ≤ p ≤ upper-d`. This linear program measures the largest distance to the nearest box face over interior triangle points. **The table is 6 mm thick, so this metric saturates at 3 mm. It is neither vertical penetration nor a minimum translation to separate the objects.** Zero-thickness geometry, 0.5 mm shell thickness, 1.2 mm collision radius and native contact distances are different definitions. The old 1.5 mm threshold is not applied to this metric; `1e-8 m` is only a numerical zero tolerance.

An independent polygon-clipping/bisection algorithm computes the same quantity at fixed frames 0, 56, 112, 168 and 224. Maximum disagreement is approximately `4.37e-14 m`. Both algorithms share recorded geometry and MuJoCo forward kinematics: this cross-check is not independent physics or hardware validation.

The [22 KB reference fixture](evidence/grasp/table-reference.npz) contains five frames of 169 vertices, 288 triangles, table bounds and source hashes. It supports geometry reproduction without robot assets or simulation steps. It is a fixed derived sample, not the full nine-second recording. Original models, trajectories, measurements, plans and failures remain retained; this repository packages reports, media and the small fixture, not everything needed to rescore the full historical record after cloning.

## Reproduction and outputs

From the repository root, using its installed environment:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_offline_scoring.py'
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_grasp_evidence.py'
.venv/bin/python -m unittest discover -s tests -p 'test_cloth_table_audit.py'
```

With a complete recording you retained:

```bash
.venv/bin/python demos/cloth-folding/src/verify_cloth.py RECORD --output NEW_REPORT.json
# The original historical record returns 2: geometry review required.
# The report must be outside RECORD and must not already exist.
.venv/bin/python demos/cloth-folding/src/compare_scoring.py RECORD --output NEW_COMPARISON.json
.venv/bin/python demos/cloth-folding/src/render_cloth.py RECORD --output NEW_MEDIA_DIR
```

`compare_scoring.py` specifically regresses this historical bad recording. Its exit 0 means expected bad evidence and negative controls were identified correctly, not a successful grasp. `verify_cloth.py` exits 0/1/2 for limited protocol pass, protocol failure and geometry review. Native run-summary `verified`/`validation.passed` fields cover online measurements only.

Rebuild the curve with `src/plot_scoring.py evidence/grasp/scoring-comparison-v2.json --output NEW_PLOT.svg --language en` (paths relative to this demo; requires Matplotlib, and Noto Sans CJK SC for Chinese). Plotting executes no physics. Reports record input/scorer SHA-256 hashes and reject inputs changing during the read. [Media provenance](media/grasp-provenance.json) binds the GIF/video to these inputs: 225 consecutive frames, 25 fps, nine seconds, zero physics steps during replay. Prior media remain available at [v0.14.2](https://github.com/huangkiki/Dexlab/tree/v0.14.2/demos/cloth-folding/media).

## Remaining coverage gaps

- Independent cloth-versus-robot triangle checks are absent; this report cannot establish finger/cloth separation.
- Saved 25 Hz states cannot cover inter-frame transients or continuous collision. Neither 100 Hz contacts nor per-step maxima are a complete surface audit.
- Self-surface checks exclude shared-vertex pairs and do not guarantee finite-thickness separation.
- Material measurements and hardware feedback remain absent. There is no successful bimanual folding or engine-accuracy ranking claim.

This slice accepts the scorer when it correctly refuses incomplete success evidence. The exact remote submission gate and source-tree identity are attached to the [code release](https://github.com/huangkiki/Dexlab/releases); this report does not rerun the historical physical trajectory.
