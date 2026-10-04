# 稳定版引擎准入

[English](engine-qualification.md) | [简体中文](engine-qualification.zh-CN.md)

发布元数据、导入成功、设备基础检查、完整任务验收是不同层次。依赖兼容不等于苹果或布料场景通过。

## 冻结清单

2026-10-04 UTC（本地 2026-10-05）重新核对官方发布与 PyPI 信息。本轮隔离 GPU 检查候选为 MuJoCo 3.14.0、MuJoCo Warp 3.14.0、Warp 1.17.0。历史演示安装器保持原固定版本，旧记录仍为历史证据。

| 配置 | 状态 | 边界 |
|---|---|---|
| MuJoCo 3.14.0 原生 | 待验 | 尚需完整苹果回归与夹布诊断 |
| MuJoCo Warp 3.14.0 + Warp 1.17.0 | 待验 | 每卡运行/接触检查不等于 SDF 抓取通过 |
| Newton 1.6.0 `sim` | 组合受阻 | MuJoCo 与 MJWarp 的 ~3.12 依赖和最新 3.14 冲突 |
| Genesis 1.4.3 | 待验 | 刚体与布料分别准入，见 #42 |
| SuperDex FP64 1.0.0 | 已有历史任务证据 | 版本稳定不等于新组合通过 |
| Isaac Sim 6.1.0 | 待验 | 须核验内嵌 PhysX 与完整任务 |
| ovphysx 0.6.3 | 排除于稳定版主比较 | 发行包分类为 Alpha |

## 可复现 GPU 基础检查

`scripts/probe_mjwarp.py` 模拟 32 份独立的 0.1 kg、半径 0.05 m 球体落到平面，步长 2 ms，共 1,000 步。逐步采样，检查原生库与绑定一致性、有限状态、完整时间、明显穿越、最终支撑和静置。5 mm 明显穿越、2 mm 最终高度误差、0.02 m/s 静置速度是基础检查阈值，不是抓取验收或实测材料公差。输出记录模型/源码哈希、版本、精度、求解器和失败。

按可用设备每卡一个进程、显式隔离 GPU。预热使用独立状态。编译、逐步回传与并行负载使整体耗时不能作为引擎速度排名。沿用研究锁和资源限制，不新增调度器；设备被占或内存/磁盘预算不足时拒绝运行。运行前核对官方 wheel 与安装文件，不改引擎、不忽略依赖冲突。

## 本轮测得结果

六个设备先各运行 32 份相同初态副本，默认参数的六份记录一致且均未通过侵入检查。随后六卡分别运行六组参数：**4 组通过、2 组失败**。这不是 192 次独立随机试验，也不是留出测试或引擎排名。

![逐配置侵入与失败](evidence/engine-qualification/contact-parameters.zh-CN.svg)

| 步长 (ms) | 接触时间常数 (ms) | 最大几何侵入 (mm) | 完整基础检查 |
|---:|---:|---:|---|
| 2 | 20 | 18.254 | 失败 |
| 0.5 | 20 | 21.703 | 失败 |
| 2 | 4 | 0.498 | 通过 |
| 0.5 | 4 | 4.157 | 通过 |
| 1 | 4 | 3.686 | 通过 |
| 0.5 | 2 | 1.972 | 通过 |

原生 MuJoCo 同一默认 XML 的侵入为 18.254210 mm，MJWarp 为 18.254361 mm。这个对照支持“默认软接触参数导致本场景失败”，不支持“GPU 更容易穿模”。缩短接触时间常数后四组通过，但离散步长的作用不单调；低侵入不等于已证明准确或收敛。未修改引擎或放宽阈值。CUDA 状态为 float32；版本、模型、脚本和官方二进制哈希均在记录中。

[全部结果与原生对照轨迹](evidence/engine-qualification/contact-probes.json) · [原始脚本 v1](evidence/engine-qualification/probe-v1.py) · [参数对照脚本 v2](evidence/engine-qualification/probe-v2.py) · [官方 wheel 哈希](evidence/engine-qualification/official-wheel-manifest.json) · [绘图溯源](evidence/engine-qualification/plot-provenance.json)

## 尚未完成的准入

`engine_versions.validate_versions` 的测试覆盖过期清单、预览版、撤回/缺失证据、绑定与原生版本不符及 extras 冲突。返回成功仍明确 `runtime_qualified: false`，目前只是元数据检查基础，还没有接入派发门禁。完整运行证据、源码/产物冻结、正式批次集成和发布前复核仍属 #41。六卡原始回执已核对，失败全部保留；不得把这组开发检查当成任务准入。

[官方 MJWarp 用法](https://mujoco.readthedocs.io/en/stable/mjwarp/index.html) · [MuJoCo 发布](https://github.com/google-deepmind/mujoco/releases/tag/3.14.0) · [MJWarp 发布](https://github.com/google-deepmind/mujoco_warp/releases/tag/v3.14.0) · [Warp 发布](https://github.com/NVIDIA/warp/releases/tag/v1.17.0)
