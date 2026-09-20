# DexLab

[简体中文](README.md) | [English](README.en.md)

**OpenArm + Wuji 灵巧手，在 MuJoCo 与 SuperDex 中夹住苹果梗、抬升并保持。**

## MuJoCo

![MuJoCo 抓梗近景](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex 抓梗近景](demos/apple-stem-grasp/media/superdex-sdf.gif)

动图连续展示完整 14 秒过程：接近 → 两指闭合 → 抬升 → 保持。仅显示抓取近景；展示相机跟随记录中的苹果，不参与控制。两个后端均由 MuJoCo 渲染器回放实际物理轨迹。[MuJoCo 视频](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex 视频](demos/apple-stem-grasp/media/superdex-sdf.mp4)

## 抓取细节

- 右手拇指与食指夹梗，左臂停放；苹果与梗是 **0.2 kg 的单个自由刚体**。
- 苹果、拇指指腹和食指指腹均为 **SDF 碰撞体**。没有附着约束、物体位置驱动或引擎源码补丁。
- 控制使用**已知物体位姿、逆运动学和脚本化关节目标**，不是视觉策略或学习得到的技能；无需模型 API key。
- 两个后端分别调参。MuJoCo 使用 SDF 接触点搜索与软接触约束，步长 **0.5 ms**；SuperDex 使用表面采样积分与平滑罚能，步长 **2 ms**。相同的 SDF 几何不代表相同的接触力定律。

独立验收覆盖连续 3 秒保持中的离桌、两指支撑、穿透、相对腕部位移和动量平衡；接近阶段允许果身接触。当前是单个已调优场景，不模拟梗弯曲或断裂，也没有真机精度结论。

[MuJoCo 验收](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex 验收](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [参数与引擎实现差异](docs/sdf-backends.zh-CN.md)

## 运行

Linux x86_64，先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或者
bash demos/apple-stem-grasp/run.sh --backend superdex
```

SDF 构建和规划完成后打开窗口；服务器添加 `--headless`。两条命令均通过 **UniLab 注册任务 `DexLab-AppleStem-v0`** 的逐步接口运行；当前原生 SDF 场景由 DexLab 管理，尚未替换为 UniSim 内置后端。

[安装](docs/installation.zh-CN.md) · [任务接口与复现](demos/apple-stem-grasp/README.zh-CN.md) · [自动研究与 issues](docs/autoresearch.zh-CN.md)

## 致谢

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[OpenArm](https://github.com/enactic/openarm) 和 [Wuji](https://github.com/wuji-technology)。SuperDex 抓梗演示收录于 [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex)；Astra 参与开发与调试。

代码：[Apache-2.0](LICENSE)。第三方资产保留各自条款，见[资产来源](docs/ASSETS.zh-CN.md)。
