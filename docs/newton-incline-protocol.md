# Newton Physics incline protocol

[English](newton-incline-protocol.md) | [简体中文](newton-incline-protocol.zh-CN.md)

This is an initial fixed-configuration cohort for [#149](https://github.com/huangkiki/Dexlab/issues/149), under the six-engine parent #121. It does not establish a shared tuning/holdout comparison, hardware calibration or reliable coverage-v1 credit. Another solver is not another task type.

## Identity and physical model

Newton **1.6.1**, source `713fecdc41caf0c9d726f5c016939f36e66e3dff`, was the latest official stable release at the 2026-10-09 freeze; 1.7.0rc1 was a prerelease. The 749 installed Newton Python files match both its official wheel and that Git tree. Warp **1.18.0** has 479 code files, including two native libraries, matching its official wheel. The independent native environment uses Python 3.12.12 and NumPy 2.5.3. No engine patches or framework adapter are used. State precision is FP32, on CPU.

Use the [original incline conditions and physical limits](incline-comparison-protocol.md): a uniform 40 mm, 64 g cube at rest, its bottom flush with an infinite plane; gravity [0,0,-9.81] m/s², local COM zero and isotropic inertia mL²/6. Rotate plane and cube about +Y. Each profile has 15° static μ=.5, 35° sliding μ=.5 and 15° nominal μ=0 at 2/1/.5 ms: 2 s each, scoring .5–2 s. A tenth case disables cube collision at 15°/.5/1 ms while retaining both shapes. There are no drives or state writes after initialization.

Every shape explicitly uses density 1000 kg/m³, ke=2500 N/m, kd=100 N·s/m, kf=1000 N·s/m, zero adhesion/restitution/torsional/rolling friction, zero margin and .01 m detection gap. These are synthetic native model settings, not identified material properties. Solver formulations consume these fields differently; identical names do not imply equivalent contact laws. Initial failures are not replaced with outcome-tuned settings.

The frozen shapes have equal friction values. [XPBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2304-L2323) uses their arithmetic mean. [SemiImplicit](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L429-L459) and Featherstone's shared contact kernel do so too; [VBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/rigid_vbd_kernels.py#L995-L1011) uses their geometric mean. Kamino's archived resolved configuration selects `friction_mix_mode="average"` ([source](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/config.py#L1146)). Thus these pair-combination rules preserve .5 and 0 for this equal-material fixture. This does not equate projection, penalty, compliant or friction-regularization laws.

## Solver and observation scope

| Profile | Frozen choices | Native force observation |
|---|---|---|
| XPBD | 100 iterations; default contact weighting/relaxation; no restitution | Accumulated impulses converted by `update_contacts`, wrench on shape0 |
| SemiImplicit | Angular damping 0; remaining native defaults | Actual COM wrench in `state.body_f`; no public per-contact force |
| Featherstone | Angular damping 0; remaining native defaults | Negative linear component of post-step `body_f_ext`; no public per-contact force |
| VBD legacy | 100 iterations; `rigid_compliant_alm=False` | `collect_rigid_contact_forces`, force on body1 |
| VBD compliant | 100 iterations; `rigid_compliant_alm=True` | Same API, separate formulation |
| Kamino PADMM | Explicit PADMM selection; native resolved defaults | `update_contacts`, wrench on shape0 |
| Kamino DVI | Explicit DVI selection; native resolved defaults | Same API, separate algorithm |

Full effective options, topology and initial states are frozen by per-case admission hashes. `add_body()` already creates one FREE joint/articulation; adding another is erroneous. SemiImplicit uses a stand-alone `add_link()` because its joint branch writes forces to an internal temporary buffer; the body still has six free rigid-body state components. Newton gravity has a world row and an additional global row.

Featherstone's `eval_rigid_tau` negates and shifts the native external wrench in place; its post-step linear part therefore needs sign restoration. VBD mutates its input state. Save contact geometry and input state before stepping, and clone `body_q_prev` before the call, with the initial input pose for the first step. Its final force query follows the last dual update; short diagnostics of force–state disagreement remain separate evidence. Never infer measured contact forces from velocity differences.

The clock is the caller's scheduled step intervals; no independent native clock is claimed. Raw state continuity, contact identities/capacity, force convention, geometry, parameter hashes and finite values are checked before the shared analytic metrics. FP32 representation checks use a frozen eight-epsilon criterion scaled by quantity magnitude. This engineering criterion is not a derived forward-error bound for iterative updates; the [results report](newton-incline-results.md) distinguishes its failures from physical error findings. The physical limits, including **1e-7 N·s impulse consistency**, remain unchanged. Missing force channels stay explicitly missing. Failed or interrupted cases remain in the denominator.

Style3D is a particle cloth solver and ImplicitMPM a granular/elasto-plastic particle solver; neither is a stand-alone integrator for this fixed free-rigid-cube protocol. Their constructor setup errors are preserved as development failures, not the evidence for that scope judgment. `SolverMuJoCo` uses the MuJoCo core and cannot add Newton-core coverage; compatible wrapper/conversion comparisons remain separate from these native profiles.

## Budget and reproduction

Freeze seven serial launches, 70 episodes and at most 161,000 updates; each profile has an 1800 s service limit. Based on a measured 520 MiB development peak, the minimum adaptive tier is 8 GiB, with four-core quota, zero swap and a separate 8 GiB launch reserve. The six-hour/64-start development package is separate from the formal pinch budget. Record whole-service resources and native step time; neither is a cross-engine speed ranking.

Commands use the repository's `bounded_run.py` and `research_guard.py` wrappers. The recorder takes `--protocol`, `--proof`, `--output` and optional `--admission-only`. Rescore an extracted profile with `python -m dexlab.newton_incline_score --input PROFILE --output score.json`; scoring imports no physics engine. See the [results report](newton-incline-results.md) for immutable artifacts, failures and costs. DVI reached its original 1800 s limit during the negative; the unchanged nine positives and a separately frozen complete negative form an explicitly attributed continuation. Both attempts remain archived.

Sources: [official release](https://github.com/newton-physics/newton/releases/tag/v1.6.1), [free-body builder](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L5104-L5170), [Featherstone wrench conversion](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/kernels.py#L1377-L1386), [VBD force query](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L3705-L3855).

## Portable commands

Use the immutable archive linked in the results report with official `newton==1.6.1`, `warp-lang==1.18.0`, `numpy==2.5.3` and `packaging==25.0`, Python 3.12.12, and this checkout installed editable. Keep measured resource paths local:

```bash
python scripts/bounded_run.py --profile adaptive --resource-plan "$NEW_PLAN" \
  --cpu-cores 4 --peak-receipt "$MEASURED_RECEIPT" \
  --data-dir "$DATA_DIR" --io-device "$DATA_DEVICE" --timeout 1800 \
  --receipt "$RESOURCE_RECEIPT" -- \
  python scripts/research_guard.py run --lock "$RESEARCH_LOCK" \
  --kind qualification --receipt "$WINDOW_RECEIPT" -- \
  python -m dexlab.newton_incline --protocol frozen-v1/xpbd.json \
  --proof reports/official-proof.json --output "$NEW_OUTPUT"
```

Each profile has its own output and receipt. A new full DVI repeat needs a prospectively frozen longer wall budget based on measured cost; the original timeout remains a failure. Recover the archived interrupted negative using `python scripts/resume_newton_incline.py --input campaign-v1/kamino-dvi --output "$NEW_OUTPUT"` inside the same wrapper with the separate 600 s budget. The original recorder is unchanged. Scorer revision 2 adds only recovery provenance validation; six original completed reports remain byte-equivalent as parsed JSON. The original interrupted campaign remains inadmissible.

For engine-free replay, use the archive's `scoring-source` directory and NumPy 2.5.3: `PYTHONPATH=scoring-source python -m dexlab.newton_incline_score --input continuation-v1/kamino-dvi --output score.json`. Use `campaign-v1/PROFILE` for the other six profiles.
