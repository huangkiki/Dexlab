# 实验目录

代码继续使用现有目录，避免改路径破坏资产引用、复现命令或历史证据。每个实验连接问题、配置、原始记录、独立评分、结果报告和失败。

| 实验 | 代码入口 | 研究问题与状态 |
|---|---|---|
| 苹果梗抓取 | [demos/apple-stem-grasp/](https://github.com/huangkiki/Dexlab/tree/main/demos/apple-stem-grasp/) | OpenArm 双臂＋Wuji，SDF–SDF 摩擦夹持；默认场景与历史扰动测试分列 |
| 机器人夹布 | [demos/cloth-folding/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-folding/) | 夹持、抬升、释放；保留历史桌体相交失败；修复后一个 9 秒开发场景通过，鲁棒性未验证 |
| 接触与驱动 | [demos/contact-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/contact-benchmark/) | 滑动、压入/卸载、载荷与瞬态；合成响应不等于真机标定 |
| 基础布料 | [demos/cloth-benchmark/](https://github.com/huangkiki/Dexlab/tree/main/demos/cloth-benchmark/) | 拉伸、下垂、碰撞与折叠下落；各材料与求解器能力单列 |
| PhysX | [demos/physx-contact/](https://github.com/huangkiki/Dexlab/tree/main/demos/physx-contact/) | 原生刚体、SDF、关节和表面布料；不把单例成功外推到留出测试 |
| Genesis | [#42](https://github.com/huangkiki/Dexlab/issues/42) | 刚体限定范围证据已交付；[PBD 薄布诊断](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.zh-CN.md)包含失败对照，完整验收尚未完成 |

`src/dexlab/` 保留共享任务注册、评分与记录逻辑；`scripts/` 放安装、复算、文档及研究工具。只有有实际重复或不变量的部分进入共享代码，不另建通用仿真框架。

## 苹果抓梗的控制与动力学

右手拇指和食指夹梗，左臂停放。苹果与梗组成 0.2 kg 自由刚体。动作来自已知位姿、逆运动学与固定关节目标；实际位姿由物理引擎积分，物体无附着或位置驱动。连续保持窗口为 11–14 s，接近阶段允许果身接触。

展示相机跟随记录中的苹果，仅用于回放。没有视觉控制、梗断裂或真机准确性的验证结论。

[抓取实现与参数](https://github.com/huangkiki/Dexlab/blob/main/docs/sdf-backends.zh-CN.md) · [全部任务盘点](https://github.com/huangkiki/Dexlab/blob/main/docs/inventory/README.zh-CN.md)

## 连续近景记录

以下是原固定版本的开发场景回放，不代表留出场景成功率。夹布动图保留了已检出的桌体相交失败。

::::{grid} 1 1 2 2
:gutter: 3
:::{grid-item-card} MuJoCo
![MuJoCo](../../../demos/apple-stem-grasp/media/mujoco-sdf.gif)
:::
:::{grid-item-card} SuperDex FP64
![SuperDex FP64](../../../demos/apple-stem-grasp/media/superdex-sdf.gif)
:::
:::{grid-item-card} PhysX
![PhysX](../../../demos/physx-contact/media/physx-sdf.gif)
:::
:::{grid-item-card} 夹布：几何失败
![夹布：几何失败](../../../demos/cloth-folding/media/grasp.gif)
:::
::::

## 真机采集准备

双 UR7e 与两个相同 CTAG2F90D 的[采集协议、空模板和日志校验器](https://github.com/huangkiki/Dexlab/blob/main/docs/hardware/README.zh-CN.md)已提供。命令、实测反馈和独立参考分开记录；未知数据保持未知。此功能只读文件，不控制机器人；格式通过不代表真机标定。

## 摩擦响应开发实验

[16 次平面实验报告](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/FRICTION_RESPONSE.zh-CN.md)保留 MuJoCo 3.14.0 / SuperDex FP64 全部成对结果、实际初态、速度区间阻力比与成本。全部运行通过现有平面检查，但低速阻力不同；这不是等效材料标定或引擎精度排名。

## 修复后的夹布开发场景

![连续夹持、抬升与释放近景](../../../demos/cloth-folding/media/compliance-grasp.gif)

一个 9 秒候选通过固定 v3 标准，自接触穿透仍接近阈值。[指标、失败对照、录像溯源与完整命令](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-folding/SETTLING.zh-CN.md)。该结果不替换上方历史失败，也不证明鲁棒性。
