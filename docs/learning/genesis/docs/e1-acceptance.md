# E1 验收与后续任务

对应 [Issue #2](https://github.com/huangkiki/genesis-atlas/issues/2)。先修 E0 已在默认分支 `4fa7a76e7ebbd4e9b58b7c04f277527af32d7450`；本阶段从该提交开始，交付 [建模、坐标、状态与时间](modeling-state-time.md)和 [原生 API 阅读片段](../examples/state_layout.py)。记录日期：2026-10-09。

## 验收契约

| 要求 | 文档证据与范围 |
|---|---|
| 坐标、单位、姿态与惯量 | 第2–3节：SI、Euler度与关节弧度、wxyz、作者/内部/质心frame、取样点速度、组合惯量与定密度缩放 |
| 建模与资产 | 第1、3节：生命周期、Morph/Material/Surface分工、URDF/MJCF映射、固定link合并、几何/惯量/许可分离 |
| 状态维度、所有权、reset | 第4–6节：q/v流形及索引、getter复制、batch布局、八类solver状态、基础reset与完整checkpoint的差异 |
| 时间与数值基础 | 第7节：dt/substeps/iterations、速率协商、可微窗口、积分分支及步前/步后采样 |
| 原理与应用两条路线 | A1/A2专题完成；B0/B4基础交付，约束求解/完整数值与多物理离散化继续由E3/E6承担 |
| 原生接口与练习 | 字段对照、8类易错症状、9道带答案阅读练习；保留原生API，无跨引擎封装 |
| 版本与证据 | 所有源码结论绑定官方提交 `216a708e06124595521a9d36a51fae5393fd4ff8`；文件身份在 [sources.json](sources.json)，固定链接在 [source-map.md](source-map.md)及专题 |
| 验证与未运行边界 | 下表列静态验证；没有 import/build/step 引擎运行、实验、性能基准、训练或评分器 |

## 验证记录

验证命令和结果在本分支最终提交前完成；提交由 Git 历史与本阶段集成 PR 绑定，不把旧提交的检查移用于后续实现。

| 检查 | 结果 | 可证明的内容 |
|---|---|---|
| `git diff --check` | 通过 | 空白错误 |
| `python scripts/check_docs.py` | 通过 | 本仓库 Markdown 相对链接目标存在 |
| 对仓库 `.py` 与 Markdown `python` 片段运行 `ast.parse` | 通过：2个Python文件，0个Python围栏 | Python语法，不证明依赖或运行正确 |
| 固定来源审计 | 通过：35个blob、90个固定源码链接 | 所引官方blob URL的提交/path/行号、manifest身份与Git tree一致 |
| 自审对照Issue | 已完成，未声明独立审查批准 | 检查公式假设、claim与原生实现、显式列出未覆盖范围 |

首次来源审计发现两处行号终点超出文件长度（inertial.py 与 states/solvers.py），已改为实际末行并重新全量通过。固定来源审计同时验证所引路径属于该提交的 Git tree，下载内容计算 `SHA1("blob " + byte_length + NUL + content)` 与 manifest 和 tree 一致；每个行号范围落在实际文件中。这证明引用身份，不自动证明每段解释正确，解释另经下列自审核对。

主 agent 审查发现基类与派生类 setter 的默认值不同，已修正表格与习题：`KinematicEntity` 默认为 `False`，`RigidEntity` 覆盖为 `True`，并补齐对应源码。

## 源码发现与未解决问题

- Morph 参数说明称 quat 覆盖 euler，但实际校验器拒绝二者同时给出；教程以校验器为准。
- `relative=True` 恢复作者原点，不代表父坐标系；free joint `get_qpos` 仍是内部原点。
- MPM/SPH/PBD/FEM 的基础状态恢复忽略 `envs_idx`，Tool 未传递该参数；不能由 Scene 签名证明混合场景的局部 reset 隔离。
- SF `get_state/set_state` 为空；完整 checkpoint 还受 solver.data 与 IPC 限制。接口名不等于所有 solver 支持。
- `reset(state)` 会替换登记初态、清零时钟并重启部分周边状态；完整 checkpoint 与基础查询状态契约不同。
- 非Euler自由刚体的中点分支排除可微路径，不能仅按 integrator 枚举推断全部积分公式。

这些均为固定源码阅读发现，未用运行复现替代或补强。运行层正确性、多物理 reset 回归与数值稳定性仍未验收；以后复用 DexLab 对应版本/工况的证据，不在本阶段另建实验。

## 每项完成后的复盘

E1 已提供控制课依赖的 joint索引、姿态/速度frame、输入与状态区分和控制时钟基础。下一项建议 **E2 驱动、机器人与任务接口**，先逐项追踪 `control_dofs_*`、驱动范围、关节映射和 FK/IK，再写不执行的最小片段与任务接口说明。E3与E4同样需等待E1实际合入默认分支；E5/E6必须保留本章发现的多物理reset/checkpoint限制。E7才验收完整双路线，不把本章基础覆盖写成整个课程完成。
