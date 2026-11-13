# 求解器、积分器与数值误差的边界

本篇完成 B3/B4；先修为[动力学执行链](dynamics-and-pipeline.md)、[软接触与锥](contact-models.md)、正定矩阵和梯度的概念。固定 MuJoCo 3.15.0 原生核心。这里只推导并追源码，没有运行收敛、稳定性、性能或可微实验；这些说明不能构成引擎排名。

## 1. 三层问题各自改变什么

| 层 | 原生选项/字段 | 改变的对象 |
|---|---|---|
| 接触与约束模型 | `condim`, `cone`, `solref/solimp`, `friction`, `impratio` | 力可行域、参考加速度、正则化与几何装配 |
| 约束数值算法 | `solver`, `iterations/tolerance`, `ls_*`, `noslip_*`, warmstart | 当前优化问题怎样近似求解及什么时候停 |
| 状态推进 | `integrator`, `timestep` | 加速度怎样推进状态；discrete 更把有效惯量放进约束求解 |

`mj_defaultOption` 的本版默认是 Euler、pyramidal、Newton、100 次上限、tolerance=1e-8，line search 上限 50、ls_tolerance=0.01、noslip_iterations=0、timestep=0.002 s。[实际初始化](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_init.c#L51) 这些默认值**不是** DexLab 的运行配置：报告中的 elliptic、1e-10 等需以各批 manifest 为准。100 次不能写成“每步实际执行 100 次”。

## 2. 从动力学消去加速度，得到 dual 问题

先限制在冻结当前 q/v、无 adhesion、无 IPC、无 NoSlip 后处理的连续加速度分支。令 `a0=M⁻¹τs`、`J` 为装配后的 Jacobian、`ar=efc_aref`、`R` 为正对角正则化，定义

$$
A=JM^{-1}J^T,\quad b=Ja_0-a_r.
$$

则 dual 优化为

$$
\min_{f\in\Omega}\ \frac12f^T(A+R)f+b^Tf,\qquad
 a=a_0+M^{-1}J^Tf.
$$

Ω 是各行/块可行域的直积：等式力无符号限制；frictionloss 力在上下界内；limit/无摩擦接触是非负；摩擦接触是 elliptic 锥或非负 pyramid 边权。冻结的 M 正定且 R 正时目标严格凸；这说明固定接触集合的**软模型优化问题**有唯一最优力，不等于整个接触切换轨迹光滑、稳定或物理参数正确。[约束优化与算法](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1464)、[AR 构造](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L3240)

这不是硬刚体互补问题原封不动的求解：R 使力与约束加速度允许软偏差，有限阻抗下出现小量滑移并不自动说明 solver 未收敛。反过来，如果 f 的可行性已满足，动力学梯度仍可能没收敛。

`b` 是加速度型残差，`(A+R)f+b` 也是；`f` 包含 N/N·m 或变换后的边坐标。目标不是物理能量 J，也不能将任意约束分量不归一化地当成同单位误差相加。选定广义坐标与行标度后，源内的归一化才能解释 tolerance。

## 3. Primal：在加速度空间求解

定义软约束代价

$$
s(z)=\max_{f\in\Omega}\{-z^Tf-\tfrac12 f^TRf\},\qquad z=Ja-a_r,
$$

得到 reduced primal

$$
\min_a\ \frac12(a-a_0)^TM(a-a_0)+s(Ja-a_r).
$$

在相应光滑分区，梯度 `g=M(a−a0)−Jᵀf(a)`。等式行的 `f=−z/R`，frictionloss 在力限幅之外成为线性代价，单边行与 elliptic 锥按状态选分支。Newton 使用 `Htotal=M+JᵀHcJ` 形式的 Hessian，其中 Hc 表示约束代价的二阶块（elliptic 锥块可能耦合）。不是只用 `JᵀJ`，也不是每个接触都永远有相同二阶项。[代价/力/状态更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L3513)、[primal 核心](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2800)

`discrete` 路径保留这一优化结构，但把 M 替成有效 metric，并将 τs 加上 stiffness/actuator shift。只有同时替换 metric、smooth acceleration、R 和 reference，方程才一致；不能仅在积分最后偷偷换一个质量矩阵。

## 4. 三个 solver 的实际工作

### PGS：约束力空间中的块更新

[PGS 本版实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L449)预计算 AR 对角倒数。对标量行，在其他分量固定时先做无约束极小化，再投影到区间/非负轴。对 elliptic 接触，先沿 normal 或 cone ray 更新，再固定 normal，在至多 5 维摩擦椭球内解小型 QCQP；不是把每个切向简单独立 clamp。

3.15 还包含默认打开的 thread-local `mj_nesterov_momentum=1`、外推后的可行域投影与自适应 restart；每轮以内部固定种子的 PCG32 洗牌**约束块**访问顺序。它不是每次随机 wall-clock seed，也不是文献中最朴素的固定次序 PGS。该符号是 benchmark/test 用内部开关，不把它教成公开 MJCF 选项。[外推与乱序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L500)

### CG：非线性共轭方向，不是解一次线性 CG

CG 优化加速度代价，使用预条件梯度（基础 metric solve，特殊 metric 有自己的近似预条件算子），再进行一维 line search。[预条件分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L1528) 主编译分支为 **Hager–Zhang** 更新，共轭性丢失时重启，带 beta 下界；`mjCG_PRP` 条件宏才切到 Polak–Ribière Plus。因此不能用旧教程的一句“MuJoCo CG=PR+”覆盖这个固定提交。[方向更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2942)

### Newton：Hessian 与线搜索

Newton 用解析约束二阶块形成 `Htotal`，Cholesky 分解求方向 `−Htotal⁻¹g`，约束状态变化时增量更新分解；椭圆锥需要其耦合 Hessian。密集/稀疏路径及 discrete metric 的组装不同。[Hessian 装配](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2338) Newton 每轮工作更多或迭代更少是算法结构上的可能性，不能据此宣称对所有场景更快。

CG/Newton 共用 [PrimalSearch](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L1970)：沿搜索方向计算代价、导数和二阶导数，尝试一维 Newton，再括区间/中点更新，受 ls_iterations/ls_tolerance 限制。官方“exact line search”描述目标是求方向上的极小点，**有限预算和数值停止并不保证精确达到它**；源码可返回无改善、未成功括区间或预算耗尽后的候选。`alpha==0` 会使主循环退出。

## 5. 真正的终止条件与诊断

主循环归一化系数在单块为 `scale=1/(meaninertia*max(1,nv))`；primal 岛路径改用岛内惯量对角和的倒数。统计量与原始 cost/gradient 不是同一尺度。[scale 与首轮判断](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2828)

| 算法/阶段 | 退出依据（另有 maxiter 上限） |
|---|---|
| PGS 每轮 | 缩放的 cost improvement `< tolerance` |
| CG 首次 | `max(0, 0.5*scale*gᵀP⁻¹g) < tolerance` 的预条件梯度证书；具体 P 由该路径决定 |
| Newton 首次 | 上述证书**且**缩放梯度范数过阈值；否则建 Hessian，再检查梯度与 Newton decrement 的组合 |
| CG/Newton 循环后 | 正的 improvement 小于 tolerance，或缩放梯度范数过阈值；Newton 还接受 decrement 过阈值 |
| CG/Newton line search | alpha=0 可直接退出；内部另受 ls_* 控制 |
| NoSlip | 自己的 improvement 与 noslip_tolerance，自己迭代上限 |

普通 bare-M 情况，强凸性给出 `cost(a)−cost* ≤ 0.5 gᵀM⁻¹g`；源码注释指出仅小 cost gap 在很硬方向上仍可能留有较大力误差，所以 Newton 首次零轮判断加了 gradient gate。[准确条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2850)、[主循环条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L2920)、[PGS 条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L715)

这也修正官方 warmstart 简述的省略：**Newton 不是仅 gap 小就一定零轮返回**。`tolerance=0` 关闭正阈值意义的提前收敛判断，但不保证强制执行满次数；零搜索步/数值停滞等控制流仍存在，PGS 的实际 comparison 也不是计数器锁定。

应联读 `solver_niter[island]`、`solver[island,iteration]` 的 improvement、gradient、lineslope、nactive、nchange、neval、nupdate 与模型选项；统计数组有固定存储上限，实际迭代计数可以超出保存条目。NoSlip 会把计数与统计追加到主 solver 后，不能把总数直接解释为 Newton 轮数。[统计字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L85)、[NoSlip 追加](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L935)

`tolerance=1e-10` 不表示“接触力误差 ≤1e-10 N”，也不保证穿透 ≤1e-10 m。目标缩放、力/加速度条件、接触模型、步长误差和模型误差必须分别解释。

## 6. Warmstart、岛、NoSlip

Warmstart 保存的是 `qacc_warmstart`。下一次先在**新的 J/R/reference**下把旧加速度映射成候选力与代价，再比较：PGS 的 force candidate 若比零力差就清零；primal 比较旧加速度的 Gauss+constraint cost 与 qacc_smooth 的 cost，选择较好加速度。关闭 warmstart 则以 qacc_smooth 与零 efc_force 开始。不是拿旧 contact index 对应的 efc_force 生搬硬套。[完整 warmstart](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1071)

有限迭代下 warmstart 会影响最后值，读数重现需保存它；若完全收敛，则差异由同一个最优问题约束。sleep 的隐藏派生状态与 IPC 跨步状态还需要更严格恢复，不能以一个 qpos/qvel 文件声称完全复现，详见 E1。

**Island** 把树与约束构成的耦合图拆成独立块；同一机器人树中的远端 DOF 仍可能通过惯量耦合，不是“每个 contact 一个线程”。discrete 的跨树 tendon metric 也会连接岛，flex metric 当前仍可使约束求解退回单块。每岛可独立停，PGS/CG/Newton 都有岛入口；dispatch 的潜力不构成并行性能测量。[耦合建图](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_island.c#L338)、[求解与 fallback](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1237)

**NoSlip** 是主 solver 后的摩擦后处理，重解 frictionloss 和接触摩擦，使用去掉 R 的 dual 残差；elliptic 固定法向，pyramid 调整相反边权而保持其和。它不改回一个统一的原始优化问题，也不保证消除一切滑动；不能和 “提高主 solver 精度” 视为同一动作。[后处理源码](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_solver.c#L764)

## 7. 从连续加速度到数值积分

把所有已求力合成 `F(q,v)`，暂时冻结 q，定义**正阻尼符号** `D=−∂F/∂v`。一阶线性化隐式速度更新为

$$
(M+hD)\Delta v=hF(q,v)=hMa,\quad
v^+=v+\Delta v,\quad q^+=\operatorname{integrate}(q,hv^+).
$$

这是 frozen-q、一次线性化、所选导数范围内的公式；不是求完整非线性 backward Euler 到收敛。配置更新必须使用流形积分，四元数不能逐项相加。源内 `qDeriv=∂F/∂v`，所以实现写 `M−h*qDeriv`，与上式符号一致。[implicit 实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1803)

| integrator | 3.15 实际处理 | 主要限制 |
|---|---|---|
| Euler | 先更新 v，再用新 v 更新 q；启用时把 DOF damping 导数加入对角 qH | 3.15 实现还含 damping polynomial 与映射到 joint 的 actuator damping；不是所有力都隐式 |
| implicit | 用 smooth-force 速度导数，包含 RNE 偏置导数，稀疏 LU | 不包括约束力导数；受 M 拓扑稀疏限制，跨分支 tendon damping 可能不能完整进入 |
| implicitfast | 去掉全局 RNE 速度导数并作对称处理，用对称分解 | 独立 free rigid subtree 的局部非对称陀螺项另算，不能说“一概删除所有陀螺项” |
| RK4 | 固定步长四 stage，阶段间重新 forward，四元数按配置增量积分 | 不是四个长度 h 的物理子步；接触切换/饱和下不承诺全局四阶，split-step 不能保留 RK4 |
| discrete | 把有效 metric 和隐式约束行放入 solver；最后直接 advance | qacc 是 `(v⁺−v)/h`，与 h 相关；支持组合见下节 |

[五种积分器说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L630)、[Euler 对角项](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1511)、[free-body 局部条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L808)。减小 h、增加 solver 迭代、增加应用控制频率分别作用在不同误差上；一个参数不能替代另一个。

## 8. discrete：metric、shift 与行权重必须一起变

在稳定符号的线性弹簧/阻尼局部近似下，让 `D,K` 为正半定贡献，

$$
\widehat M=M+hD+h^2K,\qquad
\widehat M a_0=F(q,v)-hKv.
$$

推导：`F(q⁺,v⁺)≈F−Kh(v+ha)−Dha`，代入 `Ma=F(q⁺,v⁺)` 即得上式。此式假定当前切空间线性化、冻结几何/系数与符合稳定符号的力项；实际肌肉/PD、tendon、fluid、flex 分支还按各自算子和 shift 组装，不能把任意用户回调导数自动包括进去。[metric 构建](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L4240)、[stiffness shift](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L3913)

一条参考弹簧阻尼行中，用本篇前文接触系数 Krow/Brow/I（与上面的广义矩阵 K/D 区分），隐式行因子为

$$
\gamma=1+hB_{row}+h^2K_{row}I,\quad
R^+=R/\gamma,\quad
 a_r^+=\frac{-B_{row}v_c-K_{row}I(r+h v_c)}{\gamma}.
$$

R 有阻抗上限对应的 floor，不能无限趋零；connect/weld 还有 Jdot·v 修正，adhesion 偏置在缩放后加入。对正格式、接触/limit 且 `h²Krow I>1` 的过硬行，refsafe 把 Krow 改为 `1/(h²I)` 并调整/限制 B；这与连续路径 timeconst≥2h 不同。[R/refsafe 更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2225)、[reference 同步](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L3470)

线性隐式处理能缓解刚度造成的步长限制，但几何穿透、未解析的碰撞时刻、控制延迟、力饱和和条件数仍限制结果。不能把官方对单行稳定性的讨论扩大成“任意步长任意模型都正确”。加速度传感器得到的是该分支的有限差分量；是否等同真实传感器还需其滤波、带宽、噪声与采样协议，不能从公式直接推定。

| 组合 | 固定源码支持边界 |
|---|---|
| discrete + PGS | tendon/actuator coupling metric 类被排除，相关力显式积分；不是与 primal 完全相同的有效 metric |
| discrete + primal + NoSlip | 主求解使用完整 metric，后处理用已分解 backbone 的 AR 近似，漏掉 coupling |
| discrete + flex metric + PGS/NoSlip | 运行时拒绝 |
| discrete + flex + Newton | 一般 attachment 或不可装配 interpolated 节点会拒绝，需 CG 路径 |
| discrete + sleep | 无 islands 或有 flex metric 时拒绝 |
| implicit/implicitfast + flex elasticity | 本版要求改用 discrete；Euler/RK4 的原有显式处理不等于稳定性保证 |
| IPC | 要求 discrete+CG，拒绝 fwdinv、sleep；涉及 2D flex 时常规 constraint stage 可跳过，最终步在 IPC 积分器里产生 |

[运行时 option 校验](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1715)、[PGS coupling 排除](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L4287)、[IPC stage 分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1944)。这里明确支持边界，不声称完成 E6 的 IPC 内循环、完整 flex 弹性与各 GPU 后端课程。discrete 的独立 free-body 陀螺修正还要求其 DOF 无约束/metric 耦合，不能只凭 freejoint 就假定启用。[解耦检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L895)

## 9. 可微与误差预算

原生 `mjd_transitionFD` 是有限差分的离散转移 Jacobian，状态扰动维度 `2*nv+na`，不是 `2*nq+na`；不等于核心已经提供所有接触的端到端解析自动微分。该函数明确拒绝 RK4、history delays 和 sleep；会恢复所需 state/ctrl/warmstart，并考虑 control clamp。[函数边界](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L538)、[状态恢复](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L300)

即使导数函数可调用，接触集合变化、锥状态切换、饱和和几何非光滑仍可使导数不连续。差分步长太小放大浮点/迭代误差，太大跨过活动集边界；warmstart/solver 停止的变化也会污染差分。教程不把 FD 接口存在视为任意控制任务的梯度正确性证明。IPC 还含不在该状态向量内的跨步量，不能把这套 compact FD 契约外推为完整 IPC 状态的 Jacobian。

## 10. 阅读练习与答案

**题 1：** Newton + pyramidal 是不合法组合吗？

**答：** 合法。cone 定义可行域，solver 定义算法，两个 option 独立；本版默认就是这个组合。

**题 2：** solver_niter=0 能证明没接触或没求解吗？

**答：** 不能。无约束会是零；CG/Newton 的 warmstart 证书也可零轮退出。查 nefc、efc_force、warmstart、tolerance 和返回路径。

**题 3：** 两次设置 tolerance 相同，为什么不能说绝对力误差相同？

**答：** 检查量可能是 cost improvement、梯度、decrement，且按惯量/岛缩放；模型刚度、坐标与条件数改变 cost 到力误差的关系。

**题 4：** `solref=(-k,-b)` 很硬，换 discrete 后是否仍把 t 下限设成 2h？

**答：** 非正直接格式没有正 timeconst 下限；discrete 对正格式过硬接触/limit 用另一套 K/B 调整和 R floor。不能套连续分支的统一夹法。

**题 5：** qacc 在 discrete 下变了，是不是只是积分器最后改了 qvel？

**答：** 不是。有效 metric、smooth solve、约束 reference/R 都已改变，qacc 本身就是步的速度差除以 h；同状态不同 h 可产生不同 qacc。

**题 6：** NoSlip 打开后 solver_niter 超过 iterations，是否越界？

**答：** 统计把主解与后处理追加累计；两者各有上限。还需区分固定统计存储容量与实际总迭代数。

**题 7：** 为什么缩小 h 不能修复漏掉的碰撞 pair？

**答：** 过滤/几何表示决定是否装配力；时间离散化再细也不能补回被过滤掉的约束。

**题 8：** 为什么 FD 状态用 nv 扰动 qpos？

**答：** 配置在流形上，单位四元数只有三个局部旋转自由度；差分需切空间扰动与配置积分，不能四个四元数分量独立扰动后当同一物理系统。
