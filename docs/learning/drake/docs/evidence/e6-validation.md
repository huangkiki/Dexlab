# E6 静态验收记录

任务：[Issue #7](https://github.com/huangkiki/drake-atlas/issues/7)。基线为 `13839700c33d41524aad8b904b079b4ef112a95b`，E3 及 E5 已实际合入；本阶段完成 B6 原生扩展与 B7 综合源码链。源码课程交付与原生运行资格分别记录。

## 交付内容

- [原生 System 扩展](../systems-extensions.md)：端口依赖、缓存、状态/事件、TemplateSystem、Context 复制与 scalar converter，以及原生力元素/体积力扩展。
- [标量与可微边界](../scalar-capabilities.md)：seed/梯度含义、AD/symbolic 支持矩阵、几何忽略/抛错、SAP 隐式导数、非空 FEM 限制与优化前置条件。
- [特色能力与综合源码链](../engine-boundaries.md)：MathematicalProgram、轨迹优化/GCS、FEM 材料/状态/接触积分、内部 MPM、Propeller/Wing/MLP 与完整原生链。
- [scalar_lag.py](../../examples/scalar_lag.py)：原创一阶滞后 LeafSystem_[T]，原生 TemplateSystem 构造/copy，真实 state-only 输出依赖与未调用的局部 AD 阅读函数。
- 每篇 7 道有答案练习，共 21 道；双语 README、导读、课程、roadmap、版本、例子目录、来源地图与清单同步。E7 未开始。

## 固定来源与人工核对

官方阅读版本 Drake 1.57.0，commit `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，实际 Git tree `6353dc7fc1a0aec84904838e7a39a38932594597`。本轮新增 31 个引用文件，[sources.json](../sources.json) 共 173 个文件；按 `SHA1("blob " + decimal_size + NUL + bytes)` 对固定官方 tree、清单和下载字节核对，缓存未提交到本仓。

| 重点 | 对照固定声明、实现和绑定的结论 |
|---|---|
| 原生扩展 | 状态/输出/事件职责、依赖 tickets、Python callback 的 GIL；TemplateSystem 必须传 converter，copy 必须保留固定配置 |
| 标量转换 | System 与 Context 分别转换/建立；输入当前值需显式拷贝；Diagram 能力取交集；AutoDiffXd 当前是 Drake 自有 AD 的别名 |
| 几何/物理方法 | symbolic 连续接触在碰撞几何非空时拒绝；SAP 更新拒绝 symbolic，但保留结构查询；点距离不支持形状可能被忽略；hydro AD 只由 pose 引入 |
| SAP | 当前隐式导数与旧 Plant 注释分别保留；存在内部导数不等于完整任务可微或梯度通过运行校验 |
| 柔性体 | 非空 DeformableModel 只支持 double/discrete/SAP；is_empty 同时要求没有 body 和 force density，Finalize 移除不支持转换；节点 q/v/a、3×N/3×2N 接口形状与 Schur 恢复链分别说明 |
| FEM 配置差异 | 两个 damping setter 实际检查旧成员，下游 DampingModel 检查新入参；Python Config 没有绑定 subdivision setter，不按 C++ 字段名称推断 Python 方法 |
| 特色归属 | DirectCollocation/Transcription 有具体状态/输入/AD 假设；MPM 是 internal/private；Propeller/Wing 是力模型，MLP 是原生网络 System，不是完整 CFD/GPU/训练系统 |

原生例子的 DeclareVectorInput/OutputPort size 重载、prerequisites、DoCalcTimeDerivatives、ContinuousState.CopyToVector 和 AD helper 均对照固定 Python 绑定。tau 是固定普通配置，只播种 x；xdot=6 m/s、对 x 偏导 −20 s⁻¹ 是解析预测，未输出任何原生数值。

## 检查结果

| 检查 | 结果及范围 |
|---|---|
| `git diff --check` | 通过 |
| `git diff --cached --check` | 通过，包含全部新建正文、例子和本记录 |
| `python3 scripts/check_docs.py` | 通过，仓内 Markdown 相对链接全部存在 |
| 固定源码身份与引用 | 173 个文件 Git blob 匹配固定 tree 与清单；638 处官方 blob 引用均为固定 SHA，行号不越界，引用文件集合与清单一致 |
| Python AST | 8 个 examples 文件与全部 5 个完整 Python Markdown 围栏通过；新例子无顶层实例构造，但 decorator/模板注册仍会在 import 时执行，本轮未 import |
| 源码静态合同 | 通过：AutoDiff 别名、TemplateSystem、Diagram 能力交集、空 FEM 转换条件、damping 旧成员/下游入参检查、FEM 绑定与 MPM private 目标 |
| 文本与独立算式 | 三篇分别 98/94/139 行，各 7 道附答案练习；块公式采用 `$$`；标准库核对一阶滞后值/偏导及 Rayleigh 量纲算式，无原生执行 |

源码身份与行范围只说明引用对应固定内容；AST 不验证 ABI、模板注册、Python 重载或运行语义。人工审阅中修正了 damping setter 引用起点，并把 FEM 配置与模型注册的 Python 绑定分开引用；无上游补丁或运行缺陷复现声明。主审要求进一步拒绝 tau 的 NaN/Inf，已加入 math.isfinite 并保留固定配置边界。首轮静态断言使用了 Config 的参数名来匹配 DampingModel，按实际 mass_coeff_alpha/stiffness_coeff_beta 修正后全量通过；没有放宽非负检查要求。

## 未执行与下一项

本阶段未安装/import pydrake，未构建原生 System/Plant/Diagram/Context，未执行装饰器注册、scalar conversion、AD/symbolic 求值、梯度检查、优化 Solve、柔性体/刚体接触、仿真、渲染、训练、benchmark 或独立实验。没有生成状态轨迹、梯度结果、图像或性能数字；未检测本机 solver 是否安装/可用。

不改变 DexLab [#117](https://github.com/huangkiki/Dexlab/issues/117) 的运行资格；后续实验仍复用 DexLab。建议下一项 E7，按两条路线全文审校、明确 A0 剩余内容并整理证据入口；本阶段未启动，开始前须重新核实最新 main、Issue/PR 和 E2–E6 实际合入。
