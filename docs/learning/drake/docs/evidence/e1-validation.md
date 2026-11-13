# E1 验证记录

范围：[Issue #2](https://github.com/huangkiki/drake-atlas/issues/2)「建模、坐标、状态与时间」。基于已交付 E0 的 `main` 提交 `2e6f34b4fef269cea5498546a63d61b4a3cfd87b`，在 `docs/e1-modeling-state-time` 分支完成。此记录描述本地源码教学验收，不替代后续 PR/合入状态；相应提交由本文件的 Git 历史及 Issue/PR 记录定位。

## 需求与可审查交付

| 要求 | 本项证据 | 边界 |
|---|---|---|
| 原生建模、导入、单位、资产、坐标、姿态与惯量 | [模型与坐标](../modeling-state-time.md)第 1–4 节 | 原创模型；无第三方资产复制 |
| 维度、关节映射、内存引用与所有权 | [状态与时间](../state-time.md)第 1–2 节 | double getter 与其他标量路径区分 |
| 重置、快照、缓存与恢复范围 | 状态页第 3–4 节 | 不承诺外部资源/Simulator 的完整 checkpoint |
| 连续/离散、时间步、积分器与采样 | 状态页第 5–6 节 | E1 交付语义基础，E3 仍负责完整数值/接触分析 |
| 原生例子、陷阱、阅读练习与答案 | [原创例子](../../examples/model_state.py)，两章共 13 题 | 语法/源码验证；未执行例子 |
| 两路线真实进度与英文入口 | [目录](../curriculum.md)、[路线](../roadmap.md)、[English](../../README.en.md) | A1/A2 交付；B0/B4 仅基础；E2–E7 待开发 |

## 固定源码与重点结论

官方版本 `v1.57.0` 的提交为 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，GitHub API 读回的 tree 为 `6353dc7fc1a0aec84904838e7a39a38932594597`。当前核验 32 个源文件、112 处固定源码链接。用于本文的所有官方 blob 链接均指向该提交，文件列入 [sources.json](../sources.json)。下载内容的 Git blob SHA-1 与官方树逐文件一致；已检查链接的行号不超出对应文件，并人工读取关键范围确认语义。

重点核对如下，避免沿用旧教程或仅按函数名称推断：

- `MultibodyPlant` 的 C++/Python 构造器均要求显式 time_step；只有 Config 给出 0.001 s 默认值。
- 一般 free-body setter 接受 joint parent/child frame 的相对量；本例使用显式 floating-base world pose 入口。
- `SetDefaultContext` 实现重置参数和 State，不重置 time/accuracy/fixed input；复制方法也有各自排除项。
- 根 Context 克隆、数值数组副本和外部资源 checkpoint 是不同层次。
- Quaternion floating joint 的 q 为 wxyz + translation，v 为 parent frame 中表达的 angular + linear。
- 离散 dynamics 输出默认使用最近更新的抽样 State；kinematics 输出和直接 Calc/Eval API 的当前值语义不同。
- `AdvanceTo` 的事件边界与 `AdvancePendingEvents` 的同时间状态更新不同；改时间后复用 Simulator 要 Initialize。

例子的 Python 入口另对照了 [Plant 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L531-L556)、[Plant/SceneGraph 组装绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L1481-L1497)、[Parser 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/parsing_py.cc#L112-L151)、[SpatialVelocity 参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/math_py.cc#L110-L118)、[RigidTransform 参数](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/math/math_py_monolith.cc#L60-L76)、[Context 克隆绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L517-L521)、[System 默认状态与 Context 入口绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L517-L526)。语法通过不能替代这些签名核对；签名核对也不能证明运行成功。

## 检查与未执行项

已完成的本地检查：

1. `git diff --check`：空白检查通过。
2. `python scripts/check_docs.py`：全部 Markdown 本地目标存在。
3. Python `ast.parse`：新增 Python 文件及仓库 Markdown 中完整的 Python fenced blocks 均通过，不截取“可通过”的部分。
4. 只用 Python 标准库解析原创 URDF 字符串，核对 XML 格式、mass=2、完整边长、对角惯量与均匀盒公式、惯性积为零；没有导入或执行 pydrake。
5. 所有固定源码链接的提交、文件、Git blob 身份及行范围通过核对；正文重大结论人工对照原始实现/合同，源文件总表见 manifest。
6. 人工审读课程范围、单位、公式符号、引用/副本、默认值、采样阶段和所有权，修正导读中可能暗示“构造器有缺省 time_step”的措辞。此为作者自审，不冒称独立审稿批准。

检查过程修正：首次核验脚本把“按 commit 查询 Git tree API 返回的 sha 字段”直接当作 tree 对象 SHA，断言未通过。随后从 Git commit API 读出真正的 tree SHA，并按该 tree 重新下载完整递归树；最终全部 blob、链接与语法检查通过。该失败来自核验脚本的身份假设，不是放宽文件校验。

没有执行：Python import、Parser/Finalize/Context 操作、仿真步进、碰撞/接触、GUI/渲染、硬件、基准、训练或独立物理评分。因此 ABI、依赖平台、实际 Parser 接受情况和运行数值仍未验证；不能把本记录当作 DexLab Drake 运行资格或跨引擎对照证据。

## 本项后的任务判断

A1/A2 已按本项合同展开；B0/B4 的约束装配、完整动力学、接触时间离散、稳定性/容差与可微边界继续在 E3 验收。E1 合入后 E2/E3/E4 的依赖可满足，建议先 E2 衔接驱动、机器人与任务接口。推进前必须重新检查远端 main、Issue 与已有 PR，不能从本地文档状态推断合入。当前未开始 E2。
