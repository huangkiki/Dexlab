# Prepare and run a CHORD task

[简体中文](README.zh-CN.md) | [Tracking issue](https://github.com/huangkiki/Dexlab/issues/282)

Prepare one fixed Sharpa/Isaac Lab task for training or checkpoint evaluation. The tool inventories local inputs and writes an isolated upstream command; it does **not** launch training. The separate [native execution path](NATIVE.md) has trained and reloaded tissue-box: **1/3 training/reload, 0/3 qualified recording/scoring and full migration**. Recorder parity failed; no learned-skill result is claimed.

## Task cards

| CLI task | Fixed sequence | Recipe and present limit |
| --- | --- | --- |
| `tissue-box` | `tissue_box_simple` | Bundled monocular reconstruction; force-closure guidance. Contact-matching rewards are disabled both initially and in the curriculum. |
| `box-grab` | `dataset_s07_box_grab_01` | ARCTIC contact-wrench guidance; keep the articulated box. Licensed processed motion, matching assets and checkpoint access are required. |
| `mixer-use` | `dataset_s01_mixer_use_01` | ARCTIC articulated manipulation; same data gates. Joint/hold/release scoring awaits reference-phase inspection. |
| `synthbox-smoke` | `synthbox_box_open_000` | Procedural engineering fixture only. One environment, one iteration, eight rollout steps and primitive robot collision geometry; excluded from the 3-task count. |

The task cards retain their static `source-checked` status. `blocked` is a local preflight result, not a failed policy. Actual native attempts and their distinct training/recording/scoring states are in the [result manifest](results/native-20261102.json). The [manifest](tasks.json) pins upstream revision, paths, timing, source/terms and reward overrides. The manifest also carries verified upstream LFS SHA-256 values and preflight rejects mismatches. Actual file hashes are measured into each preflight; absent checkpoint hashes remain null. Neither a hash nor file presence grants a dataset license.

## Start with a local inventory

Use Python 3.10+ for this standard-library preparation tool. CHORD itself needs its **separate upstream Isaac Lab 2.3.2 environment**; do not install it into DexLab's Python environment. Follow the [pinned setup guide](https://github.com/nvidia-isaac/video_to_data/blob/0530204f3a085fb9ba9cc41b771fc4c853edeab8/robotic_grounding/docs/SETUP.md), including robot LFS files. ARCTIC/MANO and example checkpoints may require authorized accounts. This tool neither downloads nor accepts their terms.

Set `CHORD_SOURCE` to the repository root at `0530204f3a085fb9ba9cc41b771fc4c853edeab8`, `CHORD_PYTHON` to the interpreter/wrapper in that runtime, and `CHORD_RUNS` to an existing mounted data directory. Paths must be visible in the same host/container namespace. Optional `--data-root` replaces the upstream bundled `human_motion_data` root.

```bash
python3 demos/chord/prepare.py preflight --task tissue-box \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON"
```

The JSON lists each file with SHA-256, missing files/LFS pointers/error pages, URDF mesh dependencies, checkout identity, Python package metadata and GPU visibility. Exit 2 means a concrete blocker; exit 0 means only that these static checks found the inputs. Parquet magic is checked, **not** its semantic schema or valid motion. Native PhysX version, contact/VOC readbacks, license provenance and resource admission remain pending even on exit 0. The interpreter probe reads release files and package metadata separately without starting Isaac Sim.

## Prepare a finite command

The following only prepares a one-iteration command for inspection. It is not an adequate task-training budget or a migration result:

```bash
python3 demos/chord/prepare.py train --task tissue-box \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON" \
  --seed 24 --num-envs 1 --iterations 1 \
  --attempt "$CHORD_RUNS/tissue-plan-001"
```

Each new attempt contains `preflight.json`, `command.json` and a review-only `command.txt`. A blocked plan is retained with exit 2. Explicit seed, environment count and iterations prevent accidental use of upstream's large defaults. Real tasks retain 24 rollout steps per environment, 100 Hz physics and 20 Hz control. Preparation does not enforce wall time or allocate the GPU. Before executing the reviewed command, qualify inputs in the upstream loader and freeze measured budgets using DexLab's [resource controls](../../docs/task-coverage.md#resources-and-recovery), `research_guard.py` and `bounded_run.py`. Never execute outside those controls or treat `execution_admitted: false` as approval.

To prepare evaluation, supply an explicit checkpoint and positive step limit:

```bash
python3 demos/chord/prepare.py eval --task box-grab \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON" \
  --seed 24 --num-envs 1 --steps 200 --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/box-eval-plan-001"
```

The checkpoint is copied and hash-checked inside the new attempt because upstream exports files beside it. Existing attempts, including interrupted ones, are rejected. The pinned evaluation script resets to the first reference frame, disables VOC and removes its curriculum; actual assistance still requires native verification. A reference that begins in contact cannot establish acquisition from free placement. The generated upstream command preserves that source configuration, not proof that it executed it. Native readback found a first-step reset-assistance gap; the [DexLab evaluator](NATIVE.md) corrects it before the first action.

## Remaining migration work

Issue #282 retains actual optimizer updates/checkpoint reload, native recording, recorder parity, finite per-task training, independent evaluation/scoring and sourced replay. A prepared command, a successful process exit or pretrained weights alone meet none of those scientific acceptance conditions. PhysX is the sole selected training backend; other DexLab engines are not supported by this migration. FlashCHORD/Newton, Wuji retargeting and cross-engine comparisons are deferred.
