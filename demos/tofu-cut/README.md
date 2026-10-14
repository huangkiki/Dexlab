# Synthetic tofu halving

[English](README.md) | [简体中文](README.zh-CN.md)

A single-cut CPU TLMPM reference based on [BladeMaster v2](https://arxiv.org/abs/2609.27342v2): dynamic blade/material reaction, persistent separation after withdrawal and a one-sided diagnostic impulse. Synthetic parameters; no robot arm or real-food calibration.

[![Recorded tofu surface](../../docs/evidence/cutting/tofu/surface-poster.png)](https://huangkiki.github.io/Dexlab/en/latest/cutting.html)

[Method, parameters, acceptance, results and bounded reproduction](https://huangkiki.github.io/Dexlab/en/latest/cutting.html) · [Protocol source](../../docs/site/en/cutting.md)

- Run: `python -m dexlab.tofu_cut --output NEW_DIRECTORY`
- Negative controls: `--mode partial` / `--mode uncut`
- Rescore: `python -m dexlab.cutting_score RUN_DIRECTORY`
- Replay: `python -m dexlab.cutting_showcase RUN_DIRECTORY --output MEDIA_DIRECTORY`

Use the bounded, shared-guard command in the protocol for physics and postprocessing. Optional dependencies are in `dexlab[cutting,cutting-render]`. Every run records states, per-step observations, configuration, source hashes and an independent score. The experiment is a custom reference task, not a seventh qualified engine.

[Original v0.61.0 particle replay](media/replay.gif) is preserved. [Three sequential banana cuts](../banana-cut/README.md) extend the implementation with persistent multi-cut history.
