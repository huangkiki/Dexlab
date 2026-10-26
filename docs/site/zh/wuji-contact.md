# Wuji 双指夹球：夹紧力增加，为什么仍未通过保持检查？

**这次尚未找到合格的 solver failure。** 固定手腕的 Wuji 手在后两次实验中一直夹着球，但最大位移分别为 **2.459 mm、2.734 mm**，超过事前冻结的 **2 mm** 要求。两点接触还保留了一个未被接触力矩约束的转动方向。当前证据支持继续检查抓持与接触建模，不能据此评价引擎的普遍能力。

![v3 完整 4.4 秒记录回放：准备、保持和张开；球上的方向标记只用于展示原始姿态](../../evidence/wuji-contact/v3.gif)

动图来自同一原始轨迹，包含失败和释放阶段，原速播放。球上的十字是**回放时添加的方向纹理**，没有改变碰撞形状或物理轨迹；动图不能用于测量角速度。物理记录为 2 kHz，视频为 30 fps，动图为 15 fps。[完整视频](../../evidence/wuji-contact/v3.mp4) · [回放来源与帧映射](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/v3-render.json)。

## 先复算已有记录

在 DexLab 仓库根目录执行，需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)。使用隔离的 Python 3.12.12，只安装 NumPy 和 Matplotlib 及其依赖；不安装仿真引擎，不需要 GPU、真机或模型 API key。首次下载依赖和[不可变原始证据包](https://github.com/huangkiki/Dexlab/releases/tag/wuji-contact-evidence-v1)，随后可以离线复算。

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/evidence-bundle.json \
  --destination downloads/wuji-contact-v1
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py downloads/wuji-contact-v1/runs/02-v3-hold-release \
  --output results/wuji-contact-v1-rescore
```

打开 `measurements.png` 看位移、速度、原生接触力和实际力矩；同目录的 CSV 保留完整时间序列，JSON 给出独立评分与输入哈希。应看到 `record_integrity_pass: true`、`numerical_balance_pass: true`，以及 **`hold_pass: false`**。这是保留的实验失败，不是复算失败。换成包中的 `00-hold-release` 或 `01-v2-hold-release` 可检查前两次记录；每次使用新的输出目录。

![v3 完整记录的独立复算；绿色区间为评分保持段](../../evidence/wuji-contact/v3-measurements.png)

## 三次实验分别说明了什么

对象为半径 10 mm、质量 20 g 的合成球，惯量为 `2mr²/5`。手腕固定；0.2–0.8 s 闭合，1.0 s 移除所有准备力，1.2–3.2 s 评分，随后张开至 4.4 s。保持位移始终相对 **1.0 s** 的状态计算，没有移动参考点或放宽门槛。2 mm 是球直径的 10%，是本任务约定，不是普遍精度标准。

| 批次 | 事前确定的设置 | 保持最大位移 | 结果与首个已知问题 |
| --- | --- | ---: | --- |
| v1 | 凸包手掌，显式采样 PD | 24.422 m | 首帧已有 4.981 mm 手掌/拇指根部自穿透；控制线性化也不稳定。输入不合格，不能用来归因 solver。 |
| v2 | 同源手掌改原生 SDF；同增益改隐式采样 PD，2 ms 控制周期 | 2.459 mm | 持续双指接触，但未满足 2 mm 保持。两项输入修正不能被解释为单一算法因果效应。 |
| v3 | 只将 v2 控制周期缩短为 0.5 ms；物理步长仍 0.5 ms | 2.734 mm | 夹紧力增加，位移没有改善；该控制频率假设未获支持。 |

三个批次各执行一条完整正例，并按各自停止条件不再执行其余五项。**逐指卸载、张指、禁用接触和零摩擦对照均未获得本轮资格**，没有把未执行项写成通过。更早的 v1 报告曾把掉落后无接触写为释放通过；原报告保留，更正报告要求先通过保持，不能把“没抓稳后掉出去”当成成功主动释放。[完整尝试、未执行项与成本](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/results.json)。

## 已有轨迹揭示的接触结构

以下是**事后诊断**，没有改变原评分，也没有增加物理采集。

| 保持段观测 | v2 | v3 |
| --- | ---: | ---: |
| 两指持续有效接触 | 100% | 100% |
| 指垫平均法向力 | 0.265 / 0.280 N | 0.758 / 0.772 N |
| 切向力/法向力范围（名义摩擦系数 1.0） | 0.321–0.472 | 0.101–0.240 |
| 驱动饱和、其他部位支撑 | 均为零 | 均为零 |
| 两指固定参考点中点的最大移动，10 ms 抽样 | 0.186 mm | 0.093 mm |
| 球相对该中点的最大移动，同样抽样 | 2.345 mm | 2.696 mm |
| 每个保持步的有效接触点数 / 纯接触力映射秩 | 2 / 5 | 2 / 5 |

每个保持段的 4,000 步都只有两个有效指垫接触点，原生读回的接触力矩为零。在两个接触点任意施加力，都不能产生绕它们连线的力矩。用接触点 `p1,p2` 和球心 `c` 构造的映射为：

```text
G = [ I                  I               ]
    [ skew(p1-c) / r     skew(p2-c) / r  ]
```

长度用球半径 `r` 归一化后，两条记录中 G 的秩均为 5。球心到接触连线的距离分别为 0.298–0.774 mm、0.310–0.985 mm；重力相对该连线存在非零力矩，最大绝对值约 0.119、0.154 mN·m。**提高法向力不会凭空补出这个抗扭方向。** 球的记录姿态也发生了明显转动，不能仅因表面没有纹理而把它看作静止。

这不是“秩 5 必然抓不住”的结论：某些特殊重力对齐状态仍能平衡。接触点会迁移、手指也在运动，当前诊断尚未唯一解释全部位移，更没有建立固定转轴摆模型或真实柔性指垫的准确性。[可执行诊断与方程](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/diagnose.py) · [结果](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/diagnosis.json)。

## 数值一致性通过，不等于任务或真机验证通过

独立评分从接触坐标系重建世界力，检查 `mΔv = Δt(Fcontact + mg + Fprep)`。v2、v3 最大残差约为 `1.65e-17 N·s`。利用球的各向同性惯量，另检查角冲量；最大残差约 `1.4e-20 N·m·s`。自由关节角速度先从物体系转换到世界系，转换约定见 [MuJoCo 官方文档](https://mujoco.readthedocs.io/en/stable/overview.html#floating-objects)。

这些检查用于发现单位、坐标系、力的符号和记录时刻问题，不证明接触模型符合真实材料。记录没有数值警告，v3 最高迭代数为 5，但这些字段也不代替求解器终止原因或收敛性研究。这里报告的是抓持配置未达到约定的稳定性要求。

## 重跑、已修复入口和剩余边界

[原生复现说明](https://github.com/huangkiki/Dexlab/tree/main/demos/wuji-contact)给出固定依赖、资产校验、独立输出、评分与回放命令。使用未修改的 MuJoCo 3.17.0；刚体物理为 CPU/float64，合成摩擦与控制增益不是硬件标定值。手的质量、惯量、关节与力矩上限来自固定 Wuji 源资产；手掌 SDF 和其他手指凸包是明确的碰撞近似。

入口现检查**全手初态接触**，超过原 1 mm 穿透容差便在第一步物理推进前拒绝；更正主动释放判据，补齐资产下载清单格式，并分开记录状态、力和实际控制周期。v3 另保存核心/绑定版本及原生二进制哈希；早期记录没有这些新增字段，不能追补为当时已观测。

三个原生过程总计 740.956 s，原 12 次 / 7,200 s 账本剩余 9 次 / 6,459.044 s；未增加预算。v3 外层观察进程退出后，受限仿真服务仍完整结束，按实际终态恢复记账，没有重复运行。该事件与物理失败分别保留。

目前仅有这一原生路径的开发记录。[适用性矩阵](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/applicability.json)仍保留其他引擎和历史配置的未执行状态。本结果没有完成 [#251](https://github.com/huangkiki/Dexlab/issues/251) 的合格正例与全部对照，也没有启动 [#48](https://github.com/huangkiki/Dexlab/issues/48) 的接触切换、受控旋转和十个开发后验证条件。
