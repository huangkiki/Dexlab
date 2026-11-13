# 多物理与综合源码追踪：先确定力、状态与执行路径

本课完成B7的机制追踪，并补足B6多物理边界。先读[扩展生命周期](extensions-and-callbacks.md)、[flex](flex-and-elasticity.md)、[IPC](ipc-contact-mode.md)和[后端/导数](backends-and-differentiation.md)。使用同一固定3.15.0树；没有运行任何模型或外部耦合系统。本课的“支持”指源码存在及其已读条件，不代表精度、性能或工程工况验收。

## 1. 什么进入了同一个动力学方程

E3将广义力按来源分开。在这里，多物理首先意味着其他物理过程给机械系统贡献力或演化状态；不是打开一个笼统的“multiphysics”选项。

$$
M(q)\dot v+c(q,v)=\tau_{\rm act}+\tau_{\rm spring}
+\tau_{\rm damper}+\tau_{\rm fluid}+\tau_{\rm user}+J^\mathsf{T}f.
$$

这是力来源的概念分解：具体重力补偿、弹性metric和constraint分配以实现为准，不能把已计入passive的某一项再次加进总力。滑动坐标对应N，旋转坐标对应N·m；在世界系施加的三维力要通过Jacobian/`mj_applyFT`转换，不能直接写进任意qfrc列。[被动力分账与回调](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L941-L1040)。

| 过程 | 当前原生路径 | 仍需独立定义/验证的内容 |
|---|---|---|
| 刚体弹簧/阻尼、重力补偿 | model参数→passive/actuation | 能量含义、参数来源、补偿是否当作控制 |
| 连续体弹性 | flex材料→力/切线metric | 材料辨识、离散分辨率、倒置/稳定性边界 |
| 流体对刚体的近似力 | inertia-box或geom ellipsoid→qfrc_fluid | 不是流场PDE、自由表面或流固耦合验收 |
| 刚体链的弯曲/扭转 | cable passive plugin | 独立插件实现与构建/生命周期 |
| 热、电、化学或外部CFD | 应用/插件可提供状态与力 | 本课没有发现并验收一个通用原生多场求解器 |
| 学习控制与可微优化 | 外部任务/学习系统或特定后端 | 策略梯度、物理导数、传输/同步分别定义 |

这里最后两行是扩展设计边界，不是宣布MuJoCo不能用于这些系统；可表达的接口与已实现的物理模型是两件需要分别举证的事。

## 2. 原生fluid是无流场状态的近似力模型

`option.density`和`viscosity`控制流体密度ρ与动力黏度η；`wind`是世界系速度m/s。被动力入口只在ρ和η**都为零**时早退；因此可以单独使用黏性阻尼。质量太小的body被跳过。每body若有geom启用ellipsoid，就走该body的geom模型，否则走惯性盒模型，避免把两者默认叠加。[选择代码](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L812-L846)。

这里没有网格上的流体速度/压力状态，也没有求解Navier–Stokes方程；它把机械速度映射成近似外力。设置水的density不会由这条路径自动产生自由液面、浸没比例或排水体积静水浮力。风本身也是指定外部输入，没有被物体反作用更新为一个流场。[模型定位](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/fluid.rst#L1-L22)、[完整惯性盒力路径](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1047-L1103)。

惯性盒形状来自body主惯量与质量，而不是视觉mesh轮廓。对物理可行的对角主惯量、正质量m，半长为：

$$
r_i=\sqrt{\frac{3(I_j+I_k-I_i)}{2m}},\qquad
r_{\rm eq}=\frac{r_x+r_y+r_z}{3}.
$$

代码存放的是完整边长2r，并用最小值保护开方。把源码box误当半长会产生面积/力矩的倍率错误；修改惯量也会改变这种流体几何近似，即使视觉外观不变。[文档半长](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/fluid.rst#L26-L45)、[代码全长](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1047-L1057)。

## 3. 在正确frame里核对力和量纲

取惯性主轴局部系，线速度v是body质心相对wind的速度，角速度ω单位rad/s。惯性盒的两类平移力为：

$$
f_{D,i}=-2\rho r_jr_k|v_i|v_i,\qquad
f_{V,i}=-6\pi\eta r_{\rm eq}v_i.
$$

对应黏性力矩为：

$$
\tau_{V,i}=-8\pi\eta r_{\rm eq}^{3}\omega_i.
$$

ρ单位kg/m³，η单位Pa·s=kg/(m·s)，所以两个f都是N，τ是N·m。密度控制二次速度阻力、黏度控制一次速度阻尼，它们不能当作同一“阻力系数”互换。阻力相对于流体速度做耗散；有风时物体机械能可以上升，因为指定风是外部能量源。[公式](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/fluid.rst#L47-L83)。

实现用`mj_objectVelocity(...mjOBJ_BODY,...,1)`取得**质心、惯性轴**局部六维速度，减去转入局部系的wind线速度，再将力/力矩旋回世界系，通过`mj_applyFT`在质心累加`qfrc_fluid`。不能把BODY解读成E1的XBODY体原点，也不能忘记空间量的rot:lin次序。[转换与施力](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1059-L1103)。

这些公式是惯性盒近似，不是把真实不规则物体的流场积分“简写”出来的恒等式。只拟合一种速度/姿态后，不能假定所有Reynolds区间和来流方向均可信。

## 4. ellipsoid路径更细，但仍需要逐项读执行

`geom fluidshape="ellipsoid"`选择几何半轴模型。五个`fluidcoef`依次调blunt drag、slender drag、angular drag、Kutta lift、Magnus lift，默认0.5/0.25/1.5/1/1；它们不是五个接触摩擦系数。计算使用geom局部系速度，并在geom位置施加世界力/力矩，所以偏离质心的geom会影响广义力矩。[参数表](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/fluid.rst#L90-L152)、[实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1108-L1164)。

“added mass”这个名字尤其容易过读。当前正常调用把`local_accels`传NULL，保留速度耦合项；函数里直接乘加速度的附加质量项由于qacc依赖而未在这条路径启用。因此不能仅根据该函数名宣称它已经把完整流体附加惯量并入M并隐式求解。[调用](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1144-L1153)、[条件分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L1170-L1205)。

流体力依赖速度，其解析局部导数服务于相应隐式积分；这与“整个模拟可反向求导”不同。对刚体fluid，文档建议implicit/implicitfast；如果同时含E6的flex弹性，应先服从当前flex对discrete等组合检查，不能把一个独立模块的建议当作所有组合都接受。[流体积分说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/computation/fluid.rst#L17-L22)、[flex组合检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1715-L1800)。

也不要把flexcomp生成点body的惯性盒阻力直接解释成连续薄布气动力。该近似用body质量/惯量，各点的建模惯量未必代表布面投影面积；真实流固耦合、遮挡或压差模型仍需独立建模与证据。

## 5. 怎样放入自己的物理记忆

假设应用希望给电机增加一个集中热模型，设计方程可以是：

$$
C_{\rm th}\dot T=I^2R-h_cA(T-T_a).
$$

Cth单位J/K，I单位A，R单位Ω，hcA单位W/K，两侧单位W。这里是**说明接口选择的自建模型**，不是MuJoCo自带热模拟功能。机械力矩与电流的关系、温度影响的限流/电阻以及环境换热都要由应用给出，ctrl不能未经转换当作电流。

若做原生插件，T是物理记忆，应进入可恢复的plugin_state或合适的act状态；plugin_data适合可重建缓存。compute只按当前状态评估所需力/读数，状态演化要绑定advance/act_dot的真实时序。若外部系统持有T，则checkpoint必须同时记录该系统，不能仅存qpos/qvel。[插件状态契约](extensions-and-callbacks.md)、[恢复边界](recording-and-replay.md)。

一个按步advance的外部积分器与RK4中间阶段不是自动高阶耦合。若希望温度/电流与机械系统联合隐式求解，还要提供耦合方程、导数及solver入口；当前四种plugin capability不等于任意替换多场Newton系统。先定义离散耦合算法，再解释误差，不能只把同步频率调高就声称守恒或稳定。

## 6. 从一张flex片段追到机械输出

[原创片段](../examples/extensions-boundaries/README.md)是一张父body为world的full二维小网格，pin两个顶点，使用stretch+bend材料与discrete/CG。没有风、学习任务或IPC。本轮只解析文本；下表是**若以后调用原生API时应核对的执行链**，不是已观测结果。

| 阶段 | 模型/运行字段与入口 | 从源码应回答的问题 |
|---|---|---|
| 编译建模 | flexcomp→body/joint/flex；`flex_vertbodyid` | 哪些点依附world？自由点如何产生自由度与质量？ |
| 材料编译 | young/poisson/thickness→stiffness/bending数据 | 参数是Pa、m、s中的哪个量？哪些组合会拒绝？ |
| 位置更新 | `mj_forward`→`mj_flex`→`flexvert_xpos` | body局部顶点如何映射世界位置？ |
| 被动力 | flex stretch/bend→`qfrc_spring`/阻尼项 | 元素力怎样gather/scatter到广义坐标？ |
| 离散动力学 | effective metric + CG | 哪些切线被隐式处理，哪些模型组合不支持Newton？ |
| 接触 | 原生constraint rows | 本例未启用IPC；摩擦/过滤遵循哪个路径？ |
| 观测 | 读取字段/传感器前确认阶段 | 当前读取的是forward派生位置还是积分后待刷新值？ |
| 保存 | 模型身份+数值状态+应用状态 | 相同数组shape是否足以确定材料、拓扑与完整恢复？ |

编译链见[flexcomp生成](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_flexcomp.cc#L479-L551)与[材料构造](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_mesh.cc#L4851-L4890)；执行链见[flex位置](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L553-L635)、[被动力分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_passive.c#L708-L730)和[离散兼容性](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1715-L1800)。这些入口能把模型字段和运行意义接起来，不能拿一处“有这个字段”替代全部执行证据。

把同一场景切换到IPC是新数值问题：先检查维数、附着运动、CG/discrete限制及摩擦缺失；再看CCD部分推进日志与状态恢复。切换到设备后端也是新执行程序：MJX JAX拒绝flex，本树Warp有部分flex但没有CPU discrete/IPC对应分派。不要把这两个变更藏在一个“backend参数”后直接比较结果。[IPC限制](ipc-contact-mode.md)、[后端矩阵](backends-and-differentiation.md)。

## 7. 读能力声明时形成完整证据链

读到“支持某能力”后，依次定位：声明/解析、编译检查、实际计算分派、输出字段及frame/时点、reset/copy/state恢复、后端入口。任何一环仍缺证据，就把它写成具体未核项。例如SNH有mjSpec字段与CPU分支，但XML没有同名属性；IPC有CCD分支，却不能用d.warning为零证明完整推进；Warp存在history代码，但MJX包装层make_data的初始化另有差异。

这些判断都基于固定3.15.0树；版本升级时应重新走调用链。源码说明模型意图，静态检查说明文档与片段结构，只有将来具备明确工况、日志与指标的运行才说明该工况表现。实验将复用[DexLab](https://github.com/huangkiki/Dexlab)，不会在Atlas另建评分器或混合不同任务排名。

## 8. 带答案阅读练习

1. **density=0、viscosity>0是否必然没有流体力？** 不是；入口仅在两者都零时早退，可存在黏性项。
2. **惯性盒阻力完全由可视mesh形状决定吗？** 不是；形状来自质量与主惯量，代码box是全长。
3. **rho v²乘什么才成为力？** 还要面积；惯性盒为2rj rk，ρ的kg/m³乘m²和m²/s²得到N。
4. **打开ellipsoid会再加一遍同body惯性盒力吗？** 不会，当前body分派选择geom模型并关闭该body惯性盒路径。
5. **addedMassForces函数存在就说明完整附加惯量加入M了吗？** 不说明；正常调用local_accels=NULL，直接加速度项未启用。
6. **把T藏在plugin_data里、只保存qpos/qvel够恢复热耦合吗？** 不够；T是物理记忆，应可序列化并与应用输入共同恢复。
7. **flex点body的fluid阻力能直接当布面空气动力学验收吗？** 不能，惯量近似与布面气动模型不同，需独立定义和验证。
8. **一份XML转到MJX后编译成功就等于CPU能力全保留吗？** 不能；需逐段核对后端拒绝条件、执行链、输出与恢复语义。

E6至此交付扩展机制与源码综合追踪。A0的完整安装/构建课程、全路线审校及DexLab证据入口整理仍留E7；没有把源码教学交付写成全路线或实验验收完成。
