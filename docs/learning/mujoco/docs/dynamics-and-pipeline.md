# 从广义动力学到一次 mj_step

本篇完成 E1 留下的 B0 动力学与稀疏数据结构，并展开 B1。先修是[状态与时间](state-and-time.md)和基础矩阵运算；理解控制力来源可接读[E2 驱动](actuation-and-control.md)。基线是 MuJoCo **3.15.0 原生 CPU 核心**及其官方 Python 绑定，固定 SHA 见[来源表](sources.json)。这里的执行链不等于 MJX、Warp、宿主集成或历史 DexLab 批次的执行链。

本轮没有导入引擎、编译 MJCF 或推进动力学；公式是解释，片段只做语法检查。阅读顺序建议本篇 → [接触模型](contact-models.md) → [求解与积分](solvers-and-integration.md) → [力观测](force-observations.md)。

## 1. 先声明方程在什么空间成立

考虑正质量/惯量的刚体树，以广义位置 `qpos` 表示配置，以 `qvel` 表示配置切空间速度。暂不含 sleep、IPC、插件自定义状态，也暂不使用 `discrete` 有效惯量分支。瞬时加速度满足

$$
M(q)a+c(q,v)=\tau_{\mathrm{passive}}+\tau_{\mathrm{actuator}}+
\tau_{\mathrm{applied}}+J(q)^T f,\qquad a=\dot v.
$$

这里 `q` 长 `nq`，`v/a/τ` 长 `nv`；四元数使 `nq` 与 `nv` 可以不同，不能把 `a` 直接加到 `qpos`。`M` 是 `nv × nv` 对称广义惯量；`c` 包含重力、科里奥利和离心偏置。`J` 是本次装配出的 `nefc × nv` 约束 Jacobian，`f` 是各行的约束力坐标。接触、关节限位、摩擦损失、闭环等式共用它，但各行的物理单位和可行域不同。

在一致 SI 模型中，平移自由度的 `v/a/τ` 是 m/s、m/s²、N，转动自由度则是 rad/s、rad/s²、N·m（弧度视为无量纲）。因此 `M` 的平移块、转动块和耦合块分别具有 kg、kg·m²、kg·m 的量纲；不能把整块矩阵叫“质量 kg”。功率配对 `τᵀv` 具有 W，虚功关系 `τ_constraint=Jᵀf` 保持这个配对：约束线速度行对应 N，角速度行对应 N·m，pyramid 边坐标需要先解码。

`τ_applied` 在此包含用户 `qfrc_applied` 和把 `xfrc_applied` 投影后的总和。核心实际先形成

$$
\tau_s=\texttt{qfrc_passive}-\texttt{qfrc_bias}
 +\texttt{qfrc_applied}+\texttt{qfrc_actuator}
 +\operatorname{project}(\texttt{xfrc_applied}),\quad a_0=M^{-1}\tau_s.
$$

`qacc_smooth=a0` 中的 smooth 表示**尚未加入约束求解结果**，不是模型没有任何不光滑项；例如被动力可有摩擦/饱和。`qfrc_bias` 在左边、从 `qfrc_smooth` 中减去；错误地再减一次重力会改变模型。[合成与线性求解实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1005)

## 2. M 和 c 如何从模型得到

### 2.1 空间表示先消除大坐标误差

`mj_fwdKinematics` 更新树、质心、tendon 等位置相关量；`cdof` 用空间运动向量表示各自由度，内部惯量/空间向量采取以运动树的子树质心为参考的表示。不要把内部 `cvel/cinert/cfrc` 当作 body 原点的普通笛卡尔量。E1 已给出局部/世界 pose 与 BODY/XBODY 的区别；[力观测篇](force-observations.md)继续解释 wrench 的参考点。

### 2.2 复合刚体惯量，不是逐 body 独立相加

[复合刚体算法 `mj_crb`](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L1901)先从子节点向父节点累加 `cinert` 到 `crb`，再按 DOF 与祖先的运动基计算 `M(i,j)`。对角还含 `dof_armature` 和支持的 actuator armature；`mj_makeM` 继续加入 tendon armature。这些都是**惯量项**，不能把 armature 当成力矩限制或阻尼。

树形拓扑使很多 DOF 对不耦合，核心存下三角稀疏矩阵。正定假设下用 `M=LᵀDL` 的反向稀疏分解存入 `qLD/qLDiagInv`，通过代入求 `M⁻¹b`，无需显式求逆。接近奇异的 pivot 被夹住会产生惯量警告；“还能算出数字”并不证明质量、惯量或机构设置合理。[分解与警告](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L1986)

### 2.3 RNE 计算偏置

[递归 Newton–Euler `mj_rne`](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L2362)令世界的空间线加速度为 `-gravity`，前向递推各 body 加速度和惯性 wrench，后向把子 body 力传给父 body，再投影到 `cdof`。`flg_acc=0` 去掉 `M a`，得到偏置，之后还加 tendon armature 的偏置项。它不是只算重力，也不是接触求解器；换 solver 不会把这个惯性递推换成 XPBD。

## 3. 3.15 的数据表：不要照搬旧 qM 写法

| 数据 | 含义与布局 | 阅读时的约束 |
|---|---|---|
| `data.M`, `model.M_rownnz/M_rowadr/M_colind` | 下三角 CSR 惯量，长度 `nC` | 不是可直接 reshape 的 `nv²` 数组 |
| `data.qLD`, `qLDiagInv` | 稀疏惯量因子及逆对角 | 不是另一个原始惯量矩阵 |
| `data.efc_J`, `efc_J_rownnz/rowadr/colind` | 本次约束 Jacobian；dense 时行主序，sparse 时 CSR | `nefc` 每次接触装配都可能变 |
| `data.efc_type/id` | 行种类及该种类的对象编号 | `efc_id` 不能一律当 contact ID |
| `data.efc_pos/margin/vel/aref` | 行位置、阈值、速度、参考加速度 | 摩擦行没有弹簧位置残差；surfacevel 会修正接触相对速度 |
| `data.efc_R/D/KBIP` | 正则化、其倒数、刚度/阻尼/阻抗/阻抗导数 | `efc_D=1/R` 不是积分公式中的阻尼矩阵 D |
| `data.efc_AR` | dual 路径使用的 `J M⁻¹ Jᵀ+R` 或该路径的有效 metric 版本 | primal 不一定构建完整 AR；不能无条件读它 |
| `qacc_smooth/qacc`, `qfrc_smooth/qfrc_constraint` | 约束前后加速度、光滑合力/约束投影 | `discrete` 改变 qacc 与 metric 的语义 |

字段直接见 [mjData](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L263)及[约束 arena 数组](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L348)。本版公开 `mj_fullM(model, data, dst)` 把惯量展开到目标矩阵；若只需要乘积，`mj_mulM`、`mj_mulJacVec`、`mj_mulJacTVec` 避免假设底层布局。[API 声明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L614)

`jacobian="auto"` 在**实现中 `nv >= 60` 就用 sparse**。[分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L32)与同提交 [XML 文字](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L422)在恰好 60 的边界存在措辞差异；本课按实现。稀疏与稠密只是存储/线性代数选项，不等于改了摩擦锥或物理接触律。

## 4. 约束如何装配

[装配顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2975)是 equality → DOF/tendon frictionloss → limits → contacts。例如 weld 闭环引入等式行，hinge 超限引入单边行，两个物体的摩擦接触引入一个锥块。`nefc` 是**标量求解行数**而不是接触点个数；`condim=6` 的 pyramidal 接触会用 10 行，而 elliptic 用 6 行。

对普通 geom 接触，分别算接触点属于两 body 时的 Jacobian，取 `J2-J1`，投影到 contact frame；pyramid 再把法向与摩擦方向按边基混合。`contact.efc_address=-1` 表示没有装配进去，不要对它做数组切片。[接触装配](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L1623)

约束行/投影矩阵分配在 `mjData` 的 arena 中，位置阶段会重新构造；不要跨步保存 contact index、行地址或底层数组视图作为稳定标识。保存数据时拷贝，并携带 geom 身份、位置、时间和配置。场景变更使接触配对变化，单凭 index 不能跟踪“同一个物理点”。

## 5. 一步调用链与可读量

下面是原生 `mj_step` 的路径概括，不是自行拼接阶段的替代实现。

```text
mj_step
  checkPos / checkVel
  mj_forward -> mj_forwardSkip(NONE)
    checkDiscrete: 验证选项兼容性
    fwdPosition: FK/com/tendon -> makeM/factorM -> collision
                 -> makeConstraint -> island -> projectConstraint -> transmission
                 -> 构建 discrete metric
    sensorPos / energyPos
    fwdVelocity: 速度 -> passive -> reference（discrete 延后）-> RNE bias
                 -> 更新 metric 的速度依赖值
    sensorVel / energyVel
    mjcb_control（启用 actuation 时）
    fwdActuation -> 更新 actuator metric
    discrete: 最终 metric 上的 regularization + reference
    fwdAcceleration -> fwdConstraintStage
    sensorAcc（按需 RNE post-constraint）
  checkAcc / 可选 forward-inverse 对照
  Euler / RK4 / implicit / implicitfast / discrete（含 IPC 分支）
  更新状态、时间和插件推进
```

[位置/速度阶段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L133)、[forward 全链](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1957)、[`mj_step`](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L2023)共同构成依据。位置阶段的投影只说明符号/存储已准备；尤其 discrete 下最终 R、reference 和 dual 数据还要等 actuator metric 确定。

| 调用结束 | 已完成 | 不该据此假定 |
|---|---|---|
| `mj_kinematics` | pose | 碰撞、约束力、传感器已更新 |
| `mj_collision` | 基于已有几何 pose 的接触检测 | 已解出接触力 |
| `mj_step1` | 位置/速度阶段、相应传感器与回调 | 本次 control 已经被 solver 使用 |
| `mj_forward` | 在当前状态求动力学与传感器，时间不推进 | 已经历一个物理时间区间或达到静力平衡 |
| `mj_step2` | 控制/约束/加速度及一次积分 | RK4 仍被保留；实际 split-step 对 RK4 落到 Euler |
| `mj_step` | 新的积分状态与时间 | 所有派生量都恰好属于这个新状态 |

RK4 中间 stage 会重做 forward、跳过传感器；通常的 step 返回混合“新积分状态”和“步内求解量”，且 RK4 中间缓存更不能看作末态一致快照。若要在末态测一次静态读数，明确调用新的 forward 并标成**新求解**，不能把它替代刚走完那一步的力。[RK4 缓存与最终更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1630)、[状态采样契约](state-and-time.md)

## 6. 易错点与定位顺序

1. **以为 `ncon==nefc`。** 先查 exclude、efc_address、dim 和 cone，再看其他约束行。
2. **读到旧的力后只增加 iterations。** 先确认是否只做了 kinematics/collision，读数属于哪个 forward/step 阶段。
3. **用 `M @ qacc` 与 actuator 比较就判断守恒失败。** 要包括 bias、passive、外力和约束；discrete 还换了有效 metric/shift。
4. **把 implicit 名称理解为接触也全隐式。** 四种连续加速度路径的约束求解先于积分修正，详见下一篇。
5. **把 API 核心、绑定、GPU 后端混为一体。** 本篇固定 C 源码；同名选项不构成其他后端同算法的证据。

## 7. 阅读练习与答案

**题 1：** 一个 free body 无其他关节，为什么 `M` 不是 `7×7`？

**答：** qpos 为位置三元组加四元数共 7 项，而广义速度为 6 项；M 作用在速度切空间，故为 `6×6`。不能对四元数分量定义第七个独立动量。

**题 2：** 模型有一个 condim=3 接触，使用 pyramidal，还带一个 joint frictionloss。能直接取前三个 efc_force 当接触力吗？

**答：** 不能。摩擦损失在接触前装配；接触需根据 efc_address 找到 4 条 pyramid 边，再用 mj_contactForce 解码到 6D wrench。

**题 3：** `mj_forward` 后用 `data.M.reshape(nv,nv)` 报错，是否说明模型编译失败？

**答：** 不说明。M 是长度 nC 的稀疏下三角；用本版 mj_fullM 或 mj_mulM。形状错误与动力学正确性是不同问题。

**题 4：** 机械臂末端很重，只把该 body 的惯量当作近端关节惯量会漏什么？

**答：** 漏掉姿态/力臂导致的平行轴贡献、其余后代的复合惯量、关节间耦合与 armature；CRB/RNE 沿树累计这些项。

**题 5：** 只改 ctrl，可总是调用 `mj_forwardSkip(..., VEL, ...)` 吗？

**答：** 仅在位置、速度及所有上游依赖确实仍有效时才可复用；若同时改了 qpos、qvel、模型/被动配置或相关外部回调状态，跳过阶段会用旧缓存。discrete 的 actuator metric 仍在后段刷新，不能自行省略。

**题 6：** 把 sensorAcc 移到 collision 后就读“碰撞力”可以吗？

**答：** 不可以，检测只给几何。参考、控制、无约束加速度和约束求解尚未完成；力与加速度观测要等相应解及所需 RNE 后处理。
