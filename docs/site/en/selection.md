# Engine and solver starting points for a new scene

Describe contact scale, mass/load, sticking/sliding, contact-switch frequency, geometric complexity, compliance and acceptable cost. A recommendation identifies **core / solver / runtime path / version / effective configuration**. Matching solver names or asset files does not establish equivalence.

| Scene features and difficulty | Evidenced starting candidate | First checks in the new scene |
| --- | --- | --- |
| Small-cube normal compliance and loading/unloading | [Normal response](normal-response): native MuJoCo 3.11 and SuperDex 1.0 have separate frozen response profiles; historical PhysX retains only its original scope. | Effective stiffness, mass/inertia, contact count and separating loads; synthetic targets are not material properties. |
| Specified transients and computation cost | [Transients and cost](transient-cost): low-impedance MuJoCo 3.14 is a candidate for this synthetic target, with full settings/timing in the report. | Oscillation, no tension, load epochs and native/observation cost; [transfer failures](mass-size-transfer) require new mass/size checks. |
| Incline support and low-friction sliding | [Six-engine matrix](coverage.md): select valid observations near the target conditions, such as the native PhysX 5.9 PGS development baseline. | Static-friction threshold, frictionless controls, momentum, acceleration and rotation; initial pass rates are not equal-budget tuned rankings. |
| Finite-pad pinch with load/drive limits | [Genesis force-cap cases](pinch-load) and MuJoCo cube-pinch records. | Per-side drive/normal force, torque, slip, low-force negatives and release; inertia mutation separately needs #145 admission. |
| Robot grasping with complex collision geometry | [MuJoCo/SuperDex 14 s SDF scene](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md), including its full assets, versions and control. | Collision preparation, native contact readback and complete lift/hold/release; one historical scene does not establish robustness for new assets. |
| Asset migration across frameworks or CPU/GPU paths | [Matched-core comparison](framework-path): use default/aligned attribution protocols first. | Source assets, intermediate models, effective parameters, clock, contact path/capacity and reset; unmatched versions cannot isolate a framework-only cause. |
| Cloth compliance/self-contact, pushing or in-hand rotation | [Full scope](coverage.md) and [future tasks](dexterity.md); existing cloth failures also guide diagnosis. | Task-specific positives, negatives and physical checks; not run is not unsupported, and folded drop is not active folding. |

Retain candidate settings, parameter sensitivity, physical error, stability, cost, tested transfer range and failures for each selection. Prefer offline analysis of existing logs; add only the smallest experiment required by a concrete evidence gap. Without a matching scene, label the result a starting candidate and freeze development and unseen-validation conditions separately.

Use latest stable native versions for new admission and official compatible combinations for frameworks. Older versions still support historical mechanism knowledge; report matched-core attribution separately from versions used for selection. Resource limits, installation and visual replay cannot replace physical acceptance.

**LIBERO starting point:** [preserve the native version/configuration and audit observation timing first](libero-workflow.md). No new physics configuration qualifies in this cohort; 1 ms is not a general fix.
