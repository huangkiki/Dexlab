## What does the same ball report as it approaches?

Take effective `margin=0.003` and `gap=0.004` under the MuJoCo 3.9 and later convention. These are three positions for an ordinary sphere–plane contact.

| Distance from the plane | Readback for the pair | What it tells the controller |
| --- | --- | --- |
| 8 mm | No record | The ball is outside the 7 mm detection region. |
| 5 mm | Record with `efc_address=-1` | The controller can see the approach. Ordinary contact exerts no force yet. |
| 2 mm | Record with `efc_address>=0` | The ball has entered the 3 mm force region. Read the normal force to check whether it carries load. |

Think of a sensor outside a door. It can report an approach before anything touches the door. This illustrates the order of detection and force activation. Actual force depends on motion, loads and constraint softness.

If you expect support and observe no force, compare `dist` with `includemargin`. If the pair is still in the buffer, check {ref}`margin and version semantics <contact-distance-thresholds>`. If it is inside the force region but still has a negative `efc_address`, inspect `exclude` and whether the degrees of freedom allow a constraint row. When a row exists, use `mj_contactForce` to measure the force. These checks describe ordinary contact. Adhesion has its own activation rules.

{ref}`Find contact parameters by symptom <contact-tuning>`
