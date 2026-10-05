<div align="center">

# DexLab

**机器人接触动力学：从模型与参数，到可复核的实验结论。**

[中文文档](docs/site/zh/index.md) · [English](README.en.md) · [实验代码](demos/) · [结果与数据](docs/evidence/README.zh-CN.md) · [研究任务](https://github.com/huangkiki/Dexlab/issues)

</div>

> 归档基础设施更新：本地归档现在先验证内存、CPU 与磁盘 I/O 硬限额；异常终止保留源和回执。成功、超时与隔离 OOM 检查通过，两类历史归档完成受限读取复核。[运行边界](docs/remote-research.zh-CN.md#本地归档硬资源限制)

DexLab 基于 **UniLab** 组织刚体抓取、布料和基础接触实验，研究碰撞几何、接触律、求解器及驱动对**穿透、滑移、抖动与计算成本**的影响。每项结论连接原始记录、独立评分、参数来源与失败案例。

## 本机执行与自动交付

实验优先使用通过准入的本机，实测资源余量并强制 cgroup 限额，禁用实验 swap。每次选项先复审优先级，中断任务通过实际句柄恢复；远端作为可选执行位置。[执行与恢复协议](docs/autoresearch.zh-CN.md#本机优先执行与恢复)。

## 灵巧操作任务路线

[新版研究证据账本](docs/dexterity-ledger.zh-CN.md)覆盖38篇论文身份与19个仓库入口，区分定向源码审查、摘要筛选及未验证运行时。关键结论：上游成功指标须独立复核；目标关节值、估算力矩和触觉代理不能当实测量；自定义引擎与历史配置不进入最新稳定版比较。可选动作回放 #52、触觉历史 #53 已设依赖和预算。

当前实现集中于抓持与接触诊断。新增 [六层研究地图](docs/dexterity-roadmap.zh-CN.md) 将 ManiSkill、抓取评测、触觉、数据生成与本体研究映射到具体实验；[ManiSkill 原生任务 #47](https://github.com/huangkiki/Dexlab/issues/47) 与 [手内旋转 #48](https://github.com/huangkiki/Dexlab/issues/48) 已排入计划，**尚未实现，不算已支持**。

## 当前结论

| 研究问题 | 已有证据 | 结论与限制 |
|---|---|---|
| 动力学能否夹起苹果梗？ | 默认场景通过；历史 10 场景回归：MuJoCo **1/10**、SuperDex **10/10** | 说明各固定配置的鲁棒性，**不是引擎真实精度排名** |
| 夹布是否物理有效？ | **176/225** 保存帧存在布—桌相交，最大内部深度 **3.00 mm** | 评分漏检已修正，物理修复尚未完成 |
| 材料与接触如何影响结果？ | 拉伸、下垂、滑动、加载及瞬态的成功和失败均保留 | 材料和驱动尚未完成跨引擎实测校准 |
| 能否说明真机表现？ | 尚无正式标定集与独立实测测试集 | 实测误差与 sim-to-real 能力未知 |

下面的图表均为**原固定版本的历史证据**。新批次采用官方最新稳定版并重新验收，见 [版本准入 #41](https://github.com/huangkiki/Dexlab/issues/41)；[Genesis #42](https://github.com/huangkiki/Dexlab/issues/42) 已纳入计划，尚无运行结果。

## 关键实验结果

### 苹果梗：成功率与失败发生在哪里

10 个冻结场景改变质量、水平位置与朝向，共 20 次实验，未为这些场景重新调参。

| 历史配置 | 完整验收通过 | 95% Wilson 区间 |
|---|---:|---:|
| MuJoCo 3.11.0 · 0.5 ms | 1 / 10 | 1.8–40.4% |
| SuperDex 1.0.0 FP64 · 2 ms | 10 / 10 | 72.2–100% |

![逐场景接触重叠、腕部位移与完整协议失败](docs/evidence/apple-metrics.zh-CN.svg)

叉号表示完整验收失败。原生接触重叠与独立表面侵入是不同量；**腕部相对位移不是材料滑移**。两套配置的步长、摩擦和驱动不同，不能据此归因引擎优劣。PhysX 目前只有独立开发场景，未进入这组留出测试。

[协议与失败明细](docs/benchmark.zh-CN.md) · [指标定义与复算](docs/evidence/README.zh-CN.md) · [原始数据与来源](docs/evidence/cohorts.json)

### 夹布：看起来抓住了，几何检查仍然失败

![布—桌相交时间线](demos/cloth-folding/media/table-diagnostic.zh-CN.svg)

原 9 秒连续记录在 225 个保存帧中有 176 帧桌体相交。检查覆盖零厚度三角面，不能证明有限厚度或帧间无碰撞。**评分修复不等于物理修复**；完整夹持、抬升与释放仍由 [#32](https://github.com/huangkiki/Dexlab/issues/32) 验证。

[旧新评分及测量边界](demos/cloth-folding/SCORING.zh-CN.md)

<details>
<summary><strong>展开：七个完整历史批次的全部结局</strong></summary>

![历史批次分布](docs/evidence/outcomes.zh-CN.svg)

每行对应不同任务与协议，失败和不支持均保留。开发集与留出集分列，不合并成引擎总分。[完整技术报告](docs/evidence/README.zh-CN.md)

</details>

## 连续近景演示

<table>
<tr><th>MuJoCo · 默认开发场景</th><th>SuperDex FP64 · 默认开发场景</th></tr>
<tr><td><img src="demos/apple-stem-grasp/media/mujoco-sdf.gif" alt="MuJoCo 连续抓梗近景" width="100%"></td><td><img src="demos/apple-stem-grasp/media/superdex-sdf.gif" alt="SuperDex 连续抓梗近景" width="100%"></td></tr>
<tr><th>PhysX · 独立开发场景</th><th>机器人夹布 · 几何失败记录</th></tr>
<tr><td><img src="demos/physx-contact/media/physx-sdf.gif" alt="PhysX 连续抓梗近景" width="100%"></td><td><img src="demos/cloth-folding/media/grasp.gif" alt="保留桌体相交失败的夹布回放" width="100%"></td></tr>
</table>

苹果动图连续展示 14 秒接近、闭合、抬升与保持。展示相机只用于回放，不参与控制。[MuJoCo 视频](demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex 视频](demos/apple-stem-grasp/media/superdex-sdf.mp4) · [PhysX 报告](demos/physx-contact/apple.zh-CN.md) · [夹布报告](demos/cloth-folding/README.zh-CN.md)

## 实验方法与引擎差别

OpenArm 双臂＋Wuji，右手拇指/食指夹梗、左臂停放。苹果与梗为 **0.2 kg 自由刚体**，苹果及两指腹均使用 SDF；没有物体附着、位置驱动或引擎源码补丁。控制来自**已知位姿、逆运动学与脚本关节目标**，不是视觉策略或学习得到的技能。

| 历史后端 | 接触实现 | 步长 | 需要披露的近似 |
|---|---|---:|---|
| MuJoCo | SDF 接触搜索＋软约束 | 0.5 ms | SDF 离散、接触点与约束参数 |
| SuperDex FP64 | 表面采样积分＋平滑罚能 | 2 ms | 采样密度、平滑与罚响应 |
| PhysX | 原生 SDF 接触＋TGS | 1 ms | SDF 分辨率、接触离散与扭转半径 |

保持窗口为 11–14 s；验收离桌、两指支撑、穿透、相对腕部位移和动量平衡，接近阶段允许果身接触。相同源表面不等于相同离散几何或接触定律，不模拟梗弯曲或断裂。

[参数来源与底层实现](docs/sdf-backends.zh-CN.md) · [基准设计](docs/site/zh/benchmark.md) · [模型审查](docs/model-audit.zh-CN.md)

## 实验代码与文档

| 实验 | 代码 | 详细报告 |
|---|---|---|
| 苹果梗抓取 | [apple-stem-grasp](demos/apple-stem-grasp/) | [运行与验收](demos/apple-stem-grasp/README.zh-CN.md) |
| 机器人夹布 | [cloth-folding](demos/cloth-folding/) | [失败复核](demos/cloth-folding/SCORING.zh-CN.md) |
| 接触、驱动与瞬态 | [contact-benchmark](demos/contact-benchmark/) | [研究结果](demos/contact-benchmark/README.zh-CN.md) |
| 多求解器布料 | [cloth-benchmark](demos/cloth-benchmark/) | [材料与留出实验](demos/cloth-benchmark/README.zh-CN.md) |
| PhysX 接触与布料 | [physx-contact](demos/physx-contact/) | [能力与限制](demos/physx-contact/README.zh-CN.md) |

**[中文文档站源码](docs/site/zh/index.md) · [English documentation](docs/site/en/index.md)**。文档站维护快速开始、实验目录、结果、引擎原理、benchmark 和开发规范；Sphinx 严格构建并维护两种语言，发布配置已纳入仓库。在线地址需部署验证后公布。

## 快速复现

Linux x86_64，安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后运行原固定版本演示：

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或 --backend superdex；无显示环境添加 --headless
```

无需模型 API key。SDF 构建与规划完成后打开窗口；运行命令使用 UniLab 注册任务，原生场景由 DexLab 管理。[完整安装](docs/installation.zh-CN.md) · [仅构建文档](docs/site/zh/quickstart.md#仅构建文档)

## 参与与致谢

请用 [Issue](https://github.com/huangkiki/Dexlab/issues) 提交可复现问题、参数实验或失败案例。实验 PR 同步结论、指标图表与中英报告；无读者影响的内部修改说明理由。[开发与发布流程](docs/autoresearch.zh-CN.md)

感谢 [UniLab](https://github.com/unilabsim/UniLab)、[Project SuperDex](https://github.com/unilabsim/project_superdex)、[MuJoCo](https://github.com/google-deepmind/mujoco)、[Newton](https://github.com/newton-physics/newton)、[OpenArm](https://github.com/enactic/openarm) 和 [Wuji](https://github.com/wuji-technology)。文档组织参考 [RLinf](https://github.com/RLinf/RLinf)。SuperDex 抓梗演示收录于 [Awesome Astra Embodied AI · Case 7](https://github.com/zjwzcx/Awesome-Astra-Embodied-AI#case-7-dexterous-apple-stem-grasp-in-superdex)，Astra 参与开发与调试。

代码：[Apache-2.0](LICENSE)；第三方资产见[来源与许可](docs/ASSETS.zh-CN.md)。

最新稳定版运行准入正在推进：[版本清单、GPU 基础检查及边界](docs/engine-qualification.zh-CN.md)。设备检查不等于抓取成功，也尚未开放正式 benchmark 派发。

六卡基础接触对照已实际完成：六组参数中 4 组通过、2 组失败。默认软接触下仅减小步长并未减少侵入；详见上面的逐配置报告。这不是苹果抓取验收。
