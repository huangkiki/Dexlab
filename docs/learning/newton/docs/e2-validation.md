# E2 验证记录

对应 [Issue #3](https://github.com/huangkiki/newton-atlas/issues/3) 与[控制、机器人与任务](control-robotics-tasks.md)。实现基于已发布 E1 的 main `9423d6ef3d0572f8adf746c6dedd30175bd21543`；本记录覆盖本地源码/静态验收，外部发布、CI 和合入状态由 Issue 与对应提交追踪。

## 要求与证据

| 要求 | 实际交付 |
|---|---|
| A3 控制到实际驱动 | 正文第 1–5、9–10 节；Control、内置 drive 与显式 Actuator 的消费者、单位、限幅、状态/延迟、调度和 reset |
| A5 机器人原生接口 | 第 2、6–9 节；q/qd/target/compact 映射，FK/状态重建/目标 IK 区分，TCP/Jacobian 换点，限位与闭环边界 |
| A7 任务接口 | 第 10–11 节；外部命令的时间/frame/映射要求，接近/闭合/保持/释放、连续 dwell、超时与终态；具体观测协议留给 DexLab |
| 公式与实际源码 | PD/PID 与单位、implicit-effort 简化推导、LM 与 DLS 的不同 lambda、原生 IK residual 方向；沿 kernel 而非只凭参数名解释 |
| 易错点与阅读练习 | 第 12 节对照表及 8 道带答案练习 |
| 最小原创例子 | [标量原生驱动](../examples/e2_scalar_drive.py)、[二连杆目标 IK](../examples/e2_target_ik.py)、[任务阶段函数](../examples/e2_task_phases.py)；正文有完整 controller 端口连接 Python 片段 |
| 导航和真实状态 | 中英文 README、curriculum、roadmap、versions、source-map 与 manifest；E3–E7 保持未实现状态 |

## 实际执行的静态检查

Python **3.12.12**，不 import Newton/Warp，不调用任何教学例子：

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

- 全仓相对 Markdown 链接通过。
- AST 解析通过：**4 个教学 Python 文件**（E1 的 1 个 + E2 的 3 个）与 **1 个 Markdown Python 片段**。任务阶段函数同样没有执行；本文不把静态检查说成运行测试。
- [sources.json](sources.json) 共 **52 个固定源码文件**（E1 的 22 个 + E2 新增 30 个）；各自按 `SHA1("blob " + byte_length + NUL + bytes)` 与同一官方提交的 Git tree、manifest 三方对照。
- 全仓 **175 个 Newton blob 链接**均使用固定提交、已在 manifest 登记且行号有效。首次链接检查发现 `Actuator.step` 引用结束行超出文件，已改为实际文件末尾 L539 并通过复查。
- 人工语义自审与源码检查区分：有效行号不证明解释正确。重点沿 builder 注册/分配、Actuator 输出、solver 消费、controller 端口、IK residual/Jacobian 与任务状态转移逐项核对。
- 内容 SHA-256 与检查边界见 [e2-validation.json](e2-validation.json)。E1 验收是其发布时快照；本阶段扩展公共来源清单，所以旧记录中的 manifest 摘要不应被解释为以后每个版本的同一内容。

## 审查中纠正和保留的边界

1. 确认公开 `newton.controllers` 未导出内部 `select_joints`；课程使用公开构造器的 joints/articulations，内部 helper 仅作源码入口。
2. 区分 actuator Drive 名称与机器人 Controller 名称；这两个 API 都标注实验性。组合 actuator 的 SISO/no-transmission 边界单列。
3. 沿 MuJoCo kernel 确认标量 joint_f 进入 qfrc_applied、FREE/DISTANCE 经独立路径进入 xfrc_applied；没有把 actuator forcerange 扩大为对任意外力的饱和承诺。
4. 记录 solver 对 target_mode、effort/velocity limit、BALL/FREE drive 与闭环的差异；明确内部 target 与外部 joint_f 可能叠加。
5. 明确目标 IK 与 differential IK 的 residual 方向、LM 的 lambda 与 DLS 的 lambda²区别；DLS 的等价公式不代表实现显式求逆，实际用单边 Jacobi SVD。
6. 官方 differential IK 示例直接绑定 State 并 FK，是运动学展示；新增 PD 例子显式连接 Control/actuator/XPBD，但本章仍未执行它。
7. 任务阶段函数不虚构接触、滑移或成功数据；输入事件须由未来实际观测与协议提供。超时与过期观测优先转 FAILED，终态持续至显式 reset。

## 未验证与下一项

没有运行二进制、资产导入、IK 求解、物理控制、抓持实验、训练、性能基准或精确恢复。不存在由本章产生的控制稳定性、IK 收敛率或抓取成功率。具体 gains、阈值、延迟和设备能力不得从例子升级成实测结论。

A3/A5/A7 的源码与教学交付满足本阶段契约。下一项优先 E3，展开接触/约束求解、完整数值语义以及观测力/冲量；E4 可独立推进，E5 仍等待 E4。每一项仍需单独实现、审查、验证与交付，不因本章完成而提前关闭。
