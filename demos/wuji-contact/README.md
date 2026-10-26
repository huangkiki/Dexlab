# Wuji grasp, unload and release

[English](README.md) | [简体中文](README.zh-CN.md)

Run a fixed-wrist Wuji hand pinching a 20 g sphere, then inspect whether measured contacts actually hold and release it. The object has no latch, weld or external support after preparation. This is a synthetic numerical fixture, not a calibrated hardware model.

The preserved v2 record maintained two-pad contact but moved **2.459 mm**, exceeding the frozen **2 mm** hold limit. A small force/momentum residual did not make the task pass. The earlier v1 record failed initial geometry/control admission. [The new prospective batch](PROTOCOL-v3.md) changes only the control period, from 2 ms to 0.5 ms; its outcome must be established from its own raw record. All batches retain the same hold reference and acceptance thresholds.

## Run the native fixture

From the repository root, use Linux x86_64, [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.12 and an isolated environment. Physics uses CPU MuJoCo 3.17.0; it does not need a GPU, SuperDex, Torch or a model API key. The pinned robot archive is about 16 MB. The native SDF scene has measured memory use above 2 GiB; allow 8 GiB and expect several minutes for 4.4 simulated seconds. These commands install only the demo's dependencies in uv's isolated environment.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/assets.json \
  --destination downloads/wuji-contact-assets
PYTHONPATH=demos/apple-stem-grasp/src \
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python demos/wuji-contact/run.py --robot-assets downloads/wuji-contact-assets/robot \
  --protocol demos/wuji-contact/protocol-v3.json --case hold-release \
  --output results/wuji-contact-first
```

The output contains the exact native scene, planned joint targets, runtime/source hashes, initial-geometry check, effective settings and every pre/post-step observation. An existing output directory is rejected. `recorded` means that data collection completed; it does not mean the grasp passed.

## Score and plot the saved record

This step imports no simulation engine and never advances physics. It first checks the raw hash, clocks, state continuity, native force reconstruction and linear momentum balance, then evaluates the unchanged task criteria.

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py results/wuji-contact-first \
  --output results/wuji-contact-first-report
```

Open `measurements.png`; `measurements.csv` retains the full recorded time series and `report.json` separates record integrity, numerical balance, holding, release and unloading. Write each report to a new directory outside its input. The graph uses labelled symmetric-log scales to show both millimetre-scale holding and the later free fall. A failed hold cannot qualify as successful active release simply because the object falls clear.

The frozen cases also include `unload-index_finger`, `unload-thumb`, `open`, `no-contact` and `zero-friction`. In the qualification batch, run them only after the positive hold/release passes. The two unloading commands are judged by the selected pad's measured force; object loss after losing one of two contacts is reported separately. Zero-friction retention would require examining geometric support, not immediately blaming the solver.

[Original protocol and criteria](PROTOCOL.md) · [v2 geometry/controller correction](PROTOCOL-v2.md) · [v3 control-rate hypothesis](PROTOCOL-v3.md) · [Explicit applicability](applicability.json) · [Issue #251](https://github.com/huangkiki/Dexlab/issues/251)

This first native fixture does not establish a cross-engine comparison, material accuracy, in-hand rotation or a numerical solver failure. Contact switching and post-development validation remain separate work in [#48](https://github.com/huangkiki/Dexlab/issues/48).
