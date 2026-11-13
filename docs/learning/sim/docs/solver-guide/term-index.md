# 全部登记术语：角色、章节与原生来源

[教程目录](README.md) · [六引擎配置卡](09-engine-configurations.md) · [版本与证据边界](source-versions.md)

清单冻结于 [DexLab 7e4a077 的角色词表](https://github.com/huangkiki/Dexlab/blob/7e4a0774efb4f8b332e866e1495e032b4969c8aa/docs/solver-taxonomy.json)。共 **63 个按引擎登记的 token**；Newton 的 `semiimplicit` / `semi_implicit` 是同一展示名称的两个别名，合并这个别名后为 62 项。计数是教学覆盖分母，不是独立算法数、已运行配置数或任务覆盖数。

每项链接共同解释与固定版本原生导读；原生导读进一步给出官方源码、字段、限制及历史证据。名称已经解释不表示所有组合都可用或已资格。

## MuJoCo · 7 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `newton` / Newton | 约束求解 | [第 4 单元](04-constraints.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `cg` / CG (nonlinear) | 约束求解 | [第 4 单元](04-constraints.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `pgs` / PGS | 约束求解 | [第 4 单元](04-constraints.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `elliptic` / elliptic | 摩擦锥 | [第 3 单元](03-friction.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `pyramidal` / pyramidal | 摩擦锥 | [第 3 单元](03-friction.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `euler` / Euler | 积分配置 | [第 6 单元](06-time-and-budget.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |
| `implicitfast` / implicitfast | 积分配置 | [第 6 单元](06-time-and-budget.md) | [MuJoCo 导读](https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md) |

## SuperDex · 21 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `newton` / Newton | 外层非线性 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `bfgs` / BFGS | 外层非线性 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `sr1` / SR1 | 外层非线性 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `cg` / CG | 线性子求解 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `gmres` / GMRES | 线性子求解 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `ldlt` / LDLT | 线性子求解 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `lu` / LU | 线性子求解 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `minres` / MINRES | 线性子求解 | [第 5 单元](05-nonlinear-and-linear.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `async_cg` / ASYNC_CG | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `augmented_cg` / AUGMENTED_CG | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `parallel_cg` / PARALLEL_CG | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `cuda_cg` / CUDA_CG | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `cuda_gmres` / CUDA_GMRES | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `experimental_cuda_sparse_cholesky` / EXPERIMENTAL_CUDA_SPARSE_CHOLESKY | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `experimental_cuda_sparse_ldlt` / EXPERIMENTAL_CUDA_SPARSE_LDLT | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `experimental_cuda_sparse_lu` / EXPERIMENTAL_CUDA_SPARSE_LU | 线性子求解 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `auto` / AUTO | 线性分支选择 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `c1_regularized` / C1_REGULARIZED | 摩擦正则化/模型 | [第 3 单元](03-friction.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `cinf_regularized` / CINF_REGULARIZED | 摩擦正则化/模型 | [第 3 单元](03-friction.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `experimental-shell` / experimental-shell | 柔性实现 | [第 7 单元](07-representations.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |
| `fp64` / FP64 | 标签中的精度 | [第 8 单元](08-backends-and-identity.md) | [SuperDex 导读](https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md) |

## Genesis · 9 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `newton` / Newton | 约束求解 | [第 4 单元](04-constraints.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `cg` / CG (nonlinear) | 约束求解 | [第 4 单元](04-constraints.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `pbd` / PBD | 柔性实现 | [第 7 单元](07-representations.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `rigid coupling` / rigid coupling | 耦合路径 | [第 7 单元](07-representations.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `elliptic` / elliptic | 摩擦锥 | [第 3 单元](03-friction.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `pyramidal` / pyramidal | 摩擦锥 | [第 3 单元](03-friction.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `convex` / convex | 接触模型 | [第 2 单元](02-contact.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `signorini` / Signorini | 接触模型 | [第 2 单元](02-contact.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |
| `approximate_implicitfast` / approximate_implicitfast | 积分配置 | [第 6 单元](06-time-and-budget.md) | [Genesis 导读](https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md) |

## Newton Physics · 14 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `xpbd` / XPBD | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `vbd` / VBD | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `vbd legacy` / VBD legacy | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `vbd compliant` / VBD compliant | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `semiimplicit` / SemiImplicit | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `semi_implicit` / SemiImplicit | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `featherstone` / Featherstone | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `kamino` / Kamino | 实现/系统 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `style3d` / Style3D | 柔性实现 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `implicitmpm` / ImplicitMPM | 柔性实现 | [第 7 单元](07-representations.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `padmm` / PADMM | 动力学求解后端 | [第 8 单元](08-backends-and-identity.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `dvi` / DVI | 动力学求解后端 | [第 8 单元](08-backends-and-identity.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `euler` / Euler | 积分配置 | [第 6 单元](06-time-and-budget.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |
| `100 sweeps` / 100 sweeps | 更新/预算选项 | [第 6 单元](06-time-and-budget.md) | [Newton Physics 导读](https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md) |

## PhysX · 6 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `pgs` / PGS | 约束求解 | [第 4 单元](04-constraints.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |
| `tgs` / TGS | 约束求解 | [第 4 单元](04-constraints.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |
| `surface cloth` / surface cloth | 柔性实现 | [第 7 单元](07-representations.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |
| `patch friction` / patch friction | 摩擦正则化/模型 | [第 3 单元](03-friction.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |
| `external forces every iteration` / external forces every iteration | 更新/预算选项 | [第 6 单元](06-time-and-budget.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |
| `friction every iteration` / friction every iteration | 更新/预算选项 | [第 6 单元](06-time-and-budget.md) | [PhysX 导读](https://github.com/huangkiki/physx-learning/blob/c9effd1ecfd5ff6d6ad12c5f65318574a6940803/docs/solver-reading-guide.md) |

## Drake · 6 个 token

| 登记 token / 展示名称 | 角色 | 共同解释 | 固定原生来源与限制 |
|---|---|---|---|
| `sap` / SAP | 约束求解 | [第 4 单元](04-constraints.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |
| `klagged` / kLagged | 离散接触近似 | [第 9 单元](09-engine-configurations.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |
| `ksap` / kSap | 离散接触近似 | [第 9 单元](09-engine-configurations.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |
| `ksimilar` / kSimilar | 离散接触近似 | [第 9 单元](09-engine-configurations.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |
| `hydroelastic` / hydroelastic | 接触模型 | [第 2 单元](02-contact.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |
| `point` / point | 接触模型 | [第 2 单元](02-contact.md) | [Drake 导读](https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md) |

## 表格中的五项身份与资格说明

以下状态或包装名称来自冻结首页及用户提供的表，不伪装成已确认的算法角色。

| 名称 | 所属记录 | 解释入口与保留边界 |
|---|---|---|
| SolverMuJoCo | MuJoCo 相关包装/后端路径 | [后端与身份](08-backends-and-identity.md)：实际 core、路径和算法继续核对 |
| algorithm unqualified | MuJoCo 相关记录 | [版本与证据](source-versions.md)：未满足对应算法资格，不是算法名称 |
| historical readback incomplete (#126) | PhysX 历史路径 | [PhysX 配置卡](09-engine-configurations.md)：保留缺失，当前默认值不能补历史观测 |
| pending qualification | PhysX 记录 | [后端与身份](08-backends-and-identity.md)：资格依任务、配置、路径和协议确定 |
| not qualified | Drake 记录 | [六引擎解读](09-engine-configurations.md)：已有运行/失败与完整覆盖资格分别解释 |

## English summary

All 63 engine-specific tokens in the frozen vocabulary have a role, shared lesson and pinned native guide. One Newton alias yields 62 distinct per-engine display entries. Five additional identity/qualification labels are explained separately. These counts describe educational coverage, not executed algorithms, valid combinations or physical task qualification.
