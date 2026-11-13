# 用 DexLab 案例检验自己的理解

[回到首页](../README.md) · [共同基础](foundations.md) · [DexLab 首页](https://github.com/huangkiki/Dexlab)

Sim Learning 解释引擎机制、原生接口和源码；DexLab 保存研究问题、冻结协议、测量与评分记录。读完课程后，可以带着具体问题进入报告，观察机制怎样影响一个明确工况。

## 按问题选择入口

| 学习问题 | DexLab 入口 | 阅读时重点核对 |
|---|---|---|
| 怎样冻结同一批次的版本、参数与工况？ | [斜面比较 manifest](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/incline-comparison/manifest.json) | 参与引擎、配置身份、同工况配对；未参与者不能从别的报告补进排名 |
| 控制限额、实际驱动力和夹持表现有什么关系？ | [夹持力限额报告](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.zh-CN.md) | 输入与读回的区别、限额生效位置、控制与接触各自的证据 |
| 一个最小接触案例究竟证明了什么？ | [Newton 接触报告](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-contact.zh-CN.md) | 场景、solver、精度、步长、正例与负例；球–平面覆盖不能外推成抓取对照 |
| 原生 PhysX 与宿主集成如何区分？ | [原生 PhysX 接触目录](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/README.zh-CN.md) · [历史接触目录](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/README.zh-CN.md) | SDK、binding、Isaac/UniSim 宿主各自身份，历史批次与新准入的区别 |
| 如何设计后续共同任务协议？ | [统一驱动与夹持失效边界路线](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-roadmap.zh-CN.md) | 协议、资格、实现和已完成实验分别处于什么阶段 |
| 一个引擎暂时没有已验收结果怎么办？ | [Drake 接入任务 #117](https://github.com/huangkiki/Dexlab/issues/117) | 实际状态、缺失证据、依赖和恢复条件，以当前 Issue 与报告为准 |

这些链接是具体阅读入口，可能随 DexLab 维护而更新。引用某项结果时还应记录报告提交、冻结 manifest 或发布物身份。总仓不复制一份可能过时的结果表。

## 从章节到证据的阅读顺序

1. 在引擎课程中确认你讨论的是模型、控制器、接触律、求解器还是积分器。
2. 打开报告的版本和配置记录，区分核心、绑定、后端与宿主；未知项保留未知。
3. 核对单位、坐标、质量/惯量、几何、初始状态、输入、采样时刻和评分窗口。
4. 查报告实际验证的命题，并一起阅读失败、未运行、不支持和受阻项。
5. 将结论限制在该批次工况；需要更广泛结论时回到 DexLab 的研究任务与准入流程。

例如，教学中追到了某个 solver 的当前默认配置，只能解释该源码版本的默认行为；它不能补填历史实验缺失的运行设置。实验观察、解析验证和真实硬件校准也各有不同证据要求。

当前 Sim Learning 开发阶段不新增实验批次、训练、基准或评分器。后续实验复用 DexLab 已有协议和证据体系；课程的源码/语法验收不会被写成物理验收。
