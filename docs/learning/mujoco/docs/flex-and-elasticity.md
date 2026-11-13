# Flex与弹性：从顶点归属到广义力与有效惯量

本课覆盖B6的原生可变形机制。先读[模型与坐标](modeling-and-frames.md)、[动力学执行链](dynamics-and-pipeline.md)和[求解/积分](solvers-and-integration.md)。固定3.15.0源码，所有模型仅文本审查，没有编译、求解或形变实验。

## 1. skin、flex、flexcomp、cable分别是什么

| 名称 | 原生含义 | 不能替代 |
|---|---|---|
| skin | 根据骨骼body更新视觉顶点/法线 | 不产生碰撞或弹性力 |
| flex | 由顶点归属、元素连接和材料参数描述的物理几何 | 不是一组只有视觉mesh的body |
| flexcomp | 生成body/joint/flex等低层结构的建模宏 | 不是运行时另一种solver |
| cable plugin | 在刚体链上施加弯曲/扭转被动力 | 不等于flex有限元 |

flex的元素可为1D线段、2D三角形、3D四面体，并带碰撞半径。顶点可以属于不同body，也可以全部属于同一个body形成刚性flex。元素本身不是独立新增广义坐标；它的运动由附着body或插值node决定。[建模说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/modeling.rst#L1340-L1399)、[skin边界](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4631-L4649)。

`flexcomp`编译为具体body质量/惯量和连接。默认full构造会给自由点生成平移自由度；pin点依附父body，不能把“pin”普遍解释成世界坐标恒定。若父body会动，点随它运动并将反力映射回去。[生成路径](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_flexcomp.cc#L479-L551)。

## 2. 坐标与力的映射保留在原生数据里

非插值顶点的世界位置来自所属body：

$$
x_i=p_{b(i)}+R_{b(i)}r_i,\qquad
v_i=J_i(q)v,\qquad
\tau_{\rm flex}=\sum_i J_i(q)^\mathsf{T}f_i.
$$

这里rᵢ是body局部顶点坐标，xᵢ单位m，Jᵢ把广义速度映射到m/s；广义力分量因滑动/转动坐标而具有N或N·m单位。把一个点pin到旋转body不仅传递力，也可产生力矩；直接把顶点力写进同编号qfrc列会丢失这一映射。

| 字段 | 所在对象 | 阅读意义 |
|---|---|---|
| `flex_dim`, `flex_vertnum`, `flex_elemnum` | model | 元素维数、顶点/元素数 |
| `flex_vertadr`, `flex_elemdataadr` | model | 拼接数组的起始地址，不是byte offset |
| `flex_vertbodyid`, `flex_vert` | model | 顶点归属和局部坐标 |
| `flexvert_xpos`, `flexedge_length/velocity` | data | 当前派生世界位置、边长/变化率 |
| `flexedge_J`, `flexvert_J` | data | 相应边/顶点约束的稀疏运动映射 |
| `flex_stiffnessadr`, `flex_stiffness`, `flex_bending` | model | 编译后的材料/弯曲数据，不能当简单每点弹簧数组 |

`mj_flex`计算世界位置、插值位置、边长及相关Jacobian；不是向每个顶点独立加上qpos。[位置/插值](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L553-L635)、[Jacobian装配](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L698-L742)。非插值弹性力通过gather/scatter处理一般body附着，保持虚功关系；有效metric中的映射也沿同样关系处理。[弹性力与scatter](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L522-L620)、[metric映射](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L1624-L1655)。

## 3. 三种保形机制不能混称同一种刚度

**边弹簧/阻尼**使用边长度L和参考长度L₀，力沿边方向，标量为：

$$
f_e=k_e(L_{e0}-L_e)-c_e\dot L_e.
$$

k单位N/m，c单位N·s/m，然后由边Jacobian转为广义力。当前编译器仅允许1D的edge stiffness；不能用二维布料的每条边独立弹簧替代其完整连续体材料语义。[运行力](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L732-L766)、[编译限制](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L4577-L4606)。

**边/应变等式约束**用constraint rows限制形变，依赖solref/solimp和solver，不是“young趋于无穷大”的同一算法。`flexcomp/edge equality`有false/true/vert/strain，插值布局有自己的兼容约束。当前编译器拒绝边等式与拉伸young同时存在；纯bending例外可与边约束组合。还拒绝等式与edge stiffness同时存在。旧XML说明中“任意叠加”或必须用旧Solid/Membrane插件的措辞不能覆盖这些检查。[等式兼容性](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L6233-L6252)、[XML equality类型](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4032-L4045)。

**连续体弹性**从形变梯度和材料能量得到力。young单位Pa=N/m²，poisson无量纲；当前实现范围要求0≤ν<0.5。大位移/有限转动不等于允许任意大应变、倒置或任意材料本构。

以StVK材料为例，设参考到当前的梯度F无量纲，Green应变Eₛ和能量密度W为：

$$
E_s=\tfrac12(F^\mathsf{T}F-I),\qquad
W=\mu\operatorname{tr}(E_s^2)+\tfrac{\lambda}{2}\operatorname{tr}(E_s)^2,
$$

$$
\mu=\frac{Y}{2(1+\nu)},\qquad
\lambda=\frac{Y\nu}{(1+\nu)(1-2\nu)}.
$$

Y、λ、μ单位Pa，乘参考体积得到J。ν接近0.5会使λ变大，改变数值条件；不能通过更大的Young常数直接宣称“更接近真实”。编译器将材料整理为边长度平方差上的局部系数，运行时逐元素计算张力和力，再scatter。[材料编译](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L3440-L3520)、[运行分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L540-L581)。

## 4. 2D壳：碰撞半径与材料厚度是两个量

`elastic2d`的none/bend/stretch/both决定哪些被动力生效。thickness控制材料能量缩放，radius控制几何接触厚度。两者可以为同一物理厚度建模，但不是引擎自动绑定的字段。拉伸刚度随厚度一阶缩放，板弯曲刚度含三次厚度：

$$
D_{\rm bend}=\frac{Yt^3}{12(1-\nu^2)}.
$$

这个关系假设对应各向同性薄板模型，单位为N·m。把t加倍，弯曲项并非只加倍；模型拟合不能把碰撞radius当作唯一厚度旋钮。[弯曲系数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L4328-L4342)、[参数语义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4518-L4555)。

Rayleigh damping参数单位秒，用于把刚度映射到阻尼；它不是edge damping的N·s/m系数。StVK路径按一步边长度变化构造广义阻尼；SNH路径用PSD切线保证该阻尼的瞬时功非正。因此同名“damping”跨不同层不能直接比较数值。[阻尼实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L587-L620)。

## 5. 3D SNH是本版mjSpec能力，不是已公开的XML同名属性

`mjsFlex.elastic3d`明确标注“experimental、mjSpec only”：0为StVK，1为Stable Neo-Hookean。当前XML schema/read table没有同名属性；不要向`<elasticity>`里臆造`elastic3d="1"`并宣称受支持。[公开spec字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjspec.h#L496-L508)、[XML读取表](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/xml/generated/mjcf_read_table.inc#L442-L449)。

编译检查要求SNH为非插值3D flex，使用discrete积分器。其24系数tetra块保留StVK边基底，再加入三次项和有符号体积项；运行通过额外系数选择SNH，而不是仅换一组Young/Poisson数值。[检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L4597-L4606)、[SNH编译系数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L3488-L3520)、[运行体积/张力项](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L540-L583)。

求解metric使用PSD投影的材料Hessian；这里的稳定化切线与“原始能量Hessian处处正定”不是同一个声明。材料支持也不证明所有初始倒置、刚体附着或步长都得到物理可信结果，当前没有相应实验。

## 6. 插值减少自由度，也改变模型与兼容性

trilinear和quadratic让物理节点插值出几何顶点；节点数、碰撞顶点数和广义自由度数因此不同。相同表面网格不保证与full布局有相同可表达形变。`flex_interp`当前用正值表示体积插值、负值表示壳插值，绝对值表达order；不是单纯bool。

固定源码已经存在插值壳的弯曲系数编译及`mj_flexPassiveBendInterp`运行分支，因此旧XML页“trilinear/quadratic不支持bending”不能作为本树的完整结论。需要满足壳模式、bending数据、正厚度/Young等具体条件。[插值壳编译](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L5096-L5110)、[运行条件](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L223-L251)。另一方面，当前编译器拒绝插值flex的self-collision；不会因为渲染连续就自动获得同样自碰撞能力。[检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L4580-L4586)。

## 7. 从被动力到求解metric，而非换个积分器名称

discrete路径把弹性/阻尼切线放入E3的有效metric。概念上局部正定近似可写成：

$$
\widehat M\approx M+hC+h^2K.
$$

这里是说明各项量纲与耦合的局部形式，实际还有投影、映射和不同算子类别；不是要求显式构造一个统一稠密矩阵。对一般附着flex，CG可通过gather→局部Hessian乘→scatter应用算子；Newton需要可装配结构。原生检查因此拒绝部分Newton布局，而不是所有solver互换。[metric实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_derivative.c#L1624-L1655)、[运行组合检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1741-L1800)。

本版的重要限制：SNH与passive flex contact需要discrete；有弹性metric项的flex不再通过implicit/implicitfast旧路径隐式积分，代码要求改用discrete。Euler/RK4的显式弹性路径仍有对应条件，但不能当成隐式稳定性保证。discrete+flex metric不支持PGS/NoSlip或sleep；一般附着优先检查CG，mocap附着没有弹性阻尼所需的真实广义速度。[同一检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1715-L1800)、[附着约束说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4551-L4556)。

## 8. 碰撞接触还有独立选择

默认flex接触沿原生constraint rows，与材料被动力分开。接触点可能涉及多个顶点，其力通过几何权重和body Jacobian映射，不能像刚体geom只认两个body。selfcollide控制候选剪枝；3D activelayers控制参与碰撞的tetra层数，均不直接改变Young模量。[flex几何碰撞](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_flex.c#L1-L90)、[属性](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4565-L4590)。

`contact passive=true`把适用的flex–flex/静态几何接触改为只有法向的被动penalty，刚度来自质量与固定自然频率，metric隐式处理其曲率；移动body接触保留constraint路径。它不提供CCD的防穿越保证。IPC则另有AL+CCD外循环，见[下一课](ipc-contact-mode.md)；不要将两者称为相同的“软接触选项”。[passive契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L4605-L4626)。

[原创flex片段](../examples/extensions-boundaries/README.md)只读编译布局的预期接口，没有编译或推进。它帮助核对pin、地址和材料参数，不提供弯曲刚度、稳定性或碰撞证据。

## 9. 带答案阅读练习

1. **给skin设很细的mesh会增加物理柔性吗？** 不会；skin仅视觉，flex/body/joint和材料决定物理。
2. **pin点一定固定在世界中吗？** 不一定；它依附指定body，body运动时点随动并可传反力/力矩。
3. **thickness翻倍、radius不变会怎样？** 材料拉伸/弯曲缩放改变，碰撞几何厚度不自动改变；薄板弯曲系数含t³。
4. **边等式+stretch Young是否任意可叠加？** 本版编译器拒绝冲突，纯bending与边等式可有不同规则；不能照旧说明推断。
5. **SNH是否写一个XML属性就能用？** 本版elastic3d是mjSpec-only，且要求非插值3D和discrete。
6. **减少插值节点只影响速度吗？** 还改变可表示形变、Jacobian和兼容性；不等价于原full模型。
7. **所有implicit积分器都隐式处理本版flex弹性吗？** 不；源码要求相应metric路径使用discrete，需读具体组合检查。
8. **passive接触没有摩擦，调大friction能留住斜面上的布吗？** 对该法向路径无效；需选择有摩擦的接触路径，不能用参数名推断其生效。
