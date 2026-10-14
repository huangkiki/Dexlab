# Do cut pieces stay independent?

```{raw} html
:file: _cutting-comparison.html
```

Measured GIFs show opening, interior volume and piece motion derived from saved states. GIF playback is slowed; clocks retain physical time. [Paper audit and measurement definitions](cutting-fidelity.md).

## What the original comparison tests

The [BladeMaster project](https://jango6324.github.io/blademaster/#comparison) and [paper v2, IV-A / Fig. 5](https://arxiv.org/abs/2609.27342v2) test history retention after two parallel cuts. After withdrawal, only the left piece receives an initial leftward velocity; motion of the middle and right pieces reveals unwanted shared-grid coupling. Both reference clips were published by the BladeMaster authors, including their comparison against [Ou and Tavakoli (2025)](https://arxiv.org/abs/2502.18437).

| Observation | BladeMaster (author-reported) | CRESSim-MPM (author-reported) | DexLab |
| --- | ---: | ---: | --- |
| Mean gap at first half-depth cut; 0.5 mm blade | 0.654 mm | 4.059 mm | Independent dynamic estimator below; matched sampling unverified |
| Middle-piece volume contraction after two cuts | 0.506% | 8.746% | Independent dynamic estimator below; matched sampling unverified |
| Single-piece motion after withdrawal | Left piece moves away; others stay nearby | Middle and right pieces also move left | 5 mm grid: 2.398 mm relative left-piece motion; both passive drifts below 0.031 mm |

The first two columns contain author-reported numbers, not independently reproduced in DexLab; the third contains measurements from our separate configuration. Our maximum proxy overlap and their mean gap width are different quantities. Reference media remain external, attributed embeds on the original host; they are not copied into this repository or labeled as DexLab results. The third column's raw records, failures and controls are in the [two-cut tofu experiment](tofu-comparison.md).

## DexLab event measurements (5 mm grid)

Signed openings use an affine material-face estimator; volume uses middle-region interior tetrahedra. These independently defined estimates and synthetic settings do not support a ranking against the author-reported values above.

| Event | Saved time (s) | Cut 1 (mm) | Cut 2 (mm) | Middle ΔV (%) |
| --- | ---: | ---: | ---: | ---: |
| First cut at half depth | 0.82 | +0.496 | — | -1.323 |
| Both cuts withdrawn | 4.00 | +0.124 | +0.250 | -2.509 |
| Before motion probe | 4.20 | +0.124 | +0.262 | -2.509 |
| Final | 5.00 | +0.134 | +2.623 | -2.479 |

<a href="_static/cutting/tofu-sequential/measurements.json">Per-frame values</a> · <a href="_static/cutting/tofu-sequential/particles.gif">Measured GIF</a>

## Protocol for a future matched comparison

1. **Freeze one question.** Does the first discontinuity remain mechanically separated after the second cut? Freeze block dimensions, material parameters, sampling, blade geometry, trajectories and contact model before running. Resolve missing author parameters rather than estimate them from screenshots.
2. **Align events.** Save first half-depth, first withdrawal, second withdrawal, single-piece velocity initialization and a fixed elapsed interval. Synchronize only shared-input runs; never stretch clips to imply equal speed or cost.
3. **Measure separately.** Sample gap distributions in the same material-coordinate band, declare the middle-piece volume estimator, and record every piece's centroid motion, momentum and external impulse. A visible gap does not replace connectivity scoring.
4. **Keep counterexamples.** Uncut, partial-cut and history-disabled-after-withdrawal ablations; half-step and finer-sampling sensitivities. Retain failed, invalid and not-run cases.
5. **Qualify before ranking.** Every executed implementation needs source/binary versions, shared inputs, independent scoring, budgets and raw records. Author videos are references. No matched three-method comparison or superiority ranking has yet been established.

This is a reusable comparison workflow. A new benchmark still needs its own frozen protocol and resource budget. This page first delivers the three-column view and explicit provenance.
