# Chaos Physics 学习模块

Unreal Engine 5 里的方块落到地面时，Chaos 会计算碰撞与刚体运动。用这个例子走一遍原生工作流，从配置可碰撞的形状，到回放求解器里的物体与接触。

## 从这里开始

1. [搭一个能落地的方块](box-contact.md)。用 Unreal Editor 搭出碰撞开启和关闭两组场景，逐步检查方块与地面的接触。
2. [读懂子步、碰撞事件与关节](solver-observations.md)。用同一场景区分游戏帧和物理子步，再用合页练习检查约束。

需要可运行 Chaos Visual Debugger 的 Unreal Engine 5 编辑器。教程使用 Epic 文档的英文菜单名。编辑器练习是按官方接口整理的复现步骤，DexLab 尚未运行此 UE 场景。

{ref}`全部课程 <all-courses>` · [同主题的 Bullet 练习](../bullet-learning/index.md) · [Epic 的 Chaos Physics 文档](https://dev.epicgames.com/documentation/en-us/unreal-engine/physics-in-unreal-engine)

```{toctree}
:hidden:

box-contact
solver-observations
```
