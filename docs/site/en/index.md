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

  <div class="home-evidence-grid" data-reveal-group>
    <article class="home-evidence-card home-evidence-card-wide" data-reveal-item>
      <div class="home-evidence-media home-evidence-split">
        <video controls muted loop playsinline preload="metadata" poster="../../zh-cn/latest/_static/cutting/tofu-cut-push/surface-rtx-poster.png" aria-label="Latest tofu two-cut and side-push recording">
          <source src="../../zh-cn/latest/_static/cutting/tofu-cut-push/surface-rtx.mp4" type="video/mp4">
        </video>
        <video controls muted loop playsinline preload="metadata" poster="../../zh-cn/latest/_static/cutting/banana-cut-push/surface-rtx-poster.png" aria-label="Latest banana three-cut and side-push recording">
          <source src="../../zh-cn/latest/_static/cutting/banana-cut-push/surface-rtx.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">01 / Cutting and pushing</p>
      <h3>Three or four pieces must move independently after the cuts.</h3>
      <p>Latest records: tofu becomes three pieces after two cuts; banana becomes four after three.</p>
    </article>
    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" aria-label="Wuji point and torsional contact comparison">
          <source src="../../zh-cn/latest/_static/wuji-contact/comparison.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">02 / Friction and torque</p>
      <h3>Persistent contact does not prevent rotation about the grasp line.</h3>
      <p>Point contact lacks the required torque direction; synthetic torsional contact brings retention back inside its original threshold.</p>
    </article>
    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" poster="../../zh-cn/latest/_static/studio/apple.png" aria-label="OpenArm and Wuji apple-stem grasp record">
          <source src="../../zh-cn/latest/_static/studio/apple.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">03 / Apple-stem grasping</p>
      <h3>A fixed task can still produce different outcomes across configurations.</h3>
      <p>Read MuJoCo and SuperDex differences together with step size, drive and contact representation.</p>
    </article>
    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" aria-label="Cloth grasp and motion record">
          <source src="../../zh-cn/latest/_static/cloth-studio/grasp.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">04 / Cloth</p>
      <h3>Grasping, lifting and completing a fold are separate checks.</h3>
      <p>Seven native configurations produced 105 frozen records; material responses are not cross-engine calibrated.</p>
    </article>
    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" poster="../../zh-cn/latest/_static/studio/incline.png" aria-label="Six-engine incline comparison record">
          <source src="../../zh-cn/latest/_static/studio/incline.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">05 / Six-engine incline</p>
      <h3>Contact representation and numerical gates still change the result.</h3>
      <p>Fixed profiles can be compared individually, but not combined into a universal solver ranking.</p>
    </article>
  </div>

  <div class="home-result-table" data-reveal-group>
    <table data-reveal-item>
      <caption>Controlled variables and acceptance results</caption>
      <thead><tr><th>Experiment</th><th>Controlled variable</th><th>Key readback</th><th>Result</th></tr></thead>
      <tbody>
        <tr><th>Cutting and pushing</th><td>Tofu 0.125 ms, η=5 Pa·s; banana 0.25 ms, η=0</td><td>Active-piece displacement; knife–material impulse</td><td><strong>Pass</strong><small>11.096 / 10.209 mm</small></td></tr>
        <tr><th>Contact torque</th><td>Point contact replaced only by torsional contact</td><td>Retention displacement; peak angular velocity</td><td><strong>2.734 → 1.025 mm</strong><small>29.336 → 0.024992 rad/s</small></td></tr>
        <tr><th>Apple grasp</th><td>Same set of ten fixed regression scenes</td><td>Lift, support, retention, penetration and release</td><td><strong>MuJoCo 1/10 · SuperDex 10/10</strong><small>Fixed profiles</small></td></tr>
        <tr><th>Cloth</th><td>Same frozen holdout set</td><td>Deformation, sag, penetration, residual motion and cost</td><td><strong>52 / 105 pass</strong><small>Materials not calibrated</small></td></tr>
        <tr><th>Six-engine incline</th><td>Static, sliding and nominal zero friction; three steps</td><td>Displacement, velocity, force and numerical consistency</td><td><strong>Per-profile verdicts</strong><small>No composite ranking</small></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="home-answers" aria-labelledby="answer-heading">
  <section id="research-diagnosis"></section>
  <header class="home-section-head">
    <p>Three conclusions</p>
    <h2 id="answer-heading">Read these three judgments first.</h2>
  </header>
  <div class="home-answer-grid" data-reveal-group>
    <article id="experiment-findings" data-reveal-item>
      <span>01 / Experiment findings</span>
      <h3>Results are failure boundaries, not engine rankings.</h3>
      <p>Contact model, geometry, coupling and assisted retention can change the task verdict. Smaller steps and more iterations are not universal fixes.</p>
      <a href="experiments.html">Open the experiment catalogue →</a>
    </article>
    <article id="solver-map" data-reveal-item>
      <span>02 / Solver understanding</span>
      <h3>Separate engine, model, coupling and numerical configuration.</h3>
      <p>A name can belong to different layers. Profiles become comparable only after versions, contact representation, budgets and runtime readbacks are frozen.</p>
      <a href="solver-taxonomy.html">Read the solver taxonomy →</a>
    </article>
    <article id="root-causes" data-reveal-item>
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
