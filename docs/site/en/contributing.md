# Add experiments and maintain reports

## Deliver an experiment

1. State the hypothesis, official versions, parameter provenance, approximations, budget, controls and acceptance in an issue.
2. Keep code, configuration and entrypoints in the corresponding `demos/` directory; shared scoring lives in `src/dexlab/`.
3. Save actual initial states, actions, trajectories, contacts and every outcome. Separate scoring from control and retain failures.
4. Update the experiment card and report in both languages: finding, setup, metric plots, failures, limitations and reproduction.
5. Explain reader-entry changes in the PR. Update the relevant website pages for capabilities, findings, significant failures and reproduction changes; update the concise README when positioning, representative previews or the recommended starting point changes.

## README and documentation

Keep README short: project purpose, representative experiment animations, one recommended starting point and website links. The site maintains research and usage details without duplicating full reports across README and the homepage.

| Content | Where to maintain it |
| --- | --- |
| Purpose, representative previews and minimal commands | Both READMEs; previews link to site reports. |
| Navigation by reader goal | The homepage Start here section, navigation and indexes. |
| Full methods, parameters, outcomes, failures and reproduction | The relevant experiment or usage page, linked from the experiment index. |
| External papers | References, topic guides and complete bibliographies, with sources, check dates and reading depth. |
| Plans, blockers and incremental progress | Current Work, issues, PRs and releases. |

Maintain the Newton guide in `docs/references/newton-reading-guide*.md` and its bibliography in `newton-publications*.md`; language pages include that content directly. When updating the upstream snapshot, reconcile the bibliography and seven-topic guide entry sets in both languages, preserving the comparison-only marker. Abstract checks must not be presented as full-paper reviews or reproductions.

Before publication, check source pages, site navigation, language switching and README entrypoints. After merge, verify the live revision and page content. Keep code runnable and private deployment details out of public documentation.

Every figure identifies versions, units, sample size, time window, uncertainty and provenance. Retain failed cases; unmatched calibration, geometry or tuning budgets do not support fair engine rankings.

## Publishing documentation

The site uses Sphinx, MyST and PyData Sphinx Theme, with information organization inspired by [RLinf](https://rlinf.readthedocs.io/en/latest/), not its research claims. Both languages share a theme and build command, defaulting to Chinese with search and dark mode.

`scripts/build_docs.py` strictly builds both languages. GitHub Actions checks PR builds and can deploy GitHub Pages after main merges. Read the Docs configuration is included; project import needs access to that service. Configuration alone is not a live deployment: verify actual pages, language switching, search, plots and mobile layout after publication.

[Contribution and autoresearch](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) · [Issue queue](https://github.com/huangkiki/Dexlab/issues)

## Execution and recovery

Experiments prefer a resource-qualified local host; remote execution is optional. Review priorities and live jobs before selection, preserve interrupted evidence, and keep one executor. The [full workflow](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) documents enforced limits, timing/archive exclusion and delivery conditions. Continuous goals proceed between scheduled recovery checks; cloning does not install a scheduler.

[Actual delivery and interruption recovery audit](https://github.com/huangkiki/Dexlab/blob/main/docs/autonomous-delivery.md)
