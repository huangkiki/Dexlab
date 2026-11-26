(contact-distance-thresholds)=
## Check the MuJoCo version and both thresholds

This applies to ordinary geom contacts. In this table, `margin` and `gap` are the values used by the pair.

| MuJoCo version | Detection threshold | Force activation threshold `includemargin` |
| --- | --- | --- |
| 3.9 and later | `margin + gap` | `margin` |
| Before 3.9 | `margin` | `margin - gap` |

A collision distance `dist` below the detection threshold can produce a record. Below the force threshold, ordinary contact enters the force region. Since 3.9, dynamically generated pairs sum the two geom margins and sum the two gaps. An explicit `contact/pair` supplies its own values. If global contact override is enabled, also check `o_margin`.

When migrating an older model with nonzero `gap`, the release notes specify `margin_new = margin_old - gap_old` and `gap_new = gap_old`. Read back both thresholds. Newer versions allow negative `margin`, with `margin + gap >= 0` still required for detection. [MuJoCo 3.9 migration notes](https://mujoco.readthedocs.io/en/4.0.0/changelog.html#version-3-9-0-may-27-2026)

## The object moves away before visibly touching

- Start with the surfaces apart and move them together. At each physics step, inspect the target pair's `dist`, `includemargin`, `efc_address` and normal force from `mj_contactForce`. Find the first step with normal force.
- If `0 < dist < includemargin` at that step, the force threshold accounts for early activation. In newer versions, reduce effective `margin` with other settings fixed. Compare the distance at force onset and the final resting separation. If `dist` is already nonpositive despite a visible gap, check the offset between the collision and visual meshes.
- To give the controller more advance notice, see [`gap`](gap.md). If the timing is right but the object then sinks too far or bounces, check [`solref` and `solimp`](soft-constraint.md).

{ref}`Find contact parameters by symptom <contact-tuning>`
