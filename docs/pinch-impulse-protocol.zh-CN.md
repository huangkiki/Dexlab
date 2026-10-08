# 夹持冲量残差诊断协议

[English](pinch-impulse-protocol.md) · [冻结清单](evidence/pinch-impulse/manifest.json) · [原始结论](pinch-load-results.zh-CN.md)

Issue #109 定位 v0.45.0 临界夹持残差。这是独立诊断预算；原 18 例（包括 6 例记录拒绝）保持原结论。本协议阶段尚未运行新物理实验。

## 固定设计

沿用原协议导向夹面／自由方块：64 g、40 mm 方块，两个 100 g 导向夹面，合成摩擦 0.5；显式预加载 0.5 s（其中前 0.2 s 夹紧命令爬升），随后质心向下加载 1 s。共六例：R=1/2 × Newton 停止容差 1e-6/1e-10/1e-14。固定阻抗 0.9、步长 1 ms、Euler、最多 100 次迭代。同一 R 下只改变容差。官方 MuJoCo 3.15.0 执行前须重新核实稳定版准入，不静默换引擎。

唯一六例批次，每例 1.5 s，不调参重跑替换；单执行者、每次 30 分钟上限，实测内存／磁盘准入、cgroup CPU／内存／任务／时限、零 swap、挂载盘输出、独占计时窗口。正式发布完整回归另计。

## 原生观测与独立分解

每个求解时刻记录步前后速度、qacc、完整原生质量矩阵 M、qfrc_smooth/constraint/bias/passive/actuator/applied、物体外载、状态、警告、有效约束数、各岛迭代数和每次迭代 gradient/improvement，不截断有效岛。统计量有缩放，不等于 SI 单位的实测力。原生步进后读取，不额外 forward，也不写状态。

h=0.001 s，delta_v=v_after-v_before：

- 总残差 r=M delta_v-h(qfrc_smooth+qfrc_constraint)。
- 积分项 e=M(delta_v-h qacc)。
- 力平衡项 f=h(M qacc-qfrc_smooth-qfrc_constraint)。
- 独立核对 r=e+f、速度更新、原生 M 与声明对角质量／惯量、光滑力组成（驱动+被动+外载−偏置）。

前五个广义分量为平动，后三个为转动。分解闭合阈值分别 1e-12 N s / N m s；速度更新阈值 1e-12 m/s / rad/s；光滑力组成阈值 1e-12 N / N m。质量矩阵按各广义分量的单位检查，绝对阈值 1e-14。原物理阈值保留作背景，不修改以接受新结果。

容差 1e-10 的两例须与清单中已发布的对应 trace 哈希绑定，并比较全状态（各分量单位下绝对 1e-12）；不匹配则不能直接归因于原轨迹。报告残差峰值/RMS、积分项/力项、容差敏感性及非单调性、迭代触顶、运动以及总计/准备/原生步进/观测成本。代数恒等式不等于物理准确；容差变化是数值干预，不是材料标定。无法解释则继续标未确定。

唯一批次前先完成缺观测、篡改加速度/速度/力、质量/配置/时刻/来源错误等负例测试，并冻结完整记录器和评分器。六例全部报告，包括诊断失败；不宣称普适引擎优越性或真机精度。

来源：[官方动力学与求解器](https://mujoco.readthedocs.io/en/stable/computation/index.html)、[原生类型](https://mujoco.readthedocs.io/en/stable/APIreference/APItypes.html)及已安装官方 3.15.0 头文件。qfrc_smooth 是无约束广义合力；gradient/improvement 有缩放。
