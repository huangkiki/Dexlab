# 按角色理解配置，不把名称排成求解器榜单

[English](solver-taxonomy.md) | [简体中文](solver-taxonomy.zh-CN.md)

比较单位是带版本的**物理核心＋运行路径＋物理模型＋数值配置**，不是一个算法名。首页采用[显式的分引擎展示词表](solver-taxonomy.json)；历史覆盖清单、观测、计数和判定不变。词表解释记录中的名称，不证明未观测到的执行分支。

## 这些名称分别表示什么

| 记录示例 | 角色与边界 |
| --- | --- |
| MuJoCo `PGS`、`CG`、`Newton` | 其约束问题的可选求解方法；此处 CG 是非线性共轭梯度。仍须区分原始／对偶形式与摩擦锥兼容性，同一角色不证明计算工作量或收敛相同。 |
| SuperDex `Newton / GMRES` | 外层非线性方法／内层线性系统方法。记录中的 CG、GMRES、LDLT 等线性选项，不与外层 Newton 同级。AUTO 表示分支选择，不证明实际执行了 LDLT。 |
| SuperDex `BFGS / SR1` | 记录的外层方法选项。已有报告说明，已测 assembly period=1 时执行 Newton 等价步，不能算成另外两个已验证算法。 |
| Genesis `Newton / elliptic / signorini` | 约束方法／摩擦锥／接触模型选项；`PBD / rigid coupling` 是另外的柔性实现与耦合路径。 |
| Newton Physics `Kamino / PADMM`、`Kamino / DVI` | 系统实现／动力学求解后端。XPBD、VBD、Featherstone 标签标识原生实现，具体方程与适用对象须逐路径核查。Style3D、ImplicitMPM 不是通用线性子求解器。 |
| PhysX `PGS / patch friction` | 约束方法／摩擦模型；surface cloth 是柔性路径，不是另一种刚体约束方法。 |
| Drake `SAP / kLagged / hydroelastic` | 约束方法／离散接触近似／接触模型。point、hydroelastic 与 kLagged/kSimilar/kSap 不应展平成独立算法。 |

具体实现证据见冻结报告：[MuJoCo](mujoco-incline-results.zh-CN.md)、[SuperDex](superdex-incline-results.zh-CN.md)、[Genesis](genesis-incline-results.zh-CN.md)、[Newton Physics](newton-incline-results.zh-CN.md)、[PhysX](physx-incline-results.zh-CN.md)、[Drake](drake-contact-paths-results.zh-CN.md)。术语一手参考包括 [MuJoCo 求解器说明](https://mujoco.readthedocs.io/en/stable/computation/index.html#solvers)与 [Kamino 动力学后端说明](https://newton-physics.github.io/newton/1.6.0/api/_generated/newton.solvers.SolverKamino.html)。这些参考不能覆盖历史记录的真实运行时身份。

概览汇集不同配置使用过的名称，**不表示所列选项的任意组合都受支持或已测试**。未知名称保持明确待核实。积分、精度、迭代／更新选项与框架路径分别描述。原生碰撞几何不等于可见网格；同名参数或相同迭代次数不代表同一模型或相同计算预算。

## 分开两种比较目标

**场景选型：** 在明确物理参考、有限开发预算和新的冻结验证条件下比较完整候选配置，报告误差、稳定性、实测成本、全部失败与不可观测项。

**算法归因：** 固定声明的数学／物理问题及相关接口，改变求解方法，并检验竞争解释。几何、接触律、控制器、精度和 solver 一起改变，不能隔离单个算法的贡献。

[SDF 后续 #178](https://github.com/huangkiki/Dexlab/issues/178)负责细特征有效几何及接触响应资格。披露深度／间距与一次细梗抓取成功不证明等价。[布料后续 #179](https://github.com/huangkiki/Dexlab/issues/179)分开材料响应、离散、碰撞／耦合及抓取控制；保留 #32 的限定修复与 #77 的否定证据，不宣称普遍成功或普遍失败。

## 证据按不同维度阅读

分别给出记录完整性、数值一致性、物理参考适用性／误差、任务结果及归因可信度。观测无效不证明任务不可能，任务成功不证明材料准确。历史评分、失败分母与阈值保持不变。新的精度协议须有来源支持的误差论证、事前冻结及新的验证，不能看见失败后只增大 epsilon。

对不可访问或未开源的实现，明确每条说法属于作者描述、公开文档、源码推导、配置值还是运行观测。不编造源码访问、原生读回、许可、隐藏 SDF 网格或历史分支遥测。缺失证据应给具体恢复条件，而不是换成更强的形容词。

## 维护方式

明确新标签角色后，凭来源更新 `docs/solver-taxonomy.json` 的分引擎映射；此前未知标签继续显示。通过 `scripts/build_visual_research.py` 同步生成中英 README 与首页，运行分类专项测试及已有完整适用门禁。展示词表不授予实验资格，也不改变任务覆盖。[当前工作入口](current-work.zh-CN.md)统一维护优先级和暂停状态。
