# DexLab

[简体中文](README.md) | [English](README.en.md)

**基于 UniLab 的机器人接触动力学实验：审查模型，量化接触行为，复现抓取结果。**

DexLab 用可复现的刚体抓取和布料实验研究穿透、抖动、打滑与数值稳定性。案例包括 **OpenArm 双臂 + Wuji 灵巧手抓苹果梗、夹布**，以及多求解器的布料拉伸、下垂和碰撞测试。每项实验保留参数来源、原始轨迹、独立验收及失败记录。

[快速运行](#运行) · [实验结果](#实验结果) · [诊断工具](#模型审查与诊断) · [研究方法](docs/research-focus.zh-CN.md) · [版本发布](https://github.com/huangkiki/Dexlab/releases)

## MuJoCo

![MuJoCo 抓梗近景](demos/apple-stem-grasp/media/mujoco-sdf.gif)

## SuperDex

![SuperDex 抓梗近景](demos/apple-stem-grasp/media/superdex-sdf.gif)

## PhysX

![PhysX 抓梗近景](demos/physx-contact/media/physx-sdf.gif)

动图连续展示完整 14 秒过程：接近 → 两指闭合 → 抬升 → 保持。展示相机跟随记录中的苹果，不参与控制；MuJoCo 渲染器回放各引擎的实际位姿。[MuJoCo 视频](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex 视频](demos/apple-stem-grasp/media/superdex-sdf.mp4) · [PhysX 视频与复现](demos/physx-contact/apple.zh-CN.md)

## 机器人夹布

![Wuji 夹布、抬升与释放近景](demos/cloth-folding/media/grasp.gif)

MuJoCo flex 布料与 Wuji 手通过摩擦接触完成夹持、抬升和释放；连续 9 秒记录，独立验收通过。此任务使用已知状态与脚本控制，机器人碰撞体采用凸网格近似；未使用布料附着约束。双臂折叠仍未通过。[视频与物理指标](demos/cloth-folding/README.zh-CN.md)

## 引擎与实验

| 原生配置 | 当前验证范围 |
|---|---|
| MuJoCo 3.11.0 | SDF–SDF 抓梗、flex 布料、机器人摩擦夹布 |
| SuperDex 1.0.0 FP64 | SDF–SDF 抓梗、实验性三角薄壳 |
| Newton XPBD / VBD / Style3D / SemiImplicit / Featherstone | 固定上游版本的布料实验；各求解器的材料与自接触能力分别记录 |
| PhysX / Isaac Sim 5.1 | [SDF–SDF 抓梗](demos/physx-contact/apple.zh-CN.md)、[基础接触与驱动](demos/physx-contact/README.zh-CN.md)、[54 关节运动](demos/physx-contact/robot.zh-CN.md)；独立表面复核通过，失败对照保留；[原生表面布料](demos/physx-contact/cloth.zh-CN.md) |

布料基准已完成 **105 次冻结留出实验：52 次通过协议检查、53 次失败，无超时**。覆盖拉伸、下垂、球面覆盖和折叠下落；名义材料尚未完成跨求解器校准，不按通过数排名真实精度。[全部结果与运行方法](demos/cloth-benchmark/README.zh-CN.md#留出结果)

PhysX 原生表面布料另完成 **15 个冻结留出场景：10 通过、1 表面相交失败、4 外力拉伸不支持**。9 次开发场景细化中 8 次通过；重复运行与加密网格的失败均保留。[结果、动图与原始证据](demos/physx-contact/cloth.zh-CN.md)

接触力学开发实验覆盖滑动、压入/卸载和双指载荷扫描。原始失败完整保留；相同圆柱表面细化后，SuperDex 的四种夹持/滑落条件通过开发检查。材料响应尚未跨引擎校准。[实验、失败与复现](demos/contact-benchmark/README.zh-CN.md)。

法向加载另完成 17 次开发检查，11 通过、6 失败；静态斜率匹配后，质量迁移与保持波动仍需分别验证。[响应标定与失败记录](demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md)。

苹果 SDF 抓取通过 **UniLab** 注册和逐步执行，原生场景由 DexLab 管理；PhysX 刚体实验使用 **UniSim 的 Isaac Sim 后端**，独立布料任务复用其运行环境。刚体与布料分别评分；未完成或不支持的能力明确标记。

## 抓取细节

- 右手拇指与食指夹梗，左臂停放；苹果与梗是 **0.2 kg 的单个自由刚体**。
- 苹果、拇指指腹和食指指腹均为 **SDF 碰撞体**。没有附着约束、物体位置驱动或引擎源码补丁。
- 控制使用**已知物体位姿、逆运动学和脚本化关节目标**，不是视觉策略或学习得到的技能；无需模型 API key。
- 各后端分别调参。MuJoCo 使用 SDF 接触搜索与软约束，步长 **0.5 ms**；SuperDex 使用表面采样积分与平滑罚能，步长 **2 ms**；PhysX 使用原生 SDF 接触与 TGS，步长 **1 ms**，显式配置扭转接触半径。相同源表面不代表相同的离散几何或接触力定律。

独立验收覆盖连续 3 秒保持中的离桌、两指支撑、穿透、相对腕部位移和动量平衡；接近阶段允许果身接触。动图对应默认场景；不模拟梗弯曲或断裂，也没有真机精度结论。

[MuJoCo 验收](demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex 验收](demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [参数与引擎实现差异](docs/sdf-backends.zh-CN.md)

## 实验结果

苹果抓梗已完成 **10 个冻结场景、两个后端共 20 次实验**。扰动质量、水平位置与朝向；沿用已发布策略，未针对这些场景重新调参。

| 配置 | 完整验收通过 | 成功率 95% Wilson 区间 |
|---|---:|---:|
| MuJoCo 3.11.0，0.5 ms | 1 / 10 | 1.8–40.4% |
| SuperDex 1.0.0 FP64，2 ms | 10 / 10 | 72.2–100% |

这是各自配置的任务鲁棒性结果，**不构成引擎精度排名**。全部失败和原始证据均保留；另完成 6 次步长实验，MuJoCo 0.25 ms 因穿透超限失败，更小步长未呈现单调改善。100 个正式测试场景已冻结，尚未完成评估。

PhysX 当前通过单个开发场景的抓梗验收，尚未纳入上述留出测试。其原生接触距离与独立参考表面穿透分别报告。[参数、失败与测量边界](demos/physx-contact/apple.zh-CN.md)

[基准协议、全部结果与复现](docs/benchmark.zh-CN.md) · [演示默认场景指标](docs/sdf-backends.zh-CN.md#结果与限制) · [诊断定义](docs/jitter.zh-CN.md)

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

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[Newton](https://github.com/newton-physics/newton)、[OpenArm](https://github.com/enactic/openarm) 和 [Wuji](https://github.com/wuji-technology)。SuperDex 抓梗演示收录于 [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex)；Astra 参与开发与调试。

代码：[Apache-2.0](LICENSE)。第三方资产保留各自条款，见[资产来源](docs/ASSETS.zh-CN.md)。
