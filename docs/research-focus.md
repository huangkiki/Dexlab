# Research focus

[English](research-focus.md) | [简体中文](research-focus.zh-CN.md)

DexLab investigates **the validity and numerical behavior of robot simulation models**. Tasks provide repeatable experiments for examining rigid bodies, collision geometry, joints, contact, and drives. The objective is to explain and reduce modeling error while balancing physical fidelity, stability, and computational cost.

## Delivered scope and work queue

Five UniLab tasks cover apple stem, cloth, sliding, indentation and cylinder pinch. DexLab owns native MuJoCo/SuperDex grasp scenes. PhysX rigid paths use UniSim scene contracts and its Isaac Sim worker; surface cloth reuses runtime discovery only. The [complete inventory](inventory/README.md) maps controls, observations, independent scoring, parameter provenance and failures. Registration alone does not establish native backend equivalence.

New episodes also export a [read-only model audit](model-audit.md): source and runtime inertials, joints, drives, collision filters, and initial-overlap findings.

Historical deliveries and follow-up work are maintained in GitHub issues; the links below include completed slices, not only pending work:

- [模型审查 / Model audit](https://github.com/huangkiki/Dexlab/issues/1)
- [抖动与接触间断 / Stability diagnostics](https://github.com/huangkiki/Dexlab/issues/2)
- [冻结场景与步长研究 / Frozen regression](https://github.com/huangkiki/Dexlab/issues/3)
- [UniSim 内置适配器等价性 / Built-in adapter qualification](https://github.com/huangkiki/Dexlab/issues/4)
- [PhysX / IsaacSim](https://github.com/huangkiki/Dexlab/issues/5)
- [真机测量与校准 / Hardware calibration](https://github.com/huangkiki/Dexlab/issues/6)

## Parameter provenance and current assumptions

Record each parameter's value, units, source or derivation, uncertainty, and overrides. Keep measured values, inherited model values, geometric estimates, task assumptions, and numerical tuning distinct.

| Quantity | Current origin | Assumption or limitation |
|---|---|---|
| Robot geometry, joint frames, masses, centers of mass, inertia tensors | UniLab's OpenArm/Wuji prefab; [asset provenance](ASSETS.md) and [model transfer](../demos/apple-stem-grasp/src/mujoco_model.py) | Inherited model values, not independently measured or validated hardware parameters |
| Apple and stem geometry | Derived NVIDIA meshes with recorded source hashes | One rigid body; no bending, fracture, or deformable finger tissue |
| Apple mass | Explicit `mass=0.2` kg in [scene construction](../demos/apple-stem-grasp/src/wuji_stem_grasp.py) | Task assumption, not a weighed apple; mass properties constructed by SuperDex are transferred to MuJoCo |
| SDF resolution and collision filtering | Engine-specific discretization and adapter settings in [backend details](sdf-backends.md#engine-implementation) | Approximate surfaces and normals; finite sampling; local wrist self-collision exclusion |
| Friction and contact response | SuperDex friction 0.5 retained from the baseline; MuJoCo friction 1.0 set by the demo; penalty/constraint response and regularization configured in the controllers | Not identified skin–stem material properties; equal coefficients do not imply equivalent engine behavior |
| Joint drives and motion | Scripted targets, IK, gain/damping settings and grasp-height offsets in the controllers | Known-pose control with explicit motion priors; no learned grasp skill or measured actuator model |
| Timestep and solver tolerances | MuJoCo 0.5 ms; SuperDex 2 ms; engine-specific iteration limits | Numerical choices validated for this case, limited timestep experiments are separately reported, not a convergence proof or matched speed benchmark |
| Acceptance thresholds | Explicit task criteria in [the verifier](../demos/apple-stem-grasp/src/verify_sdf_grasp.py) | Engineering acceptance limits, not real-world accuracy estimates; do not relax them to hide failures |

The MuJoCo adapter temporarily uses positive inertial placeholders to compile massless links, restores their source values, and checks the assembled mass matrix before stepping. This documented conversion does not prove that every source link has physically realistic inertia.

## Investigation workflow

These are experiment-design principles; implementation scope and acceptance progress are maintained in the corresponding issues.

1. **Audit the model.** Check units and scale, frames, center of mass, inertia symmetry and physical plausibility, joint axes and limits, collision geometry, initial overlap, contact filters, and drive limits. Compare the collision model with the visible surface. Record source values and every local override.
2. **Isolate the failure.** Reduce a task to a settling body, one joint, a sliding contact, or a two-finger hold. Log the first failing step and retain its configuration. A visually quiet or successful trajectory alone is insufficient evidence.
3. **Vary one factor at a time.** Sweep geometry resolution, timestep/substeps, solver tolerance/iterations, contact response, friction, and drive gains separately. Recheck earlier passing cases. Changing friction, gains, and grasp alignment together cannot identify a single cause.
4. **Freeze and replay.** Fix acceptance criteria before tuning, retain failed trials, freeze the selected configuration, and evaluate held-out scenes. Save versions, hashes, initial conditions, commands, forces, states, verdicts, and continuous recordings.
5. **Calibrate against hardware.** When measurements are available, synchronize joint motion, load/force, object motion, and timing. Identify parameters on one dataset and validate on another, reporting sensor and identification uncertainty. This stage has not yet been performed here.

## Failure measurements

| Symptom | Evidence to collect | Hypotheses to test |
|---|---|---|
| Penetration or tunneling | Maximum depth, duration, contact normals, approach velocity, collision masks | Shape/scale error, initial overlap, insufficient sampling or temporal resolution, contact compliance |
| Jitter | Position/velocity and contact-force time series, RMS/peaks, frequency content | Drive–contact coupling, excessive stiffness, discontinuous normals, convergence limits |
| Intermittent contact or slip | Contact persistence, normal/tangential forces, support balance, relative translation/rotation | Geometry, alignment, insufficient normal load, friction law and regularization |
| Numerical instability | First non-finite state, solver warnings/residuals, acceleration spikes | Invalid inertia, contradictory constraints, timestep, drive or solver settings |
| Excessive cost | Preparation time, time per simulated second, per-step timings, memory, scene/contact counts | SDF construction, collision workload, solver iterations, recording and rendering overhead |

These are investigation hypotheses, not diagnoses from appearance alone. Compliant-contact overlap should be assessed against declared tolerances and geometry scale. Current wrist-relative object displacement is not cumulative material-point slip; momentum balance is not an energy-conservation test. The [offline jitter diagnostics](jitter.md) report RMS/peaks, sampling coverage and per-pad low-load intervals without changing grasp thresholds. Full energy balance is unavailable from current logs.

For parameter semantics, consult [MuJoCo's solver guide](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters), the [SuperDex source references](sdf-backends.md#engine-implementation), and the PhysX [rigid-body dynamics guide](https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/RigidBodyDynamics.html). Engine-specific settings should be compared through measured behavior rather than copied by name.

## Reproducibility and regression

Run the existing lightweight asset and acceptance tests after [installation](installation.md):

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Acceptance tests use synthetic logs to detect missing steps, missing finger support, fruit-body support, and excessive relative motion. They test the verifier; they do not replace a new physics run. Use the [demo commands](../demos/apple-stem-grasp/README.md#run) and [independent verification](../demos/apple-stem-grasp/README.md#verify-and-render) for actual dynamics.

Multi-scene physics regression is tracked in [issue #3](https://github.com/huangkiki/Dexlab/issues/3). Experiments must preserve all failures and compare both physical tolerances and runtime under the same hardware and logging conditions. Report model preparation, stepping, and rendering separately; any speed claim must state its workload and accuracy/stability criteria.

Each maintained documentation page has English and Simplified Chinese versions with reciprocal links. The repository homepage is Chinese (`README.md`), with English in `README.en.md`. Update both together; retain original third-party licenses and notices.

[Back to DexLab](../README.en.md)
