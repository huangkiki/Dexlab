# DexLab

**Contact-rich robot manipulation, beyond rigid-body simulation.**

[Research overview](https://huangkiki.github.io/Dexlab/en/latest/index.html) · [Experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Research distillation](https://huangkiki.github.io/Dexlab/en/latest/distillation.html) · [Sim-to-Real Gap](https://huangkiki.github.io/Dexlab/en/latest/failure-root-cause-atlas.html) · [Learn simulation](https://huangkiki.github.io/Dexlab/en/latest/learning.html)

DexLab is my personal research project exploring how Agent Skills and simulation can improve each other.

A grasp can fail because of the policy or because the simulator does not handle contact and friction accurately.

DexLab starts with concrete problems like this. **Use tasks to expose problems, run controlled experiments to identify their causes, then improve the relevant part of the simulation.**

The improved simulation helps the Agent learn new Skills. With those Skills, the Agent can take on harder tasks and probe the limits of the simulation.

<p align="center">
  <a href="https://huangkiki.github.io/Dexlab/en/latest/index.html">
    <img src="docs/site/_static/images/dexlab-architecture.webp" width="100%" alt="DexLab architecture: tasks and protocols, systems under test, action execution, environment backends, and evidence and scoring">
  </a><br>
  <sub>DexLab platform architecture. <a href="https://huangkiki.github.io/Dexlab/en/latest/coverage.html">See validation by task and engine.</a></sub>
</p>

## Selected experiments

- **Contact model changes the verdict:** point versus torsional contact in a two-finger sphere grasp.
- **Cutting is checked beyond the animation:** tofu and banana records verify piece connectivity, contact impulse and independent motion.
- **A grasp is not a fold:** cloth experiments score deformation, penetration, residual motion and release separately.
- **Engines are compared per profile:** six-engine incline results retain failures and validity checks instead of producing a ranking.

[Browse all experiments →](https://huangkiki.github.io/Dexlab/en/latest/experiments.html)

## Evidence boundary

There are currently **no hardware experiments**. “Physical correctness” here means reproducible consistency inside a frozen simulation model: auditable inputs, analytic or engineering references, positive and negative controls, conservation checks and regression after each declared parameter change. It does not claim real-material calibration or sim-to-real accuracy.

[Read the validation boundary →](https://huangkiki.github.io/Dexlab/en/latest/index.html#physical-validity)

## Citation

```bibtex
@software{dexlab2026,
  author  = {Kiki Huang},
  title   = {DexLab: A Physics-Centric Research Platform for Contact-Rich Robot Manipulation},
  year    = {2026},
  url     = {https://github.com/huangkiki/Dexlab}
}
```

[Email](mailto:huangyue0719@outlook.com) · [GitHub](https://github.com/huangkiki)
