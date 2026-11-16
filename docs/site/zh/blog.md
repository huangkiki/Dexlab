# DexLab 项目与对比实验

<div class="blog-intro">
<p class="blog-tagline"><strong>Contact-rich robotics, beyond rigid-body simulation.</strong></p>
<p>DexLab 是一个以物理为中心的研究平台，研究接触、形变和材料分离下的机器人操作。它把失败拆成可观察、可归因、可复算的证据，再反馈给技能与仿真。</p>
<blockquote><p><strong>用模型暴露仿真缺口，再用更可信的仿真改善模型。</strong></p></blockquote>
<nav class="blog-intro-links" aria-label="DexLab 介绍与阅读入口">
  <a href="about.html">项目与技术文档</a>
  <a href="index.html">研究首页</a>
  <a href="_static/research/dexterous-simulation.html">研究导读</a>
</nav>
<p class="blog-scope">当前范围：接触、抓取、布料、切割与多引擎对比。跨任务统一结论仍在建设中。</p>
</div>

(architecture)=
## 架构

<figure class="blog-architecture">
<a href="_static/images/dexlab-architecture.png"><img src="_static/images/dexlab-architecture.png" width="100%" alt="DexLab 平台总览：任务与协议、被测系统、动作执行、环境后端、证据与评分"></a>
<figcaption>DexLab 平台总览：任务与协议、被测系统、动作执行、环境后端、证据与评分。任务缩略图仅说明任务类型；实际实现与验证范围见覆盖矩阵。</figcaption>
</figure>

<p class="blog-deck blog-architecture-note">脚本、策略与模型通过动作适配和控制器连接环境，环境返回观测；原生状态与接触记录进入独立评分，诊断结果再用于改进下一轮实验。</p>

(why-dexlab)=
## Why DexLab?

<p class="blog-deck">机器人策略在仿真中失败时，我们通常只看到一次失败。它可能来自策略、控制器、场景配置、接触离散、材料模型或数值求解。</p>

<blockquote class="blog-question"><p><strong>When a robot fails in simulation, is it the policy that fails, or the physics we trusted?</strong><br>仿真里的失败，是策略失败，还是我们信任的物理失败？</p></blockquote>

<p class="blog-deck"><strong>这页从对比实验读起：</strong>它不给出“谁赢了”的引擎排行榜，而是把接触、抓持、布料、耦合和斜面实验整理成三条线索：对比实验测出了什么，几个 solver 各自显示出什么边界，以及失败最早发生在哪一层。</p>

(evidence-feature)=
## 代表性实验

<div class="blog-evidence-grid">
<article class="blog-evidence-card">
  <a class="blog-evidence-media" href="cut-push.html"><img src="_static/cutting/showcase.gif" alt="豆腐与香蕉切割后直接侧推的记录回放" loading="lazy"></a>
  <p class="blog-evidence-kicker">01 / 切割与侧推</p>
  <h3>切完，仍要证明三块、四块能独立运动。</h3>
  <p>最后一块不再被同一切面带动，才不是只切出了画面。</p>
</article>

<article class="blog-evidence-card">
  <a class="blog-evidence-media" href="wuji-contact.html"><img src="_static/wuji-contact/hold-comparison.png" alt="点接触与抗扭接触的保持段轨迹比较" loading="lazy"></a>
  <p class="blog-evidence-kicker">02 / 摩擦与抗扭力矩</p>
  <h3>一直有接触，球仍可能绕夹持线转动。</h3>
  <p>点接触缺少力矩方向；补上抗扭接触后，保持才进入原定门槛。</p>
</article>

<article class="blog-evidence-card">
  <a class="blog-evidence-media" href="benchmark.html"><img src="_static/studio/apple.png" alt="苹果梗抓取实验记录" loading="lazy"></a>
  <p class="blog-evidence-kicker">03 / 苹果梗抓取</p>
  <h3>同一条抓梗任务，固定配置仍可能给出不同结果。</h3>
  <p>MuJoCo 与 SuperDex 的差异必须连同步长、驱动和接触表示一起读。</p>
</article>
</div>

<div class="comparison-matrix blog-evidence-matrix">
<table>
<caption>三组代表实验与 MotrixSim 公开报告的对应关系</caption>
<thead><tr>
<th scope="col">主题</th>
<th scope="col">DexLab 实测</th>
<th scope="col">MotrixSim 公开报告</th>
<th scope="col">能否直接并表</th>
</tr></thead>
<tbody>
<tr><th scope="row"><strong>切割与侧推</strong><small>豆腐 / 香蕉</small></th>
<td>豆腐 3 块，香蕉 4 块；活动块侧推 <strong>11.096 / 10.209 mm</strong></td>
<td>当前报告首页未给出同协议切割实验</td>
<td><span class="matrix-result mixed">不应并表</span></td></tr>
<tr><th scope="row"><strong>接触力矩</strong><small>Wuji 双指夹球</small></th>
<td>点接触 → 抗扭接触：位移 <strong>2.734 → 1.025 mm</strong></td>
<td><a href="https://motrixsim.motphys.com/#contact-grasping">抓取摩擦阈值</a>、<a href="https://motrixsim.motphys.com/#friction-rotation">滚动摩擦与后旋</a></td>
<td><span class="matrix-result mixed">机制相近</span></td></tr>
<tr><th scope="row"><strong>苹果抓取</strong><small>OpenArm + Wuji</small></th>
<td>10 个固定回归场景：MuJoCo <strong>1/10</strong>，SuperDex <strong>10/10</strong></td>
<td><a href="https://motrixsim.motphys.com/#sdf-collision">SDF 精细几何抓苹果演示</a></td>
<td><span class="matrix-result mixed">任务相近</span></td></tr>
</tbody>
</table>
</div>
<p class="matrix-note">MotrixSim 内容为公开技术报告中的外部结果；DexLab 数值来自本项目保存记录。任务、几何、控制和评分尚未对齐，因此这里只建立阅读对应关系，不生成跨协议胜负。</p>

<div class="blog-evidence-detail">
<div>
  <strong>切割判据</strong>
  <p>豆腐刀面冲量 0.092625 N·s；香蕉 0.021000 N·s。无侧推对照按预期拒绝。</p>
</div>
<div>
  <strong>抗扭判据</strong>
  <p>峰值角速度 <b>29.336 → 0.024992 rad/s</b>；抗扭接触内禀力矩 0.022138 mN·m。</p>
</div>
<div>
  <strong>苹果判据</strong>
  <p>差别是固定配置的鲁棒性，不是纯 solver 排名；20 个回归记录中 11 通过、9 失败。</p>
</div>
</div>

<nav class="blog-entry-links" aria-label="开始阅读">
  <a class="blog-entry-primary" href="#blog-preview">先看三个判断</a>
  <a href="#experiment-findings">实验结论</a>
  <a href="#solver-map">Solver 认知</a>
  <a href="#root-causes">失败根因</a>
</nav>

(blog-preview)=
## 先看三个判断

<div class="blog-verdict-grid">
<article class="blog-verdict">
  <p class="blog-verdict-label">01 / 实验结论</p>
  <h2>结果是失效边界，不是引擎排行榜。</h2>
  <ul>
    <li><strong>接触模型缺项时，加力没有用。</strong> Wuji 补上抗扭接触后，两秒最大位移从 2.734 降到 1.025 mm。</li>
    <li><strong>几何离散和辅助方式能翻转成败。</strong> SuperDex 的圆柱表面从 256 细化到 4,096 个三角形后，过载穿透从 2.267 降到 0.481 mm。</li>
    <li><strong>小步长、更多迭代不是通用修复。</strong> 固定参数迁移仍只有 1/30 通过工程检查、0/30 通过瞬态目标。</li>
  </ul>
  <a href="#experiment-findings">查看全部实验结论</a>
</article>

<article class="blog-verdict">
  <p class="blog-verdict-label">02 / Solver 认知</p>
  <h2>先分清引擎、模型、耦合和数值配置。</h2>
  <ul>
    <li><strong>同名不等于同层。</strong> MuJoCo 的 PGS、Newton 是约束求解选项；Newton Physics 是包含多个 solver 的引擎。</li>
    <li><strong>不同配置有自己的失效方式。</strong> 摩擦锥、网格、精度、停止条件和耦合路径都会改变结果。</li>
    <li><strong>通过数不能直接相加。</strong> 六引擎斜面使用不同接触表达与数值门禁，只能逐配置归因。</li>
  </ul>
  <a href="#solver-map">查看六个平台的认知</a>
</article>

<article class="blog-verdict">
  <p class="blog-verdict-label">03 / 失败根因</p>
  <h2>很多“solver 失败”在迭代前已经注定。</h2>
  <ul>
    <li><strong>先查任务、几何、控制和辅助。</strong> 浅夹持、力预算和 latch 都能直接决定结果。</li>
    <li><strong>再查双向耦合与运行时路径。</strong> Newton Kamino–VBD 的默认双连接在 ADMM 开始前就被构建校验拒绝。</li>
    <li><strong>最后才看离散与残差。</strong> 收紧容差可以降低冲量残差，却不一定消除蠕滑或跨步长差异。</li>
  </ul>
  <a href="#root-causes">查看失败根因与本轮验证门槛</a>
</article>
</div>

<nav class="blog-jump" aria-label="Blog 专题">
  <a href="#experiment-findings">实验结论</a>
  <a href="#solver-map">Solver 认知</a>
  <a href="#root-causes">失败根因</a>
  <a href="#blog-guide">研究导读</a>
  <a href="#blog-policy">策略与评测</a>
  <a href="#blog-learn">仿真学习</a>
</nav>

<p class="blog-reading-note"><strong>先读方式：</strong>表中保留绝对数值和限定条件。不同实验族的分母不同，不能加总成成功率，也不能据此给出“某引擎更强”的结论。</p>

(experiment-findings)=
## 一、对比实验分别得出了什么？

下面按“改变了一个什么变量”组织。比“谁通过了几次”更重要的是：结果是否真的对应了那次改变。

| 实验族 | 实际控制的变化 | 关键读回 | 现在能得出的结论 |
| --- | --- | --- | --- |
| Wuji 点接触 / 抗扭接触 | 只补上绕夹持线的抗扭接触能力 | 最大保持位移 **2.734 → 1.025 mm**；峰值角速度 **29.336 → 0.024992 rad/s** | 点接触缺少所需的力矩方向；问题首先是接触模型，不是夹得更紧或更换 solver |
| 平面、压入、夹圆柱 | 固定质量、控制、步长和几何，比较 MuJoCo、SuperDex、PhysX | 38 次开发实验：**25 通过、13 失败**；原始圆柱表面 SuperDex **1/4**，细化后 **4/4** | 各配置有可解释的局部边界；38 次不是独立随机试验，也不能合成引擎成功率 |
| 静力响应与卸载 | 匹配目标静态法向响应，再看动态响应 | 17 次中 **11 通过、6 失败**；部分 PhysX 工况先触发稳定性或惯量读回门禁 | 静态刚度拟合不能证明动态材料或卸载行为一致 |
| 瞬态响应与成本 | 固定目标 K、D 与载荷历史，扫描 3 个步长 | 27 次中 **9 通过、18 失败**；更小步长没有自动修复卸载拉力 | 数值细化必须和物理模型、成本与独立验收一起读 |
| 容差与步长 | 固定接触、初态和模型，只改变停止容差与步长 | 容差收紧 100 / 10,000 倍后，SuperDex 跨步长差异仍约 **3.206 mm**；MuJoCo 冲量残差下降但约 2 mm/s 蠕滑仍在 | 数值闭合改善不等于保持机制被修复 |
| 质量 / 尺寸迁移 | 冻结三套名义配置，换 10 组质量与尺寸 | 工程检查 **1/30**，瞬态目标 **0/30**，联合 **0/30** | 失败的是三套固定参数映射；没有证明其他映射或引擎算法必然失败 |
| 苹果抓梗回归 | 同一任务队列、独立后端配置 | 20 次中 **11 通过、9 失败**；固定配置下 MuJoCo **1/10**、SuperDex **10/10** | 只证明该批配置的鲁棒性差异；步长、驱动和接触表示未匹配，不是纯 solver 横评 |
| 布料留出 | 7 个原生配置、105 条冻结记录 | **52 通过、53 失败**；材料未做跨求解器等效标定 | 每个配置只在自己的协议内成立；不能把通过数合成排名 |
| Newton Kamino–VBD 耦合 | 一处与两处 FIXED 连接；再切换近邻关节可见性 | 默认双连接在构建时拒绝 `ROD`；`joint_proximal_bodies=False` 后，单 / 双连接都完成 10 × 1 ms | 失败发生在 ADMM 迭代前，是当前分区构建兼容性；不是 ADMM 被证明不收敛 |
| RSS 海绵擦拭 | 保留原控制，只移除或保留 latch | 历史匹配对照：原版 **3/3**，无 latch **0/3**；清洁比例约 **95.47% → 39.92%** | 任务成功依赖辅助保持；无 latch 失败尚不能唯一归给 SuperDex 接触 solver |
| 六引擎斜面 | 共享任务目标，但各引擎独立接触表示、配置与数值门禁 | 结果按配置分裂；存在通过、物理失败、数值拒绝和未解释小残差 | 缺少同材料目标、等效接触表示和统一门禁，不能生成总排名 |

<div class="blog-callout">
<strong>把这组实验压缩成一句话：</strong>最可信的结论都是“在什么条件下，哪个机制改变了什么结果”。数字越大、横轴越多，并不自动越接近通用引擎结论。
</div>

(solver-map)=
## 二、对这几个 solver 应该形成什么认知？

<div class="solver-grid">
<article class="solver-card">
  <header><h3>MuJoCo</h3><code>约束求解 + 原生配置</code></header>
  <p><strong>这轮真正看到的：</strong>同一斜面任务中，contact cone 与数值配置会改变结果；elliptical 配置 3/9、pyramidal 配置 0/9，同时有 6 条数值一致性拒绝。</p>
  <p><strong>正确认知：</strong>MuJoCo 的 PGS、非线性 CG 或 Newton 是可选求解角色；“MuJoCo 通过/失败”必须带着版本、接触模型、阻抗、步长和容差。</p>
</article>

<article class="solver-card">
  <header><h3>SuperDex</h3><code>接触离散 + 外层 / 内层求解</code></header>
  <p><strong>这轮真正看到的：</strong>有限指垫边缘对表面三角形数量敏感；256 / 1,024 / 4,096 个三角形对应过载穿透 2.267 / 0.858 / 0.481 mm，最细配置才四种条件全过。</p>
  <p><strong>正确认知：</strong>它暴露了“接触几何、罚力模型、停止条件、线性求解预算”如何共同影响结果。局部网格修复不等于默认配置修复。</p>
</article>

<article class="solver-card">
  <header><h3>Genesis</h3><code>接触表达 + PBD / 刚体耦合</code></header>
  <p><strong>这轮真正看到的：</strong>legacy PBD–rigid 路径中，名义摩擦 0.01 与 0.5 给出相同轨迹，布片仍以约 0.2 m/s 滑动 60 mm；动量账本还出现一个 2 ms 步长的反力延迟。</p>
  <p><strong>正确认知：</strong>这定位到该版本的接触与耦合路径，说明“有摩擦参数”不等于切向保持真的进入动力学；不能推广成 Genesis 所有软体配置都失败。</p>
</article>

<article class="solver-card">
  <header><h3>Newton Physics</h3><code>多 solver + 分区 / 精度路径</code></header>
  <p><strong>这轮真正看到的：</strong>Newton Physics 同时包含 XPBD、PADMM、DVI、VBD、Kamino 等路径。Kamino–VBD 默认双连接在构建校验处失败，而独立 XPBD 球—平面正负对照可以通过。</p>
  <p><strong>正确认知：</strong>“Newton 失败”不是有效句子；必须写清 solver、耦合方式、分区、精度和是否已进入迭代。FP32 数值门禁拒绝正例，也不等于任务在物理上不可能。</p>
</article>

<article class="solver-card">
  <header><h3>PhysX</h3><code>PGS / TGS + 适配器语义</code></header>
  <p><strong>这轮真正看到的：</strong>斜面配置中 PGS 两种各 7/9、TGS 两种各 3/9，另有 13 条正例被数值门禁拒绝；TGS 的微小残差尚没有唯一解释。</p>
  <p><strong>正确认知：</strong>PGS 与 TGS 是不同固定配置，不是可互换标签。适配器字段、惯量读回和求解路径必须先通过资格检查，再做物理比较。</p>
</article>

<article class="solver-card">
  <header><h3>Drake</h3><code>接触路径 + 接触近似</code></header>
  <p><strong>这轮真正看到的：</strong>6 种 contact path 的正例通过数为 0–6/9；lagged 摩擦逐面公式能重构额外切向支撑，但仍有 5 条微小冲量残差未解释。</p>
  <p><strong>正确认知：</strong>contact path 本身就是结果身份。解释了一部分切向支撑，不等于闭合所有残差，更不能把某一配置包装成 Drake 的整体上限。</p>
</article>
</div>

<div class="blog-callout">
<strong>比较 solver 时至少冻结：</strong>核心与绑定版本、物理模型、接触 / 摩擦表示、耦合方式、内外层算法、步长、迭代与容差、CPU / GPU、精度、运行时读回和评分器。少一项，结论的对象就可能从“solver”变成了“某次配置”。
</div>

(root-causes)=
## 三、对比实验中的失败根因

<div class="blog-answer-strip" aria-label="第一失效层的检查顺序">
  <span>任务 / 几何</span><b>→</b><span>控制 / 辅助</span><b>→</b><span>碰撞 / 接触 / 耦合</span><b>→</b><span>离散 / 残差</span><b>→</b><span>观测 / 评分</span>
</div>

判因按最早偏离预期的证据走。末帧里的“接触力归零”“没有抬起来”或“RMSE 很大”都只是现象；如果缺少能区分机制的运行时读回，就保留为未唯一确定。

| 案例 | 从初始条件 / 动作到任务后果 | 第一失效层 | 证据边界与下一判因门槛 |
| --- | --- | --- | --- |
| Wuji 夹球 | 球心相对夹持线偏置 **0.310–0.985 mm** → 偏心重力矩需要抗扭支持 → 两个点接触在保持期一直存在，但绕夹持线力矩为零 → 球持续转动 / 漂移。合成抗扭接触后位移与角速度大幅下降。 | **接触模型缺项** | 证明当前夹具需要抗扭接触，不证明真实指垫参数或 solver 错误。下一步是接触斑、指垫顺应性与新初态下的十组条件。 |
| RoboDojo layout 011 | 上缘浅夹持 → 抬升加速度放大载荷，面包相对腕部转角 **6.93°→12.45°**，上缘余量 **14.41→2.87 mm** → 接触滚出上缘，双指法向冲量从约 **0.25→0.0019 N·s** → 空夹爪继续闭合，面包下落。 | **策略 / 任务几何** | 转动与余量丢失早于冲量塌缩；闭爪命令没有漏发。下一步冻结抓取深度做 `0.016/0.028/0.034 m` A/B，并读回材质 pair、切向冲量与接触斑。 |
| Newton Kamino–VBD 双连接 | 添加第二处 FIXED 连接 → 跨岛近邻可见性把 ROD 关节暴露给 Kamino → Kamino 在 ADMM 迭代开始前拒绝分区。关闭 `joint_proximal_bodies` 后，单 / 双连接都构建并推进 10 × 1 ms。 | **构建 / 耦合兼容性** | 这是可绕过的默认配置失败，不是连接精度、力传递或完整操作验收；也没有重现更大场景中的 CUDA 700。下一步需验收约束误差与完整任务。 |
| Newton / MuJoCo VBD 毛巾 | 相同控制器下，Proxy 的 `staggered/1` 在按压阶段耗尽 600 步预算，闭合结束时距夹持目标 **7.58 mm**、夹爪宽 **9.56 mm**，尚未形成有效抓取 → 布料抬升为 0。one_way 可抬升约 **96.4 mm**，但布料反力不加载手臂。 | **耦合配置 + 控制边界** | 外迭代 4 / 16 次与 lagged 传递没有机会修复一个尚未建立的抓取；不能称 Proxy 已抓住后滑落或不收敛。下一步先让两种耦合都建立同一抓取，再比较保持与反力。 |
| Genesis PBD 布料 | 夹爪抬升 **79.988 mm** → 名义摩擦 0.01 与 0.5 的轨迹相同，布片仍以约 **0.2 m/s** 滑动 **60 mm**，最低高度仍约 **4 mm**；自由体动量还反向延迟一个 2 ms 步 → 布料没有被带离桌面。 | **接触 / 耦合模型** | 证据定位到该版本 legacy PBD–rigid 路径；重力补偿只修了夹爪自身高度。下一步应在支持双向耦合的另一路径重复同一摩擦梯度与动量账本。 |
| RSS 海绵擦拭 | latch 提供额外柔顺节点约束 → 海绵持续留在指间并完成擦拭；只移除 latch 后，匹配对照由 **3/3** 变为 **0/3**，夹持材料位移达到约 **440 mm** 量级。 | **控制 / 辅助保持** | 证明原任务依赖辅助约束，不是纯摩擦能力。下一步需在无 latch 条件下分别改变接触模型与双向反馈，才能讨论 SuperDex solver 的贡献。 |
| SuperDex 圆柱边缘 | 原始 256 三角形表面过载时穿透 **2.267 mm** → 缩步长与迭代上限 100→400 未消除原失败 → 只改表面细化到 1,024 / 4,096 后穿透 **0.858 / 0.481 mm**，最细配置四种条件全过。 | **碰撞 / 几何离散** | 中间网格仍失败，说明不是“网格越多数字单调更好”的排名。下一步要检查原生烘焙几何和接触斑，不能把 4,096 三角形配置写成默认 solver 修复。 |
| 旧夹布评分 | 在线协议只检查顶点 → 225 个保存帧中 **176 帧**存在三角形内部穿桌，最大深度 **3.00 mm** → 无效轨迹被历史任务评分记为通过。 | **观测 / 评分 → 几何** | 修评分器不会修轨迹；新 9 s 单手候选通过也不替代旧双手折叠的应变、释放和终态验收。下一步分别报告几何有效性与任务成功。 |
| 六引擎斜面 | 各引擎以不同接触表达、摩擦正则化、停止条件和精度进入任务 → 得到通过、物理失败、数值拒绝与未解释残差的混合结果 → 不能从终端位置反推一个共同 solver 根因。 | **接触 / 数值 / 未唯一确定** | MuJoCo、SuperDex、Genesis、Newton、PhysX、Drake 只能逐配置判定。下一步必须统一材料目标、几何、观测与数值门禁，再决定是否值得做真正的跨配置比较。 |

<div class="blog-conclusion">
<p><strong>当前最准确的判断：</strong>这些实验已经定位到若干可验证的引擎 / 配置层机制，包括接触模型缺项、几何离散敏感、接触与刚体耦合不足、构建分区不兼容，以及数值停止或精度门禁。</p>
<p>但它们没有建立“某个 solver 在其所有配置和任务上必然失败或必然更强”的结论。任务失败、物理无效、数值无效和记录无效必须分开记账。</p>
<p><a href="failure-root-cause-atlas.html">查看完整失败根因图谱与所有已归类案例</a> · <a href="solver-failure-audit.html">查看逐引擎 solver 失败复盘</a> · <a href="solver-taxonomy.html">查看求解配置分层</a></p>
</div>

## 继续读全部文章

(blog-guide)=
### 研究导读

先看完整问题框架，再进入具体文章：接触需要提供什么、失败发生在哪一层，以及实验结论在哪里成立。

<ul class="blog-links">
  <li><a href="_static/research/dexterous-simulation.html">当我们在讨论灵巧操作仿真时，我们在讨论什么？</a></li>
  <li><a href="_static/research/dexterous-simulation.html#layers">六层问题：从接触、策略到真实迁移</a></li>
  <li><a href="_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons">CoRL 2026：DexLab 的阅读结论</a></li>
</ul>

(blog-contact)=
### 接触与物理

先问任务需要什么力、力矩和接触历史，再讨论模型、参数与 solver。

<ul class="blog-links">
  <li><a href="wuji-contact.html">点接触与抗扭接触：一次抓持对照</a></li>
  <li><a href="contact-response.html">预测误差更低，就能预报接触失效吗？</a></li>
  <li><a href="solver-taxonomy.html">物理模型、数值问题与 solver，分别负责什么？</a></li>
</ul>

(blog-diagnosis)=
### 失败与诊断

沿动作、状态和受力追踪第一失效层，把任务评分与物理证据放在一起读。

<ul class="blog-links">
  <li><a href="failure-root-cause-atlas.html">失败根因图谱：沿着证据找第一失效层</a></li>
  <li><a href="robodojo-bread-slip.html">闭爪命令正确，面包为什么仍会掉？</a></li>
  <li><a href="rss-wiping.html">去掉辅助保持，再看擦拭任务</a></li>
</ul>

(blog-policy)=
### 策略、技能与评测

先确定动作由谁生成、执行边界在哪里、经验保存在哪里，再用独立证据判断它是否有效。完整自主改进流程仍是研究方向。

<div class="blog-subgrid">
<section class="blog-subtopic">
<h4>策略表示</h4>
<p>动作是学习得到的连续策略、运行时生成的程序，还是固定代码？</p>

<ul>
  <li><a href="code-as-policy.html">Code as Policy 专题：四种系统形态</a></li>
  <li><a href="_static/research/dexterous-simulation.html#robodojo-astra">RoboDojo / Astra：纠正动作与可靠接触控制</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h4>执行边界</h4>
<p>Agent harness、控制器、仿真器和评分器各拥有什么证据？</p>

<ul>
  <li><a href="code-as-policy.html#execution-stack">Code as Policy：程序下面还有哪些层？</a></li>
  <li><a href="model-evaluation.html">怎样把模型、执行与评分分开？</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h4>技能与记忆</h4>
<p>修复保存在代码、文本还是技能库，什么时候才能复用？</p>

<ul>
  <li><a href="_static/research/dexterous-simulation.html#capx-aspire">CaP-X / ASPIRE：从 trace 到技能晋升</a></li>
  <li><a href="_static/research/dexterous-simulation.html#coap">COAP：固定代码、显式状态与受控改动</a></li>
</ul>
</section>

<section class="blog-subtopic">
<h4>评测与归因</h4>
<p>抽象层级、反馈、预算、留出集和评分怎样改变结论？</p>

<ul>
  <li><a href="code-as-policy.html#cap-evaluation">Code as Policy 评测字段清单</a></li>
  <li><a href="_static/research/dexterous-simulation.html#benchmark-gaming-audit">榜单高分如何被误读？</a></li>
</ul>
</section>
</div>

(blog-learn)=
### 仿真学习

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
