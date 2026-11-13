# Genesis 从 Scene 到刚体求解

阅读基线：`216a708e06124595521a9d36a51fae5393fd4ff8`，来源为官方固定源码。本篇是对象与关键机制导读，完整专题仍在开发；本轮仅做源码/文档核对，没有运行仿真实验。

## 1. 初始化、场景与实体

[gs.init](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/__init__.py) 设置全局运行环境；本版本 precision 使用字符串 `"32"` 或 `"64"`，backend 是另一项选择。场景由 [Scene](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/scene.py) 组织，内部 [Simulator](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/simulator.py) 负责不同求解器的调度。实体、材料、morph、surface 不能视作同一种对象。

[hello_genesis](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/examples/tutorials/hello_genesis.py) 给出从初始化到场景构建的原生顺序。添加对象与 build 是不同阶段：先描述拓扑与配置，再生成仿真所需结构。是否显示 viewer 不决定物理在 CPU 还是 GPU 上求解。

## 2. 批量维度是 API 契约

`Scene.build(n_envs=0)` 表示非批量用法；正数引入批量维度。写状态、读状态和控制时都要核对 shape，不要把 `n_envs=1` 自动当成没有 batch 维度。`env_spacing` 服务于场景显示排列，不应擅自加到环境内部的物理坐标。

多个环境应有明确的状态、reset 索引和控制输入归属。批量机制、张量设备及 CPU/GPU 拷贝已在 [E5](batch-learning-data.md) 展开；当前不做吞吐基准或训练。

## 3. 设置状态与控制实体

[RigidEntity](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py) 中 `set_qpos`、`set_dofs_position` 属于状态设置；`control_dofs_position/velocity/force` 是控制接口。配置坐标、DOF 速度和控制索引不是同一个数组空间。

学习关节控制时同时追踪目标、增益、力限制与求解器中实际使用的驱动力。不能因为 position 命令返回成功就推断物体通过物理过程到达目标。机器人资产还应核对自由基座、关节顺序、限位、惯量与碰撞网格。

## 4. 原生配置与历史实验分别记录

[RigidOptions](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py) 的本版本字段默认值包含 approximate_implicitfast 积分、Newton 约束求解、25 次迭代上限、pyramidal 摩擦锥和 noslip_iterations=0；tolerance 的声明值为 None，不能直接把它写成数值终止阈值，必须继续追初始化时如何解析。

这些是指定源码版本的默认字段，不代表用户运行配置，也不代表 DexLab 历史夹持实验。特别是历史报告提到 elliptic 时，必须保留其实际配置证据，不能被这里的默认值覆盖。

## 5. 从刚体步进走向约束算法

阅读路径为 Scene.step → Simulator → [rigid solver](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py) → [constraint solver](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py)。在每层标出哪些数据输入、哪些状态被修改、何时调用碰撞与约束求解。

CG 与 Newton 的分支、[noslip](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/noslip.py) 修正与积分配置分开学习。摩擦锥表示影响约束问题；改变算法与改变接触模型不应混为一个“精度按钮”。本版本刚体初始化拒绝 requires_grad 与 elliptic 的组合，这说明可微支持需要检查具体配置，不能只看项目总体介绍。

## 6. 渲染、多物理与学习接口

[Camera](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/vis/camera.py) 和 [触觉选项](https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/sensors/tactile.py) 是不同传感路径。图像、深度、接触力与触觉输出分别核对数据形状、单位、帧、更新阶段；视觉材质不应直接解释成物理材料。

这些观测接口已在 [E4 传感器与渲染专题](sensors-rendering.md) 展开，包含分割ID、轴深度/range和缓存时序的固定版本差异。

[E6 多物理、可微与扩展](extensions-boundaries.md)按 material→solver→coupler→state/backward 展开，涵盖热/触觉专项及能力缺项。求解器、耦合器、可微路径与 rigid solver 的支持集合分别列出，不把 batch 与异构拓扑混为一谈。[E5 批量、学习与数据](batch-learning-data.md)已展开 reset/step、终止/截断、随机种子、观测拼接、日志与回放；明确官方任务示例与外部训练器的边界，本阶段不启动策略训练。自查：能否解释 build 前后允许的操作、batch 维度、状态设置与控制的差别、默认值的解析路径？专题展开见[完整路线](curriculum.md)。

实验最终复用 [DexLab](https://github.com/huangkiki/Dexlab) 并保留原版本、配置和工况；当前不另建实验批次或评分器。
