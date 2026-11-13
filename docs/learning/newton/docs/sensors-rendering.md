# E4：传感器、渲染与可视化

本章完成 A6 的原生接口与源码专题。先修 [E1：模型、状态与时间](modeling-state-time.md)；涉及力时衔接 [E3：接触与力观测](contact-solvers-forces.md)。从“这个数组表示什么、什么时候更新”出发，贯通相对位姿、IMU、接触观测、几何射线、相机图像与显示后端。

阅读版本为 Newton **1.6.1**，官方固定提交 `713fecdc41caf0c9d726f5c016939f36e66e3dff`。这里没有导入原生引擎、打开窗口、执行渲染或仿真。示例仅 AST 验证；源码支持不代表本机驱动、窗口系统或可选宿主包已经验收。返回 [Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas)。

## 1. 观测、查询和显示分别做什么

`newton.sensors` 的公开出口实际列出 **4 类**：SensorContact、SensorFrameTransform、SensorIMU、SensorTiledCamera。概念页概述有 “five” 字样，但列举和固定导出均为四类；不据这一文字计数补造第五种传感器。[公开导出](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/sensors.py#L5-L29)、[概念页列举](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/sensors.rst#L107-L118)。

| 入口 | 读取/计算 | 输出与边界 |
|---|---|---|
| `SensorFrameTransform.update(state)` | body pose 与 shape/site 局部变换 | 相对位姿；不解动力学 |
| `SensorIMU.update(state)` | body_q、body_qd、body_qdd 与 world gravity | site 坐标中的 specific force 和角速度；依赖加速度 producer |
| `SensorContact.update(state, contacts)` | solver 已写入的 contact force 与几何 | 线性力、摩擦分解/矩阵；不自动计算接触求解 |
| `SensorTiledCamera.update(...)` | 当前几何 BVH、相机射线、材质/光照 | 调用者传入的图像缓冲；不必创建 viewer |
| `newton.intersect_ray(...)` | model 上已 refit 的 shape BVH | 最近命中距离/shape ID/world normal；不是含噪声的完整 LiDAR |
| `newton.viewer.*` | model/state 或已经生成的图像 | 交互显示、外部记录或文件；不统一等同于相机传感器 |

一个字段需要经过 **申请存储 → producer 填充 → sensor 计算 → consumer 读取**。IMU 构造默认请求 `body_qdd`，Contact 构造请求 `Contacts.force`；应先创建 sensor，再分配 State/Contacts。已有对象不会因 Model 后来新增请求就自动长出数组。Camera 则把结果写入 update 的输出参数；不能照搬 `sensor.depth` 的访问方式。[生命周期概述](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/sensors.rst#L12-L27)、[IMU 请求与分配](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L155-L164)、[相机输出参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L176-L229)。

所谓“传感器帧率”首先是调用调度。物理推进、派生量计算、图像生成、窗口刷新和保存可以有不同频率；API 名称中有 sensor，并不意味着它自己按真实时间采样。

## 2. Site、选择顺序与相对位姿

Site 是带 `ShapeFlags.SITE` 的 shape 索引，保存 body-local 变换，可以附在 body 上，也可用 body=-1 定义 world 固定参考。它不是 body ID；默认 `visible=False`。一个可显示的 site 也不因此成为碰撞实体。[add_site](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L8191-L8227)、[ShapeFlags](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/flags.py#L27-L44)。

字符串选择器用 glob；正则必须预编译，按 fullmatch；多个 glob 返回按模型标签顺序扫描得到的并集。整数列表按传入顺序返回，不能假定它自动去重或按编号排序。把两组 glob 各自展开后“长度一样”不证明语义配对正确；多 world 时保留显式 ID、label、world 映射。[match_labels 实现](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/selection.py#L425-L472)。

`SensorFrameTransform(model, shapes=..., reference_sites=...)` 接受普通 shape 或 site 作为目标，但 reference 必须是 site。单个 reference 广播给所有目标，否则必须与目标数 1:1；不是所有目标×所有 reference 的笛卡尔积，也不按同名后缀自动配对。[选择、验证和广播](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_frame_transform.py#L149-L211)。

令 $T_{WB}$ 把 body 坐标映到 world，$T_{BS}$ 为 shape 局部变换，则附体目标 $T_{WS}=T_{WB}T_{BS}$；静态目标直接用保存的 world transform。参考 site 为 R 时：

$$T_{RS}=T_{WR}^{-1}T_{WS}.$$

它把目标局部向量变到参考坐标，也表达目标在参考中的位姿。平移单位 m，quaternion 无量纲；Newton/Warp transform 的展开顺序是位置 xyz 加四元数 xyzw。输出是 Warp `(N,)` transform，转 NumPy 后通常为 `(N,7)`，不是 N 个 4×4 矩阵。[世界变换与相对变换 kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_frame_transform.py#L16-L78)、[输出契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_frame_transform.py#L81-L119)。

update 只读 `state.body_q`。直接写 `joint_q` 后若尚未 FK，读到的是旧 body pose；sensor 不替你补 FK。结果数组在下一次 update 被复用，跨时刻保存要复制；本 API 没有自动生成 timestamp 或有效性标记。[update 的输入与输出](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_frame_transform.py#L221-L245)。

## 3. IMU：加速度不是简单的速度差

### 原生量与点约定

`SensorIMU(model, sites=..., request_state_attributes=True)` 的 `accelerometer` 和 `gyroscope` 均为 `(N,)` 的 vec3，NumPy 展开 `(N,3)`。单位分别 m/s² 和 rad/s，输出在各自 **site 坐标系**。没有把结果定义为度/s、world 加速度或有重力的运动学加速度。[IMU 含义](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L72-L83)、[形状、单位与构造参数](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L113-L140)。

在固定刚体、无柔性安装、各输入来自一致时刻的假设下，设 C 是质心、S 是 site，$r^W=R_{WB}(p^B_S-p^B_C)$，则

$$f^S=R_{WS}^{T}\left[a_C^W-g^W+\alpha^W\times r^W
+\omega^W\times(\omega^W\times r^W)\right],\qquad
\omega^S=R_{WS}^{T}\omega^W.$$

这是源码的重力扣除、切向加速度和向心加速度三部分；`body_qdd` 的前三维是 world COM 加速度、后三维是 world 角加速度，`body_qd` 的角速度在后三维。site 偏离 COM 时只做坐标旋转会漏掉两项。静态 site 分支直接返回 $R_{WS}^{T}(-g)$ 与零角速度。[State 空间量](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L125-L146)、[完整 IMU kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L16-L69)。

纸面检查：传感器轴与 world 一致、$g=(0,0,-9.81)$ m/s²，静止且支撑时应为 $(0,0,9.81)$；理想自由落体且无旋转时为零。这是公式的自洽检查，**没有运行落体或静止实验**。只输出一个接近 9.81 的数不能证明上游加速度已更新。

### 谁产生 body_qdd，何时有效

IMU 的 update 只检查 `body_qdd is not None`，没有检查 solver 支持、更新时间或初始化后是否有过有效动力学计算。因此分配得到零数组、`eval_fk` 成功、或换用 XPBD，都不能单独证明 IMU 加速度有物理意义。它也没有自行用相邻速度做有限差分。[update 防护与实际输入](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L180-L206)。

本章具体沿 **MuJoCo-Warp** 路径核对 producer：Newton step 对请求的扩展字段开启 RNE postconstraint，禁用 sensors 与请求 body_qdd/body_parent_f 不兼容时抛错；转换 kernel 从 backend 的 cacc/cvel 换到 Newton COM 线性加速度并加回 world gravity，随后 IMU 按上式扣 gravity。不能看到两处 gravity 就凭直觉删除一处。[RNE 申请和禁用防护](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4441-L4462)、[COM 加速度转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L2958-L3010)。

采样阶段仍须记录：adapter 在后端 step 后先把新 joint 状态经 FK 写入 State，再从 backend 中现存的 cacc/cvel 写入 body_qdd。E3 已核对的固定 MuJoCo-Warp `step` 先 forward 再积分；这里没有额外的步后 forward 让所有派生量在最终 pose 重新求值。因此不能把 `imu.update(state_out)` 自动标为“所有输入均在 $t_{n+1}$ 精确重算”。Euler 与 RK4 的内部计算阶段不同；课程记录 producer/stage，不虚构统一的端点时间戳。[adapter 步进顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4157-L4178)、[FK 后的扩展字段转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L5269-L5290)。外部依赖沿用 [E3 锁定清单](e3-dependency-sources.json)及[积分说明](contact-solvers-forces.md)。

CPU MuJoCo 分支没有走同一申请路径，源码还保留 `TODO: handle use_mujoco_cpu`；本章只把上述 Warp producer 作为已追踪路径，不把类名相同当作 CPU 加速度读回已验收。其他 solver 也要查真实 writer。标准 SensorIMU 没有 bias、噪声、饱和、带宽、时延或随机游走参数；现实 IMU 模型需另定义，不能由“传感器”名称推定。[原生构造范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py#L119-L164)。

## 4. Contact sensor：观测消费不是新的接触求解

E3 已追踪 `Contacts.force` 的 producer/side/COM 和缺口。此处强调传感器职责：先请求 force，再在同一接触 generation 上完成 solver step、`solver.update_contacts(...)`，然后 `sensor.update(state, contacts)`。不要在读回前重新碰撞、排序或 clear。Kamino 的 producer 还需匹配的 State；VBD 的独立 body1 力读回不能直接当通用 buffer。[构造请求](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L321-L329)、[update 入口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L684-L725)。

| 输出 | 轴与单位 | 需要保留的语义 |
|---|---|---|
| `total_force` / `total_force_friction` | `(n_sensing,)` vec3，world，N | 总接触力/其切向分量；measure_total=False 时为 None |
| `force_matrix` / `force_matrix_friction` | `(n_sensing,max_counterparts)` vec3，world，N | optional；不同 world 的 counterpart 列按各自映射解释，空列补零 |
| `sensing_transforms` | `(n_sensing,)` transform，world，m/单位四元数 | sensing body/shape 的位姿；不是接触作用点 |
| `position_matrix` | sensing × counterpart × vec3，world，m | 按力模长加权的接触中点；不是六轴 wrench 的通用作用点 |

输出把各 world 的 sensing objects 平铺为行，不提供固定的 world×sensor reshape 保证；对应关系应读 `sensing_indices` 与逐行 `counterpart_indices`。全局 counterpart（如地面）可以映到每个 world 的列，局部 counterpart 按 world 解释。具体属性名、分配与布局以[多 world 布局](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L298-L315)、[SensorContact 属性](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L363-L405)和[分配与索引](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L639-L669)为准。sensor 只取 spatial force 的线性部分：body0 加、body1 减；normal 用来分解切向力。它没有输出完整六轴 F/T，也没有压力贴图或光学触觉图像。无有效力时 position 不应解读成真实接触位置。state=None 时仍更新 force、position 清零，而 sensing_transforms 留旧值；没有一个统一 valid flag 替你区分这些字段的更新时间。[可选 State 与清零分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L684-L738)。[聚合与位置权重](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L90-L155)。

XPBD weighting 的近似、恢复 pass 没进入读回，以及固定 MuJoCo adapter 的 torque 换点缺口，仍见 [E3](contact-solvers-forces.md)。更换消费类不会补全 producer 丢掉的信息。接触线画得正确也不证明力单位、方向或采样阶段正确。

## 5. 几何射线：使用哪个 BVH 就查询哪个世界

`newton.intersect_ray` 接收 world origins、归一化且非零的 world directions、每条 ray 的 world ID。输入为长度 R 的 vec3 数组和 int32 world 数组；可选输出距离 `(R,)` m、shape ID `(R,)` int32、normal `(R,)` vec3 world。未命中：距离 -1、ID -1、法线零。[公开几何出口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/__init__.py#L51-L73)、[原生契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/raycast.py#L916-L955)、[命中与 miss 写入](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/raycast.py#L988-L1045)。

对单位方向 $d^W$，命中点 $p^W=o^W+\rho d^W$；若方向未归一化，返回的 ray 参数就不能直接当米。它查询该 ray 所属 world，默认还查询 global world=-1；可通过 `enable_global_world=False` 关闭附加 global 查询。多 world 隔离是数据中的 group root，不是靠把场景摆远。不要把 viewer 为便于观察加的 world spacing 写回物理坐标。[group root 与世界查询](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/raycast.py#L995-L1025)。

该入口没有 `state` 参数，也没有独立 `max_distance` 参数。它读取 **Model 上缓存的 BVH 和 world transforms**；几何变动后先 `model.bvh_refit_shapes(state)`，结构/纳入集合改变则 rebuild。需要量程时在读回后按距离筛选，不能把相机的 `RenderConfig.max_distance` 当成此函数参数。[build/rebuild](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1624-L1645)、[refit](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1716-L1743)。

默认 shape BVH 按 `ShapeFlags.VISIBLE` 构建，不是默认按 COLLIDE_SHAPES。自定义 mask 的纳入条件是按位相交“任一命中”，还需形状类型被 BVH 支持。相机和此查询共用 model.bvh_shapes；重建为碰撞 shape mask 会同时改变其后相机使用的集合，不能无条件声称 Camera 永远独立过滤 VISIBLE。只 refit 不会重新选出刚变为可见的新 shape。[mask 与 enabled 集合](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1624-L1697)、[实际 enabled kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/bvh.py#L177-L192)。

`intersect_ray` 只遍历形状；相机另有 particle、变形三角面和 Gaussian 路线，两者不保证同一 hit 集合。射线查询也不自动提供扫描时序、回波强度、多回波、运动畸变或传感器噪声；这些不是此次几何 API 已实现的能力。

## 6. Tiled camera：从标定到七个通道

### 相机轴与射线

Camera transform 是 **camera→world**，不是 world→camera 外参。默认 pinhole 轴为 +X 向右、+Y 向上、-Z 向前；图像 py 向下，像素中心使用 `+0.5`。对垂直视场角 $\phi$、宽 W、高 H，令

$$u=(p_x+0.5)/W-1/2,\quad v=(p_y+0.5)/H-1/2,$$
$$d^C=\operatorname{normalize}\left(2u\tan(\phi/2)W/H,-2v\tan(\phi/2),-1\right).$$

$p_x,p_y$ 为像素索引、$\phi$ 单位 rad；视场角不以 degrees 传入。辅助函数也可收 focal length/aperture/offset，三者使用一致长度单位即可，因为方向只涉及比值。[pinhole kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/camera_utils.py#L400-L440)、[公开 ray helper](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L415-L470)。

OpenCV 标定 helper 会反解畸变，把 y-down/z-forward 方向转成上述 camera 轴；它不替你把任意外参矩阵改成 camera→world。无畸变且标定和渲染分辨率相同，方向对应 normalize(((px+0.5-cx)/fx), -(py+0.5-cy)/fy, -1)。有畸变时先反求 normalized coordinate；固定实现有限次迭代并检查 forward residual，失败返回零射线。渲染 kernel 将零射线写成 miss；不能把它当合法的 (0,0,0) 方向继续几何反投影。[反解预算与阈值](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/camera_utils.py#L443-L447)、[验收、坐标变换与像素映射](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/camera_utils.py#L617-L667)、[零射线处理](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py#L166-L184)。

原生还提供 USD pinhole、OpenCV fisheye、F-theta、Kannala–Brandt K3 helpers；参数次序、像素/弧度单位和有效视场应逐项使用原生契约，不把各类畸变多项式系数直接互换。本章解释坐标/无效射线边界，未验收真实镜头标定精度。[OpenCV fisheye](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L795-L840)、[F-theta](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L879-L929)、[Kannala–Brandt](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L965-L1013)。

### 批量维度和输出字段

设 B=world_count，C=camera_count，H/W 为图像尺寸。**变换、射线和输出的前两轴不相同**：

| 数组 | Warp shape / element type | 含义 |
|---|---|---|
| camera_transforms | `(C,B)` transformf | 每个相机、每个 world 的 camera→world |
| camera_rays | `(C,H,W,2)` vec3f | 第 0 个是相机局部 origin，第 1 个是 direction；所有 world 共用这组内参射线 |
| color_image / albedo_image | `(B,C,H,W)` uint32 | packed RGBA；分别为着色/未着色颜色，默认显示 sRGB |
| hdr_color_image | `(B,C,H,W)` vec3f | 线性 HDR RGB，不是 uint8 屏幕图 |
| depth_image | `(B,C,H,W)` float32 | 沿 ray 的命中距离，m |
| forward_depth_image | 同上 | 投影到 camera -Z 的深度，m |
| normal_image | `(B,C,H,W)` vec3f | world normal；mesh 可使用插值顶点法线作 smooth shading |
| shape_index_image | `(B,C,H,W)` uint32 | Newton shape ID 或特殊集合 ID；不是任务语义类别 |

NumPy 转出 vec3 图像会多出末维 3；uint32 color 则仍是单个 packed 元素。`SensorTiledCamera.utils.create_*_image_output` 负责分配；`update` 的各通道传 None 可跳过写入。源码会核对 shape，但调用者仍应确保 dtype/device 正确。[通道说明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L45-L65)、[完整 update API](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L176-L229)、[shape 验证](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render_context.py#L253-L325)、[buffer helper](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L298-L413)。

原始 color 的 packed RGBA 要经 `to_rgba_from_color` 等原生 helper 变成 `(B*C,H,W,4)` uint8，不能把 uint32 自动当四个传感器通道。`flatten_*` 拼图会丢失直观的 B/C 分轴，需要保留 tile→world/camera 映射。[拼图与 RGBA 变换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L1149-L1222)。

### 两种深度不能互换

设单位 world ray 为 $d$、camera forward 单位向量为 $f$，则

$$z=\rho(d\cdot f),\qquad p^W=o^W+\rho d.$$

对标准中心 pinhole，这是沿 ray 的 range $\rho$ 与光轴深度 z。偏离光轴 60° 时，range=2 m 对应 forward depth=1 m，不能把两者塞进同一反投影公式。原生允许自定义非零 ray origin；这时字段实际仍按“ray 距离乘方向投影”计算，不额外加 origin 到 camera center 的偏移。鱼眼超出前半球可有有效 hit 但负 forward depth，**不能普遍用 forward_depth>=0 当有效掩码**。[两个深度的 writer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py#L226-L237)。

### Miss、分割与完全空场景

固定 `ClearData` 的默认 `clear_depth=0.0`、`clear_shape_index=0xFFFFFFFF`。类概述写“负 depth 表示 no hit”，但实际默认 writer 用配置值；应主动选择 `ClearData(clear_depth=-1.0)`，同时保存 shape ID/有效性掩码。只用 `depth>=0` 检测有效像素会误收默认清屏零值。[实际默认值](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/types.py#L115-L123)、[clear writer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py#L57-L84)、[miss 与 hit 分支](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py#L213-L237)。

`shape_index_image` 对普通 shape 返回模型全局索引，不会自动变成每 world 的局部 index；变形三角集合和粒子集合另有 `0xFFFFFFFD`、`0xFFFFFFFE` 特殊 ID，miss 为 `0xFFFFFFFF`。不要把所有非 miss ID 都拿去索引 `model.shape_label`，也不要用随机色可视化替代语义标签表。[特殊 ID](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/raytrace.py#L18-L32)、[粒子与变形三角命中](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/raytrace.py#L206-L274)。

还有完全空场景的边界：`RenderContext.render` 只在存在 shapes/particles/triangle mesh/gaussians 时进入整个 kernel 分支；否则不写输出。即使传了 ClearData，也不能承诺 update 必然清空旧帧。本章例子显式填充每个返回通道的 sentinel，使调用者定义的无效输出不依赖这一分支。该结论来自代码流，未通过运行复现。[几何存在条件](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render_context.py#L230-L267)、[唯一 render launch](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render_context.py#L327-L401)。

### 几何同步、材质与可微范围

finalize 为初始状态建 BVH。每次几何 pose 改变，先 `model.bvh_refit_shapes(state)`；粒子改变则还需 `bvh_refit_particles(state)`。Camera.update 内部 sync_transforms 更新变形三角数据，但不代替这两次 model BVH refit。相机自己移动、场景不变时则无需因为相机 pose 改变而重建形状树。[sync_transforms 范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L159-L174)、[update 调用](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L232-L252)、[particle refit](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py#L1783-L1815)。

RenderConfig 的 `enable_global_world`、max_distance、backface_culling、particle 与贴图/阴影开关改变观测模型。默认贴图/阴影关闭，albedo 与 shaded color 不相同；反射材质与纹理生成的亮度也不是物理压力或触觉信号。shape 色/基础纹理按 sRGB 输入、内部转线性，packed 输出可选 sRGB/linear，HDR 保留线性。[RenderConfig](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/types.py#L54-L112)、[颜色空间约定](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py#L61-L65)。

这些 ray 与 render kernel 使用禁用反传的路径，不能仅因输入是 Warp array 就宣称完整 differentiable renderer。[render kernel 声明](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py#L86-L87)。此处不讨论噪声/曝光积分/rolling shutter/真实镜头 PSF 的已实现模型；它们没有出现在上述原生参数和采样链中。

## 7. Viewer：显示后端及宿主边界

原生公共流程通常是 `set_model(model)`，随后对选定时刻调用 `begin_frame(t) → log_state(state) → end_frame()`，结束时 `close()`。`begin_frame` 保存显示时间；`log_state` 更新显示对象，并不会推进 solver。viewer 的 world offsets/layer transform 是显示布局，不能当作传感器外参。[frame 与 state 显示](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer.py#L1042-L1082)。

| 后端 | 固定适配层做什么 | headless/结果边界 |
|---|---|---|
| ViewerGL | pyglet/OpenGL 交互场景与图像面板 | headless 仍创建隐藏 GL window/context；不等于无图形驱动 |
| ViewerNull | 空显示实现，end_frame 计数 | 不产生 RGB/depth；无窗口不意味着后台有相机图像 |
| ViewerUSD | 把场景/时间样本写到 USD，close 保存 | 文件是可供宿主渲染的场景，不是已渲染图像 |
| ViewerFile | 记录 model/state 的直接 Warp 数组快照 | 不是 solver checkpoint；Control、Contacts、输入/内部缓存需另记录 |
| ViewerRerun | 将数据交给 Rerun 可视化宿主 | 外部 SDK/历史保留模式另有配置，不是 Camera tensor producer |
| ViewerViser | browser/server 展示，也可记录 .viser | 浏览器显示/回放不等于 Newton 的图像或物理测量 |
| ViewerRTX | 先组装 USD，再交 OVRTX；版本分支可用 OVStage | 独立渲染宿主；异步模式可显示上一帧，不能把屏幕呈现当当前 State |

[公共 viewer 出口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/viewer.py#L5-L27)、[GL context 创建](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/gl/opengl.py#L1171-L1214)、[Null 行为](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_null.py#L127-L149)、[USD 时间与保存](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_usd.py#L231-L275)、[File 记录范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/visualization.rst#L347-L367)、[RTX 宿主、版本选择与异步模式](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_rtx.py#L112-L195)。

Newton 固定 SHA 只锁住 adapter。OVRTX/OVStage、pxr/USD、Rerun、Viser、pyglet、驱动与窗口系统有独立身份；Warp 1.18.0 仍是既有学习候选，未安装验证。官方文档中的已验证宿主矩阵是上游报告，不是本仓复现，也不能由 Newton 版本号补推当前机器的宿主版本。[RTX 上游验证范围](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/visualization.rst#L305-L328)。

交互输入也有独立边界：GL 的 `apply_forces(state)` 会调用 picking/wind 的力写入；单纯 log_state 没有推进物理，但应用若在 solver 前调用 apply_forces，viewer 便参与了控制输入。回放/对照必须记录这个调用，而不能把所有 viewer 行为都当成纯观察。[实际力入口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_gl.py#L2124-L2136)。

### 截屏、传感器图像和展示图不能混用

`ViewerGL.get_frame()` 读取最后的 GL framebuffer，返回 `(H,W,3)` uint8 RGB，原点左上；GPU 路径用 CUDA-GL interop，CPU 路径经过 host buffer。它跟随 viewer camera、显示 layout、装饰/选择状态和可选 UI，不返回 SensorTiledCamera 的 depth 或 shape IDs。[get_frame](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_gl.py#L2177-L2275)。

`viewer.log_image` 则展示已有图像；基类是 no-op，固定 GL 后端 override。接口接受灰度或 1/3/4 通道、单张或 batch，uint8 或 `[0,1]` float32；原始米制 depth 直接展示会被 clip。先用 `to_rgba_from_depth` 做显示映射，同时保留未经映射的 depth 数据；显示色标不是新的物理单位。[log_image 契约](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer.py#L2041-L2066)、[GL override](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_gl.py#L1862-L1870)、[深度显示转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py#L1261-L1317)。

USD 的样本索引是 `int(time * fps)`；过近的两次 log 若落在同一个索引，不能指望文件保留两份独立时间样本。ViewerFile 的重放恢复记录的状态而非重执行控制/接触方程；为复现保留输入、源版本与 solver 缓存是另一项数据工程，留 E5 展开。[USD 时间量化](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_usd.py#L231-L244)、[File 状态复制](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1176-L1240)。

## 8. 更新时间、批量与重置的共同原则

| 数据 | 需要更新的东西 | 保存时要带的元数据 |
|---|---|---|
| 相对位姿 | 对应 State 的 body_q，经 FK/solver 写入后 sensor.update | source state/time、目标与参考 site ID |
| IMU | 有效 qdd producer、q/qd/qdd 阶段与 sensor.update | backend/integrator、计算阶段、sensor→body 变换、gravity |
| Contact | 原 contact generation、对应 solver force readback | interval/dt、力组成、world/side、接触几何时刻 |
| Ray/camera | 对应 State 的 BVH refit、相机 pose/rays、输出写入 | world/camera axes、内参、clear/mask、颜色空间、源时间 |
| Viewer | 已选择的 log_state/log_image 与 backend frame | 显示时间、view/layout、异步呈现/记录范围 |

采样频率 $f_s$ 与步长 h 无整比时，不应用“每 N 步”冒充准确周期；可按仿真时间累计下一采样时刻，必要时标记实际采样偏差。跨步 held observation 不等于 interpolation，更不等于真实曝光积分。`numpy()` 会把设备数据交给 host，异步系统还需明确拷贝完成和 buffer 复用时点；不要把指针引用当不可变快照。

重置后需要重新更新观测并清理外部 timestamp/valid 标记，不能把上一 episode 的 image/IMU 数字配给新 State。世界掩码重置也不自动等于 sensor 输出只重算同样 mask；这些接口多数按已有选择列表或完整 B×C 发射 kernel。部分 world 的数据有效性应由调度层记录，不能只看数组 shape。

## 9. 原创例子：一帧几何深度的生命周期

[examples/e4_camera_frame.py](../examples/e4_camera_frame.py) 构建一个显式 world 的 primitive box，生成一组 pinhole rays，在 world 中放置 camera，refit 后填充并写入 range/forward-depth/shape ID。没有 viewer，也没有 solver；目的只是让每一步原生调用与维度可见。**文件未执行，只做 AST 检查**。

例子在 update 前显式填充 miss sentinel，保护完全空的渲染分支；它保留 axis order、source time、clear ID 和 shape 映射。这里使用原始 `uint32` ID，不把粒子/变形集合特殊 ID 混成模型索引。后续循环应复用静态 rays/output buffers，并在每次观测后按需要复制；一次静态例子不能证明运行兼容性、相机标定精度或视觉一致性。

## 10. 易错点与阅读练习

| 说法/现象 | 沿源码核对 |
|---|---|
| IMU 数组不为 None 就是实测加速度 | 申请存储不等于 producer 写入；检查计算阶段 |
| 静止 IMU 应输出零 | accelerometer 是 specific force；先扣 gravity 再换轴 |
| 相机视场 60 就是 60° | 原生 FOV 单位 rad |
| `(B,C)` transform 直接喂相机 | transforms 是 `(C,B)`，输出才是 `(B,C,H,W)` |
| depth 和 forward_depth 可随意互换 | 只有光轴方向两者相同；任意镜头还要考虑有效掩码 |
| 图里看不见所以物体不碰撞 | VISIBLE 与 COLLIDE_* 以及 BVH mask 分开 |
| camera.update 自动同步所有几何 | model shapes/particles BVH refit 由调用者负责 |
| miss 一定是负 depth | 默认 clear_depth=0；空几何分支甚至不写输出 |
| 每个 shape_index 都能索引 shape_label | 特殊集合 ID 和 miss 必须先处理 |
| headless 就完全不需要渲染依赖 | GL、Null、Camera、RTX 是不同路径 |

1. 3 个目标、1 个 reference site 会输出多少 transform？两个长度为 3 的选择器会输出 9 个吗？
2. 无旋转、site 位于 COM，world gravity=(0,0,-9.81)，$a_C=(0,0,-9.81)$ 时 accelerometer 是多少？
3. $\omega=(0,0,2)$ rad/s、$\alpha=0$，site 距 COM 的 world 偏移 r=(0.1,0,0) m；仅向心项是多少？
4. B=4、C=2、H=48、W=64，三类输入/输出的 shape 是什么？vec3 normal 转 NumPy 后呢？
5. ray 相对 forward 为 60°，range=2 m；forward depth 是多少？可否直接用它乘单位 ray 获得位移？
6. 默认 clear_depth=0 时，用 depth>=0 取有效像素哪里错？鱼眼 forward depth<0 一定 miss 吗？
7. 改了 State.body_q 后只调用 camera.update，为什么图像可能仍用旧位置？如果只改 visibility 呢？
8. 先为几何查询把 shape BVH 重建成 COLLIDE_SHAPES mask，再渲染，会自动恢复 VISIBLE 集合吗？
9. camera 的 shape_index 为 0xFFFFFFFE 时，可否拿它索引 shape_label？它证明哪一个粒子的 ID 吗？
10. ViewerGL 截图与 SensorTiledCamera RGB 相同尺寸，为什么仍不能当成相同观测？
11. fps=60 的 ViewerUSD 在 t=0.001/0.002 s 各写一次，源码将使用什么样本索引？
12. 创建 IMU 后给 body_qdd 分配零值，再更新静止 site 得到 +g，为什么这不能证明 solver 已支持加速度输出？

<details>
<summary>参考答案</summary>

1. 3 个；1 个 reference 广播。两个长度为 3 的列表是一一配对，仍为 3 个，需自行核对标签对应。
2. 零 specific force；这里重力导致自由落体加速度被扣除，和支撑静止不同。
3. $\omega\times(\omega\times r)=(-0.4,0,0)$ m/s²；还要加 COM、切向和重力项，再换到 sensor 坐标。
4. transforms `(2,4)`；rays `(2,48,64,2)` vec3；输出 `(4,2,48,64)`。normal 的 NumPy shape 为 `(4,2,48,64,3)`。
5. 1 m。不能；ray displacement 是 range×ray，若只拿 z，要用 z/(d·f) 恢复 range，并处理零投影。
6. miss 默认也是零，所以会误收；超过前半球的有效 ray 命中可产生负 forward depth，应依正确的 ID/有效性契约判断。
7. update 的三角数据同步不 refit model shape BVH。pose 改动 refit；纳入集合改变需要 rebuild，不能只 refit。
8. 不会；相机读取同一个 model BVH/启用列表。调用者必须维持所需集合，不能假定独立过滤自动修复。
9. 不可；它是粒子集合特殊 ID，不是一个 model shape ID，也不是单粒子身份。
10. camera pose、显示布局、材质/光照、UI、通道编码与更新时间均可能不同；相同尺寸只说明像素数相同。
11. 两次都是 int(t×60)=0；不能把调用次数当作不同 USD time sample。
12. IMU kernel 只读零加速度并扣 g，就能给出外观合理的值；它只检查数组存在，不验证 writer 或更新时间。

</details>

## 11. 验收与后续

[E4 验收](e4-validation.md)记录固定源码身份、语法/链接检查、人工审查范围以及未执行事项。A6 的原生 sensing/query/viewer 链已展开；这不代表已验收真实摄像机/IMU/触觉硬件模型，也不是渲染视觉 QA 或性能测试。

下一项 E5 已具备 E2/E4 前置，可展开 batch/reset/learning/data 生命周期；专用 renderer/solver 扩展与完整可微实现继续留 E6。实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 的冻结版本、工况与限制，不用此处源码默认值补写历史运行数据。
