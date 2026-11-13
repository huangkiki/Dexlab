# E2 验证记录

对应 [Issue #3](https://github.com/huangkiki/drake-atlas/issues/3)。已核实 E1 基线 `d679d6235330901d5ff91eefd5b5450149cc43eb` 同时存在于本地 main 和 origin/main，无进行中 PR；在 `docs/e2-control-robotics` 分支实现。本记录说明本地内容与静态验收，提交由 Git 历史定位，远端交付状态由主任务另行核实。

## 合同与交付

| 验收要求 | 可审查文件 / 范围 |
|---|---|
| A3：输入到驱动、单位、索引、限额、PD、回调周期 | [驱动与机器人](../control-robotics.md)第 1–2 节；sampled_pd.py |
| A5：资产/关节映射、FK/Jacobian/IK、限位、外部控制边界 | 同页第 3–4 节；arm_kinematics.py |
| A7：任务阶段、观察合同、时序、异常、原生 State/事件 | [任务接口](../task-interfaces.md)；task_sequencer.py |
| 公式假设、易错点、带答案练习 | 两章共 14 题；两杆解析模型、PD 与 inverse dynamics 单位分开 |
| 中文课、英文入口、真实课程状态和系列总入口 | README 中英文、curriculum、roadmap、versions、examples/README |
| 固定源码与实现核对 | [source-map](../source-map.md)、[sources.json](../sources.json)，全部 blob 链接固定同一提交 |

核心与绑定基线均是 Drake v1.57.0 官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，tree `6353dc7fc1a0aec84904838e7a39a38932594597`。源码身份不等于本地 wheel、编译选项或运行能力；没有以宿主版本代替核心版本。

## 核对的关键路径

1. Plant 实例输入装配 → 全模型输入相加 → effort clipping；SAP PD 约束使用未单独截断的前馈，加反馈后执行总限额，并从 solver 结果回读净驱动。
2. input_start、q/v 起点、实例内 actuator 顺序各自独立；URDF effort 暂存与 transmission 创建 actuator 的路径；原创例子选择显式 actuator。
3. FixValue 会覆盖已连接的端口源并复制输入；PID、限幅、ZOH 的状态/时序分别解释，未声称自动 anti-windup。
4. FK 和 Jacobian 的 TCP、measured/expressed frame、kV/kQDot 与行排列。
5. IK 构造装配模型运动学约束、Context 会被修改、碰撞约束需要 Diagram/SceneGraph 查询环境；classic 与 Systems differential IK 的能力边界分开。
6. PiecewisePolynomial → TrajectorySource → PID 的参考接口、绝对 Context 时间和导数堆叠；轨迹平滑不等于动态可行。
7. 原生 LeafSystem 的事件读旧 Context、写 next State；output 的依赖声明只对应实际读取；Fault 与框架 EventStatus.Succeeded 分开。

签名另外对照 [PID 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/controllers_py.cc#L256-L285)、[Saturation 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L492-L496)、[ZOH 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L705-L718)、[IK 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/inverse_kinematics_py.cc#L75-L103)、[Jacobian 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L658-L672)、[BasicVector 副本](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_values.cc#L55-L66)、[输出依赖绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L893-L910)、[离散状态声明绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L1155-L1169)。IK 代价/初值对照 [MathematicalProgram](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program.h#L1117-L1148)及其 [SetInitialGuess](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program.h#L3181-L3200)。

## 实际验证

- `git diff --check` 和 `python scripts/check_docs.py`：通过；本地 Markdown 目标存在。
- 4 个 Python 示例文件及 Markdown 中 3 个完整 Python fenced blocks 用 `ast.parse` 检查：通过；没有执行 imports、examples 或被检查的 callback。
- 标准库提取原创 ARM_URDF 并解析 XML：核对两关节 parent/child、轴/原点/限位、两个 link 的中央惯量及质心、无 transmission/碰撞几何。用均匀盒公式核对中央惯量，用两杆几何公式检查文中的解析 TCP/Jacobian 结论；不调用引擎。
- `sources.json` 中 59 个文件的 Git blob 与固定官方 tree 一致；201 处官方 blob 引用均使用固定提交、已收录路径和有效行号。重大语义另人工读函数实现/合同，不能用行号检查替代结论核对。
- 作者自审：课程覆盖、索引和坐标、力/加速度反馈增益单位、采样时序、规划 Context 独立性、状态机终止/故障语义和英文状态一致。未声称独立 reviewer 批准。

取源过程中一次旧目录猜测导致 externally_applied_spatial_force 路径 404，已由固定 Git tree 定位为 `multibody/plant/`；一次新缓存父目录缺失造成写入失败，创建对应目录后按同一 blob 重新核对。保留失败原因，没有更换版本或放宽校验。

## 限制与下一项

没有运行模型构建、FK/Jacobian、IK 求解、控制、任务事件、碰撞、传感、GUI、实验、训练或性能基准。源码与语法不能证明数值、依赖 ABI、控制稳定性或抓取成功；所有目标/阈值仅教学用。任务例子没有机械臂参考生成器、接触传感源或通用安全动作，接口边界在正文明确给出。

内建 PD 的公开头文件合同限定离散 Plant，当前实现还包含连续净驱动计算代码；本课不以代码分支存在扩大公开支持范围，也不声称已运行验证连续内建 PD。若后续需要该配置，应单独审校其实际支持边界。

下一项建议 E3：讲清接触模型、求解和力观测，给 E2 状态机的 force/slip 观测提供准确原生语义。E4 负责传感/渲染；E5 仍依赖 E4。推进前重新核实 main、Issue 和 PR；本项未启动 E3，实验与评分继续复用 DexLab。
