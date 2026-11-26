# PhysicsNeMo：位置预测准了，接触事件也准吗？

在 Wuji 的[已有离线诊断](contact-response.md)里，三个合格抓持回合的常速预测，100 ms 后的位置误差只有 **0.018–0.023 mm RMSE**，但两个接触保持基线漏掉了释放或卸载阶段记录到的全部接触丢失窗口。位置挪得很少时，某根手指也可能已经卸力。要预测这种切换，一要让模型看得到动作，二要单独考它能不能判断哪根手指何时松开。重叠窗口是同一回合的读数，不是独立重复。

NVIDIA PhysicsNeMo 是训练物理代理模型的 PyTorch 工具箱；代理是对某类仿真结果的预测器，不是通用物理引擎。两个来自该工具箱的例子，正好把「给对输入」和「验对结果」拆开了。

## 给模型看见会改变结果的条件

同一个翼型转到不同迎角，形状没变，受到的气流和压力会变。`DomainMesh` 把网格、带名字的边界和工况留在同一份数据里。Transolver、GeoTransolver、GLOBE 可以从同一份 DrivAerML 数据提取不同输入，不必各存一套预处理数组。但库只检查数据结构，不知道实际边界条件和单位是否齐全。[论文 §3、§5](https://arxiv.org/html/2610.39072v1#S3) · [固定版本实现](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/mesh/domain_mesh.py)

在作者的**合成热传导对照**中，改变壁面温度和热流，三种骨干在同一组 200 个留出几何上，仅看几何时的相对误差都是 **86.6%**；给全局摘要降到 **42.5–45.7%**，给每段边界自己的条件才降到 **5.5–9.4%**（边界变化强度 σ=1，八种子中位数）。差别来自模型知道了什么，不是换存储格式带来的精度。[表 6 与协议](https://arxiv.org/html/2610.39072v1#A2.T6)

回到握球：同一个起始姿态下，「继续保持」和「卸载食指」应作为不同的后续输入，而不是把两个结果都硬塞给同一个无动作模型。用于评分的下一次接触读数不能倒过来喂给预测器。

## 单独量接触，也要量探针的盲区

DeFormer 用初始车壳、厚度和查询时刻先预测形变，再冻结主网，在**预测形状**上寻找局部节点—面配对，用图网络预测位置修正。它不用前一帧推进下一帧，也不报告可靠的接触力。Yaris 配方还有独立的评估时墙面裁剪。[官方配方](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#deformer-recipes-data-preparation-training-and-evaluation) · [固定版本修正器](https://github.com/NVIDIA/physicsnemo/blob/84ffe103a9e228335ca59987ed3674c0c2715195/physicsnemo/experimental/models/deformer/corrector.py)

作者报告，主网加修正后，整车位置 RMSE 由 **7.6 降到 7.5 mm**。在 20 个验证设计里，窄搜索的额外壳面穿越为 **61,930 → 9,091** 个节点帧；扫得更深后为 **75,342 → 15,111**，改善从约 6.8 倍变成约 5.0 倍。薄壳相互穿越后，节点若离面太远，窄搜索反而配不上该面。这里确认的是**搜索覆盖先漏掉深穿越**，不是确定了预测为何穿越。计数以参考解为基准；参考解也存在穿越，节点帧不是独立撞击次数。[评估定义与搜索上限](https://docs.nvidia.com/physicsnemo/26.11/physicsnemo/examples/structural_mechanics/crash/README.html#evaluate)

握球也应分开记录「手指法向载荷低于阈值」和「两表面已经分离」。前者是原生接触事件口径，后者要有独立几何证据；没有候选配对不能当作测得了正间隙。

## DexLab 先做哪一个判断？

保留原生仿真和独立评分。等 [#261](https://github.com/huangkiki/Dexlab/issues/261) 有相容输入和合格的原生重复后，从同一前缀分叉做保持与食指卸载；先比简单动作基线，再问局部接触修正能否在留出整回合上额外减少逐指事件漏报，而不把自由空间误判成接触。一起报告事件时间、位姿、探针覆盖和端到端成本。若事件收益未超过重复波动，不升级模型。

这是从论文、官方车撞配方和 DexLab 已有离线记录得到的研究建议。没有复测 NVIDIA 的车撞结果，也没有在 DexLab 训练新模型、替换求解器或验证真机收益。[Discussion #425](https://github.com/huangkiki/Dexlab/discussions/425)
