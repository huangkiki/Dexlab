# 引擎、求解器与建模假设

同一个视觉网格、参数名称或关节目标，不保证引擎求解了同一个物理问题。

## 历史苹果配置的差别

| 项目 | MuJoCo | SuperDex FP64 | PhysX |
|---|---|---|---|
| 接触路径 | SDF 接触搜索与软约束 | 表面采样积分与平滑罚能 | 原生 SDF 接触与 TGS |
| 物理步长 | 0.5 ms | 2 ms | 1 ms |
| 关键近似 | SDF 离散化与接触点搜索 | 表面采样密度与平滑罚响应 | SDF 分辨率、接触离散与扭转半径 |
| 证据边界 | 默认场景与历史 10 场景分别报告 | 默认场景与历史 10 场景分别报告 | 单个开发抓取，不在上述留出集 |

碰撞表示、接触律、积分器、约束求解器与驱动应分别记录。SDF 描述几何，不能单凭“SDF”推断摩擦响应或穿透水平；较小步长也不自动意味着误差单调变小。

[参数来源与底层差别](https://github.com/huangkiki/Dexlab/blob/main/docs/sdf-backends.zh-CN.md) · [接触与材料研究](https://github.com/huangkiki/Dexlab/blob/main/docs/research-focus.zh-CN.md)

## 最新稳定版准入

新批次冻结当日核查官方最新稳定核心、solver、绑定与封装；记录实际加载版本、哈希、精度和计算路径。轮内不升级。alpha/beta/RC/dev、撤回包与实验性 solver 选项不进入主比较。不兼容的组合明确阻塞，不静默退回旧版本。

2026-10-04 已核实发布线索：[MuJoCo 3.14.0](https://github.com/google-deepmind/mujoco/releases/tag/3.14.0)、[Genesis 1.4.3](https://github.com/Genesis-Embodied-AI/genesis-world/releases/tag/v1.4.3)、[Newton 1.6.0](https://github.com/newton-physics/newton/releases/tag/v1.6.0)。仅此带日期的清单不证明任务资格。MuJoCo 3.14.0 已有[结果报告](results.md)所列夹布与摩擦开发证据；Genesis 和 Newton 仍需分别验收。

Newton 的 MuJoCo 扩展仍限制 3.12.x，不能称底层最新；ovphysx 0.6.3 的分发分类为 Alpha。稳定绑定、内嵌核心和独立 SDK 必须分别核查。[版本任务 #41](https://github.com/huangkiki/Dexlab/issues/41)

## Genesis 的范围

先验刚体支撑、滑动、夹持释放，再单独验证 PBD 薄布与耦合；MPM/FEM 体材料分列。Genesis 的 Newton 是算法名，不是 Newton Physics 项目。SDF-SDF 不支持时明确报告，不隐藏凸包替代。[资格任务 #42](https://github.com/huangkiki/Dexlab/issues/42)

## GPU 接触开发证据

MuJoCo Warp 3.14.0 的六卡参数对照得到四组通过、两组失败，固定 5 mm 侵入阈值未改。更小步长未使穿透单调改善。这是合成球—平面诊断，不是抓梗或夹布资格验收。[完整结果、图表与复现记录](https://github.com/huangkiki/Dexlab/blob/main/docs/engine-qualification.zh-CN.md)。
