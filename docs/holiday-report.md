# DexLab holiday report: findings and remaining questions

Evidence cutoff: v0.42.1. This report consolidates delivered work; unexecuted experiments are excluded. Planned for v0.42.2; GitHub Release metadata determines publication status.

## Main conclusion

This phase moved from demonstrating a grasp to explaining success and failure with independently reviewable evidence. With a fixed standard block, friction and action sequence, low finger actuator limits provided insufficient support while higher limits sustained and released the block. Contact, penetration and momentum records support that interpretation within the declared model. Parameter transfer, cloth grasping and adapter admission also produced useful negative findings. **These results establish configuration-specific mechanisms and boundaries, not a ranking of physical realism across engines.**

DexLab studies contact-rich robotic manipulation in trustworthy simulation. Trustworthiness remains an evidence requirement, not an achieved hardware-accuracy certification.

## Six reportable findings

| Question | Evidence | Conclusion and limit |
|---|---|---|
| How do finger limits affect block grasping? | 40 mm,64 g block;16 completed episodes.0.2/0.4 N fail holding;0.8/10 N pass hold/release, including preregistered ±2 mm offsets | Supports insufficient load support in this model. Actuator limits are not measured contact forces; four levels do not identify an exact threshold or population success rate |
| Do nominal contact parameters transfer? | Three configurations across ten mass/size combinations; joint targets met in0/30 runs | Fixed mappings fail these synthetic targets; this is neither measured material error nor proof of an engine defect |
| Does the tested Genesis cloth support frictional grasping? | Inspected PBD/rigid coupling lacks tangential friction; gripper rises79.988 mm while cloth minimum height stays4 mm; momentum gate fails | Current declared configuration is not admitted. Geometry/reset success cannot cancel grasp or momentum failure; not a universal cloth-model verdict |
| Does synthetic tactile depth prove load support? | Batch1 has nonzero depth but zero native contact force; batch3 passes limited development gates;32/64 grids preserve paired physical trajectories | Geometric depth is an observation, not force, pressure or calibrated sensing. All three controller versions and failures remain visible |
| Can basic contact be independently checked? | Newton XPBD CPU fixture: maximum penetration0.000849 mm, support error0.051353%; collision-disabled control loses support | Validates this support/negative-control fixture, not complete grasping, SDF or hardware fidelity |
| Has an adapter simplified the task? | Unmodified UniSim1.7.10 loader rejects Genesis1.4.3; isolated initialization/cache reads FP32;0 migrated paths and0 demonstrated removed lines | Retain native FP64 ownership. Private compatibility work lacks paired physics qualification and is not released support |

Evidence: [force limits](force-limit-results.md), [mass/size transfer](../demos/contact-benchmark/TRANSFER.md), [cloth](genesis-cloth.md), [synthetic tactile](synthetic-tactile.md), [Newton contact](newton-contact.md), [adapter boundary](unisim-reuse-boundary.md). Each detailed report provides versions, parameters, acceptance, cases, costs and reproduction.

## Lead experiment for a presentation

Use the standard block as the narrative: freeze the object, action sequence and scorer, vary only the actuator limit, then examine held-out offsets.

In the descriptive center-case window, a0.4 N per-finger limit yields about0.4000 N combined upward finger support and0.22784 N table support. At0.8 N, finger support is about0.62834 N with no table support. Block weight is0.62784 N. This supports the stated model-specific explanation; the diagnostic window was selected after execution and is not a preregistered acceptance window.

Numerical validity16/16 does not mean16 successful grasps: six grasp failures and three open controls are retained. Four of eight offset grasp cases pass. Maximum penetration0.665158 mm is below the original1 mm engineering gate, which is not calibrated real-world error.

![Measured failure and success replay](evidence/force-limit/comparison.gif)

Genesis supplies dynamics; MuJoCo only displays measured states without a second dynamics rollout. Animation does not replace full-rate evidence.

## Delivered value and claim boundaries

- Reproducible standard-object experiments with native parameter readback, independent scoring and negative controls.
- Bilingual reports linking successes and failures to versions and raw evidence.
- Explicit admission boundaries for contact, actuation, synthetic observations and adapters.

Historical apple-stem demonstrations and ten-case regressions retain their historical labels. The1/10 versus10/10 results describe their fixed configurations, not engine superiority. Common measured force/displacement, slip and release references are still missing. Visual closed-loop control, learned policies and hardware transfer have not been established.

## Tonight's release scope and acceptance

Concentrate development on this report and one formal stage release; do not dispatch new research experiments. Preserve every unfinished candidate.

1. Check the six claims against delivered evidence; complete both reports and homepage links.
2. Validate links, version, diff and applicable tests without changing physics criteria.
3. Submit and review the report PR under the existing workflow, merge when qualified, publish one new release with report/validation assets, and verify remote tag and assets before declaring publication complete.

Tonight is the target, not proof of delivery. External service failures must be reported as such. A formal stage release does not close all research issues or certify physical realism.

## Next questions, in order

1. **Measured reference (#6):** object dimensions/mass, gripper force-displacement, slip/release and uncertainty. These enable real-world error claims.
2. **Frozen comparison (#3):** separate calibration and held-out evaluation, align tasks/budgets/criteria, report error and cost. No realism ranking without reference data.
3. **Adapter decision (#4):** execute the prepared native/adapter comparison for parameters, state, full contacts and reset; measure actual maintenance reduction. Retain native ownership if benefit is not demonstrated.
4. **Further tasks (#47→#48/#52):** qualify native versions and observability before task integration and action replay. Cloth and real tactile sensing retain separate model/measurement requirements.

These future questions do not block this report release. Expand through testable questions rather than task count or additional success videos.
