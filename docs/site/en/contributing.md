# Add experiments and maintain reports

## Deliver an experiment

1. State the hypothesis, official versions, parameter provenance, approximations, budget, controls and acceptance in an issue.
2. Keep code, configuration and entrypoints in the corresponding `demos/` directory; shared scoring lives in `src/dexlab/`.
3. Save actual initial states, actions, trajectories, contacts and every outcome. Separate scoring from control and retain failures.
4. Update the experiment card and report in both languages: finding, setup, metric plots, failures, limitations and reproduction.
5. Explain the homepage impact in the PR. New capabilities, findings, significant failures and reproduction changes update README; internal-only maintenance may explain why no reader-facing update is needed.

## README and documentation

README presents the project, current conclusions, key plots, continuous close-ups and documentation entrypoints. This site and linked source reports maintain full parameters, methods, per-case results and failure analysis. Keep code runnable and private deployment details out of public documentation.

Every figure identifies versions, units, sample size, time window, uncertainty and provenance. Retain failed cases; unmatched calibration, geometry or tuning budgets do not support fair engine rankings.

## Publishing documentation

The site uses Sphinx, MyST and PyData Sphinx Theme, with information organization inspired by [RLinf](https://rlinf.readthedocs.io/en/latest/), not its research claims. Both languages share a theme and build command, defaulting to Chinese with search and dark mode.

`scripts/build_docs.py` strictly builds both languages. GitHub Actions checks PR builds and can deploy GitHub Pages after main merges. Read the Docs configuration is included; project import needs access to that service. Configuration alone is not a live deployment: verify actual pages, language switching, search, plots and mobile layout after publication.

[Contribution and autoresearch](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.md) · [Issue queue](https://github.com/huangkiki/Dexlab/issues)
