# DexLab

```{raw} html
<div class="home story-home" id="top">
<section class="story-hero" aria-labelledby="home-heading">
  <div class="hero-copy">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis"><span>让智能体与仿真，</span><strong>在实验中共同进化。</strong></p>
    <p class="hero-lead">我关注智能体如何通过实验改进操作技能与物理仿真。由人确定目标与边界，让智能体参与问题发现、实验和迭代；完整自主闭环尚未验证，已有成果以具体实验为准。</p>
  </div>
  <a class="directory-entry" href="#experiments">
    <span class="directory-action">直接看实验与研究结论</span>
    <span class="directory-summary">同一页看完代表性实验、Solver 边界、失败根因和深读入口。</span>
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

<section class="home-evidence" id="experiments" aria-labelledby="evidence-heading">
  <section id="research-findings"></section>
  <span id="research-content"></span>
  <span id="evidence-feature"></span>
  <span id="blog-preview"></span>
  <header class="home-section-head">
    <p>Representative experiments</p>
    <h2 id="evidence-heading">从画面直接进入判据。</h2>
    <span>任务试验 → 第一失效层 → 修复 → 独立复验</span>
  </header>

  <div class="home-evidence-grid" data-reveal-group>
    <article class="home-evidence-card home-evidence-card-wide" data-reveal-item>
      <div class="home-evidence-media home-evidence-split">
        <video controls muted loop playsinline preload="metadata" poster="_static/cutting/tofu-cut-push/surface-rtx-poster.png" aria-label="豆腐两刀三块后直接侧推的最新记录">
          <source src="_static/cutting/tofu-cut-push/surface-rtx.mp4" type="video/mp4">
        </video>
        <video controls muted loop playsinline preload="metadata" poster="_static/cutting/banana-cut-push/surface-rtx-poster.png" aria-label="香蕉三刀四块后直接侧推的最新记录">
          <source src="_static/cutting/banana-cut-push/surface-rtx.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">01 / 切割与侧推</p>
      <h3>切完，仍要证明三块、四块能独立运动。</h3>
      <p>最新记录：豆腐两刀三块、香蕉三刀四块；最后一块不再被同一切面带动。</p>
    </article>

    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" aria-label="Wuji 点接触与抗扭接触的同时间原速比较">
          <source src="_static/wuji-contact/comparison.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">02 / 摩擦与抗扭力矩</p>
      <h3>一直有接触，球仍可能绕夹持线转动。</h3>
      <p>点接触缺少力矩方向；补上抗扭接触后，保持才进入原定门槛。</p>
    </article>

    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" poster="_static/studio/apple.png" aria-label="OpenArm 与 Wuji 苹果梗抓取记录">
          <source src="_static/studio/apple.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">03 / 苹果梗抓取</p>
      <h3>同一条抓梗任务，固定配置仍可能给出不同结果。</h3>
      <p>MuJoCo 与 SuperDex 的差异必须连同步长、驱动和接触表示一起读。</p>
    </article>

    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" aria-label="布料夹持与运动记录">
          <source src="_static/cloth-studio/grasp.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">04 / 布料</p>
      <h3>夹住、抬起与完成折叠是三个不同验收。</h3>
      <p>7 个原生配置共 105 条冻结记录；材料未做跨求解器等效标定。</p>
    </article>

    <article class="home-evidence-card" data-reveal-item>
      <div class="home-evidence-media">
        <video controls muted loop playsinline preload="metadata" poster="_static/studio/incline.png" aria-label="六引擎斜面同步比较记录">
          <source src="_static/studio/incline.mp4" type="video/mp4">
        </video>
      </div>
      <p class="home-evidence-label">05 / 六引擎斜面</p>
      <h3>同一任务，接触表达和数值门禁仍会改变结果。</h3>
      <p>固定配置可以逐项比较，但不能拼成通用 solver 排名。</p>
    </article>
  </div>

  <div class="home-result-table" data-reveal-group>
    <table data-reveal-item>
      <caption>代表性实验的控制变量与验收结果</caption>
      <thead><tr><th>实验</th><th>控制变量</th><th>关键读回</th><th>结果</th></tr></thead>
      <tbody>
        <tr><th>切割与侧推</th><td>豆腐 0.125 ms、η=5 Pa·s；香蕉 0.25 ms、η=0</td><td>活动块相对位移；刀面接触冲量</td><td><strong>通过</strong><small>11.096 / 10.209 mm</small></td></tr>
        <tr><th>接触力矩</th><td>只把点接触改为抗扭接触</td><td>保持位移；峰值角速度</td><td><strong>2.734 → 1.025 mm</strong><small>29.336 → 0.024992 rad/s</small></td></tr>
        <tr><th>苹果抓取</th><td>同一组 10 个固定回归场景</td><td>离桌、支撑、保持、穿透与释放</td><td><strong>MuJoCo 1/10 · SuperDex 10/10</strong><small>固定配置</small></td></tr>
        <tr><th>布料</th><td>同一冻结留出集</td><td>形变、下垂、穿透、残余运动与成本</td><td><strong>52 / 105 通过</strong><small>材料未等效标定</small></td></tr>
        <tr><th>六引擎斜面</th><td>静止、滑动与名义零摩擦；三个步长</td><td>位移、速度、力与数值一致性</td><td><strong>逐配置判定</strong><small>不合并为引擎排名</small></td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="home-answers" aria-labelledby="answer-heading">
  <section id="research-diagnosis"></section>
  <header class="home-section-head">
    <p>Three conclusions</p>
    <h2 id="answer-heading">先读三个判断。</h2>
  </header>
  <div class="home-answer-grid" data-reveal-group>
    <article id="experiment-findings" data-reveal-item>
      <span>01 / 实验结论</span>
      <h3>结果是失效边界，不是引擎排行榜。</h3>
      <p>接触模型、几何离散、耦合方式和辅助保持都可能直接改变任务结果。小步长和更多迭代不是通用修复。</p>
      <a href="experiments.html">查看实验目录 →</a>
    </article>
    <article id="solver-map" data-reveal-item>
      <span>02 / Solver 认知</span>
      <h3>先分清引擎、模型、耦合和数值配置。</h3>
      <p>同一个名字可能属于不同层；只有冻结版本、接触表示、预算和运行时读回后，配置之间才可能比较。</p>
      <a href="solver-taxonomy.html">查看求解配置 →</a>
    </article>
    <article id="root-causes" data-reveal-item>
      <span>03 / 失败根因</span>
      <h3>很多“solver 失败”在迭代前已经注定。</h3>
      <p>先查任务、几何、控制和耦合，再查离散、残差与评分；证据不足时保留为未唯一确定。</p>
      <a href="failure-root-cause-atlas.html">查看失败根因图谱 →</a>
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
    <h2 id="next-heading">按需要继续。</h2>
  </header>
  <div class="home-next-grid">
    <a href="experiments.html"><strong>全部实验</strong><span>任务、协议、结果与失败记录</span></a>
    <a href="_static/research/dexterous-simulation.html"><strong>研究导读</strong><span>灵巧操作仿真的六层问题</span></a>
    <a href="learning.html"><strong>仿真学习</strong><span>MuJoCo 起点与六个引擎课程</span></a>
  </div>
</section>

<section class="home-contact" id="research-scope" aria-labelledby="contact-heading">
  <span id="contact-author"></span>
  <div>
    <p>DexLab · Kiki Huang</p>
    <h2 id="contact-heading">联系作者</h2>
    <span>想复现实验、指出问题，或者只是想聊聊仿真，都欢迎。</span>
  </div>
  <nav aria-label="联系作者">
    <a href="mailto:huangyue0719@outlook.com">邮件</a>
    <a href="https://github.com/huangkiki">GitHub ↗</a>
  </nav>
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
研究旧链接 <blog>
研究资料 <references>
参与项目 <contributing>
```
