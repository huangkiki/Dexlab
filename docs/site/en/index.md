# DexLab

```{raw} html
<div class="home story-home" id="top">
<section class="story-hero" aria-labelledby="home-heading">
  <div class="hero-copy">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis"><span>Agents and simulation,</span><strong>improving together through experiments.</strong></p>
    <p class="hero-lead">I study how agents can help improve manipulation skills and physics simulation through experiments. Humans set goals and boundaries; agents help identify questions, experiment and iterate. A complete autonomous loop remains unverified; current findings come from individual experiments.</p>
  </div>
  <a class="directory-entry" href="../../zh-cn/latest/blog.html" lang="zh-CN" hreflang="zh-CN">
    <span class="directory-action">打开研究内容目录</span>
    <span class="directory-summary">Or keep scrolling to see how DexLab moves from a failure to an independently checked finding.</span>
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

<section class="loop-story" aria-labelledby="loop-heading">
  <div class="loop-intro">
    <h2 id="loop-heading">A finding is more<br>than a single run.</h2>
    <p>A task can expose a skill gap or a simulation gap. Locate the earliest failing layer, then put the fix back into an independent test.</p>
    <p class="loop-current"><span>Current path</span><strong data-loop-current>Task trial → Independent retest</strong></p>
  </div>
  <ol class="loop-route">
    <li data-loop-step="Task trial" data-loop-label="Task trial">
      <span class="step-mark">01</span>
      <h3>The task fails first</h3>
      <p>A real task exposes a grasp, contact, control or policy problem before a metric is chosen.</p>
    </li>
    <li data-loop-step="First failing layer" data-loop-label="First failing layer">
      <span class="step-mark">02</span>
      <h3>Find the first failing layer</h3>
      <p>Trace action, state and force backward; separate the primary cause, amplifiers and unresolved mechanisms.</p>
    </li>
    <li data-loop-step="Improve skill or simulation" data-loop-label="Improve skill or simulation">
      <span class="step-mark">03</span>
      <h3>Improve the skill or the simulation</h3>
      <p>Fix the policy, execution boundary or physics model, and retain the evidence for each change separately.</p>
    </li>
    <li data-loop-step="Independent retest" data-loop-label="Independent retest">
      <span class="step-mark">04</span>
      <h3>Retest independently</h3>
      <p>Change conditions and rerun. Task success, visual plausibility and physical explanation do not substitute for one another.</p>
    </li>
  </ol>
</section>

<section class="reading-map" aria-labelledby="map-heading">
  <header class="map-intro">
    <h2 id="map-heading">Start here.</h2>
    <p>The homepage explains the project and architecture; the Blog records experiments and failures; learning starts from simulation fundamentals.</p>
  </header>

  <div class="reading-paths">
    <a class="reading-path" href="#architecture-heading">
      <span>01 / Project</span>
      <strong>What DexLab is, and how a task becomes evidence.</strong>
      <small>Positioning, system architecture and research loop</small>
    </a>
    <a class="reading-path" href="../../zh-cn/latest/blog.html" lang="zh-CN" hreflang="zh-CN">
      <span>02 / Blog</span>
      <strong>Read experiments, solver boundaries and failure causes.</strong>
      <small>Recorded comparisons, criteria, matrices and the complete index</small>
    </a>
    <a class="reading-path" href="learning.html">
      <span>03 / Learn</span>
      <strong>Start with time, contact and numerical solving.</strong>
      <small>The MuJoCo route and courses for six engines</small>
    </a>
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
Contributing <contributing>
```
