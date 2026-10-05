# 原生几何检查

[English](NATIVE_GEOMETRY.md)

基础 SuperDex 接触实验实际使用 **BOX–PLANE** 碰撞体。输入三角网格与原生参考表面都不能作为 SDF 烘焙证据；这里不描述另一个苹果梗 SDF 演示。

`SuperDexPlane.record_geometry()` 复制原生参考表面、局部形状 AABB、实际碰撞体类型和实际位姿／速度。七个固定局部采样点按实际位姿转到世界坐标，再调用 `get_points_distance_to_surface`。独立检查使用解析盒距离和另一套旋转实现，拒绝缺测、坐标系／尺寸／类型错误、内部距离符号错误及缺失采样点。1e-12 m 只覆盖坐标运算误差，不是材料或穿透验收阈值。采样一致不证明整个碰撞表面或组合接触律正确。

SuperDex 可显式使用 `contact_indent_run.run(..., record_native_geometry=True)`。默认关闭；其他后端拒绝此查询配置。运行记录保存观测，独立验收在请求该功能时检查它。

开发证据：官方 FP64 运行时读回 BOX／PLANE、8 顶点、12 三角形与 ±0.02 m 边界。固定 0.8 秒法向加载轨迹、0.5 ms 步长，分别运行一次查询关闭和开启。所有记录的状态数组与完整接触记录完全相同。原驱动在两次仿真完成后的离线比较中漏传接触读取器参数而失败；随后只修复离线比较，没有重跑或覆盖仿真。这是一组无干扰对照，不是真机验证或统计可重复性证明。

原始证据已本地保留，公开附件交付及完整 PR 回归门禁待完成。不据此声明 SDF 几何准确性。

两条轨迹均未通过原来的 `no_tensile_normal_force` 检查。查询无干扰通过，不代表原接触问题修复。可用 `python demos/contact-benchmark/report_geometry.py EXTRACTED_PAIR` 离线复算几何、记录完整性、逐步状态与接触记录一致性，以及全部原验收失败。

证据包已解压核对 165 个文件哈希，离线报告完全一致；[包大小、哈希与全部判定](../../docs/evidence/native-geometry-v1.json)。公开附件以实际 Release 为准。
