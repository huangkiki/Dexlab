# 法向接触响应

[简体中文](NORMAL_RESPONSE.zh-CN.md) | [English](NORMAL_RESPONSE.md)

**静态响应相同，不代表材料动力学相同。** 本开发协议使用官方 MuJoCo 3.11.0、SuperDex 1.0.0 FP64 与 PhysX/Isaac Sim 5.1，量化这一差别。未修改引擎源码或二进制；PhysX 通过公开的本地 UniSim 适配器扩展启用原生柔顺接触。

![响应、质量迁移与稳定性](media/normal-response-v1.png)

## 协议与参数来源

边长 40 mm 的无摩擦方块从水平面上静止接触开始。每个物理步施加规定的竖直质心力：重力补偿减去 **2、4、6、−1 N** 的向下载荷，每段 0.2 秒；负载荷使方块向上释放。无位置伺服、附着或运行时位姿重写。参考质量为 0.2 kg，步长 0.5 ms。

预先规定 **20 kN/m** 的工程响应目标，对应 0.1/0.2/0.3 mm 几何压入量。这是人工设定的响应规格，不是 Wuji 指腹、苹果材料或真实软垫的测量值。各阶段末尾 50 ms 计算均值和标准差；只用 2/6 N 端点拟合，4 N、0.1/0.4 kg 质量及 0.25 ms 步长验证固定方案。这些属于开发迁移检查，不是随机留出试验。

冻结检查包括：载荷/响应误差 5%、平台标准差 5 μm、最大穿透 1 mm、动量残差低于重力的 5%、无拉力、有限倾斜与横漂，以及释放后完全分离、接触力归零。瞬态穿透与动量检查覆盖**每个物理步**。阈值先于候选实验写入，没有放宽。

| 原生配置 | 参数及含义 |
|---|---|
| MuJoCo | 固定阻抗 `solimp=[0.9,0.9,0.001,0.5,2]`；初始直接格式 `solref=[-10000,-100]`。2–6 N 实测割线斜率 80,003.75 N/m，得到刚度参数幅值 `10000 × 20000 / 80003.75 ≈ 2499.883`；阻尼仍为 100。精确值保存在场景矩阵。 |
| SuperDex | 罚系数 12,500,000；阈值 1 μm；平滑半宽 0.5 μm；法向黏性阻尼为 0。按方块接触面面积及目标斜率选择初值，由原生积分确定实际响应；不能直接解释为可迁移的杨氏模量。 |
| PhysX | 原生基于力的柔顺接触：**每条接触约束 5,000 N/m、2 N·s/m**，平均组合，关闭加速度弹簧。四个面接触点用于估计整体响应初值，再用实测力和压入量检验。TGS 8/2，接触偏移 0.1 mm，静止偏移为零。 |

MuJoCo 的直接格式指定约束加速度参考，受阻抗与惯量影响，不是单位 N/m 的力弹簧。PhysX 力弹簧作用于每条原生接触约束，接触点数量和位置变化可能改变整体响应。参见 [MuJoCo 模型文档](https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters)与 [PhysX 柔顺接触文档](https://nvidia-omniverse.github.io/PhysX/physx/5.4.0/docs/RigidBodyDynamics.html#compliant-contacts)。适配器路径同时核实了已安装 SDK 的 schema 和实际原生运行，并非只依据文档。

迁移实验前另行声明 MuJoCo 换算：直接格式 `solref` 的**两个分量**都乘以 `0.2 / mass`。这是当前固定阻抗、固定方块—平面几何的显式换算，不是通用材料映射。固定原生参数和换算后的结果均保留，没有根据验证结果再调参。

## 结果与失败

**17 次全部完成：11 次通过全部检查，6 次失败。** 这是不同条件的开发检查，不是独立伯努利试验或引擎排名，不附成功率置信区间。[完整报告](evidence/normal-response-v1.json)保留每项结果。

- MuJoCo 初值未匹配响应目标。拟合后的参考与半步长场景通过；固定原生参数时，0.1/0.4 kg 的斜率约为 **10.01/40.04 kN/m**，均失败。预先声明的质量换算得到 **20.04/19.93 kN/m**，均通过。
- SuperDex 静态斜率接近目标，但 0.4 kg 与半步长场景的平台波动分别达到 **9.23、8.85 μm**，超过 5 μm。步长减小后积分耗散减少只是待检验的解释，尚非已证实根因。没有针对验证结果重调阻尼。
- PhysX 静态斜率接近目标，但 0.4 kg 场景的平台波动为 **6.39 μm**。该场景还未通过原有惯量检查：导入后对角惯量为 `0.00010666700109140947`，声明值为 `0.00010666666666666668 kg·m²`，差值超过原有 3 ppm 容差。源 MJCF 保留完整精度；原生导入舍入记录保留待查，没有改称精确匹配。

法向参数和实际观测一起归档。PhysX 柔顺参数从 reset 前组合 USD 的材料绑定读回，**并非直接读取原生材料张量**。实际力、运动、质量/惯量、worker 退出、接触力账目及源码/产物哈希分别检查。静态匹配尚不能证明阻尼、摩擦、SDF 接触几何、抓取鲁棒性或真机精度一致；后续仍见 [Issue #10](https://github.com/huangkiki/Dexlab/issues/10)。

## 复现

使用仓库环境；PhysX 还需 `scripts/setup_physx.sh` 及已说明的 SDK 条件。安装脚本使用独立的 `UniSim-physx-compliance` 目录，保留旧适配器目录。公开矩阵固定全部候选，包含初始和迁移失败，不执行在线调参。

```bash
.venv/bin/python demos/contact-benchmark/normal_response.py run runs/normal-response \
  --suite benchmarks/contact-normal-v1.json
.venv/bin/python demos/contact-benchmark/normal_response.py verify runs/normal-response
.venv/bin/python demos/contact-benchmark/plot_normal_response.py \
  runs/normal-response/report.json --output runs/normal-response/response.png
```

单次力加载使用 `python -m dexlab.contact_indent_run --protocol normal-load --engine mujoco --normal-parameters profile.json --output runs/normal-one`，参数文件采用表中原生字段名。原有压入/滑动默认配置保留。

发布证据包包含精确矩阵、全部状态数组及接触力账目、原生与源码快照、记录哈希、离线复核和绘图脚本。`verify` 返回零表示全部既有结果复现，**包括物理失败**；运行错误单独识别。实验与苹果批次共享机器，耗时不作为隔离性能测量。

当前安装使用 `UniSim-physx-precision`：[后续瞬态实验](TRANSIENT_RESPONSE.zh-CN.md)修正惯量导出舍入，物理阈值不变。v0.13 历史归档保持不变；复跑原适配器请使用 v0.13.0 tag。新运行可能通过惯量检查，但稳定性失败仍保留。
