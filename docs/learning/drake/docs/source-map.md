# drake-atlas 固定版本源码入口

阅读基线：`1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。以下入口已核对官方 Git 树与文件内容身份；不是全仓审查或运行验收记录。

本阶段先理解引擎架构、建模、步进、控制、接触/求解、传感器/渲染、性能与扩展。独立实验、基准、训练和评分暂不开展，后续复用 DexLab。

| 源码文件 | 阅读目的 |
|---|---|
| [multibody/plant/multibody_plant.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h) | 核对对象职责、数据布局、参数与版本约定 |
| [multibody/plant/multibody_plant_config.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant_config.h) | 核对对象职责、数据布局、参数与版本约定 |
| [multibody/plant/multibody_plant.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.cc) | 核对对象职责、数据布局、参数与版本约定 |
| [multibody/plant/compliant_contact_manager.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/compliant_contact_manager.cc) | 区分接触几何、接触律与数值近似 |
| [multibody/plant/contact_model_doxygen.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_model_doxygen.h) | 区分接触几何、接触律与数值近似 |
| [multibody/contact_solvers/sap/sap_solver.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.h) | 识别算法、输入状态、配置与限制 |
| [systems/framework/context.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context.h) | 核对对象职责、数据布局、参数与版本约定 |
| [systems/framework/diagram.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram.h) | 核对对象职责、数据布局、参数与版本约定 |
| [systems/analysis/simulator.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.h) | 追踪构建、步进、数据更新与生命周期 |
| [geometry/scene_graph.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/scene_graph.h) | 追踪构建、步进、数据更新与生命周期 |
| [multibody/parsing/parser.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h) | 核对对象职责、数据布局、参数与版本约定 |
| [geometry/meshcat_visualizer.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/meshcat_visualizer.h) | 区分传感数据、可视化与物理状态 |

## E1：模型、状态与时间的追踪入口

专题：[模型与坐标](modeling-state-time.md) → [状态与时间](state-time.md)。下表补充本次实际引用的固定文件；对应行号在专题就近标注，Python 签名与源码核对范围见[验收记录](evidence/e1-validation.md)。

| 文件 | E1 阅读重点 |
|---|---|
| [bindings/pydrake/math/math_py_monolith.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/math/math_py_monolith.cc) | RigidTransform 平移构造与数学操作 |
| [bindings/pydrake/multibody/math_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/math_py.cc) | SpatialVelocity 的 w/v 参数 |
| [bindings/pydrake/multibody/parsing_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/parsing_py.cc) | Parser 原生 Python 重载与严格模式 |
| [bindings/pydrake/multibody/plant_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc) | 构造器显式 time_step、getter 引用/副本、free-body 参数 |
| [bindings/pydrake/systems/framework_py_semantics.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc) | Context.Clone Python 绑定 |
| [bindings/pydrake/systems/framework_py_systems.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc) | System.SetDefaultContext 与子 Context Python 入口 |
| [common/value.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/value.h) | abstract value 的复制/Clone 语义与外部资源边界 |
| [math/rigid_transform.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/rigid_transform.h) | X_AB、点/方向变换、RPY 与四元数入口 |
| [multibody/math/spatial_force.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_force.h) | 力矩/力排列与参考点 |
| [multibody/math/spatial_velocity.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_velocity.h) | 角/线速度排列、measured/expressed frame、参考点 Shift |
| [multibody/parsing/package_map.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/package_map.h) | 本地包映射、资源 URL 与远程资源边界 |
| [multibody/tree/joint.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint.h) | position_start 与 velocity_start 分别位于 q 和 v |
| [multibody/tree/multibody_tree.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/multibody_tree.cc) | free-body setter 实际转交 mobilizer 的路径 |
| [multibody/tree/quaternion_floating_joint.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/quaternion_floating_joint.h) | q/v 布局、parent/child frame 与速度表达 |
| [multibody/tree/spatial_inertia.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h) | 中心惯量、UnitInertia、平行轴、有效性 |
| [systems/analysis/integrator_base.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/integrator_base.h) | 连续误差控制、fixed-step 与事件边界 |
| [systems/framework/context_base.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.h) | System 与 Context 树的一一对应、Clone 根条件 |
| [systems/framework/diagram_builder.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram_builder.h) | Build 的单次使用与系统所有权 |
| [systems/framework/system.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.cc) | SetDefaultContext 实际重置的字段 |
| [systems/framework/system.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.h) | 子 Context 获取、默认状态及输入复制 API |

## E2：驱动、机器人与任务接口

专题：[驱动与机器人](control-robotics.md) → [任务接口](task-interfaces.md)。原生输入到输出/事件的引用范围见正文及[E2 验证](evidence/e2-validation.md)，本次新增以下固定文件。

| 文件 | E2 阅读目的 |
|---|---|
| [bindings/pydrake/multibody/inverse_kinematics_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/inverse_kinematics_py.cc) | Python IK Context 重载与位置约束参数 |
| [bindings/pydrake/systems/controllers_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/controllers_py.cc) | PID 的 Python 参数和端口名 |
| [bindings/pydrake/systems/framework_py_values.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_values.cc) | BasicVector 副本与数值访问 |
| [bindings/pydrake/systems/primitives_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc) | Saturation 与 ZeroOrderHold Python 参数 |
| [multibody/inverse_kinematics/add_multibody_plant_constraints.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/add_multibody_plant_constraints.h) | 关节/四元数/闭链等约束及硬软距离区别 |
| [multibody/inverse_kinematics/differential_inverse_kinematics.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/differential_inverse_kinematics.h) | 经典微分 IK 的 N(q)、速度/加速度限制和 stuck |
| [multibody/inverse_kinematics/differential_inverse_kinematics_system.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/differential_inverse_kinematics_system.h) | Systems 微分 IK 的端口与 v=qdot 限制 |
| [multibody/inverse_kinematics/inverse_kinematics.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.cc) | IK 模型约束装配与关闭 joint-limit 的实际范围 |
| [multibody/inverse_kinematics/inverse_kinematics.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/inverse_kinematics/inverse_kinematics.h) | IK 约束、Context 所有权/修改与碰撞前置条件 |
| [multibody/parsing/detail_urdf_parser.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/detail_urdf_parser.cc) | URDF transmission 与 actuator 的创建 |
| [multibody/plant/externally_applied_spatial_force.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/externally_applied_spatial_force.h) | 作用点在 B 表达、空间力在 world 表达 |
| [multibody/plant/sap_driver.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc) | PD + 前馈联合限额、SAP 净驱动读回 |
| [multibody/tree/joint_actuator.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint_actuator.cc) | 增益有限性、非负约束与关闭 controller |
| [multibody/tree/joint_actuator.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/joint_actuator.h) | actuator 输入位置、限额、增益与公开适用模式 |
| [solvers/mathematical_program.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program.h) | IK 二次代价、初值接口 |
| [solvers/mathematical_program_result.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program_result.h) | 优化结果成功状态、解与约束诊断 |
| [systems/controllers/inverse_dynamics.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/inverse_dynamics.h) | inverse dynamics 力项和重力补偿 |
| [systems/controllers/inverse_dynamics_controller.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/inverse_dynamics_controller.h) | 加速度反馈、完全驱动假设和模型参数 Context |
| [systems/controllers/pid_controller.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/controllers/pid_controller.h) | PID 状态、维度、反馈与投影 |
| [systems/framework/input_port.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/input_port.h) | Eval、FixValue 的覆盖与复制 |
| [systems/framework/leaf_system.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h) | 离散 State、周期事件和输出依赖声明 |
| [systems/primitives/saturation.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/saturation.h) | 逐元素限额与 direct feedthrough |
| [systems/primitives/zero_order_hold.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.h) | 保持状态、首次采样及初始化 |
| [bindings/pydrake/trajectories_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/trajectories_py.cc) | 三次轨迹 Python 重载与参数 |
| [common/trajectories/piecewise_polynomial.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.h) | 三次路径插值、样本列和端点导数 |
| [systems/primitives/trajectory_source.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.cc) | Context 时间求值、堆叠顺序及区间外导数 |
| [systems/primitives/trajectory_source.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.h) | 轨迹输出阶数与 System 所有权 |

## E3：接触、求解与力观测

阅读链：[材料与几何](contact-models.md) → [求解与时间](contact-solvers.md) → [力与采样](contact-observation.md)。已存在的 Plant/SapDriver/SAP 参数源码继续复用；新增入口如下。

| 固定源文件 | 本轮核对目的 |
|---|---|
| [bindings/pydrake/geometry/geometry_py_scene_graph.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_scene_graph.cc) | Python surface/normal/inspector 字段 |
| [geometry/collision_filter_manager.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/collision_filter_manager.h) | 候选对、固有排除与模型/Context manager 生命周期 |
| [geometry/proximity_properties.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/proximity_properties.h) | 材料属性与 rigid/compliant hydroelastic 构造参数 |
| [geometry/query_object.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.h) | hydro 支持对、网格、fallback 与 scalar 边界 |
| [geometry/query_results/contact_surface.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_results/contact_surface.h) | surface 身份、world 网格与弹性压力场 |
| [geometry/query_results/penetration_as_point_pair.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_results/penetration_as_point_pair.h) | 见证点、穿透与 B→A 法向 |
| [multibody/contact_solvers/contact_solver_results.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/contact_solver_results.h) | 内部力/速度/广义量，核对 ft 遗留注释 |
| [multibody/contact_solvers/sap/contact_problem_graph.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/contact_problem_graph.h) | clique、cluster 和参与图的范围 |
| [multibody/contact_solvers/sap/sap_contact_problem.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_contact_problem.h) | 线性化动量、A、v* 与 clique |
| [multibody/contact_solvers/sap/sap_friction_cone_constraint.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_friction_cone_constraint.cc) | R、near-rigid 下界及摩擦锥投影 |
| [multibody/contact_solvers/sap/sap_friction_cone_constraint.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_friction_cone_constraint.h) | 线性柔顺、relaxation time 与正则化 |
| [multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc) | Similar/Lagged 的 n0、z、cost 与 impulse |
| [multibody/contact_solvers/sap/sap_hunt_crossley_constraint.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.h) | Hunt–Crossley 近似与参数量纲 |
| [multibody/contact_solvers/sap/sap_model.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc) | cost/gradient/Hessian、负平方根缩放 |
| [multibody/contact_solvers/sap/sap_solver.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.cc) | Newton/线搜索、实际终止与 AutoDiff 隐函数路径 |
| [multibody/plant/contact_properties.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_properties.cc) | 刚度/耗散/relaxation time/动态摩擦的实际组合 |
| [multibody/plant/contact_results.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_results.h) | point/hydro/deformable 结果集合 |
| [multibody/plant/coulomb_friction.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/coulomb_friction.h) | 静态与动态摩擦的调和平均 |
| [multibody/plant/discrete_update_manager.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc) | 接触装配、面心求积、力读回与 q 更新 |
| [multibody/plant/hydroelastic_contact_info.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/hydroelastic_contact_info.h) | A 侧 centroid wrench 与 surface 所有权 |
| [multibody/plant/hydroelastic_traction_calculator.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/hydroelastic_traction_calculator.cc) | 连续 hydro traction、atan 摩擦与面积积分 |
| [multibody/plant/point_pair_contact_info.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/point_pair_contact_info.h) | B 侧力、点、分离与 slip speed |
| [bindings/pydrake/geometry/geometry_py_common.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_common.cc) | Python 材料/geometry property 接口 |
| [bindings/pydrake/geometry/geometry_py_hydro.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_hydro.cc) | Python hydroelastic 属性重载 |

## E4：传感器、渲染与时间合同

固定版本下的相机、图像绑定、时间事件、理想惯性和显示链；文档已交付、原生运行未执行。复用前期 QueryObject/SceneGraph、MultibodyPlant、SpatialForce 和 ZeroOrderHold 声明文件。新增引用如下：

| 固定文件 | 阅读目的 |
|---|---|
| [bindings/pydrake/geometry/geometry_py_render.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_render.cc) | camera、VTK 参数和 factory Python 绑定 |
| [bindings/pydrake/systems/sensors_py_accelerometer.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_accelerometer.cc) | 重力默认和缺失 AddToDiagram 绑定 |
| [bindings/pydrake/systems/sensors_py_gyroscope.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_gyroscope.cc) | gyro Python 端口与 helper 边界 |
| [bindings/pydrake/systems/sensors_py_image.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_image.cc) | HWC NumPy 视图和引用所有权 |
| [bindings/pydrake/systems/sensors_py_rgbd.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/sensors_py_rgbd.cc) | 相机和内参 Python 重载 |
| [geometry/geometry_state.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/geometry_state.cc) | camera world pose、按 renderer_name 分派与 viewpoint 更新 |
| [geometry/meshcat.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/meshcat.h) | 服务、线程、Flush 和 StaticHtml 的边界 |
| [geometry/meshcat_visualizer.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/meshcat_visualizer.cc) | publish/初始化事件及录制实现 |
| [geometry/meshcat_visualizer_params.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/meshcat_visualizer_params.h) | publish period、role、prefix 与 hydro 网格 |
| [geometry/query_object.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_object.cc) | 渲染前更新 pose/configuration 和分派 |
| [geometry/render/render_camera.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/render/render_camera.h) | 光学 pose、clipping 与有效深度区间 |
| [geometry/render/render_engine.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/render/render_engine.h) | 渲染输出与 label 注册合同 |
| [geometry/render/render_label.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/render/render_label.h) | label 语义、保留值与用户映射 |
| [geometry/render_vtk/render_engine_vtk_params.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/render_vtk/render_engine_vtk_params.cc) | 平台默认与不支持 backend 回落 |
| [geometry/render_vtk/render_engine_vtk_params.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/render_vtk/render_engine_vtk_params.h) | VTK backend 字段和显示限制 |
| [multibody/math/spatial_acceleration.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_acceleration.h) | 刚性安装点的空间加速度平移 |
| [perception/depth_image_to_point_cloud.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/perception/depth_image_to_point_cloud.cc) | 反投影、列序、float32 和无效值实现 |
| [perception/depth_image_to_point_cloud.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/perception/depth_image_to_point_cloud.h) | 类型、scale、可选 pose 与无效点合同 |
| [systems/primitives/zero_order_hold.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/zero_order_hold.cc) | 向量/abstract 状态与更新事件 |
| [systems/sensors/accelerometer.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.cc) | 加速度平移、减重力及 C++ 接线 |
| [systems/sensors/accelerometer.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/accelerometer.h) | 比力、body/frame 与默认重力 |
| [systems/sensors/camera_config.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_config.h) | renderer 类型与配置身份 |
| [systems/sensors/camera_config_functions.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_config_functions.cc) | 连续/Async 分支与 LCM publish offset |
| [systems/sensors/camera_info.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_info.cc) | 内参验证与 FOV 转换 |
| [systems/sensors/camera_info.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/camera_info.h) | 针孔、像素中心、光学坐标 |
| [systems/sensors/gyroscope.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/gyroscope.cc) | 旋转表达及端口依赖 |
| [systems/sensors/gyroscope.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/gyroscope.h) | 角速度定义、安装方向和理想模型 |
| [systems/sensors/image.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/image.cc) | 32F/16U 单位、截断与无效值转换 |
| [systems/sensors/image.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/image.h) | 像素存储、尺寸和 resize |
| [systems/sensors/pixel_types.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/pixel_types.h) | 各像素类型与哨兵常量 |
| [systems/sensors/rgbd_sensor.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.cc) | 参数、渲染调用、pose 与 image_time |
| [systems/sensors/rgbd_sensor.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor.h) | frame、图像端口及构造合同 |
| [systems/sensors/rgbd_sensor_async.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.cc) | worker 捕获、几何版本、future 和输出 |
| [systems/sensors/rgbd_sensor_async.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_async.h) | capture/output 时序、参数和线程限制 |
| [systems/sensors/rgbd_sensor_discrete.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.cc) | ZOH 接线与 image_time 导出差异 |
| [systems/sensors/rgbd_sensor_discrete.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rgbd_sensor_discrete.h) | 离散相机声明与更新时间 |
| [systems/sensors/rotary_encoders.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rotary_encoders.cc) | offset、floor 量化与参数 |
| [systems/sensors/rotary_encoders.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/rotary_encoders.h) | rad、选择/量化、采样边界 |
| [systems/sensors/sim_rgbd_sensor.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/sensors/sim_rgbd_sensor.cc) | 连续 sensor 与消息发布原生接线 |

## E5：环境隔离、随机化与数据所有权

固定源码下从 Context/Simulator 到学习端口、随机事件、记录器与回放的完整链。复用既有 simulator.h、context.h、leaf_system.h、framework_py_semantics.cc、primitives_py.cc 等登记；只完成源码与静态验收，未运行批量、学习或数据回放。新增引用如下：

| 固定文件 | 阅读目的 |
|---|---|
| [bindings/pydrake/common/default_scalars_pybind.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/common/default_scalars_pybind.h) | double 引用与其他标量复制策略 |
| [bindings/pydrake/gym/_drake_gym_env.py](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/gym/_drake_gym_env.py) | 原生学习端口、step 异常与 reset/handler/render 差异 |
| [bindings/pydrake/systems/analysis_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/analysis_py.cc) | Simulator Context 共享、GIL 与串行 MonteCarlo |
| [common/parallelism.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/parallelism.h) | 线程配置、默认串行和最大值锁存 |
| [common/random.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/random.h) | MT19937 RNG、复制与原生分布单位 |
| [common/trajectories/discrete_time_trajectory.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/discrete_time_trajectory.h) | 离散时刻定义域、容差和 ZOH 语义 |
| [multibody/tree/revolute_joint.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/revolute_joint.h) | 原生关节角随机分布 |
| [multibody/tree/rigid_body.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/rigid_body.h) | Context 质量/COM/空间惯量参数 |
| [systems/analysis/monte_carlo.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.cc) | 主线程初始化、worker 推进和索引结果 |
| [systems/analysis/monte_carlo.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/monte_carlo.h) | factory/output、RNG snapshot 与并行合同 |
| [systems/analysis/simulator.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/analysis/simulator.cc) | 时间回退校验、Context 替换与统计重置实现 |
| [systems/framework/context_base.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/context_base.cc) | 根 Context clone 与依赖指针修复 |
| [systems/primitives/random_source.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.cc) | 离散/abstract RNG 状态、事件和随机输入接线 |
| [systems/primitives/random_source.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/random_source.h) | 实例 seed、固定 seed 与采样保持 |
| [systems/primitives/vector_log.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.cc) | Reserve、扩容与样本追加 |
| [systems/primitives/vector_log.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.h) | 矩阵方向、容量、Clear 和时间值限制 |
| [systems/primitives/vector_log_sink.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.cc) | nothing_ticket 缓存、发布事件与时间戳 |
| [systems/primitives/vector_log_sink.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h) | logger trigger、根/子 Context 与日志非状态性 |
| [bindings/pydrake/common/module_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/common/module_py.cc) | Python RNG 构造与分布枚举 |
| [common/trajectories/piecewise_polynomial.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.cc) | ZOH 忽略末样本、value 时间 clamp 的实际实现 |

## E6：原生扩展、标量与特色能力

专题：[System 扩展](systems-extensions.md) → [标量与可微限制](scalar-capabilities.md) → [优化/FEM/综合源码链](engine-boundaries.md)。复用既有 Plant、SceneGraph/QueryObject、SAP、LeafSystem、System、Python Systems/Plant 绑定；下表为本轮新增固定文件。只有源码与静态验收，没有 AD、优化或柔性体运行。

| 固定文件 | 阅读目的 |
|---|---|
| [bindings/pydrake/autodiffutils/autodiffutils_py_everything.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/autodiffutils/autodiffutils_py_everything.cc) | AD 播种、值与梯度提取的原生 Python 绑定 |
| [bindings/pydrake/multibody/fem_py.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/fem_py.cc) | FEM 材料枚举与配置的实际 Python setter/getter |
| [bindings/pydrake/systems/scalar_conversion.py](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/scalar_conversion.py) | TemplateSystem 构造、copy 和 converter 注册契约 |
| [common/ad/auto_diff.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/ad/auto_diff.h) | 当前 Drake AD 的数值、动态偏导和常量语义 |
| [common/autodiff.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/autodiff.h) | AutoDiffXd 当前别名身份 |
| [geometry/optimization/graph_of_convex_sets.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/optimization/graph_of_convex_sets.h) | GCS 凸松弛、rounding 及最优性边界 |
| [math/autodiff.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/autodiff.h) | 导数播种顺序和矩阵展开 |
| [multibody/fem/damping_model.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/damping_model.cc) | 下游 Rayleigh damping 实际入参非负检查 |
| [multibody/fem/damping_model.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/damping_model.h) | 质量/刚度阻尼、单位和模态阻尼比 |
| [multibody/fem/deformable_body_config.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/fem/deformable_body_config.h) | 本构、默认参数及 damping setter 旧值检查差异 |
| [multibody/mpm/BUILD.bazel](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/mpm/BUILD.bazel) | 内部 MPM 目标可见性及尚待公开的集成边界 |
| [multibody/mpm/mpm_model.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/mpm/mpm_model.h) | 内部 MPM 状态、backward-Euler 能量与对象归属 |
| [multibody/plant/deformable_driver.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_driver.cc) | free FEM、Schur complement 与接触后状态恢复 |
| [multibody/plant/deformable_model.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.cc) | double/discrete/SAP 约束与柔性时间积分 |
| [multibody/plant/deformable_model.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/deformable_model.h) | 注册、节点状态矩阵、约束与空模型标量转换 |
| [multibody/plant/propeller.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/propeller.h) | 原生推力/反扭矩模型、端口与无状态边界 |
| [multibody/plant/wing.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/wing.h) | 平板气水翼系数、空间力输入输出及单位 |
| [multibody/tree/deformable_body.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/deformable_body.cc) | FEM 单元、本构和离散 q/v/a 状态装配 |
| [multibody/tree/force_density_field.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_density_field.h) | 体积力场的 Context 资源及参考体积重力 |
| [multibody/tree/force_element.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_element.h) | 刚体力、能量、功率与 scalar clone 扩展责任 |
| [planning/trajectory_optimization/direct_collocation.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_collocation.cc) | 连续状态和 abstract 输入的实际拒绝点 |
| [planning/trajectory_optimization/direct_collocation.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_collocation.h) | 配点假设、AutoDiff 与 Context/输入生命周期 |
| [planning/trajectory_optimization/direct_transcription.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/direct_transcription.h) | 单周期离散或 Forward Euler 连续路径 |
| [planning/trajectory_optimization/kinematic_trajectory_optimization.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/planning/trajectory_optimization/kinematic_trajectory_optimization.h) | B-spline 路径、时长与 qdot 约定 |
| [solvers/mathematical_program_doxygen.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/mathematical_program_doxygen.h) | 优化程序对象与问题结构 |
| [solvers/solve.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/solve.h) | MathematicalProgram 求解后端分派 |
| [solvers/solver_interface.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/solvers/solver_interface.h) | available/enabled/问题属性与解成功的区别 |
| [systems/framework/diagram.cc](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram.cc) | 整图 scalar converter 能力交集 |
| [systems/framework/scalar_conversion_traits.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/scalar_conversion_traits.h) | 有向转换支持和丢失标量信息的边界 |
| [systems/framework/system_scalar_conversion_doxygen.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system_scalar_conversion_doxygen.h) | System 转换、Context 复制和独立播种顺序 |
| [systems/primitives/multilayer_perceptron.h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/multilayer_perceptron.h) | 原生网络 Context 参数与解析 backprop |
