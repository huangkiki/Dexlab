# DexLab

**以经典物理规律与已有经验公式为参照，通过可复现实验，研究接触与摩擦对机器人抓取的影响，评估物理仿真的可信度。**

这项研究服务于两个目标：

| 你面临的问题 | DexLab 提供的答案 |
| --- | --- |
| **场景表现不好，应该改什么？** | 找到偏离物理预期的位置，区分参数、接入、模型假设与求解过程的影响，给出有证据的配置修正和 solver 改进方向。 |
| **面对新场景，怎样选择引擎／solver？** | 根据相近接触与摩擦条件的实验，选择候选配置，了解参数敏感性、适用边界、稳定性和成本，逐步积累场景适配经验。 |

[English](README.en.md) · [中文文档站](https://huangkiki.github.io/Dexlab/zh-cn/latest/index.html) · [研究经验](docs/site/zh/experience.md) · [诊断与试参方法](docs/site/zh/diagnosis.md) · [场景选型指南](docs/site/zh/selection.md)

## 我们已经知道什么

这些结论来自已有报告和日志，适用范围随证据一起保留。它们支持下一次实验的起点；历史结果不自动代表当前所有版本或新的留出验证。

| 物理问题 | 已有发现 | 对抓取仿真的意义 |
| --- | --- | --- |
| 法向响应 | 在固定方块实验中，MuJoCo 静态响应能通过参数校准接近目标；改变质量后，原参数不再保持同一响应。 | 参数必须结合质量、阻抗与接触构型解释。[条件与证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#normal-response) |
| 瞬态与成本 | 27 条响应—成本记录中，MuJoCo 低阻抗配置 9/9 联合通过，高阻抗与该 SuperDex 配置均 0/9；缩小步长并不普遍消除误差。 | 同时验证动态响应、无拉力、稳定性与额外计算成本。[条件与证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#transient-cost) |
| 质量／尺寸迁移 | 三个固定配置的 30 条迁移记录全部完成，0/30 联合通过。 | 单场景成功不足以推荐直接迁移；先检查接触尺度与参数转换。[失败也可复用](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#mass-size-transfer) |
| PhysX 接触观测 | 原生 SDK 5.9.0 的四组斜面配置存在不同失败；部分记录触发 FP32 冲量一致性检查。 | 先区分观测有效性与物理误差，有限试参失败不能证明引擎不适用。[诊断案例](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#physx-observation) |
| 夹持与释放 | Genesis 固定夹具的 16 个案例显示驱动力限额改变保持边界；机器人 SDF 抓取有独立历史验收。 | 看实际承载、滑移与释放，不能只看接触力误差。[条件与证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#pinch-load) |
| 框架接入 | 匹配核心和 CPU 模型后，原生与 Isaac Sim 的有效 GPU 字段仍可能不同；对齐四项也未解释全部轨迹差异。 | 保存资产转换及最终有效参数，按具体差异归因。[对照与未解问题](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#framework-path) |

响应研究中的刚度／阻尼目标是**合成目标**；解析关系用于**数值验证**；真实材料与机器人准确性需要独立测量。三者分别表述，已有实验无需等待真机数据才能产生有价值的结论。

## 场景表现不好时如何分析

以“接触表现异常”为例，先声明物理参照与假设，再检查几何、质量／惯量、坐标、控制时刻、有效参数和接触读回。随后固定场景与目标，提出可检验假设，做有限参数试验，用独立评分确认改善及成本。剩余差异再进入接触生成、摩擦表示、约束求解、停止条件、积分和精度的机制研究。

已有 PhysX 案例中，禁碰撞前后初始化质量的顺序导致负例质量错误；修正接入后，其他数值残差仍然存在。参数改善、接入修正、算法研究方向和未解问题分别记录。[完整诊断方法与命令](docs/site/zh/diagnosis.md)

**AI 自动试参是研究方法之一。** AI 利用已有经验提出假设与候选参数；现有执行器、预算账本和独立评分保留所有尝试、失败、有效参数与成本。有限搜索未找到配置时，结论是当前搜索范围尚未成功。新迁移条件事前冻结，历史日志不能充当新留出。

## 新场景如何选择

先描述接触尺度与载荷、粘着／滑动、接触切换、几何及柔顺性，再查找邻近实验。每个候选起点都附版本／路径、参数来源、误差与失败边界，并列出新场景首先要做的验证。

| 新场景的主要困难 | 从哪里开始 |
| --- | --- |
| 法向柔顺、加载卸载或瞬态响应 | [法向／瞬态经验](docs/site/zh/selection.md)；核对合成目标和接触律，验证质量／尺寸迁移。 |
| 支撑、斜面滑动、低摩擦 | [六引擎斜面证据](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#six-engine-incline)；先确认观测有效，再比较接近目标工况的配置。 |
| 有限指面夹持、抬升与释放 | [夹持与 SDF 起点](docs/site/zh/selection.md)；核对驱动力、惯量、滑移和负例。 |
| 更换框架或导入资产 | [原生／框架对照](https://huangkiki.github.io/Dexlab/zh-cn/latest/experience.html#framework-path)；比较转换来源、有效参数和时刻。 |

推荐依赖与目标场景相关的证据，兼顾**物理可信度、稳定性和成本**。覆盖更多任务意味着积累了更广的已验证范围；覆盖表本身不决定某个新场景的最佳方案。

## 研究范围与复现

| 已有研究范围 | 证据入口 |
| --- | --- |
| 六引擎基础接触／斜面及适用 solver；碰撞、夹具夹持和机器人抓取 | [完整配置矩阵与各协议状态](docs/site/zh/coverage.md) |
| 布料力学、预折叠下落、机器人夹布 | [历史协议与失败](docs/site/zh/coverage.md)；预折叠下落不等于主动折布成功。 |
| 推动、手内旋转与扩展抓取 | [研究路线](docs/site/zh/dexterity.md)；未运行、受阻和不支持分别标注。 |

矩阵保留引擎核心、solver、运行路径、版本、通过／部分通过／失败／未运行／接入受阻／不支持及证据。重复、步长扫描、更换框架不增加任务类型；不同历史协议不合并计数。新 coverage-v1 可靠覆盖尚未验收，历史能力仍以原协议为界。

[安装与复现](docs/installation.zh-CN.md) · [全部报告](docs/site/zh/results.md) · [原始数据与版本](https://github.com/huangkiki/Dexlab/releases) · [研究与开发看板](https://github.com/users/huangkiki/projects/4)

本轮优先复用证据、补齐诊断案例所需缺口，再向夹持／抓取迁移；六引擎矩阵和 594 回合夹持研究继续保留。**定时开发保持暂停。** [开发与验收约定](docs/autoresearch.zh-CN.md)
