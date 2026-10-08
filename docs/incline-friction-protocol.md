# Incline friction: preregistered analytical evaluation

[简体中文](incline-friction-protocol.zh-CN.md)

This protocol supports #95. It specifies a numerical accuracy experiment; no result is claimed yet. The [frozen manifest](evidence/incline-friction/manifest.json) contains all 18 cases. New hardware measurements are not a prerequisite.

## Reference and assumptions

The [OpenStax friction model](https://openstax.org/books/university-physics-volume-1/pages/6-2-friction) bounds static tangential force by μsN and approximates sliding force by μkN. Our derived reference for a nonrotating rigid block is tanθ≤μs at rest and a=g(sinθ−μk cosθ) sliding downhill. The coefficient 0.5 is a deliberately selected model input, not a measured material property. The frictionless control uses a=g sinθ. This is a test against an idealized response, not a universal material-accuracy claim.

A free 40mm cube of mass64g begins with its bottom tangent to the plane, zero velocity and orientation aligned to it. Uniform-box inertia is mL²/6 per axis. Gravity is9.81m/s². The plane is infinite; no joint constrains motion, no actuator or other external force acts, and no state is overwritten after initialization. World normal is (sinθ,0,cosθ); downhill tangent is (cosθ,0,−sinθ). Rotation invalidates the nonrotating reference beyond the declared limit; failures remain in the report.

## Native semantics and matrix

Use official MuJoCo3.15.0, package/native version agreement and recorded runtime hashes. Model XML and compiled configuration must be retained. Use a free joint, analytic box/plane geometry, condim3, Newton solver100 iterations/tolerance1e−10, Euler integrator, elliptic cone, impratio1. Both geoms have identical sliding coefficient, no torsional/rolling friction, and identical contact parameters. Read the actual pair friction from native contacts; MuJoCo's single sliding coefficient does not independently identify μs and μk.

MuJoCo implements [soft constraints and contact parameters](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters). Fix solref=(0.02,1) seconds/damping ratio; separately test constant impedance0.9 and0.99 using solimp=(d,d,0.001,0.5,2). These are declared numerical settings, not fitted materials. For each setting test h=0.002,0.001,0.0005s. The unchanged time constant exceeds2h at every step size. Time refinement at fixed contact parameters and contact-parameter sensitivity must be reported separately; persistent ideal-reference error is not automatically a time-integration error.

Three regimes: static15°/μ0.5, sliding35°/μ0.5, frictionless15°/μ0. These are separated from the marginal tanθ=μ boundary and below the cube's ideal tipping angle. Total3×2×3=18 cases; no tuning after observing results. Run2s each, score0.5–2s to expose settling separately. Report initial-to-final motion too: excluding a transient must not hide its displacement. No success-rate statistical inference from these deterministic cases.

## Measurements and acceptance

Save every integration-step time, actual position/quaternion, linear/angular velocity, summed native force on the box, contact distances/friction and warning counters. Force belongs to the solve preceding integration; retain its time explicitly. Do not recompute it with mj_forward after stepping. Position/velocity are postintegration. Preserve all data and source/config/runtime hashes.

For the scoring window, anchor s0,v0 to its measured first sample; compare v=v0+aτ and s=s0+v0τ+aτ²/2. Also report the unanchored initial-rest reference over the whole run. This distinguishes steady sliding accuracy from startup effects without erasing either. Fit acceleration by least squares on velocity versus time. Static creep is maximum displacement relative to the original initial position, plus maximum speed during the scoring window. Report orientation change, maximum contact penetration and normal/tangential contact-force residual relative to mg cosθ and the declared Coulomb/static support reference. Also compute the discrete impulse balance mΔv−(F+mg)h at matching solve epochs.

Predeclared engineering tolerances (not textbook-certified universal accuracy): static creep≤1mm and speed≤1mm/s; sliding velocity RMSE≤0.01m/s, position RMSE≤0.01m, acceleration error≤0.05m/s²; orientation change≤0.01rad, penetration≤1mm, force-reference RMSE≤0.01N. Report each metric separately and the joint result. Do not relax these if they fail. Missing/nonfinite/truncated traces, wrong time/axes/units or detected state injection invalidate evidence. A scorer cannot establish the absence of arbitrary malicious trace fabrication; source review and frozen native execution supply provenance.

Publish all18 results and error/cost curves, including nonmonotonic refinement and failures. Distinguish setup, native-step, observation and total wall time; rendering is absent. One resource-admitted worker, maximum30min per invocation, existing cgroup memory/CPU/tasks/swap/I/O limits. No transfers or large checksums during timed stepping. Repeating the campaign requires a documented defect and a new immutable evidence directory, retaining the failed campaign.

## Interpretation

This first engine supplies a baseline, not an engine ranking. It tests whether modeled friction supports or accelerates a standard body as expected and how numerical choices affect the answer. Grasp force capacity also depends on contact normals, actual normal force and geometry; these incline results alone do not validate a robot controller, arbitrary materials or the full grasp task. Later independent slices can add centered1D impacts, restitution, conservation and symmetry once their reference assumptions are checked.
