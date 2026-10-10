# Drake 接触路径协议

[English](drake-contact-paths-protocol.md) | [简体中文](drake-contact-paths-protocol.zh-CN.md)

[#151](https://github.com/huangkiki/Dexlab/issues/151) 扩展[原始准入](drake-incline-protocol.zh-CN.md)，保留1 µm间隙v2历史批次。官方原生 Drake **1.57.0**，源码 `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，Python3.12.12、NumPy2.5.3、CPU FP64。冻结前核实GitHub/PyPI最新稳定版，402个分发文件与官方wheel及#117完全一致。未转换框架资产、未修改引擎。

## 固定矩阵与参数

当前离散solver为SAP，近似为kLagged、kSimilar、kSap；各配点接触或hydroelastic，共六个有效配置。复用旧kLagged/hydroelastic九正例与负例，其余五配置分别在独立进程执行九正例与一负例。同值枚举别名不另计配置。当前刚性方块/柔顺半空间资产下，fallback走hydroelastic：三个独立20步静态配对的状态、力和接触记录完全一致。其他资产可能回退到点接触，不声称全局等价。[版本化API/源码记录](evidence/drake-contact-paths/source-links.json)。

保持原40 mm/64 g方块、零COM、各向同性惯量、重力9.81；15°静态μ=.5、35°滑动μ=.5、15°μ=0；2/1/.5 ms、2 s、.5–2 s评分窗。初始离面1 µm；无地面负例1 ms/2 s。点模型忽略hydroelastic属性，但资产几何保持一致。

- Hydroelastic：刚性方块网格分辨率.01 m；柔顺平面模量1e8 Pa、厚度.1 m。
- 点接触：每几何显式刚度2e6 N/m，串联后1e6 N/m；是工程工况，不代表材料标定或与hydroelastic刚度等价。
- 静/动摩擦相同，原生调和组合；Hunt–Crossley耗散0、静摩擦正则化速度1e-4 m/s、近刚性阈值1.0。
- 每几何显式松弛时间.1 s，原生相加为.2 s。kSap使用Kelvin–Voigt松弛时间、忽略Hunt–Crossley耗散；Lagged/Similar相反。源码默认值与实际读回分开；新属性均直接读回。[组合律](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/contact_properties.cc)及[接触构造](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc)。

不按结果调参。初始固定配置不属于统一调优预算/冻结留出集验收，不计可靠coverage-v1。增加配置不增加任务类型。

## 观测与验收

记录原生初始质量/惯量/坐标/材料及采样端口设置。逐步保存状态、原生广义接触力和力矩；hydroelastic保存积分面力，点接触保存原生作用于B的力并按配对顺序换算到方块。点对还保存见证点、穿透、法线、作用点和滑动/分离速度；hydroelastic新增每个面的面积、质心、法线、采样压力与平面压力梯度，这些不是每面求解后力读回。

采样力对应整段更新，几何取更新起点，速度取终点。核对时钟、位置/速度、接触力之和、绕旧COM的世界系力矩、符号和几何；初始化后不写状态。原生接触使用动态存储并核对复制数量，不虚构固定容量。求解迭代、实际收敛容差及Python未绑定的compliance类型值仍明确缺失。[点对符号](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/point_pair_contact_info.h)、[采样接触路径](https://github.com/RobotLocomotion/drake/blob/1e1466ba466e7ce8fa9fcca4e086ce1383e5427d/multibody/plant/discrete_update_manager.cc)。

物理阈值不变：静态位移/速度.001 m/.001 m/s，滑动位置/速度RMSE .01 m/.01 m/s，加速度.05 m/s²，转动.01 rad，几何穿透.001 m，力平衡RMSE .01 N，连续支撑；状态/接触冲量检查仍为 **1e-7 N·s**。无效正例留在九例分母内，负例必须观测有效且被拒绝；公共评分器与旧数据未修改。

## 预算、资源与复现

正式冻结50次启动/115000次更新。独立六小时/64次开发包用了34次启动/13360次更新，包含零步准入、短程路径检查、三条旧滑动压力补采和两条独立残差重复。不占夹持主线700次预算。

短程峰值179.15 MiB，选择最小 **8 GiB/四核配额**、零swap、另留8 GiB桌面空间。正式服务峰值225.70 MiB，无memory-high/OOM或CPU限流。新未知/复杂任务仍从16/24 GiB开始。控制器日志名冲突使第一条完成后、第二个原生进程启动前退出；保留失败，续跑仅补49例，复用第一条。引擎代码、协议和资源冻结均未改变。

在既有bounded runner与研究锁内执行。[发布证据](https://github.com/huangkiki/Dexlab/releases/tag/v0.55.0)含输入和可移植采集器；完整命令见[英文协议](drake-contact-paths-protocol.md#budget-resources-and-reproduction)。单例使用 `python -m dexlab.drake_incline --protocol "$CASE_PROTOCOL" --proof "$PROOF" --output "$NEW_CASE" --record-only`；离线评分用 `scripts/score_drake_contact_paths.py`，公式诊断用 `scripts/diagnose_drake_lagged.py`，均可在只有NumPy2.5.3的环境重放。

公开副本仅脱敏本地安装/回溯路径，逐项保存原/公开哈希并更新runtime引用绑定；状态、接触、准入和协议字节不变，私有原件保留。服务成本和原生调用成本分别呈现，不作为引擎速度排名。[结果](drake-contact-paths-results.zh-CN.md)。
