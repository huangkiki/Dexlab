# Drake：接触路径结果

[English](drake-contact-paths-results.md) | [简体中文](drake-contact-paths-results.zh-CN.md)

原生 **Drake1.57.0 / CPU FP64 / SAP** 已覆盖三种近似与点/hydroelastic两种接触路径的初始斜面记录。固定工程配置、**未按结果调优**，不作为引擎排名或可靠任务覆盖准入。[协议、身份与命令](drake-contact-paths-protocol.zh-CN.md) · [完整清单](evidence/drake-contact-paths/manifest.json) · [归档与重放](https://github.com/huangkiki/Dexlab/releases/tag/v0.55.0)。

| SAP approximation / contact | Positive passes | Invalid positives | Valid rejected negative |
|---|---:|---:|---:|
| kLagged / hydroelastic (reused #117) | 6/9 | 0 | 1/1 |
| lagged-point | 0/9 | 0 | 1/1 |
| similar-hydroelastic | 5/9 | 2 | 1/1 |
| similar-point | 0/9 | 2 | 1/1 |
| sap-hydroelastic | 3/9 | 0 | 1/1 |
| sap-point | 2/9 | 1 | 1/1 |


| Configuration | Sliding timestep | Maximum momentum residual (N·s) |
|---|---:|---:|
| similar-hydroelastic | sliding-h0.001 | 1.135117926e-07 |
| similar-hydroelastic | sliding-h0.0005 | 2.131288136e-07 |
| similar-point | sliding-h0.001 | 1.376389105e-07 |
| similar-point | sliding-h0.0005 | 1.363337982e-07 |
| sap-point | sliding-h0.0005 | 1.698106175e-07 |


动量检查仍为1e-7 N·s，五条无效正例保留在分母中。独立新进程对Similar/hydroelastic1 ms与SAP/point.5 ms的状态和接触逐项完全复现。参数、时钟、接触和及独立广义力/力矩检查通过；小量动量残差的完整解释由[#165](https://github.com/huangkiki/Dexlab/issues/165)继续验证。无效观测不证明引擎无法完成任务，也不证明物理准确。

Similar/hydroelastic通过两个静态和三个名义零摩擦工况；SAP/hydroelastic通过三个静态；SAP/point通过1/.5 ms零摩擦；其余两组点配置均未通过。失败包含支撑中断、力不平衡、位移、转动与穿透，减小步长并不普遍改善结果。点模型的单配对接触与hydroelastic面接触不同，相同资产尺寸不等价。无地面负例观测有效并被正确拒绝。五份 `*-score.json` 保存位移、速度、加速度、转动、穿透、支撑及耗时；无效观测不赋予物理验收指标。

## 旧Lagged滑动为何接近静止

三条补充观测重放与#117的状态、力、广义力、数量和时间戳 **完全一致**。压力梯度匹配 authored 平面；实际法线还包含很小的侧面，不能把所有接触一概投影成唯一平面来归因。初版平面分解诊断及其局限保留。

源码中Lagged切向冲量使用 **先前弹性法向冲量** 限幅，输出的法向冲量则使用更新后速度。耗散0时，每个合格面满足 `fe0=A*p; k=A*(-grad_plane·n); fn=max(0,fe0-h*k*vn_next)`，以及 `Ft=-μ*fe0*vt_next/sqrt(|vt_next|²+epsilon²)`。

[离线诊断](../scripts/diagnose_drake_lagged.py)由质量/惯量和源码Delassus近似重建正则化，累加各面法向/切向贡献。2/1/.5 ms的向量力最大重建误差为 **2.365e-13 /1.871e-13 /3.930e-13 N**；这是实测重建误差，不是修改后的验收容差。原生平均下坡力约−.361 N；在相同已观测状态下把摩擦限幅换成更新后法向量，代数结果为−.179/−.206/−.240 N。该反事实只诊断方程，**不是**kSimilar仿真或修复后的轨迹。

证据支持将过强切向支撑归因于已实现的滞后摩擦响应及实际面几何，不支持“适配器力符号读错”。这不会让原失败变成准确，也不证明普遍引擎缺陷。每面求解后冲量/实际迭代仍未暴露，公式量明确属于源码推导。[Lagged方程](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_hunt_crossley_constraint.cc) · [Delassus近似](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/contact_solvers/sap/sap_model.cc) · [数值报告](evidence/drake-contact-paths/lagged-formula-public-v1.json)。

## 成本、恢复与边界

50个正式原生进程完成115000次更新。原生调用累计 **4.678698 s**、观测 **3.961814 s**、建模 **0.457769 s**、工况墙钟 **16.858062 s**。两次正式服务总计44.645 s，含启动与控制器失败；峰值225.70 MiB，8 GiB/四核限制下无memory-high/OOM/CPU限流。[计数器与压力](evidence/drake-contact-paths/resources.json)。不同计时范围不能混用为引擎速度排名。

日志名冲突发生在第二个原生进程启动前，失败记录保留；续跑复用第一例，仅补49例。开发34次启动/13360步含零步/短程准入、三条旧观测补采及两条独立数值重复，与正式和夹持预算分开。公开元数据脱敏有显式哈希记录，原生观测不变，支持无引擎离线重放。

fallback及枚举别名不额外计有效配置。此批只覆盖 **斜面**，基础接触/碰撞/夹持/抓取与框架路径仍由[#121](https://github.com/huangkiki/Dexlab/issues/121)、[#152](https://github.com/huangkiki/Dexlab/issues/152)跟踪。旧#117及历史批次保留自身协议。增加solver行不增加任务类型，也不触发下一夹持切片。

## 全部新增工况

| Profile | Case | Verdict | Force RMSE (N) | Rotation (rad) | Penetration (m) |
|---|---|---|---:|---:|---:|
| lagged-point | static-h0.002 | fail / 失败 | 0.914017 | 0.0480727 | 0.000260203 |
| lagged-point | static-h0.001 | fail / 失败 | 0.569409 | 0.00616052 | 2.14521e-05 |
| lagged-point | static-h0.0005 | fail / 失败 | 0.483948 | 0.00435504 | 9.18007e-06 |
| lagged-point | sliding-h0.002 | fail / 失败 | 0.771351 | 0.053002 | 0.000228128 |
| lagged-point | sliding-h0.001 | fail / 失败 | 0.517506 | 0.0113026 | 2.03728e-05 |
| lagged-point | sliding-h0.0005 | fail / 失败 | 0.480135 | 0.00715864 | 6.04426e-06 |
| lagged-point | frictionless-h0.002 | fail / 失败 | 0.696747 | 0.278998 | 0.0010982 |
| lagged-point | frictionless-h0.001 | fail / 失败 | 0.408008 | 0.023033 | 0.000151765 |
| lagged-point | frictionless-h0.0005 | fail / 失败 | 0.216658 | 0.000904812 | 9.31601e-06 |
| lagged-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| similar-hydroelastic | static-h0.002 | fail / 失败 | 0.747741 | 0.00125539 | 3.69029e-05 |
| similar-hydroelastic | static-h0.001 | pass / 通过 | 1.91757e-07 | 0.000113872 | 8.47573e-06 |
| similar-hydroelastic | static-h0.0005 | pass / 通过 | 2.99865e-07 | 4.03214e-05 | 1.36893e-06 |
| similar-hydroelastic | sliding-h0.002 | fail / 失败 | 3.54752 | 3.13962 | 0.0034847 |
| similar-hydroelastic | sliding-h0.001 | invalid / 无效 | — | — | — |
| similar-hydroelastic | sliding-h0.0005 | invalid / 无效 | — | — | — |
| similar-hydroelastic | frictionless-h0.002 | pass / 通过 | 3.89324e-06 | 3.71514e-06 | 3.69029e-05 |
| similar-hydroelastic | frictionless-h0.001 | pass / 通过 | 3.90137e-06 | 1.8128e-07 | 8.47573e-06 |
| similar-hydroelastic | frictionless-h0.0005 | pass / 通过 | 3.78805e-06 | 5.16191e-08 | 1.36893e-06 |
| similar-hydroelastic | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| similar-point | static-h0.002 | fail / 失败 | 1.24196 | 0.579581 | 0.000752525 |
| similar-point | static-h0.001 | fail / 失败 | 1.20581 | 0.137582 | 0.000172008 |
| similar-point | static-h0.0005 | fail / 失败 | 0.841577 | 0.0200776 | 1.51416e-05 |
| similar-point | sliding-h0.002 | fail / 失败 | 5.87829 | 3.14122 | 0.00243922 |
| similar-point | sliding-h0.001 | invalid / 无效 | — | — | — |
| similar-point | sliding-h0.0005 | invalid / 无效 | — | — | — |
| similar-point | frictionless-h0.002 | fail / 失败 | 0.696747 | 0.278998 | 0.0010982 |
| similar-point | frictionless-h0.001 | fail / 失败 | 0.408008 | 0.023033 | 0.000151765 |
| similar-point | frictionless-h0.0005 | fail / 失败 | 0.216658 | 0.000904812 | 9.31601e-06 |
| similar-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| sap-hydroelastic | static-h0.002 | pass / 通过 | 7.53842e-07 | 0.00174914 | 6.98226e-05 |
| sap-hydroelastic | static-h0.001 | pass / 通过 | 7.71259e-07 | 0.00107974 | 3.85492e-05 |
| sap-hydroelastic | static-h0.0005 | pass / 通过 | 4.81753e-07 | 0.000570978 | 1.97884e-05 |
| sap-hydroelastic | sliding-h0.002 | fail / 失败 | 3.91991 | 3.13934 | 0.00262861 |
| sap-hydroelastic | sliding-h0.001 | fail / 失败 | 3.89722 | 3.13952 | 0.00118512 |
| sap-hydroelastic | sliding-h0.0005 | fail / 失败 | 7.20703 | 3.14113 | 0.000804191 |
| sap-hydroelastic | frictionless-h0.002 | fail / 失败 | 0.00481608 | 0.198409 | 3.88287e-05 |
| sap-hydroelastic | frictionless-h0.001 | fail / 失败 | 1.52561 | 3.1407 | 0.00241714 |
| sap-hydroelastic | frictionless-h0.0005 | fail / 失败 | 3.71195 | 3.1412 | 0.000987014 |
| sap-hydroelastic | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |
| sap-point | static-h0.002 | fail / 失败 | 0.339866 | 0.0458186 | 0.00395454 |
| sap-point | static-h0.001 | fail / 失败 | 0.253228 | 0.0210218 | 0.000479555 |
| sap-point | static-h0.0005 | fail / 失败 | 0.261055 | 0.00706249 | 0.000218955 |
| sap-point | sliding-h0.002 | fail / 失败 | 3.88151 | 3.13998 | 0.00133591 |
| sap-point | sliding-h0.001 | fail / 失败 | 6.09537 | 3.1399 | 0.000705559 |
| sap-point | sliding-h0.0005 | invalid / 无效 | — | — | — |
| sap-point | frictionless-h0.002 | fail / 失败 | 0.162925 | 0.0047957 | 0.00715774 |
| sap-point | frictionless-h0.001 | pass / 通过 | 2.82731e-06 | 0.000143903 | 6.14185e-05 |
| sap-point | frictionless-h0.0005 | pass / 通过 | 9.53597e-07 | 5.16191e-08 | 2.94452e-05 |
| sap-point | negative-no-floor | valid negative / 有效负例 | 0.62784 | 0 | 18.9609 |


Archive / 归档：`dexlab-drake-contact-paths-v1.tar.gz`，50023597 bytes，1074 files。SHA-256：`9e30d58c3ad3395a405dac335430e1e942e792e81463c0b0e4a40529c10b505c`。[Manifest / 清单](evidence/drake-contact-paths/archive.json)。
