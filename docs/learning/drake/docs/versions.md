# 版本与证据边界

| 身份 | 当前记录 |
|---|---|
| 阅读版本 | 1.57.0 |
| 官方源码 | [RobotLocomotion/drake](https://github.com/RobotLocomotion/drake/tree/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d) |
| 固定提交 | `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d` |
| 源文件身份 | [sources.json](sources.json) 中的 Git blob 已与下载文件核对 |
| 已完成检查范围 | 文档相对链接、固定来源与源码文件身份；API 片段只做语法检查 |
| 原生运行与实验 | 本阶段未开展 |
| 专题状态 | E1/E2/E3/E4/E5/E6 已交付；其他主题见[课程目录](curriculum.md) |

固定文件身份不能证明整个引擎已审查，也不能证明候选二进制与源码具有相同构建配置。核心、绑定、插件和宿主身份分别记录。当前版本的默认值不用于补填 DexLab 历史配置。

[DexLab](https://github.com/huangkiki/Dexlab) 保留实验版本与协议；本仓不修改或追认其结果。

E1 具体文件、源身份、绑定核对、语法和未执行项见[验收记录](evidence/e1-validation.md)。源码标签、Python wheel 安装版本与运行宿主是不同证据，本次只确认固定源码及绑定代码。

E2 的控制/运动学/任务资料按同一源码基线阅读，新增验证见[E2 记录](evidence/e2-validation.md)。未运行 IK 求解、控制闭环或抓取任务；优化可行性和动态执行能力仍须分别验证。

E3 沿固定核心与绑定追踪接触、SAP 与力观测，[验证记录](evidence/e3-validation.md)保留源码注释/实现差异和全部未运行项。本版本 solver 枚举仅有 SAP；其三种接触近似与历史 TAMSI 资料分开，不能补写 DexLab 历史批次配置或 #117 运行资格。

E4 的[静态证据](evidence/e4-validation.md)覆盖相机、传感器、图像绑定、渲染和显示的固定实现。未安装或 import pydrake，未运行 EGL/GLX、VTK、Meshcat、Async 或惯性传感器；源码默认 backend 与本机实际图形设备不是同一证据。

E5 的[静态记录](evidence/e5-validation.md)覆盖 Systems/Simulator、MonteCarlo/随机化、官方 DrakeGymEnv、向量日志与 trajectory 回放。Python helper 与 C++ 并行能力分开；固定源码的 handler、初始化顺序和返回所有权差异不等于已完成运行复现或上游修复。未 import、采样、模拟、训练或性能测试。

E6 的[静态记录](evidence/e6-validation.md)覆盖标量转换、Python 原生扩展、几何/接触方法支持、优化前置条件、FEM 和内部 MPM 的实际归属。源码中的模板或 converter 不作为端到端可微证据；本轮未执行 AD、symbolic、优化或任何柔性/多物理运行。
