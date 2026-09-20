# Autoresearch

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

A scheduled Codex worker reads GitHub issues, implements one bounded change, runs verification, commits it on an isolated branch, and opens a PR. `scripts/autoresearch.py` manages the queue, worktree, checks and submission; Codex performs the research and edits. The script alone is not a model or an autonomous optimizer. It does not run Astra/Jev inside the grasp controller.

## Queue and execution

1. Select an open issue labeled `autoresearch`, excluding `needs-input` and issues with an open `autoresearch/issue-N` PR. Lowest issue number first; an empty queue produces `null`.
2. Create or resume `.autoresearch/worktrees/issue-N`, based on `origin/main`. Existing work is preserved. Only one scheduled worker operates this queue.
3. Read the acceptance criteria and source evidence. Implement a bounded change; record parameter origins, assumptions and failed experiments. Update both documentation languages.
4. Run unit tests and both full 14-second native SDF grasps through UniLab, followed by independent verification. Failure stops submission.
5. Commit, push `autoresearch/issue-N`, and create/update a PR with changes and evidence. Main is not rewritten or automatically merged. `Fixes #N` closes the issue only after merge.

Run these queue commands from the primary checkout; install and edit code inside the returned isolated worktree.

```bash
python3 scripts/autoresearch.py next
python3 scripts/autoresearch.py start 1
# In the returned worktree: bash scripts/setup.sh, then implement the issue.
python3 scripts/autoresearch.py check .autoresearch/worktrees/issue-1
python3 scripts/autoresearch.py submit 1 --summary-file /path/to/review.md
```

`submit` reruns the checks immediately before committing; a past passing log is insufficient. Authentication is supplied by the existing `gh` and Git setup. For SSH-based installations, configure the repository's origin accordingly. Each worktree needs its own editable install; do not share a virtualenv whose editable package points to a different checkout. Asset and uv download caches are reusable.

## Scheduling

The Codex app heartbeat checks this thread hourly and handles at most one issue per run. Scheduling is local to the app/account: cloning this repository does not create a schedule or grant model access. The host must be available, with authenticated GitHub tools and its Python environment. The worker reports a submitted PR or a concrete blocker and stays quiet for an unchanged empty queue. It must not retry the same failing experiment indefinitely.

This implements issue-driven assisted research, not guaranteed unattended scientific discovery. A model audit or reproducible experiment can be automated; missing hardware measurements cannot. PR review remains the gate to main.

## Current issues

- [#1 Model audit](https://github.com/huangkiki/Dexlab/issues/1) — ready for autoresearch.
- [#2 Jitter and contact interruption](https://github.com/huangkiki/Dexlab/issues/2) — ready for autoresearch.
- [#3 Frozen regression and timestep study](https://github.com/huangkiki/Dexlab/issues/3) — research backlog.
- [#4 UniSim built-in adapter qualification](https://github.com/huangkiki/Dexlab/issues/4) — research backlog.
- [#5 PhysX / IsaacSim](https://github.com/huangkiki/Dexlab/issues/5) — needs a supported worker environment.
- [#6 Hardware calibration](https://github.com/huangkiki/Dexlab/issues/6) — needs measured data.

[Research parameters and assumptions](research-focus.md) · [DexLab](../README.en.md)
