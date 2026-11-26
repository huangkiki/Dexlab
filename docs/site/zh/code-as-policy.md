# Code as Policy：从“模型写代码”到可验证的机器人技能

> **一页速览**
>
> | 维度 | 内容 |
> | --- | --- |
> | **涉及工作** | ① [Code as Policies (arXiv:2209.07753)](https://arxiv.org/abs/2209.07753)（路线源头）<br>② [CaP-X (arXiv:2603.22435v2)](https://arxiv.org/abs/2603.22435v2) · [COAP (arXiv:2610.12369v1)](https://arxiv.org/abs/2610.12369v1) · [ASPIRE (arXiv:2607.00272v2)](https://arxiv.org/abs/2607.00272v2)<br>③ [GR00T 2 白皮书 (2026-11)](https://research.nvidia.com/labs/gear/gr00t-2) + 反例对照 [SuperMimic-manipulation](https://github.com/emoPointer/supermimic_manipulation) |
> | **固定源码** | [`capgym/cap-x@53e9966d`](https://github.com/capgym/cap-x/tree/53e9966d7a8e2fa7494676772bccc35280f5c0ed)（MIT） · [`NVlabs/ASPIRE@fa00f0ef`](https://github.com/NVlabs/ASPIRE/tree/fa00f0ef2bc1d91d594b9aa502c22133c9f538f7)（Apache-2.0） · `Isaac-GR00T` 非默认分支 `codex/n2-action-expert@7e492ad1`（评估许可） · [`supermimic_manipulation@eda7da48`](https://github.com/emoPointer/supermimic_manipulation/tree/eda7da480c6d92a68cc41c9628b7efdae08cae23) · COAP 暂无公开仓库 |
> | **核心问题** | 端到端 VLA 在长时任务编排、异常恢复与失败归因上不透明；而把机器人策略直接写成代码时，模型能力、API 抽象脚手架、执行反馈模态、技能晋升与物理接触控制常常混作一团，无法判断究竟是哪一层起作用。 |
> | **核心做法** | 把任务语义、状态变量、感知反馈与恢复逻辑写成可审计的程序或技能卡：CaP-X 拆解抽象层与反馈变量；COAP 冻结在线显式状态机、离线改代码；ASPIRE 用逐原语 trace 与独立验证者晋升技能卡；GR00T 2 将 System-2 Agent、CaP 恢复与 WAM 接触操作通过单控制者分层解耦。 |
> | **开源现状** | CaP-X 与 ASPIRE 完整开源；COAP 未见公开代码；GR00T 2 默认仓库仍为 N1.7（公开 N2 分支为评估许可证且 base checkpoint 私有）。 |
> | **对 DexLab 判决** | **`experiment`（采纳反馈视图消融、单控制者恢复合同与独立验证者 skill card，不以 Code Agent 替代物理引擎或评分器）** — 先验证细粒度执行证据能否改善已有失败链归因，再讨论技能晋升或局部控制器对照。 |

---

## 一、这条路线与四项代表工作具体做了什么？

**Code as Policy（CaP）首先不是“又一个 VLA 模型”，而是一种显式控制表示：把任务阶段、条件分支、感知测量与失败恢复写成可检查、可修改的程序。**（注意简称区分：本文 `CaP = Code-as-Policy`，与 [Discussion #309](https://github.com/huangkiki/Dexlab/discussions/309) 中的 `CAP = Contact-Anchored Policy` 不是同一路线。）

### 1. 问题设定、输入输出与四层执行栈

以“夹起面包片、抬升、放入盘子”为例，程序依次调用 `localize_object` → `select_grasp` → `move_to_pose` → `close_gripper` → `verify_hold` → `open_gripper`。相比端到端策略，代码路线的输入通常是**语言目标 + 结构化感知/状态 API + 执行反馈 trace**，输出是**可执行任务程序、技能卡或受限工具调用序列**；但它同时把可靠性拆成四个必须分清所有权的层次：

(execution-stack)=
| 层 | 它回答的问题 | 典型内容 | 时标特征与不应混为 |
| --- | --- | --- | --- |
| **任务层（System 2）** | 下一步做什么、何时重试或停止 | 语言目标、阶段状态、成功谓词、恢复决策 | 外环秒级（CaP-X 迭代 `6.8–23.8 s`；GR00T 2 Agent 中位 `7.5 s`）；不能直接替代高频控制 |
| **程序层（CaP）** | 如何组合感知、条件分支与恢复动作 | Python 状态机、循环、异常分支、白名单原语调用 | COAP 冻结程序 CPU 中位 `0.3 ms`；但返回 `True` 不等于物理成功 |
| **技能 / 策略层** | 单个定位、抓取或接触操作如何实现 | 抓取生成、IK/规划器、VLA/WAM 动作块（`73–167 ms`）或局部接触控制器 | 不应把可执行的 task program 与自然语言 task skill 混为一谈 |
| **执行与评分层** | 命令如何变成关节/接触响应、谁判成败 | 仿真器/真机控制器、原生接触读回、独立 scorer | 程序与 Agent 绝不应直接读取 reward 或改写成功谓词 |

### 2. 四类系统全景与核心机制拆解

近年来这一方向分化出四种形态迥异的系统，切忌混称为同一种“AI 写代码控制机器人”：

(policy-map)=
| 工作 | 运行时谁做决策 | 核心产物与机制 | 解决的核心瓶颈 | 关键证据边界 |
| --- | --- | --- | --- | --- |
| **[CaP-X](https://arxiv.org/abs/2603.22435v2)** | Coding model 单轮/多轮生成程序 | 基准 + 抽象层级/反馈模态/并行采样对照框架 | 剥离“模型能力”与“人工高层 API 脚手架” | 论文 v2 写 187 任务，源码 README 为 39 任务；技能库仅从成功样本编译、缺独立验证者 |
| **[COAP](https://arxiv.org/abs/2610.12369v1)** | **在线零模型**（固定代码状态机）；Agent 仅离线改代码 | 3 类显式状态 + 5 层共享库 + worktree diff 变更门禁 | 让状态、任务逻辑与代码演进完全可审计、确定性运行 | 全部为 RoboDojo 仿真，依赖 benchmark 常量；截至核查日未见作者公开代码 |
| **[ASPIRE](https://arxiv.org/abs/2607.00272v2)** | Coding agent 在线调试、诊断与修复 | 逐原语 trace 引擎 + 独立验证者晋升技能库 + K 路进化搜索 | 防止把单次偶然成功污染成共享技能 | 固定白名单 API 决定上限；验证通过只证知识可传递、不证跨任务泛化；调用成本高 |
| **[GR00T 2](https://research.nvidia.com/labs/gear/gr00t-2)** | System-2 Agent 编排；CaP 恢复；2B WAM 执行接触 | MCP 工具服务 + 单 control worker + 联合视频-动作 DiT | 把长任务阶段/掉落恢复与精细接触操作解耦 | 97%–98% 依赖 DAgger/RL/恢复技能组合；默认仓库仍为 N1.7，N2 分支为评估许可 |
| *[HexaShell](https://arxiv.org/abs/2610.23479) / [Auriga](https://arxiv.org/abs/2611.01112)* | 通用 VLM 在 harness 中逐轮写短代码/调工具 | 通用工具、沙箱、回读 + 约 39–61 行 Markdown **task skill** | 降低跨任务工程适配 | harness 本身贡献大量成功率；task skill 是文本说明书，不是冻结代码程序 |

下面把四项核心工作的具体机制拆开：

1. **CaP-X — 把抽象层级与视觉反馈变成受控实验（§3、`cap-x@53e9966d`）**：系统拆开 4 个变量：（1）**抽象层级**（高层宏 vs 定位/抓取/IK 低层原语）；（2）**时间交互**（单轮开环 vs 多轮读报错改代码）；（3）**感知接地**（纯文本日志 vs 直接交错原始 RGB 图 vs 先把前后帧转成“物体是否移动、夹爪是否接触”的**结构化视觉差分文字**）；（4）**测试时计算**（多轮、技能合成与 9 路单模型 / 3×3 多模型并行采样）。一个反直觉发现是：**直接把原始 RGB 图塞给 coding model 往往不如纯执行文本，而把前后帧先转成结构化视觉差分再交回代码模型则显著提升**——说明反馈并非越多越好，必须与代码决策空间对齐。

![CaP-X 高低层 API 抽象对比](https://arxiv.org/html/2603.22435v1/high_vs_low.png)

*图 1（[CaP-X Figure 2](https://arxiv.org/html/2603.22435v1#S3.F2)）：高层封装掩盖了大量任务先验，拆到底层感知/规划/控制原语后模型成功率明显分化，凸显评测必须固定并登记 API 抽象层级。*

2. **COAP — 离线改代码、在线冻结显式状态机（§3、`2610.12369v1`）**：COAP 明确与在线调大模型的 Agent Harness 划清界限。在线输入仅三路 RGB、语言、关节角、末端位姿与夹爪回显，代码显式维护**环境状态**（物体位姿/尺寸/关系及误差、来源、时间）、**机器人状态**与**任务状态**（阶段、手—物分配、跨遮挡记忆），并按 `运动 → 感知 → 操作原语 → 对象族 → 任务程序` 五层组织。coding agent 只在离线读失败记录、于独立 worktree 提交完整 diff，通过兼容性与默认关闭保护并在验证布局上超过重跑噪声边际后才合并。
3. **ASPIRE — 逐原语 trace 与独立验证者晋升门禁（§3、`ASPIRE@fa00f0ef`）**：执行引擎记录每次原语调用的输入输出、关键帧、mask overlay、抓取候选与规划状态，并将被测代码隔离在白名单内（禁止读取 reward、success 或特权状态）。新修复先以 proposal 独立存放，交由**看不到提出者代码的 fresh verifier** 在同任务 **5 个开发 seed、最多 2 次尝试内达到 ≥4/5 成功**才晋升为 `verified`，且后续任务逐条标记 `useful / misleading / wrong / not-applicable`。当单轨迹修复陷入平台期时，再开启 K 候选进化搜索并在冻结 held-out 集评测。

![ASPIRE 执行引擎、技能晋升与进化搜索系统架构](https://arxiv.org/html/2607.00272v1/system_design.png)

*图 2（[ASPIRE Figure 1](https://arxiv.org/html/2607.00272v1#S2.F1)）：ASPIRE 将逐原语执行追踪、独立验证者技能库晋升与多候选进化搜索连成闭环，并强制隔离开发 seed 与留出 seed。*

4. **GR00T 2 — Agent + CaP + WAM 三层分工与 SuperMimic 局部反例**：GR00T 2 用冻结 Wan VAE + Cosmos-Reason1 + 2B Cosmos-Predict2.5 DiT 联合去噪多视角未来视频与 48 步动作块（支持 joint video-action 或 disjoint action-only 推理），专攻难以脚本化的接触操作；System-2 Agent 通过 MCP 调用 `wam_act`/`stop_wam`、`localize_object`（SAM 3）和 `move_to_pose`（cuRobo）做阶段调度与掉落恢复，并由**单一 control worker 串行化命令**避免双源抢控。但社区独立适配 **[SuperMimic-manipulation](https://github.com/emoPointer/supermimic_manipulation)** 提供了关键反例：在已知任务、固定工作台与低维全状态的 mjlab 仿真中，单任务可微世界模型控制无需视觉大模型即可完成螺母套柱（`95.0%`）与抽屉放胶囊（`90.2%`，各 256 held-out resets）——说明 WAM 的真正不可替代处在于**开放视觉、语言、多任务与跨本体**，而非“只有大 WAM 能完成局部接触”。

### 3. 主实验设置、结果汇总与自带反例

| 工作与基准 | 条件与分母 | 核心结果（作者报告） | 这组结果实际证明了什么 / 关键反例 |
| --- | --- | --- | --- |
| **CaP-X**（7 核心任务，12 模型） | 100 trials/tier；对照抽象层、多轮、视觉差分与 9 路并行 | 撤掉高层宏后成功率显著下滑；多轮 + 结构化视觉差分 + 并行采样大幅拉回 | **API 脚手架与反馈格式会主导分数**；单报“某模型成功率高”无法区分模型与接口贡献 |
| **COAP**（RoboDojo 42 双臂任务） | 仿真 RGB + 本体 + 语言，在线无模型 | COAP **`70.24%`** vs 最强 WAM `29.64%` / VLA `27.96%`；Memory **`90%`** vs Harness `47%`；在线 CPU 中位 **`0.3 ms`** | 显式状态与测量在仿真长时/精度任务优势显著；但全部在仿真，且 62% 失败仍在感知/接触层 |
| **ASPIRE**（LIBERO-Pro，Opus 4.6） | 零样本 → 逐原语 trace + 技能库 → +进化搜索 | 平均成功率 **`14% → 62% → 72%`**（特定全配置最高可达 99%） | **最大跳升来自执行引擎 trace 与技能循环（+48 pp）**，进化搜索排第二（+10 pp）且成本陡增 |
| **GR00T 2 Agent+CaP**（真机装配 & 插接） | 3 类随机倒料装配各 100 次；5 连续插接各 20 次 | 装配 SFT+DAgger `84/71/78` → +Agent+CaP **`98/97/97`**；连续插接 SFT+RL+Agent **`19/20`（网线）、`20/20`（充电器）** | 系统分工显著拉高长任务可靠性；**反例：无 RL 仿真中 S2 干预仅 `24%`（RoboDojo 188/773）与 `56%`（RoboCasa 553/988）成功** |
| **SuperMimic-manipulation**（ARX5 mjlab） | 256 held-out resets，每任务单训（A100 3.4–10.5 h） | `square` **`95.0%`**、`drawer` **`90.2%`**；但 `drawer` 另一种子仅 `75.9%`（checkpoint 波动 `24–90%`） | 已知全状态仿真中专用控制器可胜任局部接触；但无视觉/语言/跨本体/真机能力 |

---

## 二、哪些隐藏前提与反例可能改变判断？

1. **`S2 intervenes ≠ S2 rescues`，且视觉成功检查本身会漏判**：GR00T 2 报告的 300 次 Agent 装配中有 3 次失败是**螺丝只旋进一半却被 GR00T 2 与 Agent 双双判成完成**；仿真失败人工归类中，38%–39% 是恢复动作比运动规划工具更精细，24%–38% 进入不可恢复或超时状态；YAM 清桌中机器人有 38% 时间在干等 Agent（中位 7.5 s/轮）。
2. **抽象泄漏与技能污染**：高层 `pick()` 返回成功常掩盖浅夹持或滑移；CaP-X 固定源码 `53e9966d` 的技能编译只筛选成功 trial，若评分器存在漏洞，错误策略会被自动固化成共享函数；即使通过 ASPIRE 的 5-seed 验证，源码也明确写道它只证明“修复知识能传递给新验证者”，不证明跨任务泛化，且入库后缺乏持续复验。
3. **跨论文总分不可直接横比**：COAP 在 RoboDojo 的 `70.24%`、HexaShell 的 `85.0%` 与 GR00T 2 在 layout bank 0 的 `75.8%` 使用不同的布局集合、观测常量、尝试预算与默认执行器选择，绝不能拼成一张跨论文排行榜。

(cap-evaluation)=
### 评测 Code as Policy 时的 7 项最低登记清单

任何可信对比至少必须同步登记：（1）可用原语的抽象层级及是否给示例；（2）单轮/多轮次数、反馈模态与 token/调用预算；（3）工具返回值是否包含实际到达、接触、错误码与关键帧；（4）开发 seed、未见检查 seed 与冻结 held-out seed 的隔离边界；（5）程序、模型、harness、控制器、仿真器与评分器版本号；（6）无效运行、超时、接口报错与物理失败是否全部计入同一分母；（7）被测程序或 Agent 能否读取 reward、success、原生特权状态或未来状态。

---

## 三、对 DexLab 的借鉴判断与最小验证切片

(dexlab-policy)=
对 DexLab 而言，Code as Policy 最有价值的落点是**把失败归因、控制权切换与诊断知识沉淀做成可审计的工程实验**，而不是用代码 Agent 替代物理引擎或评分器。

- **直接借鉴**：
  1. **四层唯一所有权 + 单控制者合同**：任务层（阶段与恢复选择）、程序层（白名单原语）、执行层（仿真/控制器读回）与独立评分层彻底分离；任何执行者切换前先停止旧控制源并记录 `command_owner`、`recovery_attempted`、`recovery_succeeded`、`stage_resumed` 与 `full_task_succeeded`；严禁程序/Agent 读取 reward 或 success。
  2. **先做反馈视图消融，再谈 Agent 编排**：把已有失败记录组织成不同粒度的观察包，验证到底哪一层证据能把竞争物理假设分开。
  3. **带触发前提与晋升状态的 skill card**：把失败根因沉淀为 `失败签名 → 触发前提 → 修复动作 → 适用边界 → 支持证据 → 反例`，严格区分 `verified_once`、`transferred` 与 `refuted`。
- **需适配验证**：
  - 在已知全状态仿真接触任务上，将 SuperMimic 风格的 task-specific 局部接触控制器与同环境 PPO、固定脚本、通用 WAM 放在**同一观测权限与同一独立 scorer** 下对照，明确通用模型与专用控制器的性价比边界。
- **暂不采用**：
  - 不搭建多 Agent 平台、自动任务课程或默认开启 9 路并行/进化搜索；
  - 不让自然语言 `task skill` 与可执行 `task program` 共用一个模糊标签；
  - 不把作者在 RoboDojo / LIBERO-Pro / 真机上的组合成功率当作 DexLab 可默认达到的基线。

### 第一步最小可证伪验证切片

- **验证问题**：在 DexLab 已公开的 [烤面包滑落失败记录](robodojo-bread-slip.md) 上，冻结物理与独立评分，仅改变反馈视图与控制权合同，是否能显著提升**首次失效层归因**的准确率与可复算性？
- **固定条件与对照**：
  1. **反馈消融（源自 CaP-X / COAP）**：对同一批冻结失败轨迹分别提供视图 `A`（任务阶段、终态谓词、前后图或结构化视觉差分）与视图 `B`（在 `A` 基础上加入逐原语请求/实际到达、接触建立/丢失、法向冲量与首次滑移时间），由独立诊断者分别写出首次失效链；
  2. **单控制者与技能卡晋升（源自 GR00T 2 / ASPIRE）**：先跑固定脚本基线，再对比受限 Agent（只读结构化状态、只能调用白名单恢复原语、禁读 reward/success）；若产出修复，交由不看原代码的 fresh verifier 在 5 个开发 seed（最多 2 次尝试）上验证并独立报告留出 seed。
- **通过与停止标准**：最低门槛是“能准确指向现有测量真正支持的第一失效层、区分竞争解释、保持失败/超时分母与旧评分不变”。若更细 trace 不改善归因、或固定脚本已能完成同等恢复，则直接止损，不扩展 Agent 或技能库。

---

## 四、可核查来源与证据范围

- 论文与白皮书：[Code as Policies (arXiv:2209.07753)](https://arxiv.org/abs/2209.07753) · [CaP-X (arXiv:2603.22435v2)](https://arxiv.org/abs/2603.22435v2) · [COAP (arXiv:2610.12369v1)](https://arxiv.org/abs/2610.12369v1) · [ASPIRE (arXiv:2607.00272v2)](https://arxiv.org/abs/2607.00272v2) · [HexaShell (arXiv:2610.23479)](https://arxiv.org/abs/2610.23479) · [Auriga (arXiv:2611.01112)](https://arxiv.org/abs/2611.01112) · [GR00T 2 白皮书](https://research.nvidia.com/labs/gear/gr00t-2/assets/gr00t2_whitepaper.pdf)
- 固定源码：[`capgym/cap-x@53e9966d`](https://github.com/capgym/cap-x/tree/53e9966d7a8e2fa7494676772bccc35280f5c0ed) · [`NVlabs/ASPIRE@fa00f0ef`](https://github.com/NVlabs/ASPIRE/tree/fa00f0ef2bc1d91d594b9aa502c22133c9f538f7) · `Isaac-GR00T` `codex/n2-action-expert@7e492ad1` · [`emoPointer/supermimic_manipulation@eda7da48`](https://github.com/emoPointer/supermimic_manipulation/tree/eda7da480c6d92a68cc41c9628b7efdae08cae23)
- 相关讨论与站内延伸：[COAP #335](https://github.com/huangkiki/Dexlab/discussions/335) · [CaP-X #341](https://github.com/huangkiki/Dexlab/discussions/341) · [ASPIRE #342](https://github.com/huangkiki/Dexlab/discussions/342) · [GR00T 2 #419](https://github.com/huangkiki/Dexlab/discussions/419) · [面包滑落证据](robodojo-bread-slip.md) · [模型评测协议](model-evaluation.md) · [灵巧操作仿真导读](dexterous-hand-simulation.md)
- **核查范围（2026-11-26）**：综合自各论文/白皮书原文及固定提交的静态源码核查。全部成功率、延迟与恢复占比均为作者报告；COAP 未见公开代码库，GR00T 2 官方正式开源代码标为 2026-12（非默认 N2 分支受评估许可证约束且基座权重私有）；本轮未运行外部 Agent、外部 benchmark 或 DexLab 新增物理实验。
