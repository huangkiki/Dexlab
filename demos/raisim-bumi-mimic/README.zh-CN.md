(raisim-bumi-mimic)=
# RaiSim 作为 Bumi BlinkMimic2 训练后端

**问题：能否保持 BlinkMimic2 的 actor、世界模型和 replay 更新器不变，只把物理 transition 采集换成 RaiSim？** 首轮用六段 LAFAN 动作和冻结的 Bumi checkpoint 实现了这条边界。它不是 40 段资格验证、随机化鲁棒性测试或真机结果。

有价值的工程结论比“RaiSim 训练更好”窄得多：适配器必须保持 Bumi 的 21 关节顺序、浮基、执行器增益与限幅、转子惯量、20 ms 策略周期、5 ms 物理子步、参考目标、接触观测和终止顺序。第一次实现立即暴露了一个契约错误：厂商 URDF 中的 `velocity="0"` 被当前 RaiSim 解释成真实零速度锁死，于是策略改变了关节目标，关节却保持不动。

## 冻结协议

| 字段 | 冻结值 |
| --- | --- |
| 策略 | 从本地完整 checkpoint warm start 的 BlinkMimic2 |
| 算法 schema | `blink2-k8-h32-startup-objective-v6` |
| Bumi 源码 | `2454535c967cd1d6f04dfe0f0289f3c6c608e596` |
| RaiSim | 2.16.0，FP64 CPU 物理 |
| 环境 | 512 个独立 world、16 个工作线程 |
| 时序 | 5 ms 物理子步，每 20 ms 策略步执行 4 次 |
| 预算 | 2 小时或新增 5,000 次更新 |
| 动作 | walk、run、jump、dance、fall-and-get-up、fight |
| 评测 | 每段一个名义条件闭环回合 |

六段归档是冻结 LAFAN40 manifest `604554646ef99f390dcd88fef06bc98bbbb6ffbbd9722f0b97d01203d75afbdf` 的确定性子集，保留原关节／body 顺序、起止帧和逐帧数据。

完整 checkpoint 是 **warm start**，不是精确恢复：actor、critic、dynamics 和兼容 optimizer 被恢复；replay、sampler、episode ID 和执行器历史因物理来源改变而重建。因此不能把后续变化归因于某一次 optimizer 状态迁移。

## 实现边界

原生库为每个环境持有一个 `raisim::World`，批量提供 reset、step、全状态、body 位姿、接触冲量和时钟读回。Python 保留现有 BlinkMimic2 参考动作、actor、世界模型、policy learner、reward、replay 和更新顺序。

Bumi 适配器恢复了 URDF 缺失或特殊编码的 PD、力矩限幅、转子惯量和逐关节速度上限。接触力等于原生接触冲量除以物理步长；非足接触和 body 误差仍可观测。

## 闭环结果

| Checkpoint | 完成数 | 平均 body 位置误差 | 现象 |
| --- | ---: | ---: | --- |
| 冻结 MuJoCo checkpoint 直接在 RaiSim 运行 | 5/6 | 0.0584 m | fall/get-up 早期失败，其余五段完成 |
| RaiSim 第 10,500 次更新 | 4/6 | 0.0376 m | 误差下降，但 fight 与 fall/get-up 失败 |
| RaiSim 第 11,500 次更新 | 2/6 | 0.0589 m | walk 与 run 也退化 |
| RaiSim 第 12,000 次更新 | 1/6 | 0.0433 m | 仅 walk 完成；更低平均误差来自更早失败 |
| RaiSim 第 15,000 次更新／最终 averaged | 0/6 | 0.0399 m | 六段均在完成前失败 |
| RaiSim 第 15,000 次更新／在线 actor | 0/6 | 0.0373 m | 退化不只是最后五个 actor 平均造成 |

完成数和跟踪误差回答不同问题。较短存活轨迹上的更低平均 body 误差不是更好的任务结果。最终报告同时保留两者，也不把早期失败从分母删除。

训练闭环本身没有崩溃或非有限物理 transition：新增 5,000 次更新、采集 6,432,768 个环境步、总墙钟 2,447.66 秒。因此负面的任务结果 **不是基础设施失败**。它说明在新 transition 分布上继续联合更新 actor／世界模型，使闭环策略更不可靠。

## 第一失效层：倒地起身

冻结 MuJoCo checkpoint 在无 reset 噪声的 RaiSim 中评测，`fallAndGetUp1_subject4` 在控制第 31 步首次失败：

| 步 | 状态／证据 | 后果 |
| ---: | --- | --- |
| 1 | 参考位姿载入，已有接触 | 初态有限且与冻结归档一致 |
| 4 | anchor 姿态误差越过 0.4 rad，峰值接触约 86 N | 平动误差增大前，姿态已经发散 |
| 7 | anchor 水平误差越过 0.125 m，峰值接触约 411 N | 支撑响应与 body 姿态开始耦合 |
| 16 | anchor 高度误差越过 0.125 m，峰值接触约 1,460 N | 垂直支撑丢失 |
| 17 | 末端高度误差越过 0.2 m | body 已离开参考支撑流形附近 |
| 31 | 姿态 1.10 rad、水平误差 0.87 m、base 高度 0.335 m | 原定 0.8 rad 姿态门禁终止回合 |

现有证据支持的链条是 **低姿态参考 reset → 较大的策略目标变化 → 姿态发散 → root 高度损失 → 终止**。最早的决定性信号是姿态，而不是末帧倒地。当前六段实验尚不能唯一区分执行器响应、地面接触、reset 穿透和策略敏感性；需要固定状态的 contact/action 消融才能继续判因。

## 最终策略：六段第一失效步

最终 averaged actor 在每一段都越过跟踪门禁。下表是名义单／多环境回放中的首次终止，不是视频末帧现象。

| 动作 | 第一失效步 | 进度 | 现有证据支持的最早触发 |
| --- | ---: | ---: | --- |
| `walk1_subject1` | 12,089 | 92.5% | 姿态误差达 0.825 rad；末端高度误差 0.407 m；终止帧峰值接触约 82 N |
| `run1_subject5` | 5,695 | 47.9% | 末端高度误差 0.434 m；姿态 0.779 rad 仍低于 0.8 rad 门禁 |
| `jumps1_subject1` | 5,433 | 44.4% | 姿态误差 0.936 rad，末端高度误差 0.403 m |
| `dance1_subject3` | 3,271 | 49.7% | 姿态误差 0.897 rad；末端高度误差 0.397 m |
| `fallAndGetUp1_subject4` | 1,617 | 19.2% | 姿态误差 0.900 rad；anchor 高度和末端误差也越界，峰值接触约 1,306 N |
| `fight1_subject3` | 1,689 | 13.8% | anchor 高度误差 0.255 m 越过 0.25 m；末端高度误差 0.363 m |

共同链条是 **策略轨迹偏离参考 → root 与末端关系退化 → 未改变的跟踪门禁终止回合**。训练改变的是控制器，不是评分门禁。当前运行不能区分世界模型偏差、actor 对想象状态过拟合、不兼容 replay 统计和保留学习率过大；下一步应做连续受控消融，而不是再跑一条混合长训练。

[机器可读协议](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/protocol.json) · [最终 averaged 评测](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/final-averaged.json) · [最终在线 actor 评测](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/final-online-actor.json) · [第一失效步测量](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/failure-first-steps.json) · [训练指标](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/metrics.jsonl) · [运行与 checkpoint manifest](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/raisim-manifest.json) · [源码清单](https://github.com/huangkiki/Dexlab/blob/main/demos/raisim-bumi-mimic/evidence/raisim-source-manifest.sha256)

## 证据边界

- 首轮 RaiSim 适配器没有宣称已完成质量、质心或接触材料随机化。
- 训练关闭原版 exam／failure-frontier 阶段，以隔离后端变化；没有复刻 BlinkMimic2 的完整高级调度。
- 只报告六段名义评测，不把它与 MuJoCo 完整 40 段成功率混成同一分母。
- 没有真机标定或 Bumi 实机部署。
- 不以本案例把 RaiSim 晋升为 DexLab 默认后端。
