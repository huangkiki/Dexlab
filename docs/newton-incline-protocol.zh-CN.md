# Newton Physics 斜面协议

[English](newton-incline-protocol.md) | [简体中文](newton-incline-protocol.zh-CN.md)

这是六引擎父项 #121 下 [#149](https://github.com/huangkiki/Dexlab/issues/149) 的初始固定配置批次，不建立共享调优／留出比较、真机标定或可靠 coverage-v1 计数。增加 solver 不增加任务类型。

## 身份与物理模型

2026-10-09 冻结时官方最新稳定版为 Newton **1.6.1**，源码 `713fecdc41caf0c9d726f5c016939f36e66e3dff`；1.7.0rc1 属于预发布。安装的 749 个 Newton Python 文件同时匹配官方 wheel 与 Git 树。Warp **1.18.0** 的 479 个代码文件（含两个原生库）匹配官方 wheel。独立环境使用 Python 3.12.12、NumPy 2.5.3，原生 CPU FP32；未修改引擎，也未经过框架适配器。

保留[原始斜面条件与物理阈值](incline-comparison-protocol.zh-CN.md)：均匀 40 mm、64 g 方块静止，底面贴合无限平面；重力 [0,0,-9.81] m/s²，局部 COM 为零，各向同性惯量 mL²/6。平面与方块绕 +Y 旋转。每配置包含 15° 静态 μ=.5、35° 滑动 μ=.5、15° 名义 μ=0，步长 2/1/.5 ms；每例 2 s，评分 .5–2 s。第十例在 15°/.5/1 ms 禁用方块碰撞，保留两个几何体。无驱动，初始化后不写状态。

形状参数显式设为：密度 1000 kg/m³，ke=2500 N/m、kd=100 N·s/m、kf=1000 N·s/m，黏附／恢复／扭转摩擦／滚动摩擦为零，margin 为零，检测 gap=.01 m。这些是合成数值模型设置，不是识别得到的材料性质。不同 solver 消费字段的方式不同；同名参数不代表接触定律等价。不得根据初次失败调参后替换原记录。

冻结的两个形状取相同摩擦值。[XPBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/xpbd/kernels.py#L2304-L2323) 使用算术均值；[SemiImplicit](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/semi_implicit/kernels_contact.py#L429-L459) 与 Featherstone 共用的接触核同样如此；[VBD](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/rigid_vbd_kernels.py#L995-L1011) 使用几何均值。Kamino 的已归档有效配置选择 `friction_mix_mode="average"`（[源码](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/kamino/config.py#L1146)）。因此，这些组合规则在本次同材质夹具中均保留 .5 和 0；这不表示投影、惩罚、柔顺或摩擦正则化定律等价。

## Solver 与观测范围

| 配置 | 冻结设置 | 原生力观测 |
|---|---|---|
| XPBD | 100 次迭代；默认接触 weighting／relaxation；关闭恢复 | `update_contacts` 将累计冲量转换为 shape0 受力 |
| SemiImplicit | 角阻尼 0，其余原生默认 | `state.body_f` 中真实 COM 力；无公共逐接触力 |
| Featherstone | 角阻尼 0，其余原生默认 | 对步后 `body_f_ext` 的前三维取负；无公共逐接触力 |
| VBD legacy | 100 次迭代，`rigid_compliant_alm=False` | `collect_rigid_contact_forces` 返回 body1 受力 |
| VBD compliant | 100 次迭代，`rigid_compliant_alm=True` | 同一接口，独立接触模型 |
| Kamino PADMM | 显式选择 PADMM，其余已解析原生默认 | `update_contacts` 返回 shape0 受力 |
| Kamino DVI | 显式选择 DVI，其余已解析原生默认 | 同一接口，独立算法 |

逐工况哈希冻结全部有效选项、拓扑与初态。`add_body()` 已创建一个 FREE 关节及 articulation，重复添加是错误。SemiImplicit 的关节分支使用内部临时力缓冲，因此采用独立 `add_link()`，仍保留自由刚体的六维速度状态。Newton 重力数组含工作 world 和额外 global world 两行。

Featherstone 的 `eval_rigid_tau` 会原地将外力取负并移到求解原点，步后线性力必须还原符号。VBD 会修改输入状态：接触几何与输入状态须在步前保存；调用前克隆 `body_q_prev`，首步采用初始输入姿态。最终接触力查询发生在末次 dual 更新之后；力与状态不一致的短诊断单独保留。不能从速度差反推数值，冒充原生测得的接触力。

时钟记录调用者安排的步区间，不声称存在独立原生时钟读回。共同解析评分之前核对状态连续性、接触身份／容量、力约定、几何、参数哈希及有限值。FP32 表示检查采用按量纲大小缩放的固定八倍 epsilon 工程检查，并非针对多次迭代推导的前向误差界；[结果报告](newton-incline-results.zh-CN.md)区分其失败与物理误差结论。包括 **1e-7 N·s 冲量一致性**在内的物理阈值均不变。缺失力通道保持缺失，失败与中断都留在分母。

Style3D 是粒子布料 solver，ImplicitMPM 是颗粒／弹塑性粒子 solver；二者都不是本协议固定自由刚性方块的独立积分器。构造时的配置错误保留为开发失败，不充当上述范围判断的证据。`SolverMuJoCo` 使用 MuJoCo 核心，不能增加 Newton 核心覆盖；兼容封装／转换路径另行对照。

## 预算与复现

冻结七次串行启动、70 回合、最多 161000 次更新，每配置服务上限 1800 s。开发实测峰值约 520 MiB，因此选择最小自适应 8 GiB 档、4 核配额、零 swap，启动另留 8 GiB。六小时／64 次启动的开发包独立于正式夹持预算。记录整服务资源与原生 step 时间，不作跨引擎速度排名。

命令通过仓库的 `bounded_run.py` 与 `research_guard.py` 执行。记录器接受 `--protocol`、`--proof`、`--output` 及可选的 `--admission-only`。解压后可运行 `python -m dexlab.newton_incline_score --input PROFILE --output score.json`，评分不导入物理引擎。不可变产物、失败与成本见[结果报告](newton-incline-results.zh-CN.md)。DVI 在负例中触发原 1800 s 时限；保持原九个正例不变，配合单独冻结的完整负例组成明确归因的续接，两个尝试均归档。

来源：[官方版本](https://github.com/newton-physics/newton/releases/tag/v1.6.1)、[自由刚体构造](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/sim/builder.py#L5104-L5170)、[Featherstone 力转换](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/featherstone/kernels.py#L1377-L1386)、[VBD 力查询](https://github.com/newton-physics/newton/blob/713fecdc41caf0c9d726f5c016939f36e66e3dff/newton/_src/solvers/vbd/solver_vbd.py#L3705-L3855)。

## 可迁移命令

使用结果报告中的不可变归档，官方 `newton==1.6.1`、`warp-lang==1.18.0`、`numpy==2.5.3`、`packaging==25.0`，Python 3.12.12，并将本工作树安装为 editable。资源路径保留在本地：

```bash
python scripts/bounded_run.py --profile adaptive --resource-plan "$NEW_PLAN" \
  --cpu-cores 4 --peak-receipt "$MEASURED_RECEIPT" \
  --data-dir "$DATA_DIR" --io-device "$DATA_DEVICE" --timeout 1800 \
  --receipt "$RESOURCE_RECEIPT" -- \
  python scripts/research_guard.py run --lock "$RESEARCH_LOCK" \
  --kind qualification --receipt "$WINDOW_RECEIPT" -- \
  python -m dexlab.newton_incline --protocol frozen-v1/xpbd.json \
  --proof reports/official-proof.json --output "$NEW_OUTPUT"
```

每个配置使用独立输出和回执。重新完整运行 DVI 时，须按已测成本事前冻结更长时限，原超时仍保留为失败。可在同一包装器内，以独立 600 s 预算执行 `python scripts/resume_newton_incline.py --input campaign-v1/kamino-dvi --output "$NEW_OUTPUT"`，恢复归档中的未完成负例。原生记录器不变；评分修订 2 只增加续接来源核验，原六组完整评分的解析 JSON 完全一致，原中断 campaign 仍不能准入。

无引擎复核使用归档内 `scoring-source` 及 NumPy 2.5.3：`PYTHONPATH=scoring-source python -m dexlab.newton_incline_score --input continuation-v1/kamino-dvi --output score.json`。另六组使用 `campaign-v1/PROFILE`。
