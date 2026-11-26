# Chaos Physics: Drop a box onto a floor

Why does the same visible floor support the box in one run and let it pass through in another? Change whether the floor participates in physics collision, then trace the result from the visible mesh to the solver contact.

## Build the scene

Create a level in Unreal Engine 5 and remove the template floor or anything else that might intercept the box. Record the editor version. Use two basic 100 cm Cube meshes with simple box collision and zero rotation. Confirm in the Static Mesh Editor that the simple collision shape encloses the mesh.

| Body | Center Z | XYZ scale | Physics settings |
| --- | --- | --- | --- |
| Floor | −10 cm | `(8, 8, 0.2)` | Static, Simulate Physics off, BlockAll |
| Box | 100 cm | `(0.2, 0.2, 0.2)` | Movable, Simulate Physics and gravity on, PhysicsActor |

Place both at X=Y=0. Override the Box mass to 1 kg and set its linear and angular damping to zero. Assign a zero-restitution Physical Material to both through **Phys Material Override**. Record gravity. At −980 cm/s², the bottom of the box starts 90 cm above the floor and the ideal free-fall time from rest is about 0.43 s. Use that as a reference. The first sampled contact depends on the collision geometry, contact settings and actual substeps. [Collision response](https://dev.epicgames.com/documentation/en-us/unreal-engine/collision-response-reference-in-unreal-engine) · [Physical materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/physical-materials-user-guide-in-unreal-engine)

## Record two runs and step through them

1. Open **Tools → Debug → Chaos Visual Debugger**. Keep the **Local Editor** target, enable collision data under **Data Channels**, and choose **Record to File** before clicking **Play** in Unreal Editor. Stop once the box settles and save the `.utrace`. [Epic’s recording walkthrough](https://dev.epicgames.com/documentation/en-us/unreal-engine/recording-to-file)
2. Select Box during playback. Use the **Solver Timeline** to inspect the first active Box–Floor contact and the preceding substep. The box should still be falling one substep earlier. Its downward speed should decrease as support develops. At rest the center Z should approach 10 cm and the vertical velocity should approach zero.
3. Restart the level and change only the Floor’s **Collision Enabled** setting to **No Collision**. The floor is still visible. Record again and inspect the same time interval and body pair. The box should fall through the floor height, with no load-bearing contact for the pair in the recording.
4. If the box also crosses the floor in the first run, check the Box physics state, the responses on both components, and their actual simple shapes. Once those are confirmed, look for the first contact substep and the velocity response to identify where behavior first diverges.

Use position, velocity and the collision constraint together to check for support. These are observations to make in your own run. DexLab did not collect an Unreal trace for this exercise. [Chaos Visual Debugger guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/getting-started-with-chaos-visual-debugger)

[Course contents](index.md) · [Next: substeps, events and joints](solver-observations.md)
