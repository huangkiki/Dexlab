# Wuji 双指夹球：点接触与抗扭接触

**同一只手、同一控制器和动作，改变接触模型后，保持最大位移从 2.734 mm 降到 1.025 mm，通过原定 2 mm 门槛。** 这里使用 MuJoCo 已有的抗扭接触能力，没有修改求解器。结果说明这一合成夹持配置对接触模型敏感；目前没有建立合格的 solver failure，也没有验证真实指垫材料。

![同时间、原速的完整 4.4 秒回放：左为点接触 v3，右为抗扭接触 v4](../../evidence/wuji-contact/comparison.gif)

左侧点接触配置保持失败，右侧抗扭配置保持及张开释放通过。两侧均包含准备、保持和释放，原速播放。球上的十字是**回放时添加的方向纹理**，不参与碰撞或物理计算。视频为 30 fps、动图为 15 fps；转动指标来自 2 kHz 原始记录，不能从动图估算。[完整视频](../../evidence/wuji-contact/comparison.mp4) · [原始轨迹与帧映射](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/comparison.json)。

## 不装仿真引擎，先复算结果

需要 Git 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。下面从新目录下载代码和不可变证据包，用隔离的 Python 3.12.12、NumPy、Matplotlib 复算；不需要 GPU、真机、SuperDex、Torch 或 API key。证据包约 **141 MiB**，展开约 **382 MiB**，建议预留 2 GB 空间。

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/huangkiki/Dexlab.git Dexlab-wuji
cd Dexlab-wuji
git sparse-checkout init --cone
git sparse-checkout set scripts demos/wuji-contact
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/evidence-bundle.json \
  --destination downloads/wuji-contact-v1
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py downloads/wuji-contact-v1/runs/03-v4-hold-release \
  --output results/wuji-contact-v4
```

打开 `results/wuji-contact-v4/measurements.png` 看曲线。同目录 CSV 保留完整时间序列，`report.json` 应给出 `record_integrity_pass`、`numerical_balance_pass`、`hold_pass`、`release_pass` 均为 `true`，保持位移约 **0.001025 m**。把输入改为 `02-v3-hold-release`、输出换成新目录，可复算原点接触失败：位移约 **0.002734 m**，保持和释放资格均为 `false`。失败结果保留在包中，不表示下载或复算失败。

[原始数据、逐文件哈希与许可](https://github.com/huangkiki/Dexlab/releases/tag/wuji-contact-evidence-v1)包含四批开发记录、所有已执行与未执行项、历史评分及更正、模型和源码。不要在原始输入目录内写输出。

## 比较改变了什么

对象是半径 10 mm、质量 20 g、惯量 `2mr²/5` 的合成球。Wuji 手腕固定，0.2–0.8 s 闭合，1.0 s 移除全部准备力，1.2–3.2 s 评分，随后张开至 4.4 s。位移始终相对 **1.0 s** 的状态；没有移动参考点或放宽门槛。

| 批次 | 事前确定的设置 | 保持最大位移 | 结论 |
| --- | --- | ---: | --- |
| v1 | 凸包手掌，显式采样 PD | 24.422 m | 首帧已有 4.981 mm 自穿透，控制线性化也不稳定；输入不合格。 |
| v2 | 同源手掌改原生 SDF；隐式采样 PD，2 ms 控制周期 | 2.459 mm | 持续双指接触，未通过 2 mm 保持。两项输入修正不隔离单一因果效应。 |
| v3 | 仅将控制周期缩短为 0.5 ms；物理步长不变 | 2.734 mm | 夹紧力增加，保持仍失败；频率假设未获支持。 |
| v4 | 沿用 v3，只给球接触增加合成抗扭定律 | 1.025 mm | 原保持、主动释放及新增角动量检查通过。 |

v4 使用 `condim=4`，滑动摩擦系数仍为 1，抗扭摩擦长度为 **0.002 m**，没有激活滚动摩擦。用均匀压力圆斑作解析近似：合成半径 `a=3 mm`、`mu=1` 时，纯扭转极限 `T/N=(2/3)*mu*a=0.002 m`。抗扭长度和保持位移门槛碰巧都为 2 mm，但含义不同。

这没有模拟弹性体积或真实接触斑变形，`a` 也不是实测值。MuJoCo 的联合滑动/扭转椭圆锥是进一步近似，上式只确定纯扭转截距。参数在本批启动前冻结，没有按结果扫参。[v4 协议](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/PROTOCOL-v4.zh-CN.md) · [原生接触模型](https://mujoco.readthedocs.io/en/stable/computation/index.html#condim)。

![原始状态给出的完整保持段比较；灰色为不评分的沉降段](../../evidence/wuji-contact/hold-comparison.png)

**v4 仍存在缓慢漂移。** 上图绿色位移曲线继续增加；通过两秒保持窗口，不等于无限时长静止抓持。这里没有延长已冻结的实验去补结论，长时间保持仍需另行验证。

## 为什么点接触一直夹着，球仍然转动

v2、v3 的两个保持段各有 4,000 个物理步，每一步均为两个有效指垫接触，原生接触力矩为零。两点任意施力都不能产生绕两点连线的力矩；按球半径归一化的纯力抓持映射 `G=[I,I; skew(p1-c)/r,skew(p2-c)/r]` 秩为 5。

v3 中，球心距离接触连线 0.310–0.985 mm，重力绕该线的力矩非零；两指固定参考点中点最多只移动约 0.093 mm，球相对其中点却移动约 2.696 mm。提高法向力不会增加点接触本身缺少的力矩方向。这是事后结构诊断，不是“所有秩 5 抓持都失败”的证明：特殊重力对齐状态仍可能平衡，而且这里的手指与接触点会移动。

| 保持段测量 | 点接触 v3 | 抗扭接触 v4 |
| --- | ---: | ---: |
| 双指有效接触 | 100% | 100% |
| 平均指垫法向力 | 0.758 / 0.772 N | 0.815 / 0.829 N |
| 最大线速度 | 25.110 mm/s | 0.539 mm/s |
| 最大角速度 | 29.336 rad/s | 0.024992 rad/s |
| 单接触最大内禀力矩 | 0 | 0.022138 mN·m |
| 驱动饱和、其他部位支撑 | 均为零 | 均为零 |

v4 从准备阶段起就使用新接触定律，因此也影响准备结束时的状态。这个开发对照支持“新接触模型使该夹持配置通过验收”；不能把全部历史位移唯一归因于一个自由度，也不能把转动路径长度当成受控净旋转。[可执行诊断](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/diagnose.py) · [各次诊断](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/diagnosis.json)。

## 保持以外的对照

| 对照 | 实测结果 | 判定 |
| --- | --- | --- |
| 保持与主动释放 | 保持 1.025 mm；张开后无接触并掉落 | 符合冻结要求 |
| 卸载食指 | 所选指垫末段最大法向力 0 N；保持位移 1.025 mm | 符合冻结要求 |
| 卸载拇指 | 所选指垫末段最大法向力 0 N；保持位移 1.025 mm | 符合冻结要求 |
| 保持张指 | 保持评分 拒绝；最大位移 23.7456 m | 符合冻结要求 |
| 禁用球接触 | 保持评分 拒绝；最大位移 23.7456 m | 符合冻结要求 |
| 名义零摩擦 | 保持评分 拒绝；最大位移 23.3643 m | 符合冻结要求 |

名义零摩擦是把所有 geom 的三项系数置零；原生接触读回仍有 **1e-5** 的数值下限，所以不能描述为严格数学零。单指卸载后掉落可以是合理结果，卸载按所选指垫的实测法向力单独验收。v1–v3 各因正例失败停止，其余 **15 项仍为未运行**，没有用 v4 替写历史批次。v1 原评分曾把掉落后无接触计作释放通过；原评分保留，更正评分要求先通过保持。最终自审又用解析反例发现：两侧力抵消会让合力为零，但不代表接触已解除。释放检查现按每个接触的力判断，阈值不变；原始轨迹没有重跑，九条记录的任务判定均未改变。[释放反例与离线复算](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/release-rescore-audit.json)。[完整尝试与成本](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/wuji-contact/results.json)。

## 数值一致性、复现与边界

独立评分重建原生接触力，检查 `mΔv=Δt(Fcontact+mg+Fprep)`；v4 保持/释放正例的最大残差约 `1.65e-17 N·s`。同一正例的角动量检查包含接触点力臂、内禀力矩及外力矩，最大残差约 `4.74e-22 N·m·s`。自由关节角速度按[官方约定](https://mujoco.readthedocs.io/en/stable/overview.html#floating-objects)从物体系转到世界系。这些检查验证符号、时刻与记录一致性，不证明真实材料准确性，也不代替数值收敛研究。

[原生运行与回放说明](https://github.com/huangkiki/Dexlab/tree/main/demos/wuji-contact)提供固定依赖和资产校验。物理为未修改的 MuJoCo 3.17.0、CPU/float64；手的质量、惯量、关节和力矩上限来自固定源资产，控制与材料参数为合成设置。手掌采用原生 SDF，其余手部碰撞仍为源网格凸包。

入口修复包括：全手初态穿透预检、主动释放判据、资产下载清单格式、状态/力的时间标注，以及核心/绑定版本和二进制身份记录。前三批原始数据不变。v3 外层观察进程退出后，受限服务仍完整结束，按实际终态恢复记账且没有重跑；后续会计驱动独立于前台会话运行。

本轮累计 **9 次原生启动 / 3433.724 s**，原 12 次 / 7,200 s 预算剩余 3 次 / 3766.276 s，未重置额度。v4 六项开发对照均达到各自冻结要求。本页面不把历史未运行项算作完成。

这只是首个原生路径的开发资格；[适用性矩阵](https://github.com/huangkiki/Dexlab/blob/main/demos/wuji-contact/applicability.json)保留其他引擎和历史配置的未执行状态。[#251](https://github.com/huangkiki/Dexlab/issues/251) 的交付状态以合并、部署和逐项验收为准；[#48](https://github.com/huangkiki/Dexlab/issues/48) 的接触切换、受控旋转和十个开发后验证条件尚未完成。
