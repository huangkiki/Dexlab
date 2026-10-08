# DexLab

**研究机器人如何在可信的仿真中完成接触密集操作。**

我们从标准方块抓取出发，用斜面摩擦、一维碰撞和夹持实验，检查仿真中的力、运动与接触是否符合声明的物理模型。这个仓库提供**实验结论、可复现代码和原始数据**，帮助解释物体为什么抓得住、为什么滑落，以及哪些仿真结果值得相信。

[English](README.en.md) · [实验报告](docs/site/zh/results.md) · [安装与复现](docs/installation.zh-CN.md) · [版本与数据下载](https://github.com/huangkiki/Dexlab/releases)

## 我们得出了什么结论

### 1. 碰撞后的速度正确，不代表碰撞过程准确

在官方 MuJoCo 3.15.0 的一维弹性碰撞实验中，18 个工况均通过末态判据，但接触重叠达到 **5–20 mm**。进一步改变刚度和步长后，27 个工况中有 **24 个末态通过，只有 2 个同时满足预设的 1 mm 重叠预算**。因此，评价碰撞必须同时看速度、能量和接触过程。

[弹性碰撞结果](docs/elastic-impact-results.zh-CN.md) · [刚度与穿透对照](docs/impact-stiffness-results.zh-CN.md) · [离散接触解释](docs/impact-discrete-results.zh-CN.md)

### 2. 求解更精确，不一定抓得更稳

在 MuJoCo 3.15.0 的标准方块夹持诊断中，收紧求解容差显著减小了力与运动记录之间的残差，但方块在加载一秒后仍下滑约 **2 mm**。数值力平衡改善与物体保持是两个不同结果，必须分别测量。

[夹持承载与滑移](docs/pinch-load-results.zh-CN.md) · [六个工况的残差诊断](docs/pinch-impulse-results.zh-CN.md)

### 3. 夹持力限额会改变抓取成败

在 Genesis 的固定标准方块夹具中，16 个工况显示：**0.2/0.4 N 力限额无法保持物体，0.8/10 N 能保持并释放**；在 ±2 mm 初始偏移下保持了这一结果。这给出了该夹具的可复现实验边界。

[全部工况、失败和原始记录](docs/force-limit-results.zh-CN.md)

![标准方块夹持、抬升与释放](demos/contact-benchmark/media/genesis-pinch.gif)

*上图为 Genesis 实测状态的连续近景回放，由 MuJoCo 显示；对应固定配置演示，全部力限额工况见报告。*

### 4. 一个场景调好的接触参数，不能直接当作通用材料参数

三个固定接触配置迁移到十组质量／尺寸组合后，**30 次运行均未满足指定的合成动态响应联合目标**。这说明这些参数映射的适用范围有限，需要在不同载荷和尺寸下检查。

[参数迁移实验与全部结果](demos/contact-benchmark/TRANSFER.zh-CN.md)

这些结论分别对应报告中冻结的引擎版本、模型和工况，属于解析模型与数值实验结论；真实材料精度需要实测参照。它们不能合并成引擎优劣排名。

## 从哪里开始

- **看结论与图表：** [完整实验报告](docs/site/zh/results.md)，以及[阶段总结](docs/holiday-report.zh-CN.md)。
- **复算结果：** 每份报告链接冻结协议、评分代码和原始记录；公开归档见 [Releases](https://github.com/huangkiki/Dexlab/releases)。
- **运行演示：** 按[安装说明](docs/installation.zh-CN.md)配置环境后，运行下方苹果梗抓取示例。

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或 --backend superdex；无显示环境添加 --headless
```

演示的 SDF 构建和规划完成后打开窗口，无需模型 API key。各研究实验的版本与运行命令以对应报告为准。

后续工作、未完成任务和阻塞统一在 [Issues](https://github.com/huangkiki/Dexlab/issues) 跟踪。

## 代码与来源

实验使用官方物理引擎，保留参数来源、失败工况与独立评分。[实验目录](demos/) · [开发流程](docs/autoresearch.zh-CN.md) · [资产来源与许可](docs/ASSETS.zh-CN.md)

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[Genesis](https://github.com/Genesis-Embodied-AI/Genesis)、[Newton](https://github.com/newton-physics/newton)、[OpenArm](https://github.com/enactic/openarm) 与 [Wuji](https://github.com/wuji-technology)。代码采用 [Apache-2.0](LICENSE)。
