# PhysX 斜面：原生 SDK 结果与数值边界

[English](physx-incline-results.md) · [协议与复现](physx-incline-protocol.zh-CN.md)

四组原生 **PhysX SDK 5.9.0 / CPU / FP32** 配置完成 36 个正例与四个禁接触负例。PGS、每迭代摩擦 PGS 各通过 **7/9**，两组 TGS 各通过 **3/9**；四个负例均观测有效且被正确拒绝。**13 条正例未通过冻结的数值检查**，保留在分母中。这是固定配置的初始结果，尚无共同调优、冻结留出集或 coverage-v1 可靠覆盖信用。

| 配置 | 正例通过 | 无效正例 | 有效记录中的物理失败 | 负例 |
|---|---:|---:|---|---|
| PGS | 7/9 | 1 | 无摩擦 .5 ms：力平衡 | 有效、拒绝 |
| PGS 每迭代摩擦 | 7/9 | 0 | 滑动与无摩擦 .5 ms：力平衡 | 有效、拒绝 |
| TGS | 3/9 | 6 | 有效正例中无 | 有效、拒绝 |
| TGS 每迭代外力 | 3/9 | 6 | 有效正例中无 | 有效、拒绝 |

四组均通过三个静止工况。PGS 另通过 1/.5 ms 滑动及 2/1 ms 无摩擦；每迭代摩擦 PGS 另通过 2/1 ms 滑动及 2/1 ms 无摩擦。步长变小未单调改善这些固定配置：两组 PGS 的 .5 ms 无摩擦力平衡 RMSE 为 **.010485 N**，超过 .01 N；每迭代摩擦 PGS 的 .5 ms 滑动为 **.012763 N**。这三个有效失败的其他冻结指标通过。保留原结果，不调出替代配置覆盖失败。

## 无效记录说明什么

PGS 的 2 ms 滑动法向冲量方向差异最大 **1.008973e-10 N·s**，略高于冻结的 1e-10 N·s 工程检查。回调将 FP32 法向量乘以 FP32 标量得到冲量；检查再与解析平面法向比较，它不是推导出的舍入误差界。因此保留无效判定，不在看到结果后改标准。

两组 TGS 的六个运动工况均超过未变的 **1e-7 N·s** 状态/冲量一致性门槛，最大残差范围 **1.093918e-7–1.964716e-7 N·s**。将名义质量/重力换成原生 FP32 读回也不能消除超限。原生[接触求解器](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1566-L1584)分开执行 FP32 冲量累计与速度更新，[写回](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/source/lowleveldynamics/src/DyTGSContactPrep.cpp#L1863-L1922)暴露累计冲量。这确认了观测路径，并未唯一分解每一项残差的原因。

对 PGS 滑动和 TGS 无摩擦的 2 ms 工况各做一次独立进程重复，除耗时外，**1,000** 步状态、参数和接触流逐条完全一致。短程静止诊断中，四组反转 actor 加入顺序也完全重现。没有官方引擎补丁或初始化后状态写入。检查失败本身不证明状态注入、漏力或引擎无法完成该任务。[重复证据](evidence/physx-incline/repeat-result.json) · [数值解释与源码](evidence/physx-incline/readback-interpretation.json)。

[后续 #163](https://github.com/huangkiki/Dexlab/issues/163)负责有界数值分析，以及任何另行事前冻结、配有独立留出集的新精度协议；原评分不变。[描述性测量](evidence/physx-incline/observations/pgs.json)及同目录 `pgs-friction`、`tgs`、`tgs-external` 保存每条记录的位移、速度、加速度、旋转、穿透、支撑、力误差、残差和成本。归一化四元数方向的旋转量明确只是诊断，不能改变验收。

## 准入失败与范围

零步准入发现负例质量错误：先关闭碰撞再调用 `updateMassAndInertia`，辅助函数会忽略方块。记录器已改为先初始化质量惯量，再仅关闭碰撞。旧十工况准入及四条短程错误质量负例均保留；最终 40 项准入在正式运行前核实 64 g 和预期惯量。最初编译使用过时几何 API，并遇到未改动 SDK 头文件中的 GCC 警告，准备失败也保留。一次模块发现失败发生在任何原生启动前，随后用显式冻结源码路径重新启动。

SDK 5.9 仅有 patch friction，旧一维/二维摩擦不可用；TGS 自带逐次摩擦，其逐次外力标志对 PGS 无效。这些是源码核实的适用性判定，不是把运行错误改称不支持。CPU SDK 批次不准入 GPU 或 Isaac/ovphysx 路径。[版本选择](evidence/physx-incline/release-selection.json)区分明确版本的稳定 SDK 与封装发布，[#152](https://github.com/huangkiki/Dexlab/issues/152)继续处理框架兼容对照。

[有界历史复用审计](evidence/physx-incline/history-reuse-audit.json)没有找到核心身份已知、协议匹配的 PhysX 九例历史数据；新读回不补写 #126 的历史遥测。[准备失败](evidence/physx-incline/prior-failures.json) · [官方源码及构建身份](evidence/physx-incline/official-proof.json)。

## 资源与证据

四个串行采集服务共 **10.782 s**，记录 **92,000** 次更新；带记录的原生 simulate/fetch/接触复制调用共 **1.243 s**。采集峰值 **76.227 MiB**，CPU 限流周期为零，无 memory-high/OOM 事件。批内冻结 **8 GiB / 四核配额 / 零 swap**，启动另留 8 GiB。当前小型 CPU 模型没有显示增加配额的必要；这些是带记录的正确性成本，不是跨引擎吞吐量。[资源遥测](evidence/physx-incline/resources.json) · [各工况耗时](evidence/physx-incline/timing.json)。

开发单独使用 64 次原生启动：50 次零步准入，14 次诊断/重复，共 2,240 次更新。SDK 编译、依赖安装和提交回归另计准备成本。首次依赖安装触发 archive 配置的 32 任务上限，独立环境在 adaptive 的 128 任务上限下恢复，失败回执保留。

[评分与协议](evidence/physx-incline/profiles.json) · [原始归档](https://github.com/huangkiki/Dexlab/releases/download/v0.54.0/dexlab-physx-incline-v1.tar.gz) · [SHA256](evidence/physx-incline/archive.json)
