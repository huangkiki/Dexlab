(external-references)=
# Research guides and references

```{toctree}
:maxdepth: 1
:caption: In this section

Dexterous-hand simulation guide <dexterous-hand-simulation>
Newton topic reading guide <newton-reading-guide>
Publications using Newton <newton-publications>
Manda engine-comparison guide <manda-physics-engines>
UniCross reference review <unicross>
Roadmap <dexterity>
```

Reading on research context and evaluation methods. External experiments are identified separately from DexLab results and do not count toward this project's engine coverage or passes.

## Start with the questions behind dexterous-hand simulation

[What are we discussing when we discuss dexterous-hand simulation?](dexterous-hand-simulation.md) starts with rotating a bottle and connects six layers: tasks, bodies, physics, sensing, policies and validation. It introduces seven representative papers alongside DexLab's holding, wiping and cloth cases, providing context before choosing an engine or reading individual papers.

## Publications using Newton

[The topic guide](newton-reading-guide.md) explains all 35 papers across seven topics, with routes through contact and differentiation, simulation calibration, and world models. Each entry has a plain-language summary and source link; the reading scope is abstracts and author pages.

The [complete publication index](newton-publications.md) includes all 35 works in Newton's official `PUBLICATIONS.md` snapshot checked on 2026-11-02: 34 research entries and one comparison-only entry. It preserves paper titles, authors, dates and source links, with attribution to The Newton Developers under CC BY 4.0. This is an external bibliography, not a record of DexLab reproductions.

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
