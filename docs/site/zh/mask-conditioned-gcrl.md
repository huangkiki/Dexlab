# 视觉目标 mask 怎样进入 DexLab：先证明它是进度信号，再谈 GCRL

> **一页速览**
>
> | 维度 | 内容 |
> | --- | --- |
> | **涉及工作** | *Dynamic Object Masks as Goal Representations for Visual Goal-Conditioned Reinforcement Learning*（University of Alberta / Amii / McGill / Vector Institute 等，RLC 2026，[arXiv:2510.06277v2](https://arxiv.org/abs/2510.06277v2)，2026-08） |
> | **固定源码** | [`fahimfss/GCRL@771cf55`](https://github.com/fahimfss/GCRL/tree/771cf5567ef656f941f0ace0e2881d38988fd94b)（MIT License） |
> | **核心问题** | 视觉目标条件强化学习（GCRL）通常依赖 3D 特权坐标、类别 one-hot、CLIP 文本或预采目标图：前两者要么需要昂贵位姿估计、要么缺少空间位置，而单纯 3D 距离奖励在抓取时只鼓励末端靠近中心、不鼓励夹爪对位。 |
> | **核心做法** | 每步在 RGB 图像后拼接一张随观测实时更新的**二值目标 mask 通道**（三帧堆叠输入策略），并将**全图或夹爪 ROI 内的 mask 像素占比**经 sigmoid 放大作为密集接近奖励。 |
> | **开源现状** | 训练与真机脚本已开源（MIT）；**未提供预训练 policy checkpoint**，且仿真依赖外部 RoboHive 物体资产。 |
> | **对 DexLab 判决** | **`pilot`（只借鉴视觉进度信号的单调性与扰动审计门槛，暂不引入视觉 GCRL 训练栈）** — DexLab 已在 [PR #411](https://github.com/huangkiki/Dexlab/pull/411) 完成 LIBERO 离线审计，证实伪框与遮挡可直接欺骗 ROI 进度分。 |

---

## 一、这篇工作具体做了什么？

在没有可靠 3D 物体位姿估计的视觉机器人里，策略既需要知道“画面里哪个物体是目标”，又需要知道“自己离它有多近、有没有落进夹爪之间”。Dynamic Object Masks 的做法非常直接：**用每步重算的目标二值 mask 统一承担目标条件输入和密集接近奖励**。

### 1. 问题设定与输入 / 输出

- **场景与瓶颈**：当机械臂（UR10e / Franka）从桌面抓取目标或移动机器人（Create3）导航找目标时，如果只给类别 one-hot 或 CLIP 文本，策略仍要自己从 RGB 里反推目标空间位置；如果用末端到物体中心的 3D 距离做奖励，夹爪往往会停在苹果旁边（中心距离很小，但苹果并未落进两指之间）。
- **输入**：
  - **视觉输入**：将当前帧 RGB 与对应的目标二值 mask $m_t$ 按通道拼接为 4 通道图像 $I_t' = [I_t^{\mathrm{cam}}, m_t]_C$，再把最近 3 帧堆叠成 `90 × 160 × 12` 张量 $I_t = [I_t', I_{t-1}', I_{t-2}']_C$，让策略同时看到目标位置、尺度和运动方向；
  - **本体状态**：机械臂关节位置与上一动作（抓取任务额外加入双指接触二值标志）。
- **输出**：由 4 层 CNN + LayerNorm + tanh 编码器接 Actor/Critic 输出低层关节速度（机械臂）或底盘速度（Create3）。仿真与真机从零学习使用 **5-Q 集成 SAC**（配合 random shift 与 weight clipping 稳定像素训练）；UR10e 零样本 sim-to-real 使用 **PPO**。

### 2. 系统流水线与三个核心模块

1. **动态目标 mask 生成器（`env_v1.py` / `franka_dense_env.py`）**：仿真中并非运行真实语义分割，而是用**特权物体中心经相机矩阵投影成矩形框**，再乘以代码里逐物体手写的宽高缩放与偏移参数；真机上替换为颜色阈值、Detic（固定类别词表 + 置信度 0.5）或 Grounding DINO（开放词表文本 prompt）输出的矩形框。
2. **全图 mask 奖励与夹爪 ROI 阶段切换（`env_v2.py`）**：普通 reaching 任务统计全图 mask 像素占比；抓取任务将统计区域收缩到**夹爪两指之间的固定 ROI**——只有物体真正落进可抓窗口，mask 重叠面积才增大。一旦双指均触发接触，mask 清零，奖励立刻切换到接触、抬升高度与任务完成项。
3. **真机视觉域适配（UR10e sim-to-real）**：在 PPO 训练中叠加关节噪声、初始姿态偏移、光照/模糊扰动，并将仿真图像与随机真实背景按 **80% / 20%** 线性插值以缩小视觉域差；部署端运行 Grounding DINO（约 120 ms/step）配合底层 500 Hz servoJ 控制。

![Figure 4: 夹爪 ROI mask 引导桌面抓取序列](https://arxiv.org/html/2510.06277v2/plots_and_images/pick.jpg)

*图 1（原论文 [Figure 4](https://arxiv.org/html/2510.06277v2#S4.F4)）：抓取阶段只统计两指之间 ROI（绿色框仅作示意，不输入策略）内的目标 mask 面积以引导夹爪对位；最后两帧双指接触后清除 mask 并切换至接触与抬升奖励。*

### 3. 核心机制与关键公式

论文把“目标在哪里”与“离目标多近”压缩进下面两组公式（§3–4、式 3–5）：

$$
R' = \frac{1}{H \times W}\sum_{i=1}^{H}\sum_{j=1}^{W}\mathbf{1}\!\left\{m_t^{ij} > 0\right\},
\qquad
R^{\mathrm{mask}} = \frac{2}{1 + e^{-10 R'}} - 1 \in [0, 1]
$$

在 UR10e 桌面抓取中，mask 接近奖励再与物理接触、抬升、终态项拼接成组合密集奖励：

$$
R^{\mathrm{pick}} = -1.1 + R^{\mathrm{reach}} + R^{\mathrm{contact}} + R^{\mathrm{lift}} + R^{\mathrm{goal}}
$$

- $H, W$：整幅图像或夹爪 ROI 的高与宽；$R'$ 为激活像素占比；
- 常数 $10$：sigmoid 斜率超参，用于在目标尚远、mask 占比很小时放大面积增量梯度；
- $R^{\mathrm{contact}}$（双指首次接触 `+10`，后续每步 `+0.1`）、$R^{\mathrm{lift}} = 1 - 3.3 D$（接触后按离目标高度距离 $D$ 给分）、$R^{\mathrm{goal}}$（达标一次性 `+10`）；
- **机制直觉**：当腕部相机直视目标并向前靠近时，透视投影天然使目标在画面里变大；把 $R'$ 限定在夹爪 ROI 内，则把“靠近中心”收窄为“把物体送进两指之间”。但这一单调性高度依赖**第一视角相机 + 稳定无误检的 detector**。

### 4. 主实验设置、结果汇总与自带反例

| 实验 / 任务 | 对比条件与预算 | 关键指标（作者报告） | 这组结果实际证明了什么 / 反例 |
| --- | --- | --- | --- |
| **仿真视觉 Reaching**（Franka / UR10e-MuJoCo） | 20 个 RoboHive 物体（15 训 / 5 留出），SAC 30 万步，11 种子 × 25 次/物 | Mask 训练/留出准确率 **`99.9%`** vs 3D position `98.9% / 98.8%`；收敛快于 one-hot / CLIP / 目标图 | 证明动态 mask 是有效的视觉目标接口；`1.0 pp` 差距不足以单凭此项宣称优于特权坐标 |
| **仿真桌面 Pick-up**（UR10e-MuJoCo） | 从零训练 SAC 100 万步，11 种子 × 6 类物体 × 50 次试验 | Mask GC+reward：**9/11 种子**超过 `90%` 成功；3D position+distance 仅 **2/11 种子**超过 `90%` | 最有说服力的机制证据：ROI mask 补上了 3D 距离不引导夹爪对位的缺口（仍依赖接触/抬升奖励） |
| **移动视觉导航**（Create3-Isaac Sim） | 方形场地寻找彩色墙贴，颜色阈值生成 mask | Mask 收敛更快，**反例：最终中位数低于始终拥有 3D 坐标的基线** | 目标不在视野内时，mask 必须先盲搜再靠近，空间信息弱于全局坐标 |
| **UR10e 零样本 Sim-to-Real**（Table 1） | 10 种子挑最佳 PPO 策略，Grounding DINO，每类 25 次，15 cm 阈值 | In-dist **`96%`**（0.076 m）；OOD-1 **`92%`**（0.13 m）；OOD-2 **`92%`**（0.092 m） | 展示仿真到真机接口迁移潜力，但存在 best-of-10 选优偏差且目标位姿预录 |
| **Franka 真机从零学习**（Figure 3c） | 腕部相机 10 万步（每回合 100 步），RTX 3090，Detic（157 ms）vs Grounding DINO（168 ms） | Detic 约 6 万步学会 reaching；**反例：Grounding DINO 因误检框被奖励利用而训练彻底失败** | 直接暴露核心失效层：`误检框 → 假 mask 面积 → 错误高奖励 → 策略优化 detector 漏洞` |

![Figure 3c: Franka 真机从零学习中 Detic 与 Grounding DINO 失败对比](https://arxiv.org/html/2510.06277v2/plots_and_images/rw_scratch_franka.png)

*图 2（原论文 [Figure 3](https://arxiv.org/html/2510.06277v2#S4.F3)）：Franka 真机从零训练曲线。Detic 稳定收敛，而 Grounding DINO 的误检框进入 mask-size 奖励后被策略迅速利用，导致真机任务失败。*

---

## 二、哪些隐藏前提与反例可能改变判断？

1. **“Object-agnostic”被仿真实现收窄为已知池内实例泛化**：静态核查固定源码 `env_v1.py` 发现，仿真 mask 是由特权物体中心投影并乘以**逐物体手写宽高缩放与偏移**拼出的矩形框，而非开放世界分割。作者在 Limitations 中也明确将其界定为 object-agnostic **reaching**，而非通用部位级抓取（如杯柄、剪刀把手）。
2. **“策略不读 3D 坐标”不等于“真机实验无特权定位”**：公开真机代码 `franka_dense_env.py` 虽未把 3D 坐标喂给 actor，但仍用预先记录的 `target_pos` 计算末端距离并在 `< 0.13 m` 时终止回合。策略输入与实验验收使用的特权字段必须严格分账。
3. **mask 面积单调性在固定外视相机、遮挡与误检下天然失效**：论文没有做 mask 漏检、闪烁、部分遮挡与面积抖动的受控消融。在 Grounding DINO 失败案例中，最早失效层是视觉目标生成与奖励语义，而非 SAC 或物理求解器。
4. **抓取成功由多阶段物理奖励共同撑起**：双指接触后 mask 立刻清零，抓持稳定与抬升仍完全取决于真实接触、几何与物理参数，不能把抓取成功率全部归功于 mask 表示。

---

## 三、对 DexLab 的借鉴判断与最小验证切片

在 DexLab 里，视觉进度信号一旦进入奖励或阶段判据，就会把“检测器出错”伪装成“物理或策略失败”。**我们已在 2026-11-18 基于 LIBERO `demo_0` 固定相机回放完成了该论文启发的首个离线审计切片（[PR #411](https://github.com/huangkiki/Dexlab/pull/411) / [LIBERO 审计报告](libero-workflow-report.md)）**，用 28 个阶段点 + 4 种可控扰动实测验证了上述风险：

- 基线 target-mask ROI overlap 中位数随阶段上升（接触前 `0` → 接触到抬升 `0.535` → 抬升到成功 `0.877`，接触前后排序 AUC `0.861`），但两个 post-success 样本出现目标 mask 丢失——证明该实现不能把 mask 当作完成信号；
- **7 次漏检**把 AUC 拉低至 `0.738`；**3 帧延迟**错位接触阶段；**ROI 内伪框**把接触前 overlap 抬高至 `0.780`（证实高分可由假进度造出）；**部分遮挡**反而缩小分母抬高 overlap，说明面积变化不能单向解读。

据此形成 DexLab 的明确取舍：

- **直接借鉴**：
  1. **视觉进度信号单调性与扰动审计合同**：任何视觉 mask 进入策略或奖励前，必须同回合保存 mask 存在性、面积、中心误差、ROI overlap、真实距离与原生接触事件，并跑通遮挡/漏检/伪框/延迟四项扰动检验。
  2. **拆开四类权限字段**：actor 观测输入、奖励输入、episode 终止条件与最终验收真值必须分栏登记。
  3. **把检测错误单列为独立失效层**：禁止把 `detector error → reward error → policy failure` 糊成“RL 训练不稳定”。
- **需适配验证**：
  - 仅在腕部相机 + 真实检测器输出下通过上述单调性与抗误框门槛后，再小范围对比 mask 条件、目标图条件与特权坐标条件。
- **暂不采用**：
  - 不把 mask-size reward 当作物理接触或抓取成功；
  - 不因单一抓取案例引入通用检测器/分割框架或完整视觉 GCRL 栈；
  - 不把 99.9% reaching 准确率外推到任意未知几何或固定第三人称相机。

### 下一步可证伪验证切片

- **验证问题**：在已完成固定相机 LIBERO 离线审计（PR #411）的基础上，将同一套 4 扰动审计迁移到**腕部第一视角相机 + 真实开放词表检测器输出**上，ROI overlap 与 mask 存在性门控能否在接触前/接触中/抬升阶段把真实进度与伪框/遮挡分开？
- **固定条件与对照**：冻结同一批带原生接触读回的录制轨迹，不训练策略、不改物理引擎，比较“原始 ROI overlap”与“带连续帧一致性 + 置信度门控的 ROI 信号”在四类扰动下的阶段排序 AUC 与假进度率。
- **通过与停止标准**：若门控后仍出现伪框把失败/未接触阶段排到成功阶段之前，先修视觉目标表示与检测合同，不启动任何视觉 GCRL 训练。

---

## 四、可核查来源与证据范围

- 论文：[Dynamic Object Masks as Goal Representations for Visual GCRL (arXiv:2510.06277v2)](https://arxiv.org/abs/2510.06277v2)（全文 5 张 Figure、1 张 Table、5 个公式完整阅读）
- 固定源码：[`fahimfss/GCRL@771cf55`](https://github.com/fahimfss/GCRL/tree/771cf5567ef656f941f0ace0e2881d38988fd94b)（静态核查 `env_v1.py`、`env_v2.py`、`rl_chemist/env.py`、`franka_dense_env.py`、`detic.py`）
- DexLab 关联记录：[Discussion #405](https://github.com/huangkiki/Dexlab/discussions/405) · [Research intake #406](https://github.com/huangkiki/Dexlab/issues/406) · [LIBERO 离线审计 PR #411](https://github.com/huangkiki/Dexlab/pull/411) · [模型评测边界](model-evaluation.md)
- **核查范围（2026-11-26）**：论文与固定源码均为静态核查，所有论文成功率、真机时长与迁移数字均为作者报告（本轮未运行 RoboHive、MuJoCo、Isaac Sim、SAC/PPO、Detic 或 Grounding DINO）；DexLab 离线审计数据来自已合并的 [PR #411](https://github.com/huangkiki/Dexlab/pull/411) 既有机器记录。
