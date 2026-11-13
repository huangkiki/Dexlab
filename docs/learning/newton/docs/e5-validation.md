# E5 验证记录

对应 [Issue #6](https://github.com/huangkiki/newton-atlas/issues/6) 和[批量、学习接口与数据](batch-learning-data.md)。开发基线为已发布 E4 `d4dd7b912c208f78e960315bb22408492ebc9e79`；开始与恢复时核对 main/origin/main、工作区、Issue OPEN 及无在途 PR，沿用 `docs/e5-batch-learning-data` 分支。E2/E4 前置已在基线内。本记录描述本地源码/静态交付，远端发布与 CI 以实际提交为准。

## 范围与证据

| 要求 | 本次交付 |
|---|---|
| 多 world 原生设计 | builder add/replicate、B+2 starts、global 两段、collision 过滤、异构数据与后端限制 |
| reset 生命周期 | State/Control/Contacts 分层、clone/alias、B+1 mask、MuJoCo/VBD/XPBD reset 差异、sensor/policy/task 所有者 |
| 学习接口 | 单步/子步/动作重复时钟、原生 ONNX policy 的观察/动作/映射/实际 capture 范围、外部 Kamino/Torch 与 Isaac Lab 指针 |
| CPU/GPU 与性能边界 | JIT/模型/步进/复制/观测分开；Warp 视图、D2H、stream、CPU APIC 与 graph 地址不变量；不提供计时结论 |
| 数据与 sim-to-real | seed/offset 与随机量身份、Model 通知路径、ViewerFile 记录/回放的实际局限、采样阶段和元数据契约 |
| 扩展入口 | attribute frequency/assignment/namespace/references、按需存储与 producer 区分、记录消费者差异 |
| 学习材料 | 10 道带答案练习；一个原创两 world 公共缓冲重置/快照例子；一个 MuJoCo reset 阅读片段 |
| 状态同步 | 中英 README、curriculum、roadmap、versions、source-map、独立 Warp manifest、Newton manifest 与本验收 |

## 实际检查

检查解释器为 **Python 3.12.12**，只使用 stdlib 文本/AST/哈希，不 import 教学代码或原生引擎。

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

- 文档相对链接和 whitespace 通过。
- AST：全仓 **7 个教学 Python 文件、3 个 Markdown Python 片段**通过，均未执行。
- [Newton 来源清单](sources.json)：**106 个文件**，本章新增 **7 个**，Git blob 与固定官方 tree/下载 bytes 一致；全仓 **456 个 Newton blob 链接** revision、登记与行号范围通过。
- [Warp 独立清单](e5-warp-sources.json)：官方 v1.18.0 的 annotated tag object、peeled commit、完整 tree 与 **6 个被引用文件**的 Git blob/SHA-256/行数核对通过；全仓 **20 个 Warp blob 链接** revision/登记/行号范围通过。未把 Warp 文件放进 Newton manifest。
- E3 独立 MuJoCo-Warp 依赖清单的 **3 个文件、13 个链接**重新核对通过，保持独立身份，未修改该清单。
- 首次来源检查发现 Control.clear 的链接末行写成 120，超过该文件实际 117 行；已修正正文/源码地图两处锚点并重新通过全部来源检查。
- 人工语义审查核对本章源码锚点、下标/单位、重置所有者、官方示例时间算式与 graph 范围、record/playback 实际读写。原生最小例子只采用两份单标量关节的明确条件，未扩展为通用 reset。
- 本章块公式使用 `$$`；未做浏览器渲染/视觉验收。内容 SHA-256 见 [e5-validation.json](e5-validation.json)。历史 E1–E4 的 manifest 摘要是当时快照，不代表本轮来源清单。

## 保留的源码发现与边界

1. **同名 reset 不代表同一语义。**基类/XPBD 无公共状态恢复；Newton 的 SolverMuJoCo 以 joint 为主，Warp 分支清选中后端持久输入/历史，native CPU 只在选中 world 0 时清其唯一 MjData；VBD 以 body/particle 为主。`Control.clear(model)` 无 world mask；使用 `clone_variables=False` 共享默认控制，不能拿该对象充当初值快照。
2. **固定官方 policy 时钟存在差异。**每次 step 的实际物理提交是 D=4、S=1、h=0.005 s，共 0.020 s；sim_time 只增加 0.005 s。课程据控制流推导并提示数据时间来源，未修改或运行上游。
3. **Warp 1.18 已有 CPU graph，仍是实验性接口。**Newton policy capture 条件含 CPU；它只捕获 simulate，未捕获整个策略推理循环。graph 不重放任意 Python，双缓冲和保存历史必须处理地址所有权。
4. **ViewerFile 不是完整续算 checkpoint。**record 克隆顶层 State 数组，跳过 namespace，Model 是引用，payload 没有逐帧时间/Control/solver/RNG/policy 信息；playback 直接赋 history 数组，之后原地修改可能污染历史。保存方法捕获异常且只在 verbose=True 时打印；公开 save_recording 默认 False，失败可能静默。调用返回不证明文件完整写入。
5. **固定源码身份不代表装配/运行资格。**Warp 采用独立官方版本作为 API 解释基线，没有以安装版本或兼容性验证名义呈现；外部 warp_nn、Torch、Isaac Lab 的安装与完整实现未审查/验收。
6. **例子只恢复本模型存在的公共 joint/control 数据。**没有 solver，因此不掩饰内部缓存/接触重建的缺项；清 Contacts 使全批次接触失效，不能读取旧力。CPU `.numpy().copy()` 产生独立 host 值，仍不构成包含所有所有者的 checkpoint。

## 未开展与后续

没有原生 import、模型/后端编译、JIT、示例执行、物理/碰撞/渲染、策略推理、训练、基准、性能计时、数据集采集或文件回放执行。没有获得实际轨迹、跨设备确定性或 sim-to-real 证据。课程来源覆盖本章追踪路径，不等于整个 Warp 或所有后端已经完整审查。

E6 接续专用 solver/耦合/扩展及完整可微链，E7 做双路线综合审校；正式实验复用 DexLab。本子任务只完成本地提交，等待主任务独立审查后处理远端交付。
