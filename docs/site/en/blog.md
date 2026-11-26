# Blog

Solver and simulation fundamentals, findings from DexLab experiments, and research distillation.

```{raw} html
<nav class="blog-jump" aria-label="Blog sections">
  <a href="#solver-fundamentals">Solver and simulation fundamentals</a>
  <a href="#experimental-findings">Experimental findings</a>
  <a href="#distillation">Research distillation</a>
</nav>
```

(solver-fundamentals)=
## Solver and simulation fundamentals

- [One step, several clocks](mujoco-learning/step.md)

  Use a single physics step to understand the simulation step, control period and display rate.

- [Contact, friction and solving](mujoco-learning/contact.md)

  Follow an object onto a table to see when contact activates and how friction limits sliding.

- [Why does a sliding block lift off after the contact solve converges?](complementarity-contact-models.md)

  Use a sliding block to see what the solver is solving and how the contact model changes the answer.

- [How do multiple solvers stay in sync, and what does preCICE do?](solver-coupling.md)

  See how solvers exchange state and forces within one scene.

- [What are we talking about when we talk about the sim-to-real gap?](failure-root-cause-atlas.md)

  Follow the evidence in time to find where a simulation first goes wrong.

(experimental-findings)=
## Experimental findings

- [Why does the ball still spin between two gripping fingers?](wuji-contact.md)

  Compare point and torsional contact to explain rotation about the line between the fingertips.

- [How can we tell if a simulated cut fully separates tofu or banana?](cut-push.md)

  Push the last piece sideways and check whether the sides of the cut can move independently.

- [Cloth: one scene, different engines](cloth-comparison.md)

  Compare a freely sagging strip and a sheet draped over a sphere to study bending and contact separately.

- [LIBERO: from a native task to a verifiable change](libero-workflow.md)

  All ten demonstrations still completed at half the step size, while fewer passed contact-related checks.

- [RoboDojo toast: bread loss and contact escape during insertion](robodojo-bread-slip.md)

  Synchronized motion and contact records show why similar-looking failures lead to different fixes.

(distillation)=
## Research distillation

What DexLab can borrow from external papers and projects, what the authors verified, and what still needs testing here.

- [PhysicsNeMo: does accurate position prediction get contact events right?](physicsnemo-contact-surrogates.md)

  Shell crossings and finger unloading show why pose error and contact events need separate tests.

- [Can a DONIC tracking score tell whether a handoff succeeded?](donic-bimanual-tracking.md)

  A cup handoff shows what contact and support observations add to a tracking score.

- [Goal masks: test the progress signal before using it for GCRL](mask-conditioned-gcrl.md)

  The authors’ apple grasp illustrates how a goal mask supplies feedback and how localization errors can affect it.

- [Physical captions: check reference coverage before judging video facts](physcapbench.md)

  A page-turning example shows how an evaluation can distinguish omitted details from invented ones.

- [NeuralActuator: modeling actuator error while keeping physical contact](neural-actuator.md)

  Read the authors’ 500 g load test and see what still needs checking when contact is disabled.

- [Code as Policy: from model-written code to verifiable robot skills](code-as-policy.md)

  Use a failed grasp to see how program actions and feedback can be inspected.

[More experiments and evidence](experiments.md) · [Dexterous-hand simulation guide](dexterous-hand-simulation.md) · [Paper Sharing](paper-sharing.md)

```{toctree}
:hidden:

donic-bimanual-tracking
physicsnemo-contact-surrogates
```
