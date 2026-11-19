# 当我们在讨论灵巧手仿真时，我们在讨论什么

**2026-11-19 专题增补：[Felis：六电机主动脊柱是机制，事件触发的策略合同才是可迁移部分](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterous-hand-simulation.html#felis-policy-contract)。** 该项目公开推理代码与三个训练好的策略，不是训练框架。DexLab 暂观察欠驱动机构，先借鉴其观测、reset、release 和控制器边界。

**2026-11-19 专题增补：[RaiSim 能跑通 Bumi BlinkMimic2 transition 闭环，不代表策略训练成功](https://huangkiki.github.io/Dexlab/zh-cn/latest/raisim-bumi-mimic.html)。** 六段本机实验恢复了 Bumi 执行器语义，采集 643 万个 RaiSim 环境步并完成 5,000 次更新；冻结策略从 5/6 完成降到训练后的 0/6。最可迁移的结论是：solver 名称之下的物理学习器必须单独验收。

**2026-11-18 专题增补：[RaiSim：CPU 快速训练不等于全局物理更准](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#raisim-physics-boundary)。** RaiSim 的论文影响力和真机迁移证据主要来自高频机器人控制，不是所有接触任务上的精度排名。DexLab 可把它作为独立求解器对照，但暂不应把所有任务迁移过去。

**2026-11-18 专题增补：[RoboDojo 仿真可信度审计：先读回参数、检查数值与评分](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#robodojo-simulator-audit)。** 技术博客沿着“参数送达 → 数值可能性 → 求解守恒 → 评分语义”检查一个 Isaac Sim benchmark。最值得 DexLab 借鉴的是四道前置检查，不是把任何真机失败都改写成 Sim-to-Real Gap。

**2026-11-17 专题增补：[Closing the Loop：硬件限位、闭环传动与 reset 要分层验收](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#closing-loop-transmission)。** Unitree G1 脚踝的串行模型忽略了曲柄—推杆闭链。作者依次处理实测限位、传动雅可比、控制增益、reset 一致性和积分器稳定性；可迁移的是这条判因顺序，不是“所有资产都应立刻改成闭环”。

**2026-11-16 专题增补：[CaP-X 与 ASPIRE：先验证反馈，再晋升技能](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#capx-aspire)。** 两篇同属 Code-as-Policy：CaP-X 把 API 抽象层级和反馈通道变成受控变量；ASPIRE 要求失败修复经隔离复现后才进入技能库。DexLab 先借这两道证据门，不先迁移整套 Agent。

**2026-11-16 专题增补：[COAP：可审计状态、任务程序与首次失效层](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#coap)。** 最值得借的不是“纯代码超过 VLA”，而是显式状态、任务/原语分层和受控代码改动；DexLab 先把它用于一条已有接触失败记录，不整体切换策略路线。

**2026-11-15 专题增补：[把吞吐、成本和完整训练闭环分开](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterous-hand-simulation.html#throughput-cost-closed-loop)。** 以 RaiSim 供应商自建的 CPU MuJoCo 与 GPU Newton 对照为例，小批量、大批量、FP32/FP64、射线查询与不同接触工作不能压成一个引擎总分。

**2026-11-13 专题增补：[RoboColiseum：动作回放、仿真可信度与完整任务评测](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterous-hand-simulation.html#robocoliseum)。** 先 Discussion，再沉淀可迁移机制、时序/反力边界与验证条件。

**2026-11-12 专题增补：[CoRL 2026 哪些论文最值得 DexLab 学](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#corl-2026-dexlab-lessons)。** 逐项筛查官方录取清单，结论是先借随机实例统计评测、接触失败分层诊断与接触事件校准，不先换大模型或仿真引擎。

**2026-11-12 专题增补：[从“评分漏洞”到“榜单投机”](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#benchmark-gaming-audit)。** 以 CoRL 2026 Oral Best Paper Award Finalist 为例，把缺失能力探针、训练支持内重采样、数据距离和统计可检测性接到 DexLab 当前评分审计。

**2026-11-11 专题增补：[现有仿真 benchmark 与 DexLab 的借鉴顺序](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#simulation-benchmarks-2026)。** 按物理误差、任务能力、重复性与真实预测价值整理代表工作，并给出源码快照和实施边界。

**[打开本机原版研究页面：当我们在讨论灵巧操作仿真时，我们在讨论什么？](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html)**

原版保留完整排版、六层问题、38 篇论文筛选、19 个仓库对照和展开正文，并追加[10 月论文增补](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#october-2026)：14 篇相关工作与 1 篇背景参考按六层框架归位。优先读 DiffContact、RoboJEPA、Rollback，再结合 DiffGIPC、HandsOn、SuperMimic。原版中的 Obsidian 链接仍打开本地笔记；论文与仓库链接可公开访问。[未增补的 9 月原版](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation-2026-09-14.html)与本机文件逐字节一致。

**2026-11-03 专题增补：[多示范共享策略与动力学模型](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#shared-dexterous-tracking)。** 补入 FlashDexRetarget、ReDexT、Dex-SuperMimic 与 Weave 接入，展开已有 DONIC、SuperMimic 条目。这些外部工作不计入原来的 38 篇论文、19 个仓库或 DexLab 复现实验。

**2026-11-11 专题增补：[RoboDojo / Astra：模型、动作执行和评分](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#robodojo-astra)。**

**2026-11-12—13 失败诊断：[RoboDojo 烤面包的面包脱落与入槽接触逃逸](https://huangkiki.github.io/Dexlab/zh-cn/latest/robodojo-bread-slip.html)。**

以下保留较短的阅读路线，原版研究页面是完整调研入口。

**我们在讨论：怎样在可控的虚拟环境中研究手如何完成操作、为什么失败，以及哪些结果值得拿到真实机器人上验证。** 要模拟的既有物体运动，也有手的驱动、接触、传感、控制时钟和任务条件。引擎名称、画面和运行速度各自只能回答一部分问题。

本文从“拿起一个瓶子，在手里转动，再放下”出发，整理六层问题、五种研究路线和三个实验起点。这里的灵巧操作包括多指或双手的抓取、换指、工具使用与柔性物体操作；普通夹爪的研究只有在接触或传感机制可借鉴时作为邻接参考。

## 从一只手转动瓶子说起

这段看似连续的动作，其实验要求并不相同：

1. **碰到瓶子：** 碰撞几何应当让手指在正确的位置接触。
2. **拿稳瓶子：** 手指需要提供足够的承载力和抗转动力矩，驱动也要能实现这些力。
3. **在手里转动：** 部分接触要保持，另一些要滑动、滚动或换指；还要区分物体相对手掌的转动和手腕整体移动。
4. **放下并松手：** 物体应得到新的支撑，手指张开后不再黏住它。

因此，“没有掉下来”“姿态变了”和“完成手内操作”应分别验收。起步时由桌面托住、用虚拟约束吸住，还是由手独立拿稳，也必须写清。一次失败首先告诉我们某个环节没有达到要求，归因还需要对照实验。

## 六层问题：先确定希望仿真帮什么忙

| 层次 | 要问的问题 | 应当留下的证据 |
| --- | --- | --- |
| **任务与接触** | 要抓住、换指、拧紧，还是完成某个精度要求？ | 初态、接触阶段、成功窗口、扰动和失败类型。 |
| **本体与执行器** | 手能动到哪里，实际能施加多大的力？ | 碰撞几何、质量惯量、关节与驱动耦合、力矩限幅、增益和延迟。 |
| **物理演化** | 接触如何产生，摩擦与形变怎样影响下一步运动？ | 接触位置与法向、力与力矩、穿透、滑移、步长及求解预算。 |
| **传感与观测** | 策略知道什么，真机能否得到同样的信息？ | 相机或触觉的生成方式、遮挡、噪声、标定、采样频率和时间戳。 |
| **数据与策略** | 仿真用来规划、学习、扩增示范，还是筛掉失败动作？ | 有效轨迹率、物体与接触类型覆盖、训练输入、交互量和总成本。 |
| **校准与验证** | 哪些预测经得起独立检查，哪些能迁移到真实系统？ | 数值参照、留出条件、真实测量、失败记录和不确定度。 |

这六层是本文组织问题的框架，并不是某篇论文提出的统一算法。它们通过一个循环联系起来：**策略根据观测选择动作，控制器和执行器把动作变成物理输入，环境演化后产生下一次观测。** 任务与评分规定整个循环何时算成功。

例如，策略发出“关节转到这里”的目标，控制器会根据误差产生力矩；它不同于直接给定力矩，更不同于直接写入关节位置。同样的目标序列，换一组增益、限幅或执行频率，实际接触过程也可能不同。物理子步、控制更新和传感采样应分别记录。执行器输入与输出的区分可参照 [MuJoCo 执行器模型](https://mujoco.readthedocs.io/en/stable/computation/index.html#actuation-model)。

## 接触判断、接触响应、数值求解，各自在做什么

先把“接触算得好不好”拆成三个可检查的问题：

- **接触判断：** 哪两个表面相遇？接触位置、法向和距离是多少？渲染用的网格与碰撞用的形状需要分别查看。
- **接触响应：** 在这些接触处，允许怎样的法向力、滑动摩擦、抗扭力矩或形变？
- **数值求解与时间推进：** 如何计算耦合的运动与接触响应，再从当前状态推进到下一时刻？步长、停止容差和计算预算是什么？

这是功能上的划分；具体实现可以把几步耦合起来。MuJoCo 文档分别说明了[碰撞检测](https://mujoco.readthedocs.io/en/stable/computation/index.html#collision-detection)、[接触模型](https://mujoco.readthedocs.io/en/stable/computation/index.html#contact)与[约束求解](https://mujoco.readthedocs.io/en/stable/computation/index.html#constraint-solver)。比较软件时，还应区分引擎、任务框架、求解算法和积分器，见 [DexLab 求解配置分层](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html)。

**算得更充分，只能先说明更充分地求解了所选模型。** 如果模型缺少任务所需的力矩方向，增加迭代次数本身不会补上这种物理作用；缩小时间步的数值敏感性，也需要与真实材料准确性分别检验。

### “可微”到底是哪一段可微

可以把梯度理解成一个局部问题：**动作或参数稍微变化，下一步状态或任务损失会怎样变化？** 讨论可微仿真时，应同时说明对谁求导、经过哪些模块，以及接触切换处如何处理。

例如，手指尚未碰到瓶子时，微小动作可能完全不影响瓶子；动作稍大一些，进入接触后才会推动它。沿当前分支计算的局部梯度，不自动包含跨过这道边界后的效果。

代码中有 `if/else`，不意味着所有分支内部都不能求导；某个接触求解器能给出梯度，也不意味着接触对选择、碰撞特征切换和整个长时轨迹都处处光滑。平滑近似、固定接触分支和自定义导数还会给出不同的梯度含义。

实际评估至少应分开检查**前向运动、局部梯度和用该梯度更新动作后的收益**。有限差分是局部核对手段，跨越不光滑边界时要说明扰动尺度，不能把一次梯度检查当作所有接触模式的保证。[Warp 官方微分文档](https://nvidia.github.io/warp/latest/user_guide/differentiability.html)介绍了自动微分的限制及 Jacobian、有限差分和梯度检查工具；具体引擎与版本的覆盖范围仍需单独核对。

## 触觉、画面和物理状态要分别验收

指尖合力、压力分布、胶垫形变和光学触觉图像，描述的是不同层次的信息。接触力数组不会自动成为一个经过标定的触觉传感器；漂亮的相机画面也不能证明策略通过相机完成了闭环控制。

选择观测时，可以沿着“任务需要知道什么”向下追问：保持抓取需要判断是否在滑；插入可能需要判断偏向哪一侧；换指还可能需要接触历史。**相同的当前位姿，未必对应相同的触觉内部状态。** [HydroShear](https://arxiv.org/abs/2603.00446v2)就是把黏着—滑动与路径相关剪切纳入触觉模型的代表。它在夹爪与 GelSight Mini 条件下报告的结果，不能直接当作多指全手换指能力。

另一方面，[Taccel](https://arxiv.org/abs/2504.12908v2)把机器人、物体与触觉传感器放入刚柔接触求解中。两类工作投入的建模环节不同，应该比较任务所需信号与计算成本，而不能只比较输出图像。

记录实验时，要注明物体真值是否只用于训练、部署时用的是估计值还是直接真值，以及触觉模型是否反馈影响物理运动。恢复中途状态时，还要保留实现所需的传感、控制与物理历史状态。

## 研究者怎样使用仿真

仿真可以用于反复尝试、重放失败和改变条件，也可以用来在线预测下一小段动作。冻结任务分布、接口、预算与计分规则后，才形成可比较的 benchmark。下面五种路线可以组合使用，成本也应合并计算。

| 路线 | 仿真主要承担什么 | 仍需补齐什么 |
| --- | --- | --- |
| **细化接触与形变** | 计算对任务关键的接触、凝胶或物体形变。 | 材料与传感器标定，以及额外算力是否带来有效收益。 |
| **对齐观测表示** | 生成力、深度或剪切等便于与真实信号对齐的表示。 | 真实传感到该表示的映射，以及被舍弃的信息是否重要。 |
| **生成与筛选数据** | 变换示范、执行新轨迹、过滤失败。 | 新数据是否增加接触类型和恢复机会，而不只是增加帧数。 |
| **重定向与课程学习** | 把人类动作转成机器人的可执行操作，逐步撤去训练辅助。 | 机器人驱动约束、辅助撤去后的表现和部署观测条件。 |
| **简化仿真并用真实数据补齐** | 学习可复用的粗粒度技能。 | 真实触觉、精细控制与恢复，以及所需真实数据和人时。 |

这张表是对下列文献的研究归纳，不是 DexLab 已实现的五项能力，也不构成方法排名。更复杂的仿真是否值得，取决于它改善了哪个可测量的失败。

## 多条示范，怎样共用策略与动力学模型

同一只手拿起瓶子、转动瓶子和放下瓶子，可以共享控制经验；动作目标不同，部分接触动力学仍然相同。但物体形状、质量、摩擦或关节结构改变时，共享模型也需要相应条件与状态表示。这条路线连接第五层“数据与策略”、第三层“物理演化”和第六层“验证”。

**共享策略**让同一套参数根据当前状态与参考动作选择控制；**共享 world model**学习状态和实际动作如何产生下一状态，并可通过想象 rollout 的梯度训练策略。前者可以只用 FlashSAC 或 PPO，二者并不绑定。物理仿真吞吐、经验复用和可微优化带来的收益应分别比较。

| 工作与核查入口 | 共享什么、怎样学习 | 结果应该怎样理解 |
| --- | --- | --- |
| [FlashDexRetarget · v2](https://arxiv.org/html/2610.01849v2) | 多参考 FlashSAC；左右手各有 actor–critic，每侧参数跨示范共享。几何、距离和未来参考帮助区分交互。 | 已有多示范联合训练，没有 SuperMimic 式可微 WM。论文的 CHORD 对照使用 PPO，不能将其加速比移植到当前 FlashCHORD。 |
| [DONIC · v1](https://arxiv.org/html/2610.29997v1) | PPO + BC、接触角色奖励与成功轨迹回收；共享双手跟踪策略。 | 最大训练集合为 3,420 条参考。同一冻结 checkpoint 分别评估未见轨迹与未见物体，与训练期间累计转换数不同。 |
| [ReDexT · 官方项目页](https://aim-uofa.github.io/ReDexT/) | 共享残差策略根据执行反馈修正 IK 命令，支持冻结执行和整批适应。 | 每种手分别训练一套策略，跨该手的轨迹共享；共享适应后的结果不是零样本泛化。 |
| [Dex-SuperMimic · 仓库快照](https://github.com/CumulusAlpha/Dex-Supermimic/blob/2becb7380fed86171056f9bf4338b2a6a0c14b01/README.md) | 学习到的 WM、想象 rollout 与策略更新用于 Wuji 手转方块、转笔。 | 三个任务配置不等于一个权重联合完成三个任务，也没有建立 CHORD 多示范规模的结果。 |
| [rethinking-supermimic · 仓库快照](https://github.com/btx0424/rethinking-supermimic/blob/c2b1126e1de9990354290c2c231481b29bc265db/README.md) | 接入 Weave / Weave XHand 手—物参考，提供基于学习模型的策略更新入口。 | 数据与训练接口属于实现证据；所查 README 未报告新增手—物任务的成功率或加速基准。 |

[FlashDexRetarget 项目页](https://holiday-robot.github.io/FlashDexRetarget/)报告 XHand 的 50 条示范中 90% 在 29 GPU 小时内转换成功，1,000 条示范中 600 多条在 60 GPU 小时内成功转换。这是作者的累计数据转换结果，不能直接解释成最终冻结策略在全部示范上的稳定成功率。不同论文的手型、初态、阈值和计算成本口径不同，本表不构成性能排名。

### SuperCHORD 可以提出什么问题

“多示范共用策略”已有上述先例。将 CHORD 接触力旋量指导、共享手—物 WM 与参考条件策略结合起来，可以作为研究设想；本次定向检索不足以支持“首次”的主张，也没有建立 DexLab 的训练结果。

有辨别力的比较是：每条示范独立训练、相同示范联合 FlashSAC、相同联合设置下通过 WM 梯度更新策略。先固定奖励来区分共享与模型的收益，再比较接触指导的增益。可以从同一种手与兼容物体表示开始，先按示范均匀采样；这是建议，不是已经冻结或执行的实验协议。

统一记录总 GPU 小时、仿真交互量、累计转换数、最终 checkpoint 的训练集覆盖、未见轨迹与未见物体表现。模型还需检查前向误差、接触附近动作响应以及更新后原生仿真收益；低预测误差本身不能证明优化方向有用。首次阅读建议按 FlashDexRetarget → DONIC / ReDexT → 两个 SuperMimic 实现的顺序，分别理解共享训练、泛化和动力学模型优化。

本专题核查于 2026-11-03，依据上述论文、官方项目页与固定仓库快照；没有重新完成所有论文的全文精读，也没有复测作者结果。

## 七篇代表工作，分别回答什么问题

| 工作与来源 | 主要贡献落在哪里 | 阅读时继续追问 |
| --- | --- | --- |
| [BODex · v3](https://arxiv.org/abs/2412.16490v3) | 用双层优化合成灵巧抓取，并用仿真和真实抓取验证。 | 稳定抓取覆盖哪些载荷与物体？是否涉及后续换指和连续操作？ |
| [Taccel · v2](https://arxiv.org/abs/2504.12908v2) | 高性能刚柔接触与视触觉仿真。 | 吞吐对应什么传感器数量、网格、并行规模与硬件？ |
| [HydroShear · v2](https://arxiv.org/abs/2603.00446v2) | 模拟具有接触历史的剪切与黏滑观测。 | 校准用了什么真实数据？任务是夹爪还是多指手，初态如何布置？ |
| [DexMimicGen · v2](https://arxiv.org/abs/2410.24185v2) | 从少量人类示范扩增双手灵巧操作轨迹。 | 新物体、接触模式和失败恢复覆盖了多少？真实数据成本是什么？ |
| [DexMachina · v1](https://arxiv.org/abs/2505.24853v1) | 通过逐渐减弱的虚拟物体控制器，学习跟随人类示范的物体效果。 | 辅助何时撤去？比较手型时采用什么驱动与腕部条件？ |
| [DexScrew · v2](https://arxiv.org/abs/2512.02011v2) | 先在简化仿真中学指步，再采集真实示范训练触觉策略。 | 任务进度与完整成功怎样区分？真实采集和初始装配由谁完成？ |
| [Dex-X · v3](https://arxiv.org/abs/2609.07747v3) | 用仿真交互补全人类视频缺失的触觉监督，学习视触觉策略。 | 仿真教师与真实部署各测了哪些任务？观测、参考运动和泛化条件是什么？ |

这些论文分别研究抓取生成、接触与触觉、示范扩增或策略迁移；它们并非七个可以直接排名的物理引擎。这里的概括依据链接版本的官方摘要与既有研究笔记，问题列是阅读和复现时要核对的条件，不是在宣称论文遗漏了这些信息。

看数字也要保留单位与分母：任务进度不是整项任务成功率；帧数不是独立示范数；聚合并行步数不是单环境实时率；特定任务的真实成功率不能代表所有任务。论文实验、公开代码和实际复现分别提供不同证据。

## 用 DexLab 的三个案例检验这些区分

| 案例 | 已有证据 | 解释边界 |
| --- | --- | --- |
| [Wuji 双指夹球](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html) | 相同控制下，点接触改为合成抗扭接触，两秒保持的最大位移由 **2.734 mm** 降为 **1.025 mm**，通过原定 2 mm 门槛。 | 接触模型改变了该配置的验收结果；参数不是实测指垫材料，仍有慢漂移，也没有证明求解器故障或手内旋转成功。 |
| [海绵擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html) | 固定配置下，辅助保持时 **3/3** 通过，去掉辅助后 **0/3**。 | 支持该条件下的辅助依赖；不能据此断言底层求解器普遍失效。 |
| [布料操作](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html) | 单手夹持、抬升与释放通过；完整折叠记录的最大边长应变 **12.55%**，超过预设 **5%** 上限。 | 局部动作可执行与完整任务通过是两个验收层次；折叠还存在其他未满足项。 |

这些案例提醒我们分别报告：记录是否可信、计算是否符合所选模型、物理参照是否成立、任务是否完成、真实系统是否验证。已有证据的详细归因见[失败复盘](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-failure-audit.html)，策略与后端的验收约定见[模型评测协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)。

## 从哪个实验开始

**先检查抓持与释放。** 选择一个手、一个简单物体和固定腕部，明确载荷与保持窗口。先让正例具备资格，再加入张指、禁接触或低摩擦等有预期的对照；记录原生接触、物体运动和驱动饱和。基础承载不成立时，先定位原因，再解释换指失败。[Wuji 已有案例](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)提供可离线复算的起点。

**再判断什么触觉信息有用。** 在相同任务条件下比较无触觉、指尖力、几何或剪切表示和更详细的触觉模型。先核对信号与事件时间，再在匹配预算下比较策略收益；保留渲染、学习和真实标定成本。这是建议的实验设计，并非本站已完成的触觉对比。

**最后判断仿真减少了什么真实成本。** 比较示范扩增、功能重定向与真实数据补齐时，固定测试对象和任务要求，分别记录真实示范数、采集人时、仿真交互量及留出表现。没有真实测试时，可以先验证数值和任务条件，但迁移收益应保持待验证。

无论选哪条路线，运行前都应写下一张实验卡：**目标与初态、模型及版本、动作与观测接口、时钟、成功与失败条件、对照、预算、原始记录位置。** 任务、参数和验收变更要形成新的条件记录。继续阅读可从 [Newton 七类论文导读](https://huangkiki.github.io/Dexlab/zh-cn/latest/newton-reading-guide.html)、[实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html)和[诊断方法](https://huangkiki.github.io/Dexlab/zh-cn/latest/diagnosis.html)进入。

## 精细插接：不要把 RLT 与 CAP 当作替代方案

以 Ethernet 插接为例，至少要分开三个问题：目标接口和接触位置是否明确，机器人到达接口后能否完成接触阶段，以及几何、柔顺、力控和评分是否允许真正插入。把它们都称为“1 mm 精度”会混淆机械间隙、位姿误差、控制分辨率和成功窗口。

[RL Token（RLT）](https://arxiv.org/abs/2604.23073)面向第二层：基础 VLA 先完成大范围动作，冻结后的小型 actor–critic 在 RL token、机器人状态和 VLA 参考 action chunk 上改进最后 5–20 秒的关键阶段。论文的 400–1000 是按任务变化的**在线训练 episode 数**，不是示范条数；此前还需要每项任务 1–10 小时遥操作数据。作者另报实际机器人运动数据约 15 分钟至 5 小时，但 reset、人工奖励、干预、阶段切换和总墙钟也属于真实成本。Ethernet 基础策略本来已接近高成功率，RLT 的主要收益是减少试探、提高关键阶段吞吐，不能概括成从零学会插接。

[Contact-Anchored Policies（CAP）](https://arxiv.org/abs/2602.09017)面向第一层：用三维 contact anchor 明确交互位置，并通过正向运动学持续跟踪。其 Close 任务消融中，RGB-only 为 58%，CAP 为 96%，支持接触点条件化在该条件下的价值；公开训练集有 20,365 条示范、约 23.1 小时，覆盖 Pick / Open / Close。论文和 [EgoGym](https://github.com/omarrayyann/EgoGym) checkpoint 没有 Ethernet、peg-in-hole 或 1 mm 插接结果，因此 CAP 不是已验证的 RLT 低数据或更高精度替代。

对 DexLab，更可迁移的是四层验收：**目标锚定**记录坐标系、深度和标定误差；**关键接触阶段**记录进入/退出、局部动作、接触与力；**交互预算**同时记录示范、episode、机器人运动时间、墙钟、reset、人工干预、失败和磨损；**完整任务**从抓取、搬运、对准到插入/锁止定位首次失败层。critical-phase reset 与 home-position full-task 应分别评测，成功率、完成时间、重试和接触力也不能压成一个分数。

只有基础策略稳定到达目标附近、主要失败确实在最后接触阶段时，RLT 式局部在线强化才是合理候选；只有主要问题是“在哪里交互”时，CAP 式锚定才应优先。二者可以组合，但目前仍是待验证提案。完整证据、成本拆分和评分负例见 [Discussion #309](https://github.com/huangkiki/Dexlab/discussions/309)；本节没有新增 DexLab 插接实现或实验。

## 现有仿真 benchmark：它们测什么，DexLab 应当借什么

**2026-11-11 调研结论：优先借鉴评测方法，把接触模型误差、计算重复性、任务完成与真实预测能力分别报告。** SimBenchmark、ContactBench、GPUSimBench、GAUGE 最贴近 DexLab 的物理诊断；DexGraspBench、ContactBench 1.0、HandsOn 提供操作任务设计；SIMPLER 提供仿真是否能帮助选择真实策略的验收思路。任务更多、成功率更高或 FPS 更大，各自只能支持对应范围的结论。

本专题覆盖机器人操作与接触仿真，兼顾柔性物体、任务泛化和 GPU 性能；不把自动驾驶、导航或视频生成的所有 benchmark 收作同一排行榜。以下是代表性调研，不声称穷尽。内容是外部机制分析与迁移建议，没有新增 DexLab 物理实验，也没有改变已有验收协议或工作顺序。

### 用一次“拿起瓶子、转动、放下”区分评测对象

这是自拟的说明例子。瓶子没掉下来，可能是接触真的能承载，也可能是手腕运动、辅助约束或评分窗口掩盖了问题。瓶子转到了目标角度，也可能是整个手腕转动，尚未发生预期的手内换指。放到目标区域后立即计分，还可能接受尚在运动或仍被手指夹住的物体。

同一段动作因此需要几种不同的检查：物体相对手掌的位姿、承载与接触切换、松手后的稳定状态、超时与失败原因，以及计算成本。若要据此选真实机器人策略，还需要在相同条件下对多种策略做仿真与真机配对。这个例子贯穿下面的取舍，不能用任一单项分数替代全部证据。

### 代表性 benchmark 地图

表中的“可借鉴”是本次分析，不代表已经接入 DexLab。论文覆盖、代码覆盖与排行榜使用的子集可能不同。

| 评测对象 | 工作与主要机制 | DexLab 可借鉴什么 | 结论边界 |
| --- | --- | --- | --- |
| 引擎数值与成本 | [SimBenchmark](https://leggedrobotics.github.io/SimBenchmark/about/methodology.html)：简单碰撞体、接触/多体场景，报告误差与实时倍率。 | 在相同物理问题下画误差—成本曲线，说明控制、步长和预算。 | 历史软件与 CPU 配置；不能照搬为当前 GPU 引擎排名。 |
| 接触模型与算法 | [ContactBench / Contact Models in Robotics](https://arxiv.org/html/2304.06372v3)：统一实现不同接触问题及求解方法，检查互补性、摩擦和数值自洽。 | 区分“模型选择改变了物理行为”和“同一模型求解不充分”。 | 算法重实现不等于各官方引擎全部实现；论文明确讨论了实现差异。 |
| GPU 扩展与重复性 | [GPUSimBench](https://arxiv.org/html/2607.13059v1)：吞吐、显存、批内差异、重复运行差异及真实斜面碰撞分布。 | 把并行环境数也当实验变量，检查扩容是否改变结果。 | 两个扩展性场景和一个真实对照场景，单套软硬件；不覆盖全部接触、柔性或视觉工作负载。 |
| 真实动力学参照 | [GAUGE](https://arxiv.org/html/2608.05948v1)：真实轨迹、物理参数与不确定度，涵盖刚体、绳、织物、体积软体。 | 记录测量重复性、参数来源及机制相关的误差。 | 22 个任务族不等于全部完成引擎评测；论文引擎实验用 14 个任务族。代码发布边界见下文。 |
| 抓取稳定性 | [DexGraspBench](https://github.com/JYChen18/DexGraspBench)：MuJoCo 中的桌面提升、外力扰动、解析抓取指标与穿透检查。 | 将初始几何、抓持过程、扰动保持和解析指标分开。 | 当前主分支与论文 baseline 分支不同；稳定抓取不证明换指或长程操作。 |
| 日常接触技能 | [ContactBench 1.0](https://jingyi-xiang.github.io/contactbench/)：8 类技能、36 项参考任务，可打印机构及阻力变化。 | 用插入阻力、旋转需求等行为变量定义难度，同时报告进度与用力。 | 与上面的求解器 ContactBench 无关；论文任务数、仿真实现数和已评测策略子集要分别计数。 |
| 灵巧操作与迁移 | [HandsOn](https://arxiv.org/abs/2610.26765)：Core-50 与无目标任务示范的 Transfer-16，含组合与柔性任务。 | 用任务阶段定位首次失败，区分接触建立、协调和已达目标的保持。 | 论文的定性真机展示不构成全任务定量迁移；当前代码扩展也不能并入原论文数据口径。 |
| 操作学习与采样 | [ManiSkill3](https://github.com/mani-skill/ManiSkill)：SAPIEN 上的操作任务、GPU 物理和视觉采样。 | 规范任务接口，并分开测无视觉、带视觉和记录数据时的成本。 | 框架吞吐不等于策略训练吞吐；同一底层引擎的不同框架不是独立引擎样本。 |
| 多任务/元学习 | [Meta-World](https://github.com/Farama-Foundation/Metaworld)：相关操作任务上的多任务与元强化学习。 | 分开训练任务与未见任务，比较学习预算和适应能力。 | 学习能力基准，没有单独校准接触力和真实材料。 |
| 视觉操作与示范 | [RLBench](https://github.com/stepjam/RLBench)：任务变体、示范生成和多种观测/动作模式。 | 固定任务变体、相机与控制模式，再比较策略。 | 路径规划产生的示范和任务成功判定，不是独立的物理真实性证明。 |
| 知识迁移 | [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO)：空间、物体、目标及混合知识迁移。 | 保留受控分布变化，避免同时更换物体、目标和控制器后无法归因。 | 常用 LIBERO-10 与完整 130 任务集合不是同一分母；成功率不测材料保真。 |
| 连续任务链 | [CALVIN](https://github.com/mees/calvin)：语言指令串联，报告完成前 1 至 5 项的比例及平均链长。 | 保留跨子任务物理状态，查看失败在哪一环累积。 | 原脚本序列开头重置环境、每个子任务重置模型；物理连续与策略记忆连续要分开。 |
| 双臂鲁棒性 | [RoboTwin 2.0](https://robotwin-platform.github.io/leaderboard.html)：clean / randomized 评测。 | 固定训练数据后测随机化条件下的退化。 | 随机化抗性并不自动等于真实迁移；须注明训练配置及随机化轴。 |
| 场景与组合泛化 | [RoboCasa365](https://github.com/robocasa-benchmark/leaderboard)：Atomic-Seen、Composite-Seen、Composite-Unseen。 | 将见过的基本技能与未见组合分开计分。 | 365 项任务库与当前榜单的 50 个目标任务不同，不能互换成功率分母。 |
| 家庭活动语义 | [BEHAVIOR-1K](https://arxiv.org/abs/2403.09227)：BDDL 初态/目标、OmniGibson 对象状态与活动。 | 明确任务意图、对象状态和必要事件。 | 部分活动涉及显式状态转换规则；语义完成不能一概解释为连续物理机制已验证。 |
| 柔性物体策略 | [SoftGym](https://proceedings.mlr.press/v155/lin21a.html)：布、绳和流体等高维、部分可观测操作。 | 定义形变任务与观测差异，检查覆盖、铺平等任务目标。 | 主要比较策略学习；真实材料验证需要另外的测量参照。 |
| 仿真对真实策略的预测 | [SIMPLER](https://simpler-env.github.io/)：控制和视觉对齐、仿真/真机配对评估。 | 检查仿真是否保留策略优劣次序，并报告绝对成功率误差。 | 结论依赖已测机器人、任务与策略；相关性高不等于接触参数正确。 |
| 持续作业 | [HolidayFactory / DexLab 既有分析](https://github.com/huangkiki/Dexlab/discussions/302)：job 事件与跨 job 状态。 | 先审计评分，再设计保持—卸载/重建接触—释放的短序列。 | DexLab 中仍是提案；持续状态、恢复和 run 级统计尚未因此完成。 |

近期的 [RoboLab](https://github.com/NVlabs/RoboLab) 与 [RoboDojo](https://arxiv.org/abs/2607.04434) 也提供规模化任务评测入口，本次作广度索引，没有审计其完整评分实现。它们的任务目录可供后续选例；当前优先级仍是把已有接触实验的判据与失败解释做清楚。

### 最值得迁移的五个机制

**1. 同时问“解得准不准”和“选的物理模型对不对”。** SimBenchmark 的 rolling 场景将速度与解析参照比较；ContactBench 进一步把接触律偏离、求解精度与步长敏感性拆开。对瓶子抓持，接触模型若缺少必要的抗扭作用，仅增加迭代不一定能保持住。DexLab 已有这种区别的直接证据：Wuji 合成夹球的抗扭接触改变了保持位移，但没有建立真实指垫参数或求解器失效。建议沿已有解析斜面与夹球记录，分别整理参考误差、同模型残差、步长/容差敏感性和耗时；理想刚性库仑关系只在所声明假设下作为参照，不用它无条件否定有意建模的柔顺接触。[ContactBench §IV](https://arxiv.org/html/2304.06372v3#S4) · [DexLab Wuji 证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)

**2. 向真实重复测量对齐，同时保留任务需要的观测。** GAUGE 将几何、物理参数、真实轨迹和实验波动放在一起，避免把一个更细步长的仿真当成真值。其 §3.2 的刚体广义轨迹是位置，织物与体积软体使用各自形变表示；对 DexLab 的瓶子转动，还必须保留姿态、相对手掌旋转和接触事件。它使用的轨迹时间对齐也应与原时间轴误差分开，避免隐藏延迟。先借鉴测量与参数来源的组织方式；真实材料准确性仍要有相应的实物数据。[GAUGE §3.2 与附录 B](https://arxiv.org/html/2608.05948v1#S3.SS2)

**3. 用并行规模与重复运行检查计算稳定性。** GPUSimBench 区分同一批环境间的差异和独立运行间的差异。DexLab 若后续扩展 GPU 批量接触实验，可在相同初态、输入和计时边界下改变并行数，观察位姿误差、接触丢失及成功判定是否变化，再联合看吞吐和显存。源码中的 MuJoCo Warp 吞吐按“环境数 × 测试步数 / 墙钟时间”计算，包含显式同步；这不是单环境控制频率。还应单列冷启动/编译、稳态步进、观测/渲染和记录成本。这是建议的检查维度，不预设哪种引擎必然不确定。[GPUSimBench §III–VII](https://arxiv.org/html/2607.13059v1#S3)

**4. 把成功过程、合理用力与评分漏洞放在同一张结果单上。** DexGraspBench 提供保持与扰动协议，ContactBench 1.0 通过机构阻力改变行为要求，HandsOn 则把复杂任务分阶段观察。迁移到 DexLab 时，先复用现有夹球、释放和 LIBERO 记录审计评分：只进入目标区域、仍被夹持、隐藏支撑、错误事件顺序或直接改写评分状态，分别会不会被接受；合理成功又是否误拒。随后才设计接触阶段任务。ContactBench 1.0 同时报告成功、进度和峰值用力，但其具体力阈值不能直接成为另一只手的安全阈值。[ContactBench 1.0 实验](https://jingyi-xiang.github.io/contactbench/) · [DexLab 当前设计顺序](https://github.com/huangkiki/Dexlab/blob/4867a8637b5999f4169a6dd8a36ecf6ffdede989/docs/current-work.md)

**5. 最终检查仿真是否帮助作出正确选择。** SIMPLER 的价值是比较同一批策略在仿真与真实环境中的表现。其指标代码同时提供 Pearson 相关性和 mean maximum rank violation（MMRV）：后者衡量仿真排错顺序时，涉及的真实表现差距有多大。DexLab 后续若具备配对真机条件，应在未用于调参的条件上同时看绝对成功率偏差、排序错误和不确定度。当前的物理诊断与脚本回放不能冒称这种策略评价已经完成。CALVIN 的链长统计可借来描述连续任务可靠性，但还要声明策略记忆和环境状态分别何时重置。[SIMPLER 指标源码](https://github.com/simpler-env/SimplerEnv/blob/eddb5690749a1e34267807c0f7b5eede323918d7/simpler_env/utils/metrics.py#L134) · [CALVIN 序列实现](https://github.com/mees/calvin/blob/fa03f01f19c65920e18cf37398a9ce859274af76/calvin_models/calvin_agent/evaluation/evaluate_policy.py#L124)

<a id="throughput-cost-closed-loop"></a>
### 吞吐、成本与完整训练闭环：FPS 只回答其中一段

> **TL;DR：** RaiSim 的对照最值得借鉴的不是“CPU 全面胜过 GPU”，而是把选择拆成小批量延迟、大批量吞吐、每美元成本和完整训练闭环。物理步更快，只在物理占端到端时间的主要部分时才可能转成训练收益。

以 Wuji 批量任务为例，一轮包含“接触状态 → 策略动作 → 物理推进 → 新观测／奖励”。若一轮 100 ms、物理只占 20 ms，即使物理快 10×，理想情况下整轮也只从 100 ms 降到 82 ms；这个 100/20 ms 只说明算术关系，不是任何一方的实测。[作者的随机动作报告](https://raisim.com/sections/BenchmarkNewton.html)在作者指定硬件与价格口径下报告：1 world 的吞吐为 RaiSim/Newton 的 95.77×（ANYmal）和 13.43×（Strandbeest），到 4,096 worlds 的 FPS/USD 仍为 3.40×／2.04×。计时每十步更新随机目标，包含目标生成与物理，但排除策略推理、观测、奖励、episode reset、渲染和记录。[固定文档快照](https://github.com/raisimTech/raisim2Lib/blob/f256e315b4c6196f55d15f27a9a16a776213db8b/docs/sections/BenchmarkNewton.md) · [原始测量数据](https://github.com/raisimTech/raisim2Lib/blob/f256e315b4c6196f55d15f27a9a16a776213db8b/docs/public/raisim_newton_random_actions.json)

这也是一组不同数值工作的比较：RaiSim CPU 使用 FP64，Newton SolverMuJoCo / MuJoCo Warp 使用 FP32；求解器、约束与轨迹不同，轨迹平均接触数也不同。动作目标逐位相同只证明输入一致，不能把比率解释为接触正确性排名。对 DexLab，下一次获得授权的批量学习实验应分别记录物理稳态、观测／奖励、推理与传输、reset／恢复、记录／渲染五个时钟，再合成每个有效 transition 的成本；同时冻结并行规模、动作序列和任务判据，保留不同规模下的接触事件与首次失败层。

迁移顺序应先用现有日志估算物理是否为端到端主瓶颈，再决定是否比较 1、少量 world 与填满设备的批量；本轮没有启动这类性能实验。只有物理占比高，且小批量候选路径保持接触／任务结果稳定时，才把后端迁移前移；若主要耗时在 reset、观测或策略侧，先换物理引擎不会解决主要问题。完整取舍与证据边界见 [Discussion #334](https://github.com/huangkiki/Dexlab/discussions/334)。

<a id="mujoco-workload-spectrum"></a>
### 单线程 CPU 对照：2.36–147.16× 是一条瓶颈谱

RaiSim 的 MuJoCo 页面补足了单线程 CPU 视角：10 个有效 workload 的中位耗时比为 2.36–147.16×。接触密集项约为 2.4–4.8×，Strandbeest 闭环为 2.74×，布料为 11.92×，heightmap LiDAR 与 primitive ray 分别为 25.71×、147.16×。这些数字支持“不同瓶颈产生不同倍率”，不支持一个可跨任务搬运的全局引擎系数。[固定文档](https://github.com/raisimTech/raisim2Lib/blob/7cddae549d59f4ff3cbe05236f6c101fbab4894/docs/sections/Benchmark.md) · [原始结果](https://github.com/raisimTech/raisim2Lib/blob/7cddae549d59f4ff3cbe05236f6c101fbab4894/docs/public/benchmark_results.json)

同一个 `primitive_ray_scaling` workload 就能显示计时边界为何重要：完整 launcher 为 RaiSim 0.016 s、MuJoCo 2.427 s（147.16×）；JSON 的中位场景构建约 7.31 ms 对 1,535.95 ms（约 210×），纯 10,000-ray query 约 2.803 ms 对 836.698 ms（约 299×）。若任务只构建一次却持续扫描，构建与查询成本应分别决定优化目标；若每次 reset 都重建，构建成本才进入高频路径。

MuJoCo 八块软体堆叠行必须排除：公开配置使用不同粒子、质量和碰撞半径，时间推进到 0.020 s、约第 20 步时 QACC 出现 `NaN/Inf/huge`。launcher 虽返回 0，作者没有用 9.17 s 对 0.445 s 生成速度比。现有证据只能定位到“软体接触／形变数值演化在 20 ms 内失去有限性”；要区分材料、几何、迭代或 solver 主因，还需匹配参数并保存第 0–20 步的 QACC、粒子间距、穿透、接触力、约束残差和能量。

对 DexLab，下一步仍是先分解场景构建、持续物理、接触查询、LiDAR／ray、观测、策略、reset 和记录，再按主导瓶颈选优化层。这份 MuJoCo 3.13.0 单线程结果也不能与 Newton 页的 MuJoCo Warp 3.17.0 FP32 GPU 批量结果合成总排名。失败 case 判因门槛与完整边界见 [Discussion #334 补充](https://github.com/huangkiki/Dexlab/discussions/334#discussioncomment-19645295)。

<a id="raisim-physics-boundary"></a>
### RaiSim：一个为高频机器人控制而生的 CPU 物理栈

> **TL;DR：** RaiSim 的论文影响力来自“足够快的动态接触 + 可用的训练工具链 + 真机迁移记录”，不是“所有接触都比其他引擎更准”。对 DexLab，它值得作为独立求解器对照，暂不值得成为所有任务的主物理后端。
>
> **例子：** 一个四足机器人策略输出关节目标后，RaiSim 计算关节动力学与地面接触冲量，再把新状态交给 PPO。只要这个回路足够快，策略就可以在普通 CPU 上并行采集；真机迁移还依赖执行器模型、域随机化、观测、控制与标定。它们共同成功，不能单独归功于 RaiSim 的接触律。
>
> **它证明：** RaiSim 可以承载高影响力机器人学习工作。**它不证明：** RaiSim 的摩擦、形变、穿透或能量耗散在 DexLab 的所有任务上都优于其他引擎。

RaiSim 不是对另一个物理引擎的封装，而是自有的闭源多体仿真栈。当前公开文档与头文件可确认的主要路径是：刚体与关节体动力学、AABB broadphase、解析/SAT/MPR/GJK-EPA narrowphase，以及按约束行扫描、对摩擦接触使用二分法的接触求解。普通刚体接触会缓存上一轮冲量作为 warm start；接触以冲量报告，除以时间步才得到力。[Contact and Collision](https://raisim.com/sections/Contact.html) · [Collision Detection](https://raisim.com/sections/CollisionDetection.html)

公开 workspace 只提供 RaiSim 与 rayrai 的二进制、头文件、示例和包裹层，没有引擎源码与完整内部测试。因此这里能核对公开 API、配置与可观测语义，不能审计 solver kernel。论文还跨越 RaiSim v1、v2 和各自 fork；复现实验应使用论文仓库固定的依赖与设置，不能把当前版本行为反填旧结果。

它也是原生 CPU 物理系统。`raisimGymTorch` 为每个环境创建一个 `raisim::World`，用 OpenMP 在 CPU 上并行 step、reset 和观测；PyTorch 策略可以在 CPU 或 GPU 上训练。GPU 主要承担神经网络和 rayrai 渲染，不是这套框架里的物理后端。[raisimGymTorch](https://github.com/raisimTech/raisim2Lib/tree/v2.16.0/raisimGymTorch)

#### 为什么有一批论文反复使用它

1. **历史速度优势。** 2018 年的逐接触求解论文报告，18-DOF 四足机器人多接触单步在单 CPU 核上少于 20 µs，并明显快于复杂场景中的 PGS；2019 年 ANYmal 工作报告“刚体 + 执行器网络”的完整混合仿真接近 500K steps/s，单 CPU、单 GPU 训练均不超过 11 小时。[Per-Contact Iteration](https://doi.org/10.1109/LRA.2018.2792536) · [ANYmal 2019](https://arxiv.org/html/1901.08652)
2. **接触可观测。** 原生接口可读接触位置、法向、坐标系和冲量，适合把接触事件直接写进 reward、老师策略观测和失败记录。
3. **训练与资产形成复用链。** URDF、地形生成、C++ 向量环境和 `raisimGymTorch` 降低了从机器人模型到 PPO 试验的成本；后续团队常直接复用已有机器人资产和代码。
4. **高影响力真机结果形成正反馈。** 当一个引擎先支撑了动态四足、野外感知和长时任务，后续工作沿用它的风险低于重新搭建整套栈。这是“工具与经验”的优势，不是物理精度的单独证明。

#### 工作谱系：哪些论文真正把 RaiSim 用作核心工具

下表是代表性样本，不是完整论文总数，也不把官网列名当作独立评审。论文的成功首先归属于各自的任务、控制、学习与硬件系统。

| 工作 | RaiSim 在系统中的角色 | 阅读边界 |
| --- | --- | --- |
| [Hwangbo et al., 2019](https://arxiv.org/html/1901.08652) | ANYmal 动态运动与恢复；刚体和接触推进，执行器网络补偿驱动差距 | 高速混合训练回路，不等于纯 RaiSim 速度或精度 |
| [Lee et al., 2020](https://arxiv.org/html/2010.11251v1) · [Miki et al., 2022](https://arxiv.org/html/2201.08117) · [Choi et al., 2023](https://doi.org/10.1126/scirobotics.ade2256) | 四足在野外、雪地、植被、泥地和沙地等条件下的策略训练 | 泥、雪、植被和可变形地面多为部署条件；仿真里仍要分别核对实际地形与材料模型 |
| [RMA, 2021](https://arxiv.org/html/2107.04034v1) | A1 的基座策略和环境适应模块全部在 RaiSim 中训练 | 证明“快模拟 + 域随机化 + 在线适应”可迁移，不是证明接触参数自动正确 |
| [Circus ANYmal, 2021](https://arxiv.org/abs/2011.08811v2) | 四足用四肢操纵瑜伽球，零样本上真机 | 作者明确说明当时模拟器不能模拟球的形变，并用接触速度惩罚绕开这一差距 |
| [Concurrent policy/state estimator, 2022](https://arxiv.org/html/2202.05481v2) | 策略、价值函数和状态估计器在 RaiSim 中联合训练 | 真机速度结果依赖估计器、控制器和整机系统，不是单独引擎读数 |
| [Whole-body manipulation, 2023](https://arxiv.org/html/2308.16820) | 300 个环境、Ryzen 9 5950X + RTX 3070，约 15 小时训练整身推物 | 仿真成功率与真机重物操作是不同条件；没有做引擎精度消融 |
| [D-Grasp, 2022](https://arxiv.org/abs/2112.03028) · [ArtiGrasp, 2024](https://arxiv.org/abs/2309.03891) · [RobustDexGrasp, 2025](https://arxiv.org/abs/2504.05287) | 手–物接触策略、articulated object 与灵巧抓取；官方实现使用 RaiSim | 展示多指手与复杂物体可用接触冲量训练；不是跨引擎材料准确性比较 |
| [RAIBO2, Nature 2026](https://doi.org/10.1038/s41586-026-11102-5) | 低耗散步态训练链的一部分 | 单次充电完成马拉松是整机、硬件损耗模型、电机和策略的共同结果 |
| [DiffContact, 2026](https://arxiv.org/html/2610.35852v1) | 用 1 ms 步长做快速前向 rollout，再在反向使用自定义接触梯度 | 论文同时注明标准 RaiSim 在滑动时可能偏离最大耗散，因此它不是用于证明“标准 RaiSim 精确”的案例 |

#### 为什么“采用得多”不能改写成“物理更准”

独立接触研究指出，标准 RaiSim 在滑动接触下不严格满足最大耗散原理，会低估能量耗散，并给出了修正。[Reconciling RaiSim](https://doi.org/10.1109/TRO.2024.3430711) 与 [Contact Models in Robotics](https://arxiv.org/html/2304.06372v3)进一步说明，接触互补条件、摩擦锥、数值容差和时间步都会改变轨迹。

因此，“更准”必须绑定到具体量：接触点、法向力、切向冲量、滑移、能量耗散、穿透还是任务成功率。接触参数未等效时，任何跨引擎数字都不能被读成精度排名。RaiSim 的直接优势更适合表述为：**在动态刚体与关节体任务上，能在 CPU 上以较低工程成本得到足够快、能迁移的 rollout。**

#### 对 DexLab 的接入边界

现阶段不把 RaiSim 扩成所有接触、布料、苹果与灵巧手任务的主后端。更有信息量的第一步，是在已有 `ContactPlane` 的静止、滑动和零摩擦 case 上增加可选适配器，并冻结：

- RaiSim 与 `raisim2Lib` 的精确 tag、原生库哈希和 FP64 配置；
- 与记录一致的刚体质量、惯量、碰撞形状、初态、重力、摩擦和时间步；
- 积分方案、最大迭代数、每约束阈值，以及 episode reset 后的 solver warm-start 清理；
- 接触点、法向、接触坐标系、`impulse / dt`、求解轮数、stall 状态和有限性检查。

只有 RaiSim 产生可复现的求解器敏感差异、并暴露现有记录看不到的首个失效层时，才把它晋升为正式对照后端。若结论只是轨迹略有不同，保留研究页中的谱系与证据边界，不增加整套任务维护成本。后续已经完成安装和六段 Bumi 实验，记录如下，但仍不构成全后端替换资格。

<a id="raisim-bumi-blinkmimic2"></a>
### Bumi BlinkMimic2：训练闭环跑通，策略却退化

> **TL;DR：** 适配器能在 RaiSim 上采集真实 transition、更新 BlinkMimic2 并保存／重载 checkpoint。这证明可执行的训练后端边界，而不是有用的替代方案：冻结策略在 5,000 次更新后从 5/6 完成降到 0/6。
>
> **例子：** Bumi 策略输出 21 个归一化关节目标；RaiSim 以四个 5 ms 子步推进浮基模型，原世界模型／replay 更新器再从 20 ms transition 学习。所有基础设施保持有限，但闭环 actor 随后越过参考姿态和末端高度门禁。
>
> **它证明** RaiSim 能在 512 个 CPU world 上承载 Bumi transition 与更新闭环。**它不证明** 物理来源改变后，原 replay 统计、actor 目标和保留学习率仍然有效。

第一个适配缺陷比策略更早且可具体定位：当前 RaiSim 把厂商 URDF 的 `velocity="0"` 当成真实关节锁死。恢复逐关节速度上限后，冻结 checkpoint 从 0/6 回到 5/6，第一失效也从“关节不动”变成真实闭环漂移。

| Checkpoint | 完成数 | 平均 body 位置误差 |
| --- | ---: | ---: |
| 冻结 MuJoCo 策略直接在 RaiSim 运行 | 5/6 | 0.0584 m |
| 第 10,500 次更新 | 4/6 | 0.0376 m |
| 第 11,500 次更新 | 2/6 | 0.0589 m |
| 第 12,000 次更新 | 1/6 | 0.0433 m |
| 第 15,000 次 averaged actor | 0/6 | 0.0399 m |

更短存活轨迹上的更低误差不是改进。最终策略在每段都越过参考门禁；walk 活到 92.5%，fight 在 14% 失败。共同链条是策略漂移 → root 与末端关系退化 → 未改变的 0.8 rad 姿态或 0.4 m 末端高度门禁。当前运行不能区分世界模型偏差、actor 对想象状态过拟合、不兼容 replay 统计和保留学习率过大。

这是一条可执行的负结果：先冻结 actor 检验世界模型，再冻结世界模型并用较小、干净 replay 检验 actor，然后才考虑另一条混合 5,000 次更新。 [协议、失败与原始指标](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/README.zh-CN.md)。

<a id="benchmark-gaming-audit"></a>
### 从“评分漏洞”到“榜单投机”：高分究竟识别了什么

> **TL;DR：** 机器人榜单不需要篡改 scorer 也能被“hack”——模型可以不学榜单声称要考的能力，只利用任务编号、固定测试分布或贴近测试的训练数据，仍然拿到高分。
>
> **例子：** LIBERO 本来想考“机器人能否读懂指令并完成操作”，但一个不读语言、只查 task ID 的约 0.09B DINOv2+MLP，在 Spatial/Object/Goal 上仍得到 99.0%/100.0%/98.8%。这就像声称考阅读理解，学生不读文章，只记住“第 3 题选 B”也能拿满分。
>
> **它证明** LIBERO 总分本身不能证明语言理解能力。**它不证明** 高分 VLA 一定没有语言能力，也不证明所有 benchmark 都无效。对 DexLab，先审计 scorer，再做“去掉声称能力”的最小探针和训练支持内重采样，最后才扩展 persistent contact sequence。

Jiang 等人的 [What Are We Actually Benchmarking in Robot Manipulation?](https://arxiv.org/abs/2606.04233)（CoRL 2026 Oral, Best Paper Award Finalist）并不是在证明“所有榜单都造假”。它更严格的结论是：**总分可能同时由目标能力、任务捷径、长期适配的窄测试分布、训练数据距离和统计噪声产生，因而高分未必能唯一识别所声称的能力。** 这与直接改 scorer 是两个层次：先问 evaluator 是否接受伪完成，再问协议是否允许不具备目标能力的系统得高分。

| 诊断 | 论文的最小反证 | 被破坏的榜单解释 |
| --- | --- | --- |
| 缺失能力探针 | LIBERO 上约 0.09B 的 DINOv2+MLP 不读语言，只用 task-ID embedding；Spatial/Object/Goal 为 99.0%/100.0%/98.8%。 | “高分必然证明语言理解、大模型或广泛泛化”不成立。这不证明高分 VLA 没有这些能力。 |
| 可检测性与配对统计 | 从只有总分的记录构造 paired Wald 方差上下包络，分成必然显著、必然不显著与无法判断。 | “新分数略高就是真进步”不成立；无法判断也不能偷换成已证明不显著。 |
| 训练支持内重采样 | CALVIN 保持同一 1,000-sequence manifest，只重采样训练范围内 block pose；X-VLA/GR-1/RoboFlamingo 的 ATC 下降 1.027/0.749/0.498，95% CI 均不跨 0。 | 长期调参可能适配了窄测试分布。只换 sequence manifest 影响很小，当前证据不支持强样本记忆解释。 |
| 数据来源依赖 | SimplerEnv 中，每任务 120 条贴近官方 grid 的脚本仿真 demo 训练 22M policy，合计 91/96；X-VLA 报告 92/96。 | 同一总分未必证明从真实 BridgeData V2 到仿真测试的跨域泛化。这是有意偏向测试域的存在性反例，不是公平模型排名。 |

对 DexLab，不应以又加一个总分来回应这些结果。当前 [Discussion #302](https://github.com/huangkiki/Dexlab/discussions/302#discussioncomment-19558057) 的最小顺序是：

1. 保留 region/tolerance、事件顺序、idle、隐藏支撑与 state injection 的 **scorer mutation audit**，先确认评分语义。
2. 对每项声称的语言、视觉、触觉或手内能力，去掉该信号，或用 task ID、固定动作、特权状态替代。若仍接近原分，只能声称完成了当前测试分布。
3. 在已声明的训练支持内重采样物体初姿、支撑高度、相机、接触初态与语义对称条件；这与故意制造 OOD 应激分开。
4. 披露训练数据是否共享资产、scene template、seed/grid、仿真器或生成器；评测前冻结实例、分母和独立统计单位，保存逐 episode/run 的成对结果。

这些诊断是单向反证：找到捷径能否定“分数必然证明能力”，未找到当前捷径不能完成 benchmark validity proof。RoboCasa/RoboTwin 2.0 的简单探针明显落后于榜首，只能说它们没被这一探针破掉。当前方案仍是设计输入，没有启动 DexLab 新实验。

### 对 DexLab 的具体取舍

DexLab 已有独立评分、解析斜面、接触保持和任务/诊断分离的记录。本次调研补充的是：怎样给这些结果提供更明确的比较轴，以及哪些外部证据能够改变下一步决策；不把现有工作重新包装成一套新平台。

| 借鉴顺序 | 对应缺口与最小验证建议 | 通过后能说什么；仍不能说什么 |
| --- | --- | --- |
| **先审计评分与能力可识别性** | 基于当前 Wuji / LIBERO 记录准备合理成功和伪完成反例；再去掉一项声称能力并做一个训练支持内重采样，保存逐实例配对结果。 | 可说明已检查反例下判据符合任务意图，且当前最小捷径未复现；不能说明所有漏洞已穷尽或能力已被完整识别。 |
| **再建立接触机制的误差—成本对照** | 在已有合格案例上分开改接触模型、步长或容差；保留绝对误差、敏感性、耗时和全部失败。 | 可说明条件内的数值/任务取舍；不能推为全引擎或真实材料排名。 |
| **有批量运行需求时检查并行影响** | 冻结设备、版本、输入和随机性，改变批量规模并重复独立运行；把记录开/关作为受控变量。 | 可界定该软件栈和场景的稳定区间；不能从终态差异直接断言某个 GPU 内核是原因。 |
| **评分可靠后做短连续序列** | 保持→卸载/重建接触→释放；明确环境、控制器、策略和传感历史的重置边界，以整条 run 统计。 | 可检验错误如何跨阶段积累；不替代既有手内滚动/换指验收。 |
| **具备真实参照后检验选择价值** | GAUGE 式重复测量与 SIMPLER 式多策略配对分开设计，留出条件，报告不确定度。 | 可检验具体物理量或策略排序的外推；无真实记录时保持未验证。 |

这些是候选设计，执行时仍需遵守 DexLab 已冻结的适用引擎矩阵、资源预算与完整验收；一个小例子不会缩小原有义务。现阶段暂缓引入完整家庭任务库、统一替换后端或把各种指标压成一个总分。如果已有评分在有力反例下可靠，而主要误差出现在柔性物体或真实策略排序，优先级才应转向相应的材料测量或 sim/real 配对。

### 发布状态、源码核查与证据边界

前一轮广度调研读取了论文相关章节、官方项目/评测文档及下列固定版本关键文件，未安装运行这些外部 benchmark、复测排行榜、训练策略或做硬件实验。2026-11-12 增补另外通读 Manipulation Benchmark Audit 全文/附录，并复算其当前公开 CPU 统计产物；没有重跑 policy、仿真 rollout 或真机。表中多数广度条目只核查官方描述，未逐项审计完整实现；“源码可见”也不等于“本轮运行通过”。

GAUGE 的 [Hugging Face 数据仓库](https://huggingface.co/datasets/InternRobotics/GAUGE-Dataset/tree/main) 可见资产、轨迹与元数据目录；本轮只核查目录，未下载或校验全量数据。其 GitHub 快照仅有说明、许可及媒体，README 仍写评测工具待发布，因此可以研究协议和数据组织，不能称为已核实可直接运行的完整工具链。ContactBench 1.0 则已存在官方项目页链接的仿真仓库：README 列出 22 个基础任务对应 73 个可运行行、另一个仅场景任务，并明确不含策略学习/评估管线；这些发布说明不等于本轮复现，也不能与论文的 36 项参考任务等同。

| 固定快照 | 本轮检查位置与用途 |
| --- | --- |
| [SimBenchmark `3fd1764635`](https://github.com/leggedrobotics/SimBenchmark/tree/3fd17646352f4c1c2c3108f93dae00f2a2d60097) | `benchmark/include/RollingBenchmark.hpp`、MuJoCo rolling 实现：解析速度误差和耗时记录。 |
| [ContactBench `76fd04b814`](https://github.com/Simple-Robotics/ContactBench/tree/76fd04b8149fbc9360ff3a4fd2454c0fc7011c02) | `contact-problem.hxx`、`examples/cube.py`：不同互补性量与场景入口；论文采用 v3（2024-07-21）。 |
| [GPUSimBench `7d39254e66`](https://github.com/zhanghuzhenyu/gpu_sim_bench/tree/7d39254e6642bef924166ac74e7c6940c713a471) | 公共默认值、MuJoCo Warp 计时、Genesis 斜面脚本；论文采用 v1。没有据此断言所有后端默认参数已等价。 |
| [GAUGE `5a6207c22d`](https://github.com/InternRobotics/GAUGE/tree/5a6207c22d1dc0bf321369875963e7fa259bcbfb) | 仓库树、README 与论文 v1 的 §3、附录 B：发布范围、观测与误差定义。 |
| [DexGraspBench `d9ea6cf282`](https://github.com/JYChen18/DexGraspBench/tree/d9ea6cf282de1f463c20fa54b4f68d7025bad40e) | `eval.yaml`、`fc_mocap.py`、`tabletop_mocap.py`：主分支阈值、六向外力与桌面评测入口。 |
| [ContactBench 1.0 仿真 `f51f6aab24`](https://github.com/Michaelwyx/contactbench-sim/tree/f51f6aab24ac72c8b4435643efe058c07d73c735) | 仓库树及 README：任务/变体、机构参数来源与策略管线发布边界；未审计全部机构实现。 |
| [HandsOn `fee28452fa`](https://github.com/TsinghuaC3I/HandsOn/tree/fee28452fa50d3ee906445f1717ce2449cc83798) | README、评估边界文件：区分原论文任务、PhysX/Wuji1 示范与后续 Newton/Wuji2 扩展；阶段结论归于论文报告。 |
| [SIMPLER `eddb569074`](https://github.com/simpler-env/SimplerEnv/tree/eddb5690749a1e34267807c0f7b5eede323918d7) | `simpler_env/utils/metrics.py`：Pearson 与 MMRV；未把相关性解释为参数标定。 |
| [CALVIN `fa03f01f19`](https://github.com/mees/calvin/tree/fa03f01f19c65920e18cf37398a9ce859274af76) | `evaluate_policy.py`：默认 1,000 条序列、最多 5 个子任务、环境与模型不同的 reset 位置。 |
| [Manipulation Benchmark Audit `a5ad04ab0f`](https://github.com/ripl/ManipulationBenchmarkAudit/tree/a5ad04ab0f26d46680c4d1c24911c728d37f7d16) | `CLAIMS.md`、claim-to-artifact map、逐 episode/sequence 摘要与统计代码；本轮 `recompute_claims.py` 和 `validate_release.py --skip-exact-inputs` 通过。arXiv v1 的 LIBERO 19.8% 与 camera-ready 产物 144/789 = 18.3% 分开引用。 |

与本次迁移判断直接相关的 DexLab 基线是 [`4867a8637b`](https://github.com/huangkiki/Dexlab/tree/4867a8637b5999f4169a6dd8a36ecf6ffdede989)：`docs/current-work.md`、`incline_score.py`、`pinch_score.py` 和 `libero_score_v2.py`。其中 LIBERO v2 明确把记录与数值诊断同物理有效性、学习策略评价分开。本专题延续这些边界；不改变原 38 篇论文、19 个仓库的历史计数。

<a id="corl-2026-dexlab-lessons"></a>
## CoRL 2026 录取论文：DexLab 最应该先学什么

> **TL;DR：** 这届最值得 DexLab 学的不是又一个大 VLA 或 GPU 引擎，而是三个能让当前结果更可信的机制：**用 seed 分布和方差分解决定评测预算；把低速精密修正与持续接触力分开诊断；先校准接触事件的时间和误报，再追求稠密触觉或更复杂形变。**
>
> **一个连贯例子：** 评测以太网插头插入时，seed 冻结初始偏差、间隙、支撑和摩擦档位；日志分开接触进入/退出、微小动作、力历史和首个失败层；按到达→对齐→插入→坐实评分；最后用 seed 方差与同 seed 试次方差决定增加场景还是增加重复。
>
> **证据边界：** 这些是论文和官方项目的静态精读结论；本轮没有重跑作者代码、真机或 DexLab 新实验。

### 筛选方法

2026-11-12 按 [CoRL 2026 官方录取页](https://2026.corl.org/program/accepted-papers) 逐项筛查 687 篇录取论文，先按任务/接触、本体/执行、物理、观测、数据/策略、真实验证六层筛选，再精读与 DexLab 当前缺口最相关的论文。已经单独整理的 Manipulation Benchmark Audit、SuperMimic、RLT/CAP 等不重复冲高本次推荐数。优先级依据是“能否改善物理失败归因、评测可识别性或 sim/real 证据”，不是 oral/spotlight 头衔或模型规模。

### 优先借的五个机制

| 顺序 | 工作与作者证据 | DexLab 应该借什么 | 不能借题发挥的结论 |
| --- | --- | --- | --- |
| **1. 随机挑战评测** | [Benchmarking Real-World Robotic Manipulation through Stochastic Challenges](https://arxiv.org/html/2611.12804v1)：两个实验室、Spot/Stretch、568 次真机试验；区分 seed 难度方差与同 seed 试次方差。 | 保存 `seed → task → repeat → outcome`；在实验前声明最小重要差值、显著性和 power；方法间优先保留配对 seed。 | KALLAX 任务不是灵巧接触物理标定；不同团队的场景重建方差未测，成功标签仍需审计。 |
| **2. 先分开精度失败与力失败** | [Demystifying When and Why VLAs Fail in Contact-Rich Tasks and How to Fix Them](https://arxiv.org/html/2608.01402v2) (FACT, Spotlight)：5 项真机接触任务、约 2,500 rollouts；报告 FACT 平均 66%，最强对照约 40.5%。 | 日志增加低幅动作分布、接触进入/退出、当前力与力历史；用 first-failing-layer 区分“没对准”和“对准了但没维持正确力”。 | 作者结论依赖单一机器人/F-T 传感器，低噪采样分析与力注入都与具体架构相关；不支持“多加力通道必然有效”。 |
| **3. 先校准接触事件，再造稠密触觉** | [Blind Dexterous Grasping via Real2Sim2Real Tactile Policy Learning](https://arxiv.org/html/2606.11767v2)：用真实接触 onset/offset 校准 SDF 阈值和 penalty；onset 误差从 426 ms 降到 96 ms，FPR 从 4.2% 降到 2.2%。 | 对已有 pinch/hold 记录先做事件级对齐：接触进入/退出时间、F1、FPR，并保留空抓、滑移、脱落三类失败。 | 论文真机总抓取成功率仅 27%（seen/unseen 各10 件、每件 5 次）。它证明校准改善事件一致性，不证明已解决稳定抓取。 |
| **4. 参数化柔性任务与分阶段评分** | [WireCraft](https://arxiv.org/html/2606.18097v3) (Spotlight)：连接器插入、clip routing、channel seating；铰接链/FEM 线缆，仿真与 UR5 数据。 | 借“到达 vs 插入/坐实”分阶段指标，为切割、绳/线操作冻结几何、难度轴和失败类型，再记录载荷与损伤代理。 | 两种线缆模型都未与真实线缆定量标定，力未验证，真机只覆盖一台 UR5 的选定设置；不能称为物理保真已证明。 |
| **5. 用消融证明“广度先验”与“精密微调”的分工** | [Play2Perfect](https://arxiv.org/html/2606.26428v4) (Oral)：无任务 dexterous play 预训练后做稀疏奖励精密装配；作者报告比 scratch 省 33× 样本。 | 学它的对称消融：物体/接触多样性先验、精密接触任务微调、不同公差和阶段成功分开评估。 | 主成功容差为 1 cm，紧配合实验是另一组机械间隙；真机试次少，任务依赖位姿跟踪和外部技能编排，不是完整自主装配管线。 |

### 有条件借鉴，不是当前第一顺位

| 方向 | 候选工作 | 触发条件 |
| --- | --- | --- |
| 触觉 policy 时间角色 | [PACE](https://arxiv.org/html/2610.16308v1) (Oral) 将慢变持续接触状态、突发事件与未来接触后果分开。 | DexLab 真正训练 chunk policy 时；现在可先按三种时间角色记日志，不急着复制网络。 |
| 低成本外力估计 | [FACTR 2](https://arxiv.org/html/2606.12406v2) (Oral) 从电机力矩减去学习的自由空间逆动力学，估计外部关节力矩。 | 做 HIL/真机采集且没有 F/T 传感器时；绝对力标度仍需外部标定。 |
| 统一触觉表示 | [UniVTAC](https://arxiv.org/html/2602.10093v1) 覆盖 3 种传感器、8 任务，报告仿真编码器平均 +17.1%、真机三任务 43.3%→68.3%。 | 已经有两种以上真实触觉传感器与统一任务时；当前 60 次真机 rollout 与人工判分不足以代替物理校准。 |
| 柔性物体预测与不确定性 | [PGRD](https://arxiv.org/html/2607.13451v1) (Spotlight) 用可优化弹簧质点模型+残差速度 Transformer；[CORD-SLS](https://arxiv.org/html/2606.14188v1) (Spotlight) 用平滑接触可微仿真和 conformal uncertainty 做绳/布 MPC。 | 切割/绳/布成为当前主线时；残差轨迹精度不等于材料/力可识别，接触平滑梯度不等于原始刚性接触梯度。 |
| 引擎与工具链 | [Kamino](https://arxiv.org/html/2603.16536v2) (Spotlight) 针对含闭环约束的 GPU 并行多体；[RoboKit](https://github.com/OpenRoboKit/RoboKit) 提供 batch/differentiable kinematics 与优化器。 | 只在实际遇到闭环/模仿关节瓶颈，或需要统一批量运动学目标时审计；它们不直接解决当前 scorer 和接触证据缺口。 |

### 对当前 DexLab 顺序的影响

CoRL 2026 没有推翻当前顺序，而是把它补完：

1. **scorer semantics audit 仍然第一。** 如果伪完成也能得分，更大的 $K$ 只会更精确地估计错误量。
2. **通过后立即保存分层、配对原始结果。** 从一个小型先导批估计 seed 方差与试次方差，再冻结预算；不把这一步冒充新实验已获批或已完成。
3. **短 persistent sequence 沿用同一合同。** 保持→卸载/重建接触→释放的整条 run 才是独立统计单位；链内各帧、接触或阶段不能冒充独立样本。
4. **暂不引入新大引擎/大任务库。** 只当当前 scorer 可靠，且 first-failing-layer 明确指向闭环约束、柔性物体或触觉表示时，再启动 Kamino、PGRD/CORD-SLS 或 UniVTAC 的定向复现。

本专题是官方录取清单筛选与优先论文全文审读。表中数字是作者报告，没有作为 DexLab 实测数据；除公开项目页/仓库外，本轮没有安装运行外部系统。完整统计推导、3 张图和 2 张表已另行保存在 Obsidian 的 `StochasticChallenges` 笔记。

<a id="robodojo-astra"></a>
## RoboDojo / Astra：把模型、动作执行和评分分开

**2026-11-11 蒸馏：[完整专题与核查入口](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#robodojo-astra)。** 最值得借鉴的是动作回执和受控扰动诊断。这项工作让语言模型选择末端目标，固定的非学习程序完成检查、路径转换与插值，最后由环境判分；它支持研究通用模型的动作闭环，尚不足以支持替代快速、连续的接触控制。

以夹起剪刀为教学例子：模型估计位置并请求移动，工具层执行，下一轮用实际到达位置和图像纠偏，再闭爪、抬升。当前[源码](https://github.com/RoboProbe/RoboProbe/blob/3c0bc68383a75bf3fa2d7bfc5ab1d1241c7e171e/policy/RoboDojo_Agent_L3_Inspect_EEF/policy.py#L545)还安排先移臂、后改变夹爪并同步双臂。“没有 VLA”不等于没有控制先验；25 Hz 轨迹执行也不等于模型以 25 Hz 闭环决策。

从公开[逐布局 JSON](https://github.com/RoboProbe/RoboProbe/blob/3c0bc68383a75bf3fa2d7bfc5ab1d1241c7e171e/results/l3_inspect_eef_official_2100/astra_task_layouts.json)复算，42 项、2,100 次试验中成功 472 次，五维等权 SR 为 22.48%、过程 Score 为 28.97；精度 SR 只有 4%，长时序 8.25%，16 项任务没有成功。过程分和完整成功率应分别解释。作者[报告](https://robodojo-benchmark.com/report/gpt-6-astra-eval#zero-shot-real)的真机试验因不安全动作和设备损坏中止，没有完成官方 18 任务协议。

解释比较还需保留三条边界：

- [论文 §3 与附录 H](https://arxiv.org/html/2609.24170v1#S3)说明 LLM 收到了 wiki 任务说明和阶段评分提示，公开 VLA 没有在同等输入下重跑；主结果为单种子。
- 论文写默认 100 次调用，当前[结果说明](https://github.com/RoboProbe/RoboProbe/blob/3c0bc68383a75bf3fa2d7bfc5ab1d1241c7e171e/results/l3_inspect_eef_official_2100/README.md)与代码写 170，并披露两个任务的定向重跑。必须按实际记录恢复配置，不能混成一个历史条件。
- [附录 C/D](https://arxiv.org/html/2609.24170v1#A3)的单示范结果不代表少样本学习普遍无效；扰动选择了原本成功的八个布局，没有历史消融或同扰动 VLA 对照，取反后的工具边界也提供线索。纠正动作不自动证明历史学习或独有的适应能力。

### 烤面包案例：闭爪命令不等于有效夹持

2026-11-12 的一批离线 Code-as-Policy 运行覆盖 100 个不同 seed/layout 工况，成功 19 个。81 个失败的回合级归因中，79 个是策略执行问题、2 个是策略机械问题；不能用两个掉落片段把整批失败改写为仿真器失败。但两个局部事件揭示了同一个可观测机制：闭爪命令持续为 `0`，双指法向冲量却从约 0.25 N·s 降至接近 0，之后空夹爪继续闭合。

[完整同步视频、接触曲线和能量边界](https://huangkiki.github.io/Dexlab/zh-cn/latest/robodojo-bread-slip.html)区分两种失效。layout 002 的上缘浅夹持被相邻面包和货架接触放大，面包绕接触边滚出；layout 011 没有释放前的明显外碰撞，面包直接从离质心约 4.42 cm 的上缘接触滑落。第一优先级是加深抓取、拒绝窄夹持并做低速试提；仿真侧再读回 finger–bread 材质 pair、combine mode、切向冲量与接触面积，并对刚性薄片和顺应性代理做匹配 A/B。当前 0.07 kg 刚体面包没有压缩、粗糙度或指垫顺应性，这会放大边缘接触的突变，但尚未建立 PhysX 求解器错误、真实面包标定或跨引擎排名。

独立的 2026-11-13 v67 批次成功 65/100；35 个失败中有三个入槽接触逃逸。搬运阶段没有先掉片，异常从槽口卡滞开始：`s1/l026`、`s1/l049` 先停在目标上方 19/28 mm，继续向下后，观测关节 FK 的 TCP 却在 40–44 ms 内向上移动 10.6–28.3 cm；`s0/l025` 在首个深压动作内发生同类逃逸。固定实现证明这是真实仿真状态，不是 IK 回退；但高刚度主动驱动本身会做功，且缺逐步驱动力矩、接触冲量和穿透记录，所以当前根因写作“槽口卡滞后的主动控制—刚性接触耦合失稳”，A/C/N 的内部归因仍为 U，不能直接写成 solver 凭空注入全部能量。

DexLab [已有 Poke 适配](https://github.com/huangkiki/Dexlab/blob/4867a8637b5999f4169a6dd8a36ecf6ffdede989/docs/roboapi-poke.zh-CN.md)具备会话与工具回执，但任务观测和动作映射仍需逐项接入。结合[当前评分审计方向](https://github.com/huangkiki/Dexlab/blob/4867a8637b5999f4169a6dd8a36ecf6ffdede989/docs/current-work.zh-CN.md)，先在一个合格案例保存观测、请求、工具处理、实际执行、到达误差和独立评分，再比较完整历史与仅当前观测，在固定提示、转换和双重预算下加入一种坐标偏差。分别检查语义选择、运动到达、接触保持与释放，并保留失败、超时、主动放弃、基础设施错误和成本缺失。这是待验证设计，没有启动实验；暂不扩任务榜单或新建代理框架。

核查于 2026-11-11：论文 v1、当日报告和 RoboProbe `3c0bc68383a75bf3fa2d7bfc5ab1d1241c7e171e`。本轮做了静态源码核对和已发布结果的算术复算，没有重跑模型或物理任务。原始采集、预算版本对应和跨仿真器/真机泛化仍未独立验证；134 个已评分 Astra episode 的成本 transcript 缺失。槽位保留真实布局 ID，其中 13 个 ID ≥ 50。钢琴及其他本体案例不并入主榜；原 38 篇论文、19 个仓库统计不变。

(robodojo-simulator-audit)=
## RoboDojo 仿真可信度审计：先证明仿真收到参数，再讨论 Sim-to-Real

**2026-11-18 蒸馏：[完整讨论与最小验证门槛](https://github.com/huangkiki/Dexlab/discussions/388)。** [What does RoboDojo really simulate?](https://p-b-p-b.github.io/blog/2026/what-does-robodojo-really-simulate/)（Bo Peng, Wenhao Chai, Zhifei Li）没有先比较模型，而是沿四个可独立失效的关卡检查 RoboDojo 的 Isaac Sim 仿真端：

`对象与真机规格 → 任务参数/资产 → 引擎运行时读回 → 数值与求解检查 → 接触/物体响应 → 任务评分`

这里最重要的认识是：**“配置里有这个值”“脚本无报错”“画面看起来像”和“评分给了分”，都不等于仿真在计算任务声称的物理。** 当失败来自参数未送达或评分漏检时，继续调策略、加域随机化或换迁移算法只是在下游放大错误。

### 用一个木琴任务看评分缺口

任务说明要求琴槌实际击打八个琴键，但当前评分主要检查琴槌的 `beat` 点是否位于琴键上方，`z` 在 `0.01–0.036 m` 内，没有要求接触事件或冲量。[源码 L19](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/fbfbbcb3801397fa00dcffaef3ca64d97c3fe76f/task/RoboDojo/tasks/play_Xylophone.py#L19)

因此，让琴槌依次从所有琴键上方掠过、实际接触为零，也能累计击打阶段。[作者运行负例](https://p-b-p-b.github.io/blog/2026/what-does-robodojo-really-simulate/#scoring) 这说明失败首先位于“评分是否检查任务”，早于“策略是否会工具操作”。相似地，瓶子任务说明要求拿起放入箱中，阶段分却只检查瓶体位于箱体上下范围。[源码 L26](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/fbfbbcb3801397fa00dcffaef3ca64d97c3fe76f/task/RoboDojo/tasks/put_bottles_into_dustbin.py#L26) 作者报告直接把三个瓶子推落可拿 `40`，不做任务直接退出可拿 `100`，木琴悬空扫过可拿 `100`；修正检查后三种捷径均为 `0`。

### 四道前置检查

| 关卡 | 要问的问题 | 最低证据 |
| --- | --- | --- |
| 参数送达 | 配置里的摩擦、质量、惯量、限位和控制参数是否进入引擎？ | 配置值、资产导入值、运行时读回、生效时刻和一次可观测响应。 |
| 数值可能性 | 这些值是否能对应现实物体或本体？ | 尺寸、密度、质量、惯量、关节范围、驱动力和控制器限幅。 |
| 求解与守恒 | 改变不应改变结论的数值条件后，响应是否保持？ | `dt`/`dt/2`、重复运行、批量对照，以及穿透、冲量、速度和能量账。 |
| 评分语义 | 分数检查的是任务，还是接近目标等代理量？ | 真实完成的 positive control；idle、无接触、隐藏支撑、错误 carry/reset 等 negative controls。 |

原文的瓶子案例还给出了一条完整的非物理时间线：钢瓶从 `0.92 m` 释放，以约 `3.0 m/s` 落入箱内；首次接触时它已进入被压在箱底的轻瓶内部，并在单个 `4 ms` 步内反转为向上 `3.5 m/s`，升到 `1.06 m`，比释放点高 `0.14 m`，最后落到箱外。**现有证据支持的第一失效层是接触/求解计算产生了非物理响应**；质量、惯量和未送达的摩擦可能是放大器，但修正设置后反弹仍能复现，因此不能把默认摩擦单独写成主因。下一步应读回每步接触距离、法向冲量、速度修正、求解迭代与步长对照，在没有这些量前把内部机制保留为待定。

### DexLab 先学哪一步

不要先扩大榜单、换引擎或给模型重新排名。先在一条已有合格记录上补齐四张短表：参数请求/读回、数值 plausibility、`dt` 与能量对照、evaluator 正负控制。用“面包滑落”或“入槽接触逃逸”都行；只有现有日志缺少的量才补采。

如果参数未送达，先修数据与场景生命周期；如果数值明显不可能，先查资产和本体参数；如果相同输入在不同步长或批量下给出相反响应，先查接触与求解；如果评分接受伪完成，先修 evaluator；上述都正常而固定输入下仍有可重复的非物理响应，再做接触标定或求解器对照；只有仿真链路和真机测量都可信，剩余差异才属于材料、感知或 Sim-to-Real 迁移。

作者深读 3 个任务，其他 51 个只做轻量检查；数值参照来自规格表和现实物体，不是真机测量；修复对照使用 20 个 layout 和手写解。这些结果支持“评测链有可复现缺口”，不支持“54 个任务全部无效”，也尚未证明某个特定 Isaac Sim/PhysX 参数是全部异常的单一根因。本轮静态核对了 RoboDojo `fbfbbcb3801397fa00dcffaef3ca64d97c3fe76f` 的部分源码，没有独立重跑 Isaac Sim、作者修复或任务策略。


<a id="robocoliseum"></a>
## RoboColiseum：回放动作、检验响应，再比较完整任务

**最值得借鉴的是把仿真可信度与模型评测接起来。** 先固定真实发出的动作，让仿真自己算出机器人和物体的响应；再用独立条件检验拟合是否有效，最后在明确预算内比较完整任务。平台的场景规模与榜单不应替代这条证据链。[完整讨论与取舍](https://github.com/huangkiki/Dexlab/discussions/329)

以“抓起杯子、转向、放下”为教学例子：记录关节与夹爪目标，同时保留实际到达、接触建立、持物和释放。如果逐帧写入杯子位姿，只能复现画面；让它通过接触动力学自行运动，才能检查同一输入是否产生相近响应。该例不是作者新增实验。RoboColiseum [平台报告 §1](https://robocoliseum.ai/techreport/robocoliseum#en-sub-1-1)描述约 100 Hz 指令回放与 1 ms 物理子步，并把源后端拟合、冻结参数迁移和目标后端适配分开。

### 三个值得迁移的区分

| 区分 | 为什么会改变判断 | DexLab 应保留什么 |
| --- | --- | --- |
| 控制、接触与观测残差 | 强位置反馈能掩盖动力学误差；像素偏差也可能来自相机 | 请求与实测响应、接触事件、观测有效掩码；有效拟合参数与实测材料参数分开 |
| 物理状态与渲染 | 改外观可以不改接触，但接口相同不保证动力学等价 | 状态所有者、坐标系、时钟、控制与求解配置；跨引擎结论必须保留参数转换与重新拟合条件 |
| 进度、完整成功与成本 | 子步骤得分、整段任务完成和资源消耗回答不同问题 | 原生评分、完整成功率、推理调用、发出/实际完成的步数、仿真时间与墙钟，保留失败和超时分母 |

平台 [§1.4](https://robocoliseum.ai/techreport/robocoliseum#en-sub-1-4)报告 16 项任务、22 组机器人—任务配对的 Pearson `r=0.9686`；[配对图](https://sim-challenge-frontend.ks3-cn-beijing.ksyuncs.com/reports/robocoliseum/figure-fa13c3bb2eab.png)的拟合为 `sim=0.913×real+0.054`。这支持已测配置下的分数相关性，不能推出每项误差小于 10%，也不证明固定任务内的模型排名或新任务预测可靠。后两者需要独立留出条件、逐项误差和不确定性；校准一个砝码不能保证整台秤全量程准确，类比只用于说明拟合与验证的分离。

### 多引擎接口之后，还要追反作用与时序

报告 [§2.3](https://robocoliseum.ai/techreport/robocoliseum#en-sub-2-3)说明 CPU MuJoCo 推进机器人，连杆状态驱动 libuipc 物体/柔性接触，IPC 接触力不回传 CPU。核查的 Genie Sim `083793f23876` [driver](https://github.com/AgibotTech/genie_sim/blob/083793f238762d336ce8570d22118a60a6830875/source/geniesim_ros/src/ros_ws/src/genie_sim_engine_libuipc/genie_sim_engine_libuipc/driver.py#L309)已支持可选同步屏障与刚体代理：上一完成时刻的物体状态送入 CPU，本地代理接触可影响机器人，再把机器人状态交给 IPC。这不等于 IPC 原生反力回传或同一步联合求解；默认异步 `latest` 与显式 `barrier` 也不能混为同一时间协议。

因此，拉布料的形状演示可以有价值，但要研究布料拉力如何拖慢手、改变腕力矩或触发失握，必须另查反作用如何进入机器人动力学。统一接口、更多子步和漂亮画面都不能替代这个证据。

### 评测协议随难度变化，历史结果要保留

Season II [§3.3](https://robocoliseum.ai/techreport/robocoliseum#en-sub-3-3)描述 Agent 与 VLA/WAM 分榜、固定官方集与动态检查集、执行/推理预算及完整完成奖励；动态集不进入总分。它提供了比单一进度榜更完整的方向，但服务器具体阈值、原始结果与评分版本仍是复算所需条件。不要把 Season I 与 Season II 混成同一排名。

[Agent2Act v1 §III-A](https://arxiv.org/html/2610.27865v1#S3.SS1)的主实验按任务等权聚合子步骤分，每个 case 运行一次；这不是完整成功率或重复运行稳定性。其[执行层](https://github.com/AgibotTech/genie_sim/blob/083793f238762d336ce8570d22118a60a6830875/source/agent2act/docs/architecture.md#a-pure-motion-request)检查并转换模型动作，以后续观测形成反馈，环境独立判分。工具接受、发出动作和物理完成应分别记录。

**DexLab 的优先顺序：先沿用评分语义审计，把一条已有合格记录的输入—响应—接触—评分链整理清楚，再设计独立条件和双重预算。** 缺少实机数据时，内部一致性可以研究，但不称为 Real2Sim 标定。暂缓整个平台迁移；只有第一失效层明确需要新材料或接触能力时，再按既有 UniSim 分工论证接入。本轮为 2026-11-13 的报告、图表与固定源码核查，没有运行外部模型/仿真或改变 DexLab 物理实现；原论文与仓库筛选统计不变。


(coap)=
## COAP：可审计状态、任务程序与首次失效层

**2026-11-16 蒸馏：[完整讨论与验证门槛](https://github.com/huangkiki/Dexlab/discussions/335)。** [Code-Only-as-Policy（COAP）](https://arxiv.org/abs/2610.12369)最值得 DexLab 借鉴的，不是“纯代码策略在 RoboDojo 超过 VLA/Agent Harness”，而是把状态、任务逻辑和诊断改动组织成可审计对象。它不构成替换现有仿真后端或验收协议的证据。

沿用已有的烤面包失败案例：闭爪命令持续为 `0`，法向冲量却衰减，面包从浅夹持处滑落。COAP 式表示会进一步把请求、实际到达、指—物相对位姿、接触建立/丢失、持物检查、搬运速度和任务阶段放进同一条状态链。这样“加深抓取”“拒绝窄夹持”“低速试提”“接触参数失配”才不再混成一句“策略失败”。该例是解释，不是新增作者实验。

### 三个可迁移机制

1. **显式状态不是多存变量，而是让决策前提可审计。** COAP 分别保存机器人、环境和任务状态；测量记录带来源、误差与时间，动作由代码从这些值推出，而不是继续藏在模型权重或上下文里。
2. **任务逻辑与共享原语分开。** 任务程序规定子目标顺序、参数、恢复和终止；共享层提供感知、运动与抓/搬/推/放等操作。DexLab 不需要照搬代码库，但应保持任务、控制、接触读回和评分各自的状态所有权。
3. **改动要经过兼容性和留出验证。** 作者让 coding agent 读取失败状态、生成完整可运行 diff，在分支上做数值与运动学检查，再以超过重跑噪声的验证改进决定是否合并；共享代码优先通过默认关闭参数扩展，旧调用路径保持不变。

论文在 RoboDojo 的 42 个仿真双臂任务上报告 70.24% SR，最强 WAM 为 29.64%、最强 VLA 为 27.96%；新任务运行的代码约 83% 来自共享库。失败分析把 62% 归到状态测量、37% 归到代码逻辑（作者按“最小的可阻止改动”分类）。这些是作者在公开 benchmark 配置下报告的结果，不是跨本体、跨引擎或真机常量。

### 必须保留的证据边界

- 全部结果仍在仿真中；相机参数、机器人 mesh、物体尺寸和桌面高度是 benchmark 常量，真机仍需重新测量与接触调参。
- 每项任务仍需少量专门代码和离线开发、验证成本；70.24% 不等于零样本完成任务族。
- 失败类别是作者为诊断设定的单一“最小修复”标签，不是感知、控制器、接触求解和评分漏洞的独立物理根因占比。
- 在已检查版本与公开 GitHub 搜索范围内未见作者代码库，不能把论文结果称成本轮已复现。
- 与当前 RoboDojo/Astra 的输入、调用预算、模型和评分版本不同，不能仅凭总分形成同条件策略排名。

### DexLab 的最小验证

先选“面包滑落”或“入槽接触逃逸”中的一条已有合格记录，不改任务与评分，只补：

`任务阶段 → 请求动作 → 实际到达 → 接触/夹持状态 → 物体六维响应 → 判分`

关键量至少带 `value / source / time / uncertainty`，并区分 commanded、measured、estimated 和 scored。然后用同一初态改变一个变量，例如抓取深度或搬运速度。最小验收不是成功率变高，而是首次失效层更明确、同配置状态链可复算、失败分母完整，且改动未污染旧任务路径。

若这条链不能改善归因或复现，就不应继续建共享代码库；若主要误差来自评分或物理响应，优先级仍回到 scorer audit 或接触标定。只有当显式状态与受控改动稳定后，才讨论扩展到更多任务。暂不采用全自动 RSI、通用 task library 或用代码成功率替代物理/真机验收。

核查于 2026-11-16，论文 `2610.12369v1`。本轮读取摘要、方法、层级、失败分类、扩展/RSI 统计与限制，没有公开代码复现、模型推理、物理重跑或真机实验；原论文与仓库筛选统计不变。


(capx-aspire)=
## CaP-X 与 ASPIRE：先验证反馈，再晋升技能

**2026-11-16 蒸馏：[CaP-X 完整讨论](https://github.com/huangkiki/Dexlab/discussions/341)与 [ASPIRE 完整讨论](https://github.com/huangkiki/Dexlab/discussions/342)。** 两篇都是 Code-as-Policy，但给 DexLab 的启发应分开：CaP-X 是实验设计模板，ASPIRE 是技能记忆的准入协议。

仍以“闭爪后法向冲量衰减、面包滑落”为例。高层反馈只会留下“抓取函数已调用、最后失败”；结构化视觉差分可以说“搬运中物体先移动、后离开夹爪”；逐原语 trace 才能把闭爪命令、实际指宽、相对位姿、冲量和首次滑移放到同一时间轴。若提出“增加抓取深度并低速试提”，这仍只是候选修复；只有验证者在不看原修复代码时，凭失败签名、触发条件和修复说明在留出场景复现，才能晋升为共享技能。

[CaP-X](https://arxiv.org/abs/2603.22435)最值得借的是受控变量：API 从人工高层宏切到低层原语、单轮切到多轮、反馈从终态文本切到 RGB 或结构化视觉差分，并保留模型、提示和采样预算。作者报告高层抽象提高分数，移除后性能下降；文本化的视觉差分通常比直接交错原图更适合程序修复。因此策略比较不能只报总分，必须登记抽象层、交互轮数和反馈表达。其固定源码仍主要从成功 trial 抽取函数，评分器若接受错误成功，技能库也会固化错误。

[ASPIRE](https://arxiv.org/abs/2607.00272)进一步把逐原语 trace、修复技能、独立验证和留出评测接起来。当前公开实现要求 fresh verifier 看不到提出者最终程序，以 5 个开发 seed、最多 2 次尝试、至少 4/5 成功作为单次晋升门槛；文档同时明确，这证明文字能传递修复，不证明跨任务泛化。作者并报告细粒度执行引擎比再增加进化搜索带来更大的主要收益；进化搜索应解决明确平台期，而不是成为默认开销。

**DexLab 的优先顺序：** 先为一个已有失败案例建立反馈契约，并比较“终态/视觉进度”与“逐原语/接触状态”两种观察包的归因能力；再把根因整理成 `失败签名 → 触发前提 → 修复动作 → 适用边界 → 支持证据 → 反例/未测范围` 的 skill card；最后才评估技能库晋升、进化搜索或反向重跑。被测程序不能读取 reward、success 或 privileged state；开发与留出 seed 分开，`verified_once`、`transferred` 和 `refuted` 不得混写。

最小验收不是平均成功率上升，而是首次失效层更明确、proposal 在隔离条件下可复现、反例能阻止错误触发、失败分母不变且留出结果未回流调参。若反馈没有改善归因，先改测量选择性；若主要误差来自评分或物理，仍回到 scorer audit 或接触标定。本轮核查 CaP-X `2603.22435v2`、固定源码 `53e9966d`，以及 ASPIRE `2607.00272v2`、固定源码 `fa00f0ef`；没有运行外部 Agent、仿真、物理重跑或真机实验，全部性能数字均为作者报告。

(closing-loop-transmission)=
## 硬件限位、闭环传动与 reset：保真度不是一个开关

**2026-11-17 蒸馏：[Closing the Loop 完整讨论](https://github.com/huangkiki/Dexlab/discussions/372)。** [原文](https://kzakka.com/closing-the-loop/)处理的是 Unitree G1 脚踝：常见串行模型把 pitch 和 roll 当作独立关节，真实机构却由电机、曲柄和推杆形成两个闭链。

**最值得借的是按可观测后果逐层加模型：硬件限位 → 传动耦合 → 控制映射 → reset → 积分器/约束求解。** 例如，仿真写入一个机械止挡不允许的组合角；串行关节范围会放行，实测切角限位应拒绝。再恢复闭链后，如果 reset 只写脚踝角而不移动电机，杆长不一致会让求解器产生校正力和位置瞬态。即使 reset 一致，把脚踝位置执行器、`implicitfast` 和 4 ms 步长放在一起，闭链误差仍可能增长。每一步都新增不同的状态与首次失效层。

**不要把这个结果压成“2 ms 是安全线”。** 作者在 MuJoCo 4.0.1 上报告，闭链误差在约 2 ms 及以上开始增长；`discrete` 让约束求解与状态更新共享有效惯量，因而稳定了该模型，并非给所有模型提供普遍保证。`discrete` 下的 `qacc` 是这一步的速度差分 `(v⁺ - v) / h`，不是连续时间加速度。限位行切换、`forcerange` / `actuatorfrcrange` 饱和、armature／阻尼和接触正则化仍要分别观测。先读回精确运行时版本：MuJoCo 4.0.1 修复了 4.0.0 的稀疏 Cholesky 缺陷，该缺陷会在稀疏约束 Jacobian 上让 Newton 收敛变慢、产生错误加速度甚至发散。

DexLab 的其他步长实验提供边界，而不是 G1 复现：LIBERO 的 2→1 ms 对照把留出物理诊断从 5/10 降到 3/10，原生步进成本约翻倍；冻结抓梗基准的 h、h/2、h/4 为 2/3 通过，也不能宣称单调收敛。小步长可以减少部分离散误差，同时改变接触采样、active set 与成本。G1 实验应先固定执行器位置、力限幅和接触／限位参数，再比较步长，并记录杆长残差、实际力、`qacc/qvel`、墙钟及独立的守恒账。

| 本体的模型 | 多表示了什么 | 何时值得用 |
| --- | --- | --- |
| 串行关节 + 实测切角限位 | 近似可达域，没有电机/杆件闭链状态 | 重定向、初始训练；先固定一个简单基线 |
| spatial tendon + equality | 理想杆长、位姿相关传动、电机状态 | 力矩、惯量或控制增益会改变结论 |
| 显式 rod body + connect | 杆的质量、惯量、碰撞和端部自由度 | 这些因素进入被研究的任务或失败 |

作者报告，在其 LAFAN1 重定向中，机械限位之外的着地脚样本有 1.5% 超过 1°；对负载着地样本估算，少于 0.1% 需要单电机超过 25 N·m，因此“限位修正后的串行模型已足够做初步训练”是有条件判断。恢复闭链后，传动雅可比 `G` 使脚踝扭矩和反射惯量随位姿变化。作者还报告：同一串行训练设置中，直接给两个电机各 14.25 N·m/rad，名义站姿的等效 pitch 刚度约为 62、roll 约为 19，而训练口径为每个脚踝关节 28.5；一个 6 秒舞蹈片段、256 组配对 rollout 的失败率从约 16% 升到约 20%。这表明控制接口不能只比较同名参数，但只覆盖一个策略、一个片段和特定失败阈值。

**DexLab 的顺序：** 先给已有资产补一张“joints / tendons / equality / actuator placement / integrator / reset / soft-limit”审计表；只有当失败指向组合限位、驱动耦合或控制映射时，才做“加切角的串行基线对一致初始化的 tendon 闭环”的受控比较。reset 与积分器必须是独立变量；最终是否掉下或误差是否变小，不足以证明闭环值得。当前评分语义与 [Discussion #302](https://github.com/huangkiki/Dexlab/discussions/302) 仍是更早的判因层；这里的“闭环”是运动学闭链，不是 [#334](https://github.com/huangkiki/Dexlab/discussions/334) 所说的完整训练闭环。

核查于 2026-11-17。已读取原文、公式、表格、随文模型包和 MuJoCo 4.0.1 官方发布说明；包内五个 MJCF 都写有 `discrete`，并分别提供 serial、tendon、rod-body 以及执行器在脚踝/电机上的变体。模型包 SHA-256 为 `32eb7206e4996b7d76956590544039377fe3ec67e9387a7a2df2f7334f3529d5`。当前环境 MuJoCo 为 3.12，低于模型要求的 3.16；本轮没有运行硬件限位测量、256 组策略 rollout 或积分器扫描，因此性能与成功率仍是作者报告。文中的 DexLab 步长反例来自其他接触任务，不是 G1 复现。

(felis-policy-contract)=
## 事件触发的策略不等于权重文件：Felis 的主动脊柱与控制合同

**2026-11-19 蒸馏：[Felis 完整讨论](https://github.com/huangkiki/Dexlab/discussions/416)。** [Felis](https://frank-zy-dou.github.io/blog/felis/) 是一个小型猫形四足：腰部两轴主动脊柱由 2 个电机驱动 yaw 和 pitch，四条腿各有一个髋电机，共 6 个主动电机。项目页报告仿真机器人从倒置释放到落地姿态约需 0.66 s，同一机构还完成走路和跳跃。机构本身值得观察，但更接近 DexLab 当前缺口的，是围绕策略写清楚的观测与事件合同。

具体看一次倒置释放：项目说明在 2.5–3.5 m 的释放高度上，策略每 20 ms 读取姿态、角速度、六个关节的位置与速度、时间和释放高度，再输出六个关节位置目标，交给每轴 PD 环。动作历史与时间相位在 release 时清空；如果机器人仍被手握住就开始运行，或晚 100 ms 才触发，即使网络和物理完全相同，也已经不是同一回合。

这不是被动柔性关节。两轴腰部主动改变身体形状；在随质心运动的坐标系里，内部弯曲与扭转的时序可以改变整体姿态，不需要接触、尾巴或反作用轮。项目页的阅读列表也列出了更早的猫翻身与主动脊柱机器人，因此可防守的贡献是紧凑的系统集成，不是首次发现空中翻身。

公开证据已经支持实机存在、明确的仿真到策略接口与动态演示；它尚不支持硬件成功率结论。释放条件、重复次数、失败分母、控制延迟、力矩跟踪、能耗与 sim-to-real 误差都没有公开。已核查仓库包含推理代码、三个小型 actor 和一致性数据，但明确不含训练代码、仿真资产与 3D 模型；核查树中也未见许可证。parity 只核对导出模型与参考 rollout 的动作，不是物理任务验收。

**对 DexLab 的判断是 watch。** 在具体操作失败证明“近端躯干或手腕运动能替代远端手指自由度”，且改变机构能区分失败解释之前，不新增主动脊柱运动任务。已有策略一旦依赖 release、接触建立、松手或 reset，则应借这份合同：分别记录事件时间、观测时间、模型输出、实际下发目标和控制模式；reset 不只要覆盖初始位姿，还要清空动作历史与时间状态。

核查于 2026-11-19，依据渲染后的项目页与仓库提交 `605e9f6d07d8e4ce166ddd1988578a345dec665d`。本轮环境未安装 PyTorch，因此没有运行 parity 或策略示例；没有新增 DexLab 任务、训练、物理扫描或真机实验。


## 来源与维护范围

本文由 2026-09-10 建立、2026-09-14 补充的《当我们在讨论灵巧操作仿真时，我们在讨论什么》研究笔记整理为公开导读，保留六层框架、研究路线和证据边界。**2026-11-02** 核对了本文引用的官方摘要、文档与 DexLab 已发表案例；HydroShear 和 Dex-X 的入口分别更新到 v2、v3。这里没有重新完成原笔记的全部文献筛选，也没有将旧版细节无条件移植到新版。

2026-11-03 按作者要求公开原版自包含 HTML，保留其 9 月来源和核查口径，再独立追加 10 月工作；本页仍是简版阅读路线。外部论文不记作 DexLab 复现，推荐的实验仍需单独冻结协议后执行。原版快照 SHA-256：`2c41d2ee32f8094298d2398e3950d5b749a3030a62a07e25128df6d709823c00`。

2026-11-12 增补 RLT / CAP 精细插接边界，依据论文、官方项目页与公开仓库入口做静态核查；没有运行策略、checkpoint、仿真或真机实验。Discussion 先行记录取舍，页面只保留长期结论。

2026-11-16 增补 COAP 的状态证据与代码改动门槛。该节沿用现有评分审计优先顺序，没有新增策略实现、实验或外部复现；完整讨论与版本边界见 [Discussion #335](https://github.com/huangkiki/Dexlab/discussions/335)。

2026-11-16 增补 CaP-X / ASPIRE 的反馈契约与技能晋升门槛。两者分别以实验设计和技能准入影响后续评测，不代表已采用代码 Agent、自动技能库或进化搜索；完整讨论见 [Discussion #341](https://github.com/huangkiki/Dexlab/discussions/341) 与 [Discussion #342](https://github.com/huangkiki/Dexlab/discussions/342)。

2026-11-17 增补 G1 脚踝闭环传动的本体建模边界。该节把硬件限位、传动状态、控制映射、reset 和积分器分开，不表示 DexLab 已迁移闭环资产或复现作者实验；完整讨论见 [Discussion #372](https://github.com/huangkiki/Dexlab/discussions/372)。

2026-11-18 增补 RoboDojo 的参数送达、数值 plausibility、求解守恒与评分正负控制审计。外部运行结果来自作者博客，DexLab 侧只做了固定源码静态核对；不表示 DexLab 已完成相应实现、物理重跑或真机验证。完整讨论见 [Discussion #388](https://github.com/huangkiki/Dexlab/discussions/388)。

2026-11-19 增补 Felis 的策略合同边界。依据渲染后的项目页与固定推理仓库核查；欠驱动主动脊柱保留为 watch，事件/reset 边界供后续策略评测借鉴。本轮没有训练、物理或真机结果，完整讨论见 [Discussion #416](https://github.com/huangkiki/Dexlab/discussions/416)。
