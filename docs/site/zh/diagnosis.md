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
