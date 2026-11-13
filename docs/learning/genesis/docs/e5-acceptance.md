# E5 验收与后续任务

对应 [Issue #6](https://github.com/huangkiki/genesis-atlas/issues/6)，从已发布 E4 的 main `4a3221eee0261d92fcf2ad912a707641e13836ad` 开始；本地与 origin/main 一致、工作树干净，E2/E4 文档与提交祖先已核实。实现分支 `docs/e5-batch-learning-data`。记录日期：2026-10-09。

交付 [批量、学习接口与数据](batch-learning-data.md)与原创 [batch_data_api.py](../examples/batch_data_api.py)，更新中英 README、导读、课程、roadmap 和来源表；保留 Sim Atlas 系列首页。无第三方源码或资产复制进入仓库，原创片段沿用本仓 Apache-2.0 许可。

## 覆盖与边界

| A8 / A9 / B6 要求 | 实际交付 |
|---|---|
| 批量隔离/异构 | 第1节：B=0/1 轴、逐行状态与共享 INFO、矩形索引/负索引、异构单根与 joint/link/DOF检查，纠正过时single-link注释 |
| reset/step | 第2节：物理/任务/观测分层、三种时钟、全批step与局部reset的全局副作用；保留E1多物理限制 |
| CPU/GPU/Torch | 第3节：backend/device/precision、getter复制、内部零拷贝、detach与CPU数组别名；明确build会试步 |
| 官方学习接口 | 第4–5节：Go2四返回、先reward后reset再obs、动作延迟/索引、1001步timeout、配置变异、缓冲所有权；区分外部训练器 |
| 终止/截断 | 第5节：保留terminal obs、两类结束及同时发生条件、solver failure、任务/RNN状态；bootstrap公式前提明确 |
| 随机化 | 第6节：q/v与INFO/STATE、质量/COM/惯量/摩擦/驱动参数、重置顺序、seed调用流与相似尺度公式 |
| 导出/回放 | 第7–9节：SimState/export/checkpoint/轨迹/视频、exact/compressed字段、source_digest范围、seek不是动作重跑 |
| 记录器 | 第8–9节：pre-step采样、末帧/时间戳回退、CPU所有权、队列丢旧、NPZ全量缓冲、cleanup与schema |
| sim-to-real | 第10节：参数/延迟/传感标定假设、相关性和实际能力差距；保留未来DexLab复用边界 |
| 性能/扩展 | 第11节：冷build/JIT、phase与GPU异步、吞吐/RTF、内存量纲、回调veto、记录器线程注册与可微/外部学习区别 |
| 阅读与例子 | 16题附答案；两个原生数据入口与一个所有权转换函数；无init/build/step主程序或学习wrapper |

**没有原生 import、构建、物理、渲染、训练、实验、性能基准或评分器。** 只审读固定 Genesis 1.4.3 源码；RSL-RL 只有官方调用方的 `>=5.0.0` 下界，未固定或安装外部实现，未验收 PPO 内部、外部 checkpoint 或依赖兼容性。跨设备/版本确定性、物理续跑、长期采集系统和实机标定均未验证。A0、E6 专项内部和 E7 综合审校仍待开发，不能将本章批量刚体主线推广为全多物理支持。

## 静态检查与自审

| 检查 | 状态 | 证据含义 |
|---|---|---|
| `git diff --check` | 通过 | 空白与冲突标记 |
| `python scripts/check_docs.py` | 通过 | 全仓 Markdown 相对文件链接 |
| Python AST / 完整 Python 围栏 | 通过：6个Python文件、1个完整围栏 | 只解析语法，没有导入/执行例子 |
| 固定SHA、manifest、Git blob/tree、行锚点 | 通过：96个blob、401个固定源码链接 | 所有来源内容哈希、固定提交、收录与实际行范围及reference定义 |
| 原创既有URDF静态回归 | 通过：3 links、2 joints及box惯量 | 没有加载引擎或运行模型 |
| GitHub Markdown API | 通过：5个块公式均生成display math-renderer | 使用 `$$`；只是Markdown标记渲染，不是浏览器像素/原生渲染验收 |
| 原生调用/派生实现与公式自审 | 已完成，最终独立主审待执行 | 跟踪Scene→Simulator→getter/setter及writer实现，不以注释替代执行分支 |

新增15个实际引用的固定源码文件到 manifest，全部96份缓存重新计算 Git blob SHA1，与官方固定 tree 和 sources.json 对照。源码仅保留在独立工作缓存，没有复制到仓库。第一轮链接检查因本验收页尚未写入失败；第一轮行锚点检查发现3个引用末行超过文件结尾，已按实际内容收紧并重跑。负索引与标量范围检查经审读补充；所有权提醒明确每实例独立配置深副本、rew_buf/extras不可按引用保存历史。

## 固定版本发现与下一项

- Scene.reset 的 per-env steps 与全局 tape 游标不同；使用 entity.set_qpos 的任务 episode 又有自己的时间。
- Go2 四返回且不保存 terminal obs；严格 `>` 超时、硬编码 latency、全局/本地DOF地址重合假设和 reward_scales 原地缩放均已展开。
- Scene.add_entity 的异构single-link注释滞后于 description 的多link分支；实际单根/相同关节结构检查保留。
- link质量等 INFO 与摩擦倍率 STATE 的普通reset行为不同；DOF INFO zero-copy分支不能由envs_idx推断已逐环境存储。
- data_to_array 不保证独立CPU存储；CSV/NPZ队列可丢旧，NPZ另有全程累积；reset不自动划分episode文件。
- exact普通帧与末checkpoint字段不同；n_envs=1仍默认exact；seek/play不是控制重积分，source_digest不是Git SHA或完整运行环境身份。

建议下一项 **E6 引擎特色、扩展与能力边界**：接续 E3 的多物理/耦合/可微内部与 E4 热/触觉专项；待本切片主审发布后领取。E7 再复核实现与注释差异并整理 DexLab 复用入口。按当前授权只做本地提交，不推送、不改远端 Issue/Project、Obsidian、总仓或其他引擎仓库。
