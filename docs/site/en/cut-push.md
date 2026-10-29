# Finish the last cut, then push with the blade

Two tofu cuts create three pieces; three banana cuts create four. After the last cut, the blade lifts just clear of the board, stays inside the kerf, pushes sideways, then withdraws. Every frame shows measured knife contact force and each material region’s x displacement from its initial position.

```{raw} html
<div class="cutting-showcase cut-push-showcase"><div class="cutting-showcase-grid"><section class="cutting-player" aria-label="Tofu: two cuts, then push"><header><h3>Tofu: two cuts, then push</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu-cut-push/surface-rtx.mp4" data-poster="_static/cutting/tofu-cut-push/surface-rtx-poster.png" aria-pressed="true">Surface · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu-cut-push/particles.mp4" data-poster="_static/cutting/tofu-cut-push/particles-poster.png" aria-pressed="false">Particles</button></div></header><video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu-cut-push/surface-rtx-poster.png"><source src="_static/cutting/tofu-cut-push/surface-rtx.mp4" type="video/mp4"></video></section><section class="cutting-player" aria-label="Banana: three cuts, then push"><header><h3>Banana: three cuts, then push</h3><div class="cutting-view-switch"><button type="button" data-cutting-view="surface" data-src="_static/cutting/banana-cut-push/surface-rtx.mp4" data-poster="_static/cutting/banana-cut-push/surface-rtx-poster.png" aria-pressed="true">Surface · RTX</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/banana-cut-push/particles.mp4" data-poster="_static/cutting/banana-cut-push/particles-poster.png" aria-pressed="false">Particles</button></div></header><video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/banana-cut-push/surface-rtx-poster.png"><source src="_static/cutting/banana-cut-push/surface-rtx.mp4" type="video/mp4"></video></section></div></div>
```

Force and displacement come from saved simulation states; no direct material velocity increment. Synthetic materials, without real-food calibration.

The surface views use RTX path tracing, soft area lights and material-attached flesh textures. The original particle views remain available through the switch. [Surface reconstruction and replay provenance](cutting-surface.md) describe the geometry repair; saved particles, blade motion, forces and task scores are unchanged.

## Reading the frame

The first row shows knife-on-material contact magnitude |F| and world Fx/Fz (N), excluding the drive and board support. The second shows each fixed material region’s centroid x displacement (mm), ordered left to right, relative to the initial state. Regions remain connected before cutting. Time is native physical time; GIF playback is uniformly slowed for readability.

Display displacement and acceptance displacement have separate baselines: acceptance starts at the end of the final cut (3.30 s for tofu, 5.30 s for banana), testing the active piece relative to the remaining pieces. Cutting compression does not count as successful side pushing.

## Motion and reference

Tofu uses a 90×30×30 mm block, 5 mm grid and 0.5 mm blade. Banana retains the curved synthetic geometry, 6 mm grid and 1 mm blade. The displayed tofu run uses 0.125 ms and banana uses 0.25 ms; the 0.25 ms tofu record remains the sensitivity baseline. Density is 1100 kg/m³, E=6 kPa and ν=0.35; these are synthetic rather than measured food properties.

The displayed tofu adds **Newtonian viscosity, η=5 Pa·s**, to fixed-corotated elastic stress. Banana retains the η=0 elastic baseline. The coefficient is a predeclared synthetic parameter, not fitted to food or video appearance. The default `--viscosity 0` retains the old path; this tofu showcase explicitly uses `--viscosity 5`.

With spatial velocity gradient `L=grad_X(v) F⁻¹` and symmetric rate `D=(L+Lᵀ)/2`, the viscous Cauchy stress is `σᵥ=2ηD`. Its first Piola form `Pᵥ=JσᵥF⁻ᵀ` is added to internal forces. This chooses zero second-viscosity coefficient, corresponding to bulk viscosity `2η/3`. The rate uses the current cut-compatible P2G velocity before this step's force impulses, with explicit integration. Separated cut histories do not exchange viscous forces.

[BladeMaster §III-B](https://arxiv.org/html/2609.27342v2) mentions optional Newtonian viscosity. This equation and η=5 are declared implementation choices here, not an author-provided tofu calibration. PIC/FLIP (FLIP fraction 0.95), tangential contact damping and knife-drive damping retain their existing settings and remain distinct from material viscosity.

Each step records `dt Σ V₀ Pᵥ:grad_X(v) = dt Σ 2ηV₀J D:D`. This is constitutive viscous dissipation, not total mechanical energy change including gravity, contact, drive and numerical transfer. Rigid translation and rotation have zero symmetric rate; material viscosity need not eliminate rigid rocking on the board.

After the last cut, the edge target rises from −4 mm to 2 mm over 0.20 s, staying inside the material; it moves sideways by 12 mm over 1.20 s, then withdraws to 36 mm over 0.60 s. Tofu is pushed left and recorded for 6 s; banana is pushed right and recorded for 8 s. These are drive targets; rendering uses the actual integrated knife pose. Cutting is disabled during pushing; the solver advances material positions and velocities.

## Tofu jitter check

After withdrawal, the left piece repeatedly reverses during 5.4–6.0 s while knife contact is zero. Halving the timestep from 0.25 ms to 0.125 ms reduces its centroid x peak-to-peak motion at 20 Hz display samples from **0.199 mm to 0.071 mm**. Native-particle second-difference RMS drops from **0.133 mm to 0.032 mm**. Surface and particle motion improve together; the earlier elastic showcase selected the latter run without smoothing frames, changing positions or adding material velocity.

Both complete records pass the original mechanical acceptance. Whole-worker time increases from **627.38 s to 1254.22 s**, including initialization, recording and scoring, rather than pure solver time. Initial gravity settling is retained; the material is not pre-equilibrated. Contact penalties and per-second transfer dissipation also change with timestep, so this is a sensitivity improvement, not convergence or calibrated tofu damping.

[Selection record](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/showcase-selection.json) · [Raw-array diagnostic](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/motion-sensitivity.json)

## Matched comparison after adding viscosity

<!-- viscosity-results:start -->
At fixed 0.125 ms, only η changes from 0 to 5 Pa·s. In the same 5.4–6.0 s post-withdrawal window, centroid x peak-to-peak motion is **0.0711 → 0.0384 mm**; native-particle second-difference RMS **0.0323 → 0.0140 mm** (decreases); excess reversing travel **0.1820 → 0.0713 mm**. No smoothing, omitted frames or modified native positions. Maximum knife contact in this window is **0 N**.

The displayed complete 6 s tofu run passes all 18 checks. Its matched-viscosity no-push control fails only the two expected motion/contact-impulse checks. Material, knife, external-input and viscous-dissipation arrays agree exactly through 3.30 s. Final piece x displacements from the last-cut baseline are **-11.096 / -0.137 / -0.053 mm**. Complete cases and the short probe are listed separately:

| Case | Result | η (Pa·s) | Δt (ms) | Relative dx (mm) | Knife impulse (N·s) | Viscous dissipation (J) | Worker (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `viscosity-001-probe` | Short probe, not acceptance | 5 | 0.250 | -0.000 | 0.000000 | 0.000161584 | 121.11 |
| `viscosity-002-tofu` | Pass | 5 | 0.250 | 10.905 | 0.095026 | 0.000170974 | 726.92 |
| `viscosity-003-tofu-half` (shown) | Pass | 5 | 0.125 | 11.001 | 0.092625 | 0.000135789 | 1445.54 |
| `viscosity-004-tofu-half-control` | Expected rejection | 5 | 0.125 | -0.240 | -0.001006 | 0.000133319 | 1449.93 |

18 zero-viscosity material-step comparisons are bitwise identical to the old implementation; offline scores for seven complete elastic records and two historical protocols are unchanged. Tests cover shear, volumetric rate, objectivity, rigid motion, momentum and discrete dissipation. A separate auditor reconstructs velocity gradients and constitutive dissipation from each record's saved states, and checks finite, nonnegative dissipation across all substeps.

Constitutive dissipation is not total system energy loss. These changes apply only to the declared synthetic model and window. Whole-worker costs include initialization/JIT, recording and scoring. Initial gravity settling is retained; this does not establish calibrated tofu damping, force convergence or contact-model accuracy.

[Viscosity protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-protocol.json) · [Evidence](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-evidence.json) · [Matched sensitivity](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/viscosity-sensitivity.json)
<!-- viscosity-results:end -->

## Retained elastic paired validation

Each material has nominal-step, half-step and no-lateral-push cases; the original half-step tofu has an additional no-lateral-push control at the same timestep. The control retains the same vertical motion and cutting, removing only lateral drive. Independent scoring checks the native transfer graph, progressive components, mass, positive Jacobian, overlap and complete momentum/external-impulse accounting. Directional knife impulse must be ≥0.001 N·s, active-piece relative displacement ≥1 mm, and other-piece |dx|≤3 mm, preserving the prior thresholds.

<!-- cut-push-results:start -->
| Case | Result | Δt (ms) | Pieces | Relative dx (mm) | Knife impulse (N·s) | Worker (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `physics-001-tofu` | Pass | 0.250 | 3 | 10.906 | 0.094646 | 627.38 |
| `physics-002-banana` (shown) | Pass | 0.250 | 4 | 10.209 | 0.021000 | 249.66 |
| `physics-003-tofu-half` (elastic baseline) | Pass | 0.125 | 3 | 11.043 | 0.091680 | 1254.22 |
| `physics-004-banana-half` | Pass | 0.125 | 4 | 10.629 | 0.020038 | 495.36 |
| `physics-005-tofu-control` | Expected rejection | 0.250 | 3 | -0.240 | -0.004750 | 634.95 |
| `physics-006-banana-control` | Expected rejection | 0.250 | 4 | -0.247 | -0.018299 | 249.55 |
| `physics-007-tofu-half-control` | Expected rejection | 0.125 | 3 | -0.236 | -0.002326 | 1248.61 |

Worker time includes initialization/JIT, recording and scoring, not just the solver. Each nominal/control pair is array-identical through the final cut; historical tofu rescoring is unchanged. Large raw NPZ files are retained and hashed. This PR provides compact evidence and reproduction commands, without a new data release.
<!-- cut-push-results:end -->

Half-step runs show timestep sensitivity, not convergence. Surfaces now use recorded-plane linked volumes, Hermite data and local dual vertices. This remains an offline CPU reconstruction limited to x/y straight cuts; coarse particle deformation can create small spikes, and visual topology cannot replace native connectivity/contact scoring. [Implementation and paper differences](cutting-surface.md). This is neither a six-native-engine cutting comparison nor a matched-author-configuration accuracy ranking ([#200](https://github.com/huangkiki/Dexlab/issues/200)).

## Reproduction and history

```bash
python -m dexlab.tofu_cut --task tofu-sequential --grid-spacing .005 --dt .000125 --viscosity 5 --motion-protocol cut-push --output TOFU
python -m dexlab.tofu_cut --task banana --motion-protocol cut-push --output BANANA
python -m dexlab.cutting_score TOFU
python -m dexlab.cutting_showcase TOFU --output TOFU_MEDIA
python scripts/render_cutting_studio.py TOFU TOFU_RTX
python scripts/render_cutting_studio.py BANANA BANANA_RTX
```

The optional RTX commands require the [studio render environment](studio-rendering.md#replay-a-rigid-scene), cutting dependencies and VTK. They read existing `manifest.json`, `states.npz` and `trace.npz`; output directories must be new. Add `--preview` for four saved frames.

Run under the [resource limits](cutting.md#reproduce). Use `--motion-protocol cut-no-push` for the control, retaining its matching positive case’s timestep and viscosity. Use `--viscosity 0 --dt .00025` for the retained elastic tofu baseline and `--dt .000125` for the banana half-step case. Historical `knife-push` (withdraw then re-enter) and `impulse` records retain their own protocols.

[Protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/protocol.json) · [Evidence](https://github.com/huangkiki/Dexlab/blob/main/demos/cut-push/evidence.json) · [Historical tofu](tofu-comparison.md) · [Historical banana](banana-cutting.md)
