# UR7e and CTAG2F90D acquisition preparation

[简体中文](README.zh-CN.md) | [English](README.md)

**Current conclusion: the acquisition protocol and offline format checks are implemented; no hardware measurements or calibrated simulation parameters exist yet.** This is [D06 #33](https://github.com/huangkiki/Dexlab/issues/33). Measurement quality must be reviewed before data enters [#6](https://github.com/huangkiki/Dexlab/issues/6). This code only reads files; it neither connects to devices nor sends motion commands.

## Research question and identifiability

The first experiment measures **quasi-static force versus compression of a specified pad/material specimen along a defined loading direction**. It estimates equivalent normal compliance, loading/unloading hysteresis and repeatability as a reproducible contact-model reference. Measure force with an independent reference sensor and displacement with an independent gauge or calibrated observation system. A commanded gripper opening is not specimen compression.

- Repeat the loading sequence with a rigid reference to characterize fixture, pad and measurement-chain compliance. If these contributions cannot be separated, report the equivalent response of the assembly, not a material constitutive law or a uniquely identified stiffness.
- With trustworthy force and displacement references, fit local equivalent stiffness `ΔF/Δδ` over a preselected nonzero compression interval. Report interval, residuals, uncertainty and hysteresis instead of reducing an arbitrary nonlinear curve to one global stiffness.
- Without an external force reference, only setting versus deformation/holding/slip observations are supported. Slip load does not uniquely identify friction when normal force is unknown; motor current is not automatically contact force.
- These measurements concern UR7e and two-finger grippers. Shared material data does not validate OpenArm/Wuji drives, pads or multi-finger grasp accuracy.

## Known hardware and missing information

The user confirms two UR7e arms and two identical CTAG2F90D grippers. Record model identities; do not publish site photographs or serial numbers. Verify left and right grippers separately: identical models can have different offsets and linkage mappings.

The manufacturer's page uses **CTAG2F90-D**, listing Modbus RTU/IO and position, speed and force feedback. Verify the installed connection, firmware, registers and force-sensing principle locally. Advertised positioning repeatability is not this experiment's measurement uncertainty. [Manufacturer model page](https://en.changingtek.com/diandong/147), accessed 2026-10-05.

UR's RTDE documentation distinguishes `target_q` from `actual_q` and exposes controller time and TCP state. Field availability depends on controller version; output packets may be skipped under load. Retain the negotiated recipe and observed intervals rather than assuming the requested frequency was delivered. [Official RTDE guide](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-guide.html), accessed 2026-10-05.

| Field verification | Required evidence | If unavailable |
|---|---|---|
| Firmware, interface and driver versions for both arms/grippers | Operator verification, actual RTDE recipe, matching register manual and file hashes | `null`; no guessed registers, scaling or wiring |
| Opening definition and linkage mapping | Pad reference surfaces; independently measured openings, loading/unloading and repeats | Retain raw codes; do not label them metres or fingertip distance |
| Gripper settings and feedback | Raw commands, acknowledgement/status, field provenance, units and quantization | Mark feedback `unverified` or `unavailable` |
| Independent force/displacement reference | Range, resolution, calibration/check method, zero drift, axis, mounting and raw files | No force-displacement calibration if either is missing |
| Tool, fixture and specimen | TCP/payload settings, pad dimensions/material/contact surfaces, mass/dimension methods, batch and ambient conditions | Keep unknown; restrict claims to the documented assembly |
| Video and synchronization | Continuous close-up originals, frame times, shared synchronization events and residuals | File creation time is not synchronization; otherwise use video qualitatively |

## Collection procedure

No motion program is provided. Site operators use the already approved equipment procedures, choose suitable loading limits, speeds and stop conditions, and record actual values in the frozen conditions. The template supplies no guessed force, speed or travel limits for an unknown fixture.

1. **Verify interfaces.** Identify each device and field document. Compare commands, feedback and independent measurements during permitted static readback and existing operations. Retain raw packets and decoding/unit conversions. Never fill unknown feedback with zero or copy commands into measured channels.
2. **Verify the measurement chain.** Zero external force/displacement sensors, check reference loads/distances, record before/after drift and define positive directions. Use common observable events to estimate clock offset/drift against the collector's monotonic clock and retain residuals. If uncertainty exceeds the effect of interest, improve the measurement before fitting.
3. **Development pilot.** Load, hold and unload the rigid reference and material specimens at multiple nonzero compression levels. Repeat mounting; check lateral slip, pose changes, saturation and fixture compliance. Use development data alone to choose loading intervals, sample rates, model family and validity criteria.
4. **Freeze the acquisition table.** List every trial, specimen, material batch, loading range/rate/hold time, gripper side, repeat count and randomized order before formal collection. Define success, anomaly and missing-data criteria. Use different specimens and complete condition groups for development, calibration and test; never randomly split adjacent frames. Choose sample count from pilot variability and the effect to resolve. The template's three trials illustrate fields, not sufficient statistical power.
5. **Collect.** Retain complete loading/holding/unloading, re-zeroing, continuous close-ups and asynchronous logs. Give every repeat its own ID. Preserve faults, saturation, dropped samples and aborted trials with reasons, not just successful curves.
6. **Seal and hand over.** Preserve raw logs; separately retain conversion scripts, versions, configurations, hashes, frozen splits and validation output. Check format first, then have #6 review timing, sensor errors, coverage and identifiability. Open the held-out test set only after freezing the model and fitting procedure. Changing a model based on test results requires a new test set.

A first round may measure one side only; unknown unused channels do not block that side's intake. Group sides separately and do not treat two traces as many independent observations. Later slip, cloth tension and complete manipulation tests need their own protocols; none is claimed validated here.

## Time, frames and uncertainty

Each asynchronous sample records collector receipt time `host_time_s`, device sampling time `device_time_s` (or `null`) and a channel sequence number within the trial. Receipt and sampling times differ. A device restart requires another trial/clock segment; do not fit across it. Retain requested rate, observed interval distribution, missing intervals, validity window and residuals of `t_host = scale_to_host * t_device + offset_to_host_s`. Contiguous logger sequence numbers do not prove the device sampled without loss.

Document each frame's origin, axes, sign, dimensions, measurement method and transformation evidence. The arm bases are independent: no combined dual-arm spatial data without their measured relative pose. TCP orientation is a rotation vector, not Euler angles. Opening is the separation between defined pad reference surfaces. Compression subtracts the pre-contact reference and declares whether fixture deformation is included.

For wrenches, state the reference point, expression frame, gravity and tool-payload compensation. A UR TCP resultant is not each finger's normal contact force. Keep nominal accuracy, resolution, repeatability and measurement uncertainty separate. `absolute_bounds` contains verified componentwise absolute error bounds with their derivation in `basis`, not arbitrary standard deviations or advertising specifications.

## Executable log contract v1

The [preparation manifest](template/manifest.json) identifies the four known devices and an unselected reference sensor. The [sample file](template/samples.jsonl) is empty: **there are no fabricated measurements**. Copy the whole template into a new acquisition directory before filling it in. Run from the repository root:

```bash
.venv/bin/python -m dexlab.hardware_log docs/hardware/template
# Exit 0: valid preparation format with missing items reported; not accepted measurements.
.venv/bin/python -m dexlab.hardware_log docs/hardware/template --require-measured
# Exit 2 is expected: this is not a complete measured intake bundle.
```

| Manifest field | Contract |
|---|---|
| `schema_version`, `protocol`, `kind` | `1`, `ctag-contact-v1`; truthfully distinguish `preparation`, `synthetic`, `measured` |
| `devices` | Side-specific identities; firmware/interface may be `null`; reference sensor registered separately |
| `artifacts` | Bundle-relative filename to SHA-256; retain raw sources, decoding/conversion, verification and frozen conditions; no private connection data |
| `clocks`, `frames` | Semantics and evidence; clock mappings/errors may be `null`; `evidence` refers to `artifacts` |
| `channels` | `signal` fixes unit, dimension and `command/feedback/reference` provenance; declare device, source field, frame, clock, status, evidence and uncertainty |
| `trials` | Unique `id`; split, specimen, condition, repetition, required channels, actual conditions, `planned/complete/aborted` and abort reason |

Each JSONL row has exactly `trial_id, channel, sequence, host_time_s, device_time_s, value, quality, reason`. Values are arrays (one component for scalars, six for joints/TCP). `quality=missing/invalid` requires `value=null` and a reason. Valid values must be finite and belong to verified channels. Gripper settings use `device_code`; only a verified opening conversion uses `m`. The complete signal/unit/dimension catalog is `src/dexlab/hardware_log.py:SIGNALS`; that module is the versioned executable format definition.

Checks reject mismatched command/feedback sources, wrong units, duplicate keys, wrong dimensions, non-finite numbers, reversed/repeated timestamps, split leakage, missing/tampered evidence and artifacts escaping the bundle. Reports expose missing items, observed sequence/invalid-sample gaps and trial statuses without interpolation or input mutation. Invalid format exits 1; valid ordinary format checks exit 0. With `--require-measured`, incomplete required intake data or non-measured kind exits 2. Only required channels and their measurement chains affect completeness; unused devices may remain unknown.

**Limit:** numbers alone cannot establish authenticity, calibration, synchronization, adequate sampling, genuine specimen groups or scientific validity. `measured_intake_ready` only describes file handover conditions; `scientific_acceptance` remains `not_assessed`. Do not remove aborted trials or gaps to obtain a completeness flag. Raw hardware data is private by default and needs a separate publication privacy check.

## Local validation and remaining work

The log validator has dedicated synthetic regression tests. The exact code tree, full suite, bilingual documentation and native simulation regression results are recorded in the delivery PR and Release. Simulation regression does not provide hardware measurements. Review is self-review unless an independent reviewer is explicitly identified.

Negative tests cover commands masquerading as feedback, zero-filled unknowns, specimens/conditions leaking across splits, packet gaps, clock reversal, NaN, altered files, path escape and preparation/synthetic bundles masquerading as measured delivery. Test values are explicitly synthetic, not hardware evidence.

Installed firmware/interfaces, reference sensor selection/error, frozen conditions and a real dataset remain unavailable. #33 delivers preparation; #6 owns subsequent measurement and fitting. The development plan's basic physical measurement remains incomplete until actual data exists.
