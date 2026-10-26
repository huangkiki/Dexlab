# Wuji grasp, unload and release

[English](README.md) | [简体中文](README.zh-CN.md)

Run a fixed-wrist Wuji hand pinching a 20 g sphere, then inspect whether measured contacts actually hold and release it. The object has no latch, weld or external support after preparation. This is a synthetic numerical fixture, not a calibrated hardware model.

The v3 point-contact configuration failed holding at **2.734 mm**. Adding the separately frozen synthetic torsional contact law in v4 reduced it to **1.025 mm**, passing the original **2 mm** limit and active release. All six v4 controls meet their respective frozen criteria. The first three failures and their 15 not-run cases remain preserved. Slow drift remains; acceptance covers only the frozen two-second hold. This is contact-model sensitivity, not a qualified solver failure.

![Synchronized point-contact / torsional-contact replay](../../docs/evidence/wuji-contact/comparison.gif)

[Start with the offline rescore and full report](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html) before installing a native runtime.

## Run the native fixture

From the repository root, use Linux x86_64, [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.12 and an isolated environment. Physics uses CPU MuJoCo 3.17.0; it does not need a GPU, SuperDex, Torch or a model API key. The pinned robot archive is about 16 MB. The native SDF scene has measured memory use above 2 GiB; allow 8 GiB and expect several minutes for 4.4 simulated seconds. These commands install only the demo's dependencies in uv's isolated environment.

If you used the sparse offline checkout, first run `git sparse-checkout add demos/apple-stem-grasp/src` to include the IK helper.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/assets.json \
  --destination downloads/wuji-contact-assets
PYTHONPATH=demos/apple-stem-grasp/src \
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python demos/wuji-contact/run.py --robot-assets downloads/wuji-contact-assets/robot \
  --protocol demos/wuji-contact/protocol-v4.json --case hold-release \
  --output results/wuji-contact-first
```

The output contains the exact native scene, planned joint targets, runtime/source hashes, initial-geometry check, effective settings and every pre/post-step observation. An existing output directory is rejected. `recorded` means that data collection completed; it does not mean the grasp passed.

## Score and plot the saved record

This step imports no simulation engine and never advances physics. It first checks the raw hash, clocks, state continuity, native force reconstruction and linear momentum balance (plus angular balance for v4), then evaluates the unchanged task criteria.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py results/wuji-contact-first \
  --output results/wuji-contact-first-report
```

Open `measurements.png`; `measurements.csv` retains the full recorded time series and `report.json` separates record integrity, numerical balance, holding, release and unloading. The CSV identifies pre/post-step times: positions and speeds are post-step, while contact force and actuator force belong to the pre-integration solve. Write each report to a new directory outside its input. The graph uses labelled symmetric-log scales to show both millimetre-scale holding and the later free fall. A failed hold cannot qualify as successful active release simply because the object falls clear.

The frozen cases also include `unload-index_finger`, `unload-thumb`, `open`, `no-contact` and `zero-friction`. In the qualification batch, run them only after the positive hold/release passes. The two unloading commands are judged by the selected pad's measured force; object loss after losing one of two contacts is reported separately. Zero-friction retention would require examining geometric support, not immediately blaming the solver.

[Original protocol and criteria](PROTOCOL.md) · [v2 geometry/controller correction](PROTOCOL-v2.md) · [v3 control-rate hypothesis](PROTOCOL-v3.md) · [Explicit applicability](applicability.json) · [Issue #251](https://github.com/huangkiki/Dexlab/issues/251)

This first native fixture does not establish a cross-engine comparison, material accuracy, in-hand rotation or a numerical solver failure. Contact switching and post-development validation remain separate work in [#48](https://github.com/huangkiki/Dexlab/issues/48).

## Replay the same observations

Rendering needs an OpenGL/EGL-capable environment. It loads the saved scene and poses without advancing physics; orientation marks are visual only.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/render-requirements.txt \
  python demos/wuji-contact/render.py results/wuji-contact-first \
  --output results/wuji-contact-first-replay
```

The MP4/GIF include all preparation, holding and release frames at original speed. `render.json` binds frames to raw-state indices and records input/output hashes.
