# E3 验收与后续任务

对应 [Issue #4](https://github.com/huangkiki/genesis-atlas/issues/4)，从已发布E2的main `02119f7226bd99c57e4ba1166bba1be09c6afb8a` 开始。E1前置章节已实际存在于该base，未仅凭Issue状态推断。记录日期：2026-10-09。

交付 [接触、求解器与力观测](contact-solvers-forces.md)与原创 [contact_readback.py](../examples/contact_readback.py)，同步中英README、课程、roadmap和来源manifest。README正文Sim Atlas名称链接系列总仓。没有复制第三方资产或代码，原创示例沿用本仓Apache-2.0许可。

## 覆盖与边界

| 单元 / Issue要求 | 实际交付 |
|---|---|
| A4 接触API | 第3–5、8–9节：碰撞表示/过滤、材料组合、sol_params setter、contact mask/frame/所有权与net force |
| B0 动力学 | 第2节：广义方程、质量/armature/阻尼、空间字段、LDLᵀ与约束数据映射 |
| B1 一步源码 | 第1–2节：配置解析、真实分派、纯刚体/耦合路径、检测/装配/求解/积分顺序 |
| B2 接触模型 | 第4–5节：max/平均组合、阻抗与参考加速度、pyramid/elliptic、convex/signorini、spin/rolling |
| B3 求解与停止 | 第6节：目标/梯度/Hessian、Newton/预条件CG、line search、warmstart、逐岛退出、noslip |
| B4 积分与数值 | 第7、10节：三种积分器、自由体midpoint特例、timeconst floor、精度与可微限制 |
| B5 力/冲量 | 第8节：A/B符号、世界线力、点力矩与纯偶矩缺项、采样阶段、子步积分与休眠旧值 |
| 其他物理分支 | 第10节明确Legacy/SAP/IPC分派与不同变量；多物理本构、SAP handler、外部IPC核心及adjoint专门推导仍留E6 |
| 练习与例子 | 12题附答案、1个完整配置围栏、原生接触读取例；例子未执行，未新增场景或实验 |

这些是知识交付，不是物理/性能验收。DexLab历史#125保持待核实；本提交的默认值、算法路径及缺项不会被写回为历史测量配置。E4–E7仍显示待开发。

## 静态检查

| 检查 | 状态 | 证据含义 |
|---|---|---|
| `git diff --check` | 通过 | 空白/冲突标记 |
| `python scripts/check_docs.py` | 通过 | Markdown相对链接目标 |
| Python AST与完整Markdown Python围栏 | 通过：4个Python文件、1个完整围栏 | 仅语法；不import或执行原生引擎 |
| 固定源码SHA、manifest与Git blob/tree核对 | 通过：53个blob、224个固定源码链接 | 文件身份、路径、行号范围及reference定义 |
| 公式/API执行链自审 | 已完成，待主agent独立复核 | 配置→派生/solver→kernel；未获独立主审批准 |

源码缓存只作为审查输入，不随仓库交付。新来源在独立E3工作目录，来源身份使用Git blob SHA1重新计算，与固定提交tree及sources.json交叉核对。旧E1/E2资产保持原样。

首次来源检查发现solver_breakdown.py与solver.py两处引用终点超过文件末行，已缩回实际函数范围并重新通过。静态检查还复核现有原创URDF结构/惯量，不将这些结果称为资产运行验收。检查结果绑定本阶段最终提交；如主审修改内容，应重跑受影响检查。

## 发现与复盘

- `friction_cone`、`contact_resolution`、constraint_solver、integrator与coupler分别记录；elliptic+Newton的默认解析不能无条件外推。
- 停止函数实际用每岛质量trace；不沿用build注释里的free-motion cost表述。
- signorini半径逐轮重锁存，停止要求与convex不同；有限迭代不能宣称达到理想硬互补解。
- 原生刚体摩擦与coup_*语义分开；spin/rolling系数为长度量，公开contact dict缺纯偶矩。
- 步后姿态、接触、笛卡尔加速度及控制重算getter属于不同阶段；休眠保存旧支撑力。
- 非Euler自由体midpoint是有资格条件的另一条积分分支，其Newton不能混作constraint_solver。

建议下一项 **E4 传感器、渲染与可视化**，承接采样frame/时点；E5依赖E4实际交付。E6继续本章列明的多物理/SAP/IPC/可微内部细节，E7统一版本/来源与课程覆盖审校。当前本地切片须经主agent复核发布，未推送、未更新远端Issue/Project或其他仓库。
