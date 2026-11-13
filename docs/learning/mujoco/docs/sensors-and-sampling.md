# 传感器与采样：一个 sensordata 不等于一个时刻

本课属于 A6，固定在 MuJoCo **3.15.0 / `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`**。先修：[状态与时间](state-and-time.md)的数组所有权与采样阶段、[力观测](force-observations.md)的作用侧和参考点。学习目标是从 MJCF 定义追到编译后的输出块、计算阶段和历史读取，判断一项观测究竟表示什么。

本课是源码课程。示例与公式没有经过传感器、动力学或设备运行验收；这里也没有噪声标定或硬件精度结论。

## 1. 四条数据路径先分开

| 路径 | 输入 → 输出 | 谁触发更新 |
|---|---|---|
| 原生 sensor | 模型中的 sensor 定义 + 物理中间量 → `d.sensordata` | forward/step 内的 POS、VEL、ACC 阶段，受 history/disable/sleep 影响 |
| 几何查询 | 当前几何 pose + 查询参数 → 距离、交点、法向等 | 调用 `mj_ray`、`mj_geomDistance` 等；也被部分 sensor 使用 |
| 图像渲染 | 模型/数据 → `mjvScene` → renderer → 像素数组 | 显式 scene update 和 render；不是 `sensordata` 的自动组成部分 |
| 交互显示 | 场景、UI、相机、扰动 → 窗口 | viewer 线程及同步；GUI 还可能反向修改控制和选项 |

原生传感器不是物理闭环的隐含控制器；它提供读数，用户才决定是否用读数更新 `ctrl`。`camera output="rgb depth"` 也不自动在 `sensordata` 分配两幅图，见[相机与查询](cameras-and-geometry-queries.md)。共同拥有“观测”名字不代表共同更新契约。[数据定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L814-L832)与[原生分阶段执行](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1504-L1666)是区分依据。

## 2. 输出块、元数据和视图所有权

设传感器 id 为 i，`a=sensor_adr[i]`，`k=sensor_dim[i]`。这一传感器的输出是 `sensordata[a:a+k]`，全数组长度为 `nsensordata`，不是 `nsensor`。`sensor_objtype/objid` 指向被测对象，`sensor_reftype/refid` 指向可选参考对象，`refid=-1` 常表示世界参考；具体 sensor 如何解释它们仍要查实现。

`sensor_datatype` 是 REAL/POSITIVE/AXIS/QUATERNION 等**语义分类**，不是 NumPy dtype；传感器底层使用该构建的 `mjtNum`，颜色图像和分割标签另有 dtype。AXIS/QUATERNION 也不表示把一个随意的用户数组自动校正为单位向量。维度由编译器决定，不能用“一个 sensor 一个数”索引。

完整原生读取片段如下；仅检查 Python 语法。它接收调用者已更新到明确阶段的 model/data，既不刷新状态也不推进时间：

```python
import mujoco


def read_sensor_block(model, data, name):
    sensor_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR, name)
    if sensor_id < 0:
        raise KeyError(name)
    start = int(model.sensor_adr[sensor_id])
    width = int(model.sensor_dim[sensor_id])
    return data.sensordata[start:start + width].copy()
```

`.copy()` 只固定这一数组的值；它没有自动保存物理采样时间、history 的源时间、frame 或模型版本。命名访问 `data.sensor(name).data` 同样是原生内存视图，需要保存时也要复制。字段与编译依据：[输出地址](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L815-L830)、[sensor 维度](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_api.cc#L1838-L1920)、[actuator 输出维度覆盖](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L8121-L8138)。本版 actuatorpos/vel/frc 可有多个输出，不能按旧枚举注释把它们一概当 scalar。

## 3. 把单位、对象和计算阶段放在一起

下表假设模型采用 m–kg–s，角度用 rad；MuJoCo 不替用户校验单位一致性。POS/VEL/ACC 是**所需计算阶段**，不是一个传感器所属的机器学习模态。实际 `sensor_needstage` 由[编译表](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L7691-L7752)确定。

| 传感器族 | 原生输出与单位 | frame / 语义及阶段 |
|---|---|---|
| jointpos / jointvel | 1：hinge rad / rad·s⁻¹；slide m / m·s⁻¹ | 只接受 hinge/slide；POS / VEL；free/ball 不用单个标量替代 |
| ballquat / ballangvel | 4 个 wxyz / 3 个 rad·s⁻¹ | ballquat 为该关节四元数；ballangvel 直接取相应 qvel；POS / VEL |
| tendonpos/vel、actuatorpos/vel/frc | tendon 标量；actuator 按输出数 | 长度、速度、驱动力的量纲由传动/gear 决定；POS/VEL/ACC，见 E2 |
| velocimeter / gyro | 3：m·s⁻¹ / rad·s⁻¹ | SITE 原点、SITE 轴；VEL；不能拿它与 body CoM 速度直接比较 |
| accelerometer | 3：m·s⁻² | SITE 原点、SITE 轴；ACC；重力补偿式 specific force，见下式 |
| magnetometer | 3：与 `opt.magnetic` 相同单位 | `R_siteᵀ magnetic`；POS；没有场梯度、硬铁软铁或噪声模型 |
| framepos/quat/xaxis/yaxis/zaxis | 3 m / 4 wxyz / 3 无量纲 | 对象相对参考对象；POS；BODY 与 XBODY 不是同一点/轴 |
| framelinvel / frameangvel | 3：m·s⁻¹ / rad·s⁻¹ | 有 ref 时含参考系运动；VEL，见下式 |
| framelinacc / frameangacc | 3：m·s⁻² / rad·s⁻² | 本实现从对象世界空间加速度复制分量；ACC，不套用相对速度公式 |
| subtreecom / subtreelinvel / subtreeangmom | 3：m / m·s⁻¹ / kg·m²·s⁻¹ | 世界轴；角动量关于子树 CoM；POS / VEL / VEL |
| force / torque / touch | 3 N / 3 N·m / 1 N | SITE 力/力矩或区域正法向合计；ACC；不是压力图 |
| rangefinder / camprojection / collision | 按配置 / 2 pixel / 按类型 | POS，见下一课；几何存在不等于接触施力 |
| contact / tactile | 固定槽 / 3N taxel 数组 | ACC；两者结构及单位完全不同，见下一节 |
| e_potential / e_kinetic / clock | 1：J / J / s | 本版三者均注册 POS；能量调用相应计算函数，clock 是模拟时间，不是墙钟 |

速度与姿态实现见 [POS](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L521-L737)、[VEL](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L867-L981)、[ACC](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1275-L1361)；关节限制见[编译器](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_objects.cc#L7850-L7862)。不要只凭“ACC”给任何数组赋予 m/s²，force 也在 ACC 阶段。

### IMU 和移动参考系的公式

设 R 将 SITE 局部向量转到世界，a 为 SITE 原点的物理线加速度，g 为世界重力。在常规连续动力学读数语义下，理想 accelerometer 对应 `Rᵀ(a−g)`。水平静止支撑且 g=(0,0,−9.81) 时其竖直分量为 +9.81；自由落体时可为 0。这是符号推导，不是本课实测。旋转刚体上偏离 CoM 的 site 还包含切向/向心加速度，不能只旋转 `qacc` 的三个元素。本版 [RNE](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L2362-L2385)将根空间加速度初始化为 −g，再由 [mj_objectAcceleration](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_util.c#L909-L973)修正到对象点，[accelerometer 分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1275-L1283)读取其线分量；离散积分器对加速度的额外约定见 E3。

设 A 为对象、B 为移动参考对象，r=p_A−p_B，R_B 为 B→世界，则：

$$
{}^B v_{A/B}=R_B^T(v_A-v_B-\omega_B\times r),\qquad
{}^B\omega_{A/B}=R_B^T(\omega_A-\omega_B).
$$

所有减法和叉积先在同一世界轴中计算。只做 `R_Bᵀ(v_A−v_B)` 会漏掉旋转参考系项。[frame velocity 源码](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L937-L966)明确做了它。framepos 则是 `R_Bᵀr`；framequat 对应 `q_B⁻¹⊗q_A`。BODY 使用 xipos/ximat（CoM 与惯性主轴），XBODY 使用 xpos/xmat（体坐标），见[对象分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L226-L278)。XML 里的 `objtype="body"` 和 `"xbody"` 必须有意识地选。

## 4. 三种接触观测，三种问题

`force/torque` 衡量指定 site 所在子体与父体的内部作用，换到 site 点/site 轴；`touch` 累加匹配区域内正的法向接触力。它们不会产生 RGB，也不等于 `sum(qfrc_constraint)`；作用侧和力矩换点公式沿用[力观测](force-observations.md)。`cacc/cfrc_int` 在需要时才由 RNE post-constraint 准备，不能从 XML 页的概括句推断任何 mj_step 后都新鲜。

### contact：把可变 d.contact 压入固定长度

使用者选择匹配对象（geom/body/subtree 或 site 区域）、`num` 槽数、`data` 字段和 `reduce`。字段必须按 `found force torque dist pos normal tangent` 的规范顺序选取。每槽宽度是所选字段宽度之和，整体可 reshape 为 `(num, slot_width)`；力/力矩在接触轴，pos/normal/tangent 在世界轴。`found` 的正数是**匹配总数**，不是稳定 contact ID：例如 num=3、匹配6条时三个槽都是6，普通逐条reduce的未填槽全零。

| reduce | 选择/合并 | 易漏信息 |
|---|---|---|
| none | 当前 d.contact 中最先匹配的 num 条 | 槽序不是跨步物体身份，几何拓扑或上游版本变化可重排 |
| mindist | 按 signed dist 从小到大选 | 更负表示更深穿透，不能把它说成最小“穿透量绝对值” |
| maxforce | 按三维力范数从大到小选 | 不按力矩排序；截断后不保留被丢弃接触的力 |
| netforce | 所有匹配合成一槽 | 输出 wrench 改为世界轴，位置是力范数加权中心；normal/tangent 为固定基轴，无真实表面法向含义 |

合力矩关于合成位置 p 是 `Σ[τ_j+(p_j−p)×f_j]`；每个接触先变到世界轴并统一作用侧。`geom1/body1/subtree1`→第二侧规定法向；反向匹配时代码同时改坐标轴和 wrench 分量，不能再把所有分量额外取负。`cutoff` 对 contact 忽略。netforce在零匹配时也会写固定normal/tangent轴，因此空结果以found==0判断，不能仅以法向非零判定。[匹配/换轴](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L318-L461)、[固定槽与 reduce](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1059-L1181)、[XML 契约](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/XMLreference.rst#L8887-L9036)。

特别注意源码边界：匹配循环枚举 `d.ncon`，没有要求 `efc_address>=0` 或正接触力；因此被 margin/gap 收集但不施力的记录也可能 `found>0`、force=0。被碰撞过滤而根本没进 d.contact 的配对当然不会出现。XML 页“忽略不产生力的接触”的措辞不能替代这个判定。若任务需要承载判断，要单独定义力条件。

### tactile：taxel 上的穿透和切向速度量，不是相机/力计

本版绑定一个 geom 和一个采样 mesh，mesh 顶点作为 geom 局部采样点。编译维度固定 `3*N`，N 是采样 mesh 顶点数；存储是 **channel-major**：先 N 个穿透量，再 N 个 tangent1 速度量，再 N 个 tangent2 速度量，应 reshape `(3,N)`，不能当 `(N,3)`。

对已接触的候选 geom，采样点转到对方局部坐标，计算其 signed distance φ。第0通道取候选间最大的 `max(−φ,0)`，单位 m；没有穿入则0。若采样 mesh 确实有每点三个法向/切向向量，另两通道分别**累加**相对速度在切向投影的绝对值，单位 m/s。不是带符号滑动向量，也不是取“最大穿透对象”的同一组速度。没有完整 tangent frame 时速度通道保持0。

源码距离分派支持 plane/sphere/box/capsule/ellipsoid/cylinder、SDF 插件以及带 octree 的 mesh；没有 octree 的 mesh 会跳过。这里也不是任意 geom 通用支持：例如 hfield 不在该[距离函数分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_sdf.c#L225-L302)里，会走不支持的错误分支。距离近似还取决于形状函数/插件或 octree，不能一概称精确欧氏距离。候选来自与传感器父 weld body 有关的现有 contact 集合，并非对所有空间物体无条件求距离。因此既依赖碰撞收集，又不同于 contactForce。官方 XML 页仍写“仅 SDF、每顶点需3 normal”；本课按[实际距离与通道计算](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L82-L184)、[候选收集](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1184-L1272)、[固定3N维度](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/user/user_api.cc#L1897-L1899)讲解，保留该版本差异；不据此声称任何网格/插件组合已运行通过。

## 5. 计算时点、interval 和 delay

对普通未禁用、未睡眠、无 history 的 sensor，forward 顺序是位置计算→POS sensor→速度计算→VEL sensor→驱动/加速度/约束→ACC sensor。`mj_step` 随后积分；返回的 qpos/qvel/time 与留下的读数不一定是同一状态。`mj_step1` 只准备前半段，不会把 gyro 以外的全部传感器都刷新。直接改 qpos 再读取旧 sensordata 也不会自动计算。详见[E3 时序](dynamics-and-pipeline.md)。

history 在 `mjData.history` 内，属于 E1 的 physics snapshot 范围。`nsample>0` 分配 ring buffer；`interval="period phase"` 的两项单位都是 s，默认 `0 0`；`delay` 单位 s；`interp` 为 zoh/linear/cubic。下表是**走内置 compute_or_read_sensor 分支的 sensor**，不能直接套到 callback/plugin。

| period | delay | 对外 sensordata | 积分推进时的 history 写入 |
|---|---|---|---|
| 0 | 0 | 本次计算结果 | 存本次输出；可供事后历史读取 |
| >0 | 0 | 到期才新算，否则读历史 | 到期才插入；period 控制连续 tick |
| 0 | >0 | 读 `time−delay` | 另算当前值，写入当前 timestamp |
| >0 | >0 | 读 `time−delay` | 到期才另算当前值并插入 |

关键路径是 [compute_or_read_sensor](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1392-L1433)→[mj_readSensor](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L965-L987)→[advanceStart](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c#L1335-L1390)。只重复 `mj_forward` 不会像积分推进那样持续写 history；render 更不写。period=2.5h、phase=0 时，在整数步时刻按 0、3h、5h、8h…计算，不是统一舍入到3h；phase=0 初始化时特判为−period。正 period 的显式非零 phase 应在 `(−period,0]` 中。

读先于写，所以正 delay 小于一步也不提供“未来的当前样本”，最小有效正延迟是一拍。reset 初始化历史值为0、时间为负；需要特定初态时有 `mj_initSensorHistory`。若查询早于最老样本，底层读取**钳到最老值**，不报错：这可能把未来于查询时刻的值用作过去的观测。不是无限长回放，也不是环形下标让内容任意绕回。[初始化与 API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_support.c#L1022-L1047)、[边界与插值](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_util_misc.c#L1478-L1558)、[delay 说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/modeling.rst#L1136-L1230)。

无 period 的固定步长采样可按最大延迟选足 `nsample`；有 period 时还要核对实际 sample timestamp 和相位，不能把 nsample 当物理步数。四元数、单位轴、contact found 等数据不宜直接套分量 cubic 插值；插值没有自动解决流形约束或离散身份。导出观测时应分别记“物理状态时刻、计算/历史样本时刻、读出时刻”，延迟读数尤其不能仅贴当前 `data.time`。

## 6. 默认值、失效与扩展

`noise=0` 默认；即使设正值，也只存噪声标准差元数据，核心不因此加入随机噪声。一般 `cutoff>0` 是 REAL 对称限幅或 POSITIVE 上限，不是低通滤波频率；碰撞距离类将它作为查询范围，contact 忽略，axis/quaternion 有编译限制。依据：[公共参数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/modeling.rst#L1062-L1134)、[实际 apply_cutoff](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L196-L221)。

`mjDSBL_SENSOR` 让阶段函数直接 return；sleep 可跳过某些传感器，跳过不意味着写NaN、清零或自动贴过期标签。调用者必须保存更新策略。RNE/subtreeVel 是部分传感器的额外工作依赖，不应为了“只读数组”假设其成本或线程可重入性。

用户 sensor 由 `mjcb_sensor(model,data,stage)` 填对应输出段；同阶段统一回调，未安装回调的段被清零。plugin 由注册的 capability/needstage 分派并调用 plugin compute，维度来自插件契约。这两类在[阶段循环](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1504-L1552)中绕开内置 history 读分支；正 delay 的推进还会进入内置 `mj_computeSensor`。因此不要把内置 delay/interval 行为承诺给 USER/PLUGIN；自定义传感器应明确其采样/历史支持，再在 E6 讨论插件生命周期。全局 callback 的并行隔离也不是每个 MjData 自动保证的。[回调/插件分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_sensor.c#L1437-L1500)。

## 7. 带答案阅读练习

1. **一个 camera rangefinder 选择 dist/point/depth，分辨率 W×H；另有一个 gyro。总共多少输出？**

答：前者每像素1+3+1=5，共5WH；gyro3，总计5WH+3。仍从 sensor_adr/dim 切片，不靠相邻 sensor id 推宽度。

2. **支撑静止的水平 IMU 与自由落体 IMU 都有 qvel=0 的初始瞬间，accelerometer 必须相同吗？**

答：不必须。读数依赖完成约束求解后的加速度；常规理想语义是 a−g。支撑与自由落体的 a 不同，这不是从初始 qvel 单独决定的。

3. **参考相机绕自身旋转，对象世界速度为0；framelinvel 只旋转0就够吗？**

答：不够。有 `−ω_ref×r` 项，静止世界点在旋转坐标系中的坐标仍变化。

4. **num=2 的 contact 两个 found 都是5，是否有十个接触？**

答：只有5条匹配、保留2槽；每个非空槽重复报告匹配总数。found>0 也不保证正力。

5. **把 tactile reshape(N,3)，用第二列作有符号滑动速度，错在哪里？**

答：实际是(3,N)通道优先，两个速度通道是各候选绝对投影之和，没有方向符号；第0通道是正穿透长度，不是 N 或 Pa。

6. **设置 noise=.01、cutoff=20 是否创建20 Hz带噪传感器？**

答：没有。noise 是元数据，cutoff 通常限幅；采样周期应由 interval 表达，滤波/噪声模型需单独定义。

7. **有 delay 的模型只调用多次 mj_forward，为何 history 没有成为长记录？**

答：计算阶段读 history；积分器的 advanceStart 才插入当前采样。相同 timestamp 的计算次数不是推进次数。

8. **关闭 sensor 后用当前 data.time 标注 sensordata，有何问题？**

答：关闭时不会清空旧输出，时间和读数可能脱节。应保存禁用/更新状态与来源时间，不能据数组非空判断新鲜。

下一课：[相机、几何查询与图像坐标](cameras-and-geometry-queries.md)；[渲染与 viewer](rendering-and-viewer.md)。
