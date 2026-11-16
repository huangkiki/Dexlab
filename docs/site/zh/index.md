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
        <picture>
          <source srcset="_static/images/dexlab-architecture.webp" type="image/webp">
          <img src="_static/images/dexlab-architecture.png" width="1774" height="887" loading="eager" decoding="async" alt="DexLab 架构图：任务与协议、被测系统、动作执行、环境后端、证据与评分，以及返回系统改进的观测链">
        </picture>
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
    <h2 id="map-heading">从这里开始。</h2>
    <p>首页解释项目与架构；Blog 记录实验与失败；学习页从仿真基础开始。</p>
  </header>

  <div class="reading-paths">
    <a class="reading-path" href="#architecture">
      <span>01 / 项目</span>
      <strong>DexLab 是什么，以及任务如何走到证据。</strong>
      <small>项目定位、系统架构与研究闭环</small>
    </a>
    <a class="reading-path" href="blog.html">
      <span>02 / Blog</span>
      <strong>看实验、Solver 边界与失败根因。</strong>
      <small>画面、判据、对照矩阵与完整文章目录</small>
    </a>
    <a class="reading-path" href="learning.html">
      <span>03 / 学习</span>
      <strong>从时间、接触与数值求解开始。</strong>
      <small>MuJoCo 路线与六个引擎课程</small>
    </a>
  </div>
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
