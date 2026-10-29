# Single-cut banana force: sampling, sensitivity and 64× particles

This experiment reproduces the **published structure** of BladeMaster Fig. 9: a vertical knife cut through a banana, shown as one sampling, the pointwise mean of 20 different particle samplings, and a refined run with one-quarter grid spacing and 64 times as many particles. The authors do not publish the raw robot-force trace, banana geometry, base grid, sampling distribution, complete end-effector trajectory or contact scales. These results therefore assess numerical integrity, dispersion and sensitivity of the frozen DexLab model; they are not an author-code or real-banana accuracy reproduction.

![Banana single-cut forces, channel accounting and sensitivity](../../../docs/evidence/cutting/banana-force/force-protocol.svg)

## Findings first

| Check | Qualified result |
| --- | ---: |
| 20 samplings: individual pre-support material peak | **0.8469 ± 0.1511 N** |
| Pointwise mean of 20 curves: pre-support peak | **0.6661 N** |
| Maximum pointwise standard deviation before support | **0.2767 N** |
| Pre-support material impulse | **0.07341 ± 0.01249 N·s** |
| 64× particles: material peak over the complete trajectory | **4.3059 N** |
| 64× particles: material impulse over the complete trajectory | **0.60183 N·s** |
| 64× curve vs 20-run mean, normalized RMSE | **2.051** |
| Frozen 64× acceptance | **Failed: no support contact within 0.5 s** |

All 20 samplings pass force-channel identity, momentum balance, positive-Jacobian, material-before-support, support-contact and cut-progress checks. One-factor sensitivity around `dt=0.125 ms` remains substantial: the pre-support normalized RMSE against seed 0 is **0.621, 0.219, 0.153 and 0.387** for `dt/2`, `dt×2`, normal scale `/2` and normal scale `×2`. The 64× run also passes finite-state, momentum, positive-Jacobian, material-contact and cut-progress checks, but fails the frozen support-contact requirement. Baseline accounting qualifies and refinement is a negative result; robust timestep, contact and particle-refinement convergence are unestablished. It cannot support a real-force accuracy claim.

## Force accounting

| Channel | Definition and use |
| --- | --- |
| Material resistance | Material reaction on the knife along `+z`; used for the material-only epoch. |
| Rigid-support resistance | Knife–board impulse divided by the timestep; the late peaks in paper Fig. 9 also include this channel. |
| Total resistance | Material resistance + rigid-support resistance. |
| Actuator | PD drive input, recorded separately and excluded from resistance. Guide torque is separate too. |

Large peaks beginning around `0.445 s` are rigid-support contact, not banana material strength. The figure's second panel uses a symmetric log scale so the roughly 1 N material response remains visible beside support peaks of tens of newtons.

## Matched fields and independent choices

The published values are used directly: E=0.4 MPa, ν=0.45, ρ=1,100 kg/m³, 30 kPa yield stress, 0.1 kg knife, friction 0.2, Gc=700 J/m² and sharpness 0.9. The 20 distinct samplings, quarter grid spacing and exact 64× particle count are also acceptance requirements.

DexLab independently chooses an authored curved banana (120 × 60 × 30 mm bounding size), stratified jitter sampling, 7.5 mm base grid, 0.125 ms base timestep, a vertical PD trajectory for a translating knife and contact scales. Plasticity uses an independent perfect-J2 radial return in principal logarithmic strain because the paper does not publish its projection. The knife remains a guided translating rigid body rather than the paper's full six-degree-of-freedom rigid-tool interface.

The cutting-band half-width follows the published `6Δx`. The paper does not publish the particle contact-radius scale `s_R`, cut-band rear/lead extents, minimum cut-advance speed, or the exact exclusion distance for intact reference neighbors. Source frozen before these runs fixes them at `s_R=1`, `b_back=2Δx`, `b_lead=2R_p`, `u_min=0` and a `2Δx` neighbor threshold, and the source hash binds those choices. The frozen JSON did not enumerate them separately, however, and this study does not sweep them. That remains a protocol boundary rather than an alignment claim.

The displayed surface still rebuilds planar seams from recorded blade paths. It does not implement the linked-volume, Hermite-data and local dual-contouring method in paper III-F. Mechanical outcomes, visible surface quality and real calibration remain separate claims.

## Reproduction

The frozen protocol and public result are [`demos/banana-force/force-protocol.json`](https://github.com/huangkiki/Dexlab/blob/main/demos/banana-force/force-protocol.json) and [`demos/banana-force/evidence.json`](https://github.com/huangkiki/Dexlab/blob/main/demos/banana-force/evidence.json). Qualified execution requires effective cgroup CPU, memory, zero-swap, task, runtime and I/O limits. Raw `runs/` traces stay in local experiment storage instead of Git.

```bash
python -m dexlab.banana_force --output <run-dir> --suite baseline
python -m dexlab.banana_force --output <run-dir> --suite sensitivity
python -m dexlab.banana_force --output <run-dir> --suite refined --segment-wall-s 3300
python scripts/build_banana_force_report.py \
  --baseline <baseline-dir> --sensitivity <sensitivity-dir> --refined <refined-dir> \
  --receipt <bounded-receipt> --evidence demos/banana-force/evidence.json \
  --figure docs/evidence/cutting/banana-force/force-protocol.svg
```

[Material and plasticity details](cutting-fidelity.md) · [Historical three-cut banana replay](banana-cutting.md) · [Continuous cutting and blade pushing](cut-push.md) · [BladeMaster paper](https://arxiv.org/html/2609.27342v2#S4.SS3)
