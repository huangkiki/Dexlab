(raisim-bumi-mimic)=
# RaiSim as a Bumi BlinkMimic2 training backend

**Question: can the existing BlinkMimic2 actor, world model and replay trainer run its physical transition collection on RaiSim without changing the learning algorithm?** This first slice implements that boundary on six LAFAN clips and a frozen Bumi checkpoint. It is not a 40-clip qualification, a randomized robustness suite or a real-robot result.

The useful engineering result is narrower than “RaiSim trains better.” The adapter must preserve Bumi's 21-joint order, floating base, actuator gains and limits, rotor inertia, 20 ms policy period, 5 ms physics substeps, reference goal, contact observations and terminal ordering. A first implementation exposed one such contract error immediately: the vendor URDF's `velocity="0"` was interpreted by current RaiSim as a true zero-velocity lock, so the policy could change joint targets while the joints stayed fixed.

## Frozen protocol

| Field | Frozen value |
| --- | --- |
| Policy | BlinkMimic2 warm start from the complete local checkpoint |
| Algorithm schema | `blink2-k8-h32-startup-objective-v6` |
| Bumi source | `2454535c967cd1d6f04dfe0f0289f3c6c608e596` |
| RaiSim | 2.16.0, FP64 CPU physics |
| Environments | 512 independent worlds, 16 worker threads |
| Timing | 5 ms physics substep, 4 substeps per 20 ms policy step |
| Budget | 2 hours or 5,000 additional updates |
| Clips | walk, run, jump, dance, fall-and-get-up, fight |
| Evaluation | One nominal closed-loop episode per clip |

The six-clip archive is a deterministic view over the frozen LAFAN40 manifest `604554646ef99f390dcd88fef06bc98bbbb6ffbbd9722f0b97d01203d75afbdf`. It preserves the original joint/body order, starts, ends and frame data.

The full checkpoint is used as a **warm start**, not an exact resume. Actor, critic, dynamics and compatible optimizer state are restored. Replay, sampler, episode IDs and actuator history are rebuilt because their source physics changed. The report therefore cannot attribute later changes to one optimizer state transition.

## Implementation boundary

The native library owns one `raisim::World` per environment and batch reset, step, full-state, body-pose, contact-impulse and clock readback. Python retains the existing BlinkMimic2 reference loader, actor, world model, policy learner, rewards, replay and update sequence.

The Bumi adapter restores values omitted or encoded unusually by the URDF: PD gains, effort limits, rotor inertia and per-joint velocity limits. Contact forces are native contact impulses divided by the physics timestep. Non-foot contacts and body errors remain observable.

## Closed-loop results

| Checkpoint | Completed | Mean body position error | Observation |
| --- | ---: | ---: | --- |
| Frozen MuJoCo checkpoint on RaiSim | 5/6 | 0.0584 m | Fall/get-up fails early; five other clips complete |
| RaiSim update 10,500 | 4/6 | 0.0376 m | Error falls, but fight and fall/get-up fail |
| RaiSim update 11,500 | 2/6 | 0.0589 m | Walk and run also regress |
| RaiSim update 12,000 | 1/6 | 0.0433 m | Only walk completes; lower mean error comes from earlier failure |
| RaiSim update 15,000 / final averaged | 0/6 | 0.0399 m | All six fail before completion |
| RaiSim update 15,000 / online actor | 0/6 | 0.0373 m | The regression is not caused only by last-five averaging |

Completion and tracking error answer different questions. A lower average body error over shorter surviving trajectories is not a better task result. The final report retains both and never drops an early failure from the denominator.

The training loop itself completed without a crash or non-finite physical transition: 5,000 additional updates, 6,432,768 collected environment steps and 2,447.66 s wall time. The negative task result is therefore **not an infrastructure failure**. It shows that continuing the actor/world-model updates on this new transition distribution made the closed-loop policy less reliable.

## First failing layer: fall-and-get-up

The frozen MuJoCo checkpoint, evaluated without reset noise in RaiSim, first fails `fallAndGetUp1_subject4` at control step 31:

| Step | State/evidence | Consequence |
| ---: | --- | --- |
| 1 | Reference pose loaded; contacts present | Initial state is finite and matches the frozen archive |
| 4 | Anchor orientation error crosses 0.4 rad; peak contact force about 86 N | Orientation is already diverging before translation |
| 7 | Anchor horizontal error crosses 0.125 m; peak contact about 411 N | Support response and body orientation are coupled |
| 16 | Anchor height error crosses 0.125 m; peak contact about 1,460 N | Vertical support is lost |
| 17 | End-effector height error crosses 0.2 m | The body is no longer near the reference support manifold |
| 31 | Orientation 1.10 rad, horizontal error 0.87 m, base height 0.335 m | Existing 0.8-rad orientation gate terminates the episode |

The supported chain is **reference low-pose reset → large policy target change → orientation divergence → root-height loss → termination**. The decisive early signal is orientation, before the final fall. The present six-clip run does not isolate whether actuator response, ground contact, reset penetration or policy sensitivity is the primary cause; those require a fixed-state contact/action ablation.

## Final policy: all six first failure steps

The final averaged actor crosses a tracking gate in every clip. These are first observed terminations from a nominal single/multi-environment replay, not end-of-video descriptions.

| Clip | First failure step | Progress | Earliest supported trigger |
| --- | ---: | ---: | --- |
| `walk1_subject1` | 12,089 | 92.5% | Orientation error reaches 0.825 rad; end-effector height error 0.407 m; peak contact force about 82 N at the terminal frame |
| `run1_subject5` | 5,695 | 47.9% | End-effector height error 0.434 m; orientation 0.779 rad is still below its 0.8-rad gate |
| `jumps1_subject1` | 5,433 | 44.4% | Orientation error 0.936 rad and end-effector height error 0.403 m |
| `dance1_subject3` | 3,271 | 49.7% | Orientation error 0.897 rad; end-effector height error 0.397 m |
| `fallAndGetUp1_subject4` | 1,617 | 19.2% | Orientation error 0.900 rad; anchor height error and end-effector error also exceed, while peak contact is about 1,306 N |
| `fight1_subject3` | 1,689 | 13.8% | Anchor height error 0.255 m crosses 0.25 m; end-effector height error 0.363 m |

The common supported chain is **policy trajectory drifts from the reference → root/end-effector relation degrades → an unchanged tracking gate terminates the rollout**. The training update changed the controller, not the scoring gate. The current run cannot distinguish world-model bias, actor overfitting to imagined states, incompatible replay statistics, and an over-large retained learning rate; that requires consecutive controlled ablations rather than another long mixed run.

[Machine-readable protocol](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/protocol.json) · [Final averaged evaluation](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/final-averaged.json) · [Final online actor](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/final-online-actor.json) · [First-failure measurements](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/failure-first-steps.json) · [Training metrics](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/metrics.jsonl) · [Runtime and checkpoint manifest](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/raisim-manifest.json) · [Source manifest](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/raisim-source-manifest.sha256)

## Evidence limits

- No mass, center-of-mass or contact-material randomization is claimed for this first RaiSim adapter.
- The learning run disables the original exam/failure-frontier phases so the backend change is isolated; it does not reproduce every advanced BlinkMimic2 schedule.
- Only nominal six-clip evaluation is reported. No success-rate comparison against the full 40-clip MuJoCo suite is made.
- No hardware calibration or real Bumi deployment is performed.
- RaiSim is not promoted to DexLab's default backend from this case.
