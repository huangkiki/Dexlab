# DexLab

**用可复现的接触、摩擦与操作实验，研究机器人为什么抓得住、会滑脱，以及怎样选择和调整物理仿真。**

[English](README.en.md) · [快速开始](#quickstart) · [完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [全部报告](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)

<a id="research-findings"></a>

## 做了哪些实验

<span id="visual-experiment-catalogue"></span>

点击实验名或动图查看完整报告与复现方法。

| 实验 | 动图预览 |
| --- | :---: |
| <a id="rss"></a>**[RSS 擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html)**<br>使用 latch 辅助固定：夹稳后用柔顺约束带动海绵局部随手运动，松开时解除。成功不代表纯摩擦保持；[查看无 latch 对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#latch)。 | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#latch"><img src="docs/evidence/studio/rss.gif" width="300" alt="RSS 使用 latch 辅助固定的原版 RTX 回放，10–19.9 s" loading="lazy"></a> |
| <a id="cut-push"></a><a id="banana-force"></a>**[连续切割与推动](https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html"><img src="docs/evidence/cutting/tofu-cut-push/surface-rtx.gif" width="207" alt="豆腐切块与推动 · RTX 回放" loading="lazy"></a> <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html"><img src="docs/evidence/cutting/banana-cut-push/surface-rtx.gif" width="207" alt="香蕉切割与推动 · RTX 回放" loading="lazy"></a> |
| <a id="scoring"></a>**[交叉浅划](https://huangkiki.github.io/Dexlab/zh-cn/latest/tofu-scoring.html)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/tofu-scoring.html"><img src="docs/evidence/cutting/tofu-scoring/surface.gif" width="233" alt="记录状态的表面重建" loading="lazy"></a> |
| <a id="apple"></a>**[苹果抓梗](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html#apple-replays)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html"><img src="docs/evidence/studio/apple.gif" width="412" alt="MuJoCo 3.16 / SuperDex 1.0 RTX replay" loading="lazy"></a> |
| <a id="cloth-comparison"></a>**[布料引擎对比](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html"><img src="docs/evidence/cloth-studio/sag.gif" width="208" alt="四引擎同场景下垂" loading="lazy"></a> |
| <a id="cloth"></a>**[机器人夹布](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html"><img src="docs/evidence/cloth-studio/grasp.gif" width="262" alt="夹布、抬升与释放" loading="lazy"></a> |
| <a id="visual-highlight-pinch"></a>**[夹持力对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#pinch)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html"><img src="docs/evidence/studio/pinch.gif" width="412" alt="驱动力限额 0.4 N／0.8 N" loading="lazy"></a> |
| <a id="visual-highlight-libero"></a>**[LIBERO 回放](https://huangkiki.github.io/Dexlab/zh-cn/latest/libero-workflow.html)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html"><img src="docs/evidence/studio/libero.gif" width="206" alt="demo 0 原生基线状态回放" loading="lazy"></a> |
| <a id="visual-highlight-incline"></a>**[六引擎斜面滑动](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#incline)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html"><img src="docs/evidence/studio/incline.gif" width="309" alt="1 ms 步长滑动记录" loading="lazy"></a> |
| <a id="visual-highlight-normal"></a>**[法向接触标定](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#normal)** | <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html"><img src="docs/evidence/studio/normal.gif" width="412" alt="合成目标的加载、保持与卸载" loading="lazy"></a> |

[完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · 动图来自实际仿真或记录回放；结果仅适用于各报告的配置与条件。

[高质量回放与复现](https://huangkiki.github.io/Dexlab/zh-cn/latest/studio-rendering.html) · [切割表面重建与限制](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-surface.html)

[到底哪个 solver 失败了？](docs/site/zh/solver-failure-audit.md) 对照 RSS 任务与 DexLab 既有记录，区分耦合缺失、配置失败和运行错误。

<a id="quickstart"></a>

## 先复算一组擦拭记录（无需 GPU）

下载一组同条件的 **latch／无 latch 原始记录**，从材料点与墨迹状态重算滑移和清洁度。需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)；命令使用隔离的 Python 3.12 环境，只安装 NumPy、Matplotlib 及其依赖。首次需要联网获取源码和依赖；证据包本身约 **126 MiB**，解包约 **349 MiB**，建议预留 2 GB 空间。下面只检出复算需要的目录。复算不需要仿真引擎、GPU 或模型 API key。

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git
cd Dexlab
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

[安装、依赖与资产来源](docs/installation.zh-CN.md) · [任务接口与命令](demos/apple-stem-grasp/README.zh-CN.md)

<a id="research-diagnosis"></a>

## 场景不对时，先查什么

先核对几何、质量／惯量、控制时刻和实际接触读回，再围绕一个明确问题调整参数，用原始记录和独立评分检查结果。已有失败、修正和下一步判断见[诊断方法](https://huangkiki.github.io/Dexlab/zh-cn/latest/diagnosis.html)。

<a id="research-selection"></a>

## 新任务怎样选引擎和配置

按载荷、接触尺度、粘着／滑动、接触切换和柔顺性找相近实验，再验证候选配置。研究涉及 MuJoCo、SuperDex、Genesis、Newton Physics、PhysX 和 Drake，但各任务覆盖与验收不同；完整配置、版本和失败见[覆盖矩阵](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)，具体起点见[场景选型](https://huangkiki.github.io/Dexlab/zh-cn/latest/selection.html)。

<a id="solver-coupling"></a>

## 多个求解器怎样协同

仿真时间、电脑耗时和数据交换周期是三个不同的量。求解器之间等待会影响运行速度，反馈延迟还会影响相互作用。[用手指与海绵理解同步、迭代与 preCICE](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-coupling.html)；preCICE 在这里是方法参考，尚未接入 DexLab。

<a id="research-scope"></a>

## 当前边界与深入阅读

以经典物理规律和已有经验关系为参照。实验成功只适用于各自版本、场景和验收条件；任务成功、数值诊断与真实物理准确性分别报告。手内旋转、主动折布、真实材料标定和视觉策略能力仍需各自验证，不能从上面的动图推出。

[研究经验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [求解配置如何分类](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [研究路线](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterity.html) · [外部参考](https://huangkiki.github.io/Dexlab/zh-cn/latest/references.html) · [数据与版本](https://github.com/huangkiki/Dexlab/releases)

[开发与验收约定](docs/autoresearch.zh-CN.md) · [当前工作与暂停状态](docs/current-work.zh-CN.md)
