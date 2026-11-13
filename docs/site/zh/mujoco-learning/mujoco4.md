# 读懂 MuJoCo 4：新能力解决什么问题？

**先问现有模型缺少什么，再看版本增加了什么。** 本课依据官方发布记录整理，核对日期为 2026-11-13；当前稳定版是 [4.0.1](https://github.com/google-deepmind/mujoco/releases/tag/4.0.1)。这些是上游能力说明，不是 DexLab 或 MATRiX 的迁移验收结果。

## 高速物体会跨过薄障碍

4.0.0 新增 **speculative contacts**。它针对一个步长内高速凸几何体穿过薄障碍的情形，提前构造接触响应。先在脑中比较物体一步的移动距离与障碍尺度，再读它的候选接触和保守推进机制。

学习时要区分：检测遗漏、接触响应、数值收敛、时间离散误差。开启这个能力不等于任意模型、任意步长都能保证不穿透。[官方机制与适用范围](https://mujoco.readthedocs.io/en/4.0.0/computation/speculative.html)

<details class="explanation"><summary>一个可以手算的尺度检查</summary>
<p>假设物体以 1 m/s 匀速运动，步长 20 ms，一步移动 20 mm。面对厚 2 mm 的障碍，只比较两个离散时刻的位置可能看不到中间穿越。这只是说明离散采样遗漏的可能性，并非对 MuJoCo 碰撞算法的复现或误差测量。</p>
<p>要验证具体改进，需要在相同几何、初始状态和输入下对照开关，保留原生接触与轨迹。观察是否还穿透之外，也要看引入了怎样的接触响应。</p>
</details>

## 材料会记住过去的形变

4.0.0 增加弹塑性，包括 joint / tendon 弹簧与二维、三维 flex；塑性形变记录在 `mjData.plastic`，状态标志为 `mjSTATE_PLASTIC`。这意味着研究卸载后的残余形变时，不能只看当前位置和速度，还要考虑材料内部状态。[4.0.0 发布记录](https://mujoco.readthedocs.io/en/4.0.0/changelog.html#version-4-0-0-november-6-2026)

对于状态恢复与连续任务，先列清保存了什么、重置了什么。支持塑性模型并不意味着参数已经对应某种真实材料。

## 看清仿真，而不只看见画面

MuJoCo 4 把 **Studio** 移出 experimental，结合 Filament 渲染、可组合调试界面和浏览器查看能力。Python 分发拆成 `mujoco-core` 与 `mujoco-studio`，`mujoco` 默认安装两者。可以先打开[官方浏览器演示](https://mujoco.org/)或[在线查看器](https://live.mujoco.org/)体验，无需从本课安装环境。[官方发布说明](https://github.com/google-deepmind/mujoco/discussions/3773)

调试工具帮助看到状态，渲染效果本身不证明接触物理或控制更准确。

## 分清 4.0 新增与 3.x 积累

`mujoco.batch` 的新批量 API 在 **3.17.0** 已加入；MJX、MuJoCo Warp、多点接触、休眠等也有各自的 3.x 演进历史。官方“3.0 到 4.0”总结不表示所有能力都在 4.0.0 首次出现。下一课把批量吞吐与单实例延迟分开。[逐版本记录](https://mujoco.readthedocs.io/en/4.0.0/changelog.html)

<details class="explanation"><summary>评估迁移时，优先读这些兼容性变化</summary>
<p>Python 3.10 已不受支持；旧版单包升级涉及文件迁移，需遵循官方安装说明。旧 composite / cable 路线被 flexcomp 替代，Studio 导入路径也有变化。4.0.0 还修正了球关节和自由关节的 RK4 姿态积分，并改变 tendon sidesite 语义；已有模型的轨迹可能因此变化。</p>
<p>4.0.1 修复了 4.0.0 引入的稀疏 Cholesky 问题：在稀疏约束 Jacobian 路径中，它可能使 Newton 得到错误 Hessian 因子，影响加速度与收敛。这是具体版本、具体路径的修复，不是“Newton 算法普遍不可靠”。</p>
<p>依据：<a href="https://github.com/google-deepmind/mujoco/blob/4.0.1/doc/changelog.rst">固定到 4.0.1 的官方变更记录</a>。本课不执行升级；历史实验仍按原冻结版本解释。</p>
</details>

## 自测：先选问题

<details><summary>如果当前问题是控制消息延迟，应该先启用 speculative contacts 吗？</summary><p>没有直接依据。先测消息、控制更新与物理步进的时序。只有证据指向单步穿越或对应碰撞机制时，speculative contacts 才是相关候选。新特性与实际瓶颈之间需要一条明确的因果联系。</p></details>

继续读：[版本与证据基线](../learn/mujoco/docs/versions.md) · [flex 与弹性](../learn/mujoco/docs/flex-and-elasticity.md) · [记录与回放](../learn/mujoco/docs/recording-and-replay.md)
