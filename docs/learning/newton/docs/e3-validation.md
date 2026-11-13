# E3 验证记录

对应 [Issue #4](https://github.com/huangkiki/newton-atlas/issues/4) 与[接触、求解器与力观测](contact-solvers-forces.md)。基线为已发布 E2 的 `25b6908a68a43c6f3238ea69688943701266ffbe`；开始时核实 origin/main、main 与此提交一致，工作区干净、没有在途 PR。当前记录描述本地交付，发布/CI/合入状态以对应提交与 Issue 为准。

## 要求与证据

| 要求 | 交付与审查边界 |
|---|---|
| A4 接触 API | 正文第 2–3 节：原生 pipeline/Contacts、过滤、margin/gap、材料组合与容量；保留记录与实际激活差异 |
| B0/B1 动力学与一步仿真 | 第 1、4、6 节：广义动力学、COM 预测、XPBD 位置/速度阶段、其他主要刚体 solver 的实际分支 |
| B2 接触模型与组合律 | 第 3–6 节：算术/几何/max/可配置材料组合、penalty、位置约束、恢复、hydroelastic 生成与消费者 |
| B3/B4 数值方法 | 第 4–7 节：有效质量、relaxation、迭代/子步、warm start、Cholesky/PADMM、MuJoCo 四种积分分支与真实终止条件、float/可微边界 |
| B5 力读回 | 第 5、8–9 节：输入/反力/冲量区别、producer、world/COM/side、时间平均、固定实现的缺口 |
| 练习与例子 | 10 道带答案阅读练习；1 个原创原生读回例子；1 个完整 Markdown 几何快照 Python 片段 |
| 完成状态 | 中英 README、curriculum、roadmap、versions、source-map；E4–E7 与专用 solver 扩展仍保留独立范围 |

## 实际静态检查

使用 Python **3.12.12**，检查脚本仅读取文本/AST，未 import Newton、Warp 或 MuJoCo：

```bash
git diff --check
python scripts/check_docs.py
python scripts/check_examples.py
```

- 全仓相对 Markdown 链接通过。
- AST 通过：全仓 **5 个教学 Python 文件**、**2 个 Markdown Python 片段**；没有执行任何教学函数。
- [Newton sources.json](sources.json)：**76 个文件**，本次新增 **24 个**；各文件按 Git blob 算法核对官方固定树与本地 bytes。
- 全仓 **294 个 Newton blob 链接**通过固定 revision、manifest 登记和行号边界检查。初检发现 SemiImplicit `step` 的链接末行写成 L216、超出实际 L215，已修正并重新通过。
- [独立依赖清单](e3-dependency-sources.json)：MuJoCo-Warp 3.12.0 官方 tag `v3.12.0` 指向 `087ac6f0ba9f33edb6bc284eb42aa6c3b16ef1f7`；三个源码文件分别与该 Git tree 的 blob、Newton uv.lock 指定 sdist 中的 bytes 完全一致；整个 sdist SHA-256 也核对通过。**13 个外部源码链接**的 revision/path/line bounds 通过。
- 内容 SHA-256 与检查范围见 [e3-validation.json](e3-validation.json)。E1/E2 记录是各自交付时的历史快照；本次公共 manifest 已扩充，不能将旧 manifest 摘要当作当前文件内容。

固定文件身份不意味着每行源码已经审查。人工自审重点是本章链接的调用链、量纲/符号、材料消费者、buffer ownership、终止和 readback；“整文件获取”与“分支语义核对”明确分开。

## 保留的源码发现

1. **XPBD 位置信息与恢复速度后处理分开。**位置循环的累计变量具 impulse 单位，读回除一次 dt；其后 restitution velocity pass 未回写该缓冲。读回不是包含全部恢复冲量的总冲击力；本次未运行冲击实验。
2. **XPBD count weighting 是近似。**两侧 1/N 独立缩放，读回使用倒数计数的调和平均 2/(N_a+N_b)。actual kernel 还按 body_id 而非动态质量筛选计数，有 ID 的 kinematic 与 world 静态侧要分开理解。
3. **接触力约定的 MuJoCo 固定组合缺口。**已锁定 helper 仅旋转 contact-frame force/torque；Newton adapter 取负但未换到 body0 COM。通用 Contacts.force 的 COM torque 契约在这一路不能无条件采用。前三维方向/side 已按源码核对；补换点公式写入正文，未修改上游、未运行修复验证。
4. **不同 producer 不能替换。**SemiImplicit/Featherstone 未 override 通用 update_contacts；VBD 有独立 collect_rigid_contact_forces，输出作用于 body1，且需要该步真实 previous pose；Kamino 则显式换 COM 并需 State。SensorContact 只消费线性部分，不能修补其他遗漏。
5. **材料组合/终止有版本边界。**XPBD 与 VBD 的 mu 组合不同；MuJoCo 的 priority/solmix、backend/contact source 和 ke/kd/kf 映射单列。XPBD 固定迭代、MuJoCo-Warp scaled improvement/gradient、Kamino PADMM 三 residual 的停止标准不可互换。
6. **MuJoCo 积分器与约束优化器分别核对。**固定后端先 forward，再走 Euler/RK4/implicit/implicitfast；Euler 的 damping 矩阵、RK4 中间态和两种速度隐式的导数/矩阵路径已展开。局部速度隐式不等于完整非线性位置/接触隐式求解，平滑 ODE 阶数不构成碰撞问题精度承诺。
7. **容量与采样不能隐去。**writer 计数可能超过已写容量；示例在 solve 前拒绝 overflow。读回前不重建/重排 Contacts，示例复制数据后才允许未来碰撞覆盖。

这些发现没有写入上游 Issue，也未被称为经运行复现的 bug 或对历史 DexLab 数据的判决。验证材料保留足够固定链接，供主审独立核对。

## 未开展与下一项

没有原生 import、执行教学片段、物理 step、仿真、benchmark、训练、评分器或性能/精度测量。source dependency 身份不是安装/ABI/运行配置身份。MuJoCo CPU 内部 C++、Kamino DVI 深层路径、Style3D/ImplicitMPM/耦合和完整可微实现留 E6；本章不称全面审查所有后端。

下一项优先 E4（传感、渲染与可视化），使 E5 满足剩余依赖；E6 已具备 E3 前置。外部实验最终复用 DexLab 的冻结版本/工况。当前子任务只本地提交，由主任务独立审查后处理发布。
