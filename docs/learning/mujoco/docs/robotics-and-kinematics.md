# E2 · 机器人映射、FK、Jacobian 与局部 IK

基线为 **MuJoCo 3.15.0 原生 C/官方 Python**，固定源码 `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`。先修：[坐标与惯量](modeling-and-frames.md)、[状态与时间](state-and-time.md)、[驱动与控制](actuation-and-control.md)，以及最小二乘和矩阵秩。本篇完成 A5 的原生机器人接口：把外部关节名称/单位映射到模型，读取正确 frame 的 FK/Jacobian，理解有条件的 IK，以及将结果转成交由控制器执行的目标。

代码仅做语法与来源检查，未运行 IK、仿真或控制实验。局部 IK 的停止阈值是教学参数，不是机器人精度指标；求出候选姿态也不证明可执行、无碰撞或抓取成功。

## 1. 机器人导入后先固定映射契约

URDF/MJCF 的资产、单位、inertial 和编译选项见 E1。导入后应建立原生名称映射，而非按文件列表顺序拼数组。外部消息顺序、joint ID、qpos 地址、qvel 地址、actuator ID 与 ctrl 地址是不同集合。

| 外部概念 | 对应 MuJoCo 信息 | 核对条件 |
|---|---|---|
| 机器人基坐标 | body 名称与其当前 `xpos/xmat` | 固定底座、free base 和世界 frame 是否区分 |
| 某个关节名称 | `model.joint(name).id` | 不存在要报错，不让 -1 当 NumPy 最后一项 |
| 关节配置切片 | `jnt_qposadr` + joint 类型宽度 | hinge/slide 1，ball 4，free 7 |
| 速度/力切片 | `jnt_dofadr` + DOF 宽度 | 与 qpos 宽度不同 |
| 执行器命令 | actuator 名称、ctrladr/ctrlnum/ctrlspec | 一个 joint 不保证一个 actuator，一个 actuator 不保证一个 ctrl |
| 末端工具 frame | 明确的 site | 法兰、工具尖端、视觉 marker、body 质心不能混用 |
| 观测时间 | `data.time` 与采样阶段 | 外部墙钟时间需独立记录，不隐式改物理步长 |

外部编码器角 $q_e$ 与模型角可用经核实的 $q_m=sq_e+b$ 映射，s 为方向/单位比例，b 为零位偏移。速度为 $v_m=sv_e$；若需要保持功率一致，力的映射还应满足 $\tau_e=s\tau_m$（一个标量、常数 s 的坐标变换假设）。不要对角度改符号却保留力矩原符号，也不要将这种坐标比例与真实齿轮效率混为一谈。

XML joint `ref` 设置模型初始 pose 对应的 qpos 值；运行 FK 的位移使用 qpos−qpos0。一个 ref=0.5 的 hinge 在 qpos=0.5 时仍处于 XML 描述的初始几何 pose，因此“全部 qpos 写零”并不总是机器人零位。[joint ref](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L2448)、[FK 关节变换](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L108)。

`mj_name2id` 未找到返回 -1；Python 名称访问提供对象化入口，但也要明确处理错误名称。静态融合、编译重排或重新编译后重建映射，不把当前 ID 写成可跨版本永久 ID。[名称 API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L602)。

## 2. FK 计算的是哪一个 frame

MuJoCo 的树形 FK 将 body 参考变换与关节运动沿父链组合。需要末端工具 pose 时，读取命名 site 的 `site_xpos/site_xmat`；需要 body 原点则读 xpos/xmat；需要质心则读 xipos/ximat。`body_pos` 是局部模型参数，不是当前世界位置。[运行字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L214)。

设置 qpos 后调用 `mj_kinematics` 会刷新运动学。计算 Jacobian 还需要由 `mj_comPos` 刷新的 subtree_com/cdof；只调用 kinematics 后立刻使用旧 cdof 是容易漏掉的依赖。完整 `mj_forward` 也能提供这些前置阶段，但还会做碰撞、控制回调等更多工作，IK 中不必为每个候选点执行全部动力学。[Jacobian 实际读取](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L176)。

[示例模型](../examples/control-robotics/two_link.xml)为世界 XY 平面中的两个 Z 轴 hinge，杆长 $L_1=0.25$ m、$L_2=0.20$ m，工具高度固定 0.2 m，参考角为零。根据建模定义，解析位置为

$$x=L_1\cos q_1+L_2\cos(q_1+q_2),\qquad y=L_1\sin q_1+L_2\sin(q_1+q_2).$$

这可用于阅读源码时核对变换方向；没有通过运行数据验证。这个二维公式只适用于本模型的轴、零位、site 和固定基座，不能用于有 ref、其他轴系或浮动基座的机器人。

## 3. 原生 Jacobian 不是有限差分 qpos

`mj_jacSite(model,data,jacp,jacr,site_id)` 返回两个 3×nv 矩阵，分别满足

$$v_{site,W}=J_pv,\qquad \omega_{site,W}=J_rv.$$

输出在世界轴下表达；Jacobian 的列属于广义速度切空间，ball/free 的四元数不产生第四个角速度列。site 原点变化会改变平移 Jacobian，纯粹改变 site 轴向不会把这两个输出矩阵自动变为 site 局部轴表达。[公开接口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L566)、[site 包装](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L274)。

若要局部轴表达，应左乘 $R_{WS}^T$；若还换参考点，必须加刚体速度的叉乘项，不能只旋转矩阵。Jacobian 的转置将**同一参考点、同一轴系**的力/力矩映射到广义力：$\tau=J_p^TF+J_r^TT$。这是一条虚功关系，不是“任何期望末端力都能由当前驱动器实现”的保证。

源码沿 DOF 祖先链从末端向根遍历，取 cdof 的角速度部分，并通过 $\omega\times r$ 修正线速度。固定 body 先查 weldid；不影响末端的 DOF 列为零。这样可以解释为什么夹爪外物体的 free joint 列不应进入手臂末端 IK，为什么浮动基座列必须明确保留或排除。[mj_jac 的祖先遍历](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L189)。

本例 XY Jacobian 的解析形式为

$$J=\begin{bmatrix}
-L_1\sin q_1-L_2\sin(q_1+q_2)&-L_2\sin(q_1+q_2)\\
L_1\cos q_1+L_2\cos(q_1+q_2)&L_2\cos(q_1+q_2)
\end{bmatrix}.$$

在伸直或折叠时两列可能相关，矩阵降秩；靠增大反馈增益不能恢复缺失的局部运动方向。若附加末端 yaw 目标，本例只有两个 DOF，却提出三个独立任务分量，一般没有精确解。

## 4. MuJoCo 提供工具，不提供通用 IK 解算入口

原生核心提供 FK、Jacobian、配置差分/积分；完整 IK 的目标、约束、优化器与停止条件由应用决定。`mj_inverse` 是逆动力学，输入加速度并求力，不是求关节角。[原生坐标说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/simulation.rst#L1415)。

对位置任务定义 $e=p_d-p(q)$，在当前配置附近 $p(q\oplus\Delta)\approx p(q)+J\Delta$。一个有阻尼的局部最小二乘步为

$$\Delta=\arg\min_z\|\bar Jz-\bar e\|^2+\lambda^2\|z\|^2
=\bar J^T(\bar J\bar J^T+\lambda^2I)^{-1}\bar e.$$

这里本例只有转动 DOF，$\bar e=e/L_*$、$\bar J=J/L_*$，$L_*=0.5$ m 用于规范化任务量纲；代码用线性求解而非显式求逆。lambda>0 改善近奇异时的步长行为，但引入偏差，不能保证可达性或全局收敛。对混合平移/旋转关节还需定义关节尺度，不能直接套用本例同一 rad 步长上限。

局部 IK 的完整最小流程是：

1. 使用独立 scratch MjData，复制必要的配置/目标 frame 输入；不要在真实控制 data 上试探候选姿态。
2. 更新 kinematics 与 comPos，得到残差和正确 DOF 列的 Jacobian。
3. 解阻尼步，限制局部步长；用 `mj_integratePos` 沿切空间更新配置。
4. 处理适用的限位，重新算残差；不下降时回溯，仍无改进则报告未收敛。
5. 同时检查残差、最大迭代、无改进退出；返回 candidate、residual、converged，不能只返回一个数组暗示成功。

[源码阅读片段 position_ik.py](../examples/control-robotics/position_ik.py)实现这一有界过程：60 次上限、6 个回溯系数、0.1 rad 的步长上限。只求两个 hinge 的 XY 位置，采用本例标量 range 投影；没有碰撞检测、闭环 equality、动力学约束或运行收敛证据。这些限制写入函数说明，不能把该片段当通用机器人 IK 库。

### 姿态、冗余与约束如何改变问题

姿态任务可定义世界轴误差 $e_R=\log(R_dR^T)$，与世界轴 Jr 配对；若定义 body 误差 $\log(R^TR_d)$，则应匹配相应的局部 Jacobian。姿态误差是 3 维旋转向量而非四元数四维差。大角度下对数映射的导数不能无条件近似为单位矩阵；上面的局部小步方法需要重新线性化，π 附近有分支问题。

同时优化位置与姿态时，应明确长度尺度/权重，例如 $[e_p/L_*,e_R]$，不能将 1 m 与 1 rad 当相同误差。冗余机器人还需确定参考姿态、关节限位裕量或其他次目标；使用阻尼伪逆构造的“零空间”投影通常不再是精确投影，因此次任务可能扰动主任务。

闭环机构的 equality 残差可作为附加约束，碰撞距离/关节限位可作为不等式；这已经超出本例的 unconstrained DLS。运动学可行不代表动力学可行；“将 qpos clamp 到 range”也不保证闭环或非碰撞约束仍满足。完整约束与接触算法在 E3 继续追踪。

## 5. joint 限位、耦合与 mocap 各自解决什么

hinge/slide range 控制标量位置范围，ball range 的上界限制总旋转角而非逐轴欧拉角；free 不支持 joint range。本版本 joint actuatorfrcrange 只对标量关节生效。限制是否启用还看 limited/autolimits，而不是“XML 中出现 range”一句话。[range/limited](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L2394)、[编译检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L3193)。

动力学 joint limit 是由约束产生响应的软限制，不是每步硬剪切 qpos。本例 IK 的标量 range 投影只是优化候选点的几何操作，不复制物理求解器。控制目标应保留限位裕量，并记录饱和/不可达；不要把目标继续推向限位后“最终速度小了”当作跟踪成功。

两指夹爪的耦合可用 fixed tendon 的长度组合或 equality joint 描述，但语义不同：tendon 提供传动/长度关系，不凭空删除自由度；joint equality 通过约束求解追踪多项式关系。对于参考值 x0/y0，原生关系是

$$y-y_0=a_0+a_1(x-x_0)+a_2(x-x_0)^2+a_3(x-x_0)^3+a_4(x-x_0)^4.$$

符号与偏移应按夹爪轴/零位推导，不能机械复制另一个机器人的 mimic multiplier。URDF 导入后还须查实际原生约束和传动是否存在，不由 `<mimic>` 文本推定运行等价。[fixed tendon](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L5405)、[joint equality](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4961)。

mocap body 是外部指定 pose 的静态运动学输入；把动态末端通过 weld 连接到它，可以构造目标约束驱动，但仍受软约束参数与场景影响。它不是“发现了机器人真实关节电机命令”。直接把抓到的物体焊接到夹爪更会改变任务物理，不能作为真实接触抓取证据。[weld 语义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4872)、[mocap 机制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/modeling.rst#L1541)。

## 6. 从 IK 候选到可执行控制接口

IK 输出 qd 后，不应直接覆盖 live data.qpos。为 scalar gear=1 position/pid 写位置 setpoint；motor 模式先算关节控制力，再做 transmission 分配/限制。IK 的 joint range 与 actuator 的 setpoint range 也应分别核对；本例 shoulder 的 joint range 为 ±2.5 rad，PID 位置输入只允许 ±1.8 rad，因此几何上满足 joint range 的候选仍可能被执行器裁剪。带动态电机时应进一步考虑内环、activation 和电气响应。轨迹还需要速度/加速度限制，离散路点要插值或限速，避免位置目标瞬间跳变。

对一般机器人可将执行器分配写成 $B^Tp\approx\tau_d$：欠驱动时目标可能不在可达子空间，多 actuator 时解可能不唯一，饱和使问题变成带约束的分配。Jacobian 转置力控制与 DLS 位置 IK 也不同：前者计算广义力，后者计算配置增量。把 IK 的 Δ 直接写进 motor ctrl 在量纲上就错了。

外部 ROS/设备控制接入应保留一条明确的单写入链：收取带时间戳和单位的消息 → 按模型名称映射 → 验证维度、范围、时效 → 在指定控制 tick 更新目标 → 原生 actuator → 步进 → 复制观测及阶段信息。网络线程只发布目标快照，物理线程负责 data 的所有写入；是否插值、保持旧值、超时中止由任务契约决定，不在 MuJoCo 回调内阻塞等待消息。

要核对“控制器发出了正确命令”，至少区分期望目标、限速目标、实际 ctrl/act、actuator_force、qfrc_actuator 和测得状态。重复发布相同消息不应重置任务计时；reset 时外部目标、内部控制器状态和模型状态一起按约定恢复。硬件到仿真的零位、单位及齿轮参数也应记录为 adapter 信息，不能写成 MuJoCo 本身的默认行为。

## 7. 阅读练习与答案

**1.** 两个 hinge 的 actuator 顺序与 joint 顺序相反，是否还能直接 `data.ctrl[:] = q_target`？

答案：不能据数组等长判断。先按 actuator 名称、transmission 与 ctrl 输入含义映射；motor 输入更不是位置目标。

**2.** 模型还有被抓物体的 free joint，为什么机器人 site 的 Jacobian 仍有这些列？

答案：输出宽度是全模型 nv；无祖先关系的列为零。IK 应显式选择机器人 DOF，避免将全模型宽度误解为全都可控。

**3.** 只更新 kinematics 后调用 jacSite，为何可能错误？

答案：jacSite 经 mj_jac 读取 cdof 与 subtree_com；需要当前配置的 comPos。读取到更新后的 site_xpos 不证明所有 Jacobian 依赖已更新。

**4.** 双杆末端想向 x 方向收缩，但初值完全伸直，DLS 是否保证立即找到弯曲解？

答案：不保证。该初值局部 x 方向一阶导数可能为零；阻尼不创造缺失的导数。需要合适初值、其他搜索策略或明确未收敛输出，不能无限循环。

**5.** 只限制 qpos 的每个数到 [-π,π] 能处理 ball joint 限位吗？

答案：不能。ball 用四元数，原生限制是相对参考的总旋转角；逐分量裁剪会破坏姿态表示。应在旋转流形上定义约束。

**6.** equality 中 y0=0.1、x0=0.2，想要 y=−x，应设置 a0、a1 为多少？

答案：a1=−1，a0=−0.3，其他系数为零；代入得到 y−0.1=−0.3−(x−0.2)，即 y=−x。忽略 reference 会引入常量偏差。

**7.** IK 返回 residual 小于阈值后，哪些结论仍没有证明？

答案：没有证明无碰撞、速度/加速度/力矩可执行、闭环一致、接触稳定、控制跟踪和实机精度。这里仅满足该局部运动学任务的数值停止条件；本课脚本更没有执行验证这一条件。

继续阅读[任务接口](task-interfaces.md)，把“目标可定义”连接到有超时、失败原因和可信观测的状态机。[验证记录](validation/e2.md)注明本次交付范围。
