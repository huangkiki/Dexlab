# MuJoCo 斜面 solver 结果

[English](mujoco-incline-results.md) | [简体中文](mujoco-incline-results.zh-CN.md)

官方 MuJoCo 3.15.0、CPU float64、Euler：三个 elliptic 配置各通过 3/9 正例，三个 pyramidal 配置均为 0/9。六个关闭平面碰撞的负例均形成有效自由落体记录，并被正确拒绝。结论仅针对[冻结的数值配置](mujoco-incline-protocol.zh-CN.md)，不表示整个引擎不能完成斜面任务，不构成材料标定或六引擎排名。没有配置获得 coverage-v1 可靠覆盖计数。

| Solver／摩擦锥 | 正例通过 | 无效正例 | 负例 |
|---|---:|---:|---|
| pgs-elliptic | 3/9 | 0 | 按预期拒绝 |
| pgs-pyramidal | 0/9 | 0 | 按预期拒绝 |
| cg-elliptic | 3/9 | 0 | 按预期拒绝 |
| cg-pyramidal | 0/9 | 3 | 按预期拒绝 |
| newton-elliptic | 3/9 | 0 | 按预期拒绝 |
| newton-pyramidal | 0/9 | 3 | 按预期拒绝 |

三个 elliptic 配置的静态工况均超出原有 1 mm 漂移限制，三个滑动工况均失败，零摩擦工况均通过。三个 pyramidal 配置在相同物理阈值下全部正例失败；其中 CG 与 Newton 各有三例名义零摩擦记录还未通过记录有效性检查。无效例保留在分母中，不能得分；不从力／状态不一致的数据宣称物理精度。各配置的清单与哈希绑定评分位于 [`evidence/mujoco-incline/`](evidence/mujoco-incline/pgs-elliptic-score.json)。

Newton/elliptic 的九个正例完整复用历史观测，原包全部 18 例及阻抗 .99 失败均保留，额外九例不计入本轮分数。原包附带了后续 recorder；[源码恢复与复用审计](evidence/mujoco-incline/history-reuse-audit.json) 从提交 `0904240e594f4e1fabb2bd908a32af830afa84b2` 找到与当时哈希完全一致的原始源码。60 次前瞻零步准入通过，九份历史 XML 的原生有效参数与新代码完全一致。历史加载库映射、逐接触账本和资源压力仍然缺失，新准入没有补写这些历史字段。

CG/pyramidal 在 2/1/.5 ms 的最大动量残差为 .0120141691/.00204689054/.000303783207 N·s；Newton/pyramidal 为 .00114039045/.0000238631735/.0000126500777 N·s，原有限制是 1e-7 N·s。逐接触重构力与原生广义力一致，加速度与速度增量也一致；问题采样处迭代数远低于上限。尚不能据此确定引擎缺陷或因果机制，[#157](https://github.com/huangkiki/Dexlab/issues/157) 负责源码与对照归因。不重跑筛掉失败，也不放宽限制。

60 个编译 XML 导出重读均在 1e-12 绝对比较阈值下检测到舍入损失，最大差异包括惯量 3.33e-11 kg·m²、位置 4.09e-8 m、旋转矩阵分量 4.03e-7。这些微小差异不等于已测得任务表现变化，采集始终使用原始 XML。几何、质心、惯量、摩擦组合、solver 参数、力／力矩坐标、接触账本和时刻独立核对。[官方 wheel 证明](evidence/mujoco-incline/official-proof.json) 绑定 137 个代码文件及实际加载的核心，无引擎补丁。

六次采集启动共完成 51 个新回合、117,000 个原生步，另复用九个历史正例。新运行记录的原生推进合计 0.519393 s、读回 2.144813 s、各例准备 0.094822 s；它们是带观测开销的记录，不作为独占性能基准或历史速度排名。前四配置整条命令耗时 137.520 s，原因是原独立评分器反复解压惰性 NPZ 数组。修订后每个通道只读取一次，前三份完整评分逐项相同；两个不一致配置的全部无效例也得到保留。后续命令耗时 1.914 s，评分修复没有重新采集物理数据。

[资源记录](evidence/mujoco-incline/resources.json) 保留 cgroup 计数、压力、CPU 限流、I/O 和整卡显存快照。冻结的 16 GiB／4 核等效配额批次峰值 113.41 MiB，无 memory-high/max/OOM 事件或 CPU 限流；下一批同类负载可采用最低 8 GiB 档。完整 SDF 夹持回归根据独立实测采用 32 GiB，不能套用小模型峰值。运行中的批次不变更资源，也不补写历史遥测。正式夹持预算未使用。

[Archive](https://github.com/huangkiki/Dexlab/releases/download/v0.50.0/dexlab-mujoco-incline-v1-evidence2.tar.gz) · SHA-256 `d6c38604d3b3110f58a98dfd82f9938133d4365c4f8391dfcd1acb31564cb13b` · 42,164,529 bytes

原始包包含新旧全部轨迹、输入／编译模型、源码快照、冻结协议、有效参数、状态账本、独立评分、资源证据及逐文件 SHA256SUMS。按包内 README 用 NumPy 离线评分。第一份打包草稿保留本地；打包修订 2 补全压力／显存／资源投影并移除私有主机路径，物理协议仍为修订 1。
