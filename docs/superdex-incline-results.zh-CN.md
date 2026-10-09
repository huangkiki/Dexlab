# SuperDex 斜面：十二组冻结 solver 配置

[English](superdex-incline-results.md) · [协议与运行命令](superdex-incline-protocol.zh-CN.md)

九组配置通过原协议的 8/9 个正例；Newton 搭配 CG、ASYNC_CG、PARALLEL_CG 各通过 6/9，各保留两条力与状态不一致的无效记录。所有配置均未通过 0.5 ms 静态位移限制。十二个负例均为有效自由落体，全部正确拒绝。这些是固定工况计数，不是成功概率、完整调参搜索或引擎总排名。

| Nonlinear / linear / friction | 正例通过 | 无效正例 | 负例 |
|---|---:|---:|---|
| NEWTON / AUTO / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / CG / C1_REGULARIZED | 6/9 | 2 | 有效，拒绝 |
| NEWTON / GMRES / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / AUGMENTED_CG / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / LDLT / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / LU / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / ASYNC_CG / C1_REGULARIZED | 6/9 | 2 | 有效，拒绝 |
| NEWTON / PARALLEL_CG / C1_REGULARIZED | 6/9 | 2 | 有效，拒绝 |
| NEWTON / MINRES / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| BFGS / AUTO / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| SR1 / AUTO / C1_REGULARIZED | 8/9 | 0 | 有效，拒绝 |
| NEWTON / AUTO / CINF_REGULARIZED | 8/9 | 0 | 有效，拒绝 |

AUTO/C1 的九个正例复用未经修改的 v0.46.0 历史记录，负例为新增；其他十一组为前瞻采集。复用前核实了官方 wheel／源码身份，以及九个原始模型的全部既有参数读回一致。历史内部线性分支、逐接触与资源遥测仍然缺失，不能用新观测补写。[历史身份审计](superdex-solver-audit.zh-CN.md)。

## 如何解释失败

六条无效记录均来自三种 CG 路径的 1／0.5 ms 名义零摩擦工况。最大动量残差分别为 **2.1045017e-7、3.5577870e-7 N·s**，超过原有 1e-7 限制。对应时刻 actor 和 scene 都报告 **STOPPED**，非线性迭代数为五／四次。原生残差范数乘步长，与独立重算的动量残差相符；逐接触力合计和独立总力矩检查通过。这支持原生步骤没有充分收敛；具体停止条件继续由 [#159](https://github.com/huangkiki/Dexlab/issues/159) 归因，尚不能断言引擎缺陷或状态注入。[原始样本诊断](evidence/superdex-incline/invalid-record-diagnosis.json)。

8/9 配置仍存在物理失败。更换线性 solver 未消除共同的 0.5 ms 静态蠕动超限；C1 与 C∞ 都是平滑摩擦，并非精确静摩擦约束。所有配置都未获得 coverage-v1 可靠覆盖资格；十二种斜面配置仍只是一种任务。跨引擎历史协议的接触模型和调参／留出预算不同，不能合并成通用排名。

## 五个 CUDA 选项在官方构建中不可用

CUDA_CG、CUDA_GMRES，以及实验性的 CUDA 稀疏 Cholesky／LDLT／LU，都在原生 `set_solver_params` 阶段被拒绝，时间尚未推进。该 FP64 wheel 没有编译 CUDA 支持；[固定源码的检查](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp#L418-L425) 与实际错误相符。可见 GPU 不能改变二进制能力。恢复条件是官方 CUDA 构建、重新核验身份／准入并冻结新批次；这不表示 SuperDex 没有 GPU 实现。

## 证据与成本

120 次零时长准入通过。十二次串行启动新增 **99 个正例＋12 个负例，每例 2 秒，共 255,000 次原生更新**；历史九例只重算评分，不重跑物理。保存了完整有效 solver 参数、局部 COM／自由度、几何、接触归属／位置／力、独立总力／力矩、原生迭代／残差、力的时刻与中断完成长度。AUTO 内部选择的线性分支仍属源码推断，因为原生统计不暴露该字段。最初 CUDA 准入失败及后续恢复记录均保留。

采集服务墙钟时间 **63.150 秒**；准备／原生步进／观测累计分别为 **7.747／7.857／18.060 秒**，其余包含序列化、进程导入等开销。带观测开销的正确性实验不用于和历史批次比较速度。独立评分不导入 MuJoCo、SuperDex 或 Drake。[逐例耗时与迭代记录](evidence/superdex-incline/timing-and-solver-stats.json)。

本批冻结为 16 GiB、四核等效配额、禁用 swap，启动另留 8 GiB，并串行隔离传输与测量。cgroup 内存峰值 **905.484 MiB**，没有内存超限或 OOM；CPU 限流三次，共 5.514 ms。后续同类记录任务可用最低 8 GiB 档；完整 SDF 回归另用实测得出的 32 GiB 档。已保存显存和压力观测，不宣称本批使用 GPU 计算。

结果出来后没有重跑轨迹或放宽阈值。之后的记录器修订仅允许保存原始非有限观测，以供独立拒绝；本批全部观测有限，因此既有数据和评分不变。采集源码与最终交付源码分别保留。

[Scores and protocol identities](evidence/superdex-incline/profiles.json) · [Official runtime proof](evidence/superdex-incline/official-proof.json) · [Native rejection of CUDA options](evidence/superdex-incline/unsupported.json) · [Resource observations](evidence/superdex-incline/resources.json)

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.51.0/dexlab-superdex-incline-v1.tar.gz) · [Archive SHA256](evidence/superdex-incline/archive.json)
