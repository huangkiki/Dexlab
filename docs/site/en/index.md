# DexLab

```{raw} html
<div class="home story-home" id="top">
<section class="story-hero" aria-labelledby="home-heading">
  <div class="hero-copy">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis"><span>Agents and simulation,</span><strong>improving together through experiments.</strong></p>
    <p class="hero-lead">I study how agents can help improve manipulation skills and physics simulation through experiments. Humans set goals and boundaries; agents help identify questions, experiment and iterate. A complete autonomous loop remains unverified; current findings come from individual experiments.</p>
  </div>
  <a class="directory-entry" href="#experiments">
    <span class="directory-action">See experiments and findings</span>
    <span class="directory-summary">Representative comparisons, solver boundaries, failure causes and deeper reading in one page.</span>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
  <div class="scroll-note" aria-hidden="true"><span>Scroll to read</span><i></i></div>
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

  <div class="evidence-inspector" role="group" aria-label="Representative experiment evidence inspector">
    <input class="evidence-input" type="radio" name="home-evidence" id="evidence-cut" aria-controls="panel-cut" checked>
    <label class="evidence-choice" id="choice-cut" for="evidence-cut"><span>01</span><span><strong>Cutting and pushing</strong><small>11.096 / 10.209 mm</small></span></label>
    <input class="evidence-input" type="radio" name="home-evidence" id="evidence-wuji" aria-controls="panel-wuji">
    <label class="evidence-choice" id="choice-wuji" for="evidence-wuji"><span>02</span><span><strong>Contact and torsional moment</strong><small>2.734 → 1.025 mm</small></span></label>
    <input class="evidence-input" type="radio" name="home-evidence" id="evidence-apple" aria-controls="panel-apple">
    <label class="evidence-choice" id="choice-apple" for="evidence-apple"><span>03</span><span><strong>Apple-stem grasp</strong><small>1/10 · 10/10</small></span></label>
    <input class="evidence-input" type="radio" name="home-evidence" id="evidence-cloth" aria-controls="panel-cloth">
    <label class="evidence-choice" id="choice-cloth" for="evidence-cloth"><span>04</span><span><strong>Cloth</strong><small>52 / 105 pass</small></span></label>
    <input class="evidence-input" type="radio" name="home-evidence" id="evidence-incline" aria-controls="panel-incline">
    <label class="evidence-choice" id="choice-incline" for="evidence-incline"><span>05</span><span><strong>Six-engine incline</strong><small>Per configuration</small></span></label>

    <div class="evidence-panels">
      <article class="evidence-panel" id="panel-cut" data-evidence="cut" role="region" aria-labelledby="choice-cut">
        <div class="evidence-media evidence-media-split">
          <video controls muted loop playsinline preload="none" poster="../../zh-cn/latest/_static/cutting/tofu-cut-push/surface-rtx-poster.png" aria-label="Latest tofu two-cut and side-push recording"><source src="../../zh-cn/latest/_static/cutting/tofu-cut-push/surface-rtx.mp4" type="video/mp4"></video>
          <video controls muted loop playsinline preload="none" poster="../../zh-cn/latest/_static/cutting/banana-cut-push/surface-rtx-poster.png" aria-label="Latest banana three-cut and side-push recording"><source src="../../zh-cn/latest/_static/cutting/banana-cut-push/surface-rtx.mp4" type="video/mp4"></video>
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Cutting / separation criterion</p>
          <h3>After cutting, prove the final piece can move independently.</h3>
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

      <article class="evidence-panel" id="panel-wuji" data-evidence="wuji" role="region" aria-labelledby="choice-wuji">
        <div class="evidence-media">
          <video controls muted loop playsinline preload="none" poster="../../zh-cn/latest/_static/wuji-contact/hold-comparison.png" aria-label="Wuji point and torsional contact comparison"><source src="../../zh-cn/latest/_static/wuji-contact/comparison.mp4" type="video/mp4"></video>
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Contact / moment direction</p>
          <h3>Persistent contact does not prevent rotation about the grasp line.</h3>
          <p class="evidence-verdict">Point contact lacks the required torque direction; synthetic torsional contact brings retention back inside its original threshold.</p>
          <dl class="evidence-ledger">
            <div><dt>Control variable</dt><dd>Point contact replaced only by synthetic torsional contact</dd></div>
            <div><dt>Native readback</dt><dd>Two-second hold displacement and peak angular velocity</dd></div>
            <div><dt>Criterion</dt><dd><strong>2.734 → 1.025 mm; 29.336 → 0.024992 rad/s</strong></dd></div>
            <div><dt>Scope</dt><dd>Two-finger ball hold; not hardware material calibration or whole-hand capability</dd></div>
          </dl>
          <a href="wuji-contact.html">Open contact records, video and independent recomputation →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-apple" data-evidence="apple" role="region" aria-labelledby="choice-apple">
        <div class="evidence-media">
          <video controls muted loop playsinline preload="none" poster="../../zh-cn/latest/_static/studio/apple.png" aria-label="OpenArm and Wuji apple-stem grasp record"><source src="../../zh-cn/latest/_static/studio/apple.mp4" type="video/mp4"></video>
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Task / frozen disturbance set</p>
          <h3>A fixed task can still produce different outcomes across configurations.</h3>
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

      <article class="evidence-panel" id="panel-cloth" data-evidence="cloth" role="region" aria-labelledby="choice-cloth">
        <div class="evidence-media">
          <video controls muted loop playsinline preload="none" aria-label="Cloth grasp and motion record"><source src="../../zh-cn/latest/_static/cloth-studio/grasp.mp4" type="video/mp4"></video>
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Deformable body / staged acceptance</p>
          <h3>Grasping, lifting and completing a fold are separate checks.</h3>
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

      <article class="evidence-panel" id="panel-incline" data-evidence="incline" role="region" aria-labelledby="choice-incline">
        <div class="evidence-media">
          <video controls muted loop playsinline preload="none" poster="../../zh-cn/latest/_static/studio/incline.png" aria-label="Six-engine incline comparison record"><source src="../../zh-cn/latest/_static/studio/incline.mp4" type="video/mp4"></video>
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Solver / same-task response</p>
          <h3>Contact representation and numerical gates still change the result.</h3>
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
      <span>03 / Failure causes</span>
      <h3>Many “solver failures” are decided before iteration.</h3>
      <p>Check task, geometry, control and coupling before discretisation, residuals and scoring. Keep unresolved mechanisms explicitly labelled.</p>
      <a href="failure-root-cause-atlas.html">Open the failure atlas →</a>
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

<section class="home-contact" id="research-scope" aria-labelledby="contact-heading">
  <h2 id="contact-heading">Contact the author</h2>
  <nav aria-label="Contact the author">
    <a href="mailto:huangyue0719@outlook.com">Email</a>
    <a href="https://github.com/huangkiki">GitHub ↗</a>
  </nav>
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
Contributing <contributing>
```
