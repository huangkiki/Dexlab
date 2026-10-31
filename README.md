# DexLab

**让仿真器与机器人模型在同一批失败样本上互相指出盲点。**

DexLab 把一次接触任务跑成证据：记录原生接触与失败层级，再决定改模型还是改仿真器。每次更新绑定模型、仿真器、协议与证据，回到同一 cohort 重跑。榜单只是这个闭环的一个视图。

[共同进化](#coevolution) · [系统组成](#architecture) · [Uranus 后端](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html) · [Poke RoboAPI 适配](demos/roboapi-poke/README.md) · [English](README.en.md) · [已完成实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [评测与防刷榜协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html) · [在线实验](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html#live-lab)

> 当前：任务、评分与证据链可用；远程执行器与公开 leaderboard 仍在建设。

<a id="architecture"></a>
## 系统组成

```text
DexLab
├── 任务与协议：场景、初始状态、seeds、预算
├── 被测对象：RoboAPI / VLA / policy
├── 环境后端：MuJoCo / Newton / SuperDex / Genesis / Uranus
├── 动作执行：IK / controller / session
└── 证据与评分：成功率、接触状态、失败归因、cohort、防刷榜
```

原生物理后端负责状态推进与接触读回；Uranus 是候选生成式观测后端，提供未来 `qpos` 对应的多视角视频。它不拥有任务、成功判据或物理真值。

## 环境后端：Uranus

**Uranus: Building the Next-Generation Simulation Infrastructure for Embodied AI**<br>
Wenkang Qin, Yukun Zhou, Noah Shen, Jisong Cai, Dongxiao Mao, Baicheng Li, Yue Zhang, Wei Sui<br>
D-Robotics / Peking University / Shanghai Jiao Tong University · arXiv 2026

Uranus 从参考观测、历史 latent、未来关节位置轨迹、机器人描述和相机几何生成同步多视角 RGB。接入 DexLab 时，RoboAPI 的末端目标需先经 IK/controller 转为 `qpos`；Uranus 生成观测后，再由独立任务判据决定 success/failure。

[论文](https://arxiv.org/abs/2609.24815) · [项目页](https://d-robotics-ai-lab.github.io/large-model-team/blog/uranus/) · [推理代码](https://github.com/D-Robotics-AI-Lab/Uranus-OSS) · [权重](https://huggingface.co/collections/D-Robotics/uranus) · [完整接口、任务与证据边界](https://huangkiki.github.io/Dexlab/zh-cn/latest/uranus-backend.html)

> 状态：文档化候选后端。DexLab 尚未提供 Uranus adapter、runner、cohort 或正式成绩；论文结果不计作 DexLab 复现。

<a id="coevolution"></a>
## 共同进化

仿真器不只是模型的“考场”。同一个失败里往往混着三种可能：模型没有学会、场景没有配好、物理本身算错了。只有把三者分开，才能决定下一步改哪里。

1. **跑任务：** 固定任务、本体、仿真版本与预算。
2. **记接触：** 保存原生状态、接触力、求解状态与轨迹。
3. **归因：** 是模型、适配器、场景，还是物理。
4. **改一边，再跑同协议：** 任何一边变了，就进入新 cohort。

模型暴露仿真失真，仿真反过来暴露模型的边界。

## 两个进化方向

| 方向 | 证据 | 说明 |
| --- | --- | --- |
| **模型跑出仿真边界** | 海绵擦拭 **3/3** 通过，去掉辅助保持 **0/3**；清洁率约 **95.47% / 39.92%**。 | 结果依赖仿真保持机制，不能直接把一次成功归给模型。 |
| **物理变化逼出策略边界** | Wuji 换接触项后，两秒保持位移从 **2.734 mm** 降到 **1.025 mm**。 | 同一控制在不同物理配置下结果不同。 |

当前主要证明了“物理条件改变结果”这一侧；外部模型接入后，才能记录另一侧。

## 每一轮留下什么

| 产物 | 用途 |
| --- | --- |
| **版本化结果** | 模型、仿真器、协议、seeds、预算和证据绑定，不混用旧分数。 |
| **失败归因** | 指出失败属于模型、适配器、场景还是物理。 |
| **可复算证据** | 原始记录和评分保留，供下一次迭代对照。 |
| **验证状态** | 区分 `local / unverified`、`official verified`、`reproducible`。 |

## 已完成实验

这些场景证明环境、观测和评分可运行，**不是外部模型的榜单成绩**。

| 任务 | 结果 |
| --- | --- |
| **[抓取与抗滑移](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)**<br>Wuji 双指夹球，点接触与合成抗扭接触。 | **2.734 → 1.025 mm**；通过 ≠ 手内操作完成。 |
| **[海绵擦拭](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html)**<br>来源：RoboSimStudio `wipe_the_bar`。 | 原版 **3/3**，无辅助 **0/3**；清洁率 **95.47% / 39.92%**。 |
| **[布料夹取](https://huangkiki.github.io/Dexlab/zh-cn/latest/cloth-comparison.html)**<br>下垂、拉伸、下落与夹布分开验收。 | 保留穿透、回弹与夹持失败。 |
| **[切割与推动](https://huangkiki.github.io/Dexlab/zh-cn/latest/cut-push.html)**<br>豆腐与香蕉连续切割。 | 保留材料分离与接触力；合成材料不等价食材标定。 |

[完整实验目录](https://huangkiki.github.io/Dexlab/zh-cn/latest/experiments.html) · [全部结果与失败](https://huangkiki.github.io/Dexlab/zh-cn/latest/results.html)

RSS 公开入口见[盘点](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-failure-inventory.html)：50 个入口，40 个任务断言，10 个教学/mock；不是 50 种独立操作，18 个论文场景仍缺原始输入。

## 计分

每任务独立算成功率，主榜取等权宏平均；长任务不加权。无效运行不进模型分母，失败和重试都保留。

## 防刷榜

正式成绩官方执行；公开集复现，隐藏集查过拟合；固定 seeds 与预算，同一 checkpoint 完成全部任务。客户自跑仅记 `local / unverified`。[完整协议](https://huangkiki.github.io/Dexlab/zh-cn/latest/model-evaluation.html)

## 参加 pilot

1. 提交不含密钥的[申请](https://github.com/huangkiki/Dexlab/issues/new?template=model-evaluation.md&title=%5BModel+eval%5D+)。
2. 私密确认 endpoint、预算与数据处理。
3. 冻结 cohort，运行 pilot。
4. 先收私有报告，再决定是否公开。

远程模型只接收可部署观测并返回动作。已提供 [Poke RoboAPI 适配层](demos/roboapi-poke/README.md)：填 `POKE_ROBOAPI_KEY` 即可查询模型、schema，或做一次不控制机器人的推理。[适配与 sim2real 对照](docs/roboapi-poke.zh-CN.md)

## 先看一组证据

无需 GPU，下载一对海绵擦拭记录，离线重算保持位移与清洁率：

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

打开 `results/rss-wiping-v1/comparison.png`。证据包约 **126 MiB**，解包约 **349 MiB**；无辅助 `task_pass: false` 是保留的物理失败。

[复算范围](https://huangkiki.github.io/Dexlab/zh-cn/latest/rss-wiping.html#offline-evidence) · [原始数据与许可](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1)

## 边界

任务成功不是物理真实；仿真通过不证明真机成功。真实材料、传感器、安全和部署仍需独立验证。

[研究经验](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html) · [求解配置分层](https://huangkiki.github.io/Dexlab/zh-cn/latest/solver-taxonomy.html) · [开发与验收](docs/autoresearch.zh-CN.md)
