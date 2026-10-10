# PhysX FP32 观测：离线分解

[English](physx-precision-diagnostics.md) · [原始结果](physx-incline-results.zh-CN.md) · [后续 #163](https://github.com/huangkiki/Dexlab/issues/163)

本分析直接复用 v0.54.0 的 **40 条**原生 PhysX SDK 5.9.0 斜面记录，核验原来源与原始文件哈希，保留原评分。**新增原生仿真启动数为零。** 目标是明确下一步假设，不能据此准入失败记录或修改物理容差。

## 发现

PGS 2 ms 滑动原先触发解析法向方向检查。将每条法向冲量投影到**归一化的原生法向读回**，而非理想平面法向，最大离轴分量从 **1.00897334e−10 降至 1.61804328e−11 N·s**。这隔离了对法向表示的敏感性；剩余还包含冲量各分量舍入，不能声称唯一误差来源已确定。原解析法向检查仍然失败。

十二条 TGS／TGS-external 运动案例，改用实际原生 FP32 质量与重力后，最大动量残差范数仍为 **1.09418828e−7–1.96463231e−7 N·s**，均超过原 1e−7 N·s 检查。每条记录现在给出首次越界、最大残差步及其前后状态时刻。例如 TGS 无摩擦 .5 ms，首次越界为第 **3269** 步，最大值在第 **3315** 步，原生常量计算的峰值为 **1.96463231e−7 N·s**。

该峰值处，两端 FP32 速度半间距相加并乘原生质量，逐轴约为 **[3.05176e−8, 8.97e−47, 7.62939e−9] N·s**。这仅是输出表示的描述性尺度，**不是**内部子步、累计冲量或求解器的前向误差界。把容差增大到观测残差，不能建立物理正确性。

下一项有界假设应区分内部速度更新、冲量累加／读回及其时刻；仅分析输出端间距不能完成这项归因。尚未证明算法缺陷、隐式状态写入或任务不可能完成。PGS 的力平衡物理失败仍与观测有效性失败分开；四组原通过数保持 **7/9、7/9、3/9、3/9**。

## 无需新增仿真即可复现

解压 [v0.54.0 原始归档](https://github.com/huangkiki/Dexlab/releases/tag/v0.54.0)，核对发布的哈希，将 `CAMPAIGN` 指向包含 `manifest.json`、`campaign.json` 及案例子目录的某个配置目录。使用仓库已准入的 NumPy 环境：

```bash
python scripts/physx_precision_diagnostics.py --input "$CAMPAIGN" --output precision-new.json
```

分别运行 `pgs`、`pgs-friction`、`tgs`、`tgs-external`。脚本先调用已有评分器核验协议、来源、模型绑定及全部原始文件。输出逐例保存原始 SHA-256、原评分、首次动量越界，以及两种法向参照下的最大值；不改写输入或原评分。

[PGS](evidence/physx-incline/precision-pgs.json) · [PGS friction](evidence/physx-incline/precision-pgs-friction.json) · [TGS](evidence/physx-incline/precision-tgs.json) · [TGS external](evidence/physx-incline/precision-tgs-external.json)

四配置离线分析耗时 18.761 s，冻结资源为 16 GiB／四核配额。这是分析成本，不是原生 solver 吞吐。#163 继续负责有源码依据的内部归因，以及任何新协议的独立留出；#152 和 #145 分别保留框架、惯量／坐标验收。
