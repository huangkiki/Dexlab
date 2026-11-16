# Blog

<nav class="blog-jump" aria-label="Blog 专题">
  <a href="#blog-guide">研究导读</a>
  <a href="#blog-contact">接触与物理</a>
  <a href="#blog-diagnosis">失败与诊断</a>
  <a href="#blog-policy">策略、技能与评测</a>
  <a href="#blog-learn">仿真学习</a>
</nav>

(blog-guide)=
## 研究导读

先看完整问题框架，再进入具体文章：接触需要提供什么、失败发生在哪一层，以及实验结论在哪里成立。

<ul class="blog-links">
  <li><a href="_static/research/dexterous-simulation.html">当我们在讨论灵巧操作仿真时，我们在讨论什么？</a></li>
  <li><a href="_static/research/dexterous-simulation.html#layers">六层问题：从接触、策略到真实迁移</a></li>
  <li><a href="_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons">CoRL 2026：DexLab 的阅读结论</a></li>
</ul>

(blog-contact)=
## 接触与物理

先问任务需要什么力、力矩和接触历史，再讨论模型、参数与 solver。

<ul class="blog-links">
  <li><a href="wuji-contact.html">点接触与抗扭接触：一次抓持对照</a></li>
  <li><a href="contact-response.html">预测误差更低，就能预报接触失效吗？</a></li>
  <li><a href="solver-taxonomy.html">物理模型、数值问题与 solver，分别负责什么？</a></li>
</ul>

(blog-diagnosis)=
## 失败与诊断

沿动作、状态和受力追踪第一失效层，把任务评分与物理证据放在一起读。

<ul class="blog-links">
  <li><a href="failure-root-cause-atlas.html">失败根因图谱：沿着证据找第一失效层</a></li>
  <li><a href="robodojo-bread-slip.html">闭爪命令正确，面包为什么仍会掉？</a></li>
  <li><a href="rss-wiping.html">去掉辅助保持，再看擦拭任务</a></li>
</ul>

(blog-policy)=
## 策略、技能与评测

先确定动作由谁生成、执行边界在哪里、经验保存在哪里，再用独立证据判断它是否有效。完整自主改进流程仍是研究方向。

<div class="blog-subgrid">
<section class="blog-subtopic">
<h3>策略表示</h3>
<p>动作是学习得到的连续策略、运行时生成的程序，还是固定代码？</p>

<ul>
  <li><a href="code-as-policy.html">Code as Policy 专题：四种系统形态</a></li>
  <li><a href="_static/research/dexterous-simulation.html#robodojo-astra">RoboDojo / Astra：纠正动作与可靠接触控制</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h3>执行边界</h3>
<p>Agent harness、控制器、仿真器和评分器各拥有什么证据？</p>

<ul>
  <li><a href="code-as-policy.html#execution-stack">Code as Policy：程序下面还有哪些层？</a></li>
  <li><a href="model-evaluation.html">怎样把模型、执行与评分分开？</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h3>技能与记忆</h3>
<p>修复保存在代码、文本还是技能库，什么时候才能复用？</p>

<ul>
  <li><a href="_static/research/dexterous-simulation.html#capx-aspire">CaP-X / ASPIRE：从 trace 到技能晋升</a></li>
  <li><a href="_static/research/dexterous-simulation.html#coap">COAP：固定代码、显式状态与受控改动</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h3>评测与归因</h3>
<p>抽象层级、反馈、预算、留出集和评分怎样改变结论？</p>

<ul>
  <li><a href="code-as-policy.html#cap-evaluation">Code as Policy 评测字段清单</a></li>
  <li><a href="_static/research/dexterous-simulation.html#benchmark-gaming-audit">榜单高分如何被误读？</a></li>
</ul>
</section>
</div>

(blog-learn)=
## 仿真学习

从 MuJoCo 的时间、接触和数值求解开始，再沿同一套问题进入其他引擎课程。

<ul class="blog-links">
  <li><a href="learning.html">MuJoCo：从时间、接触到性能的学习路线</a></li>
  <li><a href="learn/sim/docs/solver-guide/README.html">共同基础：九单元 Solver 教程</a></li>
  <li><a href="learn/superdex/docs/curriculum.html">SuperDex 课程</a></li>
  <li><a href="learn/genesis/docs/curriculum.html">Genesis 课程</a></li>
  <li><a href="learn/newton/docs/curriculum.html">Newton Physics 课程</a></li>
  <li><a href="learn/physx/docs/curriculum.html">PhysX 课程</a></li>
  <li><a href="learn/drake/docs/curriculum.html">Drake 课程</a></li>
</ul>
