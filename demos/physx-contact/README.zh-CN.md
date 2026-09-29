# PhysX 接触验收

[English](README.md) | [简体中文](README.zh-CN.md)

[Issue #5](https://github.com/huangkiki/Dexlab/issues/5) 的开发实现。
运行器通过 UniSim 1.7.10 的公开实体接口调用独立的 Isaac Sim 5.1／IsaacLab 2.3.0 工作环境。原生 PhysX 验证尚未完成，不宣称已实现 PhysX 苹果梗抓取或 SDF–SDF 接触。

## 安装与运行

先通过 `bash scripts/setup.sh` 安装 DexLab。可选工作环境需要 Linux x86_64、兼容 Isaac Sim 5.1 的 NVIDIA GPU／驱动、Git、C++ 编译器、CMake 与 uv。下载量为数 GB，独立于默认苹果演示；不更改主 Python 3.12 环境。Torch 使用按哈希固定的 CPython 3.11／CUDA 12.8 官方 wheel，普通 CUDA 依赖从 PyPI 获取。全新安装预留 35 GiB 空间，三个指定 Torch 包均已安装时预留 25 GiB。这是安装余量，不是 SDK 大小：[固定 SDK wheel 的体积审计](evidence/sdk-wheel-sizes.json)为压缩 4.36 GiB、解压 9.70 GiB，不含 Torch、普通依赖与运行缓存。

```bash
export UNISIM_ISAACSIM_HOME="$HOME/.cache/unisim/isaacsim"
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_baseline run --case rest --output demos/physx-contact/runs/rest
.venv/bin/python -m dexlab.physx_baseline run --case slide --output demos/physx-contact/runs/slide
.venv/bin/python -m dexlab.physx_baseline run --case slide-frictionless --output demos/physx-contact/runs/frictionless
.venv/bin/python -m dexlab.physx_baseline verify demos/physx-contact/runs/rest
```

每次使用新输出目录。启动错误与部分记录会保留，并给出失败判定。安装成功或场景编译成功不等于完成物理验证。

## 实验协议

质量 0.2 kg、边长 40 mm 的立方体放在水平箱体上，均使用解析盒形碰撞几何。惯量由均匀立方体公式计算，重力为 9.81 m/s²。这些是任务假设，不是真机测量。先静置 0.5 s，再以 1 ms 步长逐步记录 2 s。滑动实验只在开始时写入一次 0.5 m/s 的实际状态速度，后续被动运动；记录静／动摩擦的运行时回读。静置摩擦系数为 0.5，滑动为 0.3；零摩擦对照应保持运动。

滑动距离与理想库仑参考 `v²/(2 μ g)` 比较。根据实际位姿及解析几何独立计算盒体与平面的穿透，包含旋转影响。支撑力与该案例的 `m g` 比较，不使用固定重量。原生运行前在 `LIMITS` 冻结工程阈值：穿透小于 1 mm，平均支撑误差小于 5%，静置漂移小于 1 mm，静置／滑动末速度小于 5 mm/s，停止距离误差小于 2 mm 与 10% 中较大者，零摩擦速度误差小于 10 mm/s。

PhysX 请求位置迭代 8 次、速度迭代 2 次、接触偏移 1 mm、静止偏移为零。这是待验证的数值设置，不是材料标定。适配器导入报告区分设置值与原生回读。每次保存实际状态和接触力、源码快照与哈希、几何哈希、运行库版本、配置报告及通过／失败详情。步进耗时包含 Python／IPC 观测，不是纯求解器时间；关闭渲染。

Issue 尚需完成带负对照的法向力控制夹持、机器人关节／驱动验证，再接入苹果抓取。基础几何结果不能证明 SDF 等价或布料能力。完整引擎比较还需要共同标定、时间／几何加密以及留出场景。

来源：[Isaac Sim 5.1 Python 安装](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_python.html)、[固定 IsaacLab 源码](https://github.com/isaac-sim/IsaacLab/tree/3c6e67bb5c7ada942a6d1884ab69338f57596f77)、[UniSim 实体接口](https://github.com/unilabsim/unisim/blob/v1.7.10/docs/en/entity-scenes.md)。
