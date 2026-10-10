# Isaac Sim／MJWarp 开发诊断

[English](framework-mjwarp-diagnostics.md) | [简体中文](framework-mjwarp-diagnostics.zh-CN.md)

**接触读回已修正，三个任务的完整准入尚未完成。** 最终四个0.2秒诊断均正常退出，两个移除地面的负例通过冻结检查；两个支撑正例仍超过1e-7 N·s动量限值。可靠任务覆盖数不增加。[#152](https://github.com/huangkiki/Dexlab/issues/152)继续承接最新原生／匹配核心路径、显式资产对齐、碰撞、有限夹具夹持、重置及冻结留出。

## 冻结范围与版本

合成40 mm、64 g自由方块位于15°有限地板上方1 µm，摩擦.5、重力9.81 m/s²。每个独立进程执行200个1 ms步，单CUDA世界，Newton求解器／pyramidal锥，分别用Newton及MJWarp生成接触。每条路径各有支撑与禁用地板正负例。本批只诊断记录器，不属于旧斜面协议或新可靠覆盖验收；没有消耗正式调优和留出集。

Isaac Sim v6.1.0源标签的本地构建报告`6.1.0-rc.26+mr.0.7c206f75.local`，实际加载MuJoCo/MJWarp3.11.0、Newton1.5.0、vendor Warp1.16.0。前五个物理／转换包共1,390个文件与官方wheel一致；42个集成Python文件与官方标签一致。Warp的555个非二进制文件与PyPI一致，两个本地库虽与PyPI不同，但均与NVIDIA扩展原包一致。原包共核对701文件，只有生成的扩展元数据存在地址／格式差异。此结论不等于整套Isaac/Kit官方二进制认证。另对三个关键Python源文件核对了导入缓存代码与现场编译结果，未修改缓存。

每次物理运行前重新核对已加载MuJoCo与Warp库哈希。同版本不等于同二进制，后续匹配归因还要控制Warp构建。最新原生3.15.0及匹配原生路径仍待准入。[官方框架说明](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/physics/newton_physics.html) · [身份审计](evidence/framework-mjwarp/qualification.json)。

## 结果与失败

| 接触生成路径 | 支撑动量残差（N·s） | 原生接触合力残差（N） | 无地板读回 | 最终生命周期 |
|---|---:|---:|---|---|
| Newton | 7.8766e-7，失败 | 9.8245e-7，通过 | 通过 | 两次退出0 |
| MJWarp | 7.2076e-7，失败 | 9.4023e-7，通过 | 通过 | 两次退出0 |

接触合力限值保持1e-5 N。最终四例均通过时钟、有效步长、计数、容量和完整读回检查。200步后的GPU时钟误差2.265e-7秒，框架误差小于1.4e-16秒。编译CPU模型初始步长2 ms，框架为1 ms；实际GPU step读回1 ms。不能仅凭初始化参数判时钟错误。

`get_data_into`把检测到的接触连续排列成CPU约束地址，未正确保留不参与求解的接触。本次Newton第80步中，前两个接触GPU地址为−1，后两个从0、4起；CPU却排成0、4、8、12，而总共只有8个约束，后两项有效力因此被读成零。现在使用官方GPU `contact_force`接口，同时保存CPU表示、原生地址和约束力。独立NumPy金字塔解码与GPU力相差不超过2.24e-8 N。Newton有7/200帧、MJWarp有176/200帧出现CPU转换差异。Newton v1／v4的状态及广义力逐条完全一致，读回修复没有改变仿真轨迹。

动量失败仍独立存在。Newton最差样本的原生加速度／合力方程残差为7.8765e-4 N，求解器报告只执行1/100次迭代。停止原因尚未确立，不放宽旧限值，也不据此宣称引擎缺陷或真实材料精度。[完整分数与资源成本](evidence/framework-mjwarp/diagnostics.json)。

旧128任务上限会使初始化中断，仅限制四核affinity不能解决。新增显式256任务档，保留历史档位及冻结计划。首次正时长批次用24 GiB，实测峰值6.252 GiB，下一批依1.5倍规则选16 GiB；CPU仍四核等效，零swap，启动保留8 GiB。记录`pids.peak`，旧内核缺失则明确为null。耗时包括启动、观测和退出，不作为求解器吞吐排名。

早期负例完成记录后在退出时崩溃；改完整退出后停滞超过120秒，已停止所属进程。先关闭场景并处理10次app更新仍失败；再显式关闭异步渲染初始化，最终四例均干净退出。这只支持当前启动组合，不证明一般生命周期可靠性。全部20次启动、2,000次记录更新，包括最初10次零时长尝试，都保留在[开发历史](evidence/framework-mjwarp/development-history.json)。

## 证据与复现

[v0.56.0证据](https://github.com/huangkiki/Dexlab/releases/tag/v0.56.0)保留每代诊断及源码、原始USD、中间MJCF、精确MJB、最终参数、逐步接触读回、失败与资源回执。[压缩包身份](evidence/framework-mjwarp/archive.json)。公开导出仅遮盖本地路径及GPU UUID，逐文件记录原始／公开哈希；数值记录不变，未修改安装的引擎。

完整命令见[英文复现段](framework-mjwarp-diagnostics.md#evidence-and-reproduction)。使用已准入的官方兼容运行时、现有研究锁及冻结资源计划。命令在受限子进程内显式传入CUDA／Python路径；资源隔离器不会继承外层的这些变量。新建批次目录并写入单会话隐私设置后，四例复用冻结计划及缓存，各用独立输出、回执和Kit状态目录，物理测量与传输／评分串行。现场启动限制四个可用CPU、四个BLAS线程，关闭单会话vendor analytics，保留资源遥测；调用与回执保存了这些设置。复现先核对源码及二进制，再冻结等价启动设置。两个支撑例的评分器应返回非零；原生／框架三任务对照、重置和留出仍由[#152](https://github.com/huangkiki/Dexlab/issues/152)继续推进。
