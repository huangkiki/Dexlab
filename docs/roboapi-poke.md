# Poke RoboAPI adapter and sim2real mapping

The DexLab Poke RoboAPI adapter separates policy calls from task-specific simulation code. A task provides deployable observations and maps returned actions back to its controller; the adapter handles model discovery, sessions, action protocol, and receipts. It never stores the API key or replaces physical-robot safety logic.

## Implemented

- `RoboApiClient`: `GET /models`, `GET /models/{id}/schema`, `POST /sessions`, `POST /chat/completions`, and `POST /sessions/{id}/close`.
- `PokeSession`: tracks `session_id`, `next_turn`, the previous assistant message, and tool feedback so later turns retain execution history.
- Input validation: eight-value state, normalized xyzw quaternion, gripper in `[0,1]`, PNG/JPEG image.
- Output validation: nonempty action chunk, eight numbers per row, finite values, normalized quaternion, gripper tolerance.
- `inspect.py`: `models`, `schema`, and `infer` commands.

The key is read only from `POKE_ROBOAPI_KEY`; it is never written to logs, configuration, or the repository.

## Observation and action contract

| Field | Real/sim convention |
| --- | --- |
| `instruction` | Natural-language instruction matching the camera view; bounded by model schema `max_chars` |
| `state` | `[x, y, z, qx, qy, qz, qw, gripper]` in model task coordinates; xyzw quaternion; gripper `0` closed, `1` open |
| `image` | Wrist RGB PNG/JPEG; keep original aspect ratio and fisheye distortion; no crop, mirror, rotate, or undistort |
| `output` | `(T, 8)` absolute targets dispatched at 30 Hz |
| Control point | Flange mounting-plane center, not the gripper tip, grasp center, or camera center |

## Real versus simulated embodiment

| Dimension | Real body | Simulated body | Must match |
| --- | --- | --- | --- |
| Arm/gripper | e.g. UR5e + Robotiq 2F-85 | Matching URDF/USD, joint limits, flange definition | Joint identity, control frequency, gripper axis, flange center |
| Camera | e.g. Insta360 Ace Pro 2 + ultra-wide lens | Same pose, orientation, FOV, and distortion | Gripper position/scale in view, fisheye, brightness |
| State frame | Home + A/B/C three-point calibration | Same task frame and axes | Position, xyzw order, control point, workspace |
| Action interface | 30 Hz absolute targets with per-step receipts | Same rate and absolute-target semantics | Executed steps, boundary clipping, real state readback |
| Physical object | Measured mass, inertia, material, friction | Frozen model and contact parameters | Units, provenance, and explicit approximations |
| Rendering | Optional OVRTX high-quality RGB | Same scene, materials, lighting, camera | Rendering must not alter physics or scoring |

## Sensor configuration

The adapter passes one RGB image and one eight-value state, so simulation must produce a wrist view with the same semantics as deployment:

- fixed camera extrinsic relation to the flange control point;
- preserved fisheye intrinsics/distortion, not a wider ordinary perspective camera;
- equal-aspect resize per schema, default 1280×720 to 640×360;
- image and state sampled at the same time;
- clear gripper, object, and table edges without large over/under-exposure.

## OVRTX rendering

OVRTX provides high-quality RGB/synthetic-data replay; it does not integrate physics. Physics stepping remains native MuJoCo, SuperDex, Newton, or TLMPM. An OVRTX render must:

1. preserve original physics states and camera timestamps;
2. restore the same scene, materials, and lighting;
3. render saved states without interpolating vertices or advancing physics;
4. record frame-to-state indices, input/output hashes, and rendering cost;
5. remain visual evidence rather than a new sensor-fidelity or throughput claim.

## Representative task solvers, parameters, and thresholds

This table records implementation identity from existing evidence. Tasks not yet connected to RoboAPI still need per-task observation/action mapping; the table is not a model scorecard.

| Task | Solver and version | Key parameters/implementation | Frozen acceptance | Rendering and RoboAPI status |
| --- | --- | --- | --- | --- |
| Wuji sphere pinch | MuJoCo 3.17.0 CPU, SDF, implicit sampled PD | 20 g sphere, v4 synthetic torsional contact, protocol timestep/control period | two-second hold ≤ 2 mm, active release, negative controls | MuJoCo recorded replay; execution mapping pending |
| Apple-stem grasp | MuJoCo 3.11.0 / SuperDex 1.0.0 FP64, SDF–SDF | OpenArm arms + Wuji, known pose, IK, scripted joint targets | 14 s grasp, clearance, two-pad support, penetration, momentum | MuJoCo recorded / OVRTX replay; mapping pending |
| Sponge wiping | RSS `23417de`; Newton 1.6 / MuJoCo/MJWarp 3.12 / SuperDex 1.0 FP32 | compliant latch, 60 Hz, 16 rigid substeps, 2 SuperDex steps | cleaning ≥ 90%, peak force/pressure, return error, unassisted failures retained | tiled + OVRTX replay; mapping pending |
| Cutting/pushing | CPU TLMPM, BladeMaster reference | synthetic material, viscosity, half-step, no-push control | per-report separation/connectivity/contact-force thresholds | OVRTX surface replay; mapping pending |
| Cloth | MuJoCo / SuperDex / Newton / Genesis, task dependent | sag, stretch, coverage, folded drop, robot grasp | independent protocols with penetration and failures retained | selected OVRTX replay; mapping pending |
| Contact benchmark | MuJoCo / SuperDex and others | incline, normal, impulse, damping, mass/size transfer | analytical/engineering references with fixed denominators | static figures; mapping pending |

Every number is valid only for its reported version, scene, and acceptance condition. Changing the model, simulator, controller, or task protocol requires a new cohort.

## Boundaries

- The adapter verifies HTTP and session state, not physical-robot safety.
- `completed` means an action chunk was dispatched and its execution periods ended; it does not mean the object was grasped or the task succeeded.
- A simulation pass does not prove hardware success, and an OVRTX replay does not prove sensor fidelity.
- Official leaderboard entries require DexLab execution and anti-gaming review.
