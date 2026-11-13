# E6 验证记录

对应 [Issue #7](https://github.com/huangkiki/newton-atlas/issues/7) 与[特色求解、可微路径和原生扩展](extensions-boundaries.md)。基线为已发布 E5 `57d4da2ce4fba30cf3663893e2d9cbc4fc6accb6`；E3 前置已在该基线中，开发与恢复时核对分支、工作区、Issue OPEN 和无在途 PR。沿用 `docs/e6-extensions-boundaries`，没有覆盖中断首稿。本记录是本地源码/静态交付证据，远端发布和 CI 以实际提交为准。

## 范围与交付

| 要求 | 本次内容 |
|---|---|
| 原生扩展 | force/custom attribute/SolverBase/CouplingInterface 的责任；基类拒绝与 no-op；solver-owned 碰撞调度 |
| 特色动力学/材料 | SemiImplicit 与 VBD 的 tet 实际力/能量差异、VBD block/ROD、Style3D PD/PCG 与输入修改 |
| 多物理 | ImplicitMPM 的材料字段、FEM/流变/粒子链、隔离与 history/reset/graph；Kamino DVI 分块迭代与 Moreau |
| 原生耦合 | experimental 命名空间、ModelView/ownership、hooks；Proxy 的反馈/重启与 ADMM 的真实更新/支持边界 |
| 可微 | 初态/参数/控制的完整离散链式法则，Warp Tape 生命周期、前向值保存、冻结接触与禁用反传分支 |
| B7 综合 | 原生 Builder→Model→State→DrivePD→collision→XPBD→力读回→sensor/data 的字段、消费者与时序追踪 |
| 学习材料 | 12 道有答案练习；原创线性阻力例子，推导初速度与阻力系数的解析梯度，未执行 |
| 同步文件 | 中英 README、guide、curriculum、roadmap、versions、source-map、来源清单及本记录 |

## 实际静态检查

解释器为 **Python 3.12.12**。所有检查仅读取文本、Python AST 或哈希，不导入教学示例/原生引擎。

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

- 相对 Markdown 链接和 whitespace 检查通过。
- 全仓 **8 个教学 Python 文件、3 个完整 Markdown Python 片段**通过 AST；没有执行其 import、装饰器或函数体。新增例子另以固定源码 AST 检查 **9 个原生方法签名**，并核对 State 的 force 梯度存储分配。
- [Newton manifest](sources.json) 共 **124 个文件**，本章新增 **18 个**。下载 bytes 的 Git blob 与固定官方完整 tree 一致；全仓 **554 个 Newton blob 链接**固定 commit、登记路径和行号范围通过。
- [E6 Warp 独立清单](e6-warp-sources.json) 新增 **2 个文件**，与 [E5 的 6 个](e5-warp-sources.json)合计 **8 个**。官方 v1.18.0 tag object、peeled commit、完整 tree、各文件 Git blob/SHA-256/行数通过；全仓 **25 个 Warp 链接**固定 revision/登记/行号通过。Warp 未混入 Newton manifest。
- 既有 [E3 MuJoCo-Warp 独立清单](e3-dependency-sources.json)的 **3 个文件、13 个链接**重新核对通过，未修改该清单。
- 首次源链检查发现 SolverBase 引用末行 648 超过文件实际 644 行；修正正文与 source-map，重新通过全部来源检查。先前 scratch 文件路径定位失误与一次未匹配的编辑未改变仓库内容。
- 人工逐式/逐 consumer 审核包含量纲、VBD guard、MPM 调度与隔离、Proxy 同区间重启、ADMM 忽略/拒绝分支、Tape 梯度所有权及原生例子的假设。主任务预读指出的公式前提与引用范围已修正；最终发布仍待主审。
- 块公式使用 `$$`；没有浏览器视觉验收。正文、例子和清单 SHA-256 见 [机器可读记录](e6-validation.json)。E1–E5 验收记录保持历史快照，其旧 manifest 摘要不是本次清单的摘要。

## 保留的源码发现

1. **共同接口不保证共同执行。**SolverBase.step/update_contacts 抛未实现，其他基类 hook 有 no-op；SemiImplicit 肌肉调用处于禁用分支。原生力扩展要先找实际消费者。
2. **材料名称不构成同一离散模型。**SemiImplicit tet 偏量有特定因子；VBD 变换 Lamé 参数，alpha 分母有 guard，Hessian 抵消仅成立于单顶点 block。公式明确其假设，未做材料对照实验。
3. **隐式后端的数据与停止语义不同。**Style3D 原地改 state_in，PCG 采用固定预算。MPM 使用 FEM 网格、材料历史与内部 collider，忽略外部 Control/Contacts；普通 particle_f 未进入所核对的网格初速装配。默认共享网格，隔离模式才拒绝 global dynamic collider；reset 不恢复粒子 q/qd。
4. **DVI 与 PADMM 残差不能按同名直接比较。**PADMM 将预条件变量残差换回物理约束单位，DVI 用 cone/dual-cone 距离等定义。Moreau 的中点推进与 solver 选择独立，模块禁用反传。
5. **耦合存在明确缺项。**Proxy 的通用动量差反馈是近似，迭代重解同一区间。ADMM 跳过 FREE/DISTANCE attachment，拒绝 PRISMATIC/D6 等类型；full-surface 记录要求一个受支持 entry 拥有全部角点，跨 entry 记录会丢弃。没有把这些情形写成自动支持。
6. **梯度是整个离散函数的性质。**状态独立缓存与可导消费者都必要；retain_grad 不恢复覆写值。冻结 contact set/normal 仅有局部 kinematics 导数，Proxy/ADMM 多个 kernel 禁用 backward。初速度梯度走初态链式项，阻力系数走动力学参数项。
7. **身份和语法不等于装配与数值验收。**Warp 仍是独立的源码阅读基线；没有证明本机安装、Newton/Warp 组合兼容、梯度精度、稳定性、收敛或性能。

## 未开展与后续

没有 native import、模型/后端编译、JIT、示例执行、碰撞/物理/渲染、策略推理、训练、基准、数值梯度/finite difference 或视觉 QA。没有轨迹或物理结果，源码清单不等于全引擎全路径审查。

E7 仍待完整 A0 安装专题、两条路线总审校与 DexLab 原始版本/工况证据索引。正式实验复用 DexLab，本子任务没有开始 E7、推送或修改远端 Issue/Project。
