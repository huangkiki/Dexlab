# 研究经验：从已有实验到下一次验证

每条经验保留条件、观察、解释、建议、边界与证据；内容由版本化索引生成，并检查报告及数据摘要的 SHA-256。原始轨迹从各报告链接的不可变版本下载，按其清单复核。这里没有新留出或新增可靠覆盖。

<!-- research-experience:start -->

(normal-response)=
## 静态校准有效，质量迁移仍需检查

**条件：** 40 mm 方块，0.2 kg，0.5 ms；2/4/6/−1 N 加载。20 kN/m 是合成响应目标。

**观察：** MuJoCo 初始响应约 80 kN/m；校准后接近 20 kN/m。固定参数迁移到 0.1/0.4 kg 后约为 10.01/40.04 kN/m；事前约定的质量补偿后为 20.04/19.93 kN/m。

**解释与证据等级：** 已验证：该夹具的参考加速度约束响应与质量和阻抗有关。同名刚度参数不等于跨引擎等效材料刚度。

**建议：** 先用已声明的载荷段检查有效响应，再按明确假设做参数转换，并独立验证其他载荷与质量。

**边界：** 仅适用于此恒定阻抗、四点面接触夹具；不是任意几何的公式，也不是真实材料标定。历史 PhysX 核心身份缺失仍见 #126 审计。

**新场景首先验证：** 检查惯量、接触数、原生参数与力—位移斜率；保留离面负载段。

**候选起点：** MuJoCo 3.11.0 / native Newton：报告的 solimp=[.9,.9,.001,.5,2]，校准 solref 刚度项 −2499.883；完整阻尼与质量规则从冻结清单读取。SuperDex 1.0.0 FP64 和历史 PhysX 配置分别见报告。

**成本：** 17 条历史记录，11 通过、6 失败；包含校准和验证，不能当作统一比较。

**证据：** [demos/contact-benchmark/NORMAL_RESPONSE.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/NORMAL_RESPONSE.md) · [demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/NORMAL_RESPONSE.zh-CN.md) · [benchmarks/contact-normal-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-normal-v1.json)

(transient-cost)=
## 静态相近，不代表瞬态和成本相近

**条件：** 0.2 kg 方块；合成 K=20 kN/m、D=40 N·s/m；0.5/0.25/0.125 ms。瞬态研究含历史 PhysX，重复成本批次为 MuJoCo 3.14 / SuperDex 1.0 FP64。

**观察：** MuJoCo 低阻抗瞬态 RMS 为 2.771→1.327→0.617 µm；高阻抗为 120.654→76.542→67.765 µm。成本批次分别 9/9 与 0/9；SuperDex 为 0/9，含拉力检查失败。历史 PhysX 瞬态三例通过。

**解释与证据等级：** 已验证：这些配置的步长缩小不能普遍消除模型差异。SuperDex 该阻尼是依赖弹性接触力的项；它与恒定线性阻尼不是相同接触律。

**建议：** 将静态、瞬态、无拉力和成本一起验收；先核对接触律，再扫描步长。

**边界：** 参数来自合成目标；成本重复在同一进程重建场景，不证明独立进程重复性或通用引擎排名。历史 PhysX 缺失核心遥测，不能直接推荐为当前 SDK 配置。

**新场景首先验证：** 冻结目标响应、阻尼定义与加载时刻；同时记录原生步进和观测成本。

**候选起点：** MuJoCo 3.14 / native Newton：低阻抗 d=.001、direct solref=[−24975,−49.95] 是该响应目标的候选起点。以冻结清单为准；迁移前重新验证。

**成本：** 27 条成本记录，9 联合通过、18 失败；更小步长增加调用数，观测开销不能归为 solver 本体。

**证据：** [demos/contact-benchmark/TRANSIENT_RESPONSE.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/TRANSIENT_RESPONSE.md) · [demos/contact-benchmark/RESPONSE_COST.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/RESPONSE_COST.md) · [docs/evidence/response-cost-v1.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/response-cost-v1.json) · [benchmarks/contact-response-cost-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-response-cost-v1.json)

(mass-size-transfer)=
## 通过一个场景，不代表可直接迁移

**条件：** 质量 0.12–0.28 kg，半边长 15–25 mm，三个固定响应配置、十组条件，0.5 ms。

**观察：** 30 条全部完成；1/30 通过工程检查，0/30 通过瞬态与联合检查。未进行质量或面积参数补偿。

**解释与证据等级：** 已验证的是固定配置在这组迁移条件下失败；尚不能据此确定失败都来自求解算法。

**建议：** 新物体先做质量、尺寸和接触拓扑敏感性验证。参数补偿必须预先声明，再冻结新留出。

**边界：** 这组迁移在开发后、观测前冻结，不是隐藏盲测；旧记录不能作为新调参的未见留出。

**新场景首先验证：** 从与目标质量／几何最接近的记录开始，检查惯量、接触数、位移响应和拉力。

**候选起点：** 使用 contact-transfer-v1 清单中的 MuJoCo 3.14 高／低阻抗、SuperDex 1.0 FP64 固定配置作为失败基线；目前没有此范围内已验证可直接迁移的推荐配置。

**成本：** 30 条轨迹均保留；调参和重新准入的额外成本必须单列。

**证据：** [demos/contact-benchmark/TRANSFER.md](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/TRANSFER.md) · [docs/evidence/contact-transfer-v1.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/contact-transfer-v1.json) · [benchmarks/contact-transfer-v1.json](https://github.com/huangkiki/Dexlab/blob/main/benchmarks/contact-transfer-v1.json)

(physx-observation)=
## PhysX 异常先分清物理误差与观测误差

**条件：** PhysX SDK 5.9.0 / native CPU FP32；PGS、PGS friction-every-iteration、TGS、TGS external-forces-every-iteration，冻结九例斜面。

**观察：** 通过数为 7/9、7/9、3/9、3/9；13 条正例触发数值检查，四个负例有效且正确拒绝。TGS 运动案例状态／冲量残差为 1.09e−7 至 1.96e−7 N·s。

**解释与证据等级：** 已验证原生冲量与速度有分开的 FP32 运算路径，独立重复重现记录；尚未唯一分解每个残差的来源。禁碰撞前初始化惯量修正了先前错误的负例质量。 新离线分解表明，使用原生法向后 PGS 方向残差降低；改用原生质量／重力仍未消除 TGS 越界。原评分不变。

**建议：** 先检查质量、接触冲量时刻及 FP32 读回，再研究参数。#163 保留原检查，依据独立诊断冻结新协议并用留出验证。

**边界：** 有限四配置未通过不能证明 PhysX 不适用；没有覆盖 GPU、Isaac 路径或任意穿透场景，也没有调参成功的泛化保证。

**新场景首先验证：** 静态先核对 N=mg cosθ、摩擦不等式，滑动再核对加速度与逐步冲量。

**候选起点：** 原生 SDK 5.9.0 PGS 是此斜面开发基线的起点之一，非全局最优；使用冻结协议的质量、步长、迭代数与接触偏置，不移植同名框架默认值。

**成本：** 40 条正式记录，采集服务共 10.782 s；含观测的正确性成本，不是跨引擎吞吐排名。

**证据：** [docs/physx-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) · [docs/physx-incline-protocol.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-protocol.md) · [docs/evidence/physx-incline/profiles.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/profiles.json) · [docs/evidence/physx-incline/readback-interpretation.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/readback-interpretation.json) · [docs/physx-precision-diagnostics.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.md) · [docs/physx-precision-diagnostics.zh-CN.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-precision-diagnostics.zh-CN.md) · [docs/evidence/physx-incline/precision-pgs.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/precision-pgs.json) · [docs/evidence/physx-incline/precision-tgs.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/physx-incline/precision-tgs.json)

(pinch-load)=
## 夹持要同时解释承载、滑移和释放

**条件：** Genesis 原生有限夹具、四档力限额和 ±2 mm 初始偏移，共 16 个固定案例。另有 MuJoCo 标准方块夹持与机器人 SDF 历史场景。

**观察：** Genesis 0.2/0.4 N 限额不能保持物体；0.8/10 N 保持并释放。通过范围限于该夹具与驱动。

**解释与证据等级：** 已验证驱动限额会改变承载边界；摩擦／力矩平衡是诊断起点，不能仅凭接触力残差宣称抓取成功。

**建议：** 从物体载荷、每侧法向力和有效摩擦出发，再检查有限指面接触、滑移和释放；同步核查驱动实际输出。

**边界：** 这不是跨引擎统一夹持排名。#145 的惯量／坐标问题和 #132→#134 的共同驱动／594 回合正式研究仍独立开放。

**新场景首先验证：** 先验证无夹持／低力负例，再验证抬升、保持、偏移和释放全过程；检查对象实际运动。

**候选起点：** 复用 Genesis 力限额报告的原生版本与完整驱动参数。机器人抓取从 MuJoCo／SuperDex 已验证 14 s SDF 案例起步，并对新几何重新验收。

**成本：** 限额扫描、驱动与几何准备成本分开报告；历史机器人成功不是新任务零成本准入。

**证据：** [docs/force-limit-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/force-limit-results.md) · [docs/pinch-load-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-load-results.md) · [demos/apple-stem-grasp/README.md](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) · [docs/pinch-boundary-roadmap.md](https://github.com/huangkiki/Dexlab/blob/main/docs/pinch-boundary-roadmap.md)

(six-engine-incline)=
## 用同一物理问题识别配置差异

**条件：** MuJoCo 3.15.0、SuperDex 1.0.0、Genesis 1.4.3、Newton Physics 1.6.1、PhysX 5.9.0、Drake 1.57.0 原生斜面；每个 solver 的接触律、精度与适用配置分别记录。

**观察：** 六引擎已有正例、负例和失败证据；Genesis 名义零摩擦被原生接触抬到 .01，SuperDex BFGS/SR1 在每步重组装设置下等效执行 Newton 步骤。

**解释与证据等级：** 已验证的有效参数／执行路径差异能改变对同名配置的解释；初始通过率不能替代等预算调参后的比较。

**建议：** 按粘着／滑动、低摩擦和接触尺度筛选候选；同时查看无效记录、物理误差和成本。

**边界：** 各批协议和准入范围保持独立；完整配置表给研究范围，不给普遍排名。#157/#159/#163/#165 的数值问题仍未全部解决。

**新场景首先验证：** 先做目标工况的静摩擦阈值及无摩擦负例，再验证滑动、旋转和力—状态一致性。

**候选起点：** 从完整矩阵选择与新场景接近且观测有效的配置；精确参数取各引擎冻结协议。尚无新 coverage-v1 可靠覆盖认证。

**成本：** 仅在相同条件、预算与观测方式下比较成本；初始化与原生步进分开。

**证据：** [docs/mujoco-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/mujoco-incline-results.md) · [docs/superdex-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/superdex-incline-results.md) · [docs/genesis-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-incline-results.md) · [docs/newton-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/newton-incline-results.md) · [docs/physx-incline-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-incline-results.md) · [docs/drake-contact-paths-results.md](https://github.com/huangkiki/Dexlab/blob/main/docs/drake-contact-paths-results.md)

(framework-path)=
## 同一核心仍要检查转换后的有效状态

**条件：** 匹配 MuJoCo/MJWarp 3.11.0、Warp 1.16.0；原生与 Isaac Sim 6.1 源码标签构建，200 步小方块支撑／禁地面对照。

**观察：** 相同 CPU 模型下，55 个选定 GPU 字段中四项不同。显式对齐后仍未通过原动量检查，也未重现框架轨迹；三次独立原生过程记录完全相同。

**解释与证据等级：** 已验证：匹配导入模型不足以保证有效 GPU 模型一致；这四项也不足以解释全部轨迹差异。CPU 接触越界读回已修正，不能把不可观测值解释为零。

**建议：** 保存源资产、中间模型和最终有效参数；对齐控制时刻、接触路径、惯量及容量，再对照运行。

**边界：** 只能归因到已隔离的因素；没有证明全部内部状态一致或唯一框架根因。最新原生、完整斜面／碰撞／夹持与留出仍见 #152。

**新场景首先验证：** 先比较无接触轨迹，再检查首个差异时刻前后的模型／状态和原生接触地址。

**候选起点：** 此匹配版本只用于归因，不替代最新稳定原生与官方兼容框架双轨选型；复用公开协议的 default/aligned 两套配置。

**成本：** 保留初始化、观察、缓存与独立进程成本；200 步诊断不能代表长时抓取吞吐。

**证据：** [docs/framework-mjwarp-diagnostics.md](https://github.com/huangkiki/Dexlab/blob/main/docs/framework-mjwarp-diagnostics.md) · [docs/evidence/framework-mjwarp/matched-core.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/framework-mjwarp/matched-core.json) · [docs/evidence/framework-mjwarp/archive.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/framework-mjwarp/archive.json)

(libero-workflow)=
## LIBERO：原任务成功，不代表接触诊断通过

**条件：** 官方 cream-cheese-to-basket，Panda / robosuite 1.4.0 / MuJoCo 2.3.7 Newton elliptic；20 Hz 控制，原版 2 ms。

**观察：** 原版与 1 ms 留出动作执行均 10/10 完成原任务，物理诊断分别 5/10 与 3/10；步进成本约翻倍。五步静置后旧观测与实际末端位置某坐标相差 4.481 mm。

**解释与证据等级：** 已验证观测赋值遗漏；正接触时间常数与步长安全下限存在源码确认的耦合。更小步长没有一致改善；最大 floor 接触穿透 12.163 mm 的完整机制仍见 #174。

**建议：** 先修正观测新鲜度，区分控制目标、驱动输出与接触力；保留失败，按具体接触定位受控实验。本轮不推荐新的物理配置。

**边界：** 只有示范动作执行，未验证固定策略闭环效果、真实材料准确性或中途状态恢复；留出仅为同任务的十条示范，不是新任务泛化。

**新场景首先验证：** 核对初态与控制器重置、静置后观测、原生接触对/时刻/坐标、最终有效参数及原成功条件。

**候选起点：** 保持 LIBERO 8f1084e / robosuite 1.4.0 / MuJoCo 2.3.7 的原版配置，应用可撤销观测刷新补丁；1 ms 只是未通过筛查的对照。

**成本：** 八个候选（六种物理配置及两种审计），三个开发、十个留出示范；保留全部 40 条本协议记录。留出原生步进 2.239 s / 4.481 s；含记录的总成本见账本。

**证据：** [docs/evidence/libero/summary.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/summary.json) · [docs/evidence/libero/patch-validation.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/patch-validation.json) · [demos/libero-contact/protocol.json](https://github.com/huangkiki/Dexlab/blob/main/demos/libero-contact/protocol.json) · [docs/evidence/libero/process-repeat.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/process-repeat.json) · [docs/evidence/libero/budget.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/budget.json) · [docs/evidence/libero/resources.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/resources.json) · [docs/evidence/libero/native-package-integrity.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/native-package-integrity.json) · [docs/evidence/libero/history.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/history.json) · [docs/evidence/libero/archive.json](https://github.com/huangkiki/Dexlab/blob/main/docs/evidence/libero/archive.json)

<!-- research-experience:end -->
