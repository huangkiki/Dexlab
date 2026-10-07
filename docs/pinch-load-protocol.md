# Standard cube pinch: load and slip protocol

[简体中文](pinch-load-protocol.zh-CN.md) · [Frozen manifest](evidence/pinch-load/manifest.json) · Issue #107

## Question and reference

Does a prescribed symmetric jaw force actually produce the expected load capacity and slip? This is a guided two-jaw fixture with a free cube, not a robot policy or calibrated real material. We will execute all18 declared cases; results are pending. No physics has run for this study.

The [OpenStax friction model](https://openstax.org/books/university-physics-volume-1/pages/6-2-friction) gives |f_s|≤mu_s*N and |f_k|=mu_k*N. Here mu_s=mu_k=0.5 is a declared synthetic design value, not a measurement or a value attributed to a particular material. For symmetric nonrotating bilateral contact, mg≤mu*(N_left+N_right) permits static equilibrium. With prescribed inward force N_command=R*mg/(2*mu), R=1 is only the ideal threshold if measured normals equal the commands. At R=0.5 ideal downward acceleration is g*(1−R); R=2 predicts hold. R=1 is marginal and is reported diagnostically without a robust-hold verdict. The Coulomb approximation and guided geometry delimit the prediction.

## Native configuration and controls

Official MuJoCo3.15.0 CPU FP64, Euler, Newton100 iterations, tolerance1e-10, elliptic condim3 contact, impratio1, solref(0.02,1), constant impedance0.9/0.99; dt2/1/0.5ms. R0.5/1/2 makes18 deterministic cases. No tuning after results and no engine patches. [Official actuation](https://mujoco.readthedocs.io/en/stable/computation/index.html#actuation-model) and [contact model](https://mujoco.readthedocs.io/en/stable/modeling.html#contact) distinguish motor input and native contact response; contact softness may violate the ideal assumptions.

Cube:64g,40mm side, uniform inertia, free joint initially at origin/rest. Two100g box jaws have half sizes(0.01,0.1,6)m and centers(±0.03,0,0)m; their inward-facing surfaces initially touch the cube. Their height covers even a one-second free fall, and there is no ground or other support. Each jaw has one horizontal inward slide axis, no limit/damping/friction/armature, and unit-gear force motor. All other jaw motion is constrained by the fixture; these constraints are explicit, not robot dynamics. Only jaw–cube pairs are admitted; unexpected contacts invalidate the case.

Global gravity is zero. During0–0.5s the cube has no external load: this is explicit preload assistance. Jaw commands ramp linearly0→N_command during0–0.2s, then hold. From0.5–1.5s a constant downward cube-COM force mg is applied (equivalent cube gravity, with jaw weights supported by their guides). No cube controller or state writes after initialization. Use integer step indices for ramp/load onset. No resets between stages. Report the full preload and loaded trajectory.

## Observation and independent scoring

Each interval records input commands, actual motor/generalized forces, cube external force, pre-solve contact time, per-side world force and contact position/normal/friction/distance, generalized contact force, warning counts and post-integration state. Forces returned after mj_step belong to the pre-integration solve; do not call a new forward pass before reading them. Record body/joint/geom IDs and compiled geometry, mass/inertia, solver, contact and actuator fields. Preserve XML, full traces, metadata, runtime/source/manifest hashes and all timings. Hashing and compression are outside timed stepping.

Separate three checks: (1) commanded-load ideal prediction; (2) measured-normal friction-capacity diagnostic; (3) discrete impulse/position consistency. The second is not an independent prediction if it uses measured forces; the third is not physical truth. Check cube translation and each jaw horizontal momentum with independently summed contact forces, not just qfrc_constraint. For all cube translation components m*delta_v = h*(contact+external), and Euler delta_x=h*v_next. Track orientation and contact moments; a correct average vertical acceleration cannot override lost bilateral support, lateral drift or rotation.

Loaded-window motion errors use t≥0.6s, relative to the onset state at0.5s; also report the initial-rest ideal reference separately. For R0.5 compare acceleration, velocity and position with the ideal constant acceleration. For R2 score total loaded-stage displacement and maximum speed. R1 gets the same diagnostics but no physical pass. Report per-side normal-command RMSE, native friction bounds, bilateral-contact loss, penetration, orientation, lateral drift, preload velocity and actual onset state. Retain full-stage and scoring-window metrics, including failures before0.6s.

## Frozen engineering limits and budget

Limits are prospective research tolerances, not measured hardware uncertainty: static travel1mm/speed1mm/s; sliding velocity RMSE0.01m/s, position RMSE0.01m, acceleration error0.05m/s²; rotation0.01rad, penetration1mm, lateral drift1mm; per-side normal-command relative RMSE5%; zero loaded-stage bilateral-contact loss; force-balance RMSE0.01N. Discrete impulse residual1e-9N*s and position-update residual1e-10m; contact-cone slack1e-8N, onset cube speed≤1mm/s. Values are fixed in the manifest; never loosen a failed gate. Assess all required assumptions independently of motion agreement. Marginal R1 remains diagnostic even if these metrics pass.

Before physics, freeze protocol/manifest/scorer tests and source commit. Adversarial tests must reject wrong force epoch, missing side/contact data, altered state, command substituted for measured force and broken hashes/configuration. Native runtime and latest-stable admission are checked separately. One18-case1.5s campaign, one resource-qualified worker,30min cap, mounted-volume environment/output,16GiB/twoCPU/128tasks/swap0 and exclusive timing window. Costs include setup, native stepping, observation, serialization, scoring and canonical regressions separately. No engine ranking, population success rate or real-material fidelity claim. Publish all failures plus load/slip curves; relate their limits to grasping without claiming complete robot grasp qualification.
