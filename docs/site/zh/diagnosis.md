# 从异常到改进方向

研究入口是一个明确的物理问题。例如“方块穿透偏大”需要说明接触尺度、载荷、几何、柔顺性和可接受误差；“夹持失败”需要看承载、滑移和释放全过程。仅凭画面或一次运行无法区分参数、接入和求解机制。

## 一条可复用的诊断顺序

1. **确定物理预期。** 静态支撑检查力与力矩平衡；粘着检查 `|f| ≤ μₛN`；在刚体、恒定库仑摩擦、持续接触且不旋转等假设下，斜面滑动参照为 `a=g(sinθ−μₖcosθ)`。碰撞另需声明恢复系数、外冲量与转动。复杂多点接触不假定唯一解析解；经验公式注明来源、单位、条件和不确定度。
2. **确认观测可信。** 核对几何、质量／惯量、坐标、控制时刻、原生有效参数、接触容量和读回地址。保存源资产、中间模型及转换来源。缺少读回就是缺少证据，不能填默认值或零。
3. **进行受控参数实验。** 固定场景、目标、评分和预算，从已有经验选候选，记录假设、预期变化及来源。AI 提出下一项试验；执行器保留完整尝试，独立评分判断物理约束是否同时通过。额外迭代、步数和观测开销进入成本。
4. **定位剩余差异。** 用原生读回、源码及消融证据研究接触生成、摩擦表示、约束求解、停止条件、积分和精度。有限搜索失败只说明已试范围尚未成功。

## 三个已有案例

| 异常与参照 | 已验证改变 | 仍解释不了什么 |
| --- | --- | --- |
| 合成法向响应偏硬，参照冻结的 20 kN/m 目标 | MuJoCo 参数校准改善固定质量的响应；预声明质量转换改善两档质量验证。 | 不能推广为任意接触几何或真实材料精度。[经验与原记录](normal-response) |
| PhysX 禁碰撞负例质量不符，参照模型质量／惯量 | 在禁碰撞前调用质量／惯量初始化，修正接入顺序。 | 原生 TGS 的状态／冲量残差仍需 #163 的独立归因。[案例](physx-observation) |
| 原生／框架轨迹不同，参照相同物理输入与时间 | 对齐四项 GPU 字段；修正 CPU 接触越界读回，将不可观测标为缺失。 | 支撑轨迹差异仍在；没有唯一框架根因。[案例](framework-path) |

输出明确分成：**已验证的配置改善、已定位的接入修正、有证据的算法改进方向、未解决问题**。本轮自动修改范围为参数及有依据的接入修正；solver 源码改进先交付研究依据。

## 落地几何与原生接触力的核对

<p><img src="_static/landing/replays/policy-repeat-1/preview.gif" width="768" alt="G1 原生几何完整原速回放与记录的力曲线"></p>

全部 572 个状态边界按原始 50 Hz 播放 11.44 秒，包括末端点。画面使用保存姿态和原生模型几何，每只脚为四个半径 5 mm 的接触球，不重新积分。<a href="_static/landing/replays/policy-repeat-1/replay.mp4">完整视频 1</a> · <a href="_static/landing/replays/policy-repeat-2/replay.mp4">视频 2</a> · <a href="_static/landing/replays/policy-repeat-3/replay.mp4">视频 3</a> · <a href="_static/landing/replays/policy-repeat-1/curves.svg">力曲线</a>。

<video controls muted playsinline preload="metadata" poster="_static/landing/replays/policy-repeat-1/frame-0000.png" aria-label="G1 第一次完整复跑及同步原生接触力曲线"><source src="_static/landing/replays/policy-repeat-1/replay.mp4" type="video/mp4"></video>

<a href="_static/landing/native-v1.zip">完整记录与模型（17.75 MB ZIP）</a> · <a href="_static/landing/native-summary.json">批次报告</a> · <a href="_static/landing/native-bundle.json">归档验收</a> · <a href="_static/landing/asset-lineage.json">资产来源</a>。解压后核验全部 99 个清单条目，三份独立几何审计均精确复现。上游固定 URDF 与固定官方 Unitree 文件不同，仿真设置不代表已核实的硬件限值。归档保留原始许可和评测参考样本，不含权重及原始动作 NPZ。

[G1 落地审计](https://github.com/huangkiki/Dexlab/blob/main/demos/landing-contact/README.zh-CN.md)已在 RTX 4090 上通过固定参考栈资格：原始支撑检查与三次独立进程策略复跑均通过。每次包含 571 个控制步、2284 个物理子步及末尾 5 秒保持；末尾两秒漂移为 1.21–1.42 mm，独立步前／步后几何重建均未发现非脚部穿透或承载。

新记录还显示了时序差异：共享相同接触对集合的 6,428 个子步中，6,427 个的记录距离更接近步前几何。步前误差低于 2.38e-7 m，步后误差达到 0.0202 m。这些是三份相同种子记录中的相关子步，不是独立可靠性试验。

历史公开记录仍单独保留：29 个关节的位置完全对齐，但第 119 帧标记了几何上的非脚部接触，记录中却没有相应承载接触对。该包缺少原始模型和完整接触流；新批次没有复现此差异，不能确定其原因。保留作者首次失败及另一次通过的复评，缺失信号不当作零值。未修改的上游环境有 7 项依赖声明冲突，转换及本轮原生路径实际运行成功，其他包的调用路径仍未验证。

每次记录中有 74 个关节力样本恰好达到声明的 CPU 模型限值，没有超出。GPU 限幅分支、求解收敛残差／状态及整机质心动量仍不可观测；达到限值或任务通过都不能证明这些字段。

## AI 受控试参入口

第一条接入现有流程的路径是原生 MuJoCo／SuperDex 的 `normal-load` 开发实验。它复用 `contact_indent_run`、独立 `--verify` 和 `MigrationBudget`；不新增模型服务或调度器。PhysX 原生斜面、框架和夹持仍使用各自现有冻结协议与执行入口，不能用此入口假装完成了那些任务的参数准入。

`benchmarks/contact-trials-example-v1.json` 复用历史初始／校准配置，演示记录流程。它是已知结果的开发示例，不是新算法发现或未见留出。清单显式冻结运行版本 profile 和完整场景、全部候选参数、假设、预期效果、物理参照、证据 SHA-256、原评分和工作包。AI 在执行前填写这些内容，依据结果提出下一包；改变代码或候选需新清单并继承旧账本。

在已准入的环境、仓库根目录中，设置 `OUT`、`DATA_DIR`、`IO_DEVICE` 为自己的新输出目录、数据盘和块设备：

```bash
python -m dexlab.contact_trials init benchmarks/contact-trials-example-v1.json "$OUT"
python scripts/bounded_run.py --profile adaptive --cpu-cores 4 \
  --resource-plan "$OUT/resource-plan.json" --data-dir "$DATA_DIR" \
  --io-device "$IO_DEVICE" --timeout 900 --receipt "$OUT/resources-initial.json" -- \
  python scripts/research_guard.py run --lock "$DATA_DIR/research.lock" \
    --kind qualification --receipt "$OUT/window-initial.json" -- \
    python -m dexlab.contact_trials run "$OUT" initial-mujoco --timeout 840
python -m dexlab.contact_trials status "$OUT"
```

每个候选使用新的资源／窗口收据；批内复用冻结资源计划。再执行 `validation-mujoco-reference` 时使用同一个账本。命令返回 1 可以表示物理失败，必须检查 `attempts/*/result.json`，不能当作基础设施错误无限重试。

结果保存提出／解析／有效参数及差异、完整运行日志、独立评分、原生步进与观测成本、文件哈希和终态。进程超时仍保留尝试；遇到强杀后先确认记录的进程已结束，再运行 `python -m dexlab.contact_trials recover "$OUT"`。恢复按整个预留时长计费，不重置预算。成功记录的物理失败禁止重试；基础设施失败最多一次带理由恢复，仍受原预算约束。原有账本继承字段 `prior_budget` 与新证据工作包规则保持不变。

该开发入口不能替代留出。新的迁移或引擎比较必须事前冻结独立条件、相同调优预算、负例和验收协议；不要用已经看过的质量／尺寸记录调参后再称它们为未见验证。

## 本轮按证据缺口推进

优先复用 PhysX 旧轨迹做 [FP32 离线诊断](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.zh-CN.md)。[#163](https://github.com/huangkiki/Dexlab/issues/163) 继续负责精度归因和新协议留出；[#152](https://github.com/huangkiki/Dexlab/issues/152) 负责剩余状态／接触路径差异；[#145](https://github.com/huangkiki/Dexlab/issues/145) 负责惯量与坐标语义。已有固定模型实验不依赖惯量随机化准入。

六引擎、594 回合夹持及后续任务继续保留。资源限制不变，单执行者，定时开发保持暂停。有新证据及具体假设才追加工作包；不因等待一个引擎而阻塞独立研究。

已执行的集成检查保留两次运行版本准入失败，修正显式 profile 后继承原账本，完成 MuJoCo 3.15.0 的两个 1600 步案例：初始配置物理失败、历史校准配置通过；有效参数与独立评分均保存。这是已知候选的流程验证，不是新留出。[结果、成本与归档](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-trials-integration-v1.json)。恢复还检查受限 cgroup 已结束，覆盖子进程 PID 尚未来得及写入的中断窗口。

## LIBERO 原生工作流案例

[从完整原任务定位接触与观测问题](libero-workflow.md)：一行观测刷新修正有源码与读回证据；缩小步长的候选未通过迁移筛查。分别保存动作执行、物理诊断及策略验证边界。
