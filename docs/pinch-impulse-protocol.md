# Pinch impulse residual diagnostic protocol

[简体中文](pinch-impulse-protocol.zh-CN.md) · [Manifest](evidence/pinch-impulse/manifest.json) · [Original findings](pinch-load-results.md)

Issue #109 investigates the unresolved marginal residual from v0.45.0. This is a new diagnostic budget; the previous 18 outcomes, including six rejected records, remain unchanged. No new physics has run at this protocol stage.

## Fixed design

Reuse the declared guided-jaw/free-cube fixture and controls from the original protocol: 64 g, 40 mm cube; two 100 g guided jaws; synthetic friction 0.5; explicit preload 0.5 s, including 0.2 s command ramp; then 1 s downward cube-COM load. Six cases: R = 1 or 2 crossed with Newton stopping tolerance 1e-6, 1e-10 or 1e-14. Fix impedance 0.9, timestep 1 ms, Euler integration and maximum 100 iterations. Only tolerance changes within each R. Official MuJoCo 3.15.0 requires current stable admission before execution; never silently substitute another engine.

One six-case campaign, 1.5 s each, no tuning/replacement reruns. One worker, 30 minute invocation limit, measured RAM/disk admission, enforced cgroup CPU/memory/tasks/runtime, zero swap, mounted-volume outputs and exclusive timing window. Canonical release regressions are separate.

## Observations and independent decomposition

At each solve epoch record pre/post velocities, native qacc, full mass matrix M, qfrc_smooth/constraint/bias/passive/actuator/applied, body external load, states, warnings, active constraint count, solver iteration counts and recorded per-iteration gradient/improvement statistics. Preserve every active island without truncation. Statistics are scaled solver diagnostics, not SI force measurements. Read observations after the native step without another forward evaluation or state write.

For h = 0.001 s and delta_v = v_after - v_before:

- Total residual r = M delta_v - h (qfrc_smooth + qfrc_constraint).
- Integration term e = M (delta_v - h qacc).
- Force term f = h (M qacc - qfrc_smooth - qfrc_constraint).
- Check r = e + f independently, along with velocity integration, full native M against declared diagonal masses/inertia, and smooth-force accounting (actuation + passive + external - bias).

The first five generalized entries are translational; the last three are rotational. Closure bounds are 1e-12 N s and 1e-12 N m s respectively. Delta-v integration bounds are 1e-12 m/s and rad/s. Smooth-force bounds are 1e-12 N and N m. The mass matrix uses a 1e-14 absolute check in each entry's declared generalized-coordinate units. Original physical limits are retained for context, never modified to accept new outcomes.

At tolerance 1e-10 compare baseline states with the exact two published trace hashes listed in the manifest (absolute 1e-12 in each state component's units). A mismatch blocks attribution to the original trajectories. Report absolute peak/RMS residuals, integration and force contributions, tolerance sensitivity/non-monotonicity, cap hits, motion and total/preparation/native/observation costs. An algebraic identity alone does not prove accuracy; changing stopping tolerance is a numerical intervention, not material calibration. If observations do not explain the discrepancy, report it unresolved.

Before running, implement negative tests for missing observations, changed acceleration/velocity/forces, wrong mass/config/epochs/provenance. Freeze the completed runner/scorer sources before the only campaign. Report all six cases, including failed diagnostics; no universal engine or hardware claim.

Sources: [official equations and solver](https://mujoco.readthedocs.io/en/stable/computation/index.html), [native data types](https://mujoco.readthedocs.io/en/stable/APIreference/APItypes.html), and installed official 3.15.0 headers. In particular, qfrc_smooth is net unconstrained generalized force; solver gradient/improvement are scaled quantities.
