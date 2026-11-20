# Code as Policy：从“模型写代码”到可验证的机器人技能

## TL;DR

**Code as Policy 不应该被当成“又一个 VLA 模型”，它首先是一种控制表示：把任务语义、反馈条件和动作顺序写成可检查、可修改的程序。**

以“夹起面包、抬升、放进盘子”为例，程序可能依次调用定位、抓取生成、运动规划、闭爪、持物检查和释放。真正决定系统是否可靠的，不只是大模型会不会写 Python，而是感知值从哪里来、闭爪命令和实际夹持是否一致、接触何时丢失、机器人执行到了哪一步，以及独立评分器依据什么判定成功。

这条路线值得一个独立专题，因为现在已经出现至少四种容易混淆的形态：

- 大模型在运行时生成程序，如 CaP-X、ASPIRE；
- 程序在线冻结、模型只离线改代码，如 COAP；
- 通用 Agent harness 提供工具、测量和安全准入，如 HexaShell、Auriga；
- 任务知识写成约一页 Markdown 的 task skill，而不是运行时执行的策略代码。

**DexLab 的落点应是“用 Code as Policy 研究失败归因和技能记忆”，不是用一个代码 Agent 替代物理引擎或完整评测协议。** 先让一条已有失败记录拥有可审计的反馈链，再讨论技能晋升和自动进化。

## 1. 从一次面包滑落开始

下面只是教学伪代码，不是某个论文或 DexLab 已实现的 API：

```python
bread = localize_object("bread slice")
grasp = select_grasp(bread, strategy="top_down")
move_to_pose(grasp.approach_pose)
close_gripper()

if not verify_hold("bread slice", min_lift_m=0.02):
    raise TaskFailure("grasp_not_established")

move_to_pose(plate.approach_pose)
open_gripper()
```

这段程序看起来比端到端策略更容易审计，因为它明确写出了任务分解。但它同时引入了多个新的失效位置：

- `localize_object` 可能把邻片或货架边缘当成目标；
- `select_grasp` 可能选择上缘浅夹持；
- `move_to_pose` 的规划成功不代表实际到达；
- `close_gripper` 返回成功不等于接触能够承载重力；
- `verify_hold` 可能使用过期视觉、错误阈值或漏掉旋转；
- 最终评分器可能把“到达盘子上方”当成“放入盘中”。

所以 Code as Policy 的价值不是“写成代码，因此更可靠”，而是**把可靠性拆成可以被逐层验证的命题**。没有 trace、状态和独立评分时，代码只会把失败包装得更像一段合理的逻辑。

(execution-stack)=
## 2. 程序不是一个孤立的层

| 层 | 它回答的问题 | 典型内容 | 不应混为 |
| --- | --- | --- | --- |
| 任务层 | 要完成什么，何时停止或恢复 | 语言目标、阶段、成功谓词、重试预算 | 可直接执行的控制逻辑 |
| 程序层 | 如何组合感知与动作来实现目标 | 条件判断、循环、函数、错误分支 | 底层伺服和物理真值 |
| 技能层 | 哪些测量、抓取或运动能力可复用 | 定位、抓取生成、IK、轨迹执行、工具 API | 整任务技能文档 |
| 执行层 | 命令怎样变成关节、接触与物体响应 | 控制器、规划器、仿真/真机、时钟 | 任务成败 |

任务代码通常运行在“外环”：看到较大的状态变化后再决定下一步。接触夹持、滑移和释放可能需要毫秒级内环控制。CaP-X 作者报告的一次程序迭代约 `6.8–23.8 s`，而 VLA 的 action chunk 或单动作推理在报告条件下约 `73–167 ms`；这组数字不是公平性能排名，但足以说明 Code as Policy 更适合作为 system-2 任务层，而不是默认替代高频接触控制器。

(policy-map)=
## 3. 四类系统，不要叫成同一个东西

| 工作 | 运行时谁做任务决策 | 主要产物 | 解决的问题 | 关键边界 |
| --- | --- | --- | --- | --- |
| [Code as Policies](https://arxiv.org/abs/2209.07753) | LLM 根据语言和 API 生成程序 | 可执行 policy code | 把语言指令变成组合感知、几何与控制 API 的程序 | 依赖人工设计的 primitive 和 few-shot 示例 |
| [CaP-X](https://arxiv.org/abs/2603.22435) | coding model 在单轮或多轮中生成程序 | 基准、程序、执行反馈、技能库与 RL 接口 | 系统比较抽象层级、交互、视觉 grounding 和测试时计算 | 模型分数同时受 API scaffold、反馈和预算影响 |
| [COAP](https://arxiv.org/abs/2610.12369) | 在线运行固定代码；coding agent 离线修改 | 显式状态 + 任务程序 + 共享代码库 | 让状态、任务逻辑和代码改动可审计 | 全部结果为仿真；仍未证明跨本体/真实材料 |
| [ASPIRE](https://arxiv.org/abs/2607.00272) | coding agent 在线执行、诊断和修复 | 逐原语 trace + 可复用技能库 | 把失败修复持续沉淀并迁移到新任务 | 固定 API、前沿模型依赖、验证一次不等于泛化 |
| [HexaShell](https://arxiv.org/abs/2610.23479) / [Auriga](https://arxiv.org/abs/2611.01112) | 通用模型在 harness 中直接调工具或写短程序 | 通用工具、测量、准入与可选 task skill | 降低每个机器人/benchmark 的适配和任务专用代码 | harness 本身也贡献成功率，不能全归给基础模型 |
| [GR00T 2](https://research.nvidia.com/labs/gear/gr00t-2) | Agent 选择阶段并检查执行；WAM 做接触操作；CaP 做可脚本化修复 | 任务程序、MCP 工具、CaP 原语、WAM API | 把长任务编排、局部恢复和接触丰富操作分开 | 依赖纠错数据、RL、可靠成功检查与足够精确的恢复原语 |

这里最重要的区分不是“有没有 Python”，而是**运行时是否仍有模型、经验到底保存在代码、文本还是权重中、谁拥有安全与成功判定**。

### CaP 不是 VLA

两者都可以把视觉和语言映射为动作，但机制不同：

- VLA 通常从示范学习一个从观测到动作或动作块的策略；
- Code as Policy 让模型生成显式程序，再由规划器、控制器和机器人 API 执行；
- 代码路线更容易替换 API、插入条件分支和追踪中间量；
- VLA 更接近连续动作生成，但推理可解释性和任务逻辑定位通常更难。

二者也不是互斥关系。最现实的系统常把 Code as Policy 放在任务层，把 VLA、阻抗控制或专用控制器放在局部接触层。

### GR00T 2：Agent、CaP 与接触策略各管一段

GR00T 2 给出了一个很清楚的系统分工：**Agent 决定“做什么”，CaP 执行可编程的搬取和恢复，World-Action Model 执行难脚本化的接触丰富操作。** 三者通过 MCP 工具服务器连接，并由一个 control worker 串行化命令，避免策略和程序同时抢机器人控制权。

以随机倒料的小车装配为例：零件掉落时，Agent 检测到阶段没有前进，调用 `localize_object`、`move_to_pose` 和 `set_gripper` 重新抓取；随后把轮子对准、旋紧等需要精细接触的步骤交还给 GR00T 2。这不是“Agent 学会了装配”，而是 Agent 修复了一个可观测的局部状态，再让专门的接触策略继续工作。

论文报告三类装配从 SFT+DAgger 的 `84/71/78` 次成功提高到 Agent+CaP 的 `98/97/97`；五次连续插接在 SFT+RL+Agent 下达到 `19/20`（网线）和 `20/20`（充电器）。这些结果同时包含纠错数据、RL、任务程序、重试和成功验证，不能归因给 Agent 或 CaP 单独一项。

更重要的限制来自失败本身：在 300 次 Agent 装配里，3 次失败是螺丝只旋进一部分，GR00T 2 和 Agent 都把细微视觉差异判成完成；无 RL 的仿真中，S2 干预后也只有 `24%`（RoboDojo）和 `56%`（RoboCasa365）成功。Agent 能调用恢复程序，不代表它拥有正确的物理测量，更不代表每次恢复都有效。

这里应使用 **CaP = Code-as-Policy**。它与 [Contact-Anchored Policy（CAP）](https://github.com/huangkiki/Dexlab/discussions/309) 无关：后者用三维接触锚点消除“在哪里交互”的歧义，前者用程序组合定位、运动、夹爪和验证。GR00T 2 的完整分析见 [Discussion #419](https://github.com/huangkiki/Dexlab/discussions/419)；#419 的候选只进入 Triage，不构成实验授权。

### Task skill 不是 task program

task program 是可执行策略；task skill 是运行时模型读取的说明，例如完成条件、已验证参数、常见失败和预算。HexaShell 的 task skill 约一页文本，不是一段被固定执行的任务程序。把二者都叫“技能”会让“哪些知识真的进入了运行时决策”变得不可审计。

## 4. 为什么它有效，以及在哪里失效

### 有效机制

1. **组合性。** 同一组定位、抓取、规划和运动 API 可以按任务重新组合，不必为每个长尾指令收集完整遥操作数据。
2. **可审计性。** 每个中间测量和分支都能留下值、来源、时间和误差；失败可以落到具体 API 或状态转换。
3. **持续修改。** 失败 trace 可以转成程序 diff、约束说明或可复用 helper，而不必每次重新训练权重。
4. **反馈闭环。** 多轮执行、结构化视觉差分和 per-primitive trace 可以让模型从异常中恢复。

### 主要失效

- **抽象泄漏。** 高层 `pick()` 可能隐藏定位、抓取和持物失败；模型分数会错误归因给理解能力。
- **反馈错配。** 原图、成功标志、文本日志和接触冲量回答不同问题；反馈越多不等于诊断越好。
- **系统层级混淆。** 模型、harness、控制器、仿真器和评分器共同决定结果，不能只报一个端到端分数。
- **安全与供应链边界。** 执行模型生成的代码需要白名单工具、隔离环境和人工扩展 API；进程 watchdog 不是安全沙箱。
- **技能污染。** 从成功样本直接抽函数会固化偶然成功或评分漏洞；一次修复也不能自动晋升为通用技能。
- **成本与时延。** 多轮推理、并行候选、验证者和 evolution search 都消耗模型调用与物理 rollout。

(cap-evaluation)=
## 5. 评测 Code as Policy 时至少要记什么

CaP-X 给出的最有价值提醒，是不要把“模型能力”与“人工提供的接口脚手架”混在一起。一次可信比较至少应登记：

- 可用 primitive 的抽象层级，以及是否提供用法示例；
- 单轮/多轮次数、每次反馈的模态和 token/调用预算；
- 工具返回是否包含实际到达、接触、错误码和关键帧；
- 开发 seed、未参与调参的未见 seed 和最终 held-out seed；
- 程序、模型、harness、控制器、仿真器和评分器版本；
- 无效运行、超时、接口错误和物理失败是否进入分母；
- 被测程序能否读取 reward、success、原生状态或未来状态。

策略比较若只写“模型 A 成功率更高”，却没有这些条件，通常无法判断提升来自模型、API、更多尝试还是评分变化。

(dexlab-policy)=
## 6. DexLab 应该怎样用这条路线

### 直接借鉴

1. **把 Code as Policy 用作实验表示。** 任务逻辑、测量、动作和评分写成不同所有权，让每次失败能沿时间线追到第一失效层。
2. **先做反馈消融。** 对同一条面包或入槽失败记录，比较“终态/视觉进度”与“逐原语/接触状态”两种观察包能否改善归因。
3. **把根因整理成 skill card。** 每条至少包含失败签名、触发前提、候选修复、适用边界、支持证据与反例。
4. **技能晋升与任务成功分开。** `verified_once`、`transferred`、`refuted` 是不同状态；同任务有限 seed 复现只证明知识能传递，不证明泛化。

### 暂不采用

- 用 Code Agent 替代 DexLab 的物理引擎或独立评分器；
- 因一次成功率提升就默认引入并行候选、进化搜索和开放式技能库；
- 让 task skill 与可执行 task program 共用一个“skill”标签；
- 把作者报告、演示视频或接口存在当成 DexLab 已复现能力。

### 第一个可验证问题

选择已公开的烤面包滑落案例，冻结任务、物理和评分，只增加两类观察包：

- `A`：任务阶段、成功谓词、前后图或结构化视觉变化；
- `B`：在 `A` 上加入逐原语请求/结果、实际到达、接触建立/丢失、冲量和首次滑移。

让独立诊断者分别写首次失效链。改变判断的最低证据不是“文本更详细”，而是：

- 能否定位到现有测量真正支持的第一层；
- 竞争解释是否被区分；
- 同配置是否可复算；
- 失败分母和旧评分路径是否保持不变。

只有反馈契约稳定后，才值得测试“把修复写成 skill card，再由 fresh verifier 按卡复现”。若反馈不改善归因，增加代码生成或自动技能库只是增加成本。

## 7. 推荐阅读顺序

1. 先读原始 [Code as Policies](https://arxiv.org/abs/2209.07753)，理解“语言模型程序 + policy API”的基本命题。
2. 再读 [CaP-X](https://arxiv.org/abs/2603.22435)，看抽象层、反馈和测试时计算如何改变结论，并参考 [Discussion #341](https://github.com/huangkiki/Dexlab/discussions/341)。
3. 读 [COAP](https://arxiv.org/abs/2610.12369) 的显式状态与受控代码改动，参考 [Discussion #335](https://github.com/huangkiki/Dexlab/discussions/335)。
4. 读 [ASPIRE](https://arxiv.org/abs/2607.00272) 的 trace、技能晋升和 held-out 协议，参考 [Discussion #342](https://github.com/huangkiki/Dexlab/discussions/342)。
5. 读 GR00T 2 的 [官方白皮书](https://research.nvidia.com/labs/gear/gr00t-2/assets/gr00t2_whitepaper.pdf) 的 §3.4 与附录 G，观察 Agent、CaP、接触策略和单一控制权如何分层，参考 [Discussion #419](https://github.com/huangkiki/Dexlab/discussions/419)。
6. 最后回到 DexLab 的 [面包滑落证据](robodojo-bread-slip.md)与[模型评测协议](model-evaluation.md)，判断哪些机制能接进真实失败链。

## 证据范围

本页整理的是方法位置和可迁移机制，不是跨论文排行榜。论文性能数字均为作者报告；CaP-X、ASPIRE 的固定源码可确认 trace、反馈、技能晋升和评测边界。GR00T 2 使用 2026-11 官方白皮书核对，但官方代码要到 2026-12 才开放，因此这里没有审查其实现。本轮没有运行外部 Agent、外部 benchmark 或 DexLab 新物理实验。HexaShell/Auriga 仅按官方摘要定位为 agent harness 邻类，没有在本页重述其成功率排名。

更广的仿真问题仍从《[当我们在讨论灵巧操作仿真时，我们在讨论什么？](dexterous-hand-simulation.md)》开始；Code as Policy 是其中“策略与评测”层的一个专题，不是整个仿真研究的总框架。
