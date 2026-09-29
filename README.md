# DexLab

[简体中文](README.md) | [English](README.en.md)

**机器人接触动力学与布料仿真的可复现实验。**

DexLab 使用 UniLab 组织实验，研究碰撞、摩擦、驱动与数值求解对仿真结果的影响。以参数来源、独立验收和计算成本为依据，逐步建立从简单接触到机器人操作的基准。

[运行](#运行) · [基准协议](docs/benchmark.zh-CN.md) · [后端实现](docs/sdf-backends.zh-CN.md) · [Issues](https://github.com/huangkiki/Dexlab/issues) · [Releases](https://github.com/huangkiki/Dexlab/releases)

## 抓梗实验

OpenArm 双臂与 Wuji 灵巧手；右手拇指和食指夹住苹果梗，抬升并保持。苹果与梗是同一个自由刚体，两个指腹与苹果均使用 SDF 碰撞，无附着约束或引擎源码修改。控制输入为已知物体位姿与脚本化关节目标。

### MuJoCo

![MuJoCo 抓梗近景](demos/apple-stem-grasp/media/mujoco-sdf.gif)

### SuperDex

![SuperDex 抓梗近景](demos/apple-stem-grasp/media/superdex-sdf.gif)

连续 14 秒物理轨迹：接近、闭合、抬升、保持。两段轨迹均由 MuJoCo 回放渲染；展示相机不参与控制。[视频与来源](demos/apple-stem-grasp/README.zh-CN.md)

## 实验与后端

| 实验 / 后端 | 当前交付 |
|---|---|
| MuJoCo 3.11.0 · 原生 SDF | 单场景完整抓取验收；冻结场景与步长研究 |
| SuperDex 1.0.0 FP64 · 原生 SDF | 单场景完整抓取验收；冻结场景与步长研究 |
| PhysX / IsaacSim | [接入与物理验证 #5](https://github.com/huangkiki/Dexlab/issues/5) |
| Newton 与其他 UniSim 后端、求解器 | [运行时与能力验证 #11](https://github.com/huangkiki/Dexlab/issues/11) |
| 简单接触：压入、滑动、夹持、释放 | [基准实验 #10](https://github.com/huangkiki/Dexlab/issues/10) |
| 布料：拉伸、下垂、悬垂接触 | [独立实验组 #12](https://github.com/huangkiki/Dexlab/issues/12) |

MuJoCo 以 SDF 接触搜索生成软约束；SuperDex 在表面采样点积分平滑罚力与摩擦。两者的步长、驱动及接触参数分别配置；现有苹果结果属于任务验收，不能作为引擎精度排名。[参数、量化结果与近似](docs/sdf-backends.zh-CN.md)

当前苹果实验复用 UniLab 任务生命周期，仍由 DexLab 管理原生场景。UniSim 内置适配器的等价性单独验证；上表中的跟踪项不代表后端已经通过实验。

## 运行

Linux x86_64，安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后：

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
bash demos/apple-stem-grasp/run.sh --backend superdex
```

服务器添加 `--headless`；无需模型 API key。[环境安装](docs/installation.zh-CN.md) · [任务与独立验收](demos/apple-stem-grasp/README.zh-CN.md)

```bash
# 重跑同一组冻结场景；保留失败与原始记录
.venv/bin/python -m dexlab.benchmark run --split regression \
  --output demos/apple-stem-grasp/runs/regression-v1
```

## 评价方法

- 简单实验核查预期物理行为：能支撑，也能在超载时滑动、松手后释放。
- 任务实验使用冻结的开发、回归和测试场景；独立报告全部成功与失败。
- 分别记录穿透、保持漂移、接触支撑、数值稳定性与运行成本。布料使用独立的形变与接触指标。
- 固定参数来源、运行库、场景和评分版本。解析参照、数值收敛与真实测量分开报告。

当前没有真机材料标定或视觉自主抓取结论。[基准协议与命令](docs/benchmark.zh-CN.md) · [模型审查](docs/model-audit.zh-CN.md) · [抖动诊断](docs/jitter.zh-CN.md)

## 开发与致谢

研究任务维护在 Issues；autodev 按任务实现、验证、审查，通过后合并发版。[开发流程](docs/autoresearch.zh-CN.md)

感谢 [UniLab / UniSim](https://github.com/unilabsim/UniLab)、[SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[OpenArm](https://github.com/enactic/openarm) 和 [Wuji](https://github.com/wuji-technology)。抓梗演示收录于 [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex)。

代码：[Apache-2.0](LICENSE)。[第三方资产来源与条款](docs/ASSETS.zh-CN.md)。
