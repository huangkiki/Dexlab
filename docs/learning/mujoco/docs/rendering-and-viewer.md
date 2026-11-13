# 渲染与 viewer：从物理缓存到像素和窗口

本课属于 A6，先修[传感与采样](sensors-and-sampling.md)、[相机与查询](cameras-and-geometry-queries.md)。固定 MuJoCo 3.15.0，重点是原生 classic 路径，另说明本版 Filament 的真实接口边界。本轮没有原生 import、OpenGL 初始化、渲染截图、窗口或无窗口运行验收；“源码支持”不等于当前设备已配置成功。

## 1. 先画清资源与更新链

```text
MJCF/mjSpec -> mjModel + mjData
                  | 明确的 forward/step 阶段更新物理派生缓存
                  v
        mjv_updateScene(model, data, option, perturb, camera, category, scene)
                  | mjvScene：抽象几何、灯光、相机、装饰、渲染标志
                  v
        mjr_render(viewport, scene, mjrContext)
                  | 当前 OpenGL context 中的 framebuffer
                  v
        mjr_readPixels -> RGB/raw depth -> Python wrapper 转换 -> CPU数组
```

`mjv_` 函数完成抽象可视化；`mjr_` 是 classic OpenGL 渲染，要求当前线程有可用 OpenGL context。物理库本身不要求创建窗口。其他渲染器可以消费自己的场景表示；不要把使用 OpenGL 的显示路径当成物理求解器在 GPU 上计算的证据。[分层](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/visualization.rst#L20-L40)、[OpenGL前提](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/visualization.rst#L313-L330)。

`mjv_updateScene` 从现有 data 构建场景，**不替你调用 mj_forward**。改 qpos 后只 update_scene 仍可能读旧 geom/site/camera pose；step返回后直接render也可能使用积分前的派生量。应用须决定采样在步前、步后重算还是保留求解阶段，然后同时固定传感器和图像的 timestamp。图像读回时的墙钟并不是物理拍摄时刻。[update_scene Python实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L261-L311)、[原生scene更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_vis_visualize.c#L3698-L3743)。

## 2. mjvScene 与 mjModel 不是同一份几何列表

`MjvScene(model,maxgeom=...)` 为可视化对象分配容量。一个物理 geom 可对应多项装饰，接触箭头、相机、site、tendon 等也能进入列表，因而 scene.ngeom 不是 model.ngeom。`mjvOption` 的 geomgroup/sitegroup/flags 控制哪些项被加入，`mjCAT_STATIC/DYNAMIC/DECOR` 进一步筛类别；这些显示选项不会改物理 contype 或 sensor 的 ray 过滤。

每次 `mjv_updateScene` 通常清空并重建列表；`mjv_addGeoms` 可追加轨迹等显示对象，`mjv_updateCamera` 只更新相机。自行 `mjv_initGeom`/connector 加入的箭头和线没有 mass、碰撞、约束或 actuator；不要把画出了夹爪力箭头当成施加了该力。[场景构造](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/visualization.rst#L220-L263)。

`maxgeom` 包括装饰预算。固定版本[acquireGeom](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_vis_visualize.c#L170-L179)在满时设置 scene.status、发出警告并返回NULL，可导致场景缺项；不是自动动态扩容，也不会扩大物理接触arena。Python Renderer 的实际默认 max_geom 是10000；若课程示例设较小值，不能将其推广为所有复杂模型的容量。原生分配/释放见 [mjv_makeScene / free](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_vis_init.c#L126-L148)。

## 3. 3.15 的 Python Renderer 到底指哪一个

`mujoco.Renderer` 从 `mujoco.rendering.classic.renderer` 导入；旧 `python/mujoco/renderer.py` 是兼容转发文件。`__init__.py` 在 try/except ImportError 中导入渲染扩展和 Renderer，因此 `import mujoco` 成功也不证明 classic 渲染可用。[公开导入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/__init__.py#L66-L78)、[旧文件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/renderer.py)。

classic `Renderer(model,height=240,width=320,max_geom=10000,...)` 持有该 model、MjvScene/MjvOption、像素矩形、所选 GLContext 和 MjrContext。初始化检查 width/height不超过 `model.vis.global_.offwidth/offheight`，然后选择 offscreen framebuffer；图像尺寸来自这个构造参数，而不是模型camera.resolution。[构造](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L29-L99)。

`renderer.update_scene(data,camera="top")` 选择固定模型camera；传−1选自由相机，传 MjvCamera 可指定抽象相机；命名 camera 查找失败会报错。随后 `render()` 从保存的scene读出。分别切换 depth/segmentation 模式，每次 enable会关闭另一个；需要RGB时关闭相应模式，不能期待一次调用同时给三个输出。

| classic render模式 | 返回 shape / dtype | 内容 |
|---|---|---|
| RGB | `(H,W,3)` / uint8 | 8bit颜色，不能当线性光照、物理辐照度或自动噪声相机 |
| depth | `(H,W)` / float32 | wrapper反投影后的轴向长度，见下一节 |
| segmentation | `(H,W,2)` / int32 | 最后一维为 `(objid,objtype)`；背景`(-1,-1)` |

文档字符串部分写成 width,height，但[实际分配](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L132-L180)是height,width，遵循代码。不带out时wrapper创建数组；复用out时调用者必须提供正确shape/dtype并保证可写。尤其 segmentation 的低层out是RGB uint8编码缓冲，最后生成新的int32标签数组，因此不能假设返回值总是传入out的同一对象。保存多个时刻时需要自己的快照与元数据。

## 4. 深度缓冲如何变成长度

low-level `mjr_readPixels` 给的是depth buffer值，不直接是米。classic Python wrapper把 `readDepthMap` 设为 `mjDEPTH_ZEROFAR`，令 b=0 表示far、b=1表示near。近平面/远平面长度为：

$$
n=\mathrm{vis.map.znear}\,\mathrm{stat.extent},\quad
f=\mathrm{vis.map.zfar}\,\mathrm{stat.extent},\quad 0<n<f.
$$

固定场景尺度与普通透视frustum下，wrapper使用的反变换可整理为：

$$
z={fn\over n+b(f-n)}.
$$

所以b=1→n、b=0→f；它是相机轴向depth，range还需要像素射线。正交模式用 `z=f−b(f−n)`。内部投影系数先按float32构建，反变换用float64再转float32，目的在于配合实际GPU投影精度；不要用另一个near/far值再次“校正”已经转换过的render结果。[转换源码](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L185-L225)。

背景/远裁剪处通常读成far，不能照搬原生rangefinder的−1判无效。近远裁剪也会使物体虽然在物理空间里，图像却没有该表面。缩小near或拉大far改变深度缓冲精度条件，不能只为“看全场景”而假设数值不受影响。图像中有些显示项可能是site/装饰而非真实碰撞geom。

低层像素缓冲采用OpenGL的行方向；classic wrapper在持有自己的GLContext时调用 `flipud`，标准EGL/OSMesa/GLFW路径结果按左上开始的数组行理解。若禁用了wrapper的context而由用户提供自己的current context，代码不走同一翻转分支，应核对输出朝向，不可再无条件套一次flip。[翻转分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L253-L259)。

## 5. 分割图的ID映射和无效值

分割模式暂时打开 `mjRND_SEGMENT` 和 `mjRND_IDCOLOR`，把scene中的 `segid+1` 编到24bit RGB。wrapper重建整数 `r+256g+65536b`，再查表映射为scene geom的 `(objid,objtype)`；索引0留给背景的−1/−1。`objtype` 可是不同原生对象类型，不能把通道0全部拿去索引 model.geom_bodyid，也不是训练数据集的语义类ID。[实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L227-L251)。

若要按body合并，应先只选 `objtype==mjOBJ_GEOM` 的有效标签，再按该geom的bodyid转换；site/装饰另定策略。遮挡、显示组、透明度、scene容量和手工装饰会改变可见标签。segid是本场景的渲染编码，不是跨模型永久身份；objid也只在相同模型布局中有意义。模型重编译或资产变化后要重建映射。

## 6. context、线程和headless的生命周期

| 资源 | 创建/使用约束 | 何时需要重新处理 |
|---|---|---|
| OpenGL context | 由GLFW/EGL/OSMesa等创建；调用mjr前在当前线程make_current | context不能同时current于多线程；切线程需显式管理 |
| MjrContext | `mjr_makeContext`/`MjrContext(model,...)`在有效GL context中上传模型资源 | 换model需重建；它不是操作系统GL context |
| mjvScene | 模型及maxgeom容量、CPU抽象几何 | 每个物理采样/视觉更改后更新；新模型重建容量与引用 |
| framebuffer/viewport | offscreen容量与实际viewport分别管理 | Python构造尺寸受offscreen上限；窗口缩放则重新取framebuffer尺寸 |
| mesh/texture/hfield GPU副本 | makeContext初次上传 | 原地修改CPU资产后要相应`mjr_uploadMesh/Texture/HField`，仅update_scene不足 |

context不是pickle状态的一部分。模型重编译、销毁或替换以后，不复用旧Renderer的资源引用。低层通常先释放mjr/scene资源再结束其宿主context；使用Python wrapper则直接 `with mujoco.Renderer(...) as renderer:` 或显式close，遵守该封装自己的清理顺序，不手工拆其私有context。close后render报错；正常退出不要只依赖析构时机。[资源说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/visualization.rst#L334-L399)、[wrapper close](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/renderer.py#L316-L340)。

`MUJOCO_GL` 在classic模块**导入时**读取。Linux下egl选EGL、osmesa选软件OSMesa，通常默认走GLFW；`disable/off/false/0`让wrapper不创建context，而不是让mjr变成无需GL的软件数组运算。环境变量应在Python启动/第一次import之前设置，修改后复用已导入模块不能视为切换成功。[选择器](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/classic/gl_context.py#L17-L56)。

Headless表示不需要显示窗口，仍需要可工作的库/驱动/context。EGL可用于无窗口硬件渲染，OSMesa是无窗口软件路径；选择EGL不是MuJoCo物理GPU加速的证明。viewer交互窗口和offscreen Renderer是独立需求，不能通过在无显示主机启动viewer来验收headless。本阶段不创建这些context，仅给出分层排查：导入是否有render扩展→选哪个context provider→make_current是否成功→framebuffer容量/资源→scene数据是否新鲜→图像方向/语义。没有当前设备的成功截图或帧率结论。

## 7. viewer：用户循环与GUI循环谁拥有状态

`mujoco.viewer.launch` 是托管/阻塞的交互应用路径；`launch_passive(model,data)` 返回handle，用户脚本负责推进物理和时序，窗口线程负责显示。GUI刷新率、vsync、物理timestep不是同一个参数；passive没有替你实现稳定的实时控制调度。macOS下passive要求用 `mjpython` 将UI放在所需主线程。[官方说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/python.rst#L48-L141)、[入口检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/viewer.py#L531-L597)。

passive的 `sync()` 不是单向“显示最新帧”：它同步模型/数据到显示副本，也处理GUI控制、选项和扰动回到用户状态。`cam/opt/pert` 等共享可视化对象的修改用 `with handle.lock():` 保护；`sync()` 内部取锁，close/is_running有各自安全入口。用户模型/数据在非sync期间由用户管理，但若你另开线程或让多个调用者并发sync/step，就必须自行串行化，不能由GIL推断native共享内存安全。文档较早的“所有修改都加锁”概括与随后passive副本说明应结合读，不建立不必要的隐式跨线程写入假设。[handle方法](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/viewer.py#L224-L258)、[Sync内部锁](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/simulate/simulate.cc#L2108-L2118)。

| sync模式 | 固定3.15实际处理 | 适用边界 |
|---|---|---|
| 默认False | `mjv_copyModel` + `mjv_copyData`同步可视化所需数据 | 能拾取geom_rgba等显示变化；不是完整持久化checkpoint API |
| `state_only=True` | 对显示副本复制`mjSTATE_INTEGRATION`，再`mj_forward` | 有重新计算、callback等副作用/工作；不会带上任意模型变动，也不是完整sleep/IPC checkpoint |

真实分支见 [passive sync](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/simulate/simulate.cc#L2350-L2395)。不能为了只读显示随意开启state_only而假设完全不执行物理相关计算；本课因此连viewer.sync都未运行。默认模式复制旧派生量时也不会神奇修复用户忘记forward的问题。

`user_scn` 是用户持有的额外可视化场景，下次sync把其geoms/flags并入显示；修改后要sync，仍是显示装饰。CPU资产变动后，handle.update_mesh/texture/hfield会在viewer侧上传，方法内部加锁并等待；与直接改几何pose是不同更新路径。使用上下文管理器关闭窗口，结束状态以is_running/close为准；不把窗口关掉当物理任务成功。

## 8. Filament 边界：本版存在，但不是classic的参数开关

固定树包含 `mujoco.rendering.filament.renderer.Renderer`，其构造是 `Renderer(ctx: mjrf.Context)`，**不是** `Renderer(model,height,width)`。它管理命名scene、target、view；scene内容由调用者负责填充，target接收可写CPU buffer或可零拷贝转为CPU NumPy的DLPack对象。buffer按pixel format校验shape/dtype，例如RGB8为(H,W,3)uint8，R32F/DEPTH32F单通道float32。不要因看到DLPack就断言任意CUDA tensor都能作为此wrapper读回目标。[对象与buffer](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/filament/renderer.py#L29-L175)。

`render()` 生成views/reads请求，调用ctx.render并wait_for_frame，写入既有buffer、返回None；其深度格式、scene转换与相机配置须按这个后端单独理解，不能复制classic `render()`的shape/翻转/线性化逻辑。[提交与等待](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/rendering/filament/renderer.py#L176-L229)。本课给出API身份边界；完整Filament构建/资源系统和与其他后端的能力关系留E6，未声称当前wheel包含该扩展、该设备可运行或已做渲染质量比较。

## 9. 带答案阅读练习

1. **只改data.qpos，然后renderer.update_scene/render，为何不能保证看到新pose？**

答：update_scene消费派生缓存，不调用forward；应在确定的物理阶段更新pose，再保存该阶段timestamp。

2. **model.ngeom=100，max_geom=100为什么仍可能缺显示对象？**

答：scene还包含site、contact箭头等装饰，数量不一一对应；容量满会警告/缺项，不会自动扩大。

3. **depth像素值等于far，是否距离传感器成功看到far处平面？**

答：不能据此判断，可能是背景/裁剪；wrapper输出轴向长度而rangefinder还有独立−1哨兵和过滤。

4. **segmentation[...,0]=5，能直接认为body5吗？**

答：不能，第一通道是objid，还要看objtype；若是geom才再查geom_bodyid，背景是−1。

5. **把camera.output加入depth会让render一次返回RGB和depth吗？**

答：不会；它是模型元数据。classic的depth和segmentation是互斥模式，三次render才分别取得三种数组。

6. **MUJOCO_GL=egl能证明物理在GPU上吗？**

答：不能，它只选择classic图形context provider；创建成功和可用图像本课也未验证。

7. **修改geom_rgba后只用passive sync(state_only=True)，为何可能没变化？**

答：该路径只复制INTEGRATION状态到显示副本并forward，不复制任意模型字段；应理解默认可视化复制路径。它同时并非无计算的只读同步。

8. **将classic代码的Renderer(model,...)直接换为Filament类能保持行为吗？**

答：不能，构造、scene填充、target buffer和render返回契约不同；应按后端真实接口设计，不能用统一名字掩盖差异。

原创片段与未运行范围见[示例说明](../examples/sensing-rendering/README.md)，本阶段验收见[E4记录](validation/e4.md)。
