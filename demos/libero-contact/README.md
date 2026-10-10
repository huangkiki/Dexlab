# Native LIBERO contact diagnosis

This is the official **LIBERO-Object cream-cheese-to-basket task**, using Panda, the dataset controller, original assets, initial state and native success predicate. DexLab records action execution and diagnoses the workflow. It does not train a policy, change solver source, or count playback as task success. mjlab is outside this round.

See the [bilingual results and synchronized comparison](https://huangkiki.github.io/Dexlab/en/latest/libero-workflow.html). The first development demonstrations complete the original task; the reported slip is a hypothesis, not an established defect.

## Reproduce the frozen cohort

Use an isolated **Python 3.10** environment for the pinned legacy diagnostic stack (robosuite 1.4.0 / MuJoCo 2.3.7). The main DexLab environment remains Python 3.12 with its separately qualified cores. Do not downgrade it.

```bash
python3.10 -m venv /path/to/libero-env
/path/to/libero-env/bin/pip install -r demos/libero-contact/runtime.lock
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git /path/to/LIBERO
git -C /path/to/LIBERO checkout 8f1084e3132a39270c3a13ebe37270a43ece2a01
/path/to/libero-env/bin/pip install --no-deps -e /path/to/LIBERO
```

Download only [this official task dataset](https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/resolve/f13aa24a3da8c43c7225569f28c562979fa0e35a/libero_object/pick_up_the_cream_cheese_and_place_it_in_the_basket_demo.hdf5). Its SHA-256 must be `7ae50ed3a64bab8418fd6c8e346ba1c39da0fdaa62916a87b9d20f3745b45406`. The upstream full learning environment documents Python 3.8 / PyTorch 1.11; this Python 3.10 path qualifies native simulation and action replay only. Official source: MIT; dataset card: Apache-2.0. Assets retain upstream licensing; we publish derived observations and rendered views, not a replacement asset distribution.

```bash
/path/to/libero-env/bin/python demos/libero-contact/prepare.py \
  --libero-root /path/to/LIBERO --dataset /path/to/cream_cheese.hdf5 \
  --output /path/on/mounted-data/libero-run
export PYTHONPATH="$PWD/src"
/path/to/libero-env/bin/python -m dexlab.libero_trials status /path/on/mounted-data/libero-run/campaign
```

`prepare.py` verifies the single dataset, freezes dependency versions, source hashes, eight candidates, three development demonstrations and ten unseen demonstrations. The runner adds the official checkout to `PYTHONPATH`, required by this upstream namespace layout. It rejects a dirty or different upstream revision. Frozen inputs are rechecked at launch.

Run each candidate/demonstration through the existing `scripts/bounded_run.py` and `scripts/research_guard.py` admission/lock. Use the frozen adaptive resource plan: initially 16 GiB, 4 CPU equivalents, swap disabled, 8 GiB desktop reserve. The command inside the guard is:

```bash
/path/to/libero-env/bin/python -m dexlab.libero_trials run CAMPAIGN baseline demo_0
```

Execute baseline, step-1000us, step-500us, aligned-2000us, aligned-1000us and aligned-500us on `demo_0..2`; run recording-off and settle-audit on demo_0. All actions, including release and the final state, are retained. Then:

```bash
/path/to/libero-env/bin/python demos/libero-contact/select.py CAMPAIGN
```

This atomically freezes the development-only challenger. Heldout runs permit only baseline and this challenger on `demo_3..12`. No reselection after heldout. An unqualified challenger is a sensitivity comparison, not a recommended physics configuration. Each six-hour package allows at most eight candidates and 64 starts, including infrastructure failures. Interrupted reservations block new launches until `python -m dexlab.libero_trials recover CAMPAIGN` verifies the process is gone and accounts for its evidence. Source revisions must inherit the previous ledger; they cannot reset the budget.

## Apply and undo the observation correction

The pinned independent evaluator discards all five settling observations; the training evaluator refreshes them. The patch changes only observation assignment, preserving all five zero actions and the controller/physics sequence. Apply it to a **separate copy** of the official checkout; the reference source remains immutable:

```bash
git -C /path/to/patched-LIBERO apply --check /absolute/path/to/DexLab/demos/libero-contact/patches/refresh-settle-observation.patch
git -C /path/to/patched-LIBERO apply /absolute/path/to/DexLab/demos/libero-contact/patches/refresh-settle-observation.patch
# Undo:
git -C /path/to/patched-LIBERO apply -R /absolute/path/to/DexLab/demos/libero-contact/patches/refresh-settle-observation.patch
```

The audit measures native proprioception before/after settling. Without a compatible fixed checkpoint it does **not** establish a different first policy action or improved closed-loop success. Demo actions are observation-independent. Camera observations are disabled during recorded physics; rendered states are a separate output, not policy input.

## Evidence and rendering

```bash
/path/to/libero-env/bin/python -m dexlab.libero_score ATTEMPT/raw
/path/to/libero-env/bin/python demos/libero-contact/export.py CAMPAIGN NEW_PORTABLE_OUTPUT
MUJOCO_GL=egl /path/to/libero-env/bin/python demos/libero-contact/render.py \
  ATTEMPT/raw OUTPUT.mp4 --label 'Original / 2 ms'
```

Rendering loads the recorded full native state at 20 Hz, uses the same camera/scale and calls only `mj_forward`. Contact curves retain every integration step. The display clock starts at zero; native initial time is 0.25 s. Derived body observations and contact forces belong to the last **pre-integration** substep; state rows are **post-integration**. Full-precision parameter JSON is authoritative; saved XML is only the visualization model and may round numbers.

The published initial state contains time/qpos/qvel, not historical controller memory. Replay uses native reset plus the entire action prefix; mid-episode restores are not qualified. Published dataset terminal reward/done flags are not used for scoring: native `_check_success()` is queried for each actual action.

The scorer checks observation integrity separately from original task success and declared numerical screening (maximum target overlap ≤1 mm; p99 COM momentum residual ≤5% of weight). These screens are not official LIBERO criteria or measured material accuracy. Translational balance does not establish rotational balance. Relative gripper-frame height includes rotation and release, so it is not a pure slip measurement. Actual contact normals, actuator output and commanded controls are distinct channels.

For downloaded portable case folders, add `--libero-root /path/to/LIBERO` to the render command. XML asset locations are relocated without altering physical attributes; raw numerical arrays and contacts retain their original hashes. Native hashes and derivative export hashes are recorded separately.

The archive includes the four exact source files frozen for the executed v5 campaign. Release admission additionally verifies the declared upstream identity, selection evidence hashes and unchanged selection across heldout launches; recorder/scorer physics and the published scores are unchanged. New campaigns freeze the installed release sources.
