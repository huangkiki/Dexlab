# RoboAgentLab: can you trace an agent's command to the robot's outcome?

| At a glance | Details |
| --- | --- |
| Project | RoboAgentLab, a robotics-agent research platform built on pi |
| Input → output | A task, observations, an action interface, and a budget → tool or program execution, environment readbacks, session history, and episode results |
| Public materials | Platform code, documentation, two interaction datasets, and historical run reports. The project page lists the companion manuscript as forthcoming. Existing Show-Harness LoRA adapters can drive action units |
| Review baseline | Platform commit `edef599`, inspected 2026-11-27. The historical October 1 experiments have their own execution revisions |
| DexLab verdict | **`pilot`**. Start by checking whether existing replays can join requests, native states, and independent scores |

[Official project page](https://roboagentlab.github.io/) · [Platform README at the reviewed commit](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/README.md)

## What do you give the agent, and what comes back?

Give it a task such as “put the bowl on the table in the target location.” In LIBERO, the agent can inspect camera images, choose to approach, close the gripper, lift, and then look again. It can also call a detector that returns masks or write Python that combines primitives with conditional logic. Camera frames, detector outputs, and simulator ground truth give the agent different information. Ground truth can help diagnose execution, and comparisons of visual capability need to label that additional access. [Official interface guide](https://roboagentlab.github.io/docs/modes.html)

| Experimental variable | Typical choices |
| --- | --- |
| **Observation O1–O3** | Raw sensory input, provided perception tools, or simulator-only privileged state |
| **Execution A1–A3** | Select an action unit or skill for a fixed executor, orchestrate tools one at a time, or synthesize a constrained Python program |
| **Planner** | A frontier API model, a self-hosted model, a fine-tuned student, or model-free plan replay |

These are separate settings. The available combinations depend on the robot and its services. To compare A2 tools with A3 Python, hold the scene, seed, observations, scorer, and budget fixed. Record the available primitives and how many lower-level steps each call can advance. Fewer calls may simply mean each call does more. The project's Act / Build / Evolve taxonomy distinguishes executing robot tasks, building development workflows, and retaining improvements from feedback. The public implementation below supports inspection of execution interfaces, records, and evaluation. [Platform architecture](https://roboagentlab.github.io/#platform) · [Modes and supported settings](https://roboagentlab.github.io/docs/modes.html)

## How does a command reach the robot, and who scores it?

1. **Pi holds the task and session.** A robot extension registers observations, tools, and the episode lifecycle. Skills describe procedures, units, and how to handle feedback. The service enforces its own execution constraints.
2. **A robot manifest declares available primitives.** An end-effector move, for example, has parameters, a mutation flag, an interface tier, and dependencies. For shared environment-side primitives, tool calls and whitelisted Python calls reach the same service method. Code mode checks the manifest and available capabilities at startup and records their digest. Some TypeScript-side VLA policy loops remain available only as agent tools.
3. **Python services execute and return observations.** A single action can span multiple control steps. Images, state, or errors inform the next decision. For the code-mode example, the relevant chain is `observation → agent request → service execution → native readback`. The requested target pose and the measured pose belong in separate fields.
4. **Episode output preserves different judgments.** The agent's `finish` ends the episode and records its own claim. LIBERO uses the environment's `terminated` signal. RoboDojo retains its native verdict and a separate partial score. Some real-robot settings use an operator verdict. The generic HumanCLAW `success` field maps to navigation. Check these semantics before comparing outcomes across environments.

[Primitive and program interfaces](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/adding-a-primitive.md) · [Episode result source](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/src/robot.ts) · [Evaluation guide](https://roboagentlab.github.io/docs/evaluation.html)

## What does the public evidence cover?

The evaluation runner builds a grid of task and seed combinations and stores a session and result for each cell. A rerun can retry invalid cells while keeping valid completed results, including failures, when the configuration matches. For a model comparison, report the total number of planned attempts alongside valid task failures, planner errors, and environment errors. Keep four evidence levels distinct when using the catalog: a paper can be listed in the taxonomy, recognized by name by the wizard, represented by an explicit preset, or reproduced at a comparable score. These levels tell you increasingly more about what the installed software can do.

| Public artifact | Count or result | Supported interpretation |
| --- | --- | --- |
| Policy Interactions | **904** selected agent turns, **848** with published images | Inspect tool calls and feedback. The data card distinguishes a turn from a complete episode |
| Robotics R&D Interactions | **2,396** development turns, **184** with published images | Inspect development interactions. Unsupported base commits, patches, test results, and outcomes remain missing |
| October 1 HumanCLAW diagnostic | **2/2** for both native `NavSR@20cm` and `InteractSR`; correct seating was visually unverified in both attempts | Demonstrates a scoring boundary across two attempts at one couch scene |

The sources call the readable split `train`. A training recipe still needs verified context, deduplication, tool definitions, outcome labels, and applicable usage rights. Policy Interactions also exposes separate LeRobot v3 roots that preserve continuous execution data with their own action and coordinate conventions. A file path in a tool turn establishes a path reference. A precise call-to-frame join needs an actual linking identifier. Existing Show-Harness weights support the action-unit path. The reviewed code also includes tool and program student interfaces and SFT converters. The platform documentation reports no trained adapters or matched-condition distillation results for those two surfaces. [Policy data card](https://huggingface.co/datasets/RoboAgentLab/pi-embodied-policy-interactions/blob/09820c16208cf6f06f0d4236dfa2db3c15d42c7e/README.md) · [R&D data card](https://huggingface.co/datasets/RoboAgentLab/pi-embodied-rd-interactions/blob/8b0e75515367ae12e6af459e0a8e464d449848f5/README.md) · [Show-Harness weights](https://huggingface.co/showlab/Show-Harness-VLMs)

## Two green scores on the same couch

The historical runs used the same couch scene, self-hosted Qwen3.8-27B, a 900-second budget, and additional self-motion feedback. They ran at separate frozen revisions with identical HumanCLAW code. Native `InteractSR` checks that this is an interaction task, the agent actively stopped and performed a sit, and the pelvis touches the target mesh at the last frame of the final sit motion. Think of it as a check that the person touched the couch. To verify the seat actually supports the person, you need contact location, direction, and persistence. The published summary does not supply contact-point or support-force time series. [Author report and original replay images](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/report.md#humanclaw指标改善与视觉验收分开) · [Result JSON](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/results.json)

- **First attempt.** The instruction was to sit on the target couch. The episode took 29 decision steps with three SIT actions. Collisions occurred in 19 of 28 motion steps, and the final body-to-target AABB distance at active stop was around 8.6 cm. The native interaction metric passed. The replay showed the body behind the couch, leaving seat support unverified. The earliest identifiable gap is at seat-level acceptance during the interaction. Collisions could amplify alignment errors. The onset of misalignment needs time-aligned poses, executed displacement, and contact locations.
- **Second attempt.** The same scene took 38 decision steps with three SIT actions. Collisions occurred in 17 of 37 motion steps. Final target distance was zero at active stop and the interaction metric again passed. The author's replay placed the person near the round side table and did not confirm seating on the target cushion. The available evidence locates a gap between the target-mesh criterion and seat acceptance. Distinguishing an approach error from a sit-execution or scoring ambiguity would take a time-aligned record of which bodies and surfaces contacted the pelvis and in what direction they supported it.

![Author's first replay final frame, with the person behind the couch](https://raw.githubusercontent.com/RoboAgentLab/RoboAgentLab/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/humanclaw-run1-final.png)

![Author's second replay final frame, with the person near the round side table](https://raw.githubusercontent.com/RoboAgentLab/RoboAgentLab/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/humanclaw-run2-final.png)

The images come from the authors' replay of saved post-step physical states. They help inspect position. Measuring load or when a collision first redirected motion requires other observations.

## The first thing worth borrowing for DexLab

DexLab's [Wuji contact-response diagnostic](contact-response.md) already imports actions and native contact records, applies an independent scorer, and checks pre-intervention observations tick by tick. The part worth borrowing is the ability to inspect **one action request, its execution interval, the native readbacks in that interval, and the original scorer verdict** in one replay. Preserve the record hash, clock, units, frame, and provenance. Leave an absent agent call identifier unknown.

Use existing evidence for the first experiment. Select one qualified hold and one recorded unload from the frozen Wuji v4 diagnostic set. Preserve record hashes and the independent scorer. Validate each command-to-step interval against the original indices and timestamps, and retain the first native load change and its conditions. In an offline copy, mask one join key and check that the missing association stays unknown. **Pass criteria** are unchanged original scores and denominators for both episodes, traceability for every reported join, and no inferred association when an identifier is absent. Reuse the existing replay if it already provides that level of localization. Record the missing evidence and stop expanding the pilot if the critical joins cannot be established.

This review inspected pinned source, official docs, data cards, and historical reports. It did not rerun the platform or a DexLab simulation. The proposed work tests replay attribution while retaining DexLab's current simulator backends and scorers. [DexLab current work](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md)
