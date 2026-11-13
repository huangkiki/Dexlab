# 版本、来源与证据怎么读

[教程目录](README.md) · [DexLab 分类说明](https://github.com/huangkiki/Dexlab/blob/7e4a0774efb4f8b332e866e1495e032b4969c8aa/docs/solver-taxonomy.zh-CN.md)

本批冻结 DexLab `7e4a0774efb4f8b332e866e1495e032b4969c8aa` 的[配置角色词表](https://github.com/huangkiki/Dexlab/blob/7e4a0774efb4f8b332e866e1495e032b4969c8aa/docs/solver-taxonomy.json)和[首页表格](https://github.com/huangkiki/Dexlab/blob/7e4a0774efb4f8b332e866e1495e032b4969c8aa/README.md)。它定义本批要解释的登记名称，不证明每种组合都支持、都运行过或都通过。

| 引擎 | DexLab 登记身份 | 现有课程的阅读入口与差异 |
|---|---|---|
| MuJoCo | 3.11.0、3.14.0、3.15.0，不同历史路径 | [3.15.0 原生课程](https://github.com/huangkiki/mujoco-learning/blob/main/docs/versions.md)。源码阅读 pin `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5`；新版本的控制流不反推旧日志。 |
| SuperDex | 1.0.0，精度和运行路径分别记录 | [课程版本](https://github.com/huangkiki/superdex-learning/blob/main/docs/versions.md)。公开源码 pin `1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`；冻结报告另有 [wheel/core/binding 身份证明](https://github.com/huangkiki/Dexlab/blob/7e4a0774efb4f8b332e866e1495e032b4969c8aa/docs/evidence/superdex-incline/official-proof.json)，按批次解读，不能只用包版本号推断构建能力。 |
| Genesis | 1.4.3 | [课程版本](https://github.com/huangkiki/genesis-learning/blob/main/docs/versions.md)。阅读 pin `216a708e06124595521a9d36a51fae5393fd4ff8`；实际后端与配置仍查原批次。 |
| Newton Physics | 1.6.1 / Warp 1.18.0；历史另有 1.7.0.dev0 @ 2dee3234 | [课程版本](https://github.com/huangkiki/newton-learning/blob/main/docs/versions.md)。阅读 1.6.1 pin `713fecdc41caf0c9d726f5c016939f36e66e3dff`；不混同 dev 路径。 |
| PhysX | 登记 5.9.0，部分历史读回尚缺 | [课程版本](https://github.com/huangkiki/physx-learning/blob/main/docs/versions.md)。公开源码 `ovphysx-0.6.3` / `da950a3537927784951853c66618036f332ca0ce` 的头文件显示 5.11.0；不能据此补成历史运行二进制身份。 |
| Drake | 1.57.0 | [课程版本](https://github.com/huangkiki/drake-learning/blob/main/docs/versions.md)。配置含 SAP、接触模型和离散接触近似；资格状态单独保留。 |

## 共同先修教材

[Physics-Based Simulation](../physics-based-simulation.md) 的在线前言版本为 1.0.3（2026/3），2026-10-14 核对；本次章节映射固定到官方 Markdown 提交 `18c637eb6a7016814ac2a04e98798be0ed9b82b1`。教材版本独立于六引擎和历史运行版本；[来源记录](../physics-based-simulation-sources.json)记录实际核对范围。

## 每条结论携带什么

- **一般数学知识**：写明假设、变量、单位和适用条件；纸面例子是构造，不是引擎测量。
- **实现结论**：链接到引擎完整提交和具体文件；接口文档与源码有差异时继续追踪调用分支。
- **配置记录**：声明哪个版本、路径、字段和读回阶段；配置枚举存在不代表运行进入该分支。
- **实验观察**：返回 DexLab 的原协议、版本、有效配置与成功/失败记录；不能用当前默认值修补历史缺口。
- **未知身份或未准入**：解释缺少哪种证据，保持未知；不能把 `algorithm unqualified`、`pending qualification` 当成 solver 名称。

教程可以解释一个未通过实验资格的引擎，也可以解释一个尚未运行的合法选项。教学覆盖、运行覆盖、物理可信度与计算成本分别记录。

## English summary

The vocabulary is frozen from the linked DexLab commit. Engine source-reading pins and historical executable identities are different records. Preserve unknown branches and qualification gaps; current defaults cannot reconstruct missing historical telemetry. Paper examples, source interpretation and observed experiments are labeled separately.
