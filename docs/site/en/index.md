# DexLab

```{raw} html
<div class="home" id="top">
<section class="hero" aria-labelledby="hero-heading">
  <h1 id="hero-heading"><a href="_static/research/dexterous-simulation.html">What are we talking about <br>when we talk about <br>dexterous simulation?</a></h1>
  <p class="hero-lead">From contact and touch to policies, evaluation and real-world transfer. A guide to the papers, projects and evidence behind dexterous simulation.</p>
  <a class="guide-link" href="_static/research/dexterous-simulation.html">Read the research guide<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
  <nav class="guide-chapters" aria-label="Guide chapters"><a href="_static/research/dexterous-simulation.html#layers">Six layers of the problem</a><a href="_static/research/dexterous-simulation.html#simulation-benchmarks-2026">Simulation benchmarks</a><a href="_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons">CoRL 2026</a></nav>
  <p class="guide-language">The research guide is in Chinese.</p>
</section>
<section class="research-direction" aria-labelledby="direction-heading">
  <h2 id="direction-heading">Agents and simulation, improving together.</h2>
  <div class="research-loop" aria-label="Experiment and improvement process">
    <span>Try a task</span><span aria-hidden="true">→</span><span>Diagnose failure</span><span aria-hidden="true">→</span><span class="loop-fork">Improve skills · Improve simulation</span><span aria-hidden="true">→</span><span>Independently retest</span><span class="loop-return">↩ Ask the next question</span>
  </div>
  <p class="vision-note">I study how agents can help improve manipulation skills and physics simulation through experiments: humans set goals and boundaries; agents help identify questions, experiment and iterate. A complete autonomous loop remains unverified; current results come from individual experiments.</p>
</section>
<section class="feature" id="experiments" aria-labelledby="case-heading">
  <section id="research-findings"></section>
  <div class="section-heading"><div><h2 id="case-heading">Research findings</h2></div><a class="text-link" href="experience.html">More research findings</a></div>
  <div class="case-grid">
    <figure class="case-media"><video controls playsinline preload="none" width="896" height="504" poster="_static/research-home-wuji.png" aria-label="Original-speed Wuji point-contact versus synthetic torsional-contact replay"><source src="_static/wuji-contact/comparison.mp4" type="video/mp4"><a href="_static/wuji-contact/comparison.mp4">Download the original replay</a></video><figcaption>Recorded replay · Left: point contact / right: synthetic torsion · Same time, original speed · Click to play</figcaption></figure>
    <div class="case-story"><h3>Adding torsional contact passed the hold check.</h3>
    <ol class="case-sequence">
      <li><strong>Finding</strong><p>With the same controller, synthetic torsional contact reduces maximum two-second drift from 2.734 to 1.025 mm, passing the original 2 mm limit and active-release checks.</p></li>
      <li><strong>Evidence</strong><p>Both original point contacts persist but lack torque about their connecting line. Offset gravity drives rotation and the hold fails; more normal force does not add that missing direction.</p></li>
      <li><strong>Takeaway</strong><p>For this kind of grasp failure, check whether the contact model can supply the required torque before discussing parameters or solving. This comparison uses existing MuJoCo capability; the solver is unchanged.</p></li>
      <li><strong>Scope</strong><p>The finding is limited to this synthetic contact and two-second window; slow drift remains. The new law also affects preparation, so not all displacement can be uniquely attributed to one degree of freedom.</p></li>
    </ol><a class="text-link" href="wuji-contact.html">Read the analysis and evidence</a></div>
  </div>
  <details class="case-boundary"><summary>What does this result establish?</summary><p>The earliest identified issue is a structural gap in the contact wrench; offset gravity drives rotation about the contact line. The line is intuitively like an axis without torsional resistance, but moving fingers and contact points mean it is not a fixed hinge. The new law also acts during preparation, changing the initial state; this development comparison does not uniquely attribute all displacement to one degree of freedom.</p><p>The result is limited to the synthetic sphere, this controller and the two-second window; slow drift remains. Longer holds, contact switching and new validation conditions are the next tests. Real fingertip calibration and a complete autonomous improvement process remain unverified.</p></details>
</section>
<section class="blog-section" id="blog" aria-labelledby="blog-heading">
  <section id="research-diagnosis"></section>
  <div class="section-heading"><div><h2 id="blog-heading">Follow a research question</h2></div><a class="text-link" href="_static/research/dexterous-simulation.html">Start with the research guide (中文)</a></div>
  <div class="topic-controls" hidden aria-label="Choose a Blog topic"><button type="button" data-topic="contact" aria-controls="topic-contact" aria-pressed="true">Contact & physics</button><button type="button" data-topic="diagnosis" aria-controls="topic-diagnosis" aria-pressed="false">Failure & evaluation</button><button type="button" data-topic="agents" aria-controls="topic-agents" aria-pressed="false">Agents & simulation</button></div>
  <section class="topic-panel" id="topic-contact" aria-labelledby="heading-contact"><div class="topic-intro"><h3 id="heading-contact">Why can a tighter grasp still slip?</h3><p>Start with the forces and torques a task needs, then examine models, parameters and solving.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="wuji-contact.html"><span>Point versus torsional contact: a grasp comparison</span></a></li><li><a href="contact-response.html"><span>Does lower prediction error reveal contact failures?</span></a></li><li><a href="solver-taxonomy.html"><span>What belongs to the model, numerical problem or solver?</span></a></li></ol></section>
<section class="topic-panel" id="topic-diagnosis" aria-labelledby="heading-diagnosis"><div class="topic-intro"><h3 id="heading-diagnosis">When does task success mean better capability?</h3><p>Trace actions, state and forces to the first failing layer. Read task scores alongside physical evidence.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="failure-root-cause-atlas.html"><span>Failure atlas: finding the first failing layer</span></a></li><li><a href="robodojo-bread-slip.html"><span>The gripper is closed. Why does the bread fall?</span></a></li><li><a href="rss-wiping.html"><span>Revisiting wiping without assisted retention</span></a></li></ol></section>
<section class="topic-panel" id="topic-agents" aria-labelledby="heading-agents"><div class="topic-intro"><h3 id="heading-agents">How can one failure inform the next improvement?</h3><p>Connect skills, observations, simulation and independent evaluation to choose the next test. A complete autonomous improvement process remains a research direction.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="_static/research/dexterous-simulation.html#robodojo-astra"><span>RoboDojo / Astra: corrections and reliable contact control</span></a></li><li><a href="_static/research/dexterous-simulation.html#shared-dexterous-tracking"><span>Sharing policies and dynamics across demonstrations</span></a></li><li><a href="model-evaluation.html"><span>Separating the model, execution and scoring</span></a></li></ol></section>

</section>
<section class="learning-section" id="learn" aria-labelledby="learn-heading">
  <section id="research-selection"></section>
  <div class="section-heading"><div><h2 id="learn-heading">Simulation learning</h2><p>Start with MuJoCo: learn time, contact and solving through an interactive example and self-checks, then explore the detailed courses and version 4.</p></div><a class="text-link" href="learning.html">Start learning MuJoCo</a></div>
  <ol class="learning-map"><li><span class="step-number">1</span><h3>Build physical intuition</h3><p>State, time & dynamics</p><small>Start: vectors, matrices & basic mechanics</small><a href="learn/sim/docs/physics-based-simulation.html">Physics-Based Simulation study route</a></li><li><span class="step-number">2</span><h3>Understand contact & friction</h3><p>Geometry, forces, torques & constraints</p><small>Prerequisite: physical and state foundations</small><a href="learn/sim/docs/solver-guide/02-contact.html">Contact lesson</a></li><li><span class="step-number">3</span><h3>Read the numerical problem</h3><p>Equations, iteration, steps & tolerances</p><small>Prerequisite: contact models & linear algebra</small><a href="learn/sim/docs/solver-guide/README.html">Nine-part solver guide</a></li><li><span class="step-number">4</span><h3>Explore a native engine</h3><p>Use the API and trace the source</p><small>Continue along the application or theory route</small><a href="learn/sim/docs/learning-paths.html">Choose an engine learning path</a></li></ol>
  <div class="engine-paths"><span>Choose an engine to explore</span><div><a href="learning.html">MuJoCo</a><a href="learn/superdex/docs/curriculum.html">SuperDex</a><a href="learn/genesis/docs/curriculum.html">Genesis</a><a href="learn/newton/docs/curriculum.html">Newton Physics</a><a href="learn/physx/docs/curriculum.html">PhysX</a><a href="learn/drake/docs/curriculum.html">Drake</a></div></div>
  <div class="knowledge-bridges"><h3>Go deeper through the related concepts.</h3><ul><li><a href="learn/sim/docs/solver-guide/03-friction.html">Friction & contact torque</a><span aria-label="related experiment">↔</span><a href="wuji-contact.html">Wuji grasp comparison</a></li><li><a href="learn/sim/docs/solver-guide/07-representations.html">Deformation & coupling</a><span aria-label="related experiment">↔</span><a href="cloth-comparison.html">Cloth experiments</a></li><li><a href="learn/sim/docs/solver-guide/01-simulation-step.html">State, stepping & observations</a><span aria-label="related experiment">↔</span><a href="libero-workflow.html">LIBERO record checks</a></li></ul></div>
  <p class="language-note">Sim Learning courses are primarily in Chinese, with English terminology and reading summaries.</p>
</section>
<section id="research-scope"></section>
<nav class="technical-links" aria-label="Technical documentation"><a id="architecture" href="about.html#architecture">Architecture</a><a id="quickstart" href="quickstart.html">Setup & reproduction</a><a id="model-evaluation" href="model-evaluation.html">Evaluation protocol</a><a id="documentation-and-citation" href="about.html#documentation-and-citation">About & citation</a><a id="live-lab" href="about.html#live-lab">Browser demo</a></nav>
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
