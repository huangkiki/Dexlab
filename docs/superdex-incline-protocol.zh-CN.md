# SuperDex 斜面协议 v1

[English](superdex-incline-protocol.md) · [结果](superdex-incline-results.zh-CN.md)

#147 以历史 Newton/AUTO/C1 为中心逐项切换 solver，使用官方 SuperDex 1.0.0 FP64／API，固定构建源码 `1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`，批次前核验最新官方 wheel 与实际加载库。五个 CUDA 枚举在时间推进前被原生构建检查拒绝；十二组 CPU 配置通过零时长准入。这不是非线性、线性、摩擦与积分器的完整笛卡尔积搜索。

均匀自由方块边长 40 mm、质量 64 g，初始静止且底面贴合无限平面，g=9.81 m/s²。工况为 15°／μ=.5 静态、35°／μ=.5 滑动、15°名义零摩擦；步长 2／1／.5 ms，各 2 秒。Backward Euler，非线性上限 100 次、绝对／相对容差 1e-9；其余全部有效参数随配置保存。线性 AUTO、max_iter=-1 与容差策略保留原生语义，不代表工作量相等。非线性覆盖 Newton／BFGS／SR1；CPU 线性覆盖 AUTO／CG／GMRES／AUGMENTED_CG／LDLT／LU／ASYNC_CG／PARALLEL_CG／MINRES；另一组单独切换 C∞ 摩擦。看到结果后不调参。

罚系数 1e9 Pa/m，阈值 1e-4 m，平滑半距 5e-5 m，摩擦衰减速度 1e-3 m/s，法向与黏性阻尼为零，两物体摩擦系数相同。源码使用几何均值组合库仑系数；逐接触接口不暴露有效组合律。这些是数值参数，不是材料标定。原阈值与 0.5–2 秒窗口不变，包括 1e-7 N·s 力／状态一致性限制。[原解析假设与限制](incline-comparison-protocol.zh-CN.md)。

每组增加一个 15°／μ=.5／1 ms 的负例，在双方向禁用 actor 接触对，但保留平面资产；另检查观测力／接触数为零、速度符合纯重力。无效负例不能准入。AUTO/C1 九个正例只在归档哈希、协议身份与九个原生读回一致后复用；历史缺失字段不会变成新观测。

预算为十二次串行启动，99 个新正例＋12 个负例，255,000 次更新；每组进程上限 120 秒、工作包六小时。批次冻结 16 GiB／四核等效配额，启动留 8 GiB，禁用 swap。记录成本包含完整读回与中断保存；不消耗正式夹持预算。评分、完整回归、归档分别记录资源。原始归档包含冻结清单和采集源码哈希。

```bash
# Run only under the repository's bounded resource and research-lock wrapper.
python -m dexlab.incline_compare_run --manifest docs/evidence/superdex-incline/profiles/newton-cg-c1.json --output /data/new-cg --admission-only
python -m dexlab.incline_compare_run --manifest docs/evidence/superdex-incline/profiles/newton-cg-c1.json --output /data/new-cg-physical
# Offline, after extracting dexlab-superdex-incline-v1.tar.gz:
python -m dexlab.incline_compare_score --profile dexlab-superdex-incline-v1/campaign-v1/newton-cg-c1 --output cg-score.json
python -m dexlab.incline_compare_score --superdex dexlab-superdex-incline-v1/history/paired-incline/superdex --mujoco dexlab-superdex-incline-v1/history/paired-incline/mujoco --output historical-comparison.json
```

归档保留原始采集 manifest 与源码。公开 combined 协议／评分按来源连接历史 AUTO/C1 正例和新负例，不改写采集 manifest。独立评分先检查逐接触记录与原生总力矩，再应用原解析指标。六个 CG 系列无效正例仍计入分母，由 #159 继续归因。不增加任务类型或 coverage-v1 可靠覆盖数量。
