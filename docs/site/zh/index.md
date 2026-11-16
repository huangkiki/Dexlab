# DexLab

```{raw} html
<div class="home story-home" id="top">
<section class="story-hero" aria-labelledby="home-heading">
  <div class="hero-copy">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis"><span>让智能体与仿真，</span><strong>在实验中共同进化。</strong></p>
    <p class="hero-lead">我关注智能体如何通过实验改进操作技能与物理仿真。由人确定目标与边界，让智能体参与问题发现、实验和迭代；完整自主闭环尚未验证，已有成果以具体实验为准。</p>
  </div>
  <a class="directory-entry" href="blog.html">
    <span class="directory-action">打开研究内容目录</span>
    <span class="directory-summary">也可以继续往下，先看 DexLab 如何从失败走到可独立复验的结论。</span>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
  <div class="scroll-note" aria-hidden="true"><span>向下滚动</span><i></i></div>
</section>

<section class="architecture-view" aria-labelledby="architecture-heading">
  <header class="architecture-intro">
    <h2 id="architecture-heading">从任务，<br>到可复核的证据。</h2>
    <p>DexLab 把任务与协议、被测系统、动作执行、环境后端和证据评分放在同一条链上。观测与失败记录再返回技能和仿真，形成下一轮实验。</p>
  </header>
  <figure class="architecture-figure">
    <p class="architecture-scroll-hint">横向滑动查看完整架构</p>
    <div class="architecture-scroll" tabindex="0" role="region" aria-label="DexLab 系统架构图，可横向滚动">
      <a class="architecture-image-link" href="_static/images/dexlab-architecture.png" target="_blank" rel="noopener" aria-label="打开 DexLab 架构图原图">
        <img src="_static/images/dexlab-architecture.png" width="1774" height="887" loading="lazy" alt="DexLab 架构图：任务与协议、被测系统、动作执行、环境后端、证据与评分，以及返回系统改进的观测链">
      </a>
    </div>
    <figcaption><span>系统全景：任务进入执行栈与物理后端，观测和证据返回技能与仿真改进。移动端可横向滑动，也可以打开原图。</span><a href="_static/images/dexlab-architecture.png" target="_blank" rel="noopener">查看原图</a></figcaption>
  </figure>
</section>

<section class="loop-story" aria-labelledby="loop-heading">
  <div class="loop-intro">
    <h2 id="loop-heading">一个结论，<br>不是一次运行。</h2>
    <p>每次实验既可能暴露技能缺口，也可能暴露仿真缺口。沿最早的失效层定位原因，再把修复放回独立条件中复验。</p>
    <p class="loop-current"><span>当前路径</span><strong data-loop-current>任务试验 → 独立复验</strong></p>
  </div>
  <ol class="loop-route">
    <li data-loop-step="任务试验" data-loop-label="任务试验">
      <span class="step-mark">01</span>
      <h3>任务先失败</h3>
      <p>真实任务暴露抓取、接触、控制或策略的问题，而不是先挑一个指标。</p>
    </li>
    <li data-loop-step="第一失效层" data-loop-label="第一失效层">
      <span class="step-mark">02</span>
      <h3>找到第一失效层</h3>
      <p>沿动作、状态与受力向前追，分清主因、放大器和仍不确定的机制。</p>
    </li>
    <li data-loop-step="改进技能或仿真" data-loop-label="改进技能或仿真">
      <span class="step-mark">03</span>
      <h3>改进技能，或改进仿真</h3>
      <p>修复对应的策略、执行边界或物理模型；每条证据分别保存。</p>
    </li>
    <li data-loop-step="独立复验" data-loop-label="独立复验">
      <span class="step-mark">04</span>
      <h3>重新独立复验</h3>
      <p>换条件重测。任务成功、视觉通过和物理解释不能互相替代。</p>
    </li>
  </ol>
</section>

<section class="reading-map" aria-labelledby="map-heading">
  <header class="map-intro">
    <h2 id="map-heading">沿着问题往下读。</h2>
    <p>先看到分类，再看到具体标题。下面这五组入口直接展开，不需要先进入某个分类页。</p>
  </header>

  <div class="topic-clusters">
    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>研究导读</h3>
        <p>先理解灵巧操作仿真的问题层次，再决定从哪篇实验读起。</p>
      </div>
      <ul class="topic-links">
        <li><a href="_static/research/dexterous-simulation.html">当我们在讨论灵巧操作仿真时，我们在讨论什么？</a></li>
        <li><a href="_static/research/dexterous-simulation.html#layers">六层问题：从接触、策略到真实迁移</a></li>
        <li><a href="_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons">CoRL 2026：DexLab 的阅读结论</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>接触与物理</h3>
        <p>先问任务需要什么力、力矩和接触历史，再讨论模型、参数与 solver。</p>
      </div>
      <ul class="topic-links">
        <li><a href="wuji-contact.html">点接触与抗扭接触：一次抓持对照</a></li>
        <li><a href="contact-response.html">预测误差更低，就能预报接触失效吗？</a></li>
        <li><a href="solver-taxonomy.html">物理模型、数值问题与 solver，分别负责什么？</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>失败与诊断</h3>
        <p>沿动作、状态和受力追踪第一失效层，把任务评分与物理证据放在一起读。</p>
      </div>
      <ul class="topic-links">
        <li><a href="failure-root-cause-atlas.html">失败根因图谱：沿着证据找第一失效层</a></li>
        <li><a href="robodojo-bread-slip.html">闭爪命令正确，面包为什么仍会掉？</a></li>
        <li><a href="rss-wiping.html">去掉辅助保持，再看擦拭任务</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>策略、技能与评测</h3>
        <p>先确定动作由谁生成、执行边界在哪里、经验保存在哪里，再用独立证据判断它是否有效。</p>
      </div>
      <ul class="topic-links">
        <li><a href="code-as-policy.html">Code as Policy：四种系统形态</a></li>
        <li><a href="_static/research/dexterous-simulation.html#capx-aspire">CaP-X / ASPIRE：从 trace 到技能晋升</a></li>
        <li><a href="model-evaluation.html">怎样把模型、执行与评分分开？</a></li>
      </ul>
    </article>

    <article class="topic-cluster">
      <div class="topic-heading">
        <h3>仿真学习</h3>
        <p>从 MuJoCo 的时间、接触和数值求解开始，再沿同一套问题进入其他引擎课程。</p>
      </div>
      <ul class="topic-links">
        <li><a href="learning.html">MuJoCo：从时间、接触到性能的学习路线</a></li>
        <li><a href="learn/sim/docs/physics-based-simulation.html">Physics-Based Simulation 伴读</a></li>
        <li><a href="learn/sim/docs/solver-guide/README.html">九单元 Solver 教程</a></li>
      </ul>
    </article>
  </div>

  <a class="full-index" href="blog.html">
    <span>完整内容目录</span>
    <strong>还有实验记录、策略评测、其他引擎课程与研究资料</strong>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
</section>
</div>
```

```{toctree}
:maxdepth: 1
:hidden:

仿真学习 <learning>
项目与技术文档 <about>
安装与复现 <quickstart>
实验目录 <experiments>
结果与诊断 <results>
引擎与模型 <engines>
Blog <blog>
研究资料 <references>
参与项目 <contributing>
```
