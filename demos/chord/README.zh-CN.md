# 准备一个 CHORD 任务

[English](README.md) | [批次 Issue](https://github.com/huangkiki/Dexlab/issues/282)

为固定的 Sharpa/Isaac Lab 任务核对本地输入，生成隔离的上游训练或 checkpoint 评估命令。此入口**不启动训练**，尚无 CHORD 原生策略评估结果：**已迁移真实示范任务 0/3**。

## 任务卡

| CLI 任务 | 固定序列 | 配方与当前限制 |
| --- | --- | --- |
| `tissue-box` | `tissue_box_simple` | 上游附带单目重建数据；采用 force-closure 指导，同时关闭初始配置和 curriculum 的接触匹配奖励。 |
| `box-grab` | `dataset_s07_box_grab_01` | ARCTIC contact-wrench 指导；保留盒子的铰接结构。需要合法处理后 motion、匹配资产和权重访问权限。 |
| `mixer-use` | `dataset_s01_mixer_use_01` | ARCTIC 铰接操作；同样受数据条件限制。关节进度、保持和释放判据需检查参考阶段后冻结。 |
| `synthbox-smoke` | `synthbox_box_open_000` | 仅供工程测试的程序合成夹具。1 环境、1 迭代、8 rollout 步，机器人使用 primitive 碰撞；不计入 3 个真实示范任务。 |

四项均为 `source-checked`；`blocked` 是本地预检状态，不是策略失败。`smoke`、`policy-evaluated`、`trained-and-evaluated` 都需后续原生证据。[清单](tasks.json) 固定上游版本、路径、时序、来源/条款和奖励覆盖。清单保存已核对的上游 LFS SHA-256，预检拒绝相应文件的哈希不符；各次预检另计算实际文件 SHA-256；未取得的 checkpoint 哈希保留 null。哈希或文件存在不能证明已满足许可。

## 先核对本地输入

准备工具仅使用 Python 3.10+ 标准库。CHORD 使用**独立的上游 Isaac Lab 2.3.2 环境**，不要装入 DexLab 的 Python 环境。按[固定版本安装说明](https://github.com/nvidia-isaac/video_to_data/blob/0530204f3a085fb9ba9cc41b771fc4c853edeab8/robotic_grounding/docs/SETUP.md)准备，包括机器人 LFS 文件；ARCTIC/MANO 和示例权重可能需要授权账号。本工具不代为下载或接受其条款。

将 `CHORD_SOURCE` 设为 `0530204f3a085fb9ba9cc41b771fc4c853edeab8` 的仓库根目录，`CHORD_PYTHON` 设为该运行环境的解释器/包装脚本，`CHORD_RUNS` 设为已挂载数据盘上的输出目录。路径必须在同一主机/容器命名空间可见。可用 `--data-root` 替换上游附带的 `human_motion_data` 根目录。

```bash
python3 demos/chord/prepare.py preflight --task tissue-box \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON"
```

JSON 列出文件 SHA-256、缺失文件/LFS 指针/错误页面、URDF 引用的网格、checkout 身份、包元数据和 GPU 可见性。退出码 2 表示存在明确阻塞；0 仅表示这些静态检查发现了所需输入。Parquet 只查文件标志，**没有验证语义 schema 或 motion 有效性**。即使返回 0，PhysX 原生版本、contact/VOC 读数、许可来源及资源准入仍待核验。解释器探针只读取包元数据，不启动 Isaac Sim。

## 准备有限命令

以下只生成一轮训练命令供检查，不是足以学习任务的训练预算，也不是迁移结果：

```bash
python3 demos/chord/prepare.py train --task tissue-box \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON" \
  --seed 24 --num-envs 1 --iterations 1 \
  --attempt "$CHORD_RUNS/tissue-plan-001"
```

新 attempt 包含 `preflight.json`、`command.json` 和供检查的 `command.txt`；存在阻塞时仍保留计划并返回 2。seed、环境数和迭代数必须显式填写，避免误用上游大规模默认值。真实任务保留每环境 24 rollout 步、100 Hz 物理和 20 Hz 控制。准备过程不执行限时或分配 GPU。执行前须通过上游 loader 核验，并按 DexLab [资源规则](../../docs/task-coverage.zh-CN.md#资源与恢复)测量和冻结预算，使用 `research_guard.py` 与 `bounded_run.py`。不要绕过这些控制或把 `execution_admitted: false` 当作执行准入。

准备评估需明确 checkpoint 和正整数步数限制：

```bash
python3 demos/chord/prepare.py eval --task box-grab \
  --source "$CHORD_SOURCE" --python "$CHORD_PYTHON" \
  --seed 24 --num-envs 1 --steps 200 --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/box-eval-plan-001"
```

上游会在 checkpoint 旁边导出文件，因此准备工具先复制权重到新 attempt 并核对哈希；已有目录，包括中断后的目录，都拒绝复用。固定版本评估脚本从参考首帧重置，关闭 VOC 并移除 curriculum；实际辅助外力仍需原生检查。参考若从接触状态开始，就不能宣称从自由放置完成抓取。命令保留的是源码契约，不是环境已执行该契约的证据。

## 后续迁移范围

#282 继续承接真实优化器更新与 checkpoint 重载、原生记录、记录器一致性、逐任务有限训练、独立评估/评分和有来源的回放。命令生成、进程成功退出或预训练权重本身都不满足这些验收。本批次仅选 PhysX 训练路线，其他 DexLab 引擎尚不受此迁移支持；FlashCHORD/Newton、Wuji 重定向和跨引擎比较留在后续。
