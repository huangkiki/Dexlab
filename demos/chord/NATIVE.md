# Run and inspect a native CHORD task

[简体中文](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/NATIVE.zh-CN.md) · [Task preparation](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/README.md) · [Native migration issue](https://github.com/huangkiki/Dexlab/issues/285)

The first tissue-box policy has completed **32 environments × 50 iterations × 24 rollout steps = 38,400 samples**, followed by a separate 600-step native checkpoint reload. All 21 Adam parameter states reached 1,000 updates and contain finite, nonzero moments. This establishes execution of the training and reload path, not successful manipulation.

**Training and native reload: 1/3 demonstration tasks. Qualified recording and independent scoring: 0/3. Fully migrated: 0/3.** The procedural synthbox smoke is separate: one environment, one iteration, eight samples and 20 optimizer updates; it also completed a 600-step reload. ARCTIC box-grab and mixer-use still require authorized data and matching assets.

The [measured result manifest](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/results/native-20261102.json) contains checkpoint identities, native settings, artifact hashes and unsuccessful attempts. Raw attempts are preserved locally; this compact manifest is not a public raw-data archive. No native task video was captured.

## What the recording checks found

The tissue recorder wrote 600 pre-step records, 600 post-step records **before automatic reset**, and 3,000 physics-substep records of the applied virtual-object-control (VOC) commands. Its measured scale and applied command components were all zero. These are controller outputs, not contact-force measurements. Contact sensor buffers are recorded separately with explicit invalid-position masks.

The pinned upstream command resets the per-environment VOC scale to one, even when the evaluation configuration specifies zero assistance and zero decay steps. It only updates that scale after physics. The DexLab evaluator records this initial value and zeros the scale **before the first policy action**, without a warm-up physics step or a change to the original source. It rejects nonzero assistance before subsequent actions. Synthbox's first successful reload preceded this correction and is not VOC-off qualification.

The prospectively fixed recorder-parity tolerance is `1e-6` across all 600 returned action/observation/reward/done/object-state samples. It failed:

| Separate native processes | Maximum absolute discrepancy | Interpretation |
| --- | ---: | --- |
| GPU recorder off/on | 12.6922106743 | Recorder parity failed. |
| GPU recorder off/off repeat | 16.6666135788 | The underlying closed-loop run also fails this repeatability criterion; the recorder alone is not an established cause. |
| Default CPU recorder off/on | 15.9844508171 | Changing device did not qualify parity. |

The compared fields have different units; these maxima are **not position errors**. GPU off/on and off/off first exceeded tolerance at control step 28. A separate CPU enhanced-determinism/one-thread diagnostic stalled during initialization and was stopped with its native stack preserved; it is not a supported evaluation profile. The CPU path also warned about contact collision-group support, so its filtered contact matrices are not qualified.

`score.py tracking` rejects these attempts. No reward-derived success, reference-tracking score, holding/slip result or full-reference completion is claimed. The original tolerance and all failures remain intact in [#285](https://github.com/huangkiki/Dexlab/issues/285).

## Runtime used for these runs

The original CHORD checkout is fixed at `0530204f3a085fb9ba9cc41b771fc4c853edeab8`. The official image is `nvcr.io/nvidia/isaac-lab@sha256:f07c37e3f0c9f58f7febd0aa9a425523d282be623c0db81ac61006d0e24be07f`.

Release and Python-package versions are different: the image's Isaac Lab `VERSION` is **2.3.2**, while its `isaaclab` distribution is **0.54.2**. The standalone Isaac Sim `VERSION` is **5.1.0-rc.19+release.26219.9c81211b.gl** and it has no `isaacsim` distribution metadata. `runtime.py` preserves both identities without starting the simulator.

The runtime used Python 3.11.13, PyTorch 2.7.0+cu128, RSL-RL 3.1.2 and NumPy 1.26.0. Isolated additional packages were pyarrow 17.0.0, tensordict 0.8.3, wandb 0.22.2, onnxruntime 1.23.2, pytorch-ignite 0.5.3, coloredlogs 15.0.1 and humanfriendly 10.0. Whole-body task auto-import requires the ONNX/Ignite dependencies even for the Sharpa task. The downloaded official URDF importer was frozen at 2.4.31; later runs disabled registry updates.

Native readback identified `omni.physx-107.3.26`, TGS, GPU dynamics and broad phase, patch friction, PCM collision handling, 100 Hz physics and 20 Hz control. **The extension version is not the native PhysX core version; the latter remains unresolved.** These runs establish no cross-engine or material-equivalence result.

Follow the [pinned upstream setup](https://github.com/nvidia-isaac/video_to_data/blob/0530204f3a085fb9ba9cc41b771fc4c853edeab8/robotic_grounding/docs/SETUP.md) in a separate runtime. Accept the applicable licenses through your own authorized workflow. For the official container, provide writable Kit `cache`, `data` and `logs`, persistent runtime home, and timezone data. A read-only checkout also needs an installed/configured Git LFS clean filter with writable **external** `lfs.storage`; otherwise source verification can fail on correctly materialized assets. This does not waive any hash check.

## Reproduce the execution checks

`prepare.py` still only prepares commands. Its Hydra output now stays inside the fresh attempt. `motion.py` validates the actual legacy `ManoSharpaData` reader used by this dual-hand task, rather than the newer whole-body `motion_v1` reader. Tissue-box contains 390 source frames at 30 Hz; the native half-speed interpolation produces 518 reference frames at 20 Hz. A 600-step rollout can reset repeatedly and does not imply it completed all those reference frames.

Before executing any native command, use the [measured resource envelope and research lock](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.md#resources-and-recovery). The initial complex-model pilot used 24 GiB/4 CPU cores/256 tasks, then the approximately 5 GiB measured pilot selected an 8 GiB envelope with a 1.5 margin. Full training peaked at approximately 6 GiB within that limit; any new training batch must recalculate its margin. All attempts used zero cgroup swap and retained at least 8 GiB desktop reserve. The sampled whole-GPU stop threshold was 20,480 MiB; it is not a hard allocation quota. Each native attempt was limited to 900 seconds inside a 7,200-second cumulative native budget.

For containers, `bounded_run.py --delegate-containers` exposes `DEXLAB_BOUNDED_CGROUP`; the container must use that actual ancestor as `--cgroup-parent`, and its host PID membership must be verified. A successful Docker start alone is not isolation evidence. Keep environment installation, compression and large hashing outside timed native runs.

The following commands are **children of that qualified envelope**, in a namespace where the source, runtime, checkpoint and output paths are visible:

```bash
# Inspect a locally produced checkpoint; this does not claim native reload.
"$CHORD_PYTHON" demos/chord/checkpoint.py "$CHORD_CHECKPOINT"

# Two separate processes, identical source/checkpoint/seed and finite budgets.
"$CHORD_PYTHON" demos/chord/evaluate.py --task tissue-box \
  --source "$CHORD_SOURCE" --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/eval-off" --seed 24 --steps 600 --headless

"$CHORD_PYTHON" demos/chord/evaluate.py --task tissue-box \
  --source "$CHORD_SOURCE" --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/eval-on" --seed 24 --steps 600 --headless --record

# Offline NumPy scoring; inspect hashes before comparing preserved artifacts.
"$DEXLAB_PYTHON" demos/chord/score.py parity \
  "$CHORD_RUNS/eval-off" "$CHORD_RUNS/eval-on"
"$DEXLAB_PYTHON" demos/chord/score.py tracking \
  "$CHORD_RUNS/eval-on" "$CHORD_RUNS/eval-off"
```

Each evaluator attempt copies and hashes the checkpoint, verifies source identity, saves environment/agent configuration and records runtime identity plus invocation status. Existing attempts cannot be reused. `parity` returns exit code 2 on a measured mismatch; `tracking` recomputes parity and refuses unqualified records. A simulator process can exit zero after an initialization error, so require complete invocation records and actual optimizer/checkpoint evidence rather than an exit status alone.
