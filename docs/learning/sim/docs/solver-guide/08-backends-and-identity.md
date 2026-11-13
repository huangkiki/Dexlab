# 8. 后端、精度和实际执行身份

[教程目录](README.md) · [上一章：对象与实现](07-representations.md) · [下一章：六引擎逐行解读](09-engine-configurations.md)

配置保存了 `Newton / CUDA_GMRES / FP64`，机器也有 GPU。这仍不能证明这次接触求解用了 GPU 双精度。需要追踪请求、分派、实际调用与观测。本章承接外层/内层知识，帮助你读 CPU、CUDA、并行、AUTO 和资格状态。

## 用四层证据回答不同问题

| 证据 | 可以回答 | 不能直接回答 |
|---|---|---|
| 枚举/参数存在 | 可以写下什么请求 | 当前构建是否支持 |
| 构建、依赖与准入检查 | 当前二进制接受什么 | 本次实际走哪个分支 |
| 有效配置与执行读回 | 本次执行了什么、在哪个设备 | 对目标任务是否准确 |
| 有效观测与固定协议 | 在限定条件下是否满足验收 | 所有任务或真实材料都可靠 |

API 读回 `AUTO` 只读到了选择规则的名称。若没有分支遥测或可核实的调用路径，不能把它登记为某个具体算法已执行。

## SuperDex 的线性选项逐项定位

完整原生参数、源码和 wheel 边界见[固定 SuperDex 导读][superdex]。以下按角色帮助阅读，不提供未经测量的性能排名。

| 登记名称 | 阅读重点 |
|---|---|
| CG | 线性迭代问题与矩阵假设，区别于 MuJoCo/Genesis 非线性 CG |
| GMRES / MINRES | 一般系统与对称系统的方法背景；实际实现、重启和预条件限制 |
| LDLT / LU | 直接分解路径；pivot、对称性及存储支持不能从名称补全 |
| ASYNC_CG | 追踪异步实现和调度，不能仅凭名称宣称后台并行已经发生 |
| PARALLEL_CG | 追踪并行实现、线程与调用者；并行不等于 CUDA |
| AUGMENTED_CG | 查固定实现中增广的含义和状态；不是只增加普通 CG 的轮数 |
| CUDA_CG / CUDA_GMRES | CUDA 实现请求；确认 wheel、精度和构建准入 |
| EXPERIMENTAL_CUDA_SPARSE_CHOLESKY | 实验性 CUDA 稀疏 Cholesky 选项；确认矩阵与构建条件 |
| EXPERIMENTAL_CUDA_SPARSE_LDLT / EXPERIMENTAL_CUDA_SPARSE_LU | 对应实验性 CUDA 稀疏分解选项；名字不是可用性证明 |
| AUTO | 固定源码按 island 规模分派，不能当第十四种线性算法 |

冻结 SuperDex 源码的 AUTO 在 island 自由度不超过 50 时选 LDLT，否则选 CG；它不因为机器有 GPU 就自动选 CUDA。冻结报告还记录特定 1.0.0 FP64 wheel 对五种 CUDA 选项的步进前拒绝。这是特定构建的证据，既不能写成“这些选项已在 GPU 成功运行”，也不能外推到所有将来构建。[来源和边界][superdex]

## FP64 改变什么，不能改变什么

浮点精度影响可表示数字、舍入和线性代数误差。在 IEEE 754 binary32 的常用舍入下，$`2^{24}+1`$ 无法表示为独立于 $`2^{24}`$ 的相邻整数；binary64 能精确表示它。这是数值表示例子，不是物理引擎的测量。

更高精度可能帮助数值敏感问题，但不能修复错误的质量、单位、碰撞几何或材料假设。还需确认状态、矩阵、接触生成、设备 kernel 和输出是否使用相同标量类型；一个包名或输出数组 dtype 不证明所有中间步骤都为 FP64。

<details><summary>进阶：为什么舍入误差会被放大？</summary>

在线性问题满足相应小扰动条件时，相对解误差的估计与矩阵条件数及输入/运算扰动有关。病态矩阵可能放大很小的扰动；这并不意味着每个实际误差都达到该上界。缩放、预条件、模型/约束结构与精度是不同工具，不能只把所有问题归咎于浮点位数。

</details>

## 包装层与历史未知身份

`SolverMuJoCo` 可以指向包装或后端连接路径，不能仅凭名称认定具体原生 core、CPU/MJWarp 或求解选项。Newton Physics 的 Kamino、DVI、PADMM 也需要分别记系统与动力学后端，详见[Newton 导读][newton]。

`algorithm unqualified`、`pending qualification`、`historical readback incomplete (#126)` 与 `not qualified` 是证据状态。未知不是默认值；未资格也不等于从未运行。比如冻结 Drake 斜面报告保留通过与失败，但仍未达到 coverage-v1 资格。[Drake 证据解释][drake]

## 复现卡与练习

复现卡记录：源码 commit、包和 core/binding 身份、构建选项、设备、实际标量类型、请求配置、有效配置、执行分支、物理协议与观测文件。缺项明确写未知，不以当前版本默认值回填旧批次。

1. **GPU 可见且参数返回 CUDA_CG，足以证明执行了吗？** 不足；还需构建支持、准入结果和实际执行证据。
2. **AUTO 读回成功能把本次登记为 LDLT 吗？** 不能单凭读回；核对该版本分派输入与实际分支，并标清证据来自源码推断还是运行遥测。
3. **相同场景切 FP64 后任务通过，能证明 FP32 不适合该引擎吗？** 不能泛化；保留受控条件、有效观测、复现和误差原因，再界定结论范围。

## English summary

Requested labels, build support, executed branches and task qualification are separate evidence layers. All registered SuperDex linear options have distinct reading targets; AUTO is a dispatch rule. FP64 changes numerical representation, not material correctness. Preserve unknown historical identities and distinguish source inference from runtime telemetry. This lesson performs no device or engine execution.

[superdex]: https://github.com/huangkiki/superdex-learning/blob/3ea8d7e2d057052892917daf4bad9838e4b5c08b/docs/solver-reading-guide.md
[newton]: https://github.com/huangkiki/newton-learning/blob/68bee77269d2f63c458bb2ece11de77ec08b4b77/docs/solver-reading-guide.md
[drake]: https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md
