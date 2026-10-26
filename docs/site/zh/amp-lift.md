# 公开 AMP 抬箱：记录器一致性未通过

**两个 0.2 秒 AMP 探针正常结束，但记录前后的一致性检查失败。三个完整抬箱种子及禁用手部接触负例尚未运行。** 这是资格检查失败，不能据此判断策略抬箱失败，也不是完成的抬箱结果。

公开 `Mjlab-G1-DualArm` 权重使用 Toaster003。它与同仓库 SuperMimic/PPO-Sim tracking 的 1.5 kg 箱体任务不同；AMP 成绩不能替代缺失的 tracking 权重与评测。

![完整记录探针：0.2 秒，未通过抬箱资格](_static/amp-lift/probe.gif)

动图以 50 fps 展示全部 11 个保存的姿态边界：原生运动 0.2 秒，另加一个终点帧，播放长 0.22 秒。短探针中物体仍由地面支撑，这段时间不能评价 60 秒抬箱任务。回放没有重新推进物理。

<video controls preload="metadata" style="width:100%;max-width:100%;height:auto"><source src="_static/amp-lift/probe-replay.mp4" type="video/mp4"></video>

## 哪些检查通过，哪里停止

两个独立进程均使用种子 137、公开 actor、单环境、5 ms 物理步及每动作四个子步。初态、随机化后的有效模型、源码／运行时身份和第一条策略输入逐项相同。play 模式保留源码初始化及质量／质心／摩擦随机化，关闭虚拟 PD 和观测扰动。记录中的物体质量为 1.376522779 kg；1.30 kg 只是源码名义惯性质量总和。

| 检查 | 实际结果 |
| --- | --- |
| 原生执行 | 两个 10 动作探针正常完成，最终资源记录完整，无 OOM 或显存采样停止 |
| 第一个控制终点 | qvel 分量最大差 2.861023e-6，在冻结阈值 1e-5 内 |
| 首次越界 | 动作索引 1、0.04 秒处，qvel 最大差 2.193451e-5，大于 1e-5；相对容差仍为零 |
| 全部探针最大 qvel 差 | 动作索引 8、0.18 秒处为 5.917549e-4 |
| 记录完整性 | 40 个原生子步与 10 个控制终点通过连续性及独立力解码；力分量最大误差 1.525879e-5 |
| 完整评测 | 三个 60 秒种子及一个配对禁用手部接触负例：**未运行** |

qpos／qvel 使用原始数组比较，广义坐标含平移和转动分量；这些最大差不能当成单一物理位移或速度指标。只有一对未记录／记录探针，还无法区分原生重复运行波动与记录器影响。原资格结果继续为**失败**，没有放宽阈值。额外诊断重复需另行冻结并决定，不会把剩余完整回合名额自动改作重试。

第一次离线评分还暴露了独立的分类错误：地面位于有名字的固定子刚体，不是 body 0。评分器现按“与 world 焊接的平面”识别地面，固定箱体仍归其他支撑。原失败已保留，编译模型回归检查覆盖此情形；复算使用同一份未改动的原生记录。该修复没有解决或覆盖一致性失败。

## 独立复算证据

下载[数值证据归档](_static/amp-lift/probe-v1.zip)、[结果与归档哈希](_static/amp-lift/summary.json)及[回放来源记录](_static/amp-lift/probe-replay.json)。归档含两个完整控制流、40 个记录子步、有效模型数组、源码快照、失败资格记录、资源凭据和修正后的离线诊断。全部条目哈希与 ZIP CRC 已核对；解包复算的报告和全部数组与原评分完全相同。

```bash
unzip probe-v1.zip -d probe-v1
python demos/amp-box-lift/score.py   --run probe-v1/runs/probe-recorded-1 --output probe-rescore
```

使用本 PR 对应代码和新的输出目录；此命令不推进物理。归档不重分发编译 MJB、网格、权重或动作片段。画面资产来自 [humanoid-amp-ppo 4889389](https://github.com/shuayyy/humanoid-amp-ppo/tree/4889389118e0c88d3945dff54d2cd3f992ed815e)：Unitree G1（BSD-3-Clause）和 RoboCasa Toaster003（CC BY 4.0），保留源任务对模型的改动。[精确来源及改动说明](https://github.com/huangkiki/Dexlab/blob/main/demos/amp-box-lift/provenance.json)。原始动作采集及权重训练数据来源仍未独立核实。

## 运行时与剩余范围

隔离候选环境为 MuJoCo 3.10.0、MuJoCo Warp 3.8.0.3、Warp 1.15.0 和 Torch 2.13.0。选定 Warp 运行时代码子树与源码锁定的 3.8.0.2 提交相同。两个无界面探针能执行不代表全部依赖声明兼容：仍保留五项已知声明冲突。[案例 README](https://github.com/huangkiki/Dexlab/blob/main/demos/amp-box-lift/README.zh-CN.md)记录精确安装、官方归档／代码校验和首次安装失败。

原生账本为 **2/6 次启动，92.084833/5,400 秒**，原失败资格记录未改动。外层服务墙钟另计，分别为 88.988194 秒与 11.104492 秒。基于实测的资源方案为 32 GiB／4 CPU／零实验 swap，保留 8 GiB 桌面内存；整卡显存每 2 秒按 20,480 MiB 阈值采样，并要求至少 2,048 MiB 余量。采样间峰值不可观测，这不是显存硬分配上限。

[#259](https://github.com/huangkiki/Dexlab/issues/259)继续保留记录器资格、完整正负例、完整回合连续视频、物理解释，以及独立缺失的 tracking／squat／匹配比较输入。2 秒承载诊断、源端成功标记及仅含接触／重力的动量残差都不等于完整物理成功。本例不增加跨引擎已完成覆盖计数。
