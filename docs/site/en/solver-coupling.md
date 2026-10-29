# How do solvers synchronize, and what does preCICE do?

Imagine one solver computing **finger motion** and another computing **sponge deformation**. Both must cover simulation time **0–10 ms** in this round: the finger runs first and takes 1 ms of computer time; the sponge then takes 100 ms. These are teaching assumptions, not engine benchmarks.

| Elapsed computer time | Finger's computed simulation time | Sponge's computed simulation time |
| --- | --- | --- |
| 0 ms | 0 ms | 0 ms |
| 1 ms | 10 ms, waiting | 0 ms |
| 101 ms | 10 ms | 10 ms |

**The user waits 101 ms, but the simulated world advances only 10 ms.** Taking a minute to generate one second of animation does not add 59 seconds to the animation. Offline, with the controller following simulation time, this waiting mainly reduces throughput; hardware control has additional real-time deadlines.

Internal steps may differ: the finger takes ten 1 ms steps, the sponge takes two 5 ms steps, and both meet at simulation time 10 ms. **Ten internal finger steps do not mean ten fresh sponge-force updates.** Computer time, internal integration steps and coupling exchange intervals are different quantities. [Aligning different step sizes](https://precice.org/couple-your-code-time-step-sizes)

Even when their times align, ask: **which sponge force did the finger use to compute that motion?**

- **Compute once and advance (one explicit coupling arrangement):** the finger reaches 10 ms using the old reaction force; the sponge computes a new force from that motion; the finger uses it in the next round. Errors from stale forces can remain even if computation is instantaneous.
- **Correct the same interval repeatedly (implicit coupling):** the sponge returns a new force, the finger recomputes 0–10 ms, and the sponge updates again until the exchanged results meet convergence requirements. Every correction concerns the same interval; it must not add another 10 ms to simulation time. Failure to converge is not a valid converged result.

Running solvers sequentially or simultaneously is separate from deciding whether to repeat an interval. Shorter exchange intervals and additional corrections may improve the interaction at a cost in computation or communication; smaller internal steps in one solver do not automatically refresh feedback from the other. [Coupling schemes](https://precice.org/configuration-coupling)

**preCICE is an open-source multiphysics coupling library—a coordinator between solvers.** Once connected, it coordinates time, communicates data, maps data between different meshes and organizes iterative corrections as configured. For water hitting a flexible plate, a fluid program computes pressure and a structural program computes deformation; preCICE coordinates their exchange. The solvers and their integration still determine the physical equations, contact and friction. [Official introduction](https://precice.org/docs.html)

For grasping, old forces may remain close to current forces when contact changes slowly; rolling, slipping and finger changes need timely, complete feedback. Slow computation alone does not establish that in-hand manipulation is impossible, and successful holding does not establish reliable finger changes. preCICE is a methodological reference here: connecting MuJoCo, SuperDex or other engines still requires adapters and validation. This primer does not establish a DexLab preCICE integration or imply that RSS uses it. [RSS coupling source analysis and discussion](https://github.com/huangkiki/Dexlab/discussions/220#discussioncomment-19056253)
