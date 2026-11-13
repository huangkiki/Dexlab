# E3 验证记录

对应 [Issue #4](https://github.com/huangkiki/drake-atlas/issues/4)。开始前核实本地 main 与 origin/main 均为 E2 `fd561c91486679416fab6cc7b6b6dfb44acba911`，工作树干净、Issue OPEN、无进行中 PR；在 `docs/e3-contact-solvers` 分支实现。本文记录本地内容和静态证据；远端发布由主任务在审查后核实。

## 交付与边界

| 合同 | 文件与范围 |
|---|---|
| A4、B2：几何、材料与接触律 | [contact-models](../contact-models.md)：role/filter/Context、point/hydro、摩擦/耗散组合和原生属性 |
| B0 装配、B1/B3/B4：一步调用、动力学、数值与终止 | [contact-solvers](../contact-solvers.md)：free motion、面片离散、三种近似、SAP Newton/线性求解/终止、连续积分和可微边界 |
| B5：力、冲量与采样 | [contact-observation](../contact-observation.md)：受力侧、GeometryId/BodyIndex、wrench 参考点、平均力、sampled/live 与任务观测合同 |
| 原创原生 API | [contact_inspection.py](../../examples/contact_inspection.py)：球/地面的显式材料、Diagram/Context 和独立读回函数；未执行 |
| 阅读理解 | 三篇共 22 道带答案练习；公式假设和单位随正文给出 |

全部引用固定 Drake v1.57.0 官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，tree `6353dc7fc1a0aec84904838e7a39a38932594597`。固定链接和新增文件身份收录 [sources.json](../sources.json) 与[source-map](../source-map.md)。源码版本不是实际 wheel、宿主、ABI 或 DexLab 已验收版本。

## 语义审校中确认的差异

- `DiscreteContactSolver` 当前仅有 kSap；固定 tree 中无 TAMSI 文件。kSap/kSimilar/kLagged 是近似选择，不能复制历史 kTamsi API。
- 连续 point 使用分段 quintic Stribeck；连续 hydroelastic 的实际 traction 用 atan 正则化及 dynamic friction。离散装配也只读取 dynamic friction。
- Lagged 的 n0 是旧状态下的弹性力/法向速度重算值，不是上一轮 solver impulse；切向限额也不是当前 μγn。
- SAP 残差缩放实现为 `diag(A)^(-1/2)`，header 的正平方根注释与实现/量纲不符；cost 成功条件还实际要求 α>0.5。
- `relaxation_time` 的公开“缺失报错”文字与当前每侧 0.1 s fallback 装配不一致。示例显式给值，按实际组合解释。
- 当前 SAP AutoDiff 特化已用隐函数定理传播梯度；旧 header 中“有约束就不可用”的说明不能覆盖该实现。但未因此声称任意几何参数、接触切换或端到端任务梯度都可用。
- `ContactSolverResults.ft` 的注释误写 velocities，driver 的赋值及除 h 路径证明实际为 tangential force；vt 才是 velocity。

上述判断均在正文就近指向具体实现及有差异的声明。它们是源码审查发现，不是原生执行或上游确认的结论。

Python 签名另外核对：[材料可选参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_common.cc#L701-L719)、[hydro 属性重载](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_hydro.cc#L123-L142)、[碰撞注册](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L1073-L1089)、[point 与 hydro 读回](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L73-L155)、[几何字段](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_scene_graph.cc#L722-L788)。

## 静态检查

- `git diff --check` 与 `python3 scripts/check_docs.py`：通过。
- 全仓 5 个 Python 示例及 3 个完整 Python fences 的 `ast.parse`：通过；未执行 imports、构造函数或回调。
- 83 个 manifest 源文件 Git blob 与固定官方 tree 一致；313 处官方 blob 引用均固定同一提交，路径收录、行号在实际文件内。
- 标准库解析原创球 URDF，核对单体/无关节、质量、API 球半径和均匀实心球中央惯量；独立核对材料组合、冲量除 h、力矩平移符号：通过。
- 固定 tree 路径与 solver 枚举复核无 TAMSI 入口；主要公式与调用边界另人工读实际函数核对，不能由链接 gate 代替语义检查。
- 作者自审覆盖 Issue 范围、单位/正负号、源码矛盾与英文状态；未宣称独立 reviewer 批准。

首轮源码行号 gate 发现三个引用末行超出文件长度（penetration_as_point_pair、coulomb_friction、contact_results），按实际字段位置修正后重跑；没有改动固定版本或放宽检查。

## 未运行与下一项

未运行 Parser/模型构建、几何查询、contact Eval、Simulator、强制事件、SAP/IK、AutoDiff、传感、GUI、实验、训练或 benchmark。AST 和 blob 校验不能证明绑定运行、接触精度、稳定性、可微梯度或抓取成功。示例未创建柔性体，未提供真实 hydro slip 统计或传感器模型。

本项不改变 DexLab [#117](https://github.com/huangkiki/Dexlab/issues/117) 的运行验收状态；后续实验案例继续复用 DexLab 的原始版本和协议。下一项建议 E4，把传感器、渲染和可视化建立在本课坐标/采样合同上；E6 在 E3 合入后也满足依赖，但 E5 仍需 E4。当前未启动下一项，执行前应重新核实 main、Issue 和 PR。
