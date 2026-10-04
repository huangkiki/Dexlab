# 添加实验与维护报告

## 一项实验的交付

1. 在 Issue 写清假设、官方版本、参数来源、近似、预算、对照和验收。
2. 代码、配置与运行入口放入对应 `demos/` 实验目录；共享评分留在 `src/dexlab/`。
3. 保存实际初态、动作、轨迹、接触和所有结局。评分器独立于控制器，失败不能删。
4. 更新本站的实验卡与报告：结论、设置、指标图表、失败、局限和复现入口，中英同步。
5. PR 中说明对首页的影响。有新能力、实验结论、重要失败或复现变化时同步 README；纯内部维护没有读者影响时说明理由，不制造无意义改动。

## README 与文档站的分工

README 展示定位、当前结论、关键图表、连续近景与文档入口；完整参数表、方法推导、逐场景结果和失败分析由本站及其链接的原始实验报告维护。代码保持可运行，文档不复制私有服务器路径或实验账号。

每张图给出版本、单位、样本量、窗口、区间定义及来源。对比图同时保留失败；不要把不同标定、几何或调参预算的结果称为公平引擎排名。

## 文档发布

本站使用 Sphinx、MyST 和 PyData Sphinx Theme；参考 [RLinf 的信息组织](https://rlinf.readthedocs.io/zh-cn/latest/)，不复用其研究结论。两种语言共用主题与构建脚本，默认中文，支持搜索和深色模式。

`scripts/build_docs.py` 严格构建中英站点；GitHub Actions 对 PR 构建检查，合并到 main 后可部署 GitHub Pages。仓库包含 Read the Docs 构建配置，导入项目需相应服务账号。配置存在不代表站点已上线；发布后必须检查实际页面、语言切换、搜索、图表及移动端。

[贡献与自动研究流程](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md) · [Issue 队列](https://github.com/huangkiki/Dexlab/issues)
