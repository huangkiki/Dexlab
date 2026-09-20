# SDF–SDF 苹果梗抓取

[English](sdf-backends.md) | [简体中文](sdf-backends.zh-CN.md)

两个后端使用下载的 OpenArm 双臂机器人和 Wuji 灵巧手执行同一任务。苹果和两个抓取指腹均使用 SDF 碰撞几何。SuperDex 加载上游预计算的指腹 SDF；MuJoCo 从相同来源的指腹表面编译原生八叉树，最大深度为 9。两者采用不同的数值表示与接触求解器，并不具有完全相同的物理行为。

## 引擎底层实现

### MuJoCo：将 SDF 接触送入约束求解器

原生八叉树存储距离场，并在叶节点内部进行三线性插值。在 `mjc_SDF` 中，引擎从重叠包围盒内的多个初始点出发，对两个 SDF 构成的函数做梯度下降，生成接触位置、距离和法向。本演示的 `sdf_initpoints=40` 与 `sdf_iterations=100` 控制搜索过程，不决定摩擦或手指力量。参见 [MuJoCo 3.11.0 SDF 碰撞源码](https://github.com/google-deepmind/mujoco/blob/3.11.0/src/engine/engine_collision_sdf.c#L1040)。

这些接触通过接触雅可比进入关节系统。MuJoCo 求解耦合的软约束问题：`solref` 设置参考响应，`solimp` 设置约束阻抗。本演示采用 Newton 约束求解器和椭圆摩擦锥；`condim=4` 表示每个接触包含一个法向分量、两个滑动方向及扭转摩擦。约束求解器与 `implicitfast` 时间积分器是两个不同层次。参见官方[接触与求解器公式](https://mujoco.readthedocs.io/en/latest/computation/#contact)及[求解器参数说明](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters)。

### SuperDex：积分基于 SDF 的表面力

SuperDex 的接触路径在表面积分采样点查询对侧碰撞体。SDF 提供距离和梯度；引擎计算单位面积的力，再乘以积分权重，累加力与力矩。这些采样点构成接触表面的离散表示。参见 [`mochi_contact.cpp`](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_physics/src/mochi_contact.cpp#L2700)。

每个采样点的法向接触计算采用平滑穿透函数 `p(d)`：罚能为 `0.5 * k * p(d)^2`，其导数提供沿 SDF 梯度方向的力。阈值和平滑宽度控制接触力的起始过程。摩擦采用基于相对切向运动的正则化库仑耗散；`friction_falloff_vel` 控制零速度附近的平滑尺度，并非精确的零滑移约束。参见 [`ComputeBatchContactPenaltyForceDForce` 与摩擦计算](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_core/include/mochi_core/contact/contact_utils.h#L497)。

每个隐式积分阶段的非线性方程通过 Newton 迭代求解；本演示选择 GMRES 求解内部线性系统。这里 Newton 方法求解的问题与 MuJoCo 的约束优化不同。参见 [`StepIslandNewtonAsync`](https://github.com/unilabsim/project_superdex/blob/f216dace36464d70f224caa4253074ec365ed14f/superdex_physics/libraries/mochi/mochi_physics/src/mochi_solve.cpp#L1090)。

**源码与运行库来源：** SuperDex 源码链接固定在公开的 UniLab 基线 `f216dace`。视频对应实验使用官方 SuperDex physics/robotics **1.0.0 FP64 wheel**，不主张该源码提交就是 wheel 的精确构建版本。MuJoCo 使用官方 **3.11.0 wheel**，原生库已与 wheel 的 RECORD 校验。参见记录的 [MuJoCo](../demos/apple-stem-grasp/evidence/sdf-mujoco/engine.json) 和 [SuperDex](../demos/apple-stem-grasp/evidence/sdf-superdex/engine.json) 运行库信息。

### 对细梗抓取的影响

两个引擎都允许柔顺接触。SDF–SDF 本身既不保证夹持成功，也不消除滑移。从实现机制推断，两者的调参敏感因素有所不同：MuJoCo 的接触搜索与摩擦锥约束影响可提供的支撑；SuperDex 的表面采样、罚力响应与摩擦正则化影响积分后的力。这些是需要进一步验证的机制，不能单独解释两段记录的差异，因为摩擦系数、控制增益、步长和抓取对齐也不同。

| 发布配置 | MuJoCo | SuperDex |
|---|---|---|
| 步长 | 0.5 ms | 2 ms |
| 苹果 SDF | 八叉树，最大深度 9 | 网格，目标间距 0.2 mm |
| 拇指/食指 SDF | 从原始指腹表面生成的八叉树，最大深度 9 | 上游预计算指腹 SDF |
| 接触响应 | `solref=(0.005, 1)`、`solimp=(0.95, 0.99, 0.001)` | 罚系数 `1e10` Pa/m；接触起始阈值 0.1 mm；平滑半宽 0.15 mm |
| 滑动摩擦系数 | 1.0 | 0.5 |
| 其他摩擦配置 | `condim=4`，扭转系数 `0.001`，`impratio=3000` | `friction_falloff_vel=0.00002` m/s；关闭接触摩擦的拟合 Hessian |
| 求解器上限 | Newton：100 次迭代，容差 `1e-10` | 非线性：128 次迭代；GMRES：200 次迭代 |
| 夹持控制 | 共享目标先验，增益乘数 2 | 共享目标先验，夹持刚度 30 |
| 抓取对齐 | 腕部路径额外高度偏移 7.25 mm | 初始抓取高度偏移 1.5 mm |

这些是经过仿真调优的参数，不是测量得到的水果或皮肤材料属性。[参数来源与假设](research-focus.zh-CN.md#参数来源与当前假设)区分了资产原值、任务设定和数值调优。具体应用代码：[MuJoCo 模型](../demos/apple-stem-grasp/src/mujoco_model.py)、[MuJoCo 控制器](../demos/apple-stem-grasp/src/mujoco_grasp.py)、[SuperDex 设置与控制器](../demos/apple-stem-grasp/src/wuji_stem_grasp.py)。

## 运行

先执行 `bash scripts/setup.sh` 完成安装，无需构建引擎源码或配置 API key。随后在仓库根目录执行：

```bash
bash demos/apple-stem-grasp/run.sh --backend superdex --stem-only --headless \
  --output demos/apple-stem-grasp/runs/superdex-sdf
bash demos/apple-stem-grasp/run.sh --backend mujoco --stem-only --headless \
  --output demos/apple-stem-grasp/runs/mujoco-sdf
```

省略 `--headless` 可打开交互窗口。每次记录 14 秒仿真，实际运行时间更长。原生 SDF 编译占用较多内存，并保存较大的本地 `model.mjb`；生成模型和原始运行数据不纳入 Git。

MuJoCo 路径使用 SuperDex 读取原始机器人资产，并计算初始运动学先验与静置后的规划位姿；随后全部实验动力学通过 MuJoCo `mj_step` 执行，不回放 SuperDex 的物体位姿。MuJoCo 使用隔离的正运动学计算，将腕部路径与自身静置后的苹果位置对齐一次。两个控制器都明确接收已知物体位姿，没有 Astra 视觉策略参与。

## 验证与视频导出

对任一运行目录执行：

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/apple-stem-grasp/runs/mujoco-sdf
```

离线验收器使用保存的力、位姿和接触点，检查完整的 11–14 s 保持阶段：离桌至少 70 mm，支撑力匹配苹果重力，两个 SDF 指腹持续提供支撑，无果身/桌面/其他支撑，穿透小于 1 mm，相对腕部位移小于 2 mm、相对旋转小于 5 度，基座固定、记录有限值、接触力账目一致及动量平衡。每个物理步均有记录。接近阶段允许偶发果身接触，仅在保持阶段要求由梗支撑。缺失采样或检查失败会返回非零退出码。

渲染得到的 `mujoco-sdf.gif`／`superdex-sdf.gif` 及同名 MP4 连续回放抓取近景，展示相机跟随记录中的苹果。仅用于显示的 mocap 刚体不参与独立的动力学场景；相机也不是策略输入。

`engine.json` 记录运行库身份和 SDF 碰撞体检查；`sdf-dynamics.npz` 与 `sdf-contacts.npz` 保存原始证据；`summary.json` 保存判定。MuJoCo 还保存编译后的动力学模型，并将原生库指纹与已安装 wheel 的 RECORD 对照，不接受本地引擎补丁。

## 结果与限制

Linux 上使用发布默认配置、通过完整公开命令重新运行后，两个后端均通过全部检查：

| 指标 | MuJoCo | SuperDex |
|---|---:|---:|
| 物理步数 | 28,000 | 7,000 |
| 保持时长 | 3 s | 3 s |
| 保持期间最小离桌高度 | 124.43 mm | 115.22 mm |
| 全程最大手部穿透 | 0.159 mm | 0.452 mm |
| 保持期间相对腕部最大位移 | 0.275 mm | 0.040 mm |
| 保持期间相对腕部最大旋转 | 0.301° | 0.555° |
| 保持期间果身接触力 | 0 N | 0 N |

[MuJoCo 报告](../demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json) · [SuperDex 报告](../demos/apple-stem-grasp/evidence/sdf-superdex/summary.json) · [MuJoCo 视频](../demos/apple-stem-grasp/media/mujoco-sdf.mp4) · [SuperDex 视频](../demos/apple-stem-grasp/media/superdex-sdf.mp4)

每个证据目录包含引擎身份、执行的 Python 源码哈希以及视频/原始记录来源。大型原始数组和生成模型保留在本地；上述命令可重新生成并独立验证。视频包含每段 14 秒实验的全部 280 帧，无剪辑，使用当前 OpenArm 固定安装结构，没有移动底座。两个成功配置均从全新物理状态重复运行过，但这仍是单个已调优场景，并非留出测试基准。

抓取对齐仍然敏感：邻近的 MuJoCo 腕部高度配置会超出穿透限制或丢失抓取。仅仅留住苹果不足以证明合格；发布配置在重新构建后再次通过了完整验收。

机器人关节坐标系、动态连杆质量与惯性张量、原始表面和碰撞过滤覆盖项均从加载的 prefab 转移。固定静态刚体保持零动力学有效质量。MuJoCo 编译源资产中的无质量连杆时需要正惯性占位值；加载器在编译后恢复其原始零惯性，并在步进前检查完整质量矩阵。这是通过公开 API 转换模型，不是修改引擎源码。其他机器人碰撞体使用 `mesh`；MuJoCo 的 mesh–SDF 路径搜索三角形，而普通凸碰撞路径使用网格凸包。两个抓取指腹与苹果均为原生 SDF。腕部安装凹槽沿用适配器中的局部自碰撞排除，没有关闭指腹–苹果接触。

苹果与梗是一个刚体。尚未验证弯曲、断裂、损伤、真机或 MuJoCo Warp。同一场景的可重复性不能证明随机场景成功率。物体相对腕部的运动不是跟踪材料点的累计滑移，成功夹持也不等于零滑移。
