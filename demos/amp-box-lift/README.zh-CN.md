# 公开 AMP 抬箱基线

[English](README.md) | [简体中文](README.zh-CN.md)

准备公开的 `Mjlab-G1-DualArm` 权重，用于独立检查真实接触承载。这是使用 Toaster003 资产的 AMP 任务，与同仓库的 SuperMimic/PPO-Sim tracking 任务及其 1.5 kg 箱体分别记录。两个 0.2 秒原生探针已完成，但记录器一致性在第二个控制终点失败（qvel 差 2.193451e-5 > 1e-5）。三个完整种子和禁用手部接触负例未运行。见[完整探针报告](../../docs/site/zh/amp-lift.md)、短探针全程回放与可下载数值证据。

## 准备固定输入

固定来源为 [humanoid-amp-ppo 的 4889389 提交](https://github.com/shuayyy/humanoid-amp-ppo/tree/4889389118e0c88d3945dff54d2cd3f992ed815e)。在数据盘选择新目录，保留至少 50 GiB 空闲空间。共享研究主机上使用 `scripts/research_guard.py` 和 `scripts/bounded_run.py` 的 archive 限额执行传输。

```bash
python demos/amp-box-lift/fetch_source.py "$OUT"
```

入口检出精确提交，下载 11,932,163 字节的 `models/dualarm.pt` 和两段动作数据，核对 Git blob 身份并记录 SHA-256。保留上游锁文件，不下载无关视频和其他策略权重。输出目录已存在时拒绝覆盖；中断目录保留供诊断。此步骤不安装环境、不执行策略、不训练模型。

`inputs.json` 只证明字节身份。源仓库的 README 和包元数据声明 Apache-2.0，但没有单独的许可文件。原始动作采集和权重训练的数据来源尚未独立核实；原生准入或重新分发评估须保留这一限制。DexLab 不打包外部权重、动作或网格。

[资产来源记录](provenance.json)确认 `g1_realsense.xml` 引用的全部 35 个网格与 [Unitree 的 BSD-3-Clause 源文件](https://github.com/unitreerobotics/unitree_ros/tree/15ebe53f4cd77e7d745ae83b9d7ff90e685e8998)具有相同 Git blob。Toaster003 的六个视觉文件也与 [RoboCasa 资产索引](https://github.com/robocasa/robocasa/blob/2ce1aecdd76e29b52d32fdb160436c5a3e230b07/robocasa/models/assets/box_links/box_links_assets.json)链接的归档逐字节一致；[其 README](https://github.com/robocasa/robocasa/blob/2ce1aecdd76e29b52d32fdb160436c5a3e230b07/README.md)声明资产使用 CC BY 4.0。AMP 的 XML 增加自由根、抓取位置／碰撞标记及显式惯性参数；参考归档的 XML 为 9,389 字节，两份 XML 的哈希本来就不同。这些核验确认了指定文件的来源关系，不证明原始训练数据来源或物理结果。

## 分开记录任务条件

- 公开 AMP 任务使用高摩擦抓取标记几何。读取实际原生接触参数和编译后的质量惯量，不能套用 tracking 箱体的尺寸或 1.5 kg 质量。
- 源端 `play=True` 关闭虚拟 PD、curriculum 和观测扰动，但保留 25% 参考状态初始化及物体 XY/朝向随机化。记录实际初态，区分站立起始和参考状态起始。
- 启动时还保留物体主刚体质量缩放（0.7–1.5）、机器人/物体质心偏移，以及脚部/机器人/物体摩擦随机化。XML 的名义惯性质量合计为 1.30 kg；每回合实际质量、惯量、质心及接触参数须从执行中的 GPU 模型读取，CPU 模型模板不包含这些随机化结果。
- 源端保持判据要求高度超过单侧阈值、两侧标记传感器持续 20 个控制步，即 0.4 秒。传感器 `found` 不等于接触有承载力；该分数与独立承载、滑移、额外支撑及动量诊断分别保存。
- play 回合长 60 秒。必须在超时自动重置之前保存最后一个原生子步，不能拿重置后的观测替换轨迹终点。

源锁文件固定 mjlab 1.4.0、MuJoCo 3.10.0、MuJoCo Warp 3.8.0.2、Warp 1.15.0 和 Torch 2.13.0。该参考组合与落地案例、DexLab 当前提交门禁环境分别保留；隔离候选环境可以执行两个短探针，但仍有五项依赖声明冲突，记录器一致性检查失败。

固定依赖的元数据存在矛盾：[mjlab 的 pyproject](https://github.com/mujocolab/mjlab/blob/4360096b49c1bcc478668c11ce7d458db747e49d/pyproject.toml) 要求 MuJoCo Warp `>=3.8.0.3,~=3.8.0`，其选定的 [Warp 提交却声明 3.8.0.2](https://github.com/google-deepmind/mujoco_warp/blob/88b55fc2696960b927bc12584994bb8412b36558/pyproject.toml)。选定候选使用官方 MuJoCo Warp **3.8.0.3**，其余源锁版本保持不变。[发行版差异](https://github.com/google-deepmind/mujoco_warp/compare/88b55fc2696960b927bc12584994bb8412b36558...79c37d3e8630aba40c2b8023fa9a073fb27b62d0) 只涉及版本元数据及基准脚本；两个提交的完整 `mujoco_warp` 运行时代码子树具有相同 Git 身份 `97b878909d10a074f357f5b2a9b588e6cd696a67`。这在保留引擎代码的前提下解决版本约束，但不证明原生兼容性。源项目对 MuJoCo 的显式依赖覆盖也保留，不能静默换掉 MuJoCo 3.10.0。

## 安装隔离的候选运行时

[requirements-linux-cp312.txt](requirements-linux-cp312.txt) 固定 Linux x86_64 / CPython 3.12 的包、公开哈希与 Git 提交。这是候选安装步骤，原生环境尚未验证。它保留源端锁文件的显式依赖覆盖，因此使用 `--no-deps`，避免重新解析出另一套依赖。

将 `DEXLAB_ROOT` 设为本仓库，`SOURCE` 设为已核验的源码目录，`AMP_ENV` 设为数据盘上的**新**环境目录。安装应在有界 archive 窗口内使用数据盘缓存执行；需下载约 3.2 GB，可能构建固定版本的 evdev 源码包。失败时保留环境和日志，不重置其他环境。

```bash
test "$(uname -s)" = Linux && test "$(uname -m)" = x86_64 || exit 1
test ! -e "$AMP_ENV" || exit 1
uv --no-config venv --python 3.12 "$AMP_ENV"
uv --no-config pip install --python "$AMP_ENV/bin/python" --no-deps \
  -r "$DEXLAB_ROOT/demos/amp-box-lift/requirements-linux-cp312.txt"
uv --no-config pip install --python "$AMP_ENV/bin/python" --no-deps \
  -e "$SOURCE/rsl_rl" -e "$SOURCE" -e "$DEXLAB_ROOT"
```

下文原生命令使用该环境的 Python。运行入口在创建环境之前独立检查包版本、Git 来源、wheel 哈希及实际导入的源码路径。安装成功不代表 CUDA 执行或记录器一致性已合格。

保留 `--no-config`：源项目宽松的 `mujoco>=3.8.0.dev0` 覆盖配置会替换显式 wheel 要求。首次安装因此选到了 3.17.0，元数据核查在任何原生启动前将其拦下。随后仅恢复冻结的 3.10.0 包，保留失败审计与安装日志。修正后的 130 个 wheel 版本／安装来源和三个源码包均与清单一致；MuJoCo 与 MuJoCo Warp 已安装代码另与通过哈希检查的官方归档逐项核对。安装器缺失的归档哈希字段不手工伪造。

仍有五项依赖声明冲突：DexLab 应用层的 UniLab／UniSim 依赖未装入此参考环境，Torch 声明也与参考栈不同；mjlab 声明 MuJoCo `~=3.8.0`、mjviser `>=0.0.14`，源端则固定 3.10.0，选定 mjviser 提交声明 0.0.13。保留这些冲突及原始来源的覆盖关系，不宣称整个环境兼容；必须由有限的无界面探针资格认定实际执行路径。

将 `MUJOCO_WARP_WHEEL` 设为在传输窗口中下载并保留的[官方 3.8.0.3 wheel](https://files.pythonhosted.org/packages/82/f5/30c736dfe87ad7e8f7a7f8f43b80e0ff43c6af46cef65ba95d3ba172129a/mujoco_warp-3.8.0.3-py3-none-any.whl)路径。冻结 SHA-256 为 `dfbfa24e376e0b03bf6dcebaed7ef69b4885280a020e5f0fd805c125fae3d129`。每次原生启动都会检查归档及其代码与已安装发行包是否一致，不依赖可选的 PEP 610 哈希元数据。

## 有限评测入口

`protocol.json` 指定两个独立进程的记录器一致性探针、三个 60 秒策略回合（种子 137–139），以及种子 137 的四个手／腕碰撞几何禁用负例。该负例也移除这些几何与地面的碰撞；其他身体部位仍可能支撑物体，必须单列。上限为六次原生启动、每进程 900 秒、累计 5,400 秒。协议本身不构成启动准入：输入来源、独立运行环境及基于实测的资源方案仍须核验。

满足前提后，只创建一次新的持久预算；每个命名案例均在已有 research guard 和 bounded runner 内执行：

```bash
python demos/amp-box-lift/init_budget.py "$BUDGET" --resource-plan "$RESOURCE_PLAN"
CUDA_VISIBLE_DEVICES="$GPU_UUID" python demos/amp-box-lift/run.py --upstream "$SOURCE" --budget "$BUDGET" \
  --case probe-native --output "$RUN" --resources "$RESOURCE_RECEIPT" \
  --mujoco-warp-wheel "$MUJOCO_WARP_WHEEL"
```

`RESOURCE_RECEIPT` 是外层 `bounded_run.py` 的资源回执，不是手填成功标志。另起进程和新输出目录运行 `probe-recorded`，再离线执行 `python demos/amp-box-lift/qualify.py --budget "$BUDGET"`。准入比较完整控制记录、实际随机化模型、原生子步和独立力解码，并要求两个服务的最终资源遥测。完整回合拒绝缺失或已变化的资格记录。超时或中断预算必须恢复，不能重建预算清除已用次数。

每次原生调用的外层 bounded runner 须指定 `--gpu-uuid "$GPU_UUID" --gpu-memory-limit-mib 20480`，并让 `CUDA_VISIBLE_DEVICES` 使用同一 UUID；协议要求设备至少保留 2,048 MiB 空间。启用后的保护每 2 秒采样整张显卡占用，超限或遥测缺失时只停止本次工作进程组，并保留最终资源回执。这是采样停止阈值，不是 GPU 硬分配上限；采样间峰值不可观测。不使用这些选项的既有 bounded 运行保持原行为。AMP 入口在创建环境前拒绝缺失或不匹配的实时资源记录。

运行器沿用源端 actor 加载与推理路径、动作裁剪和唯一一次初始重置，在原始自动重置前捕获终止反馈。同时保留该终点与返回的重置后观测，标明两者含义。入口没有渲染器、训练调用或新增状态注入。短记录探针已有独立完整性诊断及保存姿态的全程回放；完整回合和对应物理评分／视频仍被一致性失败阻塞。

## 记录器实现状态

`dexlab.amp_lift_record.AmpLiftRecorder` 观察原始 `sim.step()` 边界，保留 CUDA graph。逐原生子步记录前后状态、外加力、求解迭代数、原始接触/约束数组及 Warp 原有解码器输出的接触力；同时保存随机化后的 GPU 模型参数和 CPU 模型模板。接触容量溢出会被拒绝，中断时保留当前动作已观察到的前缀。记录器不执行 `mj_forward`，不替换为 CPU 求解。

`dexlab.amp_lift_audit` 从保存的已解约束独立换算接触力。解析夹具覆盖棱锥/椭圆摩擦表示、未激活接触、缺失/越界地址，以及故意篡改的力。离线测试也拒绝缺少最终资源遥测的探针，并检查自动重置前的保持状态得以保留。这些仅是表示和记录完整性测试，不证明持续承载或原生记录器资格。

该模块还按明确的编译后几何 ID 区分左手、右手、地面与其他接触作用于物体的力/力矩；在合力抵消前统计承载接触对，并依据每个刚体的质量、惯量和原生质心运动学计算整个关节化物体的动量。坐标换算也与独立的 CPU MuJoCo 子树运动学夹具一致。这些辅助函数不假设 step 返回后的全部字段都属于积分后时刻，也不据此判定任务成功。

## 离线轨迹诊断

记录运行后，在新输出目录复算诊断：

```bash
python demos/amp-box-lift/score.py --run "$RUN" --output "$AUDIT"
python demos/amp-box-lift/pair.py --reference "$SEED137_RUN" \
  --negative "$NO_HAND_RUN" --output "$PAIR_REPORT"
```

报告保留每段连续双手承载窗口、地面／其他承载、物体倾斜和穿透、手坐标系内的相对位移、执行器接近力限幅的采样、外加输入及相邻时刻动量残差。它检查初态、每个子步衔接和重置前终点，独立解码接触力，并记录全部输入文件哈希。原生 float32 时钟按其真实舍入加法核验；固定绝对时钟容差会误拒回合后段的正常子步。

窗口时长按原生步数乘协议步长计算，同时单列量化后的原生时钟间隔。净抬升读取已识别的物体自由关节在初态与重置前最后积分状态中的位置；接触计算时刻的采样抬升另外报告，避免用最后一帧派生位置替代积分后终点。

2 秒承载诊断拒绝地面支撑和末帧偶然到位。手坐标系相对位移排除手与物体共同运动，但不等于接触材料点滑移。动量残差当前只计接触与重力；armature、外加广义力、非接触约束及积分效应仍需归因后才能作物理资格判断。最后一个积分后终点没有后续原生运动学采样，因此完整 12,000 子步只能提供 11,999 个相邻动量区间。源端成功与 `task_success: null` 分开保留。解析夹具已检查这些区别。实际短探针还暴露了固定子刚体地面的分类问题，评分器现按 world weld ID 识别，原失败仍保留。短探针记录完整性通过，完整原生评测仍受阻。

`pair.py` 核对两个完整种子 137 回合的权重／运行时身份、初态及有效物理模型，仅允许四个预先声明的手／腕碰撞掩码变化。禁用几何会改变编译器生成的碰撞候选列表长度，因此该列表不作恒等比较；绕过掩码的显式接触对仍会被拒绝。质量变化或初态不匹配时，不能把该负例解释为配对对照。

## 保存姿态回放

完整记录通过独立完整性评分后，使用相同 MuJoCo 版本和已有系统 FFmpeg 渲染全轨迹：

```bash
python -m dexlab.amp_lift_replay --run "$RUN" --audit "$AUDIT" \
  --protocol "$DEXLAB_ROOT/demos/amp-box-lift/protocol.json" --output "$REPLAY"
```

入口核对全部已评分输入与诊断曲线的哈希，保留初态和每个 50 Hz 控制终点，包括自动重置前的终点；重置后返回的观测不能替换它。每个边界显示一帧，因此 60 秒回合额外保留最后一帧。清单记录实际原生时钟、视频时长及每帧对应的最后一个已完成受力子步。

保存的编译几何只通过 `mj_kinematics` 和 `mj_camlight` 更新，不进行积分、碰撞查询或力求解。曲线保持原生力与派生状态的计算时刻；回放不是新的物理结果，CPU 几何模板也不模拟 GPU 的质量／质心／摩擦随机化。短探针全部 11 帧已渲染；完整 60 秒回放仍需通过资格的完整回合记录。

[#259](https://github.com/huangkiki/Dexlab/issues/259)继续承接有限原生协议、正负例、独立评分、完整轨迹及双语结果。缺失的 tracking 权重、无箱 squat/带箱 lift 对照，以及任何匹配条件下的 SuperMimic/PPO 比较均保留为独立义务；AMP 输入准备不完成这些项。
