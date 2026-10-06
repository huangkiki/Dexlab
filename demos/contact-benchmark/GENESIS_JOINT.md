# Genesis joint limits: audit imports before interpreting improvement

[简体中文](GENESIS_JOINT.zh-CN.md)

**The imported slider has extra armature; authored mass alone does not explain motion.** With explicitly zero armature, changing the limit time constant from10ms to4ms reduces peak violation from1.791mm to0.611mm, satisfying the previously frozen1mm engineering criterion. This does not establish hardware accuracy or transfer to other robots.

![Measured joint-limit trajectories](../../docs/evidence/genesis-joint-limits.png)

Every physics step uses measured joint position, not commanded position. All four enabled-limit upper-target traces are shown without smoothing. Lower-target and disabled-limit controls remain in the [complete score](../../docs/evidence/genesis-joint-score.json); [plot provenance](../../docs/evidence/genesis-joint-plot.json).

## Question and fixed criteria

Does timestep or constraint response explain overshoot? Does imported inertia match the declared model?

A synthetic0.1kg slider has range[0,50]mm, actual initialq25mm and targets−50/+100mm. Gravity and collisions are disabled. PD gains100/10, effort±5N,2ms steps,1s/500samples. Official Genesis1.4.3/Quadrants1.3.3, CPU FP64, Newton/approximate-implicitfast, no-slip disabled; full settings recorded.

Enabled limits must remain within1mm throughout. This is a preregistered engineering criterion, not a hardware/vendor tolerance. Disabled-limit controls must end at least10mm outside, detecting hidden target clamping. Mass, armature, inertia matrix, damping, gains, actual initial position, limits and effort range are independently checked; a good trajectory cannot compensate for a failed model audit.

## Import and instrumentation findings

Unspecified armature imports as0.1kg for this prismatic joint, giving physical generalized inertia0.2kg. Explicit zero gives0.1kg. Earlier results describe an as-imported configuration, not a pure0.1kg slider; retain both configurations.

In position mode, `get_mass_mat()` can include implicit actuator damping: here `dt*kv=0.02kg`. The corrected runner reads inertia in zero-force mode at rest with zero gravity before enabling position control. The initial scoring failure that treated this augmented matrix as physical inertia is retained as an instrumentation-semantics error, not a physics failure.

Native source: `genesis/utils/mjcf.py` imports solreflimit; `rigid_solver.py` sanitizes solver parameters and exposes the matrix; `abd/forward_dynamics.py` updates implicit matrices; `RigidJoint.get_sol_params()` reads actual parameters. No engine edits. Default time constant reads0.010s, explicit reads0.004s; the other six parameters match.

## Complete configuration results

16traces: two armatures × two time constants × limits on/off × both targets. One execution per configuration, not a success-rate estimate.

| Armature | Time constant | Enabled-limit peak, both directions(mm) | 1mm criterion |
|---|---:|---:|---|
| Imported0.1kg | 10ms | 1.498 | Fail |
| Imported0.1kg | 4ms | 0.226 | Pass |
| Explicit0kg | 10ms | 1.791 | Fail |
| Explicit0kg | 4ms | 0.611 | Pass |

All16 model audits match their declared configurations. All8 disabled controls exceed approximately50mm. Earlier as-imported10ms-response runs at2/1/0.5ms steps peak at1.498/1.902/1.914mm, all failing1mm. Finer timesteps alone did not fix this configuration. That historical refinement is not a zero-armature study.

## Reproduction and remaining scope

Use the [Genesis environment](GENESIS_CONE.md) and bounded resource admission:

```bash
python -m dexlab.genesis_joint_probe /path/to/new-output
python -m dexlab.genesis_joint_score /path/to/new-output
python scripts/plot_genesis_joint.py /path/to/new-output /path/to/new-figure.png
```

Output overwrite is refused. Source hash, models, native parameters, full traces and phase timings are retained; scoring does not import the engine. Raw archive delivery accompanies a future release; current figures/scores are locally validated candidate evidence, not a publication claim. Short CPU runs are not speed rankings.

This adopts [Manda's layered audit method](https://mandarobotics.com/blog/comparing-physics-engines/index.html), not a reproduction of its pendulum experiment. #42 pinch/release, GPU batching, continuous replay and hardware calibration remain incomplete.

Evidence bundle: [release attachment](https://github.com/huangkiki/Dexlab/releases/download/v0.30.0/genesis-joint-evidence-v1.tar.gz), [hash manifest](../../docs/evidence/genesis-joint-manifest.json). The locally verified archive has80members,1,126,996bytes; SHA256 `5f93fdf18a6938a6d989fc40c728bf01db52d7a5207090bc5ee2df3134029a16`. It includes failed timestep refinements and the earlier matrix-readback mistake. The attachment becomes available when v0.30.0 is published.
