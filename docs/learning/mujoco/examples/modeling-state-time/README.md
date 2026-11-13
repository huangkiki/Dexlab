# E1 原生字段阅读片段

配合[建模与坐标](../../docs/modeling-and-frames.md)和[状态与时间](../../docs/state-and-time.md)阅读。

- [frames.xml](frames.xml)：原创 MJCF，展示 free、slide、hinge、ball、偏移质心与 site；不是待比较的机器人或接触工况。
- [inspect_state.py](inspect_state.py)：读取地址、区分视图与副本、展示配置空间积分/差分和快照。脚本没有 `mj_step`，但加载会调用 MuJoCo 编译器，编译器可能执行内部一致性计算。

**本轮仅做 Python AST、XML well-formedness 与固定源码核对，两个文件均未交给 MuJoCo 执行或编译。** XML 结构检查不验证 MJCF schema、质量矩阵或加载成功；源码预测不是实测输出。

如后续自行阅读执行，需要[安装说明](../../docs/installation.md)中的 MuJoCo 3.15.0 Python 环境。从仓库根目录运行 `python examples/modeling-state-time/inspect_state.py`。这里保留命令供读者使用，本仓本阶段没有运行该命令。

按声明推导，`nq=13`、`nv=11`、`nu=1`、`nactuator=1`：free 为 7/6，slide 与 hinge 各 1/1，ball 为 4/3。不要把这一组模型的 `nu == nactuator` 推广到 3.15.0 的多维驱动器。
