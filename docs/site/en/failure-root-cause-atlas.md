# What do we mean when we discuss the Sim-to-Real Gap?

This article answers one question: **what makes a simulation claim trustworthy?**

## The short answer

The Sim-to-Real Gap is not the difference between a final frame and a video, and it is not an error detached from the evidence used to define it. More precisely:

> **The gap is the earliest broken link in an evidence chain.**

The task may be wrong; configuration may never reach runtime; the actuator may not supply enough force; collision geometry or the contact model may not express the required mechanism; timestep and stopping conditions may invalidate the numerical solution; observation, scoring or logging may make failure look like success. Beyond all of these, only hardware data can test real-world error.

Five questions must be answered separately:

1. **Did the task succeed?** This only says whether the frozen scorer's task predicates passed.
2. **Is the model physically consistent?** Check support, force and torque, non-penetration, coupling, conservation and budgets.
3. **Is the numerical result valid?** Check solver status, residual, sensitivity to timestep and stopping conditions.
4. **Is the record trustworthy?** Check for stale observations, field mappings, missed failures and recorder perturbation.
5. **Has reality been tested?** Only real sensors, actuators, materials and task measurements can answer this.

> **Without hardware experiments, DexLab can establish parameter delivery, state identity, closed budgets, valid controls and reproducibility. It cannot establish real material parameters, hardware timing, real-world task error or completed sim-to-real transfer.**

## Find the earliest broken layer

<div class="gap-chain" role="group" aria-labelledby="gap-chain-title">
  <div class="gap-chain-copy">
    <p id="gap-chain-title">The final failure is one event; a trusted assumption can break much earlier.</p>
    <strong>Freeze the same task and initial state, then walk backward along the causal chain.</strong>
  </div>
  <ol class="gap-chain-track">
    <li><span>0</span><strong>Preflight<br>identity</strong><small>Runtime readback, units, frames and initial state agree</small></li>
    <li><span>P</span><strong>Task<br>action</strong><small>Grasp placement, action order, clearance and goal are viable</small></li>
    <li><span>A</span><strong>Actuator<br>assistance</strong><small>A named mechanism supplies the required force, torque or retention</small></li>
    <li><span>G</span><strong>Collision<br>geometry</strong><small>The engine accurately represents the shapes and discretisation used</small></li>
    <li><span>C</span><strong>Contact<br>material</strong><small>Normal response, friction, contact moment and coupling are sufficient</small></li>
    <li><span>N</span><strong>Numerical<br>solution</strong><small>Timestep, stopping, residual and precision leave a valid result</small></li>
    <li><span>O</span><strong>Observation<br>evidence</strong><small>Inputs, scoring, fields and recording are trustworthy</small></li>
  </ol>
  <div class="gap-chain-boundary">
    <span><b>P/A/G/C/N/O</b> are the model-internal first-failure domains. If preflight fails, repair evidence identity before attributing a mechanism</span>
    <span><b>Hardware validity</b> is not supplied by model-internal checks</span>
  </div>
</div>

Several boundaries matter:

- **P and G do not overlap.** P asks whether the requested grasp and action make the task viable. G asks whether the engine accurately represents that already planned geometry. One is task design; the other is collision representation.
- **A is not automatically the solver.** If a finger-force limit, hidden assistance or controller budget decides the result, record A first. A later contact event does not justify relabelling it as a contact or solver defect.
- **N does not mean “smaller timestep is more real.”** A smaller step can shift phase, expose instability or increase cost. Only a sensitivity record with fixed model and inputs establishes the numerical behavior.
- **O comes before dynamics attribution.** If an observation is stale, a field is mis-mapped or a score misses the real failure, later physical measurements cannot rescue the claim.
- **Insufficient evidence stays at U.** `U` means the present records cannot uniquely separate mechanisms; it is not a new physical root cause.

The “first failing layer” is not necessarily the earliest timestamp anomaly. It is **the earliest assumption required by the claim that the present evidence disproves or cannot support.** A primary cause may have amplifiers, but an amplifier does not replace the proven first layer.

## Four cases, one causal chain each

<div class="gap-evidence-gallery">
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="robodojo-bread-slip.html" aria-label="Open the complete RoboDojo layout 011 record">
      <img src="_static/robodojo-bread-slip/layout-011-preview.gif" alt="RoboDojo layout 011 recording of shallow top-edge pinch, bread rotation and loss of contact geometry" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">P · Task action</span>
      <strong>The bread does not simply “drop”</strong>
      <p><b>Causal chain:</b> shallow top-edge pinch → about 4.58 m/s² upward acceleration during lift amplifies effective load → the bread rotates in the gripper plane and mean top-edge margin falls from 14.41 to 2.87 mm → bilateral normal impulse drops from about 0.25 to 0.0019 N·s → the bread falls and hits the table.</p>
      <small><b>Evidence boundary:</b> the close command remains zero and no neighbor or shelf impulse occurs before release. Full tangential impulse, resolved runtime material pairing and the native collision mesh are absent, so the evidence proves P plus the lift amplifier, not the remaining split among friction, compliance or the PhysX solver.</small>
      <a href="robodojo-bread-slip.html">Open the complete timeline and controls →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="_static/force-limit/comparison.gif" aria-label="Open the Genesis low-force pinch comparison GIF">
      <img src="_static/force-limit/comparison.gif" alt="Genesis pinch and lift comparison at 0.4 N and 0.8 N per-finger force limits" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">A · Actuator budget</span>
      <strong>“Cannot grasp” may only mean “cannot afford the force”</strong>
      <p><b>Causal chain:</b> per-finger limits of 0.2/0.4 N → the table still carries about 0.428/0.228 N and the object does not leave the table with the gripper; at 0.8/10 N, finger support reaches about 0.628 N, close to object weight, and table support reaches zero.</p>
      <small><b>Evidence boundary:</b> this is a physically explained task failure, not a numerical-solver defect. ±2 mm positional controls retain the result; the GIF is a measured-pose replay, while the force ledger supports the judgment.</small>
      <a href="visual-comparisons.html#pinch">Open the pinch and release comparison →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="wuji-contact.html" aria-label="Open the complete Wuji point- and torsional-contact report">
      <img src="_static/wuji-contact/comparison.gif" alt="Synchronized Wuji point-contact failure and torsional-contact pass in the same task" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · Contact material</span>
      <strong>Contact can persist while the sphere rotates</strong>
      <p><b>Causal chain:</b> the sphere center is offset about 0.310–0.985 mm from the pinch line → torsion about that line is required → the force-only point-contact grasp map has rank five and cannot supply it → both contacts remain present while the sphere rotates and drifts.</p>
      <small><b>Evidence boundary:</b> adding only synthetic torsional contact lowers two-second maximum displacement from 2.734 to 1.025 mm and peak angular speed from 29.336 to 0.024992 rad/s. This identifies a missing contact-moment direction in the fixture, not calibrated fingertip material or a solver defect.</small>
      <a href="wuji-contact.html">Open the contact model and hold curves →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="libero-workflow.html" aria-label="Open the LIBERO workflow report">
      <img src="_static/visual/libero-demo0-baseline.gif" alt="LIBERO native task and recording view" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">O · Observation evidence</span>
      <strong>A task can succeed while its record remains untrustworthy</strong>
      <p><b>Causal chain:</b> reset produces an observation → five additional zero-action settling steps change state → evaluation continues from the pre-settling observation → end-effector position has moved 4.481 mm and the gripper joint value 12.143 mm → actions and diagnostics begin from a stale state.</p>
      <small><b>Evidence boundary:</b> fetching a fresh observation repairs state identity; it does not establish policy improvement. Changing the physics step from 2 to 1 ms lowers diagnostic passes from 5/10 to 3/10 and nearly doubles cost, so a smaller step cannot replace attribution.</small>
      <a href="libero-workflow.html">Open the observation lifecycle and full record →</a>
    </figcaption>
  </figure>
</div>

These cases cover P, A, C and O. The full G and N boundaries, unresolved items and positive/negative controls remain in the configuration records; this guide does not manufacture two extra “representative stories” to make the taxonomy look even.

## Why task success is not physical correctness

A task pass only says that the scorer's predicates passed. It does not automatically establish that:

- collision geometry covers the real contact;
- the contact model supplies the required force or moment;
- external force, actuation, support and energy budgets close;
- the numerical solution meets its frozen gate;
- observations, field mappings, scoring and recording leave the claim intact.

A pass count cannot be added across different material targets, contact models, initial states, precision, stopping conditions and scorers. Equal task names do not establish equal physical problems. Such a sum mixes model differences, invalid records and task failures into a falsely precise ranking.

## What can be claimed without hardware

| Can be established | Cannot be established |
| --- | --- |
| Configuration reached runtime and recorded state matches execution | Configuration values equal real material, sensor or actuator parameters |
| Positive and negative controls are valid under one task, initial state, input and scorer | Simulated timing, latency and actuator response equal hardware |
| Force, torque, momentum, angular momentum and energy budgets close inside the model | Real contact and material behavior outside the model are also closed |
| Changing timestep, tolerance, precision or a parameter produces a recorded response | “Finer,” “more stable” or “more like video” means more real |
| Task pass or failure is reproducible in the frozen model | Sim-to-real transfer has been completed |

DexLab currently has **zero hardware experiments**. This page therefore discusses simulation-internal physical and evidentiary validity, plus the real-world error that remains unmeasured. It does not merge those two conclusions.

## Five-step failure audit

1. **Freeze five verdicts.** State task success, physical consistency, numerical validity, record validity and real-world validity separately.
2. **Order the evidence in time.** Place command, actuator state, relative pose, geometric margin, contact force or impulse, external collision, residual and task outcome on one timeline.
3. **Close budgets and conservation first.** Who carries the weight? Does the required moment direction exist? Do external force, impulse and energy balance?
4. **Change one variable and retain controls.** Vary grasp depth, force limit, latch, collision mesh, contact model, timestep and tolerance separately.
5. **Read runtime state, not intent.** Verify resolved material pairs, contact parameters, solver, precision and collision shape. If evidence is insufficient, record `U` and name the next discriminating gate.

## Where the full evidence lives

This page is a reading path, not a duplicate ledger:

- [Complete experiment directory](experiments.md): historical demos, research experiences and later additions.
- [All results and failures](results.md): continue through outcomes, failures and evidence boundaries.
- [Per-configuration solver audit](solver-failure-audit.md): inspect backend, configuration and numerical-gate differences.
- [Historical evidence inventory](solver-failure-inventory.md): inspect public entrypoints, evidence directories and successful negative controls.

## References

1. Elie Aljalbout et al. [The Reality Gap in Robotics: Challenges, Solutions, and Best Practices](https://arxiv.org/abs/2510.20808). arXiv:2510.20808, 2025.
2. Google DeepMind. [MuJoCo documentation](https://mujoco.readthedocs.io/). Contact, solver and runtime documentation.
3. Bo Liu et al. [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](https://arxiv.org/abs/2306.03310). arXiv:2306.03310, 2023.
4. Chen et al. [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](https://arxiv.org/abs/2607.04434). arXiv:2607.04434, 2026.
5. Meta Research. [SuperDex](https://github.com/facebookresearch/project_superdex). Official repository and versioned implementation.

### Project citation

```bibtex
@software{dexlab2026,
  author  = {Kiki Huang},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```
