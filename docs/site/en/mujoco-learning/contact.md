# Contact, friction and solving: three different layers

**The contact model specifies possible forces and torques; the solver computes them; the integrator advances state.** A different solver cannot supply a torque direction excluded by the model.

## Why can two fingers fail to hold a sphere?

Imagine two ideal point contacts. Each applies force but no intrinsic contact moment. Their forces cannot produce torque about the line joining the points. If gravity creates torque about that axis, increasing grip force may not stop rotation.

Think of an ideal axle passing through the sphere: rotation about that direction remains unconstrained by the point forces. This explains an instantaneous geometric direction. It does not imply fixed fingers or that every two-point grasp must fail.

## Identify the layer you are changing

- **Model:** normals, friction directions, contact dimension and soft-constraint parameters define the problem. `condim` changes available contact components; sliding, twisting and rolling are different mechanisms.
- **Numerical solve:** MuJoCo's PGS, nonlinear CG and Newton solve the constraint problem. Iteration budgets, tolerances and warmstart affect the approximation and its cost.
- **Time evolution:** the step and integrator affect the trajectory. A smaller solver residual does not establish a smaller trajectory error or better material fidelity.

(contact-tuning)=
## Which setting should I check for this symptom?

Find the two collision shapes involved at the first abnormal step. Check whether the pair is recorded, whether it produces force and what direction and magnitude that force has.

| What you see | What to check first | Which setting to change |
| --- | --- | --- |
| Collision shapes overlap, but the intended pair never appears | At an overlapping pose, verify the geom pair, contact flags and exclusions. If it only misses at speed, compare a smaller step. | [`contype` / `conaffinity`](../concepts/collision-filtering.md) or `timestep`, depending on where the contact went missing. |
| The object gets pushed away before touching | At the first step with normal force, verify `0 < dist < includemargin`. If the collision shapes already overlap, compare them with the rendered surfaces. | Since MuJoCo 3.9, reducing effective [`margin`](../concepts/margin.md) delays force activation. Check `o_margin` if global override is on. |
| There is a contact record but no measured force | If `efc_address=-1`, compare `dist` with `includemargin` to see whether the pair is still in the detection buffer. | Use [`gap`](../concepts/gap.md) for earlier detection. Check [`margin`](../concepts/margin.md) for force at that distance. MuJoCo 3.9 changed these two settings. |
| The object slides down the pads, spins about a pad normal or keeps rolling on a surface | Read `contact.dim`, then check local tangential velocity, angular velocity and normal load. | Use [`condim`](../concepts/condim.md) to check available components, then check [`friction`](../concepts/friction.md) for the observed direction. |
| An active, loaded contact drifts slowly near rest | Check for spare capacity in the friction cone and record tangential velocity and pose. | Compare [`impratio` with elliptic cones or a separate `noslip_iterations` pass](../concepts/friction.md), one change at a time. |
| Force starts at the right time, but the object then sinks too far or bounces | Measure peak penetration, normal force and rebound height from contact onset. | Check [`solref` / `solimp`](../concepts/soft-constraint.md) and the timestep. |
| XML changed, but the contact readback stayed the same | Check both geoms, explicit pairs and global overrides. | Check how [`priority` / `solmix`](../concepts/contact-parameter-mixing.md) combine the values. |

## Self-check: model or iterations?

```{raw} html
<form class="quiz" data-answer="a" data-correct="Correct. Check whether the model can provide the required torque before judging the numerical solution." data-incorrect="Iterations and tolerance affect the solution of the specified problem; they cannot add a torque component excluded by the model.">
  <fieldset><legend>A point-contact model has no twisting component and the object rotates about the contact line. What is the most informative next check?</legend>
  <label><input type="radio" name="contact" value="a">Inspect torque demand, geometry and actual contact components</label>
  <label><input type="radio" name="contact" value="b">Immediately multiply iterations by ten</label>
  <label><input type="radio" name="contact" value="c">Switch renderers</label></fieldset>
  <button type="submit" data-enhanced hidden>Check answer</button><p class="quiz-feedback" role="status" hidden></p>
</form>
<details><summary>Read the explanation</summary><p>Inspect the model and torque demand first. If the model supplies the required components but measurements show a large numerical residual, then design a solver comparison. Dropping alone does not diagnose a solver defect.</p></details>
```

## Turn a symptom into evidence

Record contact points, normal and tangential forces, intrinsic moments, object velocity, actuator saturation and other support. Follow contact formation, loading and failure in time. This chain determines whether the next useful change belongs to the model, control or solving.

DexLab has an existing [Wuji point-versus-torsional-contact case](../wuji-contact.md). The final lesson returns to its measurements and limits.

Read more: [Soft constraints, `solref`, and `solimp`](../concepts/soft-constraint.md) · [Soft contact and friction cones](../learn/mujoco/docs/contact-models.md) · [Solvers and integration](../learn/mujoco/docs/solvers-and-integration.md) · [Force observations](../learn/mujoco/docs/force-observations.md) · [Official contact dimensions](https://mujoco.readthedocs.io/en/4.0.0/computation/index.html#condim)
