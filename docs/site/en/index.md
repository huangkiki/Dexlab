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
    <h2 id="map-heading">Keep reading by question.</h2>
    <p>See the categories and the article titles together. These five groups are already open; there is no category page to click through first.</p>
  </header>

  <div class="topic-clusters">
    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>Research guide</h3>
        <p>Start with the layers of the dexterous-simulation problem, then choose an experiment.</p>
      </div>
      <ul class="topic-links">
        <li><a href="../../zh-cn/latest/_static/research/dexterous-simulation.html" lang="zh-CN" hreflang="zh-CN">当我们在讨论灵巧操作仿真时，我们在讨论什么？</a></li>
        <li><a href="../../zh-cn/latest/_static/research/dexterous-simulation.html#layers" lang="zh-CN" hreflang="zh-CN">六层问题：从接触、策略到真实迁移</a></li>
        <li><a href="../../zh-cn/latest/_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons" lang="zh-CN" hreflang="zh-CN">CoRL 2026：DexLab 的阅读结论</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>Contact and physics</h3>
        <p>Establish the force, torque and contact history the task requires before tuning a model or solver.</p>
      </div>
      <ul class="topic-links">
        <li><a href="wuji-contact.html">Point versus torsional contact: a grasp comparison</a></li>
        <li><a href="contact-response.html">Can lower prediction error forecast contact loss?</a></li>
        <li><a href="solver-taxonomy.html">What belong to the physical model, numerical problem and solver?</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>Failure and diagnosis</h3>
        <p>Trace the first failing layer through action, state and force, with task scores and physical evidence together.</p>
      </div>
      <ul class="topic-links">
        <li><a href="failure-root-cause-atlas.html">Failure root-cause atlas</a></li>
        <li><a href="robodojo-bread-slip.html">Why can bread still slip after a correct grasp command?</a></li>
        <li><a href="rss-wiping.html">Remove assisted retention and revisit the wiping task</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>Policy, skills and evaluation</h3>
        <p>Identify who generates actions, where execution ends and where experience is stored before evaluating the system.</p>
      </div>
      <ul class="topic-links">
        <li><a href="code-as-policy.html">Code as Policy: four system forms</a></li>
        <li><a href="../../zh-cn/latest/_static/research/dexterous-simulation.html#capx-aspire" lang="zh-CN" hreflang="zh-CN">CaP-X / ASPIRE：从 trace 到技能晋升</a></li>
        <li><a href="model-evaluation.html">How should model, execution and scoring be separated?</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>Simulation learning</h3>
        <p>Begin with time, contact and numerical solving in MuJoCo, then follow the same questions into other engines.</p>
      </div>
      <ul class="topic-links">
        <li><a href="learning.html">MuJoCo learning route</a></li>
        <li><a href="learn/sim/docs/physics-based-simulation.html">Physics-Based Simulation study route</a></li>
        <li><a href="learn/sim/docs/solver-guide/README.html">Nine-part solver guide</a></li>
      </ul>
    </article>
  </div>

  <a class="full-index" href="../../zh-cn/latest/blog.html" lang="zh-CN" hreflang="zh-CN">
    <span>打开完整内容目录</span>
    <strong>实验记录、策略评测、其他引擎课程与研究资料</strong>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
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
