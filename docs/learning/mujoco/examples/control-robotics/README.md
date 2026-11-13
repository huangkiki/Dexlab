# E2 原生控制与运动学片段

配合[驱动与控制](../../docs/actuation-and-control.md)、[机器人与运动学](../../docs/robotics-and-kinematics.md)和[任务编排](../../docs/task-interfaces.md)阅读。

| 文件 | 用途 | 运行状态 |
|---|---|---|
| [two_link.xml](two_link.xml) | 原创平面双铰链模型：一个双输入 PID、一个 gear=2 motor，关闭碰撞、重力为零 | 仅 XML 结构检查，未编译 MJCF |
| [inspect_control.py](inspect_control.py) | 显示 nactuator/nu/nout 与控制/输出地址，追踪一次 forward 的限幅 | 仅 AST 与源码核对，未执行 |
| [position_ik.py](position_ik.py) | 用原生 FK/Jacobian/integratePos 构造有迭代上限与回溯的局部 XY IK | 仅 AST 与源码核对，未执行、未验证收敛 |

按 XML 与源码推导，`nq=nv=2`、`nactuator=2`、`nu=3`、`nout=2`；这是静态预测，不是运行日志。两个脚本均没有 `mj_step`，但模型编译和 forward 本身会进行原生计算，因此本轮也未执行这些调用。

读者后续可在[安装说明](../../docs/installation.md)对应的 3.15.0 环境中运行 `python examples/control-robotics/inspect_control.py` 或 `python examples/control-robotics/position_ik.py`。IK 仅适用于这个无闭环、无接触的两个标量 hinge 模型；结果是候选配置，不是机器人可执行轨迹。任务状态机课给出接口与失败分支，不提供未验证的抓取演示。
