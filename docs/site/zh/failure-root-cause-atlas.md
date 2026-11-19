# 当我们在讨论仿真 Sim-to-Real Gap 问题时，我们在讨论什么？

**DexLab 是 Kiki Huang 的个人研究项目。** 这篇文章把现有实验重新组织成一个问题：仿真里“看起来对”或“任务成功”，究竟能证明什么？

## 先给结论

Sim-to-Real Gap 通常被说成一个误差、一次失败，或者“仿真器和现实不一样”。这些说法都不够具体。

更可检验的定义是：**Gap 是一条逐层失效的证据链。** 任务和本体可能不代表现实；目标参数可能没有送达引擎；单位、初态或执行器预算可能先错；几何、接触和耦合可能不支持任务；步长和停止条件可能使记录无效；观测、评分和日志可能把失败记成成功；即使这些都在冻结模型内通过，没有真机数据仍不能证明现实误差。

因此 DexLab 不从“哪个引擎最好”开始，而从最早偏离预期的那一层开始。面包滑落前的法向载荷归零、布料穿桌后的任务失败、缩小步长后的指标变差，都是结果；第一失效层可能更早出现在抓取几何、执行器预算、辅助约束、碰撞覆盖、接触定律、观测刷新或证据记录。

> **没有真机实验时，可以证明的是：参数确实送达、数值记录自洽、守恒与预算闭合、正负对照有效、参数变化后的回归可复现。不能证明的是：真实传感器时序、真实执行器响应、真实材料参数和 sim-to-real 迁移已经完成。**

本页统一用五个问题复盘实验：**现象 → 第一失效层 → 因果链 → 证据证明／未证明什么 → 下一次判因门槛**。这里的“根因”只指现有证据能够定位到的最早一层；证据不足时保留 `未唯一确定`，成功或只做了准入检查的实验记为 `未观察到可归因失败`。

## Gap 不是一件事，而是一条链

<div class="gap-chain" role="group" aria-labelledby="gap-chain-title">
  <div class="gap-chain-copy">
    <p id="gap-chain-title">同一句“仿真失败”，可能坏在任何一层。</p>
    <strong>先找最早偏离，再解释最后结果。</strong>
  </div>
  <ol class="gap-chain-track">
    <li><span>01</span><strong>任务<br>与本体</strong><small>问的是不是同一个问题</small></li>
    <li><span>02</span><strong>参数<br>送达</strong><small>配置是否真的进入运行时</small></li>
    <li><span>03</span><strong>单位<br>与初态</strong><small>后续轨迹是否从同一状态开始</small></li>
    <li><span>04</span><strong>执行器<br>预算</strong><small>谁提供任务所需的力和力矩</small></li>
    <li><span>05</span><strong>几何·接触<br>材料</strong><small>需要的物理机制是否存在</small></li>
    <li><span>06</span><strong>观测·评分<br>记录</strong><small>结论读的是不是可信状态</small></li>
    <li><span>07</span><strong>真机<br>验证</strong><small>现实误差是否被独立测量</small></li>
  </ol>
  <div class="gap-chain-boundary">
    <span><b>P/A/G/C/N/O</b> 由模型内读回、正负对照、守恒与回归检验</span>
    <span><b>真机外部有效性</b> 不由前六层的仿真通过自动补足</span>
  </div>
</div>

| 判断层 | 要问的问题 | 若这一层先错，后面的结论会怎样 |
| --- | --- | --- |
| 1. 任务与本体定义 | 任务目标、机器人、物体、环境和成功条件是否代表要研究的现实问题？ | 物理引擎再稳定，也可能在回答另一个问题 |
| 2. 参数实际送达 | 配置中的质量、惯量、摩擦、接触对、求解器和精度是否真的进入运行时？ | 文件名和 YAML 正确，不代表原生状态正确 |
| 3. 单位、初态与时钟 | 长度、质量、角度、重力、reset、控制和物理步是否一致？ | 后续轨迹从错误起点开始 |
| 4. 执行器与受力预算 | 指力、力矩、支撑、功和能量由谁提供，是否可能完成目标？ | “抓不住”可能只是物理上合理地失败 |
| 5. 几何、接触、材料与离散 | 碰撞形状、法向、摩擦、接触力矩、软硬耦合和时间步是否能表达所需机制？ | 有接触不等于有承载，有穿透不等于 solver 错误 |
| 6. 观测、评分与记录 | 策略和评分读到的是新状态吗？评分是否覆盖真实失效？日志是否扰动运行？ | 过期观测、漏检评分或记录器差异会制造假结论 |
| 7. 真机外部验证 | 真实传感器、执行器、材料、时延和任务表现是否被独立测量？ | 仿真内部通过仍不能称为 sim-to-real 验证 |

后文仍使用 `P/A/G/C/N/O/U` 七类第一失效层：`P` 对应任务和几何，`A` 对应控制、执行器和辅助，`G` 对应碰撞与几何离散，`C` 对应接触、材料和耦合，`N` 对应时间离散、停止和精度，`O` 对应观测、适配器、评分和证据，`U` 表示现有记录不足以唯一区分多个机制。分类允许“主因 + 放大器”；放大器不能替代已经证实的第一失效层。

## 代表性实验：每一层都在现有博客里出现过

| 研究层 | 代表实验 | 关键判断 |
| --- | --- | --- |
| 任务几何 | RoboDojo layout 011 | 面包先在浅夹持中转动，上缘余量从 14.41 缩到 2.87 mm，随后法向冲量才塌缩；最终掉落不是根因 |
| 执行器与隐藏辅助 | 0.4 N 夹持、RSS 擦拭 | 低指力留下桌面支撑；RSS 的 3/3 成功依赖 latch，去掉后为 0/3 |
| 几何与耦合 | 旧夹布、Genesis PBD 薄布 | 顶点评分可通过而三角形仍穿桌；名义摩擦改变但切向保持仍缺失 |
| 接触力矩空间 | Wuji 点接触 | 两指始终有接触，球仍绕夹持线转动；补上抗扭方向后峰值角速度从 29.336 降到 0.024992 rad/s |
| 参数迁移与瞬态 | 质量／尺寸迁移、接触起始 | 名义点可拟合，但 30 组联合目标 0/30；收紧停止容差不消除蠕滑 |
| 观测与比较语义 | LIBERO、香蕉 64×、AMP | 陈旧观测、错误接触相位和记录器差异都必须在动力学归因前排除 |
| 多引擎比较 | 六引擎斜面 | 相同任务不等于相同材料目标、接触表达和数值门禁，不生成假排名 |
| 真机外部验证 | 硬件采集协议 | 只有协议，没有合格真机数据；真机实验数仍为 0 |

这些实验共同说明：**Sim-to-Real Gap 不是最后一帧与视频的差距，而是“我们凭什么相信这条结论”的差距。**

## 从画面看，Gap 先在何处断裂

<div class="gap-evidence-gallery">
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="robodojo-bread-slip.html" aria-label="查看 RoboDojo layout 011 完整记录">
      <img src="_static/robodojo-bread-slip/layout-011-preview.gif" alt="RoboDojo layout 011：上缘浅夹持、面包转动与接触几何消失的记录画面" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">P · 任务几何</span>
      <strong>面包不是“突然掉了”</strong>
      <p>双指法向冲量塌缩前，OBB 代理的上缘平均余量已经从 <b>14.41</b> 缩到 <b>2.87 mm</b>；随后接触几何才消失。</p>
      <small><b>证据边界：</b>画面能看见姿态变化；第一失效层由同相位的余量、转角与冲量时间线确定，不能只看 GIF 猜根因。</small>
      <a href="robodojo-bread-slip.html">查看 layout 011 完整记录 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="_static/force-limit/comparison.gif" aria-label="打开 Genesis 低力夹持对照 GIF">
      <img src="_static/force-limit/comparison.gif" alt="Genesis 0.4 N 与 0.8 N 每指力限额下的夹持与抬升对照" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">A · 执行器预算</span>
      <strong>“抓不住”可能只是力预算不够</strong>
      <p>低限额下只剩 <b>0.2/0.4 N</b> 指力，桌面仍承担约 <b>0.428/0.228 N</b>；提高到 0.8/10 N 后，物体才随夹爪离桌。</p>
      <small><b>证据边界：</b>这是可解释的物理失败，不是数值 solver 缺陷；画面是测量姿态回放，支撑结论仍来自力账本。</small>
      <a href="visual-comparisons.html#pinch">查看夹持与释放对照 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="wuji-contact.html" aria-label="查看 Wuji 点接触与抗扭接触完整报告">
      <img src="_static/wuji-contact/comparison.gif" alt="Wuji 同任务点接触失败与抗扭接触通过的同步记录" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · 接触扳手空间</span>
      <strong>一直有接触，球仍会绕夹持线转</strong>
      <p>点接触配置下两指接触持续存在，峰值角速度约 <b>29.336 rad/s</b>；只补抗扭方向后降到 <b>0.024992 rad/s</b>。</p>
      <small><b>证据边界：</b>证明当前夹具缺少一个接触力矩方向，不外推为真实指垫参数或所有 solver 的普遍缺陷。</small>
      <a href="wuji-contact.html">查看接触模型与保持曲线 →</a>
    </figcaption>
  </figure>
  <figure class="gap-evidence-item">
    <a class="gap-evidence-media" href="visual-comparisons.html#incline" aria-label="查看六引擎斜面完整对照">
      <img src="_static/visual/incline-static-0.001.png" alt="六个物理引擎在相同斜面场景中的静止响应、版本、精度与通过或失败标记" loading="lazy" decoding="async">
    </a>
    <figcaption>
      <span class="gap-evidence-kicker">C · N · U</span>
      <strong>同一个任务名，不等于同一个物理目标</strong>
      <p>六引擎斜面分别记录静止、滑动和名义零摩擦；接触表达、数值精度、停止门禁与无效记录必须逐配置保留。</p>
      <small><b>证据边界：</b>这张图支持配置差异与拒绝原因，不支持把不同预算和门禁相加成“引擎排行榜”。</small>
      <a href="visual-comparisons.html#incline">查看同步回放与完整矩阵 →</a>
    </figcaption>
  </figure>
</div>

## 七类第一失效层

| 代码 | 第一失效层 | 判据 | 代表案例 |
| --- | --- | --- | --- |
| **P 策略／任务几何** | 抓取点、动作顺序、净空、目标或终止逻辑先错 | 在接触或求解异常前，动作已经把系统带入不可保持状态 | RoboDojo 上缘浅夹持、邻片干涉 |
| **A 控制／执行器／辅助** | 力限额、控制状态或隐藏保持机制先决定结果 | 受力账本能由控制预算或额外约束闭合 | 0.2/0.4 N 指力不足、RSS latch |
| **G 碰撞／几何离散** | 碰撞形状、网格、接触点或评分几何先失真 | 同一物理设置只改几何覆盖，失效边界改变 | 旧夹布三角形穿桌、圆柱表面细化 |
| **C 接触／材料／耦合** | 摩擦、法向响应、接触力矩、双向耦合或材料映射不满足任务 | 控制与几何有效，但所需的力／力矩方向或耦合不存在 | Wuji 点接触缺抗扭、Genesis PBD 无切向保持 |
| **N 时间离散／求解停止／精度** | 步长、停止条件、残差或数值表示先违反门禁 | 固定模型与输入后，数值门禁或细化曲线拒绝结果 | SuperDex 接触起始、部分斜面和夹持记录 |
| **O 观测／适配器／评分／证据** | 状态过期、字段映射、评分覆盖或记录一致性先失败 | 动力学结论依赖的输入或测量已经不可信 | LIBERO 陈旧观测、AMP 记录器一致性、旧夹布评分 |
| **U 未唯一确定** | 现有记录只能缩小范围，不能区分多个机制 | 缺少受控 A/B、运行时读回或同相位比较 | MJWarp 路径差异、部分多引擎斜面残差 |

分类允许“主因 + 放大器”。例如 RoboDojo layout 011 的主因是 **P：上缘浅夹持**，抬升加速度是放大器；缺少顺应性可能贡献，但当前只能记为待验证的 **C**，不能替代已证实的几何链。

## 已有实验覆盖总表

### 15 个历史 demo

| 实验 | 观察到的失败或边界 | 第一失效层 | 当前判因 |
| --- | --- | --- | --- |
| `apple-stem-grasp` | 历史十场景 MuJoCo 1/10、SuperDex 10/10；步长、摩擦、驱动和接触表示未匹配 | **U**，候选为 C/G/控制配置 | 只能描述固定配置鲁棒性，不能从跨后端差异推出引擎根因；默认开发场景通过不等于历史队列已修复 |
| `banana-cut` | 三刀／四段机械分离通过，原始开发失败保留 | 未观察到可归因的发布失败 | 证明合成切割历史和机械分离，不证明真实香蕉力学 |
| `banana-force` | 64× 粒子工况 0.5 s 内未到达砧板接触相位，nRMSE 2.051 | **O：比较相位／时窗不对齐** | 先失败于“没有比较同一物理阶段”；不能用它证明细化不收敛或材料力错误 |
| `cloth-benchmark` | 7 配置／105 记录通过数不同，材料与接触假设未等效 | **U** | 可以保留各自协议结果，不能合并成引擎排名或共同材料失败 |
| `cloth-folding` | 旧记录 176/225 帧三角形穿桌；旧双手还失败于应变、释放和终态 | **O → G**，随后是任务几何 | 顶点评分先漏检，独立三角形检查暴露真实穿桌；新 9 s 单手候选通过但不等于双手折叠完成 |
| `contact-benchmark` | 38 个早期开发实验 25 通过、13 失败；后续分解为几何、响应、迁移、卸载和数值门禁 | **G/C/N/U**，按子协议判定 | 不存在一个“contact benchmark 根因”；见下方逐项卡片 |
| `cut-push` | 数值抖动、步长影响和材料差异保留；刀面推动对照可闭合 | **U**（对未标定物性） | 已证明位移来自刀面接触，不证明真实食材精度；成功记录不强行制造失败根因 |
| `cutting-refinement` | 细化记录通过机械检查 | 未观察到可归因失败 | 只支持既定合成机械检查，不是连续极限或真实材料收敛认证 |
| `libero-contact` | 原任务可成功，但 settling 后评测使用陈旧观测；物理诊断仅部分通过 | **O：状态刷新语义** | 一行刷新修复观测身份；没有证明策略成功率因此提高，也没有把其余接触失败归给 solver |
| `physx-contact` | 接触报告 API 缺失由适配器补齐；15 个布料配置中 1 个表面穿越、4 个外力接口不支持 | **O/G/能力边界** | 原生基元通过只证明局部准入；接口不支持不是物理失败，表面穿越需单独几何诊断 |
| `rss-wiping` | 有 latch 3/3，通过；仅移除 latch 后 0/3 | **A：辅助保持依赖** | 任务成功依赖附加柔顺节点约束；无 latch 失败尚不能唯一归为接触 solver |
| `tofu-comparison` | 历史两刀与当前刀推输入不同 | **O：协议不可直接比较** | 不能把作者末端初速度与当前刀面接触推动合成同一物理对照 |
| `tofu-cut` | 完整切割与未切／部分切负对照符合协议 | 未观察到可归因的发布失败 | 支持合成拓扑变化，不支持任意姿态切割或真实豆腐标定 |
| `tofu-knife-push` | 半步长、无推和材料对照保留；未完成真实材料精度判定 | **U**（物性） | 已闭合“谁推动了末块”，未闭合材料误差 |
| `tofu-scoring` | 默认与半步长保持底部连通，未切负例被拒绝 | 未观察到可归因失败 | 支持指定引导切口和连通性评分，不外推自由切割 |

### 8 项研究经验

| 经验 | 第一失效层与因果链 | 结论边界 |
| --- | --- | --- |
| `normal-response` | MuJoCo 固定参数的质量迁移改变有效斜率；SuperDex／PhysX 部分工况先触发稳定性或惯量读回门禁：**C/O** | 静态刚度匹配不代表动态材料等效；PhysX 惯量序列化修复后稳定性失败仍在 |
| `transient-cost` | MuJoCo 高阻抗不匹配目标；SuperDex 的载荷相关阻尼在卸载产生瞬时拉力，缩步未消除：**C**，步长是 **N** 放大／诊断变量 | 27 次中 9 次联合通过、18 次失败；不能把脚本总耗时当 solver 排名 |
| `mass-size-transfer` | 三套固定映射不含质量／面积补偿，30 组联合目标 0/30：**C：参数映射超出适用域** | 失败的是冻结映射，不是原生算法被证明错误；其他映射仍可能成立 |
| `physx-observation` | 原始适配器缺少或误分类接触／地面字段：**O：适配器语义** | 适配修复只恢复可观测性，不自动把物理任务改为通过 |
| `pinch-load` | 低阻抗慢蠕滑、高阻抗改善；临界载荷有接触丢失／再碰撞；6 条记录因残差门禁无效：**C + N** | 3/18 通过、9 个物理失败、6 个数值拒绝；残差下降不等于蠕滑消失 |
| `six-engine-incline` | 每个后端的接触表达、摩擦正则化、停止条件和数值精度不同：**C/N/U** | 只能逐配置归因；分母和门禁不同，不生成总排名 |
| `framework-path` | 对齐 CPU 模型和核心后仍有 GPU 字段／轨迹差异：**O/U** | 已缩小到框架路径与运行时字段，尚未唯一定位到某个核心算法 |
| `libero-workflow` | settling 后未刷新 observation 先造成 4.481 mm 末端位姿和 12.143 mm 夹爪关节语义偏差：**O** | 修复观测语义，不声称策略收益；1 ms 物理诊断 3/10 低于 2 ms 的 5/10，缩步不是自动修复 |

### 其余注册证据族

这些队列不是新的独立任务目录，但同样属于历史实验账本。重复指向上表或下方卡片的 `cloth-studio`、`cutting`、`force-limit`、`framework-mjwarp`、`genesis-cloth`、`libero`、`pinch-load` 和 `rss-wiping` 不重复计数。

| 证据族 | 第一失效层 | 根因结论与边界 |
| --- | --- | --- |
| `drake-contact-paths` / `drake-incline` | **C + U/N** | kLagged 摩擦公式能重构额外切向支持，说明滑动偏差含接触近似机制；5 条微小冲量残差仍未唯一解释 |
| `elastic-impact` | 未观察到终态门禁失败 | 18/18 只证明有限终态检查；没有连续轨迹或真实材料参考时不外推碰撞精度 |
| `engine-qualification` | **O/G** | 版本与 API 准入通过不等于任务准入；MuJoCo 新版本布料样本仍出现桌面侵入，几何失败没有被“升级成功”覆盖 |
| `genesis-incline` | **C/N** | 接触表达、名义零摩擦下限和 CG 停止一致性共同影响结果；只能逐配置判因 |
| `impact-discrete` | 未观察到离散方程重构失败 | 54/54 与声明的离散更新一致；这不证明连续时间物理精确 |
| `impact-phase` / `impact-stiffness` | **G/N/C** | 接触到达相位、刚度与步长共同改变穿透；浮点边界拒绝保留，最细网格不作真值 |
| `incline-comparison` / `incline-diagnosis` / `incline-friction` | **C/U** | 同几何但接触模型不等效；单改 `impratio` 不能消除整套失败，软接触静漂和滑动误差仍在 |
| `mujoco-incline` | **C/N/U** | elliptic 3/9、pyramidal 0/9 且有 6 条数值一致性拒绝；证明固定配置结果，不证明 MuJoCo 普遍失效 |
| `newton-incline` / `newton-xpbd` | **N/O**；球—平面准入无失败 | 大量斜面正例先被 FP32 数值门禁拒绝，门禁不是严格误差上界；独立 XPBD 球—平面正／负对照通过 |
| `physx-incline` | **N/U** | PGS/TGS 结果与 13 条数值拒绝并存；TGS 微小残差尚未唯一解释 |
| `superdex-incline` | **C/N** | 0.5 ms 静漂、摩擦正则化与 CG `STOPPED` 残差并存；BFGS/SR1 在 assembly=1 下实际等效 Newton，不作为独立算法归因 |
| `pinch-impulse` | **N + C** | 收紧停止容差使冲量残差下降，但蠕滑没有消失；数值闭合改善不等于保持机制修复 |
| `synthetic-tactile` | **A/O** | 重力补偿先掩盖真实支撑，导致端点误差；延长跟踪后的局部通过是控制修正，不是触觉传感真实性验证 |
| `unisim-contact-migration` / `unisim-reuse` | **O**，适配范围内无新增根因 | 21 对原生／适配器重评分一致且保留低力失败；证明包装层语义，不创造新的 solver 能力或任务成功 |
| `studio` / `visual` | 不产生物理根因判定 | 复用已有轨迹和来源做展示；视觉一致不是新仿真运行或物理验收 |

### 后续新增入口

| 实验 | 第一失效层 | 当前结论 |
| --- | --- | --- |
| Wuji 夹球 | **C：接触扳手不完备** | 点接触的纯力抓取映射秩为 5，不能抵抗绕夹持线的重力矩；提高法向力不会创造缺失力矩方向 |
| RoboDojo layout 002 | **P/G：上缘浅夹持 + 邻片／货架净空不足** | 邻片冲量先放大转动，接触滚出上缘；不是漏发闭爪命令 |
| RoboDojo layout 011 | **P：上缘浅夹持**；抬升是放大器 | 面包先在夹爪平面内旋转、上缘余量缩小，之后法向冲量才塌缩；不是“载荷无故消失” |
| RoboDojo v67 `s0/l025`、`s1/l026`、`s1/l049` | **P → U(A/C/N)：槽口卡滞后继续深压；逃逸内部归因未唯一确定** | 向下目标期间，观测关节 FK 的 TCP 反向上升 10.6–28.3 cm；证明仿真状态逃逸，不足以把全部能量唯一归给 solver |
| AMP 抬箱 | **O：记录器一致性资格失败** | 两个探针正常结束但记录前后状态差超限；不能据此判断 AMP 策略抬箱失败，完整回合未运行 |
| 接触丢失预测 | **O／模型目标** | 常速模型降低位置误差却漏报释放事件；低位姿误差不是接触事件预测能力 |

[逐目录、逐后端的完整旧清单](solver-failure-inventory.md)继续保留 RSS 50 个公开入口、全部证据目录和成功负对照；`docs/evidence` 根目录的 manifest、图表和版本附件归随其所属队列，不冒充独立实验。本页不把外部示例的 scoped pass 改写成 DexLab 的失败实验。

## 完整失败案例卡

下表卡保留每个失败或边界案例的原始数字、时间线、证据和下一门槛。代表实验表负责给出阅读路径；这些卡片负责避免把汇总结论写成无法复查的概括。

### 1. RoboDojo layout 011：为什么没有碰撞也会掉？

- **现象：** step 188 双指法向冲量从约 0.25 N·s 降至 0.0019 N·s，随后自由落体；闭爪命令始终为 `0`。
- **第一失效层：P，浅抓取几何。** step 186→188，面包相对腕部的平面内转角约 **6.93°→12.45°**，OBB 代理的上缘平均余量从 **14.41→2.87 mm**，然后接触几何消失。
- **因果链：** 上缘浅夹持 → 抬升阶段约 **4.58 m/s²** 向上加速度放大有效载荷 → 面包绕夹持线转动、接触滚向上缘 → 双指冲量塌缩 → 空夹爪继续闭合 → 面包下落并在 step 192 撞桌。
- **证据证明：** 转动和上缘余量丢失早于法向冲量塌缩；释放前没有邻片／货架冲量。
- **证据未证明：** 无完整切向冲量、运行时材质 pair 和原生碰撞网格，不能唯一拆分摩擦、刚性边缘、缺少顺应性与抬升加速度各自贡献，更不能宣称 PhysX solver 缺陷。
- **下一门槛：** 相同初态下冻结抓取深度，A/B `0.016 → 0.028 → 0.034 m`；同时读回材质 pair、切向冲量和接触斑，再测顺应性模型。

[完整 GIF 与两例对照](robodojo-bread-slip.md) · <a href="_static/robodojo-bread-slip/layout-011-root-cause.json">派生时间线 JSON</a>

### 2. Wuji：为什么夹得更紧仍会绕轴滑？

- **现象：** v3 两个点接触在 4,000 个保持步中都存在，但球仍漂移，最大角速度约 29.336 rad/s。
- **第一失效层：C，接触扳手空间缺一个方向。** 纯法向／切向力构成的抓取映射秩为 5，原生接触绕法线力矩为零；球心相对夹持线的 0.310–0.985 mm 偏置产生绕夹持线重力矩。
- **因果链：** 质心偏置 → 需要绕夹持线的抗扭力矩 → 点接触模型不提供该方向 → 有接触、有法向力仍持续转动／漂移。
- **受控证据：** 只增加合成抗扭接触后，两秒最大位移 **2.734→1.025 mm**，角速度峰值 **29.336→0.024992 rad/s**。
- **边界：** 这证明当前夹具的接触模型机制，不证明真实指垫参数已标定，也不证明 solver 错误。

[Wuji 报告](wuji-contact.md)

### 3. 0.4 N 夹持：为什么合理地失败？

- **现象：** Genesis 0.2/0.4 N 每指力限额不能保持，0.8/10 N 可以。
- **第一失效层：A，执行器力预算。** 低限额时两指向上支持只有 0.2/0.4 N，剩余约 0.428/0.228 N 仍由桌面承担；0.8/10 N 时手指支持约 0.628 N，闭合物体约 0.628 N 重量。
- **因果链：** 指力上限 → 摩擦支持上限不足 → 桌面仍承载 → 抬升时物体未随夹爪离桌。
- **边界：** 这是物理上可解释的任务失败，不是数值 solver 缺陷；±2 mm 对照保持同一结论。

### 4. RSS 擦拭：为什么“成功”依赖隐藏保持？

- **现象：** 原任务 3/3，通过；只移除 latch 后 0/3，清洁率约 95.47%→39.92%，即使接触力更高也会脱手。
- **第一失效层：A，额外辅助约束。** latch 通过 `pin_nodes + ride` 提供约 4,000 N/m、20 N·s/m 的柔顺保持，不是纯摩擦夹持。
- **因果链：** latch 提供额外随手运动的支持 → 海绵持续留在指间 → 完成擦拭；移除后海绵离开夹爪 → 按压控制失败并提前结束。
- **边界：** 证明任务结论依赖辅助，不足以在无 latch 条件下唯一分离接触模型和 solver 贡献。

[擦拭对照](rss-wiping.md)

### 5. 旧夹布：为什么任务评分通过却仍穿桌？

- **现象：** 旧在线协议通过；独立检查发现 225 个保存帧中 176 帧有布料三角形内部穿过桌面，最大深度 3.00 mm。
- **第一失效层：O，评分覆盖不足；暴露的物理失败层是 G。** 顶点都在桌面上方并不保证三角形内部不穿过桌面。
- **因果链：** 只检查顶点 → 漏掉三角形—桌面相交 → 无效轨迹被记作通过 → 独立面片检查才恢复真实判定。
- **边界：** 修评分器不会修轨迹；新 9 s 单手候选通过也不替代旧双手折叠的应变、释放和终态失败。

### 6. Genesis PBD 布料：为什么重力补偿也夹不起来？

- **现象：** 夹爪抬升 79.988 mm，布料最低高度仍约 4 mm，两个 ±3 mm 位置对照也失败。
- **第一失效层：C，PBD—刚体接触保持／耦合不足。** 官方路径中名义摩擦 0.01 与 5 的轨迹相同，布片以约 0.2 m/s 滑动 60 mm；动量响应还呈现一个 2 ms 步延迟。
- **因果链：** 缺少可观察的切向保持 → 指面不能传递抬升所需摩擦 → 重力补偿只修夹爪自身高度 → 布料仍留在桌面；同一步动量账本因延迟拒绝。
- **边界：** 证据定位到该版本的 legacy PBD／刚体路径，不外推 Genesis 所有柔性配置。

### 7. LIBERO：为什么任务能成功，记录仍不可信？

- **现象：** 5 个零动作 settling 步之后，评测继续使用 settling 前 observation；末端位置已变化 4.481 mm，夹爪关节变化 12.143 mm。
- **第一失效层：O，观测生命周期。** 环境状态更新了，策略／评分输入没有刷新。
- **因果链：** reset observation → 额外 settling 改变状态 → observation 未重新获取 → 动作和诊断以过期状态开始。
- **修复边界：** 一行刷新恢复状态身份；尚未证明策略收益。把步长从 2 ms 改成 1 ms 后物理诊断反而从 5/10 降到 3/10且成本近翻倍，说明缩步不是替代归因。

[LIBERO 报告](libero-workflow.md)

### 8. 质量／尺寸迁移：为什么名义点调好后 0/30？

- **现象：** 三个冻结配置 × 十组质量／尺寸，原工程检查 1/30，瞬态目标 0/30，联合 0/30。
- **第一失效层：C，参数映射没有表达质量和面积依赖。** 候选直接复用名义点参数，未做质量／面积补偿。
- **因果链：** 名义点拟合 → 场景质量／尺寸改变 → 有效惯量、接触数或面积改变 → 同一原生参数不再对应同一合成 K/D 目标。
- **边界：** 否定的是这三套冻结映射的迁移能力，不是否定所有映射或引擎算法。

### 9. 接触瞬态与夹持蠕滑：为什么更多迭代／更小步长不够？

- **现象：** SuperDex 接触起始的摩擦工况在 1→0.125 ms 下相邻网格差异不单调；收紧停止容差 100/10,000 倍后差异仍约 3.206 mm。MuJoCo 临界夹持的冲量残差随容差下降，但蠕滑不消失。
- **第一失效层：C + N。** 数值停止误差确实影响残差，但接触定律／阻抗仍决定蠕滑和卸载行为。
- **因果链：** 收紧容差 → 数值闭合改善；若物理模型仍产生载荷相关阻尼、软接触或不完备保持 → 任务漂移继续存在。
- **边界：** 最细网格不是真值；没有拟合收敛阶，也没有实测材料参考。

### 10. 香蕉 64×：为什么 RMSE 大不能叫“不收敛”？

- **现象：** 细化工况 nRMSE 2.051，但 0.5 s 内粒子尚未触及砧板支撑。
- **第一失效层：O，比较没有到达同一相位。** 基准曲线已经经历支撑接触，细化曲线还处在不同阶段。
- **因果链：** 粒子细化改变到达时间／计算预算 → 固定时窗截到不同事件相位 → 直接曲线 RMSE 混合了相位差和力差。
- **下一门槛：** 先用接触事件对齐或延长到共同终止条件，再比较力—位移；当前不能声称收敛或不收敛。

[香蕉测力](banana-force.md)

### 11. AMP：为什么程序跑完仍判失败？

- **现象：** 两个 0.2 s 探针正常结束，但记录开关前后的状态一致性超限。
- **第一失效层：O，记录器资格。** 在证明记录无扰动前，录下的完整策略回合不能作为动力学证据。
- **因果链：** 启用记录 → 状态差异超过冻结阈值 → 记录路径未通过资格 → 停止后续三种子和无手接触负例。
- **边界：** 这是实验仪器失败，不是 AMP 抬箱策略失败；完整任务尚未执行。

[AMP 记录器报告](amp-lift.md)

### 12. RoboDojo v67：向下压为什么反而向上弹？

- **现象：** 三个 case 的目标均为 `z=0.924 m`；动作后的 TCP 却到达 `1.049–1.258 m`，相对动作前上升 10.6–28.3 cm，并伴随 13.0–47.8 cm 三维目标误差。
- **第一失效层：P，槽口卡滞后仍执行深位置目标。** `s1/l026` 与 `s1/l049` 在逃逸前已停在目标上方 19/28 mm；`s0/l025` 的卡滞和逃逸发生在同一 `seat` 动作内。运输阶段没有先脱落。
- **因果链：** 插入位姿／净空不足 → 面包／手指／槽沿形成高约束多点接触 → 高刚度位置驱动继续做功 → 观测关节状态在 40–44 ms 内向侧上方逃逸 → 夹持释放或撤离／IK 失败 → 槽占用无法确认、任务终止。
- **证据证明：** `final_xyz` 来自每步观测关节角的 FK，不是规划器回退；被冻结源码同时存在 4400 刚度、0 次速度迭代、关闭 stabilization 和错误的面包摩擦字段映射等风险放大器。
- **证据未证明：** 本批没有逐步驱动力矩、接触冲量、穿透和运行时材质 pair；执行器本身是能量源，不能从端点位姿直接推出“被动 solver 凭空注入全部能量”。异常的 A/C/N 内部分摊仍是 U。
- **下一门槛：** 先在第一次卡滞时退出 20–30 mm；冻结三例逐项 A/B 速度／位置迭代、stabilization、去穿透速度与步长，并用 4 ms 的 `Στ·Δq`、接触冲量和 `Δ(K+U)` 闭合能量账本。

[三个腕部 GIF、逐例时间线与修复顺序](robodojo-bread-slip.md) · <a href="_static/robodojo-bread-slip/contact-escape-v67.json">机器可读证据</a>

## 六引擎斜面：为什么不强行给一个根因？

斜面队列是“逐配置诊断”，不是一个共享根因实验：MuJoCo 有摩擦锥／阻抗和数值一致性拒绝；SuperDex 的 0.5 ms 静漂与 CG 停止残差并存；Genesis 同时涉及接触表达、名义零摩擦下限和停止精度；Newton 大量正例先被 FP32 数值门禁拒绝；PhysX PGS/TGS 的部分微小残差尚未唯一解释；Drake 的 lagged 摩擦能重构额外切向支持，但仍有小冲量残差。这里最诚实的分类是 **C/N/U**，每个后端只在自己的协议内下结论。

如果没有同一材料目标、等效接触表示、统一观测和共同数值门禁，把通过数相加只会把“模型不同、记录无效和任务失败”混成一个假排名。

## 没有真机实验，物理正确如何被证明？

答案不是“仿真看起来真实”，而是把能独立检验的部分拆开：

1. **实现一致：** 配置是否真正送达，记录是否对应实际运行状态。
2. **数学自洽：** 单位、初态、力—位移、动量、角动量和能量账本是否闭合。
3. **数值可靠：** 固定模型后改变步长、容差、精度和预算，记录敏感性而不是宣称“越细越真实”。
4. **物理边界：** 法向支撑、摩擦锥、接触力矩、非穿透、耦合与释放是否符合当前模型假设。
5. **评分有效：** 正例、负例、idle、无接触、零摩擦、隐藏支撑和错误 reset 是否被正确拒绝。
6. **外部有效性：** 只有真实传感器、执行器、材料和任务测量才能评价对应的 reality gap。

前五层可以通过仿真、解析参考和反例审计；第六层不能由前五层替代。当前 DexLab 已完成前五层中的多项有限检查，真机实验数仍是 **0**，因此不能报告真实材料误差、硬件时延误差或已经完成的 sim-to-real transfer。

## 每次判断都按这个顺序查

1. **冻结结果定义。** 任务成功、物理有效、数值有效、记录有效分别判定。
2. **找最早变化。** 从命令、执行器、相对位姿、几何余量、接触数／冲量、外部碰撞、残差到任务结果按时间排序。
3. **先做守恒和预算。** 重量由谁支撑？所需力矩方向是否存在？外力、冲量和动量是否闭合？
4. **只改一个变量。** 抓取深度、力限额、latch、碰撞网格、接触模型、步长或容差一次只改一项。
5. **保留正负对照。** open/no-contact/zero-friction、无地面、无推动、无辅助和重复记录都要留下。
6. **运行时读回。** 不用配置文件代替最终材质 pair、combine mode、solver、精度和碰撞形状。
7. **证据不足就停在 U。** 缺切向冲量、材料实测或原生网格时，写清下一门槛，不把候选机制包装成根因。

[旧版 solver 失败复盘](solver-failure-audit.md)保留逐引擎和历史证据；本文把它们重新组织为 Sim-to-Real Gap 的逐层判断。两者都不构成真实材料标定、真机验证或通用引擎排名。

## 参考文献

1. <a id="ref-reality-gap"></a>Elie Aljalbout et al. [The Reality Gap in Robotics: Challenges, Solutions, and Best Practices](https://arxiv.org/abs/2510.20808). arXiv:2510.20808, 2025.
2. <a id="ref-mujoco-paper"></a>Emanuel Todorov, Tom Erez, and Yuval Tassa. [MuJoCo: A physics engine for model-based control](https://doi.org/10.1109/IROS.2012.6386109). IROS, 2012.
3. <a id="ref-mujoco-docs"></a>Google DeepMind. [MuJoCo documentation](https://mujoco.readthedocs.io/). Current official engine and contact documentation.
4. <a id="ref-genesis"></a>Genesis Authors. [Genesis: A Generative and Universal Physics Engine for Robotics and Beyond](https://genesis-world.readthedocs.io/en/latest/). Official documentation and citation.
5. <a id="ref-newton"></a>The Newton Developers. [Newton Physics documentation](https://newton-physics.github.io/newton/). Solver, contact and versioned API documentation.
6. <a id="ref-physx"></a>NVIDIA. [PhysX SDK](https://github.com/NVIDIA-Omniverse/PhysX). Official source and release documentation.
7. <a id="ref-drake"></a>Russ Tedrake and the Drake Development Team. [Drake: Model-Based Design and Verification for Robotics](https://drake.mit.edu/), 2019.
8. <a id="ref-libero"></a>Bo Liu et al. [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](https://arxiv.org/abs/2306.03310). arXiv:2306.03310, 2023.
9. <a id="ref-robodojo"></a>Chen et al. [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](https://arxiv.org/abs/2607.04434). arXiv:2607.04434, 2026.
10. <a id="ref-robosimstudio"></a>RoboSimStudio Authors. [RoboSimStudio: An Interactive Toolkit for Rapid Real2Sim of Robot Manipulation Tasks](https://arxiv.org/abs/2610.18835). arXiv:2610.18835, 2026.
11. <a id="ref-superdex"></a>Meta Research. [SuperDex](https://github.com/facebookresearch/project_superdex). Official repository and versioned implementation.

### 项目引用

```bibtex
@software{dexlab2026,
  author  = {Kiki Huang},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```
