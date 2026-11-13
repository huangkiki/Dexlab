# C++ 阅读片段

[E1：状态边界](e1_state_boundary.cpp) 对应[建模、坐标、状态与时间](../docs/modeling-state-time.md)。原生 C++，没有 Python 包装器，没有 `main`；调用方负责初始化与资源生命周期，前置条件写在文件中。

本阶段不运行 SDK 或新仿真实验。语法/类型检查结果与未覆盖范围见[验证记录](../docs/validation/e1.md)。

[E2：驱动与机器人](e2_control_robotics.cpp) 对应[控制专题](../docs/control-robotics.md)：平移关节配置、target/持久 effort、工具 FK 与 Jacobian 行映射。候选参数未作运行验证；源码/编译检查见 [E2 记录](../docs/validation/e2.md)。

[E3：接触报告复制](e3_contact_readback.cpp) 对应[接触、求解器与力观测](../docs/contact-solvers.md)。分别保留法向点、切向 anchor、事件与可用性，示范关于 world 参考点的已报告点冲量矩；不宣称完整 wrench，不聚合 CCD。无 `main`、无链接/运行；[E3 检查记录](../docs/validation/e3.md)注明语法/类型检查边界。

[E4：单束 scene query](e4_scene_query.cpp) 对应[传感、场景查询与调试显示](../docs/sensors-rendering.md)：原生 preFilter 排除提供的自身 actors，选择最近 BLOCK，检查有效位并复制数值；调用方负责一致的 pose/场景采样边界和 query mask。无 `main`、无 SDK 链接/运行，不是 RGB 或 LiDAR 产品。[E4 检查记录](../docs/validation/e4.md)列出固定头文件语法/类型检查与未执行范围。

[E5：批量边界](e5_batch_boundaries.cpp) 对应[批量、学习接口与数据](../docs/batch-learning-data.md)：无状态 simulation filter shader 识别环境/共享静态 world，Direct GPU 关节读回按 scene-wide maxDofs 检查 buffer 容量并使用原生事件。调用方负责 scene 初始化、GPU 内存/索引和同步；没有分配、链接或运行。[E5 验收记录](../docs/validation/e5.md)给出语法检查和责任边界。

[E6：原生约束行](e6_constraint_row.cpp) 对应[扩展与能力边界](../docs/extensions-boundaries.md)：固定 world 轴上的双 attachment force spring，显式填写 Jacobian、几何误差、原始冲量限幅和 force writeback 标志。只实现原生 row-prep 回调，不含 connector/资源创建或 Scene，不构成完整插件；[E6 验收](../docs/validation/e6.md)记录 syntax/type 检查与未运行范围。
