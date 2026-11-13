# 4. 约束问题怎样求解

[教程目录](README.md) · [上一章：摩擦](03-friction.md) · [下一章：外层与内层](05-nonlinear-and-linear.md)

“Newton 比 PGS 高级，所以直接选 Newton”缺少了最重要的一步：它们在这个引擎里解什么问题？本章先用一个接触行理解局部更新，再定位整体系数、非线性方向和 SAP。先修是接触、摩擦和矩阵向量乘法。

## 速度、约束与冲量

在固定的一步内，把示意动力学写为

```math
M(v^+-v^*)=J^T p,\qquad u=Jv^+.
```

$`v^*`$ 表示无这些约束冲量时的速度，$`p`$ 为约束冲量，$`J`$ 把广义速度映射到约束速度。平移接触的 $`p`$ 单位 N·s；混合转动、关节和接触的广义量不能统一标成这个单位。离散实现可能使用不同于裸质量矩阵的有效动力学矩阵，模型选择也会改变约束关系。

这组动力学关系还不够：需要接触、摩擦、限位和其他约束的法则，才能确定要解的问题。

## PGS：逐行更新并立即使用新状态

对于一个无柔顺、无摩擦的法向教学模型，设当前速度为 $`u`$、目标速度为 $`b`$、有效逆质量为 $`w\gt0`$、累计冲量为 $`p\ge0`$：

```math
p_{new}=\max(0,p+(b-u)/w).
```

用增量 $`p_{new}-p`$ 更新速度，然后处理下一行。后面的约束会再次影响前面的状态，因此通常要多轮 sweep。这个标量投影展示 PGS 的局部思路，没有涵盖实际锥、block、柔顺与 articulation 处理。

例如 $`p=0`$ N·s、$`u=-1`$ m/s、$`b=0`$、$`w=2`$ kg⁻¹，则本轮新增冲量为 0.5 N·s。若下一行又改变当前接触速度，就不能声称整个系统已满足约束。

## 非线性 CG 与 Newton：方向从哪里来

对可微目标 $`F(z)`$，非线性 CG 的方向可写成

```math
d_k=-g_k+\beta_k d_{k-1},\qquad g_k=\nabla F(z_k).
```

再通过步长选择更新状态。$`\beta`$ 的公式、重启规则、可行性处理和停止条件都属于具体实现。它不是拿一个固定矩阵运行线性 CG；后者在[第 5 章](05-nonlinear-and-linear.md)单独解释。

Newton 则利用局部二阶模型，典型方向由 $`H_kd_k=-g_k`$ 得到，再配合线搜索、正定化或其他约束处理。存在非光滑点时还要读实际问题及分支，不能把无约束光滑公式直接套到所有接触代码。

固定 MuJoCo 中的 PGS、非线性 CG 和 Newton 是约束求解选项；Genesis 也提供非线性 CG/Newton，但模型及合法组合不同。原生配置和固定源码见 [MuJoCo][mujoco]、[Genesis][genesis]。同名方法不说明两个系统的未知量、目标和容差相同。

## TGS 与 SAP 放在哪一层

| 名称 | 此处应建立的认识 | 继续读什么 |
|---|---|---|
| PhysX TGS | 位置迭代包含内部时间推进，有限预算的含义与普通 sweep 不同 | [PhysX 导读][physx]和[时间与预算](06-time-and-budget.md) |
| Drake SAP | 求解离散约束问题；内部还使用 Newton 方向与线性求解 | [Drake 导读][drake]，记录接触模型和离散近似 |
| kSap / kSimilar / kLagged | Drake 的离散接触近似，决定交给 SAP 的法则 | 不列成三个与 SAP 并排的 solver |

<details><summary>进阶：为什么残差小仍可能不准确？</summary>

残差衡量当前离散问题某组方程或最优性条件是否满足。建模误差来自实际物体与模型的差别；离散误差来自时间/空间近似；求解误差来自没有精确解出该离散问题。把第三项减小，不能保证前两项同步减小。还要核对残差的定义、尺度、绝对/相对判据以及采样时刻，不能用同一个数值阈值比较不同引擎的任意日志字段。

</details>

## 配置、诊断与练习

先写明未知量与问题，再记录算法、迭代上限、容差、实际停止原因和响应观测。若启用了 warm start，要把初始迭代状态与可复现条件也记下来。不要只留下 `solver=Newton`。

1. **100 次 PGS 与 100 次 Newton 是否是相同成本？** 不是；一次局部 sweep 和一次含矩阵装配/线性求解的非线性更新工作量不同，成本需实测。
2. **线性方向残差已很小，是否该物理步已收敛？** 不一定；线性系统只是当前局部问题，更新后还需检查外层目标、约束与停止条件。
3. **切换 solver 同时改变 cone 后效果改善，能归因 solver 吗？** 不能单独归因；问题表示和求解方法同时改变，需要受控对照。

## English summary

Identify the discrete problem before comparing solvers. PGS illustrates local projected updates, nonlinear CG uses gradient history, and Newton builds local second-order directions. PhysX TGS changes internal temporal updates; Drake SAP solves problems defined by separate contact approximations. Iteration counts, convergence and physical accuracy are distinct. No native experiment is reported.

[mujoco]: https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
[physx]: https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md
[drake]: https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md
