# 历史证据与完整配置矩阵
html_theme.sidebar_secondary.remove: true
html_theme.sidebar_primary.remove: true
---

<div class="research-eyebrow">DEXLAB / PHYSICS EVALUATION NOTES</div>

# 接触如何影响抓取？

<div class="research-deck">从物理规律出发，检验仿真的解释。</div>

以经典物理规律与已有经验公式为参照，通过可复现实验研究接触与摩擦。这里先展示已得到的结论，再给出模型、求解器、原始数据与适用边界。

<div class="research-links"><a href="#comparison">阅读引擎对照 ↗</a><a href="#coverage">查看六引擎覆盖</a><a href="https://github.com/huangkiki/Dexlab/releases">代码与数据 ↗</a></div>

<div class="research-meta">当前数据交付 v0.54.0 · 解析验证 / 固定工况 · 全引擎矩阵尚未完成</div>

## 现在能做哪些任务

按任务选择运行入口，再查看对应协议、环境和结果。下表记录 **DexLab 已实现并保留证据的范围**；“已运行”包含失败，“通过”只覆盖报告指定的版本、配置和场景。

| 任务 | 已有引擎与验证状态 | 运行与证据入口 |
|---|---|---|
| 斜面摩擦、一维碰撞 | MuJoCo／SuperDex 已有斜面配对，含通过与失败；一维碰撞已有 MuJoCo 记录 | [斜面对照](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.zh-CN.md) · [碰撞](https://github.com/huangkiki/Dexlab/blob/main/docs/elastic-impact-results.zh-CN.md) |
| 平面滑动、法向加载／卸载、圆柱夹持 | MuJoCo／SuperDex／PhysX 已运行开发案例，保留失败与几何细化结果 | [接触实验与命令](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/README.zh-CN.md) |
| 有限夹具夹持、抬升、保持与释放 | Genesis 已完成 16 个力限额工况；可研究驱动力与失败机制 | [力限额结果与复现](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.zh-CN.md) |
| 机器人 SDF 苹果梗抓取 | MuJoCo／SuperDex 已通过指定 14 s 场景；PhysX 有独立单场景验收，配置与准备链分别披露 | [MuJoCo／SuperDex](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.zh-CN.md) · [PhysX](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/apple.zh-CN.md) |
| 布料拉伸、下垂、球面覆盖、预折叠下落 | MuJoCo flex／SuperDex shell／Newton Physics 有历史实验，包含失败；PhysX 表面布料另有被动实验，逐节点外力拉伸不支持 | [布料基准](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/README.zh-CN.md) · [PhysX 范围](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.zh-CN.md) |
| 机器人夹布、抬升与释放 | MuJoCo 3.14 的指定 9 s 开发案例通过有限协议；自接触接近阈值，尚无稳健性结论 | [通过配置、失败与命令](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.zh-CN.md) |
| 刚体球—平面基础接触 | Newton Physics 1.6.1 / XPBD 的正常、重复及禁碰撞对照完成准入；未覆盖机器人抓取 | [协议、记录与复核](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.zh-CN.md) |

双手折布尚未证明成功。已完成MuJoCo/MJWarp3.11.0原生匹配核心对照。原生支撑同样未通过动量检查；对齐四项GPU字段后仍失败，轨迹仍与Isaac Sim不同，三次独立原生重复完全一致。CPU接触读回现已拒绝越界地址，可靠任务覆盖数不变。[结果与归因边界](https://github.com/huangkiki/Dexlab/blob/main/docs/framework-mjwarp-diagnostics.zh-CN.md)。

Drake 1.57.0 首轮斜面九例中六例通过、三例滑动失败，负例正确拒绝；[完整记录](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.zh-CN.md)。统一驱动接入差异已由 [#143](https://github.com/huangkiki/Dexlab/issues/143) 验证，完整研究批次仍见 [#130](https://github.com/huangkiki/Dexlab/issues/130)。

**覆盖概览描述研究范围；选型还要结合目标场景的物理可信度、稳定性与成本。** 我们同时看任务类型、物理可信度、跨工况稳定性和执行成本：能在保留判据的前提下可靠完成更多任务类型，才扩大该配置的已验证能力。安装成功、适配器声明、同一任务的多个求解器或重复运行都不增加任务类型；历史不同协议的通过数不合并成通用排行榜。


## 不同 solver 的任务覆盖度

MuJoCo 3.15.0 首轮六配置：elliptic 各 3/9，pyramidal 各 0/9；六个负例正确拒绝。CG／Newton 的 pyramidal 路径各有三例力–状态一致性失败，均保留为无效记录。 [详细证据 / Evidence](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.zh-CN.md).

SuperDex 1.0.0 FP64 的十二组斜面配置中，九组 8/9、三种 CG 路径各 6/9；全部负例正确拒绝，五个 CUDA 选项在官方构建中不支持。失败与历史缺失完整保留。 [Evidence / 详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.zh-CN.md).

BFGS／SR1 保留每步重组装的设置，实际执行等价 Newton 步骤；这些是配置记录，不能算额外验证了两种算法。

Genesis 1.4.3 原生斜面五组配置分别为 6/9、3/9、0/9、0/9、0/9；名义零摩擦被原生接触抬至 .01，七条 CG 一致性失败全部保留并完成停止条件诊断。 [Evidence / 详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.zh-CN.md).

Newton Physics 1.6.1 原生斜面七配置通过数为 1/9、0/9、0/9、0/9、0/9、1/9、4/9；49 条正例及两个 VBD 负例未通过数值检查。DVI 超时与单独续接均保留；不据此声称引擎排名或可靠覆盖。 [详细证据](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.zh-CN.md)。

PhysX SDK 5.9.0 原生斜面四配置通过 7/9、7/9、3/9、3/9；四个负例均有效且被拒绝，13 条正例触发冻结数值检查。失败及原始读回全部保留；不计入可靠覆盖，也不推断框架路径表现。[结果与复现](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.zh-CN.md) · [精度验证 #163](https://github.com/huangkiki/Dexlab/issues/163)。

Drake 1.57.0 的三种 SAP 近似与点/hydroelastic接触已有六配置斜面证据：复用旧6/9，新配置0/9、5/9、0/9、3/9、2/9。五条新增正例超过原动量检查，全部失败保留；旧Lagged滑动合力已由独立源码公式重建至4e-13 N以内。未增加可靠任务覆盖。[协议、结果与复现](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.zh-CN.md) · [残差后续验证 #165](https://github.com/huangkiki/Dexlab/issues/165)。

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
| **Drake · SAP / kLagged / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-incline-qualification-v2 | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 6/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
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
| **PhysX · PGS / patch friction**<br>native SDK CPU FP32 · 5.9.0<br>physx-incline-v1-pgs | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 7/9](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · PGS / friction every iteration**<br>native SDK CPU FP32 · 5.9.0<br>physx-incline-v1-pgs-friction | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 7/9](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · TGS / patch friction**<br>native SDK CPU FP32 · 5.9.0<br>physx-incline-v1-tgs | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · TGS / external forces every iteration**<br>native SDK CPU FP32 · 5.9.0<br>physx-incline-v1-tgs-external | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kLagged / point**<br>native CPU FP64 · 1.57.0<br>drake-contact-paths-v1-lagged-point | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kSimilar / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-contact-paths-v1-similar-hydroelastic | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 5/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kSimilar / point**<br>native CPU FP64 · 1.57.0<br>drake-contact-paths-v1-similar-point | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [失败 0/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kSap / hydroelastic**<br>native CPU FP64 · 1.57.0<br>drake-contact-paths-v1-sap-hydroelastic | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · SAP / kSap / point**<br>native CPU FP64 · 1.57.0<br>drake-contact-paths-v1-sap-point | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过 2/9](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **MuJoCo · MJWarp Newton / pyramidal / Newton contacts**<br>Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 · 3.11.0<br>isaac-mjwarp-clock-v6 | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) |
| **MuJoCo · MJWarp Newton / pyramidal / MJWarp contacts**<br>Isaac Sim6.1.0 local tag build / Newton1.5.0 / vendor Warp1.16.0 · 3.11.0<br>isaac-mjwarp-clock-v6 | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) |
| **MuJoCo · MJWarp Newton / pyramidal / MJWarp contacts**<br>Native matched core / vendor Warp1.16.0; original and four-field aligned · 3.11.0<br>native-mjwarp-matched-v1 | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) | [未运行](https://github.com/huangkiki/Dexlab/issues/152) |

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


## 先看三个结论

::::{grid} 1 1 3 3
:gutter: 3
:::{grid-item-card} 01 / 接触配置影响漂移
:class-card: research-finding
**引擎名称不足以预测结果。** 同一方块的斜面对照中，固定配置下 SuperDex 满足更多判据；提高阻抗后的历史 MuJoCo 配置却有更小静态漂移。

[看参数与反例](#comparison)
:::
:::{grid-item-card} 02 / 末态正确不等于过程准确
:class-card: research-finding
**24/27 末态通过，2/27 同时满足穿透预算。** 碰撞速度、能量和接触重叠需要分别检查，单一成功分数会遗漏问题。

[看碰撞证据](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.zh-CN.md)
:::
:::{grid-item-card} 03 / 力残差更小不等于抓得更稳
:class-card: research-finding
**收紧容差后，方块仍下滑约 2 mm。** 数值一致性改善与抓取保持是不同结果；必须直接测量运动。

[看夹持证据](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-impulse-results.zh-CN.md)
:::
::::

(comparison)=
## 同一个方块，两种固定配置

40 mm · 64 g · 相同初态与重力 · 2 / 1 / 0.5 ms 三个步长 · 每例 2 秒。MuJoCo 复用已核验记录，SuperDex 新增九例。**这是双引擎阶段对照，不是六引擎排名。**

| 工况与观测 | MuJoCo 3.15.0 | SuperDex 1.0.0 FP64 |
|---|---|---|
| 15° 静摩擦，μ=0.5 · 位移 | **1.301–1.336 mm** · 0/3 通过 | **0.708–1.132 mm** · 2/3 通过 |
| 35° 滑动，μ=0.5 · 承载与运动 | 转动、间歇失去支撑 · 0/3 | 评分窗内稳定滑动 · 3/3 |
| 15° 名义零摩擦 · 速度 RMSE | **8.21×10⁻⁵ m/s** · 3/3 | **8.04×10⁻¹²–1.52×10⁻¹⁰ m/s** · 3/3 |

<div class="research-caution"><strong>反例也属于结论。</strong> 历史 MuJoCo impedance=0.99 的静态漂移为 0.141–0.179 mm，小于上表 SuperDex。SuperDex 静态漂移随步长细化反而增大；MuJoCo 的名义零摩擦存在原生下限。不能据此宣布通用优胜者。</div>

**求解配置。** MuJoCo：Newton / Euler / elliptic，impedance=0.9，100 次迭代上限，容差 1e-10。SuperDex 同字节配置重建：Newton / AUTO（小系统源码路径为稠密 LDLᵀ）/ C1 正则化摩擦；历史记录为 Backward Euler、100 次上限、绝对与相对容差 1e-9。[身份、组合律与历史遥测缺口 #124](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-solver-audit.zh-CN.md)。相同 μ 不等于材料或接触模型等价。速度误差评分窗为 0.5–2 s，初始瞬态与失败详见报告。

[完整结果与原始数据](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.zh-CN.md) · [冻结协议](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-protocol.zh-CN.md) · [参数清单](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/incline-comparison/manifest.json)

(coverage)=
## 六个引擎，覆盖到哪里？

下表索引相同起始物理工况的各批次；各批次独立冻结原生观测与评分，尚不是共同调优/留出集的六引擎排名。历史身份与新准入分开保留；完整 solver 行见上方自动生成矩阵。

| 引擎 | 已记录版本 / solver | 九组配对斜面协议 | 其他已有证据 |
|---|---|---|---|
| MuJoCo | 3.15.0 / Newton | 已运行，含失败 | 碰撞、夹持诊断 |
| SuperDex | 1.0.0 FP64 / [Newton 配置重建；历史遥测边界](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-solver-audit.zh-CN.md) | 已运行，含失败 | 加载、参数迁移 |
| Genesis | 1.4.3 / 五组原生配置 | [已运行，含失败与无效记录](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.zh-CN.md) | 历史力限额证据单列 |
| Newton Physics | 1.6.1 / Warp 1.18.0 / 七组原生配置 | [已运行，含失败、中断及明确续接](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.zh-CN.md) | 球–平面负例另有证据 |
| PhysX | 原生 SDK 5.9.0 / PGS、TGS 四配置 | [7/9、7/9、3/9、3/9](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.zh-CN.md) | 历史框架核心缺口不回填；对照 #152 |
| Drake | 1.57.0 / SAP / kLagged / hydroelastic | [6/9；滑动失败](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-incline-results.zh-CN.md) | 负例正确拒绝；其他配置 [#151](https://github.com/huangkiki/Dexlab/issues/151) |

历史审计 [#124](https://github.com/huangkiki/Dexlab/issues/124)、[#125](https://github.com/huangkiki/Dexlab/issues/125)、[#126](https://github.com/huangkiki/Dexlab/issues/126)已完成有界搜寻与归因审查：SuperDex 同字节重建、Genesis 匹配源码推导、PhysX 三组场景读回分别保留；缺失遥测不回填，无法支持的精确核心版本及算法因果归因撤回。新实验由各引擎资格子项承接，使用独立记录；审计结项不增加可靠任务覆盖。

[所有后续任务与阻塞](https://github.com/huangkiki/Dexlab/issues) · [PhysX 接入问题 #47](https://github.com/huangkiki/Dexlab/issues/47)。接入层与原生引擎分开；Newton Physics 也不是 MuJoCo 的 Newton 求解算法。

## 下一阶段：统一驱动与夹持失效边界

接触路径对照已找到低力差异的配置来源：24 进程原生诊断隔离了参数批存储因素，随后对齐存储的 38 次启动／56 回合通过全部 19 组对照与 12 项精确重放，原误差阈值不变。旧版六组失败和低力抓取失败均保留。该结果限定于显式披露的 Genesis 1.4.3／本地适配补丁组合，不增加任务类型数。[原因、证据与复现](https://github.com/huangkiki/Dexlab/blob/main/docs/unisim-contact-migration.zh-CN.md) · [#143](https://github.com/huangkiki/Dexlab/issues/143)。

[开发路线](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-roadmap.zh-CN.md) · [专题 Discussion](https://github.com/huangkiki/Dexlab/discussions/129) · [研究总任务](https://github.com/huangkiki/Dexlab/issues/130)

[共同协议与数据接口 v1](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-protocol.zh-CN.md)已实现：固定有限夹具、1 ms 外部 PD 时钟、594 个正式项、24 个对照及最多 32 个资格／桥接项，提供工况展开与记录结构校验。下一步为双后端资格与独立评分；后端尚未准入，正式批次尚未运行。六引擎缺项继续跟踪，历史结果保持原范围。

## 我们怎样检验

1. **先定义参照。** 静摩擦 |f| ≤ μₛN；临界条件 tanθ=μₛ；滑动加速度 a=g(sinθ−μₖcosθ)。先声明刚体、库仑摩擦、初态与适用条件，再与原生观测对比。
2. **固定工况，公开差异。** 对齐质量、惯量、几何、坐标、控制与初态；记录引擎和 solver 版本、精度、步长、求解预算与接触参数。
3. **保留失败，检查敏感性。** 同时报告绝对误差、过程轨迹、收敛/敏感性和成本。支持丢失、旋转、不可观测参数不会被隐藏在平均值里。
4. **区分证据边界。** 解析验证、带来源的经验参照和真实系统验证分别报告。前两者可以独立开展，不能替代具体材料的实测标定。

## 从接触实验回到抓取

![Genesis 夹持、抬升与释放的原生状态回放](../../../demos/contact-benchmark/media/genesis-pinch.gif)

Genesis 原生状态的连续回放，由 MuJoCo 显示。16 个固定工况中，0.2/0.4 N 力限额无法保持，0.8/10 N 能保持并释放；包含 ±2 mm 初态偏移。此结果限于该夹具，不是跨引擎抓取排名。

[力限额完整报告](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.zh-CN.md) · [全部研究结果](results.md) · [安装与复现](quickstart.md)

<div class="research-footer">组织方式参考 <a href="https://mandarobotics.com/blog/comparing-physics-engines/index.html">Manda Robotics 的物理引擎比较</a>：先结论、逐项对照、公开差异。本站数值只来自 DexLab 已发布证据。</div>



## 学习引擎：Sim Atlas

[Sim Atlas · 仿真图谱学习首页](https://github.com/huangkiki/sim-atlas) 组织六个引擎的完整应用与原理源码路线，提供共同基础和各仓课程入口。[总看板](https://github.com/users/huangkiki/projects/2) 记录实际开发进度。当前课程专注引擎机制，后续案例复用这里的版本、工况与证据；课程完成度与实验覆盖分别记录。
