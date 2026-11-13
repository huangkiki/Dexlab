<h1 align="center">DexLab</h1>
<p align="center"><strong>Agents and simulation, improving together through experiments.</strong></p>
<p align="center">
  <a href="https://huangkiki.github.io/Dexlab/en/latest/">Website</a> ·
  <a href="https://huangkiki.github.io/Dexlab/en/latest/#blog">Blog</a> ·
  <a href="https://huangkiki.github.io/Dexlab/en/latest/#experiments">Experiments</a> ·
  <a href="https://huangkiki.github.io/Dexlab/en/latest/#learn">Learning map</a> ·
  <a href="README.md">简体中文</a>
</p>

**DexLab is for robot-learning and embodied-intelligence researchers working on contact-rich manipulation.** We explore recursive self-improvement (RSI): agent failures expose simulation gaps, and more trustworthy simulation helps improve agents.

**Try a task → diagnose failure → improve skills and simulation → independently retest → ask the next question.**

Humans set goals and boundaries; agents progressively help discover questions, experiment and iterate. Existing work centers on contact comparisons, failure diagnosis and rescorable evidence. A complete autonomous RSI loop remains a research direction.

<a id="findings"></a>
## Start with a failure

<a href="https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html"><img src="docs/evidence/wuji-contact/comparison.gif" width="720" alt="Original-speed 4.4-second Wuji replay: point contact on the left, synthetic torsional contact on the right"></a>

**Still in contact. Why does the sphere rotate?** Under the same controller, point contacts lack a torque direction about their connecting line. Offset gravity drives rotation, and hold drift exceeds the limit. Adding synthetic torsional contact reduces maximum two-second drift **2.734 → 1.025 mm**, passing the original **2 mm** limit and active-release checks.

This completed contact-model comparison still shows slow drift; it does not establish a complete autonomous RSI loop or real fingertip calibration. The new contact law also affects preparation, so the full displacement cannot be uniquely attributed to one degree of freedom. [Read the causal analysis, controls and next tests →](https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html)

## Explore further

| Your next step | Start here |
| --- | --- |
| **Read the research Blog** | [Follow questions and topics](https://huangkiki.github.io/Dexlab/en/latest/#blog): contact and physics, failure and evaluation, agents and simulation. |
| **Inspect experiments and evidence** | [Experiment directory](https://huangkiki.github.io/Dexlab/en/latest/experiments.html): tasks, records, comparisons and reproduction. |
| **Learn simulation systematically** | The [learning map](https://huangkiki.github.io/Dexlab/en/latest/#learn) connects prerequisites to experiments. Courses are maintained in [Sim Learning](https://github.com/huangkiki/sim-learning), primarily in Chinese with English terminology and summaries. |

<a id="architecture"></a><a id="quickstart"></a>
[Architecture](https://huangkiki.github.io/Dexlab/en/latest/about.html#architecture) · [Setup & reproduction](https://huangkiki.github.io/Dexlab/en/latest/quickstart.html) · [Contribute](https://huangkiki.github.io/Dexlab/en/latest/contributing.html) · [Apache-2.0](LICENSE)
