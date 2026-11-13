# From failure to the next improvement

**Learning should let you explain what to change next, and why.** Use DexLab's existing Wuji sphere-grasp case to connect time, contact models and evidence.

## Follow actions through to consequences

In this synthetic fixture, the gripper closes, preparation support is removed at 1.0 s, and holding is scored from 1.2 to 3.2 s.

In point-contact v3, both fingers maintain contact throughout holding, but the contacts supply no intrinsic moment. The sphere's center of mass lies about 0.310–0.985 mm from the contact line, and gravity creates nonzero torque about it. Rotation and displacement relative to the pad reference develop; maximum hold displacement reaches **2.734 mm**, exceeding the original 2 mm threshold.

The evidence first points to a contact-model torque limitation: forces at two points cannot generate torque about their connecting line. Dropping alone does not diagnose a solver defect. The fingers and contacts move, so this instantaneous geometric analysis does not uniquely explain the entire trajectory. [Full measurements and raw-record entry](../wuji-contact.md)

## What changed, and what was measured?

Version v4 retains the hand, controller and commands while adding synthetic torsional friction to object contacts. Maximum hold displacement becomes **1.025 mm**, passing the original hold and active-release criteria. The solver is unchanged. The experiment uses native **MuJoCo 3.17.0**, not version 4.

<details class="explanation"><summary>Why do the limits still matter?</summary>
<p>The new contact law acts during preparation too, changing the state when support is removed. The development comparison qualifies this contact configuration in this fixture; it does not uniquely attribute every displacement difference. Material parameters are synthetic, not measured fingertip calibration. Slow drift remains, and indefinite holding was not established.</p>
<p>Think of adding resistance about the instantaneous “axle”: the model gains a previously missing kind of moment. Real pressure distributions, deformation and changing state are more complex than an ideal axle. The analogy cannot replace measured native moments and states.</p>
</details>

## Choose the next experiment

Ask a question that evidence can distinguish. For example: would the torsional component still help with matched support-removal states? Answering requires matched state, control and independent measurements. This is a possible controlled comparison, not a completed result.

Use the same chain in an actual system: define the task → locate the first failing layer → change one mechanism → reassess under the original criteria. Questions already answered by retained records do not require another full engine matrix.

<a id="how-this-connects-to-rsi-simulation"></a>

## Connecting skill improvement with simulation improvement

Policy failures can expose gaps in simulation or observations. After improving simulation, separately test whether the policy benefits. Reciprocal improvement requires evidence on both sides. The case above completes a contact-configuration comparison; it does not demonstrate a fully autonomous loop of discovering a problem, changing an engine and improving a policy.

<details><summary>Self-check: does 1.025 mm prove MuJoCo 4 is better than an older release?</summary><p>No. The comparison changes contact configuration within MuJoCo 3.17.0. It neither compares engine versions nor modifies the solver. The conclusion must stay within the actual intervention and measurements.</p></details>

## Continue reading

Open the [full Wuji case](../wuji-contact.md) for recorded replay, measurements and limits. Return to the <a href="../_static/research/dexterous-simulation.html">research guide</a> for the wider questions, or follow the [complete MuJoCo courses](../learn/mujoco/docs/curriculum.md) through modeling, state, contact, solving and source code.
