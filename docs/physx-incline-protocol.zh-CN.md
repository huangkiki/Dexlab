# 原生 PhysX 斜面协议

[English](physx-incline-protocol.md) | [简体中文](physx-incline-protocol.zh-CN.md)

[#150](https://github.com/huangkiki/Dexlab/issues/150) 验证官方 **PhysX SDK 5.9.0** 的四组固定 CPU 配置，源码 `517a0073715120e114ee055b63b26c95e00d9039`，标签 `110.1-omni-and-physx-5.9.0`。这是直接使用 C++ SDK 的新批次，不补写历史 Isaac 核心身份、不比较框架转换，也不计入 coverage-v1。框架兼容路径由 [#152](https://github.com/huangkiki/Dexlab/issues/152) 单独处理。

## 模型与适用配置

保留[原九工况](incline-comparison-protocol.zh-CN.md)：均匀 40 mm、64 g 方块，惯量 mL²/6，局部质心为零，重力 [0,0,-9.81] m/s²。方块与无限平面绕 +Y 旋转，初始底面贴合。静止 15°/μ=.5、滑动 35°/μ=.5、无摩擦 15°/μ=0，分别使用 2/1/.5 ms 步长，每次 2 s，评分窗 .5–2 s。第十个 15°/.5/1 ms 负例在质量惯量初始化后关闭方块碰撞。没有驱动、阻尼、休眠或初始化后的状态写入；每个工况独立进程。

两形状接触偏移 .0001 m、静止偏移零，静动摩擦相同，恢复系数零，材料组合为平均，保留原生强摩擦。物体使用八次位置、两次速度迭代，CPU 分派器一个线程。实际容量、几何、坐标、质量、惯量、材料、初态和场景参数在正时长运行前逐工况读回并冻结哈希。FP32 数值以 17 位小数精度保存，不重新导入有损导出的模型。

| 配置 | 原生 solver | 附加设置 |
|---|---|---|
| PGS | 投影 Gauss–Seidel | 原生摩擦迭代时序 |
| PGS friction | PGS | 每次迭代计算摩擦 |
| TGS | 时间 Gauss–Seidel | 原生外力施加时序 |
| TGS external | TGS | 每次迭代施加外力 |

四组均使用 PCM、增强确定性和 patch friction。SDK 5.9 仅保留 patch friction，旧的一维、二维摩擦选项已不可用。TGS 本就逐次计算摩擦，因此切换 PGS 摩擦标志不另算一组有效 TGS 配置。逐次外力标志对 PGS 无效。依据冻结版本的[场景定义](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/include/PxSceneDesc.h)。本批次不声称完成 GPU 准入。

## 观测与冻结验收

在 `onContact` 回调内复制瞬时接触流。`extractContacts` 只给出**法向冲量**；`extractFrictionAnchors` 另给出世界坐标系摩擦冲量。按方块在 actor pair 中的位置确定符号，再将两者相加，不能用速度差伪造测得的接触力。保存标志、通道可用性、声明与实际接触数、patch 数、位置、分离距离，以及记录器 256 条容量。缺失或截断使工况无效。依据[回调 API](https://github.com/NVIDIA-Omniverse/PhysX/blob/517a0073715120e114ee055b63b26c95e00d9039/physx/include/PxSimulationEventCallback.h)。

仿真接收 FP32 步长，同时记录请求值和准确有效值；时间取 N 倍有效步长，另核对 `PxScene::getTimestamp()` 的步计数。检查前后状态连续和初始化后无状态写入。TGS 逐次重力不等价于使用末速度的一次半隐式 Euler 位置更新，因此不施加该恒等式；此判断在正式结果前依据 SDK 文档冻结。模型参数读回允许八个 FP32 epsilon × max(abs(expected),1e-8)，冲量方向检查绝对容差为 1e-10 N·s；这些不是迭代算法的前向误差界。

原物理阈值保持不变：静止位移/速度 .001 m/.001 m/s，滑动位置/速度 RMSE .01 m/.01 m/s，加速度误差 .05 m/s²，旋转 .01 rad，原生报告穿透 .001 m，力平衡 RMSE .01 N，并要求持续支撑。独立状态/冲量一致性仍为 **1e-7 N·s**。穿透取接触生成时原生分离距离，没有另算步末几何穿透。所有失败及无效观测留在九正例分母中。负例须观测有效，且评分拒绝无支撑运动。当前固定配置不做结果调优；共同开发集/留出集比较需另行冻结。

## 构建、预算与复现

官方 SDK 文件在编译前后均与 Git 树比对。官方归档有 22 个 PhysX 子树外的 Windows 命令文件做了 CRLF 规范化；2,155 个 PhysX 文件逐字节匹配 Git。没有引擎补丁。使用 GCC 11.4、CMake 3.22.1 及官方 `linux-gcc-cpu-only` Release 预设构建静态库。记录器是本项目代码。

```bash
cmake -S "$SDK_ROOT" -B "$BUILD" -DPHYSX_PRESET=linux-gcc-cpu-only \
  -DCMAKE_BUILD_TYPE=release -DPX_OUTPUT_LIB_DIR="$BUILD/lib" \
  -DPX_OUTPUT_BIN_DIR="$BUILD/bin" -DPX_OUTPUT_DLL_DIR="$BUILD/bin"
cmake --build "$BUILD" --parallel 4 --target PhysX PhysXExtensions PhysXCooking
bash scripts/build_physx_incline.sh "$SDK_ROOT" \
  "$BUILD/lib/bin/linux.x86_64/release" "$RECORDER"
```

运行前冻结源码、记录器二进制、运行器、独立及公共评分器、准入和资源哈希。四组串行配置共 40 次独立进程、92,000 次更新，每组最长 1800 s。零步准入实测峰值 46 MiB，选择最小档 **8 GiB / 四核配额**、零 swap，启动另留 8 GiB。未知新任务仍从 16 GiB、复杂模型 24 GiB 起测，不能把这个小模型的测量套到全部任务。六小时/64 次开发包与夹持研究预算相互独立。

每组使用已有资源限制及研究窗口，部署路径仅在本地配置：

```bash
python scripts/bounded_run.py --profile adaptive --resource-plan "$NEW_PLAN" \
  --peak-receipt "$MEASURED_RECEIPT" --cpu-cores 4 --timeout 1800 \
  --data-dir "$DATA_DIR" --io-device "$DATA_DEVICE" --receipt "$RESOURCE_RECEIPT" -- \
  python scripts/research_guard.py run --lock "$RESEARCH_LOCK" \
  --kind qualification --receipt "$WINDOW_RECEIPT" -- \
  python -m dexlab.physx_incline --protocol frozen-v1/pgs.json \
  --proof reports/official-proof.json --binary "$RECORDER" --output "$NEW_OUTPUT"
```

二进制哈希与构建绑定：重新构建须重新准入并事前冻结身份，不能改旧批次。使用归档内评分代码及 NumPy 2.5.3，无需安装物理引擎即可重算：

```bash
PYTHONPATH=frozen-v1/scoring-source python -m dexlab.physx_incline_score \
  --input campaign-v1/pgs --output score.json
```

原生步耗时含 simulate/fetch 和接触复制，不含 JSON 输出/压缩，与其他研究任务互斥。全服务成本含调度和工况之间的压缩。二者均不是跨引擎速度排名。见[结果与保留失败](physx-incline-results.zh-CN.md)。
