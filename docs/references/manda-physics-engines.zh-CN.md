# 机器人仿真物理引擎对比：中文阅读导引

这份参考资料帮助读者理解跨引擎比较需要控制哪些条件、应观察哪些指标，以及实验结论的适用范围。它是 DexLab 的原创摘要与阅读导航，不是原文的逐段翻译，也不是 DexLab 自行复现的实验报告。

- 原文：[Comparing physics engines for robotics simulation](https://mandarobotics.com/blog/comparing-physics-engines/index.html)
- 发布方：Manda Robotics；文章未列出个人作者。
- 原文发布日期：2026-10-05；本导读核查日期：2026-10-08。
- 配套背景：[仿真框架与物理引擎概览（英文）](https://mandarobotics.com/blog/comparing-physics-engines/primer.html)。

## 先明确比较的对象

这里的对象是四套具体执行配置，不能仅凭产品名称把结果推广到其所有后端、版本或默认参数。以下版本按原文记录，并不表示当前最新版本。

| 比较路线 | 原文记录的版本 | 刚体实验执行方式 |
| --- | --- | --- |
| PhysX | 宿主 Isaac Sim 6.1.0.0；未单独给出 PhysX 核心版本 | CPU TGS，float32 |
| Newton / MuJoCo-Warp | Newton 1.5.2、MuJoCo-Warp 3.11.0、Warp 1.16.0 | GPU，float32 |
| MuJoCo CPU | MuJoCo 3.11.0 | CPU，float64 |
| Genesis | Genesis 1.4.1 | GPU，float64 |

表格对应刚体比较。进入软体章节后，求解器组合发生变化：PhysX 使用 GPU 路线，原生 MuJoCo-Warp 与 Newton 的 MuJoCo-Warp + VBD 耦合路线也分开讨论。阅读软体结果时，应回到该节确认材料、网格、耦合方式和步长。

## 最值得带走的一个例子

在原文的[滑块试验](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-01)中，在 2 ms 步长下，各引擎的停止位置仅相差约 0.05 mm，接触合力峰值却相差接近十倍。这提示我们：终点接近，仍可能存在不同的接触过程。

阅读这个例子时，要区分接触合力、单个接触点的力和冲量；峰值还依赖采样与物理步长。比较图像时，也应同时检查坐标轴、单位、记录频率和统计窗口。仅凭轨迹重合或一项成功判据，无法判断完整动力学过程是否一致。

## 按问题进入原文

- 想检查比较是否公平：先读[方法](https://mandarobotics.com/blog/comparing-physics-engines/index.html#method)，查看导入后的几何、质量、质心、惯量和关节参数如何核对。建议把“源文件相同”和“引擎内部模型相同”列成两个独立问题。
- 想理解控制器与引擎的关系：读[机器人试验](https://mandarobotics.com/blog/comparing-physics-engines/index.html#step-robot)和[控制器调参](https://mandarobotics.com/blog/comparing-physics-engines/index.html#controller-transfer)。共享控制器指相同控制方程、增益、目标与更新节奏；反馈读取不同状态时，输出力矩可以不同。
- 关注抓取或精密接触：从[插入](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-insertion)和[软体](https://mandarobotics.com/blog/comparing-physics-engines/index.html#scenario-deformable)进入。先确认失败发生在模型导入、数值有效性、接触反馈还是任务执行阶段，再解释结果。
- 想选择运行后端：读[性能](https://mandarobotics.com/blog/comparing-physics-engines/index.html#runtime)，同时查看精度、并行环境数、硬件和计时范围。单环境延迟与批量总吞吐回答的是不同问题。

## 使用这些结论的边界

原文没有实机测量真值；MuJoCo CPU 和解析参考也不能替代硬件验证。网页中的动画是在统一渲染器里回放已记录姿态，不是在浏览器重新运行各引擎。多数配置只有一次试验，局部重复和减半步长检查不能直接当作统计置信区间或完整收敛研究。

尤其应保留软体章节的限定：PhysX 的初始化与接触设置尚未验证，不能把所展示的失败解释成 PhysX 不具备软体抓取能力。不同路线使用相同名义材料参数，也不意味着内部材料模型已经校准等价。更多限制见[原文局限](https://mandarobotics.com/blog/comparing-physics-engines/index.html#limitations)；数据与审计入口见[复现说明](https://mandarobotics.com/blog/comparing-physics-engines/index.html#reproducibility)。

对 DexLab 的后续实验，一个可执行的阅读产物是比较记录表：分别填写模型导入检查、控制输入语义、接触配置、记录指标与失败判据，并标注哪些项目尚未验证。这样能把文献观察转成可检查的问题，而不是提前给引擎排位。

记录时可以把结果拆成三个层次：任务是否完成、状态轨迹如何变化、力与数值诊断是否可信。三者应分别定义，不能用“成功”替代后两项。若发现差异，建议先用简化场景固定初始状态、输入序列和记录时刻，排查导入与测量，再逐步恢复闭环控制和复杂接触。这个顺序是本导读建议的复现思路，不表示 DexLab 已完成验证。

## 来源与使用说明

在本次核查范围内，未找到适用于该文章全文翻译及图表、脚本再发布的明确许可。因此本页采用独立表述的摘要与阅读导航，仅链接原站，不收录原文全文、图表、回放数据或网页脚本。后续若取得明确授权，可再制作相应译本；当前页面不代表原作者认可或背书。
