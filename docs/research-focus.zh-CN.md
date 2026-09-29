# 研究重点

[English](research-focus.md) | [简体中文](research-focus.zh-CN.md)

DexLab 研究**机器人仿真模型的合理性与数值行为**。通过可重复的任务实验，分析刚体、碰撞几何、关节、接触和驱动模型，解释并降低建模误差，同时兼顾物理精度、稳定性与计算开销。

## 已实现与工作队列

当前已实现 UniLab 注册任务、单场景 reset/step/close、两个原生 SDF 后端和独立动力学验收。场景由 DexLab 自身管理，尚未使用 UniSim 内置后端。见[任务接口](../demos/apple-stem-grasp/README.zh-CN.md#unilab-任务接口)。

新运行还会导出[只读模型审查](model-audit.zh-CN.md)：源值与运行时惯量、关节、驱动、碰撞过滤及初始重叠发现项。

后续工作统一维护在 GitHub issues，不在文档重复维护 TODO：

- [模型审查 / Model audit](https://github.com/huangkiki/Dexlab/issues/1)
- [抖动与接触间断 / Stability diagnostics](https://github.com/huangkiki/Dexlab/issues/2)
- [冻结场景与步长研究 / Frozen regression](https://github.com/huangkiki/Dexlab/issues/3)
- [UniSim 内置适配器等价性 / Built-in adapter qualification](https://github.com/huangkiki/Dexlab/issues/4)
- [PhysX / IsaacSim](https://github.com/huangkiki/Dexlab/issues/5)
- [真机测量与校准 / Hardware calibration](https://github.com/huangkiki/Dexlab/issues/6)

## 参数来源与当前假设

每个参数应记录数值、单位、来源或推导过程、不确定性及覆盖修改。实测值、继承的模型值、几何估计、任务设定和数值调优需要区分。

| 参数或模型项 | 当前来源 | 假设或限制 |
|---|---|---|
| 机器人几何、关节坐标系、质量、质心、惯性张量 | UniLab 的 OpenArm/Wuji prefab；参见[资产来源](ASSETS.zh-CN.md)和[模型转移](../demos/apple-stem-grasp/src/mujoco_model.py) | 继承的模型值，未独立测量或验证为硬件参数 |
| 苹果与梗几何 | 从 NVIDIA 网格派生，记录来源哈希 | 单个刚体；不模拟弯曲、断裂或手指软组织变形 |
| 苹果质量 | [场景构建](../demos/apple-stem-grasp/src/wuji_stem_grasp.py)中显式设置 `mass=0.2` kg | 任务假设，不是苹果称重结果；SuperDex 构建的质量属性被转移至 MuJoCo |
| SDF 分辨率与碰撞过滤 | [后端说明](sdf-backends.zh-CN.md#引擎底层实现)中的引擎离散化和适配器配置 | 表面与法向近似、有限采样，以及腕部局部自碰撞排除 |
| 摩擦与接触响应 | SuperDex 沿用基线摩擦系数 0.5；MuJoCo 由演示设置为 1.0；罚力/约束响应和正则化在控制器中配置 | 不是辨识得到的皮肤–果梗材料属性；相同系数不代表相同引擎行为 |
| 关节驱动与运动 | 控制器中的脚本目标、逆运动学、增益/阻尼和抓取高度偏移 | 已知位姿控制与显式运动先验；没有学习到的抓取技能或实测执行器模型 |
| 步长与求解器容差 | MuJoCo 0.5 ms、SuperDex 2 ms，以及各自的迭代上限 | 针对此案例验证的数值选择，并非收敛性研究或同等条件速度基准 |
| 验收阈值 | [验收器](../demos/apple-stem-grasp/src/verify_sdf_grasp.py)中的显式任务标准 | 工程验收边界，不是真实世界精度估计；不能为掩盖失败而放宽 |

MuJoCo 适配器使用临时的正惯性占位值编译无质量连杆，然后恢复源值并在步进前检查组装后的质量矩阵。这一有记录的转换过程不能证明每个源连杆的惯量都符合真实物理。

## 研究流程

以下是实验设计原则，具体实现范围和验收进度以对应 issue 为准。

1. **审查模型。** 检查单位和尺度、坐标系、质心、惯量对称性与物理合理性、关节轴与限位、碰撞几何、初始重叠、接触过滤及驱动限幅。比较碰撞模型与可见表面，记录源值和所有本地覆盖项。
2. **隔离故障。** 将任务简化为刚体静置、单关节运动、滑动接触或两指保持。记录首个失败步并保存对应配置。画面安静或轨迹成功本身不足以作为验证证据。
3. **逐项改变参数。** 分别扫描几何分辨率、步长/子步、求解器容差/迭代数、接触响应、摩擦和驱动增益，并复查原先通过的案例。同时改变摩擦、增益与抓取对齐无法确定单一原因。
4. **冻结并复现。** 调参前固定验收标准，保留失败试验，冻结选定配置后测试未用于调参的场景。保存版本、哈希、初始条件、命令、力、状态、判定及连续录像。
5. **对照真机校准。** 获得实测数据后，对齐关节运动、载荷/力、物体运动和时间戳。在一组数据上辨识参数，在另一组数据上验证，并报告传感器与辨识的不确定性。本项目尚未进行这一阶段。

## 故障测量

| 现象 | 需要记录的证据 | 待检验的原因 |
|---|---|---|
| 穿透或隧穿 | 最大深度、持续时间、接触法向、接近速度、碰撞掩码 | 形状/尺度错误、初始重叠、采样或时间分辨率不足、接触柔顺性 |
| 抖动 | 位置/速度与接触力时序、均方根/峰值、频率成分 | 驱动与接触耦合、刚度过大、法向不连续、求解收敛限制 |
| 接触间断或打滑 | 接触持续性、法向/切向力、支撑平衡、相对平移/旋转 | 几何、对齐、法向载荷不足、摩擦定律与正则化 |
| 数值不稳定 | 首个非有限状态、求解器告警/残差、加速度尖峰 | 不合理惯量、约束冲突、步长、驱动或求解器设置 |
| 开销过大 | 准备时间、每仿真秒耗时、逐步耗时、内存、场景/接触规模 | SDF 构建、碰撞工作量、求解器迭代、记录与渲染开销 |

这些是需要实验检验的原因，不能只凭外观下诊断。柔顺接触的重叠应结合声明的容差与几何尺度评估。当前物体相对腕部位移不是材料点累计滑移，动量平衡也不是能量守恒检验。抖动与能量诊断的验收要求见 [issue #2](https://github.com/huangkiki/Dexlab/issues/2)。

参数语义参见 [MuJoCo 求解器指南](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters)、[SuperDex 源码依据](sdf-backends.zh-CN.md#引擎底层实现)，以及后续 PhysX 工作可参考的[刚体动力学指南](https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/RigidBodyDynamics.html)。不同引擎的配置应通过测量行为比较，不能仅按参数名称照搬。

## 可复现运行与回归

完成[安装](installation.zh-CN.md)后，可运行已有的轻量资产与验收测试：

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

验收测试使用合成日志，检查缺失物理步、缺失手指支撑、果身支撑和相对运动超限等情况。这是在测试验收器，不能替代重新运行物理仿真。实际动力学实验使用[演示命令](../demos/apple-stem-grasp/README.zh-CN.md#运行)和[独立验收](../demos/apple-stem-grasp/README.zh-CN.md#验证与视频导出)。

多场景物理回归见 [issue #3](https://github.com/huangkiki/Dexlab/issues/3)。实验须保留全部失败，并在相同硬件与记录条件下同时比较物理容差和运行成本。模型准备、物理步进、渲染需分别计时；任何速度结论都应说明工作负载与精度/稳定性要求。

每个维护中的文档页面均提供英文和简体中文版本，并相互链接。仓库首页使用中文 `README.md`，英文版位于 `README.en.md`。更新时同步两版；第三方许可证与声明保留原文。

[返回 DexLab](../README.md)
