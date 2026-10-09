# DexLab

**以经典物理规律与已有经验公式为参照，通过可复现实验，研究接触与摩擦对机器人抓取的影响，评估物理仿真的可信度。**

我们用斜面摩擦、一维碰撞和夹持实验，对照解析解、守恒律及有来源的经验关系，检查仿真中的力、运动与接触。这个仓库提供**实验结论、可复现代码和原始数据**，分析哪些可测因素影响抓取表现，并明确结论的适用条件。

[English](README.en.md) · [中文文档站](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [实验报告](docs/site/zh/results.md) · [安装与复现](docs/installation.zh-CN.md) · [版本与数据下载](https://github.com/huangkiki/Dexlab/releases)

文档站按每次 main 合并自动更新；首页提供实验结论、同工况对照与六引擎覆盖状态。

## 现在能做哪些任务

按任务选择运行入口，再查看对应协议、环境和结果。下表记录 **DexLab 已实现并保留证据的范围**；“已运行”包含失败，“通过”只覆盖报告指定的版本、配置和场景。

| 任务 | 已有引擎与验证状态 | 运行与证据入口 |
|---|---|---|
| 斜面摩擦、一维碰撞 | MuJoCo／SuperDex 已有斜面配对，含通过与失败；一维碰撞已有 MuJoCo 记录 | [斜面对照](docs/incline-comparison-results.zh-CN.md) · [碰撞](docs/elastic-impact-results.zh-CN.md) |
| 平面滑动、法向加载／卸载、圆柱夹持 | MuJoCo／SuperDex／PhysX 已运行开发案例，保留失败与几何细化结果 | [接触实验与命令](demos/contact-benchmark/README.zh-CN.md) |
| 有限夹具夹持、抬升、保持与释放 | Genesis 已完成 16 个力限额工况；可研究驱动力与失败机制 | [力限额结果与复现](docs/force-limit-results.zh-CN.md) |
| 机器人 SDF 苹果梗抓取 | MuJoCo／SuperDex 已通过指定 14 s 场景；PhysX 有独立单场景验收，配置与准备链分别披露 | [MuJoCo／SuperDex](demos/apple-stem-grasp/README.zh-CN.md) · [PhysX](demos/physx-contact/apple.zh-CN.md) |
| 布料拉伸、下垂、球面覆盖、预折叠下落 | MuJoCo flex／SuperDex shell／Newton Physics 有历史实验，包含失败；PhysX 表面布料另有被动实验，逐节点外力拉伸不支持 | [布料基准](demos/cloth-benchmark/README.zh-CN.md) · [PhysX 范围](demos/physx-contact/cloth.zh-CN.md) |
| 机器人夹布、抬升与释放 | MuJoCo 3.14 的指定 9 s 开发案例通过有限协议；自接触接近阈值，尚无稳健性结论 | [通过配置、失败与命令](demos/cloth-folding/SETTLING.zh-CN.md) |
| 刚体球—平面基础接触 | Newton Physics 1.6.1 / XPBD 的正常、重复及禁碰撞对照完成准入；未覆盖机器人抓取 | [协议、记录与复核](docs/newton-contact.zh-CN.md) |

双手折布尚未证明成功。Drake 1.57.0 首轮斜面九例中六例通过、三例滑动失败，负例正确拒绝；[完整记录](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.zh-CN.md)。统一驱动接入差异已由 [#143](https://github.com/huangkiki/Dexlab/issues/143) 验证，完整研究批次仍见 [#130](https://github.com/huangkiki/Dexlab/issues/130)。

**我们的评价标准：更好的引擎，应能可靠覆盖更多类型的任务。** 我们同时看任务类型、物理可信度、跨工况稳定性和执行成本：能在保留判据的前提下可靠完成更多任务类型，才扩大该配置的已验证能力。安装成功、适配器声明、同一任务的多个求解器或重复运行都不增加任务类型；历史不同协议的通过数不合并成通用排行榜。

## 不同 solver 的任务覆盖度

MuJoCo 3.15.0 首轮六配置：elliptic 各 3/9，pyramidal 各 0/9；六个负例正确拒绝。CG／Newton 的 pyramidal 路径各有三例力–状态一致性失败，均保留为无效记录。 [详细证据 / Evidence](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.zh-CN.md).

SuperDex 1.0.0 FP64 的十二组斜面配置中，九组 8/9、三种 CG 路径各 6/9；全部负例正确拒绝，五个 CUDA 选项在官方构建中不支持。失败与历史缺失完整保留。 [Evidence / 详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.zh-CN.md).

BFGS／SR1 保留每步重组装的设置，实际执行等价 Newton 步骤；这些是配置记录，不能算额外验证了两种算法。

Genesis 1.4.3 原生斜面五组配置分别为 6/9、3/9、0/9、0/9、0/9；名义零摩擦被原生接触抬至 .01，七条 CG 一致性失败全部保留并完成停止条件诊断。 [Evidence / 详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.zh-CN.md).

Newton Physics 1.6.1 原生斜面七配置通过数为 1/9、0/9、0/9、0/9、0/9、1/9、4/9；49 条正例及两个 VBD 负例未通过数值检查。DVI 超时与单独续接均保留；不据此声称引擎排名或可靠覆盖。 [详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.zh-CN.md)。

<!-- task-coverage:start -->

状态：完整通过 / 部分通过 / 失败 / 未运行 / 接入受阻 / 不支持。点击单元格查看证据或恢复条件。

**历史协议分别展示；通过只表示该协议的验收。** 新协议可靠覆盖须完成正例、负例、独立物理评分和冻结留出验证，并保持相同调优预算。

### 刚体任务 · 历史协议

| 引擎核心 / solver / 路径 / 版本 / 批次 | 基础接触 | 斜面 | 碰撞 | 夹具夹持 | 机器人抓取 |
| --- | --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · PGS / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-pgs-elliptic-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · PGS / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-pgs-pyramidal-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · CG / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-cg-elliptic-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · CG / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-cg-pyramidal-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · Newton / elliptic / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-newton-elliptic-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · Newton / pyramidal / Euler**<br>native CPU FP64 · 3.15.0<br>mujoco-incline-newton-pyramidal-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / approximate_implicitfast**<br>UniSim 1.7.12 + disclosed local patch · 1.4.3<br>genesis-contact-migration-v4 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/unisim-contact-migration.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · historical readback incomplete (#126)**<br>SDK historical · historical core identity unrecovered (#126)<br>rigid-history | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kLagged / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-incline-qualification-v2 | [未运行](https://github.com/huangkiki/Dexlab/issues/151) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/151) | [未运行](https://github.com/huangkiki/Dexlab/issues/151) | [未运行](https://github.com/huangkiki/Dexlab/issues/151) |
| **MuJoCo · Newton / implicitfast**<br>native · 3.11.0<br>apple-sdf-14s | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |
| **SuperDex · Newton / GMRES / FP64**<br>native · 1.0.0<br>apple-sdf-14s | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |
| **SuperDex · NEWTON / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-auto-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-cg-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / GMRES / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-gmres-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / AUGMENTED_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-augmented-cg-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / LDLT / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-ldlt-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / LU / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-lu-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / ASYNC_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-async-cg-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / PARALLEL_CG / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-parallel-cg-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / MINRES / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-minres-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · BFGS / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-bfgs-auto-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · SR1 / AUTO / C1_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-sr1-auto-c1-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / AUTO / CINF_REGULARIZED**<br>native CPU FP64 · 1.0.0<br>superdex-incline-newton-auto-cinf-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 8/9](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CUDA_CG / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / CUDA_GMRES / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_CHOLESKY / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_LDLT / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · NEWTON / EXPERIMENTAL_CUDA_SPARSE_LU / C1_REGULARIZED**<br>official FP64 wheel, CUDA disabled · 1.0.0<br>superdex-incline-cuda-unavailable-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / elliptic / signorini / approximate_implicitfast**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-incline-v1-newton-elliptic-signorini | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / elliptic / convex / approximate_implicitfast**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-incline-v1-newton-elliptic-convex | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / pyramidal / convex / approximate_implicitfast**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-incline-v1-newton-pyramidal-convex | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · CG / elliptic / convex / approximate_implicitfast**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-incline-v1-cg-elliptic-convex | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · CG / pyramidal / convex / approximate_implicitfast**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-incline-v1-cg-pyramidal-convex | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / pyramidal / Signorini**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-signorini-unsupported-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · CG / elliptic / Signorini**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-signorini-unsupported-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · CG / pyramidal / Signorini**<br>native CPU FP64 / Quadrants 1.3.3 · 1.4.3<br>genesis-signorini-unsupported-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · XPBD / 100 sweeps**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-xpbd | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 1/9](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · SemiImplicit**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-semiimplicit | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · Featherstone**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-featherstone | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · VBD legacy / 100 sweeps**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-vbd-legacy | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9；负例无效](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · VBD compliant / 100 sweeps**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-vbd-compliant | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9；负例无效](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · Kamino / PADMM / Euler**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-kamino-padmm | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 1/9](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · Kamino / DVI / Euler**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>newton-incline-v1-kamino-dvi | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 4/9](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · Style3D**<br>native particle solver · 1.6.1 / Warp 1.18.0<br>newton-incline-particle-scope-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · ImplicitMPM**<br>native particle solver · 1.6.1 / Warp 1.18.0<br>newton-incline-particle-scope-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [不支持](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · SolverMuJoCo; algorithm unqualified**<br>Newton wrapper / unqualified · Newton 1.6.1; MuJoCo core unqualified<br>newton-mujoco-wrapper-unqualified | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |

### 操作任务 · 历史协议与缺项

| 引擎核心 / solver / 路径 / 版本 / 批次 | 推动 | 手内旋转 | 夹布抬升 | 主动折布 |
| --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **PhysX · pending qualification**<br>ManiSkill / SAPIEN · official combination pending #47<br>rigid-history | [接入受阻](https://github.com/huangkiki/Dexlab/issues/47) | [接入受阻](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Drake · SAP / kLagged / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-incline-qualification-v2 | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **MuJoCo · Newton / implicitfast**<br>native · 3.14.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Genesis · PBD / rigid coupling**<br>native CPU FP64 · 1.4.3<br>genesis-cloth-diagnostic | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [失败](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |

### 布料任务 · 历史协议分别展示

| 引擎核心 / solver / 路径 / 版本 / 批次 | 拉伸 | 下垂 | 球面覆盖 | 预折叠下落 |
| --- | --- | --- | --- | --- |
| **MuJoCo · Newton**<br>native cpu float64 · 3.11.0<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **SuperDex · experimental-shell**<br>native cpu float64 · 1.0.0<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [部分通过 3/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · xpbd**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · vbd**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · semi_implicit**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · featherstone**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Newton Physics · style3d**<br>native cpu float32 · 1.7.0.dev0 @ 2dee3234<br>cloth-heldout-v1 | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [完整通过 4/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [失败 0/4](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) | [部分通过 1/3](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json) |
| **Genesis · PBD / rigid coupling**<br>native CPU FP64 · 1.4.3<br>genesis-cloth-diagnostic | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Drake · not qualified**<br>native · not qualified<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **PhysX · surface cloth**<br>Isaac Sim 5.1.0.0 / IsaacLab 0.47.2 · historical core identity unrecovered (#126)<br>physx-cloth-final-v2 | [不支持](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) |

**新协议可靠覆盖：尚未验收。** 这不表示已有引擎不能完成任务；历史结果不自动追认为新协议结果。

布料数字从 105 份历史摘要逐例重算，不等于重新评分完整轨迹。Featherstone 布料使用半隐式粒子核；预折叠下落不是主动折布。缺少实验不等于不支持。

[清单与生成规则](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.zh-CN.md)

<!-- task-coverage:end -->

Genesis 1.4.3 PBD 的驱动夹布／保持工况已运行并失败，见[保留的负面结果](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md)。其平面支撑、伸展／弯曲响应及连通折叠诊断不等于表中七种配置的共同布料留出协议。


下一步按[覆盖优先开发计划](https://github.com/huangkiki/Dexlab/blob/main/docs/task-coverage.zh-CN.md)推进：迁移差异 → 各引擎独立基础实验 → 原生 MJWarp／Isaac Sim 对照 → 推动、旋转与布料；夹持 594 回合研究穿插推进。原生用最新稳定版，框架用官方兼容组合，归因对照另做核心版本匹配。

接触路径对照已找到低力差异的配置来源：24 进程原生诊断隔离了参数批存储因素，随后对齐存储的 38 次启动／56 回合通过全部 19 组对照与 12 项精确重放，原误差阈值不变。旧版六组失败和低力抓取失败均保留。该结果限定于显式披露的 Genesis 1.4.3／本地适配补丁组合，不增加任务类型数。[原因、证据与复现](docs/unisim-contact-migration.zh-CN.md) · [#143](https://github.com/huangkiki/Dexlab/issues/143)。

## 引擎、求解器与版本

下表区分**已有证据**与**同工况对照**；不同任务、版本的结果不能拼成统一排名。版本是报告中的实测版本，不代表当前最新版。

| 引擎 / 运行版本 | 求解器与数值配置 | 已有证据范围 |
|---|---|---|
| MuJoCo 3.15.0 | Newton 求解器；Euler 积分；elliptic 摩擦锥；100 次迭代上限，容差 1e-10 | 下方九组斜面配对，以及碰撞、夹持诊断 |
| SuperDex 1.0.0 FP64 | 同字节配置重建：Newton、线性 AUTO（小系统源码路径为稠密 LDLᵀ）、C1 正则化摩擦；历史记录：Backward Euler、100 次上限、绝对/相对容差 1e-9。[证据与历史遥测缺口 #124](docs/superdex-solver-audit.zh-CN.md) | 下方九组斜面配对；[冻结配置](docs/evidence/incline-comparison/manifest.json) |
| Genesis 1.4.3 CPU FP64 | 历史记录：Newton / approximate_implicitfast / elliptic，noslip=0；[源码解析与历史有效参数读回缺口 #125](docs/genesis-solver-audit.zh-CN.md) | [16 组夹持力限额实验](docs/force-limit-results.zh-CN.md)，未参与下方斜面配对 |
| Newton Physics 1.6.1 / Warp 1.18.0 | CPU SolverXPBD，float32；4 次迭代，dt=1 ms | [球–平面及负例](docs/newton-contact.zh-CN.md)，不等于抓取对照 |
| PhysX（历史 Isaac Sim 5.1；UniSim 及直接 SDK 路径） | 三组 SDK 对照读回 PGS/TGS 与外力时序；表面布料单列。[分批审计与原生核心身份缺口 #126](docs/physx-solver-audit.zh-CN.md) | [历史接触实验](demos/contact-benchmark/README.zh-CN.md)；不属于下方双引擎批次 |
| Drake | 1.57.0 / SAP / kLagged / hydroelastic / CPU FP64 | [斜面 6/9；保留滑动失败与负例](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.zh-CN.md) |

历史审计 [#124](https://github.com/huangkiki/Dexlab/issues/124)、[#125](https://github.com/huangkiki/Dexlab/issues/125)、[#126](https://github.com/huangkiki/Dexlab/issues/126)已完成有界搜寻与归因审查：SuperDex 同字节重建、Genesis 匹配源码推导、PhysX 三组场景读回分别保留；缺失遥测不回填，无法支持的精确核心版本及算法因果归因撤回。新实验由各引擎资格子项承接，使用独立记录；审计结项不增加可靠任务覆盖。

后续评测必须覆盖 **MuJoCo、SuperDex、Genesis、Newton Physics、PhysX、Drake** 及适用的已登记求解器配置。每份报告列出完整工况矩阵：已通过、已失败、受阻、不支持或未运行；缺项必须关联 Issue，补齐前仅称阶段结果。既有结果保留原范围，不追认成全引擎评测。ManiSkill/SAPIEN/Isaac Sim 是接入层，UniLab 是任务层，不能重复计作独立引擎；Newton Physics 与 MuJoCo 的 Newton 算法也不是一回事。

## 引擎对比：同一个方块，两种固定配置

官方 **MuJoCo 3.15.0** 与 **SuperDex 1.0.0 FP64**：相同 40 mm／64 g 方块、初态与重力，三个步长（2／1／0.5 ms），每例 2 秒。复用已有 MuJoCo 数据，新增九例 SuperDex 对照。

| 工况 | MuJoCo（impedance=0.9） | SuperDex（固定 penalty 配置） |
|---|---|---|
| 15° 静摩擦，μ=0.5 | 漂移 **1.301–1.336 mm**，0/3 通过 | 漂移 **0.708–1.132 mm**，2/3 通过 |
| 35° 滑动，μ=0.5 | 转动、间歇失去支撑，0/3 通过 | 评分窗内稳定滑动，3/3 通过 |
| 15° 名义零摩擦 | 速度 RMSE **8.21×10⁻⁵ m/s**，3/3 通过 | 速度 RMSE **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s**，3/3 通过 |

**结论：接触配置会改变漂移和稳定性，不能只凭引擎名称判断。** SuperDex 在这组固定配置下满足更多判据，但细化步长反而增大了静态漂移；已有 MuJoCo impedance=0.99 结果的漂移仅 **0.141–0.179 mm**，小于上述 SuperDex 结果。零摩擦差异还涉及 MuJoCo 的原生摩擦下限。速度误差使用 0.5–2 s 窗口；初始瞬态、全部失败及不同接触模型的条件见报告。

[完整对照、参数和原始数据](docs/incline-comparison-results.zh-CN.md)。这些计数是固定工况的容差判定，不能推广为真实材料精度或通用引擎排名。

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

## 下一阶段：统一驱动与夹持失效边界

[开发路线](docs/pinch-boundary-roadmap.zh-CN.md) · [专题 Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [研究总任务](https://github.com/huangkiki/Dexlab/issues/130)

[共同协议与数据接口 v1](docs/pinch-boundary-protocol.zh-CN.md)已实现：固定有限夹具、1 ms 外部 PD 时钟、594 个正式项、24 个对照及最多 32 个资格／桥接项，提供工况展开与记录结构校验。下一步为双后端资格与独立评分；后端尚未准入，正式批次尚未运行。六引擎缺项继续跟踪，历史结果保持原范围。

## 学习各个引擎：Sim Atlas

**[Sim Atlas · 仿真图谱学习首页](https://github.com/huangkiki/sim-atlas)** 提供双路线地图、共同基础与六引擎入口；每个引擎维护独立学习仓库，沿应用和原理源码两条路线，讲解建模、状态与时间、控制、接触求解、传感渲染、并行与扩展。

[GitHub Projects 总看板](https://github.com/users/huangkiki/projects/2) 按引擎、学习路线和阶段管理六仓任务，提供开发看板与课程总表。

[MuJoCo Atlas](https://github.com/huangkiki/mujoco-atlas) · [SuperDex Atlas](https://github.com/huangkiki/superdex-atlas) · [Genesis Atlas](https://github.com/huangkiki/genesis-atlas) · [Newton Atlas](https://github.com/huangkiki/newton-atlas) · [PhysX Atlas](https://github.com/huangkiki/physx-atlas) · [Drake Atlas](https://github.com/huangkiki/drake-atlas)

首批导读与固定版本源码地图已交付，完整专题仍在开发。当前先理解引擎机制，后续实验复用 DexLab 的版本、配置与工况记录。课程完成度与上方实验证据覆盖分别记录。

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
