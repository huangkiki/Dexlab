# Add experiments and maintain reports

```{toctree}
:maxdepth: 1
:caption: In this section

Studio replay rendering <studio-rendering>
```

## From a question to an experiment

Start with a question that can change a decision: **question → scoring-semantics audit → minimal comparison → failure attribution → finding**. Reuse existing records and check positive controls, counterexamples and required observations before deciding to run more physics. Discussion #302 prioritizes scorer semantics; a short persistent contact sequence remains a design candidate. CHORD and model work first need repeatability and action-response evidence.

[Full research workflow](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md#research-loop) · [Current selection and recovery](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.md)

## Deliver an experiment

1. State the hypothesis, official versions, parameter provenance, approximations, budget, controls and acceptance in an issue.
2. Keep code, configuration and entrypoints in the corresponding `demos/` directory; shared scoring lives in `src/dexlab/`.
3. Save actual initial states, actions, trajectories, contacts and every outcome. Separate scoring from control and retain failures.
4. Update the experiment card and report in both languages: finding, setup, metric plots, failures, limitations and reproduction.
5. Explain reader-entry changes in the PR. Update the relevant website pages for capabilities, findings, significant failures and reproduction changes; update README when positioning, architecture, representative previews or the recommended starting point changes, or an important milestone is delivered.

## README and documentation

Organize README as purpose → findings and conditions → representative experiments → research milestones → recommended start. Each finding should explain a development decision and link nearby evidence and limits; keep architecture and full research detail on the site. Select milestones from merged commits that add a finding, reproducible evidence or a necessary research entry, explicitly labeling preparation. Toy projects such as the claw machine, interface polish and individual commits belong in demonstration pages and history, not research progress.

| Content | Where to maintain it |
| --- | --- |
| Project purpose, findings and conditions, research milestones, representative previews and the shortest start | Both READMEs; findings and previews link to evidence, and preparation is not presented as a completed experiment. |
| Navigation by reader goal | The homepage Start here section, navigation and indexes. |
| Full methods, parameters, outcomes, failures and reproduction | The relevant experiment or usage page, linked from the experiment index. |
| External papers | References, topic guides and complete bibliographies, with sources, check dates and reading depth. |
| Plans, blockers and incremental progress | Current Work, issues, PRs and releases. |

Maintain the Newton guide in `docs/references/newton-reading-guide*.md` and its bibliography in `newton-publications*.md`; language pages include that content directly. When updating the upstream snapshot, reconcile the bibliography and seven-topic guide entry sets in both languages, preserving the comparison-only marker. Abstract checks must not be presented as full-paper reviews or reproductions.

Before publication, check source pages, site navigation, language switching and README entrypoints. After merge, verify the live revision and page content. Keep code runnable and private deployment details out of public documentation.

Every figure identifies versions, units, sample size, time window, uncertainty and provenance. Retain failed cases; unmatched calibration, geometry or tuning budgets do not support fair engine rankings.

Keep six top-level entries: Getting started, Experiments, Results & diagnosis, Engines & models, Research guides and Contributing. Add pages to the relevant section’s toctree; cutting cases belong under Cutting & pushing. Give each page one toctree parent, mirror the hierarchy and filenames in both languages, and keep existing page URLs stable.

## Publishing documentation

The site uses Sphinx, MyST and PyData Sphinx Theme, with information organization inspired by [RLinf](https://rlinf.readthedocs.io/en/latest/), not its research claims. Both languages share a theme and build command, defaulting to Chinese with search and dark mode.

`scripts/build_docs.py` strictly builds both languages. GitHub Actions checks PR builds and can deploy GitHub Pages after main merges. Read the Docs configuration is included; project import needs access to that service. Configuration alone is not a live deployment: verify actual pages, language switching, search, plots and mobile layout after publication.

[Contribution and autoresearch](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) · [Issue queue](https://github.com/huangkiki/Dexlab/issues)

## Execution and recovery

Experiments prefer a resource-qualified local host; remote execution is optional. Review priorities and live jobs before selection, preserve interrupted evidence, and keep one executor. The [full workflow](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) documents enforced limits, timing/archive exclusion and delivery conditions. Continuous goals proceed between scheduled recovery checks; cloning does not install a scheduler.

[Actual delivery and interruption recovery audit](https://github.com/huangkiki/Dexlab/blob/main/docs/autonomous-delivery.md)
