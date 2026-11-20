# DexLab

```{raw} html
<div class="home story-home" id="top">
<section class="story-hero" aria-labelledby="home-heading">
  <div class="hero-copy">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis"><span>Agents and simulation,</span><strong>improving together through experiments.</strong></p>
    <p class="hero-lead">Experiments connect tasks, execution, contact dynamics, evidence tracking and failure attribution into one reproducible research chain: humans set goals and boundaries while agents participate in question discovery, experiment design and iteration.</p>
    <p class="hero-scope"><strong>Current scope</strong> Findings establish reproducible physical consistency within frozen simulation models. Autonomous experiment loops and physical-robot validation are the next evidence layer; no hardware dataset is included yet.</p>
  </div>
</section>

<section class="architecture-view" aria-labelledby="architecture-heading">
  <header class="architecture-intro">
    <h2 id="architecture-heading">From a task<br>to checkable evidence.</h2>
    <p>DexLab puts tasks and protocols, systems under test, action execution, environment backends, and evidence and scoring on one path. Observations and failure records return to skill and simulation improvement for the next experiment.</p>
  </header>
  <figure class="architecture-figure">
    <p class="architecture-scroll-hint">Scroll horizontally to view the full architecture</p>
    <div class="architecture-scroll" tabindex="0" role="region" aria-label="DexLab system architecture diagram, horizontally scrollable">
      <a class="architecture-image-link" href="../../zh-cn/latest/_static/images/dexlab-architecture.png" target="_blank" rel="noopener" aria-label="Open the original DexLab architecture image">
        <picture>
          <source srcset="../../zh-cn/latest/_static/images/dexlab-architecture.webp" type="image/webp">
          <img src="../../zh-cn/latest/_static/images/dexlab-architecture.png" width="1774" height="887" loading="eager" decoding="async" alt="DexLab architecture: tasks and protocols, systems under test, action execution, environment backends, evidence and scoring, and the observation loop returning to system improvement">
        </picture>
      </a>
    </div>
    <figcaption><span>The system view: tasks enter the execution stack and physics backends; observations and evidence return to skill and simulation improvement. On mobile, scroll horizontally or open the original image.</span><a href="../../zh-cn/latest/_static/images/dexlab-architecture.png" target="_blank" rel="noopener">Open original</a></figcaption>
  </figure>
</section>

<section class="concept-entry" aria-label="Concept field and experiment entry">
  <div id="concept-field-slot"></div>
  <a class="directory-entry" href="#experiments">
    <span class="directory-action">Start with representative experiments and findings</span>
    <span class="directory-summary">Begin with five representative experiments and three research judgments; physical-validation boundaries and regression conditions close the page.</span>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
</section>

<section class="home-evidence" id="experiments" aria-labelledby="evidence-heading">
  <section id="research-findings"></section>
  <span id="research-content"></span>
  <span id="evidence-feature"></span>
  <span id="blog-preview"></span>
  <header class="home-section-head">
    <p>Representative experiments</p>
    <h2 id="evidence-heading">From recorded behaviour to criteria.</h2>
    <span>Task trial → First failing layer → Repair → Independent retest</span>
  </header>

  <div class="evidence-sequence" aria-label="Representative experiment evidence sequence">
      <article class="evidence-panel" id="panel-cut" data-evidence="cut" data-evidence-reveal role="region" aria-labelledby="evidence-cut-title">
        <header class="evidence-panel-head">
          <span>01</span>
          <strong>Cutting and pushing</strong>
          <small>11.096 / 10.209 mm</small>
        </header>
        <div class="evidence-media evidence-media-split">
          <img src="../../zh-cn/latest/_static/cutting/tofu-cut-push/surface-rtx.gif" alt="Latest tofu two-cut and side-push recording" width="100%" loading="lazy">
          <img src="../../zh-cn/latest/_static/cutting/banana-cut-push/surface-rtx.gif" alt="Latest banana three-cut and side-push recording" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Cutting / separation criterion</p>
          <h3 id="evidence-cut-title">After cutting, prove the final piece can move independently.</h3>
          <p class="evidence-verdict">Direct pushing after the last cut produced independent displacement for three tofu pieces and four banana pieces.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Tofu 0.125 ms, η=5 Pa·s; banana 0.25 ms, η=0</dd></div>
            <div><dt>Native readback</dt><dd>Relative displacement of active pieces and knife-contact impulse</dd></div>
            <div><dt>Criterion</dt><dd><strong>Pass · 11.096 / 10.209 mm</strong></dd></div>
            <div><dt>Scope</dt><dd>Synthetic materials and a fixed cut-and-push protocol; not food calibration</dd></div>
          </dl>
          <a href="cut-push.html">Open records, controls and raw data →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-wuji" data-evidence="wuji" data-evidence-reveal role="region" aria-labelledby="evidence-wuji-title">
        <header class="evidence-panel-head">
          <span>02</span>
          <strong>Contact and torsional moment</strong>
          <small>2.734 → 1.025 mm</small>
        </header>
        <div class="evidence-media">
          <img src="../../zh-cn/latest/_static/wuji-contact/comparison.gif" alt="Wuji point and torsional contact comparison" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Contact / moment direction</p>
          <h3 id="evidence-wuji-title">Persistent contact does not prevent rotation about the grasp line.</h3>
          <p class="evidence-verdict">Point contact lacks the required torque direction; synthetic torsional contact brings retention back inside its original threshold.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Point contact replaced only by synthetic torsional contact</dd></div>
            <div><dt>Native readback</dt><dd>Two-second hold displacement and peak angular velocity</dd></div>
            <div><dt>Criterion</dt><dd><strong>2.734 → 1.025 mm; 29.336 → 0.024992 rad/s</strong></dd></div>
            <div><dt>Scope</dt><dd>Two-finger ball hold; not hardware material calibration or whole-hand capability</dd></div>
          </dl>
          <a href="wuji-contact.html">Open contact records, GIF and independent recomputation →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-apple" data-evidence="apple" data-evidence-reveal role="region" aria-labelledby="evidence-apple-title">
        <header class="evidence-panel-head">
          <span>03</span>
          <strong>Apple-stem grasp</strong>
          <small>1/10 · 10/10</small>
        </header>
        <div class="evidence-media">
          <img src="../../zh-cn/latest/_static/studio/apple.gif" alt="OpenArm and Wuji apple-stem grasp record" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Task / frozen disturbance set</p>
          <h3 id="evidence-apple-title">A fixed task can still produce different outcomes across configurations.</h3>
          <p class="evidence-verdict">Read MuJoCo and SuperDex differences together with step size, drive, mass, position and contact representation.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Same set of ten fixed regression scenes with no held-out retuning</dd></div>
            <div><dt>Native readback</dt><dd>Lift, support, sustained hold, penetration and release</dd></div>
            <div><dt>Criterion</dt><dd><strong>MuJoCo 1/10 · SuperDex 10/10</strong></dd></div>
            <div><dt>Scope</dt><dd>Fixed-profile comparison, not an engine accuracy ranking</dd></div>
          </dl>
          <a href="experiments.html#apple-replays">Open close-up replays and fixed-scene results →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-cloth" data-evidence="cloth" data-evidence-reveal role="region" aria-labelledby="evidence-cloth-title">
        <header class="evidence-panel-head">
          <span>04</span>
          <strong>Cloth</strong>
          <small>52 / 105 pass</small>
        </header>
        <div class="evidence-media">
          <img src="../../zh-cn/latest/_static/cloth-studio/grasp.gif" alt="Cloth grasp and motion record" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Deformable body / staged acceptance</p>
          <h3 id="evidence-cloth-title">Grasping, lifting and completing a fold are separate checks.</h3>
          <p class="evidence-verdict">Deformation, penetration, residual motion and cost are scored separately on one frozen held-out set.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Seven native configurations on the same frozen held-out set</dd></div>
            <div><dt>Native readback</dt><dd>Deformation, sag, penetration, residual motion and cost</dd></div>
            <div><dt>Criterion</dt><dd><strong>52 / 105 pass; 53 failures retained</strong></dd></div>
            <div><dt>Scope</dt><dd>Material responses are not cross-engine calibrated</dd></div>
          </dl>
          <a href="cloth-comparison.html">Open cloth configurations, failures and evidence limits →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-incline" data-evidence="incline" data-evidence-reveal role="region" aria-labelledby="evidence-incline-title">
        <header class="evidence-panel-head">
          <span>05</span>
          <strong>Six-engine incline</strong>
          <small>Per configuration</small>
        </header>
        <div class="evidence-media">
          <img src="../../zh-cn/latest/_static/studio/incline.gif" alt="Six-engine incline comparison record" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Solver / same-task response</p>
          <h3 id="evidence-incline-title">Contact representation and numerical gates still change the result.</h3>
          <p class="evidence-verdict">Static, sliding and nominally frictionless cases are decided per profile rather than as one engine total.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Three contact conditions and three steps across six fixed engine profiles</dd></div>
            <div><dt>Native readback</dt><dd>Displacement, velocity, support force, geometric overlap and observation validity</dd></div>
            <div><dt>Criterion</dt><dd><strong>Passes, failures and invalid records remain separate</strong></dd></div>
            <div><dt>Scope</dt><dd>Different protocols and budgets do not form a universal solver ranking</dd></div>
          </dl>
          <a href="visual-comparisons.html#incline">Open synchronized replay, curves and the complete matrix →</a>
        </div>
      </article>
  </div>
</section>

<section class="home-answers" aria-labelledby="answer-heading">
  <section id="research-diagnosis"></section>
  <header class="home-section-head">
    <p>Three conclusions</p>
    <h2 id="answer-heading">Read these three judgments first.</h2>
  </header>
  <div class="home-answer-grid">
    <article id="experiment-findings">
      <span>01 / Experiment findings</span>
      <h3>Results are failure boundaries, not engine rankings.</h3>
      <p>Contact model, geometry, coupling and assisted retention can change the task verdict. Smaller steps and more iterations are not universal fixes.</p>
      <a href="experiments.html">Open the experiment catalogue →</a>
    </article>
    <article id="solver-map">
      <span>02 / Solver understanding</span>
      <h3>Separate engine, model, coupling and numerical configuration.</h3>
      <p>A name can belong to different layers. Profiles become comparable only after versions, contact representation, budgets and runtime readbacks are frozen.</p>
      <a href="solver-taxonomy.html">Read the solver taxonomy →</a>
    </article>
    <article id="root-causes">
      <span>03 / Sim-to-Real Gap</span>
      <h3>The simulation gap begins before the engine.</h3>
      <p>Check task definition, parameter delivery and force budgets through contact, scoring and hardware validation. Keep unresolved mechanisms explicit.</p>
      <a href="failure-root-cause-atlas.html">Read the Sim-to-Real Gap guide →</a>
    </article>
  </div>
</section>

<section class="home-next" aria-labelledby="next-heading">
  <section id="research-selection"></section>
  <span id="blog-guide"></span>
  <span id="blog-policy"></span>
  <span id="blog-learn"></span>
  <header class="home-section-head">
    <p>Keep exploring</p>
    <h2 id="next-heading">Continue by need.</h2>
  </header>
  <div class="home-next-grid">
    <a href="experiments.html"><strong>All experiments</strong><span>Tasks, protocols, results and retained failures</span></a>
    <a href="../../zh-cn/latest/_static/research/dexterous-simulation.html"><strong>Research guide</strong><span>Six layers of dexterous simulation</span></a>
    <a href="learning.html"><strong>Learn simulation</strong><span>MuJoCo route and six engine courses</span></a>
  </div>
</section>

<section class="home-validity" id="physical-validity" aria-labelledby="validity-heading">
  <header class="home-section-head">
    <p>Validation boundary</p>
    <h2 id="validity-heading">No hardware experiments.<br>How is physical correctness checked?</h2>
    <span>Claim limit: reproducible physical consistency inside a frozen simulation model.</span>
  </header>

  <div class="validity-boundary">
    <strong>Hardware experiments: 0</strong>
    <div>
      <p><strong>DexLab's claim:</strong> physical correctness is not a single “simulation succeeded” score. It is a chain of independently falsifiable checks: declared values reach the engine; units, mass, inertia and joint limits stay plausible; conservation and timestep perturbations do not produce contradictory behavior; contact and object responses stay inside physical bounds; and task scoring rejects idle, near-miss, hidden-support and wrong carry/reset shortcuts.</p>
      <p>Passing them establishes reproducible consistency inside a frozen model; it does not prove sim-to-real. Without real sensor, robot or material data, we report neither real-material error, hardware timing error nor a reality gap. A hardware experiment remains the external validity check. <a href="https://github.com/huangkiki/Dexlab/discussions/388">Read the full evidence chain, failure cases and limits in Discussion #388 →</a></p>
    </div>
    <a href="https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.zh-CN.md">View the hardware protocol →</a>
  </div>

  <p><a class="lab-button" href="https://github.com/huangkiki/Dexlab/discussions">Explore DexLab Discussions <span aria-hidden="true">→</span></a></p>

  <ol class="validity-chain" data-reveal-group>
    <li data-reveal-item>
      <span>Freeze the input</span>
      <h3>First prove the same object is computed.</h3>
      <p>Record versions, source and asset hashes, units, scale, mass and inertia, initial state and control timing. Missing fields stay unknown rather than being filled with defaults.</p>
    </li>
    <li data-reveal-item>
      <span>Positive and negative controls</span>
      <h3>A positive passes and a negative is rejected.</h3>
      <p>Controls share the same initial state and actions; only the tested condition is removed or replaced. A negative that accidentally passes invalidates the check.</p>
    </li>
    <li data-reveal-item>
      <span>Native readback</span>
      <h3>Visuals explain; numbers decide.</h3>
      <p>Independently check penetration, contact force, supporting object, momentum and angular-momentum residuals, actuation saturation and task stage. Similar pixels do not imply equivalent physics.</p>
    </li>
    <li data-reveal-item>
      <span>Parameter regression</span>
      <h3>Change one declared variable and rerun the full gate.</h3>
      <p>Freeze thresholds and variables before the run. After a change, rerun task positives and negatives, base response, conservation checks and prior regressions. Do not reuse old passes or delete failures.</p>
    </li>
  </ol>

  <div class="validity-records" data-reveal-group>
    <article class="validity-record" data-reveal-item>
      <header>
        <p>01 / Cutting and pushing</p>
        <h3>Visible knife contact must explain the displacement.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>The final cut preserves three or four connected pieces, then checks active-piece displacement, knife impulse, cut history and native state. Motion and force come from stored simulation state; no material velocity is injected. The full positive passes 18 checks and the no-push negative is rejected.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>At a fixed timestep, only viscosity changes from η=0 to 5 Pa·s. The complete 6 s acceptance and no-push control are rerun, plus shear, volumetric, objectivity, rigid-motion, momentum and discrete-dissipation tests. Eighteen zero-viscosity material steps remain bit-identical and seven elastic records remain unchanged. Half-step behavior is sensitivity evidence, not convergence.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>Material values are synthetic and not calibrated to tofu or banana. Initial gravity settling is retained; local jitter improvement does not establish real damping or accurate knife contact force.</dd>
        </div>
      </dl>
      <a href="cut-push.html">Open the cutting protocol →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>02 / Contact torque</p>
        <h3>Change only the contact model, then test hold, release and negatives.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>With the same hand, controller and action, only the ball contact changes from point to torsional. Independent checks cover continuous two-pad contact, the 2 mm hold limit, active release, single-finger unloading, open/no-contact/zero-friction negatives, linear momentum and angular momentum.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>Torsional parameters are frozen before the run; they are not swept to fit the result. v4 changes only the contact model and reruns six development controls. Historical v1–v3 failures and 15 unrun cases remain visible and are not backfilled.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>The ball, pads and torsional patch are synthetic. v4 still drifts slowly; passing a two-second window does not prove indefinite holding or a real fingertip material.</dd>
        </div>
      </dl>
      <a href="wuji-contact.html">Open the torsional-contact comparison →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>03 / Apple-stem grasp</p>
        <h3>Ten fixed regressions allow only two fingertips to support the apple.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>MuJoCo and SuperDex use the same ten fixed cases, including each frozen apple mass and pose, plus the same scripted action. Twenty-three checks cover a free rigid body with no attachment or object actuation, lift, two SDF pads supporting through hold, no table or other support, bounded penetration, retention, release and momentum balance.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>Timestep changes rerun the full checks, not only the video. MuJoCo covers 0.125/0.25/0.5 ms and SuperDex covers 0.5/1/2 ms. MuJoCo at 0.25 ms remains a retained penetration failure, showing the gate can reject a candidate. The regression suite is frozen before evaluation and the test split is not used to retune.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>MuJoCo 1/10 and SuperDex 10/10 describe two fixed configurations only. Stem deformation, fracture, real friction material and hardware precision are not validated, and this is not a universal engine ranking.</dd>
        </div>
      </dl>
      <a href="experiments.html#apple-replays">Open the apple-grasp records →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>04 / Cloth</p>
        <h3>Deformation, penetration, residual motion and cost are separate checks.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>Seven configurations share hanging and sphere-drape tasks in 105 frozen records. Checks cover protocol, shape, oscillation, surface crossing, penetration, residual motion and cost. Playback reads stored vertices; the renderer performs zero physics steps and never moves vertices to hide penetration.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>A material or solver change becomes a new profile and reruns all 15 cases for each task; old passes are not reused. The comparator rejects mismatched initial states, rest meshes or timelines. Different engine budgets prevent pass counts from becoming a physical-accuracy ranking.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>Materials are not cross-calibrated and 52/105 is not a real-fabric accuracy rate. A green result means the frozen protocol passed, not that real cloth parameters were identified.</dd>
        </div>
      </dl>
      <a href="cloth-comparison.html">Open the cloth comparison →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>05 / Six-engine incline</p>
        <h3>Read the analytic reference, three timesteps and invalid rows together.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>The same 40 mm, 64 g block is tested while static, sliding and at nominal zero friction, with 0.5/1/2 ms timesteps. Checks cover displacement, velocity, force and numerical consistency. The static friction inequality and <i>a</i>=<i>g</i>(sin θ−μ cos θ) are analytic or engineering references, not physical measurements.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>Timestep is already a nine-case cross design. Contact law, precision and execution path are frozen with each full profile. Positives, negatives, failures and invalid rows remain in the denominator; the best post-change result cannot replace history.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>Contact laws, budgets and applicability differ. Nine cases support per-profile decisions only; no engine passes all nine and the matrix is not a universal solver ranking.</dd>
        </div>
      </dl>
      <a href="visual-comparisons.html#incline">Open the six-engine matrix →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>06 / Calibration and transfer</p>
        <h3>A fixture-local calibration must be retested on another load.</h3>
      </header>
      <dl>
        <div>
          <dt>What it guarantees</dt>
          <dd>The same MuJoCo four-point contact fixture is checked against a synthetic 20 kN/m target. It starts near 80 kN/m and reaches about 20 kN/m after calibration. The unloaded separation segment remains in the dataset so gap motion is not miscounted as contact response.</dd>
        </div>
        <div>
          <dt>Regression after a parameter change</dt>
          <dd>Direct transfer to 0.1/0.4 kg gives 10.01/40.04 kN/m and fails as expected. A predeclared mass compensation gives 20.04/19.93 kN/m and passes again. Every change is checked on loading, unloading, separation and neighboring masses, not only on the calibrated load.</dd>
        </div>
        <div>
          <dt>What it cannot prove</dt>
          <dd>20 kN/m is a synthetic engineering target, not real stiffness. The result belongs only to this constant-impedance fixture and does not generalize to arbitrary geometry or real materials.</dd>
        </div>
      </dl>
      <a href="visual-comparisons.html#normal">Open the normal-response protocol →</a>
    </article>
  </div>
</section>

</div>
```

```{toctree}
:maxdepth: 1
:hidden:

Learn simulation <learning>
Project & documentation <about>
Getting started <quickstart>
Experiments <experiments>
Results & diagnosis <results>
Engines & models <engines>
Research guides <references>
Concept index <concepts/index>
Contributing <contributing>
```
