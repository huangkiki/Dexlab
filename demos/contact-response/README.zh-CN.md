# Wuji 接触预测诊断

[English](README.md) | [简体中文](README.zh-CN.md)

预测抓持中的物体将移到哪里、各手指是否继续承载接触。本入口在**已有六个合成 Wuji v4 回合**上评估保持和常速基线，不包含学习模型，不启动物理仿真或策略训练。

六个回合已全部导入并独立复算，保持／常速诊断和 14 项解析回归完成实现验证；这不等于动作条件模型合格。[完整机器可读报告](../../docs/evidence/contact-response/baselines.json)。[Issue #261](https://github.com/huangkiki/Dexlab/issues/261) 保留候选模型准入、新原生重复／干预和控制收益验收。已有 release/unload 记录使用不同命令，不能作为已合格的因果三分支实验。[Wuji 抓持资格结果](../wuji-contact/README.zh-CN.md) 仍是原任务结论。


## 实际基线误差

100 ms 时域下，每回合有 100 个起点，范围为 1.20–3.18 s；目标时点可延伸至 3.28 s，包含释放／卸载刚开始的部分。这些来自单次开发回合的窗口相互相关，不是重复试验。

| 源案例 | 保持位置 RMSE（mm） | 常速位置 RMSE（mm） |
| --- | ---: | ---: |
| hold-release | 0.0491 | 0.0221 |
| unload-index_finger | 0.0484 | 0.0181 |
| unload-thumb | 0.0505 | 0.0232 |
| open | 1342.0424 | 49.2953 |
| no-contact | 1342.0424 | 49.2953 |
| zero-friction | 1326.2571 | 49.2953 |

常速在这里降低了短时位移误差，但两种接触保持基线均不能预报丢失。在命令释放／卸载阶段、100 ms 时域下，三个抓持案例分别有 5/6、6/6、5/5 个食指／拇指丢失窗口，两种基线全部漏报。这些窗口互相重叠，不是独立物理事件次数。常速也忽略重力：自由落体对照约 49.2953 mm 的误差符合半隐式参考式 `g*h*(h+dt)/2`，其中 `h=0.1 s`、`dt=0.0005 s`、`g=9.81 m/s²`。

[逐阶段、手指、时域的完整数据](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-response/baselines.json) 同时保留原任务评分和预测诊断。SHA-256：`ae888c5cd970f6f9ab694741203484c30c00a049ab7c92be37350b55ca1d0c98`。独占窗口复算得到逐字节相同的报告；这只验证离线可复算性，不是新的原生重复。原生因果响应和控制收益仍未评价。

## 离线运行

使用 Linux CPython 3.12、NumPy 2.5.2 和已验收的 [Wuji 证据包](https://huangkiki.github.io/Dexlab/zh-cn/latest/wuji-contact.html)。下列命令不导入 MuJoCo、Torch 或 GPU。`BUNDLE` 是包含 `runs/` 的解包目录。

```bash
python demos/contact-response/baselines.py \
  --bundle "$BUNDLE" --output response-baselines.json
```

入口核对固定证据包索引、所选 manifest 和原始观测哈希，重新运行已修正的 Wuji 独立评分器，检查状态连续性，只导入六个 v4 回合。不完整或数值不一致的记录会被拒绝。物理数组指纹会识别重压缩、计时变化和四元数符号变化后的相同回合；副本单独列出，保留的整回合只属于 `diagnostic-only` 分区。这里没有训练／测试划分或独立留出验证主张，原证据包仍保留 v1–v3 失败。

冻结的 `protocol.json` 使用 20、100、200 ms 预测时域和 20 ms 起点步幅。这些是描述性时域，不是调参所得的通过阈值。逐回合报告，重叠窗口和共有的抓取前缀相互相关，窗口数不等于独立试验数。几何距离只覆盖原生求解器实际报告的接触；未报告接触不等于测到了正间隙。

## 输入和输出时序

| 字段 | 单位／坐标 | 可用时点 |
| --- | --- | --- |
| 20 个关节位置／速度 | rad／rad/s，源端顺序 | 第 `i` 步求解前 |
| 物体位置／线速度 | m／m/s，世界坐标 | 第 `i` 步求解前 |
| 物体四元数／角速度 | wxyz／rad/s，角速度为局部坐标 | 第 `i` 步求解前 |
| 关节目标 | rad，位置命令 | 求解前；两种基线忽略动作 |
| 请求力矩 | N m，裁剪前 | 控制输出，区别于实测执行器力矩 |
| 指垫法向载荷 | N，逐指垫—物体接触求和 | 只用已完成的第 `i-1` 步 |
| 未来状态和接触标签 | 同上，第 `i+h` 步 | 只用于评分，不反馈给预测 |

常速基线外推平移，并在四元数右侧积分局部角速度；保持基线复制起点姿态。两者沿用上一个已完成求解的接触标签，使用 v4 原有的 0.02 N 法向载荷阈值。相向载荷可能在净力中抵消，所以不能用净力代替接触标签。两种基线均不能预见接触切换。

报告区分辅助准备、稳定前过渡、保持和命令释放／卸载起点；按手指和时域拆分接触建立、持续、丢失、无接触及丢失后重接触窗口，包含窗口中间发生的切换。输出位置／姿态误差、终点接触混淆计数、建立／丢失事件计数。精确率或召回率分母为零时记为 `null`，不算成功。跨阶段窗口保留起点所属阶段，不用单一汇总分数代替逐回合证据。

## 比较连续前缀

`prefix.py` 检查干预前的**每一帧**，包含干预时点的状态，但控制命令和求解观测只取严格早于干预的部分。位置、旋转测地角、速度、请求／实测控制、外部输入、指垫载荷以及接触身份、坐标框架和力／力矩分别按单位比较。原生接触数量或顺序变化会拒绝兼容性。

```bash
python demos/contact-response/prefix.py \
  --baseline "$BASELINE" --repeat "$REPEAT" --intervention "$INTERVENTION" \
  --protocol frozen-prefix-protocol.json --output visible-prefix.json
```

后续协议必须提供 `intervention_start_s`、`horizon_s`、非空 `tolerance_basis` 和 `prefix.UNITS` 中的全部容差。没有默认原生数值阈值：上游的 1 mm、动作 +0.15 和噪声比例属于另一机器人／环境。须在新响应结果出现前，连同 #261 要求的原生矩阵、有限预算一起冻结并说明依据。

即使可见前缀兼容，结果仍是 **`UNIDENTIFIED`**。现有源记录格式不能证明独立新进程或完整编译模型一致，隐藏求解器缓存不可观测，也仍缺少实测重复波动范围和预先声明的效果／方向阈值。所报告的干预／重复最大位移差仅用于诊断。预测误差变小不能替代物理任务成功或控制收益。

设计借鉴 [Ref2Dex-agent](https://github.com/hitsz-oyx/Ref2Dex-agent/blob/31cdb9ac759838b83d62bbc0addfd5cf28f3dff4/src/task/dex-contact-mbrl/tools/audit/compare_serial_response.py) 的 baseline/repeat/intervention 连续比较，并要求按单位检查整个可见前缀，不能只凭干预瞬间的物体位置放行。本目录不重新分发外部权重或资产。
