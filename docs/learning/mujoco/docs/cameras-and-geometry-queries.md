# 相机与几何查询：像素、射线和接触各问什么

本课属于 A6，先修[建模与坐标](modeling-and-frames.md)、[传感与采样](sensors-and-sampling.md)。固定 MuJoCo 3.15.0 源码；公式默认 m–kg–s、列向量。目标是分清模型相机、可视化相机、投影 sensor、ray sensor 和渲染深度的空间契约，避免把同名 depth 当作相同测量。

## 1. 相机有三个对象层次

`mjModel` 中 camera 是 MJCF 编译结果，拥有 body/target/mode、pos/quat、fovy、projection、resolution、intrinsic 等参数；`mjData.cam_xpos/cam_xmat` 是该状态下的世界 pose。camera 可以随 body、跟踪 body/CoM 或朝向目标，不能永远把声明的局部 quaternion 当最终外参。物理位置计算更新这些 pose。

`mjvCamera` 是可视化的抽象选择器：FREE、TRACKING、FIXED、USER。FIXED 的 fixedcamid 选择模型 camera；FREE/可视化 TRACKING 在模型 camera 数组之外。`mjvGLCamera` 才是渲染低层 pose/frustum，场景内含左右眼两个，非立体模式会合成中间视点。因而“viewer 当前相机”和名为 top 的模型 camera 不必相同。[模型字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L497-L513)、[可视化相机层次](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/visualization.rst#L123-L166)。

MuJoCo camera 的 **−Z 向前、+Y 向上、+X 向右**；site rangefinder 却沿 site **+Z**。设 R 为 `cam_xmat.reshape(3,3)`、C 为 cam_xpos，世界点 P 的相机坐标为：

$$
P_c=R^T(P-C)=(X,Y,Z)^T,\qquad z=-Z.
$$

在前方需要 z>0。这是 MuJoCo 相机坐标，不能直接贴上视觉库的 +Z forward/+Y down 标签；转换外参时必须转换轴，而不只是转置矩阵。相机到世界是 R，世界到相机才是 Rᵀ。

## 2. 居中透视相机的像素与长度

先限定 **perspective、fovy、无显式 sensorsize/intrinsic、居中主点**。W/H 是模型 camera.resolution，用于原生相机传感器。fovy 总以度给出，不受 compiler.angle 影响；投影像素原点在左上，u 向右、v 向下。方形像素下：

$$
f_x=f_y={H\over 2\tan(\mathrm{fovy}\,\pi/360)},\quad
u=f_x{X\over z}+{W\over2},\quad
v=-f_y{Y\over z}+{H\over2}.
$$

fx/fy 单位 pixel，X/z 无量纲；(col,row) 像素中心对应 `(col+.5,row+.5)`。反投影的未归一化局部方向是：

$$
\tilde d_c=\left({col+.5-W/2\over f_x},\ -{row+.5-H/2\over f_y},\ -1\right),
\quad d_w={R\tilde d_c\over\|\tilde d_c\|}.
$$

射线为 C+ρd_w，ρ 是距离/range；轴向深度 z=ρ·(−d_c,z)（此处 d_c 是归一化方向）。离光轴越远，相同 z 的 range 越大。对于此居中透视模型：

$$
\rho=z\sqrt{1+((u-W/2)/f_x)^2+((v-H/2)/f_y)^2}.
$$

不满足这些相机假设时应重建实际 frustum/射线，不应机械使用这个公式。[像素射线实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_util_misc.c#L499-L539)、[fovy/内参分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L902-L939)。

## 3. resolution、output、intrinsic 的不同职责

| 参数/数组 | 本版意义 | 不能推出的结论 |
|---|---|---|
| `camera.resolution="W H"` | 模型记录的像素分辨率；camprojection 和 camera rangefinder 使用它 | 不会自动把 `Renderer(height,width)` 改为这个尺寸 |
| `camera.output` | 支持图像类型的元数据位标志 | 不调用 renderer、不自动填 sensordata、不是后台采集任务 |
| `camera.fovy` | perspective 为度；orthographic 为全高长度 | orthographic 的45默认长度通常不适合小场景 |
| `sensorsize` | 开启物理长度内参，fovy 被内参路径取代 | 长度单位不能混 mm 和 m |
| `focal/focalpixel` | 两轴焦距，长度或 pixel | 像素值优先的具体编译处理见源码，不在读数时二次缩放 |
| `principal/principalpixel` | 相对图像中心的偏移 | 不要直接把它当传统 K 的绝对 cx/cy |
| `vis.global.offwidth/offheight` | classic offscreen framebuffer 容量 | 与 camera.resolution 是不同存储/生命周期 |

规范及默认值见 [XML camera](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L3153-L3214)，原生编译见 [camera intrinsic](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L4436-L4489)。渲染容量见下一课。

### 固定版本里三个相机路径不完全一致

这不是可以忽略的“数值误差”：

- **camprojection** 的 [cam_project](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L280-L314)只用 focal/sensorsize 或 fovy，固定加 W/2,H/2；没有读 principal 偏移，也没有 projection 类型参数，因此不能视为任意正交/偏心相机的通用投影函数。
- **camera rangefinder** 的 [mju_camIntrinsics](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L902-L937)在显式 sensorsize 分支中，把 intrinsic[2:4] 缩放后直接作为 cx/cy 传给像素射线函数，而编译器储存的是主点偏移，未在此分支加 W/2,H/2。本课不替上游代码补这个中心偏移，也不声称它与渲染自动像素对齐。
- **orthographic rangefinder** 的 [mju_camPixelRay](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_util_misc.c#L520-L539)在两个轴都用 `fovy/2` 乘归一化像素偏移；渲染 [frustum 构造](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_vis_visualize.c#L564-L580)保留竖直 fovy，横向由[视口比例](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/render/classic/render_gl3.c#L780-L822)决定。因此非方形视口也不应默认两条路径范围一致。

classic 渲染的 [getFrustum](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_vis_visualize.c#L442-L451)实际使用 principal 构造左右/上下范围。应用若依赖相机间像素严格对应，需要明确选择路径、尺寸和内参，并在以后获得运行授权时专门核验。本文只确认上述源码分支，未运行成像标定，也没有给上游提交 bug 修复。

## 4. camprojection 与 rangefinder

`camprojection` 输出指定 site 的2个像素坐标，POS阶段计算。它没有遮挡检测，不裁到图像矩形，镜头后方点也会被除法投影；z≈0 时还有防止极小除数的分支。任务中至少区分前方、画幅内、无遮挡三件事；2D 坐标落在图内只解决其中一项。[文档](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L7497-L7534)和[实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L280-L314)。

rangefinder 必须选择 site 或 camera。site只有一条+Z射线；camera 按 row 外循环、col 内循环排列 H×W 条。默认 `data="dist"`，可按 `dist dir origin point normal depth` 固定顺序组合。每像素字段连续，sensor_dim=WH×字段总宽；site令WH=1。[MJCF契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L7414-L7495)、[运行分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L545-L638)、[编译维度](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_api.cc#L1901-L1913)。

| 字段 | 宽度 / 单位 | 命中 | 未命中 |
|---|---|---|---|
| dist | 1 / m | 从射线原点沿单位方向的距离 | −1 |
| dir | 3 / 无量纲 | 世界单位方向 | (0,0,0)，不能据此恢复未命中射线 |
| origin | 3 / m | 世界射线原点 | 仍写真实原点 |
| point | 3 / m | 世界交点 | (0,0,0) |
| normal | 3 / 无量纲 | 世界表面向外法向 | (0,0,0) |
| depth | 1 / m | camera 为 `−(P−C)·R[:,2]`；site 为 dist | −1 |

只有有效标记/距离判断后才能使用交点；零坐标本身不是无效哨兵，因为真实世界原点也可被击中。正交 camera 的各射线原点不同，不能从相机中心与交点直接求 dist。上述字段由 [fill_raydata](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L468-L516)写入。

原生 rangefinder 对 geom 查询，并排除所属 **body id** 的 geom，不是整个机器人或整个 weld subtree。camera/site若直接属于 world，会排除 world 上的地面；将它装在明确的 mount body 上会改变这一筛选。rangefinder 传 `geomgroup=NULL`，所以 viewer 里关掉某一组显示不使该组从读数消失。透明排除按 material 存在与否选用其 alpha 或 geom alpha，不是两个 alpha 无条件相乘；详见下一节。

## 5. 直接几何查询的过滤和算法边界

`mj_ray(model,data,pnt,vec,geomgroup,flg_static,bodyexclude,geomid,normal)` 在本版末尾可返回 geom id 与法向。输入点/方向在世界轴，返回射线参数 x 满足 `pnt+x*vec`。若 vec 不是单位向量，x **不是米制距离**；接口只检查方向非零，不替调用者归一化。没有交点则返回−1、geomid−1。`mj_multiRay` 共享原点、批量方向并有 cutoff；正交相机因原点不同没有简单复用同一原点假设。[签名](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L692-L708)、[逐 geom 实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ray.c#L1305-L1351)。

射线[排除顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ray.c#L68-L99)是 body id、透明度、是否包含与世界焊接的静态体、可选 geomgroup。没有 material 时看 geom alpha==0，有 material 时看 material alpha==0。`contype/conaffinity` 是接触配对过滤，不能直接作为射线的可见性掩码。ray dispatch 对 mesh、hfield、SDF、primitive 分别查询；mesh 进入 [ray tree](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ray.c#L952-L970)，不等价于动力学凸包接触。

`mj_geomDistance` 则询问两个 geom 的 signed distance/见证点，输入 `distmax` 限制搜索范围，返回值可能被钳为 distmax；fromto 是世界轴两端点。它直接分派 collision function/native CCD，并不通过整套动态碰撞过滤，也不创建接触力。如果该配对没有实现函数，也可返回 distmax。因此 `distance==distmax` 不能无条件理解为真实距离恰好等于上限。接触力必须经过 E3 的装配/求解链。[实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L520-L614)。

原生 `distance/normal/fromto` collision sensor 对 geom/body 组合做查询；body 枚举其直接附着 geom，不自动递归整个 subtree；`cutoff` 作为最大距离，不是一般 amplitude clamp。fromto 未找到有效更近结果时为0；normal 从见证点差得到，深穿透/退化下不宜把它当稳定 tracking feature。`insidesite` 还可查询点/对象位于 site 区域的关系，它不是渲染可见性或接触判据。[collision sensor](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L726-L843)。

## 6. 深度图不是 rangefinder 的替代名字

| 区别 | 原生 camera rangefinder | classic Renderer depth |
|---|---|---|
| 生命周期 | 原生POS sensor，可受 history/disable/sleep 影响 | 场景更新及 render 时读取图像 |
| shape | sensordata平面块，按(H,W,fields)解释 | (H,W) float32 |
| 空间几何 | geom射线、所属body排除、原生ray过滤 | visual scene，可包含装饰geom/site/视觉选项 |
| 裁剪与无命中 | 射线无命中−1，不使用经典渲染near/far可见区间 | near/far裁剪；背景深度到far，不能按−1判断 |
| 距离定义 | dist是射线距离，depth是相机轴向 | wrapper返回轴向深度；低层readPixels先给归一化缓冲值 |
| 尺寸与内参 | 使用模型camera.resolution及前述版本分支 | viewport/Renderer尺寸与实际frustum |

即使都选择 depth，过滤、时点、内参或装饰不同也会有差异；本课没有建立它们数值相等的回归结论。[渲染课](rendering-and-viewer.md)给出深度缓冲反变换。以后复用 DexLab 图像或读数时也须保留对应路径，而不是只记录“depth”。

## 7. 原创阅读片段和练习

[单状态观测片段](../examples/sensing-rendering/README.md)使用居中透视相机，把 gyro/accelerometer、相机 rangefinder、camprojection 与三类渲染数组放在同一处读。它有意不引入采集器框架；本轮仅 AST/XML 结构检查，未做模型编译或成像。

1. **相机局部点(1,0,−2)，fx=100、W=200、H=100，居中透视投影是多少？range与depth是多少？**

答：u=150、v=50；depth=2，range=√5。这里是连续像素坐标，不是取整后的数组索引。

2. **把 camera quat 原样复制给 site，二者射线同向吗？**

答：默认不，camera看−Z，site rangefinder射+Z。需要有意旋转，而非只改类型名。

3. **camprojection在画面中央能否断言无遮挡？**

答：不能；它不做遮挡测试，背后点也能投影。还需前方深度判断、边界判断及适当几何/渲染可见性查询。

4. **camera.resolution=640×480，Renderer(height=240,width=320)，哪幅是640×480？**

答：原生camera rangefinder按模型640×480；Renderer输出240×320。camera.output不改变任何一个分配。

5. **world camera照向world plane，图像看得到地面而rangefinder为−1，一定是故障吗？**

答：不是必然，rangefinder排除所属body的geom，world plane被排除。还要检查其他过滤与射线方向。

6. **ray vec=(0,0,2)，返回x=3；路程是3 m吗？**

答：不是，在一致单位下路程为x‖vec‖=6 m。ray参数只有单位方向时才直接是距离。

7. **显式principalpixel=0时能否用camprojection确认所有渲染/range像素对齐？**

答：不能。固定版本三个路径对主点及正交投影的分支不同；应先限定居中fovy透视路径和尺寸，运行对齐验证仍未进行。

8. **geomDistance返回distmax且fromto全零，是否能把0作为最近接触点？**

答：不能；它可能表示超过上限或该配对缺少算法。零fromto不是有力接触记录，也没有经过求解器。
