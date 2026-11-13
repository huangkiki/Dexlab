# E2 验收与后续任务

对应 [Issue #3](https://github.com/huangkiki/genesis-atlas/issues/3)。先修E1已在main提交 `50a029b32dd1de3e1c63ce17e705013ae995a3a4` 实际交付；本阶段从该提交开始。记录日期：2026-10-09。

交付 [驱动、机器人与任务接口](control-robotics-tasks.md)、[原生阅读片段](../examples/control_kinematics.py)及 [原创URDF](../examples/assets/two_joint_arm.urdf)。无第三方资产复制，原创文件随本仓Apache-2.0许可。

## 验收范围

| Issue要求 | 对应证据 |
|---|---|
| 控制输入到实际驱动 | 第1、3节：派生类setter、控制模式缓冲、gain/bias公式、FORCE/VELOCITY/POSITION、限幅、重算getter与实际广义力区分 |
| 关节/资产映射 | 第2节：名字到qs/dofs两套列表、参考q映射、URDF/MJCF执行器与mimic导入边界 |
| FK/IK与限位 | 第5–7节：TCP/frame、Jacobian顺序、FK查询副作用、IK shape/default/mask/DLS/residual、joint分支限制及原生规划valid语义 |
| 批量与控制周期 | 第4、8节：环境×DOF目标shape、batch_dofs_info、mode切换、callback暂停及实际step时钟 |
| 任务接口 | 第8节：初始化/接近/闭合/保持/释放/失败的动作、观测条件、超时与记录；没有抓取成功或实证声明 |
| 双路线与练习 | A3/A5/A7知识专题交付，10道附答案练习；来源固定到官方SHA，原理扩展与完整课程仍待E3–E7 |
| 最小片段状态 | Python/URDF仅静态检查，未执行Genesis，不进行独立仿真、实验、benchmark、训练或评分器开发 |

## 验证记录

| 检查 | 结果 | 证据意义 |
|---|---|---|
| `git diff --check` | 通过 | 空白错误检查 |
| `python scripts/check_docs.py` | 通过 | 本仓Markdown相对链接目标 |
| `ast.parse`覆盖仓库Python及Markdown Python围栏 | 通过：3个Python文件、0个Python围栏 | 语法；不证明原生运行 |
| XML结构与原创资产参数核对 | 通过：3个link、2个revolute joint | 名字/父子/轴/限位/惯量结构、均匀box惯量公式；不证明资产导入或动力学 |
| 源码引用审计 | 通过：42个blob、146个固定源码链接 | manifest/blob/tree一致，固定SHA路径与行号有效 |
| Issue逐项自审 | 已完成，待主agent集成审查 | 公式假设、派生执行路径及局限；无独立审查批准声明 |

源码审计按Git blob规则重新计算内容SHA1，并对照该提交的Git tree与sources.json；源码本地缓存只作审查输入，不随仓库交付。检查结果绑定本阶段提交/集成记录，后续修改需重跑。

初次来源审计发现misc.py和inverse_kinematics.py的两处行号终点越界，已按实际文件末行修正并重新通过全部来源检查；没有将检查失败记为通过。

## 已知限制与自审重点

- E1主审曾发现基类/派生类默认值不同；本轮明确追踪RigidEntity覆盖，再查solver和kernel。
- IK签名的tolerance和执行中的n_qs与部分注释不一致；教程按实际签名、广播和返回路径。
- 控制力getter重算当前请求并限幅，不代表上次子步输出；free旋转还与步进公式不同。
- Jacobian接口linear在前；free旋转增量与动力学角速度frame不同；球关节分支不能仅凭继承API宣称正确支持。
- 模型参数的环境维由batch_dofs_info决定，不能把动态输入的批量支持推广到共享增益/range。
- 原生规划拒绝free/ball，valid mask在包装层取反；起/终点已有接触pair被排除，不能宣称绝对无碰撞。
- IK/路径只是候选，不能当作真实机器人到达、抓稳或释放；可微目标记录也不证明IK/规划/任务逻辑均可微。

## 完成后的重新规划

下一项建议 **E3 接触、求解器与力观测**。E2已经将输入、裁剪后的驱动力、平滑/约束广义力与任务条件分开，可从已固定的源码字段继续讲接触与求解，避免把getter混作力传感器。E4可独立开展；E5还依赖E4。后续保留E1多物理reset/checkpoint限制，并在E7统一审校，不能用当前E0–E2交付代替完整课程完成。
