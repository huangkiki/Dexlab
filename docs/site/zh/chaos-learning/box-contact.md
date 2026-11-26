# Chaos Physics：搭一个能落地的方块

地板看起来一样，为什么一次托住方块，另一次方块直接穿过去？这个练习只改地板是否参与物理碰撞，借此核对从可见网格到求解器接触的整条链。

## 搭场景

在 Unreal Engine 5 新建关卡，清掉模板自带的地面或其他会挡住方块的物体。记录编辑器版本。两物体使用带简单盒体碰撞的 100 cm 基础 Cube，保持旋转为零。确认 Static Mesh Editor 里的简单碰撞包住网格。

| 物体 | 中心 Z | XYZ 缩放 | 物理设置 |
| --- | --- | --- | --- |
| Floor | −10 cm | `(8, 8, 0.2)` | 静止，Simulate Physics 关闭，BlockAll |
| Box | 100 cm | `(0.2, 0.2, 0.2)` | Movable，Simulate Physics 和重力开启，PhysicsActor |

两者都放在 X=Y=0。把 Box 的质量覆盖为 1 kg，线性与角阻尼设为 0。把恢复系数为 0 的 Physical Material 通过 **Phys Material Override** 赋给两者。记录重力，若使用 −980 cm/s²，方块下表面与地板相差 90 cm，从静止自由落到地面的解析时间约为 0.43 s。这个数给出量级，采样到的首次接触还取决于碰撞几何、接触设置和实际子步。 [碰撞响应](https://dev.epicgames.com/documentation/en-us/unreal-engine/collision-response-reference-in-unreal-engine) · [物理材质](https://dev.epicgames.com/documentation/en-us/unreal-engine/physical-materials-user-guide-in-unreal-engine)

## 录两次并逐步检查

1. 打开 **Tools → Debug → Chaos Visual Debugger**。保留 **Local Editor** 目标，在 **Data Channels** 中启用碰撞数据，点 **Record to File** 后再点 Unreal Editor 的 **Play**。等方块落稳后停止录制，保存 `.utrace`。 [Epic 的录制步骤](https://dev.epicgames.com/documentation/en-us/unreal-engine/recording-to-file)
2. 在回放里选中 Box，沿 **Solver Timeline** 查看第一次有效的 Box–Floor 接触及其前一子步。前一子步应当仍在下落。有效支撑建立时，下落速度应减小。静置后中心 Z 应接近 10 cm，竖向速度接近零。
3. 重启同一关卡，只把 Floor 的 **Collision Enabled** 改为 **No Collision**。地板仍然可见。再次录制，检查相同时间段和同一物体对。方块应继续下落并越过地板高度，录制中应没有这对物体的承载接触。
4. 如果正例也穿过地面，先核对 Box 的物理状态、两侧碰撞响应和实际的简单形状。形状和过滤都确认后，再查接触首次出现的子步及速度变化，判断问题出现在哪一环。

这里用位置、速度和接触约束交叉确认支撑。两组结果均为你运行时应检查的现象，DexLab 本次没有采集 UE 轨迹。 [Chaos Visual Debugger 操作指南](https://dev.epicgames.com/documentation/en-us/unreal-engine/getting-started-with-chaos-visual-debugger)

[课程目录](index.md) · [下一课：子步、事件与关节](solver-observations.md)
