# DexLab

```{raw} html
<div class="home story-home" id="top">
<div class="home-opening">
  <header class="story-hero" aria-labelledby="home-heading">
    <h1 id="home-heading">DexLab<span>.</span></h1>
    <p class="hero-thesis">让智能体与仿真，<br><strong>在实验中共同进化。</strong></p>
  </header>

  <figure class="home-overview" data-home-reveal id="architecture" aria-label="DexLab 架构图">
    <a id="architecture-heading" href="_static/images/dexlab-architecture.png" target="_blank" rel="noopener" aria-label="打开 DexLab 架构图原图">
      <picture>
        <source srcset="_static/images/dexlab-architecture.webp" type="image/webp">
        <img src="_static/images/dexlab-architecture.png" width="1774" height="887" loading="eager" decoding="async" alt="DexLab 架构，从任务、被测系统、动作执行和环境后端，到证据与评分，再用实验结果改进系统。">
      </picture>
    </a>
  </figure>

  <div class="experiment-intro" data-home-reveal>
    <p class="opening"><strong>任务失败，<br>并不一定是策略的问题。</strong></p>
    <p>也可能是仿真本身的数值问题，或是场景约束与评测流程影响了结果。</p>
  </div>

  <section id="genesis" aria-label="Genesis 斜面实验">
    <p class="case-copy" data-home-reveal><strong><span>求解器停止迭代时，</span><span>力和运动仍可能对不上。</span></strong> 在斜面实验中，方块从静止开始。Genesis 的 <strong>CG</strong> 在迭代改进量低于停止阈值时退出。第 106 步，方块的动量变化与重力和接触力产生的总冲量相差 <strong class="measure">3.32 × 10⁻⁷ N·s</strong>，是验收上限 <strong class="measure">1.00 × 10⁻⁷ N·s</strong> 的 <strong>3.32 倍</strong>。</p>
    <figure data-home-reveal>
      <picture>
        <source media="(max-width:600px) and (prefers-reduced-motion: reduce)" width="560" height="844" srcset="_static/homepage-evidence/genesis-incline-mobile.jpg">
        <source media="(prefers-reduced-motion: reduce)" srcset="_static/homepage-evidence/genesis-incline.jpg">
        <source media="(max-width:600px)" width="560" height="844" srcset="_static/homepage-evidence/genesis-incline-mobile.gif">
        <img width="1080" height="420" loading="lazy" src="_static/homepage-evidence/genesis-incline.gif" alt="OVRTX 斜面回放与实测残差同步。第 106 步的残差为 3.32 × 10⁻⁷ N·s，验收线为 1.00 × 10⁻⁷ N·s。">
      </picture>
      <figcaption>15° 斜面，步长 1 ms。OVRTX 回放与实测曲线同步，到第 106 步停留后循环。<a class="figure-links" href="_static/homepage-evidence/genesis-incline.gif">GIF 原图</a> · <a href="_static/homepage-evidence/genesis-incline.mp4">视频</a></figcaption>
    </figure>
    <p class="sources"><a href="https://github.com/huangkiki/Dexlab/blob/7363a9c5b1af2fb1045b132b545f098e03ae5194/docs/genesis-incline-results.zh-CN.md">斜面实验</a></p>
  </section>

  <section id="sponge" aria-label="双臂海绵擦拭">
    <p class="case-copy" data-home-reveal><strong><span>完成这项擦拭任务，</span><span>依赖仿真额外施加的抓持约束。</span></strong> 双臂实验中，夹爪夹住海绵后，仿真用柔顺约束牵住一小片海绵，让它随夹爪移动。两组沿用同一控制器和求解配置，刚体侧用 <strong>MJWarp 的 Newton</strong>，海绵侧用 <strong>SuperDex 的 Newton</strong>，内层按源码配置选用 <strong>CG</strong>。有辅助时 <strong>3/3 通过</strong>。撤去辅助后，海绵在擦拭中滑脱，控制器因压靠失败提前结束擦拭，<strong>0/3 通过</strong>。</p>
    <figure data-home-reveal>
      <picture><source media="(prefers-reduced-motion: reduce)" srcset="_static/homepage-evidence/sponge-wiping.jpg"><img width="1042" height="294" loading="lazy" src="_static/homepage-evidence/sponge-wiping.gif" alt="双臂海绵擦拭并排回放。左侧保留辅助，右侧撤去后在擦拭过程中滑脱"></picture>
      <figcaption>
        <span class="caption-pair"><span>有辅助 · 清洁率 95.5%</span><span>撤去辅助 · 清洁率 39.9%</span></span>
        两组第一次记录，仿真 14–41.25 秒，OVRTX 回放 2 倍速。<a class="figure-links" href="_static/homepage-evidence/sponge-wiping.mp4">视频</a>
      </figcaption>
    </figure>
    <p class="sources"><a href="rss-wiping.html">海绵擦拭对照</a></p>
  </section>

  <section id="libero" aria-label="LIBERO 独立评测">
    <p class="case-copy" data-home-reveal><strong><span>首条动作还没发出，</span><span>评测流程就可能</span><span>让观测落后于仿真。</span></strong> LIBERO 的官方独立评测脚本在设置初态时保存了一份观测，随后让仿真静置五步。期间，机械臂末端的 Y 坐标变化了 <strong class="measure">4.481 mm</strong>。脚本丢弃了这五步返回的新观测，于是<strong>策略用静置前的观测算出第一条动作，仿真从静置后的状态执行它</strong>。</p>
    <figure data-home-reveal>
      <picture><source media="(prefers-reduced-motion: reduce)" srcset="_static/homepage-evidence/libero-first-observation.jpg"><img width="1122" height="432" loading="lazy" src="_static/homepage-evidence/libero-first-observation.gif" alt="LIBERO 五步静置的原生复现，末端 Y 坐标变化 4.481 mm，评测输入保留在第 0 步"></picture>
      <figcaption>
        <span class="caption-pair"><span>旧观测对应的状态</span><span>仿真当前状态</span></span>
        OVRTX 同机位回放。五步之后，末端 Y 坐标变化 4.481 mm。片段止于首条策略动作之前。<a class="figure-links" href="_static/homepage-evidence/libero-first-observation.mp4">视频</a>
      </figcaption>
    </figure>
    <p class="sources"><a href="libero-workflow-report.html">LIBERO 流程审计</a> · <a href="https://github.com/Lifelong-Robot-Learning/LIBERO/blob/8f1084e3132a39270c3a13ebe37270a43ece2a01/libero/lifelong/evaluate.py#L260-L273">独立评测源码</a></p>
  </section>

  <p id="conclusion" class="opening" data-home-reveal><strong>智能体从仿真反馈中学习，<br>实验中的行为记录又为检验和修正仿真模型提供证据。</strong></p>
</div>

<section class="concept-entry" aria-label="概念墙与实验入口">
  <div id="concept-field-slot"></div>
  <a class="directory-entry" href="#experiments">
    <span class="directory-action">先看代表性实验与结论</span>
    <span class="directory-summary">从五个代表实验和三个研究判断开始；物理验证边界与回归条件放在全文末尾。</span>
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
  </a>
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

  <div class="evidence-sequence" aria-label="代表性实验证据序列">
      <article class="evidence-panel" id="panel-cut" data-evidence="cut" data-evidence-reveal role="region" aria-labelledby="evidence-cut-title">
        <header class="evidence-panel-head">
          <span>01</span>
          <strong>切割与侧推</strong>
          <small>11.096 / 10.209 mm</small>
        </header>
        <div class="evidence-media evidence-media-split">
          <img src="_static/cutting/tofu-cut-push/surface-rtx.gif" alt="豆腐两刀三块后直接侧推的最新记录" width="100%" loading="lazy">
          <img src="_static/cutting/banana-cut-push/surface-rtx.gif" alt="香蕉三刀四块后直接侧推的最新记录" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">切割 / 分离判据</p>
          <h3 id="evidence-cut-title">切完，仍要证明末块能独立运动。</h3>
          <p class="evidence-verdict">最后一刀直接侧推后，豆腐三块、香蕉四块均出现独立相对位移。</p>
          <dl class="evidence-ledger">
            <div><dt>控制变量</dt><dd>豆腐 0.125 ms、η=5 Pa·s；香蕉 0.25 ms、η=0</dd></div>
            <div><dt>原生读回</dt><dd>活动块相对位移与刀面接触冲量</dd></div>
            <div><dt>判据结果</dt><dd><strong>通过 · 11.096 / 10.209 mm</strong></dd></div>
            <div><dt>适用范围</dt><dd>合成材料与固定切推协议，不是食材标定</dd></div>
          </dl>
          <a href="cut-push-report.html">查看完整记录、对照与原始数据 →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-wuji" data-evidence="wuji" data-evidence-reveal role="region" aria-labelledby="evidence-wuji-title">
        <header class="evidence-panel-head">
          <span>02</span>
          <strong>接触与抗扭力矩</strong>
          <small>2.734 → 1.025 mm</small>
        </header>
        <div class="evidence-media">
          <img src="_static/wuji-contact/comparison.gif" alt="Wuji 点接触与抗扭接触的同时间原速比较" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">接触 / 力矩方向</p>
          <h3 id="evidence-wuji-title">一直有接触，球仍可能绕夹持线转动。</h3>
          <p class="evidence-verdict">点接触缺少力矩方向；补上合成抗扭接触后，保持才进入原定门槛。</p>
          <dl class="evidence-ledger">
            <div><dt>控制变量</dt><dd>只将点接触改为合成抗扭接触</dd></div>
            <div><dt>原生读回</dt><dd>2 秒保持位移与峰值角速度</dd></div>
            <div><dt>判据结果</dt><dd><strong>2.734 → 1.025 mm；角速度 29.336 → 0.024992 rad/s</strong></dd></div>
            <div><dt>适用范围</dt><dd>双指夹球工况；不是真机材料标定或全手能力</dd></div>
          </dl>
          <a href="wuji-contact-report.html">查看接触记录、GIF 与独立复算 →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-apple" data-evidence="apple" data-evidence-reveal role="region" aria-labelledby="evidence-apple-title">
        <header class="evidence-panel-head">
          <span>03</span>
          <strong>苹果梗抓取</strong>
          <small>1/10 · 10/10</small>
        </header>
        <div class="evidence-media">
          <img src="_static/studio/apple.gif" alt="OpenArm 与 Wuji 苹果梗抓取记录" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">任务 / 固定扰动集</p>
          <h3 id="evidence-apple-title">同一条抓梗任务，固定配置仍可能给出不同结果。</h3>
          <p class="evidence-verdict">差异必须连同步长、驱动、质量、位置和接触表示一起读。</p>
          <dl class="evidence-ledger">
            <div><dt>控制变量</dt><dd>同一组 10 个冻结场景，不针对留出场景重调参</dd></div>
            <div><dt>原生读回</dt><dd>离桌、支撑、持续保持、穿透与释放</dd></div>
            <div><dt>判据结果</dt><dd><strong>MuJoCo 1/10 · SuperDex 10/10</strong></dd></div>
            <div><dt>适用范围</dt><dd>固定配置对照，不是引擎精度排名</dd></div>
          </dl>
          <a href="experiments.html#apple-replays">查看连续近景与固定场景结果 →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-cloth" data-evidence="cloth" data-evidence-reveal role="region" aria-labelledby="evidence-cloth-title">
        <header class="evidence-panel-head">
          <span>04</span>
          <strong>布料</strong>
          <small>52 / 105 通过</small>
        </header>
        <div class="evidence-media">
          <img src="_static/cloth-studio/grasp.gif" alt="布料夹持与运动记录" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">柔性体 / 分阶段验收</p>
          <h3 id="evidence-cloth-title">夹住、抬起与完成折叠是三个不同验收。</h3>
          <p class="evidence-verdict">同一冻结留出集按形变、穿透、残余运动与成本分别判定。</p>
          <dl class="evidence-ledger">
            <div><dt>控制变量</dt><dd>7 个原生配置与同一冻结留出集</dd></div>
            <div><dt>原生读回</dt><dd>形变、下垂、穿透、残余运动与成本</dd></div>
            <div><dt>判据结果</dt><dd><strong>52 / 105 通过，53 条失败保留</strong></dd></div>
            <div><dt>适用范围</dt><dd>材料未做跨求解器等效标定</dd></div>
          </dl>
          <a href="cloth-comparison-report.html">查看布料配置、失败与证据边界 →</a>
        </div>
      </article>

      <article class="evidence-panel" id="panel-incline" data-evidence="incline" data-evidence-reveal role="region" aria-labelledby="evidence-incline-title">
        <header class="evidence-panel-head">
          <span>05</span>
          <strong>六引擎斜面</strong>
          <small>逐配置判定</small>
        </header>
        <div class="evidence-media">
          <img src="_static/studio/incline.gif" alt="六引擎斜面同步比较记录" width="100%" loading="lazy">
        </div>
        <div class="evidence-copy">
          <p class="home-evidence-label">Solver / 同工况响应</p>
          <h3 id="evidence-incline-title">同一任务，接触表达和数值门禁仍会改变结果。</h3>
          <p class="evidence-verdict">静止、滑动和名义零摩擦逐配置判定，不合并成引擎总分。</p>
          <dl class="evidence-ledger">
            <div><dt>控制变量</dt><dd>三种接触条件和三个步长，六个固定引擎配置</dd></div>
            <div><dt>原生读回</dt><dd>位移、速度、支撑力、几何重叠与观测有效性</dd></div>
            <div><dt>判据结果</dt><dd><strong>通过、失败和无效记录分别保留</strong></dd></div>
            <div><dt>适用范围</dt><dd>不同协议与预算不拼成通用 solver 排名</dd></div>
          </dl>
          <a href="visual-comparisons.html#incline">打开同步回放、曲线与完整矩阵 →</a>
        </div>
      </article>
  </div>
</section>

<section class="home-answers" aria-labelledby="answer-heading">
  <section id="research-diagnosis"></section>
  <header class="home-section-head">
    <p>Three conclusions</p>
    <h2 id="answer-heading">先读三个判断。</h2>
  </header>
  <div class="home-answer-grid">
    <article id="experiment-findings">
      <span>01 / 实验结论</span>
      <h3>结果是失效边界，不是引擎排行榜。</h3>
      <p>接触模型、几何离散、耦合方式和辅助保持都可能直接改变任务结果。小步长和更多迭代不是通用修复。</p>
      <a href="experiments.html">查看实验目录 →</a>
    </article>
    <article id="solver-map">
      <span>02 / Solver 认知</span>
      <h3>先分清引擎、模型、耦合和数值配置。</h3>
      <p>同一个名字可能属于不同层；只有冻结版本、接触表示、预算和运行时读回后，配置之间才可能比较。</p>
      <a href="solver-taxonomy.html">查看求解配置 →</a>
    </article>
    <article id="root-causes">
      <span>03 / Sim-to-Real Gap</span>
      <h3>仿真的差距不只在引擎里。</h3>
      <p>从任务、参数送达和受力预算一直检查到接触、评分与真机验证；证据不足时保留为未唯一确定。</p>
      <a href="failure-root-cause-atlas.html">阅读 Sim-to-Real Gap 全景 →</a>
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

<section class="home-validity" id="physical-validity" aria-labelledby="validity-heading">
  <header class="home-section-head">
    <p>Validation boundary</p>
    <h2 id="validity-heading">没有真机实验，<br>物理正确如何被证明？</h2>
    <span>结论上限：冻结仿真模型内的可复验物理一致性。</span>
  </header>

  <div class="validity-boundary">
    <strong>真机实验：0</strong>
    <div>
      <p><strong>DexLab 的 claim：</strong>物理正确不是“仿真成功”这一总分，而是一条可逐层证伪的证据链。先证明配置值真的到达引擎；再检查单位、质量、惯量、本体限位与现实量级；用守恒和时间步扰动排除自相矛盾的数值行为；检查接触和物体响应没有越过物理边界；最后要求评分拒绝 idle、接近但不接触、隐藏支撑和错误搬运／reset 等伪完成。</p>
      <p>全部通过，也只说明冻结模型内部可复核、可重复，不自动证明 sim-to-real。没有真实传感器、机器人或材料数据，就不报告真实材料误差、硬件时序误差或 reality gap；真机实验仍是外部有效性检查。<a href="https://github.com/huangkiki/Dexlab/discussions/388">完整证据链、失效 case 与边界见 Discussion #388 →</a></p>
    </div>
    <a href="https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.zh-CN.md">查看真机采集协议 →</a>
  </div>

  <p><a class="lab-button" href="https://github.com/huangkiki/Dexlab/discussions">进入 DexLab Discussions <span aria-hidden="true">→</span></a></p>

  <ol class="validity-chain" data-reveal-group>
    <li data-reveal-item>
      <span>输入先冻结</span>
      <h3>先证明算的是同一对象。</h3>
      <p>记录版本、资产与源码哈希、单位、缩放、质量／惯量、初态和控制时序；缺失字段保持未知，不用默认值补齐。</p>
    </li>
    <li data-reveal-item>
      <span>正负对照</span>
      <h3>正例通过，反例必须被拒绝。</h3>
      <p>正例和负例共享同一初态与动作，只关闭或替换被检验的条件；负例意外通过会让整项检查失效。</p>
    </li>
    <li data-reveal-item>
      <span>原生读回</span>
      <h3>画面只解释现象，数值决定通过。</h3>
      <p>独立核对穿透、接触力、支撑对象、动量和角动量残差、驱动饱和与任务阶段；不能从画面相似推出物理等价。</p>
    </li>
    <li data-reveal-item>
      <span>改参回归</span>
      <h3>每次只改声明变量，重跑完整门禁。</h3>
      <p>阈值与变量在运行前冻结；改参后重跑同任务正负例、基础响应、守恒检查和旧回归，旧结果不复用，失败不删除。</p>
    </li>
  </ol>

  <div class="validity-records" data-reveal-group>
    <article class="validity-record" data-reveal-item>
      <header>
        <p>01 / 切割与侧推</p>
        <h3>看得见的刀面接触必须解释位移。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>最后一刀后保留三块／四块连通身份，检查活动块相对位移、刀面接触冲量、分离历史与原生状态；运动和力来自保存的仿真状态，没有直接注入材料速度。完整正例通过 18 项检查，无侧推负例按预期被拒绝。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>固定步长只把黏度从 η=0 改为 5 Pa·s，重跑完整 6 s 验收与无侧推对照；另做剪切、体积、客观性、刚体运动、动量和离散耗散测试。18 组零黏性步进逐位一致，7 份纯弹性完整记录不变；半步长只单列为敏感性检查，不冒充收敛。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>材料参数是合成值，没有豆腐／香蕉实测标定；初始重力沉降未预平衡，局部抖动改善也不代表刀接触力或真实食材阻尼准确。</dd>
        </div>
      </dl>
      <a href="cut-push-report.html">查看切割协议与证据 →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>02 / 接触力矩</p>
        <h3>只改接触表示，检查保持、释放和反例。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>同手、同控制器、同动作下，只将球的点接触改为抗扭接触。独立检查双指持续接触、2 mm 保持门槛、主动释放、单指卸载、张指／禁接触／名义零摩擦负例，并核对线动量与角动量残差。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>抗扭参数在运行前冻结，没有按结果扫参；v4 只改变接触模型，再跑六项开发对照。历史 v1–v3 的失败与 15 项未运行记录继续保留，不用 v4 回填或替换。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>球、指垫和抗扭斑均为合成设置，没有真实指垫材料；v4 仍会缓慢漂移，2 s 窗口通过不等于无限时长稳定保持。</dd>
        </div>
      </dl>
      <a href="wuji-contact.html">查看抗扭接触对照 →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>03 / 苹果梗抓取</p>
        <h3>十组固定回归只允许两指真正支撑。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>MuJoCo 与 SuperDex 使用同一组 10 个固定场景（各自冻结质量与姿态）和相同脚本动作；23 项检查覆盖自由刚体无附着、无物体驱动、离桌、两片 SDF 指腹持续支撑、无桌面或其他支撑、穿透上限、保持、释放和动量平衡。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>步长变化会重跑完整检查，而不是只看抓取视频：MuJoCo 测 0.125／0.25／0.5 ms，SuperDex 测 0.5／1／2 ms。MuJoCo 的 0.25 ms 因穿透越界被保留为失败，说明测试确实有拒绝能力。回归集在评价前冻结，测试划分不用于回调参数。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>固定格式下 MuJoCo 1/10、SuperDex 10/10 只是两个冻结配置的任务结果；没有梗变形、断裂、真实摩擦材料或硬件精度验证，也不是跨引擎通用排名。</dd>
        </div>
      </dl>
      <a href="experiments.html#apple-replays">查看苹果抓取记录 →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>04 / 布料</p>
        <h3>形变、穿透、残余运动和成本分别验收。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>七种配置共用下垂和球面覆盖任务，共 105 条冻结记录；逐项检查协议、形状、振荡、表面穿越、穿透、残余运动和成本。回放直接读取保存的顶点，渲染器执行 0 个物理步，也不移动顶点消除穿透。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>材料参数或求解配置变化会被当作新的 profile，重新记录同任务的完整 15 条案例，不沿用旧通过结果；初态、静止网格或时间轴不一致时，比较器直接拒绝拼接。跨引擎预算不同，因此通过数不能拼成物理精度排名。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>材料没有跨引擎等效标定，52/105 不代表真实织物准确率；绿色通过只表示满足该条冻结协议，不等于真实布料参数已经识别。</dd>
        </div>
      </dl>
      <a href="cloth-comparison.html">查看布料对照 →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>05 / 六引擎斜面</p>
        <h3>解析参照、三个步长和无效记录一起读。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>同一 40 mm、64 g 方块比较静止、滑动和名义零摩擦，每个条件跑 0.5／1／2 ms 三个步长；检查位移、速度、力与数值一致性。静摩擦不等式和滑动加速度 <i>a</i>=<i>g</i>(sin θ−μ cos θ) 是解析／工程参照，不是实物测量。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>步长本来就是九例交叉设计；接触模型、精度和执行路径随完整 profile 冻结。正例、负例、失败和无效记录全部保留在分母中，不能用某次参数调整后的最好结果替换历史。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>每个引擎的接触律、预算和适用范围不同，九例结果只支持逐配置判断；没有一套引擎通过全部九例，也不能据此生成通用 solver 排名。</dd>
        </div>
      </dl>
      <a href="visual-comparisons.html#incline">查看六引擎矩阵 →</a>
    </article>

    <article class="validity-record" data-reveal-item>
      <header>
        <p>06 / 参数标定与迁移</p>
        <h3>本夹具校准通过，必须换载荷再验一次。</h3>
      </header>
      <dl>
        <div>
          <dt>物理保证</dt>
          <dd>同一 MuJoCo 四点面接触夹具以 20 kN/m 合成目标检查加载窗口；初始约 80 kN/m，校准后约 20 kN/m。验收同时保留离面段，避免把卸载或间隙运动误算成接触响应。</dd>
        </div>
        <div>
          <dt>改参后如何回归</dt>
          <dd>固定参数直接迁移到 0.1／0.4 kg 时得到 10.01／40.04 kN/m，按预期失败；采用事前写明的质量补偿后为 20.04／19.93 kN/m，才重新通过。每次改参都检查加载、卸载、离面和邻近质量，不能只复测原始载荷。</dd>
        </div>
        <div>
          <dt>不能证明</dt>
          <dd>20 kN/m 是合成工程目标，不是真实材料刚度；结论只适用于此恒定阻抗夹具，不能外推成任意几何或真实接触参数。</dd>
        </div>
      </dl>
      <a href="visual-comparisons.html#normal">查看法向响应协议 →</a>
    </article>
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
Paper sharing <paper-sharing>
概念索引 <concepts/index>
参与项目 <contributing>
```
