# E4：传感器的采样、延迟与 Context 所有权

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [相机与渲染](sensors-rendering.md) · [惯性与力传感](inertial-force-sensing.md)

本篇使用与相机篇相同的 Drake v1.57.0 固定源码；先修 [E1 事件与时间](state-time.md)。目标是能够回答“这份图像观察了哪个场景时刻，何时可供控制器使用”，而不是只知道调用 Eval。

## 1. 四个时间不是一个字段

对采样传感器至少区分：仿真当前时间 t、捕获场景时间 t_capture、输出可用时间 t_output、宿主实际完成工作的墙钟时间。控制器也有自己的采样事件。即使所有频率都是 30 Hz，若 offset 或事件类别不同，它们也不自动同步。

| 系统 | 计算/更新时间 | 读取结果 |
|---|---|---|
| `RgbdSensor` | 下游按需 Eval；图像反映输入 QueryObject 的当前场景 | 连续输出模型，未内置相机采样事件、延迟或曝光 |
| `RgbdSensorDiscrete` | 给各输出包周期 ZeroOrderHold，默认 1/30 s | 在采样事件之间保持；本版 image_time 导出存在源码差异，见下节 |
| `RgbdSensorAsync` | capture 与 output 两组周期 unrestricted update | 保持最近已交付图像，包含显式正延迟 |
| `MeshcatVisualizer` | 周期/强制 publish | 发给外部显示，不产生相机采样状态 |
| `Accelerometer/Gyroscope` | 直接根据输入计算 | 无原生采样、噪声或时延；输入自身可能已经采样 |

[连续传感器合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.h#L48-L51)、[连续 image_time 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.cc#L284-L291)、[离散包装](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.h#L17-L65)、[async 事件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L246-L270)。缓存可以避免对未失效的同一输出重复计算，但它不等于固定帧率。特别是 `CalcDepthImage16U` 内部直接重新调用 32F 渲染再转换；同时读取两个深度端口不能假定共用一次渲染。[转换调用链](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.cc#L244-L259)。

## 2. ZeroOrderHold 真正保持了什么

周期 T、offset δ≥0 时，更新时刻为 δ+kT；向量 ZOH 保存 discrete state，abstract ZOH 保存 abstract state，通过 unrestricted update 将输入复制进去。图像、RigidTransform 属于后者，时标 vector 属于前者。输出只读状态，不会因为你 Eval 而主动补采样。[状态和初值](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.h#L13-L46)、[两类事件实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.cc#L17-L36)、[复制输入](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.cc#L62-L78)。

图像 ZOH 的初值是给定 model image，通常是有尺寸的全零数组；向量默认零。尚未采过帧时的 `time=0` 不能证明已捕获 t=0 图像。只构建 Diagram/CreateDefaultContext 不会产生有效样本；要在后续获准运行时按事件历史区分初始化占位与真实样本。系统把图像存入状态后，相机上游的持续变化不会直接更新这份图像。

离散包装器内部同时创建 color、32F depth、16U depth、可选 label、body pose 和时间的 ZOH。即使下游没读某个端口，ZOH 更新仍会读取相连输入，因此仍可能渲染。只需要一种图像时，原生 `RgbdSensor` 加该输出的单独 ZOH 更直接。[实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.cc#L26-L80)、[官方提醒](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.h#L35-L41)。

**本固定提交的 image_time 导出差异：** header 宣称 `image_time_output_port()` 是长度 1 的向量；实现 L75–78 确实创建并连接了 zoh_image_time，但 L79–80 导出的是 `zoh_body_pose->get_output_port()`。据此，该名称实际连接 abstract RigidTransform 输出，不能照声明把它当作时间标量。这是固定 blob 的静态发现，未运行复现，也未宣称上游已修复。[声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.h#L103-L108)、[实际导出](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.cc#L68-L80)。

[原创示例](../examples/sampled_camera.py)采用原生连续 RgbdSensor，将 **depth32F、X_WB 和 image_time 分别连接同周期/offset 的 ZOH**；显式导出正确的时标 ZOH。没有实现跨引擎包装类，也没有修改上游。示例使用锚定球体与世界固定相机，只用于读懂连接图；未构造或执行。真实移动相机还需保存 X_BD，保证后续重投影用的是捕获时的 X_WD，而不是控制器读取时的当前 pose。

## 3. Async 延迟不是墙钟 deadline

设频率 f、捕获偏移 δ、延迟 d：

$$
t_{capture,k}=\delta+k/f,\qquad t_{output,k}=t_{capture,k}+d,\qquad 0<d<1/f.
$$

初次输出前 image 为零尺寸，内部时间为 NaN；到 output 事件才交付对应 capture 的图像。例：f=20 Hz，δ=0.01 s，d=0.02 s，在 0.01/0.06/0.11 s 捕获，0.03/0.08/0.13 s 交付。在 t=0.07 s 读取的仍是 0.01 s 场景；图像年龄是 0.06 s，不是固定 d=0.02 s。[时间合同及构造条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.h#L61-L95)、[参数约束](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.h#L119-L151)、[初始结果](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L150-L164)。

实现有两组同频不同 offset 的更新：capture 启动 Worker，output 调 `Finish()`；后者实际 `future.wait()` 后 `future.get()`。所以 d 允许仿真时间在渲染期间推进，但不是“超过 d 墙钟秒就丢帧”的策略。若渲染没完成，交付事件会等待，仿真墙钟速度下降；不能凭使用 Async 宣称实时或吞吐提升。[事件声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L246-L270)、[交付](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L482-L502)、[worker 结果与 wait](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L644-L683)。

固定版还有三个明确边界：

- 主要为 out-of-process glTF renderer 设计；官方警告 VTK/GL 在这里可能线程不安全或表现不佳，不能把普通 VTK 相机替换成 Async 就宣称加速。[限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.h#L37-L46)。
- Worker 捕获的是 frame poses，不能据此认为支持 deformable configuration。形状/纹理等 perception version 改变会报错，需要重新 Initialize 建立 worker 的场景。[实际检查与捕获](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc#L600-L634)。
- 构造保留 SceneGraph 指针，SceneGraph 生命周期必须覆盖 sensor；时序参数和是否存在某类相机不能运行中任意修改，因为决定事件与端口结构。[生命周期/配置](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.h#L100-L151)。

## 4. 事件同刻不等于数据同龄

Systems 的 publish 与 update 有各自语义，不能只比较时间数字就假定“先更新再发布”。`ApplyCameraConfig` 甚至为 async LCM 发布把 offset 设为 `capture_offset+1.001*output_delay`，实现注释说明是在规避同刻 update/publish 的顺序问题。课程保留该实际行为，不把 0.1% 因子解释成传感器物理延迟。[配置实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_config_functions.cc#L268-L282)。

此外该 helper 在 `output_delay==0` 时加入连续 RgbdSensor，非零时才加入 Async；`fps` 用于发布并不自动令你直接 Eval 连续 camera 的输出变成保持值。LCM 被禁用时 helper 仍可添加相机，但不添加有效传输路径。[分支和 LCM](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_config_functions.cc#L233-L265)、[连续 camera 接线](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/sim_rgbd_sensor.cc#L43-L75)。

将来记录一帧至少需要：传感器与 renderer 配置身份、frame 约定、t_capture、t_available、实际消费时间、是否初始占位、图像 copy；移动相机还要捕获时外参。对接外部消息时核对消息时间戳究竟来自采样还是发布，不能把本地 `Context.get_time()` 直接重命名为所有模态的 capture_time。

## 5. QueryObject、参数与快照

从 SceneGraph 输出 Eval 得到的是与特定 Context 关联的 live QueryObject。应短作用域使用，每次计算重新 Eval；将对象复制会产生冻结场景的 baked 查询，代价较高，后续原 Context 变化不再更新它。它不是轻量的永久“scene handle”。[live/baked 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h#L29-L60)。

`RgbdSensor` 默认配置保存在 System，对已有 Context 的修改用 `SetX_PB(sensor_context,...)`、`SetColorRenderCamera` 等；改 `set_default_*` 不应当作修改已经存在的 Context。内部 setter 会 ValidateContext 并写 abstract parameter，输出计算随参数失效重算。[参数访问](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.cc#L99-L168)、[默认参数复制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.cc#L294-L298)。

SceneGraph 的模型添加 renderer/role 与 Context 重载也各有范围。应在创建 root Context 前完成基础场景；修改特定 root 的 scene_graph 子 Context 要明确只影响那个实例。Python AddRenderer 绑定引用复制重载；它不要求调用者长期持有最初 renderer 对象，也不能据此认为 GPU/窗口/线程资源可以任意跨 Context 共享使用。[C++ 所有权](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/scene_graph.h#L713-L740)、[Python 重载](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_scene_graph.cc#L351-L359)。

重置需要同时考虑 plant 状态、图像 ZOH 状态、Async worker、输出有效性和外部显示。只 SetPositions 或 SetTime 不会替你清空这些系统或重新安排历史；使用完整 Diagram 的 Context/事件合同处理。尤其不能把复制 Context 宣称为克隆正在运行的线程、网络服务或 Simulator 积分历史，参见 [E1 clone 边界](state-time.md)。

## 6. 阅读练习与答案

1. **ZOH 输出仍是旧图像，多 Eval 几次能更新吗？** 答：不能，输出取保持状态，需要采样更新事件；Eval 连续 RgbdSensor 是另一种语义。
2. **本版离散 sensor 的 image_time 可直接 `Eval(...)[0]` 吗？** 答：不能依赖声明；导出代码连了 body-pose ZOH。应明确暴露正确的时间 ZOH 或采用经核验的另一条路径，且记录版本差异。
3. **20 Hz、δ=0.01、d=0.02，在 0.07 s 消费哪帧？** 答：上次可用帧 0.03 s 交付，捕获于 0.01 s；下一帧 0.08 s 才交付。
4. **Async d=20 ms 是否保证 20 ms 墙钟内得到图像？** 答：不保证，output 事件可能等待 future；d 属于仿真时间模型。
5. **保持了图像却直接接当前 X_WB 到点云转换器，有什么后果？** 答：移动相机的旧图像会用新位姿变换，造成几何错位；应保持捕获时位姿且乘 X_BD。
6. **把连续 camera 的 fps 配置改大是否改变碰撞精度？** 答：不是。相机/发布/控制/plant 各有时间事件；更频繁渲染也不证明更准确的物理或成像。
7. **修改默认相机内参后已有 Context 图像没变，原因是什么？** 答：System 默认值与 Context 参数不同；对正确的 sensor 子 Context 用对应 Set API，注意输出尺寸改变与旧 NumPy 视图失效。

本篇没有运行事件、相机、渲染线程或网络传输。静态示例与字段检查见 [E4 证据](evidence/e4-validation.md)。
