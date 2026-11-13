# E5：日志采样、数据所有权与回放

[Sim Atlas 学习首页](https://github.com/huangkiki/sim-atlas) · [多环境与重置](batch-lifecycle.md) · [随机化与学习接口](randomness-learning.md)

阅读基线：Drake 1.57.0，固定官方提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`。先修 E3 力观测和 E4 capture/available/consume 时间。本篇完成 A9 的采样、存储、回放与模型差距解释，补充 B6 数据拷贝及外部记录接口。没有生成数据集、运行引擎或新建实验评分器。

## 1. 原生 VectorLogSink 的位置

`VectorLogSink` 是接收数值向量的无状态 sink；记录的数据由每份 Context 的独立 cache 持有，不是控制反馈状态。`LogVectorOutput(port, builder, ...)` 是添加 sink 并连接端口的便利函数；不能把它连接到 Image/ContactResults 等 abstract 端口，并期待自动得到表格。见[logger 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h#L21-L45)和[原生接线 helper](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h#L140-L184)。

| 需求 | 原生 API / 数据形状 | 关键限制 |
|---|---|---|
| 记录 n 维向量 | VectorLogSink(n, ...)；LogVectorOutput | n 由输出端口决定；各行单位/顺序由应用另外声明 |
| 从根 Context 找记录 | `logger.FindLog(root_context)` | 根 Context 必须属于包含 logger 的系统；不是任意同形 Context |
| 已有 logger 子 Context | `logger.GetLog(logger_context)` | 不要把根 Context 直接交给 GetLog |
| 可变日志 | FindMutableLog / GetMutableLog | Clear / Reserve 操作日志，不重置物理状态 |
| 时间列 | `sample_times()`，长度 M | 记录 publish 时的 Context time，不是所有输入的真实采集时刻 |
| 数据矩阵 | `data()`，形状 `(n, M)` | 每列一个样本；常见机器学习 `(M,n)` 约定需显式转置 |

对应[Find/Get API](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h#L102-L137)及[VectorLog 形状和容量](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.h#L16-L79)。对 n 维 double、M 帧，仅数值和时间的主体存储约为 $8M(n+1)$ bytes，不包括容量余量、Python 对象和元数据；实际内存不能仅由文件压缩大小估计。

## 2. per-step、periodic 与 forced 是不同采样合同

默认 `publish_period=0` 启用 **per-step + forced**。它通常从 Initialize 发布开始，随后受 Simulator 内部步/事件分割影响；不是策略循环频率，也不是固定均匀时间栅格。

`publish_period>0` 的简便构造启用 **periodic + forced**。周期发布 offset=0，但另一次 ForcedPublish 仍会增加样本；比如 DrakeGymEnv 的 human render 可能触发它。因此“传了 0.01 s”不等于“数据中只有严格 100 Hz、且绝无重复时间戳”。要仅周期日志，可显式指定 `{TriggerType.kPeriodic}` 和正周期；如果去掉 forced，人工 ForcedPublish 就不再是该 logger 的抓帧操作。见[默认与显式 trigger 集合](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.h#L64-L96)及[事件声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.cc#L15-L70)。

对选定的 periodic-only logger，名义采样时刻为：

$$
t_k = kT_{\mathrm{log}},\qquad T_{\mathrm{log}}>0.
$$

此式描述已执行发布事件的时标，不保证预定最终时刻已经处理完所有事件，也不保证 log 输入对应同一物理采样时刻。E3 sampled force 可能对应前一个 Plant 更新，E4 Async image 可能更早捕获；同一 logger 的同列只是**本次发布读到的值**。需要在数值端口里同时提供 source timestamp，或者独立记录各模态时标再按约定关联。

`WriteToLog` 实际执行 `AddData(context.get_time(), input.Eval(context))`，见[写入路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.cc#L112-L115)。VectorLog 不检查时间单调、重复或有限值，也不校验数值合理性，见[容器合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.h#L16-L22)。它是内存记录器，不是已经清洗的 episode 数据集。

## 3. 日志不属于 State，reset 要单独管理

源码为日志声明一个 `nothing_ticket()` 依赖的 cache entry，计算回调为空，publish 直接修改其中的容器，见[日志缓存声明](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log_sink.cc#L32-L40)。所以 SetDefaultContext/SetRandomContext 只重设 state/parameters 时，不会自动清掉历史记录。若把时间从 5 s 改回 0 再初始化，旧日志和新回合可以拼在同一个容器中，出现时间回退。

若需要空的新回合，可创建新的 Context；若复用 Context，在保存需要的数据后明确 `FindMutableLog(root_context).Clear()`。Clear 只把样本数量置零，保留容量；Reserve 提前申请容量、追加超容量会扩容，不会形成环形缓冲或自动落盘。见[Clear/Reserve 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.h#L34-L79)和[追加与扩容实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/vector_log.cc#L16-L40)。长回合必须有明确的记录策略和内存预算，不能假定 VectorLogSink 会截断历史。

Context.Clone 复制缓存，logger 历史随之复制；“给每个 clone 清物理状态”不会把这些前缀日志变成独立新轨迹的空记录。日志 cache 应只用于观测，不从这里反读数据驱动物理，否则缓存的观察用途与状态的动力学职责混淆。

## 4. Python 返回的是副本还是借用

| 具体读取 | 固定绑定语义 | 保存到长期记录的做法 |
|---|---|---|
| `OutputPort.Eval(context)`，vector | 先创建 Eigen 向量副本，再转 Python | 已与原 Context 向量值分离；仍需定义时间/单位 |
| `OutputPort.Eval(context)`，abstract | 解包 AbstractValue，可能引用 Context 内对象并保持其寿命 | 按具体类型做明确副本/序列化，不能假定深复制 |
| `OutputPort.EvalBasicVector` | 返回内部 BasicVector 引用 | 若要长期保存数值，取值后 copy；不要写原生输出缓存 |
| `VectorLog.data()` / sample_times，double | 绑定允许引用；data 显式构造 Eigen Map | 在 Clear、追加扩容、Context 销毁/替换前 `.copy()` |
| AutoDiff/Expression 日志 | 标量绑定转为复制，object dtype | 不是默认数值训练数组，更不是 GPU tensor/完整梯度图 |
| Image.data、Gym rgb_array 切片 | 可能共享图像内存 | 如需独立帧，显式 copy，并保存捕获 pose/time |

源码见[Eval 与 abstract 所有权](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L49-L70)、[EvalBasicVector](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/framework_py_semantics.cc#L855-L866)、[日志 Python 绑定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/systems/primitives_py.cc#L603-L632)和[double 引用与其他标量复制策略](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/bindings/pydrake/common/default_scalars_pybind.h#L34-L73)。图像的 HWC、uint8/uint16/float32 与单位详见[E4 图像合同](sensors-rendering.md)。借用生命周期有效与“内容永远不变”是两个问题：保持 owner 存活也无法使后续写入成为独立快照。

最小阅读片段（未执行；logger 属于 diagram，root_context 是该 diagram 的根 Context）：

```python
def copy_log(logger, root_context):
    log = logger.FindLog(root_context)
    time_s = log.sample_times().copy()
    values = log.data().copy()  # rows are fields; columns are samples
    return time_s, values
```

先明确拿到独立 CPU 数值副本，再由应用决定 NumPy 文件、列式表、图像文件或学习框架 tensor 的格式、dtype、转置和 GPU 拷贝。Drake 的内存日志 API 没有替应用承诺某种文件 schema、压缩策略、原子落盘或跨设备零拷贝。

## 5. 一条可解释记录的最小元数据

以下是本课程建议的数据合同，不是 Drake 内建输出格式；后续沿 DexLab 原协议使用，不另建评分器。

| 字段组 | 应保存的具体内容 | 少了它会混淆什么 |
|---|---|---|
| 身份 | episode/env id；engine/core/binding 源码与二进制版本；模型/资产 hash | 不同拓扑、构建配置与原生默认值 |
| 配置 | Plant 步长、接触近似/solver、积分器/容差、控制/传感/日志周期与 trigger | 策略步、物理更新、观测保持和数值误差 |
| 状态/动作 | q/v 映射、关节/actuator 名、动作定义与单位、是否限幅、保持区间 | 状态设置、驱动命令、目标值与实际反馈 |
| 模态时间 | capture、available、consume/log 时间；source sequence 与有效标志 | 延迟、丢帧、旧输出、初始化零值及事件边界 |
| 坐标与量纲 | frame、参考点、受力侧、RGB/depth/label 格式及无效值 | wrench 方向、深度单位、body/world 混用 |
| 随机性 | 种子/流策略、回合实际参数、拓扑/资产选择、外部 RNG 身份 | 同种子不同消费顺序、未记录的 domain randomization |
| 结束/故障 | terminated/truncated 原因、目标/实际时间、异常及有效样本范围 | 正常结束、时间上限、数值失败与部分轨迹 |

例如某图像 capture=0.060 s，available=0.080 s，在 0.090 s 记录，消费时图像 age=0.030 s；log 时间不能反写成曝光时间。力观测如果是步平均力 N，不能当作瞬时冲量 N·s；有 wrench 时还要保留作用点，见 E3。理想状态和带延迟/噪声的 sensor output 应分别命名，不用“observation”一个词抹掉来源。

## 6. 回放首先选择要重放哪一层

**信号回放**：把已记录向量随时间送进原生端口。`TrajectorySource` 保存 trajectory 的克隆并在当前 Context 时间求值，输出维度由行数及导数阶数决定；它不会自动理解这些数值是 N、rad 还是 m。见[TrajectorySource 合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.h#L17-L62)及[求值路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.cc#L149-L180)。

**运动学/视觉回放**：按记录设置 q 或 frame pose 再发布显示，可以审查动作/几何轨迹；它绕开真实动力学推进，不能验证接触、力矩、能量或控制稳定性。显示同一运动不是独立物理复现，采样时 pose 与图像的关联仍要正确。

**动力学重放**：使用同一模型、初态、参数和动作保持时序重新推进。需要保存求解/积分配置、事件安排、随机流和外部输入等；仅 q/v 起点相同不保证长时逐位相同。RNG snapshot 或 Context clone 也没有完整复制 Simulator 和外部设备。当前课程不承诺跨平台 bitwise 相等，未来应使用 DexLab 的实际协议和误差标准验证。

对信号插值，先审记录时间是否严格递增、是否有重复和缺失，再选择原生 trajectory：

| 原生 trajectory | 定义域和插值 | 数据使用限制 |
|---|---|---|
| `DiscreteTimeTrajectory` | 只在采样时间容差内定义值；不是阶梯保持 | 若连续积分器在任意中间时刻请求值，可能抛异常；不能直接当连续控制源 |
| `DiscreteTimeTrajectory.ToZeroOrderHold()` / `PiecewisePolynomial.ZeroOrderHold` | 区间内使用左侧样本，显式建立保持 | N 个 break 只构造 N−1 个区间；最后样本值被忽略，只保留它的 break time；保持最后动作需要另给后一时间边界及对应数据 |
| `PiecewisePolynomial.FirstOrderHold` | 相邻样本之间线性插值 | 改变了动作波形，不能用它冒充原先的零阶保持动作或四元数球面插值 |

见[离散 trajectory 与 ZOH 区别](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/discrete_time_trajectory.h#L14-L53)、[时间/维度/容差合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/discrete_time_trajectory.h#L66-L110)和[ZOH/FOH 工厂](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.h#L207-L256)。DiscreteTimeTrajectory 的合法时间需严格递增、间隔大于时间容差；日志容器本身没有这类检查，二者不能无条件直接衔接。

ZOH 的末样本处理要按实现理解：[构造循环](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.cc#L762-L785) 只访问 samples[0] 到 samples[N−2]。例如 break=[0,0.1] s、samples=[2,4]，只构造保持 2 的一个区间，末样本 4 不会得到独立的保持段。若要在 [0.1,0.2) s 保持 4，必须明确补上 0.2 s 边界和一列对应数据，例如 break=[0,0.1,0.2]、samples=[2,4,4]；最后一列仍只为满足样本/时间列数合同，其值不参与生成区间。

`TrajectorySource` 调用 trajectory 的 `value(time)`；对 PiecewisePolynomial，这条[虚函数路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.h#L811-L815) 进入 [DoEvalDerivative](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/common/trajectories/piecewise_polynomial.cc#L209-L223)，将域外时间 clamp 到 start_time/end_time，再求值，而非继续多项式外推。上述两 break 的 ZOH 在 t=0.2 s 仍会返回 2，不会改用被忽略的 4。**能返回一个端点值不代表原记录在该时刻有效**；回放程序仍需显式限定有效时间范围。这里核对的是 `value` 路径，不概括所有 trajectory 类型或其他求值入口。TrajectorySource 的 zero_derivatives_beyond_limits 则控制附加导数块的域外归零，与主 value 的类型相关边界行为分开。

对于向量信号，若 $t\in[t_k,t_{k+1})$，零阶保持为 $u(t)=u_k$；一阶保持为：

$$
u(t) = (1-\alpha)u_k + \alpha u_{k+1},\qquad
\alpha = \frac{t-t_k}{t_{k+1}-t_k}.
$$

这里假设 $t_{k+1}>t_k$ 且信号可在线性空间插值；四元数、离散 label、接触模式不满足直接套用此公式的语义。不要线性插值跨故障或跨回合的动作，更不能只对显示轨迹插值就说物理轨迹已复现。

`TrajectorySource.UpdateTrajectory` 修改的是 **System 成员**，没有 Context 参数；多个 Context 共享该 System 时，不是仅替某个环境换轨迹。它还涉及缓存依赖与线程并发，不能靠修改成员就假设已有 Context 立即以安全方式刷新全部依赖。源码见[trajectory 成员](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.h#L60-L79)和[UpdateTrajectory 实现](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/primitives/trajectory_source.cc#L95-L115)。每环境不同命令可用独立 System 或已声明的 Context 状态/输入合同设计，不能无说明地并行改共享源。

## 7. 易错点与 sim-to-real 边界

- `LogVectorOutput(..., publish_period)` 默认仍含 forced trigger；截图/显示可能产生额外日志，不能把样本数量直接当策略步数。
- 清 State 不清日志缓存；Clone 不创建空日志；Clear 保留容量且不会撤销旧 NumPy 借用带来的共享关系。
- logger 的每列是发布时读到的各值，时间戳不自动代表各传感器 capture time。
- 原生日志不会自动保存模型、单位、坐标、随机抽样和异常信息；这些必须显式进入协议。
- domain randomization 改变模拟分布，不等于已证明真实传感延迟、摩擦、执行器动态和资产尺度被覆盖；真实标定与差异验证仍是未来独立证据。

## 8. 阅读练习与答案

1. **log.data 形状 (6,1000) 表示什么？** 答：六个数值字段、1000 个样本列；不自动说明六维是 wrench，字段的单位/表达坐标/参考点须另存。
2. **10 ms periodic 默认 logger 在 5 ms ForcedPublish 会怎样？** 答：默认包含 forced，可能新增 5 ms 样本；严格周期用途应显式只选 kPeriodic，并核对初始化/边界事件。
3. **同一 Context reset 到 t=0 后 SetDefaultContext，为何旧帧还在？** 答：日志是独立 cache，不是 State；需要保存后 Clear，或建立新 Context。
4. **`saved = log.data()` 后 Clear 再追加可以当上回合独立数据吗？** 答：double 绑定可能借用底层存储，写入/扩容会改变或失效；应在容器变动前显式 copy。
5. **60 ms 捕获、80 ms 可用、90 ms 记录的图像 age 是多少？** 答：30 ms；10 ms 只是在可用后等待的部分，记录时间不是捕获时间。
6. **DiscreteTimeTrajectory 样本在 0、0.1 s，可直接供 0.03 s 的控制求值吗？** 答：一般不能；它仅在样本时刻容差内有定义。需要明确转 ZOH/其他插值，并知道这改变了什么信号合同。
7. **播放保存 q 得到相同动画，能证明接触力与原运行一致吗？** 答：不能；运动学播放绕过动力学和求解。要比较动力学必须按模型/配置/动作/随机与事件合同重放并独立验证。

[静态验证与未执行范围](evidence/e5-validation.md)。
