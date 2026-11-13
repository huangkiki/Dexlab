# E1 验证记录

对应 [Issue #2](https://github.com/huangkiki/newton-atlas/issues/2) 与[模型、坐标、状态与时间](modeling-state-time.md)。这是源码与静态验收记录；外部 PR、提交与合入状态在 Issue 中追踪。E1 从已含 E0 导读的默认分支 `81dbda3c7e4918d448cf7bd93aa2f696d0c2765b` 开始。

## 本章完成了什么

| Issue 要求 | 交付与核对位置 |
|---|---|
| 坐标、单位、姿态、惯量 | 正文第 2–4 节：变换定义、COM、惯量公式、导入缩放；对照 builder、惯量与 importer 实现 |
| 原生建模与资产 | 第 1、4 节：body/shape/joint/articulation；URDF/MJCF/USD 的不同来源语义及许可记录 |
| 状态维度与所有权 | 第 1、5–6 节：q/qd start 表、maximal/generalized 权威字段、COM frame 与 Warp 排列 |
| reset、快照、采样与时间 | 第 7–8 节：双缓冲、碰撞采样时刻、base/后端 reset 边界与调用者时钟 |
| 原理基础、易错点、练习 | 第 3、6、9–11 节：惯量推导、符号纠错、预测积分、故障表与 8 道带答案练习 |
| 最小原生例子 | [examples/e1_model_state.py](../examples/e1_model_state.py)：偏心 primitive、明确分配/步进/采样/冷复位；仅语法检查 |
| 双语入口和真实进度 | 中英文 README、curriculum、roadmap、versions 与 source-map 均更新；B0/B4 只标基础部分 |

## 执行过的检查

使用 Python 3.12 做语法与文档检查，没有 import `newton` 或 `warp`。检查命令：

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

源码检查使用官方固定提交 `713fecdc41caf0c9d726f5c016939f36e66e3dff` 的递归 Git tree，以及同一提交的 raw 文件：

1. 对 [sources.json](sources.json) 的 **22 个文件**计算 Git blob SHA-1，即 `SHA1("blob " + byte_length + NUL + file_bytes)`，逐一与官方 tree 中的 blob 和 manifest 对照。
2. 扫描本仓 Markdown 内 **90 个 Newton blob 链接**，要求 revision 等于固定提交、文件已列入 manifest，行号上下界有效。
3. 人工阅读正文使用的实现分支；anchor 有效只证明定位存在，不证明语义，不能代替逐项源码审查。
4. 解析 **1 个教学 Python 文件、0 个 Markdown Python fenced snippets** 的 AST。普通文本流程图不是 Python 片段；脚本从不导入或执行教学文件。CI 增加同一 `check_examples.py` 静态门禁。

机器可读的内容摘要与状态见 [e1-validation.json](e1-validation.json)。没有测试框架或跨引擎抽象加入教学例子。

## 自审发现与保留限制

- 以明确参考点推导并对照 XPBD kernel，记录上游 conventions 的力矩换点、body/spatial twist 两处符号不一致。只限定本版本这两处表述，不据此宣称整个引擎错误。
- 记录 URDF/MJCF 显式惯量缩放和固定密度缩放的差别；USD legacy 刚体非单位 metadata 限制不能被“导入成功”掩盖。
- 区分 `body_qd` 与 FREE/DISTANCE `joint_qd` 的 frame/参考点，以及 Control 的 world wrench 特例；维度相同不能推出字段可互换。
- `eval_fk/ik` 的读写范围与 Solver 权威坐标表示明确；`State.assign` 不包括 solver/controller/RNG 的全套历史，base reset 不提供通用恢复保证。
- 最小例子未执行，API 调用仅对照所读版本；没有验证二进制兼容、设备可用性、物理行为、数值稳定性、性能或精确续算。
- E1 完成 A1/A2；B0 的完整动力学/约束与 B4 的完整数值/可微限制仍待 E3。E2–E7 未由本章代为完成，当前没有新增 DexLab 实验。

## 下一项选择

E1 合入后先做 E2，沿已明确的状态/控制边界解释驱动、机器人与任务接口。复审依据和其他依赖见 [roadmap](roadmap.md)；不提前关闭 E2，不把示例语法通过当作课程后续主题的验收。
