# 任务、参数与证据盘点（D01）

[English](README.md) | [简体中文](README.zh-CN.md)

**结论：现有证据支持具体配置下的接触实验，尚不支持真实材料精度或引擎总排名。** 夹布的旧通过记录已被几何复核否定；抓梗、布料与基础接触各自的协议不能混合统计。

盘点日期：2026-09-30；源码基线 [8be5d6a](https://github.com/huangkiki/Dexlab/tree/8be5d6a7aacfaa4d762ff17a78f6af28553adc72) (v0.15.0). 本次仅盘点，不调模型、控制器、阈值或引擎。外部项目另见[固定版本任务卡](upstream.zh-CN.md)，属于源码阅读，未在 DexLab 复现。

## 执行路径

下表命令从仓库根目录执行；`python` 指本仓库 `.venv/bin/python`，`OUT` 必须是新目录。先按[安装说明](../installation.zh-CN.md)准备对应可选后端；`MJ_RECORD` 为完整 MuJoCo 抓梗记录。这里只审核入口，没有在盘点过程中运行所有实验。引擎别名 `mujoco/superdex/physx`；第三方 SDK、GPU 和资产条件见各行链接。

| ID / 任务 | 源码与配置 | 运行入口 | 场景 / 引擎 / 几何 | 控制与可观测量 | 独立评分与边界 |
|---|---|---|---|---|---|
| A1 — 苹果梗 SDF 抓取 | [apple_stem](../../src/dexlab/tasks/apple_stem.py) · [协议](../../docs/sdf-backends.zh-CN.md) | `bash demos/apple-stem-grasp/run.sh --backend mujoco --headless` (`superdex`) | DexLab 原生场景；MuJoCo / SuperDex FP64；刚性苹果与 SDF 指腹 | 已知位姿规划、绝对关节目标；实际关节、物体位姿、逐步接触力 | `verify_sdf_grasp.py RECORD`；保持、支撑、穿透、动量、腕部相对运动 |
| A2 — 苹果场景与步长回归 | [benchmark](../../src/dexlab/benchmark.py) · [suite](../../benchmarks/apple-stem-v1.json) | `python -m dexlab.benchmark run --split regression --output OUT` | 复用 A1；冻结质量、平移、转角；双方参数分别固定 | 批次调用 A1；并非新控制器 | 逐次 A1 评分；`benchmark report` 另检查记录完整性，不重算物理 |
| A3 — PhysX 苹果梗 | [physx_apple](../../src/dexlab/physx_apple.py) · [复现](../../demos/physx-contact/apple.zh-CN.md) | `python -m dexlab.physx_apple --source-run MJ_RECORD --output OUT` | DexLab 场景描述 → UniSim IsaacSimBackend → SDK；原生 SDF/TGS | 转移模型、脚本关节目标；物体/连杆位姿、原生接触账本 | `physx_geometry.py` + `physx_apple_score`；采样表面上界单列 |
| C1 — 机器人摩擦夹布 | [scene](../../demos/cloth-folding/src/cloth_model.py) · [复核](../../demos/cloth-folding/SCORING.zh-CN.md) | `bash demos/cloth-folding/run.sh --no-video --robot-model MJ_RECORD/model.xml --output OUT` | DexLab 直接构建 MuJoCo flex；无附着约束 | 脚本关节目标；关节、布顶点、在线接触摘要、25 Hz 回放 | `verify_cloth.py RECORD --output NEW.json`；历史记录返回几何复核状态 2 |
| C2 — 基础布料：拉伸、下垂、球面覆盖、折叠下落 | [cloth_benchmark](../../src/dexlab/cloth_benchmark.py) · [cloth-v1](../../benchmarks/cloth-v1.json) · [self-contact](../../benchmarks/cloth-self-contact-v1.json) | `python -m dexlab.cloth_benchmark run --solver mujoco --case dev-sag --output OUT` | DexLab 原生场景；MuJoCo flex、SuperDex shell、Newton 五条求解器路径 | 规定节点力或自由演化；节点位置/速度；SuperDex 速度用差分 | `cloth_benchmark verify RECORD`；固定点、应变、障碍表面、自交、原生警告 |
| C3 — PhysX 表面布料 | [physx_cloth](../../src/dexlab/physx_cloth.py) · [worker](../../src/dexlab/physx_cloth_worker.py) · [说明](../../demos/physx-contact/cloth.zh-CN.md) | C2 + `--solver physx-surface --device cuda:0 --iterations 16` | DexLab 专用 SDK worker；复用 UniSim 环境发现；原生表面变形体 | 节点状态读取；外加节点力 API 不支持，拉伸不得替换算法后计为通过 | 复用 C2 评分；CPU 不支持；不等于 UniSim 内置布料后端 |
| R1 — 平面滑动 | [contact_plane_native](../../src/dexlab/contact_plane_native.py) · [case](../../demos/contact-benchmark/cases/dev-slide.json) | `python -m dexlab.contact_plane_native --engine mujoco --case demos/contact-benchmark/cases/dev-slide.json --output OUT` | DexLab 刚体盒/平面；MJ/SD 直接原生，PhysX 经 UniSim worker | 静置后一次初速度、其后无驱动；位姿、速度、力 | 同模块 `--verify RECORD`；减速度、动量、穿透、姿态 |
| R2 — 压入/卸载 | [contact_indent_run](../../src/dexlab/contact_indent_run.py) · [case](../../demos/contact-benchmark/cases/dev-indent.json) | `python -m dexlab.contact_indent_run --engine superdex --case demos/contact-benchmark/cases/dev-indent.json --output OUT` | 同 R1 所有权；刚体接触响应，非软组织形变 | 世界系质心力；实际位移、接触力、卸载后间隙 | 同模块 `--verify RECORD`；受力、穿透、释放 |
| R3 — 双指圆柱载荷 | [contact_pinch_run](../../src/dexlab/contact_pinch_run.py) · [case](../../demos/contact-benchmark/cases/dev-cylinder-overload.json) | `python -m dexlab.contact_pinch_run --engine physx --case demos/contact-benchmark/cases/dev-cylinder-overload.json --output OUT` | 64 边棱柱近似圆柱 + 盒指腹；非 SDF；同 R1 所有权 | 冻结质心力协议；位姿、速度、原生接触点力、参考几何重叠 | 同模块 `--verify RECORD`；保持/超载/无摩擦/释放；SAT 独立几何 |
| R4 — 静态响应与瞬态 | [runner](../../demos/contact-benchmark/normal_response.py) · [static](../../benchmarks/contact-normal-v1.json) · [transient](../../benchmarks/contact-transient-v1.json) | `python demos/contact-benchmark/normal_response.py run OUT --suite benchmarks/contact-normal-v1.json` (or `contact-transient-v1.json`) | 复用 R2；20 kN/m 合成目标；瞬态另声明 40 N·s/m | 分段载荷、质量/步长迁移；压入与响应时序 | `normal_response.py verify RECORD`；退出 0 指全部历史结果可重现，包含失败 |
| P1 — PhysX 静置与滑动基础资格 | [physx_baseline](../../src/dexlab/physx_baseline.py) · [说明](../../demos/physx-contact/README.md) | `python -m dexlab.physx_baseline run --case rest --output OUT` (`slide`, `slide-frictionless`) | DexLab 描述 → UniSim IsaacSimBackend；盒/地面 | 初状态后自由演化；刚体状态、质量惯量/材料回读 | 同模块 `verify RECORD`；基础协议，不能替代抓取 |
| P2 — PhysX 旧盒夹持 | [physx_pinch](../../src/dexlab/physx_pinch.py) · [protocol](../../demos/physx-contact/pinch.zh-CN.md) | `python -m dexlab.physx_pinch run --case hold --output OUT` (`overload`, `frictionless`) | UniSim worker；盒物体、移动关节指腹；不是 R3 圆柱 | 限幅驱动、载荷/摩擦对照；物体运动、支撑 | 同模块 `verify RECORD`；记录原来的失败与适配修复 |
| P3 — PhysX 关节驱动与机器人模型转移 | [drive](../../src/dexlab/physx_drive.py) · [robot](../../src/dexlab/physx_robot.py) · [transfer](../../src/dexlab/robot_transfer.py) | `python -m dexlab.physx_drive run --force-timing substep --output OUT`; `python -m dexlab.physx_robot run --source-run MJ_RECORD --output OUT` | UniSim worker；一维受载驱动 / 54 关节继承模型 | 目标与加载时序；实际关节/连杆状态、原生驱动回读 | 各模块 `verify RECORD`；跟踪、模型/FK 一致性；不是硬件精度 |
| P4 — PhysX SDF 孔洞与接触账本 | [sdf](../../src/dexlab/physx_sdf.py) · [details](../../src/dexlab/physx_contact_details.py) | `python -m dexlab.physx_sdf run --case sdf-hole --output OUT`; `python -m dexlab.physx_contact_details run --output OUT` | UniSim worker；环/球 SDF vs 凸包对照；另有滑块 | 重力/初速度；位姿、法向/切向接触力 | 各模块 `verify RECORD`；孔洞几何、动量账本；不是完整抓取 |
| L1 — 历史 SuperDex 抓取入口 | [wuji_stem_grasp](../../demos/apple-stem-grasp/src/wuji_stem_grasp.py) · [旧评分](../../demos/apple-stem-grasp/src/verify_wuji_sequence.py) | `python demos/apple-stem-grasp/src/wuji_stem_grasp.py --help`；历史复核 / historical scoring: `python demos/apple-stem-grasp/src/verify_wuji_sequence.py demos/apple-stem-grasp/evidence` | 保留的原生 SuperDex 脚本；不冒充 A1 当前 SDF 协议 | 已知状态、IK、手指协同先验；历史轨迹 | 历史验收口径；不并入新协议成功率 |

渲染/视频、`model_audit`、`jitter`、`cloth_report`、归档工具是上述记录的展示或诊断入口，不新增物理任务。几何复核使用已记录的状态，仍受模型、空间采样和时间覆盖限制。[模型审查](../model-audit.zh-CN.md) · [抖动](../jitter.zh-CN.md) · [归档协议](../remote-research.zh-CN.md)。

## UniLab 实际复用到哪里

[注册模块](../../src/dexlab/tasks/__init__.py)声明 5 个任务 ID，均为单场景逐步接口；注册并不统一接触定律。

| ID | 原生路径 / 数据契约 |
|---|---|
| `DexLab-AppleStem-v0` | MJ/SD；实际关节 + 特权苹果位姿 + 时间；绝对关节目标。 |
| `DexLab-Cloth-v0` | MJ/SD/Newton/isaacsim；节点状态与规定节点力；PhysX 外力限制见 C3。 |
| `DexLab-ContactPlane-v0` | MJ/SD/PhysX；空动作 `(1,0)`，初速度后自由运动。 |
| `DexLab-ContactIndent-v0` | MJ/SD/PhysX；世界系质心力，协议约束。 |
| `DexLab-ContactCylinder-v0` | MJ/SD/PhysX；40 维状态、规定 `(1,3,3)` 力；动作必须符合冻结协议。 |

表内 PhysX 是引擎名称；UniLab 的精确 `sim_backend` 键是 `isaacsim`。SuperDex 抓梗的现有法向力列为占位值，不能用于估算法向载荷或摩擦裕量；其他已记录接触量按各自评分协议使用。

这些接口返回占位零奖励，没有训练策略。苹果的 MuJoCo/SuperDex 场景由 DexLab 原生代码持有；PhysX 刚体路径实际经过 UniSim 的场景契约与 worker，布料则只复用运行环境。当前 UniLab 1.3.3 / UniSim 1.7.10；[显式适配补丁](../../scripts/patches/unisim-1.7.10-physx-adapter.patch)不是官方引擎源码修改。是否进一步统一由 [#4](https://github.com/huangkiki/Dexlab/issues/4) 验证，不能仅依据注册成功宣称后端等价。

## 参数来源账本

| 类别 | 当前事实 / 近似 | 依据 |
|---|---|---|
| 实测 | 没有纳入正式硬件标定数据；UR7e 双臂 + 两个相同 CTAG2F90D 是用户确认的硬件型号，不是误差测量。 | [硬件](https://github.com/huangkiki/Dexlab/issues/6) |
| 继承 | OpenArm/Wuji 几何、关节框架、质量惯量来自 prefab；转换一致不等于实物一致。 | [assets](../ASSETS.zh-CN.md) · [model audit](../model-audit.zh-CN.md) |
| 设定 / 几何推导 | 苹果 0.2 kg、刚性梗；R3 半径 10 mm、半高 30 mm、64 边棱柱，最大径向误差约 12.05 µm；均匀质量假设。 | [SDF](../sdf-backends.zh-CN.md) · [contact](../../demos/contact-benchmark/README.md) |
| 调优 / 数值选择 | 默认抓梗 μ：MJ 1.0、SD 0.5、PhysX 1.0；dt：0.5/2/1 ms；SDF 离散、求解器、驱动、对齐偏移各自配置。 | [MJ/SD](../sdf-backends.zh-CN.md) · [PhysX](../../demos/physx-contact/apple.zh-CN.md) |
| 合成目标拟合 | R4 的 20 kN/m 静态目标及 40 N·s/m 瞬态目标为工程设定；2/6 N 拟合、4 N 验证，不是实测材料辨识。 | [normal](../../benchmarks/contact-normal-v1.json) · [transient](../../benchmarks/contact-transient-v1.json) |
| 布料名义参数 | 面积质量、网格、钉扎、厚度/碰撞半径与刚度在 suite/引擎构建器里声明；不同求解器同名 stiffness 不构成同材料。 | [suite](../../benchmarks/cloth-v1.json) · [builders](../../src/dexlab/cloth_engines.py) · [shell](../../src/dexlab/cloth_superdex.py) |
| 未知 / 未覆盖 | 指腹与梗真实摩擦/柔顺、布料拉伸弯曲曲线、执行器带宽、持久材料点滑移、完整能量收支、传感器误差尚无完整数据。 | [methods](../research-focus.zh-CN.md) · [jitter](../jitter.zh-CN.md) |

## 证据覆盖与下一步

以下为已发布历史结果，不是本轮重新运行所有实验。各项分母是不同协议的场景数/开发配置数，不能相加排名。

| 路径 | 已有结果 | 解释与缺口 |
|---|---|---|
| A1/A2 | MJ 1/10，SD 10/10；另 6 次步长开发实验 | [全部失败与区间](../benchmark.zh-CN.md)；100 场景正式测试尚未完成 / 100-scene formal evaluation incomplete |
| A3 | 单个 PhysX 开发场景通过 | [记录](../../demos/physx-contact/apple.zh-CN.md)；没有留出集结果 / no held-out result |
| C1 | 旧协议通过；225 帧中 176 帧桌体相交，最大内部深度 3 mm | [D02](../../demos/cloth-folding/SCORING.zh-CN.md)；非原生穿透距离、非竖直穿透；机器人表面独立复核和帧间覆盖仍缺失 / not native or vertical penetration; robot-surface and interframe coverage remain incomplete |
| C2 | 7 配置 × 15 留出场景：52/105 通过，53 失败 | [记录](../../demos/cloth-benchmark/README.md)；非真实布料误差 / not real-fabric error |
| C3 | 15 留出：10 通过、1 失败、4 不支持；另 9 次细化 8 通过 | [记录](../../demos/physx-contact/cloth.zh-CN.md)；不支持不能当运行失败或成功 / unsupported is distinct from failure or success |
| R1–R3 | 38 开发配置：25 通过、13 失败 | [原始与细化结果](../../demos/contact-benchmark/README.md)；非随机成功率 / not a random success rate |
| R4 | 静态 11/17；瞬态 6/12 同时通过两类检查 | [static](../../demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md) · [transient](../../demos/contact-benchmark/TRANSIENT_RESPONSE.zh-CN.md)；是合成响应目标 / synthetic response targets |

**开发顺序建议：** 在现有 [#32](https://github.com/huangkiki/Dexlab/issues/32) 修复夹布物理与覆盖；[#31](https://github.com/huangkiki/Dexlab/issues/31) 统一指标定义和历史重评；[#33](https://github.com/huangkiki/Dexlab/issues/33) 编写真机采集协议。任务卡借鉴“接触模式 → 控制 → 观测 → 物理检查”的分层；先用最小接触实验隔离误差，再用抓取/操作验证迁移。这里不新增重复任务，也不把上游示例列为已经完成的功能。

没有独立隔离测得的统一速度排名；现有部分时间含记录、IPC 或并发影响。正式速度窗口必须暂停归档、传输和校验。视觉闭环、触觉材料辨识、真实 UR7e/夹爪标定仍未由本报告证明。

[返回首页](../../README.md)
