# 灵巧操作研究证据账本

**研究决策：** 优先完成 ManiSkill 原生接入（#47）和手内旋转独立评分（#48）。其他方法先借鉴评价与输入审计协议，暂缓未经准入的运行时、自定义引擎分支及依赖真机的训练。两个有预算的可选后续任务是[动作回放 #52](https://github.com/huangkiki/Dexlab/issues/52)与[合成触觉历史 #53](https://github.com/huangkiki/Dexlab/issues/53)，均不先于核心接触/布料修复。



2026-10-05 核对历史范围中的 **38 篇论文摘要页、19 个仓库入口**。这不是 38 篇完整方法审查或 19 个项目复现；源码、驱动、观测权限和资产许可未查明时保留未知。详见 [论文记录](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-papers.json)与[仓库记录](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-sources.json)。

## 论文版本与审查深度

下表列出版本、标题和摘要页身份；部分任务与方法审计见后文，其余完整方法审计仍待完成。版本固定链接优先于会变化的 latest 链接。

| 论文 / Paper | 版本 / Revision | 更新日期 / Revision date |
|---|---|---|
| [ManiSkill3: GPU Parallelized Robotics Simulation and Rendering for Generalizable Embodied AI](https://arxiv.org/abs/2410.00425v2) | v2 | 2025/05/30 |
| [DexGraspNet 2.0: Learning Generative Dexterous Grasping in Large-scale Synthetic Cluttered Scenes](https://arxiv.org/abs/2410.23004v1) | v1 | 2024/10/30 |
| [DexMimicGen: Automated Data Generation for Bimanual Dexterous Manipulation via Imitation Learning](https://arxiv.org/abs/2410.24185v2) | v2 | 2025/03/06 |
| [TacEx: GelSight Tactile Simulation in Isaac Sim -- Combining Soft-Body and Visuotactile Simulators](https://arxiv.org/abs/2411.04776v1) | v1 | 2024/11/07 |
| [Sampling-Based Model Predictive Control for Dexterous Manipulation on a Biomimetic Tendon-Driven Hand](https://arxiv.org/abs/2411.06183v3) | v3 | 2025/08/04 |
| [BODex: Scalable and Efficient Robotic Dexterous Grasp Synthesis Using Bilevel Optimization](https://arxiv.org/abs/2412.16490v3) | v3 | 2025/09/03 |
| [MuJoCo Playground](https://arxiv.org/abs/2502.08844v1) | v1 | 2025/02/12 |
| [Sim-to-Real Reinforcement Learning for Vision-Based Dexterous Manipulation on Humanoids](https://arxiv.org/abs/2502.20396v2) | v2 | 2025/09/01 |
| [ManipTrans: Efficient Dexterous Bimanual Manipulation Transfer via Residual Learning](https://arxiv.org/abs/2503.21860v1) | v1 | 2025/03/27 |
| [Taccel: Scaling Up Vision-based Tactile Robotics via High-performance GPU Simulation](https://arxiv.org/abs/2504.12908v2) | v2 | 2025/09/12 |
| [Dexonomy: Synthesizing All Dexterous Grasp Types in a Grasp Taxonomy](https://arxiv.org/abs/2504.18829v2) | v2 | 2025/09/03 |
| [A Survey of Robotic Navigation and Manipulation with Physics Simulators in the Era of Embodied AI](https://arxiv.org/abs/2505.01458v2) | v2 | 2026/06/09 |
| [DexGarmentLab: Dexterous Garment Manipulation Environment with Generalizable Policy](https://arxiv.org/abs/2505.11032v3) | v3 | 2025/10/12 |
| [TeleOpBench: A Simulator-Centric Benchmark for Dual-Arm Dexterous Teleoperation](https://arxiv.org/abs/2505.12748v2) | v2 | 2025/09/15 |
| [DexMachina: Functional Retargeting for Bimanual Dexterous Manipulation](https://arxiv.org/abs/2505.24853v1) | v1 | 2025/05/30 |
| [Dex1B: Learning with 1B Demonstrations for Dexterous Manipulation](https://arxiv.org/abs/2506.17198v1) | v1 | 2025/06/20 |
| [HumanoidGen: Data Generation for Bimanual Dexterous Manipulation via LLM Reasoning](https://arxiv.org/abs/2507.00833v2) | v2 | 2025/11/16 |
| [In-Hand Manipulation of Articulated Tools with Dexterous Robot Hands with Sim-to-Real Transfer](https://arxiv.org/abs/2509.23075v3) | v3 | 2026/03/05 |
| [SPIDER: Scalable Physics-Informed Dexterous Retargeting](https://arxiv.org/abs/2511.09484v3) | v3 | 2026/09/26 |
| [Learning Dexterous Manipulation Skills from Imperfect Simulations](https://arxiv.org/abs/2512.02011v2) | v2 | 2026/02/25 |
| [Dexterous Manipulation Policies from RGB Human Videos via 3D Hand-Object Trajectory Reconstruction](https://arxiv.org/abs/2602.09013v2) | v2 | 2026/02/11 |
| [FlowHOI: Flow-based Semantics-Grounded Generation of Hand-Object Interactions for Dexterous Robot Manipulation](https://arxiv.org/abs/2602.13444v1) | v1 | 2026/02/13 |
| [Dex4D: Task-Agnostic Point Track Policy for Sim-to-Real Dexterous Manipulation](https://arxiv.org/abs/2602.15828v1) | v1 | 2026/02/17 |
| [Grasp to Act: Dexterous Grasping for Tool Use in Dynamic Settings](https://arxiv.org/abs/2602.20466v1) | v1 | 2026/02/24 |
| [Tacmap: Bridging the Tactile Sim-to-Real Gap via Geometry-Consistent Penetration Depth Map](https://arxiv.org/abs/2602.21625v2) | v2 | 2026/05/12 |
| [HydroShear: Hydroelastic Shear Simulation for Tactile Sim-to-Real Reinforcement Learning](https://arxiv.org/abs/2603.00446v1) | v1 | 2026/02/28 |
| [Structural Action Transformer for 3D Dexterous Manipulation](https://arxiv.org/abs/2603.03960v1) | v1 | 2026/03/04 |
| [PTLD: Sim-to-real Privileged Tactile Latent Distillation for Dexterous Manipulation](https://arxiv.org/abs/2603.04531v3) | v3 | 2026/06/18 |
| [UltraDexGrasp: Learning Universal Dexterous Grasping for Bimanual Robots with Synthetic Data](https://arxiv.org/abs/2603.05312v1) | v1 | 2026/03/05 |
| [Grounding Sim-to-Real Generalization in Robotic Manipulation: An Empirical Study with Vision-Language-Action Models](https://arxiv.org/abs/2603.22876v2) | v2 | 2026/06/29 |
| [Blind Dexterous Grasping via Real2Sim2Real Tactile Policy Learning](https://arxiv.org/abs/2606.11767v2) | v2 | 2026/06/11 |
| [Labimus: A Simulation and Benchmark for Humanoid Dexterous Manipulation in Chemical Laboratory](https://arxiv.org/abs/2606.31037v2) | v2 | 2026/07/01 |
| [Learning Dexterous Manipulation Using Contact Wrench Guidance From Human Demonstration](https://arxiv.org/abs/2607.00033v2) | v2 | 2026/08/14 |
| [TouchWorld: A Predictive and Reactive Tactile Foundation Model for Dexterous Manipulation](https://arxiv.org/abs/2607.07287v2) | v2 | 2026/07/09 |
| [LabDex: A Hierarchical Benchmark for Dexterous Manipulation in Laboratories](https://arxiv.org/abs/2608.18618v1) | v1 | 2026/08/19 |
| [Does Imitation Learning Preserve Temporal Robustness in Dexterous Manipulation? An Expert-Learner Comparison Across Task Execution Speeds](https://arxiv.org/abs/2609.01453v1) | v1 | 2026/09/01 |
| [Morphology and actuation as inductive biases in robotic hand manipulation](https://arxiv.org/abs/2609.05206v1) | v1 | 2026/09/04 |
| [Dex-X: Learning Visual-Tactile Dexterous Manipulation From Human Videos with Simulated Interaction](https://arxiv.org/abs/2609.07747v3) | v3 | 2026/10/01 |

## 仓库与许可证据

固定 SHA 代表源码入口身份，不代表对应论文版本或可运行性。LICENSE 元数据不授予资产再分发权；未发现根目录许可证不代表其他目录没有条款。

| 仓库 / Repository | 固定源码 / Source | 审查 / Review |
|---|---|---|
| mani-skill/ManiSkill | [62ff3a5896](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/README.md) | README / metadata |
| JYChen18/BODex | [06b9a3c908](https://github.com/JYChen18/BODex/blob/06b9a3c90870d33bde9d6c665d4ed2819471407e/README.md) | README / metadata |
| JYChen18/DexGraspBench | [d9ea6cf282](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | README / metadata |
| NVlabs/dexmimicgen | [940e8a1b3a](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md) | README / metadata |
| MandiZhao/dexmachina | [adae5bf620](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md) | README / metadata |
| Taccel-Simulator/Taccel | [cb23bc251b](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md) | README / metadata |
| MMintLab/hydroshear | [f815b82fdf](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md) | README / metadata |
| DH-Ng/TacEx | [adceed41af](https://github.com/DH-Ng/TacEx/blob/adceed41afb7cb48f9ec1f66a662fb8e5a06627f/README.md) | README / metadata |
| wayrise/DexGarmentLab | [e4e298e696](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md) | README / metadata |
| x-robotics-lab/dexscrew | [3bde4e3a4d](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md) | README / metadata |
| Genesis-Embodied-AI/genesis-world | [02908fe647](https://github.com/Genesis-Embodied-AI/genesis-world/blob/02908fe6474d8b073b662347a8794614fa250658/README.md) | README / metadata |
| InternRobotics/UltraDexGrasp | [e0f9784a9b](https://github.com/InternRobotics/UltraDexGrasp/blob/e0f9784a9bf3030995b635c21ef8621ca3477ea8/README.md) | README / metadata |
| cyjdlhy/TeleOpBench | [4cc410d149](https://github.com/cyjdlhy/TeleOpBench/blob/4cc410d149ce63c86f485b257cba3b3e0ec031d6/README.md) | README / metadata |
| dexx-code/dexx-code | [88728c83c9](https://github.com/dexx-code/dexx-code/blob/88728c83c983b623ed1da0e2a203dc983fd8866b/README.md) | README / metadata |
| facebookresearch/project_superdex | [1d7150946f](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/README.md) | README / metadata |
| google-deepmind/mujoco | [07dfe91655](https://github.com/google-deepmind/mujoco/blob/07dfe91655630418a39bf863e454b0ad9fb8fbc0/README.md) | README / metadata |
| google-deepmind/mujoco_playground | [ef4fefc130](https://github.com/google-deepmind/mujoco_playground/blob/ef4fefc13033c0468af4ef651847f5348af0c7d7/README.md) | README / metadata |
| isaac-sim/IsaacLab | [a710e671a2](https://github.com/isaac-sim/IsaacLab/blob/a710e671a2a28492ebdbc433972190b7d7730670/README.md) | README / metadata |
| newton-physics/newton | [009158e62b](https://github.com/newton-physics/newton/blob/009158e62b862b3b9d829397d6db583515ae1271/README.md) | README / metadata |

## 尚未完成

#46 在研究交付通过验收前保持开放。每项记录的 solver、源码及资产未知项仍须在运行时接入前解决；#47/#48 尚未实现。

## ManiSkill 源码审计：上游成功不等于物理验收

固定源码 `62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3`；本节为静态审查，尚未运行新任务。ManiSkill1 [v5](https://arxiv.org/abs/2107.14483v5) 侧重物体泛化，ManiSkill2 [v1](https://arxiv.org/abs/2302.04659v1) 扩展任务与控制器；当前 MS3 资产和 solver 不能自动视为论文原始配置。

- [PickCube](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/pick_cube.py)：成功由目标距离和机器人静止组合，持续支撑与释放需独立评分。非 state 的额外输入仍含抓持状态和目标位置；选择 RGB 不自动代表纯视觉。
- [PushCube](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/push_cube.py)：平面接近与高度上界不能独立排除物体穿到桌下，需加入明确负例。
- [旋转任务](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/dexterity/rotate_single_object_in_hand.py)：Level0–3 使用 AllegroHandRightTouch，累计无符号角度。128 步往返摆动的代数反例可超过4π而净转角为零；这不是已运行的物理漏洞复现。独立记录相对手掌的有符号旋转、掉落与换指；PD 估算力矩不当作实测力矩。
- [手部控制](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/agents/robots/allegro_hand/allegro.py)：位置/增量 PD 的目标关节值不同于实际关节状态。[触觉输入](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/agents/robots/allegro_hand/allegro_touch.py) 给出接触冲量幅值，不是经过标定的触觉图像；逐字段审查输入权限。

[源码记录](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/maniskill-task-audit.json) · [代数负例](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/maniskill-angle-counterexample.json)。#47/#48 同时保留上游成功与独立评分，并验证重置隔离。实际安装 solver 身份与资产条款仍待准入。

## 合成、重定向与数据：复用什么

[方法账本](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-method-decisions.json)记录候选的一手定位、未知项、决策和预算；均未运行复现。

| 方法 | 已核查边界 | 复用决定与可证伪实验 |
|---|---|---|
| Dexonomy | 固定源码的 MuJoCo3.3.3 属历史配置。六轴加载和末态误差是不同验收；默认5cm/15°不是本项目阈值。hard配置注释与执行代码不一致：代码仍用noslip2、impratio10，只降低摩擦。 | 借鉴抓型分类及加载协议；同物体/手型/载荷比较3类抓型，逐项输出失效方向。记录运行时参数，不照抄注释。 |
| Dex1B | 数据数量不证明可执行轨迹率或接触模式覆盖；实现身份、solver和资产条款未核实。 | 暂缓大数据；固定小样本分别计生成、执行、独立通过率，保留过滤失败。 |
| SPIDER | 固定README明确保存状态回放不证明动作重跑等价；非商业条款与数据来源分别审查。 | 借鉴回放审计；同一动作序列自由演化与状态回放对照，禁止在评分期间注入物体状态。 |
| CHORD | 附录B含物体/接触状态和内部物体辅助控制；全身变体观测不同。reset后辅助力有warm-up，不能只看策略动作维度。 | 借鉴接触力矩空间与辅助力记录；逐阶段记录外力，正式独立评分排除未披露辅助。 |

当前只做协议研究，不训练或下载大资产。候选小探针最多10工况、单个合格执行者、30分钟上限；缺源码/solver/资产依据或独立物理评分失败即停止。要执行前另建/补全独立Issue及依赖，不能将本表当成实现授权扩张。

## 触觉模型不能混同物理后端

| 工作 / 审查版本 | 可复用边界 | 最小反证实验 |
|---|---|---|
| [HydroShear v1](https://arxiv.org/html/2603.00446v1) | 路径相关剪切观测，假设平面弹性体及允许侵入的柔顺接触；教师与学生输入不同。 | 同终态用不同路径及脱离重接触到达，分别检查记忆、重置和刚体动力学。 |
| [Tacmap v2](https://arxiv.org/html/2602.21625v2) | 几何触觉图；观测几何不同于物理碰撞几何。 | 只改变感知分辨率，分别比较图像误差与接触合力。 |
| [PTLD v3](https://arxiv.org/html/2603.04531v3) | 需要真实环境的特权数据采集再蒸馏，不是零数据迁移。 | 分别审计教师、价值网络、采集端和部署策略的输入，移除部署禁用的物体位姿。 |
| [TacEx v1](https://arxiv.org/html/2411.04776v1) | 胶体物理、光学与标记合成分开；历史打滑不能推广为当前PhysX缺陷。 | 相同给定轨迹分别比较力/形变与光学输出。 |
| [Taccel v2](https://arxiv.org/html/2504.12908v2) | ABD/FEM IPC及运动学约束，接触和驱动要分别准入。 | 固定网格的压入、剪切、卸载，记录残差、力、侵入及分阶段开销。 |

独立实现的限定几何占据观测器已完成[三批有界实验](https://github.com/huangkiki/Dexlab/blob/main/docs/synthetic-tactile.zh-CN.md)。这不代表接入或认证了上游触觉运行时、剪切记忆或硬件精度。上游输入、solver与许可边界仍见[方法账本](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/dexterity-method-decisions.json)。

## 抓取评估与双臂数据生成

| 方法 | 证据边界 | 决策与可证伪的小实验 |
|---|---|---|
| [BODex v3](https://arxiv.org/html/2412.16490v3) | 论文重力保持超过3秒，容许5cm/15°偏差；几何穿透和合成速度是另外的指标。 | 借鉴加载协议，保留 DexLab 阈值；固定物理参数比较同一组抓取。 |
| [DexGraspBench 源码入口](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | README 明确物体质量由30g变100g，kp由1变5，与 BODex 论文不同。 | 分别记录两套配置，独立排查质量和驱动变化，之后才比较方法。 |
| [DexMimicGen v2](https://arxiv.org/html/2410.24185v2) | 变换后的动作段开环执行，只保留整段任务成功的演示。 | 分开统计尝试、执行和保留数量；失败轨迹也进入独立评分。 |
| [DexMachina 源码入口](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md)及[论文](https://arxiv.org/html/2505.24853v1) | 安装依赖自定义 Genesis/rl-games 分支；训练使用逐渐衰减的虚拟物体辅助控制。 | 暂缓直接接入运行时；借鉴辅助力记录，独立评估时要求辅助物体力为零。 |

以上是研究决策，不是新增已支持任务。官方稳定引擎准入、可执行源码审查及资产许可仍是前置条件。可选探针保持最多10例、30分钟预算，尚未启动训练。

## 布料与工具操作：成功视频不能单独证明什么

[DexGarmentLab v3](https://arxiv.org/html/2505.11032v3) 使用粒子 PBD，并调节黏附和摩擦。没有固定连接块不等于仅靠摩擦抓取；附录I仍讨论粒子空隙、穿透与抖动。借鉴任务分类，但须单独检验黏附：固定网格和驱动，分别改变黏附与摩擦，检查张手释放和残余吸附。固定版本 README 面向 IsaacSim4.5.0，尚未通过本项目最新稳定版准入。

[DexScrew v2](https://arxiv.org/html/2512.02011v2) 区分仿真特权教师、本体感知学生、真机遥操作和触觉行为克隆。这才是其仓库关联的论文，不能与另一篇关节工具论文混淆。借鉴各阶段输入审计，分别统计有符号旋转、轴向进度和完整完成；缺少真实数据时暂缓硬件复现，不能把进度比例改称成功率。

两者仍为研究参考，资产和运行时准入未完成。本次审查没有运行布料或工具训练。

## 本体与驱动

[腱驱动手 MPC v3](https://arxiv.org/html/2411.06183v3) 区分目标关节角、腱命令与估计关节状态。VLM 根据视频调整目标函数权重，MPC 则使用测得的物体状态，并非直接纯 RGB 控制。借鉴这一接口审计，分别测试状态估计延迟和执行器限幅，同时记录控制超时与保持失败。

[形态与驱动研究 v1](https://arxiv.org/html/2609.05206v1) 分离运动学、驱动映射及其组合，实验使用历史 MuJoCo3.10.0。ACBH 模型及实验代码需向作者申请，不能称完整公开可复现。借鉴在已有合法模型上对执行器→关节、关节→指尖映射的有限差分检查；结构条件数不能替代动力学任务验收。

两者仍为协议参考，准确源码、资产条款及独立运行证据尚有缺口；本轮不引入新手模型或训练。

## 精度、任务组合与点轨迹策略

- [Labimus v2](https://arxiv.org/html/2606.31037v2)：借鉴完成度、精度与阶段诊断的分开评分。其干粉近似使用刚体微元，不能由此认定本项目已具备颗粒物理能力。在已有任务中测试“动作完成但误差超限”的负例。
- [LabDex v1](https://arxiv.org/html/2608.18618v1)：借鉴原子/组合任务边界及命令/状态溯源。真机与仿真共用任务名称不证明动力学匹配，准确 solver 仍未核实。测试第二阶段失败的两阶段过程。
- [Dex4D v1](https://arxiv.org/html/2602.15828v1)：教师完整几何与学生部分配对点输入不同。借鉴可见性审计，不改称原始 RGB 策略。测试目标丢失且不补入真值点的行为。

三者仍为研究参考；候选探针仅用已有资产，保持10例/30分钟预算。完整实验室、颗粒与策略训练接入暂缓。

## 其余候选：已筛选，不等于已复现

以下仅据固定版本摘要进行筛选，保留为参考或暂缓实现；探针是本项目提出的验证方案，不是已有实验结果。方法账本明确保留源码、许可和运行时未知项。

| Candidate / 候选 | Decision / 决策 |
|---|---|
| [MuJoCo Playground](https://arxiv.org/abs/2502.08844v1) | 参考运行时设计；先完成 ManiSkill 准入，再考虑其他任务接入 |
| [Physics simulator survey](https://arxiv.org/abs/2505.01458v2) | 仅作分类参考；不能代替引擎资格证据 |
| [TeleOpBench](https://arxiv.org/abs/2505.12748v2) | 借鉴遥操作接口与时延协议；暂缓完整基准接入 |
| [HumanoidGen](https://arxiv.org/abs/2507.00833v2) | 借鉴显式标注溯源；暂缓生成系统 |
| [Articulated-tool refinement](https://arxiv.org/abs/2509.23075v3) | 借鉴关节阻力敏感性协议；暂缓依赖真机的学习 |
| [VIDEOMANIP](https://arxiv.org/abs/2602.09013v2) | 借鉴重建与动作执行的区别审计；暂缓训练 |
| [FlowHOI](https://arxiv.org/abs/2602.13444v1) | 参考手物交互表示；暂缓生成流程 |
| [Grasp-to-Act](https://arxiv.org/abs/2602.20466v1) | 借鉴动态载荷保持协议；暂缓学习控制器 |
| [Structural Action Transformer](https://arxiv.org/abs/2603.03960v1) | 参考关节角色表示；暂缓策略训练 |
| [UltraDexGrasp](https://arxiv.org/abs/2603.05312v1) | 借鉴抓取策略分组；暂缓大规模数据 |
| [Sim-to-real generalization study](https://arxiv.org/abs/2603.22876v2) | 借鉴单因素配对校准；暂缓真机排名 |
| [Blind tactile grasping](https://arxiv.org/abs/2606.11767v2) | 借鉴接触事件标定；缺少真机数据时暂缓 |
| [TouchWorld](https://arxiv.org/abs/2607.07287v2) | 参考规划与反馈时钟分离；暂缓基础模型系统 |
| [Temporal robustness study](https://arxiv.org/abs/2609.01453v1) | 借鉴不同执行速度的配对评估；暂缓训练 |
| [Dex-X](https://arxiv.org/abs/2609.07747v3) | 参考触觉监督来源；暂缓可执行接入 |

## 三项视觉与数据方法的定向审查

| 来源 | 借鉴决策与边界 |
|---|---|
| [DexGraspNet2.0](https://arxiv.org/html/2410.23004v1)，§3.2–3.3 | 借鉴物体/杂乱程度划分与候选统计。单视角深度生成抓取姿态后验收抬升，不代表连续 RGB 控制；分别记录碰撞淘汰、抬升与持续保持。 |
| [ManipTrans](https://arxiv.org/html/2503.21860v1)，§3–4 | 借鉴有效重力、摩擦与阈值记录。训练放宽物理及终止条件，评分前须冻结正常评估配置；暂缓训练。 |
| [人形视觉 RL](https://arxiv.org/html/2502.20396v2)，感知配置 | 借鉴固定标定相机与跟踪特征溯源。头部深度及第三视角分割得到的3D特征并非原始纯 RGB 输入；遮挡测试不允许用仿真真值填补丢失特征。 |

这些定向论文审查不代表源码或资产许可已通过、已安装准确 solver 或已完成运行复现。
