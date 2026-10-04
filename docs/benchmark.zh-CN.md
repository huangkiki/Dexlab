# 基准协议

[English](benchmark.md) | [简体中文](benchmark.zh-CN.md)

DexLab 将**受控物理比较**与**任务鲁棒性评估**分开。前者要求共同的物理目标响应、控制规律与边界条件；后者允许后端独立配置，但必须冻结配置并公开调参条件。现有苹果场景属于后者，不代表材料已标定或引擎精度排名。

## 苹果场景：可执行的第一层

[apple-stem-v1.json](../benchmarks/apple-stem-v1.json) 在实验运行前提交冻结：20 个开发场景、10 个回归场景、100 个正式测试场景，三组 ID 与种子互不重叠。每个场景记录具体数值，两个后端读取同一行，不依赖引擎内部 RNG 的一致性。默认策略来源于 v0.1.0，没有针对这些场景重新调优。

| 参数 | 分布与单位 | 来源 |
|---|---|---|
| 苹果质量 | 均匀 0.16–0.24 kg | 工程扰动假设 |
| 初始水平偏移 x、y | 分别均匀 −5–5 mm | 工程扰动假设 |
| 初始绕竖直轴旋转 | 均匀 −10–10° | 工程扰动假设 |
| 碰撞几何、驱动、接触参数 | 沿用冻结的各后端默认值 | [后端说明](sdf-backends.zh-CN.md) |

上述范围不是硬件测量分布。机器人基座和台面不变；苹果质量变化同时改变其惯量。初始苹果始终先用 SuperDex 在固定 2 ms 下静置 3 秒，随后已知位姿规划器生成动作。MuJoCo 接收同一准备过程导出的物理模型，再进行原有的一次位置对齐。因而这不是端到端纯 MuJoCo 准备链，也不是冻结绝对关节命令的受控比较。

```bash
# 先复核未扰动基线；独立输出目录，不覆盖历史证据
.venv/bin/python -m dexlab.benchmark run --case baseline \
  --output demos/apple-stem-grasp/runs/benchmark-baseline
# 10 个配对回归场景，共 20 个完整 14 秒实验
.venv/bin/python -m dexlab.benchmark run --split regression \
  --output demos/apple-stem-grasp/runs/benchmark-regression
# 冻结策略后一次性评估 100 个场景，共 200 个实验
.venv/bin/python -m dexlab.benchmark run --split test \
  --output demos/apple-stem-grasp/runs/benchmark-test
# 在相同未扰动场景上分别运行 h、h/2、h/4
.venv/bin/python -m dexlab.benchmark run --case baseline --timestep-sweep \
  --output demos/apple-stem-grasp/runs/benchmark-timestep
```

`--backend mujoco|superdex|all` 选择后端，`--case regression-000` 选择当前 split 内的单个场景。默认每实验超时 1200 秒，`--timeout` 可修改；超时与崩溃计入失败，保留日志。完整场景计算时间通常长于仿真时间。

`--resume` 仅在场景、源文件、环境和选择完全一致且已有证据哈希未变时跳过已完成实验。没有终态记录的目录不会自动重跑：先检查原进程，保留中断证据，再使用新目录。输出包含 `run.json`、原始 suite 副本、每实验的 `job.json`、`result.json`、`episode.log`、原始物理数组及独立评分。所有预定实验始终出现在 `report.json` 的分母中，包括 pending、runtime_error 和 timeout；报告须完成后才能作为最终结果。

CLI 返回 0 表示所有实验完成评分，**不表示每次抓取成功**。报告含全部逐场结果、失败项和成功率的 95% Wilson 区间；不能只挑成功视频或只平均成功场景。正式测试结果不能用于再调同版策略，改设计应创建新版本测试协议。

新批次将 MuJoCo 编译模型按 1 MiB 切块、无损 gzip 压缩，并以内容哈希命名。不同场景的相同块通过硬链接共享磁盘空间；每条记录仍含完整的 `model-chunks/` 和清单，复制到其他文件系统后可独立使用。只有按顺序恢复的完整 SHA-256 与原模型一致，才移除原始二进制副本。不得原地修改以哈希命名的块。验收器和抖动诊断也兼容原始 MJB 与旧版 `model.mjb.gz`。物理数组和失败记录完整保留；剩余磁盘不足 4 GiB 时停止启动新场景。

## 已完成的实验

10 个配对回归场景全部完成评分，没有运行错误或超时。MuJoCo 默认配置通过 **1/10**，SuperDex 通过 **10/10**；95% Wilson 区间分别为 **1.8–40.4%** 与 **72.2–100%**。失败包含保持漂移、失去支撑和穿透超限，不能只统计成功场景。另行冻结的 100 个正式测试场景尚未完成评估。首轮因负科学计数法偏移触发参数传递错误、未能启动对应仿真而中止，全部记录保留。修复仅改变参数编码，不调整策略、场景或验收阈值；完整配对测试使用新目录重跑。

| 后端 | 步长 | 完整验收 | 全程最大手部穿透 |
|---|---:|---|---:|
| MuJoCo | 0.5 ms | 通过 | 0.15918 mm |
| MuJoCo | 0.25 ms | **失败：穿透超限** | 1.15241 mm |
| MuJoCo | 0.125 ms | 通过 | 0.17969 mm |
| SuperDex | 2 ms | 通过 | 0.45226 mm |
| SuperDex | 1 ms | 通过 | 0.45167 mm |
| SuperDex | 0.5 ms | 通过 | 0.45200 mm |

步长扫描使用同一个默认场景，各配置一次；不构成成功率估计。结果没有证明单调收敛，也不能据此把某引擎作为真实物理参照。判定沿用 1 mm 穿透上限，未因失败改变阈值。

[全部回归记录](../demos/apple-stem-grasp/evidence/benchmark/regression-v1.json) · [全部步长记录](../demos/apple-stem-grasp/evidence/benchmark/timestep-v1.json)。报告含每次判定、参数、耗时、环境和原始文件哈希；完整数组与模型仍在各运行目录，报告本身不足以独立重评分或回放。

```bash
# 不重跑物理：核对完整批次的场景、记录和文件哈希，保留每次失败
.venv/bin/python -m dexlab.benchmark report \
  demos/apple-stem-grasp/runs/benchmark-regression --output regression-report.json
```

报告收集器拒绝不完整批次、被修改的证据、与检查项矛盾的成功标记，以及与逐场结果不一致的汇总；输出不得覆盖已有文件。旧批次保留当时的源码哈希；新批次另外归档 Python 源码快照，恢复与收集时核对其内容。它验证归档完整性，不重新计算物理评分。

## 测量与时间步

验收沿用原有离桌、持续两指支撑、保持漂移、穿透和动量平衡阈值。预期质量由冻结场景传给独立评分器，不从运行器声称的质量推定；独立复核非默认质量时需提供 `verify_sdf_grasp.py RUN --expected-mass-kg MASS`。

- 物理步进逐步记录；中间结果不可用时标记未知。保持窗口仍为 [11, 14) 秒。
- 保持漂移与去均值 RMS 不代表材料点累计滑移。现有 SuperDex 接触法向力列为占位值，不据此计算摩擦容量。
- 准备耗时包含 SDF、静置、机器人加载、规划和显示模型构建；`physics_step_seconds` 只计原生积分调用。另报包含控制、读数与导出的执行时间；无窗口实验的渲染时间为 0。
- MuJoCo 的 h=0.5 ms，SuperDex 的 h=2 ms；各取 h/2、h/4。既有 MuJoCo 接触时间常数 5 ms 在该扫描中不触发 2h 的下限调整。驱动目标按物理步采样，移动目标速度由离散差分计算，因此比较的是整个任务的时间离散化，不是孤立求解器误差。
- 更小步长仅是数值收敛参照，不是真实物理真值。跨引擎只能在相同物理目标和容差下进一步比较速度—误差曲线。

## 接触力学实验

已实现的三个开发任务、38 次完成记录和已知失败见[接触力学实验](../demos/contact-benchmark/README.zh-CN.md)。当前名义配置未完成共同材料校准，正式留出评估仍未开始。

[Issue #10](https://github.com/huangkiki/Dexlab/issues/10) 实现压入/卸载、平面滑动、双指夹圆柱的载荷扫描和完全释放。需同时覆盖应成功与应失败条件。对理想水平法向、无几何卡住、无其他支撑的库仑模型，静态支撑上界为 `mu * (N_left + N_right)`；载荷超过上界应滑动。有限柔顺、扭转摩擦与复杂几何不得套用该简式。

受控比较固定源几何、质量惯量、物理控制规律、更新频率和限幅。接触刚度等参数以独立压入/滑动曲线匹配目标响应，不直接复制不同引擎的同名数值。共同参考几何用于复核穿透；记录接触处实际切向相对速度、法向载荷和数据覆盖。果身接触允许，但夹梗支撑与果身辅助支撑分别统计。

## 后端与求解器

[Issue #4](https://github.com/huangkiki/Dexlab/issues/4) 审查 UniSim 接入等价性；[PhysX #5](https://github.com/huangkiki/Dexlab/issues/5) 与 [Newton/其他后端 #11](https://github.com/huangkiki/Dexlab/issues/11) 分别交付运行证据。

范围覆盖固定版本 UniSim 声明的 MuJoCo/mjbatch、SuperDex、MJWarp、Newton、Motrix、Drake、Genesis、IsaacGym 与 IsaacSim，并审查 Newton 的刚体求解器 MuJoCo、XPBD、VBD、Featherstone、SemiImplicit 和 Kamino 的实际可用性。引擎、积分器、约束求解器和封装分开标识；Newton SolverMuJoCo 不算独立的非 MuJoCo 物理实现。缺失 SDK、SDF、关节或接触读数不能静默降级，更不能标为通过。

## 布料实验

已发布 7 个原生求解器配置的 105 次冻结留出实验：52 次通过协议、53 次失败；名义材料尚未完成跨求解器校准。机器人夹布通过了原协议，但后续独立几何复核检出 225 帧中有 176 帧桌体相交（最大内部深度 3.00 mm）；物理修复与双臂折叠尚未通过验收。[结果与复现](../demos/cloth-benchmark/README.zh-CN.md) · [机器人夹布](../demos/cloth-folding/README.zh-CN.md)。

[Issue #12](https://github.com/huangkiki/Dexlab/issues/12) 与刚体实验共享版本、证据和运行管理，但单独评分。首组实验为固定边拉伸/卸载、重力下垂、解析障碍物上的悬垂与接触；依据求解器支持情况增加自碰撞。

记录网格拓扑与分辨率、面密度/总质量、厚度、拉伸/剪切/弯曲/阻尼、静止构形和固定点。比较形变、下垂、残余运动、穿透、约束误差与成本，执行时间和空间分辨率研究。不同本构模型先校准响应；体积软体不能冒充薄壳布料。真实精度仍需 [#6](https://github.com/huangkiki/Dexlab/issues/6) 的材料与传感器测量。

## 方法依据

[ContactBench](https://arxiv.org/abs/2304.06372) 区分接触模型与数值近似；[SimBenchmark](https://leggedrobotics.github.io/SimBenchmark/) 比较速度—误差曲线；[GAUGE](https://internrobotics.github.io/GAUGE/) 提供实测参照思路。本协议的场景范围与验收阈值由 DexLab 声明，不是这些项目提供的硬件结论。

法向静态匹配后的[瞬态开发验证](../demos/contact-benchmark/TRANSIENT_RESPONSE.zh-CN.md)固定 K、D 与载荷历史，并比较三个步长。12 项候选中 6 项通过综合检查，所有失败保留；这些确定性检查不应当作随机成功率。
