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

新批次分别准入原生最新稳定路径和框架官方兼容组合。核心、绑定、框架版本及其哈希、精度、计算路径分别记录，批次内冻结。较旧的内嵌核心不自动成为阻塞；归因实验另行匹配核心版本，版本不能匹配时不声称差异仅由框架造成。

2026-10-04 已核实发布线索：[MuJoCo 3.14.0](https://github.com/google-deepmind/mujoco/releases/tag/3.14.0)、[Genesis 1.4.3](https://github.com/Genesis-Embodied-AI/genesis-world/releases/tag/v1.4.3)、[Newton 1.6.0](https://github.com/newton-physics/newton/releases/tag/v1.6.0)。仅此带日期的清单不证明任务资格。MuJoCo 3.14.0 已有[结果报告](results.md)所列夹布与摩擦开发证据；更新的原生斜面批次见下文，与这些历史任务分别展示。

已准入的 Newton 1.6.1 包在 `sim` 扩展声明 `mujoco~=3.12.0` 和 `mujoco-warp~=3.12.0`；不能称底层最新；ovphysx 0.6.3 的分发分类为 Alpha。稳定绑定、内嵌核心和独立 SDK 必须分别核查。[版本任务 #41](https://github.com/huangkiki/Dexlab/issues/41)

## Genesis 的范围

先验刚体支撑、滑动、夹持释放，再单独验证 PBD 薄布与耦合；MPM/FEM 体材料分列。Genesis 的 Newton 是算法名，不是 Newton Physics 项目。SDF-SDF 不支持时明确报告，不隐藏凸包替代。[资格任务 #42](https://github.com/huangkiki/Dexlab/issues/42)

## GPU 接触开发证据

MuJoCo Warp 3.14.0 的六卡参数对照得到四组通过、两组失败，固定 5 mm 侵入阈值未改。更小步长未使穿透单调改善。这是合成球—平面诊断，不是抓梗或夹布资格验收。[完整结果、图表与复现记录](https://github.com/huangkiki/Dexlab/blob/main/docs/engine-qualification.zh-CN.md)。


## 合成触觉观测

支持盒体/固定薄层的几何占据图（MuJoCo夹具），非剪切记忆、光学渲染或真机标定。三批结果及未通过对照见[报告](https://github.com/huangkiki/Dexlab/blob/main/docs/synthetic-tactile.zh-CN.md)。

## 双轨准入与 Drake 结果

Drake 1.57.0 的三种 SAP 近似与点/hydroelastic接触已有六配置斜面证据：复用旧6/9，新配置0/9、5/9、0/9、3/9、2/9。五条新增正例超过原动量检查，全部失败保留；旧Lagged滑动合力已由独立源码公式重建至4e-13 N以内。未增加可靠任务覆盖。[协议、结果与复现](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.zh-CN.md) · [残差后续验证 #165](https://github.com/huangkiki/Dexlab/issues/165)。

## 原生斜面批次

[覆盖矩阵](index.md)分别保留初始批次。[Genesis 1.4.3](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.zh-CN.md)记录五组原生 CPU 配置。[Newton 1.6.1 / Warp 1.18.0](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.zh-CN.md)记录七组：XPBD 与 Kamino PADMM 各通过 1/9 正例，DVI 通过 4/9，其余未通过。49 个无效正例、两个无效 VBD 负例及 DVI 中断尝试全部保留；显式续接仅补齐缺失的负例。这些固定配置不计入可靠覆盖 coverage-v1，也不构成等额调优比较或引擎排名。

原生 PhysX SDK 5.9.0 的四组 CPU patch-friction 配置已完成新斜面批次，通过 7/9、7/9、3/9、3/9；13 个数值无效正例保留，四个负例均有效并被拒绝。[完整协议与证据](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.zh-CN.md)。框架兼容核心与转换路径仍由 [#152](https://github.com/huangkiki/Dexlab/issues/152) 单独验证，不能把原生结果归给 Isaac 或历史核心。


已完成MuJoCo/MJWarp3.11.0原生匹配核心对照。原生支撑同样未通过动量检查；对齐四项GPU字段后仍失败，轨迹仍与Isaac Sim不同，三次独立原生重复完全一致。CPU接触读回现已拒绝越界地址，可靠任务覆盖数不变。[结果与归因边界](https://github.com/huangkiki/Dexlab/blob/main/docs/framework-mjwarp-diagnostics.zh-CN.md)。
