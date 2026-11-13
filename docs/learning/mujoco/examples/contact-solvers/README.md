# 原生接触与力字段阅读片段

**本轮未执行。** 只做 Python AST 与 XML 结构解析；没有导入 MuJoCo、编译模型、调用 forward/step、测量力或跑 benchmark。若将来执行 `inspect_contacts.py`，它会编译模型并做一次原生 `mj_forward`；编译器也可能进行内部测试计算。它没有时间推进循环，也不提供静态平衡或碰撞实测证明。

配合[接触模型](../../docs/contact-models.md)、[求解与积分](../../docs/solvers-and-integration.md)和[力观测](../../docs/force-observations.md)阅读。XML 与 Python 均为本仓原创，几何只有 plane/sphere，无第三方资产。

- [plane_spheres.xml](plane_spheres.xml)定义地面与两个 free sphere。位掩码允许 plane–sphere、禁止 sphere–sphere；明确选用 Euler/Newton/elliptic，不依赖默认配置来推断历史批次。
- 根据几何手算，两球表面距地面分别为 1 mm、4 mm；本版 margin 和为 2 mm、gap 和为 3 mm。普通无 adhesion 时，前者位于施力区，后者在检测 gap 内。**这是字段与几何推导，未声称运行生成了特定数量/数值的 contact。**
- [inspect_contacts.py](inspect_contacts.py)演示 `contact.geom`、`exclude/efc_address`、`mj_contactForce`、frame 转置和 CoM 力矩平移。Flex 的 geom=-1 必须显式处理，本例跳过。
- 同时展示 3.15 的 `mj_fullM(model,data,dst)` 与 `mj_mulJacTVec`。只打印本模型的广义力账本，不加入误差阈值或独立评分器；有 adhesion、IPC 或 passive flex 时必须重新判断分项语义。
- 记录的是同一次 forward 的 solve time；不是 1 ms 运动内平均力，不应把力乘任意时长变成“实测冲量”。

静态检查从仓库根运行：

```sh
python scripts/check_examples.py
```

检查脚本不会执行上述 Python。数值表现、MJCF schema、实际绑定调用和运行版本身份均未运行验收；后续实验复用 DexLab 的冻结工况。
