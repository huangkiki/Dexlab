# DexLab

**为机器人模型提供接触丰富操作的统一评测与失败诊断。**

接入远程模型服务与客户机器人配置，在冻结的任务、仿真版本、随机种子和资源预算下评测抓取、保持、擦拭、布料、切割与插接等能力。DexLab 返回任务等权成功率、多次运行稳定性、逐任务矩阵和失败证据；**正式榜成绩由 DexLab 官方环境运行，不接受团队自报分数。**

[申请模型评测 pilot](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+) · [评测协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html) · [English](README.en.md) · [已完成实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [在线实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab)

> 当前阶段：评测所需的场景、原生观测、独立评分和证据链已存在；远程模型执行器与公开 leaderboard 正在建设中。公开 Issue 只提交可公开信息，不要填写 API Key、私有地址或权重凭据。

## 你会得到什么

| 输出 | 内容 |
| --- | --- |
| **榜单主成绩** | 固定任务集上的任务等权宏平均成功率，同时展示每个任务的结果，避免用原始回合数把长任务偷偷加权。 |
| **稳定性与成本** | 多次运行的成功率分布、超时、调用延迟、动作错误和资源预算。 |
| **失败诊断** | 说明失败发生在观测/接口、抓取、保持、滑移、接触切换、动作超时还是物理无效运行，并保留对应证据。 |
| **可复核状态** | 区分本地未验证结果、DexLab 官方执行结果，以及客户自愿公开材料后的外部可复现结果。 |

## 为什么用 DexLab，而不是只看一段成功视频

接触丰富操作里，“物体被抬起来”并不等于夹住了，“任务结束”也不等于物理过程可信。DexLab 记录原生状态、接触读回、实际命令、评分结果和失败分母，再把以下问题分开：

- 模型能否完成完整任务；
- 失败从哪一步开始；
- 仿真引擎或场景配置是否让这次评测无效；
- 结果是否只能在一个固定布局上成立；
- 其他团队能否复核或复现这个成绩。

适合通用操作模型、VLA/WAM、Agent-as-policy 和远程机器人 API 团队；它评的是模型、适配器、控制器和客户机器人配置共同组成的**端到端系统**，不把不同本体折算成一个虚构的“模型纯能力”系数。

## 已经完成哪些实验

这些场景证明任务环境、观测和评分链可运行，**还不是任何外部模型的排行榜成绩**。

| 接触任务 | 已记录结果 |
| --- | --- |
| **[抓取、保持与抗滑移](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)**<br>Wuji 双指夹球，同一控制下比较点接触与合成抗扭接触。 | 两秒保持位移由 **2.734 mm** 降到 **1.025 mm**，通过原 2 mm 门槛；抓持通过不等于手内操作完成。 |
| **[海绵擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html)**<br>来源为 RoboSimStudio `wipe_the_bar`；保留辅助保持与无辅助对照。 | 原版 **3/3** 任务通过，无辅助保持 **0/3**；最终清洁率约 **95.47% / 39.92%**。 |
| **[布料夹取与释放](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html)**<br>下垂、拉伸、覆盖、下落和机器人夹布分开验收。 | 保留穿透、回弹和夹持失败；不把布料动图直接写成完整折布能力。 |
| **[切割与刀面推动](https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html)**<br>豆腐和香蕉的连续切割、刀面接触与推动。 | 展示材料分离和实测接触力；合成材料结果不等于真实食材标定。 |

[查看完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [查看全部结果和失败](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)

### RSS 实验怎样纳入目录

现有 [RSS 公开入口盘点](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-failure-inventory.html) 覆盖上游 `b001cc7` 的 **50 个公开入口**，其中 40 个带任务范围断言、10 个是教学/渲染/硬件 mock。它们按刚性抓取、布料/软体、绳索/线缆、擦拭/袋/胶带、切割、颗粒/液体/面团和策略执行等任务族纳入检索；目标评分与其场景可能共享同一回合，不能写成 50 种独立操作。论文图 5 的 18 个精确场景仍缺原始输入，与 50 个公开入口不是同一分母。

## 怎样给一个模型计分

正式 cohort 在运行前冻结任务、本体、引擎版本、seeds、重复次数、超时、资源上限和评分器。每个任务先独立计算成功率，主榜再对任务等权求宏平均。

- 同一任务的所有回合都进入分母；
- 不因为某个任务回合多或运行贵就获得额外权重；
- 基础设施故障与模型失败分别记录；
- 引擎、场景或记录无效导致无法评测时，不把环境缺陷算成模型失败；
- 所有重试和失败保留，不能从多次尝试中只提交最好一次。

报告同时显示任务矩阵、成功率波动和失败类别。单项任务失败不会因为没有进入一个平均值就消失。

## 防刷榜

DexLab 借鉴公开 benchmark 的官方执行与隐藏验证思路，并保留接触实验自己的证据边界：

- **官方计分**：正式成绩由 DexLab 控制任务、场景重置、观测、模型调用和评分；客户自跑结果只能标为 `local / unverified`。
- **公开集 + 隐藏验证集**：公开布局用于复现和迭代，隐藏场景变化用于检测坐标硬编码、固定轨迹和只针对公开任务调参。
- **固定预算**：seeds、重复次数、超时和资源上限预先冻结，不允许无限重跑到最高分。
- **固定系统**：同一榜单项必须使用同一 checkpoint 和推理流程完成所有任务，不按任务暗中切换不同模型。
- **技术复核**：检查适配器、动作接口、重复模型、最小改动换名和异常的逐任务选择。
- **保留全部尝试**：模型失败、接口失败、超时、无效运行和平台故障分开记账。

正式榜会区分以下状态：

| 状态 | 含义 | 是否上榜 |
| --- | --- | --- |
| `local / unverified` | 团队自行运行，尚未使用官方冻结条件计分 | 否 |
| `official verified` | DexLab 官方执行并通过接口、泄漏和反刷榜检查 | 是 |
| `reproducible` | 在 official verified 基础上，公开足够配置与材料供外部复核 | 独立徽章 |

原始视频、轨迹和权重默认私有；客户可自愿公开。DexLab 内部完成官方复核，不等于社区已经独立复核。[完整评测与防刷榜协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)

## 怎样参加 pilot

1. 提交一个不含密钥的 [模型评测申请](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+)：模型类型、机器人配置、观测/动作接口、关注任务和公开意愿。
2. 通过私密渠道确认 endpoint、凭据、预算和数据处理方式。
3. 冻结一次 cohort，完成接口资格和 pilot 运行。
4. 先收到私有报告；决定是否申请公开榜或公开可复现材料。

远程模型服务是首选接入方式。模型端只需要接收部署时可获得的观测并返回动作，不读取评分器、未来状态或仿真特权信息。正式接口 schema 会在一轮 pilot 前冻结；当前仓库尚未发布可直接连接的托管服务端点。

## 先检查现有证据

无需 GPU，可以先下载一组海绵擦拭原始记录，从材料点和墨迹状态离线重算保持位移与清洁率：

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git
cd Dexlab
git sparse-checkout init --cone
git sparse-checkout set scripts demos/rss-wiping
uv run --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python scripts/download_assets.py \
  --manifest demos/rss-wiping/evidence-bundle.json \
  --destination downloads/rss-wiping-v1
uv run --offline --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python demos/rss-wiping/rescore_bundle.py downloads/rss-wiping-v1 \
  --output results/rss-wiping-v1
```

打开 `results/rss-wiping-v1/comparison.png` 查看曲线；同目录包含 CSV 和 `report.json`。证据包约 **126 MiB**，解包约 **349 MiB**。无辅助保持的 `task_pass: false` 是保留的物理任务失败，不是下载失败。

[复算范围与失败索引](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence) · [原始数据与逐文件许可](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1)

## 结果边界

任务成功不是物理真实性本身。物理真实性先由引擎和场景资格检查负责；模型主要按任务成功率与稳定性评测。仿真通过不证明真机成功，隐藏验证集也不证明真实世界泛化。真实材料、传感器、机器人安全和部署可靠性仍需独立验证。

[研究经验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [求解配置如何分类](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [开发与验收约定](docs/autoresearch.zh-CN.md)
