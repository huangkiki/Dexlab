# 碰撞刚度联合评测协议

[English](impact-stiffness-protocol.md) | [简体中文](impact-stiffness-protocol.zh-CN.md)

本项在v0.44.0原有弹性末态阈值之外，增加独立1mm几何重叠预算（球直径的1%）。它是预先声明的工程几何预算，不是实测材料参数或完整抓取验收。

复用已发布的9个等质量工况（刚度10000s^-2），新增18例：刚度100000/1000000s^-2 × 入射速度0.5/1/2m/s × 步长1/.5/.25ms。其余设置与[弹性协议](elastic-impact-protocol.zh-CN.md)相同。[清单](evidence/impact-stiffness/manifest.json)冻结全部工况、基线哈希和阈值。官方MuJoCo3.15.0 CPU FP64、Intel Core i9-14900K；16GiB/两核配额/128任务/swap0/1800s硬限制、单研究窗口、挂载盘输出。无正式开发试验或按结果调参。

独立报告覆盖27例，保留旧判定，再加全速率采样的最大几何重叠条件。报告原生峰力及其步长、有符号冲量误差、接触时长、准备/步进/观测/总成本。旧基线计时来自同硬件上的上一批串行运行；没有计时随机化或重复，不宣称统计显著加速。三档步长仅提供敏感性证据，不声称普适收敛阶。无需获得正面联合结果，也不得事后放宽阈值。

直接刚度是加速度空间的求解参数，不是材料杨氏模量。u/sqrt(k)仅是简单标量柔顺模型下的诊断尺度，本项没有独立验证完整瞬态定律。提高刚度可能降低重叠并增大离散误差，必须同时观察两项约束。

Sources / 来源: [MuJoCo solver reference](https://mujoco.readthedocs.io/en/stable/modeling.html#reference), [OpenStax conservation](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions), [v0.44.0 evidence](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.0).
