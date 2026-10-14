# 豆腐状软块对半切

依据 [BladeMaster，arXiv:2609.27342v2](https://arxiv.org/abs/2609.27342v2) 的机制，实现一个**豆腐状软块对半切**任务：力驱动刀具切入、撤刀，再以单侧诊断冲量检查两块材料是否能够独立运动。这是独立编写的 CPU 实现，不是作者源码，也不代表复现其 GPU 速度或真实食材精度。

```{raw} html
<section class="cutting-player" aria-label="豆腐对半切">
<header><h3>豆腐对半切</h3><div class="cutting-view-switch" aria-label="视图"><button type="button" data-cutting-view="surface" data-src="_static/cutting/tofu/surface.mp4" data-poster="_static/cutting/tofu/surface-poster.png" aria-pressed="true">表面</button><button type="button" data-cutting-view="particles" data-src="_static/cutting/tofu/particles.mp4" data-poster="_static/cutting/tofu/particles-poster.png" aria-pressed="false">粒子</button></div></header>
<video controls autoplay muted loop playsinline preload="metadata" poster="_static/cutting/tofu/surface-poster.png" aria-label="豆腐对半切"><source src="_static/cutting/tofu/surface.mp4" type="video/mp4"><a href="_static/cutting/tofu/surface.mp4">观看视频</a></video>
<p>切开、撤刀，再检验两块独立运动。</p>
</section>
```

实体表面与粒子视图使用同一份保存的物理状态；当前展示按实际物理时间播放。蓝色、橙色代表持久切面标签；颜色不同本身不能证明力学分离。2.4 秒时对右半块施加已知外部冲量，这是诊断干预，不是机器人操作策略。首版不接机械臂、视觉控制器或学习策略。

## 已实现机制

| 论文机制 | 实现与范围 |
|---|---|
| 式 1–2：固定参考插值模板 | 每粒子八个三线性参考权重；固定共旋弹性、显式 MUSL、PIC/FLIP，FP64 |
| 式 3–7：几何侧别与接触功 | 单把有限直刀、持久 `0 → 1/2` 标签；切割带半宽 `6 Δx`，后方范围 `2 Δx` 加相对扫掠，前方范围为两个代理球半径 |
| 式 8–9、17：相容逻辑网格 | P2G 和 MUSL 中同时进行 0/1、0/2 保守交换，1/2 不交换；FLIP 差分使用式 17 的耦合后旧动量 |
| 式 10–13：材料接触 | 当前空间球代理；排除参考距离小于 `2 Δx` 的近邻，切面两侧豁免；持久切向历史与库仑滑动 |
| 式 14–16：刀具接触 | 长方体最近点、预测间隙冲量，同一冲量反向反馈到动态刀具；导向机构约束姿态，记录反作用力矩 |
| 方向性切割阻力 | 接触功向 `Gc V^(2/3) (1−ζ)/ζ` 阈值累积，损伤饱和后的接触释放正切进方向冲量；损伤不缩放弹性，也不直接触发分离 |
| 渲染 | 从材料采样单元提取外表面和暴露切面，按相容切割历史嵌入保存的变形；提供粒子对照。不是论文的局部双重轮廓算法 |

刀具质量 0.2 kg，有三个动态平移自由度。有限幅 PD 驱动跟踪刃口高度目标，材料反力会改变刀具速度。重力补偿导向机构固定刀具姿态，刚性砧板单边止挡产生单独记录的外部冲量。这不是论文中可自由旋转的落刀实验。此处保留 v0.61.0 单刀基线；新版本增加 [香蕉连续三刀](banana-cutting.md)。交叉刀路、塑性、黏性、GPU 内核尚未验收。

## 参数与冻结验收

软块尺寸 60 × 30 × 30 mm，密度 1,100 kg/m³，杨氏模量 6 kPa，泊松比 0.35。密度和模量借用论文 §IV-A 的软块示例，其余设置为本实验选定的合成参数，**均未经过真实豆腐标定**。总质量 59.4 g。默认网格 7.5 mm，每单元八粒子，共 1,024 粒子，时间步 0.5 ms。刀具尺寸 1 × 50 × 40 mm。

其余选定参数：PIC/FLIP 混合 0.95；法向缩放 0.1；静／动摩擦 0.3/0.2；切向刚度／阻尼缩放 0.05/0.1；切割能量尺度 0.5 J/m²、锋利度 0.9。驱动刚度／阻尼为 250 N/m、14 N·s/m，力限额 10 N。球代理半径为 `Δx/4`。接触罚函数及切向刚度随时间步变化，因此减小时间步是敏感性测试，不能直接视为同一本构模型的收敛证明。

3 秒过程：稳定至 0.3 秒，下切至 1.3 秒，保持至 1.6 秒，撤刀至 2.2 秒，2.4 秒施加诊断冲量。刃口目标可达 −4 mm，以加载砧板止挡；实际刃口不能穿过砧板。诊断对初始右侧粒子增加 (0.12, 0, 0.1) m/s 速度，对应外部冲量 (0.003564, 0, 0.002970) N·s。

首轮运行前冻结验收：初始为一个传递连通分量；最终为两个分量，各质量比例与 0.5 相差不超过 0.02；切面标签持久；相对 x 位移至少 1 mm、被动半块 x 位移至多 3 mm；刀具完全撤出；材料反力大于 0.001 N；形变雅可比至少 0.05；代理球重叠不超过一个半径；独立复算动量误差至多 10⁻⁹ N·s。记录校验另核对帧速度、外部冲量及刀具反力反馈。这些属于数值／任务检查，不代表真实切割力精度。

## 证据与边界

| 案例 | 对半切 | 分量 | 相对位移 (mm) | 材料峰值反力 (N) | 记录耗时 (s) |
|---|---|---:|---:|---:|---:|
| `004-full` | 通过 | 2 | 3.221 | 0.07661 | 24.06 |
| `005-partial` | 拒绝 | 1 | 0.166 | 0.06947 | 24.11 |
| `006-uncut` | 拒绝 | 1 | 0.147 | 0.00000 | 24.13 |
| `007-half-step` | 通过 | 2 | 4.187 | 0.15817 | 48.35 |
| `008-refined` | 通过 | 2 | 2.863 | 0.06367 | 47.42 |

五个正式记录的数值记账检查均通过；三个完整切割均为 0.5/0.5 质量比例。时间步减半后材料反力峰值从 0.07661 变为 0.15817 N，**尚未建立力值收敛**。正式批次 cgroup 峰值内存 181–261 MiB。包含开发和导出失败在内，共 8 次调用累计 307.37 秒，未超出首轮冻结的 36 次／7,200 秒预算（单次 600 秒）。微内核单元检查与仓库交付门禁单独记账。

第 001 次完成物理过程但评分序列化失败；002–003 修正论文式 17 的 FLIP 表达、反馈记账和相对扫掠，作为已被替代的开发记录保留原始哈希。004–008 使用相同冻结的求解器／评分源码。以上耗时不含渲染，也不能证明实时性能。

[全部调用指标、源码哈希与失败](https://github.com/huangkiki/Dexlab/blob/main/demos/tofu-cut/evidence.json) · [原始记录，含开发尝试](https://github.com/huangkiki/Dexlab/releases/download/v0.61.0/tofu-cut-evidence-v1.tar.gz)。

独立评分器不导入求解器，而是从原始记录中的参考插值图重建连接，包含未赋值粒子造成的间接连接。部分切割和未切割必须保持连接、不能通过对半切任务。短时探测、缺失观测、改变冻结阈值或改动文件哈希会被拒绝，或不能通过任务完成项。

球代理接触允许有限重叠；重建表面是显示近似，不是切口质量测量。一次对称对半切不能证明四分之一切割精度、真实豆腐切割力、任意轨迹鲁棒性或真机安全。真机阶段仍需辨识弹性、摩擦和切割阻力，再独立验证力曲线与分离后的质量比例。

## 复现

安装 DexLab 环境和可选 `cutting` 依赖后，使用仓库已有资源限额与共享研究锁。每次输出目录必须是新目录。以下从仓库根目录运行：

```bash
python -m pip install -e '.[cutting]'
CUT_ROOT=/path/on/mounted/data/tofu-test
mkdir -p "$CUT_ROOT"
python scripts/bounded_run.py --profile adaptive \
  --resource-plan "$CUT_ROOT/plan.json" --cpu-cores 4 --io-device /dev/sda \
  --data-dir "$CUT_ROOT" --timeout 600 --receipt "$CUT_ROOT/resources.json" -- \
  python scripts/research_guard.py run --lock /path/to/shared/window.lock \
  --kind qualification --receipt "$CUT_ROOT/window.json" -- \
  .venv/bin/python -m dexlab.tofu_cut --output "$CUT_ROOT/full"
.venv/bin/python -m dexlab.cutting_score "$CUT_ROOT/full"
```

挂载设备和共享锁路径替换为主机实际配置。`--mode partial`、`--mode uncut` 保留其负任务评分；`--dt 0.00025`、`--grid-spacing 0.006` 对应已记录的敏感性案例。运行器退出成功只表示记录完成，任务成败读取 `score.json` 或评分器退出码。回放命令为 `python -m dexlab.cutting_showcase RUN --output MEDIA`，仅读取记录，应在单独受限后处理窗口中执行。

每次运行保存 `manifest.json`、`states.npz`、`trace.npz`、`score.json`，包含源码／依赖版本和 SHA-256。资源收据与累计账本保留失败及成本。[源码与实验入口](https://github.com/huangkiki/Dexlab/tree/main/demos/tofu-cut) · [实现任务 #192](https://github.com/huangkiki/Dexlab/issues/192) · [切割讨论 #191](https://github.com/huangkiki/Dexlab/discussions/191)。
