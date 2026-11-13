# Newton 从 ModelBuilder 到 Solver

阅读基线：`713fecdc41caf0c9d726f5c016939f36e66e3dff`，来源为官方固定源码。本篇是对象与关键机制导读，完整专题仍在开发；本轮仅做源码/文档核对，没有运行仿真实验。

按顺序展开见 [E1 建模/状态](modeling-state-time.md)、[E2 控制/机器人](control-robotics-tasks.md)、[E3 接触/求解](contact-solvers-forces.md)、[E4 感知/渲染](sensors-rendering.md)、[E5 批量/数据](batch-learning-data.md) 和 [E6 特色求解/扩展](extensions-boundaries.md)。各专题包含带答案练习与固定源码；API 例子未经执行。A0 完整安装专题与全路线审校仍待 E7。

## 1. 模型、状态与执行器分开

Newton 的 [overview](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/guide/overview.rst) 与 [ModelBuilder](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py) 是入口。Builder 组织 bodies、shapes、joints 等模型元素，finalize 后形成 [Model](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/model.py)；[State](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/state.py) 保存随时间变化的状态，[Control](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/control.py) 承载控制，Contacts 承载碰撞结果。Solver 负责具体推进算法。

阅读 [pendulum 示例](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/examples/basic/example_basic_pendulum.py)，给 model、state_0/state_1、control、contacts 标注读写方向。常见双缓冲模式在 step 后交换输入输出状态；忘记交换会使后续读取或推进使用错误的状态。

## 2. 空间量约定必须逐字段读

Newton 的 State.body_qd 定义为质心的世界系线速度在前三项、世界系角速度在后三项。这与 Warp 一些原生 spatial vector 的排列约定不同。不能因为两者都长 6，就直接混用。

位置/姿态、自由度坐标、速度与控制维度分别核对；四元数顺序与 transform 构造遵循 [conventions](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/conventions.rst) 和实际字段。涉及力矩换作用点时，先写清方向、表达坐标及参考点，再按源码实现推导；不要复制一条不带约定的空间向量公式。

## 3. 碰撞与动力学的接口

[collisions](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/collisions.rst) 解释形状、碰撞生成和 contacts。碰撞检测输出不是最终接触力，solver 可以使用不同的接触模型、迭代方式和支持集合。

模型导入、关节驱动、闭环约束与机器人控制应以当前 solver 的支持为前提。同一 ModelBuilder 能描述一个字段，不表示所有 solver 都会消费该字段。

## 4. Solver 是重要的能力边界

先读 [solver 索引](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/solvers/index.rst)，再分别进入实现。[SolverXPBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/solver_xpbd.py) 使用 XPBD 约束修正，本版本构造默认 iterations=2；这不能替代 DexLab 某次运行指定的 4 次迭代配置。

该实现明确说明一些限制：按接触数加权的刚体修正可能不保持动量；返回接触力和父关节反力带有近似；关节限位按硬位置约束处理，不能期待 limit_ke/kd 在该路径发挥弹簧阻尼作用。armature、joint friction、effort/velocity limit 等支持也应按本版本文档逐项核对。

[SolverMuJoCo](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/mujoco/solver_mujoco.py) 接入 MuJoCo/MuJoCo-Warp 路线。外部后端及其构建身份需单列，不能把该路径的结果简单算作另一套独立算法的对照证据。

## 5. Warp、world 与性能

[worlds](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/docs/concepts/worlds.rst) 解释多环境组织；Warp 负责相应数组与计算内核。CPU/GPU、设备数组、JIT、graph capture、同步和 host 读取都是不同成本来源。一个 GPU 可见或者库能 import，并不能证明某个 workload 使用了 GPU 加速。

学习并行路径时标注哪些数据可以批量、哪些回调触发同步、哪些 topology 变化需要重新构建。当前只做接口和源码解释，不新增性能基准。

## 6. 控制、可视化与扩展怎么继续

控制专题从 Control 和 solver 消费位置追踪；观测专题从 State/Contacts 和 readback 追踪；可视化是消费者，不能充当物理正确性的验证。可微、软体、插件等特性也按 solver 单列，避免用项目层能力概述替代具体支持矩阵。

[E6](extensions-boundaries.md)具体追踪 SemiImplicit/VBD 的不同 tet 力、Style3D 的输入修改、MPM 的网格与材料历史、Kamino 的 DVI，以及 Proxy/ADMM 的实体所有权和约束支持。梯度需要独立前向值和完整可微消费者；创建 requires_grad 数组不是端到端保证。B7 用模型→控制→接触→XPBD→观测串起完整阅读路径，帮助检查每个字段的写者、读者和失效条件。

阅读练习：在原生示例中标出每个数组的所有者和设备；解释 state buffer 交换；选一个 joint 字段查明 XPBD 是否支持它。完整专题进度见[课程路线](curriculum.md)。

实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 并保留原版本、配置和工况；当前不另建实验批次或评分器。
