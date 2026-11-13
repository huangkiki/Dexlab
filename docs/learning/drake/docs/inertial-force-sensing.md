# E4：惯性、编码器与力观测

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [相机与渲染](sensors-rendering.md) · [采样与延迟](sensor-timing.md) · [E3 力观测](contact-observation.md)

本篇完成 A6 中理想惯性传感器、编码器及力/触觉观测的边界。仍固定 Drake v1.57.0 源码；不执行 native 模型、动力学或传感器回调。先理解 [E1 空间向量](modeling-state-time.md)和 [E3 sampled/live 输出](contact-observation.md)。

## 1. 原生系统与端口合同

| 对象 | 输入 | 输出与单位 | 内置模型 |
|---|---|---|---|
| `Accelerometer` | body poses、spatial velocities、spatial accelerations | 长度 3，S 中比力，m/s² | 刚体上指定位置、方向、给定恒定重力；无噪声/偏置 |
| `Gyroscope` | body poses、spatial velocities | 长度 3，S 中相对世界的角速度，rad/s | 固定安装方向；平移不影响角速度；无噪声/偏置 |
| `RotaryEncoders` | 选定输入位置分量，假设为 rad | 各编码器角度，rad | 标定 offset 和可选量化，不自动采样 |
| `plant.get_reaction_forces_output_port()` | plant Context 与动力学输入 | JointIndex 顺序的 SpatialForce | 关节 child 侧、Jc 原点、Jc 表达的反力 |
| `plant.get_contact_results_output_port()` | plant 的接触/动力学输出 | point/hydro 的力和接触几何 | 求解器读回，不是带阵列、带宽、噪声的触觉硬件 |

[Accelerometer 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.h#L17-L63)、[Gyroscope 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/gyroscope.h#L17-L37)、[编码器](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rotary_encoders.h#L14-L51)、[关节反力](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1280-L1305)。IMU 的 body 索引来自传入 RigidBody，输入数组来自同一个 plant 的 BodyIndex 顺序；不能把多个 plant 的同名 body、ModelInstanceIndex 或 GeometryId 混接。

## 2. Accelerometer：为什么静止时不应为零

设传感器 S 刚性固定在 body B，安装位姿 X_BS，世界 W 为惯性参考。R_SW 将世界向量转到 S，`r_W=R_WB p_BS_B` 是 Bo→So。理想刚体下：

$$
a_{WSo}=a_{WBo}+\alpha_{WB}\times r_W
 +\omega_{WB}\times(\omega_{WB}\times r_W),
\qquad f_S=R_{SW}(a_{WSo}-g_W).
$$

假设 S 相对 B 固定，所以没有相对运动导致的 Coriolis 项；所有叉乘分量均以 W 表达。a 与 g 单位 m/s²，ω 为 rad/s，α 为 rad/s²，r 为 m。`SpatialAcceleration` 上半部是角加速度、下半部是线加速度，不能把六维数组直接当 accelerometer 输出。

实现先按 BodyIndex 取 X_WB、V_WB、A_WB，计算 r_W，然后 `A_WB.Shift(r_W,V_WB.rotational())`，最后 `R_SW*(A_WS.translational()-gravity_vector)`；Shift 实现明确包含 α×r 与 ω×(ω×r)。[测量实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.cc#L42-L70)、[空间加速度平移](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_acceleration.h#L115-L159)。

设 S 与 W 对齐、g_W=(0,0,−9.81)：静止支撑时 a=0，输出 (0,0,+9.81)；理想无旋转自由落体 a=g，输出零。若绕 z 轴以 ω=2 rad/s 匀速旋转、S 在 x=0.1 m，向心项为 (−0.4,0,0) m/s²。把传感器放在不同位置会改变 accelerometer，但不会改变同一刚体上的理想 gyro 角速度。

**默认重力是零向量。** 构造 `Accelerometer(body,X_BS)` 不会自己向 plant 查询 g；要模拟 proper acceleration 必须显式传入与 plant 一致的世界重力。若漏传，静止时读零、自由落体时读 g，含义变成坐标加速度而非期望的比力。[构造默认值](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.h#L56-L63)。C++ 的 `AddToDiagram(body,X_BS,g_W,plant,builder)` 会添加系统并连接三组 body 输出，但仍由调用者提供 g_W。[接线实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.cc#L73-L87)。

固定版 Python 绑定尚未导出两个 IMU 类的 `AddToDiagram`，不能把 C++ helper 原样抄到 Python。下面是完整、未执行的原生接线函数；plant 已 Finalize，body 必须来自该 plant，X_BS 与 g_W 的单位和坐标如上。它只返回两个系统供下游读取，采样需另行设计。[Accelerometer 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_accelerometer.cc#L25-L46)、[Gyroscope 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_gyroscope.cc#L25-L38)。

```python
from pydrake.systems.sensors import Accelerometer, Gyroscope


def connect_ideal_imu(builder, plant, body, X_BS, g_W):
    accelerometer = builder.AddSystem(Accelerometer(body, X_BS, g_W))
    gyroscope = builder.AddSystem(Gyroscope(body, X_BS))
    builder.Connect(
        plant.get_body_poses_output_port(),
        accelerometer.get_body_poses_input_port(),
    )
    builder.Connect(
        plant.get_body_spatial_velocities_output_port(),
        accelerometer.get_body_velocities_input_port(),
    )
    builder.Connect(
        plant.get_body_spatial_accelerations_output_port(),
        accelerometer.get_body_accelerations_input_port(),
    )
    builder.Connect(
        plant.get_body_poses_output_port(), gyroscope.get_body_poses_input_port()
    )
    builder.Connect(
        plant.get_body_spatial_velocities_output_port(),
        gyroscope.get_body_velocities_input_port(),
    )
    return accelerometer, gyroscope
```

## 3. 离散 plant 下“理想公式”也要查输入年龄

plant 的 body poses、velocities 始终是当前状态的 kinematic 输出；body accelerations 是 dynamic 输出，默认 sampled 模式保持上一步计算所得加速度。Accelerometer 并不携带自己的统一采样历史，它会直接使用当前接进来的三组数值。因此步后 Eval 可能把新 pose/ω 与保存的旧 dynamics A 组合起来；不能仅凭测量端口名给它贴“同一时刻真实 IMU”标签。[plant 输出类别与时序](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L420-L447)、[加速度输出读缓存](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L4387-L4400)。

在尚未步进时 sampled acceleration 全零，经过减重力后 accelerometer 仍可能出现非零输出；这不是已经求出静态平衡的证据。`SetUseSampledOutputPorts(False)` 可让 plant 以当前输入重算动态输出，代价与离散求解语义见 E3；它也不会自动建立真实 IMU 的采样/带宽/噪声模型。[初始全零合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1023-L1046)。

正确的分析顺序是先标记 plant 输出是 continuous、sampled discrete 还是 live discrete，再决定传感器如何采样和保持。若要求整组运动学/动力学量同龄，需要在明确定义的事件边界保存它们或采用与目标含义一致的 live 计算；仅给 accelerometer 外面再套 ZOH，会保持已经计算出的值，却无法修复上游混龄。与相机合并日志时还需分别保存 capture/available/consume 时间，不以统一日志行替代时间对齐。

## 4. Gyroscope 与 RotaryEncoders

Gyroscope 实现为 `ω_S=R_BSᵀ R_WBᵀ ω_WB_W`，输出相对世界的角速度在 S 中的分量。它不是 RollPitchYaw 导数，也不是 quaternion 导数；只有特定姿态和约定下才能把某个分量等同欧拉角速度。平移 X_BS 不进入该公式。[实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/gyroscope.cc#L33-L62)。

两个惯性传感器都只声明输入和 measurement 输出，无周期状态更新；噪声、偏置随机游走、饱和、低通带宽、交轴误差和采样应由明确模型另行构造。它们也不是自动输出姿态估计的融合 IMU。源码的理想输出不得写成实机精度、稳定性或 sim-to-real 验证。[Accelerometer 端口构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.cc#L20-L38)、[Gyroscope 端口构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/gyroscope.cc#L17-L30)。

编码器先做 `q̃_i=input[index_i]−offset_i`；若给出正的每圈 ticks 数 N，则实现：

$$
y_i=\frac{2\pi}{N}\left\lfloor\frac{N\tilde q_i}{2\pi}\right\rfloor.
$$

输出仍是 rad，不是整数 ticks；使用 floor 而非四舍五入，没有自动取模到 [0,2π)。负的小角度可落到一个负 tick，例如 N=4、q̃=−0.1 rad 输出 −π/2。`set_calibration_offsets(context,...)` 写该 encoder 的参数，输入索引应按实际 q 布局选择，尤其不要把浮动体 quaternion 分量当旋转编码器角度。[计算与参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rotary_encoders.cc#L71-L105)。要省去量化用 selector-only 构造；不要传 N=0 模拟“无量化”，公式分母为零。采样仍另接 ZOH。

## 5. 力传感：先选截面和受力侧

关节 reaction 输出在 child 侧 Jc 原点，以 Jc 表达，顺序是 `[τx,τy,τz,fx,fy,fz]`，单位分别 N·m、N。它回答“在该机械连接截面上，为达到系统运动所需的反力”，不是只包含手指接触物体的那一部分。重力、惯性、驱动和其他外力可共同影响该结果；不能把它直接命名为 fingertip contact force。[反力定义](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1280-L1300)。

源码调用链是 `CalcReactionForcesOutput<sampled>`：sampled 时复制 `DiscreteStepMemory.reaction_forces`，无历史则全零；live 时调用 `CalcReactionForces`，结合外加力与对应加速度进行反力计算。它不是测量噪声或硬件标定过程。[sampled/live 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc#L4466-L4503)。

假设要把在 Jc 原点、Jc 表达的 wrench 改到传感器 So、S 表达：

$$
f_S=R_{S Jc}f_{Jc},\qquad
\tau_S=R_{S Jc}\left(\tau_{Jc}+p_{So,Jco}^{Jc}\times f_{Jc}\right).
$$

这里 `p_{So,Jco}` **从新的力矩参考点 So 指向旧点 Jco**。若使用 Drake `SpatialForce.Shift(p_JcoSo)`，参数反过来是旧点指向新点，方法内部会减该向量叉乘 f；旋转和平移缺一不可。翻换 child/parent 受力侧还需先在同一点同一表达坐标中做作用反作用，不是随便取各分量绝对值。[E3 完整符号与例子](contact-observation.md)、[Shift 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_force.h#L72-L101)。

固定 tree 只有 `lcmt_force_torque` 消息定义并不能证明存在完整六轴硬件传感器系统。本课从上述原生反力和 E3 ContactResults 说明可观察量；没有伪造 `ForceTorqueSensor` API。若以 weld 作为传感器截面，必须先确认最终拓扑保留该 joint 并能提供相应反力，不能忽略 fused/unmodeled joint 的限制。[相关反力限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1273-L1282)。

## 6. 接触压力不等于触觉图像

PointPairContactInfo 提供离散接触点合力，HydroelasticContactInfo 提供接触面和合力矩；它们没有自动给出 taxel 排布、传感层厚度、局部响应核、剪切饱和、带宽或相机式触觉成像。E3 中 hydro pressure field 是接触几何/材料模型的一部分，不能简单把压力场截图称为真实触觉相机。

对一个已经定义的传感面区域 A_i，理想法向 taxel 力可形式化为 `F_i=∫_(A_i∩contact) p(x)n(x)·n_i dA`，单位 N；面积平均压力才是 `F_i/area(A_i)`，单位 Pa。这只是说明**还需指定**传感面、坐标、正方向、积分方式与传递模型，不是本仓已实现的传感器。求解器的离散等效平均接触力也不提供任意亚步瞬时峰值。[原生 contact 读回与边界](contact-observation.md)。

## 7. 阅读练习与答案

1. **传感器静置、与世界同向、g_z=−9.81，为什么读 +9.81？** 答：测的是比力 a−g，支撑下 a=0。若读零先查是否遗漏 gravity_vector。
2. **偏置 0.1 m、ω_z=2、无角加速度，额外的 x 加速度是多少？** 答：ω×(ω×r)=−0.4 m/s²；它不能通过纯旋转 body 原点加速度得到。
3. **四元数位置导数的后三维能当 gyro 吗？** 答：不能，gyro 是空间角速度经坐标旋转；qdot 与 v 的映射已在 E1/E2 区分。
4. **初次 Eval 加速度非零，能证明已经计算接触支撑力吗？** 答：不能，sampled A 可以尚为零，减 g 本身就非零；需知道是否已有动态采样历史。
5. **给 accelerometer 加 ZOH 是否解决 mixed-age 输入？** 答：不会，只保持现有组合输出。要处理 plant 各输入的采样合同。
6. **N=4、校准后角度 −0.1 rad，编码器输出是什么？** 答：−π/2 rad，floor 有方向性；不是 0，也不是整数 −1 tick。
7. **把关节 reaction 的力除面积就得到触觉图了吗？** 答：不行，reaction 是机械截面合力，不给局部分布；还缺接触面映射、面积、方向与传感器响应。

本篇解析数值只做标准库代数核对，未运行 Drake 测量、动力学或传感器。完整静态验收见 [E4 证据](evidence/e4-validation.md)。
