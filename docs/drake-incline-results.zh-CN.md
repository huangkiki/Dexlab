# Drake：首轮斜面准入

[English](drake-incline-results.md) · [冻结协议](drake-incline-protocol.zh-CN.md) · [完整评分](evidence/drake-incline/score-v2.json) · [#117](https://github.com/huangkiki/Dexlab/issues/117)

**官方 Drake 1.57.0 / SAP / kLagged / 严格 hydroelastic 完成九个正例：六个通过，三个滑动工况失败。** 无地面负例具有有效自由落体动力学，并被未放宽的物理评分正确拒绝。这证明原生记录路径可用，不代表普遍斜面精度，也没有取得 `coverage-v1` 可靠任务覆盖资格。使用 CPU 双精度，未修改引擎。

| 工况 | 结果 | 加速度误差 (m/s²) | 力误差 RMSE (N) | 最大转角 (rad) |
| --- | --- | --- | --- | --- |
| static-h0.002 | PASS | 2.16255e-13 | 1.21e-07 | 0.000291529 |
| static-h0.001 | PASS | 5.00233e-12 | 2.51794e-07 | 7.52268e-05 |
| static-h0.0005 | PASS | 1.56514e-16 | 3.23458e-07 | 4.11151e-05 |
| sliding-h0.002 | FAIL | 1.60734 | 0.296993 | 0.00747664 |
| sliding-h0.001 | FAIL | 1.61137 | 0.457299 | 0.00469234 |
| sliding-h0.0005 | FAIL | 1.62362 | 1.02549 | 0.0118299 |
| frictionless-h0.002 | PASS | 2.98147e-06 | 3.89324e-06 | 3.71514e-06 |
| frictionless-h0.001 | PASS | 2.21743e-05 | 3.90137e-06 | 1.8128e-07 |
| frictionless-h0.0005 | PASS | 9.61167e-06 | 3.78805e-06 | 5.16191e-08 |
| negative-no-floor | FAIL (negative) | 2.53901 | 0.62784 | 0 |

原限值保持：加速度误差 0.05 m/s²、力误差 0.01 N、转角 0.01 rad、穿透 1 mm、滑动位置 RMSE 1 cm、速度 RMSE 1 cm/s。静态工况使用位移 ≤1 mm、速度 ≤1 mm/s。静态漂移为 0.128–0.153 mm；零摩擦位置误差 0.564–2.209 mm，加速度误差 2.98e-6–2.22e-5 m/s²。十份记录均通过时钟、位置/速度、接触/广义力及动量一致性检查；最大动量残差 2.783e-9 N·s，小于原 1e-7 限值。滑动工况随步长缩小，力误差反而从 0.297 增至 0.457、1.025 N，不能称为收敛。当前不归因于某个 solver 机制；[#151](https://github.com/huangkiki/Dexlab/issues/151) 承接材质/接触近似诊断与其余适用配置。

## 保留失败，明确修订

v1 的第一个工况以方块恰好接触平面初始化，在完成任何物理步之前触发官方原生网格/半空间裁剪断言，其余工况未运行。原记录器只捕获 `Exception`，原生 `SystemExit` 使 `error` 留为 null，但离线评分仍拒绝零长度记录。现在捕获、记录并重新抛出 `BaseException`，用中断与原生异常测试验证。旧失败字节保留，另附纠正说明，不改写历史元数据。

[匹配源码](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/proximity/mesh_half_space_intersection.cc) 按严格正距离统计顶点，却在只有一个正顶点的分支选非负顶点。事前登记的三个独立 0.1 s 静态诊断分别使用 1 nm、1 µm、100 µm 初始法向间隙，各完成 50 个有效步。这支持共面初始化退化的解释，但没有观测到内部三角形的实际距离符号。随后在九例结果产生前，把预先选定的 **1 µm** 间隙冻结到[协议 v2](evidence/drake-incline/protocol-v2.json)。v2 单列批次，不冒充历史初态；其他参数和物理限值不变。开发账本包含两次 campaign 启动、三次诊断启动、两次零时长准入，共 23,150 个有效物理步；未占用夹持正式批次预算。

## 资源与复现

采集冻结为 16 GiB、四核等效配额、禁止 swap、启动另留 8 GiB、1,800 s 截止。v2 整项服务耗时 4.253 s，cgroup 峰值内存 182,087,680 字节（173.65 MiB），内存 high/max/OOM 事件及 CPU 限流均为零。这仅是小型 CPU 准入实验的成本，不是引擎吞吐排名；后续同等负载按实测可选择最低 8 GiB 档，大型后端回归仍使用其独立测量的资源档位。

发现初始化时间戳错位会夸大第一个区间的 CPU/I/O 采样峰值，因此本报告明确撤回这些峰值；累计 CPU/I/O 计数、内核内存峰值和实际限额不受该问题影响。未来运行已修正时间戳，并用慢 GPU 查询的回归测试验证。物理在 CPU 上运行，桌面整卡显存读数不归属于此任务。

[下载全部轨迹和失败](https://github.com/huangkiki/Dexlab/releases/download/v0.49.0/dexlab-drake-incline-v2.tar.gz)。评分 JSON 绑定归档 SHA-256，归档含两次 campaign、三个诊断、两次准入、冻结代码/协议/官方证明、v1 错误字段纠正说明和逐文件哈希。原始物理文件逐字节保留；公开资源记录是明确选取的投影，撤回采样速率峰值。不分发官方 wheel 或私人主机路径。运行前核对官方 wheel 的 402 个带哈希文件及实际加载的原生库，源码/构建身份与 Python 包版本分别绑定。

```sh
# 独立 Python 3.12 环境；物理运行前核对官方证明。
python -m pip install drake==1.57.0
PYTHONPATH=src python -m dexlab.drake_incline \
  --protocol docs/evidence/drake-incline/protocol-v2.json \
  --proof docs/evidence/drake-incline/official-proof.json --output NEW_RUN
# 独立进程，只需 NumPy，不导入 pydrake：
PYTHONPATH=src python -m dexlab.drake_incline_score \
  --input dexlab-drake-incline-v2/campaign-v2 --output NEW_SCORE.json
```

采集须置于仓库资源限制/实验独占保护之下，性能采集期间不得并行哈希、传输或其他仿真。六引擎范围保持完整登记：MuJoCo [#146](https://github.com/huangkiki/Dexlab/issues/146)、SuperDex [#147](https://github.com/huangkiki/Dexlab/issues/147)、Genesis [#148](https://github.com/huangkiki/Dexlab/issues/148)、Newton Physics [#149](https://github.com/huangkiki/Dexlab/issues/149)、PhysX [#150](https://github.com/huangkiki/Dexlab/issues/150) 及 Drake 后续配置 [#151](https://github.com/huangkiki/Dexlab/issues/151)。没有推断其他引擎的新结果；kSap、kSimilar 及其他适用接触模型是未运行，不是不支持。冻结留出集、相同调优预算等新覆盖验收仍待完成，六个通过工况不计为六种任务。

[环境清单](evidence/drake-incline/environment.json)：Intel Core i9-14900K、Python 3.12.12、NumPy 2.5.3。主机清单采于运行之后的同一主机及未改变的独立环境，不冒充历史逐步遥测。
