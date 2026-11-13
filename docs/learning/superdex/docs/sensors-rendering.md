# E4 传感器、渲染与可视化

本章完成 A6。先读 [E1 坐标、状态与时间](modeling-state-time.md)；力观测还需 [E3 接触与求解](contact-solvers-forces.md)。需要会读刚体变换、矩阵和数组形状；不要求运行场景。应用路线先读第 1–4、7–10 节，源码路线再追第 5–6 节的投影、readback 与流水线。

版本固定为 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。本章是源码阅读与接口核对，**没有 import 原生包、启动 GUI/渲染器、仿真或采集图像**；最小例子只做语法检查。完整身份见 [sources.json](sources.json)，验收见 [E4 记录](validation-e4.md)。这里的接口存在性不证明任何历史 DexLab 二进制具有相同能力。

## 1. 先确定谁生成观测

“传感器”至少有三层含义：物理真值或几何查询、带安装位姿的组件、宿主生成的图像或设备信号。把它们都命名为 observation 不会自动统一更新时间、单位或所有权。

| 层与对象 | 固定源码中的职责 | 不能由此推断 |
|---|---|---|
| Physics `Scene` / `Actor` | 状态、接触力、SDF 与点到面距离；查询支持条件各异 | 所有查询都是硬件传感器，或都会在 getter 时重新计算 |
| Robotics `SensorBase` / `CameraSensor` | 组件生命周期、父级安装变换、相机参数；Camera 的 `reset()` 无状态可清 | `scene.step()` 会生成 RGB/depth，或存在 `camera.capture()` |
| Python `Viewer` | 通过 Polyscope 显示物理/视觉几何、辅助图形、UI 与截图 | GUI 截图就是已经标定的机器人相机 |
| Python `MochiRendererViewer` | 向独立 TCP 服务同步 actor/mesh，请求 named camera 的 lit 图像 | 客户端自动启动服务，或 Python 层暴露 C++ renderer 的全部能力 |
| C++ `mochi_renderer` | Filament 场景、窗口 presentation 与离屏 observation camera、像素读回 | 内核求解器会调度它，或 offscreen 不再需要图形后端 |
| Python `UnrealCVViewer` | 向运行中的 UE/UnrealCV 宿主同步状态并获取图像 | Python 依赖版本能证明 UE/plugin 二进制身份 |
| Studio | 资产编辑、场景 viewport、选择高亮和图形资源生命周期 | viewport 高亮就是语义分割，或 Studio 与 Physics 有同一套传感 API |

依据：[CameraSensor][sensor-camera]、[SensorBase][sensor-base]、[Polyscope viewer][viewer]、[TCP viewer][tcp-viewer]、[renderer API][renderer-api]、[UE viewer][ue-viewer]、[Studio renderer][studio-renderer]。公共 Robotics 内建传感器注册路径仅注册 Camera；内部构建分支另有注册入口，不能把内部能力补写成公开可用的力/触觉组件。[组件注册][context]

## 2. 能力与输出契约矩阵

“未暴露”限定到下表指明的固定公开路径，不声称整个生态永远不支持。

| 观测 | 可核实入口与输出 | frame / 单位 / 时点与限制 |
|---|---|---|
| RGB/RGBA：Polyscope | `Viewer.render()` 在 `offscreen=True` 时返回截图；`take_screenshot()` 转发 `ps.screenshot_to_buffer()` | 锁定参考依赖 2.5.0 下是 `uint8 (H,W,4)` RGBA，不是别名注释所写的 RGB；实际 framebuffer 尺寸可与请求窗口尺寸不同 |
| RGB/RGBA：Mochi | C++ `RenderResult.pixels` 是 `W*H*4` 字节；Python `render()` 解码为 `uint8 (H,W,C)`，当前 C++ 输出 C=4 | 显示颜色，无米/牛顿量纲；通道头由服务返回，Python 不强制 C=4，应用应校验；时间由所用流水线决定 |
| RGB：UE | `UnrealCVViewer.render()` / `take_screenshot()` 的 lit 路径通常解码 `uint8 (H,W,3)` RGB | PNG 转 RGB，NPY 三/四通道做 BGR(A)→RGB；异常/缺失相机可能返回 None 或缺少字典键，不能补黑图冒充有效帧 |
| depth | Mochi `ImageFormat` 仅 RGBA8；内部 DEPTH32F 是 depth attachment，无本章所核对的深度观测读回 API | 没有可声明的公开 `(H,W)` 米制深度输出。UE client 接受 `mode="depth"`，但服务端单位、轴向深度/射线距离及无效值尚未在本章固定 |
| segmentation | Mochi 上述 readback 无分割类型；UE client 接受 `object_mask` 文本请求 | 颜色 mask 不等于 class ID/instance ID；label 映射、遮挡、抗锯齿和宿主响应必须另核，Studio 高亮不能替代 |
| 射线 | `mochi::RayCast`（mochi_core 库） 有 C++ AABB/triangle/BVH 交点工具 | 不是公开 Physics Python Scene 的 LiDAR/raycast sensor；需自备几何、坐标变换、遍历/过滤和时序；返回 t 并非总是米 |
| 点到面距离 | `Actor.get_points_distance_to_surface(points_world, out_distances)`；N 个 3D 输入、N 个标量输出 | 输入 world m、输出 signed m；即刻几何查询，需 collider，soft mapping/PointCloud 等有不支持分支 |
| 接触采样 SDF | 注册 `SDF_DISTANCES` 后 `get_sdf_distances()`；索引 N、位置 `(N,3)`、距离 N、梯度 `(N,3)` | world m、signed m、world 无量纲梯度；N 是返回采样点数，不是像素数；步后缓存，发散可缺失/陈旧 |
| 力/力矩 | `get_contact_force_world()` / `get_contact_torque_world()`、contact/node 查询 | world N / N·m；力矩绕 actor COM；步后装配数据，详见 E3；非自动硬件 F/T 信号 |
| 触觉 | 公开注册表未提供内建 tactile sensor；接触采样点/力可作为输入 | 没有可宣称的触觉单元网格 shape、压力图、噪声或触觉图像契约；需另定义接触到传感信号模型 |

矩阵证据：[Physics Python stub][physics-stub]、[距离实现][actor]、[Ray 工具][ray]、[图像类型][render-types]、[离屏 target][offscreen-target]、[UE capture_image][ue-client]。不是“文档没写所以一定没有”：Camera 无图像是头文件明确声明，Mochi 无 depth readback 是枚举和实际读回分支共同限定，ray/触觉则是公开接口/注册范围审查。

Polyscope 的返回值特别值得追到底：[SuperDex lock][lock] 解析到 2.5.0；本章另固定官方 `nmwsharp/polyscope-py` 的 v2.5.0 提交 `8aa43f5d65d9ef54a415451c7caeebb4c0b6fde7`。[Python screenshot][ps-python] reshape 为 `(h,w,4)` 并默认垂直翻转，[C++ binding][ps-cpp] 使用 `unsigned char`。再沿该提交的 git submodule 固定 `nmwsharp/polyscope@b1f5ae82488b82d91a61d7d8c81882989216056d`：[原生头文件][ps-header]明确为每通道 1 byte 的 RGBA，[截图实现][ps-native]先绘制再读回 framebuffer；调用截图本身不推进 Physics。这个翻转可产生负行 stride；需要拥有且连续的内存时显式 `.copy()`。这证明所选源码接口，不等于验证本机 wheel 或实际 GPU 输出。

## 3. CameraSensor 的安装位姿与参数

### 3.1 从 link frame 到 world frame

令 ${}^{W}T_L$ 把 link 坐标变换到 world，${}^{L}T_S$ 是 `get_parent_from_sensor()`，则

$$
{}^{W}T_S={}^WT_L{}^LT_S,\qquad p_W=R_{WL}(R_{LS}p_S+t_{LS})+t_{WL}.
$$

旋转无量纲，平移与位置以米计。`SensorBase::GetWorldTransform()` 直接取 actor 的 `GetRootTransform()` 再右乘安装变换；actor 已是 world-resolved，不能再乘一次 Bot/Scene 的世界变换。无 actor 时返回安装变换本身，因为 scene-root→world 暂按单位变换处理。[实现][sensor-impl]

`get_actor() is None` 同时可能表示有意创建的 scene-level sensor，或原所属 actor/Scene 已销毁。不能见到 None 就默默把原腕部相机降级为 world 相机；调用者须记住原归属。Physics context 要活得比 Robotics context 更久；组件、Scene 和 renderer 是不同生命周期。[Robotics stub][bots-stub]

### 3.2 参数不是已经完成的 renderer 配置

| Python 字段 | 单位/含义 | 应用接线责任 |
|---|---|---|
| `image_width`, `image_height` | px，0 表示采用宿主默认 | 解析默认之后必须为正整数；没有生成像素 buffer |
| `fov_vertical_deg` | 垂直 FOV，deg | 与 horizontal FOV 分清；解析后应在 (0,180) |
| `near_clip`, `far_clip` | m；0 是默认占位 | 实际需 `0 < near < far`，默认值取决于 renderer |
| `look_at` | world 目标点 m，固定相机用途 | 不是父 frame 局部方向 |
| `offset_local`, `forward_axis`, `up_axis_local`, `look_distance` | EE 局部偏移 m、局部方向、局部方向、前方距离 m | 宿主必须解释和组合；方向要非零且不共线 |
| `name` | 参数中的名称 | 不等于组件 `get_name()`，也不自动成为唯一 renderer camera ID |

[参数头文件][sensor-camera]和 [cpp 构造/参数读写][sensor-cpp]不做 RGB 计算或投影有效性验证。零值被保存，不会在 `get_params()` 时填好 Filament 默认值；`set_params()` 也只是赋值。不要从参数对象凭空推导 `compute_signal()` 或 `get_image()`。

对腕部 look-at 接线，一种明确的应用约定是用 EE 位姿计算 `eye_W = t_WE + R_WE offset_local`、`target_W = eye_W + look_distance R_WE normalize(forward_axis)`、`up_W = R_WE normalize(up_axis_local)`。这是**应用公式**；不声称 CameraSensor 会自动执行，也不能和 `parent_from_sensor` 的位移重复叠加。若宿主仅支持固定 world-up 的 look-at，任意腕部滚转需完整 orientation 接口。

### 3.3 原生最小阅读例

[read_camera_metadata.py](../examples/read_camera_metadata.py) 对调用者持有的有效 CameraSensor 读取原生参数、安装变换和 world pose，复制成普通 Python 值；调用者提供 `sample_time_s` 与 `parent_kind`，明确它们是应用元数据。它不创建 Scene，不 step、不 render，也不会把参数记录命名为 image observation。已做 AST 检查，未执行。

先检查 `get_actor()` 与预期归属，再读取 world pose；返回的 `world_from_sensor_xyzw` 保留原生 xyzw。`sample_time_s` 必须是读取时对应的应用物理状态时间，不能以当前墙钟或预计的相机曝光时间代替。并发步进期间调用这些 getter 没有获得跨字段原子快照；示例要求应用保持状态不变。

## 4. 物理观测、距离与触觉的组合边界

### 4.1 两种“距离”不是同一个查询

`get_points_distance_to_surface()` 读取当前 actor root pose，把给定 world 点转为 actor 局部，再按 collider 分派。它检查输入/输出长度相同，支持 Sphere、Box、Mesh、Plane、Sdf；PointCloud/None 不支持，mapped soft SDF 明确报错。SDF 未生成好时会等待。对于 grid SDF，包围盒外值仅是基于三角不等式的上界，不能当作精确测距。[实现][actor]、[API][physics-stub]

`SDF_DISTANCES` 则在接触计算链里记录本 actor 接触采样点到相邻表面的 signed distance 与梯度；注册要在步前，步后读取。同样写“距离”并不使它成为从相机逐像素发射的 range image，也不保证包含所有表面。空间采样与 far-SDF 配置决定内容。E3 的失败状态与缓存生命周期同样适用。

### 4.2 Ray 工具的数学契约

[Ray][ray] 写作 $r(t)=o+t d$，C++ `RayCast` 返回 `optional<RayHit>`：无交点是空；命中含 `t`、intersection 和 primitive index。只有 d 为单位方向时 t 才是沿射线的米制距离；若 d 长度为 2，则同一物理距离的 t 减半。AABB 内部起点按接口约定返回 t=0。三角形/BVH 在同一坐标系下计算，不替用户选择 Physics actor、视觉 mesh 或碰撞 SDF。[实现][ray-impl]

公开 Physics stub 没有 Scene `raycast` 传感器入口。把这些底层工具组织成 LiDAR 还需扫描角、波束时间、可见性、最近命中、材质回波、无效值与输出 frame；本章不新建这类 wrapper，也不把底层几何函数包装成已存在的 native sensor。

### 4.3 力数据怎样变成传感器量

接触总力是求解器输出，F/T 传感器还需安装坐标、测量参考点、包含哪些载荷、标定和采样模型。对 world 中绕 COM 点 C 的 wrench，转到安装点 S：

$$
F_S=R_{WS}^{T}F_W,\quad
\tau_S=R_{WS}^{T}\left[\tau_C+(p_C-p_S)\times F_W\right].
$$

F 单位 N，力矩 N·m，位置 m。它只转换已有接触 wrench；不会自动加上重力、惯性、执行器反力或传感器自身质量。约束反力也不能和接触力无条件混加。时间窗口平均 $\bar F=\sum F_k h_k/\sum h_k$ 是指定分段常值近似，不能把 solver iteration 当采样周期。[E3 力观测](contact-solvers-forces.md)

触觉压力的教学关系是 $p_i\approx (F_i\cdot n_i)/A_i$（Pa），要求 F 是该小面的净法向力、面积 A>0 且法向方向约定一致。原生 contact point 的 force 已乘空间积分权重；不能再次乘面积。rod 的一维积分权重不是 m²，不能直接变成皮肤压力。触觉单元网格、弹性传递、饱和、噪声、带宽和视觉触觉材质都需单独模型；公开 Camera/接触查询没有补齐这些模型。

### 4.4 关节状态与 IMU 也需区分真值和传感模型

E1 的关节位置/速度、root/COM pose getter 可提供本体状态真值；有这些字段不代表有编码器量化、延迟或噪声。公开内建 sensor 注册表同样没有 IMU 组件。若应用自行构造理想 IMU，陀螺量是安装 frame 的角速度，$\omega_S=R_{WS}^T\omega_W$（rad/s）；理想加速度计比力为 $f_S=R_{WS}^T(a_S-g_W)$（m/s²），不是直接读世界重力。

对刚性固定在 COM 偏移 r 处的传感器，world 中 $a_S=a_C+\alpha\times r+\omega\times(\omega\times r)$。假设安装偏移不随刚体变形，不含杆臂相对运动；从离散速度差分求 a/α 还需要时间间隔、滤波及 reset 边界。这里解释物理组合责任，不宣称提供原生 IMU API，也未运行差分采样。

## 5. 图像投影、颜色和坐标

### 5.1 用 pinhole 公式理解参数，避免把 depth 当距离

在 **OpenCV 相机 frame**（x 右、y 下、z 前）的理想针孔假设下，Z>0，

$$
\begin{bmatrix}u\\v\\1\end{bmatrix}
=\begin{bmatrix}f_x&0&c_x\\0&f_y&c_y\\0&0&1\end{bmatrix}
\begin{bmatrix}X/Z\\Y/Z\\1\end{bmatrix}.
$$

u/v、f/c 用 px；X/Y/Z 用同一长度单位。对于中心主点、方形像素、零 skew 且无 crop 的对称投影，$f_y=H/[2\tan(\theta_v/2)]$，$\theta_v=2\arctan(\tan(\theta_h/2)/(W/H))$。角度进入三角函数前转 rad。Python `CameraCfg.horizontal_fov_deg` 正是按后一式转成服务器 vertical FOV；Robotics 字段已是 vertical，不应再转一次。[TCP viewer][tcp-viewer]、[配置][tcp-cfg]

轴向深度是 Z，射线距离是 $\sqrt{X^2+Y^2+Z^2}$。即使拿到一个浮点 depth buffer，还必须知道投影与编码，才能转为这两者之一。Mochi 当前公开 readback 没有这项输出；本章不提供伪 `get_depth()` 或未经证实的单位换算。

### 5.2 Native renderer 还区分镜头 frame、场景 frame 和资产 frame

`ObservationCamera::UpdateProjection()` 使用 Filament/OpenGL 相机约定（-Z 前、Y 上），与 OpenCV 的 +Z 前、Y 下不同。`SetCameraModel` 提供 fx/fy/cx/cy；`SetTransform` 接的是 camera model pose，不会因为设置内参就自动修正任意外部外参。`LookAt(eye,target)` 内部固定 world up=(0,0,1)，并非支持任意 up 向量的 Robotics 相机接口。[camera 实现][camera-impl]

同一文件对投影 X/Y 作翻转，以补偿注释所述 Vulkan offscreen readback 的 180° 旋转；代码未按 backend 分支，仅据源码不能宣称所有平台朝向都已验收。不要看图像反了就给所有 backend 统一再翻一次。

还有独立的资产兼容约定：[RenderSpace][render-space] 返回 FUR（X-forward、Y-up、Z-right），因固定 GLB 资产历史烘焙约定而保留，不能和 Filament 相机轴混为一谈。Studio [viewport][studio-viewport]在传入相机前调用 editor→renderer converter；Python TCP viewer 则直接发送位置/xyzw，并注释 glTF 修正由服务端负责。不能把任意 Y-up Physics 场景与 Z-up look-at 直接拼起来，再声称所有接口共享统一 world 轴。

### 5.3 畸变是具体实现，不是字段越多支持越全

[OpenCVCameraModel][render-types] 存八个 D 系数，但 renderer 明确仅实现 k1,k2,k3,p1,p2。k4–k6 非零会警告且不参与采样。本提交的 [Distortion shader][distortion] 对归一化坐标 x/y 计算

$$
r^2=x^2+y^2,\quad a=1+k_1r^2+k_2r^4+k_3r^6,
$$
$$
x_d=xa+2p_1xy+p_2(r^2+2x^2),\quad
y_d=ya+p_1(r^2+2y^2)+2p_2xy.
$$

这些量无量纲，采样位置再乘 fx/fy 加 cx/cy。注意具体代码是**以当前输出像素算 x/y，再用上述结果到源纹理取样**，没有一般性的逆畸变迭代；这是所实现的图像重采样方向，不能仅凭结构体写 OpenCV 就宣称与任意标定相机逐像素一致。超出源 UV 范围填黑。0 焦距占位还未解析时不可把公式当有效投影使用。

### 5.4 颜色不是光照真值

RGBA8 的每通道是 0–255 编码值，A 是 alpha，不是 depth 或 segmentation。`SceneViewSettings` 控制 tone mapping、exposure、SSAO、bloom、MSAA 等；[view settings 实现][view-settings]构建 Rec709 / sRGB / D65 输出颜色空间。所获 lit 图像不能直接作线性辐亮度或压力图；改变后处理会改变像素而不改变接触动力学。

视觉 GLB 可覆盖物理 surface mesh；`MochiRendererViewer` 的 `actor_gltfs` 是 actor 名→视觉资产映射，环境 glTF 也是视觉宿主资产，不自动创建 Physics collider。render/碰撞几何差异本身不是接触引擎异常。资产路径须对服务端可读，客户端本地存在不等于远端能够加载。[TCP mesh 同步][tcp-viewer]

## 6. 源码中的帧生成与延迟

### 6.1 C++ observation camera

沿 [MochiRenderer][renderer-impl]→[ObservationCamera][camera-impl]→[OffscreenRenderTarget][offscreen-target] 读：

1. `MochiRenderer::Create` 建立 Filament engine/scene/resource manager；DEFAULT 分支在 macOS 选 Metal，其余选 Vulkan，失败可返回 nullptr。
2. `CreateObservationCamera` 创建 named camera、离屏颜色/深度 target 和无窗口 swap chain；颜色 RGBA8 加 BLIT_SRC 用于 GPU→CPU，depth attachment 是内部遮挡资源。
3. `RenderFrame` 更新 attached camera，`beginFrame` 成功才 render/endFrame；它不是 `Scene.step()`。如果 beginFrame 跳过，之后读回的“有效字节”不能单独证明有新物理帧。
4. `ReadPixels` 请求 RGBA UBYTE，`flushAndWait` 后等待 callback；返回拥有字节的 `RenderResult`。`IsValid()` 只检查非空和正尺寸，不检查时间戳、全长/通道正确性或内容是否新鲜。

| `PipelineMode` | 固定实现的返回顺序 | 读数据时的后果 |
|---|---|---|
| `Synchronized` | 本次 RenderFrame 后阻塞读回 | 可与本次显式同步给 renderer 的状态对齐，但还要检查渲染成功/宿主同步 |
| `OneFrameDelay` | 返回缓存的上次结果，再渲染并保存本次；第一次为空 | 第 n 次调用返回第 n-1 次生成的图，不是自动 t_n 图 |
| `MaxPerformance` | 三个 ring slot 轮换；前三次无旧结果，第四次返回首次 slot 的结果 | 无模式切换时源码是三次调用前的图；名字不构成吞吐结论，当前每次仍 flushAndWait |

以上按持续使用同一模式/相机/分辨率分析。切换模式和 reset 没有通用“把所有旧帧标新”的保证；这些缓存是 renderer 状态，不属于 Physics snapshot。宿主必须丢弃或显式标识遗留结果。

异步也要分层：`ObservationCamera::RenderAndReadbackAsync()` 只排队并返回 future，调用者负责提交/处理 callback；顶层 `MochiRenderer::RenderAndReadbackAsync()` 会把多个 camera 排队后调用一次 `flushAndWait()`，再返回 future map。不能仅凭函数名推断调用立刻返回、与求解完全并行或已获得性能提升。

### 6.2 Python TCP 与 UnrealCV

`MochiRendererViewer.render()` 先收集新删 actor、更新 mesh/transform，再在同一批命令末尾附 `vget /camera/<name>/lit`。多相机结果按名字返回；不存在场景返回 None/空字典，失败相机被省略。解码从响应头读 W/H/C 再 `np.frombuffer`，不带 frame ID 或模拟时间。返回数组基于 bytes，调用者需要可写/独立快照时 `.copy()`。[TCP client][tcp-client]、[viewer][tcp-viewer]

下面是只针对该原生 viewer 的读取片段，**未执行**。前置条件是应用已经配置有效 Scene、独立且版本已核实的服务端、存在的 named camera，且读取过程中不修改物理状态。本片段不建立环境，也不赋予返回图像模拟时间标签；它可能来自服务端流水线的旧帧。

```python
from superdex.physics.viewer.mochi_renderer.mochi_renderer_viewer import (
    MochiRendererViewer,
)


def copy_mochi_frame(viewer: MochiRendererViewer, camera_name: str):
    frames = viewer.render(camera_names=[camera_name])
    if not isinstance(frames, dict) or camera_name not in frames:
        raise ValueError("requested camera did not return an image")
    frame = frames[camera_name]
    if frame.ndim != 3 or frame.shape[2] != 4 or frame.dtype.name != "uint8":
        raise ValueError("this reader requires the reviewed RGBA8 contract")
    if frame.shape[0] == 0 or frame.shape[1] == 0:
        raise ValueError("empty camera image")
    return frame.copy()
```

Python cfg 有 `offscreen` 字段，但这个 viewer 的 `render()` **没有依据它切换路径**；它始终请求图像。`set_paused()` 仅保存布尔值，follow/grid 相关方法是 no-op。构造函数只连接既有服务，且固定公开树中未定位到 `mochi_viewer` 服务端同名实现；本章不编造服务器启动命令，也不把 C++ `PipelineMode` 直接当成这条网络链路的已证明配置。

UE viewer 通过 `CoordinateTransform(source_system, unreal_system)` 变换轴，并在位置上乘 `meters_to_cm`（cfg 默认 100）；姿态转换输出 UE 的 pitch/yaw/roll 度。不要对它已经转换的位置再乘 100。[UE viewer][ue-viewer]、[UE cfg][ue-cfg]

UE 的 `UnrealCVViewer` 则明确实现 `PIPELINED` 与 `SYNCHRONIZED` 两条 lit 路径：前者首次无上一帧，后续拿先前 future，再同步 actor 并启动新 capture；后者更新 actor 后取本次 capture。相机名字需在宿主 spawn 完后 `resolve_cameras()`，不能把客户端名字当作已存在的 UE camera ID。[UE viewer][ue-viewer]、[UE cfg][ue-cfg]

[锁文件][lock]记录 Python `unrealcv` 1.2.0，但并未固定实际 UE 项目、UnrealCV plugin 构建和自定义 `lit_async` / `lit_get_latest` 服务端。客户端能拼出 depth/mask 请求只证明请求能力；它的 PNG 分支无条件转 RGB，NPY 分支对三/四通道做颜色重排、对其它形状直接返回，所以 `capture_image` 的 RGB 注释也不是任意 mode 的完整契约。本章不指定未经证实的深度单位或 mask ID 编码。

## 7. 采样顺序与元数据

应用应在一个不会并发修改状态的边界完成以下逻辑；这是调度示意，不是可运行伪 API：

```text
选定物理状态 x_k 与应用时间 t_k
    → 复制本次状态/步后 force query，记录 solver status
    → 用同一 x_k 更新 renderer 几何和 camera extrinsics
    → 发起第 k 次 capture，保存 capture_id → (t_k, camera, extrinsics, intrinsics)
    → 等待/接收可能属于更早 capture_id 的图像
    → 将图像匹配回生成它的状态，记录接收墙钟和有效性
```

物理步 h、控制周期 H、相机采样周期 Ts、渲染调用间隔和读回延迟不同。若显式每 M 个固定步请求一次，则 Ts=Mh；多相机顺序请求不自动等于同时曝光。`CameraSensor` 没有自动的 sensor period、rolling shutter、噪声、曝光时间与图像时间戳字段。

最少应保存：引擎/source/wheel/backend 身份、模拟时间、capture 序号、request/receive 时间、camera ID、所用内外参、image shape/dtype/channel order、颜色处理、成功/缺失状态、pipeline 模式、物理步是否成功。物理 state reset 不会自动重置外部 UE scene、TCP server 或所有图像缓存；reset 后先作废旧 capture 映射，再由应用完成宿主同步。这里是数据语义先修，完整数据管线仍是 E5。

## 8. GUI、headless 与资源生命周期

**Polyscope。** `ViewerCfg.offscreen=True` 控制截图返回和 UI 分支；`backend` 决定图形初始化，默认空串交由 Polyscope 选择。代码允许 headless backend，不证明当前机器支持任何特定 backend。`Viewer.__init__` 检测 Polyscope 已初始化就报错，多个 viewer 应按其说明分进程。GUI `render()` 在 paused 时继续 tick 并占住应用循环，直到继续/单步/关窗；因此不能把阻塞时长当成物理步时长。优先 context manager 或 finally 调用 `close()`，清 group/structures/callback/logging 并 shutdown。[viewer][viewer]、[backend][backend]

**Native renderer。** C++ API 不依赖窗口系统，presentation target 由宿主可选注入，observation 离屏资源仍依赖 Filament/GPU backend。renderer 拥有相机、场景和 engine，析构先清相机再清底层资源；异步 readback 未完成前不能释放其依赖。固定 [CMake][renderer-cmake]链接 Filament 等库；本章以同源树中 vendored Filament 文件身份固定依赖，不猜独立发行版或安装驱动版本。[vendored build][filament-build]

**TCP / UE。** `close()` 释放自己同步的 actor/环境或隐藏宿主 actor，并断开连接；不等于关闭外部服务。Mochi client 的连接 timeout 在连上后被改成阻塞 I/O，不能据 `connection_timeout` 保证每次 capture 都在该秒数内返回。其 close 未发送 camera destroy，重复使用相同 server/camera 名需检查残留资源。UE close 尝试 drain future 后断连；应用仍应管理宿主进程。[TCP client][tcp-client]、[viewer][tcp-viewer]、[UE viewer][ue-viewer]

**Studio / Debugger。** [Studio README][studio-readme]将其定义为需要 GPU/display 的桌面资产工具。仓内 `run_studio_linux_headless.sh` 是 Xvfb 加内部 Buck target 的脚本，不能当作公开 wheel 已保证可用的 EGL 传感采集方案；Xvfb 提供虚拟显示，不删除 GUI/图形依赖。[脚本][studio-headless] Studio viewport 颜色读回是 RGBA UBYTE，高亮 overlay 有独立 depth，可能显示被其他几何挡住的选择对象，不能作为语义 mask。[renderer][studio-renderer] `physics.debugger.attach()` 则启动/连接独立 debugger 并可能暂停 native step，它不是 observation-camera readback API。[debugger][debugger]

## 9. 易错点与定位入口

| 症状或错误理解 | 源码支持的解释 / 先查项 |
|---|---|
| CameraSensor 有参数却拿不到图 | 它无 ComputeSignal；核实宿主、render camera 和采集 API |
| 宽高写了 640×480 却数组判断失败 | cfg 是 (W,H)，array 是 (H,W,C)；Polyscope 用 framebuffer size；核对 RGBA/RGB |
| 截图应为 RGB，但出现四通道/负 stride | Polyscope 2.5.0 是 RGBA 且默认垂直翻转；需要时复制，不以注释替代实现 |
| 接触距离看起来像 depth | SDF 是接触点到表面 signed distance，既非像素轴深度，也非 ray range |
| 将 depth PNG 转 RGB 再除 100 | 未核实宿主编码/单位；颜色解码可能已经丢失原始深度 |
| 腕相机随 link 多旋转/平移一次 | actor 已 world-resolved；核对 parent_from_sensor 与 EE offset 是否重复 |
| 图像与同一行关节状态错位 | 检查 renderer pipeline、首次空帧、capture ID 与 reset 遗留缓存 |
| 画面存在物体，Physics 却没有接触 | 视觉 glTF 不自动成为碰撞几何，检查 actor/collider 与 transform 映射 |
| 力 query 为零，认定传感器无接触 | 检查注册、采样阶段、solver NONE/STOPPED/DIVERGED；参考 E3 |
| 开了 offscreen 就不再依赖 GPU/服务 | 只改变展示/读回路径；仍需具体 backend 和服务生命周期 |
| MaxPerformance / Async 名称意味着更快 | 固定实现含 flushAndWait，性能未运行验证；返回数据还有帧延迟 |
| mask 颜色就是语义类别 | 需稳定 ID→语义映射；颜色、selection overlay 与 class ID 是不同表示 |

## 10. 带答案的阅读练习

1. **`CameraSensor.reset()` 能清除上次 RGB 吗？** 不能。它只持参数和姿态、reset 空实现，没有 RGB buffer。外部 renderer 缓存由其宿主管理。
2. **已知 W←L 与 L←S，为什么不能再左乘 scene spawn pose？** W←L 已包含层级世界变换；再次乘会重复。当前 actor-less 路径则假设 scene root→world 为单位变换，需分别说明。
3. **参数 `name` 与组件 `get_name()` 相同吗？** 不保证；后者实例名也不要求唯一。renderer camera ID 的唯一性与映射由应用确定。
4. **为什么 `fov_vertical_deg=0` 不表示零视场相机？** 它是“采用默认”的元数据占位；实际 renderer 解析后才具有合法投影，不能直接放入 tan 公式。
5. **800×600、horizontal FOV=90° 时 vertical FOV 是多少？** $2\arctan(600/800)\approx73.74°$。Robotics vertical 字段已是后者，不应再次转换。
6. **Polyscope wrapper 注释 RGB，为什么本章仍写 RGBA？** `take_screenshot()` 原样转发；固定 2.5.0 Python reshape `(h,w,4)`，C++ buffer 是 unsigned char，且默认垂直翻转。
7. **颜色 target 旁有 DEPTH32F，能调用 Mochi get_depth 吗？** 不能推导这个 API。固定 RenderResult/ImageFormat 和 ReadPixels 仅走 RGBA UBYTE；内部 attachment 与公开观测不同。
8. **point distance 与 raycast 差在哪？** 前者求点到某 actor 表面的 signed scalar，后者沿 o+t d 找交点；N 点 SDF 没有针孔像素对应关系。d 未归一化时 ray t 不是距离。
9. **用读取到的 COM wrench 构造腕 F/T，遗漏什么会错？** 需旋转到传感 frame 并将力矩参考点从 COM 移到传感位置，还要说明只有接触载荷，不自动含重力/惯性等。
10. **第 4 次连续 MaxPerformance 调用拿到谁的图？** 三槽轮转下拿到第 1 次那个槽的结果，前三次为空；不能直接标第 4 次物理状态。模式切换另行处理。
11. **顶层 Async 调用返回 future，为什么仍可能阻塞？** 源码排队多 camera 后统一 flushAndWait，确保 callback 送达；只有底层 camera async 把 flush 责任交给调用者。
12. **UnrealCV client 接受 depth 参数，是否已证明米制深度？** 没有。服务端构建/编码未固定；PNG 分支还统一 convert RGB。只能证明客户端构造请求。
13. **GUI paused 时 `render()` 不返回，是否 solver 不收敛？** 不一定，Polyscope paused 循环在主动 tick UI；debugger 也可暂停 step，须分开定位。
14. **相机设置 k4 后无合理畸变，源码怎么解释？** 字段储存但未用于 shader，只有五参数模型；还需核对其输出像素→源纹理的采样方向，不能保证通用标定模型一致。
15. **headless_test.cpp 名字能证明当前 GPU 渲染成功吗？** 不能；所读测试主要检查 RenderResult、枚举与 producer/consumer buffer，且本章没有运行它。源码中的测试名不是设备运行证据。[测试来源][headless-test]
16. **为什么没给出触觉 tensor API？** 固定公开注册表没有该内建组件，contact force 只提供物理输入。触觉单元、面积、带宽、标定和输出 shape 是尚未实现的传感模型责任，不能补造原生接口。

至此 A6 的公开 API、数学解释和能力缺口已覆盖；数据导出/批量环境/学习接口留 E5，特色与扩展仍按 E6。后续实验引用 [DexLab](https://github.com/huangkiki/Dexlab)，不在本仓另建图像/触觉 benchmark。

[sensor-camera]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/sensors/camera_sensor.h
[sensor-base]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/include/superdex_robotics/sensors/sensor_base.h
[sensor-impl]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/sensors/sensor_base.cpp
[sensor-cpp]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/sensors/camera_sensor.cpp
[bots-stub]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/pybind/stubs/public/superdex_robotics/bots/__init__.pyi
[context]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/core/context.cpp
[physics-stub]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[actor]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_actor.cpp
[ray]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/geometry/ray.h
[ray-impl]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/geometry/ray.cpp
[viewer]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/viewer.py
[backend]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/backend.py
[debugger]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/debugger.py
[lock]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/uv.lock
[ue-viewer]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/unrealcv/unrealcv_viewer.py
[ue-cfg]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/unrealcv/unrealcv_viewer_cfg.py
[ue-client]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/unrealcv/unrealcv_client.py
[tcp-viewer]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/mochi_renderer/mochi_renderer_viewer.py
[tcp-cfg]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/mochi_renderer/mochi_renderer_viewer_cfg.py
[tcp-client]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/viewer/mochi_renderer/mochi_renderer_client.py
[render-types]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/include/mochi_renderer/types.h
[render-space]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/include/mochi_renderer/render_space.h
[renderer-api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/include/mochi_renderer/mochi_renderer.h
[renderer-impl]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/src/mochi_renderer.cpp
[renderer-cmake]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/CMakeLists.txt
[camera-impl]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/src/camera.cpp
[offscreen-target]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/src/offscreen_render_target.cpp
[distortion]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/materials/Distortion.mat
[view-settings]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/src/view_settings.cpp
[headless-test]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_renderer/test/mochi_renderer_headless_test.cpp
[filament-build]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/third_party/filament/CMakeLists.txt
[studio-renderer]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_studio/src/rendering/renderer.cpp
[studio-viewport]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_studio/src/rendering/viewport.cpp
[studio-readme]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_studio/README.md
[studio-headless]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_studio/run_studio_linux_headless.sh
[ps-python]: https://github.com/nmwsharp/polyscope-py/blob/8aa43f5d65d9ef54a415451c7caeebb4c0b6fde7/src/polyscope/core.py#L84-L95
[ps-cpp]: https://github.com/nmwsharp/polyscope-py/blob/8aa43f5d65d9ef54a415451c7caeebb4c0b6fde7/src/cpp/core.cpp#L110-L113
[ps-header]: https://github.com/nmwsharp/polyscope/blob/b1f5ae82488b82d91a61d7d8c81882989216056d/include/polyscope/screenshot.h
[ps-native]: https://github.com/nmwsharp/polyscope/blob/b1f5ae82488b82d91a61d7d8c81882989216056d/src/screenshot.cpp
