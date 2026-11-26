# NeuralActuator：执行器误差要单独建模，接触仍要交给物理

> **一页速览**
>
> | 维度 | 内容 |
> | --- | --- |
> | **涉及工作** | *NeuralActuator: Neural Actuation Modeling for Robot Dynamics and External Force Perception*（MIT CSAIL / CDFG & Amazon Robotics，RSS 2026 Outstanding Systems Paper，[arXiv:2607.11734v2](https://arxiv.org/abs/2607.11734v2)，2026-07-17） |
> | **固定源码** | [`Frank-ZY-Dou/Dynamics-Modeling@541a93a`](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator)（MIT） · [项目主页](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html) |
> | **核心问题** | 低成本舵机的电流—力矩映射在减速器摩擦、背隙、饱和和温漂下严重非线性，且缺少关节力矩传感器；用理想 $\tau=K_tI$ 或位置伺服做仿真时，执行器误差会污染动力学 rollout 与外力估计。 |
> | **核心做法** | 把过去 8 帧加当前帧的命令、状态与舵机 telemetry 送入轻量化 Transformer，输出广义 effort 经**可微仿真**按真实位姿轨迹反传训练（无需 torque 标签），并共享表示输出末端 3D 外力、接触门与电机状态。 |
> | **开源现状** | 代码（MIT）、11 个预训练 checkpoint、NAD 数据集（OMX / SO-101 / Franka，430 条轨迹）与 MJX / Newton / MuJoCo Warp / SuperDex 四套可微后端均已公开。 |
> | **对 DexLab 判决** | **`pilot`（先过硬件 telemetry 数据合同，再仅在执行器层试点，绝不替代接触求解）** — 官方训练明确关闭接触（`mjDSBL_CONTACT`），先确保数据能把执行器误差与接触载荷拆开。 |

---

## 一、这篇工作具体做了什么？

NeuralActuator 要解决的核心痛点很具体：低成本机械臂（如约 \$500–\$3,000 级的 SO-101、OpenManipulator-X）没有昂贵的关节扭矩传感器，但舵机自身会回传位置、速度、电流/load register、电压与温度。论文把这些**时变执行器响应**封装成一个可移植的神经网络执行器层，并接入四个不同的可微物理引擎。

### 1. 问题设定与输入 / 输出

- **场景与瓶颈**：当低成本机械臂夹持 500 g 负载运动时，经典线性模型 $\tau = K_t I$ 忽略了减速箱非线性摩擦、齿隙、电流饱和与温升，导致仿真里给同样位置命令时关节响应与真机严重偏离。如果把执行器、接触和物体一起塞进端到端黑盒世界模型，又会丢掉刚体动力学先验。
- **输入**：长度为 9 帧（过去 8 帧 + 当前帧）的窗口张量 $\mathbf{X}_t$。以 OpenManipulator-X（4 臂关节 + 1 夹爪）为例，每帧 36 维：5 个命令位置、4 臂关节角与夹爪开度、5 路电流、5 路速度、5 路电压、5 路温度、目标开度与两类位置跟踪误差（在 SO-101 上电流换成带符号 load register，在 Franka 上换成命令扭矩）。
- **输出（4 个共享表示输出头）**：
  1. 仿真广义控制输入（torque surrogate）$\boldsymbol{\tau}_t^{\mathrm{pred}} \in \mathbb{R}^{n_m}$；
  2. 原始 3D 末端外力估计 $\hat{\mathbf{f}}_{\mathrm{raw}} \in \mathbb{R}^3$；
  3. 接触概率门 $g \in [0,1]$（监督阈值为 $\|\mathbf{f}_{\mathrm{gt}}\|_2 > 0.01\ \mathrm{N}$），最终外力 $\hat{\mathbf{f}} = g\hat{\mathbf{f}}_{\mathrm{raw}}$；
  4. 逐电机健康/受限分数 $\mathbf{c} \in [0,1]^{n_m}$。

### 2. 系统流水线与四个核心模块

1. **轻量 Gated-Attention Transformer（固定源码 `models/transformer.py`）**：输入投影至 192 维加可学习位置编码，经 4 层 pre-norm 编码器（4 头注意力、384 维 FFN、带 query 相关的逐元素门控 $\sigma(\mathbf{U}\mathbf{W}_g)$），总计 **1.44M 参数、5.46M FLOPs、单步推理 0.25 ms（约 4,019 Hz）**，满足高频控制与仿真调用需求。
2. **无 Torque 标签的可微仿真训练（§III-B）**：将 $\boldsymbol{\tau}_t^{\mathrm{pred}}$ 直接输入可微物理仿真器推进到下一状态，对长达数百步的 rollout 轨迹用真实关节位姿（Huber 损失，夹爪开度乘 $\kappa_g=1000$ 放大）做 BPTT 反传，绕过缺失真实关节扭矩标签的难题。
3. **多引擎可移植执行器接口**：在固定版本源码中保持网络、数据与损失完全不变，仅替换可微动力学引擎，实现了 **MJX、Newton、MuJoCo Warp 与 SuperDex**（独立可微 fork，通过 worker 进程每步求引擎 adjoint）四个后端，说明执行器层可以作为独立模块与物理引擎解耦。
4. **NAD 数据集与多任务评测（§IV）**：通过双臂 leader–follower 遥操作采集 430 条轨迹（OMX 主实验子集 94.52 min），涵盖自由运动（34.15 min）、已知砝码 100–500 g 与六轴 F/T 传感器标定交互（46.24 min）以及在 Joint 3 加橡皮筋制造的机械受限工况（14.13 min），并延伸至 SO-101 与 Franka Panda。

![Figure 3: NeuralActuator 系统流水线与四头 Transformer 结构](https://arxiv.org/html/2607.11734v2/Figs/fig_pipeline.png)

*图 1（原论文 [Figure 3](https://arxiv.org/html/2607.11734v2#S3.F3)）：9 帧命令与舵机 telemetry 进入 4 层门控 Transformer，并行输出 torque surrogate、原始末端力、接触门与电机状态；torque surrogate 驱动可微仿真推进状态并经真实位姿反传监督。*

### 3. 核心机制与关键公式

NeuralActuator 最关键的设计取舍体现在**无力矩标签的 BPTT 监督**与**刚体动力学可辨识性**的张力之间：

$$
\mathbf{s}_{t+1} = F_t\!\left(\mathbf{s}_t, \boldsymbol{\tau}_t^{\mathrm{pred}}\right), \qquad
\boldsymbol{\tau}_t^{\mathrm{pred}} = g_\theta(\mathbf{X}_t), \qquad
\frac{d\mathbf{s}_{t+1}}{d\theta} = \frac{\partial F_t}{\partial \mathbf{s}_t}\frac{d\mathbf{s}_t}{d\theta} + \frac{\partial F_t}{\partial \boldsymbol{\tau}_t^{\mathrm{pred}}}\frac{d g_\theta(\mathbf{X}_t)}{d\theta}
$$

而在物理刚体动力学中，逆动力学广义力矩 $\boldsymbol{\tau}_{\mathrm{ID}}$ 实际等于驱动力矩与外力广义项之和：

$$
\boldsymbol{\tau}_{\mathrm{ID}} = M(q)\ddot{q} + C(q,\dot{q})\dot{q} + \mathbf{g}(q) = \boldsymbol{\tau}_{\mathrm{act}} + J_v(q)^{\top}\mathbf{f}^{\mathrm{ext}}
$$

- $F_t(\cdot)$：单步可微物理推进器；$g_\theta(\mathbf{X}_t)$：直接预测 effort（论文表 XIV 证明 direct 预测优于基于 $K_tI$ 的残差形式 $\tau_{\mathrm{base}}(u_t)+\Delta g_\theta$）；
- $\boldsymbol{\tau}_{\mathrm{act}}$ 与 $J_v(q)^{\top}\mathbf{f}^{\mathrm{ext}}$：真实的执行器输出力矩与末端外力经雅可比映射的广义力；
- **物理直觉与隐藏张力**：由于默认 **implicit coupling** 下只把 $\boldsymbol{\tau}_t^{\mathrm{pred}}$ 送进仿真、**并不把预测外力 $\hat{\mathbf{f}}$ 施加回动力学**，网络只要吐出“能让仿真位姿贴合真实位姿”的等效广义 effort 就能把位姿损失压低——这意味着 $\boldsymbol{\tau}_t^{\mathrm{pred}}$ 实质上是**包含未建模外载的仿真等效 effort**，而非可独立辨识的真实执行器力矩 $\boldsymbol{\tau}_{\mathrm{act}}$。

### 4. 主实验设置、结果汇总与自带反例

| 实验 / 来源（作者报告） | 测试条件与预算 | 关键指标数值 | 这组结果实际证明了什么 / 反例 |
| --- | --- | --- | --- |
| **OMX 负载外力 vs 模型基线**（[Table VII](https://arxiv.org/html/2607.11734v2#S5.T7)） | 100 步 rollout，7 组 200–500 g 任务；基线每步用 GT 状态，NeuralActuator 用自 rollout 状态 | Force MAE：ID-Linear `1.41 N`、ID-Friction `1.23 N`、GMO `0.66 N` → NeuralActuator **`0.12 N`** | 在该低成本舵机与 telemetry 协议下，固定线性 $K_tI$ 远不足以估计外载；不能泛化为“所有模型法都无效” |
| **OMX 自由运动与 F/T 交互**（Tables III–VI） | 500–600 步（约 10 s）长时 rollout，每任务 8 训 / 1 验 / 1 测轨迹 | 无负载关节 MAE `2.8–3.2°`（夹爪 `0.2 mm`）；6 向 F/T 交互 force MAE `0.23 N`（无接触参考近 `0.00–0.01 N`）；推力计 `0.08–0.10 N` | 长时 rollout 漂移受控，且 contact gate 能压住无接触参考段的零漂 |
| **Direct vs Residual 与 Implicit vs Explicit 耦合**（[Table XIV](https://arxiv.org/html/2607.11734v2#S5.T14)） | OMX 3 种子、SO-101 6 任务对比；explicit 把 $\hat{\mathbf{f}}$ 经 $J_v^\top f$ 注入动力学 | OMX 最差关节 MAE：Direct `0.39°` vs Residual `0.64°`；**反例：Explicit 耦合在 OMX（`0.88°→1.33°`）与 SO-101（`2.50°→6.90°`）上均显著变差** | 强行闭环注入预测外力反而恶化长时 rollout；间接印证 implicit 的高精度依赖 torque head 吸收载荷 |
| **跨平台泛化**（Tables IX–X） | 从零训练 SO-101（STS3215 舵机）与 Franka Panda（7-DoF） | SO-101 500 步 force MAE `0.47–0.73 N`，**最大单关节 MAE 达 `9.77°`**；Franka 离线 future-state-conditioned force MAE `0.26–0.42 N` | 不同硬件精度落差明显；Franka 评测属离线条件基准，不等价于闭环动力学验证 |
| **电机机械受限检测**（[Table XI](https://arxiv.org/html/2607.11734v2#S5.T11)） | Joint 3 套橡皮筋，4 条留出轨迹；手工基线用 64 步窗 | NeuralActuator Acc **`91.0%`** / Recall **`96.2%`** / AUC **`0.95`**（随机森林 `67.1% / 52.4% / 0.72`） | 独立证明 telemetry 历史蕴含非线性机械状态信息，但不等于寿命预测或通用故障诊断 |
| **在线适配与力感知 BC**（Tables VIII, XIII） | 12 条新轨迹（7,810 帧、356 s 微调）；40 次真机 BC 试验 | 曲线级跟踪误差降约 `44%`；Pick-and-Place `80%→92.5%`，Lift-and-Hold `85%→95%` | 固定任务与预训练载荷范围内有效，不能外推为未知载荷通用泛化 |

![Figure 15: OMX 上 Implicit 与 Explicit 外力耦合对比反例](https://arxiv.org/html/2607.11734v2/Figs/fig_explicit_force_omx.png)

*图 2（原论文 [Figure 15](https://arxiv.org/html/2607.11734v2#S5.F15)）：把预测末端外力真正通过雅可比注入动力学（explicit）反而比不注入（implicit）带来更大轨迹偏差，凸显执行器力矩与外部载荷的可辨识性边界。*

---

## 二、哪些隐藏前提与反例可能改变判断？

1. **官方训练主动关闭接触求解**：固定版本源码 `train_actuator_diffsim.py` 明确启用 `mjDSBL_CONTACT`，Newton 求解器仅跑 1 次迭代；负载物体不作为场景几何建模，夹爪直接跟随记录开度，训练轨迹按设计避免场景碰撞。**因此 NeuralActuator 是无接触环境下的执行器动力学拟合，不能证明接触物理更准。**
2. **rollout 吃的是真实回放 telemetry，不是反事实动作预测器**：评估阶段每步输入的电流/负载、电压与温度仍与真实录制的轨迹对齐；论文也坦承模型不能预测“未执行过的未来新命令”会产生怎样的电流和 effort 响应。
3. **外力估计仅为末端 3D 合力且强依赖独立力标注**：模型不输出 6 维 wrench、接触点位置或多指分布接触力，且 force head 必须依赖已知砝码或六轴 F/T 传感器监督。
4. **训练稳定化钳制不能等同物理真实性**：源码对输出 torque、关节速度 `qvel` 与夹爪限位做了可微 clamp，这保障了 BPTT 数值不发散，但不构成物理接触或硬件安全边界的证明。

---

## 三、对 DexLab 的借鉴判断与最小验证切片

在 DexLab 的接触与抓取诊断体系里，低成本硬件（或非理想执行器）的跟踪滞后很容易被误判为“接触求解器不准”或“摩擦系数不对”。NeuralActuator 最大的价值在于**把执行器误差明确独立成一层，并与多引擎接口解耦**；而它的接触关闭前提也划清了红线——绝不能让黑盒执行器把接触载荷吞掉。

- **直接借鉴**：
  1. **执行器 telemetry 准入合同**：在任何执行器拟合之前，强制将 `q_cmd`、`q`、`qdot`、`current/load`、`voltage`、`temperature`、独立力参考、坐标系/正负号、单调时钟与硬件实例分通道记录，拒绝“把命令回写成反馈”或时钟倒流的无效日志。
  2. **轨迹级与硬件实例级切分**：严禁按帧随机切分训练/测试集，防止温漂、摩擦历史和同一装机批次泄漏。
  3. **成对保留负例工况**：自由运动、无载荷、正常电机、机械受限、有接触与同轨迹无接触参考必须成对留档。
- **需适配验证**：
  - 当 DexLab 拿到合格的低成本舵机实测日志后，做单平台、单装机实例的 **actuator-only pilot**：保持原生接触求解器**开启**，对照 direct torque surrogate、residual $K_tI+\Delta\tau$ 与 GMO，用独立力参考检验执行器层是否偷偷吸收了接触载荷，并同步报告位姿误差、力误差、饱和、温升与无接触误报率。
- **暂不采用**：
  - 不拿 implicit torque surrogate 替代物理接触求解；
  - 不把 3D 末端合力外推为多指灵巧手接触力分布；
  - 不把读取录制 telemetry 的 rollout 当作反事实规划器或闭环世界模型；
  - 不在缺乏独立实测力参考的日志上宣称外力感知成立。

### 第一步最小可证伪验证切片

- **验证问题**：DexLab 现有的硬件日志准入链路（`src/dexlab/hardware_log.py` 与 `docs/hardware/template/manifest.json`）能否在训练任何模型之前，先通过机器检查把“命令/执行器跟踪误差”和“独立接触载荷参考”在时间、单位、方向和切分归属上可靠分开？
- **固定条件与对照**：在现有硬件日志 schema 上定义 `actuator-calibration` profile，构造合成正例与 5 类明确负例（时钟漂移/倒流、缺 effort 通道、命令复制到反馈、缺失独立力参考来源、跨轨迹帧泄漏），跑通离线准入测试，**本切片不训练模型、也不产出任何物理结论**。
- **通过与停止标准**：全部正例通过、5 类合成负例 100% 被拒且报错指向具体缺失字段。若实际硬件日志尚未满足该数据合同，先补采集与标定合同，不提前训练 Transformer。

---

## 四、可核查来源与证据范围

- 论文：[NeuralActuator (arXiv:2607.11734v2)](https://arxiv.org/abs/2607.11734v2)（RSS 2026，正文与附录完整阅读） · [项目主页](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html)
- 固定源码：[`Frank-ZY-Dou/Dynamics-Modeling@541a93a`](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator)（静态核查 `models/transformer.py`、`train_actuator_diffsim.py`、implicit/explicit coupling 与 MJX/SuperDex 后端）
- 相关讨论与追踪：[DexLab Discussion #414](https://github.com/huangkiki/Dexlab/discussions/414) · [Research intake #415](https://github.com/huangkiki/Dexlab/issues/415)
- **核查范围（2026-11-26）**：基于 arXiv `2607.11734v2` 与固定提交 `541a93a` 的静态代码审查。全部量化数值均为作者报告；本轮未运行 MJX、Newton、MuJoCo Warp、SuperDex、OMX、SO-101 或 Franka，也未采集新真机数据。
