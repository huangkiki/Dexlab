# E4 验证与范围记录

任务：[SuperDex E4 #5](https://github.com/huangkiki/superdex-atlas/issues/5)。开始时核实 actual main/origin/main 为 `5a58da78d3a44f189c7974d8630283b5aed614f7`，工作树干净、无在途 PR，E1 依赖实际在 main；建立 `docs/e4-sensors-rendering` 分支。检查日期：2026-10-09。验收记录与章节同一提交保存，实际提交由文件历史及交付记录定位。

本章以官方 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6` 为基线；外部 Polyscope Python 源码另固定 v2.5.0 的 `8aa43f5d65d9ef54a415451c7caeebb4c0b6fde7`，用于匹配上游 lock 中的参考依赖版本；其 `deps/polyscope` gitlink 进一步固定原生 core `b1f5ae82488b82d91a61d7d8c81882989216056d`。**没有 native import、GUI、图像渲染、仿真、训练、性能基准或新评分器。** 下载源码与静态工具只处理文本/字节；没有安装依赖。

## 验收对应

| A6 要求 | 交付 | 证据边界 |
|---|---|---|
| 层次和能力 | [专题](sensors-rendering.md)第 1–2 节：Physics、Robotics、Polyscope、TCP/C++ Mochi renderer、UE、Studio | 原生查询、元数据组件、宿主图像分别记录，不虚构统一 sensor API |
| RGB/depth/segmentation | 第 2、5–6 节：RGB/RGBA、原生 RGBA8-only、内部 depth attachment、UE mode 文本请求 | Polyscope 真正四通道由固定官方依赖核对；未证明宿主 depth 单位/mask ID |
| ray/force/tactile | 第 4 节：点距离/接触 SDF/C++ ray 的区别、COM wrench 移点、触觉面积与杆权重 | 无 Scene LiDAR wrapper、无内建 tactile 声明；本体状态/理想 IMU 仅解释组合责任 |
| frame/单位/投影 | 第 3、5 节：worldFromActor × parentFromSensor、pinhole、vertical/horizontal FOV、资产/相机轴、畸变采样方向 | 公式标注 frame、px/m/N/Pa、方向与假设；不以 OpenCV 字段名宣称标定一致 |
| shape/所有权/时点 | 第 2、6–7 节：buffer shape、bytes 视图/复制、三种 native pipeline、UE 延迟与 capture ID | 异步名字不代表无阻塞；不把 readback 接收时间当模拟采样时间 |
| headless/GUI | 第 8 节：Polyscope global 初始化/暂停/close、原生离屏后端、TCP/UE 宿主销毁、Studio Xvfb、Debugger | headless 不等于没有图形依赖；仓内内部 Buck 脚本不是公开 wheel 运行资格 |
| 最小片段 | [read_camera_metadata.py](../examples/read_camera_metadata.py) 和第 6 节 native TCP viewer readback 片段 | AST 通过；前者无 import 原生包，两个片段均未执行 |
| 易错点/练习 | 第 9–10 节，12 项诊断与 16 道带答案阅读练习 | 无新实验方案、指标或验收阈值 |
| 入口与状态 | 中英 README、guide/curriculum/roadmap、source-map/manifest、来源归属 | 保留 Sim Atlas 总仓入口；E5/E6/E7 未标完成 |

## 实际检查

- `git diff --check` 通过。
- `python scripts/check_docs.py` 通过。首次草稿检查曾报告尚未写入的本验收页缺失；补齐后重新运行并通过。
- 全部 124 个 SuperDex manifest 文件逐一匹配固定 Git tree 的 path/blob；本项新增 35 个文件，下载字节均按 Git blob SHA-1 校验。
- `sources.json.external_sources` 的 6 个外部文件（Python、C++ binding、MIT license、.gitmodules，以及固定 Polyscope core 的截图头文件/实现）匹配各自固定 Git tree 与下载 blob；额外核对 deps/polyscope gitlink 指向；不是把该版本归给 SuperDex 核心。
- 所有 Markdown 中这三个上游的固定 blob 链接（包括 reference-style）共涉及 130 个文件，manifest 覆盖、commit、reference 定义和 5 个显式行号锚点范围通过。
- 全部 5 个仓库 Python 文件与 2 个完整 Markdown Python 代码块经 `ast.parse` 通过；未 import 或运行这些片段。
- 自审逐项核对原生类/方法/字段、Camera reset、world pose 组合、图像 channel/dtype、readPixels 格式、pipeline 缓存/flush、距离支持分支、UE/client 边界和公式量纲。没有修改上游或复制其源文件进入本仓。

## 结论与未验证项

A6 源码课程已完成，运行未验收。没有图像正确性、深度精度、色彩标定、GPU/backend 兼容、帧率、线程稳定性或触觉传感模型的运行证据。固定源码显示的能力缺口已写入正文：CameraSensor 无图像生产、Mochi 公开 readback 无 depth/segmentation、公开注册无 tactile/IMU；客户端请求不能证明具体 UE/plugin 服务端协议实现。

所读公开树未定位到 Python MochiRendererViewer 所称 `mochi_viewer` 的同名服务端实现，不能给出已经验收的启动命令；原生 C++ renderer 库仍有明确 API。Polyscope 引用是与 lock 版本匹配的源码身份，未比对已安装 wheel 或实际设备；vendored Filament 也不等于宿主驱动身份。这些边界不会以运行实验补造为本轮课程的先决条件。

E5 所需 E2/E4 知识先修已交付，待本项实际合入后可以推进批量、学习接口与数据；E6 已具备 E3 先修，特色/可微扩展仍需单独完成。后续实验统一复用 DexLab，源码默认值不补写历史批次。远端发布、Issue/Project 和总仓由主任务在实际集成后更新。
