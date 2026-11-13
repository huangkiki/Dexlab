# 6. 时间步、子步和迭代预算

[教程目录](README.md) · [上一章：外层与内层](05-nonlinear-and-linear.md) · [下一章：对象与实现](07-representations.md)

一份配置同时写着 1 ms、20 substeps 和 100 iterations。它们不是三个表示精度的同义词。本章让你画出控制、物理和求解三个时间尺度，并解释 Euler、implicitfast 和 every iteration。先修为[仿真一步](01-simulation-step.md)。

## 先画时间线

假设策略每 20 ms 给一次动作，物理步长 $`h=1`$ ms，动作在区间内保持不变。一次策略动作覆盖 20 个物理步，即策略 50 Hz、物理更新 1000 Hz。每个物理步内部再做最多 100 次求解迭代，这些迭代没有让模拟时间额外走过 100 ms。

```text
策略动作 a[k] ────────────────── 下一次动作 a[k+1]
             20 个物理步
一个物理步：预测/装配 → 内部求解 → 状态写回
```

应根据代码确定 `substeps` 是把公开步长分成更小物理步，还是某个求解器内部的时间推进。控制器、碰撞生成和传感器不会仅凭字段名称自动以子步频率刷新。

## 同叫 Euler，更新顺序也要读

对 $`\dot x=v,\;\dot v=a(x,v)`$，最简单的显式 Euler 为

```math
v_{n+1}=v_n+h a_n,\qquad x_{n+1}=x_n+h v_n.
```

一个半隐式 Euler 形式则把位置改为 $`x_{n+1}=x_n+h v_{n+1}`$。从零速度、恒加速度开始，前者第一步位置增量为零，后者为 $`a h^2`$，解析值为 $`a h^2/2`$。这个单步特例用于辨认离散顺序，不是完整引擎精度排名。

[MuJoCo][mujoco] 的 Euler 还涉及其实际速度/阻尼处理；`implicitfast` 是特定导数与积分实现，不是“所有力和接触均完全隐式”的保证。[Genesis][genesis] 的 `approximate_implicitfast` 也必须沿质量修正与动力学调用解释。Newton Physics Kamino 的 Euler 路径先更新 twist 再推进 pose，不能看到名字就认作上述显式位置更新。[Newton 原生导读][newton]

<details><summary>进阶：稳定、收敛与准确为什么分开？</summary>

线性振子 $`\ddot x=-\omega^2x`$ 的半隐式 Euler 在非退化稳定区间要求 $`h\omega\lt2`$。这个条件没有承诺相位或幅值误差足够小，也不适用于任意接触系统。增加求解迭代改善的是当前离散问题的求解；减小 $`h`$ 改变离散问题本身。步长收敛检查还必须保持物理时长、动作和采样定义一致。

</details>

## 预算字段属于哪个循环

| 配置 | 它通常控制什么 | 不能直接换算成什么 |
|---|---|---|
| max iterations / sweeps | 指定循环的迭代上限 | 实际轮数、物理时长或误差上界 |
| tolerance | 某种残差或停止准则 | 不同引擎通用的物理精度 |
| 外层 / 内层 iterations | 非线性更新 / 局部线性求解预算 | 相同单位的工作量 |
| PhysX position / velocity iterations | 不同阶段的约束处理预算 | 统一的控制器更新频率 |
| Newton 报告的 100 sweeps | 登记的 XPBD/VBD 配置预算 | Kamino 或所有实现的通用字段 |

一个粗略工作量账本是 $`N_{step}\times N_{outer}\times N_{inner}`$，只适用于确有这些嵌套循环且每次工作相近的估算。提前停止、碰撞数量、稀疏结构和直接分解都会使它失效；成本最终应记录实际工作与测量。

## TGS 与两个更新选项

在本课固定 PhysX CPU 路径中，TGS 按岛的位置迭代预算 $`N`$ 使用内部步长 $`h/N`$；这不是 $`N`$ 次完整公开仿真调用。`external forces every iteration` 改变整步外力在内部步骤的分配；`friction every iteration` 对 PGS 改变摩擦处理频率，而固定 TGS 本来就每轮处理摩擦。[源码、条件与算例][physx]

因此，从 4 改到 8 次 TGS 位置迭代可能同时改变内部离散轨迹与求解工作。若要做纯算法对比，需要声明这项变化；不能把内部步长更小却写成“完全相同离散问题”。

## 练习与答案

1. **动作周期 20 ms，物理步长从 1 ms 减到 0.5 ms，如何保持控制频率？** 一次动作覆盖 40 步；若仍只覆盖 20 步，策略已变为 100 Hz，会混入控制变化。
2. **上限从 100 加到 200，实际每步仍在第 12 次满足容差，工作量一定加倍吗？** 不一定；记录实际循环与其他成本，不能只看上限。
3. **$`h=2`$ ms、TGS 岛位置迭代 8 次，应用每个公开步调用控制器，控制频率是多少？** 500 Hz；内部时间尺度为 0.25 ms，不会自动变成应用 4 kHz。

## English summary

Control periods, physical steps and solver iterations are different quantities. Read update order and derivative approximations behind Euler and implicitfast labels. PhysX TGS has internal temporal updates; its flags do not automatically reschedule the application. Stability, solver convergence, time accuracy and cost require separate evidence. Only paper examples are evaluated here.

[mujoco]: https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
[newton]: https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md
[physx]: https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md
