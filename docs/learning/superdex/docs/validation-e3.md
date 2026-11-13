# E3 验证与范围记录

任务：[SuperDex E3 #4](https://github.com/huangkiki/superdex-atlas/issues/4)。开始时读取 Issue/仓库规则，核实 main 为 `f55244beb17360c78082038054a7ae5e0ca7af18`，E1/E2 已实际合入、工作树干净、无在途 PR；从该 main 建立 E3 分支。检查日期：2026-10-09。本记录与课程同一提交保存，实际提交由文件历史及交付记录定位。

阅读版本为 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`。所有结论针对固定官方源码；未安装/import/运行原生引擎，未创建新实验、训练、benchmark 或评分器。来源身份见 [manifest](sources.json) 与[源码地图](source-map.md)。

## 验收对应

| 课程/要求 | 交付内容 | 证据边界 |
|---|---|---|
| A4 接触接口 | [E3 专题](contact-solvers-forces.md)第 3–5 节：colliding/collider、SDF/点云、过滤、材料逐字段组合 | API/头文件与实际分支共同核对 |
| B0 动力学补充 | 第 2 节：广义力、虚功、actor/constraint/contact 装配、刚体惯性两条路径 | 教学力平衡式明确假设；不冒充统一内核方程 |
| B1 步进链 | 第 7 节：Step、pre-step、island、stage、碰撞/装配/求解、状态/query 更新 | 正时间与零步分开；没有运行时间线 |
| B2 接触模型 | 第 4–5 节：几何平均与静态例外、维数修正、PolyReLU、C1/C∞、黏性/恢复拟合 | 实际公式与单位、非可积/导数近似边界 |
| B3 求解器 | 第 8–9 节：Newton/BFGS/SR1、线性 Auto/显式分派、预条件、EW、warm start、终止/发散 | 停止与收敛不同；源码默认不代替运行配置 |
| B4 积分 | 第 6 节：BE 推导、稳定性假设、stage/BDF 历史、h/H/α 区别、可微前提 | 欧氏常质量推导只作教学；完整可微实现留 E6 |
| B5 力与冲量 | 第 10 节：query 注册、方向、空间积分、质心力矩移点、时间平均、失败数据 | 区分 N、N·s、广义力与配置命令；无新力学测量 |
| 原生片段 | [read_contact_after_step.py](../examples/read_contact_after_step.py) | 只复制已有应用步后的观测；调用者负责提前注册和步进，未执行 |
| 易错点/练习 | 第 11 节诊断表和第 12 节 16 题答案 | 固定源码阅读练习，没有新增实验方案或评价阈值 |
| 双语与状态 | 中英文 README 正文与导航链接系列总仓，更新 curriculum/roadmap、导读与 E1 后续入口 | 课程文档完成不等于运行验收；E4–E7 仍待交付 |

## 实际检查

- `git diff --check` 通过。
- `python scripts/check_docs.py` 通过，检查本仓相对 Markdown 文件链接；远端和锚点另查。
- 89 个 source manifest 条目逐一匹配固定 Git tree 的 path/blob；下载内容以 Git blob SHA-1 算法核对。新增 27 个源码文件均保持固定 SHA。
- 所有 Markdown 固定 blob 链接，包括 reference-style，共覆盖这 89 个文件；commit、manifest 覆盖与 3 个显式行号锚点范围通过。reference-style 定义不存在缺失。
- 全部 4 个 Python 文件与 1 个 Markdown 完整 Python 代码块经 `ast.parse` 通过；没有 import 或执行这些程序。
- 自审核对原生 Python 类/字段/枚举/getter 名称，以及关键公式的分支、符号、量纲和假设。没有修改上游代码或复制上游源文件进入仓库。

自审重点：`CombineContactParams` 不使用 min；静态例外只适用于 penalty/falloff；压力密度须乘空间积分权重；C1 摩擦在平滑区是二次幅值曲线；Newton 可能用近似/PSD Hessian；AUTO 的阈值针对 island DoF；linear/nonlinear tolerance 与 norm 不混用；force query 读取已有装配而非即时重求；query 清空不能当作真实无接触。

## 未验证项与复盘

没有 native smoke、仿真、数值精度、性能、梯度或跨引擎比较证据。89 个文件的身份核对不代表已审计整个引擎；教材只覆盖本章指明的路径。源配置不能补写 DexLab 历史 [#124](https://github.com/huangkiki/Dexlab/issues/124) 的 wheel/core/binding 身份或实际执行配置。

本章源码范围已经完成；后续实验仍复用 DexLab，不把另建实验作为该源码课程交付前提。E4 传感器/渲染是下一项优先任务；E5 仍需 E4；E6 已具备 E3 先修，但特色、柔体与可微实现仍需单独开发。E7 仍等待剩余专题。远端集成、Issue 与看板状态由主任务依据实际交付核实。
