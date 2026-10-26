# Prospective control-rate batch, with the original 2 mm criterion

[English](PROTOCOL-v3.md) | [简体中文](PROTOCOL-v3.zh-CN.md)

The maintainer explicitly authorized a new batch after v2 stopped: improve the grasp baseline, inherit the remaining allowance, and keep the **2 mm** displacement threshold. Both failed positive controls remain in their original cohorts. Neither their raw data nor their scores are replaced. V2's other five cases were not run.

V2 maintained bilateral contact throughout the scored hold, with no actuator saturation or other-body support. Its maximum displacement was **2.458683 mm**, including continued lateral/vertical oscillation during holding. The force/linear-momentum residual was at floating-point precision. This is a failed task criterion, not evidence of numerical solver nonconvergence; changing the reference position, hold window or threshold would not repair it.

Offline contact inspection found tangential/normal force ratios of **0.321–0.472** during the hold, below the nominal sliding coefficient 1.0. Static analysis of the saved states confirms attenuation of the controller's feedback below nominal K. These observations motivate examining the control period before increasing friction. They do not prove a unique cause of the observed motion.

## One prospective change

Change `control_steps` from **4 to 1**: update the same finite-torque implicit sampled PD every **0.5 ms**, rather than every 2 ms. Keep the 0.5 ms native physics step, gains, force caps, grasp gap, sphere, friction, geometry, source assets and all acceptance values unchanged. This synthetic controller frequency is not a claim about real Wuji hardware.

The controller predicts constant acceleration without contact over its hold period. At zero joint velocity its actual requested feedback is `M (M+cK+HD)^(-1) K error`, where `H=N*h` and `c=H(H+h)/2`. Thus its effective static stiffness is smaller than the nominal `K`, particularly for low-inertia modes; shortening the control hold reduces that attenuation. This is a testable control-discretization hypothesis, not a prior guarantee of a successful grasp or proof that it explains all observed oscillation. The native trajectory will still measure actual force, saturation, penetration and object motion. Independent constant-force microstep tests cover both old and new control periods.

The support-removal reference remains **1.0 s**, the scored hold **1.2–3.2 s**, and the limit **2 mm**. All auxiliary forces are zero from 1.0 s onward. Do not add latch, state injection, damping of the object or hidden support. The six cases keep their original order: hold/release, unload index, unload thumb, open, no contact, zero friction. The first positive must pass before launching the remaining five; a failed positive or invalid record stops this batch. Any further redesign requires a separate evidence-based decision rather than an automatic sweep.

## Budget and interpretation

V3 inherits **2 starts and 286.775584 s**, leaving at most **10 starts and 6,913.224416 s** within the original 12-start / 7,200-second package. V3 itself has at most six named starts, each at most 900 seconds, with the existing measured 8 GiB / 4 CPU / 128-task / zero-swap envelope and shared exclusive research lock. Unused allowance is not permission to repeat failed conditions. Source/protocol hashes are recorded before launch in #251 and the immutable successor ledger.

The source-independent scorer, failure preservation and 74-row historical applicability matrix remain as in [v1](PROTOCOL.md). This is one native MuJoCo 3.17.0 development batch. It is neither an all-engine comparison nor #48's ten-condition post-development validation. A successful result would qualify this fixture and controller; it would not establish hardware fidelity or a solver failure.
