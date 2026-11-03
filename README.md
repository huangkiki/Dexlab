<h1 align="center">DexLab</h1>

<p align="center"><strong>机器人接触操作的实验与评测平台</strong></p>

<p align="center">
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/">文档</a> ·
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab">在线体验</a> ·
  <a href="#quickstart">快速开始</a> ·
  <a href="#whats-new">What's new</a> ·
  <a href="README.en.md">English</a>
</p>

**DexLab 是研究机器人接触操作的开源实验平台。** 从抓取、擦拭到布料操作与切割，你可以复现已有任务，检查接触与运动，比较物理设置，并分析操作为什么成功或失败。每个实验连接场景、控制、仿真记录和评分，让结果能够被重新检查。

<a id="architecture"></a>
<p align="center">
  <a href="docs/site/_static/images/dexlab-architecture.jpg">
    <img src="docs/site/_static/images/dexlab-architecture.jpg" width="100%" alt="DexLab 平台总览：任务与协议、被测系统、动作执行、环境后端、证据与评分">
  </a>
</p>

平台围绕一条完整的操作流程组织：**定义任务 → 执行动作 → 推进仿真 → 记录接触 → 评估结果**。图中的脚本、策略和模型通过动作执行层连接物理环境，任务协议决定如何评分。图示包含规划中的能力；各任务与后端的实际进度见[覆盖矩阵](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)。

## 实验一览

以下动图来自实际仿真录像或记录状态回放。点击查看实验条件、完整结果与复现方法。

<table>
<tr>
<td width="50%" valign="top">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html">
<img src="docs/evidence/wuji-contact/comparison.gif" width="100%" alt="Wuji point contact and torsional contact comparison" loading="lazy">
</a>
<strong>抓取：接触模型如何影响滑移？</strong><br>
相同控制下，点接触改为合成抗扭接触，两秒保持漂移从 <strong>2.734 mm</strong> 降至 <strong>1.025 mm</strong>。
</td>
<td width="50%" valign="top">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html">
<img src="docs/evidence/studio/rss.gif" width="100%" alt="Assisted sponge wiping replay" loading="lazy">
</a>
<strong>擦拭：去掉辅助还能完成任务吗？</strong><br>
辅助保持下 <strong>3/3</strong> 通过；去掉辅助后 <strong>0/3</strong>，最终清洁率约 <strong>95.47% / 39.92%</strong>。
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html">
<img src="demos/cloth-folding/media/compliance-grasp.gif" width="100%" alt="Robot grasping a deformable cloth in recorded simulation" loading="lazy">
</a>
<strong>布料：抓得住，是否也折得好？</strong><br>
机器人能够夹住并移动布片，但完整折叠仍失败：当前记录的最大边长应变为 <strong>12.55%</strong>，超过预设 5% 上限。
</td>
<td width="50%" valign="top">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html">
<img src="docs/evidence/cutting/showcase.gif" width="100%" alt="Tofu and banana cutting recorded-state surface replay" loading="lazy">
</a>
<strong>切割：形变、分离与接触力</strong><br>
连续切割与刀面推动会产生仿真状态的拓扑变化；视觉回放之外，完整报告还记录接触力、材料分离与失败。
</td>
</tr>
</table>

这些结果来自各自限定的仿真配置，不代表真机验证或统一引擎排名。[浏览全部实验 →](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html)

## Why DexLab?

同一个抓取失败，可能需要改进策略，也可能需要调整碰撞几何、摩擦模型或控制方式。**DexLab 希望帮助研究者判断该改什么，以及改完是否真的有效。**

- **从操作任务研究物理。** 围绕“物体为什么滑落”“布料为什么拉伸”等具体问题，把接触模型和求解配置放回任务中检验。
- **让实验结果可以解释。** 将控制命令、物体运动和仿真器中的接触记录放在一起，定位最先出现问题的环节。
- **让已有实验可以复用。** 提供场景、运行入口、原始记录与独立评分；可以重跑任务，也可以下载证据包离线复算。

长期目标是让仿真与模型共同改进：用模型的失败发现仿真缺口，再用经过检验的仿真评估模型。当前可用的是原生物理实验、记录与评分；RoboAPI 会话适配已加入，逐任务模型接入与公开榜单仍在建设，[Uranus](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html) 为候选生成式后端。[模型评测方向 →](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)

<a id="whats-new"></a>
## What's new

- **2026-11-03** — [在线抓娃娃机](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab)：一次下爪，同步对比 Newton、CG、PGS；支持慢放、原局重试及求解器与积分方法说明；提供 16 款角色、每柜 16 只的暗紫星月机柜和[本机 OVRTX 渲染](web/ovrtx/README.md)。
- **2026-11-03** — 上线[灵巧操作仿真调研原版](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html)，并沿原有六层框架补入 14 篇相关工作与 1 篇背景参考。
- **2026-11-02** — 新增[灵巧手仿真导读](https://huangkiki.github.io/Dexlab/zh-cn/latest/dexterous-hand-simulation.html)与 [Newton 35 篇论文分类](https://huangkiki.github.io/Dexlab/zh-cn/latest/newton-reading-guide.html)。
- **2026-10-31** — 发布 [RoboAPI 会话适配](docs/roboapi-poke.zh-CN.md)：模型发现、连续会话与动作回执；任务映射待接入。
- **2026-10-26** — 发布 [Wuji 双指夹球对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)、独立评分与离线复算包。

<a id="quickstart"></a>
## 快速开始

**先试一下，无需安装：** 打开[在线实验室](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab)，玩一局 MuJoCo 抓娃娃机：瞄准、下爪，玩偶落入取物盒才计分。

**运行第一个本地任务：** 推荐从苹果抓梗开始。Linux x86_64 上安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后：

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

验收器会写出 `summary.json`，全部检查通过时 `passed: true`。14 秒是仿真时长，实际计算通常更久；无桌面环境添加 `--headless`，每次运行使用新输出目录。

[完整安装指南](https://huangkiki.github.io/Dexlab/zh-cn/latest/quickstart.html) · [无需 GPU 的离线复算](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence)

## 文档与参与

网站持续维护完整实验报告、使用指南和研究资料：

- **看实验**：[实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [结果与覆盖](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html) · [失败复盘](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-failure-audit.html)
- **研究导览**：[当我们在讨论灵巧操作仿真时，我们在讨论什么？](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html)——保留本机原版的排版、正文和筛选功能，追加[10 月相关论文](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html#october-2026)。
- **理解方法**：[求解器与接触模型](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [论文与参考资料](https://huangkiki.github.io/Dexlab/zh-cn/latest/references.html)
- **参与项目**：[贡献指南](https://huangkiki.github.io/Dexlab/zh-cn/latest/contributing.html) · [当前工作](docs/current-work.zh-CN.md) · [问题与建议](https://github.com/huangkiki/Dexlab/issues)

代码采用 [Apache-2.0](LICENSE) 许可；第三方资产遵循各自许可。研究使用请参考[引用说明](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#documentation-and-citation)。
