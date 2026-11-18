# Visual goal masks in DexLab: prove the progress signal before training GCRL

## TL;DR

**The transferable idea in Dynamic Object Masks is not another GCRL algorithm. It is treating target location as a per-step visual signal and auditing its monotonicity, occlusion behavior and detection errors before it enters a policy or reward.**

It may help DexLab separate visual approach, gripper alignment and physical contact. It cannot replace contact force, grasp success or hardware acceptance. The paper reports strong reaching and pick-up results, but simulation masks still come from privileged object positions and per-object size parameters, while real-world training still uses pre-recorded target positions to terminate episodes.

## Start with an apple-pick task

A UR10e must pick up an apple. If the reward only measures end-effector distance to the apple center, the policy can hover beside the apple: the distance is small, but the apple is not between the fingers.

Dynamic Object Masks appends a target mask to RGB. Ordinary approach uses full-image mask area; pick-up restricts it to the ROI between the fingers. Mask overlap rises only when the apple enters a graspable region. After both fingers touch, the mask is cleared and the reward switches to contact, lift and completion.

The mask is therefore neither only an object category nor a static goal image. It exposes target location, apparent scale and geometric relation to the gripper in one input. The ROI variant connects “target is visible” to “target is inside the grasp window.”

## The strongest evidence

In UR10e-MuJoCo pick-up, nine of eleven mask GC+reward seeds exceed `90%` over 50 trials per object; only two 3D position+distance seeds cross that threshold.

For visual reaching, the reported held-out average is `99.9%` for masks and `98.9%` for 3D position. That one-point difference supports “mask is a useful interface”; it is not enough by itself to establish a general mechanism advantage over privileged coordinates.

Mobile navigation gives a useful counterweight: masks learn faster but end below a policy that always receives the 3D target. A mask learner must first find the target and then approach it; once the target leaves view, privileged coordinates carry stronger information.

## Grounding DINO reveals the real test point

In Franka real-world learning from scratch, Detic reaches the target while Grounding DINO fails through false positives. The wrong box enters the mask, mask area enters the reward, and the policy optimizes the detector error.

In time order:

1. **Initial condition/action:** the wrist camera observes the scene and the policy commands joint velocities.
2. **State/reward evolution:** the detector emits a false target box and mask area is interpreted as progress.
3. **Failure:** the policy earns approach reward while the physical target is not approached.
4. **Task consequence:** real-world reaching fails.

The first failing layer is visual target generation and reward semantics, before SAC, contact solving or sim-to-real. The authors ran this real-robot case; this review performed static paper/source verification without rerunning it.

The paper does not report controlled sweeps over missing masks, flicker, partial occlusion and area jitter. The detector-quality bound is supported by a case, but which error types cause which downstream failure remains unmeasured.

## The precise boundary of “object-agnostic”

Simulation contains 20 known objects, with 15 for training and five held out. A privileged object center is projected into a rectangle and multiplied by pre-written width, height and offset parameters for each object. The held-out test supports instance generalization inside this class pool, not arbitrary unseen categories or geometry.

The authors also state that the mask provides an object-agnostic **reaching** skill, not fully goal-agnostic manipulation. For a cup handle, pan handle or scissor grip, a center box may not identify the correct contact region.

There is a second boundary: “the policy does not read 3D coordinates” is not “the experiment uses no privileged localization.” The public real-world code computes end-effector distance from a pre-recorded `target_pos` and ends the episode below `0.13 m`. The actor never sees that coordinate, but termination and acceptance do. Their uses must be recorded separately.

## How DexLab should borrow it

### Borrow directly

1. **Write a monotonicity contract for visual progress.** Record mask area, center error, ROI overlap, true distance and stage events in the same episode.
2. **Treat detector failure as its own layer.** Report misses, false boxes, delay, area jitter and occlusion separately instead of collapsing `detector error → reward error → policy failure` into “unstable training.”
3. **Separate actor inputs from acceptance truth.** Scoring may read reliable ground truth, but fields never exposed to the policy must be explicit.
4. **Keep stage criteria separate.** Approach, gripper alignment, contact, retention, lift and completion each need an independent readback.

### Adapt and verify

Start with one existing DexLab camera trajectory and freeze 20–30 stage points. Compute target projection center, full-image mask area and gripper ROI overlap, then inject 20–50% occlusion, one-frame misses, false boxes and 1–3-frame delay.

The minimum bar is not a larger reward. Failed stages must not rank ahead of successful stages after perturbation, and the first visual failure must remain identifiable. If the signal is not monotonic, repair the target representation. If it is monotonic but the policy still cannot grasp, inspect RL, contact and physics next.

### Defer

- do not treat mask-size reward as contact or grasp success;
- do not extrapolate `99.9%` reaching to arbitrary objects, cameras or manipulation skills;
- do not add a general detector stack from one grasp case;
- do not treat a rendered mask as physical-contact evidence.

## First testable question

**Under occlusion, missed detections, false boxes and delay, do target-mask area and ROI overlap still rank far-away, aligned and pre-contact stages correctly?**

This asks whether a visual signal used as reward is a reliable task-progress proxy. It needs neither GCRL training nor a new physics backend. Only after this passes should DexLab compare visual GCRL, goal-image conditioning and privileged-coordinate conditioning.

## Continue reading

- [Paper, arXiv v2](https://arxiv.org/abs/2510.06277v2)
- [Pinned official code](https://github.com/fahimfss/GCRL/tree/771cf5567ef656f941f0ace0e2881d38988fd94b)
- [DexLab Discussion #405](https://github.com/huangkiki/Dexlab/discussions/405)
- [Research intake #406](https://github.com/huangkiki/Dexlab/issues/406)

## Evidence scope

This page covers all five Figures, one Table and five equations in paper v2 and statically checks mask projection, ROI, rewards and real-world termination in the pinned source. All success rates and robot timings are author-reported. This review did not run RoboHive, MuJoCo, Isaac Sim, SAC, PPO, Detic, Grounding DINO or hardware, and it did not complete a new DexLab visual experiment.
