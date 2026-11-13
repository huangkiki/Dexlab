# E5 静态验收记录

任务：[Issue #6](https://github.com/huangkiki/drake-atlas/issues/6)。基线为 `674dac0e2723b418711ad0ca570601d336a9b909`，对应 E2/E4 已实际合入后的 main；本阶段处理 A8/A9 与 B6 系统层合同。教程的源码交付状态与原生运行资格分开。

## 交付内容

- [环境隔离与执行生命周期](../batch-lifecycle.md)：119 行，System/Context/Simulator、reset/clone、事件边界、CPU/GPU、并行与原生系统回调。
- [随机化与学习接口](../randomness-learning.md)：120 行，RNG/RandomSource、MonteCarlo、官方 DrakeGymEnv 的端口与实际 step/reset 行为。
- [日志与回放](../data-replay.md)：138 行，trigger、日志 cache、NumPy 所有权、元数据、trajectory 和动力学重放的区别。
- [isolated_records.py](../../examples/isolated_records.py)：原创原生 Diagram、两个独立 Context/Simulator、显式 RNG、periodic-only logger、新 Context reset 和 host 数组副本；没有自动调用入口。
- 每篇 7 道有答案练习，共 21 道；中文/英文 README、导读、课程、roadmap、版本、源码地图与清单同步。

## 固定来源与关键审阅

官方阅读版本 Drake 1.57.0，commit `1e1466ba466e7ce8fa9fcca4e086ce1383e5427d`，实际 Git tree `6353dc7fc1a0aec84904838e7a39a38932594597`。本轮新增 20 个引用文件，[sources.json](../sources.json) 现有 142 个文件；全部下载字节按 `SHA1("blob " + decimal_size + NUL + bytes)` 计算，结果与清单和固定官方 tree 的 Git blob 一致。

人工对照正文、原生声明、实现与 Python 绑定，重点保留这些版本边界：

| 对象 | 已核对的实现结论 |
|---|---|
| Context reset / clone | 默认/随机 Context 只重设状态和参数，不清时间、fixed inputs 或独立 logger cache；Clone 复制 Context 缓存，不复制 Simulator/外部资源 |
| MonteCarlo | C++ 主线程串行 factory/随机 Context 设置，worker 执行 AdvanceTo/output，结果按 sample_num 落位；Python 绑定强制串行；RNG snapshot 是 factory 前状态，不是物理 checkpoint |
| RandomSource | 离散输出、abstract RNG 与周期 unrestricted event；fixed seed 仍先消费外部 fresh seed；Python 只绑定构造器，未暴露 fixed-seed setter/getter |
| DrakeGymEnv | info_handler 使用对象与 callable 返回 bool 的身份比较；reset_handler 实际三参数；先 Initialize 再设状态且没有二次 Initialize；metadata 的 ascii 与 render 的 ansi 分支不同 |
| Eval | vector 路径显式复制 Eigen 值；abstract 可引用 Context 内对象；因此 Gym 的 vector prev_observation 是 FixValue 后、AdvanceTo 前副本，不是全物理回滚 |
| 日志 | default period 仍含 forced trigger；每 Context cache 记录 publish 时间；double 日志允许借用，Clear/扩容前需复制长期数据 |
| 回放 | ZOH 用 N 个 break 构造 N−1 段，忽略末样本值；PiecewisePolynomial 的 value 路径把域外时间 clamp 到端点，不能把这个返回值解释为有效记录域的延长 |

主任务预审也指出需收紧 ZOH 末样本措辞；已补充固定 `.cc` 构造循环、value 路径和两/三 break 的端点例子。没有修补上游引擎，没有把上述源码差异描述为本机已复现的运行故障。

## 检查结果

| 检查 | 结果及范围 |
|---|---|
| `git diff --check` | 通过 |
| `git diff --cached --check` | 通过，包含新建正文、例子和验收记录 |
| `python3 scripts/check_docs.py` | 通过，全部仓内 Markdown 相对路径存在 |
| 固定源码身份与引用 | 142 个引用源文件 Git blob 匹配；539 处官方 blob 链接均为固定 SHA；每个行范围在对应文件内，清单与实际引用文件集合一致 |
| Python AST | 7 个 examples 文件及全部 5 个完整 Python Markdown 围栏均通过；新例子只有 import、函数定义和模块说明，无自动调用入口；未 import 示例模块 |
| 源码静态合同 | 通过，重新检查 Gym handler/reset/render、vector Eval copy、Python MonteCarlo 串行、Context reset 的时间/输入范围及 RandomSource Python 绑定 |
| 文本与独立算式 | 三篇各 7 道有答案练习；块公式统一为 `$$`；绝对推进时间、图像 age、日志数据量、线性插值算式用标准库核对 |

源码身份/行范围与 AST 检查不等于远程网页渲染、Python ABI 或运行验证。初轮来源登记因缺少 simulator.cc 的阅读目的条目中止，补齐后通过；静态审计脚本最初把 render 分支字段拼成 `mode`，按实际 `self.render_mode` 修正，并按绑定真实换行结构定位 MonteCarlo 后全量通过，没有放宽来源或接口要求。

## 未执行与下一项

本阶段未安装或 import pydrake/gymnasium，未构建原生模型、Diagram、Context、Simulator，未调用 Initialize/AdvanceTo、随机抽样、MonteCarlo、Gym reset/step、logger 事件、trajectory 回放、图形渲染、训练或 benchmark。没有生成轨迹、图像、奖励、性能数字或学习结果。即使将来例子运行成功，也不能据此宣称所有系统线程安全、GPU 物理、训练吞吐、sim-to-real 或跨平台 bitwise 重放能力已验收。

本次不改变 DexLab [#117](https://github.com/huangkiki/Dexlab/issues/117) 的 Drake 运行验收状态；后续实验仍复用 DexLab。建议下一项 E6，讲引擎特色和具体扩展边界；本阶段未启动，执行前仍需重新核实 main、Issue/PR 和依赖。
