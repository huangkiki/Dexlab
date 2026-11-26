# PhysicsNeMo: does accurate position prediction get contact events right?

> **At a Glance**
>
> | Field | Details |
> | --- | --- |
> | **Works Covered** | 1. *PhysicsNeMo-Mesh: GPU-Native Meshes and Simulation Cases for Physics AI* (NVIDIA, [arXiv:2610.39072v1](https://arxiv.org/abs/2610.39072v1), 2026-10-29)<br>2. Separate official recipe: [PhysicsNeMo 26.11 DeFormer Crash Corrector](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#deformer-recipes-data-preparation-training-and-evaluation) (non-paper evidence, kept distinct) |
> | **Pinned Sources** | Paper baseline [`a0de974`](https://github.com/NVIDIA/physicsnemo/tree/a0de974ed18599c10a4ffaecaaa8819cbb29dc30) · `v2.3.0` [`domain_mesh.py`](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/mesh/domain_mesh.py) · [`corrector.py`](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/experimental/models/deformer/corrector.py) |
> | **Core Problem** | Conventional physics-AI pipelines pre-bake solver outputs into model-specific flat arrays—creating I/O bottlenecks and stripping out solution-determining boundary conditions and physical field types—while global position RMSE hides local shell penetrations and contact misses. |
> | **Core Approach** | PhysicsNeMo-Mesh stores complete GPU-native simulation cases (`Mesh[n,m]` + `DomainMesh`) and derives model features on demand; DeFormer freezes a deformation backbone and adds a local node-to-facet graph corrector on the predicted shell. |
> | **Open-Source Status** | Library, aerospace, and crash recipes are public; paper benchmark scripts are noted as available upon request from the authors. |
> | **DexLab Verdict** | **`pilot` (borrow the data contract and contact-probe diagnostics; do not replace simulators)** — fix missing action conditions and contact-probe blind spots before considering learned correctors. |

---

## 1. What These Two Works Actually Do

NVIDIA PhysicsNeMo is a PyTorch toolkit for training **physical surrogate models**—predictors scoped to specific simulation outputs, not a general-purpose physics engine. Below we unpack both the **PhysicsNeMo-Mesh** paper and the separate **DeFormer** crash recipe before connecting them to DexLab.

### Problem Setup & I/O

- **Pipeline bottleneck**: CFD and structural solvers produce multi-million-element surface or volume meshes. Traditional ML pipelines flatten each run into static, model-specific arrays offline, losing named boundaries and physical tensor types. Switching model architectures requires re-running preprocessing, and whenever two cases share the same geometry under different boundary conditions, a geometry-only surrogate cannot distinguish their solutions.
- **PhysicsNeMo-Mesh I/O**:
  - **Inputs**: raw solver vertex/cell connectivity, fields attached to named boundaries (inlet flow, wall temperature/flux), and global case parameters (reference freestream velocity, Reynolds number).
  - **Outputs**: PyTorch/GPU-ready named tensor objects plus on-demand model features (normals, areas, sampled surface points, SDFs) tailored to architectures such as Transolver, GeoTransolver, and GLOBE.

### Four Core Modules of PhysicsNeMo-Mesh

1. **Unified simplex mesh `Mesh[n,m]` (§2)**: decouples spatial dimension $m$ from cell simplex dimension $n$ (each cell has $n+1$ vertices, so points, edges, triangles, and tetrahedra share uniform rectangular connectivity arrays). Fields attach to points, cells, or the full mesh with trailing shapes $()$, $(3,)$, and $(3,3)$. Tradeoff: hexahedra must be split into 5–6 tetrahedra (falling back to cell centers or dual graphs loses local geometry).
2. **Self-contained case container `DomainMesh` (§3)**: packs domain interior, **named boundaries** with their boundary conditions, and global case metadata into one memory-mapped object. The library validates tensor structure and indexing, but cannot verify physical completeness or unit consistency.
3. **Pipeline inversion — on-demand feature derivation (§4–5)**: store the physics-preserving case once, memory-map only needed tensors, and derive normals, curvature, or SDFs on GPU at training time. In the DrivAerML surface recipes, Transolver, GeoTransolver, and GLOBE all pull different inputs from the same `DomainMesh` archive without storing duplicate preprocessed datasets.
4. **Physical field types `FieldSchema` and frame transforms (§6)**: tracks tensor rank and parity (scalars, polar vectors, pseudovectors, normals). Rotating a coordinate frame rotates mesh, velocity field, and reference velocity together (preserving angle of attack), whereas rotating only the airfoil changes the physical case. Units are not enforced, and this GLOBE implementation accepts only scalars and polar vectors.

![Figure 2: AirfRANS DomainMesh case structure](https://arxiv.org/html/2610.39072v1/domainmesh_case.png)

*Figure 1 (from [Paper Figure 2](https://arxiv.org/html/2610.39072v1#S3.F2)): `DomainMesh` keeps the interior domain, named boundaries (airfoil, farfield), and global reference quantities together instead of flattening them into untyped feature columns.*

### Core Mechanism & Load-Bearing Equation: Why Missing Conditions Cap Any Backbone

In Appendix B, the authors construct a 2D steady mixed-boundary heat-conduction problem ($\Delta T = 0$, prescribed Dirichlet temperature on one wall arc and normal flux on another), decomposing temperature into a nominal harmonic field plus random boundary variation: $T = u_{\mathrm{nom}} + \sigma u_{\mathrm{var}}$, with $\sigma \in \{0, 0.1, 0.25, 0.5, 1, 2\}$.

For any predictor $v(g)$ that observes only geometry and query locations $g$, the prediction cannot vary with the random boundary coefficients $c$, yielding an irreducible **conditional risk lower bound** (Appendix B.3):

$$
\mathbb{E}[\mathrm{rel}\text{-}L_{2}(v)\mid g]
\ge R_{\sigma}(g)=\min_{v}\,\mathbb{E}_{c}\!\left[
\frac{\left\lVert u_{\mathrm{nom}}+\sigma Vc-v\right\rVert_{2}}
     {\left\lVert u_{\mathrm{nom}}+\sigma Vc\right\rVert_{2}}
\right]
$$

- $g$: geometry and interior query coordinates;
- $u_{\mathrm{nom}}$: nominal harmonic temperature field determined by the baseline wall profile;
- $V$: query evaluations of 17 harmonic basis modes (constant plus $\operatorname{Re}z^k, \operatorname{Im}z^k$ for $k \le 8$);
- $c$: random boundary coefficients independent of $g$, scaled by variation strength $\sigma$;
- **Intuition**: like pouring hot water into one mug and cold water into an identical mug while showing the model only the mug shape—no larger backbone can break through the geometric-median error floor fixed by $\sigma$.

![Figure 7: Boundary-condition dose response](https://arxiv.org/html/2610.39072v1/bc_dose_response.svg)

*Figure 2 (from [Paper Figure 7](https://arxiv.org/html/2610.39072v1#S5.F7)): as boundary variation $\sigma$ grows, all three backbones with geometry-only inputs hug the conditional risk lower bound (86.6% at $\sigma=1$); attaching per-boundary conditions cuts error to 5.5–9.4%.*

### Separate Official Recipe: How the DeFormer Local Corrector Works

In the NVIDIA 26.11 structural crash recipe, **DeFormer** tackles thin-shell crash deformation in two stages:

1. **Direct time-queried deformation backbone**: takes the initial vehicle shell, shell thickness, and query time $t$ to predict deformed nodal coordinates directly (it does **not** roll forward frame by frame and does not produce reliable contact forces).
2. **Frozen backbone + local graph corrector**: finds candidate node-to-facet pairs within a search band on the **predicted** deformed shell and applies a graph neural network to predict local position corrections that reduce shell self-crossings. At evaluation time, the Yaris recipe also applies an independent wall clamp.

### Main Experiments, Results, and Built-in Counterexamples

| Experiment / Source | Setup & Budget | Key Numbers (Author-Reported) | What This Proves / Counterexample |
| --- | --- | --- | --- |
| **Cold-read I/O** (Paper Table 2) | Local NVMe, median of 3 cold reads | DrivAerML: 388.7 → **4.44 s** (88×); HiLiftAeroML matched fields: 113.7 → **14.23 s** (8×); car boundary only: 5.2 → **0.70 s** | Memory mapping and selective field loading cut I/O sharply; the 88× headline includes extra fields read by VTK |
| **GPU geometry ops** (Paper Tables 1/3/4) | GB200 vs 72-thread Grace CPU, 17.68M-tri car, best timing | Median **198×** across 18 surface ops; **counterexample: field interpolation with cached locators is 0.96×** | Large standalone geometry ops benefit hugely on GPU, but not every op speeds up |
| **Online preprocessing overlap** (Paper Table 5) | 8.8M-tri synthetic mesh across step sizes | 127 ms step costs **2.1%** throughput; **counterexample: 23 ms step costs 35.1% pipelined** (worse than 28.9% serial) | Heavy steps hide preprocessing; **short-step models stall on host-launch contention—do not blindly copy CFD prefetching** |
| **Mixed-BC heat conduction** (Paper Table 6) | 4,000 train / 200 held-out shapes, 3 backbones × 3 inputs × 6 $\sigma$ × 8 seeds (432 GB300 runs, fp32 no TF32) | $\sigma=1$ median rel-$L_2$: geometry-only **86.6%** → 5-D global summary **42.5–45.7%** → per-boundary BCs **5.5–9.4%**; at $\sigma=2$, Transolver seed spread widens to **7.9–19.4%** | **Missing boundary inputs dominate error**; report seed spread, not medians alone, under strong variation |
| **DeFormer crash corrector** (26.11 recipe) | Yaris 20 validation designs, 5 mm vs 15 mm search band | Whole-car RMSE: **7.6 → 7.5 mm**; additional crossings **61,930 → 9,091** node-frames at 5 mm (~6.8×) vs **75,342 → 15,111** at 15 mm (~5.0×) | Global RMSE barely moves (0.1 mm) despite tens of thousands of penetrations; **a narrow probe misses deep crossings** |

---

## 2. Counterexamples, Hidden Switches, and Evidence Boundaries

1. **Storage format does not buy accuracy—and small models hit a throughput reversal**: the 86.6% → 5.5% drop comes from giving the model boundary conditions, not from switching containers. Meanwhile, Table 5 directly shows that at ~23 ms training steps, online GPU preprocessing degrades throughput more than serial execution (35.1% vs 28.9%).
2. **Smooth operator differentiability ≠ contact-dynamics gradients**: §5.1 verifies integrated surface-pressure forces via central differences ($4.0\times 10^{-7}$ relative error), which validates that smooth operator path only—not gradients across contact switching or changing neighborhoods.
3. **Three DeFormer limits that matter for manipulation**:
   - Direct time queries do not step dynamics forward and do not supply contact forces or friction;
   - The Yaris recipe applies an evaluation-time wall clamp separately from the neural corrector;
   - Widening the search band from 5 mm to 15 mm shrinks the reported reduction from ~6.8× to ~5.0×, proving that **nodes passing far through a thin shell escape narrow candidate matching**—a probe-coverage blind spot. Reference solutions also contain crossings, and node-frames are not independent impact counts.

---

## 3. What DexLab Should Borrow & First Minimal Validation Slice

In DexLab's [existing Wuji offline diagnostic](contact-response.md), constant-velocity prediction achieved **0.018–0.023 mm** 100 ms position RMSE across three qualified-grasp episodes, yet both contact-persistence baselines missed **every** recorded contact-loss window during release or unloading. An object can barely move after one finger unloads. PhysicsNeMo cleanly splits what is missing into **giving the model the right action inputs** and **measuring contact probes together with their blind spots**.

- **Adopt directly**:
  1. **Action-conditioned case contract**: from the same grasp prefix, “keep holding” and “unload index finger” must be distinct inputs. Keep prefix state, last completed observation, action sequence, frame/units/model version strictly separate from future per-finger contact labels; never feed scorer readbacks back into the predictor.
  2. **Separate contact-load vs geometric-gap diagnostics**: log “finger normal load dropped below threshold” (native contact event) separately from “surfaces separated” (independent geometry check). Zero candidate pairs within a search radius cannot be treated as a measured positive gap.
- **Validate after adaptation**:
  - Only after a simple action-aware baseline is in place, test whether a local contact corrector reduces held-out whole-episode per-finger misses without inventing spurious contact in free space.
- **Defer or reject**:
  - Do not replace native physics engines or independent scorers with PhysicsNeMo surrogates;
  - Do not copy 8.8M-triangle CFD online prefetching into small contact models (contradicted by Table 5 at 23 ms steps);
  - Do not treat a time-queried displacement corrector as a contact-force or friction solver.

### First Minimal Falsifiable Slice

- **Question**: when branching an identical qualified grasp prefix into hold vs index-finger unload, does a simple action-aware baseline catch per-finger contact-loss windows, and does a local corrector add signal beyond repeat variability?
- **Controlled comparison**: once [#261](https://github.com/huangkiki/Dexlab/issues/261) has compatible inputs and qualified native repeats, split train/held-out by **whole episodes and conditions** (overlapping windows inside one episode are not independent repeats). Keep native simulation and independent scoring, and report event timing error, pose RMSE, probe coverage across search radii, and end-to-end cost together.
- **Pass / stop criteria**: stop and avoid more complex surrogate architectures if the simple action-aware baseline already closes the event-recall gap, or if a local corrector fails to beat repeat variability without raising free-space false positives.

---

## 4. Verifiable Sources & Inspection Scope

- Paper: [PhysicsNeMo-Mesh (arXiv:2610.39072v1)](https://arxiv.org/abs/2610.39072v1) (full text and Appendices A/B)
- Pinned code: [Paper baseline `a0de974`](https://github.com/NVIDIA/physicsnemo/tree/a0de974ed18599c10a4ffaecaaa8819cbb29dc30) · [`v2.3.0 DomainMesh`](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/mesh/domain_mesh.py) · [`DeFormer corrector.py`](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/experimental/models/deformer/corrector.py)
- Separate crash recipe: [PhysicsNeMo 26.11 DeFormer Crash Recipe](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#deformer-recipes-data-preparation-training-and-evaluation) · [Evaluation definition & search limit](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#evaluate)
- Related discussion: [DexLab Discussion #425](https://github.com/huangkiki/Dexlab/discussions/425)
- **Inspection scope (2026-11-26)**: synthesized from arXiv `2610.39072v1`, static review of pinned source commits, the official NVIDIA 26.11 DeFormer recipe, and existing DexLab Wuji offline records. All PhysicsNeMo and DeFormer metrics are author-reported; no NVIDIA operator/crash benchmarks were re-run, and no new DexLab surrogates, solver replacements, or hardware experiments were executed.
