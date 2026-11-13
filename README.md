# DexLab

DexLab 是我的个人研究项目，探索 Agent Skills 与仿真如何相互改进。

一次抓取失败，可能是 policy 策略问题，也可能是仿真没有准确模拟接触与摩擦求解。

DexLab 从这样的具体问题出发，**用任务暴露问题，用对照实验定位原因，再改进对应的仿真。**

改进后的仿真再支持 Agent 学习下一轮 Skills。新的 Skills 让 Agent 能挑战更难的任务，进一步检验仿真的边界。

## [📖 阅读 Blog →](https://huangkiki.github.io/Dexlab/zh-cn/latest/#blog)

[研究结论](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [实验记录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [仿真学习](https://huangkiki.github.io/Dexlab/zh-cn/latest/learning.html) · [English](README.en.md)

<a id="architecture"></a>
<a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/#blog"><img src="docs/site/_static/images/dexlab-architecture.png" width="100%" alt="DexLab 架构示意：任务与协议、被测系统、动作执行、环境后端、证据与评分"></a>
