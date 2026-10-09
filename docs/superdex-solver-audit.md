# SuperDex incline solver audit: identity, reconstruction and limits

[简体中文](superdex-solver-audit.zh-CN.md) · [Historical result](incline-comparison-results.md) · [P0 #124][issue]

The nine historical incline cases used the same code bytes as the official SuperDex 1.0.0 FP64 and API wheels. Reconstructing the archived solver setters on those bytes reads **Newton, linear AUTO, residual-norm line search and C1-regularized Coulomb friction**. The identified source routes AUTO to **dense LDLᵀ for this small rigid system**. This is a configuration reconstruction and source trace; the original records do not contain per-step linear-solver branch telemetry. **#124 remains open for that historical executed-path evidence boundary.**

This supplement changes no trajectory, score, threshold or historical manifest. It does not attribute the 8/9 result to one algorithm, establish material equivalence, or extend the finding to other SuperDex experiments.

## Identity chain

On 2026-10-09, all nine local admission, metadata, trace and geometry files matched their bytes inside the [published archive][raw]; CRC and the recorded per-case hashes passed. The archived runner and fixture matched their campaign hashes. Each historical admission recorded package version, verified RECORD and the code aggregate below. Recomputing the same aggregate from the unchanged installation and the official wheel contents matched all nine admissions, for both distributions. The aggregate covers every package `.py` and `.so` entry, with each SHA256 checked against RECORD; it is not the wheel-file hash.

| Artifact | SHA256 / identity |
|---|---|
| Published paired archive | `9c0e86425ec03c6d045d5db5a2282310216fa892c7677deb317e9ce306504079` |
| FP64 official wheel, CPython 3.12 Linux x86_64 | `ce300f8a2b30f8043aad238f4c918f981d143256276e34935fa31382a22c02c4` |
| API official wheel, same platform | `46fa446ed0bb86815d6970d14e11f2777bcc7391119c4ebe582ac698e1373377` |
| FP64 aggregate of 7 package code files | `d6e4ac1e9e479a8f7187d19f58e4d3b9566bd2b2754471f3bb6026846d1a0cba` |
| API aggregate of 74 package code files | `3340cfec18d17cd41abb52d10a679d7bd5e09a8bfc7dbe6302d609bedbf5f7e0` |
| `libmochi_physics_double.so` | `a2a0d6e9711d16f1b07641a1192f12df24f6f7f011e864653f1f0fe9176b931d` |
| FP64 ELF Build ID (not a source SHA) | `e7d3ec045b9f43db5c56565509861dc9d2ba32c8` |
| Archived fixture `contact_plane_native.py` | `7e9745ceb0eddb29f88e4259adc8dfed3a7ae1968478498f5a3648d671c2fe07` |
| Archived runner `incline_compare_run.py` | `146d55ef1b2be2ebcc9b70920759bbb365cf3206d59c1cc544dcebdfebc67504` |
| Frozen manifest | `8a3d2f319ab8b3e355d6ed5d562cfa6fc2d22a642172538ad1e65483ef5a7591` |

The [API][api-provenance] and [FP64][fp64-provenance] PyPI provenance documents name these exact wheel SHA256 values and the official GitHub publisher. Their certificate metadata points to [API publication][publish-api] and [FP64 publication][publish-fp64], both at publication-workflow commit `d3101bd914b1a1654b1878fd1732d24d16d6f568`. Both publication logs select [wheel build 32549763602][build], whose successful run identifies source commit **`1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`**. The publication workflow checks the build result and release tag before uploading its wheelhouse. Publication-workflow SHA and compiled-source SHA are different identities. This audit read PyPI provenance and GitHub records; it did not independently verify the Sigstore certificate chain or perform a reproducible native rebuild.

Every source link below is pinned to that build commit. Downloaded source files were checked against Git blob IDs from its tree. This chain is stronger than assuming that a current default or a matching version string identifies a past run.

## Field-by-field evidence

H = directly saved in the historical archive. R = new readback using the same verified code bytes and the archived setters. S = source-derived, with the historical fixture/topology as input. R and S do not become historical measurements.

| Field | Value and evidence | Scope / limitation |
|---|---|---|
| Integrator / nonlinear budget | H: Backward Euler; 100 iterations; absolute and relative tolerance `1e-9` | Integration and termination settings do not name the algorithm |
| Nonlinear algorithm | R: `NEWTON`; [stage dispatch][step] → [NewtonSolver construction and Solve][solve] → [Newton versus BFGS/SR1 branch][newton] | Newton solution of the nonlinear residual system; not an assertion of exact energy minimization |
| Linear solver | R: `AUTO`; [island selection][dispatch] uses LDLᵀ at ≤50 DoFs, CG above; [factorization][linear] is dense below its 200-DoF sparse threshold | The archived single dynamic rigid cube and static plane give the small-system path. No per-step chosen branch or factorization telemetry was saved |
| Linear preconditioner | R: scene `PER_ACTOR`; S: AUTO→LDLᵀ overrides it to `None` | Do not describe the inferred direct solve as preconditioned CG |
| Nonlinear details | R: residual-norm line search, alpha 0.5, max 4; PSD projection `ALWAYS`; derivative assembly period 1; gradient-descent fallback false | PSD projection and fitted contact Hessians matter; “Newton” alone is incomplete |
| Linear tolerances | R: absolute `1e-9`, relative `1e-5`, max_iter `-1` (automatic), Eisenstat–Walker 2 | Source resolves the automatic iteration budget; these do not imply equal work to MuJoCo's settings |
| Convergence | H: 21,000 `CONVERGED` statuses; R: `PER_ACTOR_WEIGHTED` criterion | Convergence status does not identify the selected linear branch or prove contact accuracy |
| Pair coefficient | H: both actors μ=0.5, or both zero; S and same-binary API documentation: geometric mean `sqrt(μa μb)` | Gives 0.5 / 0 at combination, not a measured contact-point coefficient or material calibration |
| Other pair parameters | H: penalty `1e9 Pa/m`, smoothing half-distance `5e-5 m`, threshold `1e-4 m`, falloff `1e-3 m/s`, zero viscous/normal damping; [combination][combine] | Static collider uses the colliding body's penalty and falloff; threshold/smoothing come from the collider. Both actors match here |
| Friction regularization | R: `C1_REGULARIZED`; [contact evaluation][contact] and [activation][smooth] | Continuous low-speed regularization, not set-valued exact stiction |
| Normal/alignment treatment | R: `explicit_normals=false`, `fade_friction=true`, `implicit_normal_force_for_dissipation=false`; default actor `max_alignment_normals=0`, collider normal for friction | [Alignment fading and force evaluation][alignment] make the pair coefficient alone insufficient to specify friction |

Native enum variants are Newton/BFGS/SR1; C1/C∞ regularized friction; and linear CG, GMRES, CUDA CG/GMRES, augmented/async/parallel CG, MINRES, LDLᵀ, LU, experimental CUDA sparse Cholesky/LDLᵀ/LU, and AUTO. An exposed enum is not evidence that the cohort executed or qualified that variant. These are algorithms inside SuperDex; “Newton” here does not mean the Newton Physics engine.

## Contact law and numerical meaning

The [pair routine][combine] takes the geometric mean of Coulomb, viscous and normal damping coefficients. For a static collider, penalty and falloff come from the colliding actor; for two dynamic actors they use geometric means. Other fields initially come from the collider, with dimensional penalty corrections for non-surface integration. For this rigid surface pair those corrections do not introduce a rod or point-contact scale.

The [normal penalty][contact] evaluates a smoothed penetration proxy `P(x)` at `x=-d` and traction proportional to `k P(x) P′(x)`, before quadrature and mapping to rigid-body force. Its transition occupies signed distances from `1e-4 m` down to `0 m` for the recorded threshold and half-distance. A `1e9 Pa/m` penalty is a traction-law coefficient, not a lumped N/m spring constant. Contact can therefore be active at positive separation.

For [C1 friction][smooth], let `x` be tangential relative displacement and `t = falloff_velocity × stage_duration`. The force activation is `2r − r²` for `r=x/t<1` and 1 for `r≥1`. It tends to zero at zero relative displacement. The tangential force opposes slip and is scaled by μ, the normal-force estimate and the [normal-alignment factor][alignment]. The reconstructed defaults also use fitted contact-friction saturation Hessians. This explains why a nominal Coulomb coefficient does not specify exact static sticking, but does not by itself quantitatively explain every historical drift value.

## Readback and remaining work

The [preregistered diagnostic][prereg] made **zero native step calls**, one empty scene and no physics replay. The enforced envelope was 16/15 GiB, two-core quota, 128 tasks, zero swap, bounded data I/O and a 300 s deadline. It completed successfully: whole launcher 1.007 s, guarded audit command 0.546 s, kernel memory peak 109,711,360 bytes, no OOM. These are audit costs, not engine throughput. The diagnostic script SHA256 is `015c0b889917b61f77a8e59725de178e7751508752456695de78208cfb4e311b`; its complete local output SHA256 is `22c684f975ddb8ff186b8d1f410d750224db94db6a1d54eb01b007b472aee33b`. Publicly reviewable readbacks are transcribed below; original admissions remain in the immutable release archive.

```python
# In an installation first verified against both official wheel hashes above.
# Run only inside the documented bounded qualification window.
import os
os.environ["SUPERDEX_PRECISION"] = "fp64"
from superdex import physics as p
p.initialize(num_worker_threads=0)
scene = p.create_scene("solver-identity-readback")
try:
    params = scene.get_solver_params()
    params.integration_method = p.IntegrationMethod.BACKWARD_EULER
    params.non_linear_solver.max_iter = 100
    params.non_linear_solver.abs_tol = 1e-9
    params.non_linear_solver.rel_tol = 1e-9
    scene.set_solver_params(params)
    params = scene.get_solver_params()
    print(params.non_linear_solver.solver_type.name)
    print(params.linear_solver.solver_type.name)
    print(params.experimental_eval.friction_model.name)
finally:
    p.destroy_scene(scene)
```

The residual gap in [#124][issue] is **historical execution telemetry**, not an unnamed candidate algorithm: the archive lacks the full solver-parameter object, island DoF/selected-linear-solver trace, and per-contact combined-law readback. The exposed [SolverStats][stats] contains iteration counts, residual and convergence status, not the chosen linear solver. A new replay can validate a new execution and compare trajectories, but cannot create missing historical telemetry. Recovery requires discovering a contemporaneous native trace/configuration artifact tied to this cohort, or an explicitly reviewed decision to accept source-based reconstruction as the attribution boundary. Until then the Issue stays open; no blanket dependency is added to newly qualified experiments. New protocols should capture complete available solver parameters and observability limits before positive-duration runs.

<details>
<summary>Complete zero-duration solver readback (R)</summary>

```json
{
  "experimental_eval": {
    "consistency_res_norm": false,
    "consistency_res_norm_step": 0.0001,
    "explicit_normals": false,
    "fade_friction": true,
    "fitted_saturation_hessian": {
      "constraint_saturation": true,
      "contact_friction": true,
      "joint_friction": false
    },
    "friction_model": {
      "name": "C1_REGULARIZED",
      "value": 0
    },
    "implicit_normal_force_for_dissipation": false
  },
  "integration_method": {
    "name": "BACKWARD_EULER",
    "value": 0
  },
  "linear_solver": {
    "abort_if_not_spd": false,
    "abs_tol": 1e-09,
    "max_iter": -1,
    "norm_type": {
      "name": "PRECONDITIONED_RESIDUAL_L2",
      "value": 1
    },
    "preconditioner_type": {
      "name": "PER_ACTOR",
      "value": 11
    },
    "rel_div_tol": 10000000000.0,
    "rel_tol": 1e-05,
    "restart_size": 1000,
    "solver_type": {
      "name": "AUTO",
      "value": 13
    },
    "verbosity": {
      "name": "WARNING",
      "value": 2
    }
  },
  "non_linear_solver": {
    "abs_div_tol": 1000000000.0,
    "abs_tol": 1e-09,
    "convergence_mode": {
      "name": "PER_ACTOR_WEIGHTED",
      "value": 1
    },
    "d_residual_assembly_period": 1,
    "explosion_control": true,
    "gradient_descent_fallback": false,
    "line_search_alpha": 0.5,
    "line_search_max_iter": 4,
    "line_search_max_rel_increase": 0.0,
    "line_search_type": {
      "name": "RESIDUAL_NORM",
      "value": 5
    },
    "line_search_wolfe1": 0.0001,
    "line_search_wolfe2": 0.9,
    "linear_tolerance_strategy": {
      "name": "EISENSTAT_WALKER2",
      "value": 2
    },
    "max_elapsed_time_seconds": 0.0,
    "max_iter": 100,
    "psd_proj_mode": {
      "name": "ALWAYS",
      "value": 1
    },
    "rel_div_tol": 10000.0,
    "rel_step_tol": 2.220446049250313e-15,
    "rel_tol": 1e-09,
    "solver_type": {
      "name": "NEWTON",
      "value": 0
    },
    "stop_if_no_improvement": false,
    "verbosity": {
      "name": "WARNING",
      "value": 2
    }
  }
}
```

</details>

## Historical admission index

Each row refers to `paired-incline/superdex/<case>/admission.json` in the release archive. All nine carry the two aggregate identities above; their trace and geometry hashes were also checked. This audit did not rerun or rescore the physical batch.

| Case | Historical admission SHA256 |
|---|---|
| frictionless-d0.9-h0.0005 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| frictionless-d0.9-h0.001 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| frictionless-d0.9-h0.002 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| sliding-d0.9-h0.0005 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| sliding-d0.9-h0.001 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| sliding-d0.9-h0.002 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| static-d0.9-h0.0005 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |
| static-d0.9-h0.001 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |
| static-d0.9-h0.002 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |

[step]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_step.cpp#L483-L503
[solve]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_solve.cpp#L1093-L1150
[dispatch]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_simulation.cpp#L34-L125
[newton]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/solvers/newton_solver.cpp#L515-L584
[linear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/linear_solver.h#L328-L388
[combine]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.h#L867-L948
[contact]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L498-L788
[alignment]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L1080-L1175
[smooth]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/activations.h#L92-L171
[stats]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/cpp_api/mochi_structs.h#L513-L526
[raw]: https://github.com/huangkiki/Dexlab/releases/download/v0.46.0/paired-incline-raw-v1.zip
[issue]: https://github.com/huangkiki/Dexlab/issues/124
[prereg]: https://github.com/huangkiki/Dexlab/issues/124#issuecomment-6073548423
[build]: https://github.com/facebookresearch/project_superdex/actions/runs/32549763602
[publish-api]: https://github.com/facebookresearch/project_superdex/actions/runs/32757591304
[publish-fp64]: https://github.com/facebookresearch/project_superdex/actions/runs/32757336747
[api-provenance]: https://pypi.org/integrity/superdex-physics/1.0.0/superdex_physics-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl/provenance
[fp64-provenance]: https://pypi.org/integrity/superdex-physics-fp64/1.0.0/superdex_physics_fp64-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl/provenance
