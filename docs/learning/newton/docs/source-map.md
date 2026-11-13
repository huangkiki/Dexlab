# newton-atlas 固定版本源码入口

阅读基线：`713fecdc41caf0c9d726f5c016939f36e66e3dff`。以下入口已核对官方 Git 树与文件内容身份；不是全仓审查或运行验收记录。

本阶段先理解引擎架构、建模、步进、控制、接触/求解、传感器/渲染、性能与扩展。独立实验、基准、训练和评分暂不开展，后续复用 DexLab。

| 源码文件 | 阅读目的 |
|---|---|
| [docs/guide/overview.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/overview.rst) | 核对对象职责、数据布局、参数与版本约定 |
| [docs/guide/installation.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/installation.rst) | 核对对象职责、数据布局、参数与版本约定 |
| [docs/concepts/conventions.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst) | 核对对象职责、数据布局、参数与版本约定 |
| [docs/concepts/collisions.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/collisions.rst) | 区分接触几何、接触律与数值近似 |
| [docs/concepts/worlds.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst) | 核对对象职责、数据布局、参数与版本约定 |
| [docs/solvers/index.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst) | 识别算法、输入状态、配置与限制 |
| [newton/_src/sim/model.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py) | 核对对象职责、数据布局、参数与版本约定 |
| [newton/_src/sim/state.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py) | 核对对象职责、数据布局、参数与版本约定 |
| [newton/_src/sim/builder.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py) | 核对对象职责、数据布局、参数与版本约定 |
| [newton/_src/sim/control.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py) | 核对对象职责、数据布局、参数与版本约定 |
| [newton/_src/solvers/xpbd/solver_xpbd.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py) | 识别算法、输入状态、配置与限制 |
| [newton/_src/solvers/mujoco/solver_mujoco.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py) | 识别算法、输入状态、配置与限制 |
| [newton/examples/basic/example_basic_pendulum.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_basic_pendulum.py) | 理解官方最小使用顺序；本轮不执行 |

## E1 精读入口

[正文](modeling-state-time.md)的行号链接指向下面的固定文件，身份见 [sources.json](sources.json)。重点是实现分支，而不仅是 docstring。

| 文件 | 本章具体核对内容 |
|---|---|
| [newton/_src/sim/articulation.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/articulation.py) | 关节父/子变换、COM 速度换点、eval_fk/ik 的输入输出边界 |
| [newton/_src/sim/enums.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/enums.py) | body flag 与不同 joint 的坐标/速度维度 |
| [newton/_src/solvers/solver.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py) | 半隐式预测、局部惯量、kinematic 传递、base reset no-op |
| [newton/_src/utils/import_urdf.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_urdf.py) | visual/collision 分离，显式质量、惯量与 scale |
| [newton/_src/utils/import_mjcf.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_mjcf.py) | 角度/四元数解析，显式 inertial 与缩放 |
| [newton/_src/utils/import_usd.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/utils/import_usd.py) | 非单位 metadata 的不同路径及 legacy 刚体限制 |
| [newton/_src/geometry/inertia.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/inertia.py) | box 质量/惯量、旋转与平行轴定理 |
| [newton/_src/math/spatial.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/math/spatial.py) | Newton/Warp 空间量排列适配、换点和换系 |
| [newton/_src/solvers/xpbd/kernels.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py) | 以实际 COM 力臂与叉积核对 conventions 的符号冲突 |

E1 还精读上表已有的 builder.py（构建/导入/finalize）、model.py（状态/控制分配）、state.py（字段/assign）、control.py（FREE/DISTANCE 力约定）、XPBD step 与 MuJoCo reset。上游 conventions 存在本章记录的两处符号不一致，不能仅凭文件身份哈希认为其中所有公式都正确。

## E2 精读入口

[控制、机器人与任务专题](control-robotics-tasks.md)从公开导出、参数、执行分支追到输出数组。以下新增文件与 E1 的 builder/control/XPBD/MuJoCo 入口共同构成 E2 来源；仅核对所引关键分支，不宣称全文件全部功能审查。

| 文件 | 本章核对目的 |
|---|---|
| [docs/concepts/actuators.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/actuators.rst) | 原生概念、公开使用流程与当前版本限制 |
| [docs/concepts/articulations.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/articulations.rst) | 原生概念、公开使用流程与当前版本限制 |
| [docs/concepts/sites.rst](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/sites.rst) | 原生概念、公开使用流程与当前版本限制 |
| [newton/_src/actuators/actuator.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/actuator.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/clamping/clamping_max_effort.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/clamping/clamping_max_effort.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/delay.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/delay.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/drives/drive_pd.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/drives/drive_pd.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/drives/drive_pid.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/drives/drive_pid.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/effort_mode_explicit.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/effort_mode_explicit.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/actuators/effort_mode_implicit.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/actuators/effort_mode_implicit.py) | Drive、Delay、Clamping、显式/隐式 effort、状态和输出生命周期 |
| [newton/_src/controllers/impl/_common.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/_common.py) | 模型型端口、工具 Jacobian 换点、DLS/阻抗的实际输出与能力边界 |
| [newton/_src/controllers/impl/differential_ik/_common.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/_common.py) | 模型型端口、工具 Jacobian 换点、DLS/阻抗的实际输出与能力边界 |
| [newton/_src/controllers/impl/differential_ik/model_based.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/model_based.py) | 模型型端口、工具 Jacobian 换点、DLS/阻抗的实际输出与能力边界 |
| [newton/_src/controllers/impl/differential_ik/model_free.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/differential_ik/model_free.py) | 模型型端口、工具 Jacobian 换点、DLS/阻抗的实际输出与能力边界 |
| [newton/_src/controllers/impl/joint_impedance/model_based.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/impl/joint_impedance/model_based.py) | 模型型端口、工具 Jacobian 换点、DLS/阻抗的实际输出与能力边界 |
| [newton/_src/controllers/joint_selection.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/joint_selection.py) | 关节 compact 映射、标签、1-DOF 限制与唯一工具 site |
| [newton/_src/controllers/tool_selection.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/controllers/tool_selection.py) | 关节 compact 映射、标签、1-DOF 限制与唯一工具 site |
| [newton/_src/sim/ik/ik_lm_optimizer.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_lm_optimizer.py) | 目标、residual、候选/采样、LM 与 scalar 限位的实现 |
| [newton/_src/sim/ik/ik_objectives.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_objectives.py) | 目标、residual、候选/采样、LM 与 scalar 限位的实现 |
| [newton/_src/sim/ik/ik_solver.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/ik/ik_solver.py) | 目标、residual、候选/采样、LM 与 scalar 限位的实现 |
| [newton/_src/solvers/featherstone/kernels.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/kernels.py) | 目标/广义力的具体消费者、内置驱动与限位路径 |
| [newton/_src/solvers/featherstone/solver_featherstone.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py) | 目标/广义力的具体消费者、内置驱动与限位路径 |
| [newton/_src/solvers/mujoco/kernels.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py) | 目标/广义力的具体消费者、内置驱动与限位路径 |
| [newton/_src/solvers/semi_implicit/kernels_body.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_body.py) | 目标/广义力的具体消费者、内置驱动与限位路径 |
| [newton/_src/solvers/semi_implicit/solver_semi_implicit.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/solver_semi_implicit.py) | 目标/广义力的具体消费者、内置驱动与限位路径 |
| [newton/actuators.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/actuators.py) | 公开导出与实验性 API 边界，防止把内部 helper 当公共入口 |
| [newton/controllers.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/controllers.py) | 公开导出与实验性 API 边界，防止把内部 helper 当公共入口 |
| [newton/examples/controllers/example_controller_differential_ik.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/controllers/example_controller_differential_ik.py) | 核对官方示例是运动学展示还是物理执行；不运行、不复制资产 |
| [newton/examples/ik/example_ik_franka.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/ik/example_ik_franka.py) | 核对官方示例是运动学展示还是物理执行；不运行、不复制资产 |
| [newton/ik.py](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/ik.py) | 公开导出与实验性 API 边界，防止把内部 helper 当公共入口 |

E2 特别区分：`eval_ik` 状态重建与 `newton.ik.IKSolver` 目标优化；controller 输出接 State 的展示与接 Control 的动力学链；模型 effort_limit、单 actuator clamp 和任意外部力输入的不同作用范围。

## E3：接触生成到力读回

[专题正文](contact-solvers-forces.md)沿以下入口区分几何、材料、积分、求解和观测。链接都指向同一个 Newton 固定提交；可运行行为仍未验收。

| 入口 | 本章实际核对 |
|---|---|
| [CollisionPipeline.collide](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/collide.py#L2137-L2433) | 计数/AABB、过滤/broad phase、writer/narrow phase、matching/sort；容量不能当活跃数 |
| [Contacts](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contacts.py#L253-L432) | body-local support 点、world 法线、margin、可选 spatial force 契约 |
| [碰撞过滤](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/broad_phase_common.py#L234-L282) | world 与带正负号的 collision group，和位掩码区分 |
| [hydroelastic reduction](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/contact_reduction_hydroelastic.py#L983-L1017) | 压力面积积分、等效刚度和 reduction 的有限表示 |
| [XPBD.step](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L389-L569) | 临时 joint force、预测积分、位置/速度阶段 |
| [XPBD contact kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2304-L2504) | 算术材料组合、增量摩擦、COM 力臂、实际 count weighting |
| [恢复 manifold](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/restitution_kernels.py#L416-L565) | 固定内外迭代、首轮有界负增量与后续非负约束 |
| [XPBD force readback](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py#L1060-L1116) | 等效 impulse/h；组成和 lifecycle 限制 |
| [penalty kernel](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L413-L556) | SemiImplicit/Featherstone 的均值、覆盖、法向/摩擦与 body force 写入 |
| [Featherstone 矩阵](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/solver_featherstone.py#L765-L940) | H、armature、Cholesky、缓存更新周期 |
| [MuJoCo contact 转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/kernels.py#L123-L187) | priority/solmix/max friction 与 solref；非统一平均 |
| [VBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L144-L174) / [原生力读回](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L3705-L3762) | compliant ALM/legacy 与 body1 力，不冒充通用 Contacts.force |
| [Kamino 配置](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/config.py#L470-L611) / [PADMM 收敛](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/solvers/padmm/kernels.py#L1343-L1367) | 原生 residual 与单位、预算停止/收敛、warm start |
| [Kamino COM wrench](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/geometry/contacts.py#L1265-L1296) | 方向与 COM 参考点转换 |
| [SensorContact](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L90-L155) / [构造器](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py#L453-L487) | 只消费线性力；聚合、friction 分解及加权中点 |
| [contact kinematics](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/contact_kinematics.py#L35-L78) / [公开出口](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/__init__.py#L1-L120) | 几何重建与冻结接触集合导数边界，核实公开 API |

### 外部依赖单列

为核对 Newton adapter 实际调用，本章读取 [独立 MuJoCo-Warp 依赖清单](e3-dependency-sources.json)。官方固定 commit 与 Newton uv.lock 锁定的 sdist 逐文件对照通过；它没有混入只代表 Newton 的 sources.json。

- [contact_force_fn](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/support.py#L352-L391)：contact wrench 的 world 旋转，没有 COM 换点；与 Newton adapter 合看才确定固定组合的限制。
- [后端停止规则](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/solver.py#L3432-L3496)：scaled improvement/gradient 与 iteration 上限，不能译成物理穿透容差。

- [积分器分支](https://github.com/google-deepmind/mujoco_warp/blob/087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7/mujoco_warp/_src/forward.py#L353-L612)：Euler damping、RK4、多种速度隐式矩阵和状态推进；积分器与约束优化器分别选择。

专题正文和 [E3 验收](e3-validation.md)保留源码发现与未决项；源码身份核对不等于整文件或全部后端通过物理测试。

## E4：观测 producer、相机几何与显示后端

[专题正文](sensors-rendering.md)将申请存储、producer、更新时间和 consumer 分开；没有 native import、渲染或物理执行。以下为固定实现的阅读入口，具体行号见正文。

| 入口 | 本章实际核对 |
|---|---|
| [公开 sensor 导出](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/sensors.py) | 四类 sensor；不依概念页的计数字样推断额外能力 |
| [FrameTransform](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_frame_transform.py) | shape/site 配对、广播、world 相对变换、只读 body_q |
| [IMU](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_imu.py) | body_qdd 申请与消费者、COM/site 加速度、重力、输出轴 |
| [MuJoCo producer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py) | RNE 申请/禁用检查、step/FK/扩展字段转换阶段 |
| [Contact](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_contact.py) | flat sensing rows、per-world counterpart 列、可选 State 与缓存清理 |
| [shape BVH](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py) | VISIBLE 默认 mask、build/refit、model 共享缓存 |
| [射线查询](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/geometry/raycast.py) | newton.intersect_ray 的 world/global roots、距离/normal/miss |
| [TiledCamera](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/sensor_tiled_camera.py) | 七类通道、输入输出维度、sync_transforms 范围 |
| [相机射线](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/camera_utils.py) | pinhole/标定反解、坐标轴、像素中心、无效零射线 |
| [图像工具](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/utils.py) | 输出分配、原始图像与显示 RGBA 变换 |
| [render/context](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render_context.py) | 是否存在几何、shape 校验、复用输出与实际 launch |
| [render writer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/render.py) | ray/forward depth、world normal、hit/miss 与禁用反传 |
| [默认值/特殊 ID](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sensors/warp_raytrace/types.py) | ClearData、RenderConfig；另沿 raytrace.py 识别集合 ID |
| [ViewerBase](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer.py) | begin/log/end 与显示布局；log_image 基类 no-op |
| [GL viewer](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_gl.py) | log_image override、最后 framebuffer RGB、host/GPU 读回 |
| [GL context](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/gl/opengl.py) | headless 仍建立隐藏图形上下文 |
| [RTX adapter](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_rtx.py) | OVRTX/OVStage 依赖和异步呈现上一帧 |
| [File recording](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py) | 克隆直接 State 数组；不同于完整 solver checkpoint |
| [USD samples](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_usd.py) | int(time*fps) 量化与 close 保存 |
| [宿主与显示指南](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/visualization.rst) | Rerun/Viser/RTX/文件模式和上游验证边界 |

来源身份、静态检查、保留问题与下一阶段见 [E4 验收](e4-validation.md)。没有把图像尺寸、数组分配或窗口存在当作有效观测证明。

## E5：world 隔离、学习时序与数据生命周期

[专题正文](batch-learning-data.md)与[静态例子](../examples/e5_world_reset_snapshot.py)串起实体布局、选择性重置、策略输入和保存/回放。

| 入口 | 本章实际核对 |
|---|---|
| [worlds](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst#L117-L168) / [replicate](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L3130-L3220) | B+2 starts、global 前后段、复制对象生命周期、同构/异构边界 |
| [Control.clear](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py#L76-L117) / [State.assign](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py#L202-L255) | target quaternion、全量与局部 reset、namespace 与 graph 地址 |
| [MuJoCo.reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py#L4180-L4312) / [VBD.reset](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L2370-L2425) | 权威状态、flags、后端历史和更新阶段；基类/XPBD 不是自动恢复初值 |
| [policy](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L75-L170) / [推进顺序](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/robot/example_robot_policy.py#L325-L417) | 12+3n 观测、关节映射、外部 ONNX、capture 范围、物理/展示时间差异 |
| [ViewerFile](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/viewer/viewer_file.py#L1201-L1297) | 顶层 State clone、Model 引用、playback 别名、缺失的 checkpoint/时间信息 |
| [custom attributes](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/custom_attributes.rst#L858-L923) | 归属/频率/namespace、合并时实体和 world 引用重映射 |
| [Warp runtime](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L1536-L1606) / [CPU graphs](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/runtime.rst#L1850-L1952) | 不重放任意 Python；CPU graph 的实验性与操作集合 |
| [Warp 数组](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/types.py#L4521-L4559) / [Torch 互操作](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/interoperability/pytorch.rst#L44-L97) | host 读回、共享视图、同步与流、梯度所有权 |
| [Warp RNG](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/native/rand.h#L29-L81) | seed/offset、局部 RNG 状态、跨 launch 重复；不是全系统随机种子 |

Warp 身份保存在[独立清单](e5-warp-sources.json)，没有混入 Newton manifest；外部策略 runtime、Torch 和 Isaac Lab 的完整实现未在本章验收。详细保留项和检查见 [E5 验收](e5-validation.md)。

## E6：材料、原生耦合与完整导数链

[专题正文](extensions-boundaries.md)和[原创阻力例子](../examples/e6_differentiable_drag.py)以实际消费者区分共同 API 与具体算法；B7 串联前述 E1–E5 的字段到观测链。

| 入口 | 本章实际核对 |
|---|---|
| [SolverBase](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/solver.py#L538-L644) | 基类 no-op/拒绝、reset、step、读回与碰撞调度 |
| [tet forces](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_particle.py#L250-L325) | 材料参数乘体积、偏量因子；与 VBD 比较 |
| [VBD tetrahedron](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/particle_vbd_kernels.py#L173-L265) | Lamé 变换、guard、cofactor 与单顶点 block Hessian |
| [Style3D](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/style3d/solver_style3d.py#L166-L179) | 输入位置原地修改；另追 PD matrix 和 PCG 固定预算 |
| [ImplicitMPM](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/implicit_mpm/solver_implicit_mpm.py#L2875-L2970) | FEM 流变/粒子状态顺序、实际网格速度消费者；reset/隔离/graph 分支 |
| [MPM stopping](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/implicit_mpm/solve_rheology.py#L1776-L1899) | 残差缩放、检查粒度、host/graph 停止条件 |
| [Kamino DVI](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/solvers/dvi/solver.py#L745-L857) | bilateral direct solve 与着色 unilateral 迭代交替 |
| [Moreau](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/_src/integrators/moreau.py#L250-L304) | configuration 半步、midpoint forward、更新 twist 后半步 |
| [Coupling contract](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/coupling.rst#L48-L139) | ModelView、ownership、hooks、有效质量与重力责任 |
| [Proxy restart](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/coupled/solver_coupled_proxy.py#L1316-L1335) | inner iterations 重解同一区间、反馈松弛 |
| [ADMM joint mapping](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/coupled/solver_coupled_admm.py#L2530-L2637) | 支持 BALL/FIXED/REVOLUTE，跳过 FREE/DISTANCE，拒绝其他类型 |
| [ADMM local/dual](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/coupled/admm_utils.py#L737-L767) | 实际加权速度更新；dual 不冒称物理力 |
| [Warp Tape](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/warp/_src/tape.py#L70-L175) | 逆序 adjoint、loss 前提、禁用 backward 分支 |
| [Warp differentiation](https://github.com/NVIDIA/warp/blob/f2eaed82d8d03b37bf1014cc975954067fefcf16/docs/user_guide/differentiability.rst#L8-L58) | 前向覆写、梯度消费与 retain_grad 限制 |

Newton 来源进入 [sources.json](sources.json)；两项 Warp 来源独立进入 [E6 Warp 清单](e6-warp-sources.json)，与 E5 相同固定 commit。公式前提、源码缺项和静态检查见 [E6 验收](e6-validation.md)，没有以导数存储或例子语法通过代替 native/gradient 验证。
