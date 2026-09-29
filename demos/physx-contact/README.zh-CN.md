# PhysX 接触验收

[English](README.md) | [简体中文](README.zh-CN.md)

[Issue #5](https://github.com/huangkiki/Dexlab/issues/5) 的开发实现。
运行器通过 UniSim 1.7.10 的公开实体接口调用独立的 Isaac Sim 5.1／IsaacLab 2.3.0 环境。使用下述明确披露的 UniSim 接触报告修复后，三项原生基础接触实验通过独立验收，PhysX 本身未修改。这些基础接触实验尚不能验收机器人抓取、SDF–SDF 接触或布料；受载直线关节由独立的[驱动协议](drive.zh-CN.md)验收。

## 安装与运行

先通过 `bash scripts/setup.sh` 安装 DexLab。可选环境需要 Linux x86_64、兼容 Isaac Sim 5.1 的 NVIDIA GPU／驱动、Git、C++ 编译器、CMake 与 uv。数 GB 的 SDK 位于独立 Python 3.11 环境；安装脚本还会在 DexLab 的 Python 3.12 环境安装明确披露的 UniSim 适配补丁。Torch 使用固定哈希的 CUDA 12.8 官方 wheel，普通 CUDA 依赖从 PyPI 获取。全新安装预留 35 GiB，指定 Torch 已安装时预留 25 GiB，完整审计清单中的 SDK 与 Torch 均已安装时预留 8 GiB。[SDK 体积审计](evidence/sdk-wheel-sizes.json)为压缩 4.36 GiB、解压 9.70 GiB，不含 Torch、普通依赖与运行缓存。固定 `click==8.1.7` 与 `wheel==0.45.1` 以兼容 SDK 依赖。

```bash
export UNISIM_ISAACSIM_HOME="$HOME/.cache/unisim/isaacsim"
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_baseline run --case rest --output demos/physx-contact/runs/rest
.venv/bin/python -m dexlab.physx_baseline run --case slide --output demos/physx-contact/runs/slide
.venv/bin/python -m dexlab.physx_baseline run --case slide-frictionless --output demos/physx-contact/runs/frictionless
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/runs/rest
```

每次使用新输出目录。启动错误与部分记录会保留，并给出失败判定。安装成功或场景编译成功不等于完成物理验证。

## 原生结果与适配层来源

| 实验 | 测量结果 | 验收 |
|---|---|---|
| 静置 | 平均支撑误差 0.000086%；末段速度低于 0.052 mm/s | 通过 |
| 滑动，μ = 0.3 | 停止距离 42.224 mm；库仑参考 42.474 mm | 通过 |
| 滑动，μ = 0 | 保持 0.5 m/s；2 s 移动 1.000019 m | 通过 |

每项先静置 0.5 s，再记录完整 2,000 个物理步，并检查原生质量／摩擦回读和自由／固定刚体角色。解析几何与 FP32 状态中的微小差值不代表真机精度；这里是单案例资格验证，不是成功率统计或引擎排名。

[完整记录](evidence/qualification-v1/manifest.json)包括数组、源码快照、导入报告与原始失败。无需 Isaac Sim 即可重新评分：

```bash
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/evidence/qualification-v1/rest
```

未经修改的 UniSim 1.7.10 在成对传感器初始化、物体总接触力读取两条路径上均失败，原因是导入刚体缺少 `PhysxContactReportAPI`。[五行适配层补丁](../../scripts/patches/unisim-1.7.10-physx-contact-reporting.patch)在仿真前启用报告，并更新角色缓存标识，避免复用旧 USD。原资格验证仅在上游提交 `dc41b5e79d58d9b58eba9b2f27d10d71e16cf03d` 上应用补丁，核对完整差异后构建独立包。未修改 PhysX 求解器／源码，也未放宽阈值。适配层通过 Ruff、mypy、Pyright、1,304 项测试（92 项可选运行库跳过）及打包检查；这是本地验证，不代表上游批准。

## 实验协议

质量 0.2 kg、边长 40 mm 的立方体放在水平箱体上，均使用解析盒形碰撞几何。惯量由均匀立方体公式计算，重力为 9.81 m/s²。这些是任务假设，不是真机测量。先静置 0.5 s，再以 1 ms 步长逐步记录 2 s。滑动实验只在开始时写入一次 0.5 m/s 的实际状态速度，后续被动运动；记录静／动摩擦的运行时回读。静置摩擦系数为 0.5，滑动为 0.3；零摩擦对照应保持运动。

滑动距离与理想库仑参考 `v²/(2 μ g)` 比较。根据实际位姿及解析几何独立计算盒体与平面的穿透，包含旋转影响。支撑力与该案例的 `m g` 比较，不使用固定重量。原生运行前在 `LIMITS` 冻结工程阈值：穿透小于 1 mm，平均支撑误差小于 5%，静置漂移小于 1 mm，静置／滑动末速度小于 5 mm/s，停止距离误差小于 2 mm 与 10% 中较大者，零摩擦速度误差小于 10 mm/s。

PhysX 请求位置迭代 8 次、速度迭代 2 次、接触偏移 1 mm、静止偏移为零。这是数值设置，不是材料标定。导入报告区分设置值与原生回读。成对传感器返回世界坐标系下的法向接触力，不含摩擦力；在本水平面实验中用于核对竖直支撑。每次保存实际状态、源码／适配层快照、报告／几何哈希、运行库版本及通过／失败详情。步进耗时包含 Python／IPC 观测，不是纯求解器时间；关闭渲染。

Issue 尚需机器人关节／驱动验证，再接入苹果抓取；下述理想力夹具仅覆盖基础夹持对照。基础几何结果不能证明 SDF 等价或布料能力。完整引擎比较还需要共同标定、时间／几何加密以及留出场景。

来源：[Isaac Sim 5.1 Python 安装](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html)、[固定 IsaacLab 源码](https://github.com/isaac-sim/IsaacLab/tree/3c6e67bb5c7ada942a6d1884ab69338f57596f77)、[UniSim 实体接口](https://github.com/unilabsim/unisim/blob/v1.7.10/docs/en/entity-scenes.md)。

## 受控夹持与释放

新增理想棱柱夹具：每侧实际法向载荷约 4 N，0.2 kg/μ=0.3 正常保持；0.5 kg 过载与 μ=0 两个负对照在撤去准备支撑后 200 ms 分别下落 103.39 mm、197.18 mm；完全释放后加速度接近 −9.81 m/s²。三项最终资格验证通过，第一轮行程末端读数不一致的失败保留。[协议、全部结果与复现](pinch.zh-CN.md)。

夹具仍非机器人关节/执行器或苹果抓取验证，未观测切向接触力。

## 受载关节驱动

0.1 kg 直线关节复现了 TGS 稳态位置与速度不一致。启用原生逐迭代外力选项后，通过平衡位置、静止速度、力限幅与回零检查；默认配置的失败记录保留。[协议、独立 SDK 对照及限制](drive.zh-CN.md)。当前安装脚本使用明确披露的[组合适配补丁](../../scripts/patches/unisim-1.7.10-physx-adapter.patch)，新增选项需显式开启，原有接触默认配置不变。
