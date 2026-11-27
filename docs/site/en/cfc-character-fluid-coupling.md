# CFC: how characters and fluid interact, and what the 3× and 8× speedups measure

CFC connects two models through joint-level loads. When a character lifts a foot through muddy water, the fluid model advances the water and estimates how it pushes and drags on the body. The character model predicts how the body then moves under those loads and its action. The published paper reports two training speedups. **For 10,000 training iterations, CFC is 2.93× faster on Directional Control and 3.14× on Location. For Directional Control at a normalized task return of 0.9, it takes 4.3 hours instead of 34.5 hours, a speedup of 8.02×.** [ACM TOG version of record, §4.4, Table 5 and Figure 15](https://doi.org/10.1145/3763318)

The paper by Dou, Peng et al. appeared at SIGGRAPH Asia 2025 in ACM TOG 44(6), Article 199. The authors provide figures, animation demos and slides. They use the open-source SPlisHSPlasH simulator for training reference data. The official materials reviewed contain no release of the complete CFC implementation, trained weights or training data. [Paper](https://doi.org/10.1145/3763318) · [Authors’ project page](https://frank-zy-dou.github.io/projects/CFC/)

## What does the water model compute, and what does the body model compute?

The inputs include the current character pose and velocity, the fluid particles’ positions and velocities, and a control goal. The rigid-body surfaces are also sampled as particles, so movement changes the boundary seen by the fluid model. Shared particle-wise MLPs and a one-dimensional convolution over neighbors predict a particle velocity update. Gravity and the updated velocity advance the fluid particles. Training uses SPH velocity supervision and loss terms for viscosity, incompressibility and a fluid–solid barrier. The barrier enters the fluid training loss. Surface loads are calculated separately from pressure and viscosity terms evaluated on the predicted particles. [Paper, §3.1 and Figure 4](https://doi.org/10.1145/3763318)

![Figure 3. The character and fluid models are connected by joint-level loads](https://frank-zy-dou.github.io/projects/CFC/figs/fig_world_model_method.png)

*Figure 3. The fluid model advances the particles. The character model advances the body given an action and external loads. The updated body state feeds the next fluid prediction.* [Authors’ figure](https://frank-zy-dou.github.io/projects/CFC/)

For each body segment, the method computes pressure and viscous friction on its surface particles, then sums the force and the moment about the joint. The lever arm $\mathbf r_i$ runs from the joint center to surface particle $i$. These two sums describe how the fluid pushes and turns that part of the body.

$$
\mathbf F=\sum_i(\mathbf f_i^p+\mathbf f_i^\nu),\qquad
\mathbf M=\sum_i\mathbf r_i\times(\mathbf f_i^p+\mathbf f_i^\nu).
$$

The character model uses the current body state, action and external loads to predict linear and angular accelerations, which are integrated into the next state. Its joint-load input makes it possible to pretrain on random perturbations in dry simulation. The high-level policy sees fluid particles within 3 meters of the character and produces a skill code and a residual action. A frozen low-level ASE controller supplies a dry motion skill. The residual adapts it to fluid loads. During training, task gradients flow back through predicted trajectories to the high-level policy. The character model is updated in alternation with the policy using newly collected data. [Paper, §3.1–3.3 and Figures 2–3](https://doi.org/10.1145/3763318)

## What does each speedup measure?

| Source | Fixed condition | SPH baseline | CFC | Recomputed speedup |
| --- | --- | ---: | ---: | ---: |
| Table 5, Directional Control | 10,000 training iterations | 30.30 min | 10.35 min | **2.93×** |
| Table 5, Location | 10,000 training iterations | 30.62 min | 9.76 min | **3.14×** |
| Figure 15, Directional Control | High-level policy reaches a normalized task return of 0.9 | 34.5 h | 4.3 h | **8.02×** |
| Table 2 row 10 and Figure 9, fluid forward simulation | Same 0.04 s of simulated time, 563,200 particles, with a character | 0.42 FPS | 6.95 FPS | **16.55×** |

![Figure 15. Normalized task return over high-level Directional Control training time](https://frank-zy-dou.github.io/projects/CFC/figs/fig_training_speed.png)

*Figure 15. The horizontal axis measures training hours and the vertical axis measures normalized task return. The authors associate 0.9 with visually appealing motion.* [Paper, §4.4 and footnote 5](https://doi.org/10.1145/3763318)

Table 5 includes simulation, policy training and world-model update overhead. The paper does not give a full budget covering data generation, low-level training and all pretraining. Figure 15 covers Directional Control alone. Iteration and sample counts at the threshold and a timing breakdown are unavailable, so the 8× gain cannot be apportioned between faster iterations and fewer iterations to the threshold. The high-level training setup caps all methods at 256 environments. [Paper, §4.1 and §4.4](https://doi.org/10.1145/3763318)

Table 2 aligns all methods to 0.04 s of simulated time. CFC takes one step, DiffFR takes 10 substeps, and SPH takes 100. Across all ten rows, the FPS ratio relative to SPH is about **7.4–16.6×** in the six scenes with a character and **1.9–2.3×** in the four without one. Figure 9’s reported 15× applies to the high-particle-count character setting. These timings include differences in stable time steps and execution paths. [Paper, §4.2, Table 2 and Figure 9](https://doi.org/10.1145/3763318)

## What was varied, and which components still need ablation?

| Published evidence | What changed | Result and scope |
| --- | --- | --- |
| Table 1 and Figures 6–8 | Viscosity, prediction horizon and fluid time step, with SPH as reference | At low viscosity $\nu=0.01$ and a 0.04 s time step, position RMSE grows from **0.0102 m** to **0.4880 m** as the horizon goes from 0.04 s to 0.20 s. The middle time-step row says 0.004 s while the caption says 0.001 s. This article uses the row values. |
| Figures 12–14 and Table 4 | Figure 12 uses the same controller and force scale while sweeping $\nu=0.01/0.05/0.1$. Figure 14 uses 1,500 frames for each wet and dry setting | In Directional Control, foot height rises from **0.061±0.009 to 0.119±0.044 m** and knee height from **0.403±0.012 to 0.443±0.047 m**. This is a scenario-specific motion response, with frames as the unit of observation. |
| Table 3 | Motion diversity of CFC and the dry ASE and AMP baselines over 30 exported clips | Four-second APD is **99.87 / 71.62 / 83.43** for Re-locating Control and **97.56 / 75.73 / 92.42** for Directional Control, in CFC / ASE / AMP order. Environments and rewards differ across systems, so the scores cannot isolate individual components. |
| Figures 16–18 | Human perception ratings, two-character self-play and a quadruped Ant demo | 42 participants gave 210 ratings, of which **185 were at least 3 out of 4**. The two-character and quadruped demos show simulated animation. Load fidelity and physical robot transfer need independent measurements. |

The version of record provides no controlled comparison that replaces only the joint-load interface, swaps in a monolithic world model, removes individual physics losses, disables the motion prior, residual or behavior rewards, or holds the character-model update strategy fixed. The wet/dry comparisons and viscosity sweeps vary the environment. In Table 1 and Figure 6, faster, less damped particles at low viscosity drift from SPH during rollout. In Figure 7, large errors often appear around the most dynamic regions. The earliest measured discrepancy is in the fluid state. Synchronized contact locations, joint moments, policy gradients and task outcomes would be needed to trace any downstream control effect. [Paper, §3, §4.2–4.3 and §5–7](https://doi.org/10.1145/3763318)

## What DexLab can test first

Pushing a door near its hinge and pushing at its handle with the same force turn it differently. The analogy illustrates how the lever arm changes the moment. For Wuji grasping, an external-load record also needs the link or contact surface, coordinate frame, time interval and moment. Two contact states can give the same recorded force yet respond differently to unloading.

For the existing Wuji contact study, start from the same grasp state and apply $a+\epsilon v$ and $a-\epsilon v$ along a single finger’s unloading direction $v$. Measure the task quantity on both sides in the native solver and compare the resulting direction with the surrogate gradient.

$$
D_{\epsilon}^{\mathrm{native}}J =
\frac{J_{\mathrm{native}}(a+\epsilon v)-J_{\mathrm{native}}(a-\epsilon v)}
{2\epsilon},\qquad
D^{\mathrm{model}}J=\nabla_a J_{\mathrm{model}}(a)^\mathsf{T}v.
$$

Record the load history and contact transitions first. Call the direction resolved only if both replays stay in comparable contact phases, the difference exceeds native repeat variability, and the sign holds across multiple perturbation magnitudes. If the model agrees, test whether its suggested action improves the predefined task quantity in native replay. The paper supports a speed gain in simulated training. It leaves this native finite-difference check open. In DexLab, the check remains within the existing contact study, pending qualified native repeats and paired interventions. [DexLab contact response diagnosis](contact-response.md) · [Research issue #261](https://github.com/huangkiki/Dexlab/issues/261)
