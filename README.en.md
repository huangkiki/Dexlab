<div align="center">


Manually accepted deliveries use a [reviewed ledger](docs/issue-deliveries.json) binding PR, merge commit and acceptance audit. The queue reads only merged main records and verifies live closure and ancestry. Restoring a cloth dependency does not qualify cloth physics.

Genesis joint, GPU and cost reports now distinguish published evidence from remaining unverified capabilities; see the [capability audit](demos/contact-benchmark/GENESIS_COST.md).

# DexLab

**Research question: Which measurable factors determine standard-object grasping outcomes, and why trust the simulated explanation?**

**Holiday findings:** [Conclusions, evidence boundaries and next steps](docs/holiday-report.md). Current scope is the stage report and release closeout.


Current focus: measurable standard-object grasping. Across [16 force-limit cases](docs/force-limit-results.md), 0.2/0.4 N fail retention and 0.8/10 N hold and release, including ±2 mm offsets. All failures and raw records are retained; no hardware-fidelity claim.

**Studying how robots perform contact-rich manipulation in trustworthy simulation.**

[Documentation](docs/site/en/index.md) · [简体中文](README.md) · [Experiments](demos/) · [Results and data](docs/evidence/README.md) · [Research issues](https://github.com/huangkiki/Dexlab/issues)

</div>

The standard-block task retains its native FP64 route: [UniSim admission boundary and remaining work](docs/unisim-reuse-boundary.md). Version/precision mismatch is measured; paired physics equivalence and code-reduction benefits remain unverified.

**Synthetic tactile observation:** 32/64 grids leave native trajectories unchanged; reset and detached-zero checks pass. The first batch has depth but zero contact force, the second fails endpoint matching, and the third passes the bounded checks. [All outcomes, formulas and costs](docs/synthetic-tactile.md)

![Continuous synthetic depth replay](docs/evidence/synthetic-tactile/depth-replay.gif)


**Genesis cloth: the tested frictional grasp profile is rejected.** The official PBD/rigid coupling path lacks tangential friction. Same-step momentum fails its bound; after gripper gravity compensation, holding still fails at the development position and both preregistered offsets. Repeatability and passing geometry checks do not cancel these failures. [Criteria, all outcomes and reproduction](docs/genesis-cloth.md)

| Check | Measurement | Scope |
|---|---|---|
| Actual gripper lift / minimum cloth height | 79.988 mm / 4 mm | Actuator lifts; cloth is not held |
| Same-step momentum residual / bound | 3.2e-5 / 3.3e-7 kg·m/s | Fails; reaction lags 2 ms |
| Equal-duration response | 36 cells × 2 resets, 20 ms | Strong timestep sensitivity, not material convergence |
| Connected folds | 0°, 150°, 170°, every-step checks pass | Finite saved states, not continuous collision qualification |

![Equal-time response and computation cost](docs/evidence/genesis-cloth/history-response-cost.png)

**Newton XPBD primitive contact:** official core CPU configuration reaches 0.000849 mm maximum intrusion and 0.051353% hold-force error; the collision-disabled negative loses support and matches free fall. All three traces and criteria are public; this does not qualify grasp, SDF or hardware accuracy. [Protocol, results and reproduction](docs/newton-contact.md)

![Newton XPBD controls](docs/evidence/newton-xpbd/traces.png)


> [Technical report: current results and historical failures](docs/site/en/results.md) separates cloth repair, low-speed friction response and historical grasp robustness, with metrics, sampling coverage, costs and reproduction links. A single passing case establishes neither robustness nor hardware accuracy.

DexLab uses **UniLab** to organize rigid grasping, cloth and basic contact experiments. We study how collision geometry, contact laws, solvers and drives affect **penetration, slip, jitter and computational cost**, connecting every finding to raw records, independent scoring, parameter provenance and failures.



**Genesis contact diagnostic:** the vertical transient after a horizontal velocity kick depends on friction-cone configuration. The original failure is retained; grasp qualification remains incomplete. [Protocol and limits](demos/contact-benchmark/GENESIS_CONE.md)


**Audit the model before interpreting improvement:** imported Genesis armature changes joint response. Explicit zero-armature controls retain both passing and failing limit configurations. [Parameters, traces and criteria](demos/contact-benchmark/GENESIS_JOINT.md).

![Joint-limit diagnostic](docs/evidence/genesis-joint-limits.png)

**Genesis pinch/release:** the primitive fixture adds reset repeats and open-pad negatives. Candidate contact settings meet the original 1 mm penetration criterion at three development timesteps; failed impacts remain documented. [Protocol, results and limits](demos/contact-benchmark/GENESIS_PINCH.md).

![Genesis pinch and release](docs/evidence/genesis-pinch.png)

**Genesis quality/cost:** three development timesteps pass the engineering criterion without establishing convergence; stepping, observation, writing and scoring costs are separated. [Protocol and capability audit](demos/contact-benchmark/GENESIS_COST.md).

![Genesis quality and cost](docs/evidence/genesis-cost.png)

**Continuous close-up:** recorded Genesis states, displayed by MuJoCo without physics integration. Includes closing, lifting, holding, opening and landing. The 30 fps replay does not replace per-step penetration scoring.

![Genesis measured-pose replay](demos/contact-benchmark/media/genesis-pinch.gif)

**Genesis GPU admission:** reset, two-environment isolation and capacity controls passed; synchronized stage costs are reported without claiming grasp qualification or speedup. [Protocol, costs and limits](demos/contact-benchmark/GENESIS_GPU.md).

## Reference standards and current answers

**We have no evidence that either engine better matches real grasping.** First test the declared model and numerical error; measured data are needed for physical validity. Grasp success is configuration regression only.

| Question | Reference and criterion | Current answer |
|---|---|---|
| Does collision geometry match the declaration? | Native BOX type, 40 mm dimensions and analytic signed distances; 1e-12 m covers FP64 coordinate arithmetic only | Static native readback passes; one query-on/off trajectory has identical states and contact records. [Geometry checks](demos/contact-benchmark/NATIVE_GEOMETRY.md) |
| Do nominal contact mappings transfer? | Prescribed K=20000 N/m, D=40 Ns/m synthetic model, fixed loading and preregistered mass/size cases | None of 30 episodes meets the combined target; a mapping limitation, not real-material error |
| Does finer computation improve reliability? | Fixed model, timestep refinement, reference discrepancy and measured cost | Response–cost curves are available; smaller steps do not reduce every profile's error |
| Does this match real grasping? | Same-apparatus force–displacement, slip and release measurements with uncertainty | Measured references are missing; unanswered |

**Version qualification:** v0.28.0 passed both full 14-second official MuJoCo 3.15.0 / SuperDex 1.0.0 FP64 grasp runs and independent acceptance, plus 491 tests. This qualifies the specified regression configurations, not material accuracy; historical trajectories retain their original version labels.

### Negative SDF construction-path result

For the same asymmetric box, requested spacing and measured native pose,729 interior queries differ by up to **0.129771 mm** between automatic and official precomputed SDF construction. The explicit baked grid is exportable, but is not readback of the automatic actor's internal grid. This static negative result judges neither dynamics nor hardware accuracy; the apple demo is unchanged. [Protocol and independent verification](demos/contact-benchmark/SDF_CONSTRUCTION.md)

## Paired mass and size transfer

Three frozen nominal contact profiles completed30 episodes over10 preregistered mass/size combinations: original engineering checks1/30, transient target0/30, combined0/30. All outcomes independently reproduce; all30 actual initial states and representation checks within the declared scope are complete. **Nominal-scene success does not establish parameter transfer.** No mass/area compensation was applied; failures show that these mappings miss the synthetic target, not that native algorithms are wrong. Internal cooking and combined-law observability remain incomplete.

![Per-scenario synthetic response discrepancy](docs/evidence/contact-transfer-v1.png)

[Protocol, every failure and reproduction](demos/contact-benchmark/TRANSFER.md)

**Matched damping ablation:** Zero normal damping removes recorded tensile force in all three pairs, but settling fails at two finer steps. Combined acceptance remains 0/6; this is not a complete repair. [Reference and all outcomes](demos/contact-benchmark/DAMPING_ABLATION.md)

![Paired unloading forces](docs/evidence/damping-ablation-v1.png)

**Model check before tuning:** under the documented damping law and pure-normal-translation assumptions, a fixed coefficient cannot exactly match constant tangent damping at 2,4,6 N. This analytic mismatch is not measured trajectory error; see the [conditional derivation and reproduction](demos/contact-benchmark/DAMPING_REFERENCE.md).

**Native tangent identification:** All nine default-solver cases failed the fixed momentum gate. Tightening only solver tolerances gives 9/9 valid records and damping near 20/40/60 Ns/m at 2/4/6 N. State/force epoch changes the fit; this is local numerical identification, not completed material calibration. [Protocol](demos/contact-benchmark/TANGENT_IDENTIFICATION.md)

**Applied-load identification:** MuJoCo low impedance gives9/9 valid records; all9 high-impedance records fail settling at0.4s. State and applied-load effects are fitted separately; small prediction error is not completed material calibration. [All outcomes](demos/contact-benchmark/FEEDTHROUGH.md)

**Contact conclusions and standards:** Static matching did not establish shared dynamic material; all30 paired transfer cases fail the combined target. Local identification does not repair unloading. [Acceptance audit, figures and gaps](demos/contact-benchmark/CONCLUSIONS.md)

## Current findings

| Research question | Evidence | Conclusion and boundary |
|---|---|---|
| How do the specified grasp configurations behave on ten initial-state perturbations? | Historical complete acceptance: MuJoCo **1/10**, SuperDex **10/10** | Configuration outcomes on this cohort only; differing contact, drives and timesteps prevent engine attribution or physical-accuracy claims |
| Which engineering checks does the cloth development case pass? | New 9 s development case passes pinch, lift, release and sampled geometry checks; strain 3.52% | Self penetration 1.492 mm is near its limit; one case only, historical failures retained |
| How do materials and contacts affect outcomes? | Retained stretch, drape, sliding, loading and transient successes/failures | Cross-engine measured material/drive calibration is incomplete |
| Does this establish hardware performance? | No formal calibration and independent measured test set | Measured error and sim-to-real capability are unknown |

Plots below are **historical evidence under their original pinned versions**. New batches require latest-stable qualification [#41](https://github.com/huangkiki/Dexlab/issues/41). [Genesis #42](https://github.com/huangkiki/Dexlab/issues/42) has completed bounded synthetic rigid-fixture qualification; thin cloth is tracked separately in #77.

Separate implementation consistency, numerical convergence and measured physical validity; a grasp pass substitutes for none of them. [Research standards](docs/research-focus.md#what-standard-judges-an-experiment)


The next [synthetic response–cost protocol](demos/contact-benchmark/RESPONSE_COST.md) declares 27 repeat runs to compare reference-model discrepancy and cost. All 27 runs were independently rescored: the low-impedance MuJoCo profile approaches the synthetic target under refinement; this SuperDex profile diverges from it and fails unloading no-tension checks. These results establish no hardware accuracy.

![Synthetic response and measured cost](docs/evidence/response-cost-v1.png)

## Key experimental results

**Contact-onset numerical sensitivity.** Across16 fixed-start development runs, MuJoCo adjacent-grid trajectory differences decrease; some SuperDex differences are nonmonotone or increase. Its frictionless cases still pass the existing engineering gates: a pass does not establish timestep convergence. [Protocol, all failures and per-run costs](demos/contact-benchmark/REFINEMENT.md). Twelve additional tolerance controls show that tightening stopping tolerances alone does not remove timestep sensitivity; hardware calibration remains incomplete.

### Apple stem: robustness and where failures occur

Ten frozen scenes vary mass, horizontal position and orientation: twenty runs, without retuning for these cases.

| Historical configuration | Complete acceptance | 95% Wilson interval |
|---|---:|---:|
| MuJoCo 3.11.0 · 0.5 ms | 1 / 10 | 1.8–40.4% |
| SuperDex 1.0.0 FP64 · 2 ms | 10 / 10 | 72.2–100% |

![Per-case contact overlap, wrist displacement and full-protocol failure](docs/evidence/apple-metrics.svg)

Crosses denote complete-acceptance failure. Native contact overlap and independent surface intrusion are different quantities; **wrist displacement is not material slip**. Timesteps, friction and drives differ, preventing an engine-quality ranking. PhysX has a separate development case outside this held-out cohort.

[Protocol and failures](docs/benchmark.md) · [Definitions and rescoring](docs/evidence/README.md) · [Raw-data provenance](docs/evidence/cohorts.json)

### Cloth: a plausible-looking grasp still fails geometry checks

![Cloth/table intersection timeline](demos/cloth-folding/media/table-diagnostic.svg)

The original continuous nine-second record intersects the table in 176 of 225 saved frames. The diagnostic covers zero-thickness triangles, not continuous finite-thickness separation. **A scoring fix is not a physics fix**; full pinch, lift and release remain under [#32](https://github.com/huangkiki/Dexlab/issues/32).

[Old/new scores and coverage](demos/cloth-folding/SCORING.md)

<details>
<summary><strong>All outcomes from seven complete historical cohorts</strong></summary>

![Historical cohort outcomes](docs/evidence/outcomes.svg)

Each row uses a different task/protocol. Keep failures, unsupported outcomes and development/held-out splits; do not collapse them into an engine score. [Technical report](docs/evidence/README.md)

</details>

**Cloth repair candidate (MuJoCo 3.14):** the complete 9 s pinch, lift and release passes the current protocol: maximum strain **3.52%**, lift **123.92 mm**, and zero final hand/cloth force. No table/robot/floor midsurface intrusion is detected in 225 saved frames. Self penetration **1.492 mm** is close to the 1.5 mm limit, so robustness is not established. Official engines remain unchanged; material and control parameters are uncalibrated. [Metrics, plots, continuous video and failed controls](demos/cloth-folding/SETTLING.md).


**Portable historical evidence:** the missing 105 cloth records and one robot-cloth record reproduce all 106 record objects exactly with the frozen historical scorer, retaining failures. Public projections explicitly record deployment-metadata redaction and original/public hashes; historical reproduction is not a pass under the latest protocol. [Download and reproduction](docs/evidence/PUBLIC-ARCHIVE.md).

## Continuous close-up demonstrations

<table>
<tr><th>MuJoCo · default development case</th><th>SuperDex FP64 · default development case</th></tr>
<tr><td><img src="demos/apple-stem-grasp/media/mujoco-sdf.gif" alt="Continuous MuJoCo stem grasp" width="100%"></td><td><img src="demos/apple-stem-grasp/media/superdex-sdf.gif" alt="Continuous SuperDex stem grasp" width="100%"></td></tr>
<tr><th>PhysX · separate development case</th><th>Robot cloth · single-case protocol pass</th></tr>
<tr><td><img src="demos/physx-contact/media/physx-sdf.gif" alt="Continuous PhysX stem grasp" width="100%"></td><td><img src="demos/cloth-folding/media/compliance-grasp.gif" alt="Continuous single-case cloth grasp and release" width="100%"></td></tr>
</table>

Apple GIFs continuously show fourteen seconds of approach, closing, lifting and holding. The display camera serves playback only. [MuJoCo video](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex video](demos/apple-stem-grasp/media/superdex-sdf.mp4) · [PhysX report](demos/physx-contact/apple.md) · [Cloth report](demos/cloth-folding/SETTLING.md)

## Method and engine differences

OpenArm dual arms with Wuji hands: the right thumb/index pinch while the left arm is parked. Apple and stem form a **0.2 kg free rigid body**; apple and both pads use SDF collision geometry. There is no object attachment, object-position drive or engine patch. Control uses **known poses, IK and scripted joint targets**, not a visual policy or learned skill.

| Historical backend | Contact implementation | Step | Disclosed approximations |
|---|---|---:|---|
| MuJoCo | SDF contact search + soft constraints | 0.5 ms | SDF discretization, contact points and constraint settings |
| SuperDex FP64 | Surface-sampling integration + smooth penalty energy | 2 ms | Sampling density, smoothing and penalty response |
| PhysX | Native SDF contacts + TGS | 1 ms | SDF resolution, discrete contacts and torsional radius |

The hold window is 11–14 s, checking lift, two-pad support, penetration, wrist displacement and momentum balance. Fruit contact is allowed during approach. Matching source surfaces do not imply matching discrete geometry or contact laws. Stem bending and fracture are not modeled.

[Parameter provenance and implementation](docs/sdf-backends.md) · [Benchmark design](docs/site/en/benchmark.md) · [Model audit](docs/model-audit.md)

## Experiment code and documentation

| Experiment | Code | Detailed report |
|---|---|---|
| Apple stem grasp | [apple-stem-grasp](demos/apple-stem-grasp/) | [Run and score](demos/apple-stem-grasp/README.md) |
| Robot cloth grasp | [cloth-folding](demos/cloth-folding/) | [Repair and failed controls](demos/cloth-folding/SETTLING.md) |
| Contact, drives and transients | [contact-benchmark](demos/contact-benchmark/) | [Results](demos/contact-benchmark/README.md) |
| Multi-solver cloth | [cloth-benchmark](demos/cloth-benchmark/) | [Materials and held-out cases](demos/cloth-benchmark/README.md) |
| PhysX contact and cloth | [physx-contact](demos/physx-contact/) | [Capabilities and limits](demos/physx-contact/README.md) |

**[Documentation source](docs/site/en/index.md) · [中文文档](docs/site/zh/index.md)**. The site maintains getting started, experiments, results, engine methods, benchmarks and contribution guidance. Both languages use a strict Sphinx build; deployment configuration is included. An online address will be announced after deployment verification.


[Friction-response development results](demos/contact-benchmark/FRICTION_RESPONSE.md): all 16 runs pass existing plane checks, but low-speed resistance and settled initial states differ. Per-case plots and raw-record hashes are retained; no engine-accuracy ranking.

Contact diagnosis: eight native recordings passed original acceptance; six MuJoCo static parameter-mixing controls matched expectations. SuperDex combined pair laws remain unobservable; material equivalence is not established. [Results and reproduction](demos/contact-benchmark/CONTACT_READBACK.md).

## Latest-stable qualification

Latest-stable runtime qualification is in progress: [inventory, GPU probe and limits](docs/engine-qualification.md). Device smoke does not establish grasp success or enable formal benchmark dispatch.

The six-device contact contrast completed: four of six configurations passed and two failed. Smaller timesteps alone did not reduce intrusion under default soft contact; see the per-configuration report above. This is not apple grasp qualification.

The current cloth candidate passes **397 unit tests**; its MuJoCo 3.14 single-case result is above. Published [v0.18.2](https://github.com/huangkiki/Dexlab/releases/tag/v0.18.2) completed both 14 s apple-grasp gates and official-package provenance admission. Current-source paired regression, provenance admission and commit identity are recorded in each delivery PR and Release. Historical sphere-drape failures remain separate.

## Quick reproduction

On Linux x86_64, install [uv](https://docs.astral.sh/uv/getting-started/installation/) and reproduce the original pinned demo:

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# Or --backend superdex; add --headless without a display
```

No model API key is needed. The window opens after SDF preparation and planning. UniLab registers and steps the task; DexLab owns the native scene. [Installation](docs/installation.md) · [Documentation-only build](docs/site/en/quickstart.md#build-documentation-only)

[UR7e and gripper acquisition preparation](docs/hardware/README.md): protocol, signal provenance, clocks, uncertainty and a read-only log validator. Empty templates and synthetic fixtures are not measurements; no hardware data is accepted yet.

## Local execution and autonomous delivery

Experiments now prefer a qualified local host, with measured headroom, enforced cgroup limits and zero experiment swap. Priority review precedes each task; interrupted jobs resume from verified handles. Remote execution is optional. [Execution and recovery protocol](docs/autoresearch.md#local-first-execution-and-recovery).

## Dexterous task roadmap

The [research evidence ledger](docs/dexterity-ledger.md) covers38 paper identities and19 repository entrypoints, distinguishing targeted source audits, abstract screening and unverified runtimes. Conclusions: independently score native task success; distinguish targets, estimated effort and tactile proxies from measured data; exclude custom-engine and historical profiles from latest-stable comparisons. Optional replay #52 and tactile-history #53 have dependencies and budgets.

Current implementations focus on holding and contact diagnostics. The [six-layer research map](docs/dexterity-roadmap.md) connects ManiSkill, grasp evaluation, tactile sensing, data generation and embodiment research to concrete experiments. [Native ManiSkill tasks #47](https://github.com/huangkiki/Dexlab/issues/47) and [in-hand rotation #48](https://github.com/huangkiki/Dexlab/issues/48) are planned, **not implemented or supported yet**.

## Contributing and acknowledgments

Submit reproducible problems, parameter studies and failures as [issues](https://github.com/huangkiki/Dexlab/issues). Experiment PRs update findings, plots and bilingual reports; internal-only changes explain when no homepage update is needed. [Development and release workflow](docs/autoresearch.md)

Thanks to [UniLab](https://github.com/unilabsim/UniLab), [Project SuperDex](https://github.com/unilabsim/project_superdex), [MuJoCo](https://github.com/google-deepmind/mujoco), [Newton](https://github.com/newton-physics/newton), [OpenArm](https://github.com/enactic/openarm) and [Wuji](https://github.com/wuji-technology). Documentation organization draws on [RLinf](https://github.com/RLinf/RLinf). The SuperDex grasp appears in [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex); Astra assisted development and debugging.

Code: [Apache-2.0](LICENSE). Third-party assets retain their [source terms](docs/ASSETS.md).

**Research traceability:** [Actual cloth delivery and recovery audit](docs/autonomous-delivery.md) separates reference standards, failures, independent scoring, archival and recovery evidence. Workflow success does not establish physical accuracy.

**Contact-onset contrast:** 24 fixed settings + 2 repeats pass the engineering checks, while the cone effect changes direction across settings. Passing a task check does not establish material accuracy. [Figures, complete metrics and limits](demos/contact-benchmark/CONE_PROTOCOL.md).

**Unloading observation audit:** point-level rescoring of the original six damping cases found no tension hidden by the aggregate; zero damping still fails the full transient target. [Point-level diagnosis and limits](demos/contact-benchmark/DAMPING_ABLATION.md#point-level-unloading-audit).

**Acceptance scope:** Contact diagnosis has controlled repairs and supported negative results; common dynamic material and hardware calibration remain incomplete. [Evidence and retained requirements](demos/contact-benchmark/CONCLUSIONS.md#acceptance-decision-and-remaining-work).
