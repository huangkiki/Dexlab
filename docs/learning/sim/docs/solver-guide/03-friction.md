# 3. 摩擦为什么不只是一个系数

[教程目录](README.md) · [上一章：接触](02-contact.md) · [下一章：约束求解](04-constraints.md)

策略抓住物体后缓慢滑落，你把 `mu` 加倍，训练回报变好了。这还不能定位原因：法向支撑、材料组合、摩擦近似和控制频率都可能影响结果。本章教你读摩擦锥、patch 与正则化，先修是法向接触和力/冲量的区别。

## 从一个斜面建立参照

理想各向同性 Coulomb 接触中，切向力满足

```math
\|\mathbf f_t\|_2\le\mu f_n.
```

静止时，摩擦力在容量内平衡切向外力；持续滑动时，理想动摩擦方向反向于切向相对速度。$`\mu`$ 无量纲，$`f_n`$ 和 $`\mathbf f_t`$ 单位 N。用整步冲量描述时可写相应冲量约束，但必须确认同一时间区间和离散法则。

对无转动、无其他外力的斜面方块，静止条件为 $`\tan\theta\le\mu_s`$。例如 $`\theta=20^\circ`$ 时 $`\tan\theta\approx0.364`$；理想模型下 $`\mu_s=0.5`$ 足以提供静摩擦容量。这不是某引擎一定静止的预测，因为其离散摩擦近似、材料组合与几何仍需核对。

## Elliptic 与 pyramidal 改了什么

把法向支撑固定，观察两个切向方向的允许力：理想各向同性截面是圆盘；不同方向的尺度可以形成椭圆。Pyramidal 用多面体近似锥面，在两个切向自由度的简单构造中会出现棱边与方向性。更多摩擦维度还可能包括扭转与滚动，不能都画成二维圆。

一个纯教学对照是圆盘 $`f_x^2+f_y^2\le(\mu f_n)^2`$ 与菱形 $`|f_x|+|f_y|\le\mu f_n`$。沿 45° 方向，菱形半径只有该圆盘的 $`1/\sqrt2`$。这里固定的是这两条公式的尺度；实际引擎的基、系数映射与维度必须查源码，不能直接用这个比例替所有 pyramidal 配置做材料换算。

[MuJoCo 导读][mujoco]解释 cone 与 solver 的组合，[Genesis 导读][genesis]给出模型/兼容模式的合法组合。改变 cone 会改变数值问题，不只是给同一问题换一个更快的算法。

## Patch friction 与正则化

| 名称 | 它处理的问题 | 阅读时避免的混淆 |
|---|---|---|
| PhysX patch friction | 将相关接触组织成 patch，用摩擦 anchors 处理切向作用 | 接触点数不等于独立摩擦容量的份数；法向点与摩擦 anchor 报告不必一一对应 |
| SuperDex `C1_REGULARIZED` | 在该实现中采用相应光滑摩擦形式 | 名称不能单独推出平滑尺度的数值和最终误差 |
| SuperDex `CINF_REGULARIZED` | 采用另一种平滑形式 | 更光滑不等于对任何材料更真实，也不保证任意任务更容易优化 |

固定实现和字段解释分别见 [PhysX][physx]、[SuperDex][superdex]。C1 与 C∞ 描述连续可微的阶数；实际切换位置、尺度及参数单位以原公式为准。

为理解光滑带来的代价，可看一个**非引擎特定**的教学摩擦律：

```math
\mathbf f_t=-\mu f_n\frac{\mathbf v_t}{\sqrt{\|\mathbf v_t\|^2+\varepsilon^2}},\qquad\varepsilon>0.
```

$`\varepsilon`$ 单位 m/s。低速附近力随速度平滑变化；此公式在严格零速度时给零切向力，所以不能仅凭它承担所有静摩擦平衡。这解释了为何要查具体正则化和历史变量，而不是把这里的公式认作 SuperDex、Drake 或 MuJoCo 的实现。

<details><summary>进阶：怎样设计一个可检验的诊断？</summary>

保持质量、接触几何、法向负载、物理时长和观测协议固定，分别比较摩擦平滑尺度、时间步和求解预算。记录平均滑移与速度、实际支撑、切向作用以及残差；一次只改变能解释的因素。低速蠕动可能与模型有关，也可能来自有限求解或驱动，不能只凭曲线形状完成归因。该设计是后续运行方案，本章没有执行。

</details>

## 配置与诊断练习

一份摩擦配置至少应包含：两个物体的材料及组合律、法向模型、锥或 patch 表示、正则化及单位、静/动参数的实际消费者、接触维度、时间步和迭代预算。`friction every iteration` 改的是更新频率，相关语义见[第 6 章](06-time-and-budget.md)，不能当成另一种摩擦系数。

1. **$`f_n=10`$ N、$`\mu=0.4`$ 时，理想切向容量是多少？** 4 N；法向力本身若读错或模型改变，这个计算不能解释实际抓取。
2. **两引擎都配置 mu=0.5，能直接比较滑动误差吗？** 先对齐材料组合、法向响应、摩擦近似、几何和观测，才能定义误差比较。
3. **平滑后的梯度更连续，是否证明 sim-to-real 更好？** 不能。可优化性与物理模型匹配是两个问题，需要各自证据。

## English summary

Friction depends on normal support, material combination, cone/patch representation and regularization. A circular versus diamond section illustrates directional approximation, not an engine-independent coefficient conversion. Smoothness can improve differentiability while changing low-speed response. Examples here are analytical teaching constructions; native reproduction remains deferred.

[mujoco]: https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
[physx]: https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md
[superdex]: https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md
