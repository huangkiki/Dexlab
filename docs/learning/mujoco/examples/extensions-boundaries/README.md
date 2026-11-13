# 原创flex布局阅读片段

对应[E6 flex与弹性](../../docs/flex-and-elasticity.md)和[综合追踪](../../docs/multiphysics-and-source-trace.md)。此片段是本仓原创，不复制官方模型；只做Python AST、XML结构和固定源码核对，未import引擎、编译模型、forward、渲染或仿真。

- [flex_patch.xml](flex_patch.xml)：full二维3×3网格，两个点pin到world，材料young=1000 Pa、poisson=0.3、厚度0.002 m、Rayleigh damping=0.001 s；碰撞radius=0.001 m是另一字段。discrete/CG、h=0.002 s是阅读配置，不是已验证稳定配置。
- [inspect_flex.py](inspect_flex.py)：通过原生flex ID和地址读取body归属、局部顶点连接和世界位置；没有统一后端封装。数组copy把打印内容与后续原生buffer修改分开。

若未来执行该脚本，会加载/编译MJCF并调用`mj_forward`；编译器本身也可能做测试计算。它未显式调用`mj_step`，没有时间循环。当前没有输出截图、位置数值、运行成功或材料响应结论。

阅读时分别回答：`flex_elemadr`（元素地址）与`flex_elemdataadr`（顶点索引列表地址）为何不同？pin为什么在这个父body下才是世界固定？材料厚度为何不能由radius替代？元素连接是flex局部顶点编号，为什么不能直接拿它索引所有flex的拼接数组？[原生字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/include/mujoco/mjmodel.h#L550-L590)和[flex位置实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/src/engine/engine_core_smooth.c#L553-L635)给出核对入口。

ElementTree通过只说明XML闭合与结构可解析，不代替MJCF语义检查。材料、pin编号、编译兼容性及稳定性最终仍需对应版本的原生运行验证；本阶段没有执行，也不新增实验计划。后续工况证据复用DexLab。
