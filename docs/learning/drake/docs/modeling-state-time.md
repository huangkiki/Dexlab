# E1 · 模型、坐标、状态与时间

读完本专题，应能把一份模型文件解释成 Drake 的拓扑和运行状态，给每个向量补齐坐标与单位，并说明一次读取发生在什么时刻。

先修：[对象导读](guide.md)、线性代数、刚体位姿与牛顿力学。阅读基线为 **Drake 1.57.0**，固定提交 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`；C++ 核心及 `pydrake` 绑定均按此提交阅读。未运行候选 Python 二进制，不声明它与源码构建一致；本课不需要 Isaac、ROS 或其他仿真宿主，也不把这些宿主的版本当成 Drake 版本。

| 路线 | 阅读顺序 | 本课交付边界 |
|---|---|---|
| A1 应用：建模 | 本页第 1–4 节 → 原创例子的建模部分 | 导入、资产、坐标、姿态、惯量、几何角色与 Finalize |
| A2 应用：状态 | [状态与时间](state-time.md)第 1–6 节 → 例子的 Context 部分 | 索引、状态所有权、重置、快照、缓存、时钟与输出采样 |
| B0 原理 | 本页第 3–4 节 → 状态页第 2 节 | 空间向量、惯量与 `q̇=N(q)v` 基础；完整约束与动力学装配留在 E3 |
| B4 原理 | 状态页第 5–6 节 | 连续/离散模型、Simulator 事件、积分器与求解器的区别；稳定性、接触离散与容差分析留在 E3 |

本专题是源码教学交付。例子仅做语法检查，没有执行模型构建、步进、接触、训练或性能实验。阅读练习带推导答案，均不要求运行引擎。验收范围见[记录](evidence/e1-validation.md)。

## 1. 先构建系统，再分配它的运行状态

Drake 把“系统是什么”和“此刻系统处于什么条件”分开。`MultibodyPlant` 保存 bodies、joints、frames、force elements、模型实例及端口定义；同一个系统可以有多个兼容的 `Context`。`SceneGraph` 保存几何拓扑并提供几何查询。它们不是两份互相竞争的刚体状态。

| 原生对象 | 职责 | 不应混淆的对象 |
|---|---|---|
| `RigidBody` | 刚体的身份、body frame、默认惯性参数入口 | 运行中的 `q/v` 存在 Context |
| `Frame` | 附着于刚体的坐标系；body frame 只是其中一种 | frame 原点不一定是质心，也不一定是关节原点 |
| `Joint` | parent frame 与 child frame 之间允许的相对运动 | `JointIndex` 不是它在 `q` 中的位置 |
| `ModelInstanceIndex` | 为一组模型元素和相应状态/端口建立命名范围 | 不是独立的物理世界或单独的 Simulator |
| `Parser` | 把文件内容加入现有 Plant，可向 SceneGraph 注册几何 | 不是运行期求解器，也不冻结模型 |
| `DiagramBuilder` / `Diagram` | 组装/持有子系统与端口连接 | 与并行结构的 Context 树不同 |
| `Simulator` | 调度事件和连续积分，推进 Context | 不负责把无效资产修成正确物理模型 |

同一 Plant 中的不同模型实例可以互相接触；按实例读写状态仅是数据选择。固定源码中 `world` 为模型实例 0，未显式分组的默认实例为 1，Parser 按需创建后续实例。业务代码应保存导入返回值或按名字查询，避免硬编码编号。[模型实例接口](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L328-L362)

典型构建顺序：

1. 建 `DiagramBuilder`，用 `AddMultibodyPlantSceneGraph(builder, time_step=...)` 添加并连接 Plant 与 SceneGraph。
2. `Parser(plant)` 导入模型；配置 `package_map`、添加刚体/关节/驱动器、设置固定连接和默认参数。
3. 明确哪些根刚体应固定到 world；需要固定基座时，在 Finalize 前用 `WeldFrames` 等建模 API 表达。
4. `plant.Finalize()` 固定多体拓扑、声明状态与端口，并建立相应碰撞过滤。
5. 使用已声明的端口连接控制、观测等系统，再 `builder.Build()` 得到 Diagram。
6. `diagram.CreateDefaultContext()` 创建整棵 Context 树；通过 Plant 取得属于它的子 Context，初始化运行状态。

`Finalize()` 和 `Build()` 是两个边界：前者结束 Plant 的拓扑建模，后者结束 Diagram 的组装。Finalize 不会推进时间，也不会自动解决初始穿透或保证动力学可行。Builder 单次使用，Build 后其子系统所有权交给 Diagram。不要保留一个已销毁 Diagram 中的 body/frame/plant 引用。[Finalize 职责](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L930-L949)、[Builder 生命周期](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/systems/framework/diagram_builder.h#L23-L34)

默认情况下，Finalize 为尚未连到 world 的基体选用 quaternion floating joint：一个浮动基体多出 7 个位置参数和 6 个速度自由度。1.57.0 还允许选择 RPY floating 或 weld base joint；RPY 有姿态奇异点。不要用“成功加载了 URDF”推断基座固定，也不要认为所有导入模型必然采用四元数基座。[基体关节策略](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1757-L1788)

## 2. 模型导入是语义转换，不是文件能打开就结束

### 2.1 Parser、实例和资源路径

本版本 `Parser` 列出 URDF、SDFormat、MJCF、Drake Model Directives 和 OBJ。URDF 的一个 robot 对应一个模型实例；MJCF 的多个 body 通常归入一个实例；SDFormat 和 directives 可能产生多个/嵌套实例。保留 `AddModels(...)` 返回的实例列表，随后核对名称、根刚体、关节和自由度。格式受支持不等于其所有扩展、控制器或其他引擎求解语义都被保留。[格式与实例约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h#L27-L86)

| 入口 | 输入与用途 | 容易漏掉的条件 |
|---|---|---|
| `Parser.AddModels(file_name)` | 根据文件后缀加载本地文件，可返回多个实例 | 文件中的引用资源也要能解析 |
| `AddModelsFromUrl(url)` | `file://`、`package://` 或 `model://` | package/model 名称必须在该 Parser 的 PackageMap 中解析 |
| `AddModelsFromString(text, "urdf")` | 原创内嵌小模型，格式参数不带点 | 本版本不支持传入 OBJ 正文 |
| `parser.package_map().Add(name, path)` | 把一个明确的包名映射到已有目录 | 映射本身不会修正错误的网格尺寸 |
| `AddPackageXml(...)` / `PopulateFromFolder(...)` | 从包声明/目录建立映射 | 应知道扫描的是哪个资产集合 |
| `SetStrictParsing()` | 把 Parser 警告升级成错误 | 不能证明源资产物理正确或许可完整 |
| `SetAutoRenaming(True)` | 重复加载时解决实例重名 | 自动改名后不能继续硬编码旧名字 |

例子的所有资产均内嵌原创，不依赖网络；真实模型建议记录包名、源仓库提交、资源文件哈希及许可。`PackageMap` 也有远程包功能，不能把“第一次下载到了”当成长期可复现的资产定位。离线/联网策略、缓存和包版本需要单独记录。[Parser 方法](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h#L210-L269)、[PackageMap 本地与远程资源](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/package_map.h#L48-L166)

### 2.2 单位与资产审查顺序

Parser 在格式没有另行声明时按 SI 单位和弧度解释字面量：米、千克、秒、弧度；速度分别是 m/s、rad/s；力和力矩分别是 N、N·m；转动惯量是 kg·m²。角度的“无量纲”不表示可以把 degree 数字直接当 radians 输入。[单位约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h#L83-L89)

资产审查按以下顺序进行，避免看到网格大小合适就停止：

1. **长度和姿态**：网格原点/比例、link frame、joint frame、inertial frame 是否各有依据。
2. **连接**：父子关节、运动轴、基座固定/浮动、关节类型；名称存在不证明对应关系正确。
3. **质量属性**：质量、质心、惯量参考点和表达坐标系；不要把中心惯量当成绕 link 原点的惯量。
4. **几何角色**：视觉形状、接近查询/接触形状是否存在并对齐；不能从一张渲染图推断接触网格。
5. **导入边界**：检查 Parser 警告、被忽略字段、重复名字和显式设置；后续接触材料/过滤在 E3 深入。
6. **来源与许可**：代码仓库许可不必然覆盖其中的 CAD、纹理或外部下载模型。记录每项许可，不复制未经确认的资产。

单位缩放有可推导的影响。几何长度乘 `s` 时，若密度固定，则质量乘 `s³`，中心转动惯量乘 `s⁵`；若人为固定质量，则惯量乘 `s²`。这是按均匀几何缩放推得的量纲关系，不表示 Parser 自动替你执行这些修正。

OBJ 直接导入尤其要小心：本版本按封闭体积中的均匀材料、约 1000 kg/m³ 的密度推断质量属性，顶点按米读取；非闭合网格可能产生意外结果。若 SceneGraph 已注册，还会赋予 illustration、perception 和 proximity 角色。这是此导入入口的规则，不能套用到“URDF 引用一个 OBJ 作为视觉网格”的情形。[OBJ 导入合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/parsing/parser.h#L59-L81)

### 2.3 视觉、感知、接触与惯量是四件事

`RegisterCollisionGeometry` 把几何赋予 proximity 角色；`RegisterVisualGeometry` 按重载和属性赋予 illustration/perception 角色。刚体惯性参数属于 Plant 的刚体模型，几何角色属于 SceneGraph。程序化添加一个外观漂亮的 box 不会自动等价于“质量、接触形状和相机可见性都已定义”。反过来，一个没有视觉角色的刚体仍可以有有效动力学模型。[几何注册与角色](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L2435-L2507)

## 3. 让坐标名承担检查工作

### 3.1 位姿 `X_AB` 的方向

约定 `W` 为 world，`B` 为 body，`Bo` 为 body frame 原点，`Bcm` 为质心。`X_AB` 表示 **B 在 A 中的位姿**，包含 `R_AB` 和从 `Ao` 指向 `Bo`、在 A 中表达的 `p_AoBo_A`。对于同一点 Q：

$$p_{AoQ}^{A}=R_{AB}p_{BoQ}^{B}+p_{AoBo}^{A},\qquad X_{AC}=X_{AB}X_{BC}.$$

Drake 中可写 `X_AB @ X_BC`，用 `inverse()` 反向。方向向量仅做旋转，点坐标要加平移；不能把速度向量作为点交给完整位姿变换。`RigidTransform` 自身不存 A/B 的语义标记，因此 `X_AB @ X_CB` 可能数值可乘却没有所需物理含义。[类型与坐标合同](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/rigid_transform.h#L19-L58)

两 frame 可以附着在同一刚体不同点。例如 body frame 在安装孔、inertial frame 在质心、camera frame 在镜头、joint frame 在铰链；刚体相同不意味着它们的平移为零。比较导入器、FK 和传感器输出时，先写清 frame 再比较矩阵。

### 3.2 四元数、RPY 与广义位置

Quaternion floating joint 的位置顺序为 `[qw, qx, qy, qz, px, py, pz]`，前四项为 child joint frame M 在 parent joint frame F 中的方向，后三项为从 F 原点指向 M 原点、在 F 中表达的位置。四元数使用 scalar-first 的 **wxyz**；不要把其他库常用的 xyzw 直接拷贝进来。[关节配置布局](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/quaternion_floating_joint.h#L20-L33)

单位四元数满足 `qᵀq=1`，`q` 与 `−q` 表示同一方向。因而姿态误差不能直接等同于两四元数分量的欧氏差；用于插值或角速度转换时也要处理符号与归一化。`RigidTransform` 的四元数构造路径允许非零有限四元数再生成旋转，但这不意味着任意 `SetPositions` 数组都自动满足配置约束；该 setter 的公开检查主要是 Context、长度和有限性。保持有效配置是调用者的责任。[位姿构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/rigid_transform.h#L92-L114)、[位置 setter](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L3126-L3144)

`RollPitchYaw` 对应外禀 XYZ，等价于内禀 ZYX 的反向参数叙述。它适合表达模型姿态，但在 pitch 接近 ±π/2 时会遇到参数化奇异；角速度也不是三个 RPY 角的逐项导数。选择显示姿态参数和选择积分用的配置参数是两个决定。[RPY 构造定义](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/math/rigid_transform.h#L98-L106)、[基座参数化限制](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h#L1770-L1778)

### 3.3 空间速度需要三个 frame 和一个参考点

`SpatialVelocity` 的六项是 **角速度在前、线速度在后**。写 `V_MB_E=[ω_MB_E; v_MBo_E]` 时，B 是运动 frame，M 是测量运动所相对的 frame，E 是分量表达的 frame；线速度对应 B 的原点 Bo。对象只保存数值，不替你存储这些字母。[空间速度约定](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_velocity.h#L20-L37)

仅旋转表达坐标系时，ω 和 v 都乘相同旋转矩阵。改参考点则不同：若 B、C 刚性连接、`r=p_BoCo_E`，则

$$\omega_{MC}^{E}=\omega_{MB}^{E},\qquad v_{MCo}^{E}=v_{MBo}^{E}+\omega_{MB}^{E}\times r.$$

这对应 `V_MB_E.Shift(r)`。例：ω=(0,0,2) rad/s、Bo 的线速度为零、Co 在 Bo 的 +x 方向 0.3 m，则 Co 的线速度为 (0,0.6,0) m/s。只旋转原点速度不会得到这个结果。若 C 相对 B 也在动，还要加相对运动项，不能再用刚性 Shift 代替速度合成。[Shift 实现与条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_velocity.h#L73-L116)

相应地空间力按 `[τ; f]` 排列，力矩必须注明计算点。同一点、同一表达系下 `FᵀV=τ·ω+f·v` 是功率（W）。改点必须一起变换力矩与线速度，才能保持功率不变；不能随意调换前后三项来“适配六维数组”。详细力/冲量观测在 E3。[空间力定义](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/math/spatial_force.h#L20-L48)

## 4. 惯量：质量之外还要问“绕哪一点、在哪个系”

记 `I_BP_E` 为刚体 B 绕 P 点、在 E 中表达的 3×3 转动惯量。令 `c=p_PBcm_E`，`[c]×` 为叉乘矩阵，则空间惯量为

$$M_{BP}^{E}=\begin{bmatrix}I_{BP}^{E}&m[c]_{\times}\\-m[c]_{\times}&mI_3\end{bmatrix}.$$

它与 `[ω; v_P]` 的排列一致，且各块单位不同：左上 kg·m²、交叉块 kg·m、右下 kg。不能把整个 6×6 当成六个相同单位的独立惯量，也不能把它与整个关节系统的广义质量矩阵 `M(q)∈R^{nv×nv}` 混淆。[空间惯量块结构](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h#L26-L76)

给定中心惯量 `I_BBcm_E` 时，平行轴定理是

$$I_{BP}^{E}=I_{BBcm}^{E}+m((c^{T}c)I_3-cc^{T}).$$

这是同一刚体、同一表达坐标系的平移；换表达坐标系还需 `I_A=R_AE I_E R_AEᵀ`。Drake 将这两步分别表达为 `SpatialInertia.Shift(p_PQ_E)`（从原参考点 P 移到 Q）和 `ReExpress(R_AE)`（更换表达系）。注意 Shift 的向量是 P→Q，不是质心位置的反复复用。[ReExpress 与 Shift](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h#L743-L814)

| API / 量 | 参数含义 | 常见误用 |
|---|---|---|
| `RotationalInertia` | 3×3 转动惯量，kg·m²，需自己记录参考点/表达系 | 只复制三个对角项而忽略有依据的惯性积 |
| `UnitInertia` | 单位质量转动惯量 `G=I/m`，单位 m² | 误以为是单位阵，或直接放入 kg·m² 的 I |
| `SpatialInertia(mass, p_PScm_E, G_SP_E)` | 第三项是**绕 P 的 UnitInertia** | 把中心转动惯量传进去，再由构造器“自动平移” |
| `MakeFromCentralInertia(mass, p_PScm_E, I_SScm_E)` | 第三项是**绕质心的 RotationalInertia** | 将已经平移过的惯量再次平移 |
| `SolidBoxWithMass(m, lx, ly, lz)` | 均匀实心盒，三边为完整长度，惯量绕几何中心 | 把半长当作全长，或套用到非均匀真实零件 |

默认保持惯性有效性检查，不能靠 `skip_validity_check=True` 修好不物理的资产。非负主惯量只是必要条件的一部分，真实质量分布还满足三角不等式；若报错，应追查单位、参考点、符号和几何假设。[工厂方法](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h#L116-L169)、[构造器语义与检查](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h#L475-L507)、[物理有效性条件](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/tree/spatial_inertia.h#L572-L589)

原创例子取 m=2 kg、边长 (0.2,0.4,0.6) m 的均匀盒，body frame 恰在质心、惯性主轴与盒轴对齐：`Ixx=m(ly²+lz²)/12≈0.0866667`、`Iyy≈0.0666667`、`Izz≈0.0333333` kg·m²。URDF 的 inertial origin 为零，因此无需平移。若 body 原点距质心沿 x 为 0.1 m，绕 body 原点的 Iyy/Izz 各增加 `m×0.1²=0.02`，Ixx 不变；这不是质量变化，而是力矩参考点变化。

## 5. 原创模型与阅读练习

[model_state.py](../examples/model_state.py) 内嵌一个均匀盒 URDF，显式设置 `time_step=0.001`，保留导入的模型实例，Finalize 后设置浮动基座姿态/速度，并展示 Context 克隆和位置副本。无远程资产、无隐藏封装、无 `AdvanceTo`；本轮未执行它。继续阅读[状态与时间](state-time.md)，再逐行对照例子。

1. **为什么先 Finalize，再 Build？** 写出两者各自冻结的内容，以及哪一步可获得 Plant 的最终状态尺寸。
2. **同一个 link 的 inertial origin 平移了 0.1 m，视觉 origin 不动，是否应该移动整条 link？** 说明两个 frame 的职责。
3. **把毫米资产直接按米读取，保持密度不变，质量和惯量分别误差多少倍？** 不运行，按量纲推导。
4. **相机原点相对 body 原点偏置 0.3 m，body 纯转动时，相机线速度为什么可能非零？** 使用第 3.3 节数值。
5. **给 `SpatialInertia` 传入中心惯量和非零质心偏置，为什么可能得到错误结果？** 区分它的普通构造器与工厂方法。

<details>
<summary>答案与推理</summary>

1. Finalize 建立多体拓扑并声明状态/端口；Build 完成包含 Plant 等子系统的 Diagram 组装。状态尺寸与关节在状态中的最终偏移需在 Finalize 后查询；Build 不能替代 Finalize。
2. 不应机械地移动 link。inertial origin 描述质量属性所用的参考 frame，visual origin 描述外观相对 link frame 的位姿；只有源资产确实错误时才分别修正。
3. 长度放大 1000 倍，密度不变时质量为 10⁹ 倍、惯量为 10¹⁵ 倍。若已经强制固定质量，惯量的几何尺度效应为 10⁶ 倍；必须先写清假设。
4. 相机点线速度包含 `ω×r`，本例为 (0,0.6,0) m/s。相同刚体上各点共享角速度，不共享线速度。
5. 普通构造器需要绕指定 P 的单位质量惯量；从中心数据出发应使用 `MakeFromCentralInertia` 或先正确应用平行轴定理，再按其所需单位构造。

</details>

下一页：[状态、Context 与时间](state-time.md)。后续 E2 接驱动/机器人，E3 解释约束、接触与数值求解；本课本身只覆盖 B0/B4 基础；现可继续读[E3 动力学与求解](contact-solvers.md)。
