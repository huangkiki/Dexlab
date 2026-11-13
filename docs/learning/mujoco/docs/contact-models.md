# 接触几何、摩擦锥与材料组合

本篇覆盖 A4/B2。先读[建模与坐标](modeling-and-frames.md)和[动力学执行链](dynamics-and-pipeline.md)；需要点积、矩阵转置和基本力学。固定 MuJoCo 3.15.0 原生核心，来源均指向同一 SHA。本轮只有源码与静态检查，没有碰撞/摩擦实测；参数例子是手算，不是引擎输出。

## 1. 先分清三个问题

**碰撞检测**回答哪些几何体多近、法向和接触点在哪里。**接触模型**回答在这些局部坐标下允许什么法向力/摩擦力，以及柔顺程度。**数值求解器**在当前状态、参考与正则化下找约束力和加速度。增加 `iterations` 只能改变第三项的近似程度，不能把凸包变回凹物体，也不能改正摩擦单位或漏掉的碰撞对。

原生刚体通常是点接触模型：`contact.pos` 是两表面最近位置之间的中点，`dist` 正为分离、负为穿透；`frame` 是**三行世界坐标轴**，第一行是从 `geom[0]` 指向 `geom[1]` 的法向，其余两行是切向。法向对应局部 x 轴，不能按可视化常用的 z 轴读取。[结构体契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjdata.h#L37)

## 2. 候选对到窄相：过滤比调 solver 更早

[碰撞流程](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1753)以 body/flex 的包围体与 sweep-and-prune 产生候选，再通过 body 内 BVH 的 AABB 中相筛选，最终按几何类型派发窄相函数。primitive 对可有专用函数；一般 convex 对与 mesh 凸包由 convex 碰撞路径处理。mesh 的视觉三角面不是保证凹碰撞的接口；需要明确拆分成多个凸几何或选择具备所需语义的另一表示，导入/资产边界见 E1。

`nativeccd` 这里选择原生 **convex collision detection** 路径；同提交文档描述 GJK/EPA，不能仅凭缩写 CCD 宣称刚体步进已做连续时间扫掠碰撞。`ccd_iterations/ccd_tolerance` 是几何算法停止参数，不是约束 solver 的 iterations/tolerance。多接触点算法改变接触离散化；仍不是接触面积上的压力积分。[窄相与凸碰撞](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1807)

动态 geom 对的位掩码兼容条件为

$$
(\mathrm{contype}_1\ \&\ \mathrm{conaffinity}_2)\ne0
\quad\text{或}\quad
(\mathrm{contype}_2\ \&\ \mathrm{conaffinity}_1)\ne0.
$$

这不是两个方向都必须成立。[位掩码实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L240) 还要考虑 same-weld-body、父子 body 过滤、静态/睡眠条件，以及 `<exclude body1=... body2=...>`。位掩码匹配仅表示通过这一关，不保证产生 contact。[body 对过滤](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L302)

显式 `<contact><pair .../></contact>` 使用独立配对及参数路径，不能把动态过滤规则机械套过来：geom 层 contactfilter/位掩码分支只对 `ipair<0` 执行；显式 pair 仍有睡眠、包围球与可用碰撞函数检查。用户 `mjcb_contactfilter` 也替代该 geom 位掩码检查，而不是取消更早的候选过滤。[pair 分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L565)

## 3. margin 与 gap：本版不是“取最大后相减”

对没有显式 pair 的普通两 geom，3.15 的实现为

$$
m=m_1+m_2,\quad g=g_1+g_2;
\quad\text{窄相候选距离阈值为 }m+g,\quad
\text{施力阈值为 }m.
$$

显式 pair 直接使用 pair.margin/pair.gap；启用 contact override 时 margin 会走全局覆盖。`contact.includemargin=m`。忽略 adhesion、退化/融合/无 DOF 情况，返回的 contact 在 `dist >= m` 时标为 gap/excluded；在 `dist < m` 时才进入约束装配。窄相对精确等号的检测有其实现边界，不应用“刚好相等”构造脆弱逻辑。[求和与 pair 读取](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L174)、[窄相输入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L1940)、[exclude 条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L1824)

手算：两个 geom 的 margin 为 1 mm、2 mm，gap 为 4 mm、0 mm；合成 m=3 mm、g=4 mm。表面距 5 mm 时可能被检测并记录，却不生成普通接触力；距 2 mm 时已进入施力区，尽管尚未几何穿透。**接触力不等于必须 dist<0**。正 margin 可以在分离时产生力，负 margin 则允许一定穿透后才进入施力区；检测仍需满足可用阈值配置。

`data.ncon` 只数检测记录，`contact.exclude` 可表示 gap、融合、无 DOF 或 passive flex 接触；`efc_address>=0` 才能确认有 solver 行。Geom adhesion 会特意让 gap 中的接触保持激活，见第 6 节，不能把上述无黏附条件当成所有接触的定律。

## 4. condim、摩擦系数和锥

| condim | 支持的局部 wrench 分量 | elliptic 行数 | pyramidal 行数 |
|---|---|---:|---:|
| 1 | 法向力 | 1 | 1 |
| 3 | 法向力、两个切向力 | 3 | 4 |
| 4 | 上述三力 + 绕法向扭转摩擦矩 | 4 | 6 |
| 6 | 上述四项 + 两个滚动摩擦矩 | 6 | 10 |

2 和 5 不是合法 condim。Geom 的 `friction="slide spin roll"` 有三数，接触会展开成 `[slide, slide, spin, roll, roll]`；pair 的 friction 有五数，允许两个切向/滚动方向不同。实际 friction 赋值还受最小摩擦系数夹取；若要明确无摩擦模型，使用 condim=1，不依赖把三个数填零来绕过锥行。[夹取实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L170) 滑动系数无量纲，spin/roll 是**长度**，因为约束分别比较 N·m 与 N。不能把滚动摩擦值解释成另一个无量纲库的同名参数。[condim 与量纲](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1056)、[展开实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L1808)

设无 adhesion 的局部接触力为 `f=(fn,ft1,ft2,τn,τt1,τt2)` 的前 n 个有效项，所有使用的 μ>0。Elliptic 可行域为

$$
f_n\ge0,\qquad \sum_{i=1}^{n-1}(f_{i+1}/\mu_i)^2\le f_n^2.
$$

它是**耦合预算**：扭转/滚动与滑动占用同一锥，不是给每个方向分别一个独立最大值。对 condim=3、μ=0.5、fn=10 N，两个切向分别 4 N 虽都小于 5 N，合起来仍越过圆截面。

Pyramidal 使用 `2(n−1)` 个非负边权 λ；每对边形如 `en ± μ_i ei`，重建 `f=Eλ`。其截面是内接多面体，方向响应和软约束正则化与 elliptic 不同；两者不是“同一个锥精度高低”的可互换标签。`cone` 与 `solver` 是独立选项，PGS/CG/Newton 都能进入两种锥分支。[装配边基](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L1682)、[算法适用锥](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1464)

注意同提交 computation 的 condim 段仍有“由 solver 决定 cone”的陈旧措辞；实际 `mj_isPyramidal` 只检查 `opt.cone`，以[实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L43)为准。

## 5. 材料组合有条件，不能只写 max 或平均

运行时没有一个自动辨识的“材料对象”；这些接触参数通常来自 geom 或显式 pair。对动态两 geom 的组合，按[完整函数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L1724)逐项阅读：

| 参数 | priority 不同 | priority 相同 |
|---|---|---|
| condim | 高 priority 一侧 | 两侧最大值 |
| friction 三数 | 高 priority 一侧 | 逐项最大值，再展开五数 |
| solimp 五数 | 高 priority 一侧 | 由 solmix 权重线性混合 |
| solref 两数 | 高 priority 一侧 | 两侧首项都正则 solmix 混合；否则逐项最小值 |
| geom adhesion | 高 priority 一侧 | 两侧相加 |
| margin / gap | 独立求和逻辑 | 独立求和逻辑 |

若两 solmix 都不少于 `mjMINVAL`，权重 `w=s1/(s1+s2)`；两侧都太小则各半；只有一侧太小则另一侧权重 1。因此“solmix=0 就让材质所有属性消失”不成立，它只控制对应 solver 参数的混合。friction、condim、margin 并不跟着这个权重。

直接格式 solref 使用非正数编码刚度/阻尼，取 min 相当于选择各分量更负的值，甚至可能把两个材质的不同分量组合起来；不是统一取“硬的那一整套”。混用正/非正格式也会进入 min 分支，格式合法性仍在装配时检查。

显式 pair **读取 pair 自己的** dim、五维 friction、solref、可选 solreffriction、solimp、adhesion，不再执行上述 geom 材料混合；全局 override 又可能覆盖 solver 参数/摩擦。排错应查看最终 `data.contact[i]`，而不能只看某一 geom 的 XML。[pair 参数落地](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L2030)、[override 赋值](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L188)

## 6. solref / solimp 是加速度层的软约束，不是 restitution 数字

先讨论普通连续加速度分支的一条法向行，残差 `r=dist−includemargin`（m）、相对法向速度 `vn`（m/s）。源码构造

$$
a_{ref}=-Bv_n-KI(r)r,\qquad
R=\frac{1-I}{I}\widehat A_{ii},\quad D_{row}=1/R.
$$

`I` 是 0 与 1 之间的阻抗，R 是逆惯量量纲的正则化；不是物体材料的杨氏模量。`Âii` 通常由初始构型的惯量近似，`diagexact` 可改用当前 metric backbone 的精确对角；多行耦合下 I 不等于实际加速度百分比，discrete 的 coupling 还会留下近似。后续 solver 同时决定所有行，不能逐点独立套 `F=k penetration` 复现整机。[R 与 KBIP](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2166)、[对角近似边界](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/index.rst#L1600)

`impratio` 调整摩擦方向相对法向的正则化：elliptic 首个摩擦行先取 `Rfriction=Rnormal/impratio`，其余摩擦行再按各 μ 的平方配平。增大它不是增大 Coulomb 系数，也不保证完全静止；pyramid 的边把法向与摩擦混在一起，不能把同一个数理解为独立切向刚度倍率。[实际 R 调整](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2258)

`solimp=(d0,dwidth,width,midpoint,power)` 控制残差绝对值上的阻抗曲线：零残差接近 d0，达到 width 接近 dwidth，midpoint/power 控制形状。width 的单位跟约束位置残差一致（本例 m），其余无量纲。实际参数被夹到支持范围；width 太小时退化为常值处理。[曲线实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2108)

正格式 `solref=(timeconst,dampratio)`，t 是秒、ζ 无量纲；源码的法向参考系数为

$$
K=\frac{1}{d_{width}^2t^2\zeta^2},\qquad
B=\frac{2}{d_{width}t}.
$$

直接格式 `solref=(-k,-b)` 则有 `K=k/dwidth²`、`B=b/dwidth`，k 单位 s⁻²、b 单位 s⁻¹；**k 不是 N/m**，还要通过约束惯量与阻抗得到力。摩擦损失和 elliptic 的非正常行令 K=0；pair 的非零 solreffriction 可为 elliptic 摩擦行另设参考阻尼。[系数生成](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L2184)

连续分支默认 refsafe 把正 timeconst 下限设为 `2h`；discrete 不用这条统一夹法，而是对超出步长可解析刚度的接触/限位行调整 K/B，再同时缩放 R 与 reference。详见[数值篇](solvers-and-integration.md)。把“禁用 refsafe”当作通用精度开关会绕过这项数值保护。阻尼比、碰撞速度、步长、阻抗曲线共同影响反弹；这里没有可直接跨引擎对应的单一 restitution 参数。

3.15 的 geom/pair **adhesion** 是另一项（不是 E2 的 adhesion actuator）：允许净法向拉力。核心把 `−δ Jnᵀ` 加入 `qfrc_adhesion`，同时对约束 reference 加 `Rδ`，形成下移 δ 的力锥；`mj_contactForce` 最终报告净值 `fn−δ`。在 gap 内只保留 normal 行，避免远距离切向制动。[被动吸力](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L875)、[参考偏置](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_constraint.c#L3431)、[gap 退化为 dim=1](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c#L1840)

## 7. 易错点和支持边界

- **几何离得近但没有力：** 查候选过滤、dist、margin/gap、exclude、DOF、装配地址、求解阶段；不要第一步就增大 friction。
- **视觉网格的洞被堵：** 查碰撞表示及凸包，不是接触 solver 不够迭代。
- **增加 μ 以修复穿透：** μ 改变摩擦锥，不能代替法向阻抗、参考或模型尺度检查。
- **刚好接触时切向力突变：** 检查接触建立/消失、tangent frame 变化、锥模型和正则化；保持 world-frame 与 identity 日志后才比较。
- **想用同一参数表覆盖 flex/IPC：** 不可以。flex 的 passive 接触可被标为 exclude=4，IPC 是另一个 discrete+CG 分支；本篇完成其区别，完整弹性、IPC 内循环与后端契约留到 E6。

## 8. 阅读练习与答案

**题 1：** contype1=1、conaffinity1=0、contype2=0、conaffinity2=1，位掩码关通过吗？

**答：** 通过，因为第一项 1&1 非零；但仍可能被 body、exclude 或几何距离过滤。

**题 2：** 同 priority 两 geom 的摩擦为 `(0.2,0.01,0.003)` 和 `(0.8,0.004,0.006)`，solmix 为 0 和 1，最终摩擦是多少？

**答：** 五数是 `(0.8,0.8,0.01,0.006,0.006)`，取逐项最大，不按 solmix。后一 geom 只在 solref/solimp 加权项取得全权重。

**题 3：** 第 3 节手算的 5 mm 接触与 2 mm 接触哪个可能施力？

**答：** 无 adhesion 时 2 mm 在 3 mm 阈值内；5 mm 位于 7 mm 检测带内但在施力阈值外。几何穿透不是必要条件。

**题 4：** condim=6 elliptic 的 τroll 能直接与 μslide fn 比较吗？

**答：** 不能，左右量纲不同；滚动项使用长度单位 μroll，且全部摩擦分量要满足同一个椭球预算。

**题 5：** 两侧 solref 为 `(-100,-2)` 和 `(-50,-8)`，priority 相同，组合是什么？

**答：** `(-100,-8)`，逐项最小，不能整套选第一侧或平均成 `(-75,-5)`。

**题 6：** 看到 `mj_contactForce(...)[0]<0` 就断言违反单边接触吗？

**答：** 先查 adhesion。净力扣除了被动吸力 δ，可拉到 translated cone 的范围内；普通无 adhesion 的正锥结论不能直接用到净力。

**题 7：** 为什么不存在“PGS 必然 pyramidal，Newton 必然 elliptic”的选择表？

**答：** solver 和 cone 独立；PGS 椭圆分支做 ray/normal 与小型 QCQP 更新，Newton/CG 可求两种锥。应分别记录两个 option。
