# DexLab External-Work Distillation and Research Intake Contract

[English](distill-contract.md) | [简体中文](distill-contract.zh-CN.md)

This document defines DexLab's repository-specific distillation destinations, topic classification, and Research Intake interface. Generic skills (`distill`, `autodev`) read this contract when operating on DexLab rather than hardcoding DexLab schemas inside shared skills.

## 1. Four-step delivery sequence

When asked to distill an external paper, repository, or product for DexLab without another explicit destination, follow this order:

1. **Archive the paper note first (mandatory prerequisite)**: run the full `paper-reader` workflow into the configured Obsidian library (all figures, equations, tables, concepts, and enabled MOC refreshes). Chat summaries or local drafts do not substitute for archiving; vault Git commit/push follows shared config and existing authorization. Hand off five structured assets into distillation: pinned versions & open-source status, complete method breakdown, 1–2 most informative source figure URLs, core equations, and main experiment/ablation tables with counterexamples.
2. **Publish the bilingual Blog deep-dive (single source of truth)**: write `docs/site/zh/<slug>.md` and `docs/site/en/<slug>.md` (~1,500–2,500 words). **Establish what the external work actually does first (at-a-glance card, I/O and module pipeline, 1–2 key figures, load-bearing equations, main results/ablation table) before counterexamples, DexLab transfer order, and the first minimal falsifiable slice.**
   - Read `docs/topic-taxonomy.json` and register the matching `synthesis` entry in `docs/concept-atlas.json` with `"distillation": true` and the best-fitting `topic` (reuse existing topics unless genuinely uncovered, updating bilingual tests if a new topic is added).
   - Register the page in the `:hidden:` `toctree` of both `docs/site/zh/distillation.md` and `docs/site/en/distillation.md` (do not scatter distillations into `engines.md`).
   - Run `python3 scripts/build_docs.py` plus `test_concept_atlas.py` / `test_docs_workflow.py`; never report live publication before remote readback.
3. **Post a lightweight GitHub Discussion decision card**: because the Blog page is the single source of truth, keep the Discussion concise rather than duplicating the full text:
   - `TL;DR` and concrete verdict (which DexLab choice changes, what is proved, what remains untested);
   - Links to the bilingual Blog deep-dive;
   - Key tradeoffs and what evidence would flip the decision;
   - The single valid `dexlab-intake:v1` JSON block (Section 2).
   Reuse an existing same-topic Discussion when adding evidence; create a new one only for an independent topic, and read back target, body, and URL afterward.
4. **Sync Research Intake into Triage**: after Blog and Discussion readback, run:

   ```bash
   python3 scripts/autoresearch.py intake check --discussion NUMBER
   python3 scripts/autoresearch.py intake sync --discussion NUMBER
   ```

   Actionable decisions idempotently create or update one `[Research intake]` umbrella issue in Project 4 `Triage`; `watch`/`reject` decisions create no issue. **Triage umbrellas are non-executable and never receive `auto:approved`.**

## 2. `dexlab-intake:v1` machine block contract

The Discussion body must contain exactly one fenced JSON block matching the adjacent human summary:

```markdown
<!-- dexlab-intake:v1:start -->
```json
{
  "schema_version": 1,
  "discussion": 425,
  "slug": "stable-slug",
  "title": "Short decision title",
  "decision": "pilot",
  "summary": "One-sentence technical conclusion.",
  "current_work_impact": "How this relates to docs/current-work.md.",
  "candidates": [
    {
      "slug": "slice-slug",
      "kind": "experiment",
      "goal": "Concrete falsifiable goal.",
      "entrypoints": ["repo/relative/path"],
      "first_slice": "Smallest independently verifiable deliverable.",
      "acceptance": ["Concrete measurable acceptance criterion."],
      "depends_on": [],
      "non_goals": ["Explicit out-of-scope boundary."]
    }
  ]
}
```
<!-- dexlab-intake:v1:end -->
```

- `decision`: `adopt-existing`, `pilot`, `experiment`, `watch`, or `reject`.
- `candidates[*].kind`: `experiment`, `enhancement`, `bug`, `documentation`, or `infrastructure`.
- `watch`/`reject` must have `candidates: []`; actionable decisions require at least one candidate.
- `entrypoints` must be repository-relative paths.

## 3. Promoting a slice into execution

After reviewing an umbrella issue, the maintainer promotes a selected slice with:

```bash
python3 scripts/autoresearch.py intake promote --umbrella NUMBER --slice SLUG --priority P1
```

`promote` creates a linked child issue (with a valid `Depends on:` line and validation hints) in `Todo` without ever adding `auto:approved`. Only after the maintainer separately adds `auto:approved` and the issue passes author admission and dependency checks may `autodev` / `autoresearch` execute it. See [autoresearch.md](autoresearch.md#research-intake).
