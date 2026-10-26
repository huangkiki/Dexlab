# 核对 G1 落地接触记录

[English](README.md) | [简体中文](README.zh-CN.md)

检查保存姿态上的几何相交与原生接触力是否对应同一状态、碰撞几何和物理子步。审计保留上游任务评分，不用 CPU 重新求解的力替换 GPU 记录。

公开的首次评测包包含 571 个控制步、2284 个物理子步。DexLab 独立核对了全部 29 个关节及控制边界状态：关节位置完全一致，根部角速度最大差为 2.39e-6 rad/s。作者保存的几何分类在第 119 帧（2.38 s）标记非脚部接触，但记录中的非脚部有受力接触对计数始终为零。这排除了**这份记录**的简单关节错序，尚未确定接触缓存的计算时刻，也未解释差异。公开包缺少原生模型和完整接触对；作者另一次通过的复评仍单独保留。

## 独立复算公开记录

使用 Python 3.12 和已安装的 DexLab/NumPy。将 `OUT` 设为数据盘上的新目录，保留至少 50 GiB 空间。下载入口保存原始 ZIP，核验源端 SHA-256、大小、CRC 及解压路径。共享研究主机上的传输应套用仓库 `research_guard.py` 和 `bounded_run.py` 的 archive 限额。

```bash
python demos/landing-contact/fetch_release.py --output "$OUT"
python -m dexlab.landing_audit "$OUT/evaluation" \
  --protocol demos/landing-contact/protocol.json --output "$OUT/audit.json"
```

预期 JSON 为 `state_alignment.aligned: true`、`upstream_geometric_nonfoot_frames: [119]`、`native_pairs: "unavailable"`、`task_success: null`，并记录输入和协议哈希。`unavailable` 不是零接触。输出拒绝覆盖。该入口复算下载的记录，不执行策略。

## 获取新的原生参考记录

原生资格尚待验证。固定参考栈需要 Linux/NVIDIA、Isaac Lab `46d6cc3`、Newton `71eeba1`、MuJoCo/MuJoCo Warp 3.15.0、Warp 1.17.0+cu12、Torch 2.11.0+cu128。此源端历史组合与 DexLab 3.17.0 提交门禁环境分别保留。按[固定上游准备说明](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/REPRODUCE.zh-CN.md)新建隔离环境，不运行其中的训练命令。代码、机器人资产、动作和权重保留各自来源与许可，DexLab 不重新授予其许可。

`run.py` 核验上游提交、受跟踪源码无改动和发布权重哈希，仅向原资格脚本或评测脚本注入记录器。显式设置单卡 `CUDA_VISIBLE_DEVICES`、`MUJOCO_EGL_DEVICE_ID`，使用新的输出目录。正式运行需套用冻结的 adaptive 资源方案与共享研究锁，并用已有 `MigrationBudget` 账本计入[协议](protocol.json)规定的最多 6 次尝试、累计 3600 秒。

```bash
python demos/landing-contact/init_budget.py "$BUDGET"
"$NATIVE_PYTHON" demos/landing-contact/run.py --upstream "$UPSTREAM" \
  --mode probe --case support-probe --budget "$BUDGET" --output "$PROBE_OUT"
# 仅在静态支撑资格通过后执行：
"$NATIVE_PYTHON" demos/landing-contact/run.py --upstream "$UPSTREAM" \
  --mode evaluate --case policy-repeat-1 --budget "$BUDGET" \
  --checkpoint "$CHECKPOINT" --output "$RUN_OUT"
"$NATIVE_PYTHON" -m dexlab.landing_audit "$RUN_OUT" \
  --protocol demos/landing-contact/protocol.json --geometry --output "$RUN_OUT/audit.json"
```

原生解释器需能导入本工作树的 `src`，例如为审计命令设置 `PYTHONPATH="$DEXLAB/src"`。初始化、失败和超时都消耗尝试。资格脚本包含两次无记录器对照和一次带记录器对照；资格失败则停止依赖的策略试验。完整 321 帧动作与 250 步保持不可裁剪。三个独立进程采用匹配初态，保留全部失败；该失败频率不代表随机初态可靠性。条件干预须在执行前登记唯一变化和配对对照。

记录器保存：

- 每个子步的原格式状态、控制、执行器和力数组，以及 Newton 刷新输入后、MuJoCo Warp 核心步前/步后的状态和原生时钟。
- `get_data_into` 导出的每个接触的局部力、坐标系、带符号距离和约束地址；另存过滤前的全部 Warp 候选接触。接触/约束容量溢出直接报错。
- 原生几何过滤、margin、执行器范围、分别记录的 CPU 模型与实际 GPU 参数、原生状态精度、迭代数和复制函数源码哈希。残差与收敛状态记 unavailable，不从迭代数推断。

`--geometry` 要求记录时的原生版本、模型及接触对。它仅执行 `mj_kinematics` 和 `mj_collision`，对步前/步后相同几何对比较距离，并将接触对缺失与零距离分开。原生时钟对齐本身不能确定碰撞缓存的计算时刻。CPU 接触复制测试不等于 Warp 记录器资格。

## 范围与证据

[Issue #260](https://github.com/huangkiki/Dexlab/issues/260) 继续保留物理资格、重复试验、同步曲线/录像和归因验收。源端 Warp 路径尚未通过资格；其余五引擎及直接 MuJoCo profiles 缺少相同 G1 资产/策略的合格适配器。这不是六引擎比较或生产 UniSim 适配器。

[独立历史记录审计](../../docs/evidence/landing/historical-audit.json) · [源端评测与边界](https://github.com/liudi159/supermimic-backflip-5090/blob/5b313d75e804cdd2ff1ce9bdcfa899a98eca856b/docs/EVALUATION.zh-CN.md) · [原始下载包](https://github.com/liudi159/supermimic-backflip-5090/releases/tag/v14-baseline-9029)
