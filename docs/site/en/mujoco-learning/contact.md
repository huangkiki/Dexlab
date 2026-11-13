# Contact, friction and solving: three different layers

**The contact model specifies possible forces and torques; the solver computes them; the integrator advances state.** A different solver cannot supply a torque direction excluded by the model.

## Why can two fingers fail to hold a sphere?

Imagine two ideal point contacts. Each applies force but no intrinsic contact moment. Their forces cannot produce torque about the line joining the points. If gravity creates torque about that axis, increasing grip force may not stop rotation.

Think of an ideal axle passing through the sphere: rotation about that direction remains unconstrained by the point forces. This explains an instantaneous geometric direction. It does not imply fixed fingers or that every two-point grasp must fail.

## Identify the layer you are changing

- **Model:** normals, friction directions, contact dimension and soft-constraint parameters define the problem. `condim` changes available contact components; sliding, twisting and rolling are different mechanisms.
- **Numerical solve:** MuJoCo's PGS, nonlinear CG and Newton solve the constraint problem. Iteration budgets, tolerances and warmstart affect the approximation and its cost.
- **Time evolution:** the step and integrator affect the trajectory. A smaller solver residual does not establish a smaller trajectory error or better material fidelity.

<details class="explanation"><summary>Read condim as a model choice, not a quality level</summary>
<p><code>condim=1</code> has the normal component; 3 adds two sliding components; 4 adds twisting about the normal; 6 adds two rolling components. More components do not make every task more accurate.</p>
<p>Torsional and rolling friction coefficients involve a length scale. Do not substitute a dimensionless sliding coefficient. Check the actual combined contact parameters and native readbacks, not only one geom's XML.</p>
</details>

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

Read more: [Soft contact and friction cones](../learn/mujoco/docs/contact-models.md) · [Solvers and integration](../learn/mujoco/docs/solvers-and-integration.md) · [Force observations](../learn/mujoco/docs/force-observations.md) · [Official contact dimensions](https://mujoco.readthedocs.io/en/4.0.0/computation/index.html#condim)
