## Which setting applies to sliding, twisting or rolling?

Each row retains the components from the preceding row. Directions are local to the contact.

| `condim` | Allowed components | When to check it |
| --- | --- | --- |
| 1 | Normal force | You want a frictionless comparison, or contact never produces any tangential force. |
| 3 | Adds two tangential forces | A box slides across a table or down the gripper pads. Check tangential velocity, normal load and sliding friction. |
| 4 | Adds torsional torque about the normal | A flat coin spins on a table or a pinched ball spins mostly about the grasp axis. Check angular velocity about the contact normal and torsional friction. |
| 6 | Adds rolling torques about two tangential axes | A ball keeps rolling with little tangential slip at the contact. If the real ball stops sooner under matched conditions, check rolling friction. |

Picture a coin sliding across a table, a coin spinning in place and a ball rolling across the table. These illustrate motion at an ideal contact. Actual motion can combine all three.

## Confirm that the edit took effect

1. At the onset of sliding or rotation, find the intended geom pair in `data.contact[i]`. Read `dim`, `friction` and the contact `frame`. Use [`mj_contactForce`](https://mujoco.readthedocs.io/en/4.0.0/APIreference/APIfunctions.html#mj-contactforce) for the three force and three torque components in that frame. The first component is the normal force.
2. Geom `friction` takes sliding, torsional and rolling coefficients, in that order. Sliding friction is dimensionless. The other two have units of length. A contact record has five coefficient slots, with the usable components determined by `dim`.
3. If `dim` differs from your edit, check [`priority` and explicit pairs](contact-parameter-mixing.md). If the intended direction is already enabled, hold control and normal load fixed, record velocity and torque in that direction, then change only the matching coefficient.

{ref}`Find contact parameters by symptom <contact-tuning>`
