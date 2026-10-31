# DexLab

**接触仿真的失败归因实验台。**

DexLab 把“机器人为什么抓不住、会滑脱，碰撞结果为什么不对”拆成几何与输入、控制、接触模型、求解器和评分／记录五层。它用冻结工况、原生读回、独立评分、负例与可下载原始记录定位**第一处失效**，而不是用一段成功视频猜测哪个引擎更好。

[English](README.en.md) · [Live Lab](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab) · [完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [全部报告](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html) · [快速复算](#quickstart)

## 先看一个完整案例

![Wuji v3 点接触与 v4 合成抗扭接触的完整同步回放](docs/evidence/wuji-contact/comparison.gif)

[Wuji 双指夹球](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)：同一控制与动作下，将点接触改为合成抗扭接触，两秒保持位移从 **2.734 mm** 降到 **1.025 mm**，通过原 2 mm 门槛。记录可以离线复算；这个结果说明该夹具的接触项发生了变化，**不证明 solver 失效或真机准确性**。

## 研究深度不只体现在动图

下面四项覆盖不同研究问题；分母、配置和参考并不相同，不能合并成总成功率或引擎排行榜。

| 已研究的问题 | 冻结实验 | 关键实测结果 | 不能据此说什么 |
| --- | --- | --- | --- |
| **同一物理问题，换求解配置会怎样？** | 40 mm、64 g 方块；15° 静摩擦、35° 滑动、名义零摩擦；0.5／1／2 ms。[双引擎斜面对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html) | MuJoCo 3.15.0 `Newton / Euler / elliptic` 的静摩擦漂移为 **1.301–1.336 mm**，0/3 通过；SuperDex 1.0.0 FP64 为 **0.708–1.132 mm**，2/3 通过。MuJoCo 的滑动工况还出现显著转动与接触丢失。 | 固定基线差异不是通用引擎排名；历史 MuJoCo `impedance=0.99` 的漂移反而更小。 |
| **更小步长或更紧容差是否自动解决问题？** | 16 次接触起始步长实验＋12 次独立容差对照。[接触起始细化](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/REFINEMENT.zh-CN.md) | SuperDex 在收紧停止容差后，有摩擦 `0.5 vs 0.125 ms` 的位置差仍约 **3.206 mm**。细化不是自动真值；改变步长、改变容差和改变物理模型必须分开解释。 | 不能把“更细网格”直接当作真值，也不能仅凭求解器返回 `CONVERGED` 宣称跨步长收敛。 |
| **一个场景通过后，参数能否直接迁移？** | 3 个固定配置 × 10 组质量／尺寸条件，共 30 次配对运行。[迁移报告](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/TRANSFER.zh-CN.md) | 工程检查 **1/30** 通过，瞬态目标 **0/30** 通过，联合目标 **0/30** 通过；全部失败保留。 | 失败不支持“所有映射都无效”或“某引擎算法错误”的结论，只支持：这组固定参数不能直接迁移。 |
| **从数值诊断怎样回到机器人接触？** | Wuji 抓持、保持、卸载和合成抗扭接触对照。[完整协议与证据](https://github.com/huangkiki/Dexlab/blob/main/docs/site/zh/wuji-contact.md) | 点接触改为合成抗扭接触后，两秒保持位移 **2.734 → 1.025 mm**；评分同时保留缓慢漂移条件。 | 抓持通过不等于手内操作完成，也不等于真实指腹材料已标定。 |

![30 组质量／尺寸迁移的全部失败](docs/evidence/contact-transfer-v1.png)

## 一个结论怎样成立

DexLab 区分“能跑起来”“数值自洽”“物理参照成立”“任务完成”和“根因可信”，再按下面的顺序排除竞争解释：

1. **冻结问题。** 先写明参考物理、几何、质量／惯量、初态、控制时刻、指标、阈值、版本、预算和停止条件。
2. **保留原生证据。** 保存实际参数、状态、速度、接触力／冲量、求解状态、原始记录和源码／资产哈希；缺测量记未知，不填零。
3. **独立验收。** 用解析关系、力／动量平衡、禁碰撞／零摩擦／释放等负例检查记录和评分，不只相信单次末态或成功视频。
4. **做受控敏感性。** 分别改变步长、求解容差、载荷、质量或接触尺度；可以归因的变量必须隔离，不能把几何、控制器和 solver 一起换掉后宣称算法优劣。
5. **保留失败和外推边界。** 原始数据、失败分母、成本、未观测字段和恢复条件一起发布；一个配置的结果只属于该版本、场景和验收条件。

### 不要把一个名字当成一种算法

| 必须分开的记录层 | 例子 | 为什么不能压平成一行 |
| --- | --- | --- |
| 时间积分 | MuJoCo Euler；SuperDex backward Euler | 积分方法、步长和状态更新时刻不同会改变接触瞬态。 |
| 外层约束／非线性 solver | MuJoCo PGS／CG／Newton；SuperDex Newton；PhysX PGS／TGS | PGS、Newton 和 TGS 不都在同一数学层；相同迭代数也不代表相同工作量。 |
| 内层线性 solver | SuperDex GMRES／LDLᵀ 等可选路径 | `AUTO` 是选择策略，不是“实际执行了某个分支”的证据。 |
| 接触与摩擦模型 | elliptic／pyramidal 摩擦锥、C1 正则化、PhysX patch friction | 相同名义 μ 不保证相同低速响应、粘滑或组合律。 |
| 精度与预算 | FP32／FP64、0.125–2 ms、迭代上限、绝对／相对容差 | 数值精度和停止条件会改变误差—成本关系。 |
| 运行路径 | 原生引擎、MJWarp、Isaac Sim 等框架接入 | 同一核心经过导入、转换或不同状态布局后，有效模型仍可能不同。 |

这六层共同构成“被比较的配置”。完整术语、源码依据和未知身份见[求解配置分层](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html)，逐配置覆盖与失败见[完整矩阵](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)。

## 已经能运行和检查什么

以下只列代表性入口。点击实验或动图可看完整报告、冻结参数、原始数据和复现方法；没有展示成功率的实验不会被暗示为已通过完整基准。

| 实验 | 已记录效果 |
| --- | --- |
| **[RSS 擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html)**<br>latch 辅助保持的完整记录与无 latch 对照保留；离线复算得到 0.061／449.981 mm 的保持位移差异。 | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html"><img src="docs/evidence/studio/rss.gif" width="280" alt="RSS 擦拭原版 RTX 回放"></a> |
| **[接触夹具诊断](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/README.zh-CN.md)**<br>平面滑动、法向加载、圆柱夹持，以及释放、穿透、动量和成本诊断；失败全部保留。 | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#pinch"><img src="demos/contact-benchmark/media/genesis-pinch.gif" width="220" alt="Genesis 夹持、抬升与释放"></a> |
| **[连续切割与推动](https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html)**<br>软体变形、刀面接触、推块和表面重建；保留粘性、半步长与无推动对照。 | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html"><img src="docs/evidence/cutting/tofu-cut-push/surface-rtx.gif" width="220" alt="豆腐切割与推动"></a> |
| **[布料引擎与机器人夹布](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html)**<br>下垂、拉伸、球面覆盖、预折叠下落和机器人夹布分开验收；穿透与失败不会被删除。 | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html"><img src="docs/evidence/cloth-studio/grasp.gif" width="250" alt="机器人夹布、抬升与释放"></a> |
| **[G1 落地接触](demos/landing-contact/README.zh-CN.md)**<br>固定 RTX 4090 参考栈完成支撑检查与三次完整策略复跑；历史异常缺少原模型，仍不归因。 | <a href="demos/landing-contact/README.zh-CN.md"><img src="docs/evidence/landing/replays/policy-repeat-1/preview.gif" width="340" alt="G1 原生接触力完整回放"></a> |
| **[AMP 抬箱短探针](docs/site/zh/amp-lift.md)**<br>0.2 秒记录前后一致性检查未通过，完整抬箱评测因此没有运行；未通过证据保留。 | <a href="docs/site/zh/amp-lift.md"><img src="docs/evidence/amp-lift/probe.gif" width="340" alt="AMP 抬箱短探针回放"></a> |

[完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [全部结果与失败](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)。动图来自实际仿真或记录回放；结果只适用于各报告的版本、配置和验收条件。

<a id="quickstart"></a>

## 先复算一组记录（无需 GPU）

下面下载一组同条件的 **latch／无 latch 原始记录**，从材料点与墨迹状态重算滑移和清洁度。只需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)；首次运行需要联网。证据包约 **126 MiB**，解包约 **349 MiB**，建议预留 2 GB。复算不需要仿真引擎、GPU 或模型 API key。

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git
cd Dexlab
git sparse-checkout init --cone
git sparse-checkout set scripts demos/rss-wiping
uv run --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python scripts/download_assets.py \
  --manifest demos/rss-wiping/evidence-bundle.json \
  --destination downloads/rss-wiping-v1
uv run --offline --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python demos/rss-wiping/rescore_bundle.py downloads/rss-wiping-v1 \
  --output results/rss-wiping-v1
```

打开 `results/rss-wiping-v1/comparison.png` 查看曲线。同目录还有两份 CSV 和 `report.json`；这对记录的保持阶段区域质心最大位移为 **0.061／449.981 mm**，最终清洁率为 **95.47%／39.92%**。无 latch 的 `task_pass: false` 是保留的实验失败，不是下载或复算失败。

[原始数据与逐文件许可](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1) · [复算范围和失败索引](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence)

## 想重跑仿真：苹果抓梗

上面的仓库目录安装好依赖后，可直接跑 MuJoCo 历史基线。需要 Linux x86_64 和 `uv`；不需要模型 API key。这是固定版本的历史演示，不是最新版六引擎比较环境。

```bash
git sparse-checkout disable
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh --backend mujoco \
  --output demos/apple-stem-grasp/runs/first-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

窗口会显示抓梗、抬升与保持；输出保存在 `demos/apple-stem-grasp/runs/first-mujoco/`。无桌面时在运行命令后加 `--headless`；切换 SuperDex 用 `--backend superdex`，并指定新的输出目录。显式目录必须为空，运行器不会覆盖已有成功或失败记录。

验收器写出 `summary.json`：全部检查通过时 `passed` 为 `true`；失败时保留具体检查项并返回非零退出码。14 s 是仿真时长，实际计算会更久。

[安装与资产来源](docs/installation.zh-CN.md) · [任务接口与命令](demos/apple-stem-grasp/README.zh-CN.md)

## 场景不对时，先查什么

先核对几何、质量／惯量、控制时刻和实际接触读回，再围绕一个明确问题调整参数。不要先扫一套 solver 参数，再在结果里寻找能解释失败的那一项。已有失败、受控修复和下一步判断见[诊断方法](https://huangkiki.github.io/Dexlab/zh-cn/latest/diagnosis.html)。

## 新任务怎样选引擎和配置

按载荷、接触尺度、粘着／滑动、接触切换和柔顺性找相近实验，再验证候选配置。研究覆盖 MuJoCo、SuperDex、Genesis、Newton Physics、PhysX 和 Drake，但任务覆盖、版本和验收不同；从[场景选型](https://huangkiki.github.io/Dexlab/zh-cn/latest/selection.html)进入，不要从引擎名字直接下结论。

想先补背景，可沿 [Sim Learning 的 Physics-Based Simulation 伴读路线](https://github.com/huangkiki/sim-learning/blob/main/docs/physics-based-simulation.md)阅读，再进入 [Solver 教程](https://github.com/huangkiki/sim-learning/tree/main/docs/solver-guide)。课程来源核查与 DexLab 实验资格分别记录。

## 当前边界

实验成功只适用于各自版本、场景和验收条件。任务成功、数值诊断、物理参照与真实系统准确性分别报告。手内旋转、主动折布、真实材料标定和大规模视觉策略评测仍需各自验证，不能从上文的抓取、切割或布料动图推出。

[研究经验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [求解配置如何分类](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [研究路线](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterity.html) · [外部参考](https://huangkiki.github.io/Dexlab/zh-cn/latest/references.html) · [数据与版本](https://github.com/huangkiki/Dexlab/releases)

[开发与验收约定](docs/autoresearch.zh-CN.md) · [当前工作与暂停状态](docs/current-work.zh-CN.md)
