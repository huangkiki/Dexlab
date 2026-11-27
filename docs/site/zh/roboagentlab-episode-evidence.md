# RoboAgentLab：怎样让机器人 Agent 的动作和结果对得上？

| 速览 | 内容 |
| --- | --- |
| 项目 | RoboAgentLab，基于 pi 的机器人 Agent 研究平台 |
| 输入 → 输出 | 任务、机器人观测、动作接口和预算 → 工具或程序执行、环境读回、会话与回合结果 |
| 公开状态 | 平台代码、文档、两套交互数据和历史运行报告可读。项目页将配套论文标为待发布。动作单元模式能接入已有 Show-Harness LoRA |
| 核查基线 | 2026-11-27，平台源码 `edef599`，10 月 1 日历史实验另有运行版本 |
| DexLab 判断 | **`pilot`**。先在已有回放里验证动作、原生状态与独立评分能否逐条对账 |

[官方项目页](https://roboagentlab.github.io/) · [固定版本的平台说明](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/README.md)

## 给它什么，它替你做什么？

给 Agent 一句“把桌上的碗放到目标位置”。在 LIBERO 仿真里，它可以看相机图，选择靠近、夹紧和抬起，动作执行后再看结果。它也可以调用检测器获得掩码，或用 Python 把几个原语组织成带条件的程序。相机图、检测结果和仿真器真值是三种不同的输入条件。真值能帮助定位执行问题，比较视觉能力时必须单独标出这项权限。[官方接口文档](https://roboagentlab.github.io/docs/modes.html)

| 实验里能换什么 | 典型选择 |
| --- | --- |
| **观测 O1–O3** | 原始传感器、外部感知工具、仅仿真可用的特权状态 |
| **执行 A1–A3** | 选固定执行器做一个动作单元或技能、逐次组织工具调用、编写受限 Python 程序 |
| **决策者** | API 大模型、自托管模型、微调学生，以及无模型的计划回放 |

这三项分开配置，具体组合仍取决于机器人和服务。比较 A2 工具与 A3 Python 时，要固定场景、种子、观测权限、评分和预算，还要记录原语可用集合和每次调用能推进多少低层步。否则“调用少”可能仅仅表示一条调用完成了更多动作。官网的 Act / Build / Evolve 分别描述让 Agent 做任务、搭建研发流程、用反馈保留改进这三种角色。下面可在源码检查的是执行接口、记录和评测。 [平台架构](https://roboagentlab.github.io/#platform) · [模式与支持矩阵](https://roboagentlab.github.io/docs/modes.html)

## 一次动作从哪来，谁来判结果？

1. **pi 保存任务和会话**。机器人扩展注册观测、工具及回合开始与结束。Skill 交代单位、操作顺序和如何处理反馈。服务端按自己的约束执行动作。
2. **机器人 manifest 声明可用原语**。例如移动末端的动作记录参数、是否改变环境、所属层级及依赖。能共享的环境侧原语，让工具调用和 Python 白名单走同一服务端方法。程序入口在启动时核对 manifest 和当前可用集合的摘要。部分 TypeScript 侧的 VLA 策略循环只作为 Agent 工具提供。
3. **Python 服务执行并回传观测**。一条动作可跨多个控制步，Agent 可在拿到图像、状态或错误后决定下一步。以代码模式及其可用原语为例，结束前的关键链路可以写成 `观测 → Agent 请求 → 服务执行 → 原生读回`。请求里的目标位姿和后端读回的实际位姿应分别保留。
4. **回合记录保留不同的判法**。Agent 的 `finish` 结束回合，同时保留它自己的说法。LIBERO 用环境的 `terminated`，RoboDojo 保留原生判定和单独的部分分数，部分真机配置由操作者给结论。HumanCLAW 的通用 `success` 字段映射到导航指标。跨环境比较前要先确认指标的语义。

[原语与程序接口](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/adding-a-primitive.md) · [回合记录源码](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/src/robot.ts) · [官方评测文档](https://roboagentlab.github.io/docs/evaluation.html)

## 公开证据能回答什么？

平台的评测工具把任务和随机种子组成网格，每格保存一份会话与结果。重跑时保留配置一致且有效的完结记录，包括任务失败，允许重试无效格。比较两个模型时，应保留尝试总数，并单独公开有效任务失败、规划器错误和环境错误。角色分类里出现一篇论文、向导认得一个名字、预设实现了其设置、同条件复现得到原成绩，是四种不同的证据。

| 公开材料 | 数量或结果 | 可支持的判断 |
| --- | --- | --- |
| Policy Interactions | **904** 个已筛选的 Agent 轮次，**848** 个有公开图像 | 可查看工具调用与反馈。数据卡区分轮次和完整回合 |
| Robotics R&D Interactions | **2,396** 个研发轮次，**184** 个有公开图像 | 可查看开发交互。基线提交、补丁、测试或结果缺证时保留空值 |
| 2026-10-01 HumanCLAW 诊断 | 同一个沙发场景的两次尝试，原生 `NavSR@20cm` 和 `InteractSR` 均为 **2/2**，正确坐上目标座面两次均未获视觉验收 | 一个场景里的测量边界反例，分母是两次尝试 |

两套数据的默认 `train` 提供可读取的分片。要把它当训练监督，还需核对完整上下文、去重、工具定义、结果标签和使用许可。Policy 数据里的 LeRobot v3 子目录另存连续执行记录，保留不同动作空间及坐标约定。工具会话中提到某个文件，只能支持路径关联，精确对到控制帧仍需记录方提供连接键。Show-Harness 的已有权重用于动作单元路径，固定源码中的工具和代码学生路径有接口及 SFT 转换。文档尚未给出这两条路径的已训练适配器或等条件蒸馏成绩。[Policy 数据卡](https://huggingface.co/datasets/RoboAgentLab/pi-embodied-policy-interactions/blob/09820c16208cf6f06f0d4236dfa2db3c15d42c7e/README.md) · [研发数据卡](https://huggingface.co/datasets/RoboAgentLab/pi-embodied-rd-interactions/blob/8b0e75515367ae12e6af459e0a8e464d449848f5/README.md) · [Show-Harness 权重](https://huggingface.co/showlab/Show-Harness-VLMs)

## 同一个沙发，两个分数都绿了

两次运行使用同一沙发场景、自托管 Qwen3.8-27B、900 秒预算和额外的自身运动反馈。报告使用了各自冻结的历史代码版本，HumanCLAW 源码相同。原生 `InteractSR` 检查交互任务、主动停止、曾执行坐下，以及末次坐下末帧的骨盆与目标网格接触。把它想成“碰到这张沙发”的检查。判断身体是否真的由座面承托，还要知道接触的是哪里、方向与支撑是否持续。公开结果未给出逐步接触点或支撑力时序。[作者报告与两张原始回放图](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/report.md#humanclaw指标改善与视觉验收分开) · [结果 JSON](https://github.com/RoboAgentLab/RoboAgentLab/blob/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/results.json)

- **第一次**。任务要求坐到指定沙发。回合执行 29 个决策步、3 次 SIT，28 个运动步中有 19 步碰撞，主动停止时距目标 AABB 约 8.6 cm。原生交互判定为真，回放中人位于沙发背侧，无法确认座面承托。现有证据最早能定位到坐下阶段的座面验收条件缺失。碰撞可能放大对位误差，具体哪一步走偏仍需姿态、实际位移和接触点时序。
- **第二次**。同场景重新执行，38 个决策步、3 次 SIT，37 个运动步中有 17 步碰撞。最终目标距离为 0，原生交互判定仍为真，作者回放却把人定位在沙发旁圆桌附近，未验收为坐上目标座面。现有证据确认目标家具接近或接触的指标宽于座面验收。还需逐步查骨盆与沙发座面、靠背及圆桌的接触对象和支撑方向，才能判明何时失去正确对位以及最终由谁承托。

![作者第一次回放末帧，人位于沙发背侧](https://raw.githubusercontent.com/RoboAgentLab/RoboAgentLab/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/humanclaw-run1-final.png)

![作者第二次回放末帧，人位于沙发旁圆桌附近](https://raw.githubusercontent.com/RoboAgentLab/RoboAgentLab/edef599e5656454efa39fa1807963d90b399db3d/packages/embodied/docs/reports/2026-10-01/humanclaw-run2-final.png)

两张图来自作者用保存的物理后状态重建的回放。画面能检查位置，无法单凭末帧读出载荷或推断碰撞先后。

## DexLab 先借哪一块？

DexLab 的 [Wuji 接触响应诊断](contact-response.md) 已有动作、原生接触记录和独立评分，也能检查干预前的逐 tick 观测。值得借鉴的是让读者在一次回放里追到**某条动作请求、它对应的执行窗口、窗口里的原生读回以及原 scorer 的判定**。保留记录哈希、单位、坐标系、时间基准和来源。Agent 会话中缺失的调用编号显式留空。

最小试验只读已有证据。从冻结的 Wuji v4 诊断集选一段合格持握、一段已有卸载，沿用记录哈希和独立 scorer。用原报告的索引和时间戳核验每条命令关联的执行区间，并保留首次原生载荷变化及其条件。另用一份离线副本遮去一个连接键，检查界面是否将它显示为未知。**验收**是两段的原评分及分母完全一致、所有可解释连接都能回追、缺失连接不会被前后图像补猜。若原记录已能做到同样的定位，直接复用。若关键连接缺证，记录缺口并停止扩展。

本轮核查了固定版本源码、项目文档、数据卡和作者报告，未重跑平台或 DexLab 仿真。现阶段先验证回放可归因性，沿用 DexLab 的仿真后端和评分。[DexLab 当前工作](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md)
