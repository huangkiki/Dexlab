<h1 align="center">DexLab</h1>
<p align="center"><strong>让智能体与仿真，在实验中共同进化。</strong></p>
<p align="center">
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/">网站</a> ·
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/#blog">Blog</a> ·
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/#experiments">研究结论</a> ·
  <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/#learn">学习地图</a> ·
  <a href="README.en.md">English</a>
</p>

**DexLab 分享接触丰富操作的研究结论、证据与启发，面向机器人学习和具身智能研究者。** 我们探索 RSI（递归自我改进）：让智能体的任务失败暴露仿真缺口，再用更可信的仿真帮助智能体提升能力。

**任务试验 → 诊断失败 → 改进技能与仿真 → 独立复验 → 下一个问题。**

人确定目标与边界，Agent 逐步参与问题发现、实验和迭代。已有成果以接触对照、失败诊断和可复算证据为基础；完整自主 RSI 闭环仍是研究方向。

<a id="findings"></a>
## 先看一个结论

**补上抗扭接触后，Wuji 保持检查通过。** 同一控制下，两秒保持最大位移 **2.734 → 1.025 mm**，通过原定 **2 mm** 门槛及主动释放检查。原点接触缺少绕接触连线的力矩方向，偏心重力驱动转动；这个案例提示：先检查接触模型能否提供所需力矩，再讨论夹紧力和求解参数。

<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html"><img src="docs/evidence/wuji-contact/comparison.gif" width="720" alt="Wuji 双指夹球的原速 4.4 秒记录回放：左为点接触，右为合成抗扭接触"></a>

这是已完成的接触模型对照，仍有慢漂移；不是完整自主 RSI 或真实指垫标定。新接触定律也影响准备阶段，不能把全部位移唯一归因于一个自由度。[读完整因果链、对照与下一步 →](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)

## 继续探索

| 想做什么 | 从这里开始 |
| --- | --- |
| **直接看研究结论** | [发现与适用范围](https://huangkiki.github.io/Dexlab/zh-cn/latest/#experiments)：先读结论，再看对照、依据和启发。 |
| **继续读研究 Blog** | [按问题和专题阅读](https://huangkiki.github.io/Dexlab/zh-cn/latest/#blog)：接触与物理、失败与评测、智能体与仿真。 |
| **系统学习仿真** | [学习地图](https://huangkiki.github.io/Dexlab/zh-cn/latest/#learn)连接先修知识与实验，[完整课程在本站阅读](https://huangkiki.github.io/Dexlab/zh-cn/latest/learning.html)，由 Sim Learning 维护。 |

<a id="architecture"></a><a id="quickstart"></a>
[平台架构](https://huangkiki.github.io/Dexlab/zh-cn/latest/about.html#architecture) · [安装与复现](https://huangkiki.github.io/Dexlab/zh-cn/latest/quickstart.html) · [参与研究](https://huangkiki.github.io/Dexlab/zh-cn/latest/contributing.html) · [Apache-2.0](LICENSE)
