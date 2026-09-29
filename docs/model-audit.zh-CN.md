# 模型审查

[English](model-audit.md) | [简体中文](model-audit.zh-CN.md)

苹果梗演示在场景准备期间输出只读的参数与初始重叠报告，分别记录继承值及后端覆盖值，不修复模型。审查不改变现有抓取验收阈值，也不向控制器回流信息。

## 运行与查看

完成[安装](installation.zh-CN.md)后运行完整演示：

```bash
bash demos/apple-stem-grasp/run.sh --backend superdex --headless
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless
```

每次运行在输出目录生成 `model-audit.superdex.json`。MuJoCo 路径先使用 SuperDex 加载和规划场景，因此还生成 `model-audit.mujoco.json`。快照位于苹果静置、机器人放置到预抓取姿态之后，14 秒抓取轨迹开始之前。

已有报告可以单独复查，不构建或推进仿真：

```bash
.venv/bin/python -m dexlab.model_audit \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf/model-audit.mujoco.json
```

命令打印发现项，参数错误返回退出码 1；几何警告保持可见，不自动判定模型不可用。它不修复参数，也不替代独立动力学验收。没有这些 JSON 的历史记录需要重新运行，才能获得对应快照。

## 报告内容

| 字段 | 含义 |
|---|---|
| `units` | 声明按 SI 解释：米、千克、秒、弧度、kg m² 惯量，以及 N m/rad 和 N m s/rad 转动驱动增益。这是模型假设，不是实测。 |
| `sources`、`source_record` | 机器人 prefab 文件哈希；原生报告还保留上游来源记录。运行目录的 `source-sha256.json` 标识代码。 |
| `bodies[].source/effective` | 质量、局部质心和惯性矩阵。SuperDex 的 source 是原始加载资产，缺失值保持 null；MuJoCo 的 source 是原生运行时参数，`prefab_source` 继续保留资产值。 |
| `bodies[].massless_reason` | 无几何、质量及源惯量的固定坐标链接被明确分类。未满足此条件的零质量运动连杆报错。 |
| `joints` | 原生加载的关节坐标系、轴、限位、摩擦、限位响应和力矩限制；MuJoCo 编译后的转轴、限位、阻尼、摩擦损失和 armature。 |
| `drives` | 从原生 actor 读回的姿态控制增益及饱和；MuJoCo 增益/偏置数组、力与控制范围及启用状态。任务的 MuJoCo 有效阻尼包含 `dt * kp`。 |
| `collision_filters` | 原生有方向的层过滤、prefab 显式覆盖及推断的邻接排除；MuJoCo 几何类型、掩码、接触参数、父子过滤和刚体排除。 |
| `initial_overlaps` | 查询方法、快照阶段、观测到的负距离及覆盖限制。 |
| `findings`、`errors`、`warnings` | 数值错误、缺失数据、刻意无质量坐标链接和几何重叠警告。非有限值以文本保存在合法 JSON 中并报错。 |

检查覆盖参数有限性、动态正质量、惯量形状/对称性、特征值符号与三角不等式、转轴归一化、限位顺序及驱动增益有限非负性。通过检查不代表硬件真实性。

## 静态刚体与转换假设

SuperDex 不允许对静态 actor 调用质量读取接口。报告用**零动态质量**表示其不参与动态质量计算，并保留原资产质量；这不是说安装结构实际没有重量。独立静态几何不提供刚体质心/惯量，这些字段保持 null。没有几何的 `NONE` 碰撞体不存在接触参数，记为 null。

现有 MuJoCo 转换器会为零质量刚体暂时插入正惯量占位，编译后恢复零质量/惯量，并检查组装质量矩阵。报告记录最终值及其原生来源；其中固定刚体的惯量可能在现有转换中被置零，审查不会恢复或隐藏这项差异。苹果质量是任务设定的 0.2 kg，质心与惯量由原生网格计算。驱动增益和接触系数是任务参数，不是实测电机或材料属性。

## 初始重叠警告的含义

SuperDex 对 AABB 重叠的表面对，双向确定性选取每个表面最多 256 个顶点，调用原生有符号表面距离查询。不推进仿真，不调用模型设置接口。相邻或排除的刚体对仍保留为几何证据。层过滤按方向读回；原生 API 没有公开的 actor 过滤读取接口，因此 actor 排除使用现有 prefab/转换规则推断，不能当成完整引擎接触筛选逻辑的证明。

有限顶点采样可能漏掉细小或只发生于边的交叠。原生 SDF 在 actor AABB 外返回的距离只是上界；这里将负采样值作为交叠证据，不证明整场景无碰撞。

MuJoCo 在独立 `MjData` 上复制初始关节位置并运行 `mj_forward`，报告生成接触中的负距离。运行中的模型参数与状态保持不变。查询遵守实际碰撞过滤，被排除的刚体对不会出现。这是引擎接触查询，不是穷尽网格相交检查；非 SDF 网格使用的凸包也不同于原生 SuperDex SDF，不能用警告数量比较引擎精度。

支撑接触中的微小重叠，以及被过滤的装配交叠，需要结合几何尺度与接触柔顺性解释。审查只报告距离，不引入新的成功容差。任务成功仍由[独立抓取验收](../demos/apple-stem-grasp/src/verify_sdf_grasp.py)判断。

## 验证

默认场景的准备快照中，每份报告覆盖 94 个刚体、54 个受驱动转动关节，未发现数值参数错误。识别出 13 个无几何的固定坐标链接，其中 10 个为指尖坐标。原生采样报告 82 对重叠：77 对在推断排除列表中，4 对涉及小指中节/指甲/指腹几何（无法直接读取 actor 过滤状态），另 1 对是苹果/桌面支撑。MuJoCo 生成 1 对重叠接触，即苹果/桌面，初始深度约 1.39 mm。这些是预抓取诊断，不是保持阶段穿透指标，也不能据此排列引擎优劣。

`tests/test_model_audit.py` 覆盖负/零质量、刻意无质量链接、非对称/负特征值/不满足三角不等式的惯量、非有限字段、非法轴/限位/增益、合法 JSON 输出，以及真实 MuJoCo 球体重叠与碰撞掩码变化。MuJoCo 测试还检查审查不改变运行中的状态和模型参数。原生 SuperDex 方块测试覆盖有符号距离查询、AABB 排除、静态属性可用性及刚体位姿/速度不变。接入演示的调用仍需完整双后端运行验证。

开发中的 API 探测发现接口限制：静态 actor 不允许调用 `get_mass`，独立静态几何没有刚体质心/惯量，`NONE` 碰撞体不允许调用 `get_contact_params`。导出器明确表示这些情况，不编造物理值、不调用不支持的接口。

实现：[model_audit.py](../src/dexlab/model_audit.py)。参数语义参考：[MuJoCo 惯量](https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-inertial)、[接触筛选](https://mujoco.readthedocs.io/en/stable/computation/index.html#selection)，以及已安装官方 SuperDex FP64 API 中 `Actor.get_points_distance_to_surface`、`Scene.is_layer_contact_enabled` 的文档字符串。

[研究重点](research-focus.zh-CN.md) · [苹果梗演示](../demos/apple-stem-grasp/README.zh-CN.md)
