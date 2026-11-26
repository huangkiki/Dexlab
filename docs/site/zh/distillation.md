# 蒸馏

从外部论文和项目里提炼 DexLab 值得借鉴的做法，分清作者验证了什么、还有什么要自己测。

- [PhysicsNeMo：位置预测准了，接触事件也准吗？](physicsnemo-contact-surrogates.md)

  从车壳穿越和握球卸载，看位置误差和接触事件为什么要分开测。

- [DONIC 的双手跟踪分，能看出交接成功吗？](donic-bimanual-tracking.md)

  从一次杯子交接看，怎样用接触与传力证据解释跟踪分。

- [视觉目标 mask 怎样进入 DexLab：先证明它是进度信号，再谈 GCRL](mask-conditioned-gcrl.md)

  作者的抓苹果案例里，目标区域能提供什么反馈，遮挡和定位偏差又会带来什么问题。

- [物理 caption 怎样进入 DexLab：先评参考覆盖，再查视频事实](physcapbench.md)

  从一段翻书视频看，评测怎样区分「参考里没写」和「描述了不存在的事」。

- [NeuralActuator：执行器误差要单独建模，接触仍要交给物理](neural-actuator.md)

  作者的 500 g 负载实验说明了什么，以及关掉接触后还有什么需要验证。

- [Code as Policy：从“模型写代码”到可验证的机器人技能](code-as-policy.md)

  一次抓取失败，怎样变成可检查的程序动作和反馈。

```{toctree}
:hidden:

donic-bimanual-tracking
physicsnemo-contact-surrogates
```
