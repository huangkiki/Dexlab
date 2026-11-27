# Reproduce the Chaos, Bullet and SOFA incline extension

The new batch uses the original nine incline cases and scoring limits, plus a 1 ms no-floor control. Each backend starts from rest, with only gravity and contact acting on the box. The prescribed motion and native contact law are documented separately in the [published comparison](https://huangkiki.github.io/Dexlab/en/latest/incline-extension.html).

From the repository root, point `OUT` at a fresh directory on a data volume. The frozen protocol is `docs/evidence/incline-extension/manifest.json`. The Linux Editor runner uses the bundled Chaos 5.7.1 at Unreal revision `684b4c133ed87e8050d1fdaa287242f0fe2c1153`. The PyBullet 3.2.7 run uses Linux CPU DIRECT on Python 3.11. SOFA uses the official v26.06.00 Linux/Python 3.12 binary. The previous trial artifacts and the normal workflow resource limits apply to new runs.

## Offline verification

Extract the [published archive](https://huangkiki.github.io/Dexlab/en/latest/_static/incline-extension/native-v1.zip) and run the scorer with Python, NumPy and packaging. It recomputes each outcome from the native records, independently of the physics runtimes.

```bash
python -m zipfile -e docs/evidence/incline-extension/native-v1.zip "$OUT/records"
for engine in chaos bullet sofa; do
  PYTHONPATH=src python demos/contact-benchmark/score_incline_extension.py "$engine" \
    --manifest "$OUT/records/manifest.json" --records "$OUT/records/$engine" \
    --output "$OUT/$engine-results.json"
  cmp "$OUT/$engine-results.json" "$OUT/records/$engine-results.json"
done
PYTHONPATH=src:scripts python demos/contact-benchmark/plot_incline_extension.py \
  --records "$OUT/records" --output "$OUT/curves"
```

The overlays additionally need Matplotlib and the Noto CJK fonts. They use published 1 ms records for the original six engines alongside the three new traces.

## Regenerate native records

Build the small Chaos project against the pinned engine. Set `DEXLAB` to the repository root and `UE_ROOT` to the prepared UE checkout.

```bash
project="$DEXLAB/demos/contact-benchmark/chaos-incline/ChaosIncline.uproject"
manifest="$DEXLAB/docs/evidence/incline-extension/manifest.json"
mkdir -p "$OUT"
"$UE_ROOT/Engine/Build/BatchFiles/RunUBT.sh" ChaosInclineEditor Linux Development \
  -Project="$project" -MaxParallelActions=5 -NoDebugInfo -WaitMutex
"$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" "$project" \
  -ddc=NoZenLocalFallback -NullRHI -NoSound -Unattended -NoSplash -NoP4 -NoLiveCoding \
  '-ExecCmds=Automation RunTests DexLab.ChaosIncline;SoftQuit' \
  "-DexInclineManifest=$manifest" "-DexInclineOutput=$OUT/chaos" \
  "-ReportExportPath=$OUT/chaos-automation" "-AbsLog=$OUT/chaos.log"
```

For Bullet, install NumPy and the pinned `pybullet==3.2.7` wheel in an isolated Python 3.11 environment. For SOFA use its matching Python 3.12, SofaPython3 and shared library paths. [SOFA binary release and checksums](https://github.com/sofa-framework/sofa/releases/tag/v26.06.00) · [SofaPython3 setup](https://sofapython3.readthedocs.io/en/latest/content/Installation.html)

```bash
"$BULLET_PYTHON" demos/contact-benchmark/run_bullet_incline.py \
  --manifest "$manifest" --output "$OUT/bullet"
"$SOFA_PYTHON" demos/contact-benchmark/run_sofa_incline.py \
  --manifest "$manifest" --output "$OUT/sofa"
```

The Python recorders accept `--step .001` for the 1 ms cases. The matching Chaos argument is `-DexInclineStep=0.001`. Keep both source and configuration frozen across the full batch. Each engine records its force observation epoch. Only an independently valid record can satisfy the physical response checks.

## RaiSim 2.16.0

RaiSim uses the same manifest and thresholds. Extract its archive into the records directory from the offline verification section to rescore RaiSim and generate the ten-engine curves.

```bash
python -m zipfile -e docs/evidence/incline-extension/raisim-native-v1.zip "$OUT/records"
PYTHONPATH=src python demos/contact-benchmark/score_incline_extension.py raisim \
  --manifest "$OUT/records/manifest.json" --records "$OUT/records/raisim" \
  --output "$OUT/raisim-results.json"
cmp "$OUT/raisim-results.json" "$OUT/records/raisim-results.json"
PYTHONPATH=src:scripts python demos/contact-benchmark/plot_incline_extension.py \
  --records "$OUT/records" --output "$OUT/curves"
```

The archive has SHA-256 `d796881594c8afccdbc09c75588d533011c0035358bcd56793b437eb34bd70a0`. Its receipt records checksums for the raw files, recorder and scorer. Native execution requires the activated RaiSim 2.16.0 C++ SDK and the nlohmann_json development package. Set `RAISIM_SDK` to the SDK install prefix. The recorder uses the SDK's normal activation lookup or an optional `RAISIM_ACTIVATION_FILE` path.

```bash
cmake -S demos/contact-benchmark/raisim-incline -B "$OUT/raisim-build" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$RAISIM_SDK"
cmake --build "$OUT/raisim-build" --parallel 2
"$OUT/raisim-build/record_raisim_incline" \
  docs/evidence/incline-extension/manifest.json "$OUT/raisim"
```

[Results and first-failure measurements](https://huangkiki.github.io/Dexlab/en/latest/raisim-incline.html) · [RaiSim installation](https://raisim.com/sections/Installation.html)
