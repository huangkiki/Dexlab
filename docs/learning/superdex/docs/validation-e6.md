# E6 验证与范围记录

任务：[SuperDex E6 #7](https://github.com/huangkiki/superdex-atlas/issues/7)。起点 actual main/origin/main 为 `28ce02a186d89fbf3cc4418aaa2dbdf4474c032c`，工作树干净、无在途 PR；E3 依赖 `5a58da78d3a44f189c7974d8630283b5aed614f7` 实际在 main。分支为 `docs/e6-extensions-boundaries`，检查日期2026-10-09。本记录与章节同一提交保存，精确提交由文件历史和交付记录定位。

官方源码固定为 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。新增内容没有引入新的外部实现版本；E4 Polyscope、E5 Gymnasium 的独立来源继续保留。C++ 功能、Python 绑定、构建开关、包身份与实际运行能力分别记录。

**未执行 native import、安装、模型编译、JIT、物理/反向求解、渲染、实验、训练、性能基准或独立评分器。** 原生例子与上游测试均只阅读/做文本或语法核验，不将它们的存在写成运行通过。

## 验收对应

| 范围 | 交付位置 | 核对内容与限制 |
|---|---|---|
| B6 特色 Actor | [专题](extensions-boundaries.md)第1–4节 | soft四面体FEM、本构能量/量纲、公开NeoHookean到Smith的分派、per-element覆盖、PSD与Kelvin–Voigt阻尼；shell/rod材料量纲、状态、约束和tendon区别 |
| 原生降阶与构建 | 第4节 | skinning能量/frame、ROM残差/切线投影、hyper-reduction、NeuralNetCrom直接分支deprecated、Deep Flow形状映射；feature gate与Python缺失rom字段 |
| 几何与精度 | 第5节 | colliding/collider方向、soft Auto/Sdf门限、PointCloud半径/积分量纲、自接触排除、FP64与采样/模型/步长误差分离、recentering |
| B4 可微内部深化 | 第6–7节 | rigid/articulated和skinning限制、make-differentiable配置改写、相邻step状态、adjoint符号与单位、derived-state传播、有限差分HVP/Lie transport、PCG/MINRES/Newton实际分支 |
| 查询导数和完整矩阵 | 第7–8节 | 力查询VJP关闭PSD/fitted近似、动作反作用与采样权重；full step Jacobian的rigid-only、三状态与column-major契约；reverse会修改Scene |
| B7 综合源码链 | 第9节 | soft字段→初始化/本构/接触/求解→节点与力输出；articulated target→link loss→adjoint→输入梯度；所有模块关联既有E1–E5 |
| 多物理和外部能力边界 | 第4、10节 | active材料/pressure/Deep Flow不自动构成电生理/流体/热/电磁场求解；Physics/Robotics/Lab/Studio职责，未虚构插件、Torch graph或Python自定义材料API |
| 原创最小原生例子 | [backward_one_force_step.py](../examples/backward_one_force_step.py)与第8节 | 一对已有原生step快照的反向调用；7维COM梯度、唯一DoF indices、诊断开关与状态副作用；仅AST检查 |
| 易错点与阅读练习 | 第11节 | 12项易错点、20道带答案练习；不要求实验、不产生数值结果或分数阈值 |
| 入口/课程/来源 | README中英、guide/curriculum/roadmap、source-map/sources.json | 保留Sim Atlas总仓入口；E7仍保留A0安装专题、全路线审校和DexLab完整复用索引 |

## 实际静态检查

- `git diff --check` 通过。
- `python scripts/check_docs.py` 通过，检查仓库内Markdown相对链接。
- 全部182个SuperDex manifest文件逐一与固定Git tree的path/blob匹配，并对实际缓存字节重算Git blob SHA-1；本项新增34个文件。
- 既有13个外部文件继续与各自固定Git tree/blob/字节核对，其中Polyscope相关6个、Gymnasium7个；未将外部身份混进SuperDex核心版本。未复制上游代码文件进入本仓。
- Markdown中4个上游的固定blob链接涉及195个文件，逐一检查manifest覆盖、固定commit、reference-style定义与5个既有行号锚点范围。
- 全部7个仓库Python文件和3个完整Markdown Python块经 `ast.parse` 通过；没有执行语法检查对象，没有使用import或模型编译充当语法检查。
- 新章节/验收及既有E5文件逐字节检查，不含TAB或其他非换行控制字符；全仓Markdown无异常控制字符。数学公式逐段复核，使用独立的 `$$` 展示公式，未以运行输出冒充推导。
- 自审核对原生字段/工厂/装配实现、壳和杆的量纲、ROM与binding门限、diffsim调用顺序、7维输出与Lie梯度、反向状态副作用、有限差分尺度及PCG回退条件。材料身份由公开alias→枚举选择→类型factory→响应函数补成闭环，未停留在同名文件猜测。
- 主审预读提出B4状态措辞应与E3验收一致，已改为“深化B4、补齐B6、提供B7两条追踪”；E7最终审校保持未完成。最终主审和远端集成由主任务独立执行，本记录不预先宣称通过。

## 未验证项与交付边界

本阶段完成源码课程和静态检查，没有软体/壳/杆的数值精度、材料拟合、ROM误差或速度、Deep Flow资产/wheel可用性、所有feature组合、接触稳定性、完整梯度正确性或优化收敛结果。尤其 `finite_diff_valid` 检查的是HVP尺度一致性，关掉诊断时的默认true不构成梯度证明；前向/反向/预条件三个求解层的误差也不能合并成单个“通过”标记。

原生例子假设已创建可微Scene、兼容动态独立rigid Actor、同Scene快照和收敛的恒定步长前向step。调用会实际求解并修改Scene/adjoint，未作事务性恢复，也不是多步训练wrapper。公开full Jacobian与reverse支持范围不同；当前证据不能用来证明软体、shell、rod、ROM或skinning可走这条反向链。

多物理缺口按本章检查的公开创建接口、experimental头和初始化实现限定；未对整个软件生态作“永不支持”的推断。未审查外部Torch/流体/学习框架的具体实现，不补造API或宣称端到端autograd。当前源码不能回填DexLab历史二进制、求解配置或 #124 结果。

下一项建议是E7：待E2–E6实际在main核实后，完成A0安装/版本身份课程、两条路线与最小例子的最终审校、DexLab已有材料复用索引。E6只本地交付；远端推送、Issue/Project、总仓及Obsidian均由主任务在主审后处理，当前未自行启动E7。
