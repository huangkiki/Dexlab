# 历史重评：统一指标与证据边界（D03）

[English](README.md) | [简体中文](README.zh-CN.md)

**结论：七个固定批次共 208 条记录按当前评分器重新读取；旧夹布“通过”应列为几何复核，其余批次的协议结果见下表。没有实测精度或等预算引擎排名。**

此报告为历史离线重评，不是新一轮动力学实验；发布验收见 [GitHub Releases](https://github.com/huangkiki/Dexlab/releases)。保持原控制器、引擎与物理阈值，原始输入逐文件校验，分析前后哈希必须一致。

## 结果与结论

![各批次结果](outcomes.zh-CN.svg)

| 批次 | N | 历史通过 | 当前协议通过 | 协议失败 | 几何复核 | 不支持 | 超时 / 运行失败 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 苹果抓梗回归 | 20 | 11 | 11 | 9 | 0 | 0 | 0 / 0 |
| 基础布料留出 | 105 | 52 | 52 | 53 | 0 | 0 | 0 / 0 |
| PhysX 布料留出 | 15 | 10 | 10 | 1 | 0 | 4 | 0 / 0 |
| 基础接触开发 | 38 | 25 | 25 | 13 | 0 | 0 | 0 / 0 |
| 静态响应开发 | 17 | 11 | 11 | 6 | 0 | 0 | 0 / 0 |
| 瞬态响应开发 | 12 | 6 | 6 | 6 | 0 | 0 | 0 / 0 |
| 机器人夹布诊断 | 1 | 1 | 0 | 0 | 1 | 0 | 0 / 0 |

分母属于不同任务和开发阶段，不能相加形成总成功率。基本接触、静态和瞬态批次是开发配置，不是随机成功率测试。PhysX 外力拉伸的 4 个“不支持”保留在全部场景分母中，不计作通过。未完成的苹果 100 场景测试没有并入这 20 次回归。

选取的是预先列明的完整发布批次，不是仓库全部历史运行。基础接触原始发布包还保留 3 次初始化失败；其它早期开发、资格检查和细化记录仍在各原报告中，本表没有重新评分这些记录。

![逐场景抓梗指标](apple-metrics.zh-CN.svg)

苹果图表中的两条曲线对应各自固定参数。原生重叠与相对腕部位移分面显示；1 mm / 2 mm 虚线沿用旧验收阈值，× 表示整体验收失败。位移很小也可能是根本没有提起苹果，必须结合离桌、支撑等完整检查。两条原生重叠曲线依赖不同接触算法，不能据此宣称同一表面的物理精度排名。材料点累计滑移所有记录均为未知。

机器人夹布：225 个 25 Hz 保存帧中 176 帧进入桌体，最大内部深度 3.00 mm；旧协议通过并不消除几何问题。该深度按零厚度三角面与厚 6 mm 的桌体计算，不能与 SDF 原生距离或竖直穿透合并比较。物理修复由 [#32](https://github.com/huangkiki/Dexlab/issues/32) 跟进。

## 测量契约

每条结果包含固定批次与场景 ID、历史/当前状态、失败检查、原始文件 SHA-256、当前评分器 SHA-256 和采样覆盖。数值统一为 SI；图中仅将米显式换算为毫米。定义与近似见下表及 [metrics.json](metrics.json)。未观测量为 `null`，不填零、不跨缺测帧插值。场景没有球体、地面或固定边界时，对应指标为 `not_applicable`，不是测得零。

| 指标 ID | 单位 | 定义与边界 |
|---|---|---|
| `apple.native_depth` | m | 苹果与右手原生接触点的重叠最大值；引擎接触定义与 SDF 离散各异，不是全表面精度 |
| `apple.wrist_translation` | m | 保持期苹果在腕部坐标系的位置相对首帧最大位移；不是材料点滑移 |
| `apple.wrist_rotation` | rad | 保持期相对首帧姿态的最大旋转角；不判定滚动或滑动 |
| `apple.clearance` | m | 保持期苹果最低点相对桌面最小高度；沿用记录中的几何近似 |
| `apple.support` | 1 | 保持期手部总接触力竖直分量均值除以重力；不是指令力或法向夹紧力 |
| `apple.momentum` | 1 | 全程逐步力与速度增量的动量残差最大值除以重力；不是能量守恒误差 |
| `cloth.ground_depth` | m | 相对地平面的最大顶点侵入，包含设定碰撞半径；不等于实测布厚 |
| `cloth.sphere_depth` | m | 三角形内部到球心最近距离与球半径加碰撞半径之差的正部最大值 |
| `cloth.edge_strain` | 1 | 相对静止边长的绝对应变最大值；不是连续介质应力或材料标定 |
| `cloth.pin_error` | m | 固定顶点相对初始位置的最大位移；用于边界条件检查 |
| `cloth.final_tip_sag` | m | 末帧自由端相对静止高度的平均下垂，向下为正；不是实测误差 |
| `cloth.crossing_pairs` | count | 抽样帧内非相邻三角形交叉对数最大值；排除共享顶点，不保证厚度或帧间无交叉 |
| `robot_cloth.table_depth` | m | 桌体盒并集内零厚度三角形的最大内部深度；上界为桌厚一半，不是竖直或原生穿透，不新设通过阈值 |
| `robot_cloth.intrusion_frames` | count | 超过数值零容差 1e-8 m 的侵入帧数；不是连续时间或新增物理容差 |
| `robot_cloth.anchor_error` | m | 选定材料点相对运动学锚点的最大距离，混合分离、形变与切向运动；不是累计滑移 |
| `robot_cloth.lift` | m | 保持窗口中选定材料点相对计划初始点的最大抬升；不是末帧值或整布最小离桌高度 |
| `plane.box_depth` | m | 变换后盒顶点相对 z=0 平面的最大侵入；独立解析几何，不是原生软接触距离 |
| `cylinder.sat_depth` | m | 离散棱柱与两指盒的 SAT 重叠最大值；不是理想圆柱，边数及离散误差见原始配置 |
| `contact.momentum` | 1 | 被测刚体逐步动量残差最大值除以重力；使用原生合力及声明时序，不是指令值 |
| `normal.static_error` | 1 | 2/4/6 N 平台末 50 ms 压入均值相对 20 kN/m 合成目标的最大相对误差；不是硬件精度 |
| `normal.plateau_std` | m | 三个正载荷平台末 50 ms 的总体标准差最大值；仅去均值，仍包含慢漂移 |
| `normal.transient_rms` | m | 各加载起点后 50 ms 对合成阻尼弹簧响应的最大窗口 RMS 误差；不拟合时移或偏置，不含脱离阶段 |
| `normal.transient_peak` | m | 三个瞬态窗口的最大绝对误差；与 RMS 使用同一合成参考，不是材料动力学实测 |
| `material_slip` | m | 缺少持久接触材料点对应与切向轨迹；必须记为 null，不能用零或腕部漂移替代 |

时间覆盖：抓梗为全程逐物理步记录，保持窗口 `[11,14)` 秒；基础布料与接触包括未步进初始帧；夹布表面诊断只有 25 Hz，夹持检查使用 100 Hz trace 的 `[2,hold_end)` 秒。布料自交另按 `surface_coverage` 的实际抽样间隔报告，不宣称帧间连续无碰撞。力使用被测物体世界系原生合力，并与对应步的速度增量对齐；不把驱动目标作为测得的力。

数值损坏与物理失败分开：缺文件、哈希改变、重复/截断时间戳、矛盾检查会让报告生成失败，不会缩小分母或改记为物理失败。原生警告、稳定性/保留失败等完整运行结果保留为协议失败。不支持、超时、运行错误保持独立状态。

## 两条评估轨道

| 轨道 | 本次状态 |
|---|---|
| 对实测物理参考的误差 | 未提供实测力、材料响应或真机轨迹，未知；20 kN/m + 40 N·s/m 是合成工程目标。 |
| 等预算调参后的任务性能 | 历史调参预算不等，不能称等预算 benchmark；仅报告各固定配置及协议结果。 |

当前不输出速度排行：准备、物理步进、控制/记录、渲染、归档应分别计时，旧记录未满足统一隔离条件。完整能量收支、材料滑移、真实摩擦和驱动辨识仍缺证据。

## 数据、代码与复算

[全部结果与逐文件哈希](historical-v1.json) · [逐指标 CSV](metrics.csv) · [冻结批次选择](cohorts.json) · [离线评分代码](../../src/dexlab/evidence_report.py) · [图表生成代码](../../scripts/render_evidence_report.py)

补齐的两组公开包使用显式脱敏副本及冻结历史评分器；106 条记录完整复算一致。下载目录、变换及限制见 [独立复算说明](PUBLIC-ARCHIVE.zh-CN.md)。原历史报告保留当时的可用性记录，当前下载位置以本表为准。

| 批次 | 完整原始记录 |
|---|---|
| 苹果抓梗回归 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-grasp-regression-evidence.tar.gz) |
| 基础布料留出 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz) |
| PhysX 布料留出 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz) |
| 基础接触开发 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.12.0/v0.12.0-contact-development-evidence.tar.gz) |
| 静态响应开发 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.13.0/v0.13.0-normal-response-evidence.tar.gz) |
| 瞬态响应开发 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.14.0/v0.14.0-transient-response-evidence.tar.gz) |
| 机器人夹布诊断 | [发布包](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz) |

在现有 DexLab 环境中复算，另外安装绘图依赖 `matplotlib`。私人位置文件用批次 ID 映射到解压目录；分散记录可用 `{场景ID: 本地目录}`。不提交该文件。每个根目录下应直接包含场景 ID；发布包的外层目录需要手动选择。所有原始数据可用后才能生成完整报告，命令不会联网下载或执行仿真。

```bash
.venv/bin/python -m dexlab.evidence_report \
  --locations "$PRIVATE_LOCATIONS" --output /tmp/historical-new.json
.venv/bin/python scripts/render_evidence_report.py \
  /tmp/historical-new.json --output /tmp/evidence-report
```

复算会载入保存的 MuJoCo 模型作几何/FK 分析；不会调用动力学积分。评分版本由源文件哈希集合精确绑定，而不只依赖包版本号。图表生成成功不代表新代码已通过发布门禁。

[任务与参数来源](../inventory/README.zh-CN.md) · [研究方法](../research-focus.zh-CN.md) · [首页](../../README.md)
