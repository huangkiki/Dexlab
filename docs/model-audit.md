# Model audit

[English](model-audit.md) | [简体中文](model-audit.zh-CN.md)

The apple-stem demo writes a read-only parameter and initial-overlap audit during scene preparation. It reports inherited properties and backend overrides without repairing them. The audit does not change the existing grasp acceptance thresholds or feed information into the controller.

## Run and inspect

After [installation](installation.md), run either complete episode:

```bash
bash demos/apple-stem-grasp/run.sh --backend superdex --headless
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless
```

Each run writes `model-audit.superdex.json` in its output directory. The MuJoCo path also writes `model-audit.mujoco.json`, because it first loads and plans with the native SuperDex scene. The snapshot is after apple settling and robot pre-grasp placement, before the 14-second grasp trajectory.

Recheck an existing report without constructing or advancing either simulation:

```bash
.venv/bin/python -m dexlab.model_audit \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf/model-audit.mujoco.json
```

The command prints findings and exits 1 for parameter errors; geometry warnings remain visible but do not automatically reject the model. There is no implicit repair or replacement of the independent dynamics verifier. An old run without the JSON reports must be rerun to obtain these snapshots.

## Report contents

| Field | Meaning |
|---|---|
| `units` | Declared SI interpretation: meters, kilograms, seconds, radians, inertia in kg m², rotational gains in N m/rad and N m s/rad. This is a model assumption, not a measurement. |
| `sources`, `source_record` | Hashes of downloaded robot prefab files; the native report also retains the robot's upstream source record. Episode `source-sha256.json` identifies the code. |
| `bodies[].source/effective` | Mass, local COM and inertia matrix. In SuperDex, source means the loaded original prefab; missing fields remain null. In MuJoCo, source means the native runtime, and `prefab_source` retains the original asset properties. |
| `bodies[].massless_reason` | Fixed coordinate frames with no geometry, mass or source inertia are explicitly classified. A zero-mass dynamic link without this classification is an error. |
| `joints` | Native loaded joint frames, axes, limits, friction, limit response and effort limits; MuJoCo compiled hinge axes, limits, damping, friction loss and armature. |
| `drives` | Native pose-controller gains and saturation read back from the actor; MuJoCo compiled gain/bias arrays and enabled force/control limits. The task's effective MuJoCo damping includes `dt * kp`. |
| `collision_filters` | Native directional layer permissions, explicit prefab overrides and inferred adjacency exclusions; MuJoCo geom types, masks, contact parameters, parent filtering and body exclusions. |
| `initial_overlaps` | Query method, snapshot phase, observed negative distances and coverage limitations. |
| `findings`, `errors`, `warnings` | Numerical defects, missing data, intentional massless frames and geometric overlap warnings. Non-finite evidence is retained as text in valid JSON and reported as an error. |

The checks cover finite parameters, positive dynamic mass, inertia shape/symmetry, eigenvalue signs and triangle inequality, hinge-axis normalization, ordered limits and nonnegative finite drive gains. They do not certify hardware realism.

## Static bodies and conversion assumptions

SuperDex rejects the mass getter on static actors. Their effective mass is represented as **zero dynamic mass**, with original asset mass stored separately; this is not a statement that the mounting structure physically weighs zero. Standalone static geometry does not expose rigid COM/inertia; those fields remain null. Geometry-free `NONE` colliders have no contact parameters and are recorded as null.

The existing MuJoCo adapter temporarily inserts positive inertial values for zero-mass bodies during compilation, then restores zero mass/inertia and checks its assembled mass matrix. The audit records the resulting effective values and their native source. In particular, fixed-body inertias can be zeroed by this existing conversion; the audit does not restore or conceal them. Apple mass is the task's 0.2 kg assumption; its COM/inertia are native mesh-derived estimates. Controller gains and contact coefficients are task settings, not identified motor or material parameters.

## What initial-overlap warnings mean

SuperDex checks AABB-overlapping surface pairs using deterministic, bidirectional probes of up to 256 vertices per surface and native signed surface-distance queries. No simulation step or model setter is called. Adjacent or excluded pairs are retained as geometry evidence. Directional layer filters are queried, while actor exclusions are inferred using the existing prefab/transfer rules because the native API has no public actor-filter readback. The inherited transfer helper is not a proof of the full engine contact-selection logic.

Finite vertex probes can miss small or edge-only intersections. Native SDF distances outside the actor AABB are only upper bounds; this method uses negative samples as overlap evidence and does not certify that a scene is collision-free.

MuJoCo runs `mj_forward` on a fresh `MjData` containing the same initial joint positions and reports negative distances in generated contacts. Live model parameters and simulation state remain unchanged. Effective collision filters apply, so excluded pairs do not appear. This is an engine contact query, not exhaustive mesh-intersection testing. Its non-SDF mesh convex hulls also differ from native SuperDex SDF geometry; warning counts cannot rank engine accuracy.

Small support/contact overlaps and filtered assembly intersections need interpretation against model scale and contact compliance. The audit reports distances without introducing a new success tolerance. Use the [independent grasp verifier](../demos/apple-stem-grasp/src/verify_sdf_grasp.py) for task acceptance.

## Validation

In the default scene's preparation snapshot, each report covers 94 bodies and 54 driven hinge joints, with no numeric parameter errors. Thirteen geometry-free fixed coordinate frames are identified, including ten fingertip frames. Native probes report 82 overlapping pairs: 77 fall in inferred exclusions; four involve pinky middle/nail/pad geometry (actor-filter status is not observable), and one is apple/table support. MuJoCo generates one overlapping pair, apple/table, initially about 1.39 mm. These are pre-grasp diagnostics, not hold-phase penetration measurements or a ranking of the engines.

`tests/test_model_audit.py` exercises negative/zero mass, intentional massless frames, asymmetric/indefinite/impossible inertia, non-finite fields, invalid axes/limits/gains, strict JSON output, and an actual MuJoCo overlapping sphere with collision-mask changes. The MuJoCo test also checks that the audit leaves live state and model parameters unchanged. A native SuperDex box test covers signed-distance probes, AABB rejection, static-property availability, and unchanged body pose/velocity. Full backend episodes remain required for the integration hooks.

During development, API probes exposed native restrictions: static actors reject `get_mass`, standalone static geometry lacks rigid COM/inertia, and `NONE` colliders reject `get_contact_params`. The exporter now represents these cases explicitly instead of inventing physical values or calling unsupported getters.

Implementation: [model_audit.py](../src/dexlab/model_audit.py). Parameter semantics: [MuJoCo inertials](https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-inertial), [contact selection](https://mujoco.readthedocs.io/en/stable/computation/index.html#selection), and the installed official SuperDex FP64 API docstrings for `Actor.get_points_distance_to_surface` and `Scene.is_layer_contact_enabled`.

[Research focus](research-focus.md) · [Apple-stem demo](../demos/apple-stem-grasp/README.md)
