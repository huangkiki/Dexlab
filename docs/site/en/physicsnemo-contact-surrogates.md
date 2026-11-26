# PhysicsNeMo: does accurate position prediction get contact events right?

In the [existing Wuji offline diagnostic](contact-response.md), constant velocity gave a 100 ms position RMSE of just **0.018–0.023 mm** in three qualified-grasp episodes. Yet both contact-persistence baselines missed every recorded contact-loss window during release or unloading. An object can barely move even after one finger unloads. To predict that transition, a model needs to see the action and be tested on which finger loses contact and when. Overlapping windows from an episode are not independent repeats.

NVIDIA PhysicsNeMo is a PyTorch toolkit for training physical surrogates: predictors scoped to particular simulation outputs, not a general-purpose physics engine. Two examples separate giving the model the right inputs from testing it on the right outputs.

## Show the model the conditions that change the answer

The same airfoil at different angles of attack has the same shape but different flow and pressure. `DomainMesh` keeps the mesh, named boundaries, and case conditions together. Transolver, GeoTransolver, and GLOBE can draw different inputs from the same stored DrivAerML data without each storing its own preprocessed arrays. The library checks structure; it cannot know whether physical boundary conditions and units are complete. [Paper §§3 and 5](https://arxiv.org/html/2610.39072v1#S3) · [Pinned implementation](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/mesh/domain_mesh.py)

In the authors’ **synthetic heat-conduction comparison**, wall temperature and flux vary. Across three backbones and the same 200 held-out geometries, relative error was **86.6%** with geometry alone, **42.5–45.7%** with global summaries, and **5.5–9.4%** with conditions attached to individual boundaries (variation σ=1, medians over eight seeds). That is a comparison of what the model knows, not an accuracy gain from a storage format. [Table 6 and protocol](https://arxiv.org/html/2610.39072v1#A2.T6)

Back to the ball: from the same starting pose, continuing to hold and unloading the index finger should be different inputs rather than two answers expected from one action-blind model. The subsequent contact readback belongs to the scorer, not the predictor.

## Measure contact separately, and measure what the probe misses

DeFormer predicts deformation from the initial vehicle shell, thickness, and query time. A graph corrector then uses local node-to-facet pairs found on the **predicted shape** to predict position corrections, with the first network frozen. It does not advance one frame from the previous one or establish reliable contact forces. The Yaris recipe also applies a separate wall clamp at evaluation. [Official recipe](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#deformer-recipes-data-preparation-training-and-evaluation) · [Pinned corrector](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/experimental/models/deformer/corrector.py)

NVIDIA reports that correction took whole-vehicle position RMSE from **7.6 to 7.5 mm**. Across 20 validation designs, additional shell crossings counted in node-frames changed from **61,930 to 9,091** with the narrow search, and **75,342 to 15,111** with the deeper sweep. The reduction was about 6.8-fold under one probe and 5.0-fold under the other. After a node passes far enough through a shell, the narrow search no longer pairs it with that facet. This identifies a failure in **search coverage**, not the model-side cause of the crossing. The metric is relative to the reference solution, which also contains crossings. Node-frames are not independent impacts. [Evaluation definition and search limit](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#evaluate)

In a grasp, record “the finger’s normal load fell below threshold” separately from “the two surfaces separated.” The former is the native contact-event definition; the latter requires independent geometry evidence. A missing candidate pair is not a measured positive gap.

## What should DexLab test first?

Keep native simulation and independent scoring. Once [#261](https://github.com/huangkiki/Dexlab/issues/261) has compatible inputs and qualified native repeats, branch the same prefix into hold and index unload. Compare a simple action-aware baseline first. Only then ask whether a local corrector prevents additional per-finger misses on held-out whole episodes without inventing contact in free space. Report event timing, pose, probe coverage, and end-to-end cost together. If the event gains do not exceed repeat variability, do not upgrade the model.

This is a proposal based on the paper, NVIDIA’s crash recipe, and existing DexLab offline records. The NVIDIA crash results were not reproduced here, and DexLab has not trained a new model, replaced a solver, or verified a hardware gain. [Discussion #425](https://github.com/huangkiki/Dexlab/discussions/425)
