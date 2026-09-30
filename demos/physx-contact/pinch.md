# PhysX controlled pinch and release

[English](pinch.md) | [简体中文](pinch.zh-CN.md)

Two ideal prismatic fingers isolate contact behavior. Applying 4 N inward on each side tests supported load, overload, zero friction and release through UniSim's public entity API and official PhysX. The disclosed contact-reporting adapter patch remains in use. This does not qualify robot motors, SDF, cylinders or apple grasping.

## Run and verify

Configure the worker using the [PhysX instructions](README.md), then use a new output directory for each run:

```bash
.venv/bin/python -m dexlab.physx_pinch run --case hold --output demos/physx-contact/runs/pinch-hold
.venv/bin/python -m dexlab.physx_pinch run --case overload --output demos/physx-contact/runs/pinch-overload
.venv/bin/python -m dexlab.physx_pinch run --case frictionless --output demos/physx-contact/runs/pinch-frictionless
# Offline rescoring does not start Isaac Sim
.venv/bin/python -m dexlab.physx_pinch verify demos/physx-contact/evidence/pinch-v2/qualification-v2/hold
```

## Physical protocol

Each fixed-root finger has one prismatic joint, mass 0.1 kg and an analytical box with half-extents 5×25×40 mm, initially centered at x=±15.2 mm and z=200 mm. The floating object's half-extents are 10×10×30 mm. Mass/friction follow the table below; inertia uses a homogeneous cuboid. Finger gravity is disabled; object gravity is 9.81 m/s².

Record actual joint/body states, velocities, external force commands and both contact-normal forces every 1 ms for 3.5 s. There are no position actuators or attachments. An explicit +mg object force supports preparation for the first 0.5 s only; preparation does not count as unsupported holding. Each finger receives 4 N inward until 2.5 s. Release applies 2 N outward for 25 ms, reverses for 25 ms to brake, then removes the force, avoiding sustained loading against joint stops.

| Case | Ideal friction capacity | Weight | Expected behavior |
|---|---:|---:|---|
| hold: 0.2 kg, μ=0.3 | 2.4 N | 1.962 N | Hold, then fall after release |
| overload: 0.5 kg, μ=0.3 | 2.4 N | 4.905 N | Slide after preparation support is removed |
| frictionless: 0.2 kg, μ=0 | 0 N | 1.962 N | Fall after preparation support is removed |

The capacity `μ(N_left+N_right)` assumes parallel vertical faces, horizontal normals, Coulomb friction, no adhesion and no other support. Acceptance uses measured normal forces rather than trusting force commands alone. Tangential friction forces are not independently observed; this qualifies load/motion behavior, not a complete contact-force balance or cylinder load curve.

## Independent acceptance

The scorer does not start physics. It checks all 3,500 steps, timestamps, source/data hashes, native mass/friction/topology readbacks and consistency between actual joint and finger poses. Object–finger overlap uses actual poses and analytical OBB geometry with 15 separating axes, not PhysX's reported penetration.

- Object–finger penetration below 1 mm; prismatic pose consistency within 1 μm and finger rotation-matrix error within 1e-5.
- Mean measured normal load on each side during 0.52–0.60 s within 5% of 4 N. The holding case stays within 1 mm drift and 5 mm/s over 0.7–2.5 s, with both normal forces continuously above 0.1 N.
- Both negative controls drop over 50 mm within 200 ms after preparation support is removed. Correct dropping passes the physics test.
- Over 2.8–3.5 s, normal forces stay below 0.01 N; release produces over 50 mm downward displacement. Fitted vertical acceleration differs from −g by less than 2%, with maximum velocity-fit residual below 0.01 m/s.

These are engineering qualification limits, not hardware accuracy. Tests inject adhesion after release, incorrect overload holding, hidden support, false normal forces, interrupted/missing contacts, corrupted timestamps and altered archives.

## Retained failures and scope

An initial development probe failed during preparation because UniSim rejects passive joint damping. The current fixture explicitly has zero passive damping. The first qualification used sustained outward release: its overload case failed the unchanged 1 μm joint/body consistency limit with a 1.0058 μm error at the travel stop. The second qualification uses finite opening/braking pulses; limits are unchanged, and all three first-round outcomes and trajectories are retained.

[Complete records and hashes](evidence/pinch-v2/manifest.json) include both rounds. These are single-case qualifications after development, not held-out success estimates or engine rankings. Each trajectory archives its scorer; use that version for historical rescoring rather than imposing the new release protocol on old logs. Tiny FP32 geometry differences do not establish physical hardware accuracy. Timings include Python/IPC on a shared host.
