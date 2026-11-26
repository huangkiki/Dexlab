# Chaos Physics：读懂子步、碰撞事件与关节

一个游戏帧可以包含多个物理子步。判断方块何时触地时，先选时钟，再选信号。

## 查清楚接触发生在哪一步

1. 用[方块落地场景](box-contact.md)录一份基线。保存引擎版本、项目物理配置和实际帧间隔。在 Chaos Visual Debugger (CVD) 中找到同一游戏帧对应的求解时间，沿 **Solver Timeline** 查看首个有效接触及其前一物理步。
2. 使用同步物理路径，在 **Project Settings → Physics** 打开 **Substepping**，记录 **Max Substep Delta Time** 与 **Max Substeps**。保持同一初态，检查实际录制中一个游戏帧跨了几个物理步。步长上限与子步数上限一起生效，实际步长以录制为准。
3. 在方块组件启用 **Simulation Generates Hit Events**，用 `OnComponentHit` 打印游戏侧时间与 `NormalImpulse`。碰撞回调可能等同一帧的子步都完成后才发给游戏线程。要定位具体子步，用 CVD 的求解记录。扫掠移动挡住物体时也可能触发 Hit，Epic 文档说明这种情况的 `NormalImpulse` 为零。

`NormalImpulse` 是冲量字段。要用冲量推平均力，需要同一接触、同一时间区间以及明确的单位。只有一次回调的时间或数值时，无法直接把它和 PyBullet 的逐步法向力读数对齐。 [物理子步](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-sub-stepping-in-unreal-engine) · [Hit 事件接口](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ComponentHitSignature?application_version=5.7)

## 把方块换成合页上的门

在独立关卡中放一根静止立柱和一块可模拟的板。把 **Physics Constraint Actor** 放在门轴上，指定两侧组件，把三条平移轴锁住，只释放沿门轴的一个角自由度。以约束的局部坐标为准。关掉这一对组件的互碰，先观察合页本身。门轴竖直时，可在开场给板的外侧一次横向冲量使它转动。

先做自由旋转，再只加旋转限位。用 CVD 的约束数据看允许轴、锁定轴、角度与限位设置，再核对板的实际姿态。若它绕错轴，先查约束朝向与初态。要评估驱动能否带载，则再加入固定外载，逐步查看驱动目标、实际角度与限位接触。

[课程目录](index.md) · [Epic 约束配置指南](https://dev.epicgames.com/documentation/en-us/unreal-engine/constraints-user-guide-in-unreal-engine) · [DexLab 的时间步基础](../mujoco-learning/step.md)
