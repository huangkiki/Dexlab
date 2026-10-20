# RSS 海绵擦拭：复现与 latch 对照

未改动的 RoboSimStudio 官方擦拭测试已通过 **全部 9 项断言**。独立运行的清洁率为 **95.5%**，对杆峰值接触力 **4.93 N**，保持阶段材料点区域质心在实测手坐标系下的最大位移约 **0.061 mm**。这复现了公开的辅助保持擦拭效果；手内旋转仍是另一个任务。

## 固定条件的重复实验

<!-- rss-results:start -->
**原版 3/3 任务通过；无 latch 0/3。** 六条记录均通过独立一致性检查，完整碰撞模型、初始与静置后的海绵状态、跟踪材料点索引也完全一致。

| 运行 | 清洁率（%） | 保持阶段区域质心位移（mm） | 最大材料点位移（mm） | 对杆峰值力（N） | 水平归位误差（mm） | 任务 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 原版 1 | 95.473 | 0.0606 | 0.764 | 4.910 | 0.046 | 通过 |
| 无 latch 1 | 39.918 | 449.9811 | 479.305 | 11.886 | 435.806 | 失败 |
| 原版 2 | 95.885 | 0.0606 | 0.760 | 4.895 | 0.059 | 通过 |
| 无 latch 2 | 41.152 | 444.9449 | 467.222 | 12.261 | 430.553 | 失败 |
| 原版 3 | 95.473 | 0.0608 | 0.764 | 4.932 | 0.044 | 通过 |
| 无 latch 3 | 40.329 | 440.4694 | 466.125 | 12.359 | 425.927 | 失败 |

无 latch 海绵在擦拭期间脱离夹爪。控制器随后检测到压靠失败，退出擦拭循环并归位；`done` 仅表示流程结束，清洁率与海绵归位条件仍失败。无 latch 组所有记录步的约束数均为零。

原版清洁率落在作者报告的 95.5%–95.9% 范围内。本次无 latch 批次低于作者报告的 68.7%–76.1%，跨批次差异的原因尚未隔离；此处的因果对照限定为共享本批固定几何的两组。[作者参考](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/examples/08_demos/wipe_the_bar/README.md)。

<!-- rss-results:end -->

预先选定每组第一次记录作为视频对照，完整展示任务过程。每秒仿真时间录制 10 帧，使用 RSS 自带的 tiled 碰撞几何视图。

```{raw} html
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">
<section><h3>原版：柔顺 latch</h3><video controls muted playsinline preload="metadata" style="width:100%" poster="_static/rss-wiping/original.png" src="_static/rss-wiping/original.mp4"></video></section>
<section><h3>无 latch：仅靠接触保持</h3><video controls muted playsinline preload="metadata" style="width:100%" poster="_static/rss-wiping/no-latch.png" src="_static/rss-wiping/no-latch.mp4"></video></section>
</div>
```

![六次完整轨迹：清洁率、材料区域相对位移与实测接触力](../../evidence/rss-wiping/comparison.png)

## 同一轨迹的 RTX 外观回放

已将原版第 1 次记录的 **10–20 s 连续片段**重渲染为 100 帧、10 fps、960×544 的 RTX 视频。下图左侧为 tiled 碰撞视图，右侧为 OVRTX 路径追踪，使用相同机位、相同时间戳与原始状态。金属反射、桌面纹理、机器人外壳光泽和柔和阴影来自固定版本 RSS 的材质、房间和灯光。

![同一状态与机位：左 tiled，右 RTX；10–20 s，原速回放](../../evidence/rss-wiping/rtx/comparison.gif)

[完整对照视频](../../evidence/rss-wiping/rtx/comparison-labeled.mp4) · [逐帧映射、输入哈希与状态核验](../../evidence/rss-wiping/rtx/render.json) · [媒体处理记录](../../evidence/rss-wiping/rtx/media.json)

此次回放执行 **0 个物理步**；刚体位姿、关节、海绵材料点和墨迹加载的最大绝对误差均为 0，100 对画面输出后状态与动态颜色保持不变。原始输入文件哈希也保持不变。恢复了录制时保存的地面显示开关，完整编译模型随后逐数组及哈希匹配；碰撞标志不允许改变。回放不插值、不平滑材料点，也不产生新的任务成功率。

在本次 RTX 4090、4 核等效配额的受限作业中，12 pass 的 RTX 渲染调用平均耗时 **81.75 ms/帧**，tiled 为 **3.61 ms/帧**；场景构建与预热合计 **9.80 s**。这些是该作业的渲染成本，不包含视频编码，也不构成独占硬件或端到端仿真吞吐基准。初次预检因地面显示标志未恢复而被完整模型检查拒绝；修正后两帧预检和连续片段均通过，失败记录保留。

复现需要完整 `states/*.npz` 原始记录及固定上游 RTX 环境；公开的摘要／CSV 无法代替软体顶点。见 [重渲染命令](https://github.com/huangkiki/Dexlab/blob/main/demos/rss-wiping/README.md#render-a-saved-trajectory--重渲染已有轨迹) 与 [渲染任务 #229](https://github.com/huangkiki/Dexlab/issues/229)。

## 固定了哪些条件

RSS 提交 [`23417de`](https://github.com/robosimstudio/robosimstudio/tree/23417de77edf59d614531a833334ed4e2206fc2c) 提供双 YAM 机械臂、海绵、杆、材料与脚本控制器。锁定组合为 Newton 1.6.0、Warp 1.18.0、MuJoCo/MJWarp 3.12.0 和 SuperDex 1.0.0；原生接口读回确认 SuperDex 使用单精度。控制频率为 60 Hz，每个控制周期有 16 个刚体子步、2 个 SuperDex 步。原版海绵参数为杨氏模量 80 kPa、泊松比 0.3、密度 110 kg/m³、摩擦系数 0.9、摩擦正则化速度尺度 0.1 mm/s。这些是示例设定，不是真实海绵的测量参数。

重复执行官方 CoACD 预处理时，完整模型分别出现了 499 和 505 个形状。因此，第一次带记录的原版运行单独作为**未配对参考**保留，随后缓存一次官方方法生成的分解。正式两组复用同一份 49／48 块凸分解，并核验输入、调用顺序、缓存数组与完整编译模型的哈希。上游源码和引擎二进制保持原样。

无 latch 版本保留抓取就绪条件：连续 12 个控制步稳定、开度变化不超过 0.3 mm、两侧法向力各至少 2 N、压缩量至少 2 mm。达到就绪条件后，跟踪相同材料点区域，取消 `pin_nodes` 和 `ride`，让流程继续擦拭。每个记录步检查桥接器中的实际约束数。

画面中的 pin 数量表示注册的约束组数：原版为 1 组，覆盖 106 个材料点；无 latch 为 0 组。

## 如何解释数值

独立 NumPy 评分将原生四元数归一化后构造旋转矩阵，从保存的材料点重算手坐标系中的位移。分别报告区域质心位移和最大材料点位移：两者都可能包含软体变形，反向变形还可能在质心指标中抵消。主动松开后的运动不计入保持阶段最大值。

清洁率从保存的墨水状态重算，海绵和机械臂归位误差从保存位置核对。沿用原版任务阈值：清洁率至少 90%、对杆峰值力超过 1 N、压力超过 5 kPa、海绵水平归位误差小于 20 mm、垂直误差不超过 3 mm、机械臂回到 home 的误差小于 6 mm、状态有限且流程完成。无 latch 组不会仅因没有约束而被判失败。

清洁率是原版的仿真磨损指标，不是真实墨水去除率。每组 3 次是开发复现重复，不是留出验证，也不足以估计部署可靠性。该对照只识别当前几何和配置下辅助保持的贡献，不能直接归因于摩擦定律、耦合延迟、材料精度或某个引擎的总体优劣。

## 尝试、成本与复现

<!-- rss-attempts:start -->
有限预算共使用 **4 次短预检、1 次未修改的官方测试、7 次完整记录**：1 次未配对参考和 6 次正式对照。未配对参考同样清洁 95.47%，任务与记录检查通过，但不计入正式对照分母。三次预检按计划截断于 3 秒仿真时间，第一次在启动阶段人工中止。

| 模式 | 仿真时长（s） | 受限运行耗时（s） | 峰值内存（MiB） |
| --- | ---: | ---: | ---: |
| 原版 | 59.82–59.82 | 161.3–164.7 | 1441.9–1454.9 |
| 无 latch | 41.68–41.70 | 106.5–109.4 | 1306.4–1312.5 |

独立环境安装耗时 1072.2 s，与物理运行分列。原始材料点和接触记录保留在本地；公开证据包含逐步曲线数据、摘要、配置清单与原始文件哈希。

<!-- rss-attempts:end -->

首次 RTX 预检在 539.8 秒后人工停止，首帧恰在停止前完成。因此记录为初始化成本较高，不据此判断死锁。后续使用上游 tiled 渲染器显示碰撞几何，不含 RTX 房间材质。独立评分曾因未归一化的单精度四元数产生偏差，现已修正并加入回归测试；原错误评分仍保留。

正式资源边界为 8 GiB 内存、4 个 CPU 核等效配额、128 个任务、零实验 swap，并保留 8 GiB 桌面内存余量，由现有 cgroup 工具执行。运行期间观察到其他主机任务，因此耗时仅作为工作负载成本，不用于独占性能比较。

[逐次摘要、曲线数据、配置清单与原始文件哈希](https://github.com/huangkiki/Dexlab/tree/autoresearch/issue-223/docs/evidence/rss-wiping)。

[代码、固定几何与复现命令](https://github.com/huangkiki/Dexlab/tree/autoresearch/issue-223/demos/rss-wiping) · [Issue #223](https://github.com/huangkiki/Dexlab/issues/223) · [Discussion #220](https://github.com/huangkiki/Dexlab/discussions/220) · [未修改的官方测试](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/tests/test_demo_wipe_the_bar.py)。
