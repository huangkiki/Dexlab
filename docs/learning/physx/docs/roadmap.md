# PhysX autodev 路线

一个阶段对应一个可恢复的 GitHub Issue；总看板统一管理六仓，仓库保留本引擎的原生设计。先查同题 Issue/PR 和实际合入状态，再继续工作。

| 阶段 | 交付切片 | 依赖 | 状态 |
|---|---|---|---|
| E0 | 双路线导航与固定版本源码导读 | 无 | 首批导读已交付 |
| E1 | 建模、坐标、状态与时间专题 | E0 | [源码课程已交付](modeling-state-time.md)，[检查与限制](validation/e1.md) |
| E2 | 驱动、机器人与任务接口专题 | E1 | [源码课程已交付](control-robotics.md)，[检查与限制](validation/e2.md) |
| E3 | 接触、求解器与力观测源码专题 | E1 | [源码课程已交付](contact-solvers.md)，[检查与限制](validation/e3.md) |
| E4 | 传感器、渲染与可视化专题 | E1 | [源码课程已交付](sensors-rendering.md)，[检查与限制](validation/e4.md) |
| E5 | 批量、学习接口与数据专题 | E2、E4 | [源码课程已交付](batch-learning-data.md)，[检查与限制](validation/e5.md) |
| E6 | 引擎特色、扩展与能力边界专题 | E3 | [源码课程已交付](extensions-boundaries.md)，[检查与限制](validation/e6.md) |
| E7 | A0 安装专题、双路线课程审校与 DexLab 复用入口 | E2–E6 | 待开发 |

E0 交付的是导读与导航，不是所有专题。E1–E6 逐个展开目录中的知识点，E7 按完整课程契约审校。依赖必须以实际文档或合入提交核实，不能仅凭 Issue 关闭。

每个 Issue 记录目标、范围、先修、固定版本/来源、交付文件、易错点、验收命令和剩余问题。本轮验收为文档链接、源码/公式核对及最小片段的语法检查；明确区分未运行、源码核对和运行验收。无新实验、训练、性能基准、跨引擎框架或评分器。

有可执行任务时按依赖推进；阻塞时记录原因和恢复条件。没有用户要求不创建定时任务。研究数据与实验最终引用 DexLab。

## E1 复盘与下一步

E1 将 A1/A2 的对象、坐标、质量属性、状态与时间契约落实到固定 SDK 源码和原生片段；B0/B4 只完成相应基础，不提前关闭 E3 的求解与积分任务。质心/根位姿注释歧义以及动态三角网格的 SDF 例外已在课程中说明。

本项合入目标分支后，E2、E3、E4 的共同先修成立。建议下一项 E2：先沿 articulation 的 joint frame、DOF 映射与状态/目标区别展开驱动和机器人控制；E3 再承接迭代、接触与力观测。执行前仍须读取各 Issue、现有 PR 和当前 main，不能仅凭本路线表推进。

## E2 复盘与下一步

E2 的 A3/A5/A7 源码课已将控制输入、驱动求解路径、机器人映射、FK/Jacobian/应用 IK 和任务时序连通。重点纠正了普通刚体 force 与持久 cache jointForce 的差别，以及旧 maxForce 和新 performance envelope 的不同限幅范围；未用控制目标或语法检查代替实际执行证明。

下一项建议 E3：用户要吃透引擎，drive 输入已经明确，接下来应解释实际接触/约束/力观测的生成与数值处理。E4 也具备 E1 先修；E5 仍需等待 E4。开始下一项前重新读取 main、Issue/PR 与依赖，本记录不自动领取 E3。当前不新增实验或运行比较。

## E3 复盘与下一步

E3 贯通 A4/B1–B5 的原生过滤、材料组合、CPU PGS/TGS 准备/求解/积分与读回。固定源码核对发现：只保留 patch friction；刚柔混合 damping 的概述与实现存在边界差异；法向点冲量、切向 anchor、CCD 缺项及未写回成点冲量的 torsion 必须分开标记。课程没有把这些接口或源码检查变成实际运行与完整力传感器验收。

建议下一切片 E4 传感器/渲染：沿本章的 frame、采样和观测覆盖边界继续，完成 E5 先修。E6 的 E3 先修仅在本项实际合入后成立；GPU 逐路径实现、特色几何与宿主差异继续在 E6，不由 CPU 公式推断。E7 再统一审校与 DexLab 证据复用。领取任务前重新查 main、Issue/PR 和依赖；本项不自动开始下一阶段，也不新增实验。

## E4 复盘与下一步

E4 完成 A6：raycast/sweep/overlap 的筛选、最近/任意与截断、query 索引更新/线程边界，关节传力/加速度的 frame 和有效性，几何 range 与光学 depth，以及 debug buffer、PVD/OmniPVD 和实际图像管线的责任。原生加速度 getter 的零值、cache 跳过滤、调试图元分阶段生成都不能无条件当作传感测量；章节与示例保留这些边界。

E2/E4 均实际合入后，下一项可领取 E5 批量、学习接口与数据：沿已定义的控制/观测/时钟契约，解释 reset、终止/截断、批量所有权和数据导出。E6 可独立继续 GPU/后端/扩展，E7 再统一审校与 DexLab 复用。领取前仍重新查 main、Issue/PR 和依赖；本记录不自动启动下一阶段。未运行传感器、renderer、GUI/headless 或新实验。

## E5 复盘与下一步

E5 贯通 A8/A9 与 B6 的调度/数据/扩展入口：独立 Scene 与同 Scene 批量的四类隔离、任务和完成边界、Direct GPU 的首步初始化/事件/scene-wide stride、CPU/GPU reset、随机化/确定性、学习宿主职责和记录/序列化/回放。特别保留了 GPU 读回 joint force 为输入值、UPDATE_KINEMATIC 清观测输出，以及容器 release 不释放反序列化对象/backing memory 的边界。

下一项建议 E6：在已实际合入的 E3 基础上解释 GPU 内核/后端、特色几何与自定义扩展的实现和能力限制，不把 E5 数据接口存在当作全后端运行证明。E7 再统一课程与 DexLab 证据入口。领取前仍核实 main、Issue/PR 和依赖；本记录不自动开始下一项。没有新训练、物理实验、性能数字或 sim-to-real 验收。

## E6 复盘与下一步

E6 完成 B6/B7 的原生扩展和综合源码课：custom geometry 的碰撞/查询/质量/生命周期、constraint row 与 connector、DistanceJoint 配置到 CPU PGS/getForce、公开 GPU 后端与 CPU fallback、FEM volume/surface、PBD particles 及可微/宿主责任。固定源码已公开 CUDA 实现，不能沿用旧版“GPU 一概闭源”的判断；eGPU_COMPATIBLE 也不是应用可打开的万能兼容开关。公式保留量纲、参考点与分支，未将源码可读或 syntax-only 变成运行验收。

下一项建议 E7：先核实 E2–E6 实际合入，再完成 A0 安装/环境专题及两条路线整体审校，统一剩余事项和 DexLab 原批次证据入口。用户仍延后引擎运行与实验，安装说明也不能自动触发 native build/import/JIT。当前只交付本地提交待主审，不自动开始 E7，不推送或修改远端状态。
