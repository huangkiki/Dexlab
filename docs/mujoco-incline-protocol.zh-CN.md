# MuJoCo 斜面 solver 准入

[English](mujoco-incline-protocol.md) | [简体中文](mujoco-incline-protocol.zh-CN.md)

这是六引擎研究的 MuJoCo 独立子项 [#146](https://github.com/huangkiki/Dexlab/issues/146)，接续[历史配对协议](incline-comparison-protocol.zh-CN.md)，保留全部物理阈值。增加步长、solver 或运行路径不增加任务类型。本轮解析准入与 coverage-v1 的等额调优、冻结留出集验收分开。

冻结官方 MuJoCo 3.15.0、Python 绑定 3.15.0、CPU float64，源码 `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`。采集前核实最新稳定版；实际加载库和安装代码必须匹配官方 wheel。[原生枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjtype.h)及[分派实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_forward.c)登记 PGS、CG、Newton；本批分别覆盖 elliptic 与 pyramidal 摩擦锥，固定 Euler 积分以保持历史力／速度区间。其他积分器不标为“不支持”。框架与 MJWarp 准入继续由 [#152](https://github.com/huangkiki/Dexlab/issues/152) 承接。

每个正例使用自由的 40 mm、64 g 均匀方块，重力 9.81 m/s²，静止且底面恰好接触斜面，运行 2 s。静态 15°/μ=.5、滑动 35°/μ=.5、名义零摩擦 15°，各运行 2/1/.5 ms，共九例。冻结 100 次迭代、1e-10 容差、solref [.02,1]、恒定阻抗 .9、impratio 1，以及原有阈值和 .5–2 s 评分窗。相同求解预算不代表相同收敛程度。相同优先级几何的摩擦取最大值，本实验两侧输入相同；名义零摩擦可能被原生引擎截断为微小正值，按实测报告。[固定版本组合实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_collision_driver.c)。

每个配置另需一例 2 s、1 ms 的静态负对照：关闭平面的碰撞掩码。模型中平面仍存在，但不能提供支撑。有效自由落体必须被原有物理评分拒绝；不把缺少支撑改写为零摩擦观测。Euler 采集读取积分前求解留下的力与接触坐标，状态在积分后读取。独立评分重构每个接触力，与广义接触力、加速度通道核对，保持原有 1e-7 N·s 动量一致性限制。

复用身份和协议匹配的九例 Newton/elliptic 历史正例。v0.46.0 原始包包含阻抗 .9/.99 的全部 18 例；未选入本轮的 .99 失败也保留。原始包中的源码副本是后续 recorder，campaign 保存的是最初 recorder 哈希；从提交 `0904240e594f4e1fabb2bd908a32af830afa84b2` 恢复完全匹配的原始源码，不覆盖旧包。历史安装代码与本次官方 wheel 匹配，但当时未记录加载库映射、逐接触账本和资源压力，新观测不能补写历史字段。复用前对每份原始 XML 做零步准入，并与新配置的原生读回比较。

保存输入 XML、编译导出、最终有效参数、几何／质心／惯量／坐标、逐接触距离／坐标／力／材料、力时刻、警告、实际迭代数和 arena 使用量。导出后重新编译，单独报告精度损失；物理运行始终使用原始输入，不使用可能有损的导出文件。本批不修改引擎，不调参，不在初始化后写状态，不改变物理容差。

初始采集预算为六次串行启动：五个缺失配置各九正一负，再补 Newton/elliptic 负例。零步准入、环境准备与正时长采集分开记账；新增诊断须另立假设和工作包。本次 recorder 未知负载冻结 16 GiB／4 核等效配额，启动另留 8 GiB 桌面余量、关闭 swap，保留内存压力、CPU 限流、显存和 I/O 观测。分别记录原生推进、读回和整条命令耗时，不与历史记录做速度排名。中断保存真实长度和异常，不填零冒充完整实验。

机器可读清单位于 `docs/evidence/mujoco-incline/`。完成官方 wheel 与资源准入后，复现一个缺失配置：

```sh
python -m dexlab.incline_run \
  --manifest docs/evidence/mujoco-incline/pgs-elliptic.json \
  --proof official-proof.json --output pgs-elliptic
python -m dexlab.incline_score --input pgs-elliptic --output pgs-elliptic-score.json
```

附加 `--admission-only` 做零步核对。原生命令使用仓库资源限制和研究锁。完整回归、合并和部署证据核验前，评分仍为待交付结果。
