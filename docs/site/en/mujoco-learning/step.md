# One step, several clocks

**The physics step advances state; the control period determines when inputs change; the frame rate determines when you see a picture.** They can differ. Wall time is the time the machine actually spends.

## A gripper's 20 ms

With a 2 ms physics step and a new target every ten steps, the control period is 20 ms: 50 Hz. Dynamics still evolves between targets. Holding an input does not freeze the robot or guarantee constant actuator force.

Halve the step while keeping ten steps per update, and control runs twice as often. To compare physics steps alone, adjust the repeat count to preserve the control period.

## Adjust the timeline

Predict first: what happens to control frequency if you change 2 ms to 1 ms? Then set the repeat count to 20 and recover the original control period.

```{raw} html
<div class="time-lab" id="time-lab" data-enhanced hidden>
  <label for="physics-step">Physics step h: <output id="step-value" for="physics-step">2 ms</output></label>
  <input id="physics-step" type="range" min="1" max="10" step="1" value="2">
  <label for="control-repeat">Update control every N physics steps: <output id="repeat-value" for="control-repeat">10</output></label>
  <input id="control-repeat" type="range" min="1" max="20" step="1" value="10">
  <div class="time-results" aria-live="polite"><div><span>Control period N × h</span><output id="control-period">20 ms</output></div><div><span>Control rate 1000 / (N × h)</span><output id="control-frequency">50.0 Hz</output></div></div>
  <svg class="timeline" viewBox="0 0 540 150" role="img" aria-label="Physics and control updates across 100 ms of simulated time; exact values appear above">
    <text x="30" y="20">Physics steps</text><text x="30" y="69">Control updates</text>
    <path class="axis" d="M30 41H510 M30 86H510"/><g id="time-ticks"></g>
    <text x="30" y="130">0 ms</text><text x="510" y="130" text-anchor="end">100 ms</text>
  </svg>
  <p class="note" id="time-explanation"></p>
  <p class="note">A teaching diagram. It does not run MuJoCo or measure real-time performance.</p>
</div>
<noscript><p>Examples: 2 ms × 10 steps = 20 ms (50 Hz); 1 ms × 10 steps = 10 ms (100 Hz); 1 ms × 20 steps = 20 ms (50 Hz). Enable JavaScript to adjust the timeline.</p></noscript>
```

<details class="explanation"><summary>Why can force change while the input stays fixed?</summary>
<p>The actuator defines what <code>ctrl</code> means. A position actuator can take a target position, with force depending on the actual position, velocity and other quantities. Motors, activation dynamics and limits have their own paths. Not every control input is a direct torque.</p>
<p>Think of keeping a car's accelerator pedal in one position: the input stays fixed, but the speed is not locked. This analogy distinguishes inputs from state; it does not replace the actuator equations.</p>
</details>

## Observations have a time too

After `mj_step`, the integration state has advanced. Derived quantities and sensors are produced at their own computation stages. Record simulated time, sampling stage and units together; do not silently combine forces and poses from different stages. Recompute the required forward quantities when needed, accounting for callbacks that another forward call may invoke.

In Python, `data.qpos` typically exposes native memory. Copy arrays when recording history; otherwise an “old snapshot” can change during later steps. See the [state and time course](../learn/mujoco/docs/state-and-time.md); its exact fields and state masks belong to its 3.15.0 baseline.

## Self-check: what changed?

```{raw} html
<form class="quiz" data-answer="b" data-correct="Correct. N × h sets the control period: 20 × 1 ms = 20 ms." data-incorrect="Check N × h again. Halving the physics step requires twice as many steps to preserve the control period.">
  <fieldset><legend>You change the physics step from 2 ms to 1 ms. How do you preserve 50 Hz control?</legend>
  <label><input type="radio" name="timing" value="a">Keep updating every 10 steps</label>
  <label><input type="radio" name="timing" value="b">Update every 20 steps</label>
  <label><input type="radio" name="timing" value="c">Render at 50 FPS</label></fieldset>
  <button type="submit" data-enhanced hidden>Check answer</button><p class="quiz-feedback" role="status" hidden></p>
</form>
<details><summary>Read the explanation</summary><p>Update every 20 steps. Rendering does not set the control period, and equal simulated duration does not imply equal wall time.</p></details>
```

## Back to an actual system

Read back the physics step, control timestamps and repeat count, then locate the sampling stage. For a MATRiX integration, inspect its real scheduler and logs. The teaching values of 2 ms and 50 Hz are not asserted system settings.

Read more: [Actuation and control](../learn/mujoco/docs/actuation-and-control.md) · [Dynamics and pipeline](../learn/mujoco/docs/dynamics-and-pipeline.md) · [Official simulation-loop documentation](https://mujoco.readthedocs.io/en/4.0.0/programming/simulation.html)
