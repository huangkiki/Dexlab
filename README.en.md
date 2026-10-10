# DexLab

**Use established physical laws and empirical relations in reproducible experiments to study how contact and friction affect robotic grasping, and assess the trustworthiness of physics simulation.**

The research serves two goals:

| Your question | What DexLab provides |
| --- | --- |
| **A scene performs poorly. What should improve?** | Locate departures from physical expectations, separate parameters, integration, model assumptions and solving mechanisms, and identify evidenced configuration fixes and solver improvement directions. |
| **A new scene needs an engine/solver. Where should I start?** | Use evidence from similar contact/friction conditions to choose candidate configurations, understand sensitivity, limits, stability and cost, and build practical scenario-selection knowledge. |

[简体中文](README.md) · [Documentation](https://huangkiki.github.io/Dexlab/en/latest/index.html) · [Research experience](docs/site/en/experience.md) · [Diagnosis and trials](docs/site/en/diagnosis.md) · [Scenario guide](docs/site/en/selection.md)

## What we already know

These findings reuse existing reports and logs with their original evidence boundaries. They provide starting points for another experiment, not automatic claims about all current versions or new holdouts.

| Physical question | Existing finding | Implication for grasp simulation |
| --- | --- | --- |
| Normal response | MuJoCo parameters can calibrate static response in a fixed cube fixture; changing mass changes the response of the same parameters. | Interpret parameters with mass, impedance and contact configuration. [Conditions and evidence](https://huangkiki.github.io/Dexlab/en/latest/experience.html#normal-response) |
| Transients and cost | In 27 response/cost records, low-impedance MuJoCo passes 9/9 jointly; high impedance and the tested SuperDex profile each pass 0/9. Smaller steps do not universally remove errors. | Check dynamics, no tension, stability and extra computation together. [Conditions and evidence](https://huangkiki.github.io/Dexlab/en/latest/experience.html#transient-cost) |
| Mass/size transfer | All 30 transfer records for three fixed profiles complete; 0/30 passes jointly. | Single-scene success does not justify direct transfer. Check contact scale and parameter conversion. [Reusable failures](https://huangkiki.github.io/Dexlab/en/latest/experience.html#mass-size-transfer) |
| PhysX contact observations | Four native SDK 5.9.0 incline profiles fail differently; some records trip FP32 impulse-consistency guards. | Separate valid observations from physical error. Finite failed searches cannot establish engine unsuitability. [Diagnosis case](https://huangkiki.github.io/Dexlab/en/latest/experience.html#physx-observation) |
| Pinch and release | Sixteen Genesis fixture cases show drive caps change retention boundaries; robot SDF grasps have separate historical acceptance. | Measure actual support, slip and release alongside contact-force errors. [Conditions and evidence](https://huangkiki.github.io/Dexlab/en/latest/experience.html#pinch-load) |
| Framework integration | Matched cores and CPU models can still have different effective GPU fields; aligning four fields does not explain the full trajectory divergence. | Preserve conversion provenance and effective parameters; attribute specific differences. [Comparison and open questions](https://huangkiki.github.io/Dexlab/en/latest/experience.html#framework-path) |

Response studies use **synthetic stiffness/damping targets**. Analytical relations support **numerical verification**. Accuracy for real materials and robots requires separate measurements. These evidence levels stay distinct; useful existing research need not wait for hardware data.

## How to diagnose a poorly performing scene

For an abnormal contact, declare the physical reference and assumptions, then check geometry, mass/inertia, frames, control epochs, effective parameters and contact readbacks. Fix the scene and objective, propose a testable hypothesis, run bounded parameter trials and independently score improvements and costs. Study the remaining differences through contact generation, friction representation, constraints, stopping rules, integration and precision.

One PhysX case exposed incorrect negative-control mass caused by the order of inertia initialization and collision disabling. Correcting the integration left other numerical residuals unresolved. Record configuration improvements, integration fixes, algorithm research directions and open questions separately. [Diagnosis method and commands](docs/site/en/diagnosis.md)

**AI parameter exploration is a research method.** AI uses prior experience to propose hypotheses and candidates; existing execution, accounting and independent scoring retain every attempt, failure, effective configuration and cost. An unsuccessful finite search establishes only that its tested range did not succeed. Freeze new transfer conditions beforehand; historical logs cannot become new holdouts.

## How to choose for a new scene

Describe contact scale and load, sticking/sliding, contact switches, geometry and compliance, then find nearby experiments. Every starting candidate states version/path, parameter sources, errors and failure boundaries, plus the first checks required in your scene.

| Main difficulty | Starting evidence |
| --- | --- |
| Normal compliance, loading/unloading or transients | [Normal/transient experience](docs/site/en/selection.md): check the synthetic target and contact law, then mass/size transfer. |
| Support, incline sliding or low friction | [Six-engine inclines](https://huangkiki.github.io/Dexlab/en/latest/experience.html#six-engine-incline): validate observations before comparing nearby configurations. |
| Finite-pad pinch, lift and release | [Pinch and SDF starting points](docs/site/en/selection.md): check drives, inertia, slip and negative controls. |
| Framework changes or asset import | [Native/framework comparison](https://huangkiki.github.io/Dexlab/en/latest/experience.html#framework-path): inspect conversion, effective parameters and epochs. |

Recommendations depend on evidence relevant to the target scene, considering **physical credibility, stability and cost** together. Broader validated coverage extends known scope; the coverage table alone does not choose the best solution for a new scene.

## Research scope and reproduction

| Existing scope | Evidence |
| --- | --- |
| Six-engine basic contact/inclines and applicable solvers; collision, fixture pinch and robot grasp | [Full configuration matrix and protocol states](docs/site/en/coverage.md) |
| Cloth mechanics, folded drop and robot cloth grasp | [Historical protocols and failures](docs/site/en/coverage.md); folded drop is not successful active folding. |
| Pushing, in-hand rotation and grasp extensions | [Research roadmap](docs/site/en/dexterity.md); not run, blocked and unsupported remain distinct. |

The matrix preserves core, solver, runtime path, version, passed/partial/failed/not-run/blocked/unsupported states and evidence. Repetitions, step scans and framework changes do not add task types; historical protocols are not pooled. New coverage-v1 reliability is not yet admitted; historical capabilities retain their original scope.

[Installation and reproduction](docs/installation.md) · [All reports](docs/site/en/results.md) · [Raw data and releases](https://github.com/huangkiki/Dexlab/releases) · [Research Project](https://github.com/users/huangkiki/projects/4)

This round reuses evidence and fills concrete diagnosis gaps before transfer to pinch/grasp. The six-engine matrix and 594-episode pinch study remain. **Scheduled development stays paused.** [Development and acceptance](docs/autoresearch.md)
