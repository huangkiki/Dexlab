# E6：原生 System 扩展、依赖与标量转换

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [可微与标量边界](scalar-capabilities.md) · [特色能力与综合源码链](engine-boundaries.md)

先修 E1 的 Context、E2 的事件状态机和 E5 的环境隔离。固定阅读版本 Drake 1.57.0，commit `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。本篇补齐 B6 原生扩展契约，解释一个用户系统如何正确接入缓存、事件、Diagram 与标量转换。代码均为未执行阅读材料；没有 import、模型构建、仿真或 AD 运行。

## 1. 扩展入口首先由行为决定

Drake 的主要扩展单元是 System，而不是给一个全局物理 step 安装任意回调。输入端口描述依赖，Context 保存运行数据，System 声明计算和事件；Diagram 把它们连接成图。新增模块应选择实际改变行为的最小入口。

| 需要的行为 | 原生入口 | 必须维持的契约 |
|---|---|---|
| 代数控制律、信号变换、观测计算 | LeafSystem 的向量/abstract 输入输出 | 输出由当前 Context 与输入决定；声明真实依赖，不在 Eval 中推进隐藏状态 |
| 连续控制器、滤波器或辅助动力学 | DeclareContinuousState + DoCalcTimeDerivatives | 填导数对象，不就地改 Context；导数单位是状态单位/s |
| 采样控制器、任务阶段、随机过程 | DeclareDiscreteState / DeclareAbstractState + update events | 将下一状态写到回调输出；周期/offset、事件前后语义按 E1/E5 解释 |
| 记录、消息、显示 | publish event | 不改系统物理状态；外部 I/O 副作用要显式拥有并管理 |
| 多个原生模块组合 | DiagramBuilder.AddSystem / Connect / ExportInput / ExportOutput / Build | 保留每个子 System 的端口类型、Context 与生命周期；不能把建图当运行 |
| 给刚体施加外力 | applied spatial/generalized force 输入，或原生 ForceElement 子类 | 明确作用点、表达坐标、N/N·m；内部 force element 还需能量、功率和克隆合同 |
| 给 FEM 体施加体积力场 | ForceDensityField | N/m³、当前/参考体积约定及 Context 依赖；不是刚体 wrench 的同名替代物 |

LeafSystem 的输出需要 allocator 和 calculator；向量使用 BasicVector 或派生类型，abstract 值需可复制/克隆。见[输出类型和分配](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L1150-L1188)。连续、离散、非受限和 publish 回调是不同原生接口，不应以统一 `on_step` 藏掉它们的状态写入时机。

## 2. 依赖声明既关乎速度，也关乎正确性

输出端口值是 Context 中的缓存计算结果。默认依赖所有 sources 是保守正确的做法，但可能增加失效和重算；精确 prerequisites 能减少不必要计算，也帮助判断输入到输出的 direct feedthrough。默认 LeafSystem 保守假设所有输入直通输出，见[依赖与直通](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/leaf_system.h#L1178-L1235)。

例如连续一阶滞后：

$$
\tau\dot x=u-x,\qquad y=x,\qquad \tau>0.
$$

若 u、x、y 单位为 m，则 tau 为 s、xdot 为 m/s。虽然未来的 x 会受 u 影响，同一时刻的 y 只取当前状态，所以 `y=x` **没有 u→y 的代数直通**。声明输出依赖 `all_state_ticket()` 正确；导数仍读取 u。相反，`y=2u+x` 必须包含输入依赖，不能为了绕开代数环检测而谎报只有 state。

| 声明 | 对应读取 | 错误用法的后果 |
|---|---|---|
| `all_state_ticket()` | 仅状态决定输出 | 输出还读输入却漏报，会留下旧缓存并错误隐藏直通 |
| `input_port_ticket(index)` | 对应输入决定输出 | 不能借此代表所有参数/时间依赖 |
| 默认 `all_sources_ticket()` | 保守地依赖所有源 | 可能比实际更宽；先保证正确，再精化 |
| 自建 CacheEntry | 明确 allocator、calculator、prerequisites | 缓存不得替代影响未来的动力学状态；E5 logger 的观察用途另有专门合同 |

不要依赖“我每次都调用 Eval，所以每次都运行 callback”。缓存命中可以跳过 calculator；状态/输入失效后又可能重算。随机抽样、策略隐藏状态更新、累计奖励和 episode step 等改变未来的行为，应放在更新事件或每环境拥有的外部执行合同中。E2 的 TaskSequencer 和 E5 的 RandomSource 分别给出离散状态和 abstract RNG 的例子。

## 3. Python LeafSystem 不是任意 Python 对象的复制器

Python 导数回调通过 trampoline 到 `DoCalcTimeDerivatives(context, derivatives)`，输出 calculator 通过绑定包装，回调执行时取得 GIL。见[导数 trampoline](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L306-L318)和[calculator 包装](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L165-L178)。因此 native AdvanceTo 释放 GIL 不意味着 Python callback 能自由并行；E5 的 Context 隔离仍然适用。

构造器中的固定配置，例如端口维度和明确不可变的时间常数，可以是成员；每次运行的 x、积分项、滤波历史必须是 Context 状态。可调且需要按环境或求导的参数，应声明 numeric parameter，而不是偷偷修改共享 System 成员。Context 复制与 default/random reset 的范围见 E5；外部模型、文件和网络连接的克隆不能从 Python `self` 属性推断。

如果扩展输出 abstract 类型，应确认 allocator 每次产生适当的新存储、calculator 写入正确类型、可复制对象中的引用是否仍共享外部资源。`OutputPort.Eval` 的 vector/abstract 返回所有权不同，见 E5；不要在下游长期保存一个会被后续求值更新的借用对象，再将其称作快照。

## 4. System scalar conversion 做了什么

scalar conversion 克隆的是 **System 的计算结构与配置**，将 `System<double>` 变成 `System<AutoDiffXd>` 或 `System<Expression>`。它不是把一个已运行 Context 的所有值自动变成独立变量，也不保存 Simulator 的积分历史。官方示例分开执行系统转换、新 Context 创建、状态/参数拷贝、固定输入拷贝以及导数播种，见[原生完整转换顺序](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system_scalar_conversion_doxygen.h#L8-L61)。

| 原生 API | 合同 | 仍需另外处理 |
|---|---|---|
| `ToAutoDiffXd()` / `ToSymbolic()` | 产生新 System，不支持则抛异常 | 为新 System 创建匹配 Context，重新连接需要的几何/控制图 |
| `ToAutoDiffXdMaybe()` / `ToSymbolicMaybe()` | 不支持时返回空指针，Python 对应 None | 返回非空也不保证每个运行方法支持该标量 |
| `new_context.SetTimeStateAndParametersFrom(old)` | 复制时间/精度、state/parameter 数值 | 不复制 fixed inputs，不自动设置对哪些变量求导 |
| `new_system.FixInputPortsFrom(old_system, old_context, new_context)` | 将旧输入当前值固定到新 Context，忽略断开的输入 | 不是复制动态连接；含 scalar-dependent abstract 类型的输入跨标量有显式限制 |
| InitializeAutoDiff / symbolic Variable | 显式定义独立变量及导数方向/符号 | 不会替应用选择变量顺序、坐标、物理单位或合法配置 |

System API 的失败合同和 abstract 输入限制见[转换及输入拷贝](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system.h#L1271-L1362)。例如 QueryObject 或空间力容器是标量相关的 abstract 数据时，不能假定 FixInputPortsFrom 能把任意 double 对象转成 AD 对象；转换整体 Diagram 并保留正确的原生连接通常更符合模型结构，但整图每个子系统都必须支持转换。

Diagram 的转换能力取各子 System 支持的交集；一个仅 double 的 renderer、用户 callback 或物理模型即可使整图不支持目标转换。其构造最终调用 converter 的 `RemoveUnlessAlsoSupportedBy`，见[Diagram 能力交集](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram.cc#L1634-L1641)。若只需刚体运动学或局部动力学的导数，可建立契约明确的分析图；不能简单丢掉会影响该导数的接触、外力或控制环，再把结果称为原系统梯度。

## 5. 如何声明真正支持标量转换的扩展

C++ 常见模式是 `template<typename T> class ... final`，构造时给 LeafSystem 传 `SystemTypeTag<MySystem>{}`，并实现接受 `MySystem<U>` 的 scalar-converting copy constructor。复制构造应委托到普通构造器，并带过固定配置；一般用户调用 ToAutoDiffXd/ToSymbolic，不直接调用这个内部转换构造。见[C++ 原生模式](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/system_scalar_conversion_doxygen.h#L79-L161)。

若实现仅支持非 symbolic 标量，明确使用 `NonSymbolicTraits`；若只允许从 double 转换，使用 `FromDoubleTraits`。这描述 converter 合法的有向类型组合，不是“所有成员值都可无损互转”，见[转换 traits](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/scalar_conversion_traits.h#L46-L90)。转换到 double 可能丢掉导数；含未绑定变量的 symbolic 表达式不能总是转成数值。

Python 原生工具是 `pydrake.systems.scalar_conversion.TemplateSystem`：通过 `@TemplateSystem.define` 声明支持的 T，内部类继承 `LeafSystem_[T]`，实现 `_construct(..., converter=None)` 和 `_construct_copy(other, converter=None)`，不要自定义 `__init__`。必须把 converter 交给父类，并用 `Impl._construct` 明确委托，见[TemplateSystem 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/scalar_conversion.py#L29-L110)。只写了 `class Foo(LeafSystem)` 不会自动获得完整 scalar conversion。

[scalar_lag.py](../examples/scalar_lag.py) 是原创一阶滞后例子：输入/输出一维，状态 x，固定 tau=0.05 s，输出只依赖 state，导数保留 T 运算；复制构造保留 tau。它附有未调用的局部 AD 读取函数，展示如何只对 x 播种导数，常量 u 不播种。文件没有构造实例的顶层调用，但若被 import，装饰器仍会注册 Python 模板；**本轮连 import 也未做**，仅解析整个文件 AST。端口的 size 重载和 prerequisites 参数已对照[Python 原生输出绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_systems.cc#L846-L910)；导数对象的 CopyToVector 见[ContinuousState 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L1215-L1223)。

构造器要求 tau 有限且严格为正，拒绝 NaN/Inf。代码中的 tau 是明确固定的普通数值配置，不能据此得到对 tau 的导数。若研究参数辨识，应把 tau 放入 Context 的 numeric parameter 并播种它的导数；同样要声明参数依赖。不要在 scalar-aware calculator 中调用 `.value()`、ExtractValue 或强制 `dtype=float` 来“方便计算”：这会丢掉所需信息或拒绝该类型。需要输出数值报告时才从计算链末端显式提取 value/gradient。

## 6. 刚体力和体积力的扩展要保留物理接口

原生 `ForceElement` 不只“返回一股力”：计算力贡献、势能、保守功率、非保守功率各有方法，并须支持与多体树对象对应的 scalar clone。若自定义阻尼给出负耗散符号或把力施在错误 body origin，即使代码可以调用也会违背物理合同。见[力元素接口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_element.h#L21-L35)、[力与能量方法](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_element.h#L70-L146)和[标量克隆责任](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_element.h#L208-L247)。

FEM `ForceDensityField` 可声明依赖 Context 的输入和 cache，在 Plant Finalize 时挂接这些系统资源。它输出体积力密度；均匀重力为 $f_v=\rho g$，单位 $(kg/m^3)(m/s^2)=N/m^3$，应区分按参考体积和当前体积定义。见[力密度扩展与重力](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_density_field.h#L21-L95)及[重力体积约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/force_density_field.h#L118-L147)。这类 C++ extension seam 不等于所有虚方法都存在 Python trampoline；选择 Python 实现前必须核对具体绑定，不能凭 C++ header 想象 Python override。

## 7. 易错点与带答案练习

输出依赖、Context 状态位置、生命周期和标量注册是四项独立责任。接口可实例化只说明某一层满足类型合同；它不证明动态正确、并行安全或可微，下一篇继续检查实际方法路径。

1. **`xdot=(u-x)/tau, y=x` 是否有 u→y direct feedthrough？** 答：没有；导数依赖 u 不等于当前输出依赖 u。y 声明 state ticket，导数仍读输入。
2. **把 `y=u+x` 也声明为 state-only，能消除代数环吗？** 答：只是谎报依赖，会错误使用旧缓存并漏检环；应按真实方程声明。
3. **ToAutoDiffXd 后直接使用旧 double Context 是否正确？** 答：不正确；要创建匹配新 System 的 Context，按需要拷贝数值和输入，再播种独立变量。
4. **含一个 double-only 用户系统的 Diagram 能自动忽略它后转换吗？** 答：不能；能力取交集。分析图的拆分必须明确改变了哪些模型依赖。
5. **为何 Python `_construct_copy` 需要传 converter 并保留 tau？** 答：converter 注册目标标量转换，tau 决定实际方程；漏掉任一项会失去类型支持或改变模型。
6. **在 calculator 中取 `.value()` 后继续计算有什么风险？** 答：AD 导数被移出链，symbolic 也可能无法转数值；只在报告边界显式提取。
7. **给柔性体一个 10 N 向量可直接作为 force density 吗？** 答：不可以，力密度单位 N/m³，还须明确积分体积与表达坐标；集中 wrench 是另一接口。

[静态验收](evidence/e6-validation.md)。
