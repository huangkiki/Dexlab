# Discrete contact prediction protocol

[中文](impact-discrete-protocol.zh-CN.md)

This retrospective audit tests a source-derived explanation against all 54 unique published stiffness/phase records. No new native collision runs and no parameter fitting are allowed. Formula agreement, continuous-model error and real-material accuracy are different claims. This document freezes predictions before the numerical trace comparison; the earlier endpoint results informed the hypothesis.

## Source derivation

[Source identities and frozen limits](evidence/impact-discrete/protocol.json) pin official MuJoCo 3.15.0 commit `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`. In `engine_setconst.c:930–941`, free-body translational inverse weight is 1/m. In `engine_core_constraint.c:1945–1955`, a frictionless contact uses the sum of translational inverse weights. A central sphere contact has no rotational Jacobian contribution, so A=1/m1+1/m2 is also the exact constraint inverse mass here.

For constant impedance d, the direct solref stiffness s gives K=s/d² (`engine_core_constraint.c:2206`), reference acceleration −Kd r (`:3484`) and regularization R=(1−d)A/d (`:2186`). The isolated scalar solve gives f=max(0,−Kd r/(A+R))=max(0,−s r/A). Thus relative acceleration is −s r while overlapping. This cancellation requires this isolated, constant-impedance configuration; it is not a general mapping of solref to material stiffness. Nonnegative contact is enforced at `:3577`. `engine_core_util.c:1380` enables the effective metric only for the discrete integrator, not the Euler setting used here.

`engine_forward.c:1510` uses explicit acceleration when DOF damping is zero; `:1477–1483` advances velocity before position. With compression y=2r_sphere−(x2−x1), closing speed w=v1−v2 and reduced mass m_r=1/A:

- F=m_r s max(y,0), applied as (−F,+F) at the input epoch.
- w_next=w−h s max(y,0); y_next=y+h w_next.
- Each body obeys v_next=v+h F_body/m and x_next=x+h v_next.

For active contact, q=y/(u h), v=w/u, z=s h² gives matrix `[[1−z,1],[−z,1]]`. At z=1 its cube is −I. An entering q=a in [0,1], v=1 follows `(1,1−a)`, `(1−a,−a)`, `(−a,−1)`. Zero force at zero overlap makes the a=0/1 boundaries consistent. Exact outgoing speed in this map does not establish an accurate continuous contact waveform.

## Audit and limits

Require two free spheres, central collinear motion, no gravity, friction, damping, spin, actuators, extra constraints or margins, constant impedance and Euler integration. Validate saved XML/readback and published runtime/manifest/trace bindings; unsupported inputs fail explicitly. Full rollout initializes once and never reads later measured states. One-step residuals separately use each measured input state and must not be represented as independent full-trajectory prediction. Force belongs to the pre-integration epoch.

Frozen absolute maximum residual limits: position 1e-10 m, velocity 1e-9 m/s, force 1e-6 N. Retain failures without changing old physical thresholds. Include all stiffness and phase records, not just z=1. Test altered records/hashes, wrong force epochs, boundary phases and detuning. The full 54-record scorer and report remain pending.

For an initially separated approach at speed u, the continuous model starts at t_c=gap/u, has compression u/sqrt(s) sin(sqrt(s)(t−t_c)), and ends contact at t_c+π/sqrt(s). Compare sampled trajectories and contact duration, and total kinetic plus spring energy; these are discretization diagnostics for the declared compliant model, not experimental material truth. Transient load errors matter for future grasp load/slip interpretation even when final rebound is accurate.

One admitted offline worker, mounted storage, swap disabled, enforced memory/CPU/tasks/1800-second bound. Report absolute residuals and observational cost; no performance ranking. Canonical repository submission gates still apply.
