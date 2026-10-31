# DexLab

**让仿真器与机器人模型在同一批失败样本上互相指出盲点，然后一起改进。**

模型在接触丰富任务上执行，DexLab 记录原生接触读回并归因失败；发现物理缺口就升级仿真器，发现策略缺口就回到模型。每次改动都绑定模型版本、仿真器版本和原始证据，再回到同一协议重跑。

[English](https://huangkiki.github.io/Dexlab/en/latest/index.html) · [共同进化协议](model-evaluation.md) · [Uranus 环境后端](uranus-backend.md) · [申请 pilot](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) · [Live Lab](#live-lab) · [快速开始](#quickstart) · [完整实验目录](experiments.md) · [全部报告](results.md)

(model-evaluation)=
## 仿真器与模型共同进化

DexLab 面向通用操作模型、VLA/WAM、Agent-as-policy 和远程机器人 API 团队。客户自带机器人与接口；模型执行，DexLab 记录接触与失败，再把结论送回模型或仿真器其中一边。

- **闭环：** 模型跑任务 → 记录真实接触 → 归因到模型或物理 → 升级其中一边并重跑同协议。
- **主成绩：** 每个任务先单独计算成功率，再对任务等权求宏平均；逐任务矩阵不会隐藏失败。
- **物理边界：** 引擎或场景导致运行无效时，不把仿真器缺陷算成模型失败，而是作为下一次升级仿真器的证据。
- **防刷榜：** 正式榜只接受官方执行；公开集用于复现，隐藏场景变化用于检测过拟合，全部尝试与重跑都保留。
- **状态分层：** `local / unverified`、`official verified` 和 `reproducible` 分开显示，不用“官方跑过”冒充“外部可复现”。

远程模型服务是首选接入方式。当前仓库已经证明“物理条件改变结果”这一侧；外部模型接入后，再记录“模型策略改变结果”的另一侧。远程执行器与公开 leaderboard 仍在建设中。

[查看共同进化与防刷榜协议](model-evaluation.md) · [申请模型评测](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+)

**先学再读配置表：**[Sim Learning](https://github.com/huangkiki/sim-learning) 提供中文教程和六引擎原生课程。建议先沿 [Physics-Based Simulation 伴读路线](https://github.com/huangkiki/sim-learning/blob/main/docs/physics-based-simulation.md) 学习，再读 [Solver 教程](https://github.com/huangkiki/sim-learning/tree/main/docs/solver-guide)。课程来源核对与 DexLab 实验资格分别记录。

(live-lab)=
## 浏览器实时实验

下面直接在当前网页运行 MuJoCo 3.17 WebAssembly，并使用浏览器本地 WebGPU 渲染。
三种求解配置共享相同方块、重力、摩擦、初态和时间步长。点击“运行”后可观察接触数、
切向位移、solver iterations 和实际仿真速度。

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

实时页面不会继承原生实验成绩；浏览器版本、渲染后端、MuJoCo 版本和实际运行速度会单独显示。

(research-findings)=
## 做了哪些实验

```{raw} html
<span id="visual-experiment-catalogue"></span>
```

点击实验名或动图查看完整报告与复现方法。

| 实验 | 动图预览 |
| --- | :---: |
| **[Wuji 双指夹球](wuji-contact.md)**<br>同一控制和动作下，点接触改为合成抗扭接触，两秒保持位移从 2.734 降至 1.025 mm，通过原 2 mm 门槛；可离线复算，不证明 solver 失效或真机准确性。 | <a href="wuji-contact.html"><img src="_static/wuji-contact/comparison.gif" width="300" alt="Wuji v3 point contact and v4 torsional contact, full synchronized replay" loading="lazy"></a> |
| <a id="rss"></a>**[海绵擦拭](rss-wiping.md)**<br>来源为 RoboSimStudio `wipe_the_bar`。原版使用辅助保持：夹稳后用柔顺约束带动海绵局部随手运动，松开时解除。成功不代表纯摩擦保持；[查看无辅助对照](latch)。 | <a href="rss-wiping.html#latch"><img src="_static/studio/rss.gif" width="300" alt="海绵擦拭辅助保持原版 RTX 回放，10–19.9 s" loading="lazy"></a> |
| <a id="cut-push"></a><a id="banana-force"></a>**[连续切割与推动](cut-push.md)** | <a href="cut-push.html"><img src="_static/cutting/tofu-cut-push/surface-rtx.gif" width="207" alt="豆腐切块与推动 · RTX 回放" loading="lazy"></a> <a href="cut-push.html"><img src="_static/cutting/banana-cut-push/surface-rtx.gif" width="207" alt="香蕉切割与推动 · RTX 回放" loading="lazy"></a> |
| <a id="scoring"></a>**[交叉浅划](tofu-scoring.md)** | <a href="tofu-scoring.html"><img src="_static/cutting/tofu-scoring/surface.gif" width="233" alt="记录状态的表面重建" loading="lazy"></a> |
| <a id="apple"></a>**[苹果抓梗](apple-replays)** | <a href="studio-rendering.html"><img src="_static/studio/apple.gif" width="412" alt="MuJoCo 3.16 / SuperDex 1.0 RTX replay" loading="lazy"></a> |
| <a id="cloth-comparison"></a>**[布料引擎对比](cloth-comparison.md)** | <a href="cloth-comparison.html"><img src="_static/cloth-studio/sag.gif" width="208" alt="四引擎同场景下垂" loading="lazy"></a> |
| <a id="cloth"></a>**[机器人夹布](experiments.md)** | <a href="experiments.html"><img src="_static/cloth-studio/grasp.gif" width="262" alt="夹布、抬升与释放" loading="lazy"></a> |
| <a id="visual-highlight-pinch"></a>**[夹持力对照](pinch)** | <a href="studio-rendering.html"><img src="_static/studio/pinch.gif" width="412" alt="驱动力限额 0.4 N／0.8 N" loading="lazy"></a> |
| <a id="visual-highlight-libero"></a>**[LIBERO 回放](libero-workflow.md)** | <a href="studio-rendering.html"><img src="_static/studio/libero.gif" width="206" alt="demo 0 原生基线状态回放" loading="lazy"></a> |
| <a id="visual-highlight-incline"></a>**[六引擎斜面滑动](incline)** | <a href="studio-rendering.html"><img src="_static/studio/incline.gif" width="309" alt="1 ms 步长滑动记录" loading="lazy"></a> |
| <a id="visual-highlight-normal"></a>**[法向接触标定](normal)** | <a href="studio-rendering.html"><img src="_static/studio/normal.gif" width="412" alt="合成目标的加载、保持与卸载" loading="lazy"></a> |

[完整实验目录](experiments.md) · 动图来自实际仿真或记录回放；结果仅适用于各报告的配置与条件。

[到底哪个 solver 失败了？](solver-failure-audit.md) 查看 RSS 任务、已有失败及归因边界。

(quickstart)=
## 先复算一组擦拭记录（无需 GPU）

下载一组同条件的 **latch／无 latch 原始记录**，从材料点与墨迹状态重算滑移和清洁度。需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)；命令使用隔离的 Python 3.12 环境，只安装 NumPy、Matplotlib 及其依赖。首次需要联网获取源码和依赖；证据包本身约 **126 MiB**，解包约 **349 MiB**，建议预留 2 GB 空间。下面只检出复算需要的目录。复算不需要仿真引擎、GPU 或模型 API key。

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

打开 `results/rss-wiping-v1/comparison.png` 看曲线；同目录包含两份 CSV 和 `report.json`。这一对记录的保持阶段区域质心最大位移为 **0.061／449.981 mm**，最终清洁率为 **95.47%／39.92%**。两份记录均应通过一致性检查；无 latch 的 `task_pass: false` 是保留的实验失败，不表示下载或复算失败。再次复算请换一个输出目录。

[原始数据与逐文件许可](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1) · [完整范围、失败索引和原生重跑前提](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence)。公开包包含一个历史配对；它不证明某个 solver 的普遍缺陷。

## 想重跑仿真：苹果抓梗

在上面克隆的仓库目录中，已有安装脚本可以运行 MuJoCo 苹果抓梗。需要 Linux x86_64 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)；不需要模型 API key。该入口复现固定版本的历史演示，不是六引擎最新版本比较环境。 安装前会检查已有 `.venv` 的版本与归属；不兼容或共享环境会被拒绝，请保留原环境，在独立检出目录安装。

```bash
git sparse-checkout disable
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh --backend mujoco --output demos/apple-stem-grasp/runs/first-mujoco
```

等待 SDF 准备、静置与规划后，窗口会显示抓梗、抬升和保持。输出保存在 `demos/apple-stem-grasp/runs/first-mujoco/`；无桌面时在运行命令后加 `--headless`，切换后端用 `--backend superdex` 并指定新输出目录。14 s 是仿真时长，实际计算会更久。

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

再次运行时换一个目录；下面可独立检查第二次记录，并比较两次报告：

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --output demos/apple-stem-grasp/runs/second-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py demos/apple-stem-grasp/runs/second-mujoco
diff -u demos/apple-stem-grasp/runs/first-mujoco/summary.json demos/apple-stem-grasp/runs/second-mujoco/summary.json
```

`diff` 返回 1 表示报告不同。显式目录必须为空，已有成功或失败记录均拒绝覆盖。省略 `--output` 会生成独立目录，终端的 `Run output:` 给出实际路径；后续评分请使用该路径。

验收器会写出 `summary.json`；全部检查通过时 `passed` 为 `true`，失败时保留具体检查项并返回非零退出码。

[安装、依赖与资产来源](https://github.com/huangkiki/Dexlab/blob/main/docs/installation.zh-CN.md) · [任务接口与命令](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.zh-CN.md)

(research-diagnosis)=
## 场景不对时，先查什么

先核对几何、质量／惯量、控制时刻和实际接触读回，再围绕一个明确问题调整参数，用原始记录和独立评分检查结果。已有失败、修正和下一步判断见[诊断方法](diagnosis.md)。

(research-selection)=
## 新任务怎样选引擎和配置

按载荷、接触尺度、粘着／滑动、接触切换和柔顺性找相近实验，再验证候选配置。研究涉及 MuJoCo、SuperDex、Genesis、Newton Physics、PhysX 和 Drake，但各任务覆盖与验收不同；完整配置、版本和失败见[覆盖矩阵](coverage.md)，具体起点见[场景选型](selection.md)。

(solver-coupling)=
## 多个求解器怎样协同

仿真时间、电脑耗时和数据交换周期是三个不同的量。求解器之间等待会影响运行速度，反馈延迟还会影响相互作用。[用手指与海绵理解同步、迭代与 preCICE](solver-coupling.md)；preCICE 在这里是方法参考，尚未接入 DexLab。

(research-scope)=
## 当前边界与深入阅读

以经典物理规律和已有经验关系为参照。实验成功只适用于各自版本、场景和验收条件；任务成功、数值诊断与真实物理准确性分别报告。手内旋转、主动折布、真实材料标定和视觉策略能力仍需各自验证，不能从上面的动图推出。

[研究经验](experience.md) · [求解配置如何分类](solver-taxonomy.md) · [研究路线](dexterity.md) · [外部参考](references.md) · [数据与版本](https://github.com/huangkiki/Dexlab/releases)

[开发与验收约定](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md) · [当前工作与暂停状态](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.zh-CN.md)

```{toctree}
:hidden:
:maxdepth: 1

Solver 失败复盘 <solver-failure-audit>

共同进化与模型评测 <model-evaluation>

Uranus 生成式环境后端 <uranus-backend>

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
研究路线 <dexterity>
研究账本 <research-ledger>
基准 <benchmark>
外部参考 <references>
参与贡献 <contributing>
```
