# 到底哪个 solver 失败了？2026-10-21 复盘

**本轮在 Newton 1.7 复现了 Kamino–VBD 默认双连接的构建兼容性失败，并找到可绕过它的官方配置。既有实验中最明确的物理机制证据，是 Genesis 1.4.3 的 legacy PBD–rigid 路径缺少切向摩擦，并存在一个时间步的反力延迟。RSS 海绵擦拭证明了被测配置依赖 latch 辅助保持，尚不能唯一归因于 SuperDex 求解算法。现有记录没有建立合格的 Wuji 手内操作 solver failure case。**

一次操作失败涉及几何、材料、控制、接触、耦合和数值求解。下文分别报告功能缺失、固定配置失败、数值诊断、合理的负对照和运行错误。成功例同样保留，避免为了寻找失败而遗漏反证。

## 本轮新增的直接对照

### Newton 1.7：默认双连接构建失败，关闭近邻代理可绕过

按 [Discussion 4055](https://github.com/newton-physics/newton/discussions/4055) 的原始最小模型，在 Linux / RTX 4090 / Newton 1.7 / Warp 1.18 上检查 Kamino 刚体与 VBD 绳索的跨求解器 FIXED 连接。保留原模型和 ADMM 配置，只控制是否添加第二处连接。

| 条件 | 本轮结果 | 结论范围 |
|---|---|---|
| 一处 FIXED 连接 | 构建成功；6 个刚体推进 10 × 1 ms，记录有限 | 单连接构建与短步进正对照，不是约束精度验证 |
| 两处 FIXED 连接 | 两次均在 Kamino 构建校验处拒绝 `ROD (3 instances)` | 当前默认近邻关节可见性配置下的分区兼容性失败 |

随后冻结的两次诊断仅将官方选项 `joint_proximal_bodies` 从默认 True 改为 False。单连接与双连接都构建成功，并分别推进 10 × 1 ms，全部记录有限。因此已找到可以绕过构建拒绝的配置；这还不是连接误差、力传递或完整操作精度的验收，不能宣称整个耦合问题已修复。原默认配置的两次失败保留。

失败发生在 ADMM 迭代开始之前。源码先按跨岛关节扩展近邻可见性，再创建各 solver 的模型视图；Kamino 拒绝其中的 ROD 关节。这里没有证明 ADMM 不收敛、所有配置都不支持双连接，也没有重现作者较大场景中的 CUDA 700。

首轮导入路径和后续碰撞缓冲参数两处错误来自审计脚本，均已修正并保留原记录，不计为 solver 失败。最终正对照使用官方 `CollisionPipeline.contacts()` / `collide(state, contacts)` API；引擎源码未改动。


实现位置：[ADMM 近邻可见性](https://github.com/newton-physics/newton/blob/7e75abe28b8d69522bc0b34837aaed2c303dff5a/newton/_src/solvers/coupled/solver_coupled_admm.py#L717)、[Kamino 关节校验](https://github.com/newton-physics/newton/blob/7e75abe28b8d69522bc0b34837aaed2c303dff5a/newton/_src/solvers/kamino/solver_kamino.py#L1465)。

### MuJoCo–VBD 毛巾夹取：耦合配置影响任务成败

RSS 原生 YAM 毛巾场景使用 60 Hz 控制、16 子步、VBD 5 次迭代、完整表面接触。相同原版场景和控制器，仅切换耦合配置；下表是独立进程重复，不是未见任务泛化。原版阈值为抬升超过 60 mm、末端到位误差小于 10 mm、至少半数夹持区域粒子留在手边、保持位移小于 20 mm。

| 尝试 | 耦合／传递模式／外迭代 | 布料抬升 mm | 保持位移 mm | 留在手边 | 末端误差 mm |
|---|---|---:|---:|---:|---:|
| `towel-one-way-01` | one_way | 96.5145 | 3.838 | 85.7% | 3.983 |
| `towel-proxy-01` | Proxy/staggered/1 | 0.0000 | 106.121 | 0.0% | 3.875 |
| `towel-one-way-02` | one_way | 96.3007 | 3.856 | 85.7% | 3.983 |
| `towel-proxy-02` | Proxy/staggered/1 | 0.0000 | 106.134 | 0.0% | 3.878 |
| `towel-one-way-03` | one_way | 96.3647 | 4.041 | 85.7% | 3.983 |
| `towel-proxy-03` | Proxy/staggered/1 | 0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-4iter-01` | Proxy/staggered/4 | 0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-16iter-01` | Proxy/staggered/16 | -0.0000 | 106.123 | 0.0% | 3.877 |
| `towel-proxy-4iter-02` | Proxy/staggered/4 | 0.0000 | 106.116 | 0.0% | 3.873 |
| `towel-proxy-16iter-02` | Proxy/staggered/16 | -0.0000 | 106.121 | 0.0% | 3.876 |
| `towel-proxy-lagged-01` | Proxy/lagged/1 | -0.0000 | 106.123 | 0.0% | 3.873 |
| `towel-proxy-lagged-02` | Proxy/lagged/1 | 0.0000 | 106.126 | 0.0% | 3.874 |

“没有提起布料”不自动等于“抓住后滑落”。控制算法相同，但它根据实际状态决定下一阶段，因此步数和实际命令历史并不完全相同。第三对中，17 项编译模型数组完全一致；预热/重置后的粒子位置最大差 5.424 µm、速度最大差 6.437 mm/s，不能称为逐位相同初态。额外手部读回显示：Proxy 下压阶段耗尽 600 步到位预算，闭合结束仍距夹持目标 7.58 mm、夹爪宽 9.56 mm，未建立有效抓取；one_way 可到位但不承担布料反力。因此这是耦合配置与控制器的任务兼容性失败，不能当作已合格抓取后的保持失效，更没有证明 Proxy 不收敛。尚未独立验证每个子步的接触几何或真实材料。

外迭代 4/16 次及 lagged 传递是观察首轮失败后预先冻结的诊断设置，不是独立 holdout，也不覆盖所有参数。源码未修改，失败未删除。

### 新版 RSS 海绵擦拭：保持辅助的配对消融

Newton 1.7 / MuJoCo 3.15 / SuperDex 1.0 FP32。移除附加节点约束与随手更新，保留原控制和 12 tick 接触就绪条件；使用原版任务阈值及未改动的 DexLab 独立材料点评分器。位移跟踪的是同一块材料在实测手坐标系里的移动，不能与其他口径的“滑移”混用。

| 尝试 | 记录一致性 | 任务通过 | 清洁比例 | 夹持材料位移 mm | 实际 latch 组数 |
|---|---|---|---:|---:|---:|
| `wipe-current-original-01` | True | True | 95.47% | 0.061 | 1 |
| `wipe-current-no-latch-01` | True | False | 47.33% | 446.256 | 0 |
| `wipe-current-original-02` | True | True | 95.88% | 0.060 | 1 |
| `wipe-current-no-latch-02` | True | False | 46.09% | 440.653 | 0 |

两对的编译模型、初始/静置粒子数组与跟踪材料索引完全一致，四份记录独立检查全部通过。两次无 latch 的实际约束计数均为零。

latch 不是胶水或刚性焊接：它用额外柔顺节点约束带动海绵局部。成功证明的是带该辅助的配置可完成任务；去掉辅助后的失败定位到这一完整配置，尚未把 SuperDex 接触律、反力传递和控制逐一隔离。场景与阈值来源：[原版擦拭](https://github.com/robosimstudio/robosimstudio/tree/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/wipe_the_bar)、[原始独立评分器](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos/rss-wiping/score.py)。


## 既有 DexLab 证据能归因到哪里

| 配置 | 观测 | 支持的结论 |
|---|---|---|
| Genesis 1.4.3，legacy PBD–rigid | 摩擦输入 0.01 与 0.5 的完整轨迹相同：0.3 s 横移 60 mm，仍保持 0.2 m/s；支撑与禁用耦合对照有效 | 此路径缺少切向相互作用；不代表 Genesis IPC 耦合 |
| 同路径，自由布料与自由 1 g 板，零重力 | 布料第 56 步动量变化 3.2e-5 kg·m/s，板第 57 步才收到反向变化；同时间残差超过 3.3e-7 阈值 | 测得一个 2 ms 步长的反力延迟，与源码次序一致；最终动量抵消不能覆盖瞬态失败 |
| 历史 RSS 擦拭，Newton 1.6 / MuJoCo 3.12 / SuperDex 1.0 FP32 | 匹配三对：原版 3/3 通过，无 latch 0/3；后者清洁 39.92–41.15%，夹持材料区域相对手位移 440.47–449.98 mm | 被测配置依赖辅助保持；不是作者 69/226/218 mm 的同一批数据，尚未分离接触律、控制与耦合的贡献 |
| SuperDex 1.0 FP64，有限指垫边缘接触 | 同一棱柱表面 256→1,024→4,096 三角形，过载峰值穿透 2.267→0.858→0.481 mm，动量变化率残差/重量 7.036→0.216→0.000993；缩步长和 100→400 次迭代未消除原失败 | 对表面离散敏感，最细网格通过冻结控制；不是一般性修复证明 |
| MuJoCo 3.15，临界载荷夹持 | 容差 1e-6→1e-10→1e-14，冲量残差 1.234e-6→1.240e-8→1.245e-10 N·s，但约 2 mm/s 蠕滑仍在 | 数值闭合与软接触保持是不同要求 |
| Genesis 1.4.3，刚体接触 | 名义零摩擦被钳制为实际 0.01，接触读回与斜面加速度差一致 | 此版本接触模型的表达边界 |
| Newton 1.6.1 VBD compliant | 固定第 16 步，99/101/1001 与 100/1000 终端迭代形成两组位置和返回力，残差约 4.31e-6 / 4.04e-6 N·s | 局部终端更新现象；没有证明全状态严格周期或一般性唯一根因 |

来源：[Genesis 布料](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/genesis-cloth.md)、[匹配擦拭对照](rss-wiping.md)、[接触开发实验](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos/contact-benchmark/README.md)、[夹持冲量诊断](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/pinch-impulse-results.md)、[Genesis 斜面](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/genesis-incline-results.md)、[Newton 斜面](https://github.com/huangkiki/Dexlab/blob/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/newton-incline-results.md)。

这些是历史证据。本轮重新核验注册表绑定的 **147 个文件，全部哈希一致**；按冻结评分器重算 Genesis 平面摩擦与自由体耦合原始记录，两份结果与已发布评分完全相同。注册表有 74 条引擎/配置行、54 个 cohort、13 类任务；8 项研究经验、15 个 demo 和 30 个证据目录与它们重叠，不能相加为独立实验次数。

## RSS 的成功需要附带哪些条件

RSS 是编排工具，不能整体称为“统一 IPC solver”。被测示例分别使用 MuJoCo/MuJoCo-Warp、Newton VBD、SuperDex 和 Genesis，不同任务的反馈路径不同。

| 机制 | 已展示的能力 | 对解释的限制 |
|---|---|---|
| 毛巾 `one_way` | 接触与摩擦让布料随手运动 | 布料反力不加载到手臂 |
| 纸张 `one_way` + `slide_feedback` | 软体接触负载可让夹爪滑动关节在力限处停住 | 延后一子步的等大反向力施加在滑动关节两侧，机器人净力与净力矩为零；不等于完整双向反馈 |
| 海绵 latch | 接触就绪后，柔顺节点约束带动夹持区域，开爪后解除 | 是摩擦以外的辅助保持，不是刚性焊接 |
| 标签刚性拉片 | 通过摩擦夹住拉片并揭开标签 | 没有测试直接夹住自由变形的薄膜 |
| 绳索历史接触 | 特定接触配置可保持、布线 | 示例夹爪摩擦系数为 60，没有标定为某种真实材料 |
| 吸盘 weld / wrench | 既定吸附模型可保持与释放盘子 | 吸附保持不能当作纯摩擦抓取证据 |

[上游配置](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/robosimstudio/specs/arrangement.py)、[单向与滑动关节反馈实现](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/robosimstudio/scene/physics/couplers.py)、[绳索条件](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/route_the_cable/README.md)。

### 绳索补充检查：测试通过也可能是在确认限制

本轮原版 `tests.test_superdex_cable_robot` 的 8 项断言全部通过。其中一个明确的限制对照是：在 `feedback="off"` 下，对直径 22 mm 绳索发出全闭合命令，夹爪仍能闭到小于 3 mm。该项的“通过”确认了缺少反力阻挡，不能计作成功的物理抓取。按示例的 0.80 夹持量控制时，实测宽度 19.20 mm、抬升 112.82 mm、保持漂移 0.412 mm。两种控制的区别说明，单看物体有没有抬起会漏掉接触问题。[原版测试与限制说明](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_superdex_cable_robot.py)

此前的柔软拉片小实验**不具备 solver 失败归因资格**：首次实验未成功夹住，后续预定位实验存在初态/几何问题，最后刚性正对照本身也未通过。原版刚性拉片控制则揭开了全部 144 个黏附连接。8 次尝试及 339.306 s 累计时间全部保留，不把调试失败转写为物理结论。


本轮清单的当前统计：50 个入口中 50 个通过各自范围断言，0 个跳过，0 个失败/错误待归因，0 个未完成。这不是整套测试零失败；原始失败与后续重跑见下文，完整清单保留限定条件。

[完整清单：50 个公开入口、18 个论文展示、30 个证据目录和 15 个 demo](solver-failure-inventory.md)

## libuipc / Newton 已知问题核查

本节核查源码与问题现状，Newton 4055 另有前述本地检查；没有遍历这两个项目各自的全部 examples。

| 来源 | 2026-10-21 核查状态 | 能支持的判断 |
|---|---|---|
| [Newton 4055](https://github.com/newton-physics/newton/discussions/4055) | 作者报告 Newton 1.5 / Warp 1.16；本轮在 Linux / Newton 1.7 重现双连接构建拒绝，单连接可推进，详见前文 | 默认分区兼容性问题；关闭近邻代理后可构建及短步进，不是 ADMM 数学不收敛 |
| [Newton 3660](https://github.com/newton-physics/newton/issues/3660) / [修复 3664](https://github.com/newton-physics/newton/pull/3664) | 过量分配软接触缓冲区的修复于 7 月 30 日合入 `36b2ddfe`；已检查 Newton 1.7 按兼容接触对计数分配 | 历史容量／集成问题，不应继续列为当前未修复的物理问题 |
| [Newton 1599](https://github.com/newton-physics/newton/issues/1599) | 已关闭；评论给出小惯量、碰撞 margin、旧法向、MuJoCo/MJWarp 路径等不同解释 | 保留版本和条件，不把单条评论当成独立证实的唯一原因；增加 armature 改变了惯量模型。本轮未独立复现 |
| [libuipc 423](https://github.com/spiriMirror/libuipc/issues/423) | Open；所查主分支 `c283e98` 中接触厚度与材料厚度仍耦合 | 建模表达限制，不是已验证的灵巧操作失败 |
| [libuipc 467](https://github.com/spiriMirror/libuipc/issues/467) | 10 月 20 日关闭；样例仓库 `b70f322` 的 sample 95 已使用分方向拉伸模量，需要新源码构建，旧 0.0.29 wheel 没有该 API | 旧的各向异性材料缺口不能继续作为当前源码缺陷；样例关闭重力与接触做双轴拉伸，不是接触验证 |
| [libuipc Discussion 193](https://github.com/spiriMirror/libuipc/discussions/193) | `ExternalArticulationConstraint` 已实现 | “只能 SoftTransform、不能关节驱动”的旧说法已过时；接口存在不等于闭环操作已验收 |
| [libuipc 413](https://github.com/spiriMirror/libuipc/issues/413) | Open，涉及 CMake 构建 workaround | 构建问题，不是仿真物理失败 |

本地既有 pyuipc 0.0.28 的 FEM/ABD 100 步、reset 和 FP64 读回检查只建立生命周期与精度身份，不能判断灵巧操作的成败。新样例库另有四指苹果转移示例，本轮没有声称 libuipc 缺少机器人抓取能力。

RSS 源码还有版本差异：`arrangement.py` 将 Proxy 夹布困难解释为不能回收完整表面接触反馈；但已安装 Newton 1.7 的 VBD `coupling_supports_full_surface_soft_contacts()` 返回 True，当前 Proxy 场景也能构建并执行。旧注释不能直接充当本轮失败的唯一原因。


## 运行错误与物理结论分开记账

清单按各入口的断言及完整记录判定，不意味着 RSS 整个测试套件全绿。`tests.test_examples` 的一次模块执行保留了 28 个父测试中的 1 个失败、21 个错误／子测试错误事件和 1 个缺少 Genesis 的跳过：

- 独立绳索子进程在父环境未设置 GPU 时收到空的 `CUDA_VISIBLE_DEVICES`，进入 CPU SuperDex 路径；断言却假设 GPU VBD。显式指定 GPU 后原测试通过。这里定位的是环境／测试入口假设。
- 长时间循环创建页面时，首个有效错误是 dough Nanogrid 分配 CUDA 显存不足，随后出现 CUDA 700 和极小分配失败。dough、new-kind、towel 三个页面在独立进程重跑通过。没有据此宣布 21 个错误都已逐项修复，也不把被污染上下文中的每个报错当成物理失败。
- 本地 Newton 审计脚本先后出现导入路径和碰撞缓冲 API 错误；均在负责入口修正，原失败与耗时保留。安装脚本的首次 PATH 错误也独立保留。它们不是上游 solver 的结果。

基础环境在本批实验后核验 2,248 个引擎文件，全部与已安装 wheel 的 RECORD 哈希相符；源码干净状态按每次调用检查。这里没有声称做过不存在的批前逐文件校验，也没有因依赖或运行失败改变物理阈值。


## 本轮执行与复现口径

范围是 RSS 全部公开示例及 DexLab 相关既有实验；libuipc/Newton 核查已知失败。RSS 固定为 `b001cc7e10a83577261aac4471fa45e0ced6d415`，DexLab 历史基线固定为 `c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3`。RSS 基础环境按官方锁文件安装：Python 3.12.12、Newton 1.7.0、MuJoCo/MuJoCo-Warp 3.15.0、Warp 1.18.0、SuperDex 1.0 FP32；Genesis/GaP 扩展使用独立冻结环境，没有批次内升级。

扩展环境为 Genesis 1.3.3、Quadrants 1.3.0、pyuipc 0.0.28、Torch 2.10.0，Newton/MuJoCo/Warp 与基础环境同版本。执行前逐项核对 211 个适用的 registry 版本约束，全部匹配。安装采用了单独记录的方式：镜像下载保留原锁文件哈希；三个大型 wheel 分段下载后校验完整 SHA-256；GaP 及 core 从固定 `09e45f8` 源码构建，未拉取无关的递归 benchmark 资产，RSS 本身也排除了这些 benchmark 依赖。最终离线 `uv sync` 因本地 wheel 来源身份拒绝而未通过，因此这里分别报告实际版本核验和来源／哈希检查，不称它为一次成功的完整 sync。物理断言没有改变。

原生调用使用上游 unittest 选择器，物理断言不变。构建、20 步 smoke、完整操作、目标评分、预期失败负对照及硬件 mock 各有不同意义，测试模块通过数不能替代操作成功回合数。源码保持干净，记录版本、命令、断言、资源收据及部分测量读回；几何预处理仅在输入/输出哈希一致时复用官方结果。原生断言不是逐子步独立碰撞或材料有效性验收。

在独立 checkout 中，可按清单选择相应测试。例如：

```bash
git clone https://github.com/robosimstudio/robosimstudio.git
cd robosimstudio
git checkout b001cc7e10a83577261aac4471fa45e0ced6d415
uv sync --frozen --extra superdex --no-group rtx
ROBOSIMSTUDIO_RENDERER=tiled JAX_PLATFORMS=cpu \
  .venv/bin/python -m unittest tests.test_example_grasps_cloth -v
```

水和策略任务需在另一环境安装官方 `genesis` / `gap` extras。命令给出原生入口，不承诺跨硬件相同结果；本地审计另加了有界执行和哈希核验的几何缓存。

实验在与桌面共享的 RTX 4090 上串行运行，实际 cgroup 上限为 16 GiB 内存、4 核、128 tasks、实验零 swap，桌面预留 8 GiB。新实验冻结上限为 100 次调用、累计 10,800 s、单次 600 s，最晚北京时间 23:00 停止；依赖安装与仓库交付验证单独记账。这些限制不构成统一速度基准。

执行账本最终保留 81 次新调用、累计 5,373.764 s，其中 64 次进程正常退出、17 次非零退出；非零退出包括被测失败及审计入口错误，不能当作 17 个独立 solver failure。此前柔软拉片的 8 次尝试、339.306 s 另列。可选依赖准备保留 10 次安装／下载阶段调用，累计 4,849.298 s，包含失败与取消；这不是物理运行时间。

扩展环境的最终补测包括四个策略入口、首次抓空后重试，以及倒水、目标评分、浅倾角和偏离目标两个负对照。10 次独立进程调用中的 18 项原版断言全部通过，无跳过。由此完成公开入口覆盖，不代表论文展示场景全部复现。

本地完整证据包保留账本、失败、来源快照、依赖版本、观测和对照实验的控制步轨迹。**本 PR 发布解读和清单，新原始数据包尚未作为公开 release 资产发布。** 历史公开证据见对应链接。论文场景缺失、正对照无效或物理真实性未知均保持未完成状态。

与既有讨论的关系：[Discussion 220](https://github.com/huangkiki/Dexlab/discussions/220) 提出了擦拭辅助约束和反力时序问题，本轮把辅助依赖更新为当前版本的配对证据；反馈滞后仍不能直接当作擦拭滑脱的唯一原因。[Discussion 222](https://github.com/huangkiki/Dexlab/discussions/222) 区分动作到位与接触效果，本轮毛巾诊断也要求先确认抓取是否建立。讨论中的轻触／按压／释放建议仍是独立提案，本轮没有据此启动其他开发。


剩余证据缺口与恢复条件记录在 [#247](https://github.com/huangkiki/Dexlab/issues/247)，不据此启动其他开发计划。


```{toctree}
:hidden:

solver-failure-inventory
```
