# E6 验收与后续任务

对应 [Issue #7](https://github.com/huangkiki/genesis-atlas/issues/7)，从已发布 E5 的 main `23757e16d14e9895cbb3abfae0f3c9d599a53b6b` 开始；本地与 origin/main 一致、工作树干净，E3 文档及提交祖先已核实。实现分支 `docs/e6-extensions-boundaries`。记录日期：2026-10-09。

交付 [多物理、可微与扩展边界](extensions-boundaries.md)及原创 [extensions_api.py](../examples/extensions_api.py)，更新中英 README、导读、课程、roadmap、源码地图和 manifest；保留 Sim Atlas 系列首页。第三方源码只留独立阅读缓存，没有复制到仓库。原创接口片段沿用本仓 Apache-2.0 许可。

## 覆盖与边界

| B6 / B7 要求与 E3/E4 衔接 | 实际交付 |
|---|---|
| 实体与求解器 | 第1–2节：最派生 material 分派、active 条件、统一子步及 pre/couple/post 调度；区别类名与执行消费者 |
| MPM | 第3节：F/C/Jp、p2g/grid/g2p、E/ν/Lamé、Elastic/Liquid/塑性/Snow/Sand/Muscle及CPIC/梯度条件 |
| SPH/PBD | 第4节：WCSPH压力、DFSPH循环与跨B停止尺度；位置约束、compliance/relaxation、实际volume表达式与反向缺项 |
| FEM | 第5节：体/面网格、显式应力与隐式energy/Hessian消费者、model支持集合、顶点约束与Muscle/IPC区别 |
| 耦合器 | 第6节：Legacy有效组合和前后顺序、SAP门槛、IPC外部CUDA world/本构/状态所有权及局部reset/梯度限制 |
| 特色实体 | 第7节：Hybrid实际Rigid+MPM包装与反向缺口；SF jets激活、普通实体分派/批量/状态接口限制 |
| 可微内部 | 第8–9节：gs.Tensor身份、detach/sceneless/from_torch、输入/输出桥、窗口重算、Scene.backward、active-set伴随及Newton/CG分支 |
| 热与触觉专项 | 第10节：FFT热扩散、接触换热、辐射/对流量纲疑点、RC；Elastomer直接/FFT核、厚度谱及剪切历史 |
| 原生/外部扩展 | 第11–13节：Subscriber/mutates、force_field实际消费者、材料/solver契约、IPC/渲染/RL外部身份、batch状态与共享拓扑 |
| 阅读与例子 | 18题附答案；2个原生接口函数，损失保留梯度桥、订阅返回lazy handle；正有限长度尺度校验 |

**没有原生 import、模型编译、JIT、物理/渲染/反传、训练、实验、性能基准或评分器。** 本章的“有路径”来自固定源码调用追踪，不是运行通过矩阵；有限差分梯度验收、组合资格、物理标定和长期稳定性均未做。外部 pyuipc/libuipc、Quadrants、Madrona/Luisa、RSL-RL 等核心构建与实现没有因 Genesis adapter 被引用而获得验收。完整 A0 安装与 E7 双路线综合审校仍待开发；实验继续复用 DexLab。

## 静态检查与自审

| 检查 | 状态 | 证据含义 |
|---|---|---|
| `git diff --check` | 通过 | 空白与冲突标记 |
| `python scripts/check_docs.py` | 通过 | 全仓 Markdown 相对文件链接 |
| Python AST / 完整 Python 围栏 | 通过：7个Python文件、1个完整围栏 | 只解析语法，没有导入或执行示例 |
| 固定SHA、manifest、Git blob/tree、行锚点 | 通过：119个blob、511个固定源码链接 | 所有来源哈希、固定提交、收录、实际行范围及reference定义 |
| 选定源码分支复核 | 通过：23项AST/表达式检查 | SPH/PBD空反向/ckpt、SF分派、FEM/SAP/IPC缺项、DFSPH归约、伴随分支与热流参数；不是数值测试 |
| 原创既有URDF静态回归 | 通过：3 links、2 joints及box惯量 | 没有加载引擎或运行模型 |
| GitHub Markdown API | 通过：9个块公式均生成display math-renderer | 使用 `$$`；仅GFM标记渲染，非浏览器像素或native渲染验收 |
| 原生调用/派生实现与公式自审 | 已完成，最终独立主审待执行 | 检查入口与消费者、pass/raise、循环与反向、shape/单位和实际参数传递 |

新增23个实际引用的固定源码文件到 manifest，全部119份缓存重新计算 Git blob SHA1，对照官方固定 tree 与 sources.json。第一次引用生成检查发现 SF/FEM.Elastic 两个末行超过实际文件结尾，已收紧后重跑；最初 Markdown 统计误把 inline 数学也计入 display，改按 `js-display-math` 类区分后确认9个块公式。没有以失败检查作为通过证据。

自审补充了 Newton 按 island 复用 Cholesky 与无约束环境/CG 求解路径的区别；`gs.from_torch` 默认 detach、MPM静态材料/粒子INFO共享和动态状态B轴分别说明。损失长度尺度同时拒绝非有限值和非正值。温度辐射/对流结论仅为声明单位、ρc_p构造与调用参数下的源码量纲疑点，没有扩大为已证实的数值失效。

## 固定版本发现与下一项

- `FEM.stable_neohookean` 原生隐式gradient/Hessian未实现；`linear_corotated`显式stress未实现；Muscle主动项只加在stress消费者。
- `FEM.Cloth`注释与IPC消费者不同，实际为StrainLimitingBaraffWitkinShell；体积IPC使用StableNeoHookean，不复用原生model分派。
- SF普通material分派无消费者，内部靠jets激活，batch明确拒绝；SPH/PBD的关键梯度与checkpoint接口为空。
- SAP明确拒绝couple梯度；IPC couple_grad为空、局部reset拒绝、batch INFO不兼容，运行期Genesis gravity写入未被外部world消费。
- DFSPH误差跨粒子×B求和却只除n_particles；PBD volume表达式与通常inverse mass/gradient分开使用的推导不同，未认证为标准XPBD。
- Legacy的MPM网格操作含基础推进与外场；force_field登记不等于所有solver均消费；特殊约束/Hybrid追加更新也不能由通用backward接口自动推导。
- TemperatureGrid有表面热流/体热容量纲疑点，ElastomerTaxel含布局近似与剪切历史；均不是通用热力耦合或FEM变形真值。

建议下一项 **E7**：完成 A0 安装、双路线综合审校、固定源码/注释差异清单与 DexLab 复用索引；待本切片主审发布后领取。按当前分工只做本地提交，不推送、不改远端 Issue/Project、Obsidian、总仓或其他引擎仓库。
