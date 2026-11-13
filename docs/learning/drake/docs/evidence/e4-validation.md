# E4 验证记录

对应 [Issue #5](https://github.com/huangkiki/drake-atlas/issues/5)。开始时读取 AGENTS、贡献规范、Issue/评论和 open PR，核实 main 与 origin/main 同为 E3 `acd2e0a390a27e29f51d0c030b3c01e65f5230bb`，工作树干净、Issue OPEN、无进行中 PR，E1 先修文档已合入。分支 `docs/e4-sensors-rendering`；本记录仅声明本地内容/检查，远端发布由主任务审查后处理。

## 交付范围

| A6 内容 | 交付 |
|---|---|
| 传感几何、图像和显示 | [相机与渲染](../sensors-rendering.md)：SceneGraph/QueryObject/renderer、角色、RGB-D/label、光学帧、类型/单位/视图、点云、Meshcat/headless |
| 采样、时序和生命周期 | [采样与延迟](../sensor-timing.md)：连续、ZOH、Async、capture/output/consume/wall time、事件顺序、Context/参数/所有权 |
| 动力学传感 | [惯性与力观测](../inertial-force-sensing.md)：比力/空间加速度、gyro、编码器、mixed-age 输入、机械截面反力和触觉边界 |
| 原创片段 | [sampled_camera.py](../../examples/sampled_camera.py)：锚定球体、命名 renderer、只采样所需图像及位姿/正确时标；正文中完整 Python IMU 原生接线函数 |
| 阅读练习 | 三篇共 21 道附答案练习，公式注明坐标、假设与量纲 |

固定源码为 Drake v1.57.0，commit `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，tree `6353dc7fc1a0aec84904838e7a39a38932594597`。全部 blob 引用登记在 [sources.json](../sources.json) 及[源码地图](../source-map.md)。该身份不代表实际 Python wheel、VTK/OpenGL 后端、图形设备或外部服务验收。

## 需要按实现理解的细节

- `RgbdSensorDiscrete.image_time_output_port` 的 header 声明 vector size 1，但固定 `.cc` 将 `zoh_body_pose` 导出为 `image_time`；正文链接实际 L68–80 并明确这是静态发现。示例改用连续 RgbdSensor + 独立原生 ZOH，不修改或宣称修复上游 Discrete。
- 32F 深度为 z 米，16U 为 z 毫米；转换向零截断并把 NaN 合并成太远哨兵。点云转换默认 scale=1，即使输入 16U 也要显式给 0.001 才输出米。
- Async 的 output 事件 `future.wait()`；仿真延迟不是墙钟 deadline。固定版对 VTK/GL 有限制，worker 只传播 frame poses，不提供变形 configuration 捕获。
- ApplyCameraConfig 的零延迟分支使用连续 sensor；fps 和 LCM 发布事件不是该 sensor 自身采样。非零延迟发布 offset 有实际 1.001 因子，不能当作物理机制。
- Accelerometer 必须显式提供正确重力；默认零。C++ AddToDiagram 尚未导出到 Python，两种 IMU 都使用显式端口接线。
- 默认离散 plant 的 body accelerations 来自 sampled dynamics，而 body pose/velocity 为当前运动学；把它们接进理想 Accelerometer 不会自动对齐年龄。
- 原生编码器输出 rad、量化使用 floor、无自动取模/采样；接触面/反力和一个力矩消息类型不等于完整触觉/六轴硬件传感器。

新增示例的绑定单独核对：[相机和内参](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_rgbd.cc#L49-L100)、[相机 core](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_render.cc#L170-L244)、[VTK factory](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_render.cc#L440-L466)、[几何属性](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_common.cc#L114-L137)、[锚定几何](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_scene_graph.cc#L281-L291)、[ZOH 重载](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L705-L714)。

## 检查记录

- `git diff --check`、`python3 scripts/check_docs.py`：通过。
- 122 个 manifest Git blob 与固定官方 tree 一致；445 处官方 blob 引用固定同一提交、路径已登记且行号合法。全仓 6 个 Python 示例和 4 个完整 Python fences 的 `ast.parse` 通过；未执行 imports、构造函数或回调。
- 标准库解析/代数核对：相机内参、clipping 包含测距范围、z/range 反投影、异步时间、比力、向心加速度、编码器负值量化与原生 ZOH 接线；只读源码复核上述实现差异。
- 块公式采用 GitHub 支持的 `$$` 围栏；本次未把 TeX 文本出现当成浏览器渲染验收。
- 自审范围为 Issue 合同、原生 API/绑定、单位、受力侧、时间差和能力边界；最终仍交由主任务审查，没有声称独立 reviewer 已通过。

首轮来源登记 gate 因 `geometry/query_object.cc` 尚缺源码地图说明而中止，后续链接 gate 也因此拒绝未登记的新绑定文件；补齐登记后重跑全部检查通过，没有放宽固定来源要求或跳过引用。

## 未执行与下一项

未 import pydrake、构造 renderer/模型/Diagram/Context、运行相机/IMU/事件/Async worker/Meshcat、查询/求解动力学、训练或 benchmark。没有输出图片，没有图形驱动/后端/线程安全/实时性能验收，没有 LiDAR 或真实触觉硬件模型。解析投影和比力例子是标准库算式核对，不是引擎实验。

E4 交付不改变 DexLab [#117](https://github.com/huangkiki/Dexlab/issues/117) 的 Drake 运行验收状态；实验仍计划复用 DexLab。E2、E4 实际合入后可继续 E5；当前未开始下一项，需重新读取 main/Issue/PR 后领取。
