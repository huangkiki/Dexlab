# DexLab

```{raw} html
<div class="home" id="top">
<section class="hero" aria-labelledby="hero-heading">
  <h1 id="hero-heading">Agents and simulation.<br>Improving together.</h1>
  <p class="hero-lead">What have we learned about contact-rich manipulation, what supports it, and what could it mean for your research? Read the findings, comparisons and limits.</p>
  <div class="hero-actions"><a class="button" href="#experiments">Read the findings</a><a class="text-link" href="#blog">Explore the research Blog</a></div>
  <div class="research-loop" aria-label="RSI research loop">
    <span>Try a task</span><span aria-hidden="true">→</span><span>Diagnose failure</span><span aria-hidden="true">→</span><span class="loop-fork">Improve skills · Improve simulation</span><span aria-hidden="true">→</span><span>Independently retest</span><span class="loop-return">↩ Ask the next question</span>
  </div>
  <p class="vision-note">The loop above explains how findings are produced and revised. Recursive self-improvement (RSI) is the research direction: humans set goals and boundaries; agents progressively help discover questions, experiment and iterate. Current capabilities are documented by individual experiments.</p>
</section>
<section class="feature" id="experiments" aria-labelledby="case-heading">
  <section id="research-findings"></section>
  <div class="section-heading"><div><h2 id="case-heading">Start with a finding.</h2><p>A Wuji grasp comparison: torsional contact capability changed this hold outcome.</p></div><a class="text-link" href="experience.html">More research findings</a></div>
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
  <details class="case-boundary"><summary>What does this result establish?</summary><p>The earliest identified issue is a structural gap in the contact wrench; offset gravity drives rotation about the contact line. The line is intuitively like an axis without torsional resistance, but moving fingers and contact points mean it is not a fixed hinge. The new law also acts during preparation, changing the initial state; this development comparison does not uniquely attribute all displacement to one degree of freedom.</p><p>The result is limited to the synthetic sphere, this controller and the two-second window; slow drift remains. Longer holds, contact switching and new validation conditions are the next tests. Real fingertip calibration and a complete autonomous RSI loop remain unverified.</p></details>
</section>
<section class="blog-section" id="blog" aria-labelledby="blog-heading">
  <section id="research-diagnosis"></section>
  <div class="section-heading"><div><h2 id="blog-heading">Follow the question.</h2><p>Read findings by question, understand their evidence and limits, and take the implications back to your research.</p></div><a class="text-link" href="_static/research/dexterous-simulation.html">Start with the research guide (中文)</a></div>
  <div class="topic-controls" hidden aria-label="Choose a Blog topic"><button type="button" data-topic="contact" aria-controls="topic-contact" aria-pressed="true">Contact & physics</button><button type="button" data-topic="diagnosis" aria-controls="topic-diagnosis" aria-pressed="false">Failure & evaluation</button><button type="button" data-topic="agents" aria-controls="topic-agents" aria-pressed="false">Agents & simulation</button></div>
  <section class="topic-panel" id="topic-contact" aria-labelledby="heading-contact"><div class="topic-intro"><h3 id="heading-contact">Why can a tighter grasp still slip?</h3><p>Start with the forces and torques a task needs, then examine models, parameters and solving.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="wuji-contact.html"><span>Point versus torsional contact: a grasp comparison</span><small>Change & retest</small></a></li><li><a href="contact-response.html"><span>Does lower prediction error reveal contact failures?</span><small>Offline diagnosis</small></a></li><li><a href="solver-taxonomy.html"><span>What belongs to the model, numerical problem or solver?</span><small>Concept guide</small></a></li></ol></section>
<section class="topic-panel" id="topic-diagnosis" aria-labelledby="heading-diagnosis"><div class="topic-intro"><h3 id="heading-diagnosis">When does task success mean better capability?</h3><p>Trace actions, state and forces to the first failing layer. Read task scores alongside physical evidence.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="failure-root-cause-atlas.html"><span>Failure atlas: finding the first failing layer</span><small>Topic index</small></a></li><li><a href="robodojo-bread-slip.html"><span>The gripper is closed. Why does the bread fall?</span><small>Case study</small></a></li><li><a href="rss-wiping.html"><span>Revisiting wiping without assisted retention</span><small>Controlled experiment</small></a></li></ol></section>
<section class="topic-panel" id="topic-agents" aria-labelledby="heading-agents"><div class="topic-intro"><h3 id="heading-agents">How can one failure inform the next improvement?</h3><p>Connect skills, observations, simulation and independent evaluation to choose the next test. A complete autonomous RSI loop remains a research direction.</p><a class="text-link" href="#learn">Connect to the learning map</a></div><ol class="reading-list"><li><a href="_static/research/dexterous-simulation.html#robodojo-astra"><span>RoboDojo / Astra: corrections and reliable contact control</span><small>Research Blog · Chinese</small></a></li><li><a href="_static/research/dexterous-simulation.html#shared-dexterous-tracking"><span>Sharing policies and dynamics across demonstrations</span><small>Research Blog · Chinese</small></a></li><li><a href="model-evaluation.html"><span>Separating the model, execution and scoring</span><small>Evaluation protocol</small></a></li></ol></section>

</section>
<section class="learning-section" id="learn" aria-labelledby="learn-heading">
  <section id="research-selection"></section>
  <div class="section-heading"><div><h2 id="learn-heading">Connect experiments to knowledge.</h2><p>Build intuition, then explore contact, solving and native engines. Courses live in Sim Learning.</p></div><a class="text-link" href="https://github.com/huangkiki/sim-learning">Sim Learning</a></div>
  <ol class="learning-map"><li><span class="step-number">1</span><h3>Build physical intuition</h3><p>State, time & dynamics</p><small>Start: vectors, matrices & basic mechanics</small><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/physics-based-simulation.md">Physics-Based Simulation study route</a></li><li><span class="step-number">2</span><h3>Understand contact & friction</h3><p>Geometry, forces, torques & constraints</p><small>Prerequisite: physical and state foundations</small><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/solver-guide/02-contact.md">Contact lesson</a></li><li><span class="step-number">3</span><h3>Read the numerical problem</h3><p>Equations, iteration, steps & tolerances</p><small>Prerequisite: contact models & linear algebra</small><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/solver-guide/README.md">Nine-part solver guide</a></li><li><span class="step-number">4</span><h3>Explore a native engine</h3><p>Use the API and trace the source</p><small>Continue along the application or theory route</small><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/learning-paths.md">Choose an engine learning path</a></li></ol>
  <div class="engine-paths"><span>Choose an engine to explore</span><div><a href="https://github.com/huangkiki/mujoco-learning/blob/main/docs/curriculum.md">MuJoCo</a><a href="https://github.com/huangkiki/superdex-learning/blob/main/docs/curriculum.md">SuperDex</a><a href="https://github.com/huangkiki/genesis-learning/blob/main/docs/curriculum.md">Genesis</a><a href="https://github.com/huangkiki/newton-learning/blob/main/docs/curriculum.md">Newton Physics</a><a href="https://github.com/huangkiki/physx-learning/blob/main/docs/curriculum.md">PhysX</a><a href="https://github.com/huangkiki/drake-learning/blob/main/docs/curriculum.md">Drake</a></div></div>
  <div class="knowledge-bridges"><h3>Go deeper through the related concepts.</h3><ul><li><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/solver-guide/03-friction.md">Friction & contact torque</a><span aria-label="related experiment">↔</span><a href="wuji-contact.html">Wuji grasp comparison</a></li><li><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/solver-guide/07-representations.md">Deformation & coupling</a><span aria-label="related experiment">↔</span><a href="cloth-comparison.html">Cloth experiments</a></li><li><a href="https://github.com/huangkiki/sim-learning/blob/main/docs/solver-guide/01-simulation-step.md">State, stepping & observations</a><span aria-label="related experiment">↔</span><a href="libero-workflow.html">LIBERO record checks</a></li></ul></div>
  <p class="language-note">Sim Learning courses are primarily in Chinese, with English terminology and reading summaries.</p>
</section>
<section id="research-scope"></section>
<section class="continue-section"><div><h2>Take one finding into the next question.</h2><p>Continue through the Blog for findings, evidence and implications. Full reports, data and reproduction guides are available when you want to inspect the details.</p></div><a class="button" href="#blog">Browse the research Blog</a></section>
<nav class="technical-links" aria-label="Technical documentation"><a id="architecture" href="about.html#architecture">Architecture</a><a id="quickstart" href="quickstart.html">Setup & reproduction</a><a id="model-evaluation" href="model-evaluation.html">Evaluation protocol</a><a id="documentation-and-citation" href="about.html#documentation-and-citation">About & citation</a><a id="live-lab" href="about.html#live-lab">Browser demo</a></nav>
</div>
```

```{toctree}
:maxdepth: 1
:hidden:

Project & documentation <about>
Getting started <quickstart>
Experiments <experiments>
Results & diagnosis <results>
Engines & models <engines>
Research guides <references>
Contributing <contributing>
```
