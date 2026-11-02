# 运行并检查 CHORD 原生任务

[English](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/NATIVE.md) · [任务准备](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/README.zh-CN.md) · [原生迁移 Issue](https://github.com/huangkiki/Dexlab/issues/285)

首个纸巾盒策略已完成 **32 环境 × 50 迭代 × 24 rollout 步 = 38,400 个样本**，随后在独立进程中加载 checkpoint 并运行 600 步。全部 21 组 Adam 参数状态均执行了 1,000 次更新，动量有限且非零。这证明训练和重载路径实际执行，不代表操作任务成功。

**真实示范任务训练与原生重载：1/3；合格记录与独立评分：0/3；完整迁移：0/3。** 程序合成的 synthbox 单独计数：1 环境、1 迭代、8 个样本、20 次优化器更新，也完成了 600 步重载。ARCTIC 抓盒、搅拌器任务仍缺合法数据及匹配资产。

[实测结果清单](https://github.com/huangkiki/Dexlab/blob/main/demos/chord/results/native-20261102.json)记录 checkpoint 身份、原生设置、产物哈希和失败尝试。原始尝试保留在本地；此精简清单不是公开原始数据包。本轮没有录制原生任务画面。

## 记录检查发现了什么

纸巾盒记录器写出了 600 条控制步前记录、600 条**自动重置前**的控制步后记录，以及 3,000 条物理子步的 VOC（虚拟物体控制）施加命令。记录中的辅助比例和施加命令分量均为零。这是控制器输出，不是接触力实测；接触传感器缓冲单独记录，并明确标记无效接触位置。

固定版本的上游命令在重置时把逐环境 VOC 比例设为 1，即使评估配置已指定辅助目标为 0、衰减步数为 0，也要等物理步之后才更新。DexLab 评估器保留这个初始读数，在**第一次策略动作之前**将比例清零，不额外推进预热物理步，也不改原始源码；后续动作前若读到非零辅助则拒绝继续。synthbox 首次成功重载早于此修正，不计作无辅助评估资格。

预先固定的一致性容差为 `1e-6`，覆盖全部 600 步返回的动作、观测、奖励、done 和物体状态。本轮未通过：

| 独立原生进程对照 | 最大绝对差异 | 解释 |
| --- | ---: | --- |
| GPU 记录器关/开 | 12.6922106743 | 记录器一致性失败。 |
| GPU 记录器关/关重复 | 16.6666135788 | 原始闭环运行也不满足此重复性标准，不能将原因只归给记录器。 |
| 默认 CPU 记录器关/开 | 15.9844508171 | 切换设备也未获得一致性资格。 |

比较字段的单位不同，这些最大值**不是位置误差**。GPU 关/开和关/关都在第 28 个控制步首次超出容差。另一个 CPU 增强确定性、单线程诊断在初始化阶段停住，保存原生调用栈后停止；它不属于支持的评估配置。CPU 路径还报告了接触碰撞组支持限制，因此不对其过滤接触力矩阵作资格认定。

`score.py tracking` 会拒绝这些尝试。本轮不提供由奖励推断的成功率、参考跟踪评分、保持/滑移结论或完整参考完成声明。原容差和全部失败均保留在 [#285](https://github.com/huangkiki/Dexlab/issues/285)。

## 本轮运行环境

CHORD 原始 checkout 固定为 `0530204f3a085fb9ba9cc41b771fc4c853edeab8`，官方镜像为 `nvcr.io/nvidia/isaac-lab@sha256:f07c37e3f0c9f58f7febd0aa9a425523d282be623c0db81ac61006d0e24be07f`。

发布版本与 Python 包版本不同：镜像中 Isaac Lab 的 `VERSION` 为 **2.3.2**，`isaaclab` distribution 为 **0.54.2**；独立安装的 Isaac Sim `VERSION` 为 **5.1.0-rc.19+release.26219.9c81211b.gl**，没有 `isaacsim` distribution 元数据。`runtime.py` 分别保留这两类身份，且不启动模拟器。

运行环境使用 Python 3.11.13、PyTorch 2.7.0+cu128、RSL-RL 3.1.2、NumPy 1.26.0。隔离补充的包为 pyarrow 17.0.0、tensordict 0.8.3、wandb 0.22.2、onnxruntime 1.23.2、pytorch-ignite 0.5.3、coloredlogs 15.0.1 和 humanfriendly 10.0。即使运行 Sharpa，全身任务的自动导入也需要 ONNX/Ignite 依赖。首次下载的官方 URDF importer 固定为 2.4.31，后续运行关闭了 registry 更新。

原生读回为 `omni.physx-107.3.26`、TGS、GPU dynamics 与 broad phase、patch friction、PCM 碰撞处理、100 Hz 物理和 20 Hz 控制。**扩展版本不等于 PhysX 原生核心版本；后者仍未解析。** 本轮不构成跨引擎或材料等效性结论。

在独立运行环境中遵循[固定版本上游安装说明](https://github.com/nvidia-isaac/video_to_data/blob/0530204f3a085fb9ba9cc41b771fc4c853edeab8/robotic_grounding/docs/SETUP.md)，通过自己的授权流程接受适用许可。官方容器需要可写的 Kit `cache`、`data`、`logs`、持久化运行用户目录及时区数据。只读 checkout 还需安装和配置 Git LFS clean filter，并将 `lfs.storage` 放在可写的**外部**目录，否则正确物化的资产也可能无法通过源码检查。这不免除任何哈希核验。

## 复现执行检查

`prepare.py` 仍然只生成命令；Hydra 输出现在放入新的 attempt。`motion.py` 核验此双手任务实际使用的旧版 `ManoSharpaData` loader，不套用全身任务的 `motion_v1` reader。纸巾盒含 390 帧、30 Hz 原始参考；原生半速插值产生 518 个 20 Hz 参考帧。600 步评估可以反复重置，不代表走完了全部参考帧。

执行任何原生命令前，使用[实测资源限额和研究锁](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.zh-CN.md#资源与恢复)。首次复杂模型试跑采用 24 GiB、4 CPU 核、256 tasks；约 5 GiB 的实测峰值按 1.5 倍余量选出 8 GiB 限额。完整训练峰值约 6 GiB，未超该限额；新的训练批次须重新计算余量。所有尝试均禁止 cgroup swap，并保留至少 8 GiB 桌面内存余量。全 GPU 显存采样停止阈值为 20,480 MiB，不是硬分配配额。每次原生尝试上限 900 秒，累计原生预算 7,200 秒。

容器运行时，`bounded_run.py --delegate-containers` 提供 `DEXLAB_BOUNDED_CGROUP`；容器须将该实际祖先作为 `--cgroup-parent`，并核验其宿主 PID 的真实归属。Docker 启动成功本身不能证明隔离生效。环境安装、压缩和大批量哈希不与计时原生运行并行。

以下命令是**已合格资源限额内的子命令**，其命名空间须能访问源码、运行环境、checkpoint 和输出路径：

```bash
# 检查本次本地产出的 checkpoint，不据此声称完成原生重载。
"$CHORD_PYTHON" demos/chord/checkpoint.py "$CHORD_CHECKPOINT"

# 两个独立进程，固定源码、checkpoint、seed 和有限步数。
"$CHORD_PYTHON" demos/chord/evaluate.py --task tissue-box \
  --source "$CHORD_SOURCE" --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/eval-off" --seed 24 --steps 600 --headless

"$CHORD_PYTHON" demos/chord/evaluate.py --task tissue-box \
  --source "$CHORD_SOURCE" --checkpoint "$CHORD_CHECKPOINT" \
  --attempt "$CHORD_RUNS/eval-on" --seed 24 --steps 600 --headless --record

# 离线 NumPy 评分；比较保留产物之前先核对哈希。
"$DEXLAB_PYTHON" demos/chord/score.py parity \
  "$CHORD_RUNS/eval-off" "$CHORD_RUNS/eval-on"
"$DEXLAB_PYTHON" demos/chord/score.py tracking \
  "$CHORD_RUNS/eval-on" "$CHORD_RUNS/eval-off"
```

评估器为每次尝试复制并核对 checkpoint、验证源码身份、保存环境/agent 配置及运行时身份和调用状态；拒绝复用已有目录。`parity` 实测不一致时返回退出码 2；`tracking` 重新计算一致性并拒绝未合格记录。模拟器即使初始化出错也可能以 0 退出，因此必须检查完整调用记录和真实优化器/checkpoint 证据，不能只看进程退出码。
