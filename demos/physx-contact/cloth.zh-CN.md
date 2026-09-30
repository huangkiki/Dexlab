# PhysX 原生表面布料

[English](cloth.md) | [简体中文](cloth.zh-CN.md)

PhysX 表面变形体通过已注册的 **UniLab `DexLab-Cloth-v0` 任务**运行，复用共享三角网格、场景清单和独立几何评分。任务单独管理 Isaac Sim 布料场景；UniSim 提供隔离运行环境定位，不代表其内置适配器已有布料接口。官方 PhysX、IsaacLab 文件未修改。

![PhysX 原生球面覆盖](media/cloth-drape.gif)

[Video / 视频](media/cloth-drape.mp4) · [Provenance / 来源](media/cloth-drape.json)

## 复现

先安装[可选的固定版本 Isaac Sim 环境](README.zh-CN.md)。以下命令在仓库根目录执行：

```bash
.venv/bin/python -m dexlab.cloth_benchmark run \
  --solver physx-surface --case dev-sag --device cuda:0 --iterations 16 \
  --output demos/physx-contact/runs/my-cloth-sag
.venv/bin/python -m dexlab.cloth_benchmark verify \
  demos/physx-contact/runs/my-cloth-sag
.venv/bin/python demos/cloth-benchmark/src/render.py \
  demos/physx-contact/runs/my-cloth-sag
```

非默认环境路径设置 `UNISIM_ISAACSIM_HOME`。`dev-drape` 使用球体与地面；`dev-folded-drop` 需加 `--suite benchmarks/cloth-self-contact-v1.json`。三秒实验逐 0.5 ms 记录，并包含实际初始状态；不覆盖已有输出目录。不支持 CPU 运行。

按外力拉伸的 `dev-extension` **不支持**：固定版本的表面张量 API 没有逐节点施力接口。程序在启动 SDK 前拒绝该项，保存 `unsupported` 记录，不用修改位置或速度近似指定外力。默认七求解器批量实验不变；显式添加 `--solver physx-surface --device cuda:0` 才启用此可选环境。

## 模型与参数

| 项目 | 定义 |
|---|---|
| 几何 | 原始三角表面，原生 beta `OmniPhysicsSurfaceDeformableSimAPI`；未换成四面体体积或粒子布料 |
| 材料 | 杨氏模量 20 kPa、泊松比 0、厚度 0.5 mm、动摩擦系数 0.5；名义工程输入 |
| 质量 | 场景面密度除以厚度得到体密度，同时显式指定总质量；该张量接口不提供原生节点质量读回 |
| 边界 | 固定边缘使用顶点到独立世界坐标锚点的约束；自由下落、球面覆盖无附着 |
| 求解 | 0.5 ms、16 次位置迭代，开启自碰撞与推测式 CCD；线性／弹性／弯曲阻尼及睡眠／静置阈值显式设零 |
| 接触偏移 | 表面 rest offset 等于场景半径（默认 1 mm），contact offset 为两倍 |
| 状态 | 原生表面节点位置、速度张量；节点／单元顺序及静止几何须与输入一致 |

面密度和总质量属于声明输入，不能视为独立原生质量读回。相同数值不代表与 MuJoCo flex、Newton 布料或 SuperDex 薄壳材料等价。记录原生 100 m/s 速度上限，触及上限不能通过验收。变形体不宣称静摩擦支持，见固定版本的[物理限制](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/current_limitations.html)。

SDK 初始化可能推进物理。程序归档预热状态，并在**开始记录前仅一次**恢复声明位置及零速度；测量轨迹中不写入节点状态。固定边缘使用独立世界锚点；开发阶段连接到布料祖先节点未能约束，布料自由下落，该失败保留。

隔离进程另行生成 headless 配置，保留官方物理和基础扩展，省略无关 IsaacLab RL／任务扩展；归档原文件哈希及 BSD 许可。退出时先通过公共生命周期方法清理仿真上下文回调，再停止场景，未修改 SDK。

## 验收边界

复用既有独立评分：逐记录步检查有限状态、初始条件、固定边界误差小于 1 µm、障碍物穿透小于 1.5 mm；三角形内部与球面距离、独立表面相交检查均不改阈值。相交检查约 100 Hz 采样，排除共享顶点的面，不保证连续时间无穿越或有限厚度无重叠。

额外检查原生拓扑、原始状态／源码哈希、完整 worker 日志及正常停止确认／进程退出。固定 SDK 的精确插件依赖声明警告单列。只有模型加载不能算实验通过；没有真机材料精度或引擎排名结论。

开发试验及早期 API、初始化、边界失败保留在证据索引。本实验是被动布料验收，不是机器人夹布或折叠策略。[完整布料基准](../cloth-benchmark/README.zh-CN.md) · [Issue #5](https://github.com/huangkiki/Dexlab/issues/5) / [#12](https://github.com/huangkiki/Dexlab/issues/12)。

## 冻结实验结果

固定 Isaac Sim 5.1.0.0 / IsaacLab 0.47.2 / PhysX 107.3，RTX 4090；使用既有场景清单，未依据留出结果调参。最终源码上的结果如下：

| 实验集合 | 通过 | 物理检查失败 | 不支持 |
|---|---:|---:|---:|
| 开发集，4 场景 | 3 | 0 | 1 |
| 留出集，15 场景 | 10 | 1 | 4 |
| 开发场景步长／网格细化，9 次 | 8 | 1 | 0 |

所有支持的实验均完成，正常停止，无运行错误或超时。4 个留出“不支持”均为指定外力拉伸；不能将其算作已执行的物理失败，也不能从能力覆盖分母中删去。

留出 `test-drape-03` 在 **0.22 s** 检测到 **2 对非相邻三角面相交**，失败记录保留。首轮相同数值配置得到 11 通过、4 不支持；最终复跑为 10 通过、1 失败、4 不支持。两轮引擎元数据相同，其间仅有 Python 格式／导入顺序整理与保留张量所有者的变量改名。尚未确定差异原因，不以首轮结果宣称稳定复现。

细化实验对下垂、球面覆盖、折叠下落分别使用 0.25 ms、0.125 ms，以及 17×9 网格（默认 9×5）。加密球面覆盖出现表面相交，其他 8 次通过；不能据此宣称时间／空间单调收敛。默认开发球面覆盖的最大球面穿透为 **0.03676 mm**，下垂固定边误差为 **0.138 µm**；它们是名义配置的数值观测，不是实测材料精度。

[全部逐场结果及开发失败](evidence/cloth-v1.json) · [完整原始证据包](https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz)。归档包含轨迹、源码快照、原生场景、日志、早期失败和 SHA-256 清单。离线重评分不需要启动 Isaac Sim：

```bash
# 在独立目录解压证据包，然后对其中的完整实验目录评分
.venv/bin/python -m dexlab.cloth_benchmark verify \
  /path/to/extracted/demos/physx-contact/runs/cloth-test-final-v2/test-drape-03-physx-surface
```

该失败实例预期返回非零退出码。GIF 来自首轮开发集的完整 0–3 s 轨迹，25 fps 回放，使用 MuJoCo 仅绘制已记录网格，不推进物理。主机逐步计时包含进程通信和状态读回，且采集时有其他仿真并行运行，不作为隔离条件下的引擎速度排名。

## 失败回放

![留出球面覆盖失败](media/cloth-drape-failure.gif)

[连续失败视频](media/cloth-drape-failure.mp4) · [来源](media/cloth-drape-failure.json)。这是上述 `test-drape-03` 的完整记录，标题明确标为失败；相交时刻和数量以原始轨迹的独立评分为准，25 fps 视频不能证明逐物理步无相交。
