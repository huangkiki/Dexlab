# E2 验证与范围记录

任务：[SuperDex E2 #3](https://github.com/huangkiki/superdex-atlas/issues/3)。开始时核实 default main 为 `30e46b401174111332cd116a5e3d6637d034d6ec`，E1 实际文档已合入，工作树干净、没有在途 PR；从该提交建立 E2 分支。检查日期：2026-10-09。本记录和课程同一提交保存，实际提交由文件历史/关联交付记录定位。

上游固定为 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`，见 [source manifest](sources.json) 和[源码地图](source-map.md)。固定源码课程不是候选 wheel、宿主版本或 DexLab 历史二进制的运行验收。

## 交付与验收对应

| 要求 | 对应内容 | 证据范围 |
|---|---|---|
| 控制输入到驱动 | [专题](control-robotics.md)第 1、3–6 节：JSC/OSC 返回外力、pose controller 写约束目标、transmission actuator 原生路径 | API、生成绑定及实现阅读 |
| 关节/资产映射 | 第 2 节：bot/actor space、Free 根六 DoF、dof_info、模型 effort metadata | prefab 构建与校验源码 |
| FK/IK/限位 | 第 7 节：派生 FK、Jacobian 布局、独立 IK scene、所有权、误差判据与限位区别 | Physics getter、articulated/IK 实现；没有运行求解 |
| 控制公式/单位 | 第 4–6 节：deadband PD、控制周期、Jacobian 转置、饱和、能量共轭 transmission | 教学公式注明适用假设，不假称完整内核残差 |
| 回调/任务 | 第 8 节：原生回调时序与应用任务状态机、失败/reset、外部控制集成责任 | 调用契约 + 明确标注的应用设计 |
| 片段 | [command_fixed_base_jsc.py](../examples/command_fixed_base_jsc.py)：固定根/标量 joints，输出复制与最终限幅，整套外力一次写入 | AST 及原生名称/参数核对；未 import/执行 |
| 易错点/练习 | 第 9 节 12 题带答案 | 覆盖索引、周期、限额、IK 所有权、任务责任 |
| 双语与课程状态 | 中英文 README、curriculum、roadmap；保留系列首页链接 | A3/A5/A7 文档完成，E3–E7 仍待开发 |

## 实际静态检查

- `git diff --check`：通过。
- `python scripts/check_docs.py`：相对 Markdown 文件链接通过；该脚本不覆盖远端/锚点。
- 所有 3 个 Python 文件及 Markdown 的 1 个完整 Python 代码块经 `ast.parse`：通过；不执行/import 被检查的程序。
- manifest 中 62 个固定源码文件与上游 Git tree 路径/blob 一致，下载内容按 Git blob SHA-1 算法核对；全部 Markdown 的固定 blob 链接（含 reference-style）均在 manifest，SHA 一致。
- 自审需求和最终 diff：没有修改 Physics/Robotics 上游，没有添加研究实验、训练、benchmark、评分器、跨引擎 wrapper 或应用任务框架。

本次自审重点是那些表面名称容易掩盖的行为：`set_external_forces_on_dofs` 替换整套外力；JSC saturation 不继承 Bot effortLimit；OSC 对非正限额的跳过；pose saturation 是位移/角度且不限制阻尼；IK 修改/拥有 scene、solve bool 与物理可执行性不同；自定义组件注册不自动驱动其 loop。

## 保留的边界与下一步

本章没有物理运行证据。所有“已编写/已核对”只表示课程范围和静态源码结论。

- JSC 逐分量误差不等于一般三维旋转流形控制；最小片段限制在固定根和标量关节，连续关节跨分支目标仍由应用处理。
- 固定 OSC 源码对 Jacobian 做坐标旋转，未根据 `EELinkFromEE.translation` 修正作用点偏移。不能将任意 TCP 偏置下的控制表现写成已验证能力；未测量其误差。
- Physics experimental IK/transmission 接口身份保留；IK 返回值不证明轨迹无碰撞、严格限位或驱动力可行。
- 任务阈值、实际接触观测和最终实验验收将引用 DexLab 的具体协议，当前没有生成新的阈值/评分体系。

每完成一项后重新审视依赖：E1 已合入，E2 的驱动/机器人/任务知识为后续接口提供基础。下一项优先 E3，把外力命令、pose tracking、transmission 接到接触/非线性求解/实际力观测；E4 仍独立可推进；E5 还等待 E4，E6 等待 E3，E7 等待其余专题。远端关闭/合入状态由实际 GitHub Issue/提交核实，课程完成不代替运行资格。
