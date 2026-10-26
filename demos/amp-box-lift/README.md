# Public AMP box-lift baseline

[English](README.md) | [简体中文](README.zh-CN.md)

Prepare the public `Mjlab-G1-DualArm` checkpoint for an independent contact-supported lift evaluation. This is the AMP task with the Toaster003 asset. It is distinct from the same repository's SuperMimic/PPO-Sim tracking task and its 1.5 kg box. No native AMP evaluation has run in DexLab yet.

## Prepare the fixed inputs

The source is [humanoid-amp-ppo at 4889389](https://github.com/shuayyy/humanoid-amp-ppo/tree/4889389118e0c88d3945dff54d2cd3f992ed815e). Use a fresh directory on a data volume with at least 50 GiB free. On shared research hosts, run this transfer through `scripts/research_guard.py` and `scripts/bounded_run.py` using the archive envelope.

```bash
python demos/amp-box-lift/fetch_source.py "$OUT"
```

The helper checks out the exact commit, downloads the 11,932,163-byte `models/dualarm.pt` and two motion clips, verifies their Git blob identities and records SHA-256 hashes. It preserves the upstream lockfile and excludes unrelated videos and policy weights. Existing output directories are refused, and interrupted directories remain available for diagnosis. It does not install dependencies, execute a policy or train a model.

`inputs.json` proves byte identity only. The repository declares Apache-2.0 in its README and package metadata but supplies no separate license file. Original motion-capture and checkpoint-training lineage has not been independently established; preserve this limitation when assessing native admission or redistribution. No external weights, motion clips or meshes are bundled in DexLab.

The [asset provenance record](provenance.json) identifies all 35 meshes referenced by `g1_realsense.xml` as exact Git-blob matches to [Unitree's BSD-3-Clause source](https://github.com/unitreerobotics/unitree_ros/tree/15ebe53f4cd77e7d745ae83b9d7ff90e685e8998). All six Toaster003 visual payloads are byte-identical to the archive linked by [RoboCasa's asset registry](https://github.com/robocasa/robocasa/blob/2ce1aecdd76e29b52d32fdb160436c5a3e230b07/robocasa/models/assets/box_links/box_links_assets.json); [its README](https://github.com/robocasa/robocasa/blob/2ce1aecdd76e29b52d32fdb160436c5a3e230b07/README.md) declares CC BY 4.0 for assets. The AMP XML adds a free root, grasp sites/collision markers and explicit inertials. The verified archive uses 9,389 bytes for its XML; the two XML hashes intentionally differ. These checks establish the identified payload lineage, not original training-data provenance or a physical result.

## Keep these task conditions separate

- The public AMP task uses high-friction grasp-marker geometries. Read effective native parameters and compiled mass/inertia; do not borrow the tracking task's dimensions or 1.5 kg mass.
- Source `play=True` disables virtual PD, curriculum and observation corruption. It retains 25% reference-state initialization and randomized object XY/yaw. Record actual initial states and distinguish standing from reference-state starts.
- Startup randomization also retains object mass scaling (0.7–1.5 on the main body), robot/object COM offsets and foot/robot/object friction changes. The XML's nominal inertial mass sum is 1.30 kg; the executing GPU model must supply the episode's actual mass, inertia, COM and contact parameters. The CPU model template alone omits these randomized values.
- The source hold predicate uses height above a one-sided threshold and both marker sensors for 20 control steps, or 0.4 s. A sensor `found` flag is not evidence of a loaded contact. Preserve that source score separately from independent carrying, slip, support and momentum diagnostics.
- The play horizon is 60 s. Record the final native substep before its automatic timeout reset; a reset observation must not replace the trajectory endpoint.

The source lockfile pins mjlab 1.4.0, MuJoCo 3.10.0, MuJoCo Warp 3.8.0.2, Warp 1.15.0 and Torch 2.13.0. This reference stack is separate from the landing case and DexLab's current submission profile. Environment compatibility and recorder qualification remain pending.

The pinned dependency metadata is inconsistent: [mjlab's pyproject](https://github.com/mujocolab/mjlab/blob/4360096b49c1bcc478668c11ce7d458db747e49d/pyproject.toml) requires MuJoCo Warp `>=3.8.0.3,~=3.8.0`, while its selected [Warp commit declares 3.8.0.2](https://github.com/google-deepmind/mujoco_warp/blob/88b55fc2696960b927bc12584994bb8412b36558/pyproject.toml). The selected candidate uses official MuJoCo Warp **3.8.0.3**, preserving all other source lock pins. Its [release comparison](https://github.com/google-deepmind/mujoco_warp/compare/88b55fc2696960b927bc12584994bb8412b36558...79c37d3e8630aba40c2b8023fa9a073fb27b62d0) changes version metadata and benchmark scripts; the complete `mujoco_warp` runtime subtree has the same Git identity, `97b878909d10a074f357f5b2a9b588e6cd696a67`, at both commits. This resolves the version constraint without modifying engine payloads. It does not establish native compatibility. The source's explicit MuJoCo dependency override is retained; do not silently replace MuJoCo 3.10.0 with a different version.

## Install the isolated candidate runtime

[requirements-linux-cp312.txt](requirements-linux-cp312.txt) preserves the selected Linux x86_64 / CPython 3.12 artifacts with published hashes and pinned Git revisions. This is a candidate installation recipe, not a verified native environment. It retains the source lock's explicit dependency overrides, so install without resolving a new dependency set.

Set `DEXLAB_ROOT` to this checkout, `SOURCE` to the verified source directory and `AMP_ENV` to a **new** data-volume environment. Run the installation inside the bounded archive window with the mounted data-volume cache; it downloads about 3.2 GB and may build the pinned evdev source package. Preserve a failed environment and its logs instead of resetting another environment.

```bash
test "$(uname -s)" = Linux && test "$(uname -m)" = x86_64 || exit 1
test ! -e "$AMP_ENV" || exit 1
uv venv --python 3.12 "$AMP_ENV"
uv pip install --python "$AMP_ENV/bin/python" --no-deps \
  -r "$DEXLAB_ROOT/demos/amp-box-lift/requirements-linux-cp312.txt"
uv pip install --python "$AMP_ENV/bin/python" --no-deps \
  -e "$SOURCE/rsl_rl" -e "$SOURCE" -e "$DEXLAB_ROOT"
```

Use this environment's Python for the native commands below. The runner independently checks package versions, Git provenance, wheel hash and imported source paths before environment construction. Successful installation alone does not qualify CUDA execution or recorder parity.

## Bounded evaluation entry

`protocol.json` specifies two fresh-process recorder parity probes, three 60 s policy runs (seeds 137–139) and a seed-137 negative control that disables the four hand/wrist collision geometries. The negative also removes their ground collisions; other body support remains possible and must be reported. The ceiling is six native starts, 900 s per process and 5,400 s total. This protocol does not itself admit a launch: input provenance, the isolated runtime and a measured resource plan remain prerequisites.

After those prerequisites, create a new durable budget once, then run each named case inside the existing research guard and bounded runner:

```bash
python demos/amp-box-lift/init_budget.py "$BUDGET" --resource-plan "$RESOURCE_PLAN"
CUDA_VISIBLE_DEVICES="$GPU_UUID" python demos/amp-box-lift/run.py --upstream "$SOURCE" --budget "$BUDGET" \
  --case probe-native --output "$RUN" --resources "$RESOURCE_RECEIPT"
```

`RESOURCE_RECEIPT` is the enclosing `bounded_run.py` receipt, not a manually supplied success flag. Run `probe-recorded` in a separate process and fresh output directory, then execute `python demos/amp-box-lift/qualify.py --budget "$BUDGET"` offline. Qualification compares the complete control records, actual randomized model, native substeps and independent force decoding, and requires both services' final telemetry. Full episodes reject missing or changed qualification. A timeout or interrupted budget must be recovered; never recreate it to clear spent attempts.

For each native invocation, the outer bounded runner must use `--gpu-uuid "$GPU_UUID" --gpu-memory-limit-mib 20480`, with the same UUID in `CUDA_VISIBLE_DEVICES`. The protocol requires at least 2,048 MiB device reserve. The opt-in guard samples whole-device usage every 2 s and stops only its workload process group on overage or missing telemetry, preserving the final resource receipt. This is a sampled stop threshold, not a hard GPU allocation cap; intervening peaks are unobserved. Existing bounded runs without these options keep their prior behavior. The AMP runner rejects absent or mismatched live resource telemetry before creating the environment.

The runner follows the source actor-loading and inference path, keeps the original action clipping and sole initial reset, and captures terminal feedback before the original automatic reset. It saves both that endpoint and the returned post-reset observations with their different meanings. No renderer, training call or new state injection is introduced. Native runs, physical episode scoring and videos are still pending.

## Recorder implementation status

`dexlab.amp_lift_record.AmpLiftRecorder` observes the original `sim.step()` boundary, preserving its CUDA graph. It saves state before and after every native substep, applied forces, solver iterations, raw contact/constraint arrays and the original Warp decoder's contact force. It keeps randomized GPU model fields alongside the CPU model template, rejects contact-capacity overflow and flushes an interrupted action's observed prefix. It does not execute `mj_forward` or substitute a CPU solve.

`dexlab.amp_lift_audit` independently converts the retained solved constraints to contact forces. Analytical fixtures cover pyramidal and elliptic representations, inactive contacts, missing/overflowed addresses and a deliberately corrupted force. Offline tests also reject missing final resource telemetry and preserve the terminal hold state across automatic reset. These are representation/integrity tests, not evidence of carrying or native recorder qualification.

The same module separates object wrenches from left-hand, right-hand, ground and other contacts using explicit compiled geometry IDs. It counts loaded pairs before force cancellation and computes articulated-object momentum from each body's mass, inertia and native COM kinematics. The frame conversion also matches a separate CPU MuJoCo subtree-kinematics fixture. These helpers do not assume all fields returned after a step share the post-integration epoch, and do not assign task success.

## Offline trajectory diagnostics

After a recorded run, recompute its diagnostics into a fresh output directory:

```bash
python demos/amp-box-lift/score.py --run "$RUN" --output "$AUDIT"
python demos/amp-box-lift/pair.py --reference "$SEED137_RUN" \
  --negative "$NO_HAND_RUN" --output "$PAIR_REPORT"
```

The report preserves every continuous bilateral carrying window, loaded ground/other support, object tilt and penetration, hand-relative drift, actuator-force-limit samples, applied inputs and adjacent-epoch momentum residuals. It checks the initial state, every substep boundary and the pre-reset terminal state, independently decodes forces, and hashes the consumed records. Native float32 time is checked against its actual rounded addition; a fixed absolute clock tolerance would incorrectly reject valid late-episode steps.

Window durations use native step count times the protocol timestep; quantized native-clock elapsed time is retained separately. Net lift uses the identified object free joint's initial and final integrated positions before reset. The contact-epoch sampled lift is reported separately, so the last derived position cannot replace the integrated endpoint.

The 2 s carrying diagnostic rejects ground support and isolated final-frame height. Hand-relative drift removes common hand/object motion but is not material contact-patch slip. Momentum residuals currently include contacts and gravity; armature, applied generalized forces, non-contact constraints and integration effects require attribution before physical qualification. The last integrated endpoint has no following native kinematic sample, so a complete 12,000-step run provides 11,999 adjacent momentum intervals. Source success and `task_success: null` remain separate. Analytical fixtures test these distinctions; native runs and video acceptance remain pending.

`pair.py` checks the two completed seed-137 cases against their checkpoint/runtime identity, initial state and effective physical model. Only the four declared hand/wrist collision masks may change. Compiler-generated collision candidate lists are excluded because disabling geometries changes their extent; explicit pairs that bypass the masks are rejected. A changed mass or unmatched initial state prevents interpreting the negative as a paired control.

[Issue #259](https://github.com/huangkiki/Dexlab/issues/259) retains the finite native protocol, positive/negative controls, independent scoring, complete trajectories and bilingual results. Missing tracking checkpoints, the squat/lift comparison and any matched SuperMimic/PPO comparison remain separate obligations; this AMP preparation does not resolve them.
