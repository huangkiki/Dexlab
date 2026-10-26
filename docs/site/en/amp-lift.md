# Public AMP lift: reference preparation

**This case tests whether the released G1 policy lifts its object through sustained hand contact. DexLab has prepared the inputs and recording/diagnostic entry points; no native AMP result is available yet.**

This case uses the public `Mjlab-G1-DualArm` checkpoint and Toaster003 model from [humanoid-amp-ppo at 4889389](https://github.com/shuayyy/humanoid-amp-ppo/tree/4889389118e0c88d3945dff54d2cd3f992ed815e). It is separate from that repository's SuperMimic/PPO-Sim tracking task, whose 1.5 kg box and unavailable tracking checkpoints cannot be substituted into this baseline.

## Established inputs and conditions

The checkpoint and two motion clips have fixed Git-blob identities and SHA-256 records. All 35 G1 meshes referenced by the task match official Unitree files. The six Toaster003 visual payloads match RoboCasa's archive; the AMP XML adds a free root, grasp markers and explicit inertials. Original motion-capture and checkpoint-training lineage is not independently established. External weights and assets are not bundled with DexLab.

| Condition | Public AMP reference |
| --- | --- |
| Model | Nominal inertial mass sum 1.30 kg; startup mass, COM and friction randomization retained |
| Initialization | Original reset ordering, including 25% reference-state starts and XY/yaw/joint randomization |
| Control | Released actor and clipping; play mode disables virtual PD and observation corruption |
| Clocks | 0.005 s physics, four substeps per action, 60 s horizon and original automatic reset |
| Source hold | One-sided height threshold and two marker flags for 0.4 s; flags do not prove loaded contact |
| Independent diagnostic | Every bilateral loaded-contact interval without ground/other support; 2 s window reported separately from task success |

The candidate uses official MuJoCo Warp 3.8.0.3 with the identical runtime subtree to the locked 3.8.0.2 commit, resolving mjlab's metadata constraint while retaining other source pins. Native compatibility and recorder parity remain unverified.

## Entry points and remaining acceptance

The [case README](https://github.com/huangkiki/Dexlab/blob/main/demos/amp-box-lift/README.md) documents input preparation, two fresh-process parity probes, three policy seeds and the paired no-hand-contact control. The ceiling is six native starts, 900 s per process and 5,400 s total, subject to input/runtime admission and a measured resource plan.

The selected GPU has a 20,480 MiB whole-device sampled stop threshold and at least 2,048 MiB reserve. Sampling every 2 s cannot establish an instantaneous peak or a hard allocation cap. The workload stops on overage or unavailable telemetry; final resource evidence remains required.

Offline fixtures test force decoding, terminal feedback, continuous carrying, ground/other support rejection, hand-relative motion, momentum jumps and negative-control mass mismatch. The report checks full record continuity and preserves hashes. Its momentum residuals include contacts and gravity; armature, generalized forces, other constraints and integration effects still need attribution. A carrying window leaves `task_success` unset.

Native trajectories, full physical qualification and continuous video remain in [#259](https://github.com/huangkiki/Dexlab/issues/259), together with the retained tracking and matched-comparison obligations. This preparation adds no completed task to the cross-engine coverage count.
