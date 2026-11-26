# Chaos Physics: Read substeps, collision events and joints

One game frame can contain several physics substeps. When checking when the box first hits the floor, choose the clock before you choose the signal.

## Find the contact step

1. Record a baseline with the [box drop scene](box-contact.md). Save the engine version, project physics settings and observed frame intervals. In Chaos Visual Debugger (CVD), find the solver time for the game frame around impact. On the **Solver Timeline**, inspect the first active contact and the preceding step.
2. Use the synchronous physics path. Enable **Substepping** in **Project Settings → Physics**, and record **Max Substep Delta Time** and **Max Substeps**. Repeat from the same initial state. Both limits apply, so check the recording for the actual physics steps within a game frame.
3. On the box component, enable **Simulation Generates Hit Events** and log game-side time and `NormalImpulse` from `OnComponentHit`. Collision callbacks can be delivered after the last physics substep of a game frame. Use the CVD solver trace to place a collision within that frame. A blocking swept move can also trigger a Hit event, for which Epic documents a zero `NormalImpulse`.

`NormalImpulse` is an impulse field. To turn an impulse into an average force, establish the contact, interval and units it represents. The time and value of one callback alone cannot align it with a per-step PyBullet normal-force reading. [Physics substepping](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-sub-stepping-in-unreal-engine) · [Hit event API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ComponentHitSignature?application_version=5.7)

## Put a panel on a hinge

In a separate level, place a static post and a simulated panel. Place a **Physics Constraint Actor** on the hinge, assign the two components, lock all three translation axes and free only the angular degree of freedom along the hinge. Use the constraint’s local frame. Disable collision between the linked components so you can inspect the hinge on its own. With a vertical hinge, apply a sideways impulse to the panel’s outer edge at startup to make it turn.

First allow free rotation, then add only the angular limit. In CVD, inspect the free and locked axes, the angular state and the limit settings, then check the panel pose. If the panel rotates around the wrong axis, check the constraint orientation and initial pose first. To study whether a drive can carry a load, apply a fixed external load and inspect the drive target, measured angle and limit contact over time.

[Course contents](index.md) · [Epic’s constraints guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/constraints-user-guide-in-unreal-engine) · [DexLab’s lesson on simulation time](../mujoco-learning/step.md)
