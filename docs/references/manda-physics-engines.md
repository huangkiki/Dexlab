# Comparing physics engines for robotics: reading guide

This reference helps readers identify the conditions, measurements, and limits that matter in a cross-engine comparison. It is an independently written DexLab summary and reading guide, not a reproduction of the article or a report of experiments reproduced by DexLab.

- Article: [Comparing physics engines for robotics simulation](https://mandarobotics.com/blog/comparing-physics-engines/index.html).
- Publisher: Manda Robotics; the article does not name an individual author.
- Published: 2026-10-05. This guide was checked on 2026-10-08.
- Background: [Overview of simulation frameworks and physics engines](https://mandarobotics.com/blog/comparing-physics-engines/primer.html).

## Identify the configurations being compared

The comparison concerns specific execution configurations. Product names alone do not justify extending its conclusions to other backends, versions, or defaults. These are the versions reported by the article, not a claim about the latest releases.

| Route | Reported versions | Rigid-body execution |
| --- | --- | --- |
| PhysX | Isaac Sim host 6.1.0.0; a separate PhysX core version is not stated | CPU TGS, float32 |
| Newton / MuJoCo-Warp | Newton 1.5.2, MuJoCo-Warp 3.11.0, Warp 1.16.0 | GPU, float32 |
| MuJoCo CPU | MuJoCo 3.11.0 | CPU, float64 |
| Genesis | Genesis 1.4.1 | GPU, float64 |

This table covers the rigid-body comparison. The deformable section changes the solver combinations: PhysX uses a GPU route, and native MuJoCo-Warp is distinguished from Newton's MuJoCo-Warp + VBD coupling route. Check that section for its material, mesh, coupling, and timestep settings.

## One useful example

In the [sliding-block experiment](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-01), at a 2 ms timestep, stopping positions differ by about 0.05 mm while peak resultant contact forces differ by nearly an order of magnitude. Similar endpoints can therefore conceal different contact histories.

When reading a force comparison, distinguish a resultant force from an individual contact force or an impulse. Check the axes, units, recording frequency, timestep, and measurement window. A visually overlapping trajectory or a single success criterion does not describe the entire dynamics.

## Read according to your question

- **Is the comparison controlled?** Start with the [method](https://mandarobotics.com/blog/comparing-physics-engines/index.html#method). Treat identical source assets and equivalent imported models as separate questions; inspect geometry, mass, centre of mass, inertia, and joint parameters.
- **What belongs to the controller?** Read the [robot experiments](https://mandarobotics.com/blog/comparing-physics-engines/index.html#step-robot) and [controller study](https://mandarobotics.com/blog/comparing-physics-engines/index.html#controller-transfer). A shared feedback controller can produce different torques when it observes different states. It is not necessarily an identical torque replay.
- **What failed in a contact task?** Visit [insertion](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-insertion) and [deformables](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-deformable). Separate import problems, invalid numerical states, contact-feedback issues, and task failures before interpreting the outcome.
- **Which execution path fits the workload?** Read [runtime](https://mandarobotics.com/blog/comparing-physics-engines/index.html#runtime) together with its precision, batch-size, hardware, and timing conditions. Single-environment latency and aggregate batch throughput answer different questions.

## Limits on interpretation

The study has no hardware ground truth. Its viewer replays recorded poses in a common renderer rather than rerunning each physics engine in the browser. Most configurations have one trial; selected repeats and timestep checks are not a complete statistical or convergence study.

PhysX's deformable initialization and contact setup remain unvalidated. Those failures do not establish a general inability to grasp deformable objects. Likewise, matching nominal material parameters should not be assumed to calibrate different internal material models. See the article's [limitations](https://mandarobotics.com/blog/comparing-physics-engines/index.html#limitations) and [reproducibility links](https://mandarobotics.com/blog/comparing-physics-engines/index.html#reproducibility).

For a future DexLab experiment, a useful reading output is a comparison record with separate entries for import checks, input semantics, contact configuration, recorded metrics, and failure criteria. Mark the unverified entries explicitly. This turns observations from the article into questions that can be tested, without assigning an engine ranking in advance.

Keep three questions separate: Did the task finish? How did the state trajectory evolve? Are the force measurements and numerical diagnostics trustworthy? Define each rather than letting “success” stand in for the others. When a discrepancy appears, a useful investigation starts with a simplified scene, fixed initial states and inputs, and aligned recording times. Check imports and measurements before restoring feedback control and complex contact. This is a proposed investigation workflow, not work already validated by DexLab.

## Source and reuse

This review did not find an explicit license covering republication of a full translation or the article's figures and scripts. This page therefore uses an independently written summary and reading navigation, linking to the original rather than including its full text, figures, replay data, or website scripts. A licensed translation could be prepared if suitable permission becomes available. This guide does not imply endorsement by the original publisher.
