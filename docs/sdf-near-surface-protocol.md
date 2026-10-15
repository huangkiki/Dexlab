# Static near-surface SDF query protocol

[English](sdf-near-surface-protocol.md) | [简体中文](sdf-near-surface-protocol.zh-CN.md)

This is a prospective implementation slice of [#178](https://github.com/huangkiki/Dexlab/issues/178). The repository supplies analytic queries, offline metrics, conservative domain classification and a capture-order helper. **Native execution and its complete executor are not qualified.** The historical 729-point report and grasp results retain their original scope and identity.

## Question and fixed inputs

Measure the observed distance field around a known box under explicitly separated automatic and precomputed SDF construction paths. Report discrepancies and missing coverage; do not assume either path is exact, equivalent or superior. This is a synthetic representation study, not material calibration, contact-solver attribution or apple-stem accuracy.

The box dimensions are 40 × 30 × 20 mm, with translation `[0.1, 0.2, 0.3]` m and a 0.7 rad rotation about z. Use the closed outward-oriented source mesh, record its exact vertices/connectivity and hashes, and bind them before native creation. Source geometry checks do not observe a cooked SDF.

`dexlab.sdf_near_surface.query_cohort` fixes the ordering and coordinates: each of six faces has a 3 × 3 tangential lattice at −1/2, 0 and 1/2 of the corresponding half-extents, with normal offsets −0.4, −0.1, 0, +0.1 and +0.4 mm. Its 270 centers comprise 108 internal, 54 surface and 108 external centers. Three central-difference steps, 20/10/5 µm along each local axis, add 4,860 samples: **5,130 queries in every case**. Those three difference steps are not spatial refinement levels or native contact normals.

## Concrete first case list

Each row is one static actor and one distance-query invocation. Run coarse levels before finer ones, preserving the same source geometry and all query coordinates. `auto` creates a triangle mesh with native automatic SDF construction; `baked` uses the official model-baking path and then creates an actor from that separately identified model.

| Case | Construction | Requested spacing on each axis |
| --- | --- | --- |
| `box-auto-2000um` | automatic | 2 mm |
| `box-baked-2000um` | precomputed model | 2 mm |
| `box-auto-1000um` | automatic | 1 mm |
| `box-baked-1000um` | precomputed model | 1 mm |
| `box-auto-500um` | automatic | 0.5 mm |
| `box-baked-500um` | precomputed model | 0.5 mm |

These six proposed invocations are within the Issue's initial 24-invocation ceiling; they do not allocate the remaining calls or authorize retries/contact experiments. Each remains subject to the 30-minute maximum, one admitted worker and a smaller measured finite run budget. Before starting, commit this concrete protocol, qualify official runtime/asset identities, record every actual admission invocation, and freeze the case budgets plus aggregate wall budget from measured evidence. If admission requires a native invocation, name and count it explicitly; it is not a free extra run. No new execution is enabled by the documentation alone.

## Required capture and domain evidence

Before observing distances, bind the approved source/runtime and API identity, actual actor/collider, actual root pose, actor-local AABB and native reference mesh. Require an actual root transform, SDF collider, correct actor identity and the frozen source geometry/frame. Save the complete queries, masks and pre-query hashes. After the single query, recheck identity and the hashes; retain raw arrays and failure stage even for partial results or exceptions. The capture helper implements ordering and record checks; a test double implementing these methods is not proof of native provenance.

The pinned public API describes an actor-bounding-box distance guarantee and an outside-box upper bound. The initial automatic-path mask therefore uses the strict interior of the actual local AABB, with a declared coordinatewise guard. The candidate's `1e-12 m` guard is an arithmetic convention requiring native applicability review, not an accuracy threshold or a certified error bound. AABB membership does not classify material interior. Do not choose masks from distance errors.

For the precomputed path, archive the baking output's dimensions, values, bounds, negative-value bounds, grid transforms, requested parameters and hashes. State that these are observations of the baking output; they are not a readback of the automatic actor's hidden grid or proof of the instantiated actor's internal identity. Domain expansion requires its own source/runtime-bound justification and native identity checks before outcomes; this protocol does not silently expand it.

Retain every boundary/unsupported point in the denominator. On the synthetic box, the current conservative mask supports 2,214 queries and leaves 2,916 unavailable. Only 108/270 centers have complete stencils at each difference step; surface/exterior center metrics remain unavailable. The first native slice must report its actual masks. This gap remains unfinished near-surface qualification, even if all supported points have small errors.

## Metrics, negatives and interpretation

Report absolute/RMS/signed distance error separately for internal and external centers, surface residuals, sign mismatches and missing counts. Report finite-difference direction-angle and gradient-norm errors for every difference step, with zero/undefined directions and original denominators. Keep per-center angles. Analytic normals are undefined on ambiguous sharp features; no arbitrary normal is selected. Real numeric inputs are required; complex, string or Boolean arrays must not be silently coerced.

Retain all construction/refinement outcomes, requested versus observed spatial scales, native/readback/recording/scoring costs, resource terminal receipts and failures. Requested spacing does not prove effective cell spacing, and an unobserved automatic grid cannot establish three observed refinement levels. No monotonic convergence or numerical accuracy threshold is assumed.

The offline negative suite covers invalid geometry/frame/values, reversed signs/directions, missing stencils, identity changes, partial calls and modified pre-query artifacts. Actual native object/runtime/API provenance and compatibility remain separate acceptance. Repository delivery also needs the complete applicable engineering gate and both documentation languages.

The six-engine/profile applicability matrix, apple/stem and finger assets, contact-search coverage, normal loading/unloading, tangential onset/slip and full grasp transfer remain in #178. Other engines are pending appropriate API/representation qualification; they are not relabeled unsupported. The six static cases cannot close those obligations or establish real-system accuracy.
