# <span lang="en">Contact and Friction Simulation for Computer Graphics</span>：<br><span lang="zh-CN">计算机图形学中的接触与摩擦仿真</span>

Sheldon Andrews, Kenny Erleben, Zachary Ferguson · ACM SIGGRAPH 2022 Courses, Article 3, pp. 1–172

{ref}`Paper Sharing <contact-friction-siggraph-2022>` · [作者版讲义 Course notes PDF][notes] · [课程网站 Course website](https://siggraphcontact.github.io/) · [ACM 出版页 ACM publication](https://doi.org/10.1145/3532720.3535640)

<p lang="en">A block on a table can slide because the contact was missed, because the friction model permits it, or because the solver stopped early. This DexLab companion works through those three cases with numbers. The examples are calculations for the stated models. The linked DexLab experiments are separate measurements.</p>

<p lang="zh-CN">桌上的方块滑了，可能是引擎漏了接触，也可能是摩擦模型本来就允许它滑，或是求解器提前结束了迭代。下面用带数字的例子把三种情况拆开。文中的算例都有明确的模型假设，链接里的 DexLab 实验则提供实际测量。</p>

## What happens in one step · 一步仿真里发生了什么

<p lang="en">For a velocity-level, hard-contact step, first apply external forces to obtain a predicted velocity. Collision detection supplies contact locations and directions. The contact Jacobian converts body velocities to relative velocities at those locations. The solver chooses impulses and maps them back to the bodies. The same impulse can affect several contacts through the bodies they share.</p>

<p lang="zh-CN">用速度层的硬接触步进作例子。先把重力、推力等外力加进去，得到预测速度。碰撞检测提供接触的位置和方向，接触雅可比把刚体的速度换算成各接触点的相对速度。求解器再找出接触冲量，把它们传回刚体。同一个冲量可以通过共有的刚体影响多个接触点。</p>

$$
\begin{aligned}
v^\star &= v+hM^{-1}f,\\
v^+ &= v^\star+M^{-1}J^\top\lambda.
\end{aligned}
$$

<p lang="en">Here h is the timestep, M the mass matrix, f the external generalized force, J the contact Jacobian, and λ the contact impulse. At a closed, inelastic contact with no stabilization term, the outgoing normal speed w is nonnegative, the normal impulse is nonnegative, and their product is zero. A contact can push back while holding the normal speed at zero. If the bodies are already separating, no normal impulse is needed.</p>

<p lang="zh-CN">这里 h 是时间步，M 是质量矩阵，f 是外部广义力，J 是接触雅可比，λ 是接触冲量。对已经闭合的完全非弹性接触，且省略稳定化项时，求解后的法向相对速度 w 和法向冲量都非负，两者乘积为零。接触可以用正冲量把法向速度托在零。如果物体自己就在分离，就不需要再推一把。</p>

$$
\begin{aligned}
w &= J_n v^+,\\
w &\ge 0,\quad \lambda_n\ge 0,\quad w\lambda_n=0.
\end{aligned}
$$

[§1.2 时间积分 / Time integration][integration] · [§1.4 不穿透约束 / Non-penetration][normal]

## Missed contacts · 物体穿过了表面

<p lang="en">Imagine a point starting 8 mm above a 2 mm thick sheet and moving down at 1.5 m/s. In a 10 ms step it travels 15 mm and ends 7 mm below the top face. Both sampled positions are outside the sheet, so an endpoint-overlap test can miss the crossing. The first continuous hit is at about 5.33 ms. With 5 ms steps, the 5 ms sample is still 0.5 mm above the sheet and the 10 ms sample is already past it. With 2 ms steps, the 6 ms sample sits 1 mm inside the sheet and an endpoint test can detect the overlap.</p>

<p lang="zh-CN">一个点从厚 2 mm 的薄板上方 8 mm 出发，以 1.5 m/s 向下运动。10 ms 里它走了 15 mm，步末落在板上表面之下 7 mm。步首和步末都在板外，只检查端点重叠就可能漏掉穿越。连续轨迹约在 5.33 ms 首次碰到板。步长减到 5 ms 时，5 ms 的采样点仍在板上方 0.5 mm，10 ms 的采样点已经越过板。步长减到 2 ms 时，6 ms 的采样点在板内 1 mm，端点检查就有机会发现这次重叠。</p>

<p lang="en">Capture the first crossing step and read back the collision pair, separation and normal. A missing pair with a verified geometric crossing puts detection first. If the solver received the pair with the wrong normal, inspect collision geometry and orientation before changing iterations. If it received a plausible pair and velocity still points into the surface, inspect the normal response and that engine’s tolerance or compliance. A plane represented as a solid half-space can report penetration at the endpoint, unlike the finite sheet in this example.</p>

<p lang="zh-CN">记录第一次穿越发生的步，读出碰撞对、间距和法向。如果几何上确认穿越、但没有碰撞对，先查检测。如果有碰撞对但法向错了，先查碰撞几何和朝向。如果碰撞对和法向都合理、求解后仍朝表面内部运动，再查法向响应，以及引擎的容差或柔顺性。把地面建成实心半空间时，步末位置本身就可能被判为穿透，这与算例中的有限厚度薄板不同。</p>

[§2 接触生成 Contact generation（p. 41）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=41) · [§2.2.1 连续碰撞检测 Continuous collision detection（p. 49）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=49)

## Stick, slip, and jitter · 黏滑和静止抖动

<p lang="en">Take a 1 kg block initially at rest on a horizontal plane. Assume no tipping, a 10 ms step, gravity of 9.81 m/s², and the same isotropic coefficient of 0.4 for the ideal sticking limit and sliding friction. Supporting the block takes 0.09810 N·s of normal impulse per step. Its friction budget is 0.03924 N·s. Below that budget, friction can exactly cancel the push. Above it, the remaining impulse produces sliding.</p>

<p lang="zh-CN">取一个静止在水平面上的 1 kg 方块。假设不会翻倒，步长 10 ms，重力加速度 9.81 m/s²，理想黏着上限和滑动摩擦共用各向同性系数 0.4。每步托住它需要 0.09810 N·s 的法向冲量，摩擦冲量上限是 0.03924 N·s。推力引起的冲量低于这个上限时，摩擦可以刚好抵消推力。超过上限时，剩余冲量会让它开始滑。</p>

$$
\begin{aligned}
\lVert\lambda_t\rVert &\le \mu\lambda_n,\\
\lambda_n &= mgh,\quad \lambda_{\rm push}=Fh.
\end{aligned}
$$

| 推力 / Push | 推力冲量 / Push impulse | 摩擦冲量大小 / Friction magnitude | 步末切向速度 / End speed |
| --- | --- | --- | --- |
| 3 N | 0.03000 N·s | 0.03000 N·s | 0 m/s |
| 5 N | 0.05000 N·s | 0.03924 N·s | 0.01076 m/s |

<p lang="en">This gives a debugging measurement. If the 3 N case slides, compare measured support and tangential impulse in the first slipping step. Low normal support can shrink the available friction even when μ is correct. Adequate support and too little tangential impulse instead point to the effective friction law, regularization, or solver accuracy. A real engine can also report a force or a sum across substeps. Compare quantities over the same interval and in the same contact frame.</p>

<p lang="zh-CN">用这组数字来排查。如果 3 N 那组也滑了，先比第一次滑动那一步的法向支撑和切向冲量。即使 μ 填对了，法向支撑偏低也会缩小可用摩擦。如果支撑足够、切向冲量却偏小，再查实际生效的摩擦模型、正则化或求解精度。引擎可能读出的是力，也可能是多个子步的累积冲量，比较前要对齐时间窗和接触坐标系。</p>

[§1.5 库仑摩擦 Coulomb friction（p. 18）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=18) · [§3 数值方法 Numerical methods（p. 60）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=60) · [DexLab 滑块实验 / Sliding-block experiment](complementarity-contact-models.md)

## Solver iterations · 两个接触为什么会互相拖累

<p lang="en">Stack two 1 kg blocks at rest, touching each other and a fixed floor. Use a 10 ms step, solve only the normal direction, start both impulses at zero, and sweep the floor contact before the block-to-block contact. Each predicted velocity is −0.09810 m/s. The floor contact first stops the lower block. The upper contact then pushes the upper block up and the lower one back down. The floor constraint is violated again after that one sweep.</p>

<p lang="zh-CN">把两个 1 kg 方块叠在固定地面上，初始静止、两个接触都闭合。取 10 ms 的步长，只解法向，两个冲量都从零开始，每轮先算地面接触再算方块间接触。两个预测速度都是 −0.09810 m/s。地面接触先停住下方块。随后方块间的接触冲量把上方块往上推，也把下方块又往下推了一点。一轮扫完，地面约束再次被违反。</p>

$$
\begin{aligned}
\lambda_{\rm floor} &\leftarrow \max(0,\,mgh+\lambda_{\rm stack}),\\
\lambda_{\rm stack} &\leftarrow \max(0,\,\lambda_{\rm floor}/2).
\end{aligned}
$$

| 迭代轮 / Sweeps | 地面冲量 / Floor impulse | 下方块速度 / Lower block velocity |
| --- | --- | --- |
| 1 | 0.098100 N·s | −0.049050 m/s |
| 4 | 0.183938 N·s | −0.006131 m/s |
| 8 | 0.195434 N·s | −0.000383 m/s |
| 精确解 / Exact | 0.196200 N·s | 0 m/s |

<p lang="en">The floor impulse converges toward the weight of both blocks integrated over the step. The lower block’s approach speed is halved each sweep for this ordering. If a finite solve is followed by a position update, residual approach speed can create overlap. Real solvers can change the result through contact ordering, warm starts, compliance, or stabilization. Hold the geometry, model and timestep fixed when testing whether a tighter solve improves support, and read both the residual and the block motion.</p>

<p lang="zh-CN">地面冲量逐步逼近两个方块的总重力在这一步内形成的冲量。按这个顺序，每扫一轮，下方块向地面逼近的速度减半。有限轮求解后若直接更新位置，这个残余速度可能造成穿透。引擎里的接触排序、热启动、柔顺性和稳定化都会影响结果。要判断加迭代能否改善支撑，固定几何、模型和时间步，同时看残差和方块实际运动。</p>

[§3.2 固定点方法 / Fixed-point methods][splitting] · [§3.3 非光滑牛顿方法 / Nonsmooth Newton methods][newton]

## Deformable contact · 软体、布料和绳子的接触

<p lang="en">Reduce the scene to one deformable patch or short strand touching a simple surface. Compare how the material deforms in free motion and what changes at contact. If it is already unstable before impact, inspect the material and time integration first. If the change starts at impact, use the chapters on deformable contact and penalties or barriers to decide what to measure next.</p>

<p lang="zh-CN">把场景缩到一小片布或一小段绳与简单表面接触。先比较自由运动中的变形和碰到表面后发生的变化。碰之前就不稳，先查材料和时间积分。变化从接触那一刻才开始，再借软体接触、罚函数和屏障法的章节，决定下一步测什么。</p>

<p lang="en">A single undamped spring shows why contact-free testing matters. With mass 0.01 kg and stiffness 1,000 N/m its angular frequency is about 316 rad/s. For this linear oscillator, semi-implicit Euler has bounded oscillations when 0 &lt; hω &lt; 2. A 10 ms step gives hω ≈ 3.16 and an unstable update. A 5 ms step gives about 1.58 and bounded oscillation, with phase error. No contact forces enter this calculation.</p>

<p lang="zh-CN">一根无阻尼弹簧就能说明为什么要先测无接触。质量 0.01 kg、刚度 1,000 N/m 时，角频率约为 316 rad/s。对这个线性振子，半隐式欧拉在 0 &lt; hω &lt; 2 时振幅有界。10 ms 得到 hω ≈ 3.16，更新会发散。5 ms 得到约 1.58，振荡有界，但相位仍有误差。这个算例里根本没有接触力。</p>

<p lang="en">For cloth, first compare strain and fold shape in free motion, then add one rounded obstacle and record the first change in minimum gap and contact impulse. For rope, also vary segment length while keeping its physical radius fixed. A coarse proxy and an integration failure can both look like penetration. An observed gap change at first contact, together with a working free-motion baseline, narrows the next test to geometry, collision detection, or response.</p>

<p lang="zh-CN">布料先对照自由运动时的应变和褶皱，再加一件圆滑障碍物，记录最小间距和接触冲量第一次变化的时刻。绳子还可以固定物理半径，只改变离散段长。碰撞代理太粗和积分失稳看起来都可能像穿透。自由运动先通过，再看首次接触附近的间距变化，就能把下一轮排查缩到几何、检测或响应。</p>

[§4 软体接触 Soft-body contact（p. 110）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=110) · [§5 罚函数与屏障法 Penalties and barriers（p. 131）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=131) · [DexLab 布料对照 / Cloth comparison](cloth-comparison.md)

## Choosing a model · 何时看硬约束、罚函数或屏障

<p lang="en">For a hard velocity constraint, inspect post-solve approach speed and normal impulse. For a simple spring penalty, the repulsion comes from overlap. Static balance with a 1 kg block and a linear normal stiffness of 10,000 N/m needs about 0.98 mm of compression, even with a converged solve. Raising stiffness reduces that equilibrium overlap and makes the fastest contact dynamics harder to integrate. An IPC-style barrier instead preserves feasibility through its distance potential and a collision-aware line search. Chapter 5 shows how that method couples the choice of contact model to the time-step optimization.</p>

<p lang="zh-CN">硬速度约束优先看求解后的逼近速度和法向冲量。简单的弹簧罚函数用压入产生斥力。1 kg 方块、法向线性刚度 10,000 N/m 时，即使求解收敛，静力平衡也需要约 0.98 mm 压入。调高刚度会减小这个平衡压入，也会提高接触振动的频率，让积分更难。IPC 一类方法通过间距势能和带碰撞检查的线搜索保持可行性。讲义第 5 章把这些模型选择和时间步内的优化放在一起讲。</p>

[§5.3 IPC（p. 138）][ipc-chapter] · [IPC 原论文 / Original IPC paper][ipc]

## Direction-dependent friction · 同一表面换个方向就滑了

<p lang="en">Keep the 1 kg block and horizontal plane. Suppose the measured sticking limits along two material axes correspond to coefficients of 0.25 and 0.55. The same 4 N pull exceeds the 2.45 N limit along the first axis and remains below the 5.40 N limit along the second. One coefficient cannot match both outcomes on this setup. When testing a simulated fabric or textured surface, rotate the material axes by 90° and keep load, pull speed, geometry, and the solver budget fixed. If the preferred slip direction rotates with the material, test a directional friction model before tuning a global coefficient.</p>

<p lang="zh-CN">还是 1 kg 方块和水平面。假设材料两个主轴方向测到的黏着上限，分别对应 0.25 和 0.55 的摩擦系数。同样的 4 N 拉力，超过第一轴的 2.45 N 上限，却低于第二轴的 5.40 N 上限。一个各向同性系数无法同时匹配这两个结果。测布料或有纹理的表面时，可以只把材料主轴旋转 90°，固定法向载荷、拉动速度、几何和求解预算。如果容易滑的方向跟着材料一起转，先对照方向相关的摩擦模型，再调全局系数。</p>

[§6 各向异性摩擦 / Anisotropic friction（p. 146）][anisotropy]

## Follow a full step in code · 沿着代码读完一步

<p lang="en">The appendix and its C++ starter project let you trace one rigid-body step from integration and contact generation to the contact Jacobian and a projected Gauss–Seidel solve. The code is a guided exercise with TODOs.</p>

<p lang="zh-CN">附录和配套的 C++ 起始项目，适合顺着代码读完一个刚体时间步。从积分、生成接触点，到组装接触雅可比，再用投影高斯–赛德尔法求解。代码里的 TODO 对应讲义的练习步骤。</p>

[附录 Appendix（p. 160）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=160) · [作者配套代码 Course exercise](https://github.com/siggraphcontact/rigidBodyTutorial)

[notes]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf
[integration]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=10
[normal]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=14
[splitting]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=68
[newton]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=85
[ipc-chapter]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=138
[ipc]: https://ipc-sim.github.io/
[anisotropy]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=146
