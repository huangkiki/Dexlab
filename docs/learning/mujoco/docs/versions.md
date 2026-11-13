# 版本与证据边界

| 身份 | 当前记录 |
|---|---|
| 阅读版本 | 3.15.0 |
| 官方源码 | [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco/tree/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5) |
| 固定提交 | `9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5` |
| 源文件身份 | [sources.json](sources.json) 中的 Git blob 已与下载文件核对 |
| 已完成检查范围 | 文档相对链接、固定来源与源码文件身份；API 片段只做语法检查 |
| 原生运行与实验 | 本阶段未开展 |
| 完整专题 | E1–E6课程已交付；A0完整安装与全路线审校仍见[课程目录](curriculum.md)的待办 |

固定文件身份不能证明整个引擎已审查，也不能证明候选二进制与源码具有相同构建配置。核心、绑定、插件和宿主身份分别记录。当前版本的默认值不用于补填 DexLab 历史配置。

[DexLab](https://github.com/huangkiki/Dexlab) 保留实验版本与协议；本仓不修改或追认其结果。

E5的JAX语言/API阅读基线单独固定为0.7.2、提交`94233144f5469af28c065aa4263a6849338eeaa1`，文件身份见[external-sources.json](external-sources.json)。MuJoCo树内MJX包与vendored Warp的实际身份、依赖约束见[MJX课程](mjx-and-device-data.md)；包声明的约束、源码阅读版本和实际运行环境是三种证据。本轮没有安装验证或生成运行锁文件。

E6沿同一MuJoCo固定树读取插件、flex/IPC和vendored Warp，未把它们替换成外部最新发布包；JAX清单新增控制流实现以核对while_loop反向规则。能力按实际编译/执行/恢复路径限定，源码支持不等于所选二进制、硬件或多模块组合已运行验收。
