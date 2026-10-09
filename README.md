# DexLab

**以经典物理规律与已有经验公式为参照，通过可复现实验，研究接触与摩擦对机器人抓取的影响，评估物理仿真的可信度。**

我们用斜面摩擦、一维碰撞和夹持实验，对照解析解、守恒律及有来源的经验关系，检查仿真中的力、运动与接触。这个仓库提供**实验结论、可复现代码和原始数据**，分析哪些可测因素影响抓取表现，并明确结论的适用条件。

[English](README.en.md) · [中文文档站](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [实验报告](docs/site/zh/results.md) · [安装与复现](docs/installation.zh-CN.md) · [版本与数据下载](https://github.com/huangkiki/Dexlab/releases)

文档站按每次 main 合并自动更新；首页提供实验结论、同工况对照与六引擎覆盖状态。

## 引擎、求解器与版本

下表区分**已有证据**与**同工况对照**；不同任务、版本的结果不能拼成统一排名。版本是报告中的实测版本，不代表当前最新版。

| 引擎 / 运行版本 | 求解器与数值配置 | 已有证据范围 |
|---|---|---|
| MuJoCo 3.15.0 | Newton 求解器；Euler 积分；elliptic 摩擦锥；100 次迭代上限，容差 1e-10 | 下方九组斜面配对，以及碰撞、夹持诊断 |
| SuperDex 1.0.0 FP64 | 同字节配置重建：Newton、线性 AUTO（小系统源码路径为稠密 LDLᵀ）、C1 正则化摩擦；历史记录：Backward Euler、100 次上限、绝对/相对容差 1e-9。[证据与历史遥测缺口 #124](docs/superdex-solver-audit.zh-CN.md) | 下方九组斜面配对；[冻结配置](docs/evidence/incline-comparison/manifest.json) |
| Genesis 1.4.3 CPU FP64 | 历史记录：Newton / approximate_implicitfast / elliptic，noslip=0；[源码解析与历史有效参数读回缺口 #125](docs/genesis-solver-audit.zh-CN.md) | [16 组夹持力限额实验](docs/force-limit-results.zh-CN.md)，未参与下方斜面配对 |
| Newton Physics 1.6.1 / Warp 1.18.0 | CPU SolverXPBD，float32；4 次迭代，dt=1 ms | [球–平面及负例](docs/newton-contact.zh-CN.md)，不等于抓取对照 |
| PhysX（历史 Isaac Sim 5.1；UniSim 及直接 SDK 路径） | 三组 SDK 对照读回 PGS/TGS 与外力时序；表面布料单列。[分批审计与原生核心身份缺口 #126](docs/physx-solver-audit.zh-CN.md) | [历史接触实验](demos/contact-benchmark/README.zh-CN.md)；不属于下方双引擎批次 |
| Drake | 尚无已验收的运行版本或求解器结果 | 接入与首轮评测见 [#117](https://github.com/huangkiki/Dexlab/issues/117) |

公开结论中的事实与来源缺口必须关联可验收 Issue，并优先于新增能力处理。SuperDex 官方包身份与配置重建、Genesis 历史求解器枚举已核实；历史读回缺口分别由 [#124](https://github.com/huangkiki/Dexlab/issues/124)、[#125](https://github.com/huangkiki/Dexlab/issues/125) 跟踪，PhysX 已恢复三组原生场景求解器读回，[#126](https://github.com/huangkiki/Dexlab/issues/126) 保留各批次核心／加载库身份及其余缺失读回。重建、源码推导与历史原生读回分别标注。

后续评测必须覆盖 **MuJoCo、SuperDex、Genesis、Newton Physics、PhysX、Drake** 及适用的已登记求解器配置。每份报告列出完整工况矩阵：已通过、已失败、受阻、不支持或未运行；缺项必须关联 Issue，补齐前仅称阶段结果。既有结果保留原范围，不追认成全引擎评测。ManiSkill/SAPIEN/Isaac Sim 是接入层，UniLab 是任务层，不能重复计作独立引擎；Newton Physics 与 MuJoCo 的 Newton 算法也不是一回事。

## 引擎对比：同一个方块，两种固定配置

官方 **MuJoCo 3.15.0** 与 **SuperDex 1.0.0 FP64**：相同 40 mm／64 g 方块、初态与重力，三个步长（2／1／0.5 ms），每例 2 秒。复用已有 MuJoCo 数据，新增九例 SuperDex 对照。

| 工况 | MuJoCo（impedance=0.9） | SuperDex（固定 penalty 配置） |
|---|---|---|
| 15° 静摩擦，μ=0.5 | 漂移 **1.301–1.336 mm**，0/3 通过 | 漂移 **0.708–1.132 mm**，2/3 通过 |
| 35° 滑动，μ=0.5 | 转动、间歇失去支撑，0/3 通过 | 评分窗内稳定滑动，3/3 通过 |
| 15° 名义零摩擦 | 速度 RMSE **8.21×10⁻⁵ m/s**，3/3 通过 | 速度 RMSE **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s**，3/3 通过 |

**结论：接触配置会改变漂移和稳定性，不能只凭引擎名称判断。** SuperDex 在这组固定配置下满足更多判据，但细化步长反而增大了静态漂移；已有 MuJoCo impedance=0.99 结果的漂移仅 **0.141–0.179 mm**，小于上述 SuperDex 结果。零摩擦差异还涉及 MuJoCo 的原生摩擦下限。速度误差使用 0.5–2 s 窗口；初始瞬态、全部失败及不同接触模型的条件见报告。

[完整对照、参数和原始数据](docs/incline-comparison-results.zh-CN.md)。这些计数是固定工况的容差判定，不能推广为真实材料精度或通用引擎排名。

## 我们得出了什么结论

### 1. 碰撞后的速度正确，不代表碰撞过程准确

在官方 MuJoCo 3.15.0 的一维弹性碰撞实验中，18 个工况均通过末态判据，但接触重叠达到 **5–20 mm**。进一步改变刚度和步长后，27 个工况中有 **24 个末态通过，只有 2 个同时满足预设的 1 mm 重叠预算**。因此，评价碰撞必须同时看速度、能量和接触过程。

[弹性碰撞结果](docs/elastic-impact-results.zh-CN.md) · [刚度与穿透对照](docs/impact-stiffness-results.zh-CN.md) · [离散接触解释](docs/impact-discrete-results.zh-CN.md)

### 2. 求解更精确，不一定抓得更稳

在 MuJoCo 3.15.0 的标准方块夹持诊断中，收紧求解容差显著减小了力与运动记录之间的残差，但方块在加载一秒后仍下滑约 **2 mm**。数值力平衡改善与物体保持是两个不同结果，必须分别测量。

[夹持承载与滑移](docs/pinch-load-results.zh-CN.md) · [六个工况的残差诊断](docs/pinch-impulse-results.zh-CN.md)

### 3. 夹持力限额会改变抓取成败

在 Genesis 的固定标准方块夹具中，16 个工况显示：**0.2/0.4 N 力限额无法保持物体，0.8/10 N 能保持并释放**；在 ±2 mm 初始偏移下保持了这一结果。这给出了该夹具的可复现实验边界。

[全部工况、失败和原始记录](docs/force-limit-results.zh-CN.md)

![标准方块夹持、抬升与释放](demos/contact-benchmark/media/genesis-pinch.gif)

*上图为 Genesis 实测状态的连续近景回放，由 MuJoCo 显示；对应固定配置演示，全部力限额工况见报告。*

### 4. 一个场景调好的接触参数，不能直接当作通用材料参数

三个固定接触配置迁移到十组质量／尺寸组合后，**30 次运行均未满足指定的合成动态响应联合目标**。这说明这些参数映射的适用范围有限，需要在不同载荷和尺寸下检查。

[参数迁移实验与全部结果](demos/contact-benchmark/TRANSFER.zh-CN.md)

这些结论分别对应报告中冻结的引擎版本、模型和工况，属于解析模型与数值实验结论；真实材料精度需要实测参照。它们不能合并成引擎优劣排名。

## 下一阶段：统一驱动与夹持失效边界

[开发路线](docs/pinch-boundary-roadmap.zh-CN.md) · [专题 Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [研究总任务](https://github.com/huangkiki/Dexlab/issues/130)

[共同协议与数据接口 v1](docs/pinch-boundary-protocol.zh-CN.md)已实现：固定有限夹具、1 ms 外部 PD 时钟、594 个正式项、24 个对照及最多 32 个资格／桥接项，提供工况展开与记录结构校验。下一步为双后端资格与独立评分；后端尚未准入，正式批次尚未运行。六引擎缺项继续跟踪，历史结果保持原范围。

## 学习各个引擎：Sim Atlas

**Sim Atlas · 仿真图谱** 为每个引擎提供独立学习仓库，沿应用和原理源码两条路线，讲解建模、状态与时间、控制、接触求解、传感渲染、并行与扩展。

[MuJoCo Atlas](https://github.com/huangkiki/mujoco-atlas) · [SuperDex Atlas](https://github.com/huangkiki/superdex-atlas) · [Genesis Atlas](https://github.com/huangkiki/genesis-atlas) · [Newton Atlas](https://github.com/huangkiki/newton-atlas) · [PhysX Atlas](https://github.com/huangkiki/physx-atlas) · [Drake Atlas](https://github.com/huangkiki/drake-atlas)

首批导读与固定版本源码地图已交付，完整专题仍在开发。当前先理解引擎机制，后续实验复用 DexLab 的版本、配置与工况记录。课程完成度与上方实验证据覆盖分别记录。

## 从哪里开始

- **看结论与图表：** [完整实验报告](docs/site/zh/results.md)，以及[阶段总结](docs/holiday-report.zh-CN.md)。
- **复算结果：** 每份报告链接冻结协议、评分代码和原始记录；公开归档见 [Releases](https://github.com/huangkiki/Dexlab/releases)。
- **运行演示：** 按[安装说明](docs/installation.zh-CN.md)配置环境后，运行下方苹果梗抓取示例。

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或 --backend superdex；无显示环境添加 --headless
```

演示的 SDF 构建和规划完成后打开窗口，无需模型 API key。各研究实验的版本与运行命令以对应报告为准。

后续工作、未完成任务和阻塞统一在 [Issues](https://github.com/huangkiki/Dexlab/issues) 跟踪。

## 代码与来源

实验使用官方物理引擎，保留参数来源、失败工况与独立评分。[实验目录](demos/) · [开发流程](docs/autoresearch.zh-CN.md) · [资产来源与许可](docs/ASSETS.zh-CN.md)

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[Genesis](https://github.com/Genesis-Embodied-AI/Genesis)、[Newton](https://github.com/newton-physics/newton)、[OpenArm](https://github.com/enactic/openarm) 与 [Wuji](https://github.com/wuji-technology)。代码采用 [Apache-2.0](LICENSE)。
