# Mask progress-signal audit

This offline experiment tests whether a target mask can serve as a task-progress
signal before any visual policy is trained. It uses the published demo-0 render,
not a new physics or policy run.

## Inputs and contract

- Video: `docs/evidence/visual/libero-demo0-baseline.mp4`, 20 fps, 640 × 480,
  SHA-256 `37e84fa770514cd892f3688843add4a34ffa80b655148e67a1f64e2dbd16cb58`.
- Event source: `docs/evidence/libero/summary.json`, SHA-256
  `fa4ab804dc6825ea2f415a520ee7e75315a0dcf94e3495b53403a5288615789b`.
- Sample set: every fifth frame, 28 samples from the 140-frame replay.
- Target mask: deterministic color/connected-component tracker initialized at
  the cream-cheese package. This is a video-specific audit mask, not a general
  detector.
- Gripper ROI: OpenCV MIL tracker initialized on the gripper, expanded by 14 px.
  Detection quality is not the subject; the audit isolates mask transforms.
- Native contact, lift, basket and success events are used only as stage labels.
  They are never inputs to the candidate progress score.

`ROI overlap` is the fraction of target-mask pixels inside the tracked gripper
ROI. `Mask area` is target-mask pixels divided by image pixels. A separate AUC
tests whether ROI overlap ranks post-contact stages above pre-contact.

## Results

| Condition | Samples | Mask absent | Triggered misses | False boxes | Delay | Mean area | Pre-contact vs post-contact AUC | First changed stage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 28 | 2 | 0 | 0 | 0 | 0.000731 | 0.861 | none |
| dropout, every 20 frames | 28 | 8 | 7 | 0 | 0 | 0.000564 | 0.738 | contact-to-lift |
| false box filling ROI centre | 28 | 0 | 0 | 28 | 0 | 0.004594 | 0.952 | pre-contact |
| three-frame delay | 28 | 2 | 0 | 0 | 3 | 0.000720 | 0.890 | contact-to-lift |
| remove right 40% of mask bound | 28 | 2 | 0 | 0 | 0 | 0.000445 | 0.829 | contact-to-lift |

Baseline median ROI overlap by stage:

| Stage | Samples | Median area | Median ROI overlap |
| --- | ---: | ---: | ---: |
| pre-contact | 11 | 0.001090 | 0.000 |
| contact-to-lift | 2 | 0.000562 | 0.535 |
| lift-to-success | 13 | 0.000609 | 0.877 |
| post-success | 2 | 0.000000 | 0.000 |

## Finding

The mask signal separates gripper approach from contact and transport in this
single replay: baseline AUC is `0.861`, pre-contact median overlap is `0`, and
lift-to-success median overlap is `0.877`.

It does **not** remain a completion signal. The target-mask extractor loses the
object in both post-success samples. This is a target-generation failure, not a
physical task failure; native success remains separate and unchanged.

The perturbations expose different failure surfaces:

- Seven frame dropouts lower AUC to `0.738` and shift the first stage at
  contact-to-lift.
- A false box makes pre-contact overlap `0.780`, so fabricated progress can
  look better than the real signal. High AUC cannot establish a valid signal.
- Three-frame delay changes contact-stage overlap and weakens the transition.
- Removing mask support outside the ROI can *increase* overlap because the
  denominator shrinks. Occlusion must therefore be audited together with area,
  not interpreted as monotonic signal loss.

## Decision

Use mask area or ROI overlap only after a quality gate that records raw mask
presence, area, ROI overlap, event stages and perturbations separately. Do not
use the mask score as physical grasp or task success. Do not train visual GCRL
from this result; this replay supports the audit contract, not policy efficacy.

Machine record: `docs/evidence/libero/mask-progress-audit-v1.json`, SHA-256
`07ab0fcb58c734a75f218b3105d6b653ea75860190f2c3128e7009dbf45b8d35`.

Reproduce:

```bash
PYTHONPATH="$PWD/src" python3 demos/libero-contact/audit_mask_progress.py \
  --video docs/evidence/visual/libero-demo0-baseline.mp4 \
  --summary docs/evidence/libero/summary.json \
  --demo demo_0 --sample-stride 5 \
  --output docs/evidence/libero/mask-progress-audit-v1.json
```
