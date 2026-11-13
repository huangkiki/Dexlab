# 7. 刚体、布料与软体为什么有不同实现路径

[教程目录](README.md) · [上一章：时间与预算](06-time-and-budget.md) · [下一章：后端与身份](08-backends-and-identity.md)

抓方块与叠布都涉及接触，但要更新的状态并不相同。把 surface cloth、MPM、Featherstone 和 Newton method 排成一个清单，会掩盖对象表示与数学问题的差异。本章帮助你先选能表达任务的模型，再读数值方法。先修是状态、质量与接触响应。

## 先问自由度保存在哪里

| 对象/表示 | 主要状态的直觉 | 还需核对什么 |
|---|---|---|
| 刚体 maximal coordinates | 每个物体的位姿和速度；关节另施加约束 | 关节误差、姿态表示、惯量与约束处理 |
| 关节广义坐标 | 用关节变量与根状态描述机构 | 拓扑、闭环限制、运动学与动力学求解 |
| 布料/壳 | 曲面顶点或其他离散自由度 | 膜与弯曲材料、厚度、质量、接触与自接触 |
| 体材料 | 体网格或粒子等状态 | 本构、形变、体积、历史变量与边界条件 |

同一渲染三角网格可以对应不同碰撞和求解表示。示例图像不能确认自由度、材料模型或耦合是否一致。

## Featherstone 与 SemiImplicit

Featherstone 在 Newton Physics 表里是实现名。固定实现用关节广义坐标，装配质量矩阵并进行 Cholesky 求解，接触采用 penalty 路径；不能由类名认定所有 Featherstone 文献算法都在这里执行。SemiImplicit 则有 maximal 刚体与材料力路径。[Newton 导读][newton]

关节广义坐标减少或组织自由度，与线性系统选择 CG/LU 是不同层面的决定；前者影响方程如何表示，后者影响一个已装配问题怎样求解。

## PBD / XPBD：预测后修正约束

位置约束方法先得到预测位置，再迭代修正。为理解 XPBD 的柔顺和乘子历史，考虑一个标量等式约束 $`C(x)=0`$，逆质量 $`w_i`$，步长 $`h`$，柔顺参数 $`\alpha`$，令 $`\tilde\alpha=\alpha/h^2`$：

```math
\Delta\lambda=\frac{-C(x)-\tilde\alpha\lambda}{\sum_i w_i\|\nabla_i C\|^2+\tilde\alpha},\qquad
\Delta x_i=w_i\nabla_i C\,\Delta\lambda.
```

公式背景见 Macklin、Müller 与 Chentanez（2016）的 [XPBD 原论文](https://matthias-research.github.io/pages/publications/XPBD.pdf)式 17–18。这是一个基本 XPBD 解释式，假设约束与参数尺度一致，省略松弛、不等式投影和不同类型约束的实现细节。若 $`C`$ 是长度，$`\alpha`$ 可按 m/N 理解，$`\tilde\alpha`$ 为 kg⁻¹；角度、体积或归一化约束必须另核对量纲。此长度约束的 $`\lambda`$ 单位为 N·s²，不是接触速度问题中单位 N·s 的冲量。乘子如何跨迭代/跨步保存也属于实现。

**不能反向给所有 PBD 实现补上这条公式。** Genesis 固定 PBD stretch 实现包含 compliance/h² 与 relaxation，但该局部公式没有保存同样的 XPBD 乘子历史；Newton 的刚体 XPBD 接触与关节也需分别追踪。[Genesis 原生路径][genesis]、[Newton 原生路径][newton]；教材第 32 章提供共同背景。

## VBD、Style3D、ImplicitMPM 与壳

| 标签 | 在登记引擎中怎样继续读 |
|---|---|
| VBD / VBD compliant / VBD legacy | Newton 的 block 更新与实际刚体分支；compliant ALM 与 legacy AVBD 的配置、历史和材料柔顺分开 |
| Style3D | Newton 固定树的专用布料实现，Projective Dynamics 外层与 PCG 内层分别计预算；不要误认成启动外部同名程序 |
| ImplicitMPM | Newton 的粒子材料状态与网格计算路径；核对材料历史、粒子/网格传递及实际控制消费者 |
| experimental-shell | SuperDex 的实验性壳实现标签；对象能力、材料和构建限制继续读[该引擎导读][superdex] |
| surface cloth | PhysX 柔性表面路径；当前源码与历史宿主 API 的身份分别记录，见[PhysX 导读][physx] |

MPM 的一条示意数据流是“粒子到网格 → 网格动力学与边界 → 回传并更新粒子”。它与固定体网格有限元的状态布局不同，也不是将一个 rigid solver 换名。教材第 27–31 章可补材料与离散背景。

<details><summary>进阶：耦合必须检查两边</summary>

两个 solver 都提供 step 方法，不代表它们已经交换力和更新状态。对刚体–布料接触，应追踪：谁生成接触，哪个系统写粒子变化，谁累积刚体反作用，在哪个时刻使用这些量。还要确定质量、参考系、冲量/力单位和是否遗漏反作用。Genesis 的 rigid coupling 是具体耦合路径标签；Newton 的 coupled ADMM 与 Kamino 的 PADMM 后端也处于不同层级。见各引擎 E6 课程，不能只从接口签名断言双向受控耦合。

</details>

## 任务选择与练习

如果任务需要布料逐节点外力，第一步是确认该原生路径能表达这些输入；若只能强制写位置，任务物理已经改变。若模型不能表达所需行为，提高 solver 预算不能补齐能力。

1. **相同三角网格与相同 Young's modulus 能证明布料模型等价吗？** 不能；厚度、离散本构、弯曲、质量、边界及接触都要核对。
2. **XPBD 柔顺参数固定，步长减半，$`\tilde\alpha`$ 如何变化？** 变为四倍；这说明公式有步长缩放，不等于无需检查离散误差或具体实现。
3. **VBD compliant 的刚度 $`k`$ 有限，提高 ALM metric 能否得到无限刚性材料？** 不能；固定 Newton 解释式 $`k_{eff}=k\rho/(k+\rho)`$ 的极限仍为 $`k`$，见原生导读。

## English summary

Choose a representation that can express the task before comparing numerical budgets. Articulated dynamics, PBD/XPBD, VBD, MPM, shells and cloth paths differ in state, material and coupling assumptions. The XPBD equation is a scoped teaching model, not a universal description of all PBD implementations. Native input consumers and reaction paths must be traced separately; no simulation is executed here.

[newton]: https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
[superdex]: https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md
[physx]: https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md
