# 历史 PhysX：求解器读回与运行时来源

[English](physx-solver-audit.md) · [逐条回执索引](physx-historical-receipts.md) · [审计 #126][issue]

**三组独立 SDK 对照明确读回了 PGS、TGS，以及逐位置迭代施加外力的 TGS。历史 PhysX 证据并非一套统一的 TGS 配置。** 其他批次通常保存了迭代／偏移设置，却没有保存求解器名称；表面可变形体使用独立接口。各批次实际加载的 PhysX 原生核心版本、构建与库文件身份仍未恢复，[#126][issue] 的审查决定撤回缺少观测记录的精确核心版本归因，以及历史批次统一使用某求解器的声明。

## 审计范围与身份层次

2026-10-09 的只读审计以仓库 `19c686437e4c40c4af2a8ccebf3272e64d6fb401` 为基线，覆盖公开的 PhysX 资格、驱动、机器人、SDF、接触明细、苹果、布料、接触开发和法向／瞬态响应证据。核验六份发布归档、仓库清单，以及与公开哈希绑定的本地苹果／机器人记录。[索引](physx-historical-receipts.md)列出 **145 条逻辑回执**，其中有复用记录和失败，不能计作 145 次独立成功实验。本次没有启动物理进程、重新评分或改变阈值。

| 层次 | 证据能确认什么 | 边界 |
|---|---|---|
| 宿主与 worker | 已记录处为 `isaacsim==5.1.0.0`、`isaaclab==0.47.2`、Torch `2.7.0+cu128`；许多 worker 还保存 `isaacsim-kernel==5.1.0.0` | 早期失败和部分开发回执缺少包清单，不继承后续运行的版本 |
| 适配器 | 已记录处为 UniSim `1.7.10`，另有各批次源码／补丁；后期回执保存聚合源码哈希 | 同版本号不代表相同适配器。独立 SDK 对照和表面仿真不经过 UniSim 物理适配器 |
| 分发包 | [历史 wheel 清单][wheels]记录官方 `isaacsim_extscache_physics-5.1.0.0`，SHA256 为 `a4b450c7b33d2ada42e1736ac48e002103aac0b93e4f618d9fa4c212762dc74b` | 分发清单不是逐次加载的原生库证明 |
| 集成层与原生核心 | 保留安装目录的 `omni.physx` manifest 为 `107.3.26`，与[官方集成注册表][registry]一致 | 当前目录检查不能识别每个历史核心。官方 [107.3 / PhysX 5.6.1 发布][release]也不能证明某次运行加载了其二进制 |

Python／包版本、集成扩展版本和原生 SDK 版本分别记录。NumPy 输出类型或 CUDA 设备名称也不能证明原生求解器精度。

## 直接求解器证据与源码解释

[独立 SDK 对照][controls]分别保存 `run.json`、源码和压缩 USD。源码显式设置 `PhysxCfg(solver_type=...)`；`scene_readback` 读取 `GetSolverTypeAttr()` 及外力属性。归档 USD 与回执一致：

| 记录 | 历史场景求解器 | 每次位置迭代施加外力 | 物理步长／配置的位置、速度迭代 |
|---|---|---|---|
| `pgs` | PGS | false | 1 ms／8、2 |
| `tgs-default` | TGS | false | 1 ms／8、2 |
| `tgs-substep` | TGS | true | 1 ms／8、2 |

最后一项改变求解迭代内部的外力施加方式，不等于执行八个独立的 1 ms Python 物理步。这些是 USD 场景配置，不是实测迭代次数或原生收敛轨迹。更早的 `direct-v1` 夹具漏设 DriveAPI，作为无效夹具保留；其 `completed` 回执不能独自证明引擎验收通过。

[归档适配器 helper][helper]构建 IsaacLab `PhysxCfg` 时没有覆盖 `solver_type`。当前保留且文件干净的 IsaacLab 源码 [`3c6e67bb5c7ada942a6d1884ab69338f57596f77`][isaaclab]定义 `0=PGS`、`1=TGS`，默认 `1`。这解释了**以该源码确为历史依赖为条件**的 TGS 路径，不能代替缺失的逐次依赖身份或名称读回。helper 的 `read_engine_solver_values` 读取 USD 设置但遗漏求解器类型，所以多份导入报告的 `solver.requested` 和 `solver.effective` 均为 `null`；这不代表 PGS、零次迭代或仿真失败。

## 分批配置与适配改动

下表 **8/2** 指配置的位置／速度迭代值，不是实际执行次数。设置仅适用于存在对应记录的条目，早期缺失字段仍缺失。报告文字中的“TGS 配置”是归因，不能自动视为独立运行时测量。

| 公开批次／回执数 | 设置与表示 | 适配器及证据边界 |
|---|---|---|
| [基础接触资格][primitive]／5 | 三份有效导入为 1 ms、8/2、接触偏移 1 mm、静止偏移 0 | 三份完成、两份原始准入错误；接触报告／角色缓存修复；没有求解器名称读回 |
| [夹持 v2][pinch]／7 | 冻结源码为 1 ms、3.5 s；有限原始几何夹指；已记录处为 8/2、1 mm/0 偏移 | 保留原始／修订资格和错误；同一接触报告补丁，不混合两轮协议 |
| [驱动 v1][drive]／13 | 上述三组明确对照、两份更早 SDK 诊断、八份适配器资格／回归回执 | 原生外力时序选项；默认设置的速度失败保留。独立 SDK 和适配器记录分开 |
| [机器人 v0.7.0][robot]／9；父子碰撞过滤复测／1 | 最终记录为 1 ms、8/2、逐迭代外力；凸碰撞体／坐标约化、54 关节无载运动 | 归档有两份拒绝导入和一份仅导入回执；后续过滤复测单列，均不等于带载 SDF 抓取 |
| [SDF v0.8.0][sdf]／16 | SDF 分辨率 256／子网格 6，对照为凸包；已记录处为 8/2、逐迭代外力；后期偏移 0.1 mm/0 | 两份早期错误；含 20 步机器人导入，非带载抓取。不给早期缺失偏移补值 |
| [接触明细][details]／1 | 1 ms、8/2、0.1 mm/0 偏移；法向接触点与摩擦锚点独立 | 适配器在摩擦 getter 复用 SDK 缓冲前复制法向缓冲；缺少求解器名称 |
| [苹果开发与公开抓取][apple]／20 | 主要为 1 ms，含一份 0.5 ms 开发记录；最终为 8/2、0.1 mm/0 偏移、最小扭转半径 1 mm、逐迭代外力 | 碰撞排除、SDF 传输和扭转选项有变化；最终回执及 107 个产物匹配公开清单。完整数组仅本地保留，未公开下载 |
| [表面布料 v0.11.0][cloth]／54 | 三角表面 `OmniPhysicsSurfaceDeformableSimAPI`；物体位置迭代 16；0.5/0.25/0.125 ms；静止／接触偏移为案例半径／两倍半径 | 直接 SDK 表面接口，不作刚体 PGS/TGS 归因；声明质量不是节点质量读回；`physx-surface` 是任务配置名 |
| [接触开发 v0.12.0][development]／10 | 九份已完成 PhysX：平面四份、压入一份、圆柱四份；基准 0.5 ms、控制周期 1 ms；8/2、0.1 mm/0 偏移 | 保留一次传感器准入错误；记录适配器身份／聚合源码哈希；法向和摩擦观测独立 |
| [法向响应 v0.13.0][normal]／5 | 0.5 ms，另有一份 0.25 ms；8/2、0.1 mm/0 偏移；每条柔顺约束 5,000 N/m、2 N·s/m | UniSim 柔顺接触扩展；参数来自组合 USD，非原生材料张量；保留 0.4 kg 稳定性与惯量失败 |
| [瞬态响应 v0.14.0][transient]／4 | 三份力弹簧在 0.5/0.25/0.125 ms 下使用阻尼 10 N·s/m；单独惯量复测仍为 2 | 精度扩展用 17 位有效数字写编译后惯量；修复适配器序列化，不改变 PhysX 精度，也不改写旧失败 |

布料归档实际包含 **42 份 `completed`、10 份 `unsupported`、一份 `preparing` 和一份 `running`**。后两份是封存的历史中间状态，不是当前活跃进程或完成实验。`completed` 也不等于验收通过；原报告中的表面交叉失败及重复分歧保持不变。

最初接触报告补丁 SHA256 为 `3042eb5d1078c605d18069ac76ae3ac2625ceb99a6c7f18c8cf9961939b39a08`。后续法向响应适配器源码聚合哈希分别为 `5397e9754f1633d90cf907c2098247f39995b3858b4a61bd6628f2f8644d6aac`（v0.13）和 `6092ace9eda2a14b0721e545c19ca480bb1efaeda27d90feabc0186ecc9cefa0`（v0.14）。不能将最新组合补丁身份套用到早期批次。布料则记录 `deformableUtils.py` 与 tensor API 的源码哈希，它们不是 PhysX 核心哈希。

后续[摩擦响应][friction]、[响应—成本][cost]和[配对迁移][transfer]研究均因稳定运行时未准入而明确排除 PhysX，不为本索引增加 PhysX 试验。

## 时刻、观测与归档核验

多数适配器时钟由声明步长和同步完成步数计算，没有原生时钟读回。接触 getter 提供最近完成子步的数据；法向接触点不能与摩擦锚点逐一配对。[接触明细报告][details]使用实际速度变化检查力账，但这不能恢复缺失的执行器力历史或原生收敛遥测。即使旧 provenance 文本写“native runtime readback”，USD 迭代界限和偏移仍属于配置证据。

六份完整归档的大小、SHA256 和全部清单项均核验通过。Tar 硬链接按逻辑文件解析，没有执行内容。仓库清单另核验基础接触 52 项、夹持 89 项、驱动 132 项，包含驱动清单中的解压日志／USD 哈希。苹果最终清单核验回执及 107 项原生产物；两个开发索引核验 11 份回执哈希与九份状态数组哈希。父子过滤复测另核验公开的回执和状态哈希。

| 发布归档 | 字节数 | SHA256 | 已核验清单项 |
|---|---:|---|---:|
| [v0.7.0 机器人][a7] | 26,639,986 | `239065360b79dbb146550684a16a9d09a3022af52da55214d29c16f734bbd3c8` | 576 |
| [v0.8.0 SDF][a8] | 2,508,468 | `1275587a5236d8523ca7d2f3060a837c8c0267667dfe6ed8d02c5f7fe97c6ae6` | 365 |
| [v0.11.0 布料][a11] | 280,621,732 | `07bb00d45c487cae3ab1a4ee987eaade24f5f37ed23c4d11970fee3690ff134e` | 1,840 |
| [v0.12.0 接触][a12] | 136,594,576 | `5a836c146ed5b726d29f60813322e68e4cb03a1ba7f9c8f301c379ec4e003279` | 709 |
| [v0.13.0 法向][a13] | 3,928,405 | `8d6b187dc6f9ce6f2e6d1175a07bac4c5a838f953b22e4dd88f00feb7dd97f7a` | 342 |
| [v0.14.0 瞬态][a14] | 3,638,099 | `2e5e1934d43e05fb0d4f86ce3f36603384fcf55b514d8cfba8af29b5d71bc199` | 276 |

## 保留限制与审查结论

已搜索六份完整归档及清单、145 条逻辑回执、保留的苹果／机器人记录、可用应用日志与匹配的适配器／SDK 源码，未确定各历史批次加载的原生核心／构建／库身份，也未恢复缺失求解器选择。某回执引用的完整 SDK 应用日志在其记录位置未保留。新探针不能生成旧证据。

**审查结论（2026-10-09）：** 撤回这些历史批次的精确原生核心版本归因，以及缺少显式读回记录的统一 TGS 声明。三组 PGS/TGS SDK 对照保留为场景设置观测；有条件的 IsaacLab 源码路径继续标为推断。历史结果可以描述已记录的宿主／路径／配置，不能用于确定核心版本之间的排名或隔离求解器的因果作用。缺失字段仍未恢复，全部原评分、失败及中间回执不变。按维护者覆盖优先计划，#126 的有界审计至此完成。

[PhysX #150](https://github.com/huangkiki/Dexlab/issues/150)、[框架对照 #152](https://github.com/huangkiki/Dexlab/issues/152)与[夹持 #132](https://github.com/huangkiki/Dexlab/issues/132)承接新准入：分开记录输入／有效设置、可获取的实际加载库与源码身份，并在冻结前说明不可观测字段。新证据使用独立批次身份。只有发现与历史回执绑定的同期原生身份或求解器快照时才重开历史问题。本次审计未使用正式夹持批次预算。

[issue]: https://github.com/huangkiki/Dexlab/issues/126
[registry]: https://docs.omniverse.nvidia.com/kit/docs/kit-registry-reference/latest/107/shared.html
[release]: https://github.com/NVIDIA-Omniverse/PhysX/releases/tag/107.3-physx-5.6.1
[isaaclab]: https://github.com/isaac-sim/IsaacLab/blob/3c6e67bb5c7ada942a6d1884ab69338f57596f77/source/isaaclab/isaaclab/sim/simulation_cfg.py
[wheels]: ../demos/physx-contact/evidence/sdk-wheel-sizes.json
[controls]: ../demos/physx-contact/evidence/drive-v1/native-drive-comparison-v1/
[helper]: ../demos/physx-contact/evidence/drive-v1/qualification/substep/unisim-physx-solver.py
[primitive]: ../demos/physx-contact/README.zh-CN.md
[pinch]: ../demos/physx-contact/pinch.zh-CN.md
[drive]: ../demos/physx-contact/drive.zh-CN.md
[robot]: ../demos/physx-contact/robot.zh-CN.md
[sdf]: ../demos/physx-contact/sdf.zh-CN.md
[details]: ../demos/physx-contact/contact-details.zh-CN.md
[apple]: ../demos/physx-contact/apple.zh-CN.md
[cloth]: ../demos/physx-contact/cloth.zh-CN.md
[development]: ../demos/contact-benchmark/README.zh-CN.md
[normal]: ../demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md
[transient]: ../demos/contact-benchmark/TRANSIENT_RESPONSE.zh-CN.md
[friction]: ../demos/contact-benchmark/evidence/friction-response-v1.json
[cost]: ../demos/contact-benchmark/RESPONSE_COST.zh-CN.md
[transfer]: ../demos/contact-benchmark/TRANSFER.zh-CN.md
[a7]: https://github.com/huangkiki/Dexlab/releases/download/v0.7.0/v0.7.0-robot-articulation-evidence.tar.gz
[a8]: https://github.com/huangkiki/Dexlab/releases/download/v0.8.0/v0.8.0-sdf-contact-evidence.tar.gz
[a11]: https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz
[a12]: https://github.com/huangkiki/Dexlab/releases/download/v0.12.0/v0.12.0-contact-development-evidence.tar.gz
[a13]: https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-normal-response-evidence.tar.gz
[a14]: https://github.com/huangkiki/Dexlab/releases/download/v0.14.0/v0.14.0-transient-response-evidence.tar.gz
