# 原生 API 阅读例子

[model_state.py](model_state.py) 使用 Drake 1.57.0 的原生 Python API，展示 Parser → Finalize → Diagram → Context、浮动基座世界位姿、空间速度、数组副本、根 Context 克隆和默认状态重置。

**交付状态：源码核对与 Python 语法检查；未执行。** 不含 Simulator、AdvanceTo、独立实验或评分器。即使以后运行并成功打印，也只证明该环境下的 API/状态操作，不证明物理、接触或性能正确。内嵌 URDF 是本课程原创均匀盒，没有外部资产。

先阅读[模型与坐标](../docs/modeling-state-time.md)和[状态与时间](../docs/state-time.md)。预测浮动基座的 nq/nv、快照与原 Context 的位置差异，以及 SetDefaultContext 后的时间，再对照固定源码解释。当前阶段不要求运行。

可在不安装/导入 Drake 的情况下检查语法：

```bash
python -c "import ast; from pathlib import Path; ast.parse(Path('examples/model_state.py').read_text())"
```

源码/语法检查不覆盖 Parser 实际接受资产、Python ABI、几何后端与运行期约束；这些限制记录在[验收文件](../docs/evidence/e1-validation.md)。

## E2：控制、机器人与任务

| 文件 | 说明 | 未执行边界 |
|---|---|---|
| [arm_kinematics.py](arm_kinematics.py) | 原创两杆 URDF，显式 actuator/焊接、TCP FK/Jacobian、独立 Context 中的 IK 问题 | 未构建模型或求解；无碰撞几何/避障声明 |
| [sampled_pd.py](sampled_pd.py) | 复用该原创资产，原生 PID → Saturation → ZeroOrderHold → actuation | 未运行闭环；参数未经调参或稳定性验证 |
| [task_sequencer.py](task_sequencer.py) | LeafSystem 周期事件与 Context 状态，接近/闭合/保持/释放/异常 | 未执行事件；force/slip 输入是假定合同，未实现传感 |

这些文件不是统一仿真封装。两个 arm 示例共享一个具体教学模型的构建函数；任务例子独立说明 Systems 的状态/事件，不伪造机械臂轨迹或接触源。所有代码均只做完整 AST、源码 API 和资产静态检查，阈值/增益/周期只是教学数值。见[控制与机器人](../docs/control-robotics.md)、[任务接口](../docs/task-interfaces.md)、[E2 验证](../docs/evidence/e2-validation.md)。

## E3：接触配置与原生字段读回

[contact_inspection.py](contact_inspection.py) 明确配置原创 sphere/ground、point 与 hydro 材料、Lagged 近似和 sampled 输出。独立 reader 保留 point 的 B 侧力、hydro 的 A 侧 wrench、作用点、几何/刚体身份与 query time，不伪造物理 sample time。main 只包含建模步骤，不调用 reader；本轮连这些建模步骤也未执行，只做 AST、源码和球惯量静态检查。它不是接触实验或触觉传感器，详见[E3 验证](../docs/evidence/e3-validation.md)。

## E4：相机的显式采样与时标

[sampled_camera.py](sampled_camera.py) 使用原创锚定球体、SceneGraph perception role、命名 VTK renderer、RGB-D 相机和三个原生 ZeroOrderHold，仅保持 depth32F、X_WB 与正确连接的 capture_time。固定版本的 RgbdSensorDiscrete 时间端口导出差异见[时序篇](../docs/sensor-timing.md)。函数未执行；甚至 renderer 构造、Diagram 构建和 Context 创建都没有运行，不存在输出图片。初始 ZOH 零值不是已经捕获的图像；需要将来有授权的事件执行才产生样本。相机 body 与 depth frame 在该例中重合，移动/偏置相机需另外核对捕获时外参。[E4 验证](../docs/evidence/e4-validation.md)。

## E5：独立 Context、随机流与日志副本

[isolated_records.py](isolated_records.py) 声明一个 RandomSource → periodic-only VectorLogSink 的原生 Diagram，为两份独立 Context 显式设置不同 Drake RNG，并各配一个 Simulator。替换回合函数分配新 Context；日志读取函数复制 host 数组。没有自动调用入口，没有物理模型或 Gym 封装，未 Initialize/AdvanceTo，连建图与随机状态设置也未执行。构建完成不代表已经产生周期日志；初态样本、t=0 更新和后续 logger 事件分别解释，见[生命周期](../docs/batch-lifecycle.md)、[随机化](../docs/randomness-learning.md)、[数据](../docs/data-replay.md)及[E5 验证](../docs/evidence/e5-validation.md)。

## E6：保留标量和依赖的一阶滞后系统

[scalar_lag.py](scalar_lag.py) 使用原生 TemplateSystem 和 LeafSystem_[T]，声明一维输入、连续状态及 state-only 输出，给出 converter/copy 契约。未调用的局部 AD 函数只播种 x；tau=0.05 s 是固定配置，u 为常量。xdot=6 m/s 与对 x 的导数 −20 s⁻¹ 来自教学解析式，未由引擎计算。模块没有顶层实例构造，但 import 仍会注册装饰器，所以本轮仅 AST 解析，未 import、转换、求值、仿真或优化。见[原生扩展](../docs/systems-extensions.md)、[标量边界](../docs/scalar-capabilities.md)及[E6 验证](../docs/evidence/e6-validation.md)。
