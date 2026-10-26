# Synthetic torsional contact — prospective v4 batch

[English](PROTOCOL-v4.md) | [简体中文](PROTOCOL-v4.zh-CN.md)

After v3 failed the unchanged 2 mm holding threshold, the maintainer selected a finite-contact-area torsional model, retaining the two fingers, sphere and remaining allowance. v1–v3 remain failed development cohorts. This new batch tests a **contact-model hypothesis**, not a new solver or a hardware-calibrated material.

## Frozen change and its meaning

Keep v3's native MuJoCo 3.17.0, source assets, SDF wrist, other collision geometry, controller, 0.5 ms physics/control periods, target motion, preparation forces, mass, inertia and all task thresholds. Change only the object's contact law to `condim=4`, with geom friction `(1, 0.002, 0)`. The hand retains `condim=3` and `(1, 0, 0)`; equal-priority parameter mixing gives object contacts sliding coefficient 1 and torsional coefficient 0.002 m. Hand self-contact remains unchanged. Any non-pad support still invalidates holding.

This is an effective soft-finger torsional law: no elastic volume, patch deformation, rolling friction, latch or prescribed object pose is added. Set a **synthetic circular patch radius a = 3 mm**. For uniform pressure `p` and Coulomb coefficient `mu=1`, a pure twist gives `N=pi*a^2*p` and `T=integral_0^a 2*pi*mu*p*rho^2 d(rho)=(2/3)*mu*a*N`. Hence `T/N=0.002 m`. This is an analytical parameter construction, not an observed patch size or a fit to a successful outcome. MuJoCo's elliptic combined sliding/twisting cone is a further approximation; the derivation establishes only its pure-twist intercept, not the full limit surface of a real pad.

[Native contact dimensions and cone](https://mujoco.readthedocs.io/en/stable/computation/index.html#condim) and [parameter mixing](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters) define the implementation. Save actual contact dimensions, friction readbacks and six-component contact wrenches. For `zero-friction`, zero all geoms' three coefficients and report native effective minima; for `no-contact`, disable both object masks. No explicit contact pair bypasses those masks.

## Acceptance, order and stopping

Use the six named cases and order from [v1](PROTOCOL.md): hold/release, unload index, unload thumb, open, no contact, zero friction. Keep the 1.0 s reference, 1.2–3.2 s holding window, **2 mm displacement**, 0.05 m/s speed, bilateral force, penetration, no auxiliary support and release/unload criteria. The three negative controls must fail holding with valid records; a dropped object after failed grasping is not an active release.

Add one stricter consistency check, without changing historical scores: for the isotropic sphere, `I*(R_after*omega_local_after - R_before*omega_local_before) - h*(sum((contact_pos-COM_before) cross F + intrinsic_moment) + external_moment)` has norm at most **1e-8 Nms at every step**. This is about 1% of `m*g*radius*h`; it checks sign/frame/epoch consistency, not the truth of the contact model. Both linear and angular checks must pass. Report rotation, actual intrinsic moments and existing force-only grasp-map rank as diagnostics, not replacement task criteria.

Static admission checks initial geometry, unchanged hand parameters, native 4D object contacts, zero-friction readbacks and contact-mask removal before dynamics. A synthetic angular-impulse test must detect omitted torsional moments. Run the first positive once; only a qualified hold **and** release permits the other five. Stop this batch on a failed positive, invalid record, missing final resource telemetry or allowance exhaustion. A failed unload or unexpected negative result is retained and reported, not tuned or rerun. No automatic redesign or parameter sweep follows a stop.

## Inherited allowance and scope

Package `wuji-contact-251-v1` remains capped at **12 starts / 7,200 s**, with **3 starts / 740.956017 s** already consumed. v4 inherits at most **9 starts / 6,459.043983 s** and itself names six starts, each at most 900 s. Preserve the original evidence list and prior ledger hash. Use the measured 8 GiB / 4 CPU / 128 tasks / zero-swap envelope and exclusive research lock. Static checks, offline analysis, rendering and repository regression are separately accounted.

Even if v4 succeeds, it only qualifies this synthetic native fixture; it does not validate a real patch, prove torsion uniquely caused all earlier motion, establish an in-hand skill, or complete the other-engine matrix / #48 holdouts. All 15 unexecuted cases from v1–v3 remain not-run. Freeze source/protocol hashes and this card in #251 before native execution.
