# 单状态原生观测阅读片段

[observations.xml](observations.xml)与[read_observations.py](read_observations.py)服务于[传感器](../../docs/sensors-and-sampling.md)、[相机与查询](../../docs/cameras-and-geometry-queries.md)、[渲染](../../docs/rendering-and-viewer.md)三课。使用固定 MuJoCo 3.15.0 原生绑定契约，代码为本仓原创，不引入统一封装或采集框架。

它在一个自由体球上定义 gyro/accelerometer/site，在独立静态 mount body 上定义居中 fovy 透视相机。相机所属 body 与 world 不同，所以 rangefinder 的 bodyexclude 不会直接排除 world plane。相机分辨率与显式 Renderer 尺寸一致，避免无意混用 W/H；rangefinder 选择 dist/point/depth 后按 `(48,64,5)` 解释，且先从 dist 判断命中。

如果以后执行，脚本会编译 MJCF、分配数据、调用一次 mj_forward，再在同一准备状态读取 sensor 和三种图像；没有显式 mj_step。模型编译器自身还可能执行测试计算，forward 包含动力学/传感器工作，Renderer 会创建图形 context，所以本轮**没有运行该脚本**。代码中的输出不是预先验证过的测量，也没有保证 ray 图和渲染深度逐像素一致。

| 项目 | 本阶段状态 |
|---|---|
| Python AST / XML 文本结构 | 已检查，见[E4 验证](../../docs/validation/e4.md) |
| 原生字段/shape/源码分支 | 固定SHA阅读核对 |
| MJCF schema、模型编译、绑定调用 | 未验证 |
| forward、IMU与几何读数 | 未执行 |
| EGL/OSMesa/窗口、RGB/depth/segmentation | 未执行；无截图或驱动适配结论 |
| 新实验、训练、性能benchmark | 本阶段不做；未来复用DexLab |

阅读时追踪五件事：传感器按 sensor_adr/dim 分块；copy固定数组值；sample_time只对这里无history的准备状态适用；RGB与depth/segmentation是不同render调用；with负责wrapper生命周期。渲染变量在退出context后仍是独立CPU数组，但context不能再使用。

原生rangefinder忽略viewer显示组，RGB场景可能含site/装饰，depth背景与ray未命中哨兵不同；这里没有做差值指标或把渲染当传感器标定。
