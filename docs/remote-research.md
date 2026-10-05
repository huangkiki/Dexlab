# Remote research and verified archives

[English](remote-research.md) | [简体中文](remote-research.zh-CN.md)

Qualification binds an exact source tree, asset profile, installed environment and official engine hashes to completed runs. It is evidence that this runtime can execute the recorded workload. It is not a benchmark ranking, proof of fresh-machine installation, or permission to run six experiments concurrently.

## Execution and measurements

Local-first execution is described in [the execution workflow](autoresearch.md#local-first-execution-and-recovery). The following remote procedure is optional: use an isolated remote checkout and its own editable environment. Preserve previous runs: each `autoresearch check` generates a unique output directory. `submit --check-remote "$DEXLAB_CHECKOUT" --remote-state "$REMOTE_STATE"` guards the entire remote gate and records separate episode and independent-verifier resource receipts. The source tree must match before and after the checks. Deployment values belong only in private configuration.

Record the environment/package inventory, source tree, input hashes, native library hashes, commands, failures and available disk space alongside the receipts. The existing UniSim adapter patch remains disclosed; this does not alter official MuJoCo or SuperDex binaries. Shared immutable packages/assets may be reused, but the project's editable installation must resolve to the tested checkout.

| Measurement | Boundary |
|---|---|
| `engine.json: physics_step_seconds` | Existing native stepping timer; excludes the full task's setup, control and recording costs |
| `runtime-timing.json: preparation_seconds` | Task initialization, including preparation inside `init_state` |
| `episode_and_recording_seconds` | Task stepping loop, including controller, recording and embedded scoring work |
| `total_task_seconds` | Initialization through close; excludes earlier imports/registry setup |
| Episode/verifier resource JSON | GNU time wall time, user/system CPU, largest child RSS high-water mark and exit code, each command separately |
| Guard receipt | Entire guarded command; RSS is not the sum of concurrent process peaks |

These durations overlap and must not be added together. Headless runs disable live rendering, but may still build display assets. Disk growth is measured separately from memory. Start with one job; qualify increased concurrency using measured CPU, memory and disk headroom. GPU count does not establish acceleration of these CPU physics backends.

## Cooperative window exclusion

`scripts/research_guard.py` uses Linux `flock` plus a persistent process-group marker. All managed timed runs and transfer/compression/hash work share one lock per host. Hold the controller's local lock throughout the whole operation, including local verification, and guard remote commands using the same remote lock:

```bash
python3 scripts/research_guard.py run \
  --lock "$LOCAL_STATE/window.lock" --kind qualification \
  --receipt "$LOCAL_STATE/unique-gate.json" -- \
  python3 scripts/autoresearch.py submit 29 --summary-file "$REVIEW" \
    --check-remote "$DEXLAB_CHECKOUT" --remote-state "$REMOTE_STATE"
```

Before starting any new window's data hashing/copying, probe the remote guard with a foreground `true` command and a new receipt, while holding the local lock. This detects work surviving a controller/SSH crash. For a formal timing window, use `--kind timing`, run only the measured command, and move setup, transfers, compression, hashes and reporting outside that interval. Inspect unrelated system activity separately. The qualification gate includes tests and source hashing and must not be presented as an isolated performance experiment.

Only one controller owns this queue. Commands must remain foreground in the guarded process group; do not daemonize or start detached descendants. The guard covers cooperative jobs, not arbitrary other users/processes. A guard killed while descendants survive leaves an active marker: new work fails with exit 75 until that group finishes. Once no live members remain, the next receipt records recovery. Do not delete lock files or manually clear live markers. Failed commands preserve their nonzero exit and receipt; a reused receipt path is refused.

## Archive a sealed apple run

Store a private JSON file containing `ssh_alias`, an absolute `remote_root`, and `archive_policy` with `local_root`, `nice` (15) and `bandwidth_KiB_per_second` (16384). Prepare/mount the archive volume first. Keep this file and raw receipts outside Git and Obsidian exports.

```bash
.venv/bin/python scripts/archive_run.py archive --config "$PRIVATE_CONFIG" \
  --checkout "$REMOTE_CHECKOUT_RELATIVE" --source "$REMOTE_RUN_RELATIVE" \
  --archive-id "$UNIQUE_RUN_ID"
```

This command owns the local window, guards remote hashing and rsync, uses one transfer at a time, idle I/O priority, and disables SSH/rsync compression. It snapshots the sealed source before and after transfer, validates every file count/size/SHA-256, reads the model and recorded states offline without simulation, independently scores the copy, and rechecks that reading did not modify the original records. It promotes a sibling staging directory only after these checks. Sidecar receipts are outside the run. A scientific failure remains a valid archive; an incomplete episode is not marked complete.

Resume with the same archive ID only for the exact unchanged source. Changed, extra or missing files fail closed; retain both source and staging data for diagnosis. Promotion and final-receipt interruptions are recoverable. No step deletes remote source data.

MuJoCo reading loads the native model and saved `qpos`; SuperDex reading loads a display-only mocap proxy and saved poses, **not a native SuperDex checkpoint**. External display assets are resolved in memory against the published hash-verified asset profile. Preserve the source/environment/input bundle separately for reproduction; a raw run directory alone does not contain the runtime or all shared assets.

## Validation scope

Tests exercise both real-process lock acquisition orders, a killed guard with a surviving child, nonzero commands, immutable receipts, corruption/missing/extra/symlink rejection, interrupted archive promotion, and separate native/display readers. Full remote qualification additionally requires both unchanged 14 s apple acceptance scorers, offline cloth rescoring with an identified scorer snapshot, a real cross-host archive and measured resource limits. Publish sanitized evidence only. Passing infrastructure checks does not resolve the cloth penetration defect or validate real hardware.

## Hard bounds for local archival

The public `archive` command now requires `archive_policy.io_device` in the private configuration and launches `scripts/bounded_run.py`. Use the archive volume's actual backing block device; do not copy another machine's device name. The system transient service runs as the invoking ordinary user. It requires an existing administrator-provided ability to run `sudo -n systemd-run`; the script does not install privileges or silently fall back to an unbounded process.

Before spawning archival, read back effective cgroup v2 limits: 8 GiB memory maximum, 6 GiB high watermark, zero swap, one CPU quota, 32 tasks, device read 16 MiB/s and write 8 MiB/s. Runtime is limited to 900 seconds. Missing controllers or mismatched limits reject execution. The internal archive entry also checks these limits. Timing and archive exclusion still use the existing research lock.

Resource receipts retain requested-operation status, effective limits, periodic cgroup counters and systemd termination result. Memory peak is kernel-measured; CPU/I/O counters are cumulative; interval-sampled rate peaks are reported separately and are not instantaneous peaks. Periodic snapshots can miss the final interval, and a killed monitor leaves incomplete telemetry. Such a run must not qualify an archive. Keep source and staging files; no source deletion is performed by this command. Use a fresh receipt on retry. Boot identity prevents stale process-group numbers from blocking recovery after a reboot; same-boot and legacy live groups remain protected.

Small local qualification checks exercised success, timeout and a 128 MiB allocation under a 64 MiB cap (isolated OOM). These establish resource enforcement, not the cause of an earlier desktop freeze or qualification of a large native-model archive. Release validation remains required.

A sealed historical SuperDex record (about 43 MB) was also hashed, read and scored under these limits: 29.8 s service wall time, about 1.08 GiB cgroup memory peak, unchanged source hashes. Its model is a display proxy, not a SuperDex native checkpoint; this is archival qualification, not engine performance. Stage receipts distinguish remote source snapshots, transfer and local verification/promotion. The 32-task cap can reject workloads that create concurrent native thread pools: one full-suite attempt failed at that cap, while the same 287 tests passed in the issue-specific editable environment using the existing direct-exec bounded launcher. Neither the cap nor acceptance criteria were relaxed. Full publication gates remain required on a qualified local or remote host.

The large historical MuJoCo archive also passed bounded native-model reading, independent scoring and SHA-256 readback. Only after local durability/readback, unchanged remote identity and a privileged read-only process-occupancy probe was its redundant remote copy removed; the full local archive remains. CPU/I/O peak rates are interval-sampled estimates (0.25 s), separate from kernel memory peaks and cumulative counters.
