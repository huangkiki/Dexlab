# SuperDex 斜面求解器审计：身份、重建与边界

[English](superdex-solver-audit.md) · [历史结果](incline-comparison-results.zh-CN.md) · [审计 #124][issue]

九个历史斜面工况的代码字节与官方 SuperDex 1.0.0 FP64 及 API wheel 一致。在相同字节上重建归档中的求解器设置，原生读回为 **Newton、线性 AUTO、残差范数线搜索、C1 正则化库仑摩擦**。已关联源码将该小型刚体系统的 AUTO 分派到**稠密 LDLᵀ**。这是配置重建和源码路径追踪；旧记录没有逐步线性求解器分支遥测。**#124 的审查结论采纳这条重建边界，永久保留缺失遥测，不再声称已观测历史线性分支。**

本补充不修改轨迹、评分、阈值或历史清单，不把 8/9 结果归因于单一算法，不证明材料等价，也不推广到其他 SuperDex 实验。

## 身份证据链

2026-10-09 核验：九例本地 admission、metadata、trace、geometry 与[公开归档][raw]对应文件逐字节一致，CRC 与逐例哈希通过。归档 runner、fixture 与 campaign 中的哈希一致。历史 admission 保存版本、RECORD 校验及下表代码聚合值；从原安装和官方 wheel 重新计算后，两个包均与全部九例一致。聚合覆盖包内每个 `.py`、`.so` 文件，并逐项检查 RECORD；它与整个 wheel 的文件哈希不同。

| Artifact | SHA256 / identity |
|---|---|
| Published paired archive | `9c0e86425ec03c6d045d5db5a2282310216fa892c7677deb317e9ce306504079` |
| FP64 official wheel, CPython 3.12 Linux x86_64 | `ce300f8a2b30f8043aad238f4c918f981d143256276e34935fa31382a22c02c4` |
| API official wheel, same platform | `46fa446ed0bb86815d6970d14e11f2777bcc7391119c4ebe582ac698e1373377` |
| FP64 aggregate of 7 package code files | `d6e4ac1e9e479a8f7187d19f58e4d3b9566bd2b2754471f3bb6026846d1a0cba` |
| API aggregate of 74 package code files | `3340cfec18d17cd41abb52d10a679d7bd5e09a8bfc7dbe6302d609bedbf5f7e0` |
| `libmochi_physics_double.so` | `a2a0d6e9711d16f1b07641a1192f12df24f6f7f011e864653f1f0fe9176b931d` |
| FP64 ELF Build ID (not a source SHA) | `e7d3ec045b9f43db5c56565509861dc9d2ba32c8` |
| Archived fixture `contact_plane_native.py` | `7e9745ceb0eddb29f88e4259adc8dfed3a7ae1968478498f5a3648d671c2fe07` |
| Archived runner `incline_compare_run.py` | `146d55ef1b2be2ebcc9b70920759bbb365cf3206d59c1cc544dcebdfebc67504` |
| Frozen manifest | `8a3d2f319ab8b3e355d6ed5d562cfa6fc2d22a642172538ad1e65483ef5a7591` |

PyPI 的 [API 发布证明][api-provenance]及 [FP64 发布证明][fp64-provenance]列出上述精确 wheel 哈希与官方 GitHub 发布者。其证书元数据关联到 [API 发布任务][publish-api]和 [FP64 发布任务][publish-fp64]，发布工作流提交均为 `d3101bd914b1a1654b1878fd1732d24d16d6f568`。两份日志都选择[构建任务 32549763602][build]，该成功任务的源码提交为 **`1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`**。发布流程核验构建成功及版本标签，再上传该 wheelhouse。发布工作流提交与编译源码提交是两个不同身份。本次读取了 PyPI 发布证明与 GitHub 记录，没有独立验证 Sigstore 证书链，也没有做原生二进制可复现重建。

下文全部源码链接固定在该构建提交，下载文件与该树的 Git blob ID 已逐项核对。这条链不依赖“当前默认值”或“版本字符串相同”的假设。

## 逐字段证据

H：历史归档直接记录。R：使用相同已验证代码字节及历史 setter 的新读回。S：以历史夹具和拓扑为输入的源码推导。R、S 不冒充历史测量。

| 字段 | 值与证据 | 范围与限制 |
|---|---|---|
| 积分／非线性预算 | H：Backward Euler；最多 100 次；绝对、相对容差 `1e-9` | 积分与终止设置不能代替算法名称 |
| 非线性算法 | R：`NEWTON`；[步进分派][step] → [NewtonSolver 构造及 Solve][solve] → [Newton 与 BFGS/SR1 分支][newton] | 求解非线性残差系统；不宣称精确能量最小化 |
| 线性求解器 | R：`AUTO`；[岛分派][dispatch]在 ≤50 DoF 时选 LDLᵀ，更多时选 CG；[分解实现][linear]在 200 DoF 稀疏阈值以下使用稠密分解 | 归档中一个动态刚性方块与静态平面对应小系统路径；旧数据没有逐步分支／分解遥测 |
| 线性预条件器 | R：场景参数 `PER_ACTOR`；S：AUTO→LDLᵀ 时覆盖为 `None` | 不能把这条直接求解路径称为预条件 CG |
| 非线性细节 | R：残差范数线搜索、alpha 0.5、最多 4 次；PSD 投影 `ALWAYS`；导数装配周期 1；梯度下降回退 false | PSD 投影与拟合接触 Hessian 都影响含义，“Newton”一个词不够 |
| 线性容差 | R：绝对 `1e-9`、相对 `1e-5`、max_iter `-1`（自动）、Eisenstat–Walker 2 | 源码进一步解析自动迭代预算，不代表与 MuJoCo 等量工作 |
| 收敛 | H：21,000 个 `CONVERGED`；R：`PER_ACTOR_WEIGHTED` 判据 | 收敛状态不揭示线性分支，也不证明接触精度 |
| 接触对系数 | H：两 actor 的 μ 同为 0.5，或同为零；S 与同二进制 API 文档：几何平均 `sqrt(μa μb)` | 组合值为 0.5／0；不是接触点原生系数测量，也不是材料标定 |
| 其他接触对参数 | H：penalty `1e9 Pa/m`、平滑半距 `5e-5 m`、阈值 `1e-4 m`、falloff `1e-3 m/s`、粘性／法向阻尼零；[组合规则][combine] | 静态 collider 时 penalty 与 falloff 取 colliding actor；阈值与平滑距取 collider。此处两 actor 值相同 |
| 摩擦正则化 | R：`C1_REGULARIZED`；[接触求值][contact]与[激活函数][smooth] | 低速连续正则化，不是集合值的严格静摩擦约束 |
| 法向与对齐处理 | R：`explicit_normals=false`、`fade_friction=true`、`implicit_normal_force_for_dissipation=false`；默认 actor `max_alignment_normals=0`、沿 collider 法向计算摩擦 | [法向对齐衰减与力求值][alignment]说明，仅给接触对 μ 不足以描述摩擦律 |

原生枚举还暴露 Newton/BFGS/SR1、C1/C∞ 正则化，以及 CG、GMRES、CUDA CG/GMRES、augmented/async/parallel CG、MINRES、LDLᵀ、LU、实验性 CUDA 稀疏 Cholesky/LDLᵀ/LU、AUTO。枚举存在不证明历史批次执行或验收了该变体。这些是 SuperDex 内部算法，Newton 算法不等于 Newton Physics 引擎。

## 接触律与数值含义

[组合函数][combine]对库仑、粘性及法向阻尼系数取几何平均。静态 collider 时 penalty、falloff 取 colliding actor；两个动态 actor 时取几何平均。其他字段初始取 collider，并对非表面积分做量纲修正。本刚性表面对不引入杆或点接触的长度尺度修正。

[法向 penalty][contact]计算在 `x=-d` 处的平滑穿透代理 `P(x)`，牵引力与 `k P(x) P′(x)` 成比例，再经积分和刚体力映射。记录的阈值与半距使过渡区覆盖有符号距离 `1e-4 m` 到 `0 m`。`1e9 Pa/m` 是牵引力律系数，不能当作集中式 `N/m` 弹簧刚度；正间隙也可能激活接触。

对 [C1 摩擦][smooth]，令 `x` 为切向相对位移、`t = falloff_velocity × stage_duration`。力激活量在 `r=x/t<1` 时为 `2r−r²`，在 `r≥1` 时为 1，零相对位移时趋于零。切向力反向于滑移，受 μ、法向力估计和[法向对齐因子][alignment]缩放。重建配置还启用拟合的接触摩擦饱和 Hessian。因此名义库仑系数不意味着严格静止；这些机制也不能单独定量解释每个历史漂移值。

## 读回与剩余工作

[预登记诊断][prereg]只创建一个空场景，**没有调用任何原生物理步进**，没有重跑实验。执行限制为 16/15 GiB、两核配额、128 任务、零 swap、有界数据 I/O、300 s 截止。执行成功：整个启动器 1.007 s，guard 内审计命令 0.546 s，内核记录内存峰值 109,711,360 字节，无 OOM。这是审计成本，不是引擎速度。脚本 SHA256 为 `015c0b889917b61f77a8e59725de178e7751508752456695de78208cfb4e311b`；完整本地输出 SHA256 为 `22c684f975ddb8ff186b8d1f410d750224db94db6a1d54eb01b007b472aee33b`。公开可审查读回转录于下方，原 admission 保留在不可变发布归档中。

```python
# In an installation first verified against both official wheel hashes above.
# Run only inside the documented bounded qualification window.
import os
os.environ["SUPERDEX_PRECISION"] = "fp64"
from superdex import physics as p
p.initialize(num_worker_threads=0)
scene = p.create_scene("solver-identity-readback")
try:
    params = scene.get_solver_params()
    params.integration_method = p.IntegrationMethod.BACKWARD_EULER
    params.non_linear_solver.max_iter = 100
    params.non_linear_solver.abs_tol = 1e-9
    params.non_linear_solver.rel_tol = 1e-9
    scene.set_solver_params(params)
    params = scene.get_solver_params()
    print(params.non_linear_solver.solver_type.name)
    print(params.linear_solver.solver_type.name)
    print(params.experimental_eval.friction_model.name)
finally:
    p.destroy_scene(scene)
```

归档缺少完整求解器参数对象、岛自由度／实际线性分支轨迹、逐接触点组合律原生读回。[SolverStats][stats]仅暴露迭代数、残差与收敛状态，不返回线性分支。已搜寻九例公开记录、保留的准入／轨迹、归档夹具／runner、精确匹配的官方 wheel 及固定构建源码；这些材料均不能提供缺失的同期遥测。

**审查结论（2026-10-09）：** R/S 仅作为同字节重建和有条件源码归因；撤回“历史上已观测 LDLᵀ”以及“8/9 结果隔离证明某算法因果优势”的解释。历史评分、失败和产物保持不变，缺失字段继续缺失。按维护者的覆盖优先计划，#124 的有界证据审计至此完成，不代表恢复了历史执行遥测。

新资格由 [SuperDex #147](https://github.com/huangkiki/Dexlab/issues/147) 与[夹持 #132](https://github.com/huangkiki/Dexlab/issues/132)承接：新正时长批次冻结前保存所有可读有效参数，并逐字段说明不可观测项。新记录具有独立身份，不能回填旧字段。只有发现绑定九例历史批次的同期产物时才重新开启该历史问题；重放或当前默认值相同均不够。

<details>
<summary>完整零时长求解器读回（R）</summary>

```json
{
  "experimental_eval": {
    "consistency_res_norm": false,
    "consistency_res_norm_step": 0.0001,
    "explicit_normals": false,
    "fade_friction": true,
    "fitted_saturation_hessian": {
      "constraint_saturation": true,
      "contact_friction": true,
      "joint_friction": false
    },
    "friction_model": {
      "name": "C1_REGULARIZED",
      "value": 0
    },
    "implicit_normal_force_for_dissipation": false
  },
  "integration_method": {
    "name": "BACKWARD_EULER",
    "value": 0
  },
  "linear_solver": {
    "abort_if_not_spd": false,
    "abs_tol": 1e-09,
    "max_iter": -1,
    "norm_type": {
      "name": "PRECONDITIONED_RESIDUAL_L2",
      "value": 1
    },
    "preconditioner_type": {
      "name": "PER_ACTOR",
      "value": 11
    },
    "rel_div_tol": 10000000000.0,
    "rel_tol": 1e-05,
    "restart_size": 1000,
    "solver_type": {
      "name": "AUTO",
      "value": 13
    },
    "verbosity": {
      "name": "WARNING",
      "value": 2
    }
  },
  "non_linear_solver": {
    "abs_div_tol": 1000000000.0,
    "abs_tol": 1e-09,
    "convergence_mode": {
      "name": "PER_ACTOR_WEIGHTED",
      "value": 1
    },
    "d_residual_assembly_period": 1,
    "explosion_control": true,
    "gradient_descent_fallback": false,
    "line_search_alpha": 0.5,
    "line_search_max_iter": 4,
    "line_search_max_rel_increase": 0.0,
    "line_search_type": {
      "name": "RESIDUAL_NORM",
      "value": 5
    },
    "line_search_wolfe1": 0.0001,
    "line_search_wolfe2": 0.9,
    "linear_tolerance_strategy": {
      "name": "EISENSTAT_WALKER2",
      "value": 2
    },
    "max_elapsed_time_seconds": 0.0,
    "max_iter": 100,
    "psd_proj_mode": {
      "name": "ALWAYS",
      "value": 1
    },
    "rel_div_tol": 10000.0,
    "rel_step_tol": 2.220446049250313e-15,
    "rel_tol": 1e-09,
    "solver_type": {
      "name": "NEWTON",
      "value": 0
    },
    "stop_if_no_improvement": false,
    "verbosity": {
      "name": "WARNING",
      "value": 2
    }
  }
}
```

</details>

## 历史 admission 索引

各行对应发布归档中的 `paired-incline/superdex/<case>/admission.json`。九例均保存上述两个聚合身份；trace、geometry 哈希也已核验。本审计没有重跑或重新评分历史物理批次。

| Case | Historical admission SHA256 |
|---|---|
| frictionless-d0.9-h0.0005 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| frictionless-d0.9-h0.001 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| frictionless-d0.9-h0.002 | `c5a3361a6b86644cee82f39a4359bc1f1f68c030afdc25d61617739a8a236cc3` |
| sliding-d0.9-h0.0005 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| sliding-d0.9-h0.001 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| sliding-d0.9-h0.002 | `574894c6c6ef3c7bfc19a16da636f1e531687dc9e102864c29766410f19c6ff6` |
| static-d0.9-h0.0005 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |
| static-d0.9-h0.001 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |
| static-d0.9-h0.002 | `004aa990a6a22b68b427f43aaefb368e31e740074c6f7d47814afa8191491225` |

[step]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_step.cpp#L483-L503
[solve]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_solve.cpp#L1093-L1150
[dispatch]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_simulation.cpp#L34-L125
[newton]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/src/solvers/newton_solver.cpp#L515-L584
[linear]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/solvers/linear_solver.h#L328-L388
[combine]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.h#L867-L948
[contact]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L498-L788
[alignment]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L1080-L1175
[smooth]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/utils/activations.h#L92-L171
[stats]: https://github.com/facebookresearch/project_superdex/blob/1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6/superdex_physics/libraries/mochi/mochi_physics/include/mochi_physics/cpp_api/mochi_structs.h#L513-L526
[raw]: https://github.com/huangkiki/Dexlab/releases/download/v0.46.0/paired-incline-raw-v1.zip
[issue]: https://github.com/huangkiki/Dexlab/issues/124
[prereg]: https://github.com/huangkiki/Dexlab/issues/124#issuecomment-6073548423
[build]: https://github.com/facebookresearch/project_superdex/actions/runs/32549763602
[publish-api]: https://github.com/facebookresearch/project_superdex/actions/runs/32757591304
[publish-fp64]: https://github.com/facebookresearch/project_superdex/actions/runs/32757336747
[api-provenance]: https://pypi.org/integrity/superdex-physics/1.0.0/superdex_physics-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl/provenance
[fp64-provenance]: https://pypi.org/integrity/superdex-physics-fp64/1.0.0/superdex_physics_fp64-1.0.0-cp312-cp312-manylinux_2_28_x86_64.whl/provenance
