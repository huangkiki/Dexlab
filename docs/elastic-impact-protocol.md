# Elastic impact protocol

[English](elastic-impact-protocol.md) | [简体中文](elastic-impact-protocol.zh-CN.md)

Two isolated free spheres, no gravity/friction/spin/actuation, equal radius0.05m, centers(-0.06,0.06)m. Masses(1,1)/(1,2)kg; incident speed0.5/1/2m/s; three steps1/.5/.25ms, 0.2s each. Full configuration and engineering tolerances are frozen in [manifest](evidence/elastic-impact/manifest.json). All18 outcomes, including failures, will be reported.

For a closed system and an elastic collision, momentum and kinetic energy give P=m1u1+m2u2, D=u1-u2, M=m1+m2 and v1=(P-m2D)/M, v2=(P+m1D)/M. e=1 is fixed before outcomes, not inferred from them. Score the last20ms only after collision and separation; a missing collision is invalid evidence. Direct MuJoCo solref=(-10000,0) uses zero damping and constant impedance0.9. The ideal reference describes asymptotic separated velocities, not the finite-duration compliant contact trajectory. There is no claim that this contact model represents a real material.

Native Euler/Newton100 iterations/tolerance1e-12; free joints preserve all12 DOFs. Capture full-rate states, preintegration contact forces, native settings/warnings and file hashes. Independent scoring checks initialization, timeline, semi-implicit Euler translation and per-body impulse consistency before physical errors. Consistency checks cannot prove arbitrary recordings authentic; provenance and reviewed runner remain necessary.

One preregistered18-case batch, <=30min, official native MuJoCo3.15.0 CPU FP64, bounded resources. Tests use synthetic records, not development physics trials. No threshold tuning, engine edits or state writes after initialization. Report absolute velocity/energy/momentum errors, restitution deviation, penetration and three-step sensitivity. Finite-step error need not decrease monotonically. This is analytical numerical validation only; real systems and multiple contacts remain separate work.

Sources / 来源: [MuJoCo direct contact reference](https://mujoco.readthedocs.io/en/stable/modeling.html#reference); [OpenStax collision conservation](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions).
