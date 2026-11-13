# 后端内部与可微边界：同一模型字段，不同执行程序

本课完成B6后端/导数主线，并连接B7源码追踪。先读[E3原生求解](solvers-and-integration.md)与[E5设备数据](mjx-and-device-data.md)。MuJoCo/MJX固定3.15.0树；JAX语义另以0.7.2固定树阅读，均见两份source manifest。没有import、JIT、梯度计算、模型编译、数值对照或GPU运行；这些来源不构成依赖兼容性锁。

## 1. 分清四个“导数”问题

| 问题 | 典型入口/实现 | 实际含义 |
|---|---|---|
| 运动学局部映射 | `mj_jac*`、配置积分/差分 | 已知状态下的Jacobian，不是整步仿真梯度 |
| 内部动力学导数 | `engine_derivative.c`等 | 为隐式积分/metric构造需要的局部偏导与近似 |
| 离散转移线性化 | `mjd_transitionFD` | 多次原生推进后的有限差分，依赖所选算法/状态恢复 |
| 自动微分 | JAX/Warp具体程序的变换规则 | 对执行的计算图求导；支持和数学光滑性需另审 |

有Newton Hessian不等于对模型参数提供autograd；有某些解析速度导数也不等于整个碰撞流水线是光滑函数。所谓“可微”必须附对象、方向、状态空间、后端和变换类型。

## 2. 原生有限差分的输入/输出空间

`mjd_transitionFD`计算局部离散状态和sensor对当前状态/控制的线性化。配置q含四元数时，扰动在速度维数nv的切空间中，线性化状态宽度为：

$$
n_x=2n_v+n_a,
$$

$$
\delta x_{t+1}=A\delta x_t+B\delta u_t,\qquad
\delta y_t=C\delta x_t+D\delta u_t.
$$

A形状(nx,nx)，B为(nx,nu)，C为(nsensordata,nx)，D为(nsensordata,nu)。y沿该步sensor执行时序产生，不能默认等于积分后完整刷新的一组观测。qpos原始数组长度nq不是姿态扰动维数；plugin_state/history/任务控制器也不是自动加到nx中。[FD入口与维数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L540-L560)。

这里nu在3.15定义为ctrl的标量宽度，nactuator才是执行器数量；ctrl限幅数组也按nu存储。B/D的列对应原始ctrl标量分量，不是每actuator一列，更不能自动解释成SO3三维旋转切空间的控制Jacobian。对多输入控制，仍需核对所选ctrl chart、归一化、限幅与扰动方向的意义。[尺寸定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L242-L250)、[输入布局](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L778-L810)、[逐标量差分](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L331-L365)。

中心差分概念上是：

$$
\frac{\partial F}{\partial x_i}\approx
\frac{F(x\oplus\epsilon e_i,u)-F(x\ominus\epsilon e_i,u)}{2\epsilon},
$$

其中输出的配置差也要用原生流形差分，不能普通相减四元数。有限ε需要在截断误差、舍入误差和接触/限幅分支变化之间取舍；不同输入分量还有不同物理单位，不存在一个ε自动保证全部列准确。

实际实现保存FULLPHYSICS|CTRL，并在需要时加WARMSTART，反复恢复后做扰动；它没有保存全部应用状态，也没有对plugin_state逐列求导。因此plugin数值状态被恢复，不等于返回A包含该状态的动力学。若actuator插件将内态放在act，可进入该维数；仍要检查回调纯度和实际插件行为。[保存/扰动契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L300-L345)、[act插件选择](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/extension.rst#L202-L219)。

本版transitionFD明确拒绝RK4、history和sleep；inverseFD另拒绝NoSlip。IPC含mask未覆盖的跨步状态，且逆动力学不支持，不能因转移API未在同一入口列出所有拒绝条件就推断它能正确差分IPC。该接口会实际反复推进模型，当前完全未执行。[transition检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L547-L558)、[inverse检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative_fd.c#L616-L634)、[IPC边界](ipc-contact-mode.md)。

模型质量/几何参数梯度也不在B中；B是控制输入导数。若要对参数做辨识，必须设计参数扰动、重新计算派生量和有效模型约束，不能把控制维数矩阵解释成任意模型参数的Jacobian。

## 3. CPU流水线中的动态结构

CPU `mj_forward`在当前状态下执行FK、质量矩阵、碰撞、约束装配、被动力/actuation、求解与传感；contact和constraint数量随状态变化，arena与稀疏结构为这些动态工作服务。discrete的有效metric还可通过算子应用flex/其他耦合，IPC进一步在step内部暂时发布rows并重新求解。

因此同样的“Newton/CG”名称指的是算法族，不意味着不同后端有相同矩阵布局、投影、迭代细节或支持扩展。CPU轨迹与GPU轨迹也不因为相同模型和seed就有逐位等价承诺。[原生执行课](dynamics-and-pipeline.md)、[原生solver课](solvers-and-integration.md)。

## 4. JAX路径：静态候选结构、masked rows与数组求解

JAX `fwd_position`按kinematics→com_pos→camlight→tendon→CRB→factor_m→collision→make_constraint→transmission推进；velocity阶段计算com_vel/RNE等。它是JAX array实现，不是在每个设备步里调用C的`mj_forward`。[位置/速度流水线](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L70-L104)。

为保持编译shape稳定，碰撞按类型、mesh和condim分组，提前确定候选输出数量。limit/contact等约束通过active mask把无效行的Jacobian/位置项置零，然后拼接efc数组；因此“数组里有某行”与CPU“当前激活的constraint计数”不是同一个观察方式。[分组](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/collision_driver.py#L15-L37)、[masked contact](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/constraint.py#L460-L493)、[装配](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/constraint.py#L693-L745)。

`max_geom_pairs`是每碰撞分组中按包围距离选候选的限制；`max_contact_points`在生成后按深度为每condim组选择接触。它们是改变保留候选/接触的策略，不只是预分配内存。调小这些值可能改变物理问题，不能在结果不合意后仅称“无损优化”。[数量推导](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/collision_driver.py#L346-L392)、[top_k选择](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/collision_driver.py#L405-L458)。

该JAX solver同时有CG与Newton分支：CG以M解预条件梯度，使用非负Polak–Ribière系数；Newton显式组装每世界Hessian，加入接触锥曲率，做对称化后Cholesky求方向。不能被函数docstring的“conjugate gradient”概述误导成只有CG。[梯度/Hessian](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/solver.py#L374-L420)、[方向/终止](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/solver.py#L557-L602)。

warmstart比较qacc_warmstart与qacc_smooth对应的代价选较优者；终止看改善、梯度与iterations。它不自动复现CPU本版discrete/flex metric/IPC的所有算子。[初始化与循环](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/solver.py#L589-L610)。

## 5. JAX可JIT不等于整条路径可反向AD

线搜索用固定长度scan包装条件推进，源码注明这一局部循环支持reverse-mode；但最外层solver在iterations≠1时实际调用`jax.lax.while_loop`。固定JAX0.7.2的while_loop接口明确说明不支持reverse-mode，因为其内存需求没有静态迭代上界。不能只看到内部scan或外层`jax.jit`就宣称默认带接触step可直接`jax.grad`。[线搜索scan](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/solver.py#L239-L253)、[外层while](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/solver.py#L599-L602)、[JAX规则](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/lax/control_flow/loops.py#L1606-L1645)。

这个结论沿公开调用链限定：[包入口直接导出step](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/__init__.py#L14-L40)，JAX分支的step调用forward，forward有约束时直接调用solver.solve；其named_scope装饰只添加名称作用域。这条链没有custom_jvp/custom_vjp或隐式求导包装替代外层while的反向规则。因此限制的是**该版本JAX后端进入约束solver、iterations≠1并对其求普通reverse-mode导数的路径**，不是所有MuJoCo模型/后端/导数接口都不可用。[调用链](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L488-L530)、[名称装饰](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L59-L67)。

无约束分支可能不进入solver，iterations=1也走不同分支，但这些条件不等于整个模型的所有操作已有梯度规则；把迭代数改成1还会改变物理求解。forward-mode、固定迭代展开或自定义隐式导数应分别审查，不能用一种路径的支持外推另一种。

即使变换能运行，得到的仍是当前数值程序的局部导数。top_k候选切换、碰撞特征变化、摩擦锥区域、限位与控制clamp会改变分支；接触边界可能不光滑。有限迭代梯度与完全收敛解的隐式梯度也不是同一个对象。读者需要先声明要优化哪个量，才能解释梯度。

## 6. Warp路径：世界数组、内核归约与条件图循环

MJX Warp经custom-vmap/FFI进入树内vendored Warp；它的forward/step使用Warp kernels和原地设备数组，不是把JAX solver简单换一个device参数。原生C回调注册表不会自动迁移；vendored model自己的`callback.control`是另一接口，执行位置在actuation前。[Warp执行链](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L1793-L1835)。

solver维护逐世界context、done与迭代计数；CG通过tiled归约构造方向，Newton还有对非elliptic约束状态变化的增量Hessian更新。elliptic区域依赖当前Jaref的曲率，不能复用同一增量快捷分支。sleep启用时压缩active DOF再求解，与普通每世界路径不同。[增量条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/solver.py#L3490-L3548)、[solve/压缩分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/solver.py#L3653-L3669)。

启用graph_conditional且iterations非零时，`nsolving`统计未结束世界，用`wp.capture_while`重复内核；否则用固定Python迭代次数调度，内核仍按各world的done处理。batch里一个世界收敛不表示整批都完成，也不表示每世界计数都等于总launch次数。[循环](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/solver.py#L3671-L3715)。

Warp runtime有AD能力不代表这个vendored物理实现已提供反向链；本树forward模块及大量solver kernels显式关闭backward。学习策略的梯度可以只经过策略网络，也可以来自无模型RL估计，两者都不要求物理step可微；应把训练算法与物理梯度分开。[forward开关](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L50-L55)、[solver kernel开关](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/solver.py#L3367-L3380)。

## 7. 固定版本能力矩阵

下表是源码支持边界，不是安装/运行验收或性能排名。MJX/Warp包与依赖身份沿[E5](mjx-and-device-data.md)，这里不引用未分析的独立最新发行版。

| 能力 | 原生CPU | MJX JAX | 树内vendored Warp路径 |
|---|---|---|---|
| solver | PGS/CG/Newton及相应组合检查 | CG/Newton；无PGS分支 | CG/Newton；拒绝PGS/NoSlip |
| integrator | Euler/RK4/implicit/implicitfast/discrete，受扩展组合限制 | step分派Euler/RK4/implicitfast | Euler/RK4/implicit/implicitfast，无discrete |
| flex | full与插值、StVK/SNH等本课范围 | put_model遇nflex明确拒绝 | 有部分flex路径；拒绝quadratic、rigid flex、flex–SDF/HField/internal碰撞 |
| IPC | 本课所述AL+CCD | 枚举有IPC，不构成实现；缺discrete step/flex | enable flag列表不含IPC、integrator不含discrete |
| native plugins | CPU注册/实例生命周期 | 不自动执行C插件；USER执行器类型被拒绝 | body/actuator/sensor plugins明确拒绝 |
| history/采样 | CPU3.15原生逻辑 | 同名history存储不等于delay/interval已实现 | 有delay/interval执行；MJX包装初始化另有差异，见下文 |
| 导数 | Jacobian/内部局部导数/有限差分各有范围 | AD由实际程序/循环规则决定 | 本树主要forward/solver kernels关闭反向 |
| 图像/显示 | E4 classic/Filament各自接口 | 物理step本身不等于图像管线 | 设备物理和渲染/读回仍需独立配置 |

JAX拒绝条件见[put_model](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L310-L386)和[step](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L515-L530)。Warp见[输入/插件/插值检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/io.py#L240-L310)、[flex碰撞拒绝](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/io.py#L401-L410)、[flag](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/types.py#L303-L316)及[积分器](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/types.py#L484-L499)。数组转换成功也不能填补执行分支缺失。

Warp上传还会针对插值壳bending damping发出未支持警告，dense模式有当前实现的nv上限；这是具体组合边界，不能因“支持flex”就在这些模型上宣称与CPU同义。JAX的history、CPP I/O枚举、device copy和容量差异继续见[E5设备课](mjx-and-device-data.md)。

## 8. history要分别检查后端执行与包装初始化

本树vendored Warp实际实现了actuator history：actuation读取延迟ctrl，advance在time增加前插入ctrl。传感器在POS/VEL/ACC各阶段末尾执行delay/interval处理；它先保留新sensor值，再读历史覆盖公开sensordata，最后把新值插入buffer。因此不能把JAX分支没有history推进的结论复制到Warp。[延迟ctrl](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L1606-L1617)、[advance插入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L332-L347)、[sensor顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/history.py#L746-L794)、[ACC接入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/sensor.py#L2840-L2842)。这一顺序还意味着单独forward可能修改后端history，不能只按CPU推进次数推断缓存演化。

直接vendored make_data会复制原生Data的history；reset kernels设置cursor、负时间戳、interval相位及四元数控制初值。反之，本版MJX公共`_make_data_warp`先建立零history，再显式跳过从vendored Data复制该字段；FFI shim又确实将传入history接到Warp Data。这是**源码可见的初始化差异**，未做运行重现，不宣称所有delay情形都失败或自动等价CPU。[直接初始化](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/io.py#L1825-L1829)、[reset内容](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/history.py#L558-L659)、[公共零字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L583-L598)、[跳过复制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L778-L808)、[FFI接入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/warp/forward.py#L1164-L1177)。

学习任务若依赖延迟/采样记忆，需要声明准确入口、初始化来源、forward/step次数和恢复内容；“支持history字段”远不足以证明时序一致。E5原生CPU例子没有使用这些设备分支，本轮也没有执行它们。

## 9. 带答案阅读练习

1. **A矩阵宽度为什么不是2nq+na？** 配置扰动在nv维切空间里，特别是free/ball的四元数冗余不作为独立扰动。
2. **transitionFD恢复plugin_state，说明A包含它吗？** 不说明；A状态宽度是2nv+na，没有plugin_state列。
3. **B能作为质量参数梯度吗？** 不能；B对ctrl输入求导，参数辨识另需定义扰动及派生量更新。
4. **JAX线搜索用scan，整个solver就支持reverse-mode吗？** 不一定；外层默认是while_loop，必须逐层检查。
5. **减少max_contact_points只是省内存吗？** 还按深度选择保留接触，可改变约束问题。
6. **Warp有AD，为什么此处不能直接宣称可微物理？** 实际forward/solver kernels关闭反向，而且FFI链也有各自规则。
7. **两后端同叫Newton就应逐位一致吗？** 不应；矩阵、锥、dtype、迭代和扩展支持都可能不同。
8. **把CPU插件model上传设备就会调用同一个C插件吗？** 不会自动发生；需后端自己的实现/支持，Warp明确拒绝多类native plugins。

继续：[多物理与综合源码追踪](multiphysics-and-source-trace.md)。
