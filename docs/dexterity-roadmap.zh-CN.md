# 灵巧操作：从研究到可运行任务

[English](dexterity-roadmap.md)

**当前缺口是任务与机制覆盖，而不只是增加引擎。** 苹果抓梗主要验证保持接触；它不能替代手内旋转、换指、双手交接、工具接触或柔性物体操作。

本页把既有六层研究框架落实为任务路线。2026-10-05 重新获取 10 个官方仓库的 README 与提交身份，属于源码入口审查，未运行这些上游任务。原有 38 篇候选、19 个仓库为历史调研范围，不能称为本轮全部重新核验；余项仍由 #46 跟踪。固定提交和 README 哈希见[来源清单](evidence/dexterity-sources.json)。许可字段是仓库元数据线索，不代表资产再分发授权。

## 六层实验契约

| 层 | 要回答的问题 | 必须保存的证据 |
|---|---|---|
| 任务与接触 | 保持、滑动、滚动、换指还是释放？ | 接触阶段、成功首次发生与保持时长、失败时刻 |
| 本体与执行器 | 目标动作是否由真实状态执行？ | 关节耦合、实际/目标关节、限幅、控制周期、延迟、腕部约束 |
| 物理 | 哪个误差改变任务行为？ | 几何侵入、支撑力、滑移起点、步长/空间分辨率敏感性 |
| 传感 | 哪些输入在部署时能取得？ | 真值权限、遮挡、噪声、标定、触觉历史与重置状态 |
| 数据与策略 | 新数据是否增加接触策略？ | 生成/执行/有效率、过滤失败、对象划分、总计算成本 |
| 校准与迁移 | 仿真是否预测真实失败？ | 独立实测、参数辨识误差、留出对象、排序一致性 |

## 首轮借鉴决策

下表是 DexLab 提议的实验，不是上游已经完成的统一对照，也不是新功能支持声明。

| 工作 | 借鉴内容 | 可证伪的最小实验 | 限制 | 任务 |
|---|---|---|---|---|
| [ManiSkill 1/2/3](https://github.com/mani-skill/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/README.md) | 任务卡、泛化划分、原生运行与动作回放 | PushCube 接入→PickCube 保持/释放→手内旋转；分别验重置和失败 | MS2 MPM 不等于 MS3 薄布；先用上游手型 | #47 / #48 |
| [BODex](https://github.com/JYChen18/BODex/blob/06b9a3c90870d33bde9d6c665d4ed2819471407e/README.md) | 抓取可行性与加载协议 | 对同一抓取施加冻结的多方向载荷，记录首次滑落 | 非商业及 cuRobo 条款分开；不直接复制百万生成管线 | #10 |
| [DexGraspBench](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/README.md) | 抓取评价与控制参数敏感性 | 冻结物体与抓取，对比质量/增益变化后的保留率 | 历史 baseline 与 main 不混用；不是手内技能评测 | #3 / #10 |
| [DexMachina](https://github.com/MandiZhao/dexmachina/blob/adae5bf620c57723d185b2757ee3ce9656927c20/README.md) | 本体与功能重定向实验设计 | 固定物体目标，分开改变腕部约束与驱动力限幅 | 定制依赖需审查；不能把悬浮腕结果解释为机械臂性能 | #48 |
| [Taccel](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md) | 刚柔接触与触觉成本分解 | 按压/切向移动/卸载：对照净力、形变和各阶段耗时 | 凝胶模型与刚体 solver 分开验；不直接接入主排行榜 | 候选 / candidate |
| [TacEx](https://github.com/DH-Ng/TacEx/blob/adceed41afb7cb48f9ec1f66a662fb8e5a06627f/README.md) | 触觉模块接口与观测层级 | 相同轨迹对比净力、几何深度、触觉图像的观测差异 | README 固定旧 Isaac 版本且为预览；仅参考，不越过稳定版规则 | 暂缓 / deferred |
| [HydroShear](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md) | 有历史的触觉与重置协议 | 相同终态比较直接到达、滑动返回、脱离重接触 | 先验观测模型；不当作替换底层动力学的证据 | 候选 / candidate |
| [DexMimicGen](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md) | 示范扩增与失败过滤审计 | 小批示范分别计生成、执行、物理有效率和接触类型 | 源码、数据许可分开；数量增加不证明新接触策略 | 候选 / candidate |
| [DexGarmentLab](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md) | 衣物任务分解与柔性接触失败 | 先验单层抓持释放与自碰撞，再考虑双手折叠 | 旧 Isaac 依赖不自动移植；视觉折叠不代表无穿透 | #28 / #32 |
| [DexScrew](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md) | 技能与真实闭环的边界 | 声明预插入初态，记录旋转进度、载荷与退出原因 | 旧 IsaacGym 路径为历史参考；进度比不当成功率 | #6 / future tool task |

## 任务支持矩阵

“计划”与“参考”均不能使用已支持徽章；每个实现都要另验官方最新稳定版本与实际底层 solver。

| 任务族 | 当前状态 | 下一验收 |
|---|---|---|
| 苹果梗静态保持 | 原生 MuJoCo/SuperDex 已有历史证据 | 最新候选与历史配置分列；见引擎准入 |
| 布料抓持/折叠 | 已有诊断，物理有效性未整体通过 | #32 修复碰撞，不能以动画成功代替验收 |
| ManiSkill 推/抓方块 | 计划，尚无运行支持 | #47 原生运行、记录、重置隔离与独立验收 |
| 多指手内旋转 | 计划，尚无运行支持 | #48 旋转、掉落、接触切换与手腕转动负例 |
| 插入/关节工具/双手交接 | 研究候选 | 确定初态、自由度、载荷与失败判据后拆任务 |
| 触觉历史/示范扩增/衣物 | 参考与候选 | 小探针先验，不能直接承诺训练或真机表现 |

## ManiSkill 系列如何进入代码

ManiSkill 1 的物体泛化、ManiSkill2 的任务多样性和 ManiSkill3 的并行任务管理是不同参考维度。先以其支持的机器人运行原生任务，记录 ManiSkill、SAPIEN 和实际 PhysX 身份；再由现有 UniLab 管理实验，避免新增调度框架。

[官方任务文档](https://maniskill.readthedocs.io/en/latest/tasks/index.html)将软体任务保留在 MS2，尚未完整移入 MS3。MPM 体材料也不等于现有三角形薄布。

1. **M1 / #47：** PushCube 检查接入与重置，PickCube 检查抓持、支撑、保持和释放。上游 reward/success 与独立物理评分分别保存；接触数据不可得则标缺测。
2. **M2 / #48：** 核实官方手内旋转任务 ID 和支持手型。先复现可用控制轨迹；没有可用策略时明确阻塞，不用随机动作冒充任务成功。Wuji 移植另验驱动和资产。
3. **冻结后评测：** 调试与留出分开；预先登记 10 个留出工况，所有失败入表。动作重跑不同于逐帧状态注入，同 seed 不保证相同初态。持续录像展示接触细节。

重实验只在受限远端执行；先单卡验证隔离再扩到可用 GPU。准备、步进、渲染和总耗时分别记账，测速期间停止传输。真机数据不应阻塞仿真接入，但没有实测就不能宣称真实精度。

## 未完成的研究审查

Dexonomy、Dex1B、SPIDER、CHORD、Dex4D、Tacmap、PTLD、Dex-X、Labimus/LabDex、TeleOpBench、腱绳 MPC 与本体驱动研究仍是历史候选。其论文版本、源码、许可、观测权限及可执行入口须逐项复核，缺代码或不兼容时保留排除原因。不得把这个名单当作本轮完成复现。

后续触觉、数据和工具任务须先给定固定输入、成功/失败、预算与退出条件，再创建独立实现项。当前顺序是 [#46](https://github.com/huangkiki/Dexlab/issues/46) → [#47](https://github.com/huangkiki/Dexlab/issues/47) → [#48](https://github.com/huangkiki/Dexlab/issues/48)；既有布料与接触修复继续保留。

## 本切片验证与复现边界

严格中英文网站构建通过。基础 `setup.sh` 环境运行 309 项测试时，PhysX 接触明细测试因缺少可选 UniSim 适配补丁报错；失败日志保留。安装与仓库 `scripts/patches/unisim-1.7.10-physx-adapter.patch` 完全一致的已披露适配源码后，309 项测试通过。该补丁修改适配层，不修改官方物理引擎；不能将带补丁环境的结果声称为基础安装全套通过。本页不包含 ManiSkill 运行结果。
