# Contact-onset refinement protocol

[English](REFINEMENT.md) | [简体中文](REFINEMENT.zh-CN.md)

The frozen16-run development batch has completed; all outcomes are retained. Existing settled half-step experiments do not isolate integration error: each timestep settles independently. This experiment instead starts a fresh scene with no presettling, and measures the resulting contact-onset transient. It is a different declared physical protocol.

The executed matrix fixes mass0.2kg, half-size20mm, initial velocity0.25m/s, gravity9.81m/s² and duration0.5s. Friction0.3 and zero-friction controls each use1,0.5,0.25,0.125ms; two engines,16 runs,600s maximum. Existing native contact/solver profiles and physical acceptance remain unchanged. All outcomes, including physical failures, remain in the report.

Before comparison, verify archive integrity, matching physical settings, native profile and actual initial state. Sample only common physical times, without interpolation. Report max/RMS position, velocity and orientation differences between successive grids. Finest-grid results are not ground truth. Coulomb-reference discrepancy is separate because compliant/regularized laws differ from that ideal model.

Hypothesis: refinement approaches a stable response over this range. Unmatched initial states prevent comparison; nonmonotone or plateaued differences do not establish convergence order. No accuracy-pass tolerance is invented without an error budget. Hidden native contact histories are not independently observed. The separate solver-tolerance study below complements this matrix; timestep refinement alone cannot certify solver convergence or hardware accuracy.

Implementation: `dexlab.contact_refinement.compare_grids`. Ten analytical, confound and archive-negative tests pass; these are not native episodes. Matrix: `benchmarks/contact-onset-refinement-v1.json`. The protocol was frozen and official-version admission completed before native execution.

![Adjacent-grid differences / 相邻网格差异](media/contact-onset-refinement-v1.png)

[All 12 paired diagnoses / 全部12组成对诊断](evidence/contact-onset-refinement-v1.json)

Observed result: MuJoCo8/8 original engineering passes; SuperDex4/8, with all four frictional onset cases failing. The1ms SuperDex frictional case fails momentum balance and the no-tipping reference condition as well as Coulomb checks; finer cases still fail Coulomb velocity checks. Those failures remain, not retuned away. All12 archive pairs have matching declared native profiles and observed starts, so their trajectories can be compared; this is not physical acceptance.

Forward maximum adjacent-grid position differences (1→0.5,0.5→0.25,0.25→0.125ms) are0.06117/0.03538/0.01539mm for MuJoCo and1.47480/1.96621/1.24122mm for SuperDex. Frictionless SuperDex passes existing engineering gates but differences increase0.16408/0.29110/0.35495mm. Thus a pass and a smaller timestep do not establish convergence. The result concerns these fixed transient protocols, not an engine-accuracy ranking. Pair sampling density changes with each grid; no convergence order is fitted. The tolerance study below probes one possible confound; the contact-onset mechanism remains incompletely identified.

## Solver status and cost

The per-run details retain all16 observed initial states, native readbacks, artifact hashes, independent scores and timings. SuperDex frictional1ms starts with one `STOPPED` step followed by499 `CONVERGED` steps; all steps in the other seven runs report `CONVERGED`. Reaching an iteration cap cannot explain every difference. Native convergence status does not establish timestep convergence. MuJoCo records warning counters; absence of warnings is not proof of solver convergence.

SuperDex readbacks are backward Euler,100 maximum iterations, absolute tolerance0.001 and relative tolerance1e-6, unchanged across timesteps. Tolerance sensitivity remains unresolved. The controlled study below varies solver tolerances independently and reads them back without retuning contact parameters.

Internal batch wall time was27.203s including child startup and version admission. Per-run `step_and_observation_seconds` includes stepping and observation queries, not pure solver time; preparation and total time are separate. Timings were not replicated and do not establish a performance ranking.

## Controlled solver-tolerance comparison

A separately preregistered12-run SuperDex batch fixes contact, initial states and the100iteration cap. At0.5/0.125ms, absolute/relative tolerances1e-3/1e-6 are jointly tightened100× and10,000×. Six frictional and six frictionless episodes all report `CONVERGED` at every step. All six frictional episodes retain failed Coulomb checks; all six frictionless episodes pass.

For frictional0.5ms, maximum position change is1.961µm from baseline to tight and0.01837µm from tight to tighter. Yet cross-timestep maximum position differences remain3.20627/3.20621/3.20621mm. Frictionless cross-timestep differences are0.554478/0.554495/0.554495mm. Tightening stopping tolerances over this range does not remove timestep sensitivity; early solver termination is insufficient as its explanation. This does not establish another untested cause. Joint tolerance scaling cannot separate their individual contributions.

[All12 scores, native readbacks, costs and14 comparisons](evidence/solver-tolerance-report-v1.json). Matrix: `benchmarks/contact-solver-refinement-v1.json`; independent scoring checks declared solver controls against native readback. Raw-archive publication and final regression remain pending.

## Reproduce the offline analysis

With the archived directories and DexLab Python dependencies installed, run from the repository root:

```bash
python demos/contact-benchmark/report_refinement.py /path/to/onset-v1 --output /path/to/new-onset-report.json
python demos/contact-benchmark/report_solver.py /path/to/solver-v1 --output /path/to/new-solver-report.json
```

Outputs must be new files outside the input archive. Neither command runs simulation; exit0 requires all comparisons and per-run details, not passing physics. The prepared raw archive contains28 episodes,603 hashed files and both original frozen campaign sources. All28 original scores reproduce exactly after extraction; native data bytes are unchanged. Archive size19,408,122bytes; SHA256 `073dd8c48708b186313a9f522b491ab2cb8a8a673189fde8b0e1bb52e7cbcc5d`. This archive is prepared locally and is not yet a published release asset.
