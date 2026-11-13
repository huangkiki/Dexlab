# E4 验收与后续任务

对应 [Issue #5](https://github.com/huangkiki/genesis-atlas/issues/5)，从已发布E3的main `444aa79fb26a15dd8fcaf4c7be7a3ae4482913bf` 开始；本地main与origin/main一致、工作树干净，E1建模/状态/时间章节已在base中。实现分支 `docs/e4-sensors-rendering`。记录日期：2026-10-09。

交付 [传感器、渲染与可视化](sensors-rendering.md)及原创 [sensor_rendering_api.py](../examples/sensor_rendering_api.py)，更新中英README、导读、课程/roadmap和来源表。Sim Atlas系列首页链接保留。无第三方代码或资产复制，原创片段沿用本仓Apache-2.0许可。

## 覆盖与限制

| A6 / Issue要求 | 实际交付 |
|---|---|
| 原生传感器与渲染分层 | 第1、3–5节：vis camera、RGB camera sensor、Raycaster/DepthCamera的独立执行链 |
| RGB/depth/seg/normal/点云 | 第3–4节：shape/dtype、OpenGL/OpenCV坐标、pinhole反投影、内部seg ID字典、normal编码与renderer分派 |
| 射线与几何 | 第5节：pattern方向、range、BVH目标、world/local点、no-hit及min_range未消费 |
| 力/IMU | 第6节：Contact计数、link系力/每轴限幅、joint output effort、proper acceleration和偏心项 |
| 触觉 | 第7节：ContactProbe/DepthProbe、Kinematic/Proximity/Elastomer输出、估计公式/量纲、候选门控/容量、状态与误差 |
| 其他sensor | 第8节：SurfaceDistanceProbe和TemperatureGrid的API、shape/单位/边界；专项模型推导留E6 |
| 时序/所有权 | 第2、4节：物理step后更新、lazy image cache、pre-step recorder与post-step视频、history/delay、reset和复制 |
| GUI/headless/批量 | 第3、4、9节：GL/Luisa/Madrona分支、显示窗口与离屏、环境布局和renderer限制 |
| 可微限制 | 第9节：逐算子证据、NumPy/uint8/cache/raycast边界，不用requires_grad总开关推断可微传感 |
| 阅读练习与例子 | 14题附答案；两个生命周期明确的原生注册/读取函数，未执行、无主程序/init/build/step循环 |

这是源码课程交付，**没有原生import、构建、渲染、仿真、实验、训练、性能基准或评分器**。GL/Luisa/Madrona具体二进制版本与平台资格未验收；法向的外部adapter通道语义、fisheye点云、跨renderer混用和真实硬件标定不作运行保证。E5–E7仍待开发；DexLab历史配置/结果未改动。

## 静态检查与自审

| 检查 | 状态 | 证据含义 |
|---|---|---|
| `git diff --check` | 通过 | 空白与冲突标记 |
| `python scripts/check_docs.py` | 通过 | 全仓Markdown相对链接目标 |
| Python AST与完整Markdown Python围栏 | 通过：5个Python文件、1个完整围栏 | 仅语法；没有import或执行原生例子 |
| 固定源码SHA、manifest与Git blob/tree | 通过：81个blob、327个固定源码链接 | 内容身份、固定提交、manifest收录、行号范围与reference定义 |
| 现有原创URDF结构与box惯量 | 通过：3 links、2 joints | 既有资产静态回归；不是运行验收 |
| 公式/API/派生实现自审 | 已完成，待主agent独立审查 | 已逐级检查配置→getter/override→kernel；不声称独立主审通过 |

新源码保存在独立E4工作目录，仅作阅读输入；未写入仓库。此次manifest新增28个实际引用文件；所有81份缓存内容重新计算Git blob SHA1，与官方固定tree和sources.json交叉核验。来源行号首轮发现4个末尾锚点越过文件结尾，已按实际文件修正；写作中间的链接检查曾因本验收页尚未写入失败，文件补齐后完整重跑通过。主审改文档后应重跑最终gate；本记录对应的最终head/tree在本次交付报告中返回。

主agent展示复核发现7个块公式的 `\[...\]` 在 GitHub Markdown 渲染为普通文本，已改成 `$$...$$`。对完整正文调用 GitHub Markdown API 后确认7个块公式均生成 `math-renderer`；这是标记渲染检查，不是浏览器像素验收或原生运行。修正后重新执行文档、diff与源码/语法静态审计。

## 固定版本发现

- 相机分割输出是压缩ID，公开解码入口是 `scene.visualizer.segmentation_idx_dict`；不能沿docstring直接索引link。
- vis set_pose的transform与pos/lookat/up实际互斥；pointcloud数组是H×W，docstring中的res顺序有误。
- RGB camera sensor只覆写read；GT和批读没有接入其独立image_cache，且不支持delay/jitter/history。
- history窗口取未加readout延迟的return ring；jitter==dt在实际EPS校验下允许。
- Raycaster.min_range存字段但未传cast；local points不加ray origin；DepthCamera.read_image返回range且未处理history维。
- BatchRenderer同step混合缓存命中可能返回None；完整新请求或force_render可避开该分支。
- Contact索引在混合solver场景需核对；ContactForce在link系按轴限幅，GT也后处理，不提供六轴wrench。
- tactile force是几何/速度感知模型，Elastomer返回marker位移；二者不等于求解器接触力或实测校准。

建议下一项 **E5 批量、学习接口与数据**，承接E2任务时序和E4观测契约；待主agent审查发布本切片后再领取。E6进一步展开热/触觉专项、多物理及可微内部；E7升级时保留并复核实现与注释差异。本地已按授权提交，不推送、不改远端Issue/Project、Obsidian或其他仓库。
