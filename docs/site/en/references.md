# External references

Reading on research context and evaluation methods. External experiments are identified separately from DexLab results and do not count toward this project's engine coverage or passes.

## Manda Robotics: comparing physics engines

What should be compared when a task runs in different simulation configurations? The [reading guide](manda-physics-engines.md) provides configuration identities, navigation, terminology and limits, with links to the original figures and interactive replays.

The article was published on 2026-10-05; the guide was checked on 2026-10-08. This is an original summary and commentary, without republishing the complete article, figures or website code.

[Original article](https://mandarobotics.com/blog/comparing-physics-engines/index.html) · [Repository reference directory](https://github.com/huangkiki/Dexlab/tree/main/docs/references)

## UniCross: continuous skill transitions

The [reference review](unicross.md) examines the question of transitioning between manipulation skills without resets, alongside existing in-hand rotation work. Review depth is limited to the project page and arXiv abstract/metadata; source, controller, assets and native parameters remain unqualified. This is a reference and reuse/defer decision, not a runnable benchmark or a DexLab reproduction.

## Compare with DexLab's own evidence

- [Engines and models](engines.md): versions, solver configurations and modeling assumptions.
- [Research results](results.md): this project's frozen protocols, raw records and failed cases.

Turn related work into checkable questions: do imported models match, how are feedback inputs generated, when are forces and impulses recorded, and how are task failures distinguished from numerical invalidity? External parameters and results do not automatically become project acceptance criteria.

```{toctree}
:maxdepth: 1

Manda engine-comparison guide <manda-physics-engines>
UniCross reference review <unicross>
```
