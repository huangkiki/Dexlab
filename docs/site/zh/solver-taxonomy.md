# 求解配置分层

比较单位是带版本的核心、运行路径、物理模型与数值配置。MuJoCo 的 PGS／非线性 CG／Newton 是可选约束求解方法；SuperDex 的 Newton 与 GMRES 分别属于外层和内层。布料实现、接触模型、离散近似、积分器及更新预算不是同级算法。

[完整双语分层说明](https://github.com/huangkiki/Dexlab/blob/main/docs/solver-taxonomy.zh-CN.md)解释各引擎的角色、来源证据、系统选型与算法归因，以及未知身份。[展示词表](https://github.com/huangkiki/Dexlab/blob/main/docs/solver-taxonomy.json)不修改历史评分、计数或资格。

[完整配置矩阵](coverage.md) · [诊断方法](diagnosis.md) · [当前工作与暂停状态](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.zh-CN.md)

细 SDF 几何资格见 [#178](https://github.com/huangkiki/Dexlab/issues/178)，布料材料与接触基线见 [#179](https://github.com/huangkiki/Dexlab/issues/179)。创建任务不代表实验通过；历史任务成功、数值一致性和真实材料精度继续分开。
