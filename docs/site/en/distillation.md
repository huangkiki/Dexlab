# Research distillation

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

```{toctree}
:hidden:

donic-bimanual-tracking
physicsnemo-contact-surrogates
```
