# DexLab

**让仿真器与机器人模型在同一批失败样本上互相指出盲点，然后一起改进。**

DexLab 把一次接触任务跑成可追溯证据：模型执行，记录原生状态、接触读回和失败层级；发现物理缺口就升级仿真器，发现策略缺口就回到模型。任何一边更新后，绑定模型版本、仿真器版本、任务协议和原始证据，重新跑同一 cohort。公开评测榜只是这个闭环留下的一个可验证视图，不是目标本身。

[理解共同进化](#coevolution) · [Poke RoboAPI 适配](demos/roboapi-poke/README.md) · [English](README.en.md) · [已完成实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [评测与防刷榜协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html) · [在线实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab)

> 当前阶段：任务场景、原生观测、独立评分和证据链已存在；远程模型执行器与公开 leaderboard 正在建设中。公开 Issue 只提交可公开信息，不要填写 API Key、私有地址或权重凭据。

<a id="coevolution"></a>
## 为什么是共同进化，而不是单向验收

仿真器不只是模型的“考场”。同一个失败里往往混着三种可能：模型没有学会、场景没有配好、物理本身算错了。只有把三者分开，才能决定下一步改哪里。

1. **模型跑任务。** 用固定任务、机器人配置、仿真版本和预算执行一轮接触操作。
2. **记录真实接触。** 保存原生状态、接触力、冲量、求解状态、命令和原始轨迹，而不是只留一段成功视频。
3. **归因失败。** 判断失败来自模型、适配器、控制器、场景还是物理；引擎缺陷导致的无效运行不扣模型分。
4. **升级其中一边，再回到同协议。** 如果暴露物理缺口，就改仿真器；如果暴露策略缺口，就改模型。任何一边变了，就进入新的版本化 cohort。

这四步让模型和仿真器不断互换角色：模型发现仿真器哪里失真，仿真器又反过来提出模型必须面对的物理条件。

## 两个进化方向

| 方向 | 现有证据 | 说明了什么 |
| --- | --- | --- |
| **模型跑出仿真器的边界** | 海绵擦拭原版 **3/3** 通过，去掉辅助保持后 **0/3**，最终清洁率约 **95.47% / 39.92%**。 | 结果高度依赖仿真中的保持机制；不能把一次成功直接归给模型策略，也不能把无辅助失败直接归给某个 solver。 |
| **物理变化逼出策略边界** | Wuji 双指夹球把点接触改成合成抗扭接触后，两秒保持位移从 **2.734 mm** 降到 **1.025 mm**。 | 同一控制在不同物理配置下结果不同；对模型来说，这就是必须面对的新条件。 |

当前仓库主要证明了“物理条件改变结果”这一侧。外部模型接入后，才能记录“模型策略改变结果”的另一侧；在此之前，共同进化是正在扩展的方法，不是已经完成的闭环。

## 每一轮会留下什么

| 产物 | 用途 |
| --- | --- |
| **版本化结果** | 每个 cohort 绑定模型版本、仿真器版本、任务协议、seeds、预算和证据，两边升级时不会混用旧分数。 |
| **失败归因** | 说明失败发生在观测/接口、抓取、保持、滑移、接触切换、动作超时还是物理无效运行。 |
| **可复算证据** | 原始记录、独立评分和复现入口保留下来，供下一次模型或仿真器迭代对照。 |
| **验证状态** | 区分 `local / unverified`、`official verified` 和 `reproducible`，不把内部复核写成外部已复现。 |

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

## 怎样给一次结果计分

每个任务先独立计算成功率，主榜再对任务等权求宏平均。同一任务的所有回合都进入分母；长任务不会因为回合多获得额外权重。基础设施故障与模型失败分开记录；引擎、场景或记录无效导致无法评测时，不把环境缺陷算成模型失败。所有重试和失败保留，不能从多次尝试中只提交最好一次。

## 共同进化需要可验证的防刷榜

为了不让“一起进化”变成挑选最好结果，DexLab 采用公开集复现、隐藏场景一致性检查、固定 seeds 与预算、同一 checkpoint 完成所有任务，以及完整尝试保留。正式成绩由 DexLab 官方执行；客户自跑结果只能标为 `local / unverified`。[完整评测与防刷榜协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)

## 怎样参加 pilot

1. 提交一个不含密钥的 [模型评测申请](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+)：模型类型、机器人配置、观测/动作接口、关注任务和公开意愿。
2. 通过私密渠道确认 endpoint、凭据、预算和数据处理方式。
3. 冻结一次 cohort，完成接口资格和 pilot 运行。
4. 先收到私有报告；决定是否申请公开榜或公开可复现材料。

远程模型服务是首选接入方式。模型端只需要接收部署时可获得的观测并返回动作，不读取评分器、未来状态或仿真特权信息。当前仓库尚未发布可直接连接的托管服务端点。

已提供 [Poke RoboAPI 适配层](demos/roboapi-poke/README.md)：填写 `POKE_ROBOAPI_KEY` 后即可查询模型、读取 schema，并做一次不控制机器人的推理调用。逐任务的仿真观测与动作执行映射见[适配与 sim2real 对照](docs/roboapi-poke.zh-CN.md)。

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

任务成功不是物理真实性本身。物理真实性首先属于具体仿真版本和场景资格；模型主要按任务成功率与稳定性评测。仿真通过不证明真机成功，隐藏验证集也不证明真实世界泛化。真实材料、传感器、机器人安全和部署可靠性仍需独立验证。

[研究经验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [求解配置如何分类](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [开发与验收约定](docs/autoresearch.zh-CN.md)
