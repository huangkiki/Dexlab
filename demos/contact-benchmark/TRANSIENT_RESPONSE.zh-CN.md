# 接触瞬态响应

[简体中文](TRANSIENT_RESPONSE.zh-CN.md) | [English](TRANSIENT_RESPONSE.md)

**先标定响应，再验证迁移；静态压入深度相同，不代表动力学相同。** 本开发实验在法向载荷协议中加入明确的阻尼目标和步长细化。使用官方 MuJoCo 3.11.0、SuperDex 1.0.0 FP64 和 PhysX / Isaac Sim 5.1，未修改引擎。

![未滤波瞬态与步长细化](media/transient-response-v1.png)

## 固定实验

无摩擦立方体边长 40 mm、质量 0.2 kg。质心外力依次产生 2、4、6、−1 N 的向下载荷，每段持续 0.2 s；末段向上释放。不使用位置伺服、附着约束或运行中的位姿覆盖。

正载荷阶段的参考是 `m*x'' + D*x' + K*x = L` 从静止出发的解析解，**K = 20,000 N/m，D = 40 N·s/m**。这是预设 Kelvin–Voigt 工程目标，不是 Wuji 指腹或苹果的实测材料。分离阶段不使用这个双向弹簧参考，避免把人工拉力当作应有行为。

每次增加 2 N，对应平衡压入增量 100 μm。各正载荷阶段前 50 ms 要求 **RMS 误差 <10 μm、峰值误差 <25 μm**；不拟合时间、位置偏移或相位。原有全程原生参数、接触力账本、动量、穿透、稳定、无拉力和完全释放检查保持不变。单独通过瞬态检查不算物理验收通过。

[12 项矩阵](../../benchmarks/contact-transient-v1.json)、目标和配置均在执行前确定。四种候选分别运行 **0.5、0.25、0.125 ms**，原生参数不随步长重调。这些是确定性的开发检查，不是留出成功率实验，不应给出二项置信区间或综合引擎排名。

## 参数来源

| 候选 | 映射与适用边界 |
|---|---|
| MuJoCo，恒定阻抗 d=0.9 | 直接格式 `solref=[-2500,-5]`。四个对称面接触下，测试 `solref=−(1−d)/(4m) × [K,D]`。这是本几何的开发假设；参考加速度约束不会因静态刚度相同就成为力弹簧。此阻尼配置**不同于**原 normal-v1。 |
| MuJoCo，d=0.001 | 同一映射得到 `solref=[-24975,-49.95]`，其余夹具设置不变。 |
| SuperDex | 沿用 normal-v1 的罚系数 12,500,000、阈值 1 μm、平滑半距离 0.5 μm；法向黏性系数设为 **10 s/m**，由 `D / 4 N` 得到。官方安装包属性说明：阻尼力正比于弹性接触力乘法向速度，**并非恒定 40 N·s/m 的阻尼器**。 |
| PhysX | 四条面接触约束分别设置 **5,000 N/m、10 N·s/m**，材料组合取平均，关闭加速度弹簧。TGS 8/2 和偏移不变。组合 USD 参数读回与真实位移/接触力分别检查。 |

[MuJoCo 求解器文档](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters)说明阻抗与参考加速度语义；[PhysX 柔顺接触文档](https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/docs/RigidBodyDynamics.html#compliant-contacts)说明力弹簧语义。SuperDex wheel 属性说明随证据归档。不能直接把同名刚度、阻尼数值跨引擎复制。

## 全部结果与失败

**12 次原生运行全部完成，6 次同时通过物理和瞬态检查，6 次失败。** 单看瞬态有 7 次通过，其中 1 次仍违反无拉力要求。[完整报告](evidence/transient-response-v1.json)保留所有结果。

| 候选 | 最差瞬态 RMS，h=0.5 / 0.25 / 0.125 ms | 综合检查 |
|---|---|---|
| MuJoCo d=0.9 | 120.65 / 76.54 / 67.77 μm | 0/3；瞬态、稳定和有限窗口载荷响应失败 |
| MuJoCo d=0.001 | 2.77 / 1.33 / 0.62 μm | 3/3 |
| SuperDex 载荷相关阻尼 | 9.21 / 12.00 / 13.75 μm | 0/3；均有瞬时拉力，其中两项瞬态 RMS 也失败 |
| PhysX 力弹簧 | 4.51 / 4.30 / 4.19 μm | 3/3；仍有响应误差 |

SuperDex 在约 0.6055 s 的释放阶段，朝上的法向力最小为 **−0.451 / −0.282 / −0.161 N**，来自原生接触账本求和，不是反推的力，也不代表永久附着。减小步长降低了峰值，但仍未通过原有无拉力检查。其 4 N 响应比 2 N 更接近恒定阻尼目标；迁移前必须考虑载荷相关的接触定律。没有利用这些验证结果再次调参，也没有放宽阈值。

MuJoCo 低阻抗候选更接近本目标，不代表引擎整体更优。PhysX 随步长细化误差仅小幅下降，不能据此声称已收敛到解析目标。接触定律不匹配，不能仅靠减小步长解决。

## 惯量导出修正

此前 0.4 kg PhysX 的惯量误差，定位到原生导入前 `MjSpec.to_xml()` 对编译后惯量的舍入。**本地 UniSim 适配器修复**在序列化后以 17 位有效数字写入质量、质心、主惯量及其坐标系。没有修改 MuJoCo、PhysX 或其数值精度；几何和关节字段的序列化不在此次范围内。

独立复跑原 normal-v1 参数，原生惯量读回 **0.00010666666639735922 kg·m²**，声明值为 0.00010666666666666668，现通过原有 3 ppm 检查。平台波动仍为 **6.387 μm**，继续违反原有 5 μm 阈值。历史失败记录保留。适配器覆盖推断惯量、旋转的显式惯量与完整张量；1,350 项测试通过、92 项可选跳过，lint、类型、打包及 19 文件精确补丁重放通过。

## 复现与计算成本

使用仓库环境；PhysX 另需其安装步骤。当前 `scripts/setup_physx.sh` 使用独立的 `UniSim-physx-precision` 目录；历史 v0.13 适配器请使用对应不可变 tag。输出目录必须是新目录。

```bash
.venv/bin/python demos/contact-benchmark/normal_response.py run runs/contact-transients \
  --suite benchmarks/contact-transient-v1.json
.venv/bin/python demos/contact-benchmark/normal_response.py verify runs/contact-transients
.venv/bin/python demos/contact-benchmark/plot_transient_response.py runs/contact-transients \
  --output runs/contact-transients/response.png
```

`verify` 检查矩阵、原生记录、源码/产物哈希及每份静态与瞬态评分。退出零表示结果成功复现，包含物理失败。发布证据包含全部 12 次运行、独立惯量复跑、评分器、执行前冻结记录、参数说明与中英文报告。

0.125 ms 步长下，0.8 s 仿真的步进加观测耗时约为：MuJoCo d=0.001 **0.31 s**，SuperDex **0.78 s**，PhysX 子进程路径 **16.43 s**；准备耗时另行记录。各路径的观测/IPC 不同，同机还在运行苹果测试，**不能作为隔离的引擎吞吐排名**。材料/摩擦标定、接触表示迁移、正式评测及受控速度—误差研究仍由 [Issue #10](https://github.com/huangkiki/Dexlab/issues/10) 跟踪。
