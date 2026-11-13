# IPC接触模式：增广拉格朗日、CCD与有限推进

本课解释固定3.15.0中`ipc` flag的实际实现。先读[flex](flex-and-elasticity.md)、[原生solver与metric](solvers-and-integration.md)及[力观测](force-observations.md)。当前模式标为experimental，下面是源码课程，没有执行IPC、验证防穿透或复现论文结果。

## 1. 名称不能替代接触律

这个模式是discrete积分器上的**barrier-free augmented-Lagrangian**路径；源码明确说明以乘子和活动集合替代log barrier。不能因名称含IPC就把经典对数屏障公式、摩擦模型或任意软体支持套过来。[文件定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L15-L20)。

它并不替代弹性模型：elastic2d仍通过有效metric进入内层问题，边等式仍可通过原生constraint rows约束形变；IPC主要负责其拥有的接触、位置级外循环和CCD推进。[模式契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L735-L767)。

| 必要条件/范围 | 此固定树实际行为 |
|---|---|
| integrator | 必须discrete |
| solver | 必须CG；内层走单体matrix-free CG |
| flags | 不支持fwdinv或sleep |
| flex | 受该模式处理的是dim=2；模型中受支持的flex统一走该模式 |
| IPC拥有的接触 | 支持flex之间/自接触，以及flex与静态plane/sphere/capsule/box/mesh |
| 保留原生rows的接触 | 移动刚体接触及其他geom类型，不获得同样CCD承诺 |
| 摩擦 | IPC拥有的pair只有法向力，忽略该pair的friction/condim切向含义 |
| 没有2D flex的模型 | 仍执行位置级step，刚体接触保持原生rows |

选项检查见[forward](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1715-L1739)，几何支持和所有权见[continuous collision](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L220-L225)、[owner谓词](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L896-L906)。网格在相关静态特征查询中使用编译mesh/hull数据，不能把名称“mesh”扩大成任意非凸三角网格的所有连续碰撞情形。

## 2. 为什么pin到旋转body会被拒绝

一部分flex点由三个slide表示；一般附着点用body的运动与点Jacobian进入求解。IPC的CCD扫掠假设是直线段，而hinge/ball/free的有限转动让点走弧线。因此附着链必须静态或只有slide，旋转关节会报错；自由flex点的slide frame也不能放在一个同时参与运动的关节树下面。[自由点/附着分类](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L617-L725)、[直线运动检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L739-L773)。

这是算法几何假设导致的支持边界，不是把关节名改成slide就能保持同样机器人运动。默认flex弹性支持的一般body附着，不自动等于IPC支持同样附着。

## 3. 位置、速度切线与接触残差

给定步长h>0，求解用广义切线w表示步末速度，再由原生配置积分得到候选位置：

$$
a=(w-v_n)/h,\qquad q_{n+1}=q_n\oplus(hw).
$$

对于纯平移点，候选位移就是hw；有四元数的刚体仍通过配置空间积分。源码维护候选iterate和已接受的`xfree/wfree`两套值，不能把“内层求到候选加速度”当成状态已经提交。[切线与端点](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L337-L386)。

对pair在当前参考位置线性化几何间隙，记c为扣除rest standoff后的线性化长度，λ为法向乘子，k为基础接触刚度，kₐ为经过age衰减的刚度。内层单侧代价可写成：

$$
\phi(c;\lambda)=\tfrac12 k_a\,[\min(c-\lambda/k,0)]^2.
$$

c单位m，k单位N/m，λ单位N，所以λ/k是长度、φ单位J。乘子更新分支等价于：

$$
\lambda_{\rm next}=\max(0,\lambda-kc).
$$

这个表达只解释该固定实现的线性化法向AL步骤，不是所有MuJoCo接触统一采用的定律。k取自然频率平方乘pair中最小的正顶点质量；全pin情况有小正值兜底。衰减影响代价中的kₐ，而乘子更新使用基础k。[质量尺度](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L81-L97)、[更新](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L156-L189)、[单侧代价](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L291-L335)。

merit还包含以有效metric衡量的惯性偏离与原生constraint代价。其惯性部分在位置能量单位下为：

$$
\Phi_G=\tfrac12h^2(a-a_{\rm smooth})^\mathsf{T}
\widehat M(a-a_{\rm smooth}).
$$

h²将广义加速度二次式转为能量尺度；刚体/弹性耦合通过同一个metric进入，不能只对flex顶点独立求penalty再事后覆盖刚体速度。[merit](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L271-L288)、[原生代价合并](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L563-L594)。

## 4. 一步如何经过内层与外层

1. 根据支持的flex、自由点与附着body建立owned DOF；预测无约束位移，查询swept候选。
2. 以跨步顶点乘子/age初始化pair活动集合，在当前已接受位置重新线性化法向和几何权重。
3. 把pair暂时发布为附加单侧constraint rows，保留原生刚体/等式rows。映射含h²，刚度相应缩放，内层调用`mj_fwdConstraintCG`。
4. 在候选方向上做merit线搜索；这只选一个能量方向，还未给出碰撞可行性证书。
5. 更新乘子与age，对已接受位置到候选位置的线段重新查询；CCD限制可提交比例，按最早接触规则纳入新候选。
6. 更新accepted tangent/位置，继续外循环，最终通过`mj_commit`提交端点、有效加速度、activation/history/time与plugins。

[临时rows](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L404-L458)、[内层求解与working-set扩充](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1057-L1102)、[merit/CCD/提交](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1128-L1282)。临时rows在内层后恢复原来的数组指针/计数；并非最后`d.contact`或`efc`里一定留有每个IPC pair供通用contactForce接口逐个读取。

## 5. CCD保护的是哪一段运动

`mjc_advance`根据参与点位移建立间隙缩小速度上界，对正的初始gap做保守推进，使受支持pair的gap保留初始值的一部分。源码使用20%的gap floor，单pair最多32次推进迭代。自碰撞可消去同flex的共同平移，但两个flex间不能消去这个平均运动，否则会低估相对闭合速度。[CCD实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L678-L767)。

这依赖初态和几何覆盖：**g₀≤0的pair在CCD缩步分支直接跳过**，交给接触求解处理；重合特征的法向还可能被置零以避免NaN。因此不能把模式描述成能自动修复任意初始自交/穿透，或对未被该路径拥有的移动刚体接触也提供相同保证。[初始间隙分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L734-L755)、[退化法向](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L488-L502)。

候选查询会考虑swept travel和当前BVH与试探位置的差异，但仍受constraint/contact flags、contype/conaffinity、selfcollide及支持的geom范围约束。主动过滤掉某pair，算法也不会替它阻止相交。[候选过滤](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L922-L985)。

## 6. 收敛、限额和不完整推进是三件事

内层CG用model的iterations/tolerance；外层另有固定上限1024、连续stall上限64和自己的速度阈值。不是把`opt.iterations=100`就得到“整个IPC恰好100次迭代”。源码累计内层solver_niter，但这个数也不是外层次数。[上限](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L937-L945)、[CG计数累加](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1062-L1082)。

线搜索最多进行8轮试探，即使没满足下降也接受最后试探；CCD随后再约束可接受运动。外层满足完整推进且接受完整线搜索步或相应收敛条件才正常退出，也可能因stall/上限退出。[线搜索](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1128-L1150)、[退出](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1210-L1235)。

特别要看**不完整推进**：只提交了部分运动，time仍前进h；这会表现为运动变慢，不能用time增长正常判断成功。实现会通过`mju_warning`报告不完整推进，而它是日志警告，不是带Data的`mj_warning`计数。因此[E5 rollout](cpu-batching.md)检查`d.warning`的填充机制不能保证捕获这条IPC警告，应该保存结构化日志及模式适用性信息。[退出警告](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1283-L1300)、[日志实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_util_errmem.c#L348-L355)、[两种warning API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mujoco.h#L999-L1028)。

## 7. 尺度、力观测与可恢复状态

当前常量按米尺度、毫米厚度、毫秒步长设置：gap cap为0.001m，基础检测band为0.003m，速度判据0.05m/s。实际pair band/standoff还按半径收窄，不是所有pair都恰好隔1mm。把模型单位整体变成厘米但不换算，不会保留同一无量纲算法。[常量](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L43-L62)、[pair band](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L623-L638)、[standoff](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_continuous.c#L481-L485)。

normal multiplier和age跨步保存在`flexvert_lambda/flexvert_conage`，不是`mjtState`的任意组合都会覆盖。活动pair还在外循环中维护，其标识/age与聚合顶点存储有自己的转换；保存qpos/qvel甚至INTEGRATION都不能声明IPC精确续跑。[顶点状态](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L119-L154)、[模式状态声明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L735-L743)。

有2D flex时，`mj_forward`跳过原constraint stage，qacc为free-flight；`mj_step`的IPC内层得到有效加速度/约束力后，再计算加速度阶段sensor，然后提交。因此该阶段用户/plugin sensor可以每步被评估两次。末尾qfrc_constraint包含原生rows与最后IPC内层rows的贡献；若运动只部分接受，它不应不加说明地解释成完整连续时间接触轨迹的平均力。[forward分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1933-L1957)、[力与sensor重算](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_ipc.c#L1247-L1282)。

## 8. 带答案阅读练习

1. **本版IPC的接触能量是log barrier吗？** 不是；实现使用单侧AL二次代价、乘子和活动集合。
2. **friction设很大，IPC布料就有大切向摩擦吗？** 该模式拥有的pair是frictionless；保留原生rows的其他接触另论。
3. **为什么不能pin到hinge链？** 当前CCD扫直线，有限转动走弧线，不符合该路径假设，代码拒绝。
4. **初始自交可以靠CCD保证修好吗？** 不可以；非正gap不走正常CCD缩步保护，退化几何也有特殊处理。
5. **time增加h说明运动全量完成吗？** 不说明；不完整推进仍增加h，并打印日志警告。
6. **rollout的Data warning检查能覆盖IPC不完整警告吗？** 不保证；此处是mju_warning日志，不修改同一Data warning计数。
7. **所有IPC接触都能从最终contact数组逐一取力吗？** 不保证；IPC临时rows会恢复，需遵循实际观测接口与聚合力语义。
8. **INTEGRATION数组能精确恢复IPC吗？** 不能覆盖跨步乘子/age等全部内部状态，需明确恢复边界。
