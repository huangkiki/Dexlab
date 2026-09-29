# DexLab

[简体中文](README.md) | [English](README.en.md)

**基于 UniLab 的机器人接触动力学实验：审查模型，量化接触行为，复现抓取结果。**

DexLab 用小而可复现的机器人任务研究仿真中的穿透、抖动、打滑与数值稳定性。当前案例是 **OpenArm 双臂 + Wuji 灵巧手抓取苹果梗**，支持官方 MuJoCo 与 SuperDex FP64 两条 SDF–SDF 动力学路径。研究重点是参数来源、碰撞与驱动模型，以及独立物理验收。

[快速运行](#运行) · [实验结果](#实验结果) · [诊断工具](#模型审查与诊断) · [研究方法](docs/research-focus.zh-CN.md) · [版本发布](https://github.com/huangkiki/Dexlab/releases)

## MuJoCo

![MuJoCo 抓梗近景](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex 抓梗近景](demos/apple-stem-grasp/media/superdex-sdf.gif)

动图连续展示完整 14 秒过程：接近 → 两指闭合 → 抬升 → 保持。仅显示抓取近景；展示相机跟随记录中的苹果，不参与控制。两个后端均由 MuJoCo 渲染器回放实际物理轨迹。[MuJoCo 视频](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex 视频](demos/apple-stem-grasp/media/superdex-sdf.mp4)

## 当前能做什么

| 能力 | 实际交付 |
|---|---|
| 双后端抓取 | 同一机器人和任务，两套原生 SDF 接触实现；逐物理步运行并保存证据 |
| 模型审查 | 导出源资产与运行时质量、质心、惯量、关节、驱动和碰撞过滤，报告初始重叠 |
| 稳定性诊断 | 位置、速度、力的 RMS/峰值与逐指接触间断；缺失数据保持未知 |
| 独立验收 | 检查完整保持过程，保留原始力与位姿记录，不靠视频判断成功 |
| Issue 驱动开发 | 自动实现、验证和审查，符合条件后合并并发布；结果可追溯至提交和日志 |

当前接入 **UniLab 任务层**。场景由 DexLab 管理，尚未采用 UniSim 内置后端；PhysX、多场景回归和真机校准的进度维护在 [Issues](https://github.com/huangkiki/Dexlab/issues)。

## 抓取细节

- 右手拇指与食指夹梗，左臂停放；苹果与梗是 **0.2 kg 的单个自由刚体**。
- 苹果、拇指指腹和食指指腹均为 **SDF 碰撞体**。没有附着约束、物体位置驱动或引擎源码补丁。
- 控制使用**已知物体位姿、逆运动学和脚本化关节目标**，不是视觉策略或学习得到的技能；无需模型 API key。
- 两个后端分别调参。MuJoCo 使用 SDF 接触点搜索与软接触约束，步长 **0.5 ms**；SuperDex 使用表面采样积分与平滑罚能，步长 **2 ms**。相同的 SDF 几何不代表相同的接触力定律。

独立验收覆盖连续 3 秒保持中的离桌、两指支撑、穿透、相对腕部位移和动量平衡；接近阶段允许果身接触。当前是单个已调优场景，不模拟梗弯曲或断裂，也没有真机精度结论。

[MuJoCo 验收](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex 验收](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [参数与引擎实现差异](docs/sdf-backends.zh-CN.md)

## 实验结果

以下为发布默认配置的单场景记录。保持窗口为 11–14 s；每个物理步均参与验收。

| 指标 | MuJoCo 3.11.0 | SuperDex 1.0.0 FP64 |
|---|---:|---:|
| 全程物理步数 | 28,000 | 7,000 |
| 保持期最小离桌高度 | 124.43 mm | 115.22 mm |
| 全程最大手部穿透 | 0.159 mm | 0.452 mm |
| 保持期相对腕部最大位移 | 0.275 mm | 0.040 mm |
| 保持期相对腕部位置去均值 RMS | 0.0786 mm | 0.0115 mm |

两者的步长、摩擦和驱动配置不同，不能据此给引擎精度排名。位移不是材料点累计滑移，去均值 RMS 仍包含缓慢漂移。完整的[验收依据](docs/sdf-backends.zh-CN.md#结果与限制)与[诊断定义](docs/jitter.zh-CN.md)说明了采样覆盖和近似。

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

## 模型审查与诊断

每次抓取运行自动导出模型审查 JSON。MuJoCo 路径同时记录原生来源与编译后参数；有意设置的无质量坐标链接与错误分开处理，报告不会静默修复模型。

```bash
# 复核模型参数，不重跑仿真
.venv/bin/python -m dexlab.model_audit \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf/model-audit.mujoco.json
# 从已有逐步记录计算抖动和接触间断
.venv/bin/python -m dexlab.jitter demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

[模型审查](docs/model-audit.zh-CN.md)解释参数与初始重叠；[抖动诊断](docs/jitter.zh-CN.md)解释载荷、缺失记录和时长上下界。报告不能证明模型已对齐真实硬件，现有记录也不足以做全系统能量收支。

## 参与研究

可复现的问题、参数实验和失败案例请提交 [Issue](https://github.com/huangkiki/Dexlab/issues)。建议附代码版本、运行命令、参数来源、原始记录与预期验收条件。自动研究只处理明确加入队列的任务，保留失败证据，不通过放宽阈值让实验过关。通过当前版本验证与审查后自动合并发版；有未解决问题时继续修复或保留阻塞。[流程与发布约定](docs/autoresearch.zh-CN.md)

## 致谢

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[OpenArm](https://github.com/enactic/openarm) 和 [Wuji](https://github.com/wuji-technology)。SuperDex 抓梗演示收录于 [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex)；Astra 参与开发与调试。

代码：[Apache-2.0](LICENSE)。第三方资产保留各自条款，见[资产来源](docs/ASSETS.zh-CN.md)。
