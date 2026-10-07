# 弹性碰撞评测协议

[English](elastic-impact-protocol.md) | [简体中文](elastic-impact-protocol.zh-CN.md)

两个孤立自由球，无重力、摩擦、自转和驱动，半径均0.05m，初始中心x=(-0.06,0.06)m。质量(1,1)/(1,2)kg，入射速度0.5/1/2m/s，步长1/.5/.25ms，每例0.2s。[清单](evidence/elastic-impact/manifest.json)冻结全部18例和工程阈值，保留所有失败。

封闭系统的弹性碰撞由动量与动能守恒给出P=m1u1+m2u2、D=u1-u2、M=m1+m2，v1=(P-m2D)/M、v2=(P+m1D)/M。e=1在观察结果前固定，不从本次结果反推。仅在确认碰撞发生、随后分离后评分最后20ms；没有碰撞属于证据无效。MuJoCo直接格式solref=(-10000,0)表示零阻尼，阻抗固定0.9。解析参照约束分离后的速度，不把有限时长的柔顺接触轨迹冒充瞬时刚性碰撞，也不代表真实材料参数。

原生Euler/Newton、100次迭代、容差1e-12，保留全部12个自由度。记录全速率状态、积分前接触力、原生设置、警告和文件哈希。独立评分先验证初态、时间轴、半隐式Euler平移与逐体冲量一致性，再计算物理误差。一致性检查不能证明任意伪造记录真实，仍需来源与记录器审查。

正式评测仅一批预登记18例、最多30分钟，官方MuJoCo3.15.0 CPU FP64及资源硬限制。单测只用合成记录，不是开发物理试验。禁止按结果调阈值、改引擎或初始化后注入状态。报告绝对速度/能量/动量误差、恢复系数偏差、穿透与三档步长敏感性，不假定误差单调收敛。这只验证解析模型的数值表现；真实系统与多接触任务独立研究。

Sources / 来源: [MuJoCo direct contact reference](https://mujoco.readthedocs.io/en/stable/modeling.html#reference); [OpenStax collision conservation](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions).
