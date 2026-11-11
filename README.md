<h1 align="center">DexLab</h1>

<p align="center"><strong>机器人接触操作的实验与评测平台</strong></p>

<p align="center">
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/">文档</a> ·
  <a href="#architecture">平台架构</a> ·
  <a href="#findings">研究结论</a> ·
  <a href="#quickstart">快速开始</a> ·
  <a href="README.en.md">English</a>
</p>

**DexLab 是研究机器人接触操作的开源实验平台。** 它把任务场景、控制、原生物理记录和独立评分连在一起，用来判断一次仿真失败来自策略、控制、几何、接触模型还是数值求解。

<a id="architecture"></a>
## 平台架构

<p align="center">
  <a href="docs/site/_static/images/dexlab-architecture.png">
    <img src="docs/site/_static/images/dexlab-architecture.png" width="100%" alt="DexLab 平台总览：任务与协议、被测系统、动作执行、环境后端、证据与评分">
  </a>
</p>

脚本、策略与模型通过动作适配和控制器连接环境，环境返回观测；原生状态与接触记录进入独立评分，诊断结果用于改进下一轮实验。

图为平台架构示意；任务、模型与后端的实际实现及验证范围见[覆盖矩阵](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)，生成式后端为研究候选。

<a id="findings"></a>
## 目前得到的结论

**目前最有用的结论是：先定位失败发生在哪一层，再决定改策略、接触模型还是求解器。** 已有证据还不支持通用引擎排名或真机精度结论。

| 已有结论 | 证据与适用范围 | 对开发的影响 |
| --- | --- | --- |
| **接触模型能改变同一抓取的成败。** | Wuji 合成夹球中，仅增加抗扭接触，两秒保持最大位移由 **2.734 → 1.025 mm**，跨过原定 2 mm 门槛；仍有慢漂移。[报告](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html) | 先核对接触建模；这个结果没有建立求解器失效或真实指垫标定。 |
| **完成任务，不代表依靠预期的物理机制完成。** | RSS 擦拭有辅助保持时 **3/3** 通过，仅去掉辅助后 **0/3**；LIBERO 原任务 **10/10** 完成，物理诊断仅 **5/10** 通过。[擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html) · [LIBERO](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) | 任务评分与接触、辅助力、记录检查分开报告。 |
| **一个工况调好的参数，不足以保证迁移。** | 三个冻结配置在十组质量／尺寸条件下，合成响应联合目标 **0/30** 通过；未做质量或面积补偿。[报告](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#mass-size-transfer) | 复核参数映射与适用范围，不能把这批失败归为引擎算法错误。 |
| **预测误差更低，不等于能预报接触失效。** | 六个已有 Wuji 回合的 100 ms 离线诊断中，常速预测降低位移误差，但接触保持基线仍漏报释放／卸载中的接触丢失。[报告](https://huangkiki.github.io/Dexlab/zh-cn/latest/contact-response.html) | 另测接触事件与动作响应；重叠窗口不算独立重复，目前没有学习模型或控制收益结论。 |

[完整结果、失败与未完成项 →](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)

## 代表实验

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
</table>

更多实验与失败：[布料折叠](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html) · [切割与推动](https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html) · [全部实验 →](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html)

## 研究主线的三个节点

- **2026-10-26｜解释抓取为什么改变：** [Wuji 接触对照](https://github.com/huangkiki/Dexlab/commit/c8d4e29586a140a7df241b928720e82ed6008f3a)连同独立评分和离线复算交付，让“看起来抓住”变成可检查的接触证据。
- **2026-10-27｜追问模型能否提前发现失败：** [接触响应诊断](https://github.com/huangkiki/Dexlab/commit/b1cb02561e0e291bdbc1ac232a46c352dd48e946)交付离线基线，保留“位移误差下降、接触丢失仍漏报”的结果；原生动作干预尚待验证。
- **2026-11-02｜连接学习与物理归因：** [CHORD 准备入口](https://github.com/huangkiki/Dexlab/commit/1a8855ccfd26ff6f1434a109954190c2775a8167)固定三任务、资产预检和有限预算命令。主线尚未完成原生任务迁移；训练候选与阻塞见[当前工作](docs/current-work.zh-CN.md)。

后续按 **研究问题 → 审计评分语义 → 最小对照 → 失败归因 → 更新结论** 推进。[开发流程与下一步](docs/autoresearch.zh-CN.md#research-loop)吸收了最新 Discussion；连续接触序列仍是待验证设计。

<a id="quickstart"></a>
## 快速开始

推荐从苹果抓梗开始。Linux x86_64 上安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后：

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
- **研究导读**：[当我们在讨论灵巧操作仿真时，我们在讨论什么？](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html)
- **理解方法**：[求解器与接触模型](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [论文与参考资料](https://huangkiki.github.io/Dexlab/zh-cn/latest/references.html)
- **参与项目**：[贡献指南](https://huangkiki.github.io/Dexlab/zh-cn/latest/contributing.html) · [当前工作](docs/current-work.zh-CN.md) · [问题与建议](https://github.com/huangkiki/Dexlab/issues)

代码采用 [Apache-2.0](LICENSE) 许可；第三方资产遵循各自许可。研究使用请参考[引用说明](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#documentation-and-citation)。
