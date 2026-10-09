# Newton Physics 斜面：区分物理失败与数值检查

[English](newton-incline-results.md) · [协议与复现](newton-incline-protocol.zh-CN.md)

在冻结的 40 mm／64 g 方块协议下，已评测 Newton 1.6.1 / Warp 1.18.0 原生 CPU FP32 的七组配置。XPBD、Kamino PADMM 各通过九个正例中的一个，Kamino DVI 通过四个，其余配置没有通过。**49 条正例未通过数值／表示一致性检查，两个 VBD 负例也未通过。** 这是初始固定配置结果，不是引擎排名、等预算调优比较或可靠 coverage-v1 准入。

| Solver 配置 | 正例通过 | 无效正例 | 禁用接触负例 |
|---|---:|---:|---|
| XPBD / 100 次迭代 | 1/9 | 6 | 有效，正确拒绝 |
| SemiImplicit | 0/9 | 4 | 有效，正确拒绝 |
| Featherstone | 0/9 | 9 | 有效，正确拒绝 |
| VBD legacy / 100 次迭代 | 0/9 | 9 | 无效，保留 |
| VBD compliant / 100 次迭代 | 0/9 | 9 | 无效，保留 |
| Kamino PADMM / Euler | 1/9 | 8 | 有效，正确拒绝 |
| Kamino DVI / Euler | 4/9 | 4 | 有效，正确拒绝；单独续接 |

三组有通过记录的配置均通过 .5 ms 静态工况；DVI 还通过全部三个滑动工况。XPBD 另两个静态工况超过位移和／或速度限制。SemiImplicit 的有效记录在当前罚函数／平滑设置下仍未通过物理验收。无效工况留在分母；无效负例不能支持可靠覆盖。

## 这些未通过记录说明什么

原始 **1e-7 N·s** 动量一致性门槛及物理误差阈值均不变。冻结的 FP32 八倍 epsilon 检查属于工程一致性检查，**不是针对多次求解更新推导出的前向误差界**。超限本身不能证明状态注入、记录器错误或任务不可能完成。未修改引擎，初始化后未写入状态。[源码与观测解释](evidence/newton-incline/readback-interpretation.json)。

- **XPBD：**原生内核分别增量更新位置、速度，经历不同 FP32 舍入，并将极小速度截为零；默认不从最终位移重算速度。六个运动工况全部超过冻结的位置／速度检查，补充测量还发现 **4.64e-7–1.50e-6 N·s** 的动量残差，超过另一条独立门槛，均保持无效。[固定版本更新内核](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L869-L938)。
- **Kamino：**Euler 路径将四元数指数与旧四元数相乘，该更新函数中没有显式重新归一化。PADMM 的范数漂移最大 **3.56e-5**，DVI 最大 **2.22e-6**，冻结检查约为 9.54e-7。原始状态全部保留，评分器不会通过归一化制造通过。[固定版本姿态更新](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/core/math.py#L544-L560)。
- **VBD：**全部正例及两个负例超过动量门槛。无接触负例在两种模式下均为 **1.74884e-5 N·s**；原生速度由 FP32 姿态差分重构。接触工况还暴露末次 primal 受力与末次 dual 更新后查询力的差异。这是冻结证据中测得的数值限制，不能唯一解释每一项残差。[速度更新](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/rigid_vbd_kernels.py#L6675-L6740)。

独立 VBD 诊断先精确复现原始 100 次迭代前缀，再固定前 15 步各 100 次迭代，仅改变第 16 步。compliant 模式在奇数上限 99/101/1001 与偶数上限 100/1000 间，分别重复相同的 X/Z 位置和返回力；离面分量／姿态仍有极小差异。该步残差在 **4.31014e-6** 与 **4.03585e-6 N·s** 间交替，增加迭代未消除这个观测模式。legacy 在选定步改善（1000 次：1.15088e-7；1001 次：3.97352e-8 N·s），但此前误差及原始 100 次迭代的完整失败均保留。诊断不能替换正式评分。[原生字段与对照](evidence/newton-incline/vbd-diagnosis.json)。

每个工况另有[原始量描述性测量](evidence/newton-incline/observations/xpbd.json)：位移、速度、拟合加速度、位置／速度误差、力误差、接触数量、范数漂移和动量残差；其他配置有对应同名文件。几何诊断明确使用归一化后的四元数方向，不计算验收。它用于查看无效记录，不能把它们悄悄转成通过。后续精度感知协议必须重新事前冻结，并用独立留出工况验证。

## 中断的负例仍然可见

DVI 完成九个正例后，冻结的 **1800 s** 服务上限在负例完成 **1588/2000** 次更新时触发中断，另有一次已尝试的更新无法确认完成。原始 campaign 仍为 `interrupted`，评分器仍拒绝它。最终 cgroup 遥测缺失，最近样本保持“最近样本”身份。

单独预登记的 **一次启动／2000 次更新／600 s** 续接仅重新初始化这个负例，沿用原记录器、模型、参数与阈值。重叠的 1588 个状态／受力样本逐项完全一致，九个已完成正例按字节复用。组合归档包含完整旧尝试，逐项校验绑定关系；没有追溯延长原时限，也没有删除原失败。[续接冻结](evidence/newton-incline/continuation-v1-freeze.json) · [恢复校验](evidence/newton-incline/scoring-revision2.json)。

## 范围与资源

Style3D、ImplicitMPM 推进粒子系统，不是本协议独立自由刚性方块的积分器。源码排除结论仅针对当前模型和版本；构造失败不是判断依据。`SolverMuJoCo` 属于 MuJoCo 核心，其兼容封装路径单独保留未运行。[范围证据](evidence/newton-incline/unsupported.json)。在[明确列出的搜寻范围](evidence/newton-incline/history-reuse-audit.json)中未找到协议匹配的 Newton 斜面历史记录；球—平面和布料历史没有改标成斜面实验。

采集冻结 **8 GiB／4 核配额／零 swap／启动另留 8 GiB**。最大已观测采集内存峰值为 **604.988 MiB**，来自 DVI 超时前最后一次采样；已完成的 PADMM 服务峰值为 515.980 MiB。DVI 采样 CPU 峰值约 1.37 核，最后样本未出现 CPU 限流，现有证据没有说明加内存或升至八核可以解决它的运行时限。

原始服务加续接合计 **3759.875 s**，已记录原生 step 调用合计 **3638.126 s**。完整评分数据集有 **161000 次更新**，另保留中断负例的 **1588 次更新**及一次无法确认完成的尝试。step 计时不含碰撞生成、读回与序列化；开发诊断独立计账，共 1000 次更新。缓存、编译开销和求解预算不同，这些带记录的正确性成本不支持速度排名。[资源](evidence/newton-incline/resources.json) · [逐例时长](evidence/newton-incline/timing.json)。

[评分与协议](evidence/newton-incline/profiles.json) · [官方身份](evidence/newton-incline/official-proof.json) · [原始归档](https://github.com/huangkiki/Dexlab/releases/download/v0.53.0/dexlab-newton-incline-v1.tar.gz) · [SHA256](evidence/newton-incline/archive.json)
