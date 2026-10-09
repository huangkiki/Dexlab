---
html_theme.sidebar_secondary.remove: true
html_theme.sidebar_primary.remove: true
---

<div class="research-eyebrow">DEXLAB / PHYSICS EVALUATION NOTES</div>

# 接触如何影响抓取？

<div class="research-deck">从物理规律出发，检验仿真的解释。</div>

以经典物理规律与已有经验公式为参照，通过可复现实验研究接触与摩擦。这里先展示已得到的结论，再给出模型、求解器、原始数据与适用边界。

<div class="research-links"><a href="#comparison">阅读引擎对照 ↗</a><a href="#coverage">查看六引擎覆盖</a><a href="https://github.com/huangkiki/Dexlab/releases">代码与数据 ↗</a></div>

<div class="research-meta">当前数据交付 v0.46.0 · 解析验证 / 固定工况 · 全引擎矩阵尚未完成</div>

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

双手折布已有实验入口但尚未证明成功；Drake 尚无已验收任务；新的 MuJoCo／Genesis 统一驱动批次尚未准入。它们分别由 [折布记录](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/README.zh-CN.md)、[#117](https://github.com/huangkiki/Dexlab/issues/117) 和 [#130](https://github.com/huangkiki/Dexlab/issues/130)／[#143](https://github.com/huangkiki/Dexlab/issues/143) 跟踪。

**我们的评价标准：更好的引擎，应能可靠覆盖更多类型的任务。** 我们同时看任务类型、物理可信度、跨工况稳定性和执行成本：能在保留判据的前提下可靠完成更多任务类型，才扩大该配置的已验证能力。安装成功、适配器声明、同一任务的多个求解器或重复运行都不增加任务类型；历史不同协议的通过数不合并成通用排行榜。


## 不同 solver 的任务覆盖度

<!-- task-coverage:start -->

状态：完整通过 / 部分通过 / 失败 / 未运行 / 接入受阻 / 不支持。点击单元格查看证据或恢复条件。

**历史协议分别展示；通过只表示该协议的验收。** 新协议可靠覆盖须完成正例、负例、独立物理评分和冻结留出验证，并保持相同调优预算。

### 刚体任务 · 历史协议

| 引擎核心 / solver / 路径 / 版本 / 批次 | 基础接触 | 斜面 | 碰撞 | 夹具夹持 | 机器人抓取 |
| --- | --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/impact-stiffness-results.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **PhysX · historical readback incomplete (#126)**<br>SDK historical · core identity pending #126<br>rigid-history | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) |
| **Drake · pending qualification**<br>native · pending #117<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/117) | [未运行](https://github.com/huangkiki/Dexlab/issues/117) | [未运行](https://github.com/huangkiki/Dexlab/issues/117) | [未运行](https://github.com/huangkiki/Dexlab/issues/117) | [未运行](https://github.com/huangkiki/Dexlab/issues/117) |
| **MuJoCo · Newton / implicitfast**<br>native · 3.11.0<br>apple-sdf-14s | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |
| **SuperDex · Newton / GMRES / FP64**<br>native · 1.0.0<br>apple-sdf-14s | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [未运行](https://github.com/huangkiki/Dexlab/issues/121) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) |

### 操作任务 · 历史协议与缺项

| 引擎核心 / solver / 路径 / 版本 / 批次 | 推动 | 手内旋转 | 夹布抬升 | 主动折布 |
| --- | --- | --- | --- | --- |
| **MuJoCo · Newton / Euler**<br>native · 3.15.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **SuperDex · Newton / AUTO / FP64**<br>native · 1.0.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Genesis · Newton / approximate_implicitfast**<br>native CPU FP64 · 1.4.3<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Newton Physics · XPBD**<br>native CPU FP32 · 1.6.1 / Warp 1.18.0<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **PhysX · pending qualification**<br>ManiSkill / SAPIEN · official combination pending #47<br>rigid-history | [接入受阻](https://github.com/huangkiki/Dexlab/issues/47) | [接入受阻](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
| **Drake · pending qualification**<br>native · pending #117<br>rigid-history | [未运行](https://github.com/huangkiki/Dexlab/issues/47) | [未运行](https://github.com/huangkiki/Dexlab/issues/48) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) | [未运行](https://github.com/huangkiki/Dexlab/issues/28) |
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
| **PhysX · surface cloth**<br>Isaac Sim 5.1.0.0 / IsaacLab 0.47.2 · core identity pending #126<br>physx-cloth-final-v2 | [不支持](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [部分通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) | [完整通过](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/cloth.md) |

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

同工况、同评分的覆盖与“有过实验”分开记录。下表对应上述九组斜面协议；版本来自已有报告，不代表当前最新版。缺失项保留在矩阵内，不能计为通过。

| 引擎 | 已记录版本 / solver | 九组配对斜面协议 | 其他已有证据 |
|---|---|---|---|
| MuJoCo | 3.15.0 / Newton | 已运行，含失败 | 碰撞、夹持诊断 |
| SuperDex | 1.0.0 FP64 / [Newton 配置重建；历史遥测边界](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-solver-audit.zh-CN.md) | 已运行，含失败 | 加载、参数迁移 |
| Genesis | 1.4.3 / Newton / approximate_implicitfast；[历史配置及读回边界](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-solver-audit.zh-CN.md) | 未运行 | [16 组力限额](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.zh-CN.md) |
| Newton Physics | 1.6.1，Warp 1.18.0 / XPBD | 未运行 | [球–平面与负例](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.zh-CN.md) |
| PhysX | 三组 SDK 对照读回 PGS/TGS；[分批配置与原生核心身份缺口 #126](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.zh-CN.md) | 未运行；接入资格待补齐 | [历史接触实验](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/README.zh-CN.md) |
| Drake | 未取得已验收版本 / solver | 未运行 | [接入任务 #117](https://github.com/huangkiki/Dexlab/issues/117) |

公开结论中的事实与来源缺口必须关联可验收 Issue，并优先于新增能力处理。SuperDex 官方包身份与配置重建、Genesis 历史求解器枚举已核实；历史读回缺口分别由 [#124](https://github.com/huangkiki/Dexlab/issues/124)、[#125](https://github.com/huangkiki/Dexlab/issues/125) 跟踪，PhysX 已恢复三组原生场景求解器读回，[#126](https://github.com/huangkiki/Dexlab/issues/126) 保留各批次核心／加载库身份及其余缺失读回。重建、源码推导与历史原生读回分别标注。

[所有后续任务与阻塞](https://github.com/huangkiki/Dexlab/issues) · [PhysX 接入问题 #47](https://github.com/huangkiki/Dexlab/issues/47)。接入层与原生引擎分开；Newton Physics 也不是 MuJoCo 的 Newton 求解算法。

## 下一阶段：统一驱动与夹持失效边界

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

```{toctree}
:hidden:
:maxdepth: 1

快速开始 <quickstart>
实验 <experiments>
研究结果 <results>
引擎与模型 <engines>
灵巧操作路线 <dexterity>
研究证据账本 <research-ledger>
Benchmark <benchmark>
参与开发 <contributing>
```

## 学习引擎：Sim Atlas

[Sim Atlas · 仿真图谱学习首页](https://github.com/huangkiki/sim-atlas) 组织六个引擎的完整应用与原理源码路线，提供共同基础和各仓课程入口。[总看板](https://github.com/users/huangkiki/projects/2) 记录实际开发进度。当前课程专注引擎机制，后续案例复用这里的版本、工况与证据；课程完成度与实验覆盖分别记录。
