# E4 验证记录

对应 [Issue #5](https://github.com/huangkiki/newton-atlas/issues/5) 与[传感器、渲染与可视化](sensors-rendering.md)。基线是已发布 E3 `4e380773873643a5760d15024e30bac973f6b297`；开始时 fetch 并核对 main/origin/main/HEAD 一致，工作区干净、Issue OPEN、无评论或在途 PR。当前记录是本地交付；发布/CI/合入以实际提交与 Issue 为准。

## 要求与证据

| 范围 | 交付与审查边界 |
|---|---|
| 原生 sensor 与观测生命周期 | 四类公开出口、申请存储/producer/update/consumer、site 选择与相对变换 |
| IMU | specific force、COM→site 加速度、重力与轴、body_qdd 申请/producer/计算阶段；不把 Warp 路径外推到 CPU |
| 接触/触觉边界 | flat rows、逐行 counterpart 映射、可选 State、力/位置更新；保留 E3 producer 限制，无六轴/压力贴图承诺 |
| 几何查询 | newton.intersect_ray 的公开导出、world/global roots、单位方向、输出/miss、共享 BVH 的 build/refit/flags |
| 相机 | pinhole/标定反解、轴/FOV/像素中心、B/C 维度、七通道、range/forward depth、颜色/ID、miss/空场景 |
| Viewer / headless | GL/Null/USD/File/Rerun/Viser/RTX 适配职责、GL context、显示与截屏、外部宿主身份、输入/呈现时刻 |
| 学习材料 | 12 道带答案阅读练习；1 个原创静态相机 API 例子；未运行或产出图像 |
| 导航与状态 | 中文/英文 README、curriculum、roadmap、versions、source-map、来源清单与本验收 |

## 实际静态检查

Python **3.12.12**；仓库 CI 同样使用 Python 3.12 进行文本/AST 检查：

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

- 全仓相对 Markdown 链接通过。
- AST：**6 个教学 Python 文件**、**2 个 Markdown Python 片段**通过；未 import 原生库或执行教学代码。
- [sources.json](sources.json)：**99 个 Newton 文件**，E4 新增 **23 个**；按 Git blob 算法逐文件核对本地 bytes 与官方固定 tree。
- 全仓 **393 个 Newton blob 链接**的 revision、来源登记和行号边界通过。人工审查另外核对本章锚点是否支撑关联说法，不能用行号存在代替语义核对。
- E3 的[独立 MuJoCo-Warp 清单](e3-dependency-sources.json)继续独立保留，未把其路径混入 Newton manifest；E4 通过 E3 课程衔接其已经锁定的积分阶段说明，没有引入新的外部源码依赖。
- 文本公式统一使用 GitHub 支持的 `$$` 块；没有宣称本轮做过浏览器或渲染视觉验收。
- 内容摘要与检查范围见 [e4-validation.json](e4-validation.json)。E1–E3 的验收是各自交付时快照，其旧 manifest 摘要不能当作当前来源清单的摘要。

## 人工审查保留的发现

1. **默认 miss depth 与概述不同。**固定 ClearData 默认是 0，而类概述称负值表示 no hit；课程以实际 writer 为准，示例显式选 -1 并保存 uint32 ID 掩码。
2. **完全无几何时不发射 render kernel。**传入 ClearData 不保证这条路径清空旧输出。示例在 update 前填充全部返回通道，未修改上游，也未把源码路径发现称为运行复现。
3. **相机与几何查询共享 Model BVH。**默认纳入 VISIBLE，build 可改 mask，refit 不重选 enabled 集合；相机 update 的三角同步不替代 model shapes/particles refit。
4. **观测轴与身份必须按 API 解释。**camera transforms 为 C×B，outputs 为 B×C×H×W；Contact 是平铺 sensing 行和每行 counterpart 列，不存在统一 world 维度。射线公开入口是 newton.intersect_ray；相机特殊集合 ID 不能索引 shape_label。
5. **IMU 存储存在不证明加速度有效。**update 没有 producer/时间检查；MuJoCo-Warp 的 RNE/转换阶段已追踪，积分后的 pose 不自动意味着 qdd 在端点重算。CPU 特殊字段路径和其他 solver 的运行有效性没有据类名推定。
6. **显示不是统一观测 producer。**GL get_frame 是 framebuffer RGB；Null 不产生图像；USD 对 time×fps 取整；File 克隆状态不等于完整 solver checkpoint；RTX 异步可呈现上一帧。GL apply_forces 是另一个实际控制入口。

## 未开展与下一项

没有安装引擎/渲染宿主、native import、JIT、physics step、camera update 执行、GL/RTX 窗口、图像产出/视觉 QA、训练、benchmark 或评分。镜头反解与射线/相机核心调用已核对，未审查全部光照、纹理、Gaussian 渲染数学或外部宿主实现；真实传感器噪声/带宽/标定模型也未验收。上游宿主测试矩阵明确作为上游报告引用。

下一项 E5 已具备 E2/E4 前置，可继续批量、学习与数据接口；专用实现及可微扩展留 E6。后续实验复用 DexLab 冻结证据。本子任务只本地提交，由主任务独立审查后处理发布。
