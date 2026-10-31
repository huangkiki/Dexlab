# DexLab

## Contact-rich robotics, beyond rigid-body simulation.

DexLab 是一个以物理为中心的研究平台，用于研究接触、形变和材料分离条件下的机器人操作。

[English](https://huangkiki.github.io/Dexlab/en/latest/index.html) · [实验目录](experiments.md) · [研究协议](model-evaluation.md) · [快速开始](#quickstart) · [系统结构](#architecture) · [Uranus 后端](uranus-backend.md)

> 当前已有原生命令、接触读回、独立评分、离线证据与多项接触实验；远程模型执行器、公开 leaderboard 和跨任务统一结论仍在建设中。

## Demo gallery

以下动图来自 DexLab 的真实仿真录像或记录状态回放。每项结果只适用于对应版本、材料假设和验收协议。

| 抓取与抗滑移 | 海绵擦拭与接触依赖 |
| --- | --- |
| <a href="wuji-contact.html"><img src="_static/wuji-contact/comparison.gif" width="100%" alt="Wuji 点接触与合成抗扭接触对照" loading="lazy"></a><br>相同控制下，点接触改为合成抗扭接触，两秒保持漂移从 **2.734 mm** 降至 **1.025 mm**。 | <a href="rss-wiping.html"><img src="_static/studio/rss.gif" width="100%" alt="辅助保持下的海绵擦拭回放" loading="lazy"></a><br>辅助保持下 **3/3** 通过；去掉辅助后 **0/3**，最终清洁率约 **95.47% / 39.92%**。 |
| **柔性物体操作** | **切割与拓扑变化** |
| <a href="cloth-comparison.html"><img src="_static/cloth-studio/grasp.gif" width="100%" alt="记录仿真中的机器人夹布" loading="lazy"></a><br>机器人能够夹住并移动布片，但完整折叠仍失败：当前记录的最大边长应变为 **12.55%**，超过预设 5% 上限。 | <a href="cut-push.html"><img src="_static/cutting/showcase.gif" width="100%" alt="豆腐和香蕉切割的记录状态表面回放" loading="lazy"></a><br>连续切割与刀面推动会产生真实的状态拓扑变化；完整报告还记录接触力、材料分离与失败。 |

<section id="model-evaluation"></section>

## Why DexLab?

机器人策略在仿真中失败时，我们通常只看到一次失败。它可能来自策略、控制器、场景配置、接触离散、材料模型或数值求解。

> **When a robot fails in simulation, is it the policy that fails, or the physics we trusted?**

DexLab 的核心工作不是给单一引擎或模型打总分，而是让下面这些问题可以被实验和证据回答：

- 相同几何、载荷和控制下，不同接触模型会改变“抓住、滑动、释放”的判断吗？
- 更小步长、更密网格或更多迭代，真的更接近物理，还是只改变了数值行为？
- 机器人能夹住布片，何时才会真正完成折叠、送布和正确释放？
- 切割、摩擦和材料分离应该怎样记录和验收，而不是只看一段视频？
- 一个 policy 或 API 的排名，能否在替换物理后端后保持不变？

当前主体是 **Physics Research Platform**。长期愿景是 **Simulation–Learning Co-evolution**：用模型暴露仿真缺口，再用更可信的仿真改善模型。Model/API benchmark 是连接两者的实验基础设施。

<section id="research-selection"></section>

## Research areas

| 方向 | 研究问题 | 当前入口 |
| --- | --- | --- |
| **Contact physics** | 法向响应、摩擦、保持、滑动、冲量和释放是否能被独立复核？ | [接触力学](contact-response.md) · [保持与滑移](wuji-contact.md) |
| **Deformable objects** | 夹持、垂坠、拉伸、层间接触和脱手如何分别验收？ | [布料对比](cloth-comparison.md) · [回放与近景](studio-rendering.md) |
| **Topology-changing interaction** | 切割和材料分离如何记录接触、连通性与材料响应？ | [切割与推动](cut-push.md) |
| **Cross-backend evaluation** | 相同物理目标和控制下，不同引擎、积分器与求解器何时可以比较？ | [引擎与求解器](engines.md) · [选型](selection.md) |
| **Policy and API evaluation** | 模型失败、适配器失败和物理无效运行如何分开？ | [评测协议](model-evaluation.md) · [RoboAPI 适配](https://github.com/huangkiki/Dexlab/blob/main/docs/roboapi-poke.zh-CN.md) |

<section id="research-findings"></section>

## Experiments and findings

| 实验 | 条件 | 结果和解释 |
| --- | --- | --- |
| **接触表示改变抓取结论** | Wuji 双指夹球，相同控制和保持窗口 | `condim=3` 漂移 **2.734 mm**，超过 2 mm；`condim=4` 为 **1.025 mm**。接触模型本身就是模型结论的一部分。 |
| **擦拭成功率依赖辅助保持** | RoboSimStudio `wipe_the_bar`，固定记录与评分 | 原版 **3/3**，清洁率约 **95.47%**；去掉辅助后 **0/3**，约 **39.92%**。 |
| **接触离散改变失效边界** | 同一圆柱、质量、力命令和步长，只改变表面三角数 | `256 → 1,024 → 4,096` 三角形时，峰值穿透为 **2.267 → 0.858 → 0.481 mm**。 |
| **同场景抓取可能依赖于后端** | 苹果抓梗，10 个配对回归场景 | 当前默认配置 MuJoCo 通过 **1/10**，SuperDex 通过 **10/10**；更小步长没有单调改善穿透。 |
| **夹住布不等于完成折叠** | OpenArm + Wuji，被动布料 | 单手夹点、抬升与释放通过；完整折叠因应变、残余接触和最终几何未达标而失败。 |

这些结果共同指向一个问题：**成功视频不足以证明材料模型、接触响应和下游策略都可迁移。**

[完整实验目录](experiments.md) · [全部结果与失败](results.md) · [研究经验](experience.md)

(live-lab)=
## Browser live lab

下面直接在当前网页运行 MuJoCo 3.17 WebAssembly，并使用浏览器本地 WebGPU 渲染。它展示同一方块、重力、摩擦、初态和时间步长下的不同求解配置；浏览器运行不会继承原生实验成绩。

```{raw} html
<div class="dexlab-live-lab">
  <iframe
    src="../../_static/live-lab/index.html?embed=1"
    title="DexLab 浏览器实时仿真实验"
    loading="lazy"
    allow="fullscreen"
  ></iframe>
</div>
```

<a id="architecture"></a>
## Architecture

```text
DexLab
├── Tasks and protocols
│   └── scenes, initial states, seeds, budgets, acceptance
├── Systems under test
│   └── RoboAPI / VLA / policy / world model
├── Environment backends
│   ├── Native physics: MuJoCo / Newton / SuperDex / Genesis / PhysX / Drake
│   └── Candidate generative backend: Uranus
├── Action execution
│   └── IK / controller / session adapter
└── Evidence and scoring
    └── success, native state, contact readback, attribution, cohorts, anti-gaming
```

原生物理后端拥有状态推进和接触读回；控制器把模型动作映射成可执行目标；任务评分器独立于被测模型。每次生成结果都有机会保留完整尝试、失败原因和可复算证据。

### Ecosystem backend: Uranus

[Uranus](https://arxiv.org/abs/2609.24815) 是 D-Robotics 的机器人视频世界模型，从未来 `qpos`、相机和机器人结构生成多视角观测。它目前是 **documented candidate generative backend**，不是已验证物理后端。

接入链路为 `RoboAPI → IK/controller → qpos → Uranus → RGB → task scorer`。它提供视觉观测，不提供原生接触状态、任务 success 或物理真值。[阅读完整介绍、候选任务和证据边界](uranus-backend.md)。

(quickstart)=
## Quick start

Linux x86_64 上安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后，运行苹果抓梗：

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh \
  --backend mujoco \
  --output demos/apple-stem-grasp/runs/first-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

验收器会写出 `summary.json`；全部检查通过时 `passed: true`。14 秒是仿真时长，实际计算通常更久。无桌面环境添加 `--headless`，每次运行使用新输出目录。

如果只想检查证据链、不安装仿真器，可从[安装与最小复现](quickstart.md)开始。完整依赖、资产和命令见该页。

## Research roadmap

1. **Contact and material response：** 将接触刚度、阻尼、摩擦与真实测量分开校准，再讨论 engine ranking。
2. **Deformable manipulation：** 从夹持、送布和释放扩展到可复核的折叠几何、自接触和材料点跟踪。
3. **Topology-changing tasks：** 为切割、分离和粘连建立连续几何、接触力与结果判据。
4. **Cross-backend attribution：** 区分 solver、integrator、collision geometry、precision、timestep 和 framework wrapper。
5. **Policy and neural backends：** 检查 API 排名和任务结论能否从原生物理迁移到 learned world model。
6. **Co-evolution：** 在证据支持后，用模型失败推动仿真改进，再用改进的仿真产生更可信的策略训练与评测。

<section id="research-diagnosis"></section>

## Evidence and boundaries

- 任务成功不等于物理真实；数值一致不等于现实正确。
- 仿真通过不等于真机成功；渲染通过不等于视觉控制。
- 不同引擎覆盖的任务、材料模型和验收条件不同，不是统一排行榜。
- 失败、无效运行和缺失读数都必须保留；不通过放宽阈值或删除反例制造成功。
- Uranus 和远程模型评测仍是候选能力，不应从论文或接口存在推断 DexLab 已完成复现。

<section id="research-scope"></section>

## Documentation and citation

[实验目录](experiments.md) · [研究经验](experience.md) · [求解配置](solver-taxonomy.md) · [覆盖矩阵](coverage.md) · [参与贡献](contributing.md) · [当前工作与暂停状态](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.zh-CN.md)

项目尚未发布配套论文；引用本仓库时请使用仓库 URL 和具体 commit / release，而不是引用尚未存在的论文结果。

```bibtex
@software{dexlab2026,
  author  = {DexLab contributors},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```

```{toctree}
:hidden:
:maxdepth: 1

Solver 失败复盘 <solver-failure-audit>
共同进化与模型评测 <model-evaluation>
高质量轨迹回放 <studio-rendering>
布料引擎对比 <cloth-comparison>
实验目录 <experiments>
安装复现 <quickstart>
研究结果 <results>
完整覆盖 <coverage>
研究经验 <experience>
诊断方法 <diagnosis>
Wuji 抓持与抗扭接触 <wuji-contact>
接触预测诊断 <contact-response>
海绵擦拭与辅助保持对照 <rss-wiping>
连续切割与刀面推动 <cut-push>
香蕉单刀测力 <banana-force>
豆腐状软块对半切 <cutting>
香蕉连续切片 <banana-cutting>
豆腐交叉浅切 <tofu-scoring>
切割方法对比 <cutting-comparison>
豆腐连续两刀与独立运动 <tofu-comparison>
切割保真度与动态测量 <cutting-fidelity>
切割表面重建 <cutting-surface>
多求解器同步与 preCICE <solver-coupling>
求解配置分层 <solver-taxonomy>
可视对照 <visual-comparisons>
LIBERO 原生流程 <libero-workflow>
AMP 记录器一致性失败 <amp-lift>
场景选型 <selection>
引擎与模型 <engines>
Uranus 生成式环境后端 <uranus-backend>
研究路线 <dexterity>
研究账本 <research-ledger>
基准 <benchmark>
外部参考 <references>
参与贡献 <contributing>
```
