# Passive-settling observation

[English](SETTLING.md) | [简体中文](SETTLING.zh-CN.md)

**Implemented and tested with synthetic states; new remote dynamics and the complete release gate are pending.** No measured first-crossing time or physics repair is claimed.

The historical recording begins after two seconds of passive settling, arm planning, and a velocity/time reset. Its first frame already intersects the table; that recording cannot reveal when the intersection first arose. The optional recorder covers initialization before planning and resets.

## Record on the qualified simulation host

After normal resource admission, use the existing robot asset configuration and a fresh output directory:

```bash
bash demos/cloth-folding/run.sh --task grasp --timestep .00025 \
  --record-settling --no-video --output demos/cloth-folding/runs/settling-diagnostic-v1
```

This still runs the complete grasp episode. Initialization remains 2 s, CG, 100 iterations and 0.5 ms steps; manipulation still switches to Newton at the requested timestep. These parameters come from the existing demo, not material calibration. Recording is off by default. When enabled, it copies the initial state and all 4,000 settling steps: 4,001 states when complete.

`settling/` stores the compiled initialization model, time, actual `qpos`/`qvel`, triangle topology, source/file hashes, engine identity and completion metadata. It does not save contact distances or forces. Copying performs no dynamics/contact queries or live-state modification. Recording adds overhead, so this is not baseline timing. Budget the additional arrays and model before dispatch; remote output size has not yet been measured.

On a Python exception, the recorder preserves the successful prefix, writes a separate `failed-state.npz`, marks the record incomplete and propagates the exception. Existing output directories are refused. Process termination or a disk write failure may still leave an incomplete directory: this is neither a crash-proof journal nor a restart checkpoint.

## Analyze without integration

After archiving, write the report outside the original record:

```bash
.venv/bin/python demos/cloth-folding/src/settling_trace.py \
  demos/cloth-folding/runs/settling-diagnostic-v1/settling \
  --output demos/cloth-folding/runs/settling-onset-v1.json
```

The analyzer validates hashes, the physical-step grid, actual-state dimensions and topology. Kinematics reconstructs the cloth; the independently tested triangle-interior/box calculation inspects each saved step until the first intrusion. The report identifies the witness triangle, coordinates/depth, previous sampled state without intrusion and actual inspected frame count. Initial intrusion has no preceding clear sample. An incomplete prefix remains incomplete even when no intersection is found.

The 10 nm numerical zero tolerance is a geometry tolerance, not a new physical threshold. This checks a zero-thickness midsurface against the verified solid table, not cloth thickness, robot contact, support force or grasp success. Later frames are not geometrically assessed after the first intrusion. Consecutive steps cannot guarantee inter-step separation; the previous clear sample is not a continuous-time onset bound. Exit code 0 means analysis completed, not physics passed.

## Validation and next experiment

Synthetic tests cover interior crossing with all vertices outside, initial intrusion, clear sequences, missing steps, corrupt inputs, partial failure, no-overwrite behavior and read-only analysis. A stubbed stepping test checks identical 4,000 initialization calls and final states with recording on/off; this is not native dynamics regression.

Next: run the unchanged configuration remotely, preserve initialization and complete grasp records, locate the first sampled intrusion, then design one-factor contact/mesh experiments. The [table-contact](TABLE-CONTACT.md) and [robot-contact](ROBOT-CONTACT.md) diagnostics remain separate evidence. Official engine binaries, control commands and physical thresholds are unchanged.
