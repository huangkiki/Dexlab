# E5 验证与范围记录

任务：[SuperDex E5 #6](https://github.com/huangkiki/superdex-atlas/issues/6)。恢复时 actual main/origin/main 均为 `cf889509f8563ea8fdb8501fc552ab1f92ad88fa`，工作树干净、无在途 PR，E2/E4 依赖实际在 main；建立并在临时暂停后复用 `docs/e5-batch-learning-data` 分支。检查日期：2026-10-09。章节与本记录同一提交保存，精确提交由文件历史和交付记录定位。

SuperDex 固定 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`；Gymnasium 另固定官方 v1.3.0 的 `53bf3e9a884783eb72ad3fc8b15780914c97c3e1`，版本对应上述 SuperDex `uv.lock`。该身份解释外部 seed/autoreset/space 行为，不代表安装 wheel 或运行资格。既有 E4 Polyscope 来源继续保留。

**没有执行 native import、模型编译、物理推进、GUI/渲染、实验、训练、性能测试或新评分器。** 源码下载只处理文本/字节；没有安装依赖、执行上游测试或运行章节例子。

## 验收对应

| 范围 | 交付位置 | 证据和限制 |
|---|---|---|
| A8 原生学习对象 | [专题](batch-learning-data.md)第1–2节 | Lab与Physics/Robotics/Studio、外部Gym/RLlib分层；控制/物理频率、clip/结构转换、CartPole实际单位与字段顺序 |
| 状态隔离与batch | 第3–4节 | 独立Scene、共享Scene快照覆盖/不覆盖范围、manager key/refcount/cleanup、render与直接Actor读回时序；P进程×K串行组织 |
| reset/step/结束协议 | 第2、4节 | reset dummy物理步、terminated/truncated、NEXT_STEP旧done掩码、SAME_STEP final_obs、DISABLED及reset_mask限制 |
| seed/随机化 | 第4、7节 | 两层整数seed相加导致重复的静态推导，显式列表、env/action RNG、初态与持续参数随机化的单位/分布/共享限制 |
| B6 设备/线程/数据移动 | 第5节 | CPU共享内存、alias/copy、Box flatten dtype、原生CUDA矩阵/vector往返与同步、context/线程/回调/构建边界；无性能结果 |
| 学习与求导身份 | 第6节 | 固定SuperDex RLlib调用点、checkpoint connector、diffsim接口/相邻原生步需求与数学假设；具体adjoint内部留E6 |
| A9 数据/记录/回放 | 第8–9节 | 可恢复handle/bytes、诊断JSON、HDF/transition/policy/video区分；recorder相对时间、post callback采样、缺失创建信息；task-specific HDF parser和sim-to-real元数据责任 |
| 原创最小例子 | 第4节Python片段及 [copy_lab_step.py](../examples/copy_lab_step.py) | 显式4环境seed list与一次批次；缓存结果复制、logical ID、名义控制时间；两个例子仅AST通过 |
| 易错点与练习 | 第10–11节 | 12项诊断、20道带答案阅读练习，无新实验或分数阈值 |
| 导航/来源/状态 | README中英、guide/curriculum/roadmap、source-map/sources.json、THIRD_PARTY | 保留 Sim Atlas 总仓；E6/E7及运行状态未标完成 |

## 实际检查

- `git diff --check` 通过。
- `python scripts/check_docs.py` 通过。
- 全部 148 个 SuperDex manifest 文件逐一与固定 Git tree 的 path/blob 匹配，并对缓存下载字节重算 Git blob SHA-1；本项新增24个。
- 全部13个外部 manifest 文件匹配各自固定 Git tree 和实际字节：保留 E4 的6个 Polyscope 文件，新增 Gymnasium 的7个文件；Gymnasium官方 v1.3.0 tag解析为本章固定commit。源码许可单独归属，未复制上游文件进入本仓。
- Markdown 中4个上游的固定 blob 链接（含reference-style）涉及161个文件，检查 manifest 覆盖、commit、reference定义及5个既有行号锚点范围。
- 全部6个仓库 `.py`文件和3个完整Markdown Python块经 `ast.parse` 通过。没有执行语法检查对象，也没有以 `py_compile` 或 import 触发原生依赖。
- 主审预读发现初稿把诊断JSON与可恢复handle/bytes并列、三处theta含TAB转义及两处希腊字母遗漏反斜杠；已拆开JSON诊断契约并修复，新增章节按字节检查无TAB/其他控制字符，公式逐段复核。
- 深度自审核对频率比与单位、CartPole字典排序/dtype、reset dummy步、seed嵌套、NEXT_STEP/最终观测、快照/持续配置/缓存所有权、共享render时序、cleanup失败、CUDA数据路径、recorder时间与Step写入阶段、外部checkpoint/数据解析边界。

## 未验证项与交付边界

A8/A9 与 B6 的本阶段源码课程已交付；无运行验收。没有 batch吞吐/扩展效率、共享Scene数值等价、fork/spawn实际稳定性、GPU或HDF构建兼容、策略训练收敛、梯度正确性、跨build回放、sim-to-real成效或字节级确定性结果。上游共享测试有发现范围和skip条件，本仓仅阅读其意图，不能把测试代码当成本地通过的报告。

最小Lab片段需要相应Python/包/资产和原生环境；原生构造/reset/step均会运行物理，因此没有在本阶段试跑。缓存读取例不含前一观测或完整模型/RNG状态，不能独立充当transition数据集或checkpoint。原生HDF记录也缺少完整Actor创建信息，不能据此宣称场景可重建。

Ray/Torch/LeRobot本章只引用固定SuperDex应用代码中可见的调用与缺口，没有引入或审查其外部实现，也未指定一个已验收的版本组合。Gymnasium固定身份来自SuperDex lock的参考依赖，不替代用户安装环境取证。原生diffsim相邻step状态与backward接口只用于界定学习集成边界；E6仍须讲透adjoint装配、参数化、特色Actor及兼容限制。

下一项建议为具备E3先修的E6，E7仍待完整课程审校。远端发布、Issue/Project、总仓及Obsidian由主任务在实际主审集成后处理；本分支只作本地交付。后续实验复用DexLab，当前源码不会补写历史 #124 配置或结果。
