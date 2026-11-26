```{index} !friction, !impratio, !noslip_iterations
```

## 抓得住却慢慢滑，该调哪一项？

1. 抓起后，在目标接触保持激活的时段，记录接触点切向相对速度、法向与切向力、物体位姿。先查 [`condim`](condim.md) 有没有相应分量，以及负载是否一直由预期的指腹承担。
2. 如果切向需求已经逼近有效摩擦锥的边界，检查有效 `friction` 和法向载荷。再核对接触点的位置和力矩需求，尤其是物体一边滑一边转的情况。
3. 如果接触持续承载，摩擦还有余量，却在近静止时缓慢漂移，可以在椭圆锥下单变量对照 `impratio`。它改变摩擦方向相对法向的约束阻抗比例。也可单独对照 `noslip_iterations`，它在主求解后做额外迭代以抑制漂移。分别比较速度、位姿和释放行为。`solreffriction` 单独控制显式 pair 在椭圆锥下的摩擦恢复响应，见 {ref}`软约束 <soft-constraint-solimp>`。

[MuJoCo 摩擦参数组合](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#contact-parameters) · [MuJoCo 仿真中的缓慢滑移](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#cslowslippage) · {ref}`按现象查接触参数 <contact-tuning>`
