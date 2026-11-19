# NeuralActuator: model actuator error separately; keep contact in physics

## TL;DR

**The transferable idea in NeuralActuator is an independent actuator layer: learn the effective effort needed by simulation from servo commands, joint state, current/load, voltage, temperature and tracking-error history. It is not a contact model.**

The authors train a torque surrogate through differentiable simulation, avoiding both `τ = K_tI` and real torque labels. This improves trajectory and force prediction on low-cost arms. But training deliberately disables contact, and the default implicit coupling does not apply predicted force to the state update. For DexLab, first prove that actuator telemetry is identifiable, then replace only the actuator layer.

## What a 500 g payload exposes

A low-cost arm holds a 500 g object. The familiar control chain converts current into joint torque:

$$
\tau=K_tI.
$$

Real servos also contain gearboxes, friction, backlash, saturation and thermal effects. Under one position command, the joint may continue to sag while the controller believes the target was delivered. If that error enters simulation unmodeled, the next diagnosis can incorrectly blame the contact solver, object mass or policy.

NeuralActuator consumes eight prior frames plus the current command, position, velocity, current or signed load, voltage, temperature and tracking error. A Transformer predicts the generalized effort required by the simulator:

$$
\mathbf s_{t+1}=F_t(\mathbf s_t,\boldsymbol\tau_t^{pred}),
\qquad
\boldsymbol\tau_t^{pred}=g_\theta(\mathbf X_t).
$$

No torque labels are required: the loss backpropagates from future measured pose through the simulator. The output is therefore a simulator-equivalent effort, not identified physical torque.

## The strongest result

On the OpenManipulator-X payload benchmark, NeuralActuator reports `0.12 N` force MAE; the paper reports `0.66/1.23/1.41 N` for GMO, ID-Friction and ID-Linear.

The important detail is not simply that a neural model wins. The model-based baselines receive GT robot state at every step, while NeuralActuator uses its own rollout state. This supports the claim that the fixed linear current-to-torque model is inadequate for this low-cost servo and telemetry chain. It does not prove that every model-based estimator is inadequate.

A separate motor-condition test adds an orthogonal signal: a Joint-3 rubber-band restriction reaches `91.0%` accuracy, `96.2%` recall and `0.95` AUC. Telemetry does contain actuator-state information, but this is not lifetime prediction or general fault diagnosis.

## The key counterexample: contact is disabled

The official training entry point enables:

```text
mjDSBL_CONTACT
```

Payloads are not scene geometry, the gripper follows the recorded aperture, and the benchmark trajectories are collision-free by construction.

Under the default implicit coupling, only the torque surrogate drives state; the predicted force is supervised but is not applied. Explicit coupling closes the force path but performs worse on both low-cost platforms.

A lower pose error can therefore come from actuator nonlinearity, an unmodeled payload, contact effects absorbed into torque, or feedback between recorded telemetry and rollout state. These explanations are not separated into identifiable actuator torque.

Placing NeuralActuator inside cutting, cloth, grasping or pinch simulation and observing a lower pose error would not prove that contact physics improved.

## What DexLab should borrow

### Borrow directly

1. **Keep actuation as its own layer.** Record command, q, qdot, current/load, voltage, temperature, torque surrogate and contact force separately.
2. **Qualify telemetry first.** Require monotonic time, command versus feedback provenance, units, signs, missing values, trajectory ID and hardware instance.
3. **Split by trajectory.** Do not randomly split adjacent frames; thermal drift, friction history and mounting batches leak across frames.
4. **Keep negative controls.** Preserve free motion, no-load, normal motor, mechanically restricted motor, contact and matched no-contact data.

### Adapt and verify

If DexLab later obtains low-cost servo logs, start with a single-platform actuator-only pilot:

- compare direct torque surrogate, residual `K_tI + Δτ` and GMO;
- keep the contact solver enabled;
- use an independent force reference to detect absorbed contact load;
- report pose, force, saturation, temperature and no-contact false positives.

The first step is not model training. It is proving that the data can distinguish controller-delivery and actuator-tracking error from real contact load.

### Defer

- do not replace a contact solver with an implicit torque surrogate;
- do not treat a 3D end-effector resultant as multi-finger contact;
- do not use recorded-telemetry rollouts as counterfactual action predictors;
- do not extrapolate a condition score to general motor health;
- do not claim verified force perception without an independent force reference.

## First testable question

**Can one DexLab actuator log separate actuator tracking error from real contact load in time, units, sign and force-reference provenance?**

If not, repair the data contract first. If yes, run a single-platform actuator pilot. Only that evidence can change a DexLab experimental decision rather than adding another difficult-to-audit model.

## Continue reading

- [Paper, arXiv v2](https://arxiv.org/abs/2607.11734v2)
- [Project page](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html)
- [Pinned official code](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator)
- [DexLab Discussion #414](https://github.com/huangkiki/Dexlab/discussions/414)
- [Research intake #415](https://github.com/huangkiki/Dexlab/issues/415)

## Evidence scope

This page reviews arXiv `2607.11734v2` and statically checks official commit `541a93aac4368e73883e86a51f31a7add6bde059`. All numbers are author-reported. This review did not run MJX, Newton, MuJoCo Warp, SuperDex, OMX, SO-101 or Franka, and collected no new hardware data.
