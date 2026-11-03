/** Teaching copy is separate from the controls so both languages stay readable. */
export function clawExplainer(en: boolean) {
  const t = (zh: string, english: string) => (en ? english : zh);
  return `<section class="physics-guide" aria-labelledby="guide-title">
    <h2 id="guide-title">${t("同一爪，为什么会有不同结果？", "One grab. Why might the results differ?")}</h2>
    <p>${t("爪子碰到娃娃时，仿真要算出接触和摩擦的作用，再把运动推进一小步。求解器负责前一个问题，积分器负责后一个问题。", "When a finger touches a toy, the simulation computes contact and friction, then advances motion by one small step. The solver handles the first problem; the integrator handles the second.")}</p>
    <details><summary>${t("Newton / CG / PGS：接触怎么求解？", "Newton / CG / PGS: how is contact solved?")}</summary>
      <dl class="method-list">
        <div><dt>Newton <span>${t("牛顿法", "Newton method")}</span></dt><dd>${t("把相互影响的约束一起考虑，用梯度和曲率计算一次整体修正。每次迭代工作较多，但往往能用较少迭代接近解。这里是 MuJoCo 的算法名，不是 Newton Physics 引擎。", "Considers coupled constraints together, using the gradient and curvature to compute a joint correction. Each iteration does more work, but often fewer are needed. This is a MuJoCo algorithm, not the Newton Physics engine.")}</dd></div>
        <div><dt>CG <span>${t("非线性共轭梯度", "Nonlinear conjugate gradient")}</span></dt><dd>${t("根据当前梯度和之前的搜索方向，一步步改进整体解，不像 Newton 那样分解完整 Hessian。它不是给娃娃换一种摩擦，也不是通常用于线性方程的线性 CG。", "Improves the overall solution using the current gradient and previous search direction, without Newton’s full Hessian factorization. It changes the search method, not the toy’s friction. This is nonlinear CG, not linear-system CG.")}</dd></div>
        <div><dt>PGS <span>${t("投影高斯–赛德尔", "Projected Gauss–Seidel")}</span></dt><dd>${t("逐项修正约束力，把结果投影回允许的范围；后面的修正立即使用前面更新的值。可以想成几个接触轮流协调，再一轮轮重复。接触彼此影响很强时，少量迭代可能不够。", "Updates constraint forces in turn and projects them back into their allowed ranges. Later updates use earlier corrections immediately. Think of contacts coordinating in repeated rounds; strongly coupled contacts may need many rounds.")}</dd></div>
      </dl>
      <p>${t("三者在解同一套接触问题。计算充分时，结果可能很接近；抓到了也不能单独证明更准确。迭代次数相同，不等于计算耗时相同。", "These methods solve the same contact problem. With sufficient convergence, results may be close; catching a prize alone does not establish accuracy. Equal iteration counts do not imply equal computation time.")}</p>
    </details>
    <details><summary>${t("显式、半隐式、隐式：下一步怎么动？", "Explicit, semi-implicit, implicit: how does motion advance?")}</summary>
      <p>${t("想象娃娃被爪子挤压后开始移动。下面是课本里欧拉方法的区别：", "Imagine a toy starting to move as the claw presses it. For textbook Euler methods:")}</p>
      <dl class="method-list">
        <div><dt>${t("显式欧拉", "Explicit Euler")}</dt><dd>${t("用当前状态算加速度，用旧速度更新位置。像根据此刻的运动状态直接往前走一步。", "Compute acceleration from the current state and update position with the old velocity: advance using what is known now.")}</dd></div>
        <div><dt>${t("半隐式欧拉", "Semi-implicit Euler")}</dt><dd>${t("先更新速度，再用新速度更新位置。不是“只算一半”；关键是更新顺序不同。", "Update velocity first, then use that new velocity to update position. It is not half a solve; the update order changes.")}</dd></div>
        <div><dt>${t("隐式欧拉", "Implicit Euler")}</dt><dd>${t("要求下一步的位置、速度和力彼此一致，把这些未知量联立求解。通常更能承受刚性系统，但大步长仍可能损失细节，稳定不等于准确。", "Solve for a next position, velocity and force that agree with one another. It often tolerates stiff systems better, but large steps can lose detail: stability is not accuracy.")}</dd></div>
      </dl>
      <p><strong>${t("当前三路统一用 implicitfast，每步 2 ms。", "All three currently use implicitfast with 2 ms steps.")}</strong> ${t("MuJoCo 的 implicitfast 对部分速度相关力做隐式处理，不是对下一步位置和全部接触一起做完全隐式求解；名为 Euler 的选项则以半隐式更新为基础，默认还隐式处理关节阻尼。不能只看名字就套课本分类。", "MuJoCo’s implicitfast treats selected velocity-dependent forces implicitly; it is not a fully implicit solve over next-step positions and all contacts. MuJoCo’s Euler option uses a semi-implicit update with implicit joint damping by default. Engine names need this extra context.")}</p>
      <p>${t("所以 Newton 不等于隐式，PGS 也不等于显式。本轮只换接触求解算法，积分方法保持一致。", "Newton does not mean implicit, and PGS does not mean explicit. This experiment changes the contact solver while keeping the integration method fixed.")}</p>
    </details>
    <details><summary>${t("这次对比怎样读？", "How should I read this comparison?")}</summary>
      <p>${t("三路复制同一个完整起点，使用同一控制序列、elliptic 摩擦锥、材料、2 ms 步长和 1e-8 停止容差；迭代上限由你选择。暖启动从同一状态开始，随后由各自求解器自然更新。", "All worlds copy one complete start state and share controls, elliptic friction cones, materials, 2 ms steps and a 1e-8 stopping tolerance. You choose the iteration cap. Warm starts share the initial state, then evolve independently.")}</p>
      <p>${t("“位置差”是三路同一只未收集玩偶的最大位置距离；首次超过 1 mm 只方便定位画面，不是误差判定。回放按 50 Hz 采样。抬升是相对下爪起点的最大玩偶高度增量。耗时是本机 mj_step 平均耗时，不是单独求解器耗时或严格性能排名；迭代数取每步最慢约束岛的次数再平均。", "Position spread is the largest pairwise distance between matching uncollected toys. The first sample above 1 mm is a replay marker, not an error verdict. Replay is sampled at 50 Hz. Lift is the greatest toy-height gain from the drop state. Time is local mean mj_step time, not isolated solver time or a rigorous speed ranking. Iterations average each step’s maximum across constraint islands.")}</p>
      <p>${t("三个画面按仿真时间同步；慢设备会一起变慢，不跳过物理步。重新瞄准时继续 Newton 那一柜；原局重试会恢复下爪起点。三路结果一致也是实验结果。", "Views share simulation time; slower devices slow all views together without skipping physics steps. Re-aim continues the Newton cabinet; repeat restores the original drop state. Agreement is also a valid result.")}</p>
    </details>
    <p class="guide-source">${t("原理来源：", "Reference: ")}<a href="https://mujoco.readthedocs.io/en/3.17.0/computation/index.html" target="_blank" rel="noopener">MuJoCo 3.17 · Computation</a></p>
  </section>`;
}
