# MuJoCo 与 SuperDex：自由方块斜面对照

[English](incline-comparison-results.md) · [预登记协议](incline-comparison-protocol.zh-CN.md) · [全部指标](evidence/incline-comparison/results.json)

相同几何、质量、初态、重力与三个步长下，两个**固定原生接触配置**给出了不同的漂移和稳定性。MuJoCo 3.15.0 impedance=0.9 九例中 3 例通过原判据，SuperDex 1.0.0 FP64 九例中 8 例通过。计数不是随机抽样成功率，更不是真实材料准确度排名。

## 可以得出的结论

- **静摩擦不是严格静止。** 15°／μ=0.5，两个引擎都有微滑移。MuJoCo 稳态速度约 0.635 mm/s，SuperDex 约 0.319 mm/s。两秒漂移分别为 1.301–1.336 mm 和 0.708–1.132 mm；1 mm 的原界限使前者 0/3、后者 2/3 通过。SuperDex 的漂移随步长细化增大，不能称为已收敛。
- **固定配置的滑动稳定性确有差别。** 35°／μ=0.5 时，MuJoCo 全程 72.8–74.15% 求解采样无接触且转动 0.169–3.130 rad，三个工况都违反解析滑动条件。SuperDex 三例均满足原联合阈值，0.5–2 s 窗口内持续支撑、转动小于 0.00414 rad。其 1/0.5 ms 工况在初始阶段仍有 0.55/0.975% 全程占比的无接触采样，不能说从初态起始终稳定。
- **名义零摩擦的偏差有已知来源。** 两者均 3/3 通过，但 MuJoCo 原生接触 μ 下限为 1e−5，窗口速度 RMSE 约 8.21e−5 m/s；SuperDex 为 8.04e−12–1.52e−10 m/s。后者接近本例的数值精度尺度，不证明任意碰撞或真实材料更准确。
- **保留反例，避免选配置排名。** 本次事先选择 MuJoCo impedance=0.9 基线；[原 #95 的 impedance=0.99](incline-friction-results.zh-CN.md) 三例静态漂移仅 0.141–0.179 mm，比本次 SuperDex 都小。未隐藏这组敏感性证据，也未事后为任一引擎调参。

## 条件与证据

40 mm、64 g 均匀自由立方体，g=9.81 m/s²，初始零速度、底面贴合斜面，2 s，无控制器或初始化后状态写入。静摩擦参考 |f|≤μN；滑动 a=g(sinθ−μcosθ) 仅用于无明显转动且持续支撑的窗口。参数及来源沿用[冻结清单](evidence/incline-comparison/manifest.json)与原协议。

MuJoCo 使用 Euler/Newton、100 次上限、容差 1e−10、solref=[0.02,1]、恒定 solimp=0.9、椭圆摩擦锥。SuperDex 使用 BACKWARD_EULER、100 次上限、绝对/相对容差 1e−9，penalty=1e9、阈值 1e−4 m、平滑半距 5e−5 m、摩擦速度平滑尺度 1e−3 m/s，法向/粘性阻尼为零。固定值来自已发布原生夹具及切向实验；**这些数值不是等价材料模型或相同求解工作量**。

九例 SuperDex 共 21,000 步均报告 CONVERGED；质量、惯量、重力、坐标、几何、初态和求解器读回通过，状态—力冲量残差均低于原 1e−7 N·s 上限。独立评分不伪造 SuperDex 不提供的组合摩擦律读数，只核验 actor 参数。MuJoCo 沿用原生组合摩擦读回。数学一致性不是排除所有观测伪造的证明。

MuJoCo 力在积分前求解，SuperDex 力在步骤后查询；二者分别与该步速度增量配对。原生接触距离的采样时刻不同，所以另报告相同姿态下的几何方块—平面最大穿透作为诊断，不改变原判据。SuperDex 九例的该几何穿透均为零，接触可在正间隙激活；这不表示碰撞模型完全刚性。

## 全部配对记录

下表速度 RMSE 与加速度误差使用 0.5–2 s 窗口，并以窗口起点实测状态初始化解析参考。MuJoCo 滑动条件失效的拟合误差仅是诊断。接触丢失比例覆盖全程；漂移/路程覆盖全程。所有阈值、力误差与逐项判定见 JSON。

静态工况仅使用静态位移与速度判据，表内滑动拟合误差不作为其通过依据。

| Case | Engine | Drift/travel (mm) | Window velocity RMSE (m/s) | Acceleration error (m/s²) | Rotation (rad) | Contact loss | Pass |
|---|---|---:|---:|---:|---:|---:|---|
| static-d0.9-h0.002 | mujoco | 1.3360 | 3.4391e-11 | 2.6294e-12 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.002 | superdex | 0.7085 | 4.9802e-16 | 7.1027e-17 | 0.00064297 | 0.000% | True |
| static-d0.9-h0.001 | mujoco | 1.3125 | 1.5649e-11 | 1.1174e-12 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.001 | superdex | 0.8471 | 1.0809e-15 | 5.7369e-17 | 0.0015764 | 0.450% | True |
| static-d0.9-h0.0005 | mujoco | 1.3008 | 9.561e-12 | 6.5559e-13 | 0.0012725 | 0.000% | False |
| static-d0.9-h0.0005 | superdex | 1.1319 | 1.948e-15 | 3.952e-16 | 0.0019206 | 0.825% | False |
| sliding-d0.9-h0.002 | mujoco | 3219.5391 | 0.099105 | 0.012352 | 3.1304 | 72.800% | False |
| sliding-d0.9-h0.002 | superdex | 3257.9769 | 5.7581e-07 | 6.6638e-07 | 0.0017856 | 0.000% | True |
| sliding-d0.9-h0.001 | mujoco | 3218.0635 | 0.068754 | 0.00090431 | 0.16872 | 74.150% | False |
| sliding-d0.9-h0.001 | superdex | 3283.6218 | 3.8327e-07 | 4.0609e-07 | 0.0041306 | 0.550% | True |
| sliding-d0.9-h0.0005 | mujoco | 3206.5829 | 0.083108 | 0.02272 | 1.2045 | 73.275% | False |
| sliding-d0.9-h0.0005 | superdex | 3309.0334 | 2.6197e-07 | 2.1428e-07 | 0.0027688 | 0.975% | True |
| frictionless-d0.9-h0.002 | mujoco | 5082.9180 | 8.209e-05 | 9.4757e-05 | 1.0324e-07 | 0.000% | True |
| frictionless-d0.9-h0.002 | superdex | 5083.1077 | 8.0447e-12 | 1.3071e-11 | 0 | 0.000% | True |
| frictionless-d0.9-h0.001 | mujoco | 5080.3791 | 8.2076e-05 | 9.4757e-05 | 1.0745e-07 | 0.000% | True |
| frictionless-d0.9-h0.001 | superdex | 5080.5687 | 1.8544e-11 | 1.9817e-11 | 0 | 0.450% | True |
| frictionless-d0.9-h0.0005 | mujoco | 5079.1096 | 8.2069e-05 | 9.4757e-05 | 1.0324e-07 | 0.000% | True |
| frictionless-d0.9-h0.0005 | superdex | 5079.2992 | 1.5159e-10 | 2.1352e-10 | 0 | 0.825% | True |

## 初始瞬态不能隐藏

下表从 t=0 的静止状态计算全程误差。SuperDex 35° 工况虽通过窗口判据，全程速度误差却随步长细化从 0.0185 增至 0.0453 m/s；不能用窗口内极小拟合误差宣称全程精确。几何穿透是补充诊断，不用于重写旧验收。

| Case | MuJoCo full velocity RMSE (m/s) | SuperDex full velocity RMSE (m/s) | MuJoCo geometric penetration (mm) | SuperDex geometric penetration (mm) |
|---|---:|---:|---:|---:|
| static-d0.9-h0.002 | 0.000714932 | 0.000684274 | 0.169099 | 0 |
| static-d0.9-h0.001 | 0.000669145 | 0.00150622 | 0.120738 | 0 |
| static-d0.9-h0.0005 | 0.000655178 | 0.00270599 | 0.120208 | 0 |
| sliding-d0.9-h0.002 | 0.077904 | 0.0185466 | 4.6068 | 0 |
| sliding-d0.9-h0.001 | 0.0553112 | 0.0321913 | 0.928803 | 0 |
| sliding-d0.9-h0.0005 | 0.0724752 | 0.0453452 | 0.959918 | 0 |
| frictionless-d0.9-h0.002 | 0.000109444 | 7.00678e-12 | 0.159249 | 0 |
| frictionless-d0.9-h0.001 | 0.00010943 | 1.61531e-11 | 0.102009 | 0 |
| frictionless-d0.9-h0.0005 | 0.000109423 | 1.2816e-10 | 0.0945565 | 0 |

## 成本与复现

新批次受限服务 3.772 s，九例准备合计 0.615 s、原生步进 0.630 s、观测 1.352 s、循环内其他记录开销 0.253 s。CPU 为 Intel Core i9-14900K，x86_64，零原生工作线程；执行限制为 16 GiB、2 CPU 配额、128 任务、零 swap、1800 s。历史 MuJoCo 报告记录同 CPU 型号，但不同时间和环境，**不作速度排名**。短计时包含噪声；没有渲染或并行传输。安装另耗 15.396 s。

| Case | SD setup (s) | SD native steps (s) | SD observation (s) | SD loop wall (s) | SD total (s) | MJ historical native steps (s) |
|---|---:|---:|---:|---:|---:|---:|
| static-d0.9-h0.002 | 0.26139 | 0.04411 | 0.06605 | 0.12234 | 0.38672 | 0.00251 |
| static-d0.9-h0.001 | 0.04760 | 0.08908 | 0.13333 | 0.24682 | 0.30024 | 0.00489 |
| static-d0.9-h0.0005 | 0.04560 | 0.17572 | 0.26266 | 0.48699 | 0.54489 | 0.00967 |
| sliding-d0.9-h0.002 | 0.04343 | 0.04229 | 0.06700 | 0.12168 | 0.16856 | 0.00181 |
| sliding-d0.9-h0.001 | 0.04317 | 0.07272 | 0.13271 | 0.23008 | 0.28009 | 0.00358 |
| sliding-d0.9-h0.0005 | 0.04362 | 0.11600 | 0.25741 | 0.42225 | 0.47988 | 0.00715 |
| frictionless-d0.9-h0.002 | 0.04369 | 0.01290 | 0.06207 | 0.08681 | 0.13295 | 0.00303 |
| frictionless-d0.9-h0.001 | 0.04311 | 0.02566 | 0.12474 | 0.17389 | 0.22154 | 0.00592 |
| frictionless-d0.9-h0.0005 | 0.04340 | 0.05124 | 0.24641 | 0.34435 | 0.39659 | 0.01166 |

```bash
# Offline rescore after extracting the release archive:
python -m dexlab.incline_compare_score --superdex paired-incline/superdex --mujoco paired-incline/mujoco --output comparison.json
# New native run, only inside the documented bounded resource/research window:
python -m dexlab.incline_compare_run --manifest docs/evidence/incline-comparison/manifest.json --output /data/new-comparison --admission-only
python -m dexlab.incline_compare_run --manifest docs/evidence/incline-comparison/manifest.json --output /data/new-physical-comparison
```

评分器只依赖 NumPy；引擎运行需官方 FP64 包。旧 MuJoCo 归档哈希、离线 CRC 和全部 18 例重评分已核验，未重跑。零步准入补加重力与平面距离读回后再次核验；正时长实验仅一批九例。失败例全部保留。新运动记录绑定采集提交 `dd5b9c0`；几何穿透诊断是后续离线补充，没有改动物理记录或阈值。

与抓取的联系：静态承载应测漂移及保持时间；滑动应先检查支撑连续性和转动，再解释摩擦加速度。该基元不直接验收完整抓取策略。后续工作集中在 [#113](https://github.com/huangkiki/Dexlab/issues/113) 和 [Issues](https://github.com/huangkiki/Dexlab/issues)，不把未完成计划写成已验证能力。

[Raw archive](https://github.com/huangkiki/Dexlab/releases/download/v0.46.0/paired-incline-raw-v1.zip) · [SHA256](evidence/incline-comparison/archive.json)
