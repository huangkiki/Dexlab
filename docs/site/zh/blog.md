# Blog

求解器的基本概念，以及仿真实验里的有趣发现。

```{raw} html
<nav class="blog-jump" aria-label="Blog 栏目">
  <a href="#solver-fundamentals">求解器与仿真基础</a>
  <a href="#experimental-findings">实验发现</a>
</nav>
```

(solver-fundamentals)=
## 求解器与仿真基础

- [一步仿真，几种时间](mujoco-learning/step.md)

  用一次物理步区分步长、控制周期和画面刷新。

- [接触、摩擦与求解](mujoco-learning/contact.md)

  从物体落到桌面开始，看接触什么时候生效、摩擦怎样限制滑动。

- [接触求解收敛了，滑块为什么还会离开桌面？](complementarity-contact-models.md)

  用滑块解释求解器正在解什么，以及接触模型怎样改变答案。

- [多求解器如何同步？preCICE 做什么？](solver-coupling.md)

  看同一场景里的求解器怎样交换状态和力。

- [当我们在讨论仿真 Sim-to-Real Gap 问题时，我们在讨论什么？](failure-root-cause-atlas.md)

  顺着失败出现的时间，找出最先出问题的环节。

- [Code as Policy：从“模型写代码”到可验证的机器人技能](code-as-policy.md)

  一次抓取失败，怎样变成可检查的程序动作和反馈。

(experimental-findings)=
## 实验发现

- [两根手指一直夹着，球为什么还会转？](wuji-contact.md)

  用点接触与抗扭接触的对照，解释球为什么能绕着夹持线转。

- [仿真里，怎么知道豆腐和香蕉真的切开了？](cut-push.md)

  侧推最后一块，检查切缝两边是否已经断开、能否各自移动。

- [布料：同一场景，不同引擎](cloth-comparison.md)

  比较布条自由下垂与布片覆盖球体，分别观察自己怎么弯、碰到东西怎么动。

- [LIBERO：从原生任务到可验证的改进](libero-workflow.md)

  把步长减半后，十次示范仍都完成，但通过接触相关诊断的次数变少了。

- [RoboDojo 烤面包：面包脱落与入槽接触逃逸](robodojo-bread-slip.md)

  用同步动作与接触记录，解释看起来相似的失败为什么需要不同的修复。

- [NeuralActuator：执行器误差要单独建模，接触仍要交给物理](neural-actuator.md)

  作者的 500 g 负载实验说明了什么，以及关掉接触后还有什么需要验证。

- [物理 caption 怎样进入 DexLab：先评参考覆盖，再查视频事实](physcapbench.md)

  从一段翻书视频看，评测怎样区分「参考里没写」和「描述了不存在的事」。

- [视觉目标 mask 怎样进入 DexLab：先证明它是进度信号，再谈 GCRL](mask-conditioned-gcrl.md)

  作者的抓苹果案例里，目标区域能提供什么反馈，遮挡和定位偏差又会带来什么问题。

[更多实验与证据](experiments.md) · [灵巧操作仿真研究导读](https://huangkiki.github.io/Dexlab/zh-cn/latest/_static/research/dexterous-simulation.html) · [Paper Sharing](paper-sharing.md)
