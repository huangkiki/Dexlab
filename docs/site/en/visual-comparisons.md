# From visible motion to physical differences

Inspect recorded states, native observations and physical references together. Each plot links its archived experiment; playback reads records without advancing physics or changing scores or tolerances.

Replay geometry keeps physical proportions; inspect small changes in the curves. Dashed lines are the declared analytical/engineering references, not measured material truth. Historical protocols do not form a universal engine ranking.

(incline)=
## Six-engine incline: shared conditions, different responses

A 40 mm, 64 g cube; static, sliding and nominal-zero-friction conditions at three timesteps. Curves and replays retain the original passes, failures and invalid records.

```{raw} html
<div class="dexlab-replay" data-language="en" data-variants="[{&quot;label&quot;: &quot;Static · 1 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-static-0.001.json.gz&quot;}, {&quot;label&quot;: &quot;Static · 2 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-static-0.002.json.gz&quot;}, {&quot;label&quot;: &quot;Static · 0.5 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-static-0.0005.json.gz&quot;}, {&quot;label&quot;: &quot;Sliding · 1 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-sliding-0.001.json.gz&quot;}, {&quot;label&quot;: &quot;Sliding · 2 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-sliding-0.002.json.gz&quot;}, {&quot;label&quot;: &quot;Sliding · 0.5 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-sliding-0.0005.json.gz&quot;}, {&quot;label&quot;: &quot;Nominal zero friction · 1 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-frictionless-0.001.json.gz&quot;}, {&quot;label&quot;: &quot;Nominal zero friction · 2 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-frictionless-0.002.json.gz&quot;}, {&quot;label&quot;: &quot;Nominal zero friction · 0.5 ms&quot;, &quot;url&quot;: &quot;_static/visual/incline-frictionless-0.0005.json.gz&quot;}]">
<div class="visual-hero"><img loading="lazy" src="_static/visual/incline-static-0.001.png" alt="Six-engine incline: shared conditions, different responses"></div>
<details class="replay-fallback" open><summary>Static figures and full data (no JavaScript required)</summary><img loading="lazy" src="_static/visual/incline-static-0.001-curves.svg" alt="Static figures and full data (no JavaScript required)"><ul><li>Static · 1 ms: <a href="_static/visual/incline-static-0.001.json.gz">JSON.gz</a> · <a href="_static/visual/incline-static-0.001-curves.svg">SVG</a> · <a href="_static/visual/incline-static-0.001.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Static · 2 ms: <a href="_static/visual/incline-static-0.002.json.gz">JSON.gz</a> · <a href="_static/visual/incline-static-0.002-curves.svg">SVG</a> · <a href="_static/visual/incline-static-0.002.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Static · 0.5 ms: <a href="_static/visual/incline-static-0.0005.json.gz">JSON.gz</a> · <a href="_static/visual/incline-static-0.0005-curves.svg">SVG</a> · <a href="_static/visual/incline-static-0.0005.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Sliding · 1 ms: <a href="_static/visual/incline-sliding-0.001.json.gz">JSON.gz</a> · <a href="_static/visual/incline-sliding-0.001-curves.svg">SVG</a> · <a href="_static/visual/incline-sliding-0.001.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Sliding · 2 ms: <a href="_static/visual/incline-sliding-0.002.json.gz">JSON.gz</a> · <a href="_static/visual/incline-sliding-0.002-curves.svg">SVG</a> · <a href="_static/visual/incline-sliding-0.002.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Sliding · 0.5 ms: <a href="_static/visual/incline-sliding-0.0005.json.gz">JSON.gz</a> · <a href="_static/visual/incline-sliding-0.0005-curves.svg">SVG</a> · <a href="_static/visual/incline-sliding-0.0005.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Nominal zero friction · 1 ms: <a href="_static/visual/incline-frictionless-0.001.json.gz">JSON.gz</a> · <a href="_static/visual/incline-frictionless-0.001-curves.svg">SVG</a> · <a href="_static/visual/incline-frictionless-0.001.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Nominal zero friction · 2 ms: <a href="_static/visual/incline-frictionless-0.002.json.gz">JSON.gz</a> · <a href="_static/visual/incline-frictionless-0.002-curves.svg">SVG</a> · <a href="_static/visual/incline-frictionless-0.002.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li><li>Nominal zero friction · 0.5 ms: <a href="_static/visual/incline-frictionless-0.0005.json.gz">JSON.gz</a> · <a href="_static/visual/incline-frictionless-0.0005-curves.svg">SVG</a> · <a href="_static/visual/incline-frictionless-0.0005.mp4">MP4 · mujoco / superdex / genesis / newton / physx / drake</a></li></ul></details>
</div>
```

**Conditions：** Native incline cohorts: MuJoCo 3.15.0, SuperDex 1.0.0, Genesis 1.4.3, Newton Physics 1.6.1, PhysX 5.9.0 and Drake 1.57.0; each records contact law, precision and applicable profiles.

**Observation：** All six have positive, negative and failed evidence. Genesis floors nominal-zero contact friction to .01; SuperDex BFGS/SR1 execute Newton-equivalent steps under assembly every step.

**Explanation：** Established effective-parameter/execution-path differences change the interpretation of same-named profiles. Initial pass rates do not replace equal-budget tuned comparisons.

**Advice：** Filter candidates by sticking/sliding, low friction and contact scale; inspect invalid records, physical error and cost together.

**Limits：** Cohort protocols and admission scope remain separate. The full matrix maps research scope, not universal rank. Numerical work remains in #157/#159/#163/#165.

Selection: MuJoCo uses the first frozen profile, PGS/elliptic. Other published baselines are SuperDex Newton/AUTO/C1, Genesis Newton/elliptic/Signorini, Newton Physics XPBD, PhysX PGS and Drake SAP/kLagged/hydroelastic. Selection does not use pass counts; all other profiles remain in the full matrix.

Reference: an ideal nonrotating Coulomb block with continuous contact has sliding acceleration a=g(sinθ−μcosθ); rest requires the static-friction inequality. Contact switching, geometry and model differences limit this reference. Drake’s initial 1 μm gap and Genesis’s native floor on nominal zero friction remain. Close-ups use the same body-follow camera rule and scale; the shared ruler retains world displacement. Invalid-record curves are diagnostic only.

**Evidence and all configurations:** [Complete solver matrix](coverage.md) · [Engine reports](engines.md) · Each replay dataset contains original scores and source hashes.

(normal)=
## Normal response: change parameters or the solver?

The same MuJoCo fixture moves from about 80 kN/m toward the synthetic 20 kN/m target. Inspect loaded-window indentation, then the complete unloading trace; success belongs to the stated checks and conditions.

```{raw} html
<div class="dexlab-replay" data-language="en" data-variants="[{&quot;label&quot;: &quot;Initial / calibrated · 0.2 kg · 0.5 ms&quot;, &quot;url&quot;: &quot;_static/visual/normal-calibration.json.gz&quot;}]">
<div class="visual-hero"><img loading="lazy" src="_static/visual/normal-calibration.png" alt="Normal response: change parameters or the solver?"></div>
<details class="replay-fallback" open><summary>Static figures and full data (no JavaScript required)</summary><img loading="lazy" src="_static/visual/normal-calibration-curves.svg" alt="Static figures and full data (no JavaScript required)"><ul><li>Initial / calibrated · 0.2 kg · 0.5 ms: <a href="_static/visual/normal-calibration.json.gz">JSON.gz</a> · <a href="_static/visual/normal-calibration-curves.svg">SVG</a> · <a href="_static/visual/normal-calibration.mp4">MP4 · initial-mujoco / validation-mujoco-reference</a></li></ul></details>
</div>
```

**Conditions：** A 40 mm cube, 0.2 kg, 0.5 ms; 2/4/6/−1 N loading. The 20 kN/m response is a synthetic target.

**Observation：** MuJoCo initially measured about 80 kN/m and approached 20 kN/m after calibration. Fixed parameters gave 10.01/40.04 kN/m at 0.1/0.4 kg; the predeclared mass conversion gave 20.04/19.93 kN/m.

**Explanation：** Established in this fixture: reference-acceleration response depends on mass and impedance. Equal parameter names do not establish equal material stiffness across engines.

**Advice：** Check effective response on declared fitting loads, apply an explicit conversion hypothesis, and validate other loads and masses independently.

**Limits：** This constant-impedance, four-point face-contact fixture does not supply a universal geometry formula or measured material calibration. Historical PhysX identity remains missing under the #126 audit.

Effective parameters: shared solimp=[0.9,0.9,0.001,0.5,2]; initial/calibrated solref and full native settings are in effective_parameters and original run.json. The −1 N separation segment remains; a separate loaded-window plot exposes small indentation. Cost and transfer figures below belong to separate historical protocols and are not pooled with this case.

**Evidence and all configurations:** [Normal protocol, all 17 results and reproduction](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/NORMAL_RESPONSE.md) · [Transfer](mass-size-transfer) · [Cost boundaries](transient-cost)

![Response and cost](../../evidence/response-cost-v1.png)

![Mass / size transfer failures](../../evidence/contact-transfer-v1.png)

(pinch)=
## Pinch: 0.4 N slips, 0.8 N holds

The same Genesis fixture and object, changing the finger-joint force limit. Compare complete closing, lifting, holding and release, with an open-gripper negative control retained.

```{raw} html
<div class="dexlab-replay" data-language="en" data-variants="[{&quot;label&quot;: &quot;Retention: 0.4 N / 0.8 N&quot;, &quot;url&quot;: &quot;_static/visual/pinch-retention.json.gz&quot;}, {&quot;label&quot;: &quot;Open negative / 0.8 N&quot;, &quot;url&quot;: &quot;_static/visual/pinch-negative.json.gz&quot;}]">
<div class="visual-hero"><img loading="lazy" src="_static/visual/pinch-dev-cap-0.4.png" alt="Pinch: 0.4 N slips, 0.8 N holds"></div>
<details class="replay-fallback" open><summary>Static figures and full data (no JavaScript required)</summary><img loading="lazy" src="_static/visual/pinch-retention-curves.svg" alt="Static figures and full data (no JavaScript required)"><ul><li>Retention: 0.4 N / 0.8 N: <a href="_static/visual/pinch-retention.json.gz">JSON.gz</a> · <a href="_static/visual/pinch-retention-curves.svg">SVG</a> · <a href="_static/visual/pinch-dev-cap-0.4.mp4">MP4 · dev-cap-0.4</a> · <a href="_static/visual/pinch-dev-cap-0.8.mp4">MP4 · dev-cap-0.8</a></li><li>Open negative / 0.8 N: <a href="_static/visual/pinch-negative.json.gz">JSON.gz</a> · <a href="_static/visual/pinch-negative-curves.svg">SVG</a> · <a href="_static/visual/pinch-dev-open.mp4">MP4 · dev-open</a> · <a href="_static/visual/pinch-dev-cap-0.8.mp4">MP4 · dev-cap-0.8</a></li></ul></details>
</div>
```

**Conditions：** A native Genesis finite fixture, four force caps and ±2 mm initial offsets: 16 fixed cases. Separate MuJoCo cube-pinch and robot SDF historical scenes also exist.

**Observation：** Genesis cannot retain the object at 0.2/0.4 N caps; 0.8/10 N holds and releases. This result is limited to the reported fixture and drive.

**Explanation：** Established: drive caps change load capacity. Friction/torque balance starts diagnosis; small contact-force residuals alone do not establish grasp success.

**Advice：** Start with object load, each side’s normal force and effective friction, then check finite pads, slip and release alongside actual drive output.

**Limits：** This is not a unified cross-engine pinch ranking. #145 inertia/frames and #132→#134 shared-drive/594-episode research remain independently open.

Reference: ideal static flat-pad retention requires μΣN≥mg; here mg/μ≈1.256 N. The plotted Σ|Fx| is a pad-force projection proxy, not measured actuator output. The 60 mm height threshold during 2–3 s is one original check; all other checks remain.

**Evidence and all configurations:** [All 16 cases, failures and costs](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) · [Historical solver audit](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-solver-audit.md)

(libero)=
## LIBERO: native task, timestep control and observation fix

Same actions, initial state, Panda and native success; original 2 ms versus unqualified 1 ms control. Heldout task success stays 10/10, screens change from 5/10 to 3/10, and cost doubles. Policy effects of observation refresh remain unverified.

```{raw} html
<div class="dexlab-replay" data-language="en" data-variants="[{&quot;label&quot;: &quot;Development demo_0: first frozen demo&quot;, &quot;url&quot;: &quot;_static/visual/libero-demo0.json.gz&quot;}, {&quot;label&quot;: &quot;Heldout demo_4: first screen regression&quot;, &quot;url&quot;: &quot;_static/visual/libero-demo4.json.gz&quot;}, {&quot;label&quot;: &quot;Heldout demo_8: maximum native overlap&quot;, &quot;url&quot;: &quot;_static/visual/libero-demo8.json.gz&quot;}]">
<div class="visual-hero"><img loading="lazy" src="_static/visual/libero-demo0-baseline.png" alt="LIBERO: native task, timestep control and observation fix"></div>
<details class="replay-fallback" open><summary>Static figures and full data (no JavaScript required)</summary><img loading="lazy" src="_static/visual/libero-demo0-curves.svg" alt="Static figures and full data (no JavaScript required)"><ul><li>Development demo_0: first frozen demo: <a href="_static/visual/libero-demo0.json.gz">JSON.gz</a> · <a href="_static/visual/libero-demo0-curves.svg">SVG</a> · <a href="_static/visual/libero-demo0-baseline.mp4">MP4 · baseline</a> · <a href="_static/visual/libero-demo0-step-1000us.mp4">MP4 · step-1000us</a></li><li>Heldout demo_4: first screen regression: <a href="_static/visual/libero-demo4.json.gz">JSON.gz</a> · <a href="_static/visual/libero-demo4-curves.svg">SVG</a> · <a href="_static/visual/libero-demo4-baseline.mp4">MP4 · baseline</a> · <a href="_static/visual/libero-demo4-step-1000us.mp4">MP4 · step-1000us</a></li><li>Heldout demo_8: maximum native overlap: <a href="_static/visual/libero-demo8.json.gz">JSON.gz</a> · <a href="_static/visual/libero-demo8-curves.svg">SVG</a> · <a href="_static/visual/libero-demo8-baseline.mp4">MP4 · baseline</a> · <a href="_static/visual/libero-demo8-step-1000us.mp4">MP4 · step-1000us</a></li></ul></details>
</div>
```

**Conditions：** Official cream-cheese-to-basket, Panda / robosuite 1.4.0 / MuJoCo 2.3.7 Newton elliptic; 20 Hz control, original 2 ms step.

**Observation：** Original and 1 ms heldout action executions both complete 10/10 tasks; numerical screens pass 5/10 and 3/10, with about double stepping cost. Five settling steps change one end-effector position component by 4.481 mm while the old observation is retained.

**Explanation：** Observation assignment omission is verified. Positive contact time constants couple to the timestep safety floor in pinned source. Smaller steps do not consistently help; the mechanism behind 12.163 mm floor overlap continues in #174.

**Advice：** Refresh observations first; distinguish controller goals, actuator output and contact forces. Retain failures and localize controlled experiments to the actual contact. No new physics profile is recommended.

**Limits：** Demonstration action execution only: no fixed-policy closed-loop effect, real-material accuracy or mid-episode restore qualification. Holdouts are ten demonstrations of one task, not new-task generalization.

Default: first frozen development demonstration, independent of outcome. Additional views show the first heldout screen regression and maximum baseline overlap, explicitly post-hoc diagnostic selections; all ten pairs remain in the full results. Video rendering never integrates physics.

The 1 mm dashed line is a declared numerical screen. Relative height includes rotation; normal force is actual contact readback. Native time = display time + 0.25 s; channels retain their pre/post-integration epochs.

**Evidence and all configurations:** [Native task, all configurations, failures and reproduction](libero-workflow.md) · [Remaining attribution #174](https://github.com/huangkiki/Dexlab/issues/174)
