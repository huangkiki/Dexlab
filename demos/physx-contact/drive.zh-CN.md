# PhysX 受载关节驱动

[English](drive.md) | [简体中文](drive.zh-CN.md)

历史配置归因见[分批求解器与版本审计](../../docs/physx-solver-audit.zh-CN.md)：区分原生场景读回、源码／报告中的 TGS 配置和缺失字段；[P0 #126](https://github.com/huangkiki/Dexlab/issues/126) 保留同期核心／加载库身份缺口。

固定基座的单自由度直线关节通过 UniSim 调用官方 Isaac Sim 5.1。启用原生 TGS 逐迭代外力选项后，完整 2 秒记录通过独立验收。默认选项未通过静止速度检查，失败记录保留。此结果限于理想直线关节，尚未验证 OpenArm/Wuji 机器人驱动、接触中的驱动或苹果抓取。

## 发现与原生对照

在 1 N 恒定外载下，位置应在 `0.01 − 1/500 = 0.008 m` 附近达到平衡。默认 TGS 中位置不再变化，但报告速度约 4.29 mm/s。完全绕过 DexLab、UniSim 和 MJCF 转换器，以 USD 直接创建同一关节，结果相同；IsaacLab 缓存与原生 PhysX 张量读数逐样本完全一致。

| 独立 SDK 配置 | 稳态位置均值 | 报告速度均值 |
|---|---:|---:|
| TGS，默认外力时序 | 8.000806 mm | 4.293650 mm/s |
| TGS，每次位置迭代施加外力 | 7.999971 mm | 0.001418 mm/s |
| PGS 对照 | 8.000002 mm | −0.000115 mm/s |

PhysX 官方说明了 TGS 外力一次施加、弹簧力分子步施加导致的稳态位置／速度差异，以及 `enableExternalForcesEveryIteration` 的作用。[官方机制说明](https://nvidia-omniverse.github.io/PhysX/physx/5.7.0/docs/Simulation.html#tgs-steady-state-velocity-and-position-discrepancy)。这支持上述最小实验的归因，不表示其他场景均已解决；表中微小差值也不代表真实硬件精度。

## 协议与参数来源

- 运动质量 0.1 kg；固定基座；无接触、无重力、无附着或运行中状态重置。惯量来自均匀盒形几何。
- 原生隐式位置驱动：`kp=500 N/m`、`kd=10 N·s/m`、最大力 2 N、行程 ±20 mm；目标先为 10 mm，1.5 s 时回到零。
- 外载在 [0.5, 1.0) s 为 −1 N，[1.0, 1.04) s 为 −3 N，其余为零。
- 物理步长 1 ms，位置／速度迭代 8/2；逐步保存实际关节和刚体状态，共 2,000 步。

上述均为独立定义的工程测试参数，不是机器人电机标定值。验收容差在资格运行前冻结：平衡位置误差 <50 μm、静止速度 <0.1 mm/s、关节与刚体位置误差 <1 μm、速度差 <1 μm/s。短时过载区间依据 `m a − F_external` 推算的驱动力需在 2 N ±0.05 N 内；它不是原生驱动力传感器读数，也未覆盖完整电机特性。

原生默认外力时序仅失败于受载静止速度；逐迭代模式通过全部 21 项检查，过载推算驱动力为 2.000002 N。新增适配项默认不启用；原有静置、滑动、零摩擦、夹持、过载和释放六项实验在新适配包上重新运行，均通过原阈值。

## 实现与复现

[组合适配补丁](../../scripts/patches/unisim-1.7.10-physx-adapter.patch)保留接触报告修复，并增加公开参数 `isaacsim_external_forces_every_iteration`。参数经主进程、工作进程布尔校验，在初始化前写入原生场景，随后核对 USD 读回。`None` 保持 SDK 默认；`False` 显式关闭；`True` 启用。不修改 PhysX 源码或二进制。

安装脚本默认使用新的 `UniSim-physx-drive` 源码目录，保留旧适配源码。若显式配置 `DEXLAB_UNISIM_SOURCE`，必须使用固定上游提交及与新补丁完全一致的工作树。适配包通过 Ruff、mypy、Pyright、1,313 项测试（92 项可选 SDK 跳过）和打包；已有环境的安装脚本重放通过，全新机器安装未重新验证。

```bash
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_drive run --force-timing substep \
  --output demos/physx-contact/runs/drive-substep
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/runs/drive-substep
# 保留默认配置对照；当前预计退出码为 1，不能改写成通过
.venv/bin/python -m dexlab.physx_drive run --force-timing default \
  --output demos/physx-contact/runs/drive-default
```

[完整证据及 SHA-256 清单](evidence/drive-v1/manifest.json)包括两项驱动资格记录、六项接触回归、三个独立 SDK 对照、源码快照、USD 场景和日志。日志与导出的 USD 场景使用无损 gzip，清单另记解压后哈希。最早的独立 SDK 场景漏建 `DriveAPI`，属于无效夹具，不能用它评价引擎；原始记录及退出处置说明均保留。后续有效场景均明确创建原生驱动。

```bash
# 不启动 SDK，复核打包的通过和失败记录
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/evidence/drive-v1/qualification/substep
.venv/bin/python -m dexlab.physx_drive verify demos/physx-contact/evidence/drive-v1/qualification/default
```
