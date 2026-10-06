# Genesis 关节限位：先核验导入，再解释改善

[English](GENESIS_JOINT.md)

**结论：默认导入存在附加惯量，不能只用源文件质量解释运动。** 在显式零附加惯量配置中，将限位时间常数从 10 ms 改为 4 ms，使本例峰值越界从 1.791 mm 降到 0.611 mm，通过原先固定的 1 mm 工程判据。它不证明真实机械限位精度，也不证明所有机器人都适用。

![实际关节越界时序](../../docs/evidence/genesis-joint-limits.png)

图中使用每个物理步的实际关节位置，不是目标位置；上限方向、启用限位的四条轨迹均显示，没有平滑。下限方向与关闭限位负例在[完整评分](../../docs/evidence/genesis-joint-score.json)中，图来源见[清单](../../docs/evidence/genesis-joint-plot.json)。

## 问题与固定标准

研究问题：限位越界主要受步长还是约束响应参数影响？导入后的惯量是否符合声明？

合成滑块质量 0.1 kg，移动范围 [0,50] mm，从实际位置 25 mm 向 −50 / 100 mm 目标运动。零重力、无碰撞，PD 增益 100/10、驱动力 ±5 N；步长 2 ms，记录 1 s 的全部 500 步。官方 Genesis 1.4.3、Quadrants 1.3.3、CPU FP64，Newton/approximate-implicitfast、关闭 no-slip。完整配置记录在原始数据中。

- 启用限位：全过程最大越界 ≤1 mm。该值是此前冻结的工程要求，并非来自厂商或真机测量。
- 关闭限位负例：最终越界 ≥10 mm，用于排除目标位置被人为裁剪。
- 导入检查单独评分：质量、附加惯量、惯量矩阵、阻尼、增益、实际初态、限位和驱动力读回。轨迹满足越界要求不能抵消导入检查失败。

## 导入检查改变了什么

源模型没有指定 armature；实际默认值为 0.1 kg（移动关节单位），因此物理广义惯量为 0.2 kg。显式清零后为 0.1 kg。此前实验应称“默认导入配置”，不能称纯 0.1 kg 滑块响应。两种配置均保留，不能只发布更好的一条。

另一次仪器检查发现：位置控制下 `get_mass_mat()` 可包含隐式驱动阻尼项；此例多出 `dt*kv=0.02 kg`。新运行器在零力模式、静止零重力状态读回惯量，再启用目标控制。第一次将带阻尼矩阵当物理惯量的评分失败保留为仪器语义错误，而非引擎物理失败。

原生来源为 `genesis/utils/mjcf.py` 的 `solreflimit` 导入、`rigid_solver.py` 的参数整理与矩阵读回、`abd/forward_dynamics.py` 的隐式矩阵更新及 `RigidJoint.get_sol_params()`。使用官方 API，不修改引擎。未指定时间常数读回为 0.010 s；显式指定读回 0.004 s，其余六项参数保持一致。

## 全部配置结果

16 条轨迹：两种附加惯量 × 两种时间常数 × 限位开/关 × 两个方向；每个配置一次执行，不是成功率估计。

| 附加惯量 | 限位时间常数 | 启用限位峰值越界（两方向，mm） | 1 mm 判据 |
|---|---:|---:|---|
| 默认 0.1 kg | 10 ms | 1.498 | 失败 |
| 默认 0.1 kg | 4 ms | 0.226 | 通过 |
| 显式 0 kg | 10 ms | 1.791 | 失败 |
| 显式 0 kg | 4 ms | 0.611 | 通过 |

全部 16 条导入检查通过各自声明的配置。8 条关闭限位负例均越界约 50 mm。先前默认附加惯量、10 ms 时间常数下细化步长 2/1/0.5 ms，峰值越界为 1.498/1.902/1.914 mm，全部未满足 1 mm 标准：不能用“步长更细一定更好”解释结果。该历史细化只针对默认导入配置，不与零附加惯量混合。

## 复现与未完成项

沿用 [Genesis 环境](GENESIS_CONE.zh-CN.md)，先通过资源限制准入，再执行：

```bash
python -m dexlab.genesis_joint_probe /path/to/new-output
python -m dexlab.genesis_joint_score /path/to/new-output
python scripts/plot_genesis_joint.py /path/to/new-output /path/to/new-figure.png
```

输出目录不可覆盖；源码哈希、模型、实际参数、全部轨迹和阶段耗时保留。评分器不加载引擎。原始归档随后续发布交付，当前评分与图表属于本地已验证候选；不得说已发布。短 CPU 运行不作性能排名。

借鉴 [Manda 的逐层审计方法](https://mandarobotics.com/blog/comparing-physics-engines/index.html)，本例先修正导入与读数解释再讨论参数效果；并未复现其摆杆实验。#42 的夹持、释放、GPU 批量、连续回放及真机校准仍未完成。

证据包：[发布附件](https://github.com/huangkiki/Dexlab/releases/download/v0.30.0/genesis-joint-evidence-v1.tar.gz)、[哈希清单](../../docs/evidence/genesis-joint-manifest.json)。本地归档已逐项读回校验80个成员，大小1,126,996字节；SHA256 `5f93fdf18a6938a6d989fc40c728bf01db52d7a5207090bc5ee2df3134029a16`。包含步长细化失败及先前矩阵读取错误。附件在v0.30.0发布后可用。
