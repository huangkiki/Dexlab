# E4：传感器、渲染与可视化

本章完成 A6：读完应能为每个观测写清「产生者、几何、坐标、单位、shape、采样阶段和有效性」，并沿原生接口追到固定实现。阅读基线为 Genesis 1.4.3、官方提交 `216a708e06124595521a9d36a51fae5393fd4ff8`；源码核对和语法检查已做，**没有 import、构建、仿真、渲染或硬件验收**。渲染依赖的安装与运行能力不能由本文推定。

先修：[E1 坐标/状态/时间](modeling-state-time.md)；力读数先读 [E3 第8节](contact-solvers-forces.md)。机器人挂载与索引参见 [E2](control-robotics-tasks.md)。本章公式默认 SI 长度/时间/力，角度字段单独标注；用 `B` 表示选中环境数、`H,W` 表示图像高宽、`P` 表示 probe 布局。没有重新设计数据框架，实验最终复用 DexLab。

## 1. 三条观测路径，先找实际产生者

| 原生入口 | 产生的数据 | 更新与范围 |
|---|---|---|
| `scene.add_camera(...)` → `genesis.vis.camera.Camera` | `render()` 的 RGB/depth/segmentation/normal；`render_pointcloud()` | 显式渲染请求；选择 Rasterizer/RayTracer/BatchRenderer，输出与环境批量依赖分支 |
| `scene.add_sensor(gs.sensors.*CameraOptions(...))` | 三种 RGB camera sensor 的 `read().rgb` | 延迟到 `read()` 渲染，缓存按全局物理 step 判新旧；不是普通 sensor ring |
| `scene.add_sensor(gs.sensors.DepthCamera/ Raycaster/ ContactForce/ …)` | 射线、动力学量或专门传感模型 | 常规 manager 在每个外层 step 后更新；`read()` 读取已更新缓存 |

`Scene.add_sensor(sensor_options)` 在 build 前注册并交给 SensorManager；直接 new 内部 Sensor 类会绕过类型分组、cache 和共享 context。`gs.sensors.Lidar` 是 `Raycaster` 的别名，不能据名字宣称另一套激光扫描硬件模型。[Scene入口][scene-sensors]、[类型与别名][sensor-ns]、[相机分派][cam-render]。

可见外观、碰撞几何、射线目标和传感器模型是四件事：纹理透明不自动移除 collision mesh；看见 MPM 粒子不等于 Raycaster 对它建了 BVH；taxel 估计力也不直接改写刚体动力学。选择入口后再选输出，不能把所有观测统称为 `scene.get_state()`。

## 2. 常规传感器：采样、缓存、延迟与 reset

### 2.1 外层时间线

```text
Scene.step
  pre-step callbacks → 可否决本次物理推进
  RecorderManager.step：读取步开始时状态/上一轮已缓存的 sensor
  Simulator.step
    全部 physics substeps → clear_external_force
    SensorManager.step：刷新共享 BVH → 各类型采样/变换/误差/输出投影
  visualizer update
  Camera.update_recording：本步推进后，达到录像采样期限才渲染
```

这条顺序由 [Scene.step][scene-step] 和 [Simulator.step][sim-step] 决定。传感器 `dt` 是外层 `sim.dt`；不是子步 `dt/substeps`。`SensorOptions` 没有通用 `update_rate` 字段，多读几次不会增加采样率，也不会每次重采噪声。否决推进时 manager 不更新；GUI 可以继续刷新，不能把新画面当作新的动力学样本。[选项][sensor-options]、[manager更新][manager-step]。

步后相机通常显示积分后的几何；ContactForce 却消费最后一个子步保存的接触力，IMU 消费求解器保存的 link 加速度。E3 已说明这些字段不是同一瞬间的完整测量。日志至少记录外层 step、dt/substeps、观测类型及“pre-step recorder / post-step cache / lazy render”阶段；不要只记录 wall clock 或视频帧号。

### 2.2 measured、ground truth 与历史不是三个独立物理世界

普通 SimpleSensor 的顺序是：raw/感知模型及measured-only物理误差 → 各分支坐标/响应变换 → 硬件误差 → `_post_process` → return ring → 延迟选样。GT 保留自己的变换/后处理分支；“ground truth”表示该传感模型的无测量误差输出，**不保证无截断、不保证等于原始 solver 数组**。例如 ContactForce 的 GT 同样经过 min/max 后处理，IMU 的 GT 仍经过轴对齐矩阵。[SimpleSensor更新][simple-pipeline]、[ContactForce后处理][force-post]、[IMU变换][imu-impl]。

硬件误差可概括为

$$
 b^{rw}_k=b^{rw}_{k-1}+\epsilon^{rw}_k,\qquad
 y_k=Q_r(x_k+b+b^{rw}_k+\epsilon_k),\qquad Q_r(x)=r\operatorname{round}(x/r).
$$

源码按 `random_walk → noise → bias → resolution` 操作；noise/random_walk 是**每次外层采样**的标准差，函数没有自动乘 `sqrt(dt)`。不同 dt 下复用数值不等于复用同一连续时间噪声谱密度；量化关闭由 resolution 的阈值判定。GT 不经过这段硬件误差。[实现][hardware]。

`delay` 单位 s，注册时换成 `round(delay/dt)` 个 step。无历史读取通过零阶保持选旧 return-ring 槽；jitter 使用均匀样本加概率取整，可能再旧一槽。配置须满足 `jitter <= delay`；SimpleSensor build/setter 的实际检查允许 `jitter == dt`（带 EPS 容差），不要照旧注释写成严格 `<dt`。[delay实现][delay]、[jitter校验][jitter]。

`history_length=K>0` 直接读取 ring 的 `[0,1,…,K-1]`，从最新到更旧：**这条历史路径绕过 delay/jitter 选样**。因此同时配置 delay 和 history 并不会得到“已延迟的历史”。上游测试明确断言该行为；本文只阅读测试，没有执行。[缓存和历史][manager-read]、[固定版本测试][history-test]。

### 2.3 shape、所有权、索引

常规传感器的内禀 shape 为 `S`，则 `read()` 返回 `S`（`n_envs=0`）或 `(B,*S)`（`n_envs>0`）；开历史后变成 `(*batch,K,*S)`。多个字段返回 NamedTuple；单字段通常是 Tensor。普通 `read(envs_idx=integer)` 经一维索引整理后仍保留长度1的 batch 轴；RGB camera sensor 的 override 会移除此轴，不能统一 `squeeze()` 猜语义。[通用格式化][sensor-read]、[camera格式化][sensor-cam-read]。

Manager 内部无历史读取是 cache view，但公共通用格式化还会做高级索引；不要仅凭 `get_cloned_from_cache` 名称或“pure view”注释判定所有权。RGB camera 默认读取直接给 image-cache 张量，后续渲染会原位覆盖。保存长期数据应显式 `.clone()`（NumPy 图像 `.copy()`），并保存对应时间；`.detach()` 只能断梯度，不是复制存储。

`scene.read_sensors()` / `entity.read_sensors()` 是按类型 tag 打包的扁平缓存，tag 来自 `gs.sensors.types.<Name>`，不是跨版本稳定的序列化 ID；有历史的类采用该类最大历史长度，不能按各实例 shape 盲拆。它通过环境高级索引产生新 tensor，适合明确布局后的批读；E5再讲数据组织。[打包实现][manager-bulk]。

`scene.reset(envs_idx=...)` 会清该批传感器 cache/ring，并调用共享 context 与各类 reset；初始普通读数不等于已进行一次测量。部分传感器 reset 会另设基线/模型内部状态。相机 reset 使下一次 read 重渲染，当前实现部分 env reset 也使整批相机失效。**快照物理 q/v 不自动包含传感器噪声游走、历史、触觉锚点、图像缓存或录像时钟。**[manager reset][manager-reset]、[camera reset][sensor-cam-cache]；物理 checkpoint 边界见E1。

## 3. `add_camera`：图像、分割和坐标

### 3.1 输出契约先按渲染器分开

`camera.render(rgb=True, depth=False, segmentation=False, normal=False, colorize_seg=False, antialiasing=False, force_render=False)` 返回固定4元组 `(rgb, depth, segmentation, normal)`。关闭的通道为 `None`；BatchRenderer的部分缓存命中例外见下文。一张图的 res 参数是 **`(W,H)`**，数组却是 **`(H,W,channels)`**。[render][cam-render]。

| 分支 | RGB | depth / segmentation / normal | 批量和依赖 |
|---|---|---|---|
| Rasterizer | OpenGL、NumPy `uint8` RGB | depth NumPy float32；seg NumPy int64内部ID；normal 是RGB编码的法向图 | `split_envs=True` 可逐环境渲染再stack；不是GPU原生批处理 |
| RayTracer | LuisaRender 的 NumPy `uint8` RGB | 同一 `Camera.render` 调用转交 **Rasterizer** | vis camera 绑定一个环境；不是全部通道经过路径追踪 |
| BatchRenderer | Madrona adapter 返回设备张量，经Genesis去alpha/分camera | 包括深度/seg/normal通道；具体底层通道契约受外部adapter版本约束 | 固定源码要求 CUDA、可导入的Linux x86-64 Madrona、同分辨率；几何提取器读取rigid visual geometry |

Rasterizer dtype 来自 [framebuffer读回][jit-read]；分割整数转换见[context解码][seg-decode]；RayTracer分支与字节读取见[render_camera][ray-render]；BatchRenderer约束和转换见[build][batch-build]、[render][batch-render]。没有据 `gs.init(precision='64')` 宣称图像为FP64；也没有据GPU可见或可import宣称这些依赖可运行。

**BatchRenderer缓存缺口**：第一次请求RGB后，同step再请求RGB+depth，会走“RGB已缓存、depth需计算”的混合分支；末尾仅返回needed通道，已缓存的RGB槽可能返回None。所有通道均缓存时的提前返回则正常。需要完整多通道快照时一次请求齐全，或 `force_render=True`；本例使用后者。该结论来自[缓存返回逻辑][batch-render]，未运行复现。

`debug=True` 的 vis camera 绕过 RayTracer/BatchRenderer，走 Rasterizer，可包含调试标记；非debug camera 通常跳过markers。GUI中的坐标轴、力箭头等不能当作机器人传感数据，更不能量取力值。[camera build][cam-build]、[raster render][raster-render]。

### 3.2 深度不是沿射线的 range

对于 pinhole，垂直 FOV 使用 degree，`f_x=f_y=f=H/(2 tan(fov/2))`（计算前转弧度），像素中心使用 `u+0.5,v+0.5`。令

$$
 x_n=(u+0.5-c_x)/f_x,\quad y_n=(v+0.5-c_y)/f_y,\quad
 p_{CV}=z(x_n,y_n,1),\quad r=z\sqrt{1+x_n^2+y_n^2}.
$$

`camera.render(depth=True)` 的 Rasterizer返回投影轴深度 `z`，单位沿模型的m。OpenGL z-buffer经过near/far反投影，远裁剪背景返回far附近，**不是必然0**。BatchRenderer ray模式代码还显式把中心射线距离乘 `1/sqrt(1+x_n²+y_n²)` 变成plane depth。公式是pinhole假设，不把thin-lens/fisheye都强行解释为理想针孔深度。[反投影][jit-read]、[batch深度转换][batch-render]、[相机换算][cam-pointcloud]、[内参属性][cam-intrinsics]。

`render_pointcloud(world_frame=False)` 用上述 `(x,y,z)`，即OpenCV风格右/下/前；`world_frame=True` 用 `T_camera @ diag(1,-1,-1,1)` 从相机OpenGL姿态转换到世界。结果实际shape是 `(*depth.shape,3)`，通常 `(H,W,3)` 或 `(B,H,W,3)`；docstring写 `(res[0],res[1],3)` 与实现不符，以reshape为准。它返回 `(points,valid_mask)`，mask为 `near < depth < far*(1-1e-3)`，没有自动删掉无效点。[pointcloud源码][cam-pointcloud]。

这个函数自身使用pinhole反投影，没有针对fisheye分支；fisheye点云的几何正确性留待单独核验。Batch depth先转NumPy，因此 pointcloud 是CPU数组而非可微设备输出。相机显示坐标还可能包含 `envs_offset`，不能把并排展示位移混入物理观测坐标；E1说明env_spacing只服务可视化。[camera batch/offset][cam-build]。

### 3.3 分割像素必须解码

`VisOptions.segmentation_level` 可选 entity/link/geom。`Camera.render` 注释说像素可直接用作link索引，**但固定实现实际返回压缩映射 `seg_idxc`**：0是背景，对应key −1；其余ID按注册顺序分配。对于刚体，key分别是 `entity.idx`、`(entity.idx,link.idx)`、`(entity.idx,link.idx,geom.idx)`；其他物理分支key需查各自注册，不能统一当三元组。

正确入口是 **`scene.visualizer.segmentation_idx_dict`**，由visualizer按主renderer选择对应字典；`colorize_seg=True` 只把ID变为便于看的颜色，颜色不是语义类别或训练标签。保存图像时同时保存映射、level与资产版本；重建场景后ID顺序可能改变。[压缩ID分配][seg-map]、[刚体key][seg-key]、[公开字典属性][seg-property]、[batch key][batch-key]。

若使用debug raster camera与主BatchRenderer混合，不保证二者映射完全相同；要沿实际输出renderer取映射，不能用主renderer字典盲解debug图。最小示例限制为主Rasterizer，没有掩盖这种分支差异。

### 3.4 法向图与附着姿态

Rasterizer normal shader用模型变换逆转置得到世界法向，fragment把 `n` 编码成 `0.5*n+0.5`，再经uint8 framebuffer读回。其像素不是直接的 `[-1,1]` 向量；在有效几何像素上可近似 `n≈2*RGB/255−1`，还存在量化、法向插值和双面处理。不能用背景像素估计接触法向，更不能默认Madrona normal也有同一编码。[vertex shader][normal-vert]、[fragment shader][normal-frag]、[normal通道读回][normal-pass]。

vis camera的 `set_pose(transform=...)` 与 pos/lookat/up 二选一；虽然docstring写优先级，实际同时传入会报错。[参数校验][cam-pose]。光轴沿OpenGL的−Z，+Y为up。`attach(link,offset_T)` 描述 link→camera 的固定变换，由 `move_to_attach` 应用。对RGB sensor，附着后的稳态 `move_to_attach` 同样算 `T_world_link @ offset_T`；未给offset_T时从options pos/lookat/up组成局部变换，和部分字段docstring声称lookat world不完全一致。对带旋转的挂载，**显式给offset_T**最容易保证语义，不能把继承的euler_offset当作所有camera派生都消费的朝向。[vis attach][cam-attach]、[sensor attach/read][sensor-cam-read]。

## 4. RGB camera sensor：同名功能不能沿基类推断

`gs.sensors.RasterizerCameraOptions`、`RaytracerCameraOptions`、`BatchRendererCameraOptions` 都返回 `CameraReturnType(rgb=...)`，`read().rgb` 是 `gs.device` 上uint8 Tensor，单环境 `(H,W,3)`，batch `(B,H,W,3)`；整数 envs_idx 直接移除batch轴。**没有 depth、normal、segmentation 字段。**[return format][sensor-cam-cache]、[read override][sensor-cam-read]。

| 选项类 | 固定版本实际行为 |
|---|---|
| RasterizerCameraOptions | 有viewer就复用viewer GL context，否则建独立offscreen context；render时split_envs=True逐环境渲染；独立路径对非rigid且n_envs>1报错 |
| RaytracerCameraOptions | 要求Scene主renderer是RayTracer；n_envs>1报错；底层注册vis camera，读取时force_render=True |
| BatchRendererCameraOptions | CUDA、同分辨率；自行建共享Madrona renderer，读取一台会渲染该类型的所有相机；选项默认use_rasterizer=True，而主`gs.renderers.BatchRenderer`默认False |

这里描述的是源码接线，未验收所有跨renderer组合。这来自 [Rasterizer派生][sensor-raster]、[RayTracer派生][sensor-ray]、[Batch派生][sensor-batch] 和 [配置][camera-options] / [主renderer配置][renderer-options]。Batch sensor首先创建的共享renderer读取该实例的use_rasterizer配置；不要以为每台同类型camera可以独立选择渲染算法。

缓存判断是 `last_render_timestep != sim.cur_step_global`。同step反复read复用图像；同step手动改变状态不会自动因“值变了”而标stale；reset显式失效。vis camera需要即时刷新时有 `render(force_render=True)`，RGB sensor的read没有该参数。调用继承基类getter也不等于强制拍照。[lazy cache][sensor-cam-read]。

**当前API接线缺口**：RGB sensor `_update_shared_cache` 是空实现，派生renderer写自己的 `image_cache`，只有 `read()` 覆写为读取它。`read_ground_truth()` 仍继承通用基类，`scene.read_sensors()` 也直接读manager通用cache；两者没有接到RGB图像缓存。不能将它们当作RGB相机接口或拿其中初始零值判“黑图”；用 `rgb_sensor.read().rgb`。这是固定源码推导，未做运行复现。[camera cache][sensor-cam-cache]、[基类GT][sensor-read]、[批读][manager-bulk]。

同理camera明确 `uses_ring_pipeline=False`，构造拒绝delay/jitter/history，不支持SimpleSensor的noise等硬件字段。图像噪声、滚动快门、曝光时间响应和RGB-D严格同步没有在这条API中建立，不能由spp/denoise字段推导出来。[基类拒绝条件][camera-reject]。

## 5. Raycaster / Lidar / DepthCamera：几何查询

### 5.1 原生pattern与输出

`gs.sensors.Raycaster(pattern=...)`（别名Lidar）支持 GridPattern、SphericalPattern、DepthCameraPattern。pattern在Genesis初始化后分配设备张量；Grid在每格有独立起点，Spherical指定扫描角度，DepthCameraPattern按像素生成归一化射线。

`DepthCameraPattern(res=(W,H), fx=…,fy=…,cx=…,cy=…)` 的射线为

$$
 d_{robot}=\operatorname{normalize}(1,-x_n,-y_n),
$$

即 **+X前、+Y左、+Z上**，与vis camera的OpenGL姿态、pointcloud的OpenCV输出都不同。FOV字段是degree，fx/fy/cx/cy是pixel。实现当fx或fy任一个缺失时重新计算二者；只给一项焦距并不能保证保留它。指定两个显式焦距可避免歧义。[pattern实现][patterns]。

`read()` 返回 `RaycasterReturnType(points,distances)`；shape为 `(*batch,*pattern.return_shape,3)` 和 `(*batch,*pattern.return_shape)`。`return_points=False` 时 points为None；距离仍存在。`DepthCamera.read_image()` 只是把read().distances reshape成 `(*batch,H,W)`，**它是射线range r，不做z投影**。它也没有envs_idx参数，shape未包含history轴；不要在history_length>0时用它，改读并按真实shape处理。[ray格式][ray-sensor]、[depth实现][depth-sensor]。

### 5.2 几何、命中与坐标边界

RaycastContext实际遍历 **rigid_solver和kinematic_solver**：rigid默认建collision faces BVH；两者中启用material.use_visual_raycasting的视觉faces可再建visual BVH，多次cast取最近命中。没有遍历MPM/SPH/PBD/FEM solver，因此这些物体即使能被renderer画出，也不能据此推断能被Raycaster检测。没有任何可cast几何会在build报错。[BVH激活][ray-context]、[传感器build][ray-sensor]。

`max_range` 单位m；无命中distance默认max_range，也可设no_hit_value（例如−1），points写零。零点可能也是真实位置，所以不能只看points是否全零；有噪声时哨兵判定还需结合明确的预处理约定。**min_range在选项中校验并存入metadata，但当前cast调用没有传它、后处理也未过滤它**；不能把配置字段当作已实现的近距离盲区。[选项][ray-options]、[kernel调用][ray-sensor]、[kernel参数][ray-kernel]。

世界点是 `origin_world + r*direction_world`。`return_world_frame=False` 实现却返回 `r*normalize(ray_dir_local)`：它是**沿射线起点的位移向量**，不加Grid起点或pos_offset；ray_dir_local已经包含euler_offset旋转。尤其Grid不能把这个值直接当完整的link-local位置，需加入对应ray_starts；若要世界命中点可直接return_world_frame=True。[write_ray_hit与射线换系][ray-hit]。

射线从选定几何求交，不是带发射时序、回波强度、多回波、材质透射、运动畸变或扫描周期的真实LiDAR模型。距离真值与RGB depth还可能因碰撞/视觉mesh不同而不同；先统一几何和坐标再讨论误差，不在本章做配对实验。

## 6. 力传感器与 IMU：动力学字段如何变成观测

### 6.1 Contact 和 ContactForce

`gs.sensors.Contact(entity_idx=body.idx,link_idx_local=k)` 的read内禀shape `(1,)`，bool判定是“参与接触条目数 > threshold”，threshold不是N。`filter_link_idx` 是**排除**的对侧global rigid link索引，不是include列表；其语义也用于ContactForce和contact-driven tactile。[选项过滤][contact-filter]、[Contact实现][contact-bool]。

混合solver场景还需核查Contact的entity索引：该类build从 `rigid_solver.entities[entity_idx]` 取实体，而通用挂载mixin从 `sim.entities[entity_idx]` 取；当两者编号不一致时存在接线风险。本例限定全刚体场景，不把它宣布为已验收的混合solver能力。[Contact build][contact-bool]、[通用挂载][sensor-mount]。

`ContactForce` 内禀shape `(3,)`，读数单位N，**附着link局部坐标**：

$$
 F_L=R_{WL}^{T}\sum_c s_c F^{internal}_c,
 \quad s_c=-1\ (link=A),\quad +1\ (link=B).
$$

源码先按A/B符号求和再逆旋转（另一非zerocopy分支逐接触做同等变换），再对每轴执行 `clip(F,−max_force,+max_force)` 和 `abs(F)<min_force → 0`。不是力的模长限额，不返回torque，也没有应用pos_offset生成六轴wrench。多个力可能相消；休眠接触可保留上次awake的支撑力。积分后的姿态用于旋转旧子步接触力，这种采样差异需与E3一起阅读。[聚合与换系][force-raw]、[后处理][force-post]。

若需要关于某参考点的力矩，可由已确认的世界接触点计算 `(p−p_ref)×F`，但这不能补齐E3指出的spin/rolling纯偶矩缺项。ContactForce和taxel并不自动构成可校准的六轴力/力矩传感器。

### 6.2 JointTorque 并非 `get_dofs_control_force()` 别名

`gs.sensors.JointTorque(entity_idx=robot.idx,dofs_idx_local=(...))` 返回所选DOF的输出端广义effort，revolute是N·m、prismatic是N。它调用 `RigidSolver.get_dofs_actuator_force`：

$$
 \tau_{out}=qf_{applied}-I_{armature}\,qacc_{constraint}
             +qf_{frictionloss}+qf_{passive}.
$$

qf_applied是保存的实际驱动力；frictionloss由对应约束行映射，passive包括耗散项，约束解加速度把负载间接带入。它不直接返回电机命令、关节所有净力或单一contact wrench，不能对比PD限额就直接下“受力超限”结论。[sensor调用][joint-sensor]、[getter字段与公式][actuator-force]。外部耦合对所有effort项的完整等价性不由这个刚体公式保证。

### 6.3 IMU 的重力与杠杆臂

`gs.sensors.IMU` 的NamedTuple字段是 `lin_acc, ang_vel, mag`，每项 `(*batch,3)`。在固定实现中

$$
 a_S=R_{WS}^T\big(a_L+\alpha\times r+\omega\times(\omega\times r)-g\big),
 \quad\omega_S=R_{WS}^T\omega_W.
$$

a单位m/s²，omega为rad/s；r是link→sensor偏移在世界系表达。静止正放加速度计会读到抵消重力的proper acceleration，而不是零。之后还会应用cross-axis矩阵与各通道误差。mag只是把配置的世界磁场向量旋转到sensor系；代码不做单位换算，`magnetic_field`及noise/bias必须使用一致的自定磁场单位，默认 `(0,0,0.5)` 不能直接标成地磁标定的Tesla值。[IMU kernel][imu-kernel]、[返回与变换][imu-impl]。

## 7. 触觉：五类量，三种来源

所有probe_local_pos都在附着link坐标，位置/半径m；输出保留原probe布局P（`(N,)` 或 `(ny,nx)`），再加batch/history。不能把 `(ny,nx)` 排布直接当相机像素或真实接触面积。

| 原生选项 | 输出与来源 | 关键限制 |
|---|---|---|
| ContactDepthProbe | Tensor `(*batch,*P)`，m；对接触候选几何做SDF/最近三角查询得到probe深度 | 由solver接触存在性预筛选；不是任意距离探测 |
| ContactProbe | 同P形状bool；深度阈值/释放阈值Schmitt状态 | 阈值是m；固定–固定被碰撞器跳过时不会凭空检测 |
| KinematicTaxel | NamedTuple `.force/.torque`，各 `(*batch,*P,3)`，link系N/N·m | 接触候选+几何深度/相对速度的估计，不是solver impulse |
| ProximityTaxel | 同样force/torque；对track_link_idx采样点云，在每个球形probe内汇总穿入量 | 依赖点云密度、采样/visual选择、半径和增益；可在真正碰撞前产生感知量 |
| ElastomerTaxel | Tensor `(*batch,*P,3)`，link系marker位移，名义m | HydroShear风格dilation/shear响应；不是力图、RGB触觉图或求解器FEM变形 |

来源：[contact probes和Kinematic配置][tactile-options]、[probe与taxel返回][kin-taxel]、[点云返回和密度归一化][prox-return]、[Elastomer形状与reset][elastic-return]。Elastomer非线性normal_exponent和dilate/shear gain带有模型尺度，不能未经标定把默认数字解释成材料SI本构常数；本章不宣称其真实传感器标定成立。

### 7.1 KinematicTaxel 的力/力矩到底如何算

对最大probe深度 `δ>0`，指数 `p=normal_exponent>=1`、link系表面法向n，源码先计算 `s=δ^p`，再用对方减sensor的相对速度 `v_rel`、法向分量 `v_n=v_rel·n`、切向 `v_t=v_rel−v_n n`：

$$
 F=k_n s n+c_n s v_n n-c_s v_t,
 \qquad T=r_{probe}\times F-c_t(\omega_{rel}\cdot n)n.
$$

这不是E3约束求解器的摩擦锥法；没有在此按 `μ F_n` 钳制切向力，也不将F施回动力学。若要公式输出N，则 `k_n` 单位N/m^p、`c_n` 为N·s/m^(p+1)、`c_s` 为N·s/m，`c_t` 为N·m·s（弧度无量纲）；改变p必须重新理解参数，不能沿用线性弹簧的N/m标签。没有接触候选时输出零；法向由SDF梯度或三角面决定，mesh预处理影响结果。[实际kernel][taxel-force]。

contact-driven路径每个sensor最多缓存1024接触、64不同对侧geom，超出会截断；网格光滑性、SDF分辨率或采样点数都不是无限精度。ContactDepthProbe / KinematicTaxel 的候选门控、排除filter与容量见[接触预筛选][taxel-prefilter]。

### 7.2 感知模型状态、误差与可视化

`contact_depth_query='sdf'/'raycast'` 选择几何深度后端；同一类共享选择，未指定时默认SDF。ProximityTaxel依赖采样云，而Elastomer按tracked几何深度计算dilation并保留shear锚点；规则平面grid可走FFT，非严格规则grid可能用平均间距近似并警告，不能只凭tensor排成二维就当精确规则网格。[深度选项][tactile-depth-options]、[Elastomer模型与参数][elastomer-options]、[FFT资格][elastic-build]。

measured分支可包含半径/增益、dead taxel、viscoelastic hysteresis、grid crosstalk等误差。单Maxwell式状态为 `xi_k=exp(−dt/tau)xi_(k−1)+(x_k−x_(k−1))`，输出 `x+strength*xi`；这是感知响应近似，GT仍是该几何/感知模型而非真实硬件。crosstalk要求平面grid且核/间距单位正确；defaults不是传感器实测标定。reset后的锚点、历史和gain重采样需与episode边界一致。[误差选项][tactile-errors]。

`draw_debug=True`显示probe、箭头、点云用于核对位置；它不会输出经过光学渲染的GelSight图像，也不会证明传感器受力与solver接触平衡。

## 8. 其他原生传感器与能力缺口

`SurfaceDistanceProbe` 用明确 `track_link_idx` 的刚体mesh查询最近距离，read返回probe布局的m值；nearest_points另有世界坐标属性。超范围distance钳到probe_radius，nearest point回probe位置。它的tracked mesh BVH按刚体假设构建，不能替代任意动态变形mesh距离场。[选项][surface-options]、[BVH构建][surface-impl]、[输出属性][surface-points]。

`TemperatureGrid`是附着刚体link的格点温度模型，read形状 `(*batch,*grid_size)`，单位°C，带接触热交换、对流/辐射及传感器RC响应；properties_dict的key为global link，多个sensor共享部分参数。它属于额外感知/热模型，不能从能返回温度推断所有动力学材料都热力耦合。具体热模型离散推导留E6；本章完成API、形状和边界索引。[温度选项][temperature-options]、[形状与滤波][temperature-impl]。

本章已列出固定版本主要原生sensor选项；真实RGB-D校准、滚动快门、事件相机、多回波LiDAR、六轴wrench和触觉光学成像没有在上述API建立统一保证。专用外围模块或未来版本的能力需要单独给出实现证据。

## 9. GUI、headless、批量与可微边界

`Scene(show_viewer=False)` 关闭交互viewer；`add_camera(GUI=False)`关闭OpenCV图像窗口，二者分别控制不同显示路径。headless不是“无需图形依赖”：Rasterizer仍建offscreen GL context，Linux会选择EGL，特定条件下可回退OSMesa；缺显示时Visualiser会提示关闭viewer。这个选择在导入OpenGL平台相关模块前发生，运行中改环境变量不能保证重新绑定。[visualizer初始化][visualizer-init]、[raster平台选择][raster-platform]。

交互viewer一直是Rasterizer，与主camera选RayTracer/BatchRenderer独立。多个Scene不能同时开启该interactive viewer；macOS不支持后台viewer线程，其默认走主线程。Viewer帧率、物理dt、相机录像fps和模型感知dt分别记录，不以“看到60fps”推断60Hz控制。[visualizer初始化][visualizer-init]。

批量约定：`n_envs=0`没有用户batch轴，`n_envs=1`仍有。vis Rasterizer `split_envs=False`可把多个环境按展示offset画到一张图；True按rendered_envs_idx分别渲染。RayTracer vis camera按env_idx绑定一个；RGB sensor拒绝n_envs>1。BatchRenderer面向所有物理env的rigid visual meshes；选择性rendered_envs_idx与camera位姿数还需保持一致，本文最小例子不做子集batch。不能将renderer支持自动推广到所有solver或所有sensor。[camera build][cam-build]、[raster分支][raster-render]、[batch build][batch-build]。

渲染图像/缓存 **不构成端到端可微接口承诺**：Rasterizer/RayTracer经NumPy/uint8，RGB sensor从NumPy转tensor或copy到uint8 cache；raycast使用离散BVH命中和kernel写缓存；通用sensor硬件层含随机与round。`SimOptions.requires_grad=True` 不自动给这些输出建立损失→像素→几何→刚体状态的backward链。一个Tensor有设备/甚至可设requires_grad，并不证明梯度穿过采样器；需逐算子/solver追踪，E6负责专门可微路径。本章不宣称所有浮点观测在数学上都不可导，只确认上述实现不能据总开关保证传感梯度。[RGB派生][sensor-raster]、[ray kernel][ray-kernel]、[硬件操作][hardware]。

## 10. 最小原生接口阅读片段

原创 [sensor_rendering_api.py](../examples/sensor_rendering_api.py)只提供两个明确生命周期的演示函数：build前在调用方已有刚体Scene注册vis camera、RGB sensor、射线DepthCamera和ContactForce；调用方完成一次已有物理step后再read。**文件没有主程序、init、build、step循环、资产下载或实验评分；本轮仅AST检查，未执行函数。**

为了看清两种深度来源，文件同时读vis projected depth与ray range，但不将它们当数值对照：两者外参/方向与geometry需另行对齐才可比较。示例只使用主Rasterizer、n_envs=0或完整rigid batch，保存返回值的独立副本，并导出segmentation_idx_dict。它不是传感器适配框架；后续任务仍直接调用Genesis API。

## 11. 阅读练习与答案

1. `res=(320,240)`、n_envs=1，RGB sensor shape是什么？**答：** `(1,240,320,3)`；`read(envs_idx=0).rgb` 为 `(240,320,3)`。普通ContactForce选择0仍通常是 `(1,3)`。
2. RayTracer生成的RGB与depth是否都是Luisa路径追踪？**答：**不是。vis Camera的depth/seg/normal转到Rasterizer；sensor RaytracerCamera只返回RGB。
3. DepthCameraPattern边缘射线距离2m，`x_n=1,y_n=0`，轴深度是多少？**答：** `z=2/sqrt(2)` m；read_image本身仍返回2m。
4. 分割像素7是不是link7？**答：**不能推断。查该renderer的segmentation_idx_dict；link级刚体key是(entity,link)，背景0→−1。
5. 把Raycaster.min_range设成1m，能保证不输出0.2m命中吗？**答：**不能，该提交min_range没传入cast/过滤；必须保留这一缺口。
6. Grid ray local points为什么丢了网格横向布局？**答：**local输出是r乘方向，没有加各ray起点；world输出才含完整起点。
7. dt=10ms、delay=20ms、history_length=3时历史最新项是哪步？**答：**history路径取当前ring槽开始，绕过delay；普通无历史读取才按2槽延迟。初始化前历史可含reset基线。
8. 同step改机器人qpos后RGB sensor read仍是旧图，哪里看？**答：**lazy cache按cur_step_global而非状态hash；vis camera可force_render，RGB sensor read无此参数；不应擅改私有stale字段冒充公开刷新API。
9. ContactForce各轴max=10N，输出(10,10,0)合力超过10N是bug吗？**答：**不是，它是每轴限幅；GT也过后处理。它没有给合力模长作10N限额。
10. KinematicTaxel力等于solver接触力吗？改变normal_exponent需改什么理解？**答：**它是深度/速度模型估计；k_n量纲随指数变成N/m^p，不能仍解释为N/m。
11. 静止IMU为何不是零？sensor与contact读数是否严格同frame？**答：**加速度计减重力，测proper acceleration；IMU/接触使用solver缓存的不同阶段，再由步后sensor处理，不能把统一读取时刻等同于统一物理采样时刻。
12. `read_ground_truth()`能读RGB相机无噪声图吗？**答：**该版本不能如此使用，继承路径未接image_cache；应使用覆写read().rgb。GT标签也不会让普通taxel变成硬件真值。
13. show_viewer=False且GUI=False能证明服务器可离屏渲染吗？**答：**不能，还需实际GL/Luisa/Madrona依赖与驱动运行验收；本章只核实路径。
14. `requires_grad=True`且观测为Torch Tensor，可直接图像优化吗？**答：**不能。要证明完整backward链；uint8、NumPy转换、离散raycast与cache写入不能靠总开关自动消除。

## 12. 完成范围与下一步

A6的原生接口、帧/单位/shape/时序、renderer和sensor分支、常见缺口已展开，状态见[E4验收](e4-acceptance.md)。源码身份不等于运行证据，官方测试只作为预期行为阅读，不计为本仓通过测试。

E5承接批量reset、观测打包、时间戳与学习/数据接口；E6进一步展开多物理专论、热/触觉专项数值模型与可微内部。本章不替DexLab历史配置补字段，不新增实验。E7应保留这些固定版本实现与docstring的差异，升级时逐项复核，不能抹成统一能力列表。

## 固定源码引用

[scene-sensors]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L584-L615
[sensor-ns]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/__init__.py#L1-L33
[cam-render]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L394-L500
[scene-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py#L1053-L1104
[sim-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py#L345-L376
[sensor-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L34-L104
[manager-step]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/sensor_manager.py#L314-L380
[simple-pipeline]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L811-L865
[force-post]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/contact_force.py#L338-L347
[imu-impl]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/imu.py#L117-L225
[hardware]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L943-L969
[delay]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L394-L435
[jitter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L735-L794
[manager-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/sensor_manager.py#L389-L420
[history-test]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/tests/sensors/test_api.py#L347-L375
[sensor-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L475-L535
[sensor-cam-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py#L281-L391
[manager-bulk]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/sensor_manager.py#L422-L482
[manager-reset]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/sensor_manager.py#L277-L312
[sensor-cam-cache]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py#L244-L272
[jit-read]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/jit_render.py#L1240-L1260
[seg-decode]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer_context.py#L1245-L1262
[ray-render]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/raytracer.py#L830-L833
[batch-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/batch_renderer.py#L273-L345
[batch-render]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/batch_renderer.py#L346-L444
[cam-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L145-L198
[raster-render]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer.py#L70-L151
[cam-pointcloud]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L502-L582
[seg-map]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer_context.py#L34-L57
[seg-key]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer_context.py#L252-L260
[seg-property]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/visualizer.py#L312-L321
[batch-key]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/batch_renderer.py#L44-L64
[normal-vert]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/shaders/mesh_normal.vert#L1-L35
[normal-frag]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/shaders/mesh_normal.frag#L1-L13
[normal-pass]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/offscreen.py#L146-L158
[cam-attach]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L213-L268
[sensor-raster]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py#L422-L559
[sensor-ray]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py#L582-L715
[sensor-batch]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py#L741-L824
[camera-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/camera.py#L1-L152
[renderer-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/renderers.py#L1-L137
[camera-reject]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L247-L263
[patterns]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/raycaster.py#L198-L285
[ray-sensor]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/raycaster.py#L511-L702
[depth-sensor]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/depth_camera.py#L11-L31
[ray-context]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/raycaster.py#L235-L347
[ray-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L610-L668
[ray-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/raycast_qd.py#L798-L900
[ray-hit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/raycast_qd.py#L687-L795
[contact-filter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L192-L218
[contact-bool]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/contact_force.py#L147-L214
[force-raw]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/contact_force.py#L294-L336
[joint-sensor]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/joint_torque.py#L25-L86
[actuator-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3049-L3085
[imu-kernel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/imu.py#L24-L77
[tactile-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py#L273-L395
[kin-taxel]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/kinematic_tactile.py#L1184-L1277
[prox-return]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L679-L754
[elastic-return]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L2186-L2200
[taxel-force]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/kinematic_tactile.py#L246-L300
[taxel-prefilter]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/kinematic_tactile.py#L85-L177
[tactile-depth-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py#L157-L212
[elastomer-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py#L396-L515
[elastic-build]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py#L1944-L1975
[tactile-errors]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py#L54-L242
[surface-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L571-L609
[surface-impl]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/surface_distance_probe.py#L33-L112
[temperature-options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py#L402-L472
[temperature-impl]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py#L664-L791
[visualizer-init]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/visualizer.py#L32-L108
[raster-platform]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer.py#L14-L42
[cam-pose]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L584-L651
[cam-intrinsics]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py#L1027-L1037
[surface-points]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/surface_distance_probe.py#L455-L465
[sensor-mount]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py#L593-L627
