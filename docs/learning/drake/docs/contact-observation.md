# E3 · 力读回：对象、作用点、表达系和采样

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · 先读[材料与几何](contact-models.md)、[求解与时间](contact-solvers.md)

本篇回答 E2 状态机的 normal_force/slip 输入应从哪里来，什么情况下仍然不能直接使用。固定源码版本仍是 Drake 1.57.0；没有执行读回、接触、传感或 DexLab 评测。

## 1. 先选择要观察的物理量

| 原生读回 | 对象、单位、排列 | 不可替代的另一量 |
|---|---|---|
| `get_net_actuation_output_port()` | actuator 坐标下总驱动，N 或 N·m | 物体接触力、传感器 wrench |
| `get_generalized_contact_forces_output_port(instance)` | 对应该实例 v 的广义接触力，N 或 N·m | 任意指定点的三维力 |
| `PointPairContactInfo.contact_force()` | **B** 受到的力，作用在 C，world 表达，N | A 的力、body frame 分量 |
| `HydroelasticContactInfo.F_Ac_W()` | **A** 受到的 `[τ;f]`，surface centroid C，world 表达，N·m / N | point 结果的 B 侧约定 |
| `get_reaction_forces_output_port()` | joint child C 在 Jc 处、Jc 表达的 wrench，按 JointIndex | 只由接触产生的力 |
| solver 内部 γ | 每项 constraint 的冲量，接触为 N·s | 已除 h 的公开报告力 |

joint reaction 可以包含为实现机构运动而传递的重力、惯性、驱动和其它作用；不能将其绝对值直接称作手指夹持力。generalized contact force 是投影后的 `Jᵀf`，一般不可唯一反推全部接触点力。[广义/反力端口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1261-L1310)、[point 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/point_pair_contact_info.h#L35-L98)、[hydro 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/hydroelastic_contact_info.h#L39-L64)

## 2. ContactResults 的两类结果必须分别遍历

`get_contact_results_output_port().Eval(plant_context)` 返回 `ContactResults`。分别遍历 `num_point_pair_contacts()/point_pair_contact_info(i)` 和 `num_hydroelastic_contacts()/hydroelastic_contact_info(i)`；fallback 场景只遍历一个集合会漏掉另一种接触。另有 deformable contacts，本文例子无 deformable body，不能把该范围默默推广为所有形变体观测。[集合接口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_results.h#L30-L108)、[Python 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L135-L155)

### 2.1 Point 的正法向与 slip

point 结果给 BodyIndex，内部 `point_pair()` 给 GeometryId。其 normal `n_BA` 指 B→A，但 `contact_force()` 是 B 受到的力，因此压缩法向幅值应按本约定取

$$f_n=-n_{BA}^{T}f_B,\qquad f_{t,B}=f_B+f_n n_{BA}.$$

理想有效压缩结果 fn≥0；诊断时应保留带符号的值及原始向量，不能先 abs/clip 把 A/B 错置掩盖。若关心 A，先取 fA=−fB。`slip_speed()` 是接触点相对切向速度的**非负范数**，`separation_speed()` 是带符号的法向分离速度；不要用 world 中某个 body 的 x 速度代替。[结果字段](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/point_pair_contact_info.h#L75-L105)

离散实现先从 contact frame 的 `[ft1,ft2,fn]` 旋转为 world 的 fB；slip 取 solver 接触切向速度的 norm。不同步的 body pose 与这个力记录拼在一起，会产生错误力臂。[离散读回装配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L443-L498)

### 2.2 Hydro 的压力、wrench 和实体映射

surface 的 `id_M()/id_N()` 分别对应 HydroelasticContactInfo 中的 A/B 侧。它们是**GeometryId**，不是 BodyIndex；用 inspector 的 geometry→FrameId，再用 Plant 的 `GetBodyFromFrameId` 找到实际 body。一个 body 上多个几何的结果可以分开，也可在相同参考点与表达系下求和。

`F_Ac_W()` 已是积分后的 A 侧空间力，排列 `[τx,τy,τz,fx,fy,fz]`。surface 的 `tri_e_MN()/poly_e_MN()` 是弹性压力场；在离散输出中它与旧几何关联，而最终 wrench 来自各面片的求解力累加。不要把 `max pressure × total area` 当成总法向力，也不能用单一 surface normal 代表曲面所有局部法向。[surface 身份与场](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/geometry/query_results/contact_surface.h#L25-L108)、[离散积分读回](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L533-L581)

公开 HydroelasticContactInfo 没有与 point 完全同义的单个 `slip_speed()` 字段。若任务需要 hydro slip，应指定位置/面片、两物体相对运动及表面速度，再定义最大值、面积/压力加权统计等观测合同；不同定义不能混成同一个阈值。该观测设计不由总 wrench 自动确定，也不是本例已实现的触觉传感器。

## 3. 换参考点与换表达系是两步

已知作用在 C、world 表达的 wrench `[τC;f]`，想改到 O，且不改变物理受力对象：

$$\tau_O=\tau_C+(p_{WC}-p_{WO})\times f,\qquad f_O=f.$$

原生 `SpatialForce.Shift(p_CO_W)` 的参数从**旧作用点 C 指向新作用点 O**，即 `p_WO−p_WC`。源码对应 `τO=τC−p_CO×f`，与上式相同。之后以 `R_SW=R_WSᵀ` 将 torque 和 force 都旋转到 sensor frame S；只旋转力而不处理力矩/作用点，会得到错误 wrench。[Shift 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_force.h#L92-L147)

例如 C=(1,0,0) m，O=(0,0,0)，f=(0,2,0) N，τC=0，则 τO=(0,0,2) N·m。这个解析算例只检查符号与单位，没有执行 Drake。

point 是 C 处无附加偶矩的力；转换到传感器原点时通常有力矩。hydro 可因分布式 traction 在 centroid 自带非零力矩，不能将它先降成三维力再重建。A/B 作用反作用只有在**同一点、同表达系**时六维向量才直接互为负；两 body 原点不同的 wrench 要先 shift 对齐。

两个对向手指给物体的净力可以近零，同时每侧压紧力都很大。故“合力 norm”不是夹持力，`||τ_contact||` 也不是。任务接口要明确观测的是左指法向和、右指法向和、两者最小值、还是传感器特定轴；对应坐标、符号和过滤对象必须一并记录。

## 4. force、impulse 与时间窗口

### 4.1 离散输出的力等于冲量除以 h

SAP 首先求 γ；`PackContactSolverResults` 按 contact 范围提取 γn/γt，再分别除以 Plant h 得 `fn/ft`；广义接触力为 `ΣJᵀγ/h`。这是该离散更新所对应的等效步平均力，不是无限时间分辨率下的瞬时撞击峰值。[实际除 h](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/sap_driver.cc#L973-L1021)

例如 γn=.02 N·s、h=.001 s，报告 fn=20 N；这个单位换算不证明真实峰值就是20 N，也不意味着把 h 减半后 γ不变。对长时间窗求冲量，应对每个**不同物理更新**的力乘其 h 后累加，不能按日志行数重复积分同一个 hold/sample。内部 `ContactSolverResults.ft` 旁的遗留注释误称 tangential velocities；数据赋值与除 h 的路径明确表明它存力，真正速度字段是 vt。[内部字段对照](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/contact_solver_results.h#L27-L49)

连续模型的 contact force 是当前状态下的正则化力；连续冲量需要对时间积分。两类值都以 N 表示，不代表具有相同时间窗口，不能直接比较逐帧最大值。

### 4.2 默认 sampled contact 属于上一次已计算更新

离散 Plant 默认将 dynamics 输出保存在 step memory。状态 x[n+1] 已更新时，contact geometry 来自该步起始配置 q[n]，力来自为这一步求出的冲量，接触速度由 J(q[n])v[n+1] 等定义。当前读回时间、几何时间和力对应的更新区间必须区分。[采样方程](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L404-L440)、[memory 保存](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc#L42-L55)

在**第一次物理更新前**，sampled ContactResults 为空；这不证明几何不相交，也不证明 SceneGraph 失效。直接 SetPositions 改了 live q，旧 sampled 输出也不会立刻变成新配置的接触。启用 live 输出会在当前状态计算下一步离散动力学相关结果，可能触发一次求解；它仍不是连续模型瞬时力。`ExecuteForcedEvents` 会推进物理状态，不能当作无副作用的“刷新力缓存”。[输出合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L488-L533)、[未采样时为空](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1313-L1322)

`ContactResults` 本身不是附带完整实验时间元数据的日志。例子只记录 `query_time_s`，没有把它伪装成 `sample_time_s`。正式复用 DexLab 时应沿用其真实事件时序记录，而不是事后假设 `query_time−h` 必为采样时刻；初始化、强制事件、事件左/右极限和异步记录都会使这种猜测不可靠。

## 5. 把读回接到 E2 任务之前

[contact_inspection.py](../examples/contact_inspection.py) 的 `read_contact_fields` 明确输出 point 的 B 侧 force 和 hydro 的 A 侧 wrench，保留 geometry/body 身份和作用点；对 NumPy 数值做副本，不把 cache-backed 引用保存为长期快照。构造函数没有调用该 reader，整个文件在本阶段也没有执行。[Python point/hydro 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/multibody/plant_py.cc#L73-L130)、[surface 几何字段绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/geometry/geometry_py_scene_graph.cc#L752-L788)

接入 E2 的 normal_force/slip guard 至少要落实：过滤指定指尖/目标物体、统一受力侧、确定法向/作用点、处理多个 contact、定义时间窗口和空样本语义、保留有效性。空结果可能表示未采样、无接触或该类别没有 contact，不应无条件变成一条“可靠零力”观测。过期数据即便力超过阈值，也不满足 E2 的新鲜度合同。

这些是原生数据到任务观测的明确映射；本轮没有新建跨引擎传感框架，也没有给 DexLab 的 Drake [Issue #117](https://github.com/huangkiki/Dexlab/issues/117) 补记运行验收。源码阅读版本、候选 wheel 和已验收实验版本继续分开。

## 6. 阅读练习与答案

1. point 的 normal 为 B→A，结果 force 是 B 所受，直接 `normal·force` 为何通常是负？
2. hydro `F_Ac_W` 与 point `contact_force()` 可以直接用相同符号求和吗？
3. 10 N 的离散报告力每隔 0.1 ms 记录一行，Plant h=1 ms；可否每行乘 1 ms 求冲量？
4. 创建 Context 后看到空 contact results，是否足够证明 sphere 与地面没有穿透？
5. 为什么左、右指的接触合力为零不表示没夹紧？
6. hydro 只有总 wrench，是否足够构造唯一的局部 slip_speed？
7. 将 C 点力矩换到 O 点，Shift 应传 `p_WC−p_WO` 还是相反？

<details><summary>答案</summary>

1. 压缩力将 B 推向 A→B，而 normal 指 B→A；按本约定 fn=−normal·force。
2. 不可。前者作用于 A，后者作用于 B；先统一对象、表达系和作用点。
3. 不可，会重复积分同一物理更新的 sampled 力。先按更新身份去重，再乘对应 h。
4. 不够。默认 sampled 输出首次步进前为空；也须检查几何与采样状态。
5. 两个大而相反的内夹力可抵消，净合力不能刻画两侧压紧水平。
6. 不够。需要指定局部位置、相对速度及统计方法；总 wrench 不唯一决定分布。
7. 传从旧点 C 指向新点 O 的 `p_WO−p_WC`，对应 τO=τC+(pWC−pWO)×f。

</details>

本专题的来源、静态核验和未运行范围见[E3 验证记录](evidence/e3-validation.md)。下一项建议 E4：传感器、渲染和可视化，在相同坐标/采样合同上继续展开。
