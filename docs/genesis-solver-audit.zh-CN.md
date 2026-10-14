# Genesis 力限额求解器审计：已记录选择与默认值解析

[English](genesis-solver-audit.md) · [历史结果](force-limit-results.zh-CN.md) · [审计 #125][issue]

16 例归档保存了 **Newton（`constraint_solver=1`）、`approximate_implicitfast`（`integrator=2`）、elliptic 摩擦锥和零次 noslip 迭代**。名称来自与历史 wheel 匹配的官方源码，不是当前版本默认值。归档保存的是调用者的选项对象，**没有完整保存求解器解析后的设置**；[#125][issue] 的审查结论保留缺失原生读回，采纳下表明确标注的匹配源码推导。

## 身份与证据范围

2026-10-07 的[官方 wheel 证明](evidence/force-limit/official-proof.json)记录 `genesis-world==1.4.3`，wheel SHA256 为 `26a8229031d66535a568fbdd15b9dcf506843fb91b739a6d4ec7a4a015bf5eb8`。2026-10-09 只读审计核验了缓存 wheel 与全部 **264** 个 Python 源码哈希；各文件 Git blob 均匹配官方 [v1.4.3 源码提交](https://github.com/Genesis-Embodied-AI/genesis-world/tree/216a708e06124595521a9d36a51fae5393fd4ff8) `216a708e06124595521a9d36a51fae5393fd4ff8`。保留的安装目录目前仍匹配这些文件；这项当前检查与历史证明分开记录。

[产物清单](evidence/force-limit/artifact-hashes.json)全部 **126** 项 SHA256 通过。16 个独立工况各含 8,000 步，共 **128,000** 个样本，归档 `initial.options` 完全一致。各例 runner 和挑战清单均匹配[冻结哈希](evidence/force-limit/frozen.json)：

| 产物 | SHA256 |
|---|---|
| 历史 runner `genesis_pinch_probe.py` | `e195c50b5fb03a38c5e29914655d491f47f106cc3330225645c45f2def23528f` |
| 独立评分器 `genesis_pinch_score.py` | `988ec53e28d2ed4bae9249dba95ae6ff45ea8d5e98657abaebe475d0b4a3fb85` |
| 挑战清单 `force-limit-v1.json` | `2ed2d8d1c608d16aaacf052d92777b55398dca1cef7e71df361f7e4e70d14e76` |

[逐例协议](evidence/force-limit/cases/)与[包版本清单](evidence/force-limit/installed-packages.json)记录 Genesis 1.4.3、Quadrants 1.3.3、Torch 2.9.1+cpu。Quadrants 是内核编译依赖，不是另一物理引擎。证据支持包与源码身份，不包含可复现编译或全部历史 JIT 机器码哈希。

## 历史记录与源码解析分列

**H** 表示历史记录中的值，也包括调用者配置；**S** 表示由匹配源码与冻结调用者／场景推导的结论。H 不自动等于原生读回，S 与未来重建也不能填成历史字段。

| 字段 | H：归档值 | S：匹配源码解释 |
|---|---|---|
| 刚体求解器 | `constraint_solver=1` | [Newton][enums]；冻结 runner 没有显式覆盖求解器 |
| 积分器 | `integrator=2` | [`approximate_implicitfast`][enums]，区别于 `implicitfast=1`；[近似说明][options] |
| 摩擦／noslip | `friction_cone=1`、`noslip_iterations=0` | Elliptic；关闭附加 noslip 阶段，摩擦仍存在 |
| 后端／精度／时钟 | CPU、FP64、种子 0；dt 0.0005 s；8,000 步 | 冻结 runner 请求确定性算法；SimOptions 使用一个子步；不宣称普遍确定性 |
| 迭代预算 | 求解器 25；线搜索 50、容差 0.01 | [允许提前退出][body]；这是上限，不是实测迭代数 |
| 求解器容差 | `null` | [FP64 解析][tolerance]在关闭 MuJoCo 兼容时得到 1e-9；[缩放后的收敛规则][exit]，不是绝对力阈值 |
| 接触解析方式 | `null`；elliptic、Newton、MuJoCo 兼容为 false | [解析分支][resolve]选择 Signorini：法向行与摩擦盘分开，摩擦盘依据生成的法向力更新 |
| 切向／法向阻抗比 | `impratio=null` | 此配置的[解析值][resolve]为 100 |
| 稀疏表示／执行体 | `sparse_solve=null`；CPU；三自由度夹具与自由方块 | [拓扑及 CPU 规则][static]选择稀疏表示与 monolithic 执行体；Newton Cholesky 路径，不是 CG；无逐步分解遥测 |
| 附加接触模式 | 扭转／滚动摩擦 false；休眠 false | 这些可选项关闭 |
| 几何材料数据 | 原生几何摩擦读回均为 0.5；平面／方块时间常数 0.002 s；关节 0.01 s | 接触组合值遵循下述源码规则，没有单独保存读回 |

为什么缺少解析值？runner 保存传入 Scene 的 `options.model_dump(...)`。[SceneOptions][copy]按[字段复制规则][copy-fields]创建副本，并从 SimOptions 继承未设置的共享字段；求解器随后解析自己的副本。因此归档中的 `null` 容差、接触解析方式、阻抗比与稀疏字段，不代表零值或运行时没有完成解析。缺失的仍是**原生读回**；S 列只描述条件确定后的源码路径。

## 接触规则与力的时刻语义

匹配源码的[接触组合函数][pair]使用 `max(mu_a * ratio_a, mu_b * ratio_b, 0.01)`，平均两几何的求解参数，并把组合时间常数下限设为两倍物理子步。因此未来的名义零摩擦对照不能假定有效系数为零。Elliptic 只说明锥形状，不能独自指定法向与摩擦耦合；这里的 Signorini 解析和阻抗比影响解释。名义 μ 相同不证明与 MuJoCo 或 SuperDex 材料等价。

每条归档记录在 `scene.step()` 后采集，时间标为 `(step+1)*dt`。[接触收尾][forces]先计算逐接触力并累加链节净力，[后处理][post]再积分状态。[读取接口][api]返回保存的接触求解量和当前状态。因此：

- 位姿和速度属于步末；接触力属于产生该步更新的求解，不是对步末位姿重新求解的力。
- 接触位置、法向、穿透来自该次积分前的碰撞／求解几何；评分器的解析桌面深度使用步末位姿，两者时刻不同。
- 力账用 **1e-8 N** 检查作用于方块的逐接触力总和与原生净接触力。这验证账目一致性，不是独立物理真值。
- 动量检查用该步接触力和重力对应 `m * (v_after - v_before)`，首步使用记录的初始速度。**5% 重力冲量**阈值与求解器容差、力账阈值分别定义。

历史控制器为 Genesis 原生位置驱动，记录了增益和力限额，**没有原生执行器输出的时间序列**。位置目标、力限额、接触力与执行器力不能互相替代。新的外部 PD 执行器资格由[协议 #131](https://github.com/huangkiki/Dexlab/issues/131)之后的 [#132](https://github.com/huangkiki/Dexlab/issues/132)承接，历史抓取成功不能代替该资格。

## 保留限制与审查结论

[#125][issue]保留缺失的同期**已解析求解器选项／静态配置快照**，具体为接触解析方式、有效容差、阻抗比、稀疏选择，以及逐接触组合参数。历史文件相应字段为 `null` 或未暴露。这限制运行时归因，不影响已恢复的 Newton／积分器名称。实际迭代数及 JIT／分解过程遥测也未保存，本报告不作相应声明。

**审查结论（2026-10-09）：** 已搜索全部 126 项清单、16 例完整记录、冻结 runner／选项和 264 份匹配官方源码，未恢复缺失原生快照。S 列仅作为有条件源码推导；撤回把它视为历史有效参数、实际迭代数或执行器输出测量的解释。按维护者覆盖优先计划，#125 有界审计至此完成。原始记录、阈值及六例保持失败均不变。

[Genesis #148](https://github.com/huangkiki/Dexlab/issues/148)与[夹持 #132](https://github.com/huangkiki/Dexlab/issues/132)承接有效参数／时刻记录要求。单独记录的[迁移 #143](unisim-contact-migration.zh-CN.md)验证新执行路径，不能修复旧观测。只有发现绑定这 16 例身份的同期新产物时才重新开启该历史问题。

本审计没有导入 Genesis、调用物理步进、重新评分或修改原始数据、阈值、成功与六个抓取失败。受限的只读源码／归档检查启动器墙时 5.074 s，内核内存峰值 306,806,784 字节，无 OOM；这是审计开销，不是物理吞吐量。没有消耗新批次的 6 小时／700 次启动额度。

## 历史记录身份索引

下表 SHA256 对**解压后的原始 JSON 字节**计算，先于解析；压缩文件与其他产物由原始清单覆盖。每行均为 8,000 样本，H 选项一致。

| 工况 | 解压记录 SHA256 |
|---|---|
| `dev-cap-0.2` | `76f97458f57ba6c0785c70f8049563281cd58da772e6a93655f41a6cb91185f9` |
| `dev-cap-0.4` | `d0a077422df494bed68451388cb15718a0bc708cefa3a11374992295b928aab1` |
| `dev-cap-0.8` | `0c1fde9432a08942aa4ecbc1f3782e66a160f676b166c0e7023327418b8c4cf6` |
| `dev-cap-10` | `e5daf2c2abfab350711f6e8112a9e5f2e5d5a292ae3291273408ab768d44654c` |
| `dev-open` | `91353c980501857672fdcda4166f408df578de253ceffe2a3ef390a37e67f8dc` |
| `dev-repeat-10` | `94d2c54b0b2f98761c27d1832e38bc10ceccfc7b3ed90129d50a02bb52299981` |
| `eval-left-cap-0.2` | `d65d7c0324168153eb340f8436f475e9ce9fe6bf9902ac5102da1371cd0aa43b` |
| `eval-left-cap-0.4` | `d151fbb916e70734cab3f6b41361b8d122a6d08fe975875c3d44c0be2d54c50f` |
| `eval-left-cap-0.8` | `2253aeeeb02df68ea4a620cad700c075b041539d6e6790382732bdee7e3ad9b5` |
| `eval-left-cap-10` | `81c82fba9040338c67a3fa9b08bfc46c81fa1ccda605a564e4b1757691a16f2b` |
| `eval-left-open` | `064a27c39d4d5a6bcaa926e57dc33c484706e72b2d1a98884e495717bbaede86` |
| `eval-right-cap-0.2` | `a4fb9e9c8d9feecb45d4a8a0fee974cf5e85e14289e5fe4d398859ae42ab67c4` |
| `eval-right-cap-0.4` | `a0774bfbb0f7e995b0a8a83aa86bdfaf23a2eb3f9ddfe3f81526ab05fe48c2fd` |
| `eval-right-cap-0.8` | `6f013782e43c68fea2684415f5fb214919ec08b1c03f6acff251e88ea5c5e6a0` |
| `eval-right-cap-10` | `17e060d31dbe9f2c27324ae551a4f57e405f7a2728929956d748eccdfc88fdf8` |
| `eval-right-open` | `9e3e545574f6ade152e45dbc2b8c882be5fd74f44af6964d94dd866cb4f37803` |

[enums]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/constants.py#L61-L112
[options]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/solvers.py#L445-L646
[copy]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/scene.py#L63-L88
[copy-fields]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/options/options.py#L112-L127
[resolve]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L263-L298
[tolerance]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L334-L341
[static]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L477-L625
[body]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5592-L5662
[exit]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/linesearch.py#L567-L615
[pair]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/collider/contact.py#L433-L463
[forces]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/constraint/solver.py#L5668-L5764
[post]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/solvers/rigid/rigid_solver.py#L3662-L3684
[api]: https://github.com/Genesis-Embodied-AI/genesis-world/blob/216a708e06124595521a9d36a51fae5393fd4ff8/genesis/engine/entities/rigid_entity/rigid_entity.py#L3162-L3264
[issue]: https://github.com/huangkiki/Dexlab/issues/125
