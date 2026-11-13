# 力、力矩、冲量与读数时点

本篇完成 B5，应用入口归 A4。先修为[接触坐标与锥](contact-models.md)、[一步执行链](dynamics-and-pipeline.md)和[E2 actuator 输出](actuation-and-control.md)。固定 MuJoCo 3.15.0 原生核心；传感器完整配置/渲染留 E4，这里只解释力观测需要的语义。所有示例未执行，不提供碰撞峰值、夹持力或稳定性结论。

## 1. 同一个“力”字下面有不同量

| 原生量 | 单位/空间 | 实际含义 |
|---|---|---|
| `ctrl` | 依执行器定义 | 控制请求，可以是位置、速度、力、四元数或组合；不是统一单位的力 |
| `actuator_force` | 各输出的力/力矩等 | 执行器输出坐标中的量，长 nout，不等于接触力 |
| `qfrc_actuator` | nv，广义力 | 经 transmission、重力补偿与 joint 限幅等步骤后的驱动力 |
| `qfrc_applied`, `xfrc_applied` | 广义力；body 世界轴力/矩 | 外部输入；xfrc 以 body CoM 为施力点，顺序 force:torque |
| `efc_force` | nefc，约束行坐标 | 等式、frictionloss、limit、contact 混合；pyramid 中是边权 |
| `qfrc_constraint` | nv，广义力 | 通常 Jᵀefc_force；不是某一 geom 的 3D 力。IPC 分支还可包含 flex contact |
| `mj_contactForce` | 6，contact 轴，force:torque | 一个接触的净界面 wrench；解码 pyramid 并扣 geom adhesion |
| `cfrc_ext`, `cfrc_int` | nbody×6，内部 com-based torque:force | RNE 后处理的外部/与父 body 相互作用 wrench，不是 body 原点力计直接读数 |
| `sensor force/torque` | site 轴，N/N·m | body 与父 body 的相互作用，转换到 site 点/轴 |
| `sensor touch` | 标量 N | 满足 body 与 site 区域/射线条件的正法向接触力之和 |

[E2 力链](actuation-and-control.md)、[mjData 字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L297)、[外力投影](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L497)。广义力坐标的符号依关节轴而定；接触局部量的符号依 geom 顺序，site 传感器又有自己的轴和参考点。没有同时记录空间、参考点、阶段的数组无法可靠比较。

## 2. `mj_contactForce` 是解码函数，不再做一次碰撞求解

[实际函数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L1157)先将 6 项结果清零，只在 ID 有效且 `efc_address>=0` 时读取该 contact 的约束行：pyramidal 调用 decodePyramid，elliptic 复制 dim 个有效分量，最后从 normal 扣除 adhesion。余下分量维持零。

因此返回 `[0,0,0,0,0,0]` 可能表示 inactive/无行，也可能表示有效行的零净力；只看返回数组不能区分。每次至少配对读 `geom[2]`、`flex[2]`、`dist`、`dim`、`exclude`、`efc_address` 与求解时刻。旧的 geom1/geom2 字段已 deprecated，新示例使用 `geom[0/1]`。[接触描述符](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L56)

普通 contact 的六项顺序是

$$
w_c=(F_n,F_{t1},F_{t2},T_n,T_{t1},T_{t2}).
$$

第一组三力 N，第二组三力矩 N·m；不要套 `mj_objectVelocity` 的 rot:lin 顺序。dim=3 时后三项为零，仅说明点接触没有直接摩擦偶矩，**不意味着关于 body CoM 的接触力矩为零**。

### 哪一侧受正力

法向从 geom[0] 指向 geom[1]。接触 Jacobian 是 `J2−J1`，所以解码后的正 wrench **作用在 geom[1] 所属 body**，geom[0] 受反向 wrench。核心 RNE 后处理正是对 body0 加 −w，对 body1 加 +w，可据此核对符号，而不用凭画面猜。[核心应用符号](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L2543)、[Jacobian 差](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L438)

Flex 侧可能 `geom=-1`；不能用 −1 直接索引 geom_bodyid，那在 Python 中会静默选到最后一个 geom。下面片段明确限定 geom–geom，flex 分布到节点的力需要其 own Jacobian/接触结构，留 E6。

## 3. 旋转轴与移动力矩参考点是两件事

令 C 为 contact.frame reshape 得到的 3×3 矩阵，其**行**为 contact 轴的世界表示，则

$$
F_w=C^T F_c,\qquad T_{p,w}=C^T T_c.
$$

此时力矩仍关于 contact.pos=p。若要关于某 body 的 CoM c：

$$
T_{c,w}=T_{p,w}+(p-c)\times F_w.
$$

先确定作用侧（符号），再用该侧 CoM；若改成 body 原点则改用 xpos，不是 xipos。最后才以需要的 body/site 轴旋转分量。纯转置矩阵只改变坐标轴，不能自动加入力臂。[RNE 接触旋转](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L2543)

手算：在世界点 p=(0.2,0,0)m 有 F=(0,0,10)N，关于原点的力矩贡献是 (0,−2,0)N·m，即使局部接触 T=0。作用在另一侧的 F、接触偶矩先全部反号，再用另一侧参考点计算。

多点接触求合 wrench 时，必须先把每个点转换到**同一坐标轴和同一参考点**再相加。不能直接相加不同 contact.frame 的三个数组。`sum(abs(normal))` 是一种标量汇总，可能用于特定夹持定义，但不是物体合力，也不是六维 wrench 范数。

## 4. 广义投影与净力账本

无 adhesion、无 IPC、无 passive flex 的常规路径中，`mj_mulJacTVec(model,data,out,data.efc_force)` 给出装配力投影，可与 `qfrc_constraint` 对照；它包括所有行，不是单一物体力。

Geom adhesion 是反例：`qfrc_adhesion` 作为 passive 的一部分已经进了 qfrc_smooth，efc_force 的 normal 仍是平移锥的正锥变量；`mj_contactForce` 则返回扣除 adhesion 的净值。若用 contactForce 重新投影净力，又额外加 qfrc_adhesion，就重复计入吸力。若只投影 efc_force 来称“所有净界面力”，又漏了被动吸力。[被动力合并](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L980)

同理 `qfrc_actuator` 的限幅不限制 qfrc_constraint、用户外力和所有被动力。观察指尖 contact force 不能只打印 actuator_force；观察关节执行器饱和也不能只读 sensor touch。

## 5. 力传感器为什么不等于 contactForce

`mj_rnePostConstraint` 从已求 qacc、外力、接触和机构作用回算 `cacc/cfrc_ext/cfrc_int`。`force/torque` 传感器先确保这个后处理已完成，再把与父 body 的 interaction wrench 从内部参考点搬到 site 点、旋转到 site 轴，分别取 force/torque 部分。[传感器实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L998)、[site 变换](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1285)

一个手腕传感器可以读到后代负载的惯性与重力传递，并不要求 sensor site 恰好落在外部接触点；反过来，free body 没有物理腕部连接，给它放一个 site 不能凭空创造真实腕部结构。原生 XML 契约把 site 挂在 child，方向约定表述为从 child 指向 parent；若物理传感器按相反侧安装，符号也要反转。不要拿某 contact 的 geom[1] 正号套用。[force/torque 契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L7304)

Touch 只累计属于 sensorized body、满足区域射线相交测试的**正**净法向接触力。源码遇到 normal≤0 就跳过，所以不能把它当作能量测拉力的黏附传感器，也不包含剪切与滚动力矩。区域外接触的法向射线若与区域相交也可能被计入；它不只是“点必须在 site 内”的集合判断。[touch 条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1012)

新 contact sensor 的聚合/排序和 E4 的完整传感器配置是另一个接口；不要把 `contactForce`、touch、force/torque 与 contact sensor 的输出互相当别名。本篇只建立读数辨别与原生力计算路径。

## 6. 时间戳比数组名字更重要

对当前状态做 `mj_forward` 后读取的是**本次状态/输入/配置上的求解结果**；没有时间推进，所以不是一段运动内测得的平均力，也没有保证达到静力平衡。只调用 collision 后再取 contactForce 更不能取得新动力学力。

常规一步中先算约束力/加速度和 sensorAcc，再推进 qpos/qvel/time。因此要把步内结果标记为如 `solve_at=t_k, step=[t_k,t_k+h]`，不能看到返回后的 `data.time=t_k+h` 就无条件把旧几何与力叫“末态观测”。RK4 各 stage 更新派生缓存但跳过传感器，结果更加不能混搭；拆分 step1/step2 要遵守 E1 与本阶段的积分限制。[forward/积分顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1993)

需要末态一致观测时，可以明确在末态重新 forward，然后拷贝字段并标记 `query_at=t_k+h`。这是另一个状态上的新求解，尤其改变控制或 warmstart 时，不应拿它冒充上一物理步已作用的力。记录数据时还应携带 solver/cone/integrator、h、iteration/tolerance、控制采样点与轴约定。

`discrete` 的 qacc 是速度差/h，相关加速度阶段观测具有步映射语义；并非所有 force 数组自动成为某真实硬件滤波后的平均值。IPC 会在自己的步求解后重算加速度阶段传感器；不能使用普通 forward 的中间值推断最终 IPC 受力，E6 再解释其完整生命周期。

## 7. 何时可以用 Fh 叫冲量

物理冲量是 `P=∫F(t)dt`（N·s），角冲量是 `L=∫T(t)dt`（N·m·s）。用单步力乘 h 是矩形求积，只有当该力代表这段时间的常值/平均作用、坐标轴及参考点处理一致时才对应该离散模型的冲量。把一次 static forward 的瞬时力乘任意时长，不能制造真实碰撞冲量。

对于多 stage RK4，单个 stage 或最后缓存的 contactForce 不等于所有 stage 的加权积分。对于 Euler 的隐式阻尼修正或 implicit 系列，MΔv 也不等于简单把所有步前瞬时力逐项乘 h。discrete 的有效 metric 是离散力平衡，但还应明确约束行、被动项与参考点怎样进入一步；“qacc 是 Δv/h”不消除这些分项区别。

若未来复用 DexLab 日志来估计一个窗口的平均力，应使用其实际采样协议、步长、frame 与接触身份，将逐样本力先变换到同一坐标/参考点，再按时间权重积分并除窗口长度；丢失的高速峰值不能靠插值宣称恢复。这里不新建采样实验、冲量评测或统一评分器。

## 8. 原生阅读片段与易错点

[原创 plane–sphere 片段](../examples/contact-solvers/README.md)只定义模型与读数流程：一次 forward、逐 contact 读取/解码、转换 geom[1] wrench 到世界 CoM、记录选项和 ncon/nefc。还演示本版 mj_fullM 与 mj_mulJacTVec 的调用。未编译/运行，也不声称输出某个接触数或支撑力。

排错顺序是：**确认状态/阶段 → 确认 contact 是否装配 → 确认作用侧/frame/参考点 → 确认 force/torque/impulse 单位 → 确认力源是否重复或遗漏 → 最后解释 solver 误差**。例如把 normal 分量写进世界 z 轴，可能恰好在水平面看起来合理，却在斜面完全错误。

## 9. 阅读练习与答案

**题 1：** condim=3 的后三项为零，物体关于 CoM 的接触力矩是否为零？

**答：** 不一定，还要加 `(contact.pos−CoM)×F`。零的是接触点处的直接摩擦偶矩。

**题 2：** 怎样把 contactForce 转成 geom[0] 侧的世界 wrench？

**答：** 先用 Cᵀ 旋转两组三分量并全部取负，随后移动到该侧需要的参考点。不要只反法向而保留切向符号。

**题 3：** efc_address=−1，Python `efc_force[-1]` 能作为零力读取吗？

**答：** 不能，它会读最后一行而不是“不存在”。先判断地址，再用 mj_contactForce；返回零也必须保留 inactive 标签。

**题 4：** fncone=3 N、adhesion=5 N，contactForce normal 为多少，touch 会加多少？

**答：** 净 normal=−2 N；touch 对非正法向跳过，贡献零。这是源码手算，不是测量。

**题 5：** 10 N 的 forward 读数乘 1 秒就能叫 10 N·s 实测冲量吗？

**答：** 不能。缺少一秒内力的时间历程和求积协议；forward 未推进时间，只有单位形式正确。

**题 6：** 相同两个物体接触，为何下一个 step 的 contact index 不能作为旧点 ID？

**答：** 检测与装配每步重建，数目/顺序/点都可变化。需要记录双方 identity、时间和几何信息，再按任务定义匹配，不能跨步复用行地址。

**题 7：** 手腕 force sensor 为何可能与指尖 normal 总和不同？

**答：** 一个是指定 site 的体间三维相互作用，含惯性/重力传递且有轴与点；另一个是各点局部法向标量汇总，忽略方向抵消和力矩，量的定义不同。
