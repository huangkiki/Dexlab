# <span lang="en">Contact and Friction Simulation for Computer Graphics</span>：<br><span lang="zh-CN">计算机图形学中的接触与摩擦仿真</span>

Sheldon Andrews, Kenny Erleben, Zachary Ferguson · ACM SIGGRAPH 2022 Courses, Article 3, pp. 1–172

{ref}`Paper Sharing <contact-friction-siggraph-2022>` · [作者版讲义 Course notes PDF][notes] · [课程网站 Course website](https://siggraphcontact.github.io/) · [ACM 出版页 ACM publication](https://doi.org/10.1145/3532720.3535640)

<p lang="en">DexLab’s reading guide starts with a practical question. If an object moves through a surface, jitters at rest, or slides when it should stick, what should you measure before changing a parameter? The course provides a way to work through the problem in order. Check which contacts were detected, how the model represents them, and how the solver computes the response.</p>

<p lang="zh-CN">这份 DexLab 导读从一个调参问题出发。物体穿过去、静止时抖动，或者该黏住却在滑，改参数前该先测什么？讲义提供了一个排查顺序。先看引擎检测到了哪些接触，再看模型如何描述这些接触，最后看求解器算出了怎样的响应。</p>

## Missed contacts · 物体穿过了表面

<p lang="en">Check whether the collision system reports a contact at the step where the object crosses the surface. If the contact is missing, log the separation at successive steps and compare a smaller timestep or continuous collision detection when the engine supports it. If contacts are present, check the reported normals and separations before comparing solver settings.</p>

<p lang="zh-CN">先看跨过表面的那一步有没有生成接触。如果没有，记录相邻步的间距，对照更小的时间步，或试试引擎支持的连续碰撞检测（CCD）。如果已经有接触，先核对引擎报出的法向和间距，再比较求解器设置。</p>

[§2 接触生成 Contact generation（p. 41）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=41) · [§2.2.1 连续碰撞检测 Continuous collision detection（p. 49）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=49)

## Stick, slip, and jitter · 黏滑和静止抖动

<p lang="en">Start with one block on a plane. Record its tangential velocity alongside the normal and tangential contact impulses, then compare different solver budgets with the friction model and timestep fixed. That comparison helps distinguish sensitivity to the iteration budget from the effects of changing the friction model.</p>

<p lang="zh-CN">先用一个平面上的滑块做对照。同时记录滑块的切向速度，以及接触的法向和切向冲量。固定摩擦模型和时间步，只改变求解迭代预算。这样能单独观察结果对迭代次数有多敏感，再决定是否需要对照不同的摩擦模型。</p>

[§1.5 库仑摩擦 Coulomb friction（p. 18）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=18) · [§3 数值方法 Numerical methods（p. 60）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=60) · [DexLab 滑块实验 / Sliding-block experiment](complementarity-contact-models.md)

## Deformable contact · 软体、布料和绳子的接触

<p lang="en">Reduce the scene to one deformable patch or short strand touching a simple surface. Compare how the material deforms in free motion and what changes at contact. If it is already unstable before impact, inspect the material and time integration first. If the change starts at impact, use the chapters on deformable contact and penalties or barriers to decide what to measure next.</p>

<p lang="zh-CN">把场景缩到一小片布或一小段绳与简单表面接触。先比较自由运动中的变形和碰到表面后发生的变化。碰之前就不稳，先查材料和时间积分。变化从接触那一刻才开始，再借软体接触、罚函数和屏障法的章节，决定下一步测什么。</p>

[§4 软体接触 Soft-body contact（p. 110）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=110) · [§5 罚函数与屏障法 Penalties and barriers（p. 131）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=131) · [DexLab 布料对照 / Cloth comparison](cloth-comparison.md)

## Follow a full step in code · 沿着代码读完一步

<p lang="en">The appendix and its C++ starter project let you trace one rigid-body step from integration and contact generation to the contact Jacobian and a projected Gauss–Seidel solve. The code is a guided exercise with TODOs.</p>

<p lang="zh-CN">附录和配套的 C++ 起始项目，适合顺着代码读完一个刚体时间步。从积分、生成接触点，到组装接触雅可比，再用投影高斯–赛德尔法求解。代码里的 TODO 对应讲义的练习步骤。</p>

[附录 Appendix（p. 160）](https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf#page=160) · [作者配套代码 Course exercise](https://github.com/siggraphcontact/rigidBodyTutorial)

[notes]: https://siggraphcontact.github.io/assets/files/SIGGRAPH22_friction_contact_notes.pdf
