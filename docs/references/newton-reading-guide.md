# Newton reading guide: what do the 35 papers study?

These works study physical computation, robot learning and simulation validation. Newton can be the engine being improved, or a tool for training, data generation or comparison.

This guide covers all **35 works** in the [complete bibliography](https://huangkiki.github.io/Dexlab/en/latest/newton-publications.html), organized into seven topics. DexLab provides the topic grouping and plain-language summaries based on **abstracts and author pages checked on 2026-11-02**, not full-paper reviews or reproductions. The upstream distinction between 34 research entries and one comparison-only entry remains unchanged; external results do not count as DexLab experiment outcomes.

## Start with a question

| Question | Suggested route | What to look for |
| --- | --- | --- |
| How is contact solved, and where do gradients come from? | [Ostrich](https://arxiv.org/abs/2609.08800) → [FlashNeRD](https://arxiv.org/abs/2610.09130) | The former studies hard-contact solving and implicit gradients; the latter keeps analytical collision detection and learns robot dynamics. Examine contact detection, force computation and differentiation separately. |
| Where does simulation diverge from reality, and how can it be adjusted? | [GAUGE](https://arxiv.org/abs/2608.05948) → [Same Action, Different Outcome](https://arxiv.org/abs/2610.10801) → [RoboSimStudio](https://arxiv.org/abs/2610.18835) | Read about measurement-based evaluation, repeated-trial variability, then model and parameter calibration. |
| How can world models support action selection? | [PointCast](https://arxiv.org/abs/2609.28393) → [PileBelief](https://arxiv.org/abs/2609.22858) | Separate future-motion prediction, interaction memory and downstream action selection. Prediction accuracy alone does not establish control success. |

These routes suggest reading order, not paper-quality rankings.

## Physics engines and contact solvers · 4

| Paper | Research question |
| --- | --- |
| [Ostrich](https://arxiv.org/abs/2609.08800) | Use larger simulation timesteps under hard contact and friction, and compute gradients for action optimization. |
| [Kamino](https://arxiv.org/abs/2603.16536) | Simulate complex mechanisms with coupled joints, including kinematic loops, in parallel on a GPU. |
| [Mixed Material Point Methods](https://research.nvidia.com/labs/prl/mixed_mpm/) | Improve simulation of sand, snow and elastoplastic materials, including two-way interaction with rigid bodies. |
| [Exact Reduced Coulomb Friction](https://arxiv.org/abs/2607.19599) | Solve sticking and sliding while retaining the exact Coulomb friction law. |

## Evaluating and calibrating simulation · 7

| Paper | Research question |
| --- | --- |
| [GAUGE](https://arxiv.org/abs/2608.05948) | Use real measurements to evaluate collision, friction and deformation in physics engines and video world models. |
| [RoboSimStudio](https://arxiv.org/abs/2610.18835) | Let people and coding agents adjust solvers, contact models and parameters to match observed physical behavior. |
| [RigPI](https://arxiv.org/abs/2606.25212) | Initialize physical parameters with a vision-language model, then refine them using motion, force measurements and differentiable simulation. |
| [Informationally Decoupled Trajectory Design](https://arxiv.org/abs/2610.10905) | Choose robot motions that separate the effects of different physical parameters for more reliable identification. |
| [Same Action, Different Outcome](https://arxiv.org/abs/2610.10801) | Measure variation across repeated cloth motions and test whether simulators reproduce that variation. |
| [ContactBench 1.0](https://arxiv.org/abs/2610.24512) | Provide reproducible physical contact tasks with matching simulation assets for evaluating robot manipulation. |
| [Probabilistic Physics Digital Twin](https://arxiv.org/abs/2610.19336) | Represent uncertain mass, friction and other properties as distributions to predict possible action outcomes and their likelihoods. |

## Learned dynamics and world models · 4

| Paper | Research question |
| --- | --- |
| [FlashNeRD](https://arxiv.org/abs/2610.09130) | Keep analytical collision detection, learn faster robot dynamics and couple the robot bidirectionally to analytically simulated objects. |
| [PointCast](https://arxiv.org/abs/2609.28393) | Predict object point trajectories from robot actions. One architecture covers rigid objects, articulated objects, cloth and rope, with separate checkpoints per regime. |
| [PileBelief](https://arxiv.org/abs/2609.22858) | Retain physical evidence from previous excavation interactions to predict terrain changes and bucket volume. |
| [PhysLDM](https://arxiv.org/abs/2610.07609) | Generate volumetric deformation trajectories with latent diffusion. **Newton is used only as a comparison baseline.** |

## Cloth, rope and deformable manipulation · 6

| Paper | Research question |
| --- | --- |
| [ForwardDLO](https://arxiv.org/abs/2609.18455) | Predict rope shape changes under bimanual actions quickly enough to evaluate more planning candidates. |
| [RopeFormer](https://arxiv.org/abs/2609.23432) | Retain action-response history across trials so a fixed policy can adapt to the current rope dynamics. |
| [DefFlow](https://arxiv.org/abs/2610.22827) | Jointly predict robot and object motion to learn grasping, moving, releasing and regrasping toward a target shape. |
| [Learning Sim-Grounded Policies for Bimanual Rope Manipulation](https://arxiv.org/abs/2605.16043) | Compare image observations with simulated rope state when learning from limited bimanual teleoperation demonstrations. |
| [SIM1](https://arxiv.org/abs/2604.08544) | Reconstruct and calibrate deformable simulation from limited real demonstrations, then expand synthetic training data. |
| [High-Fidelity 4D Cloth Capture](https://graphics.cs.utah.edu/research/projects/two-level-cloth-capture-pattern/two-level-cloth-capture-pattern.pdf) | Capture detailed cloth motion using multiple cameras and printed patterns, then complete occluded regions with physical constraints. |

## Robot control and reinforcement learning · 6

| Paper | Research question |
| --- | --- |
| [Backpropagating Through Simulation](https://arxiv.org/abs/2606.21525) | Update control policies through simulation gradients and compare with sampled policy learning using PPO. |
| [AlphaNIST](https://arxiv.org/abs/2610.13354) | Learn grasping, reorientation and assembly in simulation using binary task rewards. |
| [A Balanced Data Diet](https://arxiv.org/abs/2610.12465) | Sample tasks near the policy capability frontier to reduce wasted experience in large-scale RL. |
| [GM-Loco](https://arxiv.org/abs/2609.10286) | Learn terrain-adaptive humanoid locomotion on yielding granular ground such as sand. |
| [RoboMMT](https://arxiv.org/abs/2610.26414) | Track expressive and interactive motions such as facing and pointing while maintaining dynamic balance. |
| [Spectral Skills](https://arxiv.org/abs/2609.37677) | Encode motion segments as skills that a planner can track, chain and compose for humanoid control. |

## Agents, environment creation and planning · 3

| Paper | Research question |
| --- | --- |
| [Gym-Anything](https://arxiv.org/abs/2610.40565) | Use coding agents to create robotics simulations and audit their quality in an iterative loop. |
| [GaP](https://arxiv.org/abs/2607.05369) | Have agents assemble perception, planning and control modules into executable graphs and refine them through simulated rehearsal. |
| [DetAug](https://arxiv.org/abs/2609.18395) | Augment manipulation trajectories so execution can select routes around previously unseen obstacles. |

## Application studies · 5

| Paper | Research question |
| --- | --- |
| [LUMO](https://arxiv.org/abs/2609.18165) | Design illuminated compliant finger pads whose optical response reveals contact location. |
| [PersistGS](https://arxiv.org/abs/2606.03479) | Use differentiable rigid-body simulation to track fully occluded objects in dynamic 3D reconstruction. |
| [OrchardBench](https://arxiv.org/abs/2607.06337) | Simulate apple harvesting, including branch bending, fruit detachment, foliage occlusion and plant damage. |
| [RoboFin3D](https://arxiv.org/abs/2609.37560) | Simulate robotic grinding and sanding with changes to workpiece geometry and surface appearance. |
| [SceneFactory-3D](https://arxiv.org/abs/2610.02874) | Hold traffic scenes and controllers fixed while changing road friction and grade to evaluate driving safety. |

See the [complete bibliography](https://huangkiki.github.io/Dexlab/en/latest/newton-publications.html) for full titles, authors, dates and upstream attribution.
