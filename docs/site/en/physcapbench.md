# Physical captions in DexLab: measure reference coverage before claiming video truth

## TL;DR

**The useful idea in PhysCapBench is not another scalar “physical caption score.” It is a contract that turns a physical process into an inspectable reference and freezes whether each dimension has enough evidence before candidates are evaluated.**

It can diagnose what physical information a simulation record, failure explanation or video description omitted. It cannot replace contact force, state trajectories, native task criteria or hardware evidence. The public evaluator mostly compares a candidate with a textual Gold reference; it does not rewatch the video to verify every claim.

## Start with a page-turning task

Suppose a video shows the left hand holding a book steady while the right hand turns a page from right to left. Contact is maintained during the turn, the page state changes from right to left, and the reference also records a torque-based orientation change and event order.

The candidate “a person turns a book page” is semantically reasonable, but it leaves out:

- which hand stabilizes and which hand acts;
- the page's rotation direction relative to the book;
- when contact starts, persists or ends;
- the page's final physical state;
- which visible relation supports the causal explanation;
- the order of events.

PhysCapBench separates these into seven dimensions: event coverage, objects and roles, actions and motion, contact and interaction, states and outcomes, physical mechanisms and causality, and temporal order. The point is not a longer caption. It is to make “sounds right but omits the process” a locatable failure.

## The reusable part is the evaluation contract

A reference contains entities, initial/final states, events, roles, actions, contact, state changes, mechanisms, order and evidence. The evaluator first determines, without seeing a candidate, whether each dimension has sufficient reference evidence. It then gives the text judge the candidate and the frozen evidence.

This order reduces a common contamination: after seeing which dimensions make a method look weak, the evaluator changes Gold or removes the hard dimension. The DexLab equivalent should:

1. freeze tasks, references, applicability, scorers and failure denominators;
2. run the system under test;
3. report whether native measurements support each criterion;
4. preserve insufficient evidence as insufficient.

Data revisions should be frozen too. This review pinned [paper v2](https://arxiv.org/abs/2611.16424v2), [GitHub `0858c69`](https://github.com/hfwang2001/PhysCapBench/tree/0858c694f6aa2fae247c5fc907fb60488f27c4b7) and [Hugging Face revision `4b18722`](https://huggingface.co/datasets/hfwang01/PhysCapBench/tree/4b1872201558c6fb5e231f5be2b843ed16b2e105). The released metadata passes ID, reference, applicability and hash checks for 1,500 samples. That does not establish the factual correctness of 1,500 captions.

## What the evidence does and does not establish

The authors report that physical captions reduce third-person reconstruction LPIPS by 8.6–9.5% and egocentric LPIPS by 26.9–30.9%; both generators and PVCS move in the same direction. Instruction enrichment raises one controlled task from 37.5% to 45.0% over 40 shared scenes, and four policy families improve on average on two benchmarks.

This supports the broader hypothesis that richer physical descriptions can improve downstream conditioning and training instructions. Three boundaries remain:

- The controlled policy gain is three additional successes, with one training seed and one rollout per scene; no per-dimension description ablation or confidence interval is reported.
- The public repository contains the benchmark evaluator, not the reconstruction or policy-training reproduction packages.
- A text evaluator can miss an incorrect contact or causal claim that is absent from Gold. It measures reference agreement/coverage rather than complete video factuality.

The paper also does not report human–judge agreement. Using the score directly as a DexLab reward or task-success criterion would confuse reference coverage with physical correctness.

## Transfer order for DexLab

### Borrow directly

1. **Represent a process as an event chain:** actor/tool/target, motion, contact start/maintain/end, state before/after, visible mechanism and temporal relation.
2. **Freeze applicability before candidates:** decide whether current measurements support a criterion before running the system under test.
3. **Choose cues by what they can identify:** RGB scenes, hand pose/HOI, synchronized gripper views and trajectories answer different questions; cues do not automatically become Gold.
4. **Bind evidence to versions:** reference revision, configuration hash, frame/time window, review status and candidate visibility.

### Adapt

Simulation can use stronger evidence than a video caption: native contact force, contact establishment/loss, solver events and object pose/velocity. Keep `command ≠ measurement` and `render ≠ physical control`. Final acceptance still depends on the first failing layer, native task criteria, full-task success and appropriate hardware measurement.

### Defer

- an equal-weight seven-dimension score as a universal physical truth metric;
- one LLM judge as a direct reward;
- replacing simulation-to-real or task success with a caption-score increase.

## First testable question

Use 20–30 existing DexLab episodes spanning stable grasp, slip/contact transition and state recovery. Compare a short task instruction, a generic video caption and a structured physical caption. Besides seven-dimension coverage, separately count:

- wrong contact;
- reversed causal direction;
- wrong state transition.

Blind-review 90–120 candidates with at least two people, then compare two text or multimodal judges. The minimum bar is not longer text. The structured description must make the first failing layer easier to localize without increasing false assertions. Only then should it enter a larger data-cleaning or training-instruction pipeline.

## Continue reading

- [PhysCapBench paper](https://arxiv.org/abs/2611.16424v2)
- [Official evaluator](https://github.com/hfwang2001/PhysCapBench)
- [Public data](https://huggingface.co/datasets/hfwang01/PhysCapBench)
- [DexLab discussion #378](https://github.com/huangkiki/Dexlab/discussions/378)

See [model evaluation](model-evaluation.md) for DexLab's broader co-evolution and acceptance boundaries.

## Evidence scope

This page maps mechanisms from the paper and public implementation. It is not a PhysCapBench leaderboard reproduction or a new DexLab physics experiment. This review ran the released metadata checks and repository contract tests and checked hashes and sampled frames for representative videos. It did not call the judge endpoint or rerun caption, reconstruction or policy experiments. All downstream figures are author-reported.
