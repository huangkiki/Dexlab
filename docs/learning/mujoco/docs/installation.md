# 阅读与安装

当前课程以官方固定源码为阅读基线：[3.15.0](https://github.com/google-deepmind/mujoco/tree/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5)。阅读 Markdown 与源码无需安装仿真引擎。

`requirements.txt` 是后续 API 学习的候选依赖清单，不是经过干净安装验收的锁文件。Python 引擎须在独立环境中按官方支持范围安装；PhysX 的 Python requirements 不会安装 C++ SDK，构建入口见源码地图和官方文档。包版本、核心版本和宿主版本分别记录。

本阶段未进行物理运行、GPU、GUI 或跨平台验收。不要把本地可安装、import 成功或源码存在当成运行能力证明。后续安装课会补足平台矩阵、原生版本读回及排错；不会因此启动新的实验批次。

[源码地图](source-map.md) · [版本边界](versions.md) · [首页](../README.md)
