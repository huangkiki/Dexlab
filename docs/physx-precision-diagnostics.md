# PhysX FP32 observations: offline decomposition

[简体中文](physx-precision-diagnostics.zh-CN.md) · [Original results](physx-incline-results.md) · [Follow-up #163](https://github.com/huangkiki/Dexlab/issues/163)

This analysis reuses all **40** native PhysX SDK 5.9.0 incline records from v0.54.0, verifies their original provenance and raw hashes, and preserves original scoring. It launches **zero** native simulations. Its purpose is to sharpen the next hypothesis, not to admit failed records or change physical tolerances.

## Findings

PGS sliding at 2 ms originally fails the analytical-normal direction guard. Projecting each recorded normal impulse onto the **normalized recorded native normal** instead of the ideal plane normal reduces the maximum off-axis component from **1.00897334e−10 to 1.61804328e−11 N·s**. This isolates sensitivity to normal representation. The remainder also includes componentwise impulse rounding; it is not proof of a unique error source. The original analytical-normal check still fails.

For the twelve moving TGS/TGS-external cases, replacing nominal mass and gravity with actual native FP32 values leaves maximum momentum residual norms in **1.09418828e−7–1.96463231e−7 N·s**. All remain above the original 1e−7 N·s guard. Each record now identifies the first crossing and peak step with pre/post-state epoch. For example, TGS frictionless at .5 ms first crosses at step **3269** and peaks at step **3315**; its native-constant peak is **1.96463231e−7 N·s**.

At that peak, the summed half-spacing of the two FP32 velocity endpoints, scaled by native mass, is approximately **[3.05176e−8, 8.97e−47, 7.62939e−9] N·s** by axis. This is a descriptive output-representation scale, **not** a forward-error bound for internal substeps, accumulated impulses, or the solver. Increasing a tolerance to that observed residual would not establish correct physics.

The next bounded hypothesis should distinguish native velocity updates, impulse accumulation/writeback and their epochs. Endpoint output spacing alone cannot serve as that decomposition. No algorithm defect, hidden state write, or task impossibility is established. PGS force-balance physical failures remain separate from observation-validity failures; the original four pass counts remain **7/9, 7/9, 3/9, 3/9**.

## Reproduce without new simulations

Extract the [v0.54.0 raw archive](https://github.com/huangkiki/Dexlab/releases/tag/v0.54.0), verify its published hashes, and set `CAMPAIGN` to one profile directory containing `manifest.json`, `campaign.json` and case folders. Use the repository's qualified NumPy environment:

```bash
python scripts/physx_precision_diagnostics.py --input "$CAMPAIGN" --output precision-new.json
```

Run separately for `pgs`, `pgs-friction`, `tgs`, and `tgs-external`. The script first invokes the existing scorer to validate protocol, source, model binding and raw artifacts. Output records every case, raw SHA-256, original score, first momentum crossing and maxima under both direction references. It never rewrites the input or original scores.

[PGS](evidence/physx-incline/precision-pgs.json) · [PGS friction](evidence/physx-incline/precision-pgs-friction.json) · [TGS](evidence/physx-incline/precision-tgs.json) · [TGS external](evidence/physx-incline/precision-tgs-external.json)

The four-profile offline pass took 18.761 s in a frozen 16 GiB/four-core envelope. This is analysis cost, not native solver throughput. #163 remains open for source-backed internal attribution and any separately frozen protocol with independent holdouts. #152 and #145 retain their own framework and inertia/frame acceptance.
