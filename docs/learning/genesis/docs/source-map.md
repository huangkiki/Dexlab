# genesis-atlas 固定版本源码入口

阅读基线：`216a708e06124595521a9d36a51fae5393fd4ff8`。以下入口已核对官方 Git 树与文件内容身份；不是全仓审查或运行验收记录。

本阶段先理解引擎架构、建模、步进、控制、接触/求解、传感器/渲染、性能与扩展。独立实验、基准、训练和评分暂不开展，后续复用 DexLab。

| 源码文件 | 阅读目的 |
|---|---|
| [genesis/__init__.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py) | 核对对象职责、数据布局、参数与版本约定 |
| [genesis/engine/scene.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py) | 追踪构建、步进、数据更新与生命周期 |
| [genesis/engine/simulator.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py) | 追踪构建、步进、数据更新与生命周期 |
| [genesis/options/solvers.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py) | 识别算法、输入状态、配置与限制 |
| [genesis/engine/entities/rigid_entity/rigid_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py) | 核对对象职责、数据布局、参数与版本约定 |
| [genesis/engine/solvers/rigid/constraint/solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py) | 识别算法、输入状态、配置与限制 |
| [genesis/engine/solvers/rigid/constraint/noslip.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/noslip.py) | 识别算法、输入状态、配置与限制 |
| [genesis/engine/solvers/rigid/rigid_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py) | 识别算法、输入状态、配置与限制 |
| [genesis/vis/camera.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py) | 区分传感数据、可视化与物理状态 |
| [genesis/options/sensors/tactile.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py) | 核对对象职责、数据布局、参数与版本约定 |
| [examples/tutorials/hello_genesis.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/hello_genesis.py) | 理解官方最小使用顺序；本轮不执行 |

## E1 新增阅读入口

下面的文件身份已核对；阅读重点限定为最后一列，不代表完整算法均已审查。专题内给出固定行链接。

| 源码文件 | 阅读目的 |
|---|---|
| [genesis/options/morphs.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/morphs.py) | 姿态校验、offset/align、文件导入、固定 link 合并与几何选项 |
| [genesis/utils/geom.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/geom.py) | 四元数乘法、旋转/平移变换与惯量换系 |
| [genesis/utils/urdf.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/urdf.py) | URDF惯量读取、尺寸/质量/惯量缩放与固定关节合并 |
| [genesis/utils/mjcf.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/mjcf.py) | joint维度映射、解析器来源和不支持项的警告 |
| [genesis/engine/states/solvers.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/states/solvers.py) | 各solver查询状态、基础SimState与完整checkpoint类型 |
| [genesis/engine/states/entities.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/states/entities.py) | 实体查询状态与粒子/顶点布局 |
| [genesis/engine/states/cache.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/states/cache.py) | 查询状态缓存与梯度生命周期 |
| [genesis/engine/solvers/base_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/base_solver.py) | checkpoint数组复制、data默认能力边界 |
| [genesis/engine/entities/base_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/base_entity.py) | Entity基类生命周期和归属 |
| [genesis/engine/entities/particle_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/particle_entity.py) | 粒子实体与solver状态范围 |
| [genesis/engine/solvers/mpm_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/mpm_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/solvers/sph_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sph_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/solvers/pbd_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/pbd_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/solvers/fem_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/fem_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/solvers/sf_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/sf_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/solvers/tool_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/tool_solver.py) | 多物理get_state/set_state的字段与envs_idx消费情况；完整checkpoint能力边界 |
| [genesis/engine/materials/rigid.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/rigid.py) | 密度来源和材质职责 |
| [genesis/engine/entities/rigid_entity/inertial.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/inertial.py) | 质量/COM/惯量的几何估计、组合和显式值解析 |
| [genesis/engine/entities/rigid_entity/rigid_joint.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_joint.py) | 配置与DOF索引、局部/全局地址 |
| [genesis/engine/entities/rigid_entity/rigid_link.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_link.py) | link与inertial属性的表示入口 |
| [genesis/engine/solvers/rigid/abd/forward_dynamics.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_dynamics.py) | 速度/位置积分、局部四元数增量、中点分支和隐式阻尼 |
| [genesis/engine/solvers/rigid/abd/forward_kinematics.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/forward_kinematics.py) | 配置到世界link姿态、DOF位置、空间速度的转换 |
| [genesis/engine/solvers/kinematic_solver.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/kinematic_solver.py) | 公共getter的复制/转置和默认坐标语义 |
| [genesis/utils/array_class.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/array_class.py) | 内部数组分类、STATE/WARMSTART/DERIVED与checkpoint集合 |

## E2 新增阅读入口

[驱动与机器人专题](control-robotics-tasks.md)以派生实体→solver→kernel核对接口，以下文件只声明表中范围的源码阅读。

| 源码文件 | 阅读目的 |
|---|---|
| [genesis/engine/solvers/rigid/abd/accessor.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/accessor.py) | 追踪控制模式/目标写入与当前控制力重算、限幅 |
| [genesis/engine/solvers/rigid/abd/inverse_kinematics.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/inverse_kinematics.py) | Jacobian行/列与frame，DLS/候选/限位分支，FK查询的临时写入恢复 |
| [genesis/utils/misc.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/misc.py) | 目标shape广播和环境×DOF矩形写入 |
| [genesis/utils/path_planning.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/path_planning.py) | 原生RRT/RRTConnect的关节限制、接触排除、有效性及状态恢复 |
| [examples/tutorials/control_your_robot.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/control_your_robot.py) | 官方名字映射及模式切换示例；仅阅读，不执行 |
| [examples/tutorials/IK_motion_planning_grasp.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/IK_motion_planning_grasp.py) | 官方IK→规划→驱动调用顺序；不将示例当抓取验收 |
| [examples/tutorials/batched_IK.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/batched_IK.py) | 官方批量IK调用入口；不执行 |

## E3 新增阅读入口

[接触、求解器与力观测](contact-solvers-forces.md)继续使用已冻结的RigidSolver、ConstraintSolver、forward_dynamics、材料与配置文件，并加入以下入口。刚体内核展开至终止与读回；耦合器仅声明下表的分派/响应边界，专门推导留E6。

| 源码文件 | 阅读目的 |
|---|---|
| [genesis/engine/solvers/rigid/constraint/linesearch.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py) | 逐岛线搜索、Hager–Zhang系数、实际退出与warmstart证书 |
| [genesis/engine/solvers/rigid/constraint/solver_breakdown.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver_breakdown.py) | decomposed graph执行臂及主迭代早停 |
| [genesis/engine/solvers/rigid/constraint/island.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/island.py) | 接触/约束岛与每岛质量trace尺度 |
| [genesis/engine/solvers/rigid/collider/collider.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/collider.py) | 过滤、检测分派、容量和contact读回所有权 |
| [genesis/engine/solvers/rigid/collider/contact.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py) | 摩擦/sol_params组合与休眠接触保留 |
| [genesis/engine/solvers/rigid/collider/narrowphase.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/narrowphase.py) | 凸体/非凸/terrain/可微几何分支入口 |
| [genesis/engine/solvers/rigid/collider/broadphase.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/broadphase.py) | sweep-and-prune/全对遍历及运行期过滤 |
| [genesis/engine/solvers/rigid/abd/misc.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/abd/misc.py) | 休眠/唤醒、耦合wrench与施力frame |
| [genesis/engine/couplers/legacy_coupler.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/legacy_coupler.py) | 刚体–粒子的SDF/速度响应与动量反作用 |
| [genesis/engine/couplers/sap_coupler.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/sap_coupler.py) | 独立SAP/PCG/线搜索与收敛字段 |
| [genesis/engine/couplers/ipc_coupler/coupler.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/couplers/ipc_coupler/coupler.py) | 外部IPC world推进与状态/控制权边界 |

## E4 新增阅读入口

范围是[A6专题](sensors-rendering.md)的传感器/渲染执行链，未运行上游例子或测试。渲染外部核心的二进制与平台资格未验收。已有Camera、Scene、Simulator、RigidSolver与tactile选项继续复用上方固定来源。

| 源码文件 | 阅读目的 |
|---|---|
| [genesis/engine/sensors/base_sensor.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/base_sensor.py) | 普通/派生read、shape与误差流水线、delay/jitter、copy边界 |
| [genesis/engine/sensors/camera.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/camera.py) | RGB sensor派生实现、lazy cache、挂载和renderer分支 |
| [genesis/engine/sensors/contact_force.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/contact_force.py) | 接触计数、排除filter、A/B符号、link系力与每轴钳位 |
| [genesis/engine/sensors/depth_camera.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/depth_camera.py) | read_image只是range reshape及history限制 |
| [genesis/engine/sensors/imu.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/imu.py) | proper acceleration、杠杆臂、轴对齐和三字段输出 |
| [genesis/engine/sensors/joint_torque.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/joint_torque.py) | DOF选择与actuator output effort getter调用 |
| [genesis/engine/sensors/kinematic_tactile.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/kinematic_tactile.py) | solver候选门控、probe深度、taxel力/力矩估计与容量 |
| [genesis/engine/sensors/point_cloud_tactile.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/point_cloud_tactile.py) | Proximity/Elastomer输出、点云归一化、FFT资格与模型边界 |
| [genesis/engine/sensors/raycaster.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/raycaster.py) | pattern坐标/射线或BVH几何来源、range输出与min_range调用缺口 |
| [genesis/engine/sensors/sensor_manager.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/sensor_manager.py) | 按类更新、return ring与history、reset及批读路径 |
| [genesis/engine/sensors/surface_distance_probe.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/surface_distance_probe.py) | 刚体tracked mesh最近距离BVH与nearest_points |
| [genesis/engine/sensors/temperature.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/sensors/temperature.py) | 格点温度输出/单位与RC测量响应入口，专项推导及量纲边界见E6 |
| [genesis/ext/pyrender/jit_render.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/jit_render.py) | NumPy RGB/depth dtype及z-buffer反投影 |
| [genesis/ext/pyrender/offscreen.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/offscreen.py) | normal通道实际shader读回路径 |
| [genesis/ext/pyrender/shaders/mesh_normal.frag](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/shaders/mesh_normal.frag) | 法向到RGB编码 |
| [genesis/ext/pyrender/shaders/mesh_normal.vert](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/ext/pyrender/shaders/mesh_normal.vert) | 世界系法向变换 |
| [genesis/options/renderers.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/renderers.py) | 主renderer选项身份及BatchRenderer默认分支 |
| [genesis/options/sensors/__init__.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/__init__.py) | 原生sensor namespace、Lidar别名与类型tag |
| [genesis/options/sensors/camera.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/camera.py) | 三种RGB camera选项、分辨率/外参、history限制与Batch默认值 |
| [genesis/options/sensors/options.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/options.py) | 传感器选项、挂载/过滤/误差、射线/IMU/温度原生字段 |
| [genesis/options/sensors/raycaster.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/raycaster.py) | Grid/Spherical/DepthCamera pattern、起点方向与针孔内参 |
| [genesis/utils/raycast_qd.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/raycast_qd.py) | raycast传入字段、world/local点定义与no-hit哨兵 |
| [genesis/vis/batch_renderer.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/batch_renderer.py) | Madrona边界、rigid视觉几何、批量缓存和depth后处理 |
| [genesis/vis/rasterizer.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer.py) | headless GL路径、split_envs和输出通道分派 |
| [genesis/vis/rasterizer_context.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/rasterizer_context.py) | 压缩segmentation ID、背景和几何key映射 |
| [genesis/vis/raytracer.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/raytracer.py) | Luisa接口与RGB字节读回，非运行验收 |
| [genesis/vis/visualizer.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/visualizer.py) | viewer与camera renderer分离、segmentation字典、可视状态更新 |
| [tests/sensors/test_api.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/tests/sensors/test_api.py) | 上游history绕过delay与jitter预期；只阅读未执行 |

## E5 新增阅读入口

[批量、学习接口与数据](batch-learning-data.md)沿用已冻结 Scene/Simulator、刚体 getter/setter、初始化、misc 与 DataKind；新增下列实际引用文件。仅分析 Genesis 侧学习调用，外部 RSL-RL/TensorDict 的精确实现未固定、未安装或执行，不据此声称训练器内部已验收。所有文件均核对固定 tree/blob。

| 源码文件 | 阅读目的 |
|---|---|
| [examples/drone/hover_env.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/drone/hover_env.py) | 对照另一官方任务的 reset/reward 与 latency 使用，非统一 Env 契约 |
| [examples/locomotion/go2_env.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_env.py) | batch buffer、四返回、自动 reset、终止观测缺失、动作延迟/索引/配置所有权 |
| [examples/locomotion/go2_eval.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_eval.py) | 外部 checkpoint 加载和推理调用；不审计外部算法内部 |
| [examples/locomotion/go2_train.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/locomotion/go2_train.py) | 外部训练器身份与下界版本、任务配置、初始化与调用边界 |
| [examples/rigid/domain_randomization.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/rigid/domain_randomization.py) | 质量/惯量/COM/摩擦的原生随机化入口，仅阅读 |
| [genesis/engine/entities/rigid_entity/description.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/description.py) | 异构形态类型、单根及 joint/link/DOF 检查，与 Scene 过时注释区分 |
| [genesis/options/profiling.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/profiling.py) | 阶段窗口/FPS选项 |
| [genesis/options/recorders.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/recorders.py) | 采样、队列、CSV/NPZ/轨迹选项与默认值 |
| [genesis/recorders/__init__.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/__init__.py) | options重导出和记录器注册入口 |
| [genesis/recorders/base_recorder.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/base_recorder.py) | 采样量化、CPU数据所有权、队列丢旧、错误和flush生命周期 |
| [genesis/recorders/file_writers.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/file_writers.py) | CSV展开、NPZ全量内存缓冲与cleanup |
| [genesis/recorders/recorder_manager.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/recorder_manager.py) | 注册/build/reset/stop和自定义recording分派 |
| [genesis/recorders/trajectory.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/recorders/trajectory.py) | 数据类别、exact/compressed、分块、末帧、seek/play和头部身份 |
| [genesis/utils/serialization.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/serialization.py) | source_digest范围、场景包load与来源差异警告 |
| [genesis/utils/tools.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/utils/tools.py) | FPSTracker主机计时、窗口平均与并行吞吐口径 |

## E6 新增阅读入口

[多物理、可微与扩展边界](extensions-boundaries.md)继续逐函数复核既有 Simulator、全部 solver、Legacy/SAP/IPC、温度及触觉源文件；新增下表实际引用文件。所有条目仍为固定 Genesis 源码，外部 pyuipc/libuipc、Quadrants、Madrona/Luisa 与 RL 依赖的精确实现和运行资格不由此验收。

| 源码文件 | 阅读目的 |
|---|---|
| [examples/deformable/differentiable_push.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/deformable/differentiable_push.py) | 官方 Tool输入→MPM状态损失→backward 的阅读样例；不执行或据此认定梯度正确 |
| [genesis/engine/entities/fem_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/fem_entity.py) | 体/面网格分支、顶点约束资格、输入及状态桥 |
| [genesis/engine/entities/hybrid_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/hybrid_entity.py) | Rigid+MPM真实组合、构造包装与额外更新的反向缺口 |
| [genesis/engine/entities/mpm_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/mpm_entity.py) | 查询状态到adjoint、原生位置/速度/actuation输入及粒子约束 |
| [genesis/engine/entities/tool_entity/tool_entity.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/tool_entity/tool_entity.py) | 规定轨迹、速度/姿态推进及MPM SDF接口 |
| [genesis/engine/materials/FEM/base.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/base.py) | 原生本构接口与零stress/未实现回退 |
| [genesis/engine/materials/FEM/cloth.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/cloth.py) | 布料参数/docstring与实际IPC消费者的差异 |
| [genesis/engine/materials/FEM/elastic.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/elastic.py) | 显式stress与隐式energy/gradient/Hessian的不同支持集合 |
| [genesis/engine/materials/FEM/muscle.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/FEM/muscle.py) | 主动应力仅覆盖显式stress函数 |
| [genesis/engine/materials/MPM/base.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/base.py) | E/ν到Lamé参数、密度与本构回调 |
| [genesis/engine/materials/MPM/elastic.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/elastic.py) | corotation/neohooken与SVD资格 |
| [genesis/engine/materials/MPM/elasto_plastic.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/elasto_plastic.py) | 屈服/奇异值投影的分段映射 |
| [genesis/engine/materials/MPM/liquid.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/liquid.py) | 体积投影及viscous分支 |
| [genesis/engine/materials/MPM/muscle.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/muscle.py) | 方向与actuation主动项 |
| [genesis/engine/materials/MPM/sand.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/sand.py) | 摩擦角单位与塑性投影 |
| [genesis/engine/materials/MPM/snow.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/MPM/snow.py) | Jp历史与指数硬化 |
| [genesis/engine/materials/PBD/elastic.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/PBD/elastic.py) | compliance声明与实际volume kernel的表达式区别 |
| [genesis/engine/materials/SPH/liquid.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/SPH/liquid.py) | rho/stiffness/exponent与粒子材料参数 |
| [genesis/engine/materials/hybrid.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/hybrid.py) | 原生association回调与默认耦合模式 |
| [genesis/engine/materials/kinematic.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/materials/kinematic.py) | ghost material与Rigid继承关系 |
| [genesis/engine/solvers/rigid/constraint/backward.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/backward.py) | active-set伴随系统、Newton Cholesky/CG分支与梯度传播 |
| [genesis/grad/creation_ops.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/grad/creation_ops.py) | gs.tensor/from_torch的detach/device/dtype与clone语义 |
| [genesis/grad/tensor.py](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/grad/tensor.py) | Scene身份、detach/sceneless、Torch到Scene backward桥 |
