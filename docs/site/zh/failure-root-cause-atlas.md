# 当我们在讨论仿真 Sim-to-Real Gap 问题时，我们在讨论什么？

这篇文章只回答一个问题：**一条仿真结论，凭什么可信？**

## 先给结论

Sim-to-Real Gap 不是最后一帧与视频的差异，也不是一个可以脱离证据定义的误差。更准确地说：

> **Gap 是一条证据链中最早失效的那一环。**

任务可能定义错了；配置可能没有进入运行时；执行器可能没有足够的力；碰撞几何或接触模型可能不表达任务需要的机制；步长和停止条件可能让数值解无效；观测、评分或日志也可能让失败看起来像成功。再往后，只有真机数据才能检验现实误差。

下面五件事必须分别回答，不能用其中一个代替另一个：

1. **任务是否成功？** 只说明冻结评分器中的任务谓词是否通过。
2. **模型内物理是否自洽？** 检查支撑、力与力矩、非穿透、耦合、守恒和预算。
3. **数值是否有效？** 检查求解状态、残差、步长敏感性和停止条件。
4. **记录是否可信？** 检查观测是否过期、字段是否正确、评分是否覆盖真实失效、记录是否扰动运行。
5. **现实是否被验证？** 只有真实传感器、执行器、材料和任务测量能回答。

> **没有真机实验，可以证明“参数送达、状态一致、预算闭合、对照有效、结果可复现”。不能证明“真实材料参数、硬件时延、现实任务误差或 sim-to-real transfer 已完成”。**

## 只找最早断裂的一层

<div class="gap-chain" role="group" aria-labelledby="gap-chain-title">
  <div class="gap-chain-copy">
    <p id="gap-chain-title">最终失败只有一个，可信假设却可以更早断掉。</p>
    <strong>先冻结同一问题与同一初态，再沿因果链向前找。</strong>
  </div>
  <ol class="gap-chain-track">
    <li><span>0</span><strong>前置<br>检查</strong><small>运行时读回、单位、坐标系与初态是否一致</small></li>
    <li><span>P</span><strong>任务<br>动作</strong><small>抓取位置、动作顺序、净空与目标是否合理</small></li>
    <li><span>A</span><strong>执行器<br>辅助</strong><small>所需的力、力矩或保持是否由明确机制提供</small></li>
    <li><span>G</span><strong>碰撞<br>几何</strong><small>引擎是否准确表示任务依赖的形状与离散</small></li>
    <li><span>C</span><strong>接触<br>材料</strong><small>法向、摩擦、接触力矩与耦合是否足够</small></li>
    <li><span>N</span><strong>数值<br>求解</strong><small>步长、停止、残差与精度是否让结果有效</small></li>
    <li><span>O</span><strong>观测<br>证据</strong><small>输入、评分、字段与记录是否可信</small></li>
  </ol>
  <div class="gap-chain-boundary">
    <span><b>P/A/G/C/N/O</b> 是模型内的第一失效域；“前置检查”不通过时先修复证据身份，不进入机制归因</span>
    <span><b>真机有效性</b> 不由模型内检查自动补足</span>
  </div>
</div>

几个边界需要说清：

- **P 与 G 不重叠。** P 问“这个抓取位置和动作是否让任务可能成立”；G 问“引擎有没有准确表示这个已经规划好的几何”。同一个点，前者是任务设计，后者是碰撞表示。
- **A 不等于求解器。** 指力不足、隐藏辅助或控制器预算决定结果时，先记 A；不能因为最后发生接触，就改判为接触或 solver 错误。
- **N 不等于“步长越小越真实”。** 更细的步长可能改变相位、暴露不稳定或增加成本；只有固定模型和输入后的敏感性记录才能说明数值行为。
- **O 位于动力学结论之前。** 如果观测过期、字段错映射或评分漏检，后面的物理量再精细也不能支撑该结论。
- **证据不足就停在 U。** `U` 表示现有记录不能唯一区分多个机制，不是一种新的物理根因。

“第一失效层”也不一定是时间上最早出现的异常。它指：**结论所依赖的最早一个被现有证据否定或无法成立的假设。** 主因之外可以有放大器，但放大器不能替代已经证实的第一层。

## 四个案例，把一条链走完

<div class="gap-evidence-gallery">
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="robodojo-bread-slip.html" aria-label="查看 RoboDojo layout 011 完整记录">
      <img src="_static/robodojo-bread-slip/layout-011-preview.gif" alt="RoboDojo layout 011：上缘浅夹持、面包转动与接触几何消失的记录画面" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">P · 任务动作</span>
      <strong>面包不是“突然掉了”</strong>
      <p><b>因果链：</b>上缘浅夹持 → 抬升阶段约 4.58 m/s² 的向上加速度放大有效载荷 → 面包在夹爪平面内转动，上缘余量由 14.41 缩到 2.87 mm → 法向冲量从约 0.25 降到 0.0019 N·s → 面包下落并撞桌。</p>
      <small><b>证据边界：</b>闭爪命令始终为 0，释放前没有邻片或货架冲量。缺少完整切向冲量、运行时材质 pair 和原生碰撞网格，因此只能确认 P 与抬升放大器，不能把剩余差异单独归给摩擦、顺应性或 PhysX solver。</small>
      <a href="robodojo-bread-slip.html">查看完整时间线与对照 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="_static/force-limit/comparison.gif" aria-label="打开 Genesis 低力夹持对照 GIF">
      <img src="_static/force-limit/comparison.gif" alt="Genesis 0.4 N 与 0.8 N 每指力限额下的夹持与抬升对照" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">A · 执行器预算</span>
      <strong>“抓不住”可能只是力不够</strong>
      <p><b>因果链：</b>每指限额为 0.2/0.4 N → 桌面仍承担约 0.428/0.228 N，物体没有随夹爪离桌；提高到 0.8/10 N 后，手指支持约 0.628 N，接近物体重量，桌面支撑才降到零。</p>
      <small><b>证据边界：</b>这是一次物理上可解释的任务失败，不是数值 solver 缺陷。±2 mm 位置对照保持同一结论；GIF 是测量姿态回放，真正支撑判断的是力账本。</small>
      <a href="visual-comparisons.html#pinch">查看夹持与释放对照 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="wuji-contact.html" aria-label="查看 Wuji 点接触与抗扭接触完整报告">
      <img src="_static/wuji-contact/comparison.gif" alt="Wuji 同任务点接触失败与抗扭接触通过的同步记录" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · 接触材料</span>
      <strong>一直有接触，球仍会绕夹持线转</strong>
      <p><b>因果链：</b>球心相对夹持线有约 0.310–0.985 mm 偏置 → 需要绕夹持线的抗扭力矩 → 点接触的纯力抓取映射秩为 5，不能提供该方向 → 两指接触持续存在，球仍转动和漂移。</p>
      <small><b>证据边界：</b>只增加合成抗扭接触后，两秒最大位移由 2.734 降到 1.025 mm，峰值角速度由 29.336 降到 0.024992 rad/s。这证明当前夹具缺少一个接触力矩方向，不证明真实指垫参数已标定，也不证明 solver 错误。</small>
      <a href="wuji-contact.html">查看接触模型与保持曲线 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="libero-workflow.html" aria-label="查看 LIBERO 工作流报告">
      <img src="_static/visual/libero-demo0-baseline.gif" alt="LIBERO 原生任务与记录画面" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">O · 观测证据</span>
      <strong>任务能成功，记录仍可能不可信</strong>
      <p><b>因果链：</b>reset 生成 observation → 额外 5 个零动作 settling 步改变状态 → 评测继续读取 settling 前的 observation → 末端位置已变化 4.481 mm、夹爪关节变化 12.143 mm → 动作和诊断从过期状态开始。</p>
      <small><b>证据边界：</b>重新获取 observation 只恢复状态身份，尚未证明策略收益。把物理步长由 2 ms 缩到 1 ms 后，诊断通过数反而由 5/10 降到 3/10，成本近翻倍，说明缩步不能替代归因。</small>
      <a href="libero-workflow.html">查看观测生命周期与完整记录 →</a>
    </figcaption>
  </figure>
</div>

这四个案例分别对应 P、A、C、O。G 和 N 的完整失败边界、未判定项以及正负对照仍在逐配置记录中，不在这里制造第五、第六个“代表故事”。

## 任务成功为什么不等于物理正确

任务成功只说明评分器定义的谓词通过了。它不能自动说明：

- 碰撞几何覆盖了真实接触；
- 接触模型提供了任务所需的力或力矩；
- 外力、执行器、支撑和能量账本闭合；
- 数值解达到冻结门禁；
- observation、字段映射、评分和记录没有改变结论。

所以，“通过率”不能跨不同材料目标、接触表示、初态、精度、停止条件和评分器直接相加。相同任务名也不等于同一个物理问题。这样的总和会把模型差异、无效记录和任务失败混成一个看似精确的排名。

## 没有真机，哪些话可以说

| 可以证明 | 不能证明 |
| --- | --- |
| 配置确实送达运行时，记录对应实际状态 | 配置参数等于真实材料、传感器或执行器参数 |
| 同一任务、初态、输入和评分下的正负对照有效 | 仿真中的时序、时延和执行器响应等于硬件 |
| 力、力矩、动量、角动量和能量预算在该模型内闭合 | 模型外的真实接触和材料行为也已闭合 |
| 改变步长、容差、精度或参数后，结果按记录变化 | “更细”“更稳定”或“更像视频”就是更真实 |
| 冻结模型中的任务失败或成功可以复现 | sim-to-real transfer 已经完成 |

当前 DexLab 的真机实验数为 **0**。因此，本页讨论的是仿真内部的物理与证据可信度，以及仍未获得真机验证的现实误差，不把两者混成一个结论。

## 遇到失败，按这五步查

1. **先冻结五个判定。** 任务成功、物理自洽、数值有效、记录可信、现实有效分别写清。
2. **按时间排列证据。** 命令、执行器、相对位姿、几何余量、接触力或冲量、外部碰撞、残差和任务结果必须落在同一条时间线上。
3. **先做预算和守恒。** 重量由谁支撑？所需力矩方向是否存在？外力、冲量和能量是否闭合？
4. **一次只改一个变量，并保留正负对照。** 抓取深度、力限额、latch、碰撞网格、接触模型、步长和容差分别改动。
5. **读运行时，不读愿望。** 核对最终材质 pair、接触参数、solver、精度和碰撞形状；证据不足时写 `U`，并给出下一次判因门槛。

## 完整证据在哪里

本页是阅读路径，不重复完整账本：

- [完整实验目录](experiments.md)：查看历史 demo、研究经验和新增实验。
- [全部结果与失败](results.md)：按结果、失败和证据边界继续追踪。
- [逐配置 solver 复盘](solver-failure-audit.md)：查看引擎、配置和数值门禁的具体差异。
- [历史证据清单](solver-failure-inventory.md)：查看公开入口、证据目录和成功负对照。

## 参考文献

1. Elie Aljalbout et al. [The Reality Gap in Robotics: Challenges, Solutions, and Best Practices](https://arxiv.org/abs/2510.20808). arXiv:2510.20808, 2025.
2. Google DeepMind. [MuJoCo documentation](https://mujoco.readthedocs.io/). Contact, solver and runtime documentation.
3. Bo Liu et al. [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](https://arxiv.org/abs/2306.03310). arXiv:2306.03310, 2023.
4. Chen et al. [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](https://arxiv.org/abs/2607.04434). arXiv:2607.04434, 2026.
5. Meta Research. [SuperDex](https://github.com/facebookresearch/project_superdex). Official repository and versioned implementation.

### 项目引用

```bibtex
@software{dexlab2026,
  author  = {Kiki Huang},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```
