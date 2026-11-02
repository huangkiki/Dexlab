# Newton 论文导读：35 篇在研究什么？

这些工作分别研究物理计算、机器人学习和仿真验证。Newton 在其中可能是被改进的引擎，也可能用于训练、数据生成或对照评测。

本导读覆盖[完整书目](https://huangkiki.github.io/Dexlab/zh-cn/latest/newton-publications.html)中的 **35 篇文献**，按主要问题分为七类。分类与一句话解释由 DexLab 整理，阅读范围为 **2026-11-02 核对的摘要及作者页面**，不代表逐篇全文评审或复现。上游的 34 项研究与 1 项仅作对照的归属保持不变；外部结果不计入 DexLab 实验成绩。

## 按问题开始阅读

| 想弄清什么 | 推荐顺序 | 阅读时关注 |
| --- | --- | --- |
| 接触怎么求解，梯度从哪里来？ | [Ostrich](https://arxiv.org/abs/2609.08800) → [FlashNeRD](https://arxiv.org/abs/2610.09130) | 前者研究硬接触求解与隐式梯度；后者保留解析碰撞检测、学习机器人动力学。分别核查接触判定、力的计算和反向传播。 |
| 仿真与实物哪里不一致，怎么修改？ | [GAUGE](https://arxiv.org/abs/2608.05948) → [Same Action, Different Outcome](https://arxiv.org/abs/2610.10801) → [RoboSimStudio](https://arxiv.org/abs/2610.18835) | 依次看实测评测、重复实验的变化、模型与参数校准。 |
| 世界模型如何支持动作选择？ | [PointCast](https://arxiv.org/abs/2609.28393) → [PileBelief](https://arxiv.org/abs/2609.22858) | 区分未来运动预测、交互历史记忆和下游动作选择；预测准确并不自动保证控制成功。 |

以下顺序是阅读建议，不是论文质量排名。

## 物理引擎与接触求解 · 4

| 论文 | 研究问题 |
| --- | --- |
| [Ostrich](https://arxiv.org/abs/2609.08800) | 在硬接触与摩擦下使用较大的仿真时间步，并计算用于动作优化的梯度。 |
| [Kamino](https://arxiv.org/abs/2603.16536) | 在 GPU 上并行模拟闭环连杆等关节相互牵制的复杂机械结构。 |
| [Mixed Material Point Methods](https://research.nvidia.com/labs/prl/mixed_mpm/) | 改进沙子、雪和弹塑性材料的计算，并处理材料与刚体之间的双向作用。 |
| [Exact Reduced Coulomb Friction](https://arxiv.org/abs/2607.19599) | 改进摩擦求解，在保留库仑摩擦规律的条件下处理粘住与滑动。 |

## 检查和校准仿真 · 7

| 论文 | 研究问题 |
| --- | --- |
| [GAUGE](https://arxiv.org/abs/2608.05948) | 用真实实验数据检查物理引擎和视频世界模型中的碰撞、摩擦与变形。 |
| [RoboSimStudio](https://arxiv.org/abs/2610.18835) | 让人和编程智能体调整求解器、接触模型及参数，使仿真更接近观测到的实物行为。 |
| [RigPI](https://arxiv.org/abs/2606.25212) | 用视觉语言模型提供参数初值，再根据运动和力的测量，通过可微仿真修正参数。 |
| [Informationally Decoupled Trajectory Design](https://arxiv.org/abs/2610.10905) | 选择能区分不同物理参数影响的机器人动作，让参数辨识更可靠。 |
| [Same Action, Different Outcome](https://arxiv.org/abs/2610.10801) | 测量相同甩布动作产生的结果变化，并检查仿真是否能复现这种变化。 |
| [ContactBench 1.0](https://arxiv.org/abs/2610.24512) | 建立可重复制作实物、且配有仿真模型的接触操作任务，用于比较机器人能力。 |
| [Probabilistic Physics Digital Twin](https://arxiv.org/abs/2610.19336) | 将质量、摩擦等不确定参数表示为分布，预测动作的多种可能结果及概率。 |

## 学习动力学和世界模型 · 4

| 论文 | 研究问题 |
| --- | --- |
| [FlashNeRD](https://arxiv.org/abs/2610.09130) | 保留传统碰撞检测，用神经网络加速机器人动力学，并与解析求解的物体双向耦合。 |
| [PointCast](https://arxiv.org/abs/2609.28393) | 根据三维点和机器人动作预测物体运动；同一架构用于刚体、关节物体、布和绳子，各类分别训练。 |
| [PileBelief](https://arxiv.org/abs/2609.22858) | 记住过去挖掘透露的物理信息，预测下一铲的土堆变化与挖掘量。 |
| [PhysLDM](https://arxiv.org/abs/2610.07609) | 用潜空间扩散模型生成三维软物体的变形轨迹。**Newton 仅作对照基线。** |

## 布料、绳子与软物体操作 · 6

| 论文 | 研究问题 |
| --- | --- |
| [ForwardDLO](https://arxiv.org/abs/2609.18455) | 快速预测双臂拉动绳子后的形状，让规划器比较更多候选动作。 |
| [RopeFormer](https://arxiv.org/abs/2609.23432) | 保留前几次甩绳的动作与响应，使固定策略适应当前绳子的动力学。 |
| [DefFlow](https://arxiv.org/abs/2610.22827) | 联合预测机器人和软物体的三维运动，学习朝目标形状抓取、移动、松手与重抓。 |
| [Learning Sim-Grounded Policies for Bimanual Rope Manipulation](https://arxiv.org/abs/2605.16043) | 比较图像观测与仿真维护的绳子状态，研究少量遥操作示范下的策略泛化。 |
| [SIM1](https://arxiv.org/abs/2604.08544) | 从少量真实示范重建并校准软物体仿真，再扩充合成训练数据。 |
| [High-Fidelity 4D Cloth Capture](https://graphics.cs.utah.edu/research/projects/two-level-cloth-capture-pattern/two-level-cloth-capture-pattern.pdf) | 用多相机和布上的特殊图案精细记录真实运动，并用物理约束补全遮挡区域。 |

## 机器人控制与强化学习 · 6

| 论文 | 研究问题 |
| --- | --- |
| [Backpropagating Through Simulation](https://arxiv.org/abs/2606.21525) | 利用仿真梯度直接更新控制策略，并与 PPO 的采样学习方式比较。 |
| [AlphaNIST](https://arxiv.org/abs/2610.13354) | 在仿真中用成功或失败的二值奖励，让策略自行学习抓取、调整和装配动作。 |
| [A Balanced Data Diet](https://arxiv.org/abs/2610.12465) | 优先采样接近策略当前能力边界的任务，减少大规模强化学习中的无效经验。 |
| [GM-Loco](https://arxiv.org/abs/2609.10286) | 让人形机器人适应沙地等会下陷的颗粒地面，研究足部与地形的相互作用。 |
| [RoboMMT](https://arxiv.org/abs/2610.26414) | 让机器人执行朝向、指向等有表现力的交互动作，同时保持动态平衡。 |
| [Spectral Skills](https://arxiv.org/abs/2609.37677) | 将动作片段编码成可衔接、可组合的技能，供上层规划器控制人形机器人。 |

## 智能体、建环境与规划 · 3

| 论文 | 研究问题 |
| --- | --- |
| [Gym-Anything](https://arxiv.org/abs/2610.40565) | 让编程智能体创建机器人仿真任务，再通过创建与审查循环检查质量。 |
| [GaP](https://arxiv.org/abs/2607.05369) | 让智能体把感知、规划和控制模块组织成执行图，在仿真中反复测试与修改。 |
| [DetAug](https://arxiv.org/abs/2609.18395) | 扩充已有操作轨迹，让策略执行时能够选择绕开新障碍物的路线。 |

## 具体应用 · 5

| 论文 | 研究问题 |
| --- | --- |
| [LUMO](https://arxiv.org/abs/2609.18165) | 设计会发光的软指垫，通过受压后的光学变化定位手指接触位置。 |
| [PersistGS](https://arxiv.org/abs/2606.03479) | 在动态三维重建中，用物理仿真推算被完全遮挡物体的运动。 |
| [OrchardBench](https://arxiv.org/abs/2607.06337) | 模拟摘苹果，包括树枝弯曲、果实脱落、树叶遮挡与植物损伤。 |
| [RoboFin3D](https://arxiv.org/abs/2609.37560) | 模拟机器人打磨与砂磨，记录工件几何和表面外观的变化。 |
| [SceneFactory-3D](https://arxiv.org/abs/2610.02874) | 固定交通场景和控制器，改变路面摩擦与坡度，检查车辆安全性。 |

完整题名、作者、日期和上游署名见[完整书目](https://huangkiki.github.io/Dexlab/zh-cn/latest/newton-publications.html)。
