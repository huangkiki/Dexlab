# DexLab

从豆腐对半切、香蕉连续切片，到机器人抓取：观察接触、摩擦与分离。

<table><tr><th>豆腐对半切</th><th>香蕉连续三刀</th></tr><tr><td><a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html"><img src="docs/evidence/cutting/tofu/surface.gif" width="380" alt="豆腐对半切"></a></td><td><a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html"><img src="docs/evidence/cutting/banana/surface.gif" width="380" alt="香蕉连续三刀"></a></td></tr></table>

**豆腐对半切 · 香蕉三刀切片** — 基于实际保存状态的回放；合成材料参数，未做真实食材标定。

[▶ 表面／粒子对照与完整视频](https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html) · [豆腐实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html)


### 切后还能独立运动吗？

<table><tr><th>BladeMaster</th><th>CRESSim-MPM</th><th>DexLab</th></tr><tr><td><a href="https://jango6324.github.io/assets/blademaster/videos/10-cressim-mpm-comparison-blademaster-30fps.mp4"><img src="https://jango6324.github.io/assets/blademaster/posters/10-cressim-mpm-comparison-blademaster-start.jpg" width="245" alt="BladeMaster reference video"></a><br>作者原站视频</td><td><a href="https://jango6324.github.io/assets/blademaster/videos/10-cressim-mpm-comparison-cressim-mpm-30fps.mp4"><img src="https://jango6324.github.io/assets/blademaster/posters/10-cressim-mpm-comparison-cressim-mpm-start.jpg" width="245" alt="CRESSim-MPM reference video"></a><br>作者原站视频</td><td><a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-comparison.html"><img src="docs/evidence/cutting/tofu-sequential/particles.gif" width="245" alt="DexLab two tofu cuts"></a><br>本项目豆腐两刀 · 动态测量</td></tr></table>

前两列为 BladeMaster 作者的原站对比视频；第三列为 DexLab 豆腐连续两刀实验。三列任务一致；原作完整配置尚待对齐，不作同条件性能排名。 [→ 三列播放与对比协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-comparison.html) · [BladeMaster](https://jango6324.github.io/blademaster/#comparison) · [CRESSim-MPM](https://arxiv.org/abs/2502.18437)

动图逐帧显示切口宽度、中块体积变化与切后位移。[数值定义与论文细节对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-fidelity.html)。



**以经典物理规律与已有经验公式为参照，通过可复现实验，研究接触与摩擦对机器人抓取的影响，评估物理仿真的可信度。**

这项研究服务于两个目标：

| 你面临的问题 | DexLab 提供的答案 |
| --- | --- |
| **场景表现不好，应该改什么？** | 找到偏离物理预期的位置，区分参数、接入、模型假设与求解过程的影响，给出有证据的配置修正和 solver 改进方向。 |
| **面对新场景，怎样选择引擎／solver？** | 根据相近接触与摩擦条件的实验，选择候选配置，了解参数敏感性、适用边界、稳定性和成本，逐步积累场景适配经验。 |

[English](README.en.md) · [中文文档站](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [研究经验](docs/site/zh/experience.md) · [诊断与试参方法](docs/site/zh/diagnosis.md) · [场景选型指南](docs/site/zh/selection.md)

<!-- visual-research:start -->
## 做了哪些实验

| 实验画面／图表 | 比较对象与研究结论 |
| --- | --- |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html"><img src="./docs/evidence/cutting/tofu/surface-poster.png" width="200" alt="豆腐状软块对半切"></a> | **[豆腐状软块对半切](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting.html)**<br>CPU TLMPM / BladeMaster v2 reference<br>撤刀后，切开的两块材料能否独立运动？<br>三个完整切割均分成两块，各占50%质量；负对照保持连接。力值收敛未验证，未做真实豆腐标定。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-comparison.html"><img src="./docs/evidence/cutting/tofu-sequential/surface-poster.png" width="200" alt="豆腐连续两刀与三列对比"></a> | **[豆腐连续两刀与三列对比](https://huangkiki.github.io/Dexlab/zh-cn/latest/cutting-comparison.html)**<br>CPU TLMPM / author reference videos<br>两刀之后，左块能否独立运动？<br>5 mm 网格形成三等份；左块相对移动2.398 mm，动图显示切口、体积与位移。三列任务一致，原作完整参数尚未对齐。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html"><img src="./docs/evidence/cutting/banana/surface-poster.png" width="200" alt="香蕉连续三刀切片"></a> | **[香蕉连续三刀切片](https://huangkiki.github.io/Dexlab/zh-cn/latest/banana-cutting.html)**<br>CPU TLMPM / persistent cut history<br>后续切割会保留之前的切面吗？<br>逐刀分离与完整负对照见实验记录；表面和粒子来自相同状态，未做真实香蕉标定。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/libero-workflow.html"><img src="./docs/evidence/visual/libero-summary.png" width="200" alt="LIBERO 原生抓取：诊断与改进"></a> | **[LIBERO 原生抓取：诊断与改进](https://huangkiki.github.io/Dexlab/zh-cn/latest/libero-workflow.html)**<br>LIBERO / robosuite 1.4.0 / MuJoCo 2.3.7 · Newton / elliptic<br>如何从已有 benchmark 定位问题，再验证修改？<br>发现观测陈旧；步长试验保留成功、失败和退化，不把任务成功当作物理验收。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#normal-response"><img src="./demos/contact-benchmark/media/normal-response-v1.png" width="200" alt="法向与瞬态响应"></a> | **[法向与瞬态响应](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#normal-response)**<br>MuJoCo · SuperDex · historical PhysX<br>压入、卸载与动态响应如何随参数改变？<br>静态校准有效，动态响应和质量迁移须分别验证。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#incline"><img src="./docs/evidence/incline-friction/error-cost.png" width="200" alt="六引擎斜面与摩擦"></a> | **[六引擎斜面与摩擦](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#incline)**<br>MuJoCo · SuperDex · Genesis · Newton Physics · PhysX · Drake<br>静止、滑动和低摩擦有哪些差异？<br>原配置结果与观测有效性分列；全部失败保留。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html"><img src="./docs/evidence/impact-phase/sensitivity.png" width="200" alt="碰撞与接触起始"></a> | **[碰撞与接触起始](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)**<br>MuJoCo · SuperDex<br>步长、刚度及碰撞相位怎样影响瞬态？<br>已有相位与刚度扫描；更小步长不自动消除模型差异。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#pinch"><img src="./docs/evidence/force-limit/replays/dev-cap-0.8/frame-060.png" width="200" alt="夹具夹持、抬升与释放"></a> | **[夹具夹持、抬升与释放](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#pinch)**<br>Genesis · MuJoCo · SuperDex (separate protocols)<br>夹持为什么保持或滑脱？<br>Genesis 0.4 N 与 0.8 N 配置呈现不同保持结果。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html#apple-replays"><img src="./demos/apple-stem-grasp/media/superdex-sdf.png" width="200" alt="苹果抓梗 · SDF 接触"></a> | **[苹果抓梗 · SDF 接触](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html#apple-replays)**<br>MuJoCo · SuperDex · historical PhysX<br>复杂几何下能否连续保持？<br>已有原生连续回放与独立历史验收；不同批次分列。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html"><img src="./docs/evidence/visual/cloth-poster.png" width="200" alt="布料力学与机器人夹布"></a> | **[布料力学与机器人夹布](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)**<br>MuJoCo · SuperDex · Newton Physics · Genesis · historical PhysX<br>柔性形变、接触与保持何时失效？<br>历史柔顺夹布画面；力学、下落与夹布按独立协议记录，保留失败。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#mass-size-transfer"><img src="./docs/evidence/contact-transfer-v1.png" width="200" alt="质量／尺寸迁移"></a> | **[质量／尺寸迁移](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#mass-size-transfer)**<br>MuJoCo · SuperDex<br>固定参数能否迁移到邻近场景？<br>30 条历史迁移记录，联合验收 0/30；失败也是选型依据。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#transient-cost"><img src="./docs/evidence/response-cost-v1.png" width="200" alt="响应误差与计算成本"></a> | **[响应误差与计算成本](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#transient-cost)**<br>MuJoCo · SuperDex<br>更小误差需要什么计算代价？<br>27 条记录区分原生计算、记录和评分成本。 |
| <a href="https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#framework-path"><img src="./docs/evidence/engine-qualification/contact-parameters.png" width="200" alt="原生与框架接入路径"></a> | **[原生与框架接入路径](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#framework-path)**<br>MuJoCo / MJWarp · Newton / Isaac Sim<br>相同核心为何仍可能出现轨迹差异？<br>对齐 CPU 模型后仍有 GPU 字段差异；参数概览图非轨迹证据。 |

**待开展／未完成：** 推动、手内旋转、主动折布及更广抓取迁移分别见现有 Issue。预折叠下落不等于主动折布成功；重复、步长扫描和框架切换不增加任务类型。

## 我们已经知道什么

### 六引擎斜面：相同工况，响应不同

40 mm、64 g 方块；比较静止、滑动及名义零摩擦，三个步长。曲线与回放保留原配置的通过、失败和无效记录。

![六引擎斜面：相同工况，响应不同](docs/evidence/visual/incline-static-0.001.png)

![六引擎斜面：相同工况，响应不同 — curves](docs/evidence/visual/incline-static-0.001-curves.zh.svg)

[同步回放、逐步曲线、参数与原始证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#incline)

### 法向响应：改参数，还是改 solver？

同一 MuJoCo 场景，从约 80 kN/m 到合成目标 20 kN/m。先看加载窗口的压入曲线，再看完整卸载；成功只属于规定的物理检查与条件。

![法向响应：改参数，还是改 solver？](docs/evidence/visual/normal-calibration.png)

![法向响应：改参数，还是改 solver？ — curves](docs/evidence/visual/normal-summary.zh.svg)

[同步回放、逐步曲线、参数与原始证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#normal)

### 夹持：0.4 N 滑脱，0.8 N 保持

同一 Genesis 夹具与物体，只改变指关节驱动力限额。对照完整闭合、抬升、保持和释放，并保留张开负例。

![夹持：0.4 N 滑脱，0.8 N 保持](docs/evidence/force-limit/comparison.gif)

![夹持：0.4 N 滑脱，0.8 N 保持 — curves](docs/evidence/visual/pinch-retention-curves.zh.svg)

[同步回放、逐步曲线、参数与原始证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#pinch)

### LIBERO：原任务、步长对照与观测修正

相同动作、初态、Panda 和成功判定；原版 2 ms 与未通过筛查的 1 ms 对照。全部留出任务成功，物理诊断 5/10 对 3/10，成本约翻倍。观测刷新补丁的策略效果未验证。

![LIBERO：原任务、步长对照与观测修正](docs/evidence/visual/libero-summary.png)

![LIBERO：原任务、步长对照与观测修正 — curves](docs/evidence/visual/libero-demo0-curves.zh.svg)

[同步回放、逐步曲线、参数与原始证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/visual-comparisons.html#libero)

## 比较了哪些引擎与 solver

| 引擎 | 已登记配置的角色（非同级算法清单） | 实验版本与路径 |
| --- | --- | --- |
| **MuJoCo** | 约束求解: CG (nonlinear) · Newton · PGS<br>摩擦锥: elliptic · pyramidal<br>积分配置: Euler · implicitfast<br>角色/身份待核实: SolverMuJoCo; algorithm unqualified | 3.11.0, 3.14.0, 3.15.0; native / 历史路径详见矩阵 |
| **SuperDex** | 柔性实现: experimental-shell<br>外层非线性: BFGS · Newton · SR1<br>线性子求解: ASYNC_CG · AUGMENTED_CG · CG · CUDA_CG · CUDA_GMRES · EXPERIMENTAL_CUDA_SPARSE_CHOLESKY · EXPERIMENTAL_CUDA_SPARSE_LDLT · EXPERIMENTAL_CUDA_SPARSE_LU · GMRES · LDLT · LU · MINRES · PARALLEL_CG<br>线性分支选择: AUTO<br>摩擦正则化/模型: C1_REGULARIZED · CINF_REGULARIZED<br>标签中的精度: FP64 | 1.0.0; native / 历史路径详见矩阵 |
| **Genesis** | 柔性实现: PBD<br>约束求解: CG (nonlinear) · Newton<br>摩擦锥: elliptic · pyramidal<br>接触模型: Signorini · convex<br>耦合路径: rigid coupling<br>积分配置: approximate_implicitfast | 1.4.3; native / 历史路径详见矩阵 |
| **Newton Physics** | 实现/系统: Featherstone · Kamino · SemiImplicit · VBD · VBD compliant · VBD legacy · XPBD<br>柔性实现: ImplicitMPM · Style3D<br>动力学求解后端: DVI · PADMM<br>积分配置: Euler<br>更新/预算选项: 100 sweeps | 1.6.1 / Warp 1.18.0, 1.7.0.dev0 @ 2dee3234; native / 历史路径详见矩阵 |
| **PhysX** | 柔性实现: surface cloth<br>约束求解: PGS · TGS<br>摩擦正则化/模型: patch friction<br>更新/预算选项: external forces every iteration · friction every iteration<br>角色/身份待核实: historical readback incomplete (#126) · pending qualification | 5.9.0; native / 历史路径详见矩阵 |
| **Drake** | 约束求解: SAP<br>接触模型: hydroelastic · point<br>离散接触近似: kLagged · kSap · kSimilar<br>角色/身份待核实: not qualified | 1.57.0; native / 历史路径详见矩阵 |

原生与框架 **MJWarp** 另列运行路径及实际核心。Newton Physics 是引擎项目，Newton 也是求解算法名。SuperDex BFGS／SR1 在已测 assembly period=1 时执行 Newton 等价步；配置名不计作独立算法。

本表是研究对象概览，包含失败与未准入项；执行情况、CPU/GPU、精度、完整配置和不支持原因见 [完整矩阵 / Full matrix](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html)。

角色按各引擎的已记录名称解释，不代表这些算法求解同一问题，也不证明任意组合已经执行。AUTO 只是选择策略；未知身份不从默认值补写。

**比较边界：** 系统配置选型与受控算法归因分开；记录完整性、数值一致性、物理参照和任务结果分别阅读，原始评分与失败分母不变。 [分类与证据说明](docs/solver-taxonomy.zh-CN.md)。

细 SDF 几何与材料响应仍需 [#178](https://github.com/huangkiki/Dexlab/issues/178) 资格核验；布料材料、碰撞/耦合与夹持分别由 [#179](https://github.com/huangkiki/Dexlab/issues/179) 补齐基线。既有开发案例通过不等于公平的跨引擎材料比较。

**MJWarp 运行路径对照（归入 MuJoCo 核心）**

| 运行路径 | 实际物理核心 | solver／接触路径 | 任务验收状态 |
| --- | --- | --- | --- |
| Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / Newton contacts | [not-run](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html) |
| Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / MJWarp contacts | [not-run](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html) |
| Native matched core / vendor Warp1.16.0; original and four-field aligned | MuJoCo 3.11.0 | MJWarp Newton / pyramidal / MJWarp contacts | [not-run](https://huangkiki.github.io/Dexlab/zh-cn/latest/coverage.html) |

已有模型与时钟诊断；可靠任务验收仍按矩阵状态记录。[路径差异 #152](https://github.com/huangkiki/Dexlab/issues/152) 保留独立研究范围。

<!-- visual-research:end -->

MuJoCo 3.16.0 的[隔离资格记录](docs/engine-qualification.zh-CN.md)已核验官方环境、原生兼容性与完整 2 秒布料静置记录；首次采样中面侵入为 0.049681 mm，材料与抓取仍未获资格。完整任务准入由 [#202](https://github.com/huangkiki/Dexlab/issues/202) 单独跟踪，历史结果保留原版本，LIBERO 继续使用其单独准入的 2.3.7 路径。

LIBERO 离线评分器 v2 增加逐接触距离、物体身份与汇总穿透的一致性检查；重新计算本地哈希不能让矛盾记录通过。原始证据与诊断阈值保持不变。[评分修复与回归](https://huangkiki.github.io/Dexlab/zh-cn/latest/libero-workflow.html#scoring-integrity) · [#183](https://github.com/huangkiki/Dexlab/issues/183)

LIBERO 首动作排查定位了状态恢复后的旧 OSC 缓存，新初始化协议显式同步缓存与姿态目标，并记录保留的复位记忆。旧实验仍属原协议；完整受影响任务回归与源历史归因尚未完成，单例原生成功不证明物理准确性。[控制器状态与证据边界](https://huangkiki.github.io/Dexlab/zh-cn/latest/libero-workflow.html) · [#198](https://github.com/huangkiki/Dexlab/issues/198)

## 场景表现不好时如何分析

以“接触表现异常”为例，先声明物理参照与假设，再检查几何、质量／惯量、坐标、控制时刻、有效参数和接触读回。随后固定场景与目标，提出可检验假设，做有限参数试验，用独立评分确认改善及成本。剩余差异再进入接触生成、摩擦表示、约束求解、停止条件、积分和精度的机制研究。

已有 PhysX 案例中，禁碰撞前后初始化质量的顺序导致负例质量错误；修正接入后，其他数值残差仍然存在。参数改善、接入修正、算法研究方向和未解问题分别记录。[完整诊断方法与命令](docs/site/zh/diagnosis.md)

**AI 自动试参是研究方法之一。** AI 利用已有经验提出假设与候选参数；现有执行器、预算账本和独立评分保留所有尝试、失败、有效参数与成本。有限搜索未找到配置时，结论是当前搜索范围尚未成功。新迁移条件事前冻结，历史日志不能充当新留出。

## 新场景如何选择

先描述接触尺度与载荷、粘着／滑动、接触切换、几何及柔顺性，再查找邻近实验。每个候选起点都附版本／路径、参数来源、误差与失败边界，并列出新场景首先要做的验证。

| 新场景的主要困难 | 从哪里开始 |
| --- | --- |
| 法向柔顺、加载卸载或瞬态响应 | [法向／瞬态经验](docs/site/zh/selection.md)；核对合成目标和接触律，验证质量／尺寸迁移。 |
| 支撑、斜面滑动、低摩擦 | [六引擎斜面证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#six-engine-incline)；先确认观测有效，再比较接近目标工况的配置。 |
| 有限指面夹持、抬升与释放 | [夹持与 SDF 起点](docs/site/zh/selection.md)；核对驱动力、惯量、滑移和负例。 |
| 更换框架或导入资产 | [原生／框架对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#framework-path)；比较转换来源、有效参数和时刻。 |

推荐依赖与目标场景相关的证据，兼顾**物理可信度、稳定性和成本**。覆盖更多任务意味着积累了更广的已验证范围；覆盖表本身不决定某个新场景的最佳方案。

## 研究范围与复现

| 已有研究范围 | 证据入口 |
| --- | --- |
| 六引擎基础接触／斜面及适用 solver；碰撞、夹具夹持和机器人抓取 | [完整配置矩阵与各协议状态](docs/site/zh/coverage.md) |
| 布料力学、预折叠下落、机器人夹布 | [历史协议与失败](docs/site/zh/coverage.md)；预折叠下落不等于主动折布成功。 |
| 推动、手内旋转与扩展抓取 | [研究路线](docs/site/zh/dexterity.md)；未运行、受阻和不支持分别标注。 |

矩阵保留引擎核心、solver、运行路径、版本、通过／部分通过／失败／未运行／接入受阻／不支持及证据。重复、步长扫描、更换框架不增加任务类型；不同历史协议不合并计数。新 coverage-v1 可靠覆盖尚未验收，历史能力仍以原协议为界。

[安装与复现](docs/installation.zh-CN.md) · [全部报告](docs/site/zh/results.md) · [原始数据与版本](https://github.com/huangkiki/Dexlab/releases) · [研究与开发看板](https://github.com/users/huangkiki/projects/4)

本轮优先复用证据、补齐诊断案例所需缺口，再向夹持／抓取迁移；六引擎矩阵和 594 回合夹持研究继续保留。**定时开发保持暂停。** [开发与验收约定](docs/autoresearch.zh-CN.md)

[当前工作与暂停状态](docs/current-work.zh-CN.md)

**查阅外部研究：** [参考资料目录](docs/references/README.zh-CN.md) · [Manda Robotics 物理引擎比较中文导读](docs/references/manda-physics-engines.zh-CN.md)。外部结果与 DexLab 实验分别标注。
