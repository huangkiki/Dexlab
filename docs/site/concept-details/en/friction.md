```{index} !friction, !impratio, !noslip_iterations
```

## The grasp holds but drifts slowly. Which setting applies?

1. After lifting, record tangential relative velocity at the contact, normal and tangential forces, and object pose while the intended contacts stay active. Check [`condim`](condim.md) for the required components and confirm the intended pads are still carrying load.
2. If tangential demand is near the boundary of the effective friction cone, check effective `friction` and normal load. Also check contact positions and torque demand, especially if the object slides and rotates together.
3. If the contact keeps carrying load with spare friction capacity but drifts near rest, try varying `impratio` alone with elliptic cones. It changes friction impedance relative to the normal direction. Compare `noslip_iterations` separately. It adds a post-solve iteration stage to suppress drift. Compare velocity, pose and release behavior for each change. For an explicit pair with elliptic cones, `solreffriction` sets a separate friction response. See {ref}`soft constraints <soft-constraint-solimp>`.

[MuJoCo friction parameter mixing](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#contact-parameters) · [Slow slippage in MuJoCo](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#cslowslippage) · {ref}`Find contact parameters by symptom <contact-tuning>`
