# DexLab

```{raw} html
<div class="home" id="top">
<section class="hero" aria-labelledby="hero-heading">
  <h1 id="hero-heading"><a href="_static/research/dexterous-simulation.html">当我们在讨论<br>灵巧操作仿真时，<br>我们在讨论什么？</a></h1>
  <p class="hero-lead">从接触与触觉，到策略、评测与真实迁移。把论文、项目和实验放在一起，理解仿真能解决什么，以及结论在哪里成立。</p>
  <a class="guide-link" href="_static/research/dexterous-simulation.html">阅读研究导读<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
  <nav class="guide-chapters" aria-label="导读章节"><a href="_static/research/dexterous-simulation.html#layers">六层问题</a><a href="_static/research/dexterous-simulation.html#simulation-benchmarks-2026">仿真评测</a><a href="_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons">CoRL 2026</a></nav>
</section>
<section class="research-direction" aria-labelledby="direction-heading">
  <h2 id="direction-heading">让智能体与仿真，在实验中共同进化。</h2>
  <div class="research-loop" aria-label="RSI 研究循环">
    <span>任务试验</span><span aria-hidden="true">→</span><span>诊断失败</span><span aria-hidden="true">→</span><span class="loop-fork">改进技能 · 改进仿真</span><span aria-hidden="true">→</span><span>独立复验</span><span class="loop-return">↩ 提出下一问题</span>
  </div>
  <p class="vision-note">RSI（递归自我改进）是 DexLab 的研究方向：人确定目标与边界，Agent 逐步参与问题发现、实验和迭代。完整自主闭环尚未验证，已有成果以具体实验为准。</p>
</section>
<section class="feature" id="experiments" aria-labelledby="case-heading">
  <section id="research-findings"></section>
  <div class="section-heading"><div><h2 id="case-heading">研究结论</h2></div><a class="text-link" href="experience.html">更多研究结论</a></div>
  <div class="case-grid">
    <figure class="case-media"><video controls playsinline preload="none" width="896" height="504" poster="_static/research-home-wuji.png" aria-label="Wuji 点接触与合成抗扭接触的原速对照回放"><source src="_static/wuji-contact/comparison.mp4" type="video/mp4"><a href="_static/wuji-contact/comparison.mp4">下载原始回放</a></video><figcaption>真实记录回放 · 左：点接触 / 右：合成抗扭接触 · 同时间、原速 · 点击播放</figcaption></figure>
    <div class="case-story"><h3>补上抗扭接触后，保持检查通过。</h3>
    <ol class="case-sequence">
      <li><strong>结论</strong><p>同一控制下，加入合成抗扭接触后，两秒保持最大位移从 2.734 降至 1.025 mm，通过原定 2 mm 门槛及主动释放检查。</p></li>
      <li><strong>依据</strong><p>原配置的两点接触始终存在，却缺少绕接触连线的力矩方向。偏心重力驱动球转动，保持失败；提高夹紧力没有补上这个方向。</p></li>
      <li><strong>启发</strong><p>遇到这类抓持失败，先检查接触模型能否提供所需力矩，再讨论参数和求解。本次使用 MuJoCo 已有能力，未修改求解器。</p></li>
      <li><strong>范围</strong><p>结论限于这组合成接触与两秒窗口，仍有慢漂移；新定律也影响准备阶段，不能把全部位移唯一归因于一个自由度。</p></li>
    </ol><a class="text-link" href="wuji-contact.html">看完整分析与证据</a></div>
  </div>
  <details class="case-boundary"><summary>这个结果能说明什么？</summary><p>最早定位到的是接触扳手的结构缺口；偏心重力提供绕接触连线的驱动力矩。直觉上，两点连线像一个缺少抗扭能力的轴，但实际手指和接触点会移动，不能把它当成固定铰链。v4 从准备阶段就采用新定律，因此初态也受影响；该开发对照没有把全部位移唯一归因于一个自由度。</p><p>结论限于合成球、这组控制与两秒窗口，仍有慢漂移。长时间保持、接触切换与新的验证条件是后续门槛；真实指垫标定及完整自主 RSI 闭环尚未验证。</p></details>
</section>
<section class="blog-section" id="blog" aria-labelledby="blog-heading">
  <section id="research-diagnosis"></section>
  <div class="section-heading"><div><h2 id="blog-heading">沿着问题，继续读</h2></div><a class="text-link" href="_static/research/dexterous-simulation.html">从研究导读开始</a></div>
  <div class="topic-controls" hidden aria-label="选择 Blog 专题"><button type="button" data-topic="contact" aria-controls="topic-contact" aria-pressed="true">接触与物理</button><button type="button" data-topic="diagnosis" aria-controls="topic-diagnosis" aria-pressed="false">失败与评测</button><button type="button" data-topic="agents" aria-controls="topic-agents" aria-pressed="false">智能体与仿真</button></div>
  <section class="topic-panel" id="topic-contact" aria-labelledby="heading-contact"><div class="topic-intro"><h3 id="heading-contact">夹得更紧，为什么仍会滑？</h3><p>从接触需要提供的力与力矩出发，再讨论模型、参数和求解。</p><a class="text-link" href="#learn">连接到学习地图</a></div><ol class="reading-list"><li><a href="wuji-contact.html"><span>点接触与抗扭接触：一次抓持对照</span></a></li><li><a href="contact-response.html"><span>预测误差更低，就能预报接触失效吗？</span></a></li><li><a href="solver-taxonomy.html"><span>物理模型、数值问题与 solver，分别负责什么？</span></a></li></ol></section>
<section class="topic-panel" id="topic-diagnosis" aria-labelledby="heading-diagnosis"><div class="topic-intro"><h3 id="heading-diagnosis">任务完成，真的说明能力提高了吗？</h3><p>沿动作、状态和受力追踪第一失效层，把任务评分与物理证据放在一起读。</p><a class="text-link" href="#learn">连接到学习地图</a></div><ol class="reading-list"><li><a href="failure-root-cause-atlas.html"><span>失败根因图谱：沿着证据找第一失效层</span></a></li><li><a href="robodojo-bread-slip.html"><span>闭爪命令正确，面包为什么仍会掉？</span></a></li><li><a href="rss-wiping.html"><span>去掉辅助保持，再看擦拭任务</span></a></li></ol></section>
<section class="topic-panel" id="topic-agents" aria-labelledby="heading-agents"><div class="topic-intro"><h3 id="heading-agents">怎样让一次失败推动下一轮改进？</h3><p>连接技能、观测、仿真和独立评价，寻找值得验证的下一步。完整自主 RSI 闭环仍是研究方向。</p><a class="text-link" href="#learn">连接到学习地图</a></div><ol class="reading-list"><li><a href="_static/research/dexterous-simulation.html#robodojo-astra"><span>RoboDojo / Astra：纠正动作与可靠接触控制</span></a></li><li><a href="_static/research/dexterous-simulation.html#shared-dexterous-tracking"><span>多条示范，怎样共用策略与动力学模型？</span></a></li><li><a href="model-evaluation.html"><span>怎样把模型、执行与评分分开？</span></a></li></ol></section>

</section>
<section class="learning-section" id="learn" aria-labelledby="learn-heading">
  <section id="research-selection"></section>
  <div class="section-heading"><div><h2 id="learn-heading">仿真学习</h2><p>先从 MuJoCo 开始，理解时间、接触与求解；通过互动和自测走向已有课程与 MuJoCo 4 新特性。</p></div><a class="text-link" href="learning.html">开始 MuJoCo 学习</a></div>
  <ol class="learning-map"><li><span class="step-number">1</span><h3>建立物理直觉</h3><p>状态、时间、动力学</p><small>起点：向量、矩阵与基本力学</small><a href="learn/sim/docs/physics-based-simulation.html">Physics-Based Simulation 伴读</a></li><li><span class="step-number">2</span><h3>理解接触与摩擦</h3><p>几何、力、力矩与约束</p><small>先修：物理与状态基础</small><a href="learn/sim/docs/solver-guide/02-contact.html">接触课程</a></li><li><span class="step-number">3</span><h3>读懂数值求解</h3><p>方程、迭代、步长与容差</p><small>先修：接触模型与基础线性代数</small><a href="learn/sim/docs/solver-guide/README.html">九单元 Solver 教程</a></li><li><span class="step-number">4</span><h3>走进原生引擎</h3><p>使用接口，追踪源码</p><small>沿应用路线或原理路线继续</small><a href="learn/sim/docs/learning-paths.html">选择一条引擎路线</a></li></ol>
  <div class="engine-paths"><span>选择一个引擎深入</span><div><a href="learning.html">MuJoCo</a><a href="learn/superdex/docs/curriculum.html">SuperDex</a><a href="learn/genesis/docs/curriculum.html">Genesis</a><a href="learn/newton/docs/curriculum.html">Newton Physics</a><a href="learn/physx/docs/curriculum.html">PhysX</a><a href="learn/drake/docs/curriculum.html">Drake</a></div></div>
  <div class="knowledge-bridges"><h3>想理解得更深，从相关知识继续。</h3><ul><li><a href="learn/sim/docs/solver-guide/03-friction.html">摩擦与接触力矩</a><span aria-label="对应实验">↔</span><a href="wuji-contact.html">Wuji 抓持对照</a></li><li><a href="learn/sim/docs/solver-guide/07-representations.html">变形体与耦合</a><span aria-label="对应实验">↔</span><a href="cloth-comparison.html">布料实验</a></li><li><a href="learn/sim/docs/solver-guide/01-simulation-step.html">状态、步进与观测</a><span aria-label="对应实验">↔</span><a href="libero-workflow.html">LIBERO 记录检查</a></li></ul></div>

</section>
<section id="research-scope"></section>
<nav class="technical-links" aria-label="技术文档入口"><a id="architecture" href="about.html#architecture">平台架构</a><a id="quickstart" href="quickstart.html">安装与复现</a><a id="model-evaluation" href="model-evaluation.html">评测协议</a><a id="documentation-and-citation" href="about.html#documentation-and-citation">项目说明与引用</a><a id="live-lab" href="about.html#live-lab">浏览器演示</a></nav>
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
研究资料 <references>
参与项目 <contributing>
```
