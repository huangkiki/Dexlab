# Chaos Physics learning module

When a box lands in Unreal Engine 5, Chaos computes the collision and rigid-body motion. Use that scene to learn the native workflow, from defining collision shapes to replaying bodies and contacts in the solver.

## Start here

1. [Drop a box onto a floor](box-contact.md). Build collision-enabled and collision-disabled runs in Unreal Editor, then inspect the box and floor contact step by step.
2. [Read substeps, collision events and joints](solver-observations.md). Use the same scene to distinguish game frames from physics substeps, then inspect a hinge constraint.

You need an Unreal Engine 5 editor with Chaos Visual Debugger. The exercises follow Epic’s documented workflows. DexLab has yet to run the Unreal scene.

{ref}`All courses <all-courses>` · [The same exercise in Bullet](../bullet-learning/index.md) · [Epic’s Chaos Physics documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-in-unreal-engine)

```{toctree}
:hidden:

box-contact
solver-observations
```
