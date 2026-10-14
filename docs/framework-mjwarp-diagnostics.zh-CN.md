# 原生／Isaac Sim MJWarp 开发诊断

[English](framework-mjwarp-diagnostics.md) | [简体中文](framework-mjwarp-diagnostics.zh-CN.md)

**匹配核心的原生路径也未通过支撑动量检查。** 显式对齐四项GPU参数后，失败仍存在，也未复现框架轨迹；三次独立原生进程的全部记录完全一致。这些是开发诊断，完整斜面／碰撞／夹持验收尚未完成，可靠任务覆盖数不增加。[#152](https://github.com/huangkiki/Dexlab/issues/152)继续承接最新原生路径、剩余有效状态差异、三个完整任务、重置及冻结留出。

## 冻结范围与身份

合成40 mm、64 g方块位于15°有限地板上方1 µm，摩擦.5、重力9.81 m/s²。各进程执行200个1 ms步，单CUDA世界，Newton求解器／pyramidal锥；框架分别使用Newton或MJWarp接触，原生使用MJWarp接触，均设置移除地板负例。保留1e-7 N·s动量限值；没有正式调优、留出验收或真实材料准确性结论。

Isaac Sim v6.1.0源标签本地构建报告`6.1.0-rc.26+mr.0.7c206f75.local`，加载MuJoCo/MJWarp3.11.0、Newton1.5.0、vendor Warp1.16.0。此前核对1,390个物理／转换包文件、42个集成文件及701个vendor原包文件，只有生成的vendor元数据差异；不等于整套Isaac/Kit认证。[框架审计](evidence/framework-mjwarp/qualification.json)。

原生路径直接加载框架的精确MJB，CPU参数读回完全一致；239个MuJoCo、281个MJWarp文件匹配官方wheel，684个所选vendor Warp文件匹配已审计NVIDIA原包。逐次核对实际加载库哈希，显式记录官方Newton的休眠策略编译转换，未修改引擎。最新原生3.15.0仍待执行。[匹配身份审计](evidence/framework-mjwarp/qualification-matched.json) · [官方转换／接触说明](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/physics/newton_physics.html)。

## 结果与归因边界

| 路径 | 最大支撑动量残差（N·s） | 无地板状态检查 | 完成进程数 |
|---|---:|---|---:|
| 框架／Newton接触／v6 | 7.8766e-7，失败 | 通过 | 2 |
| 框架／MJWarp接触／v6 | 7.2076e-7，失败 | 通过 | 2 |
| 原生匹配核心／原GPU输入 | 1.0071e-6，失败 | 通过 | 2 |
| 原生匹配核心／对齐四项GPU参数 | 7.7014e-7，失败 | 通过 | 4，含两次支撑重复 |

表中10个进程均完成200步并退出0。原生检查覆盖状态、时钟、容量和动量，尚未测量逐接触力验收；框架接触合力残差仍小于1e-5 N，独立pyramid解码误差不超过2.24e-8 N。采集成功不代表物理通过。[评分、资源与对照](evidence/framework-mjwarp/matched-core.json)。

55项所选GPU字段中，初始有四项不同：`body_iquat`、`body_inertia`、`body_invweight0`、`stat.meaninertia`。这直接说明CPU导入模型相同不足以证明有效GPU输入相同。方块惯量近似各向同性，惯量坐标四元数不同不能解释为巨大物理惯量误差。受控诊断只通过官方Warp数组对齐这四项，并保存来源哈希与前后值；此后初始化及第一步的55项值／类型及所选编译选项一致，**不代表所有模型字段和内部状态都一致**。

三次对齐后的原生支撑运行记录完全相同，动量失败相同；相对框架MJWarp路径，最大位置向量差8.0851e-5 m，最大线速度向量差.019214 m/s。无地板轨迹跨路径完全一致。因此四项输入差异不足以解释全部支撑分歧，数值失败也并非框架独有。状态同步、其他内部字段及求解行为继续在[#152](https://github.com/huangkiki/Dexlab/issues/152)隔离，尚不能归因于单一框架操作或宣称引擎缺陷。

200步GPU时钟误差2.265e-7秒，框架时钟误差低于1.4e-16秒。初始CPU模型步长2 ms，有效物理步长1 ms，不能仅据初始配置判断时钟错误。

## CPU接触读回纠正

该3.11.0工况的`get_data_into`会给含未激活GPU接触的CPU表示分配连续约束地址。保留的Newton第80步GPU地址−1,−1,0,4，对应CPU地址0,4,8,12，但只有8个约束。**越界地址得到的CPU力不可作为观测值。** v0.56报告把这些值解释为零／数值差异及合并统计的错配帧数，现由边界审计纠正；原始记录和旧版本完整保留。

v5在所有主要状态／力记录相同的情况下读出了不同的越界CPU值，剩余v5工况随即停止。v6调用CPU力接口前核对完整pyramid地址宽度，越界写`null`；离线审计也对旧文件实施同样判断。Newton支撑有22条越界接触，MJWarp有5条；合法地址中的错配分别为0和172帧。地址合法不代表它对应了正确接触，仍以原GPU力为准。四例的v4／v6主要状态、广义力、时钟及计数完全一致。

## 资源与完整历史

框架v6沿用根据6.252 GiB峰值选出的16 GiB／四核／256任务冻结档。原生匹配批次先用16 GiB，测得1.147 GiB峰值，下一对齐批次据此选8 GiB／四核／128任务。零swap、启动保留8 GiB；保存内存事件、CPU限流、压力、显存和I/O遥测。整进程耗时含初始化、缓存、观测与退出，不作求解器吞吐比较。

继承六小时／64次启动账本，累计33次启动、4,400次记录更新，保留初始化／退出失败、部分执行的v5及缺失`packaging`导致的零步原生失败；依赖仅补入本任务环境。旧v0.56交付不改写。[开发历史](evidence/framework-mjwarp/development-history.json)。

## 证据与复现

[v0.57.0证据归档](https://github.com/huangkiki/Dexlab/releases/tag/v0.57.0)保留全部诊断代次、冻结协议／源码、USD／MJCF／MJB、有效参数、原始状态／接触、失败与资源回执。[归档身份](evidence/framework-mjwarp/archive.json)。仅遮盖本地路径／GPU UUID，保存原始及公开哈希，不修改数值。

完整框架和原生命令见[英文复现段](framework-mjwarp-diagnostics.md#evidence-and-reproduction)。原生采用独立Python3.12环境、经核对的MuJoCo/MJWarp3.11.0及vendor Warp1.16.0，不把PyPI同版本视为二进制相同；安装NumPy与`packaging`。复用研究锁，批次内冻结资源、四核线程设置和缓存策略，各次输出保持独立。框架用v6配置；原生分别选择matched／aligned-v1及支撑／无地板工况。支撑评分应退出非零，这些命令尚不构成完整任务验收。
