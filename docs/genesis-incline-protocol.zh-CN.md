# Genesis 斜面协议 v1

[English](genesis-incline-protocol.md) · [结果](genesis-incline-results.zh-CN.md)

原生最新稳定版准入冻结为 Genesis 1.4.3，源码 `216a708e06124595521a9d36a51fae5393fd4ff8`，Quadrants 1.3.3。安装源码和实际映射的编译库与官方 wheel 一致。CPU FP64、确定性模式、种子 0、单执行／编译线程，每例新建单世界场景，显式启用 link／DoF 参数批存储。框架兼容路径单独处理，不修改官方引擎。

均匀方块边长 40 mm，密度 1000 kg/m³、质量 64 g、主惯量 1.7066666666666674e-5 kg·m²；初始静止，底面贴合无限平面，绕 +Y 旋转。世界重力 [0,0,-9.81] m/s²，局部 COM 为零、六个自由刚体 DoF。15°／μ=.5 静态、35°／μ=.5 滑动、15°名义 μ=0，各取 2／1／.5 ms 步长、持续 2 秒。评分窗口 .5–2 秒；[原解析方程与阈值](incline-comparison-protocol.zh-CN.md) 不变，包括 1e-7 N·s 一致性限制。

官方 Newton／CG、elliptic／pyramidal、convex／Signorini 枚举形成五种适用组合；Signorini 要求 Newton／elliptic。固定 approximate_implicitfast、迭代上限 100、容差 1e-9、noslip0，禁用扭转／滚动摩擦；elliptic 的 impratio 为 100，pyramidal 为 1。保存全部有效选项和静态内核开关，不进行积分器／设备／调参笛卡尔积搜索。

步进前把两几何的 sol_params 设为 [.02,1,.9,.9,.001,.5,2]，保留构造器值和 setter 后有效值。接触参数取两几何均值，时间常数最低为 2dt；显式 .02 在本次步长扫描中不会被该下限改变。接触摩擦取两几何缩放摩擦与 .01 的最大值。名义零摩擦同时保存输入 0 和接触 .01，原模型匹配判为失败；有效模型诊断另列。同名数值不代表跨引擎材料等价。

每组增加 15°／.5／1 ms 负例：平面碰撞掩码为 1，方块为 2，两几何保留但没有可接触对。要求接触数／力为零且运动符合重力。开发时全零掩码会使原生构建移除几何，因此在正式物理前改为不相交的非零掩码。

接触法向指向 B→A，记录的力作用于 B；逐接触合计须与独立的方块净接触力 getter 一致。力与积分前接触几何属于刚完成的同一步，状态时钟来自 scene.get_time()。先核验时刻、几何、有效摩擦／sol_params、原生错误、接触数和动量，再评分。初始化后不写入状态；中断记录保存真实完成长度和尝试次数，不补零。CPU 原生循环不暴露实际迭代次数，不能用图执行计数器冒充。

采集预算为五次串行启动、50 回合、115,000 次更新，每组最多 600 秒，批次最多一小时，纳入独立六小时开发包。未知正时长峰值从 16 GiB／四核配额起步，禁用 swap、启动留 8 GiB。诊断前缀另行冻结并记资源，不能替换原评分；不消耗正式夹持 700 次预算。全部几何／选项准入在查看结果前完成，未按结果修改阈值。

```bash
# Native commands require the bounded resource/research-lock wrapper.
python -m dexlab.genesis_incline --protocol docs/evidence/genesis-incline/profiles/newton-elliptic-signorini.json --proof docs/evidence/genesis-incline/official-proof.json --output /data/admission --admission-only
python -m dexlab.genesis_incline --protocol docs/evidence/genesis-incline/profiles/newton-elliptic-signorini.json --proof docs/evidence/genesis-incline/official-proof.json --output /data/physical
# Offline, after extracting the raw archive (NumPy only):
python -m dexlab.genesis_incline_score --input dexlab-genesis-incline-v1/campaign-v1/newton-elliptic-signorini --output score.json
# Separately budgeted diagnostic prefixes:
python scripts/diagnose_genesis_incline.py --input dexlab-genesis-incline-v1/campaign-v1/cg-elliptic-convex --case static-h0.001 --output /data/diagnosis-100
python scripts/diagnose_genesis_incline.py --input dexlab-genesis-incline-v1/campaign-v1/cg-elliptic-convex --case static-h0.001 --iterations 1000 --output /data/diagnosis-1000
```
