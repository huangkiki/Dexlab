# DexLab

**接触、形变与材料分离条件下的机器人操作研究。** DexLab 用固定任务、原生接触记录和独立评分，帮助区分策略、场景配置与物理计算造成的失败。

[English](README.en.md) · [文档网站](https://huangkiki.github.io/Dexlab/zh-cn/latest/) · [实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [论文导读](https://huangkiki.github.io/Dexlab/zh-cn/latest/newton-reading-guide.html) · [快速开始](#quickstart)

## 实验预览

以下动图来自 DexLab 的真实仿真录像或记录状态回放。每项结果只适用于对应版本、材料假设和验收协议。

<table>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html">
<img src="docs/evidence/wuji-contact/comparison.gif" width="100%" alt="Wuji point contact and torsional contact comparison" loading="lazy">
</a>
<strong>抓取与抗滑移</strong><br>
相同控制下，点接触改为合成抗扭接触，两秒保持漂移从 <strong>2.734 mm</strong> 降至 <strong>1.025 mm</strong>。
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html">
<img src="docs/evidence/studio/rss.gif" width="100%" alt="Assisted sponge wiping replay" loading="lazy">
</a>
<strong>海绵擦拭与接触依赖</strong><br>
辅助保持下 <strong>3/3</strong> 通过；去掉辅助后 <strong>0/3</strong>，最终清洁率约 <strong>95.47% / 39.92%</strong>。
</td>
</tr>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html">
<img src="demos/cloth-folding/media/compliance-grasp.gif" width="100%" alt="Robot grasping a deformable cloth in recorded simulation" loading="lazy">
</a>
<strong>柔性物体操作</strong><br>
机器人能够夹住并移动布片，但完整折叠仍失败：当前记录的最大边长应变为 <strong>12.55%</strong>，超过预设 5% 上限。
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html">
<img src="docs/evidence/cutting/showcase.gif" width="100%" alt="Tofu and banana cutting recorded-state surface replay" loading="lazy">
</a>
<strong>切割与拓扑变化</strong><br>
连续切割与刀面推动会产生仿真状态的拓扑变化；视觉回放之外，完整报告还记录接触力、材料分离与失败。
</td>
</tr>
</table>

<a id="quickstart"></a>
## 开始使用

最短的仿真入口是苹果抓梗。Linux x86_64 上安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后：

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

如果只想检查证据链、不安装仿真器，可从[无需 GPU 的擦拭复算](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence)开始。完整依赖、资产和命令见[安装指南](https://huangkiki.github.io/Dexlab/zh-cn/latest/quickstart.html)。

<a id="architecture"></a>
## 在网站继续阅读

- [研究方法与系统结构](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#architecture)：如何记录、归因和复算一次失败，以及仿真与模型共同改进的研究方向。
- [实验结果与失败](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)：完整条件、指标、原始证据与复现入口。
- [模型评测协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)：远程执行和公开榜单仍在建设；[Uranus](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html) 是文档化候选后端。
- [外部参考资料](https://huangkiki.github.io/Dexlab/zh-cn/latest/references.html)：Newton 的 35 篇分类导读、完整书目及其他研究参考。

各项结果限定于对应配置与协议，不代表真机验证或统一引擎排名。网站集中维护研究与使用细节；[贡献方式](https://huangkiki.github.io/Dexlab/zh-cn/latest/contributing.html) · [当前工作](docs/current-work.zh-CN.md) · [引用方式](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#documentation-and-citation)。
