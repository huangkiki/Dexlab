# 碰撞到达相位协议

[English](impact-phase-protocol.md) | [简体中文](impact-phase-protocol.zh-CN.md)

本有限敏感性研究复用九个已发布 k=1000000 s⁻² 工况，仅新增27例：u=0.5/1/2 m/s、h=1/0.5/0.25 ms、alpha=0.25/0.5/0.75。设 x1=-0.06m、x2=0.06+u*h*alpha m；相对于名义0.02m间隙，自由飞行到达接触时刻延后 alpha*h。[清单](evidence/impact-phase/manifest.json)绑定基线哈希及全部精确参数。其余设置、原末态阈值与1mm重叠预算沿用[刚度研究](impact-stiffness-protocol.zh-CN.md)。禁止按结果调参，不要求必须得到通过工况。

两个自由1kg球体、半径0.05m，无重力/摩擦/自旋/驱动。官方MuJoCo3.15.0 CPU FP64，Euler/Newton100/容差1e-12，solref=(-1000000,0)、常数阻抗0.9，总时长0.2s、末态窗口0.02s。Intel Core i9-14900K；强制16GiB/两核/128进程/零swap/1800s，保留桌面余量并独占测速窗口。仅一次27例正式批次；源码、环境、输出在挂载盘。基线只重评，不重跑物理。

独立评分保留每例，报告末速度、能量、动量、采样重叠、峰值力、有符号冲量/误差范数、采样接触时长、建模/推进/观测/总计/评分时间与文件身份。首次接触使用 force_times[i]（积分前时刻），states[i+1]为积分后状态；与(x2-x1-2r)/u比较。接触延迟只作诊断，不新增验收门槛。峰值力依赖步长，不是已验证的连续瞬态力参考。

九组速度/步长组合均须包含0/.25/.5/.75四个相位，公布逐相位结果及速度绝对误差、相对能量误差、重叠的最小/最大/跨度。仅四个联合判定全部通过才称该有限集合通过。人为选择的相位不是随机总体、成功概率或普适稳健证明。重叠距1mm边界不超过1e-12m仅标记边界诊断，不改变严格通过判据；舍入与非单调结果均保留。

观察前指定弹性末态解析参考，不拟合恢复系数。改变自由飞行对齐可检验敏感性，但仅末态变化不能唯一识别瞬态机制或证明真实材料精度。来源：[前版](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.1)、[MuJoCo参考](https://mujoco.readthedocs.io/en/stable/modeling.html#reference)、[OpenStax守恒](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions)。
