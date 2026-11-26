# Bullet Physics: Diagnose sliding and load at a joint

A box may slide because friction is too low. A loaded robot arm may depart from its target because the motor reaches its torque limit. Read the simulation after each step to test either explanation.

## Measure friction on an incline

1. Start with the [drop script](box-contact.md). Switch to a fixed ramp and align a face of the box to it. Release the box from rest with a small gap between the faces. Hold `DIRECT`, gravity, timestep and iteration settings fixed. Record the incline angle, `lateralFriction` on both bodies and the box orientation.
2. Set the bodies’ lateral friction separately with `changeDynamics`. Use zero on both bodies for the first control. Skip the impact window. While contact persists and rotation is small, compare the slope of tangential velocity to the frictionless reference $g\sin\theta$. Restore friction for the positive case and keep reading displacement, support and slip velocity.
3. Read the two lateral friction components and their directions with `getContactPoints`. Reconstruct vectors before adding them. A box that stays still gives evidence that this condition did not exceed the static-friction threshold. To estimate the threshold, increase incline angle or tangential load in stages while the box stays in contact and clear of tipping.

## Read the joint command and measured state separately

1. Use `loadURDF(..., useFixedBase=True)` to load a robot arm with a revolute joint. Inspect `getJointInfo` to confirm the joint name, type and angle limits. Hold other joints at recorded poses and keep the arm clear of the floor.
2. With `setJointMotorControl2`, give the same revolute joint a position target and an explicit torque limit. Run without an additional load, then restart from the same pose and add a fixed load. For a sustained load via `applyExternalForce`, resend the same force and application point in world coordinates before every explicit physics step.
3. After each step, use `getJointState` to record angle, angular velocity and motor torque separately. If the angle error grows under load and torque is near the limit, raise only the limit and check if the error shrinks at the same load. The default motor can affect a passive-joint control. Disable it for a free-motion control with `VELOCITY_CONTROL` and `force=0`. For joint reaction forces, enable the force/torque sensor and check its frame separately.

These are follow-on exercises. The published course run is the paired box drop. [Official PyBullet guide](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstartguide.pdf) · [Upstream joint control example](https://github.com/bulletphysics/bullet3/blob/master/examples/pybullet/examples/jointFrictionAndMotor.py)

[Course contents](index.md) · [DexLab’s contact and friction lesson](../mujoco-learning/contact.md)
