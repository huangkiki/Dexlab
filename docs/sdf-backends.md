# SDF–SDF apple-stem grasp

[English](sdf-backends.md) | [简体中文](sdf-backends.zh-CN.md)

The two backends run the same task on the downloaded OpenArm dual-arm robot and Wuji hands. The apple and two grasp pads use SDF collision geometry in both engines. SuperDex loads the upstream precomputed pad SDFs. MuJoCo compiles native octrees from the same pad source surfaces, at maximum depth 9. These are different numerical representations and contact solvers, not identical physics.

## Engine implementation

### MuJoCo: SDF contacts feed a constraint solver

The native octree stores a distance field with trilinear interpolation inside each leaf. In `mjc_SDF`, the engine samples multiple starting points within the overlapping bounding boxes, runs gradient descent on a function of both SDFs, and constructs contact positions, distances, and normals. Here, `sdf_initpoints=40` and `sdf_iterations=100` control that search; they do not set friction or finger strength. See [MuJoCo 3.11.0 SDF collision source](https://github.com/google-deepmind/mujoco/blob/3.11.0/src/engine/engine_collision_sdf.c#L1040).

Those contacts enter the articulated system through contact Jacobians. MuJoCo solves a coupled, soft constraint problem; `solref` sets the reference response and `solimp` sets constraint impedance. The demo uses the Newton constraint solver with an elliptic friction cone. With `condim=4`, each contact includes a normal component, two sliding directions, and torsional friction. This is separate from the `implicitfast` time integrator. See the official [contact and solver formulation](https://mujoco.readthedocs.io/en/latest/computation/#contact) and [solver parameter reference](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters).

### SuperDex: integrate SDF-based surface forces

SuperDex's contact path evaluates surface quadrature samples against the opposing collider. The SDF supplies distance and gradient; the engine computes force per unit area, then multiplies by integration weights and accumulates forces and torques. These samples discretize a contact surface. See [`mochi_contact.cpp`](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.cpp#L2700).

At a sample, the normal-contact calculation uses a smoothed penetration function `p(d)`: the penalty energy is `0.5 * k * p(d)^2`, and its derivative provides the force along the SDF gradient. Threshold and smoothing width control contact onset. Friction uses regularized Coulomb dissipation based on relative tangential motion; `friction_falloff_vel` sets the smoothing scale near zero velocity. It is not an exact zero-slip constraint. See [`ComputeBatchContactPenaltyForceDForce` and friction evaluation](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L497).

The nonlinear equations for each implicit integration stage are solved with Newton iterations; this demo selects GMRES for the inner linear systems. That Newton solve acts on a different problem from MuJoCo's constraint optimization. See [`StepIslandNewtonAsync`](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_physics/src/mochi_solve.cpp#L1090).

**Source and runtime provenance:** the SuperDex code links pin the public UniLab source baseline `f216dace`. The recorded demos use official SuperDex physics/robotics **1.0.0 FP64 wheels**; that source commit is not asserted to be their exact build revision. MuJoCo uses the official **3.11.0 wheel**, with its native library checked against the wheel's RECORD. See the recorded [MuJoCo](../demos/apple-stem-grasp/evidence/sdf-mujoco/engine.json) and [SuperDex](../demos/apple-stem-grasp/evidence/sdf-superdex/engine.json) identities.

### Consequences for grasping a narrow stem

Both engines permit compliant contact. SDF–SDF alone neither guarantees retention nor eliminates slip. The implementation suggests different tuning sensitivities: MuJoCo's contact search and cone constraints affect the available support; SuperDex's surface sampling, penalty response, and friction regularization affect the integrated force. These are mechanisms to investigate, not an isolated causal explanation of the difference between the two recordings. Their friction coefficients, controller gains, timesteps, and grasp alignments also differ.

| Shipped setting | MuJoCo | SuperDex |
|---|---|---|
| Timestep | 0.5 ms | 2 ms |
| Apple SDF | Octree, maximum depth 9 | Grid, 0.2 mm target spacing |
| Thumb/index SDFs | Octrees from native pad surfaces, maximum depth 9 | Upstream precomputed pad SDFs |
| Contact response | `solref=(0.005, 1)`, `solimp=(0.95, 0.99, 0.001)` | Penalty coefficient `1e10` Pa/m; onset threshold 0.1 mm; smoothing half-width 0.15 mm |
| Sliding friction coefficient | 1.0 | 0.5 |
| Other friction settings | `condim=4`, torsional coefficient `0.001`, `impratio=3000` | `friction_falloff_vel=0.00002` m/s; fitted contact-friction Hessian disabled |
| Solver limits | Newton: 100 iterations, tolerance `1e-10` | Nonlinear: 128 iterations; GMRES: 200 iterations |
| Pinch control | Shared target prior, gain multiplier 2 | Shared target prior, pinch stiffness 30 |
| Grasp alignment | Additional 7.25 mm wrist-path height offset | 1.5 mm initial grasp-height offset |

These are tuned simulation settings, not measured fruit or skin properties. The [parameter provenance and assumptions](research-focus.md#parameter-provenance-and-current-assumptions) distinguish asset values, task assumptions, and numerical tuning. Exact application code: [MuJoCo model](../demos/apple-stem-grasp/src/mujoco_model.py), [MuJoCo controller](../demos/apple-stem-grasp/src/mujoco_grasp.py), [SuperDex setup and controller](../demos/apple-stem-grasp/src/wuji_stem_grasp.py).

## Run

Install once with `bash scripts/setup.sh`. No engine source build or API key is required. Then, from the repository root:

```bash
bash demos/apple-stem-grasp/run.sh --backend superdex --stem-only --headless \
  --output demos/apple-stem-grasp/runs/superdex-sdf
bash demos/apple-stem-grasp/run.sh --backend mujoco --stem-only --headless \
  --output demos/apple-stem-grasp/runs/mujoco-sdf
```

Omit `--headless` to open the interactive viewer. Each episode records 14 seconds of simulation; wall-clock execution is longer. Native SDF compilation uses substantial memory and saves a large local `model.mjb`; generated models and raw runs are excluded from Git.

The MuJoCo route uses SuperDex to read the original robot assets and compute the initial kinematic motion prior and settled planning pose, then runs all episode dynamics through MuJoCo `mj_step`. It does not replay the SuperDex object's poses. MuJoCo aligns its wrist path once to its own settled apple position using isolated FK. Both controllers intentionally receive known object poses. No Astra vision policy is involved.

## Verify and render

For either run directory:

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/apple-stem-grasp/runs/mujoco-sdf
```

The offline verifier uses saved forces, poses, and contact points. It checks a complete 11–14 s hold, at least 70 mm of clearance, support matching the apple's weight, continuous support from both SDF pads, no fruit/table/other support, less than 1 mm of penetration, less than 2 mm of wrist-relative displacement and 5 degrees of relative rotation, fixed base, finite records, contact-force reconciliation, and momentum balance. Every simulation step is recorded. Incidental fruit contact during approach is allowed; the stem-only criterion applies during the hold. Missing samples and failed checks result in a nonzero exit code.

The rendered `mujoco-sdf.gif` / `superdex-sdf.gif` and matching MP4 are continuous close-ups of recorded physics poses. The presentation camera follows the apple. Display-only mocap bodies never participate in the separate dynamics scene. Cameras are not policy inputs.

`engine.json` records runtime identity and SDF collider checks; `sdf-dynamics.npz` and `sdf-contacts.npz` contain raw evidence; `summary.json` contains the verdict. MuJoCo also saves the compiled dynamics model and checks its native library fingerprint against the installed wheel RECORD. No local engine patch is accepted.

## Results and limits

Fresh full-command runs on Linux passed all checks with the shipped defaults:

| Measurement | MuJoCo | SuperDex |
|---|---:|---:|
| Physics steps | 28,000 | 7,000 |
| Hold duration | 3 s | 3 s |
| Minimum hold clearance | 124.43 mm | 115.22 mm |
| Maximum hand penetration over episode | 0.159 mm | 0.452 mm |
| Maximum wrist-relative displacement during hold | 0.275 mm | 0.040 mm |
| Maximum wrist-relative rotation during hold | 0.301° | 0.555° |
| Fruit contact force during hold | 0 N | 0 N |

[MuJoCo report](../demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex report](../demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [MuJoCo video](../demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex video](../demos/apple-stem-grasp/media/superdex-sdf.mp4)

Each evidence folder includes engine identity, hashes of the executed Python sources, and video/raw-recording provenance. The large raw arrays and generated models stay local; the commands above recreate them for independent verification. Videos contain all 280 frames of each 14-second episode, without cuts. They use the current OpenArm fixture, with no mobile base. Both successful configurations were repeated from fresh physics states; this is one tuned scene, not a held-out benchmark.

Grasp alignment remains sensitive: nearby MuJoCo wrist-height settings either exceeded the penetration limit or lost the grasp. Successful retention alone is insufficient; the shipped setting passed the full acceptance criteria again after a fresh rebuild.

Robot joint frames, dynamic-link masses and inertia tensors, source surfaces, and collision-filter overrides are transferred from the loaded prefab. Fixed static bodies retain zero dynamically active mass. MuJoCo requires positive inertial placeholders to compile the source's massless links; the loader restores their exact zero inertias and checks the full mass matrix before stepping. This is model conversion using public APIs, not a change to engine source. Other robot colliders use `mesh`; MuJoCo's mesh–SDF path searches triangles, while ordinary convex collision paths use mesh hulls. The two grasp pads and apple are native SDFs. The wrist mounting recess receives a local self-collision exclusion inherited from the earlier adapter; no fingertip–apple contact is disabled.

The stem and fruit are one rigid body. Bending, fracture, damage, real hardware, and MuJoCo Warp are not validated. Same-scene repeatability does not establish a randomized success rate. Object motion relative to the wrist is not cumulative slip at a tracked material point, and successful retention is not zero slip.
