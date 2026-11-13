# 回调与插件：扩展逻辑由谁调用，状态由谁拥有

本课覆盖B6扩展API，并为B7建立从声明到执行的追踪方法。先读[驱动与控制](actuation-and-control.md)、[传感采样](sensors-and-sampling.md)和[记录与回放](recording-and-replay.md)。以下均基于固定MuJoCo3.15.0源码；没有加载动态库、import原生引擎、编译模型或执行回调。

## 1. 先区分四种扩展

| 机制 | 改变哪一层 | 状态/生命周期 |
|---|---|---|
| `mjcb_*` | 原生流水线中的全局函数指针 | 进程级注册；Python闭包由应用管理 |
| `mjpPlugin` | actuator、sensor、passive或SDF的原生扩展 | 全局插件定义 + 模型实例 + 每份Data中的实例状态 |
| decoder / encoder | 资源与`mjSpec`之间的解释/序列化 | 返回对象和资源buffer有独立所有权 |
| resource provider | 资源的读取/写入/挂载 | URI前缀注册，open/read/close等回调 |

插件不是通用“任意位置插入一步”的钩子，也不等于一个外部RL环境。四种physics capability由`mjtPluginCapabilityBit`定义，不能注册一个不存在的“custom solver”位就替代原生接触求解器。[接口头文件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjplugin.h#L26-L180)。

## 2. mjcb是全局入口，调用次数由流水线决定

`mjcb_control/passive/sensor/contactfilter/act_dyn/act_gain/act_bias/time`均是全局变量。`mj_resetCallbacks`会清空这一组物理回调；它不是只清理当前模型的控制器。[定义与reset](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_callback.c#L20-L42)。

| 入口 | 所在阶段 | 写入/返回的原生语义 |
|---|---|---|
| control | forward的加速度相关阶段，在actuation之前 | 常见写ctrl；输入单位取决于actuator，不统一是力矩 |
| passive | 内置被动力累加之后、passive plugins之前 | 通常在`qfrc_passive`上累加广义力，避免覆盖内置项 |
| sensor | POS/VEL/ACC阶段按sensor定义调用 | 写已分配sensor输出，遵守地址、维度和阶段 |
| act_dyn/gain/bias | 对应USER类型执行器分支 | 分别是内态导数、增益或偏置；不是一次统一PD回调 |
| contactfilter | 原生候选碰撞过滤 | 影响是否进入后续碰撞，不定义接触力律 |

控制回调也会在`mj_forward`中执行；RK4可能多次计算子阶段；有限差分会反复扰动并评估。IPC还会重复计算加速度阶段sensor。因此回调中的“计数加一”“取下一条网络消息”“推进外部积分器”不能无条件被当作一物理步一次。需要演化的物理内态应放到引擎有明确积分时序的位置，或由应用在明确动作边界推进。[forward控制调用](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1990-L2013)、[passive顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1019-L1040)、[IPC sensor重算](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1261-L1281)。

Python设置器保留Python对象并安装trampoline；进入Python回调要重新取得GIL。释放GIL的原生batch调用不意味着Python回调可以免费并行。源码还对free-threaded Python使用mutex保护回调注册对象，但这不使用户闭包自动成为无共享状态的控制器。[trampoline](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/callbacks.cc#L209-L255)、[设置与对象引用](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/callbacks.cc#L367-L397)。

下面是**单调用者、所有相关回调均由Python绑定管理、无并发推进**时的最小示意；传入的model/data已经存在，函数若执行会运行forward，当前只做AST审查。它演示异常时恢复注册，不提供线程隔离，也不能保存其他代码直接写入的裸C函数指针。

```python
import mujoco


def refresh_with_controller(model, data, controller):
    previous = mujoco.get_mjcb_control()
    mujoco.set_mjcb_control(controller)
    try:
        mujoco.mj_forward(model, data)
    finally:
        mujoco.set_mjcb_control(previous)
```

[get/set绑定](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/callbacks.cc#L487-L490)、[get返回Python注册对象](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/python/mujoco/callbacks.cc#L422-L427)。全局回调不适合让多个同进程任务轮流“临时安装”而不协调；Data隔离不能替它隔离闭包。

## 3. 插件定义、实例、Data是三层

`mjp_registerPlugin`把名称、属性名和函数指针注册到全局表。`mjModel.plugin[instance_id]`保存实例所用的注册slot；`nplugin`统计实例数，不是动态库数。一个实例可以被多个sensor/actuator引用，从而共享一次对象逻辑，而两个同名插件实例拥有不同状态。[注册](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_plugin.cc#L498-L536)、[实例声明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/extension.rst#L28-L127)。

MJCF首先在`extension/plugin`声明依赖；共享实例需要显式`instance`，使用点引用该实例。config的key由插件声明，值以字符串配置交给插件解释；注册了key不等于任何字符串都已通过物理有效性检查。应读插件实际的解析、范围验证和错误返回。

“插件实例线程局部”应具体理解为**状态在相应MjData中**：同一个model可为多个Data分配各自实例负载。引擎不会因为两个OS线程都拿同一个Data就自动克隆插件，也不会隔离插件内部私有的全局变量。纯逻辑/只读权重可共享，可变缓存要有明确所有者。[状态契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/programming/extension.rst#L166-L200)。

| 存储 | 含义 | 谁负责恢复 |
|---|---|---|
| `plugin_state` | `mjtNum`时间演化状态，长度由nstate决定 | 引擎state mask可包含；插件按其语义读写 |
| `plugin_data` | 不透明指针/缓存/模型权重对象 | 插件init/destroy/copy；必须能由配置与物理状态重建 |
| `act`/`act_dot` | actuator插件选择使用的内态及其导数 | 引擎积分；与plugin_state不是同一数组 |

存温度在C++对象里而只保存`plugin_state`空数组，会破坏恢复语义；把一块GPU指针写入浮点状态也不会使它成为可移植checkpoint。插件数据应是可重建实现细节，物理记忆需要放在可恢复状态中。

## 4. 沿真实生命周期追踪

1. **注册/编译**：库加载后注册定义；编译根据实例与能力配置确定nstate、sensor维度等。`mj_loadPluginLibrary`是公开加载入口，不意味着库已经为当前设备/ABI构建并验证。
2. **创建Data**：`mj_makeData`建立buffer，调用实例init，随后reset；init可分配plugin_data。返回负值会使创建失败，不应把未完成分配留给一个并不存在的正常实例销毁流程。[初始化](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1021-L1055)、[makeData](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1131-L1140)。
3. **reset**：引擎保留相应payload指针，再调用plugin reset处理状态；清零整个指针数组不是reset。[reset分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1560-L1578)。
4. **计算**：按capability调用compute；actuator_act_dot先于actuator compute，sensor按needstage，passive在被动力阶段。compute可能被重复求值，应避免偷推进时间。
5. **推进**：积分器提交内态/端点后，`advanceFinish`先增加time再调用可选advance；所以advance读到的新time与pre-step compute不同。[提交顺序](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1442-L1461)。
6. **复制**：`mj_copyData`复制数值buffer并保持目的Data自己的plugin_data指针，然后调用可选copy；不能把裸指针memcpy当深复制。[copy](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1248-L1279)。
7. **销毁**：每实例destroy释放自有资源，再释放Data buffer/arena；注册定义的生命周期与某个Data不同。[destroy](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_io.c#L1039-L1055)。

头文件用required/optional注释描述契约，而实际分派有空指针保护；例如现存无plugin_state的cable插件没有reset回调。读者应按自己使用的能力提供所需函数，而不能据一次成功注册推断所有生命周期路径都完整；注册入口主要检查名称/属性数量，不执行全套能力测试。

## 5. 用两个一方插件检验理解

`mujoco.pid`插件把积分误差与可选slew记忆放进`act`，`StateSize`返回0。`actuator_act_dot`写内态导数，compute读误差/速度并写actuator_force，advance为空，因为内态已由引擎积分。它与E2的内置PID类型是不同实现，不能交换参数后宣称行为相同。[PID内态与注册](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/plugin/actuator/pid.cc#L167-L291)。

还必须读适用范围：这个插件遍历`nu`并按旧的单输入actuator索引读取ctrl/ctrlrange；3.15核心已有多输入布局。因此不把它当作任意SO3/多输入actuator的通用PID。源码TODO也说明其隐式积分所需速度导数尚有接口缺口。[PID解析与索引](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/plugin/actuator/pid.cc#L97-L163)。

`mujoco.elasticity.cable`是passive插件，按相邻刚体的相对转动与参考曲率计算弯曲/扭转反力；它不是flex三角形/四面体有限元的别名。注册文件当前仅注册Cable，旧文档提到的Solid/Membrane/plate插件不能据名称直接当作本树可加载能力。[cable注册](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/plugin/elasticity/register.cc#L15-L22)、[曲率力](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/plugin/elasticity/cable.cc#L74-L109)、[生命周期](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/plugin/elasticity/cable.cc#L279-L318)。

## 6. SDF、decoder与resource的不同边界

SDF插件提供局部坐标的distance、gradient、编译期staticdistance/attributes与aabb。距离应以模型长度单位表达，梯度是对局部位置的导数；碰撞候选求解再负责坐标转换与接触输出。编译视觉mesh使用的是`sdf_staticdistance`，此时还没有运行Data实例；扩展文档一处写成distance，实际调用应以编译器为据。[SDF接口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjplugin.h#L158-L180)、[编译调用](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L366-L400)。

SDF碰撞以多起点局部优化寻找接触，目标包含`A+B+abs(max(A,B))`；起点数和迭代数有限，因此非凸表示不自动给出所有接触或全局最优保证。视觉mesh的细分与原生隐式碰撞场也不是同一几何近似。[目标](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_sdf.c#L428-L450)、[多起点配置](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_sdf.c#L1290-L1310)。

decoder返回新`mjSpec`，调用者负责删除；encoder把spec/model写成资源；resource provider管理实际字节。当前头文件有mount/unmount/write，旧扩展说明仍列getdir，不能照旧结构体写插件。open失败时不会自动close，open必须清理失败前分配；read给出buffer和字节数，buffer的寿命必须覆盖读取使用。[当前接口](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjplugin.h#L26-L107)。模型能被decoder读入只证明结构转换，不证明单位、惯量或接触配置已保真，仍需E1的导入审查。

## 7. 带答案阅读练习

1. **一个plugin注册两次等于两个运行实例吗？** 不等于；定义在全局表，运行实例由model声明并在每份Data中分配。
2. **compute里每次让温度加h×导数，有什么问题？** compute可能被forward/RK4/差分重复调用；应让状态推进对应明确积分/advance契约。
3. **同一个Data给两个线程，插件自然线程安全吗？** 不安全；实例负载跟随Data，不由线程访问自动克隆。
4. **nstate=0说明PID插件无记忆吗？** 不能；该插件把积分/slew记忆放在act，需沿actdim/act_dot阅读。
5. **copyData后能直接让两个Data共享可变plugin_data吗？** 不能无条件共享；需要copy处理或独立可重建缓存，避免互相修改及双重释放。
6. **SDF视觉mesh生成时能依赖运行中的plugin_data吗？** 不能，编译期用staticdistance和配置，实例尚未创建。
7. **注册表成功返回slot意味着插件支持MJX吗？** 不意味着；CPU注册和各设备后端有不同实现/拒绝条件，见后端课。
8. **resource.open失败后谁清理部分资源？** open自己清理；接口明确失败时不调用close。

继续：[flex与弹性](flex-and-elasticity.md)。
