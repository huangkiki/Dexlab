# Uranus：生成式环境后端（候选）

[English](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html) | [简体中文](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html)

> **状态：文档化候选后端，尚未实现 DexLab runner，也未进入任何正式 cohort。** 本页定义接口、评测方法和证据边界；文中论文结果不是 DexLab 复现结果。

## 原始工作

**Uranus: Building the Next-Generation Simulation Infrastructure for Embodied AI**

Wenkang Qin, Yukun Zhou, Noah Shen, Jisong Cai, Dongxiao Mao, Baicheng Li, Yue Zhang, Wei Sui<br>
D-Robotics · Peking University · Shanghai Jiao Tong University · arXiv 2026

[论文](https://arxiv.org/abs/2609.24815) · [项目页](https://d-robotics-ai-lab.github.io/large-model-team/blog/uranus/) · [推理代码](https://github.com/D-Robotics-AI-Lab/Uranus-OSS) · [SDK](https://github.com/D-Robotics-AI-Lab/Uranus-SDK) · [模型权重](https://huggingface.co/collections/D-Robotics/uranus) · [演示数据](https://huggingface.co/datasets/D-Robotics/Uranus-Demo-Data)

Uranus 是一个约 1.3B 参数的机器人视频世界模型，从参考图像、历史 latent、未来关节位置轨迹（`qpos`）、机器人描述和相机标定生成同步多视角观测。它的价值在 DexLab 中不是替代接触求解器，而是提供一种**可学习的 observation backend**。

```text
reference / generated history
        + future qpos
        + camera intrinsics & extrinsics
        + MJCF / URDF
        + optional text
                ↓
      causal autoregressive DiT
                ↓
       multi-view latent frame
                ↓
       streaming VAE decoder
                ↓
   four RGB frames per camera / step
```

## 在 DexLab 中的位置

| 层 | 职责 | Uranus 的位置 |
| --- | --- | --- |
| 任务与协议 | 场景、初始状态、seeds、预算、验收 | 不提供；由 DexLab 定义 |
| 被测对象 | RoboAPI、VLA、WAM、policy | 不提供；Uranus 只生成观测 |
| 环境后端 | 推进任务并返回观测 | **候选生成式后端** |
| 动作执行 | API 动作到控制器/关节目标 | 需要外部 IK/controller |
| 证据与评分 | 成功率、接触、失败归因、cohort | 不提供；由任务 scorer 独立计算 |

因此 Uranus 不是“另一个 DexLab”，也不能直接替代 MuJoCo、Newton、SuperDex 或 Genesis。正确关系是：

```text
DexLab task / protocol
        ↓
RoboAPI / VLA / policy
        ↓ (T, 8) end-effector targets
IK / controller / session adapter
        ↓ future qpos
Uranus observation backend
        ↓ generated RGB
task-specific observation + success evaluator
        ↓
DexLab score / evidence / cohort
```

## 接口语义

Uranus 的条件变量是**未来关节位置轨迹**，不是力矩、速度、末端位姿或原始 torque action。以当前 Poke RoboAPI 的 8 维绝对末端目标为例，集成时必须增加一步动作转换：

```text
RoboAPI output (T, 8)
    [x, y, z, qx, qy, qz, qw, gripper]
                    ↓ IK / OSC / controller
Uranus input qpos[t:t+4]
```

每一轮还需维护：

- 与输出四帧对齐的四个 qpos；
- 每帧相机内外参；
- reference RGB、MJCF/URDF 和文本任务描述；
- RoboAPI session、turn 和 tool feedback；
- API 侧 8 维状态。该状态应从实际控制目标、qpos 和前向运动学构造，不能假装 Uranus 从 RGB 中可靠恢复了物体状态；
- 任务专用 `done` 与 `success` predicate。Uranus 本身不输出二者。

## 首批建议任务

这些是 pilot 候选，不代表已经对 Uranus 开放或完成基准资格。

| 层级 | 任务 | 主要检查 |
| --- | --- | --- |
| 接口冒烟 | `reach_cube`、`move_above_object` | 动作转换、四帧时间对齐、会话状态 |
| 基础刚体 | `pick_cube_to_basket`、`lift_pot` | 抓取、抬升、物体状态 |
| 接触与位移 | `move_can_to_pot`、`push_box_to_target` | 推动方向、滑移、停止时机 |
| 目标放置 | `put_bottles_dustbin`、`place_object_basket` | 目标区域、释放后稳定性 |
| 精细操作 | `hanging_mug`、开抽屉 | 对位、铰接物体、持续接触 |
| 压力测试 | 海绵擦拭、布料夹取 | 形变与接触；只作诊断，不先做主榜 |

不建议第一版直接用切割、流体或高精度插接来证明 Uranus 是通用物理仿真器。论文已明确承认接触、物体状态转移和长时误差仍是主要缺口。

## 怎样评一个 API

每个任务固定场景、初始状态、机器人配置、相机、seeds、动作频率和回合预算，同时运行：

1. **原生参考后端**：MuJoCo / SuperDex / Newton / Genesis 等已合格配置；
2. **Uranus 候选后端**：相同初始观测、instruction 和策略接口，动作经 IK 转成 qpos；
3. **独立 scorer**：使用任务状态或经校准的视觉判据，不允许被测模型读取 scorer 状态；
4. **完整尝试保留**：接口错误、超时、无效动作和物理/视觉无效运行分别归因。

若只有一个 API，不做跨模型 Pearson/MMRV。应报告：

- 每个任务的 `success_native`、`success_uranus` 和 Wilson 区间；
- 配对 episode 的 outcome accuracy；
- false-success / false-failure 数量与案例；
- 平均成功率的差值和 bootstrap 区间；
- 失败是否集中在抓取、保持、滑移、目标放置、视觉漂移或接口错误。

若对比多个 API，再报告成功率相关性与排序一致性，并保留逐任务矩阵。Uranus 的视觉质量指标只能作为辅助，不能替代任务结果。

## 论文已经报告什么

- GE-Sim 2.0 对照中，在 100 个 AgiBot G1 样本上，140–160 秒 head view 约 `12.3 PSNR / 0.45 SSIM`，对照为 `7.1 / 0.20`；
- WorldOlympiad robotics 取得 Overall `0.722`、Interaction `0.730`，但 3D Consistency 为 `0.511`；
- RoboTwin 五任务、九个策略的闭环成功率与原生环境达到 Pearson `0.98`、MMRV `0.01`；
- 真实测试集人工一致性为 `58%`，说明视觉连续性仍可能掩盖错误交互结果。

这些结果支持“Uranus 值得作为视觉环境后端研究”，不支持“它已经能提供原生物理真值”。RoboTwin 实验还使用了针对该域的 fine-tuning 和 7,891 条失败轨迹。

## 当前限制

- 公开仓库提供 inference 和 SDK；完整训练、数据及 serving 控制面没有同步开放；
- 单会话示例约 `535 ms/latent`，四帧一次；主页所称 `24 FPS` 没有在正文中给出明确口径；
- 模型不积分力矩或速度，不显式求解接触、摩擦和任务状态；
- 多视角同步与视觉稳定性不等于物理状态正确；
- 没有内置 reward、termination、success 或 contact readback；
- 当前没有 DexLab 的 Uranus adapter、runner、容器、cohort 或正式成绩。

## 从文档到可执行后端还缺什么

1. 定义稳定的 observation/reset/step/close 适配器；
2. 为至少一个 UR5/Robotiq 风格任务提供 8D EE action 到 qpos 的独立转换；
3. 为原生参考和 Uranus 后端冻结同一初始状态与任务协议；
4. 实现并校准任务 success predicate；
5. 完成一组 pilot 后，才能把状态从 `documented candidate` 升级为 `local / unverified`。

在此之前，README 和榜单不得把 Uranus 写成已验证 backend，也不得把论文分数转写成 DexLab 分数。

## 上游入口

Uranus 的独立推理可参考官方仓库；当前需要单独下载约 17.5 GB 权重，不属于 DexLab 文档环境的安装依赖。

```bash
git clone https://github.com/D-Robotics-AI-Lab/Uranus-OSS.git
cd Uranus-OSS
uv sync
uv run python main.py \
  --weights-dir /path/to/uranus-weights \
  --sample-dir /path/to/sample \
  --output-dir /path/to/output
```

这一步验证上游推理入口，不是 DexLab 后端集成。
