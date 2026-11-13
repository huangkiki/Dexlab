# 接触、摩擦与求解：先分清三层

**接触模型规定能产生什么力与力矩；求解器决定怎样求出这些量；积分器决定状态怎样向前走。** 换求解器，不能凭空补出模型没有允许的力矩方向。

## 两个手指为什么夹不稳球？

想象两个理想点接触夹住球。每个点可以施加力，但自身不传递接触力矩。两个点的力不能产生绕两点连线的力矩；当重力对这条轴产生力矩时，单纯增加夹紧力未必能阻止转动。

像用一根理想轴穿过球：沿轴方向的转动没有被点力限制。这个类比只解释一个瞬时几何方向，不代表真实手指固定不动，也不意味着所有双点抓取必然失败。

## 分清改动属于哪一层

- **模型：** 接触法向、摩擦方向、接触维数与软约束参数决定当前问题。`condim` 改变允许的接触分量；滑动、扭转和滚动不是同一个系数的三个别名。
- **数值求解：** MuJoCo 的 PGS、非线性 CG、Newton 在给定模型下求解约束问题。迭代预算、容差与 warmstart 影响近似解和成本。
- **时间推进：** 步长和积分器影响状态演化。更小的求解残差，不等于更小的轨迹误差，更不等于材料更真实。

<details class="explanation"><summary>读懂 condim，不把它当质量档位</summary>
<p><code>condim=1</code> 只有法向分量；3 增加两个切向滑动分量；4 再增加绕法向的扭转分量；6 再加入两个滚动分量。数值更大表示模型允许更多接触分量，并不表示任何任务都更准确。</p>
<p>扭转、滚动摩擦系数涉及长度尺度，不能直接拿无量纲滑动摩擦系数的数值套用。还要核对接触对的实际组合参数与原生读回，而不只看某一个 geom 的 XML。</p>
</details>

## 自测：先查模型，还是先加迭代？

```{raw} html
<form class="quiz" data-answer="a" data-correct="对。先确认模型是否允许所需的力矩，再判断数值求解是否足够。" data-incorrect="迭代次数和容差只能影响给定问题的求解，不能添加被模型排除的接触力矩。">
  <fieldset><legend>点接触模型没有扭转力矩分量，物体绕接触连线转动。下一步最有判因价值的是？</legend>
  <label><input type="radio" name="contact" value="a">检查力矩需求、接触几何与实际接触分量</label>
  <label><input type="radio" name="contact" value="b">直接把迭代次数增加十倍</label>
  <label><input type="radio" name="contact" value="c">换一个渲染器观察</label></fieldset>
  <button type="submit" data-enhanced hidden>检查答案</button><p class="quiz-feedback" role="status" hidden></p>
</form>
<details><summary>查看解释</summary><p>先查模型与力矩需求。若记录显示模型已经有足够的力矩能力，但实际解仍有大残差，再设计数值求解对照。不能从掉落结果直接跳到 solver 缺陷。</p></details>
```

## 从现象走向证据

记录接触点、法向与切向力、接触内禀力矩、物体速度，以及执行器饱和或其他支撑。按时间检查接触何时建立、何时承载、何时发生异常。只有把这一链串起来，才知道下一次应该改模型、控制还是求解。

本站已有 [Wuji 点接触与扭转接触案例](../wuji-contact.md)。最后一课会回到它的测量和边界。

继续读：[软接触与摩擦锥](../learn/mujoco/docs/contact-models.md) · [求解器与积分器](../learn/mujoco/docs/solvers-and-integration.md) · [力观测](../learn/mujoco/docs/force-observations.md) · [官方接触维数说明](https://mujoco.readthedocs.io/en/4.0.0/computation/index.html#condim)
