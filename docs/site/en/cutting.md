# Cut a soft block in half

This experiment implements one **synthetic tofu-like block halving** task from the mechanisms in [BladeMaster, arXiv:2609.27342v2](https://arxiv.org/abs/2609.27342v2). A force-driven blade cuts and withdraws; a later diagnostic impulse checks whether the two pieces move independently. This is an independent CPU implementation, not the authors' code or a reproduction of their GPU speed or real-food accuracy.

```{raw} html
<section class="cutting-player" aria-label="Tofu halving">
<header><h3>Tofu halving</h3><div class="cutting-view-switch" aria-label="Representation"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu/surface.mp4" data-poster="_static/cutting/tofu/surface-poster.png" aria-pressed="true">Surface</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu/particles.mp4" data-poster="_static/cutting/tofu/particles-poster.png" aria-pressed="false">Particles</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu/surface-poster.png" aria-label="Tofu halving"><source src="_static/cutting/tofu/surface.mp4" type="video/mp4"><a href="_static/cutting/tofu/surface.mp4">Watch video</a></video>
<p>Cut, withdraw and check independent motion.</p>
</section>
```

Surface and particle views share the same saved physical states and play at physical speed. Blue and orange are persistent cut-side labels; colour alone does not establish mechanical separation. At 2.4 s, the right half receives a known external impulse. This is a diagnostic intervention, not a robot manipulation policy. The first version has no robot arm, camera controller or learned policy.

## What is implemented

| Paper mechanism | Implementation and scope |
|---|---|
| Eq. 1–2: fixed reference stencils | Eight trilinear reference weights per material point; fixed-corotated elasticity, explicit MUSL and PIC/FLIP in FP64 |
| Eq. 3–7: geometric side assignment and contact work | One finite straight blade, persistent `0 → 1/2` labels; cutting-band half-width `6 Δx`, rear extent `2 Δx` plus relative sweep; front extent two proxy radii |
| Eq. 8–9, 17: compatible logical grids | Simultaneous conservative exchanges between 0/1 and 0/2 in P2G and MUSL; no 1/2 exchange; the FLIP difference uses coupled old momentum as in Eq. 17 |
| Eq. 10–13: material contact | Current-space spherical proxies, reference-neighbour exclusion within `2 Δx`, lifted for opposing cut sides; persistent tangent history and Coulomb slip |
| Eq. 14–16: tool contact | Box closest-point queries, predicted-gap impulse and the same opposite impulse on the dynamic blade; attitude fixed by a guide, reaction torque recorded |
| Directional resistance | Contact work accumulates toward `Gc V^(2/3) (1−ζ)/ζ`; saturated damage releases the positive cutting-direction impulse at subsequent contacts. Damage does not scale elasticity or directly trigger separation |
| Rendering | Surface and particle replay from saved states; exposed material-cell faces with compatible deformation embedding. This differs from the paper's linked-grid dual contouring |

The 0.2 kg blade has three dynamic translation coordinates. A bounded PD drive follows an edge-height target; material reaction changes its velocity. A gravity-compensated guide fixes attitude, and a unilateral rigid-board stop supplies a separately recorded external impulse. This is not the paper's freely rotating gravity-drop experiment. This page retains the v0.61.0 single-cut baseline; the new version adds [three sequential banana cuts](banana-cutting.md). Intersecting paths, plasticity, viscosity and GPU kernels are not qualified.

## Parameters and frozen acceptance

The block is 60 × 30 × 30 mm, with density 1,100 kg/m³, Young's modulus 6 kPa and Poisson ratio 0.35. Density and modulus borrow the paper's soft-block example (§IV-A); the remaining settings are selected synthetic experiment parameters. **None is a measured tofu calibration.** Total mass is 59.4 g. The default grid is 7.5 mm, eight particles per cell (1,024 particles), with a 0.5 ms timestep. The blade is 1 × 50 × 40 mm.

Other selected constants: PIC/FLIP blend 0.95; normal scale 0.1; static/dynamic friction 0.3/0.2; tangent stiffness/damping scales 0.05/0.1; cutting-energy scale 0.5 J/m² and sharpness 0.9. Drive stiffness/damping are 250 N/m and 14 N·s/m, capped at 10 N. Particle proxy radius is `Δx/4`. Contact penalty and tangent stiffness scale with timestep, so changing timestep is a sensitivity test, not automatically a same-constitutive-law convergence proof.

The 3 s sequence settles to 0.3 s, cuts through 1.3 s, holds to 1.6 s, withdraws by 2.2 s and probes at 2.4 s. The blade's target may reach −4 mm to load the board stop; its measured edge cannot pass below the board. The probe adds velocity (0.12, 0, 0.1) m/s to particles originally on the right, equivalent to an external impulse of (0.003564, 0, 0.002970) N·s.

Acceptance was frozen before the first run: initially one connected transfer graph; finally two components with mass fractions within 0.02 of 0.5; persistent labels; at least 1 mm relative x motion with at most 3 mm passive-half x displacement; fully withdrawn blade; nonzero material reaction above 0.001 N; Jacobian at least 0.05; proxy overlap at most one radius; and independently recomputed momentum errors at most 10⁻⁹ N·s. Record checks also reconcile frame velocities, external impulses and blade reaction feedback. These are numerical/task checks, not experimental force accuracy.

## Evidence and limitations

| Case | Halving | Components | Relative motion (mm) | Peak reaction (N) | Record time (s) |
|---|---|---:|---:|---:|---:|
| `004-full` | Pass | 2 | 3.221 | 0.07661 | 24.06 |
| `005-partial` | Rejected | 1 | 0.166 | 0.06947 | 24.11 |
| `006-uncut` | Rejected | 1 | 0.147 | 0.00000 | 24.13 |
| `007-half-step` | Pass | 2 | 4.187 | 0.15817 | 48.35 |
| `008-refined` | Pass | 2 | 2.863 | 0.06367 | 47.42 |

All five final records pass numerical accounting checks. Each full cut has mass fractions 0.5/0.5. Halving the timestep changes the peak material reaction from 0.07661 to 0.15817 N; force convergence is **not established**. The final batch uses 181–261 MiB peak cgroup memory. 8 invocations including development and the failed export consumed 307.37 s, within the frozen 36-invocation / 7,200 s budget (600 s each). Microkernel tests and repository delivery gates have separate accounting.

Attempt 001 completed dynamics but failed score serialization. Attempts 002–003 corrected the paper Eq. 17 FLIP expression, feedback accounting and relative sweep; they are superseded development records, retained with their original hashes. The final solver/scorer source is frozen across 004–008. Rendering is excluded from all costs above. These timings do not establish real-time performance.

[All attempt metrics, source hashes and failures](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-cut/evidence.json) · [Raw records, including development attempts](https://github.com/huangkiki/Dexlab/releases/download/v0.61.0/tofu-cut-evidence-v1.tar.gz).

The scorer reconstructs connectivity from the reference transfer graph, including unassigned bridges. It reads saved states and native observations without importing the solver. A partial cut and an uncut block must remain connected and fail the halving task. Short probes, absent observations, altered frozen thresholds and changed artifact hashes are rejected or cannot pass completion.

Spherical contact proxies permit finite overlap. The reconstructed display surface is an approximation, not a measurement of cut quality. A symmetric half cut does not establish quarter-cut accuracy, force agreement with real tofu, robustness to arbitrary paths or robot safety. Real tests would be needed to identify elasticity/friction/cutting resistance and then validate force and separated-mass ratios independently.

## Reproduce

Install the existing DexLab environment and the optional `cutting` dependencies, then use the repository's bounded execution and shared research guard. Each output directory must be new. Example from the repository root:

```bash
python -m pip install -e '.[cutting]'
CUT_ROOT=/path/on/mounted/data/tofu-test
mkdir -p "$CUT_ROOT"
python scripts/bounded_run.py --profile adaptive \
  --resource-plan "$CUT_ROOT/plan.json" --cpu-cores 4 --io-device /dev/sda \
  --data-dir "$CUT_ROOT" --timeout 600 --receipt "$CUT_ROOT/resources.json" -- \
  python scripts/research_guard.py run --lock /path/to/shared/window.lock \
  --kind qualification --receipt "$CUT_ROOT/window.json" -- \
  .venv/bin/python -m dexlab.tofu_cut --output "$CUT_ROOT/full"
.venv/bin/python -m dexlab.cutting_score "$CUT_ROOT/full"
```

Use the actual mounted device and existing shared guard path on the host. `--mode partial` and `--mode uncut` retain their negative task scores. `--dt 0.00025` and `--grid-spacing 0.006` select the recorded sensitivity cases. A successful runner exit means the record completed, not necessarily that the task passed; use `score.json` or the scorer's exit code for the task result. Replay is generated by `python -m dexlab.cutting_showcase RUN --output MEDIA` from the saved states, under a separate guarded postprocessing window.

Each run saves `manifest.json`, `states.npz`, `trace.npz` and `score.json`, with source/package versions and SHA-256 hashes. Resource receipts and the cumulative attempt ledger preserve failures and cost. [Source and experiment entry](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-cut) · [Implementation task #192](https://github.com/huangkiki/Dexlab/issues/192) · [Cutting discussion #191](https://github.com/huangkiki/Dexlab/discussions/191).
