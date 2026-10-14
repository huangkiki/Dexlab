# Drake 斜面准入协议 v1

[English](drake-incline-protocol.md) · [Issue #117](https://github.com/huangkiki/Dexlab/issues/117)

本项是原生路径初次准入，不代表六引擎对照完成或 `coverage-v1` 可靠覆盖。正时长运行前冻结[协议](evidence/drake-incline/protocol-v1.json)、[官方 wheel 证明](evidence/drake-incline/official-proof.json)、记录器／评分器字节与资源方案；本批次不按结果调参。九例沿用原来的 40 mm／64 g 方块、15°静态 μ=.5、35°滑动 μ=.5、15°名义零摩擦、2/1/.5 ms 步长、两秒时长、0.5–2 s 评分窗及全部物理阈值。MuJoCo 的 impedance 不作为 Drake 参数。

第十例删除 1 ms 静态工况的地面，必须保持自由落体记录有效，同时不能通过独立支撑／保持验收。原生异常、截断轨迹或观测不一致将停止批次；普通物理失败继续保留为结果。初始预算为九正例、一负例，原生运行合计最多 30 分钟，单进程；冻结 16 GiB／四核自适应配额，启动另留 8 GiB。整个服务上限 1,800 s，也约束原生时长；准入成本不用于性能排名。

## 固定原生配置

Drake 1.57.0，官方构建源码 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，CPU 双精度，离散系统，**SAP 求解器／kLagged 接触近似／严格 hydroelastic 接触**。方块使用刚性 hydroelastic 表面，分辨率提示 10 mm；解析半空间使用柔顺 hydroelastic 属性，slab 厚度 0.1 m、模量 1e8 Pa。两表面 Hunt–Crossley 耗散为零、静动摩擦系数相等。配对 API 使用调和组合；相等输入保持系数，包括零。这些是数值参数，不是实测材料或与其他引擎校准后的等效参数；不启用点接触回退或替代几何。

输入 stiction tolerance 为 1e-4 m/s，near-rigid threshold 为 1.0 并核对原生 getter。离散模型解析动摩擦，忽略独立静摩擦系数。当前公开 API 暴露 SAP 和 `kSap`、`kSimilar`、`kLagged` 三种近似，不含 TAMSI。本切片仅运行 kLagged／hydroelastic；其他适用配置仍为**未运行**，由 [#151](https://github.com/huangkiki/Dexlab/issues/151)承接，不能标为不支持。

[匹配求解器源码](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_solver.h)的默认值为 Newton 最多 100 次、最优性绝对／相对容差 1e-14／1e-6、代价容差 1e-30／1e-15、精确线搜索最多 100 次，以及块稀疏 Cholesky。最优性绝对容差单位是焦耳平方根，不是力容差。这些属于**源码默认值**，不是原生 SAP 参数对象快照或实际迭代数。公开 pydrake 缺少逐步 SAP 统计／参数及 stiction-tolerance getter；材料 `HydroelasticType` 枚举没有 Python 值绑定，其读回保持 null。输入设置与可读取的几何／材料属性分别保存。

## 观测与独立验收

启用并读回 sampled 动态输出。[Plant 源码](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/multibody_plant.h)规定：动力学来自使用旧状态的本次更新，运动学来自更新后的状态。保存每个区间的起止时钟、hydroelastic 接触面的积分力／质心处力矩、面积、广义接触力、位姿及空间速度；不以步末重新求力替代原观测。逐积分点力及原生求解统计不可观测。

步进前核验原生质量／惯量／COM、方块尺寸、碰撞与平面坐标、重力、solver／接触选择、材料参数和初态。离线验收拒绝哈希变化、核心身份不符、重置污染、坐标／时钟错误、接触丢失与力符号错误。接触合力须在 1e-7 N 内匹配原生广义力的平移分量；动量一致性沿用共同 1e-7 N·s 阈值，位移增量与步末速度乘 dt 的误差不得超过 1e-10 m。穿透从记录的步末方块／平面几何解析计算，不称为原生积分点深度。位置、速度、加速度、转动、支撑与穿透的物理阈值均沿用原协议。

六引擎队列完整保留：MuJoCo #146、SuperDex #147、Genesis #148、Newton Physics #149、PhysX #150 独立执行；Drake #151 使用本接入。MuJoCo／SuperDex 历史记录保留原批次身份；不推定其他引擎或其他 Drake 配置已获得新结果。

```sh
# 在单独准入的可选 Drake 环境中，通过资源限制和互斥保护执行：
PYTHONPATH=src python -m dexlab.drake_incline \
  --protocol docs/evidence/drake-incline/protocol-v1.json \
  --proof docs/evidence/drake-incline/official-proof.json --output NEW_RUN
PYTHONPATH=src python -m dexlab.drake_incline_score --input NEW_RUN --output NEW_SCORE.json
```

## 明确登记的 v2 修订

保留 v1 原生裁剪失败后，三个事前登记的间隙诊断完成。[v2](evidence/drake-incline/protocol-v2.json) 只增加 1 µm 初始法向间隙；九个正例、负例、材质、评分窗口与限值不变，单列批次。新代码/协议哈希和 1,800 s 批次预算已在[运行前登记](https://github.com/huangkiki/Dexlab/issues/117#issuecomment-6084573507)。见[结果及全部失败](drake-incline-results.zh-CN.md)。
