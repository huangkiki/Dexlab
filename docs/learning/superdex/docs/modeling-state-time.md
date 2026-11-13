# E1 · 建模、坐标、状态与时间

完成本章后，应能从一个资产说明每个物理量的坐标、单位和来源，正确区分 pose、速度、DoF、模型与快照，并沿原生接口找到一步更新的采样时刻。这是 A1/A2 的完整专题以及 B0/B4 的基础部分；接触方程、非线性残差与线性系统在 E3 继续展开。

**先修**：[对象导读](guide.md)，矩阵乘法、刚体质心与角速度。应用读者按第 1–6 节阅读；源码读者再沿第 7–9 节追踪。源码固定在 `1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。候选发行包 `1.0.0`、Physics 内核构建、Robotics 与 Studio 是不同身份；这里核实的是源码和接口契约，没有运行原生示例、仿真或实验，也不据此补齐 DexLab 历史二进制的配置证据。

## 1. 先定义场景和资产的语义

Physics 的原生生命周期是 `physics.initialize()` → 创建/载入 shape → `physics.create_scene()` → `scene.create_*_actor()` → 查询或更新 → `physics.destroy_scene()` → `physics.shutdown()`。Shape 是几何及元数据，Actor 是场景中的实例，Scene 管理 actor、约束、求解参数和时间。一个 shape 可以供多个 actor、甚至不同 scene 使用；共享 shape 不表示共享 pose。释放 scene 后不要继续使用其 actor、snapshot 或借用数组。官方[刚体示例][rigid-example]展示单个 actor 可提前销毁，销毁整个 scene 会处理余下 actor，shutdown 释放全局资源。

| 数据 | 典型原生入口 | 应记录的内容 |
|---|---|---|
| 参考几何 | `create_tri_mesh_shape`、`load_shape_from_file` | 网格坐标单位、连接/绕序、闭合性、`bake_scale`、源资产哈希和许可 |
| 实例配置 | `create_rigid_actor` / `RigidActorParams` | 静态/动态、质量/密度、质心/惯量、初始姿态、碰撞表示 |
| 实时状态 | `Actor.get_root_transform`、速度及 DoF API | 所属 actor、frame、时间、数据是否拷贝 |
| 场景配置 | `Scene.set_gravity`、`set_solver_params` | 重力、积分与求解参数；与状态快照分开保存 |
| 机器人模板 | `robotics.load_bot_prefab_from_urdf_file` | links/joints、根关节、视觉和碰撞 mesh、导入限制 |
| 可恢复状态 | `Scene.capture_state` | 同一 scene/拓扑的可变状态；不是资产文件 |

`RigidActorParams.shape` 与 `collider_type` 不是同一个东西：前者包括表面网格等几何，后者描述**其他 actor 如何检测与该 actor 的接触**。不能从渲染外观推断接触表面，也不能从 `BOX` 推断完整物体质量来源。动态 rigid 要求有表面网格；隐式无限平面用于 static。SDF 构建参数在该 collider 路径需要且 shape 尚无 SDF 时才生效。依据：[参数契约][api]的 `RigidActorParams`（5143–5355 行）。接触的方向性与组合律留到 E3。

## 2. 坐标、旋转和单位

Physics 示例设 `gravity=[0,-9.8,0]`，采用 Y-up；Robotics 的 URDF 示例显式设 `[0,0,-9.81]`，采用 X-forward、Y-left、Z-up（FLU），并单独设置 debugger 的 coordinate space。**更改 debugger 坐标声明不会替你旋转模型、重力和初速度**。这三个量必须属于同一物理世界坐标。[Physics 示例][rigid-example]与[Robotics 示例][urdf-example]直接展示了两套约定。

本章以 m、kg、s、rad 为输入单位；重力 m/s²，线速度 m/s，角速度 rad/s，惯量 kg·m²，密度 kg/m³。这些单位来自原生字段文档；`TransformRT` 本身不会识别“这是毫米”。输入 1000 倍长的网格不等于界面缩放：若密度不变，几何相似且均匀缩放 s 倍，则质量变成 s³ 倍、质心惯量 s⁵ 倍；若另行固定质量，惯量才是 s² 倍。

令 `world_from_local = (R_WL, p_WL)`。它将 local 中的点变为 world 点：

$$x_W = R_{WL}x_L + p_{WL},\qquad d_W = R_{WL}d_L.$$

方向没有平移项。组合 `T_WL * T_LM` 从右向左作用得到 `T_WM`；逆变换的旋转为 Rᵀ、平移为 −Rᵀp。[TransformRT 实现][rt]按这个规则组合，其类型只含旋转和平移，**不含缩放**。资产缩放应在导入/烘焙层处理，而非把非单位四元数当作缩放。

[Quaternion][quat]的存储/构造顺序是 **x,y,z,w**，单位姿态为 `(0,0,0,1)`。`rotation_x/y/z(angle)` 的角度为弧度，`from_axis_angle` 与 `from_rotation_vector` 可避免手写顺序错误。3 维旋转向量 r = θa 与 4 维四元数是不同表示，后者要求单位长度。`TransformRT` 的构造/设置只在相应 debug 配置下警告非单位四元数，不能依赖它自动归一化或在发行构建中拒绝输入。

四元数 q 与 −q 表示同一旋转，直接减四个数不能作为姿态误差；角速度也不等于四元数导数。坐标约定转换为同手性正交矩阵 C 时，有 `p_new=C p_old`、`R_new=C R_old Cᵀ`；若含反射，角速度作为轴向量应使用 `det(C) C ω`。原生[坐标工具][coords]分别处理方向、位置尺度与四元数反射，不能仅交换“up”轴而遗忘旋转和惯量。

### local 原点、质心和速度采样点

`Actor.get_root_transform()` 给 local 原点在 world 中的 pose。`get_rigid_center_of_mass_local()` 给质心在 local 中的位置 c_L。于是质心世界位置是 `c_W=R_WL c_L+p_WL`；`get_center_of_mass_transform()` 保留相同旋转，平移换成 c_W。对应的 [C++ 实现][actor]在 302–336 行明确做了这个变换。

动态 rigid 的 `get_linear_velocity()` 是**质心速度，world frame**；`get_angular_velocity()` 也是 world frame。若要 local 原点或接触点 x_W 的速度，应使用刚体关系：

$$v(x_W)=v_C+\omega_W\times(x_W-c_W).$$

不要把 `v_C` 直接贴到 mesh 原点轨迹上。软体的这两个 getter 是 root 运动的估计，不是每个节点速度，更不能代表内部形变。[Actor API][api]的 9247–9315 行给出适用类型与单位。

## 3. 惯量、网格与 URDF 导入

### 质量属性必须成套一致

`create_rigid_actor` 接受 `density` 或 `mass`；同时设置时 mass 优先。未显式给出质心或惯量时从几何及密度计算。显式 `center_of_mass` 是 local 坐标中的 c_L，`moment_of_inertia` 是**关于质心、轴方向与 local 对齐**的张量，六元排列为：

```text
[ixx, ixy, ixz, iyy, iyz, izz]
I = [[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]]
```

非对角项是惯量张量的负积惯量，例如 `ixy = -∫xy dm`，不能把 CAD 导出的正积惯量原样复制。若 CAD 张量关于另一个原点 O，先以平行轴定理 `I_O=I_C+m[(d·d)I₃−ddᵀ]` 移到质心，再把轴旋到 local：`I_L=R_LC I_C R_LCᵀ`。平移和轴转换是两步，不能只修改质心数值。[惯量契约][api] 5260–5321、9226–9246 行及 [getter 实现][actor] 324–336 行一致。

物理合理性至少要求有限数、正质量、非负主惯量，并满足任一主惯量不大于其余两者之和。该版本对有限但物理无效的张量可能只警告，因此“成功创建 actor”不是模型质量验收。`set_inertia_properties` 只支持独立动态 rigid，不支持 articulated link/soft/static；之后 `set_density` 会围绕新参考质量/惯量等比例缩放，质心不变。不能用这个 setter 修补所有导入类型。

### runtime URDF 路径的实际边界

[官方 URDF 例子][urdf-example]依次调用 `load_bot_prefab_from_urdf_file`、修改 prefab、`create_context`、`create_bot`，再取得 articulated actor。解析模板与实例化是不同步骤；SDF 在创建 bot 时从 mesh 构建。源码位于[urdf_import_utils.cpp][urdf]，当前应逐项审查：

| 输入 | 此固定提交的行为 | 使用后果 |
|---|---|---|
| `<visual>` / `<collision>` | `ParseVisualOrCollision` 找首个带 mesh 的同类元素；非 mesh primitive 跳过（162–199 行） | 不能假设所有 geometry 都导入；box/cylinder/sphere 可能无碰撞 |
| mesh origin/scale | 分别保存视觉的 renderModel 变换与碰撞的 shape 变换（465–490 行） | 调整视觉不等于调整碰撞；尺度和局部 origin 要同时核对 |
| `<inertial origin>` | 解析出 rotation 与 com，但只保留 com；六项 inertia 随后原样写入 link（211–227、459–462 行） | **源码推论：非零 inertial rpy 不在此路径旋转张量**；先转成 link 轴再导入，或选择经核实的其他处理路径 |
| 根关节 | 示例说明新增 index 0 的 free `world_joint` | 固定基座应显式改成 `ArticulatedJointType.HARD`；不要把自由基座误当额外驱动关节 |
| joint origin rpy | `Rz(yaw)*Ry(pitch)*Rx(roll)`（140–159 行） | 不是任意 Euler 顺序；单轴方向应结合 joint frame 理解 |
| 非闭合 collision mesh | runtime SDF 的符号可能不可靠（官方例子已明确提示） | 加载成功、显示正常均不足以证明碰撞正确 |

上面的 inertia 限制是此源码路径的静态推论，没有用物理实验量化误差。这里不把 Studio importer 与 runtime importer 视作同一实现；官方建议复杂资产经 Studio 预处理，但本章未据此承诺 Studio 对任意 URDF 的完整保真。

资产审查时保留原文件与许可、mesh 路径解析结果、长度尺度、根 frame、质心与惯量 frame、visual/collision 的数量和变换。不要仅保存一个最终 `.superdex_bot` 名称而丢失转换来源。无需在本阶段下载或重新分发第三方资产。

## 4. 状态不是一条统一的 qpos 数组

SuperDex 使用 Scene/Actor API 和内部 ECS 组件。`get_num_dofs()` 返回该 actor 的求解自由度数量；`GetDofValues` 从 solution 取 pose，在 `poseSize != dofsSize` 时执行相应转换。[实现][actor] 685–750 行明确区分二者；[rigid 转换函数](https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/rigid_body_utils.h#L508-L526)进一步把 quaternion pose 转为旋转向量 DoF。不要套用另一引擎“全 scene 一个固定布局向量”的假设。

| actor / 表示 | 读取方式与维度 | 解释 |
|---|---|---|
| 动态 rigid 的外部 pose | `TransformRT` = translation 3 + quaternion 4 个标量 | 6 个独立自由度；四元数约束消除一个冗余维度 |
| rigid DoF 表示 | `get_dof_values([], out)`，out 长度 `get_num_dofs()`，rigid 为 6 | 质心世界位置 3 + world-from-local 旋转向量 3；不等于 quaternion 内存片段 |
| rigid 速度 | `get_linear_velocity()`、`get_angular_velocity()` 各 3 | 质心/world；不要按 pose 的 7 个标量对齐速度 |
| articulated | `get_articulated_pose(out)` / `get_articulated_joint_velocities(out)` 均按 `get_num_dofs()` 分配 | 平移 m / m·s⁻¹，转动 rad / rad·s⁻¹；索引由 joint types 与 `ArticulatedShapeInfo.dof_info` 定义 |
| soft / shell 的局部位移 | `get_displacements()` 为 3N | 相对于参考节点位置；`get_node_positions_local()` 是当前局部坐标，mesh 中参考坐标不能冒充状态 |
| rod 的位移/扭转 | `get_displacements()` 为 4N | 每节点 3 个位移 + 1 个 twist；开杆最后一个 twist 为占位，约束为零 |
| soft-skinned | getter 给蒙皮后的 3N 位移 | setter 写的是蒙皮前弹性分量，不能默认 get/set 完全对称 |

维度/表示来源：[Actor API][api]的 9460–9520、9806–9840、10245–10334、11092–11328 行。ROM、壳和杆的材料及降阶内部状态在 E6 专题深入，本章不将所有变形体都压成“3N 刚体点”。

articulated pose 虽使用 DoF 长度的向量，旋转仍在流形上。对于 3D 转动，`pose + h*velocity` 不是一般成立的更新；应用应使用 `add_articulated_delta_to_pose`、`compute_articulated_pose_delta` 进行关节感知的合成/差分。该 API 明确说 3D rotation delta 是 Lie 代数旋转增量，角速度不是旋转向量三个分量的直接时间导数。E2 再追踪 joint/link 映射与控制目标。

### 数据所有权影响日志和 Python 输出缓冲

`get_root_transform` 的 C++ 返回值是 `TransformRT` 值；修改返回对象不会直接移动 actor，必须调用 setter。`SpanConstReal` 不同：它是借用视图。[PySpan][span]保存原始 span 指针、C++→Python 零拷贝，`tolist()` 或 `copy.copy()` 才建立独立内容。readonly 仅限制写入，不让数据脱离 actor 生命周期。日志若跨步保存，显式复制，例如 `list(actor.get_displacements())`；销毁/重建 actor、reset 或内部分配后不要复用借用视图。

`get_dof_values`、`get_articulated_pose` 的 out 参数必须是可写、预先分配、类型匹配的连续数组。普通 list 不能作为 out；FP64 内核不能任意收 float32 输出数组。使用原生 `DynamicArrayReal` 并按 DoF `resize()` 可跟随当前 real 精度，或在确认构建后分配正确 dtype 的连续 NumPy 数组。不要传带 stride 的切片：[Span caster][span]的快速路径按指针和长度构造 span，本段源码没有检查步幅，错误布局可能无法由绑定层替你拒绝。不能把 `np.asarray` 默认为拷贝。

## 5. 修改状态、重置和快照

`set_root_transform` 只改变 pose，动态 rigid 的速度保留；static actor 的运动速度由相邻步 root transform 推得，要取消这次运动须按该 API 约定调用零速度。`set_velocity` 可设置动态 rigid world-frame 质心/角速度；static 只允许零，soft 不允许非零角速度，articulated link 不支持这个入口。给 link 直接设 root pose 也会报错，应修改 articulated actor 的 pose。

状态 setter 会使历史失效：`SetRootTransformImpl` / `SetVelocity` → `InvalidateActorStepHistory` → `ClearMultiStepIntegrationData`。它清除 rigid pose/vel、变形体及 articulated 等多步历史；BDF2 在修改后的第一步回退到 Backward Euler。因此，“每帧强行改 pose”既不是动力学控制，也不能维持原来的多步积分轨迹。[实现][actor]、[失效入口][invalidate]与[历史清理][clear]可串起来阅读。

完整 episode reset 应说明需要恢复哪一层：

1. 在所有 actor、约束和初始目标构造完毕后 `initial = scene.capture_state()`。
2. 在**同一 scene、相同拓扑**上 `scene.restore_state(initial, release_immediately=False)`。保留 handle 才能多次恢复；用完 `release_state(initial)`。
3. 一并恢复应用拥有的控制器时钟、任务阶段、随机数状态和用户缓存；Python 自定义对象不自动成为 Scene 快照的一部分。
4. 快照不恢复 shape、materials、scene 参数，改过重力或材料时要另行恢复；要还原拓扑，应按原始资产/配置重建 scene，再生成新快照。
5. 恢复后再取得查询视图。需要刷新渲染/查询时可用 `step(0)`，但先检查 callbacks 是否会写状态/递增用户时钟。

捕获内容包括 actor solution/transform/velocity、约束与控制目标的当前/先前值、外力，以及标记为可捕获的时间/积分组件。`mochi_capture.cpp` 按 `CaptureStateCtx` 和 `CaptureState` 属性序列化；[CSceneTime][components]包含当前/前一步 dt 和时间，[CIntegrationRigidStates][components]也带捕获标记。这解释了为什么“只存位置速度”不足以替代原生 snapshot。

[原生 capture/restore 契约][api] 12436–12568 行还规定：ROM actor scene 不支持此捕获；handle 属于原 scene；restore **不是事务**，失败可留下部分修改，应恢复已知可用检查点或重建。`release_immediately=True` 即使恢复失败也释放 handle。bytes 路径要求相同 Physics build、相同 actor/constraint 创建顺序和 component 布局，不是长期可交换文件格式。不要把一次成功读取 bytes 外推为跨版本确定性回放。

## 6. 时间步、控制周期和采样阶段

对有限正步长 h，`scene.step(h)` 调用链如下。注意总时间字段在积分前已 Advance，求解中的时间标签不能独自证明状态已经更新。

```text
SceneImpl::Step(h)
  step counter / recorder begin
  pre-step callbacks                 ← 状态通常属于 t_n
  CSceneTime::Advance(h)              ← 场景报告的步末时间变为 t_n+h
  PreStepEcs → StepEcs → PostStepEcs   ← 求解和状态/派生更新
  aggregate solver stats
  post-step callbacks                ← 步后状态，callback 自身仍可能修改它
  recorder end
```

来源：[SceneImpl::Step][scene] 488–614 行与 [CSceneTime][components] 254–310 行。外部采样建议在 `step` 返回后读取 pose、速度、时间并复制，日志明确写 `post_step`。pre-step 回调适合用 t_n 的状态形成下一步输入；后回调若又改 pose，则返回后读到的是修改结果。传感器有自己的更新逻辑，E4 会进一步拆开采样与渲染时刻。

`step(0)` 不执行动力学/Advance，仍触发前后回调、更新查询和 step counter，并清空这一轮求解统计。它不等于无副作用的 getter。`get_last_time_step()` 保留最近正步长；刚创建场景时不要把它当作用户已选步长。负值和 NaN 被原生入口拒绝并记录日志；源码判断是 `h>=0`，调用方应额外保证**有限**，不要依赖它自动拒绝正无穷。

积分 stage、物理 substep 与控制频率应分开命名。若一次控制周期 H 切成 m 次 `scene.step(H/m)`，时间仍推进 H，但会执行 m 次回调/碰撞/求解，外部目标是否保持必须由应用说明。DIRK 的多个 stage 属于一次 step 内的离散公式，不是 m 次 `scene.step`，不能据此声称控制频率翻倍。显示器 60 FPS 或 debugger 刷新也不定义 h；内部积分方法/迭代上限则不改变传入 h 的单位。

## 7. B0：从物理量到 ECS 状态

孤立刚体的动量关系可先写成质心世界系下 `p=m v_C`、`L_W=I_W ω_W`，其中 `I_W=R_WL I_L R_WLᵀ`。无额外约束时有 `m dv_C/dt=F_W` 和 `I_W dω/dt+ω×(I_Wω)=τ_C,W`。这些是教学用连续方程，包含恒定质量、刚体、惯量关于质心的假设；不能直接拿它代替引擎离散残差。

在带关节或形变自由度的系统中，可写概念式 `M(q) vdot + c(q,v) = Q + Q_constraint`，各广义力与对应虚位移做功，旋转项单位是 N·m，平移项是 N。q、v 的存储维度和表示未必相同。约束与接触如何形成离散目标/残差、以及软体能量的装配归入 E3/E6；本章先建立追踪表，避免错误拼接数据：

| 外部问题 | 源码入口 | 核实内容 |
|---|---|---|
| pose 为何不同于 root 原点 | `ActorImpl::GetCenterOfMassTransform` | 质心偏移通过 root transform 转到 world |
| DoF 为何不等于 quaternion 长度 | `ActorImpl::GetDofValues` | 先按 `poseSize` 取 solution，再转换到 `dofsSize` |
| 状态为何有历史 | `CRigidState<Current>`、`CIntegrationRigidStates` | ECS 分开保存当前解与积分 bundle |
| 快照为何包含部分字段 | `capture::CaptureState` | 属性标记驱动序列化，不是整个进程内存转储 |
| Python 日志为何随步变化 | `PySpan` 与生成的 actor binding | 借用原始数组，复制与视图是不同操作 |

链接：[Actor 实现][actor]、[组件][components]、[捕获实现][capture]、[绑定][binding]与 [Span][span]。[E3 接触、求解器与力观测](contact-solvers-forces.md)从这些状态继续追踪非线性/线性系统、残差和观测，柔体材料与可微实现细节留 E6。

## 8. B4：时间离散的最低必要知识

对光滑常微分方程 `ydot=f(t,y)`，Backward Euler 的教学形式是：

$$y_{n+1}=y_n+h f(t_{n+1},y_{n+1}).$$

右边含未知的步末状态，因此每步须解代数问题。**积分器选择离散问题，非线性求解器迭代逼近解，线性求解器解每次迭代的子问题**。增加 Newton 迭代可以减小求解误差，却不会把 Backward Euler 改成二阶时间积分。角姿态在引擎中使用相应几何表示，上式不能解释为对四元数直接逐分量相加。

固定提交的 [IntegrationMethod][int] / [系数表][coeff]包括下列方法。多步表示需要过去时间层，stage 表示当前 step 内的阶段。

| 方法 | 历史步数 / stage 数 | 源码注释给出的阶数与性质 |
|---|---|---|
| BackwardEuler（默认枚举） | 1 / 1 | 一阶、L-stable |
| BDF2 | 2 / 1 | 二阶、A-stable |
| BDF3 | 3 / 1 | 三阶；本表不另加 A-stable 承诺 |
| DIRK22 / DIRK23 / DIRK33 | 1 / 2、1 / 2、1 / 3 | 分别二、三、三阶；22/33 标 L-stable |
| SymplecticDIRK12 / 22 | 1 / 1、1 / 2 | 二阶、A-stable；12 为隐式中点，变步长时保辛性有额外限制 |

例如常步长 BDF2 的系数对应 `y_(n+1)=4/3 y_n−1/3 y_(n−1)+(2h/3) f_(n+1)`；额外历史是公式的一部分，不能只增加一个 `num_iterations` 代替。实际启动和历史失效必须遵循内核规则，不应自己捏造缺失历史。方法阶数通常假设足够光滑、求解误差受控，碰撞切换、状态跳变或强约束会破坏这些前提。

对线性测试方程 `ydot=λy`，Backward Euler 的放大因子 `1/(1−hλ)` 解释了它对衰减刚性模态的稳定性和数值耗散；这**不保证**任意 h 的非线性接触问题可收敛，也不保证高频运动、冲击峰值或能量准确。因此不把官方示例的 1/60 s 复制成所有场景的推荐步长，不用“没有发散”代替离散精度论证。

精度也不是积分阶数：FP64 表示 real 的浮点构建，不代表二阶积分、准确接触或梯度无误。`loader.py` 在 import 时选择并固定进程精度，[Physics 初始化模块][init]再用 `uses_double_precision()` 核对 native binding。`SUPERDEX_PRECISION=fp64` 必须在导入前设置，并有匹配的 native payload；输入 Python float 不会把 FP32 内核变 FP64。[loader][loader]给出选择与错误分支。

可微支持必须按执行路径验收。此提交 `make_scene_differentiable` 在 [Scene 源码][scene] 3015–3028 行要求 Backward Euler；枚举里存在 BDF/DIRK 不意味着它们都能用于该可微场景。接触导数、终止容差、梯度适用边界留给 E3/E6。

## 9. 最小原生片段与带答案的阅读练习

[examples/inspect_rigid_state.py](../examples/inspect_rigid_state.py) 接受调用方已创建的动态 rigid，展示原生输出缓冲和采样记录；不导入资产、不启动 debugger、不调用正时间步。**仅通过 Python AST 语法检查，未执行或 import SuperDex。** 代码的接口/维度由固定源核对，运行兼容性仍待对应构建验证。

1. **资产 mesh 用 mm，而场景按 m；只把初始高度除以 1000 能修好吗？** 不能。几何、质心、相关 translation 都要使用一致长度尺度；惯量/质量要按实际质量设定重新换算。固定密度时质量 s³、惯量 s⁵，固定质量时惯量 s²。
2. **root 在原点、c_L=(0.1,0,0)、R 为单位；v_C=0，ω=(0,0,1)。root 速度是什么？** `ω×(-c_L)=(0,-0.1,0) m/s`。质心不动并不等于模型原点不动。
3. **将 `(1,0,0,0)` 当作单位姿态会怎样？** xyzw 下它是绕 X 轴 π 的单位四元数；真正 identity 为 `(0,0,0,1)`。这类输入合法但语义错误，检查单位长度不能发现。
4. **为什么 7 个 pose 标量不能用 7 个 rigid 速度逐分量推进？** pose 含单位四元数冗余；刚体只有 6 独立自由度，角速度属于旋转切空间。阅读 `GetDofValues` 中 poseSize→dofsSize 的转换。
5. **更换重力、创建一个新约束后 restore 原快照能回到相同系统吗？** 不能。scene 参数未被恢复，拓扑必须一致；先重建/还原配置，不能把 restore 失败后的部分状态继续当成基线。
6. **暂停时 step(0) 为什么仍可能推进用户的任务状态机？** 前后 callback 都会调用。若 callback 无条件递增计数或写控制目标，零物理时间并不阻止这些用户副作用。应以 `StepInfo.time_step_sec` 与自己的 reset 协议处理。
7. **每帧 set_root_transform 但选择 BDF2，能说明一直使用二阶历史吗？** 不能。外部 setter 清历史，首步回退到 Backward Euler；沿 `InvalidateActorStepHistory` 阅读。这也不是施加力的控制方式。
8. **URDF 视觉正常但手指穿透，先查哪里？** 查 `<collision>` 是否 primitive 被跳过、多个 mesh 是否只有首个进入、SDF mesh 是否闭合、visual/collision origin/scale 是否一致。无需先调整 penalty 或迭代次数。
9. **URDF inertial rpy 非零、I 为非球对称张量，导入结果可靠吗？** 该固定 runtime importer 丢弃解析出的 inertia rotation，按源码推论不能保真。先把张量旋入 link 轴，保留变换来源；此结论不是 Studio 路径或历史 binary 的通用结论。
10. **为什么 `np.asarray(span)` 不能作为不可变历史日志？** span 可能借用 actor 内存；转换不承诺复制。取独立 list/拷贝并记录时刻，销毁 actor 前不保留借用视图。

本章的[验证记录](validation-e1.md)列出源码、语法、文档检查的边界。E2 继续关节映射、控制器、FK/IK 与任务接口；E3 继续接触/求解器；E4 继续感知和渲染。实验数据在后续课程复用 [DexLab](https://github.com/huangkiki/Dexlab)，不会在这里重新启动一套实验或评分系统。

[api]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/stubs/public/mochi_physics/__init__.pyi
[actor]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_actor.cpp
[scene]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_scene.cpp
[components]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_common_components.h
[capture]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_capture.cpp
[span]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/src/pybind_span.h
[binding]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/pybind/src/generated/mochi_physics_pybind_actor.generated.cpp
[quat]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/quaternion.h
[rt]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/transform_rt_inl.h
[int]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/integration/integration_params.h
[coeff]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/integration/integration_utils.h
[clear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_integration.cpp
[invalidate]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_simulation.cpp
[rigid-example]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/examples/example_rigid_bodies.py
[urdf-example]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/examples/basic/example_urdf_loading.py
[urdf]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_robotics/src/utils/urdf_import_utils.cpp
[coords]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/utils/coordinate_systems.py
[loader]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/loader.py
[init]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_python/superdex/physics/__init__.py
