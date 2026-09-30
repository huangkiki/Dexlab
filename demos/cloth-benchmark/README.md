# Cloth contact experiments

[简体中文](README.zh-CN.md) | [English](README.md)

Measure native MuJoCo flex, SuperDex experimental shells, Newton cloth and PhysX surface-deformable motion using shared surface meshes, areal density, loads, and boundary conditions. MuJoCo/Newton use explicit area-lumped vertex masses; SuperDex retains its native shell FEM inertia, with total mass checked. These are **nominal-material numerical experiments**. Constitutive responses are not yet calibrated across solvers; the results cannot rank real-material accuracy.

## Experiments and inputs

| Experiment | Boundary conditions | Independent measurements |
|---|---|---|
| Extension and unloading | Fixed left edge, 5 mN total right-edge traction: ramp 0–0.5 s, hold 0.5–1.5 s, unload 1.5–2 s, relax 2–3 s | Tip extension, edge strain, residual speed |
| Gravity sag | Horizontal strip released from rest with its left edge fixed | Tip/center sag, strain, pin error |
| Sphere drape | Free sheet falling onto a fixed 60 mm-radius sphere and horizontal ground | Sphere/ground penetration, residual motion, strain |
| Folded drop | Stress-free pre-folded sheet dropped onto a plane | Ground penetration and sampled surface crossings |

The default strip is 200 × 100 mm with 9 × 5 vertices; drape uses a 200 × 200 mm square. Areal density is 0.2 kg/m², collision radius 1 mm, duration 3 s, and timestep 0.5 ms. Records contain rest vertices, triangles, nominal masses, actual positions/velocities, and every applied force. Nominal pinned mass and dynamically free mass are reported separately.

The frozen [`benchmarks/cloth-v1.json`](../../benchmarks/cloth-v1.json) has 3 development and 12 held-out cases. Held-out cases must not inform tuning. Temporal refinement uses 0.5/0.25/0.125 ms; spatial refinement uses 9 × 5 → 17 × 9. Trapezoidal boundary quadrature preserves total traction under mesh refinement.

## Run

Complete `bash scripts/setup.sh` first. MuJoCo uses the existing 3.11.0 wheel:

```bash
.venv/bin/python -m dexlab.cloth_benchmark run \
  --solver mujoco --case dev-extension \
  --output demos/cloth-benchmark/runs/mujoco-extension
```

Newton is an optional build from a pinned upstream commit. Its MuJoCo extras, which would replace the pinned MuJoCo version, are not installed:

```bash
uv pip install --python .venv/bin/python \
  -r demos/cloth-benchmark/requirements-newton.txt
.venv/bin/python -m dexlab.cloth_benchmark run \
  --solver newton-xpbd --case dev-sag \
  --output demos/cloth-benchmark/runs/newton-xpbd-sag
```

Other options are `superdex-shell`, `newton-vbd`, `newton-semi_implicit`, `newton-featherstone`, and `newton-style3d`. SuperDex uses the already installed official 1.0.0 FP64 wheel and its experimental triangle-shell API; it is not a tetrahedral soft-body substitute. Availability of an option does not establish qualification on all experiments. `--device cpu` is the default; Newton also accepts explicit `cuda:0`. Use `--dt` and `--refine 2` for temporal and spatial refinement. Each configuration requires a fresh output directory.

Runs advance through the registered UniLab task **`DexLab-Cloth-v0`**: one `env.step` advances one native physics step. Observations contain actual vertex positions and time, plus native velocities for MuJoCo/Newton or backward-difference node velocities for SuperDex (explicitly recorded in metadata); actions are per-vertex forces in N. The benchmark uses prescribed loads, not a learned policy. DexLab owns the native scenes; this is not UniSim built-in cloth backend support.

Rescore offline:

```bash
.venv/bin/python -m dexlab.cloth_benchmark verify \
  demos/cloth-benchmark/runs/mujoco-extension
```

Render the complete recorded episode as a close-up MP4 and GIF, without advancing physics:

```bash
.venv/bin/python demos/cloth-benchmark/src/render.py \
  demos/cloth-benchmark/runs/mujoco-extension
```

![SuperDex native shell sag](media/superdex-shell-sag.gif)

Continuous 3-second playback of the recorded SuperDex shell development case. [MP4](media/superdex-shell-sag.mp4) · [Media provenance](media/superdex-shell-sag.json). This shows numerical sag, not a calibrated fabric.

## Development results

All four 3-second experiments were run on each of the seven configurations below. **13/28 passed the stated protocol checks**, including the new surface audit. These counts are not material-accuracy scores. A configuration failure does not establish an engine-wide inability.

| Native configuration | Extension | Sag | Drape | Folded drop |
|---|---|---|---|---|
| MuJoCo 3.11.0 flex | Pass | Surface crossing | Penetration | Penetration / crossing |
| SuperDex 1.0.0 FP64 shell | Pass | Pass | Penetration / crossing | Penetration / crossing |
| Newton XPBD | Pass | Pass | Penetration | Surface crossing |
| Newton VBD | Pass | Pass | Penetration | Penetration / crossing |
| Newton Style3D | Pass | Pass | Penetration | Surface crossing |
| Newton SemiImplicit | Pass | Pass | Penetration / crossing | Penetration / crossing / velocity clipping |
| Newton Featherstone | Pass | Pass | Penetration / crossing | Penetration / crossing / velocity clipping |

The 20 drape refinement runs (MuJoCo and four Newton solvers, before Featherstone/SuperDex were added) all exceeded the unchanged 1.5 mm obstacle limit. They do not establish convergence. Complete reports: [development](evidence/development.json), [refinement](evidence/refinement.json). They retain parameters, source identities, measurements, and original trajectory hashes; large raw trajectories are regenerated locally, not embedded in these reports.

The first case manifest predates the independent surface audit; its original limitation text is preserved as part of the frozen input. The current verifier adds that audit. [`cloth-self-contact-v1.json`](../../benchmarks/cloth-self-contact-v1.json) supplies one development and three held-out folded-drop cases. This is a stress-free folded rest shape, not a robot folding an initially flat fabric.

Run the frozen nominal profiles across all 15 held-out cases and seven solvers (105 episodes):

```bash
.venv/bin/python -m dexlab.cloth_benchmark batch \
  --suite benchmarks/cloth-v1.json benchmarks/cloth-self-contact-v1.json \
  --split test --output demos/cloth-benchmark/runs/heldout
```

The batch freezes source and case hashes before execution, saves each command/log, and retains failures and timeouts in the denominator. It requires a fresh directory.

## Held-out results

The first frozen batch completed **all 105 held-out episodes: 52 passed the protocol checks and 53 failed, with no runtime errors or timeouts**. Entries below are passes / cases; each episode simulated 3 seconds. Experiments have different parameter distributions and checks, so aggregate counts are not a material-accuracy ranking.

| Native profile | Extension | Sag | Sphere drape | Folded drop |
|---|---:|---:|---:|---:|
| MuJoCo flex | 4/4 | 0/4 | 0/4 | 0/3 |
| SuperDex shell | 4/4 | 3/4 | 0/4 | 0/3 |
| Newton XPBD | 4/4 | 4/4 | 0/4 | 0/3 |
| Newton VBD | 4/4 | 4/4 | 0/4 | 0/3 |
| Newton Style3D | 4/4 | 4/4 | 0/4 | 1/3 |
| Newton SemiImplicit | 4/4 | 4/4 | 0/4 | 0/3 |
| Newton Featherstone | 4/4 | 4/4 | 0/4 | 0/3 |

Every sphere-drape profile exceeded the original penetration limit. All MuJoCo sag cases and one SuperDex sag case had sampled surface crossings. Some SemiImplicit and Featherstone drape / folded-drop cases triggered the native velocity-clipping check. Thresholds and failed records were preserved; passing these checks does not establish agreement with real material extension or sag.

[All 105 records](evidence/heldout-v1.json) retain case parameters, native-library provenance, measurements, failed checks, and trajectory hashes. The command below checks trajectory, source-snapshot, and scored-summary hashes before collecting a report. It neither reruns physics nor changes raw records; use the earlier `verify` command to recompute physical metrics.

```bash
.venv/bin/python -m dexlab.cloth_report demos/cloth-benchmark/runs/heldout \
  --output demos/cloth-benchmark/runs/heldout-report.json
```

## Backend capability audit

| Profile | Native representation | Current evidence |
|---|---|---|
| MuJoCo flex | Triangle membrane and bending elasticity; flex contact | Executed development, refinement, and held-out cases |
| SuperDex shell | Experimental triangle-shell FEM; sampled surface contact and point-cloud self-contact | Official FP64 wheel exercised; volume FEM is a separate API |
| Newton XPBD | Particle spring/bending constraints | Executed; pinned solver does not provide cloth self-collision |
| Newton VBD / Style3D | Native triangle cloth with self-contact enabled | Executed; configured self-contact still fails some stress cases |
| Newton SemiImplicit / Featherstone | Semi-implicit particle forces; no cloth self-collision in the pinned feature matrix | Executed; contact instability is retained |
| Newton SolverMuJoCo / Kamino / ImplicitMPM | Not triangle-cloth profiles in the pinned feature matrix | Not silently substituted for these cloth cases |
| PhysX through Isaac Sim 5.1 | Native beta triangle surface, explicit world-edge attachments, actual node tensors | [Passive cloth qualification](../physx-contact/cloth.md); prescribed per-node-force extension unsupported |

Newton's capability boundary follows its [pinned official feature matrix](https://github.com/newton-physics/newton/blob/2dee323416ab34763d8680fa5108a28ea688efff/docs/solvers/index.rst). SuperDex's [shell parameters](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/mochi_physics_experimental.h) document area density and 2D membrane units; that reference commit is not asserted to be the exact wheel build revision.

Isaac Sim's [5.0 release notes](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/overview/release_notes.html) introduced a beta volume/surface-deformable schema, while its [5.1 API](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.core.prims/docs/index.html) still lists particle-cloth classes. The runtime audit now exercises the native beta surface path, node observations, explicit world attachments and collisions. It does not use the deprecated particle-cloth API. Per-node force upload and native nodal-mass readback are unavailable in the pinned tensor interface; those limitations are explicit.

## Parameters, evidence, and limits

- SuperDex shell material coefficients come from the official 3D-isotropic-to-shell conversion at 20 kPa, Poisson ratio 0 and 0.5 mm thickness. Contact uses surface quadrature and a point-cloud self-collider with 2 mm interaction radius; this is a sampling approximation, not triangle CCD. Native nonlinear convergence counts are reported. The public API has no node-velocity getter, so its velocity channel is derived from consecutive node positions.
- MuJoCo uses 2D flex membrane/bending elasticity with nominal Young's modulus 20 kPa, Poisson ratio 0, and shell thickness 0.5 mm. Shell thickness differs from collision radius. Newton spring, membrane, and anisotropic materials use solver-specific native coefficients recorded in `run.json`. None are measured fabric properties.
- MuJoCo's `Newton` constraint solver is distinct from the Newton physics engine. Newton XPBD uses spring/bending constraints; VBD, SemiImplicit, and Style3D use different constitutive and integration paths. Featherstone uses the shared semi-implicit particle kernels for cloth; its articulated-body solver does not make cloth implicit. Constitutive equivalence is not claimed.
- Package code/native libraries are checked against installed SHA256 RECORD entries. Versions, installation origin, source hashes, and trajectory hashes are retained. The reference source commit is separate from actual installation origin; local builds are not described as official PyPI wheels.
- Checks require a complete time grid, finite states, prescribed loads, pin error <1 μm, and sphere/ground penetration <1.5 mm. Geometry checks include triangle interiors independently of engine contact IDs. An independent triangle audit checks sampled zero-thickness surface crossings and degeneracy at a target 100 Hz, excluding pairs sharing a vertex. The report gives actual coverage. Neither check guarantees absence of inter-step crossing or finite-thickness self-overlap.
- `protocol_checks_passed` certifies only these checks. It does not certify material calibration, steady-state relaxation, or real-fabric accuracy. Strain, extension, and residual speed remain visible.
- Timing includes force upload, collision/solver completion, and observation readback. Preparation and first-step JIT are separate. Development timings collected alongside other running experiments must not rank engine speed.
- Raw trajectories include the initial and every end-of-step state. Errors preserve partial records and return a nonzero exit code. Incomplete cases cannot pass.

Robot cloth pinching/folding is a [separate experiment](../cloth-folding/README.md). Cloth and apple grasping have different models and scores; they are not combined into one ranking. Complete solver qualification, self-collision stress tests, refinement, and held-out results remain tracked in [Issue #12](https://github.com/huangkiki/Dexlab/issues/12). Hardware material calibration requires measurements.

PhysX surface cloth uses the same scene protocol, with a separate 15-case held-out batch: 10 passes, one crossing failure and four unsupported cases. These are separate from the historical 105 runs above. [Results and raw evidence](../physx-contact/cloth.md).
